import os
import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.calendar import CalendarEvent, EventType
from app.services.meeting_extractor import MeetingLinkExtractor


class GoogleCalendarService:
    SCOPES = [
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/calendar.events'
    ]
    
    def __init__(self):
        self.credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        self.token_dir = 'tokens'
        os.makedirs(self.token_dir, exist_ok=True)
        self.meeting_extractor = MeetingLinkExtractor()
    
    def get_auth_url(self, user_id: int, redirect_uri: str) -> str:
        """Generate Google OAuth authorization URL"""
        try:
            if not os.path.exists(self.credentials_file):
                raise FileNotFoundError("Google credentials.json file not found. Please add your OAuth 2.0 credentials.")
            
            # Creating OAuth flow for Google Calendar integration
            
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=self.SCOPES,
                redirect_uri=redirect_uri
            )
            
            # Simplify state - just use user_id as string
            flow.state = str(user_id)
            # OAuth state generated for user verification
            
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'  # Force consent to get refresh token
            )
            
            # Authorization URL generated successfully
            
            return auth_url
            
        except Exception as e:
            logger.error(f"Failed to generate OAuth URL: {str(e)}")
            raise Exception(f"Failed to generate auth URL: {str(e)}")
    
    def handle_oauth_callback(self, authorization_code: str, state: str, redirect_uri: str) -> Dict[str, Any]:
        """Handle OAuth callback and store tokens"""
        try:
            # Processing OAuth callback state parameter
            
            # Simplified state parsing - just convert to int
            try:
                user_id = int(state)
                # Successfully parsed user ID from OAuth state
            except (ValueError, TypeError):
                logger.error("Could not parse user ID from OAuth state - invalid state parameter")
                return {
                    'success': False,
                    'error': 'Invalid authentication state',
                    'message': 'OAuth state parameter is invalid or corrupted'
                }
            
            # Create a new flow for token exchange
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=self.SCOPES,
                redirect_uri=redirect_uri
            )
            
            # Processing OAuth authorization code exchange
            
            # Fetch token directly without state validation
            try:
                # Create token exchange request manually
                from google.auth.transport.requests import Request
                import requests
                
                # Load client secrets
                with open(self.credentials_file, 'r') as f:
                    client_config = json.load(f)
                    client_id = client_config['web']['client_id']
                    client_secret = client_config['web']['client_secret']
                
                # Exchange authorization code for tokens
                token_url = 'https://oauth2.googleapis.com/token'
                token_data = {
                    'code': authorization_code,
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'redirect_uri': redirect_uri,
                    'grant_type': 'authorization_code'
                }
                
                response = requests.post(token_url, data=token_data)
                response.raise_for_status()
                
                token_info = response.json()
                logger.info("OAuth token exchange completed successfully")
                
                # Create credentials from token response
                credentials = Credentials(
                    token=token_info['access_token'],
                    refresh_token=token_info.get('refresh_token'),
                    token_uri='https://oauth2.googleapis.com/token',
                    client_id=client_id,
                    client_secret=client_secret,
                    scopes=self.SCOPES
                )
                
                logger.info("Google Calendar credentials created and saved")
                
            except Exception as token_error:
                logger.error(f"OAuth token exchange failed: {str(token_error)}")
                return {
                    'success': False,
                    'error': f'Token exchange failed: {str(token_error)}',
                    'error_type': str(type(token_error))
                }
            
            # Store credentials for the user
            token_file = os.path.join(self.token_dir, f'token_{user_id}.json')
            with open(token_file, 'w') as token:
                token.write(credentials.to_json())
            
            # Test the connection by fetching calendar info
            service = build('calendar', 'v3', credentials=credentials)
            calendar_list = service.calendarList().list().execute()
            
            return {
                'success': True,
                'user_id': user_id,
                'calendars_found': len(calendar_list.get('items', [])),
                'primary_calendar': next((cal for cal in calendar_list.get('items', []) if cal.get('primary')), None)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_credentials(self, user_id: int) -> Optional[Credentials]:
        """Get stored credentials with ULTRA-ROBUST refresh handling - NEVER DISCONNECT"""
        token_file = os.path.join(self.token_dir, f'token_{user_id}.json')
        backup_token_file = os.path.join(self.token_dir, f'token_{user_id}_backup.json')
        
        # Try main token file first
        for attempt_file in [token_file, backup_token_file]:
            if not os.path.exists(attempt_file):
                continue
                
            try:
                credentials = Credentials.from_authorized_user_file(attempt_file, self.SCOPES)
                
                if not credentials:
                    print(f"Failed to load credentials from {attempt_file} for user {user_id}")
                    continue
                
                # ULTRA-AGGRESSIVE refresh strategy - refresh ALWAYS if close to expiry
                needs_refresh = False
                if credentials.expired:
                    needs_refresh = True
                    print(f"🚨 Token expired for user {user_id}")
                elif credentials.expiry:
                    # Refresh if less than 10 minutes remaining (instead of waiting for expiry)
                    from datetime import datetime, timezone, timedelta
                    now = datetime.now(timezone.utc)
                    
                    # Handle timezone-aware/naive datetime comparison
                    expiry_time = credentials.expiry
                    if expiry_time.tzinfo is None:
                        # If expiry is naive, assume it's UTC
                        expiry_time = expiry_time.replace(tzinfo=timezone.utc)
                    elif expiry_time.tzinfo != timezone.utc:
                        # Convert to UTC if it's in a different timezone
                        expiry_time = expiry_time.astimezone(timezone.utc)
                    
                    if expiry_time - now < timedelta(minutes=10):
                        needs_refresh = True
                        print(f"⚠️ Token expires soon for user {user_id}, preemptive refresh")
                
                if needs_refresh and credentials.refresh_token:
                    print(f"🔄 ULTRA-ROBUST: Refreshing token for user {user_id}")
                    try:
                        # Create backup before refresh
                        if os.path.exists(token_file):
                            import shutil
                            shutil.copy2(token_file, backup_token_file)
                            print(f"📋 Created token backup for user {user_id}")
                        
                        # Refresh with retries
                        for retry in range(3):
                            try:
                                credentials.refresh(Request())
                                break
                            except Exception as retry_error:
                                print(f"🔄 Refresh attempt {retry + 1} failed: {retry_error}")
                                if retry == 2:  # Last attempt
                                    raise retry_error
                                import time
                                time.sleep(1)  # Wait before retry
                        
                        # Save refreshed credentials to BOTH files
                        credential_json = credentials.to_json()
                        with open(token_file, 'w') as token:
                            token.write(credential_json)
                        with open(backup_token_file, 'w') as backup:
                            backup.write(credential_json)
                        
                        print(f"✅ ULTRA-ROBUST: Token refreshed and backed up for user {user_id}")
                        
                        # FORCE database update
                        self._force_database_connection_status(user_id, True)
                        
                    except Exception as refresh_error:
                        print(f"❌ ULTRA-ROBUST: Refresh failed for user {user_id}: {refresh_error}")
                        # Don't give up - try backup file if exists
                        if attempt_file != backup_token_file and os.path.exists(backup_token_file):
                            print(f"🔄 ULTRA-ROBUST: Trying backup token for user {user_id}")
                            continue
                        # Only mark as disconnected if ALL attempts fail
                        print(f"🚨 ULTRA-ROBUST: All token recovery attempts failed for user {user_id}")
                        return None
                
                # FINAL VALIDATION: Test actual API connectivity
                if credentials and credentials.valid:
                    try:
                        from googleapiclient.discovery import build
                        service = build('calendar', 'v3', credentials=credentials)
                        # Quick API test
                        service.calendarList().list(maxResults=1).execute()
                        print(f"✅ ULTRA-ROBUST: API connectivity confirmed for user {user_id}")
                        self._force_database_connection_status(user_id, True)
                        return credentials
                    except Exception as api_error:
                        print(f"⚠️ ULTRA-ROBUST: API test failed but credentials valid: {api_error}")
                        # Still return credentials - might be temporary API issue
                        return credentials
                
                return credentials
                
            except Exception as e:
                print(f"❌ ULTRA-ROBUST: Error with {attempt_file} for user {user_id}: {e}")
                continue
        
        print(f"🚨 ULTRA-ROBUST: All credential recovery attempts failed for user {user_id}")
        return None
    
    def _force_database_connection_status(self, user_id: int, connected: bool):
        """FORCE update database connection status with retries"""
        for attempt in range(3):
            try:
                from app.core.database import get_db
                from app.models.user import User
                
                db = next(get_db())
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    user.google_calendar_connected = connected
                    db.commit()
                    print(f"✅ FORCED database update: user {user_id} connected={connected}")
                    return
                else:
                    print(f"⚠️ User {user_id} not found in database")
                    return
            except Exception as e:
                print(f"❌ Database update attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    import time
                    time.sleep(0.5)
    
    def _mark_user_disconnected(self, user_id: int):
        """Mark user as disconnected from Google Calendar in database"""
        try:
            from app.core.database import get_db
            from app.models.user import User
            
            db = next(get_db())
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.google_calendar_connected = False
                db.commit()
                print(f"📝 Marked user {user_id} as calendar disconnected in database")
        except Exception as e:
            print(f"⚠️ Could not update database status for user {user_id}: {e}")
    
    def is_calendar_connected(self, user_id: int) -> bool:
        """Check if user has connected their Google Calendar with robust validation"""
        try:
            credentials = self.get_user_credentials(user_id)
            if not credentials:
                return False
            
            # Additional validation: try a simple API call to confirm working connection
            if credentials.valid:
                try:
                    service = build('calendar', 'v3', credentials=credentials)
                    # Simple test call to verify the connection works
                    calendar_list = service.calendarList().list(maxResults=1).execute()
                    print(f"✅ Google Calendar API test successful for user {user_id}")
                    return True
                except Exception as api_error:
                    print(f"❌ Google Calendar API test failed for user {user_id}: {api_error}")
                    # If API call fails, mark as disconnected
                    self._mark_user_disconnected(user_id)
                    return False
            
            return False
            
        except Exception as e:
            print(f"❌ Error checking calendar connection for user {user_id}: {e}")
            return False
    
    def sync_calendar_events(self, user_id: int, db: Session, days_ahead: int = 30) -> Dict[str, Any]:
        """Sync Google Calendar events with local database"""
        credentials = self.get_user_credentials(user_id)
        if not credentials:
            return {'success': False, 'error': 'Calendar not connected'}
        
        try:
            service = build('calendar', 'v3', credentials=credentials)
            
            # Get events from now to days_ahead in the future
            now = datetime.utcnow()
            time_max = now + timedelta(days=days_ahead)
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                maxResults=100,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            synced_events = []
            
            for event in events:
                # Check if event already exists in our database
                google_event_id = event['id']
                existing_event = db.query(CalendarEvent).filter(
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.google_event_id == google_event_id
                ).first()
                
                # Parse event datetime
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                if 'T' not in start:  # All-day event
                    start_dt = datetime.strptime(start, '%Y-%m-%d')
                    end_dt = datetime.strptime(end, '%Y-%m-%d')
                else:
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                
                # Extract meeting information
                event_data = {
                    'description': event.get('description', ''),
                    'location': event.get('location', ''),
                    'summary': event.get('summary', ''),
                    'notes': event.get('notes', '')
                }
                meeting_info = self.meeting_extractor.extract_meeting_info(event_data)
                
                if existing_event:
                    # Update existing event
                    existing_event.title = event.get('summary', 'Untitled Event')
                    existing_event.description = event.get('description', '')
                    existing_event.start_time = start_dt
                    existing_event.end_time = end_dt
                    existing_event.updated_at = datetime.utcnow()
                    # Update meeting information
                    existing_event.meeting_url = meeting_info.get('meeting_url')
                    existing_event.meeting_id = meeting_info.get('meeting_id')
                    existing_event.meeting_passcode = meeting_info.get('meeting_passcode')
                    existing_event.meeting_phone = meeting_info.get('meeting_phone')
                    existing_event.meeting_type = meeting_info.get('meeting_type')
                    existing_event.google_calendar_data = json.dumps(event)
                else:
                    # Create new event
                    calendar_event = CalendarEvent(
                        user_id=user_id,
                        title=event.get('summary', 'Untitled Event'),
                        description=event.get('description', ''),
                        event_type=self._determine_event_type(event),
                        start_time=start_dt,
                        end_time=end_dt,
                        google_event_id=google_event_id,
                        google_calendar_data=json.dumps(event),
                        # Add meeting information
                        meeting_url=meeting_info.get('meeting_url'),
                        meeting_id=meeting_info.get('meeting_id'),
                        meeting_passcode=meeting_info.get('meeting_passcode'),
                        meeting_phone=meeting_info.get('meeting_phone'),
                        meeting_type=meeting_info.get('meeting_type'),
                        is_synced=True,
                        sync_status="synced"
                    )
                    db.add(calendar_event)
                
                synced_events.append({
                    'title': event.get('summary', 'Untitled Event'),
                    'start': start_dt.isoformat(),
                    'end': end_dt.isoformat()
                })
            
            db.commit()
            
            return {
                'success': True,
                'events_synced': len(synced_events),
                'events': synced_events
            }
            
        except HttpError as error:
            return {'success': False, 'error': f'Google API error: {error}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_calendar_event(self, user_id: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new event in Google Calendar"""
        credentials = self.get_user_credentials(user_id)
        if not credentials:
            return {'success': False, 'error': 'Calendar not connected'}
        
        try:
            service = build('calendar', 'v3', credentials=credentials)
            
            # Format event for Google Calendar API
            google_event = {
                'summary': event_data.get('title', 'Aurora Event'),
                'description': event_data.get('description', ''),
                'start': {
                    'dateTime': event_data['start_time'].isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': event_data['end_time'].isoformat(),
                    'timeZone': 'UTC',
                },
            }
            
            # Add location if provided
            if event_data.get('location'):
                google_event['location'] = event_data['location']
            
            # Create event in Google Calendar
            created_event = service.events().insert(
                calendarId='primary',
                body=google_event
            ).execute()
            
            return {
                'success': True,
                'event_id': created_event['id'],
                'event_url': created_event.get('htmlLink'),
                'message': 'Event created in Google Calendar'
            }
            
        except HttpError as error:
            return {'success': False, 'error': f'Google API error: {error}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_calendar_insights(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get AI insights about user's calendar patterns"""
        try:
            # Get recent events
            recent_events = db.query(CalendarEvent).filter(
                CalendarEvent.user_id == user_id,
                CalendarEvent.start_time >= datetime.utcnow() - timedelta(days=7)
            ).all()
            
            if not recent_events:
                return {
                    'total_events': 0,
                    'insights': ['No recent calendar events found'],
                    'recommendations': ['Try scheduling some planned work sessions']
                }
            
            # Calculate basic insights
            total_events = len(recent_events)
            meeting_events = [e for e in recent_events if 'meeting' in e.title.lower() or 'call' in e.title.lower()]
            work_hours = sum([
                (e.end_time - e.start_time).total_seconds() / 3600 
                for e in recent_events 
                if e.start_time.hour >= 9 and e.start_time.hour <= 17
            ])
            
            insights = [
                f"You have {total_events} events scheduled in the last week",
                f"{len(meeting_events)} appear to be meetings",
                f"Total work hours scheduled: {work_hours:.1f} hours"
            ]
            
            recommendations = []
            if len(meeting_events) > total_events * 0.7:
                recommendations.append("Consider blocking time for deep work between meetings")
            if work_hours > 50:
                recommendations.append("Your schedule looks packed - consider blocking break time")
            if work_hours < 20:
                recommendations.append("You might have time for additional focused work sessions")
            
            return {
                'total_events': total_events,
                'meeting_events': len(meeting_events),
                'work_hours': round(work_hours, 1),
                'insights': insights,
                'recommendations': recommendations
            }
            
        except Exception as e:
            return {
                'total_events': 0,
                'insights': [f'Error analyzing calendar: {str(e)}'],
                'recommendations': []
            }
    
    def _determine_event_type(self, event: Dict[str, Any]) -> EventType:
        """Determine event type based on event data"""
        title = event.get('summary', '').lower()
        
        if any(word in title for word in ['meeting', 'call', 'standup', 'sync', 'interview']):
            return EventType.MEETING
        elif any(word in title for word in ['task', 'work', 'focus', 'deep work', 'coding']):
            return EventType.TASK
        elif any(word in title for word in ['break', 'lunch', 'rest', 'coffee']):
            return EventType.BREAK
        elif any(word in title for word in ['personal', 'doctor', 'appointment', 'family']):
            return EventType.PERSONAL
        else:
            return EventType.MEETING  # Default to meeting