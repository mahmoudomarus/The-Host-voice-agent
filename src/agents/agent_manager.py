import os
import json
import time
from pathlib import Path

class AgentManager:
    """
    Manages multiple AI agents with distinct personalities and knowledge.
    Coordinates with LLM, TTS, and turn-taking managers.
    """
    
    def __init__(self, config_path, llm_manager, tts_manager, active_agents=None):
        """
        Initialize the Agent Manager with configuration and dependencies.
        
        Args:
            config_path: Path to the agent configuration file
            llm_manager: Instance of LLMManager
            tts_manager: Instance of TTSManager
            active_agents: Optional list of agent IDs to activate (None for all)
        """
        self.config_path = config_path
        self.llm_manager = llm_manager
        self.tts_manager = tts_manager
        self.active_agents = active_agents
        self.load_config()
        
        # Conversation history for each agent
        self.conversation_history = {agent['id']: [] for agent in self.agents}
        
    def load_config(self):
        """Load agent configuration from file"""
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        # Get all agents from config
        all_agents = config.get('agents', [])
        
        # Filter for active agents if specified
        if self.active_agents is not None:
            self.agents = [agent for agent in all_agents if agent['id'] in self.active_agents]
            if len(self.agents) == 0:
                print(f"Warning: No matching agents found for {self.active_agents}")
                # Fall back to all agents if none match
                self.agents = all_agents
        else:
            self.agents = all_agents
            
        print(f"Loaded {len(self.agents)} agents")
        
        # Store all other config properties
        self.prompt_templates = config.get('promptTemplates', {})
        self.max_history_length = config.get('maxHistoryLength', 10)
        
    def get_agent_by_id(self, agent_id):
        """Get agent data by ID"""
        for agent in self.agents:
            if agent['id'] == agent_id:
                return agent
        return None
    
    def add_to_conversation(self, speaker, text, is_audience=False):
        """
        Add a message to the conversation history for all agents.
        
        Args:
            speaker: ID or name of the speaker
            text: The message text
            is_audience: Whether the speaker is an audience member
        """
        # Format the message
        if is_audience:
            speaker_name = "Audience Member"
        else:
            agent = self.get_agent_by_id(speaker)
            speaker_name = agent['name'] if agent else speaker
        
        message = {
            'speaker': speaker_name,
            'text': text,
            'timestamp': time.time(),
            'is_audience': is_audience
        }
        
        # Add to each agent's history
        for agent_id in self.conversation_history:
            self.conversation_history[agent_id].append(message)
            
            # Trim history if needed
            if len(self.conversation_history[agent_id]) > self.max_history_length:
                self.conversation_history[agent_id] = self.conversation_history[agent_id][-self.max_history_length:]
    
    def generate_agent_response(self, agent_id, prompt=None):
        """
        Generate a response from an agent based on conversation history.
        
        Args:
            agent_id: ID of the agent
            prompt: Optional specific prompt to respond to
            
        Returns:
            Generated response text
        """
        agent = self.get_agent_by_id(agent_id)
        if not agent:
            print(f"Agent {agent_id} not found")
            return None
        
        # Build the system prompt
        system_prompt = self._build_system_prompt(agent)
        
        # Build the conversation history prompt
        history_prompt = self._build_history_prompt(agent_id)
        
        # Combine with specific prompt if provided
        if prompt:
            user_prompt = f"{history_prompt}\n\nPlease respond to: {prompt}"
        else:
            user_prompt = f"{history_prompt}\n\nPlease continue the conversation as {agent['name']}."
        
        # Generate response from LLM
        response = self.llm_manager.generate_response(
            prompt=user_prompt,
            system_prompt=system_prompt,
            agent_id=agent_id
        )
        
        # Add the response to conversation history
        self.add_to_conversation(agent_id, response)
        
        return response
    
    def speak_agent_response(self, agent_id, text=None, output_path=None):
        """
        Generate speech for an agent response.
        
        Args:
            agent_id: ID of the agent
            text: Text to speak (if None, generates a new response)
            output_path: Optional path to save the audio file
            
        Returns:
            Path to the generated audio file or None if streaming
        """
        if text is None:
            text = self.generate_agent_response(agent_id)
        
        if not text:
            return None
        
        # Generate speech using TTS manager
        return self.tts_manager.generate_speech(text, agent_id, output_path)
    
    def _build_system_prompt(self, agent):
        """Build system prompt for an agent based on their profile"""
        template = self.prompt_templates.get('system', "You are {name}, {role}.")
        
        # Replace placeholders with agent data
        prompt = template.format(
            name=agent['name'],
            role=agent.get('role', ''),
            background=agent.get('background', ''),
            personality=agent.get('personality', ''),
            expertise=agent.get('expertise', ''),
            speaking_style=agent.get('speakingStyle', '')
        )
        
        return prompt
    
    def _build_history_prompt(self, agent_id):
        """Build conversation history prompt for an agent"""
        history = self.conversation_history.get(agent_id, [])
        if not history:
            return "This is the start of a conversation."
        
        # Format conversation history
        formatted_history = []
        for msg in history:
            formatted_history.append(f"{msg['speaker']}: {msg['text']}")
        
        return "Conversation history:\n" + "\n".join(formatted_history)
