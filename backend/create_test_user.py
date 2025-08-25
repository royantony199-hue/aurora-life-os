#!/usr/bin/env python3
"""
Create a test user for Aurora Life OS
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def create_test_user():
    """Create a test user for development"""
    db = SessionLocal()
    
    try:
        # Check if test user already exists
        existing_user = db.query(User).filter(User.username == "testuser").first()
        if existing_user:
            print("✅ Test user already exists")
            print(f"   Username: {existing_user.username}")
            print(f"   Email: {existing_user.email}")
            print(f"   ID: {existing_user.id}")
            return existing_user
        
        # Create test user
        test_user = User(
            username="testuser",
            email="test@aurora.com",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print("🎉 Test user created successfully!")
        print(f"   Username: {test_user.username}")
        print(f"   Email: {test_user.email}")
        print(f"   Password: password123")
        print(f"   ID: {test_user.id}")
        print("\n📝 You can now login with these credentials:")
        print("   Email: test@aurora.com")
        print("   Password: password123")
        
        return test_user
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()