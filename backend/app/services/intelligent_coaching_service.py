#!/usr/bin/env python3
"""
Intelligent Context-Aware Coaching Service

This service provides sophisticated AI coaching that adapts to user context,
maintains conversation coherence, and responds appropriately to different types
of queries regardless of existing goals or data in the system.
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from .openai_service import OpenAIService
from ..models.user import User
from ..models.goal import Goal, GoalStatus, GoalCategory
from ..models.task import Task, TaskStatus, TaskPriority, TaskType
from ..models.chat import ChatMessage, MessageRole, MessageType


class IntelligentCoachingService:
    """
    Advanced AI coaching service that provides contextually appropriate responses
    based on conversation flow rather than rigid goal matching
    """
    
    def __init__(self):
        self.openai_service = OpenAIService()
    
    async def coach_conversation(
        self, 
        message: str, 
        user_id: int, 
        db: Session,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Main intelligent coaching conversation handler
        
        This method analyzes the user's message in context and provides
        appropriate coaching responses regardless of existing system data
        """
        
        # Get user data for context but don't let it dominate the conversation
        user = db.query(User).filter(User.id == user_id).first()
        existing_goals = db.query(Goal).filter(Goal.user_id == user_id).all()
        recent_tasks = db.query(Task).filter(Task.user_id == user_id).limit(5).all()
        
        # Build conversation context - this is the primary source of truth
        conversation_context = self._build_conversation_context(
            message, conversation_history, user, existing_goals, recent_tasks
        )
        
        # Analyze what the user is really asking about
        query_analysis = await self._analyze_user_query(message, conversation_context)
        
        print(f"DEBUG: Query analysis: {query_analysis}")
        
        # Generate contextually appropriate response
        coaching_response = await self._generate_contextual_response(
            message, query_analysis, conversation_context, user_id, db
        )
        
        return coaching_response
    
    def _build_conversation_context(
        self, 
        current_message: str,
        conversation_history: List[Dict],
        user: User,
        existing_goals: List[Goal],
        recent_tasks: List[Task]
    ) -> Dict[str, Any]:
        """
        Build comprehensive conversation context that prioritizes what the user
        is actually discussing over what exists in the database
        """
        
        # Extract topics from conversation history
        conversation_topics = self._extract_conversation_topics(conversation_history)
        current_topics = self._extract_topics_from_message(current_message)
        
        # Build context hierarchy: conversation > current message > existing data
        context = {
            'current_message': current_message,
            'conversation_topics': conversation_topics,
            'current_topics': current_topics,
            'conversation_history': self._format_recent_history(conversation_history),
            'user': {
                'name': user.full_name if user else 'Friend',
                'id': user.id if user else 1
            },
            # Existing data is available but shouldn't dominate responses
            'existing_goals': [
                {
                    'title': goal.title,
                    'category': goal.category.value,
                    'progress': goal.progress,
                    'relevant': self._is_goal_relevant_to_conversation(goal, conversation_topics + current_topics)
                }
                for goal in existing_goals
            ],
            'recent_tasks': [
                {
                    'title': task.title,
                    'status': task.status.value,
                    'relevant': self._is_task_relevant_to_conversation(task, conversation_topics + current_topics)
                }
                for task in recent_tasks
            ]
        }
        
        return context
    
    def _extract_conversation_topics(self, conversation_history: List[Dict]) -> List[str]:
        """Extract key topics from conversation history"""
        if not conversation_history:
            return []
        
        topics = []
        for msg in conversation_history[-10:]:  # Last 10 messages
            content = msg.get('content', '').lower()
            
            # Business/service topics
            if any(term in content for term in ['ai services', 'dm setting', 'content creation', 'lead gen', 'marketing']):
                topics.append('business_services')
            
            # Lead generation topics
            if any(term in content for term in ['lead', 'leads', 'outreach', 'channels', 'clients', 'customers']):
                topics.append('lead_generation')
            
            # Health/fitness topics
            if any(term in content for term in ['exercise', 'fitness', 'health', 'workout', 'diet']):
                topics.append('health_fitness')
            
            # Goal setting topics
            if any(term in content for term in ['goal', 'achieve', 'target', 'plan']):
                topics.append('goal_planning')
                
            # Development topics
            if any(term in content for term in ['build', 'develop', 'create', 'project', 'app']):
                topics.append('development')
        
        return list(set(topics))  # Remove duplicates
    
    def _extract_topics_from_message(self, message: str) -> List[str]:
        """Extract topics from current message"""
        message_lower = message.lower()
        topics = []
        
        # Business services
        if any(term in message_lower for term in ['ai services', 'dm setter', 'content creation']):
            topics.append('ai_business_services')
        
        # Lead generation
        if any(term in message_lower for term in ['lead gen', 'leads', 'channels', 'outreach', 'reach']):
            topics.append('lead_generation')
        
        # Marketing
        if any(term in message_lower for term in ['marketing', 'promotion', 'advertising', 'clients']):
            topics.append('marketing')
        
        # Strategy
        if any(term in message_lower for term in ['strategy', 'approach', 'plan', 'how to']):
            topics.append('strategy')
        
        return topics
    
    def _format_recent_history(self, conversation_history: List[Dict]) -> str:
        """Format recent conversation for AI context"""
        if not conversation_history:
            return "No previous conversation."
        
        formatted = []
        for msg in conversation_history[-6:]:  # Last 6 messages for context
            role = "User" if msg.get('role') == 'user' else "Aurora"
            content = msg.get('content', '')
            if content:
                formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted) if formatted else "No previous conversation."
    
    def _is_goal_relevant_to_conversation(self, goal: Goal, topics: List[str]) -> bool:
        """Determine if an existing goal is relevant to current conversation"""
        goal_title_lower = goal.title.lower()
        
        # Check if goal matches conversation topics
        if 'ai_business_services' in topics or 'lead_generation' in topics:
            if any(term in goal_title_lower for term in ['business', 'income', 'revenue', 'clients', 'ai']):
                return True
        
        if 'health_fitness' in topics:
            if any(term in goal_title_lower for term in ['exercise', 'health', 'fitness', 'workout']):
                return True
                
        return False
    
    def _is_task_relevant_to_conversation(self, task: Task, topics: List[str]) -> bool:
        """Determine if a task is relevant to current conversation"""
        task_title_lower = task.title.lower()
        
        if 'ai_business_services' in topics or 'lead_generation' in topics:
            if any(term in task_title_lower for term in ['business', 'marketing', 'client', 'lead', 'ai']):
                return True
                
        return False
    
    async def _analyze_user_query(self, message: str, context: Dict) -> Dict[str, Any]:
        """
        Analyze what the user is actually asking about using AI
        instead of rigid pattern matching
        """
        
        conversation_history = context['conversation_history']
        current_topics = context['current_topics']
        
        analysis_prompt = f"""
        Analyze this user message to understand what they're asking about:
        
        RECENT CONVERSATION:
        {conversation_history}
        
        CURRENT MESSAGE: "{message}"
        
        Determine:
        1. What is the primary topic/subject they're asking about?
        2. What type of help do they need? (advice, strategy, action steps, information, motivation)
        3. What specific aspects are they interested in?
        4. How does this relate to previous conversation?
        
        Response format:
        {{
            "primary_topic": "specific topic they're asking about",
            "help_type": "advice|strategy|action_steps|information|motivation",
            "specific_aspects": ["aspect1", "aspect2"],
            "conversation_connection": "how this relates to previous messages",
            "user_intent": "what they want to accomplish"
        }}
        """
        
        try:
            response = await self.openai_service.generate_task_breakdown(analysis_prompt)
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                return analysis
        except Exception as e:
            print(f"Query analysis error: {e}")
        
        # Fallback analysis based on message content
        message_lower = message.lower()
        
        if any(term in message_lower for term in ['lead gen', 'leads', 'channels', 'reach']):
            return {
                "primary_topic": "lead generation for AI services",
                "help_type": "strategy",
                "specific_aspects": ["marketing channels", "outreach methods"],
                "conversation_connection": "building on their AI services business",
                "user_intent": "find new ways to get clients"
            }
        elif any(term in message_lower for term in ['how to', 'strategy', 'approach']):
            return {
                "primary_topic": "strategy development",
                "help_type": "advice",
                "specific_aspects": ["planning", "execution"],
                "conversation_connection": "seeking strategic guidance",
                "user_intent": "develop effective approach"
            }
        else:
            return {
                "primary_topic": "general coaching",
                "help_type": "advice",
                "specific_aspects": ["guidance"],
                "conversation_connection": "continuing conversation",
                "user_intent": "get support and direction"
            }
    
    async def _generate_contextual_response(
        self, 
        message: str, 
        query_analysis: Dict, 
        context: Dict, 
        user_id: int, 
        db: Session
    ) -> Dict[str, Any]:
        """
        Generate response that's specifically tailored to what the user is asking about
        """
        
        primary_topic = query_analysis.get('primary_topic', 'general')
        help_type = query_analysis.get('help_type', 'advice')
        user_intent = query_analysis.get('user_intent', 'get guidance')
        
        # Create comprehensive context prompt
        response_prompt = f"""
        You are Aurora, an intelligent AI life coach. You're having a natural conversation with someone.
        
        CONVERSATION CONTEXT:
        {context['conversation_history']}
        
        CURRENT MESSAGE: "{message}"
        
        WHAT THE USER IS ASKING ABOUT:
        - Primary topic: {primary_topic}
        - Type of help needed: {help_type}
        - What they want to accomplish: {user_intent}
        
        YOUR TASK:
        Respond directly to what they're asking about. Be conversational, helpful, and specific.
        
        If they're asking about business/marketing:
        - Focus on practical business advice
        - Suggest specific marketing channels and strategies
        - Give actionable recommendations
        
        If they're asking about personal goals:
        - Help them clarify and plan
        - Offer motivation and structure
        
        CRITICAL INSTRUCTIONS:
        - Address their SPECIFIC question directly
        - Build on the conversation naturally
        - Don't suggest unrelated topics or goals
        - Be conversational and warm
        - Provide 2-3 concrete suggestions
        - End with a relevant follow-up question
        
        Respond in natural, conversational language only. No JSON, no code blocks.
        """
        
        try:
            response = await self.openai_service.generate_conversational_response(response_prompt)
            
            # Generate relevant suggestions based on the topic
            suggestions = await self._generate_contextual_suggestions(query_analysis, context)
            
            # Generate tasks if appropriate
            suggested_tasks = []
            if help_type in ['action_steps', 'strategy'] and 'lead_generation' in primary_topic.lower():
                suggested_tasks = await self._generate_relevant_tasks(query_analysis, context)
            
            return {
                'response': response,
                'coaching_type': help_type,
                'suggestions': suggestions,
                'suggested_tasks': suggested_tasks if suggested_tasks else None,
                'topic': primary_topic
            }
            
        except Exception as e:
            print(f"Response generation error: {e}")
            return {
                'response': "I'm here to help with whatever you're working on. Can you tell me more about what you'd like to focus on?",
                'coaching_type': 'general',
                'suggestions': ['Tell me more about your current situation', 'What\'s your main priority right now?'],
                'suggested_tasks': None,
                'topic': 'general'
            }
    
    async def _generate_contextual_suggestions(self, query_analysis: Dict, context: Dict) -> List[str]:
        """Generate suggestions that are relevant to the user's actual query"""
        
        primary_topic = query_analysis.get('primary_topic', '').lower()
        help_type = query_analysis.get('help_type', '')
        
        if 'lead generation' in primary_topic or 'marketing' in primary_topic:
            return [
                'What\'s your ideal client profile?',
                'How do you currently measure success?',
                'What\'s your budget for marketing?'
            ]
        elif 'business' in primary_topic or 'ai services' in primary_topic:
            return [
                'Tell me about your service packages',
                'What results do your clients see?',
                'How do you differentiate from competitors?'
            ]
        elif 'strategy' in help_type:
            return [
                'What obstacles are you facing?',
                'What resources do you have available?',
                'What\'s your timeline?'
            ]
        else:
            return [
                'What would success look like for you?',
                'What\'s your biggest challenge right now?',
                'What have you tried before?'
            ]
    
    async def _generate_relevant_tasks(self, query_analysis: Dict, context: Dict) -> List[Dict]:
        """Generate tasks that are actually relevant to the user's query"""
        
        primary_topic = query_analysis.get('primary_topic', '')
        specific_aspects = query_analysis.get('specific_aspects', [])
        
        tasks_prompt = f"""
        The user is asking about: {primary_topic}
        Specific aspects: {specific_aspects}
        
        Generate 3-4 specific, actionable tasks they can do this week related to their question.
        
        IMPORTANT: Create tasks that directly address what they're asking about.
        If they're asking about lead generation for AI services, create lead generation tasks.
        If they're asking about marketing channels, create marketing research tasks.
        
        Format as JSON:
        [
            {{
                "title": "Research LinkedIn lead generation strategies",
                "description": "Study 10 successful LinkedIn profiles in AI services and analyze their content approach",
                "estimated_minutes": 45,
                "priority": "high",
                "category": "research"
            }}
        ]
        """
        
        try:
            response = await self.openai_service.generate_task_breakdown(tasks_prompt)
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                tasks = json.loads(json_match.group())
                return tasks
        except Exception as e:
            print(f"Task generation error: {e}")
        
        # Fallback tasks based on topic
        if 'lead generation' in primary_topic.lower():
            return [
                {
                    "title": "Research new lead generation channels",
                    "description": "Identify 3 new channels beyond Instagram for your AI services",
                    "estimated_minutes": 60,
                    "priority": "high",
                    "category": "research"
                },
                {
                    "title": "Create channel strategy comparison",
                    "description": "Compare pros, cons, and costs of different marketing channels",
                    "estimated_minutes": 45,
                    "priority": "medium",
                    "category": "planning"
                }
            ]
        
        return []