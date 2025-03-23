import os
import json
import requests
import time
from pathlib import Path

class LLMManager:
    """
    Manages interactions with Large Language Models for agent responses.
    Supports both local Mistral and cloud-based OpenRouter API.
    """
    
    def __init__(self, config_path):
        """
        Initialize the LLM Manager with configuration.
        
        Args:
            config_path: Path to the LLM configuration file
        """
        self.config_path = config_path
        self.load_config()
        self.initialize_engines()
        
    def load_config(self):
        """Load LLM configuration from file"""
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
        
        self.primary_engine = self.config.get('primaryEngine', 'mistral')
        self.secondary_engine = self.config.get('secondaryEngine', 'openrouter')
        self.mistral_settings = self.config.get('mistralSettings', {})
        self.openrouter_settings = self.config.get('openrouterSettings', {})
        self.fallback_strategy = self.config.get('fallbackStrategy', 'sequential')
        
    def initialize_engines(self):
        """Initialize LLM engines based on configuration"""
        self.engines = {}
        
        # Initialize primary engine (Mistral)
        if self.primary_engine == 'mistral':
            try:
                # For local Mistral via Ollama
                import ollama
                self.engines['mistral'] = {
                    'type': 'ollama',
                    'client': ollama,
                    'model': self.mistral_settings.get('model', 'mistral:7b-instruct-v0.2')
                }
                print("Mistral engine initialized via Ollama")
            except ImportError:
                try:
                    # For Mistral API
                    from mistralai.client import MistralClient
                    api_key = self.mistral_settings.get('apiKey', os.environ.get('MISTRAL_API_KEY', ''))
                    if api_key:
                        self.engines['mistral'] = {
                            'type': 'api',
                            'client': MistralClient(api_key=api_key),
                            'model': self.mistral_settings.get('model', 'mistral-medium')
                        }
                        print("Mistral engine initialized via API")
                    else:
                        print("Warning: No Mistral API key found")
                except ImportError:
                    print("Warning: Neither Ollama nor Mistral API client installed")
        
        # Initialize secondary engine (OpenRouter)
        if self.secondary_engine == 'openrouter':
            api_key = self.openrouter_settings.get('apiKey', os.environ.get('OPENROUTER_API_KEY', ''))
            if api_key:
                self.engines['openrouter'] = {
                    'type': 'api',
                    'api_key': api_key,
                    'model': self.openrouter_settings.get('model', 'anthropic/claude-3-opus:beta')
                }
                print("OpenRouter engine initialized")
            else:
                print("Warning: No OpenRouter API key found")
    
    def generate_response(self, prompt, system_prompt=None, agent_id=None, max_tokens=1000):
        """
        Generate a response from the LLM based on the prompt.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            agent_id: Optional agent ID for tracking
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        # Determine which engine to use
        engine_name = self._select_engine(agent_id)
        
        if engine_name not in self.engines:
            print(f"Warning: Engine {engine_name} not available")
            return "I'm sorry, I'm having trouble generating a response right now."
        
        # Try the selected engine
        response = self._generate_with_engine(engine_name, prompt, system_prompt, max_tokens)
        
        # If failed and fallback is enabled, try the other engine
        if not response and self.fallback_strategy == 'sequential':
            fallback_engine = next((e for e in self.engines.keys() if e != engine_name), None)
            if fallback_engine:
                print(f"Falling back to {fallback_engine}")
                response = self._generate_with_engine(fallback_engine, prompt, system_prompt, max_tokens)
        
        return response or "I'm sorry, I'm having trouble generating a response right now."
    
    def _select_engine(self, agent_id=None):
        """Select which engine to use based on agent and configuration"""
        # Default to primary engine
        return self.primary_engine
    
    def _generate_with_engine(self, engine_name, prompt, system_prompt=None, max_tokens=1000):
        """Generate response with the specified engine"""
        engine = self.engines.get(engine_name)
        if not engine:
            return None
        
        try:
            if engine_name == 'mistral':
                return self._generate_with_mistral(engine, prompt, system_prompt, max_tokens)
            elif engine_name == 'openrouter':
                return self._generate_with_openrouter(engine, prompt, system_prompt, max_tokens)
            else:
                print(f"Unknown engine: {engine_name}")
                return None
        except Exception as e:
            print(f"Error generating with {engine_name}: {e}")
            return None
    
    def _generate_with_mistral(self, engine, prompt, system_prompt, max_tokens):
        """Generate response with Mistral"""
        if engine['type'] == 'ollama':
            # Generate with Ollama
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = engine['client'].chat(
                model=engine['model'],
                messages=messages,
                options={"num_predict": max_tokens}
            )
            
            return response['message']['content']
        
        elif engine['type'] == 'api':
            # Generate with Mistral API
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = engine['client'].chat(
                model=engine['model'],
                messages=messages,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        
        return None
    
    def _generate_with_openrouter(self, engine, prompt, system_prompt, max_tokens):
        """Generate response with OpenRouter API"""
        headers = {
            "Authorization": f"Bearer {engine['api_key']}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": engine['model'],
            "messages": messages,
            "max_tokens": max_tokens
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"OpenRouter API error: {response.status_code} - {response.text}")
            return None
