# Aurora Life OS - Daily Calendar Automation

## 🎯 Overview

The Daily Calendar Automation system provides **intelligent, goal-driven calendar management** that runs automatically in the background. It creates, optimizes, and manages your calendar based on your goals, energy patterns, and productivity needs.

## ✨ Features

### Automated Daily Tasks
- **6:00 AM UTC**: Daily calendar optimization and gap filling
- **5:30 AM UTC**: Morning schedule generation with AI insights  
- **7:00 PM UTC**: Evening goal-to-calendar synchronization
- **Sunday 8:00 PM UTC**: Weekly calendar optimization
- **Every 4 hours**: Calendar health monitoring

### Smart Calendar Management
- **Goal-Based Scheduling**: Automatically schedules time blocks for active goals
- **Energy Pattern Matching**: Aligns tasks with your optimal energy levels
- **Gap Filling**: Finds empty calendar slots and fills with productive activities
- **Conflict Resolution**: Detects and resolves scheduling conflicts
- **Proactive Optimization**: Continuously improves your schedule based on patterns

## 🚀 Quick Start

### 1. Prerequisites
```bash
# Install Redis (required for background tasks)
brew install redis
brew services start redis

# Install Python dependencies
cd backend/
pip install -r requirements.txt
```

### 2. Environment Setup
```bash
# Copy and configure environment variables
cp .env.example .env

# Edit .env with your settings:
# - REDIS_URL=redis://localhost:6379/0
# - OPENAI_API_KEY=your_openai_api_key
# - DATABASE_URL=your_database_url
```

### 3. Test the System
```bash
# Run comprehensive tests
python test_scheduler.py
```

### 4. Start the Automation
```bash
# Option 1: Integrated server (recommended)
python start_server.py

# Option 2: Scheduler only
python start_scheduler.py
```

## 📋 Scheduled Tasks

### Daily Calendar Optimization
**When**: 6:00 AM UTC daily  
**What**: 
- Generates hourly schedules for the day
- Fills calendar gaps with goal work sessions
- Optimizes existing events based on energy patterns
- Creates focused work blocks (30min-2hr sessions)

### Morning Schedule Generation  
**When**: 5:30 AM UTC daily  
**What**:
- Creates comprehensive daily schedules
- Schedules morning briefings
- Optimizes task sequencing for productivity

### Evening Goal Sync
**When**: 7:00 PM UTC daily  
**What**:
- Reviews goal progress vs. calendar allocation
- Schedules additional time for under-allocated goals
- Plans tomorrow's goal work sessions
- Adjusts schedules based on daily progress

### Weekly Optimization
**When**: Sunday 8:00 PM UTC  
**What**:
- Optimizes entire week's calendar
- Balances goal work across the week
- Identifies and resolves weekly patterns

### Health Monitoring
**When**: Every 4 hours  
**What**:
- Checks calendar system health
- Ensures users have daily schedules
- Auto-fixes missing events
- Monitors automation performance

## 🔧 API Endpoints

### Scheduler Control
```bash
# Check scheduler status
GET /api/scheduler/status

# Manually trigger daily optimization
POST /api/scheduler/trigger-daily-optimization

# Bulk schedule from goals
POST /api/ai-calendar/bulk-schedule-from-goals
```

### Manual Calendar Operations
```bash
# Create smart event
POST /api/ai-calendar/smart-create

# Generate hourly schedule
POST /api/ai-calendar/generate-hourly-schedule

# Optimize weekly calendar
POST /api/ai-calendar/optimize-weekly

# Get productivity insights
GET /api/ai-calendar/productivity-insights
```

## 🧠 Intelligence Features

### Goal-to-Calendar Integration
- **Automatic Time Allocation**: Calculates required time based on goal progress and deadlines
- **Smart Session Distribution**: Spreads goal work optimally across the week
- **Progress-Based Adjustments**: Increases time allocation for behind-schedule goals

### Energy Pattern Optimization
- **Mood Integration**: Uses mood tracking data to determine optimal work times
- **Energy Level Matching**: Schedules high-energy tasks during peak times
- **Burnout Prevention**: Detects overloading and suggests breaks

### AI-Powered Insights
- **Productivity Analysis**: Tracks completion rates and optimizes future scheduling
- **Pattern Recognition**: Learns from your behavior to improve scheduling
- **Contextual Recommendations**: Suggests schedule improvements based on performance

## 📊 Monitoring

### Task Status
```bash
# View active Celery workers
celery -A app.core.celery_app status

# Monitor task execution
celery -A app.core.celery_app events

# View scheduled tasks
celery -A app.core.celery_app inspect scheduled
```

### Logs
- **Application logs**: `backend/backend.log`
- **Celery logs**: Console output from worker/beat processes
- **Task results**: Stored in Redis and accessible via API

## 🛠 Troubleshooting

### Common Issues

**Redis Connection Failed**
```bash
brew services restart redis
# or
redis-server
```

**Celery Tasks Not Running**
```bash
# Check worker status
celery -A app.core.celery_app inspect active

# Restart worker
python start_scheduler.py
```

**OpenAI API Errors**
- Verify `OPENAI_API_KEY` in `.env`
- Check API quota and billing
- Review error logs for specific issues

**Database Connection Issues** 
- Verify `DATABASE_URL` in `.env`
- Run database migrations: `alembic upgrade head`
- Check database service status

### Debug Mode
```bash
# Run with verbose logging
LOG_LEVEL=debug python start_server.py

# Test individual tasks
python -c "from app.tasks.daily_calendar_automation import calendar_health_check; print(calendar_health_check())"
```

## 🔒 Security

### Best Practices
- Never commit `.env` files with real credentials
- Use environment variables for all secrets
- Regularly rotate API keys
- Monitor task execution for anomalies

### Production Deployment
- Use separate Redis instances for production
- Configure proper logging and monitoring
- Set up health checks and alerting
- Use container orchestration for scalability

## 📈 Performance

### Optimizations
- **Task Concurrency**: Configurable worker pool size
- **Rate Limiting**: Respects OpenAI API limits
- **Caching**: Redis-based result caching
- **Batch Processing**: Processes multiple users efficiently

### Monitoring Metrics
- Task execution time
- Success/failure rates  
- User satisfaction scores
- Calendar optimization effectiveness

## 🎉 Success!

Your Aurora Life OS now has **intelligent daily calendar automation** that:

✅ **Automatically schedules goal work** based on progress and deadlines  
✅ **Optimizes your calendar** using AI and energy patterns  
✅ **Fills gaps productively** with meaningful activities  
✅ **Adapts continuously** based on your behavior and preferences  
✅ **Runs in the background** without manual intervention  

The system is now **fully automated** and will manage your calendar intelligently 24/7!