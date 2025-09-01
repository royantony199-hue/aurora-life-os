from openai import OpenAI
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.models.mood import MoodEntry
from app.models.goal import Goal
from app.models.user import User
import json
import os


class OpenAIService:
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize or reinitialize the OpenAI client"""
        try:
            # Try multiple sources for API key
            api_key = os.getenv("OPENAI_API_KEY") or settings.openai_api_key
            
            # DEBUG: Check API key availability (no sensitive info logged)
            has_env_key = bool(os.getenv('OPENAI_API_KEY'))
            has_settings_key = bool(settings.openai_api_key)
            print(f"DEBUG: Environment key available: {has_env_key}")
            print(f"DEBUG: Settings key available: {has_settings_key}")
            
            if api_key and not api_key.startswith("sk-test-key-replace"):
                print(f"DEBUG: Initializing OpenAI client with real key")
                try:
                    self.client = OpenAI(api_key=api_key)
                    print("DEBUG: OpenAI client initialized successfully")
                except Exception as e:
                    print(f"DEBUG: Failed to initialize OpenAI client: {e}")
                    self.client = None
            else:
                print("DEBUG: No valid OpenAI API key found")
                self.client = None
        except Exception as e:
            print(f"DEBUG: Failed to initialize OpenAI client: {str(e)}")
            print("DEBUG: Continuing without OpenAI client - AI features will be disabled")
            self.client = None
    
    def reload_client(self):
        """Reload the OpenAI client with updated API key"""
        self._initialize_client()
    
    async def get_emotional_response(
        self,
        user_message: str,
        user_mood: int,
        user_energy: int,
        conversation_history: List[Dict[str, str]] = None,
        user_context: Dict[str, Any] = None
    ) -> str:
        """Generate emotionally intelligent response based on user's mood and context"""
        
        # Build emotional intelligence prompt
        mood_description = self._get_mood_description(user_mood)
        energy_description = self._get_energy_description(user_energy)
        
        # Build goals context
        goals_info = ""
        if user_context and "goals" in user_context:
            goals_data = user_context["goals"]
            if goals_data["goals_count"] > 0:
                goals_list = "\n".join([
                    f"- {goal['title']} ({goal['category']}, {goal['progress']:.0f}% complete)"
                    + (f" - Due: {goal['target_date'][:10]}" if goal['target_date'] else "")
                    for goal in goals_data["active_goals"]
                ])
                goals_info = f"""
        
        USER'S ACTIVE GOALS ({goals_data["goals_count"]} total):
        {goals_list}
        
        IMPORTANT: Always relate conversations back to their goals. Help them:
        - Make progress on specific goals
        - Connect daily activities to goal achievement
        - Stay motivated and focused on what matters
        - Break down goals into actionable steps
        - Celebrate progress and wins
        """
            else:
                goals_info = """
        
        USER HAS NO ACTIVE GOALS SET.
        PRIORITY: Help them identify and set meaningful goals. Ask about:
        - What they want to achieve (career, health, personal, learning, financial)
        - What's most important to them right now
        - What would make the biggest impact in their life
        """
        
        system_prompt = f"""You are Aurora, an emotionally intelligent AI life coach and personal assistant for solopreneurs and founders. 
        
        Your personality:
        - Warm, empathetic, and understanding
        - Professional but friendly tone
        - Focus on empowerment, not dependency
        - Celebrate wins and provide gentle support during challenges
        - GOAL-FOCUSED: Everything revolves around helping them achieve their goals
        
        Current user state:
        - Mood: {user_mood}/10 ({mood_description})
        - Energy: {user_energy}/10 ({energy_description}){goals_info}
        
        Guidelines based on mood:
        {self._get_mood_guidance(user_mood, user_energy)}
        
        Always:
        - Acknowledge their emotional state if relevant
        - Connect responses to their goals when possible
        - Provide actionable advice
        - Ask follow-up questions to understand better
        - Suggest concrete next steps that advance their goals
        - Keep responses concise but meaningful (2-3 sentences max unless they ask for details)
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history[-10:])  # Last 10 messages for context
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        if not self.client:
            return "I'm currently offline. Please configure your OpenAI API key to enable AI features."
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=300,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"I'm having trouble connecting right now. How can I help you in the meantime? (Error: {str(e)[:50]}...)"
    
    async def generate_task_breakdown(self, prompt: str) -> str:
        """Generate task breakdown with more tokens for JSON responses"""
        if not self.client:
            return "I'm currently offline. Please configure your OpenAI API key to enable AI features."
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a productivity expert who creates detailed, actionable task breakdowns in JSON format. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,  # More tokens for JSON task generation
                temperature=0.3,  # Lower temperature for more consistent JSON
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error in task breakdown generation: {e}")
            return "ERROR: Task generation failed"
    
    async def analyze_goals_and_provide_coaching(
        self,
        user: User,
        goals: List[Goal],
        recent_mood_entries: List[MoodEntry] = None
    ) -> Dict[str, Any]:
        """Provide coaching analysis and recommendations based on user's goals and mood patterns"""
        
        goals_summary = "\n".join([
            f"- {goal.title} ({goal.category.value}, {goal.progress:.0f}% complete, status: {goal.status.value})"
            for goal in goals
        ])
        
        mood_analysis = ""
        if recent_mood_entries:
            avg_mood = sum(entry.mood_level for entry in recent_mood_entries) / len(recent_mood_entries)
            avg_energy = sum(entry.energy_level for entry in recent_mood_entries) / len(recent_mood_entries)
            mood_analysis = f"\nRecent mood patterns:\n- Average mood: {avg_mood:.1f}/10\n- Average energy: {avg_energy:.1f}/10"
        
        system_prompt = f"""You are Aurora, an expert AI coach for solopreneurs. Analyze the user's goals and provide personalized coaching insights.
        
        User: {user.full_name or user.username}
        Goals: {goals_summary}
        {mood_analysis}
        
        Provide coaching in this JSON format:
        {{
            "overall_assessment": "brief overall assessment of progress",
            "priority_recommendations": ["top 3 actionable recommendations"],
            "goal_insights": [
                {{"goal": "goal title", "insight": "specific insight", "next_action": "concrete next step"}}
            ],
            "motivation_message": "encouraging personalized message",
            "warning_flags": ["any concerns about burnout, unrealistic goals, etc."]
        }}
        
        Focus on:
        - Realistic, actionable advice
        - Breaking down complex goals
        - Identifying potential obstacles
        - Celebrating progress made
        - Emotional state considerations
        """
        
        if not self.client:
            return "I'm currently offline. Please configure your OpenAI API key to enable AI features."
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": system_prompt}],
                max_tokens=800,
                temperature=0.7,
            )
            
            coaching_analysis = json.loads(response.choices[0].message.content.strip())
            return coaching_analysis
        except Exception as e:
            return {
                "overall_assessment": "Unable to analyze goals at the moment",
                "priority_recommendations": ["Review your current goals and priorities"],
                "goal_insights": [],
                "motivation_message": "Keep pushing forward - you're doing great!",
                "warning_flags": []
            }
    
    async def break_down_goal(self, goal: Goal) -> List[Dict[str, str]]:
        """Break down a high-level goal into actionable tasks"""
        
        system_prompt = f"""Break down this goal into specific, actionable tasks.
        
        Goal: {goal.title}
        Description: {goal.description or 'No description provided'}
        Category: {goal.category.value}
        Target Date: {goal.target_date}
        
        Provide 5-8 concrete, actionable tasks in JSON format:
        [
            {{"task": "specific action item", "estimated_time": "time estimate", "priority": "high/medium/low"}},
            ...
        ]
        
        Make tasks:
        - Specific and actionable
        - Time-bound when possible
        - Ordered by logical sequence
        - Realistic for a busy solopreneur
        """
        
        if not self.client:
            return "I'm currently offline. Please configure your OpenAI API key to enable AI features."
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": system_prompt}],
                max_tokens=600,
                temperature=0.7,
            )
            
            tasks = json.loads(response.choices[0].message.content.strip())
            return tasks
        except Exception as e:
            return [
                {"task": "Define specific milestones for this goal", "estimated_time": "30 minutes", "priority": "high"},
                {"task": "Research best practices and resources", "estimated_time": "1 hour", "priority": "medium"},
                {"task": "Create a timeline with deadlines", "estimated_time": "20 minutes", "priority": "high"}
            ]
    
    async def detect_burnout_and_suggest_interventions(
        self,
        recent_mood_entries: List[MoodEntry],
        user: User,
        recent_messages: List[str] = None
    ) -> Dict[str, Any]:
        """Detect signs of burnout and suggest interventions"""
        
        if not recent_mood_entries:
            return {"burnout_risk": "unknown", "interventions": []}
        
        # Calculate burnout indicators
        avg_mood = sum(entry.mood_level for entry in recent_mood_entries) / len(recent_mood_entries)
        avg_energy = sum(entry.energy_level for entry in recent_mood_entries) / len(recent_mood_entries)
        declining_trend = len(recent_mood_entries) >= 3 and recent_mood_entries[-1].mood_level < recent_mood_entries[0].mood_level
        
        mood_data = ", ".join([f"Day {i+1}: mood {entry.mood_level}, energy {entry.energy_level}" 
                              for i, entry in enumerate(recent_mood_entries[-7:])])
        
        system_prompt = f"""Analyze this mood/energy data for burnout risk and suggest interventions.
        
        User: {user.full_name or user.username}
        Last 7 days: {mood_data}
        Average mood: {avg_mood:.1f}/10
        Average energy: {avg_energy:.1f}/10
        Declining trend: {declining_trend}
        
        Provide analysis in JSON format:
        {{
            "burnout_risk": "low/medium/high",
            "risk_factors": ["specific concerning patterns"],
            "interventions": [
                {{"type": "immediate", "action": "what to do right now"}},
                {{"type": "today", "action": "action for today"}},
                {{"type": "this_week", "action": "longer-term adjustment"}}
            ],
            "positive_patterns": ["things they're doing well"],
            "recovery_timeline": "expected recovery time if interventions followed"
        }}
        
        Focus on:
        - Practical, actionable interventions
        - Sustainable recovery approaches
        - Celebrating what's working
        """
        
        if not self.client:
            return "I'm currently offline. Please configure your OpenAI API key to enable AI features."
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": system_prompt}],
                max_tokens=500,
                temperature=0.7,
            )
            
            analysis = json.loads(response.choices[0].message.content.strip())
            return analysis
        except Exception as e:
            # Fallback analysis
            if avg_mood < 4 or avg_energy < 3:
                return {
                    "burnout_risk": "high",
                    "interventions": [
                        {"type": "immediate", "action": "Take a 10-minute break and do some deep breathing"},
                        {"type": "today", "action": "Reduce your task list by 30% and prioritize rest"},
                        {"type": "this_week", "action": "Schedule regular breaks and reassess your workload"}
                    ]
                }
            else:
                return {"burnout_risk": "low", "interventions": []}
    
    def _get_mood_description(self, mood: int) -> str:
        """Convert mood number to description"""
        if mood <= 2:
            return "very low/distressed"
        elif mood <= 4:
            return "low/struggling"
        elif mood <= 6:
            return "neutral/okay"
        elif mood <= 8:
            return "good/positive"
        else:
            return "excellent/energized"
    
    def _get_energy_description(self, energy: int) -> str:
        """Convert energy number to description"""
        if energy <= 2:
            return "very low/exhausted"
        elif energy <= 4:
            return "low/tired"
        elif energy <= 6:
            return "moderate/okay"
        elif energy <= 8:
            return "high/energetic"
        else:
            return "very high/peak energy"
    
    async def generate_conversational_response(self, prompt: str) -> str:
        """Generate natural conversational response without JSON formatting"""
        if not self.client:
            return "I'm currently offline. Please configure your OpenAI API key to enable AI features."
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": """You are Aurora, a warm and supportive AI life coach. 
                        
                        CRITICAL INSTRUCTION: Always respond in natural, conversational language only.
                        - Never use JSON format
                        - Never use code blocks or markdown
                        - Never use quotation marks around your response
                        - Never use structured data formats
                        - Write exactly like you're talking to a friend face-to-face
                        
                        Be warm, encouraging, and practical. Keep responses to 2-4 sentences unless more detail is needed."""
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error in conversational response generation: {e}")
            return "I'm having some technical difficulties right now, but I'm here to help! What's on your mind?"

    def _get_mood_guidance(self, mood: int, energy: int) -> str:
        """Get guidance for responding based on mood/energy levels"""
        if mood <= 3 or energy <= 2:
            return """- Be extra supportive and gentle
- Suggest smaller, manageable tasks
- Recommend rest or recovery activities
- Avoid overwhelming them with information
- Focus on immediate comfort and basic needs"""
        elif mood <= 5 or energy <= 4:
            return """- Provide gentle encouragement
- Break tasks into smaller steps
- Suggest energy-boosting activities
- Be understanding of their current limitations
- Offer practical, low-effort solutions"""
        elif mood >= 7 and energy >= 7:
            return """- Match their positive energy
- Suggest tackling challenging tasks
- Encourage ambitious planning
- Capitalize on their current momentum
- Provide detailed action plans"""
        else:
            return """- Maintain balanced, professional tone
- Provide standard coaching advice
- Ask about their goals and priorities
- Offer structured guidance
- Be encouraging but realistic"""