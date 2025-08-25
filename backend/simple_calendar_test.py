#!/usr/bin/env python3
"""
Simple Calendar Connection Test - Bulletproof Version
This bypasses all complex routing and directly tests calendar connectivity
"""

import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

def test_calendar_connection(user_id=2):
    """Test calendar connection directly"""
    print(f"🔍 Testing calendar connection for user {user_id}")
    
    token_file = f"tokens/token_{user_id}.json"
    
    if not os.path.exists(token_file):
        print(f"❌ Token file not found: {token_file}")
        return False
    
    try:
        print(f"📄 Loading token file: {token_file}")
        credentials = Credentials.from_authorized_user_file(token_file)
        
        if not credentials:
            print("❌ Failed to load credentials")
            return False
            
        print(f"🔍 Token status: expired={credentials.expired}, valid={credentials.valid}")
        
        # Refresh if needed
        if credentials.expired and credentials.refresh_token:
            print("🔄 Refreshing expired token...")
            credentials.refresh(Request())
            
            # Save refreshed credentials
            with open(token_file, 'w') as f:
                f.write(credentials.to_json())
            print("✅ Token refreshed and saved")
        
        # Test API connectivity
        print("🌐 Testing Google Calendar API...")
        service = build('calendar', 'v3', credentials=credentials)
        
        # Simple API test
        calendar_list = service.calendarList().list(maxResults=1).execute()
        calendars_found = len(calendar_list.get('items', []))
        
        print(f"✅ SUCCESS: {calendars_found} calendar(s) found")
        print(f"✅ Google Calendar API is working for user {user_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Direct Calendar Connection Test...")
    
    # Test both users
    for user_id in [1, 2]:
        print(f"\n{'='*50}")
        success = test_calendar_connection(user_id)
        if success:
            print(f"🎉 User {user_id}: CALENDAR CONNECTION WORKING")
        else:
            print(f"💥 User {user_id}: CALENDAR CONNECTION FAILED")
    
    print(f"\n{'='*50}")
    print("🏁 Direct test completed")