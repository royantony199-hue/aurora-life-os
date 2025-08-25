"""
Celery configuration for Aurora Life OS
Handles background tasks and scheduled automation
"""

from celery import Celery
from celery.schedules import crontab
import os
from app.core.config import settings

# Create Celery instance
celery_app = Celery("aurora_life_os")

# Configure Celery
celery_app.conf.update(
    broker_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    result_backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Configure beat schedule for automated tasks
celery_app.conf.beat_schedule = {
    # Daily calendar optimization at 6 AM UTC
    'daily-calendar-optimization': {
        'task': 'app.tasks.daily_calendar_automation.optimize_daily_calendars',
        'schedule': crontab(hour=6, minute=0),  # 6:00 AM UTC daily
        'args': (),
    },
    
    # Morning schedule generation at 5:30 AM UTC  
    'morning-schedule-generation': {
        'task': 'app.tasks.daily_calendar_automation.generate_morning_schedules',
        'schedule': crontab(hour=5, minute=30),  # 5:30 AM UTC daily
        'args': (),
    },
    
    # Goal-based calendar updates at 7 PM UTC (end of day)
    'evening-goal-calendar-sync': {
        'task': 'app.tasks.daily_calendar_automation.sync_goals_to_calendar',
        'schedule': crontab(hour=19, minute=0),  # 7:00 PM UTC daily
        'args': (),
    },
    
    # Weekly calendar optimization on Sundays at 8 PM UTC
    'weekly-calendar-optimization': {
        'task': 'app.tasks.daily_calendar_automation.optimize_weekly_calendars',
        'schedule': crontab(hour=20, minute=0, day_of_week=0),  # Sunday 8:00 PM UTC
        'args': (),
    },
    
    # Proactive calendar health check every 4 hours
    'calendar-health-check': {
        'task': 'app.tasks.daily_calendar_automation.calendar_health_check',
        'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours
        'args': (),
    },
}

# Task autodiscovery
celery_app.autodiscover_tasks(['app.tasks'])

# Import tasks to ensure they're registered
try:
    from app.tasks import daily_calendar_automation
except ImportError:
    pass