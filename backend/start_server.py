#!/usr/bin/env python3
"""
Aurora Life OS - FastAPI Server with Integrated Scheduler
Enhanced version that includes calendar automation
"""

import uvicorn
import os
import sys
import subprocess
import signal
import time
import threading
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

class AuroraLifeOSServer:
    def __init__(self):
        self.scheduler_process = None
        self.server_process = None
        
    def check_dependencies(self):
        """Check if all dependencies are available"""
        print("🔍 Checking dependencies...")
        
        # Check Redis
        try:
            import redis
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            r = redis.from_url(redis_url)
            r.ping()
            print("✅ Redis connection successful")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            print("💡 Install and start Redis: brew install redis && brew services start redis")
            return False
            
        # Check environment variables
        if not os.getenv('OPENAI_API_KEY'):
            print("⚠️  Warning: OPENAI_API_KEY not set")
            
        if not os.getenv('DATABASE_URL'):
            print("⚠️  Warning: DATABASE_URL not set, using default SQLite")
            
        return True
    
    def start_scheduler(self):
        """Start the Celery scheduler in background"""
        print("⏰ Starting calendar automation scheduler...")
        
        def run_scheduler():
            try:
                # Start Celery beat scheduler
                beat_cmd = [
                    "celery", "-A", "app.core.celery_app", "beat",
                    "--loglevel=info",
                    "--scheduler=celery.beat:PersistentScheduler"
                ]
                
                self.scheduler_process = subprocess.Popen(
                    beat_cmd, 
                    cwd=backend_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                print("✅ Calendar automation scheduler started")
                
            except Exception as e:
                print(f"❌ Failed to start scheduler: {e}")
        
        # Run scheduler in background thread
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        time.sleep(2)  # Give scheduler time to start
    
    def start_server(self):
        """Start the FastAPI server"""
        print("🚀 Starting Aurora Life OS API server...")
        
        # Configuration
        config = {
            "app": "app.main:app",
            "host": "0.0.0.0",
            "port": int(os.getenv("PORT", 8001)),
            "reload": os.getenv("ENVIRONMENT", "development") == "development",
            "log_level": os.getenv("LOG_LEVEL", "info").lower()
        }
        
        print(f"🌐 Server will start on http://localhost:{config['port']}")
        print("📚 API docs available at http://localhost:{}/docs".format(config['port']))
        
        # Start server
        uvicorn.run(**config)
    
    def stop_services(self):
        """Stop all services gracefully"""
        print("\n🛑 Shutting down Aurora Life OS...")
        
        if self.scheduler_process:
            try:
                self.scheduler_process.terminate()
                self.scheduler_process.wait(timeout=10)
                print("✅ Scheduler stopped")
            except subprocess.TimeoutExpired:
                self.scheduler_process.kill()
                print("⚠️  Scheduler force killed")
            except Exception as e:
                print(f"❌ Error stopping scheduler: {e}")
    
    def run(self):
        """Main run method"""
        print("🌅 Aurora Life OS - AI Personal Assistant")
        print("=" * 50)
        
        # Check dependencies
        if not self.check_dependencies():
            sys.exit(1)
        
        try:
            # Start scheduler
            self.start_scheduler()
            
            # Start main server (this blocks)
            self.start_server()
            
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_services()

def main():
    """Entry point"""
    server = AuroraLifeOSServer()
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        server.stop_services()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the server
    server.run()

if __name__ == "__main__":
    main()