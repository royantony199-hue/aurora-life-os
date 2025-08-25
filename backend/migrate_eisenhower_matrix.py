#!/usr/bin/env python3
"""
Database Migration: Add Eisenhower Matrix and Smart Rescheduling columns
"""

import sqlite3
import sys
from pathlib import Path

def migrate_database():
    """Add missing columns for Eisenhower Matrix and Smart Rescheduling"""
    
    db_path = Path(__file__).parent / "aurorya.db"
    
    print("🔧 Eisenhower Matrix + Smart Rescheduling Migration")
    print("=" * 60)
    print(f"Database: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # List of columns to add
        migrations = [
            # Eisenhower Matrix columns
            {
                'column': 'eisenhower_quadrant',
                'type': 'VARCHAR',
                'sql': 'ALTER TABLE calendar_events ADD COLUMN eisenhower_quadrant VARCHAR'
            },
            {
                'column': 'is_urgent',
                'type': 'BOOLEAN',
                'sql': 'ALTER TABLE calendar_events ADD COLUMN is_urgent BOOLEAN DEFAULT 0'
            },
            {
                'column': 'is_important', 
                'type': 'BOOLEAN',
                'sql': 'ALTER TABLE calendar_events ADD COLUMN is_important BOOLEAN DEFAULT 1'
            },
            {
                'column': 'urgency_reason',
                'type': 'VARCHAR',
                'sql': 'ALTER TABLE calendar_events ADD COLUMN urgency_reason VARCHAR'
            },
            {
                'column': 'importance_reason',
                'type': 'VARCHAR', 
                'sql': 'ALTER TABLE calendar_events ADD COLUMN importance_reason VARCHAR'
            },
            
            # Smart Rescheduling columns
            {
                'column': 'depends_on_event_ids',
                'type': 'JSON',
                'sql': 'ALTER TABLE calendar_events ADD COLUMN depends_on_event_ids JSON'
            },
            {
                'column': 'blocks_event_ids',
                'type': 'JSON',
                'sql': 'ALTER TABLE calendar_events ADD COLUMN blocks_event_ids JSON'
            },
            {
                'column': 'auto_reschedule_enabled',
                'type': 'BOOLEAN',
                'sql': 'ALTER TABLE calendar_events ADD COLUMN auto_reschedule_enabled BOOLEAN DEFAULT 1'
            },
            {
                'column': 'reschedule_buffer_minutes',
                'type': 'INTEGER',
                'sql': 'ALTER TABLE calendar_events ADD COLUMN reschedule_buffer_minutes INTEGER DEFAULT 15'
            },
            {
                'column': 'dependency_type',
                'type': 'VARCHAR',
                'sql': 'ALTER TABLE calendar_events ADD COLUMN dependency_type VARCHAR'
            }
        ]
        
        # Check which columns already exist
        cursor.execute('PRAGMA table_info(calendar_events)')
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        print(f"📊 Found {len(existing_columns)} existing columns")
        
        # Apply migrations
        successful_migrations = 0
        skipped_migrations = 0
        
        for migration in migrations:
            column_name = migration['column']
            
            if column_name in existing_columns:
                print(f"⏭️  Skipping {column_name} (already exists)")
                skipped_migrations += 1
                continue
            
            try:
                print(f"➕ Adding column: {column_name} ({migration['type']})")
                cursor.execute(migration['sql'])
                successful_migrations += 1
            except Exception as e:
                print(f"❌ Failed to add {column_name}: {e}")
                return False
        
        # Commit changes
        conn.commit()
        
        print(f"\n✅ Migration completed successfully!")
        print(f"   • {successful_migrations} columns added")
        print(f"   • {skipped_migrations} columns skipped (already existed)")
        
        # Verify the migration
        cursor.execute('PRAGMA table_info(calendar_events)')
        new_columns = cursor.fetchall()
        print(f"   • Total columns now: {len(new_columns)}")
        
        # Test a simple query to ensure everything works
        cursor.execute('SELECT COUNT(*) FROM calendar_events')
        event_count = cursor.fetchone()[0]
        print(f"   • {event_count} existing events preserved")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def verify_migration():
    """Verify that all required columns exist"""
    db_path = Path(__file__).parent / "aurorya.db"
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute('PRAGMA table_info(calendar_events)')
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        required_columns = [
            'eisenhower_quadrant', 'is_urgent', 'is_important',
            'urgency_reason', 'importance_reason', 'depends_on_event_ids',
            'blocks_event_ids', 'auto_reschedule_enabled', 
            'reschedule_buffer_minutes', 'dependency_type'
        ]
        
        print(f"\n🔍 Verification:")
        all_present = True
        for col in required_columns:
            if col in column_names:
                print(f"✅ {col}")
            else:
                print(f"❌ {col} - MISSING")
                all_present = False
        
        if all_present:
            print(f"\n🎉 All required columns are present!")
            print(f"🚀 Calendar optimization should now work!")
        else:
            print(f"\n⚠️  Some columns are still missing")
            
        return all_present
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Starting database migration...")
    
    if migrate_database():
        verify_migration()
        print("\n🎯 Ready to test: 'Optimize my calendar by priority'")
    else:
        print("\n❌ Migration failed - check errors above")
        sys.exit(1)