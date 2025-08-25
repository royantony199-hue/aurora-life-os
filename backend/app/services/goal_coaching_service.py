#!/usr/bin/env python3
"""
Goal Achievement Coaching Service
Provides intelligent conversational goal planning and step-by-step guidance
"""

import json
import re
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from .openai_service import OpenAIService
from ..models.user import User
from ..models.goal import Goal, GoalStatus, GoalCategory
from ..models.task import Task, TaskStatus, TaskPriority, TaskType
from ..models.chat import ChatMessage, MessageRole, MessageType


class GoalCoachingService:
    """
    Intelligent goal achievement coaching with conversational planning
    """
    
    def __init__(self):
        self.openai_service = OpenAIService()
        
    async def coach_goal_conversation(
        self, 
        message: str, 
        user_id: int, 
        db: Session,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Main coaching conversation handler - guides users from goals to actionable steps
        """
        
        # Get user context
        user = db.query(User).filter(User.id == user_id).first()
        current_goals = db.query(Goal).filter(Goal.user_id == user_id).all()
        recent_tasks = db.query(Task).filter(Task.user_id == user_id).limit(10).all()
        
        # Build context for AI
        context = self._build_user_context(user, current_goals, recent_tasks, conversation_history)
        
        # Analyze message intent
        intent = await self._analyze_message_intent(message, context)
        
        # Route to appropriate coaching strategy
        if intent['type'] == 'goal_definition':
            return await self._handle_goal_definition(message, context, user_id, db)
        elif intent['type'] == 'strategy_discussion':
            return await self._handle_strategy_discussion(message, context, user_id, db)
        elif intent['type'] == 'action_planning':
            return await self._handle_action_planning(message, context, user_id, db)
        elif intent['type'] == 'research_request':
            return await self._handle_research_request(message, context, user_id, db)
        elif intent['type'] == 'motivation_support':
            return await self._handle_motivation_support(message, context, user_id, db)
        else:
            return await self._handle_general_coaching(message, context, user_id, db)
    
    def _build_user_context(
        self, 
        user: User, 
        goals: List[Goal], 
        tasks: List[Task],
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Build comprehensive user context for AI coaching"""
        
        return {
            'user': {
                'name': user.full_name if user else 'Friend',
                'id': user.id if user else 1
            },
            'current_goals': [
                {
                    'title': goal.title,
                    'description': goal.description,
                    'category': goal.category.value,
                    'progress': goal.progress,
                    'status': goal.status.value
                }
                for goal in goals
            ],
            'recent_tasks': [
                {
                    'title': task.title,
                    'status': task.status.value,
                    'priority': task.priority.value,
                    'goal_id': task.goal_id
                }
                for task in tasks
            ],
            'conversation_history': conversation_history or []
        }
    
    def _format_conversation_history(self, conversation_history: List[Dict]) -> str:
        """Format conversation history for inclusion in prompts"""
        if not conversation_history:
            return "No previous conversation."
        
        formatted_history = []
        # Get last 5 messages for context (to keep prompts manageable)
        recent_messages = conversation_history[-5:]
        
        for msg in recent_messages:
            role = "User" if msg.get('role') == 'user' else "Aurora"
            content = msg.get('content', '')
            if content:
                formatted_history.append(f"{role}: {content}")
        
        if not formatted_history:
            return "No previous conversation."
            
        return "\n".join(formatted_history)
    
    async def _analyze_message_intent(self, message: str, context: Dict) -> Dict[str, Any]:
        """Analyze user message to understand coaching intent using pattern matching"""
        
        # Use simple pattern matching for better reliability
        message_lower = message.lower()
        
        # Goal definition patterns
        if any(phrase in message_lower for phrase in [
            'want to make', 'goal is', 'achieve', '$', 'earn', 'want to', 'i want', 
            'my goal', 'looking to', 'hoping to', 'trying to'
        ]):
            return {'type': 'goal_definition', 'confidence': 0.8}
        
        # Strategy discussion patterns  
        elif any(phrase in message_lower for phrase in [
            'how do i', 'what should i', 'strategy', 'plan', 'approach', 'best way',
            'how can i', 'what\'s the', 'how to', 'lead gen', 'lead generation', 
            'get leads', 'more leads', 'channels', 'what other', 'reach', 'marketing'
        ]):
            return {'type': 'strategy_discussion', 'confidence': 0.8}
        
        # Action planning patterns
        elif any(phrase in message_lower for phrase in [
            'next step', 'what now', 'to do', 'action', 'start', 'first',
            'what should i do', 'next', 'begin', 'steps'
        ]):
            return {'type': 'action_planning', 'confidence': 0.8}
        
        # Research request patterns
        elif any(phrase in message_lower for phrase in [
            'research', 'market', 'competitor', 'analyze', 'study', 'data',
            'information about', 'tell me about'
        ]):
            return {'type': 'research_request', 'confidence': 0.8}
        
        # Motivation support patterns
        elif any(phrase in message_lower for phrase in [
            'stuck', 'difficult', 'hard', 'struggling', 'frustrated', 'overwhelmed',
            'give up', 'can\'t', 'impossible', 'too much'
        ]):
            return {'type': 'motivation_support', 'confidence': 0.8}
        
        else:
            return {'type': 'general_coaching', 'confidence': 0.7}
    
    async def _handle_goal_definition(self, message: str, context: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Handle goal definition and clarification conversations"""
        
        conversation_history = self._format_conversation_history(context.get('conversation_history', []))
        
        prompt = f"""
        You are Aurora, an intelligent goal achievement coach. A user is defining their goal.
        
        CONVERSATION HISTORY:
        {conversation_history}
        
        CURRENT MESSAGE: "{message}"
        Current goals: {[g['title'] for g in context['current_goals']]}
        
        Your role: Act as a supportive life coach having a natural conversation that builds on the previous discussion.
        
        CRITICAL: 
        - Reference the conversation history to stay contextually relevant
        - Build on what the user has already shared
        - If they mentioned specific services, business goals, or challenges, address those directly
        - Don't suggest unrelated tasks or goals
        
        Respond in a warm, encouraging, conversational tone. Ask 1-2 follow-up questions to better understand their goal.
        Focus on their motivation and timeline.
        
        IMPORTANT: Reply as if you're talking to a friend. Use natural language only.
        No JSON, no code blocks, no structured data, no quotation marks around your response.
        Just write naturally like you're having a conversation.
        """
        
        response = await self.openai_service.generate_conversational_response(prompt)
        
        # Check if we should auto-create a goal
        should_create_goal = await self._should_create_goal_from_message(message, context)
        
        result = {
            'response': response,
            'coaching_type': 'goal_definition',
            'suggestions': [
                'Tell me more about your timeline',
                'What skills do you already have?',
                'What\'s your biggest motivation?'
            ]
        }
        
        if should_create_goal:
            goal_info = await self._extract_goal_from_message(message)
            result['suggested_goal'] = goal_info
            
        return result
    
    async def _handle_strategy_discussion(self, message: str, context: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Handle strategy and approach discussions"""
        
        conversation_history = self._format_conversation_history(context.get('conversation_history', []))
        
        prompt = f"""
        You are Aurora, helping a user develop their strategy to achieve their goal.
        
        CONVERSATION HISTORY:
        {conversation_history}
        
        CURRENT MESSAGE: "{message}"
        Their current goals: {[g['title'] + ' (' + str(g['progress']) + '% complete)' for g in context['current_goals']]}
        
        You are having a natural conversation as a supportive business mentor and life coach.
        
        CRITICAL CONTEXT AWARENESS:
        - Reference what they've already shared in the conversation
        - If they mentioned specific services (like AI services, DM setting, content creation), address those
        - If they're asking about lead generation or business channels, focus on that topic
        - Stay relevant to their actual business and goals mentioned in the history
        
        Respond conversationally and warmly. Validate their approach and provide practical insights.
        If it's a business idea, share relevant market insights and success factors.
        End with a thoughtful question to guide them forward.
        
        CRITICAL: Write exactly like you're talking to a friend - natural, warm, conversational.
        No JSON, no structured lists, no code formatting, no quotation marks.
        Just natural conversation flow.
        
        Keep it under 4 sentences and always end with a guiding question.
        """
        
        response = await self.openai_service.generate_conversational_response(prompt)
        
        # Generate strategy-specific suggestions
        strategy_suggestions = await self._generate_strategy_suggestions(message, context)
        
        return {
            'response': response,
            'coaching_type': 'strategy_discussion',
            'suggestions': strategy_suggestions
        }
    
    async def _handle_action_planning(self, message: str, context: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Handle converting strategies into specific actionable tasks"""
        
        conversation_history = self._format_conversation_history(context.get('conversation_history', []))
        
        prompt = f"""
        You are Aurora, helping convert strategy into specific actionable steps.
        
        CONVERSATION HISTORY:
        {conversation_history}
        
        CURRENT MESSAGE: "{message}"
        Context: {context['current_goals']}
        
        You are a motivational coach having a natural conversation. The user is ready for action steps.
        
        CRITICAL CONTEXT AWARENESS:
        - IGNORE unrelated existing goals like "Build Aurora Life OS" or "Daily Exercise" 
        - Focus ONLY on what the user is asking about in their current message
        - If they mention AI services, DM setting, content creation - respond about THOSE services
        - If they ask about lead generation channels, suggest lead gen channels for THEIR business
        - Do NOT suggest tasks about building other products or unrelated goals
        - Stay laser-focused on their current business question
        
        Acknowledge their readiness and suggest 2-3 specific steps they can take this week.
        Be practical about tools and resources they'll need.
        
        IMPORTANT: Respond in natural, flowing conversation - like you're talking face-to-face.
        No bullet points, no JSON, no structured formats, no quotation marks.
        Write in complete sentences as if speaking naturally.
        
        End by asking which step feels most doable to start with.
        """
        
        response = await self.openai_service.generate_conversational_response(prompt)
        
        # Auto-generate tasks based on the conversation
        suggested_tasks = await self._generate_action_tasks(message, context, user_id, db)
        
        return {
            'response': response,
            'coaching_type': 'action_planning',
            'suggested_tasks': suggested_tasks,
            'suggestions': [
                'Create these tasks for me',
                'What tools do I need?',
                'How long will this take?'
            ]
        }
    
    async def _handle_research_request(self, message: str, context: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Handle requests for market research and information"""
        
        # Extract research topic
        research_topic = await self._extract_research_topic(message)
        
        conversation_history = self._format_conversation_history(context.get('conversation_history', []))
        
        prompt = f"""
        Provide helpful research insights for: "{research_topic}"
        
        CONVERSATION HISTORY:
        {conversation_history}
        
        CURRENT MESSAGE: "{message}"
        Their goals: {[g['title'] for g in context['current_goals']]}
        
        CRITICAL CONTEXT AWARENESS:
        - Reference what they've shared about their specific business/services
        - If they mentioned AI services, DM setting, content creation - focus research on those areas
        - If they're asking about lead generation channels, provide channel-specific insights
        - Keep research relevant to their actual business context
        
        Provide practical, actionable research including:
        1. Market size and opportunity
        2. Target customer segments  
        3. Competitive landscape
        4. Pricing strategies
        5. Marketing channels and approaches
        6. Key success metrics to track
        
        Keep insights practical and business-focused. Include specific examples and numbers when possible.
        End with 2-3 specific research tasks they can do to learn more.
        """
        
        response = await self.openai_service.generate_conversational_response(prompt)
        
        return {
            'response': response,
            'coaching_type': 'research',
            'research_topic': research_topic,
            'suggestions': [
                'Create research tasks for me',
                'What should I analyze first?',
                'Help me find competitors'
            ]
        }
    
    async def _handle_motivation_support(self, message: str, context: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Handle motivation and mindset support"""
        
        conversation_history = self._format_conversation_history(context.get('conversation_history', []))
        
        prompt = f"""
        Provide motivational support and guidance.
        
        CONVERSATION HISTORY:
        {conversation_history}
        
        CURRENT MESSAGE: "{message}"
        Their progress: {[g['title'] + f" ({g['progress']}% complete)" for g in context['current_goals']]}
        
        CRITICAL CONTEXT AWARENESS:
        - Reference their specific challenges and goals mentioned in the conversation
        - Build on what they've shared about their business/services
        - Acknowledge their specific situation and struggles
        
        Your role:
        1. Acknowledge their feelings/concerns
        2. Provide encouragement and perspective
        3. Remind them of their progress and potential
        4. Suggest small, manageable next steps
        5. Help them refocus on their "why"
        
        Be empathetic, positive, and actionable. Help them see obstacles as opportunities to grow.
        """
        
        response = await self.openai_service.generate_conversational_response(prompt)
        
        return {
            'response': response,
            'coaching_type': 'motivation',
            'suggestions': [
                'What\'s my next small win?',
                'Review my progress',
                'Break down my next step'
            ]
        }
    
    async def _handle_general_coaching(self, message: str, context: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Handle general goal coaching conversations"""
        
        conversation_history = self._format_conversation_history(context.get('conversation_history', []))
        
        prompt = f"""
        You are Aurora, a warm and supportive AI goal coach having a natural conversation.
        
        CONVERSATION HISTORY:
        {conversation_history}
        
        CURRENT MESSAGE: "{message}"
        User context: {len(context['current_goals'])} goals, {len(context['recent_tasks'])} recent tasks
        
        CRITICAL CONTEXT AWARENESS:
        - Reference and build on the previous conversation
        - Stay relevant to what the user has actually shared
        - If they've mentioned specific business services, goals, or challenges, address those directly
        - Don't suggest unrelated topics or tasks
        
        Respond naturally and conversationally - like you're talking to a friend who needs guidance.
        Be encouraging and always suggest a practical next step.
        
        CRITICAL: Use natural language only - no JSON, no code blocks, no structured formatting.
        Write exactly like you're having a face-to-face conversation.
        """
        
        response = await self.openai_service.generate_conversational_response(prompt)
        
        return {
            'response': response,
            'coaching_type': 'general',
            'suggestions': [
                'What should I focus on today?',
                'Help me plan my week',
                'Review my goals'
            ]
        }
    
    # Helper methods
    async def _should_create_goal_from_message(self, message: str, context: Dict) -> bool:
        """Determine if we should suggest creating a goal from this message"""
        goal_indicators = ['want to', 'goal is', 'achieve', 'make $', 'earn', 'reach', 'get to']
        return any(indicator in message.lower() for indicator in goal_indicators)
    
    async def _extract_goal_from_message(self, message: str) -> Dict[str, Any]:
        """Extract goal information from user message"""
        # Simple extraction - could be enhanced with more sophisticated NLP
        return {
            'title': message[:50] + '...' if len(message) > 50 else message,
            'category': 'career',  # Default category
            'confidence': 0.7
        }
    
    async def _generate_strategy_suggestions(self, message: str, context: Dict) -> List[str]:
        """Generate contextual strategy suggestions"""
        return [
            'What resources do I need?',
            'Who should I network with?',
            'What are the risks I should know?',
            'Show me similar success stories'
        ]
    
    async def _generate_action_tasks(self, message: str, context: Dict, user_id: int, db: Session) -> List[Dict]:
        """Generate specific actionable tasks based on conversation"""
        
        conversation_history = self._format_conversation_history(context.get('conversation_history', []))
        
        prompt = f"""
        CONVERSATION HISTORY:
        {conversation_history}
        
        CURRENT MESSAGE: "{message}"
        User goals: {[g['title'] for g in context['current_goals']]}
        
        CRITICAL CONTEXT AWARENESS:
        - COMPLETELY IGNORE unrelated existing goals like "Build Aurora Life OS", "Daily Exercise", etc.
        - Generate tasks ONLY about what the user is currently asking about
        - If they mention AI services, DM setting, content creation - create tasks for THOSE services
        - If they ask about lead generation - create lead generation tasks for THEIR business
        - Do NOT create tasks about Aurora Life OS, exercise, or any other unrelated goals
        - Focus exclusively on their current business question and services mentioned
        
        Generate 3-5 specific, actionable tasks they can do this week.
        Each task should be:
        - Specific and measurable
        - Achievable in 30-120 minutes
        - Directly related to their actual business/goals discussed in conversation
        - Include clear success criteria
        
        Return as JSON array:
        [
            {
                "title": "Research LinkedIn outreach strategies for AI services",
                "description": "Analyze successful LinkedIn posts and messaging approaches for AI service providers",
                "estimated_minutes": 60,
                "priority": "high",
                "category": "research"
            }
        ]
        """
        
        try:
            response = await self.openai_service.generate_task_breakdown(prompt)
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"Task generation error: {e}")
        
        # Fallback tasks
        return [
            {
                "title": "Define success metrics",
                "description": "Write down specific numbers and dates for your goal",
                "estimated_minutes": 30,
                "priority": "high",
                "category": "planning"
            }
        ]
    
    async def _extract_research_topic(self, message: str) -> str:
        """Extract the main research topic from user message"""
        # Simple extraction - could be enhanced
        research_words = ['research', 'analyze', 'study', 'investigate', 'learn about']
        for word in research_words:
            if word in message.lower():
                # Get text after the research word
                parts = message.lower().split(word)
                if len(parts) > 1:
                    return parts[1].strip()[:100]
        
        return message[:100]  # Fallback to first 100 chars
    
    def _clean_response(self, response: str) -> str:
        """Clean AI response from JSON formatting and return plain text"""
        # Remove markdown code blocks
        if response.startswith('```json'):
            response = response.replace('```json', '').replace('```', '')
        elif response.startswith('```'):
            response = response.replace('```', '')
        
        # Try to extract clean text from JSON response
        try:
            import json
            response = response.strip()
            if response.startswith('{'):
                json_data = json.loads(response)
                # Try different possible keys for the actual response
                for key in ['response', 'message', 'text', 'answer']:
                    if key in json_data:
                        return json_data[key]
                # If it has questions, use the first one
                if 'questions' in json_data and json_data['questions']:
                    return json_data['questions'][0]
                # If it has a task, use that
                if 'task' in json_data:
                    task_data = json_data['task']
                    if isinstance(task_data, str):
                        return task_data
                    elif isinstance(task_data, dict) and 'description' in task_data:
                        return task_data['description']
        except:
            pass  # Keep original response if JSON parsing fails
            
        # Clean up any remaining formatting
        response = response.strip()
        if response.startswith('"') and response.endswith('"'):
            response = response[1:-1]
            
        return response