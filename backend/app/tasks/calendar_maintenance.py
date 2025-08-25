"""
Calendar maintenance tasks for Aurora Life OS
This module handles automatic token refresh and calendar health checks
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.services.google_calendar_service import GoogleCalendarService

logger = logging.getLogger(__name__)

class CalendarMaintenance:
    """Handles calendar maintenance tasks"""
    
    def __init__(self):
        self.google_service = GoogleCalendarService()
    
    async def refresh_all_tokens(self):
        """ULTRA-AGGRESSIVE token refresh for all users - NEVER DISCONNECT"""
        db = next(get_db())
        try:
            # Get ALL users (not just marked as connected) - some might have valid tokens but wrong DB state
            all_users = db.query(User).all()
            
            logger.info(f"🔄 ULTRA-ROBUST: Starting token refresh for {len(all_users)} users")
            
            for user in all_users:
                try:
                    # ULTRA-AGGRESSIVE: Try to get credentials regardless of database state
                    credentials = self.google_service.get_user_credentials(user.id)
                    
                    if credentials and credentials.valid:
                        # Force database to show connected
                        if not user.google_calendar_connected:
                            logger.info(f"🔧 ULTRA-ROBUST: Fixing database state for user {user.id}")
                            user.google_calendar_connected = True
                            db.commit()
                        logger.info(f"✅ ULTRA-ROBUST: Token validated/refreshed for user {user.id}")
                    else:
                        # Only mark as disconnected if we truly can't recover
                        if user.google_calendar_connected:
                            logger.warning(f"⚠️ ULTRA-ROBUST: Could not recover token for user {user.id}")
                            # DON'T disconnect immediately - try recovery first
                            await self.attempt_token_recovery(user.id, db)
                        
                except Exception as e:
                    logger.error(f"❌ ULTRA-ROBUST: Token refresh failed for user {user.id}: {e}")
                    # DON'T give up - attempt recovery
                    await self.attempt_token_recovery(user.id, db)
            
            logger.info("🏁 ULTRA-ROBUST: Token refresh cycle completed")
            
        except Exception as e:
            logger.error(f"❌ ULTRA-ROBUST: Token refresh cycle failed: {e}")
        finally:
            db.close()
    
    async def attempt_token_recovery(self, user_id: int, db: Session):
        """Last-ditch effort to recover user's calendar connection"""
        try:
            logger.info(f"🚑 RECOVERY: Attempting token recovery for user {user_id}")
            
            # Check if backup token exists
            import os
            token_dir = self.google_service.token_dir
            backup_file = os.path.join(token_dir, f'token_{user_id}_backup.json')
            
            if os.path.exists(backup_file):
                logger.info(f"🔄 RECOVERY: Found backup token for user {user_id}")
                # Try to load and test backup
                credentials = self.google_service.get_user_credentials(user_id)
                if credentials and credentials.valid:
                    logger.info(f"✅ RECOVERY: Backup token recovered for user {user_id}")
                    # Force database update
                    user = db.query(User).filter(User.id == user_id).first()
                    if user:
                        user.google_calendar_connected = True
                        db.commit()
                    return True
            
            logger.warning(f"🚨 RECOVERY: Could not recover token for user {user_id}")
            return False
            
        except Exception as e:
            logger.error(f"❌ RECOVERY: Recovery attempt failed for user {user_id}: {e}")
            return False
    
    async def health_check_connections(self):
        """Perform health check on all calendar connections"""
        db = next(get_db())
        try:
            connected_users = db.query(User).filter(
                User.google_calendar_connected == True
            ).all()
            
            logger.info(f"🩺 Health check for {len(connected_users)} calendar connections")
            
            for user in connected_users:
                try:
                    is_healthy = self.google_service.is_calendar_connected(user.id)
                    if not is_healthy:
                        logger.warning(f"🚨 User {user.id} calendar connection unhealthy")
                        user.google_calendar_connected = False
                        db.commit()
                    else:
                        logger.info(f"💚 User {user.id} calendar connection healthy")
                        
                except Exception as e:
                    logger.error(f"❌ Health check failed for user {user.id}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Health check cycle failed: {e}")
        finally:
            db.close()
    
    async def cleanup_expired_tokens(self):
        """Clean up tokens that can't be refreshed"""
        import os
        tokens_dir = self.google_service.token_dir
        
        if not os.path.exists(tokens_dir):
            return
            
        logger.info("🧹 Cleaning up expired/invalid tokens")
        
        for filename in os.listdir(tokens_dir):
            if filename.startswith('token_') and filename.endswith('.json'):
                token_path = os.path.join(tokens_dir, filename)
                user_id = filename.replace('token_', '').replace('.json', '')
                
                try:
                    user_id_int = int(user_id)
                    credentials = self.google_service.get_user_credentials(user_id_int)
                    
                    if not credentials or not credentials.valid:
                        # Token is permanently invalid
                        os.remove(token_path)
                        logger.info(f"🗑️ Removed invalid token file: {filename}")
                        
                        # Update database
                        db = next(get_db())
                        user = db.query(User).filter(User.id == user_id_int).first()
                        if user:
                            user.google_calendar_connected = False
                            db.commit()
                        db.close()
                        
                except (ValueError, Exception) as e:
                    logger.error(f"❌ Error processing token file {filename}: {e}")

# Global maintenance instance
calendar_maintenance = CalendarMaintenance()

# Scheduler functions that can be called by external schedulers
async def daily_token_refresh():
    """Daily token refresh task"""
    logger.info("🕒 Running daily token refresh")
    await calendar_maintenance.refresh_all_tokens()

async def hourly_health_check():
    """Hourly health check task"""
    logger.info("🕒 Running hourly health check")
    await calendar_maintenance.health_check_connections()

async def weekly_cleanup():
    """Weekly cleanup task"""
    logger.info("🕒 Running weekly cleanup")
    await calendar_maintenance.cleanup_expired_tokens()