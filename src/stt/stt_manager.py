import os
import json
import time
import threading
from pathlib import Path

class STTManager:
    """
    Manages speech-to-text conversion with voice activity detection.
    Uses RealtimeSTT as the primary engine.
    """
    
    def __init__(self, config_path):
        """
        Initialize the STT Manager with configuration.
        
        Args:
            config_path: Path to the STT configuration file
        """
        self.config_path = config_path
        self.load_config()
        self.initialize_engine()
        self.is_listening = False
        self.callback = None
        self.listen_thread = None
        
    def load_config(self):
        """Load STT configuration from file"""
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
        
        self.engine_name = self.config.get('engine', 'realtimestt')
        self.fallback_engine = self.config.get('fallbackEngine', 'whisper')
        self.vad_settings = self.config.get('vadSettings', {})
        self.realtimestt_settings = self.config.get('realtimeSTTSettings', {})
        
    def initialize_engine(self):
        """Initialize STT engine based on configuration"""
        self.engine = None
        
        # Initialize primary engine
        if self.engine_name == 'realtimestt':
            try:
                from realtimestt import RealtimeSTT
                
                # Create engine with VAD settings
                self.engine = RealtimeSTT(
                    model=self.realtimestt_settings.get('model', 'faster-whisper-medium'),
                    language=self.realtimestt_settings.get('language', 'en'),
                    vad_mode=self.realtimestt_settings.get('vadMode', 'silero'),
                    vad_sensitivity=self.realtimestt_settings.get('vadSensitivity', 0.8)
                )
                
                print("RealtimeSTT engine initialized successfully")
            except ImportError:
                print("Warning: RealtimeSTT not installed. Run 'pip install realtimestt'")
        
        # Initialize fallback engine if needed
        if self.engine is None and self.fallback_engine == 'whisper':
            try:
                import whisper
                self.engine = whisper.load_model("base")
                print("Whisper fallback engine initialized")
            except ImportError:
                print("Warning: Whisper not installed. Run 'pip install openai-whisper'")
    
    def start_listening(self, callback):
        """
        Start listening for speech and transcribing.
        
        Args:
            callback: Function to call with transcribed text
        """
        if self.is_listening:
            print("Already listening")
            return
        
        if self.engine is None:
            print("No STT engine available")
            return
        
        self.callback = callback
        self.is_listening = True
        
        # Start listening in a separate thread
        if self.engine_name == 'realtimestt':
            self.listen_thread = threading.Thread(target=self._listen_with_realtimestt)
            self.listen_thread.daemon = True
            self.listen_thread.start()
            print("Started listening with RealtimeSTT")
        else:
            print("Listening with fallback engine not implemented")
    
    def stop_listening(self):
        """Stop listening for speech"""
        if not self.is_listening:
            return
        
        self.is_listening = False
        
        if self.engine_name == 'realtimestt':
            self.engine.stop()
        
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=1.0)
        
        print("Stopped listening")
    
    def _listen_with_realtimestt(self):
        """Listen for speech using RealtimeSTT"""
        try:
            # Start the engine with our callback
            self.engine.start(self._on_transcribe)
            
            # Keep the thread running until stopped
            while self.is_listening:
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Error in RealtimeSTT listening: {e}")
            self.is_listening = False
    
    def _on_transcribe(self, text):
        """Handle transcribed text from RealtimeSTT"""
        if self.callback and text:
            self.callback(text)
    
    def transcribe_file(self, audio_path):
        """
        Transcribe speech from an audio file.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Transcribed text
        """
        if self.engine is None:
            print("No STT engine available")
            return None
        
        if self.engine_name == 'realtimestt':
            # RealtimeSTT doesn't directly support file transcription
            # This is a placeholder for actual implementation
            print("File transcription with RealtimeSTT not implemented")
            return None
        elif self.fallback_engine == 'whisper':
            try:
                result = self.engine.transcribe(audio_path)
                return result["text"]
            except Exception as e:
                print(f"Error transcribing file with Whisper: {e}")
                return None
        
        return None
