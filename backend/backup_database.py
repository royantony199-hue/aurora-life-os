#!/usr/bin/env python3
"""
Aurora Life OS Database Backup and Restore Utility
Preserves goals, mood entries, calendar events, and chat history
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Any

class DatabaseBackup:
    def __init__(self, db_path: str = "aurorya.db", backup_dir: str = "backups"):
        self.db_path = db_path
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
    
    def create_backup(self, backup_name: str = None) -> str:
        """Create a full backup of important data"""
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"aurora_backup_{timestamp}"
        
        backup_file = os.path.join(self.backup_dir, f"{backup_name}.json")
        
        if not os.path.exists(self.db_path):
            print(f"Database file {self.db_path} not found!")
            return None
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        
        backup_data = {
            "backup_timestamp": datetime.now().isoformat(),
            "backup_name": backup_name,
            "version": "1.0",
            "goals": self._backup_goals(conn),
            "mood_entries": self._backup_mood_entries(conn),
            "calendar_events": self._backup_calendar_events(conn),
            "chat_messages": self._backup_chat_messages(conn),
            "users": self._backup_users(conn)
        }
        
        conn.close()
        
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        print(f"✅ Backup created: {backup_file}")
        print(f"📊 Backed up {len(backup_data['goals'])} goals, {len(backup_data['mood_entries'])} mood entries, {len(backup_data['calendar_events'])} events, {len(backup_data['chat_messages'])} chat messages")
        
        return backup_file
    
    def restore_backup(self, backup_file: str, merge: bool = True) -> bool:
        """Restore data from backup file"""
        if not os.path.exists(backup_file):
            print(f"Backup file {backup_file} not found!")
            return False
        
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Restore users first
            self._restore_users(cursor, backup_data.get('users', []), merge)
            
            # Restore goals
            goals_restored = self._restore_goals(cursor, backup_data.get('goals', []), merge)
            
            # Restore mood entries
            mood_restored = self._restore_mood_entries(cursor, backup_data.get('mood_entries', []), merge)
            
            # Restore calendar events
            events_restored = self._restore_calendar_events(cursor, backup_data.get('calendar_events', []), merge)
            
            # Restore chat messages (optional, might be a lot of data)
            # chat_restored = self._restore_chat_messages(cursor, backup_data.get('chat_messages', []), merge)
            
            conn.commit()
            conn.close()
            
            print(f"✅ Restore completed!")
            print(f"📊 Restored {goals_restored} goals, {mood_restored} mood entries, {events_restored} calendar events")
            
            return True
            
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            conn.rollback()
            conn.close()
            return False
    
    def _backup_goals(self, conn: sqlite3.Connection) -> List[Dict]:
        """Backup goals table"""
        cursor = conn.execute("SELECT * FROM goals")
        return [dict(row) for row in cursor.fetchall()]
    
    def _backup_mood_entries(self, conn: sqlite3.Connection) -> List[Dict]:
        """Backup mood_entries table"""
        try:
            cursor = conn.execute("SELECT * FROM mood_entries")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            return []  # Table doesn't exist yet
    
    def _backup_calendar_events(self, conn: sqlite3.Connection) -> List[Dict]:
        """Backup calendar_events table"""
        try:
            cursor = conn.execute("SELECT * FROM calendar_events")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            return []  # Table doesn't exist yet
    
    def _backup_chat_messages(self, conn: sqlite3.Connection) -> List[Dict]:
        """Backup chat_messages table (limit to recent messages to avoid huge files)"""
        try:
            cursor = conn.execute("SELECT * FROM chat_messages ORDER BY created_at DESC LIMIT 100")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            return []  # Table doesn't exist yet
    
    def _backup_users(self, conn: sqlite3.Connection) -> List[Dict]:
        """Backup users table"""
        try:
            cursor = conn.execute("SELECT * FROM users")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            return []  # Table doesn't exist yet
    
    def _restore_goals(self, cursor: sqlite3.Cursor, goals: List[Dict], merge: bool) -> int:
        """Restore goals table"""
        if not goals:
            return 0
        
        restored = 0
        for goal in goals:
            if merge:
                # Check if goal already exists by title
                existing = cursor.execute(
                    "SELECT id FROM goals WHERE title = ? AND user_id = ?", 
                    (goal['title'], goal['user_id'])
                ).fetchone()
                if existing:
                    # Update existing goal
                    cursor.execute("""
                        UPDATE goals SET description=?, category=?, status=?, progress=?, 
                               target_date=?, updated_at=CURRENT_TIMESTAMP
                        WHERE id=?
                    """, (goal['description'], goal['category'], goal['status'], 
                         goal['progress'], goal['target_date'], existing[0]))
                    continue
            
            # Insert new goal
            cursor.execute("""
                INSERT INTO goals (user_id, title, description, category, status, progress, target_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (goal['user_id'], goal['title'], goal['description'], goal['category'],
                  goal['status'], goal['progress'], goal['target_date'], goal['created_at']))
            restored += 1
        
        return restored
    
    def _restore_mood_entries(self, cursor: sqlite3.Cursor, entries: List[Dict], merge: bool) -> int:
        """Restore mood_entries table"""
        if not entries:
            return 0
        
        restored = 0
        for entry in entries:
            if merge:
                # Check if entry exists for same user and date
                existing = cursor.execute(
                    "SELECT id FROM mood_entries WHERE user_id = ? AND DATE(created_at) = DATE(?)",
                    (entry['user_id'], entry['created_at'])
                ).fetchone()
                if existing:
                    continue  # Skip duplicate entries
            
            cursor.execute("""
                INSERT INTO mood_entries (user_id, mood_level, energy_level, notes, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (entry['user_id'], entry['mood_level'], entry['energy_level'],
                  entry['notes'], entry['created_at']))
            restored += 1
        
        return restored
    
    def _restore_calendar_events(self, cursor: sqlite3.Cursor, events: List[Dict], merge: bool) -> int:
        """Restore calendar_events table"""
        if not events:
            return 0
        
        restored = 0
        for event in events:
            if merge:
                # Check if event exists by google_event_id or title+time
                if event.get('google_event_id'):
                    existing = cursor.execute(
                        "SELECT id FROM calendar_events WHERE google_event_id = ?",
                        (event['google_event_id'],)
                    ).fetchone()
                else:
                    existing = cursor.execute(
                        "SELECT id FROM calendar_events WHERE title = ? AND start_time = ? AND user_id = ?",
                        (event['title'], event['start_time'], event['user_id'])
                    ).fetchone()
                
                if existing:
                    continue  # Skip duplicate events
            
            # Insert new event with all fields
            cursor.execute("""
                INSERT INTO calendar_events (
                    user_id, title, description, event_type, start_time, end_time,
                    google_event_id, google_calendar_data, is_synced, sync_status,
                    meeting_url, meeting_id, meeting_passcode, meeting_phone, meeting_type,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event['user_id'], event['title'], event['description'], event['event_type'],
                event['start_time'], event['end_time'], event.get('google_event_id'),
                event.get('google_calendar_data'), event.get('is_synced', False),
                event.get('sync_status', 'pending'), event.get('meeting_url'),
                event.get('meeting_id'), event.get('meeting_passcode'),
                event.get('meeting_phone'), event.get('meeting_type'), event['created_at']
            ))
            restored += 1
        
        return restored
    
    def _restore_users(self, cursor: sqlite3.Cursor, users: List[Dict], merge: bool) -> int:
        """Restore users table"""
        if not users:
            return 0
        
        restored = 0
        for user in users:
            if merge:
                existing = cursor.execute("SELECT id FROM users WHERE email = ?", (user['email'],)).fetchone()
                if existing:
                    continue
            
            cursor.execute("""
                INSERT INTO users (username, email, full_name, created_at)
                VALUES (?, ?, ?, ?)
            """, (user['username'], user['email'], user['full_name'], user['created_at']))
            restored += 1
        
        return restored
    
    def list_backups(self) -> List[str]:
        """List available backup files"""
        backups = []
        if os.path.exists(self.backup_dir):
            for file in os.listdir(self.backup_dir):
                if file.endswith('.json'):
                    backups.append(os.path.join(self.backup_dir, file))
        return sorted(backups)


if __name__ == "__main__":
    import sys
    
    backup_manager = DatabaseBackup()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python backup_database.py backup [name]    # Create backup")
        print("  python backup_database.py restore <file>   # Restore from backup")
        print("  python backup_database.py list             # List backups")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "backup":
        name = sys.argv[2] if len(sys.argv) > 2 else None
        backup_manager.create_backup(name)
    
    elif command == "restore":
        if len(sys.argv) < 3:
            print("Please specify backup file to restore")
            sys.exit(1)
        backup_file = sys.argv[2]
        backup_manager.restore_backup(backup_file)
    
    elif command == "list":
        backups = backup_manager.list_backups()
        if backups:
            print("Available backups:")
            for backup in backups:
                print(f"  {backup}")
        else:
            print("No backups found")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)