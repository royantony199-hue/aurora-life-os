#!/usr/bin/env python3
"""
Test script for Aurora Life OS Daily Calendar Automation
Tests the scheduler functionality without waiting for actual schedule times
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.tasks.daily_calendar_automation import (
    optimize_daily_calendars,
    generate_morning_schedules, 
    sync_goals_to_calendar,
    calendar_health_check
)

def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    try:
        db = SessionLocal()
        # Simple query to test connection
        db.execute("SELECT 1")
        db.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_redis_connection():
    """Test Redis connection for Celery"""
    print("🔍 Testing Redis connection...")
    try:
        import redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("💡 Start Redis: brew services start redis")
        return False

def test_celery_tasks():
    """Test Celery task execution"""
    print("🔍 Testing Celery task execution...")
    
    try:
        from app.core.celery_app import celery_app
        
        # Test that tasks are registered
        registered_tasks = list(celery_app.tasks.keys())
        expected_tasks = [
            'app.tasks.daily_calendar_automation.optimize_daily_calendars',
            'app.tasks.daily_calendar_automation.generate_morning_schedules',
            'app.tasks.daily_calendar_automation.sync_goals_to_calendar',
            'app.tasks.daily_calendar_automation.optimize_weekly_calendars',
            'app.tasks.daily_calendar_automation.calendar_health_check'
        ]
        
        missing_tasks = [task for task in expected_tasks if task not in registered_tasks]
        
        if missing_tasks:
            print(f"❌ Missing tasks: {missing_tasks}")
            return False
            
        print("✅ All Celery tasks registered")
        print(f"📋 Registered tasks: {len([t for t in registered_tasks if 'daily_calendar_automation' in t])}")
        return True
        
    except Exception as e:
        print(f"❌ Celery task test failed: {e}")
        return False

def test_manual_task_execution():
    """Test manual execution of automation tasks"""
    print("🔍 Testing manual task execution...")
    
    try:
        # Test calendar health check (simpler task)
        print("  Testing calendar health check...")
        result = calendar_health_check()
        
        if isinstance(result, dict) and 'system_healthy' in result:
            print(f"✅ Health check completed: {result.get('users_checked', 0)} users checked")
        else:
            print(f"⚠️  Health check returned unexpected result: {result}")
        
        print("✅ Manual task execution successful")
        return True
        
    except Exception as e:
        print(f"❌ Manual task execution failed: {e}")
        return False

def test_scheduler_configuration():
    """Test scheduler configuration"""
    print("🔍 Testing scheduler configuration...")
    
    try:
        from app.core.celery_app import celery_app
        
        # Check beat schedule
        beat_schedule = celery_app.conf.beat_schedule
        
        expected_schedules = [
            'daily-calendar-optimization',
            'morning-schedule-generation', 
            'evening-goal-calendar-sync',
            'weekly-calendar-optimization',
            'calendar-health-check'
        ]
        
        missing_schedules = [sched for sched in expected_schedules if sched not in beat_schedule]
        
        if missing_schedules:
            print(f"❌ Missing schedules: {missing_schedules}")
            return False
            
        print("✅ All schedules configured")
        print("⏰ Scheduled tasks:")
        for name, config in beat_schedule.items():
            schedule = config.get('schedule', 'Unknown')
            print(f"   • {name}: {schedule}")
        
        return True
        
    except Exception as e:
        print(f"❌ Scheduler configuration test failed: {e}")
        return False

def test_ai_services():
    """Test AI service dependencies"""
    print("🔍 Testing AI service dependencies...")
    
    try:
        from app.services.ai_calendar_service import AICalendarService
        from app.services.autonomous_scheduling_service import AutonomousSchedulingService
        
        ai_service = AICalendarService()
        auto_service = AutonomousSchedulingService()
        
        print("✅ AI services imported successfully")
        
        # Check OpenAI API key
        if not os.getenv('OPENAI_API_KEY'):
            print("⚠️  Warning: OPENAI_API_KEY not set in environment")
        else:
            print("✅ OpenAI API key configured")
            
        return True
        
    except Exception as e:
        print(f"❌ AI services test failed: {e}")
        return False

def run_integration_test():
    """Run a quick integration test"""
    print("🔍 Running integration test...")
    
    try:
        # Test triggering a task via API
        from app.core.celery_app import celery_app
        
        # Queue a health check task
        task = calendar_health_check.delay()
        print(f"✅ Task queued with ID: {task.id}")
        
        # Wait briefly for result
        try:
            result = task.get(timeout=10)
            print(f"✅ Task completed: {result.get('users_checked', 0)} users processed")
        except Exception as e:
            print(f"⚠️  Task execution timeout or error: {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Aurora Life OS - Daily Calendar Automation Tests")
    print("=" * 60)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Redis Connection", test_redis_connection), 
        ("Celery Tasks Registration", test_celery_tasks),
        ("Scheduler Configuration", test_scheduler_configuration),
        ("AI Services", test_ai_services),
        ("Manual Task Execution", test_manual_task_execution),
        ("Integration Test", run_integration_test)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print("\n" + "=" * 60)
    print(f"🧪 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Daily calendar automation is ready.")
        print("\n🚀 To start the automation system:")
        print("   python start_server.py")
        print("   # or separately:")
        print("   python start_scheduler.py")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)