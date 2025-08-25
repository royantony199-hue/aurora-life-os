#!/usr/bin/env python3

import sys
import os

# Set the correct working directory
os.chdir('/Users/royantony/auroyra life os/backend')
sys.path.append('.')

from app.core.database import SessionLocal, engine
from app.models.user import User
from sqlalchemy.orm import Session

def create_default_user():
    """Create a default user for testing"""
    db = SessionLocal()
    
    try:
        # Check if user with id=1 already exists
        existing_user = db.query(User).filter(User.id == 1).first()
        
        if not existing_user:
            # Create default user
            default_user = User(
                id=1,
                email="demo@auroralifeOS.com",
                username="demo",
                hashed_password="demo_password",
                full_name="Demo User",
                is_active=True,
                google_calendar_connected=False,
                onboarding_completed=True
            )
            
            db.add(default_user)
            db.commit()
            print("✅ Created default user with ID=1")
        else:
            print(f"✅ Default user already exists: {existing_user.email}")
            
    except Exception as e:
        print(f"❌ Error creating default user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_default_user()