#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from app.core.database import engine, Base
from app.models import user, chat, goal, mood, calendar as calendar_models, task

def create_all_tables():
    """Create all database tables"""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # List all tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📋 Created tables: {', '.join(tables)}")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        
if __name__ == "__main__":
    create_all_tables()