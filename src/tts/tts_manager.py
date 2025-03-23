import os
import json
import time
import random
from pathlib import Path

class TTSManager:
    """
    Manages text-to-speech conversion for multiple agents with different voices.
    Supports both ChatTTS and XTTS engines.
    """
    
    def __init__(self, config_path):
        """
        Initialize the TTS Manager with configuration.
        
        Args:
            config_path: Path to the TTS configuration file
        """
        self.config_path = config_path
        self.load_config()
        self.initialize_engines()
        
    def load_config(self):
        """Load TTS configuration from file"""
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
        
        self.primary_engine = self.config.get('primaryEngine', 'chattts')
        self.secondary_engine = self.config.get('secondaryEngine', 'xtts')
        self.voice_profiles = self.config.get('voiceProfiles', {})
        
    def initialize_engines(self):
        """Initialize TTS engines based on configuration"""
        self.engines = {}
        
        # Initialize primary engine
        if self.primary_engine == 'chattts':
            try:
                from chattts import ChatTTS
                self.engines['chattts'] = ChatTTS()
                print("ChatTTS engine initialized successfully")
            except ImportError:
                print("Warning: ChatTTS not installed. Run 'pip install chattts'")
        
        # Initialize secondary engine
        if self.secondary_engine == 'xtts':
            try:
                # This is a placeholder for the actual XTTS implementation
                # In a real implementation, you would use the XTTS API client
                self.engines['xtts'] = None
                print("XTTS engine placeholder created (actual implementation needed)")
            except ImportError:
                print("Warning: XTTS not installed. Run 'pip install xtts-api-client'")
    
    def add_interjections_and_pauses(self, text, agent_id):
        """
        Add interjections and pauses to the text based on agent profile.
        
        Args:
            text: The text to modify
            agent_id: The ID of the agent
            
        Returns:
            Modified text with interjections and pause markers
        """
        if agent_id not in self.voice_profiles:
            return text
        
        profile = self.voice_profiles[agent_id]
        modified_text = text
        
        # Add interjections
        if random.random() < profile.get('interjectionFrequency', 0):
            interjections = profile.get('interjections', ['um'])
            interjection = random.choice(interjections)
            modified_text = f"{interjection}, {modified_text}"
        
        # Add pauses (implementation depends on the TTS engine's pause syntax)
        # This is a simplified implementation
        sentences = modified_text.split('. ')
        if len(sentences) > 1 and random.random() < profile.get('pauseFrequency', 0):
            pause_idx = random.randint(0, len(sentences) - 2)
            pause_duration = profile.get('pauseDuration', {}).get('medium', 500)
            pause_marker = f"<break time='{pause_duration}ms'/>"
            sentences[pause_idx] = f"{sentences[pause_idx]}.{pause_marker} "
            modified_text = '. '.join(sentences)
        
        return modified_text
    
    def generate_speech(self, text, agent_id, output_path=None):
        """
        Generate speech for the given text using the appropriate voice for the agent.
        
        Args:
            text: The text to convert to speech
            agent_id: The ID of the agent
            output_path: Optional path to save the audio file
            
        Returns:
            Path to the generated audio file or None if streaming
        """
        if agent_id not in self.voice_profiles:
            print(f"Warning: No voice profile found for agent {agent_id}")
            return None
        
        profile = self.voice_profiles[agent_id]
        
        # Add interjections and pauses
        modified_text = self.add_interjections_and_pauses(text, agent_id)
        
        # Determine which engine to use
        engine_name = self.primary_engine
        if profile.get('preferredEngine'):
            engine_name = profile.get('preferredEngine')
        
        # Generate speech using the selected engine
        if engine_name == 'chattts' and 'chattts' in self.engines:
            return self._generate_with_chattts(modified_text, profile, output_path)
        elif engine_name == 'xtts' and 'xtts' in self.engines:
            return self._generate_with_xtts(modified_text, profile, output_path)
        else:
            print(f"Warning: Engine {engine_name} not available")
            return None
    
    def _generate_with_chattts(self, text, profile, output_path=None):
        """Generate speech using ChatTTS"""
        try:
            # If no output path is provided, generate a temporary one
            if not output_path:
                output_dir = Path("./data/audio")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(output_dir / f"{profile['name']}_{int(time.time())}.wav")
            
            # Generate speech
            self.engines['chattts'].tts(
                text=text,
                speaker=profile['name'],
                output_path=output_path
            )
            
            print(f"Generated speech saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"Error generating speech with ChatTTS: {e}")
            return None
    
    def _generate_with_xtts(self, text, profile, output_path=None):
        """Generate speech using XTTS"""
        # This is a placeholder for the actual XTTS implementation
        print("XTTS generation not implemented yet")
        return None
