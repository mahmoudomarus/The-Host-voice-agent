import os
import sys
import json
import time
import threading
import argparse
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import managers
from tts.tts_manager import TTSManager
from stt.stt_manager import STTManager
from llm.llm_manager import LLMManager
from audio.audio_manager import AudioManager
from turn_taking.turn_manager import TurnManager
from agents.agent_manager import AgentManager

# Import for UI (optional)
try:
    from ui.app import create_app, socketio
    HAS_UI = True
except ImportError:
    HAS_UI = False

class TwitterSpacesAgentSystem:
    """
    Main application for the multi-voice agent system for Twitter Spaces.
    Coordinates all components and manages the conversation flow.
    """
    
    def __init__(self, config_dir='./config', active_agents=None):
        """
        Initialize the system with configuration.
        
        Args:
            config_dir: Directory containing configuration files
            active_agents: List of agent IDs to activate (None for all)
        """
        self.config_dir = Path(config_dir)
        self.running = False
        self.active_agents = active_agents
        self.initialize_components()
        
    def initialize_components(self):
        """Initialize all system components"""
        print("Initializing Twitter Spaces Agent System...")
        
        # Initialize managers
        self.audio_manager = AudioManager(self.config_dir / 'audio_config.json')
        self.tts_manager = TTSManager(self.config_dir / 'tts_config.json')
        self.stt_manager = STTManager(self.config_dir / 'stt_config.json')
        self.llm_manager = LLMManager(self.config_dir / 'llm_config.json')
        
        # Initialize agent manager with active_agents filter
        self.agent_manager = AgentManager(
            self.config_dir / 'agent_config.json',
            self.llm_manager,
            self.tts_manager,
            active_agents=self.active_agents
        )
        
        # Initialize turn manager with only active agents
        self.turn_manager = TurnManager(
            self.config_dir / 'agent_config.json',
            active_agents=self.active_agents
        )
        
        print(f"System initialized with {len(self.agent_manager.agents)} active agents")
    
    def start(self):
        """Start the system"""
        if self.running:
            print("System is already running")
            return
        
        print("Starting Twitter Spaces Agent System...")
        self.running = True
        
        # Start STT with callback
        self.stt_manager.start_listening(self._on_transcribe)
        
        # Main loop
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Interrupted by user")
            self.stop()
    
    def stop(self):
        """Stop the system"""
        if not self.running:
            return
        
        print("Stopping Twitter Spaces Agent System...")
        self.running = False
        
        # Stop components
        self.stt_manager.stop_listening()
        self.audio_manager.cleanup()
        
        print("System stopped")
    
    def _on_transcribe(self, text):
        """
        Handle transcribed text from STT.
        
        Args:
            text: Transcribed text
        """
        print(f"Transcribed: {text}")
        
        # Determine if this is from an agent or audience
        # This is a simplified implementation - in a real system,
        # you would need to track who is speaking
        is_audience = True  # Assume all transcribed text is from audience
        
        if is_audience:
            # Add to conversation history
            self.agent_manager.add_to_conversation("audience", text, is_audience=True)
            
            # Check if current speaker should stop
            if self.turn_manager.current_speaker:
                self.turn_manager.stop_speaking()
            
            # Determine which agent should respond
            next_speaker = self.turn_manager.get_next_speaker(text, audience_active=False)
            
            if next_speaker:
                self._agent_speak(next_speaker)
    
    def _agent_speak(self, agent_id):
        """
        Have an agent generate a response and speak.
        
        Args:
            agent_id: ID of the agent
        """
        # Start the speaking turn
        if not self.turn_manager.start_speaking(agent_id):
            return
        
        # Generate response
        response = self.agent_manager.generate_agent_response(agent_id)
        
        if response:
            print(f"Agent {agent_id}: {response}")
            
            # Generate speech
            audio_path = self.agent_manager.speak_agent_response(agent_id, response)
            
            if audio_path:
                # Play the audio
                self.audio_manager.play_audio(audio_path, blocking=True)
        
        # End the speaking turn
        self.turn_manager.stop_speaking(agent_id)
        
        # Check if another agent should speak next
        next_speaker = self.turn_manager.get_next_speaker()
        if next_speaker:
            self._agent_speak(next_speaker)
    
    def test_agents(self):
        """Test agent responses without audio"""
        for agent in self.agent_manager.agents:
            agent_id = agent['id']
            print(f"\nTesting agent: {agent['name']} ({agent_id})")
            
            response = self.agent_manager.generate_agent_response(
                agent_id, 
                "Please introduce yourself and your expertise."
            )
            
            print(f"Response: {response}")
    
    def test_audio_devices(self):
        """Test audio devices"""
        print("Available audio devices:")
        devices = self.audio_manager.list_audio_devices()
        
        for device in devices:
            print(f"Index: {device['index']}")
            print(f"Name: {device['name']}")
            print(f"Input channels: {device['input_channels']}")
            print(f"Output channels: {device['output_channels']}")
            print(f"Default sample rate: {device['default_sample_rate']}")
            print()
    
    def get_agent_list(self):
        """Get list of all available agents"""
        return [
            {"id": agent["id"], "name": agent["name"], "role": agent["role"]}
            for agent in self.agent_manager.agents
        ]

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Twitter Spaces Agent System')
    parser.add_argument('--config', default='./config', help='Configuration directory')
    parser.add_argument('--test-agents', action='store_true', help='Test agent responses')
    parser.add_argument('--test-audio', action='store_true', help='Test audio devices')
    parser.add_argument('--ui', action='store_true', help='Start with web UI')
    parser.add_argument('--agent', help='Run with a single agent (specify ID)')
    parser.add_argument('--agents', help='Run with specific agents (comma-separated IDs)')
    parser.add_argument('--all-agents', action='store_true', help='Run with all available agents')
    
    args = parser.parse_args()
    
    # Determine active agents
    active_agents = None
    if args.agent:
        active_agents = [args.agent]
    elif args.agents:
        active_agents = args.agents.split(',')
    elif args.all_agents:
        active_agents = None  # None means all agents
    
    # Initialize system
    system = TwitterSpacesAgentSystem(config_dir=args.config, active_agents=active_agents)
    
    if args.test_agents:
        system.test_agents()
    elif args.test_audio:
        system.test_audio_devices()
    elif args.ui and HAS_UI:
        # Start the UI with the system
        app = create_app(system)
        print("Starting web UI on http://localhost:5000")
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    else:
        try:
            system.start()
        except KeyboardInterrupt:
            pass
        finally:
            system.stop()

if __name__ == '__main__':
    main()
