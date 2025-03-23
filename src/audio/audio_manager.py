import os
import json
import pyaudio
import wave
import threading
import time
import numpy as np
from pathlib import Path

class AudioManager:
    """
    Manages audio input and output routing for the multi-voice agent system.
    Handles virtual audio devices and audio playback/recording.
    """
    
    def __init__(self, config_path):
        """
        Initialize the Audio Manager with configuration.
        
        Args:
            config_path: Path to the audio configuration file
        """
        self.config_path = config_path
        self.load_config()
        self.initialize_audio()
        
        # Playback state
        self.is_playing = False
        self.play_thread = None
        
        # Recording state
        self.is_recording = False
        self.record_thread = None
        self.recorded_frames = []
        
    def load_config(self):
        """Load audio configuration from file"""
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
        
        self.input_device = self.config.get('inputDevice', None)
        self.output_device = self.config.get('outputDevice', None)
        self.sample_rate = self.config.get('sampleRate', 44100)
        self.channels = self.config.get('channels', 1)
        self.chunk_size = self.config.get('chunkSize', 1024)
        self.format = self.config.get('format', 'int16')
        
    def initialize_audio(self):
        """Initialize PyAudio and identify devices"""
        self.audio = pyaudio.PyAudio()
        
        # Map format string to PyAudio format
        format_map = {
            'int16': pyaudio.paInt16,
            'int24': pyaudio.paInt24,
            'int32': pyaudio.paInt32,
            'float32': pyaudio.paFloat32
        }
        self.audio_format = format_map.get(self.format, pyaudio.paInt16)
        
        # Find device indices if names are provided
        if isinstance(self.input_device, str):
            self.input_device_index = self._find_device_index(self.input_device, 'input')
        else:
            self.input_device_index = self.input_device
            
        if isinstance(self.output_device, str):
            self.output_device_index = self._find_device_index(self.output_device, 'output')
        else:
            self.output_device_index = self.output_device
        
        print(f"Input device: {self.input_device_index}")
        print(f"Output device: {self.output_device_index}")
    
    def _find_device_index(self, device_name, direction):
        """Find device index by name and direction (input/output)"""
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_name.lower() in device_info['name'].lower():
                if direction == 'input' and device_info['maxInputChannels'] > 0:
                    return i
                elif direction == 'output' and device_info['maxOutputChannels'] > 0:
                    return i
        
        print(f"Warning: {direction} device '{device_name}' not found")
        return None
    
    def list_audio_devices(self):
        """List all available audio devices"""
        devices = []
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            devices.append({
                'index': i,
                'name': device_info['name'],
                'input_channels': device_info['maxInputChannels'],
                'output_channels': device_info['maxOutputChannels'],
                'default_sample_rate': device_info['defaultSampleRate']
            })
        
        return devices
    
    def play_audio(self, audio_path, blocking=False):
        """
        Play audio from a file.
        
        Args:
            audio_path: Path to the audio file
            blocking: Whether to block until playback is complete
            
        Returns:
            True if playback started successfully, False otherwise
        """
        if self.is_playing:
            print("Already playing audio")
            return False
        
        if not os.path.exists(audio_path):
            print(f"Audio file not found: {audio_path}")
            return False
        
        if blocking:
            return self._play_audio_blocking(audio_path)
        else:
            self.play_thread = threading.Thread(target=self._play_audio_blocking, args=(audio_path,))
            self.play_thread.daemon = True
            self.play_thread.start()
            return True
    
    def _play_audio_blocking(self, audio_path):
        """Play audio from a file (blocking)"""
        try:
            self.is_playing = True
            
            # Open the wave file
            wf = wave.open(audio_path, 'rb')
            
            # Create output stream
            stream = self.audio.open(
                format=self.audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
                output_device_index=self.output_device_index
            )
            
            # Read and play chunks
            data = wf.readframes(self.chunk_size)
            while data and self.is_playing:
                stream.write(data)
                data = wf.readframes(self.chunk_size)
            
            # Clean up
            stream.stop_stream()
            stream.close()
            wf.close()
            
            self.is_playing = False
            return True
            
        except Exception as e:
            print(f"Error playing audio: {e}")
            self.is_playing = False
            return False
    
    def stop_playback(self):
        """Stop audio playback"""
        self.is_playing = False
        
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join(timeout=1.0)
    
    def start_recording(self, max_seconds=None):
        """
        Start recording audio from the input device.
        
        Args:
            max_seconds: Maximum recording duration in seconds (None for unlimited)
            
        Returns:
            True if recording started successfully, False otherwise
        """
        if self.is_recording:
            print("Already recording")
            return False
        
        self.recorded_frames = []
        self.is_recording = True
        
        self.record_thread = threading.Thread(
            target=self._record_audio, 
            args=(max_seconds,)
        )
        self.record_thread.daemon = True
        self.record_thread.start()
        
        return True
    
    def _record_audio(self, max_seconds=None):
        """Record audio from the input device"""
        try:
            # Create input stream
            stream = self.audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.input_device_index,
                frames_per_buffer=self.chunk_size
            )
            
            start_time = time.time()
            
            # Record until stopped or max_seconds reached
            while self.is_recording:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                self.recorded_frames.append(data)
                
                if max_seconds and (time.time() - start_time) > max_seconds:
                    break
            
            # Clean up
            stream.stop_stream()
            stream.close()
            
            self.is_recording = False
            
        except Exception as e:
            print(f"Error recording audio: {e}")
            self.is_recording = False
    
    def stop_recording(self, output_path=None):
        """
        Stop recording and optionally save to a file.
        
        Args:
            output_path: Path to save the recorded audio (None to not save)
            
        Returns:
            Path to the saved file or None
        """
        if not self.is_recording:
            return None
        
        self.is_recording = False
        
        if self.record_thread and self.record_thread.is_alive():
            self.record_thread.join(timeout=1.0)
        
        if output_path and self.recorded_frames:
            return self._save_recording(output_path)
        
        return None
    
    def _save_recording(self, output_path):
        """Save recorded audio to a file"""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save as WAV file
            with wave.open(output_path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.audio_format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(self.recorded_frames))
            
            print(f"Recording saved to {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error saving recording: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_playback()
        self.stop_recording()
        
        if self.audio:
            self.audio.terminate()
