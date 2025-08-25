#!/usr/bin/env python3
"""
Automated backup service for Aurora Life OS
Handles both database backups and application data exports
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
import subprocess
import schedule
import time

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.core.config import settings
from app.core.database import engine, SessionLocal
from app.models import User, Goal, Mood, CalendarEvent, Chat, Task
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BackupService:
    def __init__(self):
        self.backup_dir = Path(os.getenv("BACKUP_DIR", "./database/backups"))
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))
        
    def create_database_backup(self) -> bool:
        """Create a PostgreSQL database backup using pg_dump"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"postgres_backup_{timestamp}.sql"
            
            # Extract database connection details
            db_url = settings.database_url
            if not db_url.startswith("postgresql"):
                logger.error("Database backup only supports PostgreSQL")
                return False
            
            # Parse database URL
            # Format: postgresql://user:password@host:port/database
            from urllib.parse import urlparse
            parsed = urlparse(db_url)
            
            # Create pg_dump command
            cmd = [
                "pg_dump",
                f"--host={parsed.hostname}",
                f"--port={parsed.port or 5432}",
                f"--username={parsed.username}",
                f"--dbname={parsed.path[1:]}",  # Remove leading slash
                "--verbose",
                "--clean",
                "--if-exists",
                "--create",
                "--format=plain"
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = parsed.password
            
            logger.info(f"Creating database backup: {backup_file}")
            
            with open(backup_file, 'w') as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True
                )
            
            if result.returncode == 0:
                # Compress backup
                compressed_file = f"{backup_file}.gz"
                subprocess.run(["gzip", str(backup_file)], check=True)
                
                # Create metadata
                metadata = {
                    "type": "postgres_backup",
                    "timestamp": timestamp,
                    "database": parsed.path[1:],
                    "host": parsed.hostname,
                    "file": os.path.basename(compressed_file),
                    "size": os.path.getsize(compressed_file),
                    "created": datetime.now().isoformat()
                }
                
                with open(f"{compressed_file}.json", 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                logger.info(f"✅ Database backup created: {compressed_file}")
                logger.info(f"📏 Backup size: {metadata['size']} bytes")
                return True
            else:
                logger.error(f"❌ pg_dump failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Database backup failed: {e}")
            return False

    def create_application_backup(self) -> bool:
        """Create a JSON backup of application data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"app_data_backup_{timestamp}.json"
            
            logger.info("Creating application data backup...")
            
            session = SessionLocal()
            backup_data = {}
            
            # Backup users (without passwords)
            users = session.query(User).all()
            backup_data['users'] = [
                {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None
                }
                for user in users
            ]
            
            # Backup goals
            goals = session.query(Goal).all()
            backup_data['goals'] = [
                {
                    'id': goal.id,
                    'user_id': goal.user_id,
                    'title': goal.title,
                    'description': goal.description,
                    'status': goal.status,
                    'priority': goal.priority,
                    'target_date': goal.target_date.isoformat() if goal.target_date else None,
                    'created_at': goal.created_at.isoformat() if hasattr(goal, 'created_at') and goal.created_at else None
                }
                for goal in goals
            ]
            
            # Backup mood entries
            moods = session.query(Mood).all()
            backup_data['moods'] = [
                {
                    'id': mood.id,
                    'user_id': mood.user_id,
                    'mood_score': mood.mood_score,
                    'notes': mood.notes,
                    'created_at': mood.created_at.isoformat() if mood.created_at else None
                }
                for mood in moods
            ]
            
            # Backup calendar events
            events = session.query(CalendarEvent).all()
            backup_data['calendar_events'] = [
                {
                    'id': event.id,
                    'user_id': event.user_id,
                    'title': event.title,
                    'description': event.description,
                    'start_time': event.start_time.isoformat() if event.start_time else None,
                    'end_time': event.end_time.isoformat() if event.end_time else None,
                    'google_event_id': getattr(event, 'google_event_id', None),
                    'created_at': event.created_at.isoformat() if hasattr(event, 'created_at') and event.created_at else None
                }
                for event in events
            ]
            
            # Backup chat messages
            chats = session.query(Chat).all()
            backup_data['chat_messages'] = [
                {
                    'id': chat.id,
                    'user_id': chat.user_id,
                    'message': chat.message,
                    'response': chat.response,
                    'timestamp': chat.timestamp.isoformat() if chat.timestamp else None
                }
                for chat in chats
            ]
            
            # Create metadata
            metadata = {
                "type": "application_backup",
                "timestamp": timestamp,
                "record_counts": {
                    "users": len(backup_data['users']),
                    "goals": len(backup_data['goals']),
                    "moods": len(backup_data['moods']),
                    "calendar_events": len(backup_data['calendar_events']),
                    "chat_messages": len(backup_data['chat_messages'])
                },
                "created": datetime.now().isoformat()
            }
            
            # Combine metadata and data
            full_backup = {
                "metadata": metadata,
                "data": backup_data
            }
            
            # Save backup
            with open(backup_file, 'w') as f:
                json.dump(full_backup, f, indent=2, default=str)
            
            session.close()
            
            file_size = os.path.getsize(backup_file)
            logger.info(f"✅ Application backup created: {backup_file}")
            logger.info(f"📊 Records: {metadata['record_counts']}")
            logger.info(f"📏 File size: {file_size} bytes")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Application backup failed: {e}")
            return False

    def cleanup_old_backups(self):
        """Remove backups older than retention period"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            deleted_count = 0
            
            for backup_file in self.backup_dir.glob("*backup_*.sql.gz"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    # Remove associated metadata files
                    metadata_file = Path(f"{backup_file}.json")
                    if metadata_file.exists():
                        metadata_file.unlink()
                    deleted_count += 1
            
            for backup_file in self.backup_dir.glob("*backup_*.json"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"🗑️  Cleaned up {deleted_count} old backup files")
                
        except Exception as e:
            logger.error(f"❌ Backup cleanup failed: {e}")

    def run_full_backup(self):
        """Run both database and application backups"""
        logger.info("🚀 Starting full backup process...")
        
        db_success = self.create_database_backup()
        app_success = self.create_application_backup()
        
        if db_success and app_success:
            logger.info("✅ Full backup completed successfully!")
        else:
            logger.warning("⚠️  Backup completed with some failures")
        
        # Cleanup old backups
        self.cleanup_old_backups()
        
        return db_success and app_success

    def schedule_backups(self):
        """Schedule automatic backups"""
        # Daily database backup at 2 AM
        schedule.every().day.at("02:00").do(self.create_database_backup)
        
        # Weekly full backup on Sunday at 3 AM
        schedule.every().sunday.at("03:00").do(self.run_full_backup)
        
        # Daily application backup at 1 AM
        schedule.every().day.at("01:00").do(self.create_application_backup)
        
        # Cleanup every day at 4 AM
        schedule.every().day.at("04:00").do(self.cleanup_old_backups)
        
        logger.info("📅 Backup schedule configured:")
        logger.info("   - Daily database backup: 2:00 AM")
        logger.info("   - Daily application backup: 1:00 AM")
        logger.info("   - Weekly full backup: Sunday 3:00 AM")
        logger.info("   - Daily cleanup: 4:00 AM")

    def run_service(self):
        """Run the backup service"""
        logger.info("🔄 Starting backup service...")
        self.schedule_backups()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("🛑 Backup service stopped by user")
        except Exception as e:
            logger.error(f"❌ Backup service error: {e}")


def main():
    """Main function"""
    backup_service = BackupService()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "database":
            backup_service.create_database_backup()
        elif command == "application":
            backup_service.create_application_backup()
        elif command == "full":
            backup_service.run_full_backup()
        elif command == "cleanup":
            backup_service.cleanup_old_backups()
        elif command == "service":
            backup_service.run_service()
        else:
            print("Usage: python backup_service.py [database|application|full|cleanup|service]")
            sys.exit(1)
    else:
        # Default: run full backup
        backup_service.run_full_backup()


if __name__ == "__main__":
    main()