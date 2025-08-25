from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta, date

from app.core.database import get_db
from app.models import MoodEntry, User
from app.services.openai_service import OpenAIService
from app.routers.auth import get_current_user

router = APIRouter()
openai_service = OpenAIService()


class MoodCheckIn(BaseModel):
    mood_level: int  # 1-10 scale
    energy_level: int  # 1-10 scale
    mood_emoji: Optional[str] = None
    stress_level: Optional[int] = None
    notes: Optional[str] = None
    location: Optional[str] = None
    triggers: Optional[str] = None


class MoodAnalytics(BaseModel):
    avg_mood_7_days: float
    avg_energy_7_days: float
    avg_mood_30_days: float
    avg_energy_30_days: float
    mood_trend: str  # "improving", "declining", "stable"
    burnout_risk: str  # "low", "medium", "high"
    best_mood_time: Optional[str] = None
    worst_mood_time: Optional[str] = None


class MoodHistoryItem(BaseModel):
    id: int
    mood_level: int
    energy_level: int
    mood_emoji: Optional[str]
    stress_level: Optional[int]
    notes: Optional[str]
    created_at: datetime
    is_burnout_risk: bool


@router.post("/checkin")
async def mood_checkin(
    checkin: MoodCheckIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Daily mood check-in with 1-10 scale + emoji"""
    
    # Check if user already checked in today
    today = date.today()
    existing_checkin = db.query(MoodEntry).filter(
        MoodEntry.user_id == current_user.id,
        func.date(MoodEntry.created_at) == today
    ).first()
    
    if existing_checkin:
        # Update existing checkin
        existing_checkin.mood_level = checkin.mood_level
        existing_checkin.energy_level = checkin.energy_level
        existing_checkin.mood_emoji = checkin.mood_emoji
        existing_checkin.stress_level = checkin.stress_level
        existing_checkin.notes = checkin.notes
        existing_checkin.location = checkin.location
        existing_checkin.triggers = checkin.triggers
        mood_entry = existing_checkin
    else:
        # Create new checkin
        mood_entry = MoodEntry(
            user_id=current_user.id,
            mood_level=checkin.mood_level,
            energy_level=checkin.energy_level,
            mood_emoji=checkin.mood_emoji,
            stress_level=checkin.stress_level,
            notes=checkin.notes,
            location=checkin.location,
            triggers=checkin.triggers
        )
        db.add(mood_entry)
    
    # Check for burnout risk
    recent_entries = db.query(MoodEntry).filter(
        MoodEntry.user_id == current_user.id
    ).order_by(desc(MoodEntry.created_at)).limit(7).all()
    
    # Simple burnout detection
    is_burnout_risk = (
        checkin.mood_level <= 4 or 
        checkin.energy_level <= 3 or
        (checkin.stress_level and checkin.stress_level >= 8)
    )
    
    mood_entry.is_burnout_risk = is_burnout_risk
    
    # Get AI intervention suggestions if needed
    intervention_response = None
    if is_burnout_risk:
        try:
            intervention_analysis = await openai_service.detect_burnout_and_suggest_interventions(
                recent_mood_entries=recent_entries,
                user=current_user
            )
            intervention_response = intervention_analysis
            mood_entry.intervention_suggested = True
        except Exception as e:
            intervention_response = {
                "burnout_risk": "medium",
                "interventions": [
                    {"type": "immediate", "action": "Take a few deep breaths and drink some water"},
                    {"type": "today", "action": "Consider taking short breaks every hour"},
                    {"type": "this_week", "action": "Review your workload and priorities"}
                ]
            }
    
    db.commit()
    
    return {
        "status": "success",
        "mood_entry_id": mood_entry.id,
        "burnout_risk_detected": is_burnout_risk,
        "intervention_suggestions": intervention_response,
        "message": get_mood_response_message(checkin.mood_level, checkin.energy_level)
    }


@router.get("/today")
async def get_todays_mood(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get today's mood check-in"""
    today = date.today()
    mood_entry = db.query(MoodEntry).filter(
        MoodEntry.user_id == current_user.id,
        func.date(MoodEntry.created_at) == today
    ).first()
    
    if not mood_entry:
        return {"checked_in": False, "message": "No mood check-in for today"}
    
    return {
        "checked_in": True,
        "mood_entry": {
            "mood_level": mood_entry.mood_level,
            "energy_level": mood_entry.energy_level,
            "mood_emoji": mood_entry.mood_emoji,
            "stress_level": mood_entry.stress_level,
            "notes": mood_entry.notes,
            "created_at": mood_entry.created_at,
            "is_burnout_risk": mood_entry.is_burnout_risk
        }
    }


@router.get("/history", response_model=List[MoodHistoryItem])
async def get_mood_history(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get mood history for visualization"""
    start_date = datetime.now() - timedelta(days=days)
    
    entries = db.query(MoodEntry).filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.created_at >= start_date
    ).order_by(desc(MoodEntry.created_at)).all()
    
    return [
        MoodHistoryItem(
            id=entry.id,
            mood_level=entry.mood_level,
            energy_level=entry.energy_level,
            mood_emoji=entry.mood_emoji,
            stress_level=entry.stress_level,
            notes=entry.notes,
            created_at=entry.created_at,
            is_burnout_risk=entry.is_burnout_risk
        )
        for entry in entries
    ]


@router.get("/analytics", response_model=MoodAnalytics)
async def get_mood_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get mood analytics and patterns"""
    
    # Get entries for different time periods
    entries_7_days = db.query(MoodEntry).filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.created_at >= datetime.now() - timedelta(days=7)
    ).all()
    
    entries_30_days = db.query(MoodEntry).filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.created_at >= datetime.now() - timedelta(days=30)
    ).all()
    
    # Calculate averages
    avg_mood_7 = sum(e.mood_level for e in entries_7_days) / len(entries_7_days) if entries_7_days else 5
    avg_energy_7 = sum(e.energy_level for e in entries_7_days) / len(entries_7_days) if entries_7_days else 5
    avg_mood_30 = sum(e.mood_level for e in entries_30_days) / len(entries_30_days) if entries_30_days else 5
    avg_energy_30 = sum(e.energy_level for e in entries_30_days) / len(entries_30_days) if entries_30_days else 5
    
    # Determine trend
    if len(entries_7_days) >= 2:
        recent_avg = sum(e.mood_level for e in entries_7_days[:3]) / min(3, len(entries_7_days))
        older_avg = sum(e.mood_level for e in entries_7_days[3:]) / max(1, len(entries_7_days[3:]))
        
        if recent_avg > older_avg + 0.5:
            trend = "improving"
        elif recent_avg < older_avg - 0.5:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"
    
    # Burnout risk assessment
    burnout_count = sum(1 for e in entries_7_days if e.is_burnout_risk)
    if burnout_count >= 3:
        burnout_risk = "high"
    elif burnout_count >= 1:
        burnout_risk = "medium"
    else:
        burnout_risk = "low"
    
    return MoodAnalytics(
        avg_mood_7_days=round(avg_mood_7, 1),
        avg_energy_7_days=round(avg_energy_7, 1),
        avg_mood_30_days=round(avg_mood_30, 1),
        avg_energy_30_days=round(avg_energy_30, 1),
        mood_trend=trend,
        burnout_risk=burnout_risk,
        best_mood_time="Morning",  # TODO: Calculate from data
        worst_mood_time="Afternoon"  # TODO: Calculate from data
    )


