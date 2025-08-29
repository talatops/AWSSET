"""
Groq AI Service for AWS Chatbot
Handles AI-powered conversations and AWS command interpretation
"""

import json
import re
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from groq import Groq
from decouple import config

from utils.logger import get_aws_logger

logger = get_aws_logger()

class GroqService:
    """
    Advanced Groq AI service for AWS operations and analysis
    """
    
    def __init__(self):
        self.api_key = config('GROQ_API_KEY', default='')
        self.model_name = config('GROQ_MODEL', default='llama3-8b-8192')
        self.temperature = float(config('GROQ_TEMPERATURE', default='0.1'))
        self.max_tokens = int(config('GROQ_MAX_TOKENS', default='4096'))
        
        # Chatbot personality settings
        self.bot_name = config('CHATBOT_NAME', default='AWSBot')
        self.personality = config('CHATBOT_PERSONALITY', default='helpful_aws_expert')
        self.max_context = int(config('CHATBOT_MAX_CONTEXT', default='10'))
        
        # Initialize Groq
        if self.api_key and self.api_key != 'your_groq_api_key_here':
            self.client = Groq(api_key=self.api_key)
            self.is_configured = True
            logger.info("🤖 Groq AI service initialized successfully")
        else:
            self.client = None
            self.is_configured = False
            logger.warning("⚠️ Groq API key not configured")
        
        # Context memory for conversations
        self.conversation_contexts = {}
        
        # AWS services mapping with comprehensive keywords
        self.aws_services = {
            'ec2': ['instance', 'instances', 'server', 'servers', 'vm', 'virtual machine', 'compute', 'ec2'],
            's3': ['bucket', 'buckets', 'storage', 'file', 'files', 'object', 's3', 'blob'],
            'lambda': ['function', 'functions', 'serverless', 'lambda', 'faas'],
            'rds': ['database', 'databases', 'db', 'mysql', 'postgres', 'sql', 'rds'],
            'iam': ['user', 'users', 'role', 'roles', 'permission', 'permissions', 'policy', 'access', 'iam'],
            'cloudtrail': ['log', 'logs', 'audit', 'trail', 'events', 'activity', 'cloudtrail'],
            'vpc': ['vpc', 'network', 'subnet', 'gateway', 'security group', 'nacl'],
            'ecs': ['container', 'containers', 'docker', 'ecs', 'fargate'],
            'cloudformation': ['template', 'stack', 'infrastructure', 'iac', 'cloudformation']
        }
        
        # Enhanced action patterns with AWS-specific terms
        self.action_patterns = {
            'create': ['create', 'launch', 'deploy', 'setup', 'make', 'provision', 'spin up', 'bring up'],
            'terminate': ['terminate', 'destroy', 'kill', 'tear down'],
            'delete': ['delete', 'remove'],
            'list': ['list', 'show', 'display', 'get', 'view', 'see', 'describe', 'find'],
            'start': ['start', 'run', 'boot', 'power on', 'enable', 'turn on'],
            'stop': ['stop', 'halt', 'shutdown', 'power off', 'disable', 'turn off'],
            'reboot': ['reboot', 'restart', 'reset'],
            'update': ['update', 'modify', 'change', 'edit', 'configure', 'patch'],
            'analyze': ['analyze', 'check', 'review', 'audit', 'investigate', 'monitor']
        }

    async def process_message(self, message: str, user_id: str, conversation_id: str = None) -> Dict[str, Any]:
        """
        Process a user message and return structured response
        """
        try:
            if not self.is_configured:
                return {
                    'type': 'error',
                    'message': 'AI service not configured. Please add your Groq API key.',
                    'requires_setup': True
                }
            
            # Get conversation context
            context = self._get_conversation_context(user_id, conversation_id)
            
            # Classify intent and extract entities
            intent_result = await self._classify_intent(message, context)
            
            # Generate response based on intent
            response = await self._generate_response(message, intent_result, context)
            
            # Update conversation context
            self._update_conversation_context(user_id, conversation_id, message, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                'type': 'error',
                'message': 'Sorry, I encountered an error processing your request. Please try again.',
                'error_details': str(e)
            }

    async def _classify_intent(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """
        Classify user intent and extract AWS-related entities
        """
        try:
            # Create the classification prompt
            classification_prompt = f"""You are {self.bot_name}, an expert AWS cloud architect and DevOps specialist. Analyze this message and classify the intent with precision.

MESSAGE: "{message}"

CONTEXT: {self._format_context(context[-2:]) if context else "No previous context"}

CRITICAL CLASSIFICATION RULES:
- ANY message containing "launch", "create", "deploy", "start" + "instance" = aws_command with action=create
- Messages asking to "launch the instance" or "launch new instance" = aws_command (NOT question)
- Extract EC2 instance IDs (format: i-xxxxxxxxxxxxxxxxx) from the message
- For instance operations (start/stop/terminate), ensure instance_id is extracted
- Only classify as "question" if asking "what", "how", "why" about AWS concepts

Respond with JSON only:
{{
  "intent_type": "aws_command|question|analysis|help|greeting|other",
  "aws_service": "ec2|s3|lambda|rds|iam|cloudtrail|vpc|etc|null",
  "action": "create|list|show|get|start|stop|terminate|delete|update|describe|reboot|etc|null",
  "entities": ["instance_types", "regions", "names", "instance_ids", "etc"],
  "confidence": 0.0-1.0,
  "requires_aws_action": true/false,
  "parameters": {{"param": "value"}}
}}

EXAMPLES:
- "Launch the new instance for me" → {{"intent_type":"aws_command","aws_service":"ec2","action":"create","entities":[],"confidence":0.95,"requires_aws_action":true,"parameters":{{}}}}
- "Launch t2.micro instance" → {{"intent_type":"aws_command","aws_service":"ec2","action":"create","entities":["t2.micro"],"confidence":0.95,"requires_aws_action":true,"parameters":{{"instance_type":"t2.micro"}}}}
- "Create an instance" → {{"intent_type":"aws_command","aws_service":"ec2","action":"create","entities":[],"confidence":0.95,"requires_aws_action":true,"parameters":{{}}}}
- "Start instance i-0ff279129a87ab42" → {{"intent_type":"aws_command","aws_service":"ec2","action":"start","entities":["i-0ff279129a87ab42"],"confidence":0.95,"requires_aws_action":true,"parameters":{{"instance_id":"i-0ff279129a87ab42"}}}}
- "List my instances" → {{"intent_type":"aws_command","aws_service":"ec2","action":"list","entities":[],"confidence":0.9,"requires_aws_action":true,"parameters":{{}}}}
- "What is Lambda?" → {{"intent_type":"question","aws_service":"lambda","action":null,"entities":["Lambda"],"confidence":0.8,"requires_aws_action":false,"parameters":{{}}}}

JSON:"""

            response = await self._call_groq(classification_prompt)
            
            # Parse JSON response
            try:
                intent_data = json.loads(response)
                
                # Validate and enhance the classification
                intent_data = self._enhance_classification(message, intent_data)
                
                return intent_data
                
            except json.JSONDecodeError:
                # Fallback classification
                return self._fallback_classification(message)
                
        except Exception as e:
            logger.error(f"Error in intent classification: {str(e)}")
            return self._fallback_classification(message)

    async def _generate_response(self, message: str, intent_result: Dict, context: List[Dict]) -> Dict[str, Any]:
        """
        Generate appropriate response based on intent classification
        """
        intent_type = intent_result.get('intent_type')
        
        if intent_type == 'aws_command' and intent_result.get('requires_aws_action'):
            return await self._handle_aws_command(message, intent_result, context)
        elif intent_type == 'question':
            return await self._handle_question(message, intent_result, context)
        elif intent_type == 'analysis':
            return await self._handle_analysis(message, intent_result, context)
        elif intent_type == 'greeting':
            return await self._handle_greeting(message, intent_result, context)
        elif intent_type == 'help':
            return await self._handle_help(message, intent_result, context)
        else:
            return await self._handle_general(message, intent_result, context)

    async def _handle_aws_command(self, message: str, intent_result: Dict, context: List[Dict]) -> Dict[str, Any]:
        """
        Handle AWS command execution requests
        """
        aws_service = intent_result.get('aws_service')
        action = intent_result.get('action')
        parameters = intent_result.get('parameters', {})
        
        # Validate AWS credentials first
        credentials_check = await self._check_aws_credentials()
        if not credentials_check['valid']:
            return {
                'type': 'aws_error',
                'message': '🔐 AWS credentials are not configured or invalid. Please set up your AWS credentials first.',
                'action_required': 'setup_credentials',
                'service': aws_service,
                'original_intent': intent_result
            }
        
        # Return command execution request
        return {
            'type': 'aws_command',
            'message': f'🚀 I understand you want to {action} {aws_service} resources. Let me execute that for you...',
            'service': aws_service,
            'action': action,
            'parameters': parameters,
            'intent_data': intent_result,
            'requires_execution': True
        }

    async def _handle_question(self, message: str, intent_result: Dict, context: List[Dict]) -> Dict[str, Any]:
        """
        Handle general AWS knowledge questions
        """
        aws_service = intent_result.get('aws_service')
        
        question_prompt = f"""You are {self.bot_name}, a senior AWS Solutions Architect with 10+ years experience. Answer this question with technical depth and practical insights.

QUESTION: "{message}"
SERVICE: {aws_service or "General AWS"}
CONTEXT: {self._format_context(context[-2:]) if context else "No previous context"}

GUIDELINES:
- Provide accurate, detailed technical information
- Include AWS best practices and real-world considerations
- Mention pricing implications when relevant
- Suggest practical next steps or related services
- Use professional yet approachable tone
- Keep response focused and actionable (max 3 paragraphs)
- Use relevant emojis sparingly for emphasis

FORMAT:
🔍 [Direct Answer]
💡 [Best Practices/Considerations]
🚀 [Suggested Actions/Related Topics]"""

        ai_response = await self._call_groq(question_prompt)
        
        return {
            'type': 'answer',
            'message': ai_response,
            'service': aws_service,
            'intent_data': intent_result
        }

    async def _handle_analysis(self, message: str, intent_result: Dict, context: List[Dict]) -> Dict[str, Any]:
        """
        Handle log analysis and audit requests
        """
        return {
            'type': 'analysis',
            'message': '📊 Analysis features are coming soon! I\'ll be able to analyze CloudTrail logs, security events, and provide insights about your AWS usage.',
            'service': intent_result.get('aws_service'),
            'intent_data': intent_result,
            'future_feature': True
        }

    async def _handle_greeting(self, message: str, intent_result: Dict, context: List[Dict]) -> Dict[str, Any]:
        """
        Handle greetings and introductions
        """
        greeting_responses = [
            f"👋 Hello! I'm {self.bot_name}, your expert AWS Solutions Architect. Ready to optimize your cloud infrastructure!",
            f"🚀 Hi there! I'm {self.bot_name}, your AWS assistant with deep cloud expertise. Let's build something amazing!",
            f"🌟 Welcome! I'm {self.bot_name}, here to help you master AWS. From EC2 to architecture guidance - I've got you covered!"
        ]
        
        import random
        response = random.choice(greeting_responses)
        
        return {
            'type': 'greeting',
            'message': response,
            'intent_data': intent_result,
            'suggestions': [
                'Show me my EC2 instances',
                'Launch a new t2.micro instance',
                'What is AWS Lambda?',
                'Help me get started'
            ]
        }

    async def _handle_help(self, message: str, intent_result: Dict, context: List[Dict]) -> Dict[str, Any]:
        """
        Handle help requests
        """
        help_message = f"""🤖 **{self.bot_name} - Your Expert AWS Assistant**

I'm a senior AWS Solutions Architect ready to help you manage your cloud infrastructure!

**⚡ What I Can Do:**

**🖥️ EC2 Management:**
• "Launch a t2.micro instance" 
• "List my EC2 instances"
• "Start/stop/terminate instance-id"

**❓ AWS Expertise:**
• "What's the difference between EBS and Instance Store?"
• "EC2 pricing models explained"
• "VPC best practices for production"

**🔧 Real Commands I Execute:**
• Instance lifecycle management
• Resource listing and monitoring
• AWS service recommendations

**💡 Pro Tips:**
• Use specific instance types: "Launch t3.medium instance"
• Ask about cost optimization strategies
• Request architecture guidance for your use case

**📊 Coming Soon:**
CloudTrail analysis, S3 operations, Lambda management

Ready to optimize your AWS infrastructure? Ask me anything! 🚀"""
        
        return {
            'type': 'help',
            'message': help_message,
            'intent_data': intent_result
        }

    async def _handle_general(self, message: str, intent_result: Dict, context: List[Dict]) -> Dict[str, Any]:
        """
        Handle general conversation
        """
        general_prompt = f"""You are {self.bot_name}, an expert AWS Solutions Architect. The user said: "{message}"

This isn't directly AWS-related, but respond helpfully while steering toward cloud/AWS topics.

RESPONSE STYLE:
- Acknowledge their message appropriately
- Briefly connect it to AWS/cloud if possible
- Offer specific AWS help
- Stay professional but friendly
- Keep it concise (2-3 sentences max)

EXAMPLE: "That's interesting! While I specialize in AWS cloud architecture, I'd love to help you with your infrastructure needs. Whether it's EC2, storage solutions, or cost optimization - what AWS challenges can I assist with today?"
"""
        
        ai_response = await self._call_groq(general_prompt)
        
        return {
            'type': 'general',
            'message': ai_response,
            'intent_data': intent_result
        }

    async def _call_groq(self, prompt: str) -> str:
        """
        Make API call to Groq
        """
        try:
            if not self.client:
                return "AI service not available. Please configure Groq API key."
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Groq API call failed: {str(e)}")
            return f"Sorry, I'm having trouble connecting to my AI service. Error: {str(e)}"

    def _enhance_classification(self, message: str, intent_data: Dict) -> Dict[str, Any]:
        """
        Enhance AI classification with rule-based improvements
        """
        message_lower = message.lower()
        
        # Extract EC2 instance IDs using regex
        instance_id_pattern = r'i-[0-9a-f]{17}'
        instance_ids = re.findall(instance_id_pattern, message)
        if instance_ids:
            # Add instance ID to parameters
            if 'parameters' not in intent_data:
                intent_data['parameters'] = {}
            intent_data['parameters']['instance_id'] = instance_ids[0]  # Use first found instance ID
            
            # If we found an instance ID, it's likely an EC2 command
            if not intent_data.get('aws_service'):
                intent_data['aws_service'] = 'ec2'
            
            # Add to entities
            if 'entities' not in intent_data:
                intent_data['entities'] = []
            intent_data['entities'].extend(instance_ids)
        
        # Extract instance types (t2.micro, t3.small, etc.)
        instance_type_pattern = r'\b[a-z][0-9]+[a-z]*\.[a-z]+\b'
        instance_types = re.findall(instance_type_pattern, message_lower)
        if instance_types:
            if 'parameters' not in intent_data:
                intent_data['parameters'] = {}
            intent_data['parameters']['instance_type'] = instance_types[0]
            
            if 'entities' not in intent_data:
                intent_data['entities'] = []
            intent_data['entities'].extend(instance_types)
        
        # Map "launch" to "create" for EC2
        if intent_data.get('action') == 'launch' and intent_data.get('aws_service') == 'ec2':
            intent_data['action'] = 'create'
        
        # Enhance AWS service detection
        if not intent_data.get('aws_service'):
            for service, keywords in self.aws_services.items():
                if any(keyword in message_lower for keyword in keywords):
                    intent_data['aws_service'] = service
                    break
        
        # Enhance action detection
        if not intent_data.get('action'):
            for action, keywords in self.action_patterns.items():
                if any(keyword in message_lower for keyword in keywords):
                    intent_data['action'] = action
                    break
        
        # Special case: if we found instance IDs, likely it's a state change operation
        if instance_ids and not intent_data.get('action'):
            # Look for state change keywords
            if any(word in message_lower for word in ['start', 'run', 'boot']):
                intent_data['action'] = 'start'
            elif any(word in message_lower for word in ['stop', 'halt', 'shutdown']):
                intent_data['action'] = 'stop'
            elif any(word in message_lower for word in ['terminate', 'delete', 'destroy']):
                intent_data['action'] = 'terminate'
            elif any(word in message_lower for word in ['reboot', 'restart']):
                intent_data['action'] = 'reboot'
        
        # Boost confidence for clear AWS commands
        if intent_data.get('aws_service') and intent_data.get('action'):
            intent_data['confidence'] = max(intent_data.get('confidence', 0), 0.8)
        
        # Extra confidence boost if we extracted specific AWS identifiers
        if instance_ids or instance_types:
            intent_data['confidence'] = max(intent_data.get('confidence', 0), 0.9)
        
        return intent_data

    def _fallback_classification(self, message: str) -> Dict[str, Any]:
        """
        Fallback classification using simple rules
        """
        message_lower = message.lower()
        
        # Priority 1: Check for AWS commands (highest priority)
        aws_command_patterns = [
            ('launch', 'instance'),
            ('create', 'instance'),
            ('deploy', 'instance'),
            ('start', 'instance'),
            ('list', 'instance'),
            ('show', 'instance'),
            ('stop', 'instance'),
            ('terminate', 'instance'),
            ('reboot', 'instance')
        ]
        
        for pattern in aws_command_patterns:
            if all(word in message_lower for word in pattern):
                action = pattern[0]
                if action in ['launch', 'create', 'deploy']:
                    action = 'create'
                
                return {
                    'intent_type': 'aws_command',
                    'aws_service': 'ec2',
                    'action': action,
                    'entities': [],
                    'confidence': 0.85,
                    'requires_aws_action': True,
                    'parameters': {}
                }
        
        # Check if message contains "instance" - likely an EC2 command
        if 'instance' in message_lower:
            # Determine action based on keywords
            if any(word in message_lower for word in ['launch', 'create', 'deploy', 'make', 'new']):
                action = 'create'
            elif any(word in message_lower for word in ['list', 'show', 'display', 'get']):
                action = 'list'
            elif any(word in message_lower for word in ['start', 'run', 'boot']):
                action = 'start'
            elif any(word in message_lower for word in ['stop', 'halt', 'shutdown']):
                action = 'stop'
            elif any(word in message_lower for word in ['terminate', 'delete', 'destroy']):
                action = 'terminate'
            else:
                action = 'list'  # Default to listing
            
            return {
                'intent_type': 'aws_command',
                'aws_service': 'ec2',
                'action': action,
                'entities': [],
                'confidence': 0.8,
                'requires_aws_action': True,
                'parameters': {}
            }
        
        # Check for greetings
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon']
        if any(greeting in message_lower for greeting in greetings):
            return {
                'intent_type': 'greeting',
                'aws_service': None,
                'action': None,
                'entities': [],
                'confidence': 0.7,
                'requires_aws_action': False,
                'parameters': {}
            }
        
        # Check for help requests
        help_keywords = ['help', 'how', 'what can you do', 'commands']
        if any(keyword in message_lower for keyword in help_keywords):
            return {
                'intent_type': 'help',
                'aws_service': None,
                'action': None,
                'entities': [],
                'confidence': 0.7,
                'requires_aws_action': False,
                'parameters': {}
            }
        
        # Default classification
        return {
            'intent_type': 'general',
            'aws_service': None,
            'action': None,
            'entities': [],
            'confidence': 0.5,
            'requires_aws_action': False,
            'parameters': {}
        }

    async def _check_aws_credentials(self) -> Dict[str, bool]:
        """
        Quick check if AWS credentials are configured
        """
        try:
            from decouple import config
            # Check if AWS credentials are configured in environment
            aws_access_key = config('AWS_ACCESS_KEY_ID', default='')
            aws_secret_key = config('AWS_SECRET_ACCESS_KEY', default='')
            
            if aws_access_key and aws_secret_key and aws_access_key != 'your_aws_access_key_here':
                return {'valid': True}
            else:
                return {'valid': False}
        except:
            return {'valid': False}

    def _get_conversation_context(self, user_id: str, conversation_id: str = None) -> List[Dict]:
        """
        Get conversation context for user
        """
        key = f"{user_id}_{conversation_id}" if conversation_id else user_id
        return self.conversation_contexts.get(key, [])

    def _update_conversation_context(self, user_id: str, conversation_id: str, message: str, response: Dict):
        """
        Update conversation context
        """
        key = f"{user_id}_{conversation_id}" if conversation_id else user_id
        
        if key not in self.conversation_contexts:
            self.conversation_contexts[key] = []
        
        # Add new exchange
        self.conversation_contexts[key].append({
            'timestamp': datetime.utcnow().isoformat(),
            'user_message': message,
            'bot_response': response,
            'intent': response.get('intent_data', {})
        })
        
        # Keep only last N conversations
        if len(self.conversation_contexts[key]) > self.max_context:
            self.conversation_contexts[key] = self.conversation_contexts[key][-self.max_context:]

    def _format_context(self, context: List[Dict]) -> str:
        """
        Format conversation context for AI prompts
        """
        if not context:
            return "No previous context"
        
        formatted = []
        for exchange in context:
            formatted.append(f"User: {exchange['user_message']}")
            formatted.append(f"Assistant: {exchange['bot_response'].get('message', '')}")
        
        return "\n".join(formatted)

# Global instance
groq_service = GroqService()
