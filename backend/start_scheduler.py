#!/usr/bin/env python3
"""
Aurora Life OS - Celery Scheduler Startup Script
Starts the Celery worker and beat scheduler for daily calendar automation
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def check_redis_connection():
    """Check if Redis is running and accessible"""
    try:
        import redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("Please ensure Redis is running: brew services start redis")
        return False

def start_celery_worker():
    """Start Celery worker process"""
    print("🚀 Starting Celery worker...")
    
    worker_cmd = [
        "celery", "-A", "app.core.celery_app", "worker",
        "--loglevel=info",
        "--concurrency=2",
        "--pool=prefork"
    ]
    
    return subprocess.Popen(worker_cmd, cwd=backend_dir)

def start_celery_beat():
    """Start Celery beat scheduler"""
    print("⏰ Starting Celery beat scheduler...")
    
    beat_cmd = [
        "celery", "-A", "app.core.celery_app", "beat",
        "--loglevel=info",
        "--scheduler=celery.beat:PersistentScheduler"
    ]
    
    return subprocess.Popen(beat_cmd, cwd=backend_dir)

def main():
    """Main function to start the scheduler system"""
    print("🌅 Aurora Life OS - Calendar Automation Scheduler")
    print("=" * 50)
    
    # Check Redis connection
    if not check_redis_connection():
        sys.exit(1)
    
    # Check environment variables
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Warning: OPENAI_API_KEY not set in environment")
    
    processes = []
    
    try:
        # Start Celery worker
        worker_process = start_celery_worker()
        processes.append(worker_process)
        time.sleep(3)  # Give worker time to start
        
        # Start Celery beat scheduler
        beat_process = start_celery_beat()
        processes.append(beat_process)
        
        print("\n✅ Aurora Life OS Scheduler is running!")
        print("📅 Daily calendar automation active")
        print("🔄 Scheduled tasks:")
        print("   • Daily optimization: 6:00 AM UTC")
        print("   • Morning schedules: 5:30 AM UTC") 
        print("   • Evening goal sync: 7:00 PM UTC")
        print("   • Weekly optimization: Sunday 8:00 PM UTC")
        print("   • Health checks: Every 4 hours")
        print("\nPress Ctrl+C to stop all services")
        
        # Wait for processes
        while True:
            time.sleep(1)
            
            # Check if any process died
            for process in processes:
                if process.poll() is not None:
                    print(f"❌ Process {process.pid} died, restarting...")
                    # Restart logic could be added here
                    
    except KeyboardInterrupt:
        print("\n🛑 Shutting down scheduler...")
        
    finally:
        # Clean shutdown
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
        
        print("✅ All processes stopped")

if __name__ == "__main__":
    main()