@router.get("/insights")
async def get_mood_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI-powered mood insights and suggestions"""
    
    recent_entries = db.query(MoodEntry).filter(
        MoodEntry.user_id == current_user.id
    ).order_by(desc(MoodEntry.created_at)).limit(14).all()
    
    if not recent_entries:
        return {
            "insights": [],
            "recommendations": ["Start tracking your mood daily to get personalized insights"],
            "patterns": []
        }
    
    try:
        # Get AI analysis of mood patterns
        analysis = await openai_service.detect_burnout_and_suggest_interventions(
            recent_mood_entries=recent_entries,
            user=current_user
        )
        
        return {
            "insights": [
                f"Your average mood over the last week: {sum(e.mood_level for e in recent_entries[:7])/min(7, len(recent_entries)):.1f}/10",
                f"Burnout risk level: {analysis.get('burnout_risk', 'unknown')}"
            ],
            "recommendations": [item['action'] for item in analysis.get('interventions', [])],
            "patterns": analysis.get('positive_patterns', [])
        }
    except Exception as e:
        return {
            "insights": ["Unable to generate insights at the moment"],
            "recommendations": ["Continue daily mood tracking for better insights"],
            "patterns": []
        }


def get_mood_response_message(mood_level: int, energy_level: int) -> str:
    """Get appropriate response message based on mood/energy"""
    if mood_level <= 3:
        return "I notice you're having a tough time. Remember, it's okay to feel this way. What's one small thing you could do to care for yourself right now?"
    elif mood_level <= 5:
        return "Thanks for checking in. It sounds like things are challenging today. Would you like some suggestions to help boost your mood?"
    elif mood_level <= 7:
        return "Good to see you checking in! You're doing well maintaining balance. How can we make today even better?"
    else:
        return "Wonderful! I can see you're in a great headspace today. This is perfect energy for tackling your important goals!"