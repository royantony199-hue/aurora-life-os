#!/usr/bin/env python3
"""
Proactive AI Messaging Service
Implements smart triggers and pattern analysis for context-aware AI outreach
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from ..models.user import User
from ..models.goal import Goal, GoalStatus
from ..models.mood import MoodEntry
from ..models.calendar import CalendarEvent
from ..models.chat import ChatMessage, MessageRole, MessageType
from ..models.proactive_message_log import ProactiveMessageLog, UserProactivePreferences
from ..core.database import get_db
from .openai_service import OpenAIService


class ProactiveAIService:
    """
    Service that analyzes user patterns and triggers proactive AI messages
    Based on mood gaps, goal deadlines, energy patterns, and calendar context
    """
    
    def __init__(self):
        self.openai_service = OpenAIService()
        
    async def analyze_and_trigger_proactive_messages(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """
        Main entry point for proactive AI analysis
        Returns list of triggered messages to send
        """
        # Validate user_id
        if user_id <= 0:
            return []
            
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        # Check user preferences
        preferences = self._get_user_preferences(user_id, db)
        if not preferences.enabled:
            return []
        
        # Check if we're in quiet hours
        if self._is_quiet_hours(preferences):
            return []
        
        # Check daily rate limit
        if self._check_daily_rate_limit(user_id, preferences.max_messages_per_day, db):
            return []
        
        triggers = []
        
        # Check all trigger conditions
        mood_triggers = await self._check_mood_triggers(user_id, db)
        goal_triggers = await self._check_goal_triggers(user_id, db)
        energy_triggers = await self._check_energy_triggers(user_id, db)
        calendar_triggers = await self._check_calendar_triggers(user_id, db)
        pattern_triggers = await self._check_pattern_triggers(user_id, db)
        
        triggers.extend(mood_triggers)
        triggers.extend(goal_triggers)
        triggers.extend(energy_triggers)
        triggers.extend(calendar_triggers)
        triggers.extend(pattern_triggers)
        
        # Process and prioritize triggers
        processed_triggers = await self._process_triggers(triggers, user_id, db)
        
        return processed_triggers
    
    async def _check_mood_triggers(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Check for mood-based triggers"""
        triggers = []
        now = datetime.now()
        
        # Get recent mood entries (last 7 days)
        recent_moods = db.query(MoodEntry).filter(
            and_(
                MoodEntry.user_id == user_id,
                MoodEntry.created_at >= now - timedelta(days=7)
            )
        ).order_by(desc(MoodEntry.created_at)).all()
        
        if not recent_moods:
            # No mood entries - encourage first check-in
            triggers.append({
                "type": "mood_gap",
                "priority": "medium",
                "trigger": "no_mood_data",
                "context": "User hasn't logged any mood data",
                "suggested_action": "encourage_mood_checkin"
            })
            return triggers
        
        latest_mood = recent_moods[0]
        time_since_last = now - latest_mood.created_at
        
        # Check for mood gap (no entry in 24+ hours)
        if time_since_last.total_seconds() > 86400:  # 24 hours
            triggers.append({
                "type": "mood_gap",
                "priority": "medium",
                "trigger": "missing_checkin",
                "context": f"Last mood check-in was {time_since_last.days} days ago",
                "suggested_action": "encourage_mood_checkin"
            })
        
        # Check for consecutive low moods
        if len(recent_moods) >= 3:
            recent_scores = [mood.mood_level for mood in recent_moods[:3]]
            if all(score <= 4 for score in recent_scores):
                triggers.append({
                    "type": "mood_pattern",
                    "priority": "high",
                    "trigger": "consecutive_low_moods",
                    "context": f"Last 3 mood scores: {recent_scores}",
                    "suggested_action": "offer_support_and_strategies"
                })
        
        # Check for mood volatility
        if len(recent_moods) >= 5:
            recent_scores = [mood.mood_level for mood in recent_moods[:5]]
            volatility = max(recent_scores) - min(recent_scores)
            if volatility >= 6:  # High volatility
                triggers.append({
                    "type": "mood_pattern",
                    "priority": "medium",
                    "trigger": "mood_volatility",
                    "context": f"Mood range: {min(recent_scores)}-{max(recent_scores)}",
                    "suggested_action": "discuss_mood_stability"
                })
        
        return triggers
    
    async def _check_goal_triggers(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Check for goal-based triggers"""
        triggers = []
        now = datetime.now()
        
        # Get active goals
        active_goals = db.query(Goal).filter(
            and_(
                Goal.user_id == user_id,
                Goal.status == GoalStatus.ACTIVE
            )
        ).all()
        
        for goal in active_goals:
            # Check for approaching deadlines
            if goal.target_date:
                days_until_deadline = (goal.target_date.date() - now.date()).days
                
                # Handle overdue goals differently
                if days_until_deadline < 0:
                    overdue_days = abs(days_until_deadline)
                    triggers.append({
                        "type": "goal_deadline",
                        "priority": "high",
                        "trigger": "overdue_goal",
                        "context": f"Goal '{goal.title}' is {overdue_days} days overdue, {goal.progress}% complete",
                        "goal_id": goal.id,
                        "suggested_action": "overdue_goal_recovery"
                    })
                elif days_until_deadline <= 3 and goal.progress < 80:
                    triggers.append({
                        "type": "goal_deadline",
                        "priority": "high",
                        "trigger": "approaching_deadline",
                        "context": f"Goal '{goal.title}' due in {days_until_deadline} days, {goal.progress}% complete",
                        "goal_id": goal.id,
                        "suggested_action": "urgent_goal_support"
                    })
                elif days_until_deadline <= 7 and goal.progress < 50:
                    triggers.append({
                        "type": "goal_deadline",
                        "priority": "medium",
                        "trigger": "deadline_warning",
                        "context": f"Goal '{goal.title}' due in {days_until_deadline} days, {goal.progress}% complete",
                        "goal_id": goal.id,
                        "suggested_action": "goal_progress_check"
                    })
            
            # Check for stagnant progress
            goal_age_days = (now.date() - goal.created_at.date()).days
            if goal_age_days >= 7 and goal.progress < 10:
                triggers.append({
                    "type": "goal_stagnation",
                    "priority": "medium",
                    "trigger": "no_progress",
                    "context": f"Goal '{goal.title}' created {goal_age_days} days ago with {goal.progress}% progress",
                    "goal_id": goal.id,
                    "suggested_action": "goal_activation_help"
                })
        
        # Check for goal completion celebration
        recently_completed = db.query(Goal).filter(
            and_(
                Goal.user_id == user_id,
                Goal.status == GoalStatus.COMPLETED,
                Goal.updated_at >= now - timedelta(days=1)
            )
        ).all()
        
        for completed_goal in recently_completed:
            triggers.append({
                "type": "goal_celebration",
                "priority": "medium",
                "trigger": "goal_completed",
                "context": f"Goal '{completed_goal.title}' was completed!",
                "goal_id": completed_goal.id,
                "suggested_action": "celebrate_and_next_steps"
            })
        
        return triggers
    
    async def _check_energy_triggers(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Check for energy-based triggers"""
        triggers = []
        now = datetime.now()
        
        # Get recent mood entries with energy data
        recent_entries = db.query(MoodEntry).filter(
            and_(
                MoodEntry.user_id == user_id,
                MoodEntry.created_at >= now - timedelta(days=3)
            )
        ).order_by(desc(MoodEntry.created_at)).limit(5).all()
        
        if len(recent_entries) >= 3:
            energy_levels = [entry.energy_level for entry in recent_entries if entry.energy_level]
            
            if energy_levels:
                avg_energy = sum(energy_levels) / len(energy_levels)
                
                # Check for consistently low energy
                if avg_energy <= 3:
                    triggers.append({
                        "type": "energy_pattern",
                        "priority": "medium",
                        "trigger": "low_energy_pattern",
                        "context": f"Average energy level: {avg_energy:.1f}/10 over last {len(energy_levels)} entries",
                        "suggested_action": "energy_boost_suggestions"
                    })
                
                # Check for energy crash after high energy
                if len(energy_levels) >= 2:
                    if energy_levels[1] >= 8 and energy_levels[0] <= 3:
                        triggers.append({
                            "type": "energy_pattern",
                            "priority": "medium",
                            "trigger": "energy_crash",
                            "context": f"Energy dropped from {energy_levels[1]} to {energy_levels[0]}",
                            "suggested_action": "energy_management_tips"
                        })
        
        return triggers
    
    async def _check_calendar_triggers(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Check for calendar-based triggers"""
        triggers = []
        now = datetime.now()
        
        # Check for busy periods
        upcoming_events = db.query(CalendarEvent).filter(
            and_(
                CalendarEvent.user_id == user_id,
                CalendarEvent.start_time >= now,
                CalendarEvent.start_time <= now + timedelta(days=1)
            )
        ).order_by(CalendarEvent.start_time).all()
        
        if len(upcoming_events) >= 5:
            triggers.append({
                "type": "calendar_pattern",
                "priority": "medium",
                "trigger": "busy_day_ahead",
                "context": f"{len(upcoming_events)} events in next 24 hours",
                "suggested_action": "busy_day_preparation"
            })
        
        # Check for empty calendar (potential low productivity)
        if len(upcoming_events) == 0:
            yesterday_events = db.query(CalendarEvent).filter(
                and_(
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.start_time >= now - timedelta(days=1),
                    CalendarEvent.start_time < now
                )
            ).count()
            
            if yesterday_events == 0:
                triggers.append({
                    "type": "calendar_pattern",
                    "priority": "low",
                    "trigger": "empty_calendar",
                    "context": "No events yesterday or today",
                    "suggested_action": "productivity_encouragement"
                })
        
        return triggers
    
    async def _check_pattern_triggers(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Check for behavioral pattern triggers"""
        triggers = []
        now = datetime.now()
        
        # Check chat engagement patterns
        recent_messages = db.query(ChatMessage).filter(
            and_(
                ChatMessage.user_id == user_id,
                ChatMessage.created_at >= now - timedelta(days=3)
            )
        ).order_by(desc(ChatMessage.created_at)).all()
        
        if not recent_messages:
            triggers.append({
                "type": "engagement_pattern",
                "priority": "low",
                "trigger": "no_recent_chat",
                "context": "No chat messages in last 3 days",
                "suggested_action": "gentle_check_in"
            })
        
        # Check for time of day patterns
        current_hour = now.hour
        
        # Morning motivation (7-9 AM)
        if 7 <= current_hour <= 9:
            today_mood = db.query(MoodEntry).filter(
                and_(
                    MoodEntry.user_id == user_id,
                    func.date(MoodEntry.created_at) == now.date()
                )
            ).first()
            
            if not today_mood:
                triggers.append({
                    "type": "time_pattern",
                    "priority": "low",
                    "trigger": "morning_checkin",
                    "context": f"Good morning! Time for daily check-in",
                    "suggested_action": "morning_motivation"
                })
        
        # Evening reflection (7-9 PM)
        elif 19 <= current_hour <= 21:
            today_goals_activity = db.query(Goal).filter(
                and_(
                    Goal.user_id == user_id,
                    Goal.updated_at >= now.replace(hour=0, minute=0, second=0)
                )
            ).count()
            
            if today_goals_activity == 0:
                triggers.append({
                    "type": "time_pattern",
                    "priority": "low",
                    "trigger": "evening_reflection",
                    "context": "Evening time - good for reflection",
                    "suggested_action": "evening_reflection"
                })
        
        return triggers
    
    async def _process_triggers(self, triggers: List[Dict[str, Any]], user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Process and prioritize triggers, generate AI messages"""
        if not triggers:
            return []
        
        # Filter out triggers that are on cooldown
        valid_triggers = []
        for trigger in triggers:
            if not self._is_trigger_on_cooldown(user_id, trigger["type"], db):
                valid_triggers.append(trigger)
        
        if not valid_triggers:
            return []
        
        # Sort by priority
        priority_order = {"high": 3, "medium": 2, "low": 1}
        valid_triggers.sort(key=lambda x: priority_order.get(x["priority"], 0), reverse=True)
        
        # Get user preferences for daily limit
        preferences = self._get_user_preferences(user_id, db)
        messages_today = self._get_messages_sent_today(user_id, db)
        remaining_quota = preferences.max_messages_per_day - messages_today
        
        # Limit to remaining daily quota
        top_triggers = valid_triggers[:max(0, remaining_quota)]
        
        processed_messages = []
        
        for trigger in top_triggers:
            # Generate personalized AI message for each trigger
            ai_message = await self._generate_proactive_message(trigger, user_id, db)
            
            if ai_message:
                processed_messages.append({
                    "trigger_type": trigger["type"],
                    "priority": trigger["priority"],
                    "message": ai_message,
                    "context": trigger["context"],
                    "suggested_action": trigger["suggested_action"],
                    "goal_id": trigger.get("goal_id"),
                    "timestamp": datetime.now().isoformat()
                })
        
        return processed_messages
    
    async def _generate_proactive_message(self, trigger: Dict[str, Any], user_id: int, db: Session) -> Optional[str]:
        """Generate personalized AI message based on trigger"""
        try:
            # Get user context
            user = db.query(User).filter(User.id == user_id).first()
            recent_mood = db.query(MoodEntry).filter(MoodEntry.user_id == user_id).order_by(desc(MoodEntry.created_at)).first()
            active_goals = db.query(Goal).filter(
                and_(Goal.user_id == user_id, Goal.status == GoalStatus.ACTIVE)
            ).all()
            
            # Build context for AI
            context = {
                "trigger_type": trigger["type"],
                "trigger_context": trigger["context"],
                "suggested_action": trigger["suggested_action"],
                "user_name": user.full_name or "there",
                "recent_mood": recent_mood.mood_level if recent_mood else 5,
                "recent_energy": recent_mood.energy_level if recent_mood else 5,
                "active_goals_count": len(active_goals),
                "active_goals": [{"title": g.title, "progress": g.progress} for g in active_goals[:3]]
            }
            
            # Generate appropriate message based on trigger type
            prompt = self._build_proactive_prompt(trigger, context)
            
            response = await self.openai_service.get_emotional_response(
                user_message=prompt,
                user_mood=context.get("recent_mood", 5),
                user_energy=context.get("recent_energy", 5),
                user_context={"goals": {"goals_count": len(active_goals), "active_goals": [{"title": g.title, "category": g.category.value, "progress": g.progress, "target_date": g.target_date.isoformat() if g.target_date else None} for g in active_goals]}}
            )
            
            return response
            
        except Exception as e:
            print(f"Error generating proactive message: {e}")
            return None
    
    def _build_proactive_prompt(self, trigger: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Build AI prompt based on trigger type"""
        base_prompt = """You are Aurora, a proactive AI life coach. You're reaching out to the user based on a pattern you've noticed. 

IMPORTANT: This is a PROACTIVE message - you are initiating contact, not responding to user input.

Be warm, supportive, and natural. Keep it conversational and brief (2-3 sentences max).
Don't be pushy or overwhelming. Focus on being helpful and caring.

"""
        
        trigger_prompts = {
            "mood_gap": f"""
You noticed the user hasn't checked in with their mood recently.
Context: {trigger['context']}

Gently encourage them to share how they're feeling. Be caring but not invasive.
""",
            
            "mood_pattern": f"""
You've noticed a pattern in the user's mood that might need attention.
Context: {trigger['context']}

Offer support and acknowledge what they might be going through. Be empathetic.
""",
            
            "goal_deadline": f"""
One of the user's goals has an approaching deadline.
Context: {trigger['context']}

Offer encouragement and practical help. Focus on what they can do next.
""",
            
            "goal_stagnation": f"""
A goal hasn't seen progress in a while.
Context: {trigger['context']}

Gently check in about this goal. Offer to help break it down or adjust it.
""",
            
            "goal_celebration": f"""
The user recently completed a goal!
Context: {trigger['context']}

Celebrate their achievement and help them think about next steps.
""",
            
            "energy_pattern": f"""
You've noticed a pattern in the user's energy levels.
Context: {trigger['context']}

Offer relevant suggestions for energy management. Be supportive.
""",
            
            "calendar_pattern": f"""
You noticed something about their upcoming schedule.
Context: {trigger['context']}

Offer helpful suggestions for managing their time or productivity.
""",
            
            "engagement_pattern": f"""
You haven't heard from the user in a while.
Context: {trigger['context']}

Reach out with a friendly, casual check-in. Don't be needy.
""",
            
            "time_pattern": f"""
It's a good time for a specific type of check-in.
Context: {trigger['context']}

Offer appropriate support for this time of day.
"""
        }
        
        # Add overdue goal prompt if not present
        if trigger["type"] == "overdue_goal" and "overdue_goal" not in trigger_prompts:
            trigger_prompts["overdue_goal"] = f"""
One of the user's goals is overdue but still active.
Context: {trigger['context']}

Be supportive, not critical. Help them either reset the timeline or break it down into smaller steps to restart.
"""
        
        specific_prompt = trigger_prompts.get(trigger["type"], "Reach out with a supportive message.")
        
        return base_prompt + specific_prompt + f"""

User context:
- Name: {context['user_name']}
- Recent mood: {context['recent_mood']}/10 (if available)
- Active goals: {context['active_goals_count']}

Generate a natural, caring proactive message."""
    
    def _get_user_preferences(self, user_id: int, db: Session) -> UserProactivePreferences:
        """Get or create user preferences"""
        preferences = db.query(UserProactivePreferences).filter(
            UserProactivePreferences.user_id == user_id
        ).first()
        
        if not preferences:
            # Create default preferences
            preferences = UserProactivePreferences(
                user_id=user_id,
                enabled=True,
                max_messages_per_day=2,
                quiet_hours_start=22,
                quiet_hours_end=7
            )
            db.add(preferences)
            db.commit()
        
        return preferences
    
    def _is_quiet_hours(self, preferences: UserProactivePreferences) -> bool:
        """Check if current time is within user's quiet hours"""
        now = datetime.now()
        current_hour = now.hour
        
        # Handle overnight quiet hours (e.g., 22:00 to 07:00)
        if preferences.quiet_hours_start > preferences.quiet_hours_end:
            return current_hour >= preferences.quiet_hours_start or current_hour < preferences.quiet_hours_end
        else:
            return preferences.quiet_hours_start <= current_hour < preferences.quiet_hours_end
    
    def _check_daily_rate_limit(self, user_id: int, max_messages: int, db: Session) -> bool:
        """Check if user has hit daily rate limit. Returns True if limit exceeded."""
        messages_today = self._get_messages_sent_today(user_id, db)
        return messages_today >= max_messages
    
    def _get_messages_sent_today(self, user_id: int, db: Session) -> int:
        """Count proactive messages sent today"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        count = db.query(ProactiveMessageLog).filter(
            ProactiveMessageLog.user_id == user_id,
            ProactiveMessageLog.sent_at >= today_start
        ).count()
        
        return count
    
    def _is_trigger_on_cooldown(self, user_id: int, trigger_type: str, db: Session) -> bool:
        """Check if a trigger type is on cooldown for a user"""
        now = datetime.now()
        
        # Check if there's a recent message of this type
        recent_log = db.query(ProactiveMessageLog).filter(
            ProactiveMessageLog.user_id == user_id,
            ProactiveMessageLog.trigger_type == trigger_type,
            ProactiveMessageLog.cooldown_expires_at > now
        ).first()
        
        return recent_log is not None
    
    def _log_proactive_message(self, user_id: int, trigger_type: str, message_id: int, db: Session):
        """Log a sent proactive message with 24-hour cooldown"""
        cooldown_duration = timedelta(hours=24)
        
        log_entry = ProactiveMessageLog(
            user_id=user_id,
            trigger_type=trigger_type,
            message_id=message_id,
            sent_at=datetime.now(),
            cooldown_expires_at=datetime.now() + cooldown_duration
        )
        
        db.add(log_entry)
        db.commit()
    
    def mark_message_as_read(self, user_id: int, message_id: int, db: Session) -> bool:
        """Mark a proactive message as read"""
        log_entry = db.query(ProactiveMessageLog).filter(
            ProactiveMessageLog.user_id == user_id,
            ProactiveMessageLog.message_id == message_id,
            ProactiveMessageLog.is_read == False
        ).first()
        
        if log_entry:
            log_entry.is_read = True
            log_entry.read_at = datetime.now()
            db.commit()
            return True
        
        return False


# Background task scheduler
class ProactiveMessagingScheduler:
    """Handles scheduling and execution of proactive message analysis"""
    
    def __init__(self):
        self.proactive_service = ProactiveAIService()
        self.is_running = False
    
    async def start_monitoring(self, check_interval_minutes: int = 30):
        """Start background monitoring for proactive triggers"""
        self.is_running = True
        
        while self.is_running:
            try:
                # Get all active users (in a real app, this would be more sophisticated)
                db = next(get_db())
                users = db.query(User).all()
                
                for user in users:
                    await self.check_user_triggers(user.id, db)
                
                db.close()
                
                # Wait before next check
                await asyncio.sleep(check_interval_minutes * 60)
                
            except Exception as e:
                print(f"Error in proactive messaging scheduler: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def check_user_triggers(self, user_id: int, db: Session):
        """Check triggers for a specific user"""
        try:
            messages = await self.proactive_service.analyze_and_trigger_proactive_messages(user_id, db)
            
            if messages:
                # Store proactive messages as chat messages
                for msg_data in messages:
                    chat_message = ChatMessage(
                        user_id=user_id,
                        role=MessageRole.ASSISTANT,
                        message_type=MessageType.PROACTIVE,
                        content=msg_data["message"],
                        is_proactive=True,
                        trigger_type=msg_data["trigger_type"],
                        trigger_context={"context": msg_data["context"], "suggested_action": msg_data["suggested_action"]},
                        created_at=datetime.now()
                    )
                    db.add(chat_message)
                    db.flush()  # Get the ID before commit
                    
                    # Log the message to prevent duplicates
                    self.proactive_service._log_proactive_message(
                        user_id=user_id,
                        trigger_type=msg_data["trigger_type"],
                        message_id=chat_message.id,
                        db=db
                    )
                
                db.commit()
                print(f"Sent {len(messages)} proactive messages to user {user_id}")
        
        except Exception as e:
            print(f"Error checking triggers for user {user_id}: {e}")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.is_running = False