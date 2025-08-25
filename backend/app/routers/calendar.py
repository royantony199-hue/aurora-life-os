from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import os

from app.core.database import get_db
from app.core.config import settings
from app.models import CalendarEvent, User
from app.services.google_calendar_service import GoogleCalendarService
from app.routers.auth import get_current_user

router = APIRouter()
google_calendar_service = GoogleCalendarService()


class CalendarEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    event_type: str = "task"


class CalendarEventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    event_type: str
    is_synced: bool
    sync_status: str
    meeting_url: Optional[str] = None
    meeting_id: Optional[str] = None
    meeting_passcode: Optional[str] = None
    meeting_phone: Optional[str] = None
    meeting_type: Optional[str] = None
    
    class Config:
        from_attributes = True


class GoogleCredentialsConfig(BaseModel):
    web: Dict[str, Any]


@router.get("/connect-google")
async def connect_google_calendar(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Get Google Calendar OAuth URL for user to connect their calendar"""
    try:
        # Use 127.0.0.1 to match credentials.json configuration
        redirect_uri = "http://127.0.0.1:8001/api/calendar/google/callback"
        
        auth_url = google_calendar_service.get_auth_url(
            user_id=current_user.id,
            redirect_uri=redirect_uri
        )
        
        return {
            "auth_url": auth_url,
            "message": "Visit this URL to connect your Google Calendar"
        }
        
    except FileNotFoundError as e:
        return {
            "error": str(e),
            "setup_instructions": "To enable Google Calendar integration:\n1. Go to Google Cloud Console\n2. Create OAuth 2.0 credentials\n3. Download credentials.json to backend folder\n4. Restart the server"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/google/callback")
async def google_calendar_callback(
    code: str = None,
    state: str = None,
    error: str = None,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Handle Google Calendar OAuth callback"""
    try:
        # Check for OAuth errors first
        if error:
            return {
                "success": False,
                "error": f"OAuth error: {error}",
                "detail": "User denied access or OAuth flow failed"
            }
        
        if not code or not state:
            return {
                "success": False,
                "error": "Missing authorization code or state parameter",
                "detail": f"code: {bool(code)}, state: {bool(state)}"
            }
        
        # Use configured redirect URI or fall back to default for development
        redirect_uri = settings.google_redirect_uri or "http://127.0.0.1:8001/api/calendar/google/callback"
        
        result = google_calendar_service.handle_oauth_callback(
            authorization_code=code,
            state=state,
            redirect_uri=redirect_uri
        )
        
        if result['success']:
            # Update user's calendar connection status in database
            user_id = result['user_id']
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.google_calendar_connected = True
                db.commit()
                logger.info(f"Updated calendar connection for user {user_id}")
            else:
                logger.error(f"User {user_id} not found during OAuth callback")
            
            # Always sync calendar events when connection is successful
            try:
                print(f"🔄 Auto-syncing calendar events for user {user_id}")
                sync_result = google_calendar_service.sync_calendar_events(user_id, db, days_ahead=60)
                events_synced = sync_result.get('events_synced', 0) if sync_result else 0
                print(f"✅ Auto-sync completed: {events_synced} events synced")
            except Exception as sync_error:
                print(f"❌ Auto-sync failed: {sync_error}")
                events_synced = 0
            
            # Return HTML response that redirects back to the app
            return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Google Calendar Connected</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    .success {{ color: #52C41A; font-size: 24px; margin-bottom: 20px; }}
                    .info {{ color: #666; margin-bottom: 30px; }}
                    .redirecting {{ color: #1890FF; }}
                </style>
            </head>
            <body>
                <div class="success">✅ Google Calendar Connected Successfully!</div>
                <div class="info">
                    Account: royantony1000@gmail.com<br>
                    Calendars: {result.get('calendars_found', 0)}<br>
                    Events Synced: {events_synced}
                </div>
                <div class="redirecting">Redirecting back to Aurora Life OS...</div>
                <script>
                    setTimeout(function() {{
                        window.location.href = 'http://localhost:5173/#/profile';
                    }}, 2000);
                </script>
            </body>
            </html>
            """)
        else:
            error_detail = result.get('error', 'Unknown error')
            logger.error(f"OAuth failed: {error_detail}")
            return {
                "success": False,
                "error": error_detail,
                "detail": "OAuth token exchange failed"
            }
            
    except Exception as e:
        logger.error(f"Exception in OAuth callback: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "detail": "Internal server error during OAuth callback"
        }


@router.post("/configure")
async def configure_google_credentials(credentials: GoogleCredentialsConfig):
    """Configure Google OAuth credentials"""
    try:
        # Save credentials to file
        credentials_path = "/Users/royantony/auroyra life os/backend/credentials.json"
        
        with open(credentials_path, 'w') as f:
            json.dump(credentials.dict(), f, indent=2)
        
        # Reinitialize the Google Calendar service with new credentials
        global google_calendar_service
        google_calendar_service = GoogleCalendarService()
        
        return {
            "success": True,
            "message": "Google credentials configured successfully",
            "credentials_path": credentials_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure credentials: {str(e)}")


@router.get("/connection-status")
async def get_calendar_connection_status(
    current_user: User = Depends(get_current_user)
):
    """Check if user's Google Calendar is connected with detailed health info"""
    is_connected = google_calendar_service.is_calendar_connected(current_user.id)
    
    # Get additional connection details
    token_file = os.path.join(google_calendar_service.token_dir, f'token_{current_user.id}.json')
    connection_details = {
        "google_calendar_connected": is_connected,
        "connected": is_connected,  # Alternative field name for compatibility
        "message": "Connected to Google Calendar" if is_connected else "Google Calendar not connected",
        "token_file_exists": os.path.exists(token_file),
        "user_id": current_user.id,
        "status": "connected" if is_connected else "disconnected"
    }
    
    # If connected, add token expiry information
    if is_connected and os.path.exists(token_file):
        try:
            import json
            with open(token_file, 'r') as f:
                token_data = json.load(f)
                if 'expiry' in token_data:
                    from datetime import datetime
                    expiry_dt = datetime.fromisoformat(token_data['expiry'].replace('Z', '+00:00'))
                    now = datetime.now(expiry_dt.tzinfo)
                    hours_until_expiry = (expiry_dt - now).total_seconds() / 3600
                    
                    connection_details.update({
                        "token_expires_at": token_data['expiry'],
                        "hours_until_expiry": round(hours_until_expiry, 2),
                        "has_refresh_token": bool(token_data.get('refresh_token')),
                        "token_health": "healthy" if hours_until_expiry > 24 else "expires_soon" if hours_until_expiry > 1 else "expired_but_refreshable" if token_data.get('refresh_token') else "expired"
                    })
        except Exception as e:
            connection_details["token_error"] = str(e)
    
    return connection_details

@router.get("/profile-status") 
async def get_profile_calendar_status(
    current_user: User = Depends(get_current_user)
):
    """Profile-specific calendar status endpoint"""
    is_connected = google_calendar_service.is_calendar_connected(current_user.id)
    
    return {
        "google_calendar": {
            "connected": is_connected,
            "status": "connected" if is_connected else "not_connected",
            "message": "Google Calendar is connected and working" if is_connected else "Google Calendar not connected"
        },
        "user_id": current_user.id
    }


@router.get("/status")
async def get_calendar_status(
    user_id: int = 1
):
    """Legacy endpoint for calendar status - redirects to connection-status"""
    is_connected = google_calendar_service.is_calendar_connected(user_id)
    
    return {
        "connected": is_connected,
        "google_calendar_connected": is_connected,
        "message": "Connected to Google Calendar" if is_connected else "Google Calendar not connected"
    }


@router.post("/refresh-token")
async def refresh_calendar_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Proactively refresh Google Calendar token"""
    try:
        # Force a credential refresh by calling get_user_credentials
        credentials = google_calendar_service.get_user_credentials(current_user.id)
        
        if credentials and credentials.valid:
            return {
                "success": True,
                "message": "Token refreshed successfully",
                "token_status": "valid"
            }
        else:
            return {
                "success": False,
                "message": "Failed to refresh token - re-authentication required",
                "token_status": "invalid"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Token refresh failed: {str(e)}",
            "token_status": "error"
        }

@router.post("/sync")
async def sync_google_calendar(
    days_ahead: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually sync Google Calendar events with robust error handling"""
    try:
        # First check and refresh token if needed
        if not google_calendar_service.is_calendar_connected(current_user.id):
            # Try to refresh token one more time
            credentials = google_calendar_service.get_user_credentials(current_user.id)
            if not credentials or not credentials.valid:
                raise HTTPException(
                    status_code=400, 
                    detail="Google Calendar not connected. Please reconnect your calendar."
                )
        
        result = google_calendar_service.sync_calendar_events(current_user.id, db, days_ahead)
        
        if result['success']:
            return {
                "success": True,
                "events_synced": result['events_synced'],
                "message": f"Synced {result['events_synced']} events from Google Calendar"
            }
        else:
            # Handle specific Google API errors
            error_msg = result.get('error', 'Unknown sync error')
            if 'invalid_grant' in error_msg.lower() or 'unauthorized' in error_msg.lower():
                # Token is invalid, need re-auth
                google_calendar_service._mark_user_disconnected(current_user.id)
                raise HTTPException(
                    status_code=401, 
                    detail="Calendar authorization expired. Please reconnect your Google Calendar."
                )
            else:
                raise HTTPException(status_code=500, detail=f"Sync failed: {error_msg}")
                
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        # Catch any other errors
        print(f"❌ Sync error for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Calendar sync failed: {str(e)}")


@router.get("/events", response_model=List[CalendarEventResponse])
async def get_calendar_events(
    days_ahead: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's calendar events"""
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=days_ahead)
    
    events = db.query(CalendarEvent).filter(
        CalendarEvent.user_id == current_user.id,
        CalendarEvent.start_time >= start_date,
        CalendarEvent.start_time <= end_date
    ).order_by(CalendarEvent.start_time).all()
    
    response_events = []
    for event in events:
        response_data = {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "start_time": event.start_time,
            "end_time": event.end_time,
            "event_type": event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type),
            "is_synced": event.is_synced,
            "sync_status": event.sync_status,
            "meeting_url": event.meeting_url,
            "meeting_id": event.meeting_id,
            "meeting_passcode": event.meeting_passcode,
            "meeting_phone": event.meeting_phone,
            "meeting_type": event.meeting_type
        }
        response_events.append(CalendarEventResponse(**response_data))
    
    return response_events


@router.delete("/events/{event_id}")
async def delete_calendar_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a calendar event from both local database and Google Calendar"""
    
    # Find the event
    event = db.query(CalendarEvent).filter(
        CalendarEvent.id == event_id,
        CalendarEvent.user_id == current_user.id
    ).first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    google_deleted = False
    google_error = None
    
    # Delete from Google Calendar if it's synced
    if event.google_event_id and google_calendar_service.is_calendar_connected(current_user.id):
        try:
            # Delete from Google Calendar
            from googleapiclient.discovery import build
            credentials = google_calendar_service.get_user_credentials(current_user.id)
            if credentials:
                service = build('calendar', 'v3', credentials=credentials)
                service.events().delete(
                    calendarId='primary',
                    eventId=event.google_event_id
                ).execute()
                google_deleted = True
        except Exception as e:
            google_error = str(e)
            print(f"Failed to delete from Google Calendar: {e}")
    
    # Delete from local database
    db.delete(event)
    db.commit()
    
    return {
        "success": True,
        "message": "Event deleted successfully",
        "event_id": event_id,
        "google_deleted": google_deleted,
        "google_error": google_error
    }


@router.put("/events/{event_id}")
async def update_calendar_event(
    event_id: int,
    event_data: CalendarEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a calendar event in both local database and Google Calendar"""
    
    # Find the event
    event = db.query(CalendarEvent).filter(
        CalendarEvent.id == event_id,
        CalendarEvent.user_id == current_user.id
    ).first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    google_updated = False
    google_error = None
    
    # Update in Google Calendar if it's synced
    if event.google_event_id and google_calendar_service.is_calendar_connected(current_user.id):
        try:
            from googleapiclient.discovery import build
            credentials = google_calendar_service.get_user_credentials(current_user.id)
            if credentials:
                service = build('calendar', 'v3', credentials=credentials)
                
                # Format event for Google Calendar API
                google_event = {
                    'summary': event_data.title,
                    'description': event_data.description or '',
                    'start': {
                        'dateTime': event_data.start_time.isoformat(),
                        'timeZone': 'UTC',
                    },
                    'end': {
                        'dateTime': event_data.end_time.isoformat(),
                        'timeZone': 'UTC',
                    },
                }
                
                service.events().update(
                    calendarId='primary',
                    eventId=event.google_event_id,
                    body=google_event
                ).execute()
                google_updated = True
        except Exception as e:
            google_error = str(e)
            print(f"Failed to update in Google Calendar: {e}")
    
    # Update local event
    event.title = event_data.title
    event.description = event_data.description
    event.start_time = event_data.start_time
    event.end_time = event_data.end_time
    event.event_type = event_data.event_type
    
    db.commit()
    
    return {
        "success": True,
        "message": "Event updated successfully",
        "event_id": event_id,
        "google_updated": google_updated,
        "google_error": google_error
    }


@router.post("/events")
async def create_calendar_event(
    event_data: CalendarEventCreate,
    sync_to_google: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new calendar event"""
    
    # Create local event
    calendar_event = CalendarEvent(
        user_id=current_user.id,
        title=event_data.title,
        description=event_data.description,
        start_time=event_data.start_time,
        end_time=event_data.end_time,
        event_type=event_data.event_type
    )
    
    db.add(calendar_event)
    db.commit()
    db.refresh(calendar_event)
    
    # Sync to Google Calendar if requested and connected
    google_result = None
    if sync_to_google and google_calendar_service.is_calendar_connected(current_user.id):
        google_result = google_calendar_service.create_calendar_event(
            current_user.id,
            {
                'title': event_data.title,
                'description': event_data.description,
                'start_time': event_data.start_time,
                'end_time': event_data.end_time
            }
        )
        
        if google_result['success']:
            calendar_event.google_event_id = google_result['event_id']
            calendar_event.is_synced = True
            calendar_event.sync_status = "synced"
            db.commit()
    
    return {
        "success": True,
        "event_id": calendar_event.id,
        "google_synced": google_result['success'] if google_result else False,
        "google_event_url": google_result.get('event_url') if google_result and google_result['success'] else None,
        "message": "Event created successfully"
    }


@router.get("/insights")
async def get_calendar_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI insights about user's calendar patterns"""
    
    insights = google_calendar_service.get_calendar_insights(current_user.id, db)
    
    return {
        "calendar_insights": insights,
        "recommendations": [
            "Consider blocking 2-hour focus sessions for deep work",
            "Schedule breaks between back-to-back meetings",
            "Try time-blocking your most important tasks in the morning"
        ],
        "productivity_tips": [
            "Use calendar colors to categorize different types of work",
            "Set realistic time estimates - add 25% buffer time",
            "Block 'no meeting' times for focused work"
        ]
    }


@router.post("/maintenance/refresh-all-tokens")
async def refresh_all_tokens(
    current_user: User = Depends(get_current_user)
):
    """Manually trigger token refresh for all connected users (admin only for demo)"""
    try:
        from app.tasks.calendar_maintenance import calendar_maintenance
        await calendar_maintenance.refresh_all_tokens()
        return {
            "success": True,
            "message": "Token refresh completed for all connected users"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")

@router.post("/maintenance/health-check")
async def health_check_all_connections(
    current_user: User = Depends(get_current_user)
):
    """Manually trigger health check for all calendar connections"""
    try:
        from app.tasks.calendar_maintenance import calendar_maintenance
        await calendar_maintenance.health_check_connections()
        return {
            "success": True,
            "message": "Health check completed for all calendar connections"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.post("/disconnect")
async def disconnect_google_calendar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually disconnect Google Calendar"""
    try:
        user_id = current_user.id
        
        # Remove token files
        token_file = os.path.join(google_calendar_service.token_dir, f'token_{user_id}.json')
        backup_token_file = os.path.join(google_calendar_service.token_dir, f'token_{user_id}_backup.json')
        
        files_removed = []
        for file_path in [token_file, backup_token_file]:
            if os.path.exists(file_path):
                os.remove(file_path)
                files_removed.append(file_path)
                print(f"🗑️ Removed token file: {file_path}")
        
        # Update database
        current_user.google_calendar_connected = False
        db.commit()
        print(f"📝 Updated database: user {user_id} marked as disconnected")
        
        return {
            "success": True,
            "message": "Google Calendar disconnected successfully",
            "files_removed": len(files_removed),
            "user_id": user_id
        }
        
    except Exception as e:
        print(f"❌ Disconnect error: {e}")
        raise HTTPException(status_code=500, detail=f"Disconnect failed: {str(e)}")

@router.post("/force-reconnect")
async def force_reconnect_google_calendar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Force reconnect Google Calendar - Ultra robust connection establishment"""
    try:
        user_id = current_user.id
        
        # Step 1: Force token refresh if tokens exist
        credentials = google_calendar_service.get_user_credentials(user_id)
        if credentials:
            print(f"🔄 FORCE-RECONNECT: Found existing credentials for user {user_id}")
            # Force database update
            google_calendar_service._force_database_connection_status(user_id, True)
            
            # Test connection
            if google_calendar_service.is_calendar_connected(user_id):
                return {
                    "success": True,
                    "message": "Existing connection restored and verified",
                    "method": "credential_recovery",
                    "user_id": user_id
                }
        
        # Step 2: If no valid credentials, provide new auth URL
        try:
            redirect_uri = "http://127.0.0.1:8001/api/calendar/google/callback"
            auth_url = google_calendar_service.get_auth_url(user_id, redirect_uri)
            
            return {
                "success": False,
                "message": "Re-authentication required",
                "auth_url": auth_url,
                "method": "reauth_required",
                "user_id": user_id
            }
        except Exception as auth_error:
            raise HTTPException(
                status_code=500, 
                detail=f"Could not generate auth URL: {str(auth_error)}"
            )
            
    except Exception as e:
        print(f"❌ Force reconnect error: {e}")
        raise HTTPException(status_code=500, detail=f"Force reconnect failed: {str(e)}")

@router.get("/diagnostics")
async def get_calendar_diagnostics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Comprehensive calendar connection diagnostics"""
    try:
        diagnostics = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": current_user.id,
            "tests": {}
        }
        
        # Test 1: Basic connection check
        try:
            is_connected = google_calendar_service.is_calendar_connected(current_user.id)
            diagnostics["tests"]["basic_connection"] = {
                "status": "pass" if is_connected else "fail",
                "result": is_connected,
                "message": "Connection validated" if is_connected else "No valid connection"
            }
        except Exception as e:
            diagnostics["tests"]["basic_connection"] = {
                "status": "error",
                "error": str(e),
                "message": "Connection test failed"
            }
        
        # Test 2: Token file check
        token_file = os.path.join(google_calendar_service.token_dir, f'token_{current_user.id}.json')
        diagnostics["tests"]["token_file"] = {
            "exists": os.path.exists(token_file),
            "path": token_file,
            "status": "pass" if os.path.exists(token_file) else "fail"
        }
        
        # Test 3: Token details (if file exists)
        if os.path.exists(token_file):
            try:
                import json
                with open(token_file, 'r') as f:
                    token_data = json.load(f)
                    diagnostics["tests"]["token_details"] = {
                        "status": "pass",
                        "has_access_token": bool(token_data.get('token')),
                        "has_refresh_token": bool(token_data.get('refresh_token')),
                        "expires_at": token_data.get('expiry'),
                        "scopes": token_data.get('scopes', [])
                    }
            except Exception as e:
                diagnostics["tests"]["token_details"] = {
                    "status": "error",
                    "error": str(e),
                    "message": "Failed to read token file"
                }
        
        # Test 4: Database status
        try:
            user_status = current_user.google_calendar_connected
            diagnostics["tests"]["database_status"] = {
                "status": "pass",
                "google_calendar_connected": user_status,
                "message": f"Database shows connected: {user_status}"
            }
        except Exception as e:
            diagnostics["tests"]["database_status"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Test 5: Google API test
        try:
            from googleapiclient.discovery import build
            credentials = google_calendar_service.get_user_credentials(current_user.id)
            if credentials:
                service = build('calendar', 'v3', credentials=credentials)
                calendar_list = service.calendarList().list(maxResults=1).execute()
                diagnostics["tests"]["google_api"] = {
                    "status": "pass",
                    "calendars_found": len(calendar_list.get('items', [])),
                    "message": "Google Calendar API responding correctly"
                }
            else:
                diagnostics["tests"]["google_api"] = {
                    "status": "fail",
                    "message": "No valid credentials for API test"
                }
        except Exception as e:
            diagnostics["tests"]["google_api"] = {
                "status": "error",
                "error": str(e),
                "message": "Google API test failed"
            }
        
        # Test 6: Recent events test
        try:
            sync_result = google_calendar_service.sync_calendar_events(current_user.id, db, 7)
            if sync_result.get('success'):
                diagnostics["tests"]["sync_test"] = {
                    "status": "pass",
                    "events_synced": sync_result.get('events_synced', 0),
                    "message": "Calendar sync working"
                }
            else:
                diagnostics["tests"]["sync_test"] = {
                    "status": "fail",
                    "error": sync_result.get('error', 'Unknown error'),
                    "message": "Calendar sync failed"
                }
        except Exception as e:
            diagnostics["tests"]["sync_test"] = {
                "status": "error",
                "error": str(e),
                "message": "Sync test failed"
            }
        
        # Overall status
        failed_tests = [test for test in diagnostics["tests"].values() if test.get("status") == "fail"]
        error_tests = [test for test in diagnostics["tests"].values() if test.get("status") == "error"]
        
        diagnostics["overall"] = {
            "status": "healthy" if not failed_tests and not error_tests else "issues_detected",
            "total_tests": len(diagnostics["tests"]),
            "failed_tests": len(failed_tests),
            "error_tests": len(error_tests),
            "recommendation": "Connection appears healthy" if not failed_tests and not error_tests else "Some issues detected - check test details"
        }
        
        return diagnostics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnostics failed: {str(e)}")

@router.get("/availability")
async def get_availability(
    date: str = None,  # YYYY-MM-DD format
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's availability for a specific date"""
    
    if not date:
        target_date = datetime.utcnow().date()
    else:
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
    
    # Get events for the day
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())
    
    events = db.query(CalendarEvent).filter(
        CalendarEvent.user_id == current_user.id,
        CalendarEvent.start_time >= start_of_day,
        CalendarEvent.start_time <= end_of_day
    ).order_by(CalendarEvent.start_time).all()
    
    # Calculate free time slots (9 AM to 6 PM work hours)
    work_start = datetime.combine(target_date, datetime.min.time().replace(hour=9))
    work_end = datetime.combine(target_date, datetime.min.time().replace(hour=18))
    
    free_slots = []
    current_time = work_start
    
    for event in events:
        if current_time < event.start_time:
            # There's free time before this event
            free_slots.append({
                'start': current_time.strftime('%H:%M'),
                'end': event.start_time.strftime('%H:%M'),
                'duration_minutes': int((event.start_time - current_time).total_seconds() / 60)
            })
        current_time = max(current_time, event.end_time)
    
    # Check for free time after last event
    if current_time < work_end:
        free_slots.append({
            'start': current_time.strftime('%H:%M'),
            'end': work_end.strftime('%H:%M'),
            'duration_minutes': int((work_end - current_time).total_seconds() / 60)
        })
    
    return {
        'date': target_date.isoformat(),
        'total_events': len(events),
        'free_slots': free_slots,
        'longest_free_slot': max(free_slots, key=lambda x: x['duration_minutes']) if free_slots else None,
        'total_free_time': sum(slot['duration_minutes'] for slot in free_slots),
        'recommendations': [
            f"You have {len([s for s in free_slots if s['duration_minutes'] >= 120])} slots of 2+ hours for deep work",
            "Consider scheduling important tasks during your longest free slots"
        ]
    }


@router.get("/test-connection")
async def test_connection():
    """Test calendar connection without authentication - for debugging"""
    try:
        # Test both users
        results = {}
        for user_id in [1, 2]:
            is_connected = google_calendar_service.is_calendar_connected(user_id)
            token_file = os.path.join(google_calendar_service.token_dir, f'token_{user_id}.json')
            results[f"user_{user_id}"] = {
                "connected": is_connected,
                "token_file_exists": os.path.exists(token_file),
                "status": "✅ WORKING" if is_connected else "❌ NOT WORKING"
            }
        
        return {
            "message": "Calendar connection test (no auth required)",
            "timestamp": datetime.utcnow().isoformat(),
            "results": results
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Test failed"
        }