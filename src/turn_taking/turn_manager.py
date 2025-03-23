import json
import time
import threading
import random

class TurnManager:
    """
    Manages turn-taking between multiple agents and audience members.
    Uses VAD and keyword detection to determine when turns should change.
    """
    
    def __init__(self, agent_config_path, active_agents=None):
        """
        Initialize the Turn Manager with agent configuration.
        
        Args:
            agent_config_path: Path to the agent configuration file
            active_agents: Optional list of agent IDs to activate (None for all)
        """
        self.agent_config_path = agent_config_path
        self.active_agents = active_agents
        self.load_config()
        
        # Current speaker state
        self.current_speaker = None
        self.speaking_start_time = 0
        self.is_audience_speaking = False
        
        # Turn history
        self.turn_history = []
        
        # Last speaking time for each agent
        self.last_spoke = {agent['id']: 0 for agent in self.agents}
        
        # Lock for thread safety
        self.lock = threading.RLock()
    
    def load_config(self):
        """Load agent configuration from file"""
        with open(self.agent_config_path, 'r') as f:
            config = json.load(f)
        
        # Get all agents from config
        all_agents = config.get('agents', [])
        
        # Filter for active agents if specified
        if self.active_agents is not None:
            self.agents = [agent for agent in all_agents if agent['id'] in self.active_agents]
            if len(self.agents) == 0:
                print(f"Warning: No matching agents found for turn taking with {self.active_agents}")
                # Fall back to all agents if none match
                self.agents = all_agents
        else:
            self.agents = all_agents
        
        # Extract keywords for each agent
        self.keywords = {}
        for agent in self.agents:
            self.keywords[agent['id']] = agent.get('keywords', [])
        
        # Get turn-taking rules
        self.rules = config.get('turnTakingRules', {})
        self.max_turn_duration = self.rules.get('maxTurnDuration', 30)
        self.min_time_between_turns = self.rules.get('minTimeBetweenTurns', 2)
        self.interruption_threshold = self.rules.get('interruptionThreshold', 0.8)
    
    def get_agent_by_id(self, agent_id):
        """Get agent data by ID"""
        for agent in self.agents:
            if agent['id'] == agent_id:
                return agent
        return None
    
    def start_speaking(self, speaker_id, is_audience=False):
        """
        Mark that a speaker has started their turn.
        
        Args:
            speaker_id: ID of the speaker (agent ID or audience member ID)
            is_audience: Whether the speaker is an audience member
        """
        with self.lock:
            if self.current_speaker:
                # Someone is already speaking
                return False
            
            self.current_speaker = speaker_id
            self.speaking_start_time = time.time()
            self.is_audience_speaking = is_audience
            
            # Record turn start
            self.turn_history.append({
                'speaker': speaker_id,
                'is_audience': is_audience,
                'start_time': self.speaking_start_time,
                'end_time': None
            })
            
            return True
    
    def stop_speaking(self, speaker_id=None):
        """
        Mark that a speaker has finished their turn.
        
        Args:
            speaker_id: ID of the speaker (if None, stops current speaker)
        
        Returns:
            True if the speaker was stopped, False otherwise
        """
        with self.lock:
            if not self.current_speaker:
                # No one is speaking
                return False
            
            if speaker_id and speaker_id != self.current_speaker:
                # Not the current speaker
                return False
            
            # Update last spoke time if it's an agent
            if not self.is_audience_speaking:
                self.last_spoke[self.current_speaker] = time.time()
            
            # Update turn history
            for turn in reversed(self.turn_history):
                if turn['speaker'] == self.current_speaker and turn['end_time'] is None:
                    turn['end_time'] = time.time()
                    turn['duration'] = turn['end_time'] - turn['start_time']
                    break
            
            # Reset current speaker
            self.current_speaker = None
            self.is_audience_speaking = False
            
            return True
    
    def get_next_speaker(self, transcript=None, audience_active=False):
        """
        Determine which agent should speak next.
        
        Args:
            transcript: Recent transcript to analyze for keywords
            audience_active: Whether an audience member is requesting to speak
            
        Returns:
            ID of the next agent to speak, or None if no agent should speak
        """
        with self.lock:
            if self.current_speaker:
                # Someone is already speaking
                return None
            
            if audience_active:
                # Audience member wants to speak, let them
                return None
            
            # Determine next speaker based on transcript and turn history
            return self._determine_next_speaker(transcript)
    
    def _determine_next_speaker(self, transcript=None):
        """
        Internal method to determine the next speaker based on various factors.
        
        Args:
            transcript: Recent transcript to analyze
            
        Returns:
            ID of the next agent to speak
        """
        # If no active agents, return None
        if not self.agents:
            return None
            
        # If we have a transcript, check for explicit addressing or keywords
        if transcript:
            # Check for explicit addressing (e.g., "Alex, what do you think?")
            for agent in self.agents:
                if agent['name'].lower() in transcript.lower():
                    return agent['id']
            
            # Check for keywords
            matching_agents = []
            for agent_id, keywords in self.keywords.items():
                for keyword in keywords:
                    if keyword.lower() in transcript.lower():
                        matching_agents.append((agent_id, self.last_spoke[agent_id]))
            
            # If we found matching agents, select the one who hasn't spoken in the longest time
            if matching_agents:
                matching_agents.sort(key=lambda x: x[1])
                return matching_agents[0][0]
        
        # If no explicit addressing or keywords, use round-robin
        # Select the agent who hasn't spoken in the longest time
        agent_times = [(agent['id'], self.last_spoke[agent['id']]) for agent in self.agents]
        agent_times.sort(key=lambda x: x[1])
        return agent_times[0][0]
    
    def should_interrupt(self, speaker_id, transcript=None):
        """
        Determine if an agent should interrupt the current speaker.
        
        Args:
            speaker_id: ID of the agent considering interruption
            transcript: Recent transcript to analyze
            
        Returns:
            True if the agent should interrupt, False otherwise
        """
        with self.lock:
            if not self.current_speaker:
                # No one is speaking
                return False
            
            if not self.is_audience_speaking:
                # Don't interrupt other agents
                return False
            
            # Check if this agent is explicitly addressed in the transcript
            agent = self.get_agent_by_id(speaker_id)
            if agent and transcript and agent['name'].lower() in transcript.lower():
                return True
            
            # Check for urgent keywords that would trigger this agent
            if speaker_id in self.keywords and transcript:
                urgent_keywords = [k for k in self.keywords[speaker_id] if k.startswith('!')]
                for keyword in urgent_keywords:
                    if keyword[1:].lower() in transcript.lower():
                        return True
            
            # Otherwise, don't interrupt
            return False
    
    def get_turn_statistics(self):
        """
        Get statistics about turn-taking.
        
        Returns:
            Dictionary with turn statistics
        """
        with self.lock:
            if not self.turn_history:
                return {
                    'total_turns': 0,
                    'agent_turns': 0,
                    'audience_turns': 0,
                    'avg_turn_duration': 0,
                    'turns_by_agent': {}
                }
            
            # Count completed turns
            completed_turns = [t for t in self.turn_history if t['end_time'] is not None]
            total_turns = len(completed_turns)
            agent_turns = len([t for t in completed_turns if not t['is_audience']])
            audience_turns = len([t for t in completed_turns if t['is_audience']])
            
            # Calculate average turn duration
            if completed_turns:
                avg_duration = sum(t['duration'] for t in completed_turns) / total_turns
            else:
                avg_duration = 0
            
            # Count turns by agent
            turns_by_agent = {}
            for agent in self.agents:
                agent_id = agent['id']
                turns_by_agent[agent_id] = len([t for t in completed_turns if t['speaker'] == agent_id])
            
            return {
                'total_turns': total_turns,
                'agent_turns': agent_turns,
                'audience_turns': audience_turns,
                'avg_turn_duration': avg_duration,
                'turns_by_agent': turns_by_agent
            }
