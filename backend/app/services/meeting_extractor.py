import re
import json
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs

class MeetingLinkExtractor:
    """Extract meeting links and information from calendar events"""
    
    def __init__(self):
        # Regex patterns for different meeting platforms
        self.patterns = {
            'zoom': {
                'url': [
                    r'https?://[a-zA-Z0-9.-]*zoom\.us/j/(\d+)',
                    r'https?://[a-zA-Z0-9.-]*zoom\.us/meeting/(\d+)',
                    r'https?://[a-zA-Z0-9.-]*zoom\.us/webinar/(\d+)',
                    r'https?://zoom\.us/j/(\d+)',
                ],
                'id': [
                    r'Meeting ID:?\s*(\d{9,11})',
                    r'ID:?\s*(\d{9,11})',
                    r'Zoom ID:?\s*(\d{9,11})',
                    r'(\d{3})\s*(\d{3})\s*(\d{4})',  # Formatted ID like 123 456 7890
                ],
                'passcode': [
                    r'Passcode:?\s*([A-Za-z0-9]+)',
                    r'Password:?\s*([A-Za-z0-9]+)',
                    r'PWD:?\s*([A-Za-z0-9]+)',
                    r'pwd=([A-Za-z0-9]+)',
                ],
                'phone': [
                    r'One tap mobile:?\s*(\+\d+,\d+)',
                    r'Dial:?\s*(\+\d+)',
                    r'(\+\d{1,3}\s?\d{3}\s?\d{3}\s?\d{4})',
                ]
            },
            'google-meet': {
                'url': [
                    r'https?://meet\.google\.com/[a-z-]+',
                    r'https?://meet\.google\.com/lookup/[a-zA-Z0-9_-]+',
                ],
                'id': [
                    r'meet\.google\.com/([a-z-]+)',
                ],
                'phone': [
                    r'(\+\d{1,3}\s?\d{3}\s?\d{3}\s?\d{4})',
                ]
            },
            'teams': {
                'url': [
                    r'https?://teams\.microsoft\.com/l/meetup-join/[a-zA-Z0-9%_-]+',
                    r'https?://teams\.live\.com/meet/[a-zA-Z0-9]+',
                ],
                'id': [
                    r'Conference ID:?\s*(\d+)',
                    r'Meeting ID:?\s*(\d+)',
                ],
                'phone': [
                    r'(\+\d{1,3}\s?\d{3}\s?\d{3}\s?\d{4})',
                ]
            },
            'webex': {
                'url': [
                    r'https?://[a-zA-Z0-9.-]*webex\.com/[a-zA-Z0-9/._-]*',
                ],
                'id': [
                    r'Meeting number:?\s*(\d+)',
                    r'Access code:?\s*(\d+)',
                ],
                'passcode': [
                    r'Password:?\s*([A-Za-z0-9]+)',
                    r'Meeting password:?\s*([A-Za-z0-9]+)',
                ],
                'phone': [
                    r'(\+\d{1,3}\s?\d{3}\s?\d{3}\s?\d{4})',
                ]
            },
            'gotomeeting': {
                'url': [
                    r'https?://[a-zA-Z0-9.-]*gotomeeting\.com/join/\d+',
                    r'https?://global\.gotomeeting\.com/join/\d+',
                ],
                'id': [
                    r'Meeting ID:?\s*(\d+)',
                    r'gotomeeting\.com/join/(\d+)',
                ]
            }
        }
    
    def extract_meeting_info(self, event_data: Dict) -> Dict[str, Optional[str]]:
        """
        Extract meeting information from a calendar event
        
        Args:
            event_data: Dictionary containing event information with keys like:
                       'description', 'location', 'summary', etc.
        
        Returns:
            Dictionary with meeting information:
            {
                'meeting_url': 'https://zoom.us/j/123456789',
                'meeting_id': '123456789',
                'meeting_passcode': 'abc123',
                'meeting_phone': '+1234567890',
                'meeting_type': 'zoom'
            }
        """
        # Combine all text fields to search
        search_text = ""
        for field in ['description', 'location', 'summary', 'notes']:
            if field in event_data and event_data[field]:
                search_text += f" {event_data[field]}"
        
        # If we have HTML content, try to clean it
        search_text = self._clean_html(search_text)
        
        meeting_info = {
            'meeting_url': None,
            'meeting_id': None,
            'meeting_passcode': None,
            'meeting_phone': None,
            'meeting_type': None
        }
        
        # Try to extract from each platform
        for platform, patterns in self.patterns.items():
            extracted = self._extract_platform_info(search_text, platform, patterns)
            if extracted['meeting_url']:
                meeting_info.update(extracted)
                meeting_info['meeting_type'] = platform
                break
        
        return meeting_info
    
    def _extract_platform_info(self, text: str, platform: str, patterns: Dict) -> Dict:
        """Extract meeting info for a specific platform"""
        info = {
            'meeting_url': None,
            'meeting_id': None,
            'meeting_passcode': None,
            'meeting_phone': None
        }
        
        # Extract URL first (most reliable)
        if 'url' in patterns:
            for pattern in patterns['url']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    info['meeting_url'] = match.group(0)
                    # For Zoom, extract ID from URL if possible
                    if platform == 'zoom' and match.groups():
                        info['meeting_id'] = match.group(1)
                    elif platform == 'google-meet' and match.groups():
                        info['meeting_id'] = match.group(1)
                    break
        
        # Extract meeting ID if not already found
        if not info['meeting_id'] and 'id' in patterns:
            for pattern in patterns['id']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if len(match.groups()) == 3:  # Formatted ID like 123 456 7890
                        info['meeting_id'] = ''.join(match.groups())
                    else:
                        info['meeting_id'] = match.group(1)
                    break
        
        # Extract passcode
        if 'passcode' in patterns:
            for pattern in patterns['passcode']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    info['meeting_passcode'] = match.group(1)
                    break
        
        # Extract phone number
        if 'phone' in patterns:
            for pattern in patterns['phone']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    info['meeting_phone'] = match.group(1)
                    break
        
        return info
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and decode entities"""
        import html
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def is_meeting_event(self, event_data: Dict) -> bool:
        """Check if an event likely contains meeting information"""
        search_text = ""
        for field in ['description', 'location', 'summary']:
            if field in event_data and event_data[field]:
                search_text += f" {event_data[field]}"
        
        search_text = search_text.lower()
        
        # Check for meeting indicators
        meeting_keywords = [
            'zoom', 'meet.google.com', 'teams.microsoft.com', 'webex',
            'gotomeeting', 'meeting id', 'join url', 'conference call',
            'video call', 'dial-in', 'meeting link'
        ]
        
        return any(keyword in search_text for keyword in meeting_keywords)
    
    def generate_join_instructions(self, meeting_info: Dict) -> str:
        """Generate user-friendly join instructions"""
        if not meeting_info['meeting_url']:
            return "No meeting link found"
        
        instructions = []
        meeting_type = meeting_info.get('meeting_type', 'unknown')
        
        if meeting_type == 'zoom':
            instructions.append("🎥 Zoom Meeting")
            if meeting_info['meeting_id']:
                instructions.append(f"Meeting ID: {meeting_info['meeting_id']}")
            if meeting_info['meeting_passcode']:
                instructions.append(f"Passcode: {meeting_info['meeting_passcode']}")
                
        elif meeting_type == 'google-meet':
            instructions.append("📹 Google Meet")
            
        elif meeting_type == 'teams':
            instructions.append("👥 Microsoft Teams")
            
        elif meeting_type == 'webex':
            instructions.append("💼 Webex Meeting")
            if meeting_info['meeting_id']:
                instructions.append(f"Meeting Number: {meeting_info['meeting_id']}")
                
        else:
            instructions.append("🔗 Online Meeting")
        
        if meeting_info['meeting_phone']:
            instructions.append(f"📞 Dial-in: {meeting_info['meeting_phone']}")
        
        return " • ".join(instructions)