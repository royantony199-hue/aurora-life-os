# Google Calendar Integration Setup

To enable Google Calendar integration in Aurora Life OS, you need to set up Google Cloud credentials.

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Enable the Google Calendar API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

## Step 2: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Configure the consent screen if not already done
4. Select "Web application" as application type
5. Add authorized redirect URIs:
   - `http://localhost:8000/api/calendar/google/callback`
   - `http://127.0.0.1:8000/api/calendar/google/callback`
6. Download the JSON credentials file

## Step 3: Setup Backend

1. Rename the downloaded file to `credentials.json`
2. Place it in the backend folder: `/Users/royantony/auroyra life os/backend/credentials.json`
3. Restart the backend server

## Step 4: Test Integration

1. Go to Profile Settings in the web app
2. Click on "Google Calendar Integration"
3. You should see a "Connect" button if credentials are properly configured
4. Click "Connect" to authorize the app with your Google account

## Required Scopes

The app requests these Google Calendar permissions:
- `https://www.googleapis.com/auth/calendar.readonly` - Read calendar events
- `https://www.googleapis.com/auth/calendar.events` - Create and modify events

## Troubleshooting

- **"Credentials file not found"**: Make sure `credentials.json` is in the backend folder
- **"Authorization error"**: Check that redirect URIs match exactly in Google Console
- **"Invalid client"**: Verify the OAuth client is properly configured
- **"Access denied"**: Make sure the Google account has calendar access

## Features Available After Connection

✅ **Automatic Calendar Sync**: Import existing Google Calendar events  
✅ **Two-way Sync**: Events created in Aurora sync to Google Calendar  
✅ **Smart Scheduling**: AI suggests optimal times based on your calendar  
✅ **Conflict Detection**: Avoid double-booking  
✅ **Calendar Insights**: AI analysis of your scheduling patterns  
✅ **Free Time Detection**: Find available slots for focused work  

## Security Notes

- Credentials are stored locally and encrypted
- Refresh tokens allow long-term access
- You can revoke access anytime from your Google Account settings
- Aurora only accesses calendar data, not other Google services