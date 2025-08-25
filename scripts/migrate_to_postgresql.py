#!/usr/bin/env python3
"""
Database migration script from SQLite to PostgreSQL
Run this script to migrate existing SQLite data to PostgreSQL
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import User, Chat, Goal, Mood, CalendarEvent, Task
from app.core.database import Base
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    def __init__(self, sqlite_path: str, postgresql_url: str):
        self.sqlite_path = sqlite_path
        self.postgresql_url = postgresql_url
        
        # Create engines
        self.sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
        self.postgres_engine = create_engine(postgresql_url)
        
        # Create sessions
        SqliteSession = sessionmaker(bind=self.sqlite_engine)
        PostgresSession = sessionmaker(bind=self.postgres_engine)
        
        self.sqlite_session = SqliteSession()
        self.postgres_session = PostgresSession()

    def check_connections(self):
        """Test both database connections"""
        try:
            # Test SQLite
            self.sqlite_session.execute(text("SELECT 1"))
            logger.info("✅ SQLite connection successful")
            
            # Test PostgreSQL
            self.postgres_session.execute(text("SELECT 1"))
            logger.info("✅ PostgreSQL connection successful")
            
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    def create_postgres_schema(self):
        """Create PostgreSQL schema"""
        try:
            Base.metadata.create_all(self.postgres_engine)
            logger.info("✅ PostgreSQL schema created")
        except Exception as e:
            logger.error(f"❌ Failed to create PostgreSQL schema: {e}")
            raise

    def backup_existing_data(self):
        """Create a backup of existing data"""
        backup_data = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"migration_backup_{timestamp}.json"
        
        try:
            # Backup users
            users = self.sqlite_session.query(User).all()
            backup_data['users'] = [
                {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'hashed_password': user.hashed_password,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None
                }
                for user in users
            ]
            
            # Backup goals
            goals = self.sqlite_session.query(Goal).all()
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
            moods = self.sqlite_session.query(Mood).all()
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
            events = self.sqlite_session.query(CalendarEvent).all()
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
            chats = self.sqlite_session.query(Chat).all()
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
            
            # Backup tasks if they exist
            try:
                tasks = self.sqlite_session.query(Task).all()
                backup_data['tasks'] = [
                    {
                        'id': task.id,
                        'user_id': task.user_id,
                        'title': task.title,
                        'description': task.description,
                        'status': task.status,
                        'priority': task.priority,
                        'due_date': task.due_date.isoformat() if hasattr(task, 'due_date') and task.due_date else None,
                        'created_at': task.created_at.isoformat() if hasattr(task, 'created_at') and task.created_at else None
                    }
                    for task in tasks
                ]
            except Exception:
                logger.warning("Tasks table not found or empty, skipping...")
                backup_data['tasks'] = []
            
            # Save backup
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            logger.info(f"✅ Backup created: {backup_file}")
            logger.info(f"📊 Backup contains: {len(backup_data['users'])} users, "
                       f"{len(backup_data['goals'])} goals, {len(backup_data['moods'])} moods, "
                       f"{len(backup_data['calendar_events'])} events, {len(backup_data['chat_messages'])} chats")
            
            return backup_file, backup_data
            
        except Exception as e:
            logger.error(f"❌ Failed to create backup: {e}")
            raise

    def migrate_data(self, backup_data):
        """Migrate data to PostgreSQL"""
        try:
            # Clear existing data (if any)
            logger.info("🗑️  Clearing existing PostgreSQL data...")
            self.postgres_session.query(Chat).delete()
            self.postgres_session.query(CalendarEvent).delete() 
            self.postgres_session.query(Goal).delete()
            self.postgres_session.query(Mood).delete()
            self.postgres_session.query(Task).delete()
            self.postgres_session.query(User).delete()
            self.postgres_session.commit()
            
            # Migrate users first (due to foreign key relationships)
            logger.info("👤 Migrating users...")
            for user_data in backup_data['users']:
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    hashed_password=user_data['hashed_password'],
                    is_active=user_data['is_active']
                )
                self.postgres_session.add(user)
            self.postgres_session.commit()
            logger.info(f"✅ Migrated {len(backup_data['users'])} users")
            
            # Create user ID mapping
            sqlite_users = {user.username: user.id for user in self.sqlite_session.query(User).all()}
            postgres_users = {user.username: user.id for user in self.postgres_session.query(User).all()}
            user_id_map = {sqlite_users[username]: postgres_users[username] 
                          for username in sqlite_users if username in postgres_users}
            
            # Migrate goals
            logger.info("🎯 Migrating goals...")
            for goal_data in backup_data['goals']:
                if goal_data['user_id'] in user_id_map:
                    goal = Goal(
                        user_id=user_id_map[goal_data['user_id']],
                        title=goal_data['title'],
                        description=goal_data['description'],
                        status=goal_data['status'],
                        priority=goal_data['priority'],
                        target_date=datetime.fromisoformat(goal_data['target_date']) if goal_data['target_date'] else None
                    )
                    self.postgres_session.add(goal)
            self.postgres_session.commit()
            logger.info(f"✅ Migrated {len(backup_data['goals'])} goals")
            
            # Migrate mood entries
            logger.info("😊 Migrating mood entries...")
            for mood_data in backup_data['moods']:
                if mood_data['user_id'] in user_id_map:
                    mood = Mood(
                        user_id=user_id_map[mood_data['user_id']],
                        mood_score=mood_data['mood_score'],
                        notes=mood_data['notes'],
                        created_at=datetime.fromisoformat(mood_data['created_at']) if mood_data['created_at'] else None
                    )
                    self.postgres_session.add(mood)
            self.postgres_session.commit()
            logger.info(f"✅ Migrated {len(backup_data['moods'])} mood entries")
            
            # Migrate calendar events
            logger.info("📅 Migrating calendar events...")
            for event_data in backup_data['calendar_events']:
                if event_data['user_id'] in user_id_map:
                    event = CalendarEvent(
                        user_id=user_id_map[event_data['user_id']],
                        title=event_data['title'],
                        description=event_data['description'],
                        start_time=datetime.fromisoformat(event_data['start_time']) if event_data['start_time'] else None,
                        end_time=datetime.fromisoformat(event_data['end_time']) if event_data['end_time'] else None
                    )
                    if hasattr(event, 'google_event_id') and event_data.get('google_event_id'):
                        event.google_event_id = event_data['google_event_id']
                    self.postgres_session.add(event)
            self.postgres_session.commit()
            logger.info(f"✅ Migrated {len(backup_data['calendar_events'])} calendar events")
            
            # Migrate chat messages
            logger.info("💬 Migrating chat messages...")
            for chat_data in backup_data['chat_messages']:
                if chat_data['user_id'] in user_id_map:
                    chat = Chat(
                        user_id=user_id_map[chat_data['user_id']],
                        message=chat_data['message'],
                        response=chat_data['response'],
                        timestamp=datetime.fromisoformat(chat_data['timestamp']) if chat_data['timestamp'] else None
                    )
                    self.postgres_session.add(chat)
            self.postgres_session.commit()
            logger.info(f"✅ Migrated {len(backup_data['chat_messages'])} chat messages")
            
            # Migrate tasks
            if backup_data['tasks']:
                logger.info("✅ Migrating tasks...")
                for task_data in backup_data['tasks']:
                    if task_data['user_id'] in user_id_map:
                        task = Task(
                            user_id=user_id_map[task_data['user_id']],
                            title=task_data['title'],
                            description=task_data['description'],
                            status=task_data['status'],
                            priority=task_data['priority']
                        )
                        self.postgres_session.add(task)
                self.postgres_session.commit()
                logger.info(f"✅ Migrated {len(backup_data['tasks'])} tasks")
            
            logger.info("🎉 Data migration completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Data migration failed: {e}")
            self.postgres_session.rollback()
            raise

    def verify_migration(self):
        """Verify that migration was successful"""
        try:
            logger.info("🔍 Verifying migration...")
            
            # Count records in PostgreSQL
            user_count = self.postgres_session.query(User).count()
            goal_count = self.postgres_session.query(Goal).count()
            mood_count = self.postgres_session.query(Mood).count()
            event_count = self.postgres_session.query(CalendarEvent).count()
            chat_count = self.postgres_session.query(Chat).count()
            
            logger.info(f"📊 PostgreSQL contains:")
            logger.info(f"   Users: {user_count}")
            logger.info(f"   Goals: {goal_count}")
            logger.info(f"   Moods: {mood_count}")
            logger.info(f"   Calendar Events: {event_count}")
            logger.info(f"   Chat Messages: {chat_count}")
            
            # Test a sample query
            if user_count > 0:
                sample_user = self.postgres_session.query(User).first()
                logger.info(f"✅ Sample user: {sample_user.username} ({sample_user.email})")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration verification failed: {e}")
            return False

    def close_connections(self):
        """Clean up database connections"""
        self.sqlite_session.close()
        self.postgres_session.close()


def main():
    """Main migration function"""
    logger.info("🚀 Starting SQLite to PostgreSQL migration...")
    
    # Configuration
    sqlite_path = os.getenv("SQLITE_PATH", "./aurorya.db")
    postgresql_url = os.getenv("DATABASE_URL", "postgresql://aurora_user:aurora_pass@localhost:5432/aurora_db")
    
    if not os.path.exists(sqlite_path):
        logger.error(f"❌ SQLite database not found: {sqlite_path}")
        return False
    
    logger.info(f"📂 Source: {sqlite_path}")
    logger.info(f"🐘 Target: {postgresql_url}")
    
    # Create migrator
    migrator = DatabaseMigrator(sqlite_path, postgresql_url)
    
    try:
        # Check connections
        if not migrator.check_connections():
            return False
        
        # Create PostgreSQL schema
        migrator.create_postgres_schema()
        
        # Backup data
        backup_file, backup_data = migrator.backup_existing_data()
        
        # Migrate data
        migrator.migrate_data(backup_data)
        
        # Verify migration
        if migrator.verify_migration():
            logger.info("🎉 Migration completed successfully!")
            logger.info(f"📄 Backup saved to: {backup_file}")
            logger.info("⚠️  Remember to update your .env file to use PostgreSQL:")
            logger.info(f"   DATABASE_URL={postgresql_url}")
            return True
        else:
            logger.error("❌ Migration verification failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False
    finally:
        migrator.close_connections()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)