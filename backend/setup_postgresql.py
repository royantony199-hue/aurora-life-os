#!/usr/bin/env python3
"""
PostgreSQL Setup Script for Aurora Life OS
Helps configure and migrate from SQLite to PostgreSQL
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import subprocess
import sqlite3
from pathlib import Path

def check_postgresql_installed():
    """Check if PostgreSQL is installed and running"""
    try:
        result = subprocess.run(['pg_isready'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def create_database(db_name, username, password, host='localhost', port='5432'):
    """Create PostgreSQL database and user"""
    try:
        # Connect to PostgreSQL server (default database)
        conn = psycopg2.connect(
            host=host,
            port=port,
            database='postgres',
            user='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create user if not exists
        cursor.execute(f"""
            DO $$ BEGIN
                CREATE USER {username} WITH PASSWORD '{password}';
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        
        # Create database if not exists
        cursor.execute(f"""
            SELECT 1 FROM pg_database WHERE datname='{db_name}'
        """)
        
        if not cursor.fetchone():
            cursor.execute(f'CREATE DATABASE {db_name} OWNER {username}')
            print(f"✅ Database '{db_name}' created successfully")
        else:
            print(f"ℹ️  Database '{db_name}' already exists")
        
        # Grant privileges
        cursor.execute(f'GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {username}')
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def generate_env_file(db_name, username, password, host='localhost', port='5432'):
    """Generate .env file with PostgreSQL configuration"""
    env_content = f"""# Aurora Life OS Production Configuration
# Database Configuration
DATABASE_URL=postgresql://{username}:{password}@{host}:{port}/{db_name}
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Application Settings
ENVIRONMENT=production
DEBUG=false

# Security (Generate new keys for production!)
SECRET_KEY=your-secret-key-change-this-in-production
REFRESH_SECRET_KEY=your-refresh-secret-key-change-this
ENCRYPTION_KEY=your-encryption-key-change-this

# Google Calendar Integration
GOOGLE_REDIRECT_URI=https://yourdomain.com/api/calendar/google/callback
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# OpenAI Integration
OPENAI_API_KEY=your-openai-api-key

# CORS Configuration (Update for production)
CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]

# Rate Limiting
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
"""
    
    env_file = Path(__file__).parent / '.env.production'
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Environment file created: {env_file}")
    return env_file

def migrate_data_from_sqlite(sqlite_path, postgres_url):
    """Migrate data from SQLite to PostgreSQL"""
    print("🔄 Starting data migration from SQLite to PostgreSQL...")
    
    try:
        # This would require a more complex migration script
        # For now, just provide instructions
        print("""
📋 Data Migration Instructions:

1. Export data from SQLite:
   sqlite3 aurorya.db .dump > data_export.sql

2. Clean up the SQL file for PostgreSQL:
   - Remove SQLite-specific syntax
   - Fix data types
   - Handle sequence/auto-increment differences

3. Import to PostgreSQL:
   psql -d aurora_life_os -U aurora_user < cleaned_data.sql

4. Run Alembic migrations to ensure schema is up to date:
   alembic upgrade head

For automatic migration, consider using pgloader:
   pgloader aurorya.db postgresql://aurora_user:password@localhost/aurora_life_os
        """)
        
    except Exception as e:
        print(f"❌ Migration error: {e}")

def setup_postgresql():
    """Main setup function"""
    print("🚀 Aurora Life OS PostgreSQL Setup")
    print("=" * 50)
    
    # Check if PostgreSQL is installed
    if not check_postgresql_installed():
        print("❌ PostgreSQL is not installed or not running")
        print("Please install PostgreSQL first:")
        print("  - macOS: brew install postgresql && brew services start postgresql")
        print("  - Ubuntu: sudo apt-get install postgresql postgresql-contrib")
        print("  - Windows: Download from https://www.postgresql.org/download/")
        return False
    
    print("✅ PostgreSQL is running")
    
    # Configuration
    db_name = input("Database name [aurora_life_os]: ").strip() or "aurora_life_os"
    username = input("Database username [aurora_user]: ").strip() or "aurora_user"
    password = input("Database password [aurora_password]: ").strip() or "aurora_password"
    host = input("Database host [localhost]: ").strip() or "localhost"
    port = input("Database port [5432]: ").strip() or "5432"
    
    # Create database
    if create_database(db_name, username, password, host, port):
        print("✅ PostgreSQL database setup completed")
        
        # Generate environment file
        env_file = generate_env_file(db_name, username, password, host, port)
        
        print("\n📝 Next Steps:")
        print("1. Review and update the generated .env.production file")
        print("2. Generate secure secret keys for production")
        print("3. Configure your domain and CORS settings")
        print("4. Run database migrations: alembic upgrade head")
        print("5. Migrate data from SQLite if needed")
        
        # Ask about data migration
        migrate_data = input("\nDo you want to migrate data from SQLite? (y/N): ").strip().lower()
        if migrate_data in ['y', 'yes']:
            sqlite_path = input("SQLite database path [aurorya.db]: ").strip() or "aurorya.db"
            postgres_url = f"postgresql://{username}:{password}@{host}:{port}/{db_name}"
            migrate_data_from_sqlite(sqlite_path, postgres_url)
        
        return True
    
    return False

if __name__ == "__main__":
    success = setup_postgresql()
    if success:
        print("\n🎉 PostgreSQL setup completed successfully!")
        print("Your Aurora Life OS is ready for production deployment!")
    else:
        print("\n❌ PostgreSQL setup failed")
        sys.exit(1)