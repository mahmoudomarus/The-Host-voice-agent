from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import os
import sys
import json
from pathlib import Path

# Create Flask app and SocketIO instance
app = Flask(__name__)
app.config['SECRET_KEY'] = 'twitter-spaces-secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store the system instance globally
system = None

def create_app(system_instance):
    """
    Create and configure the application.
    
    Args:
        system_instance: The TwitterSpacesAgentSystem instance
        
    Returns:
        The configured Flask app
    """
    global system
    system = system_instance
    
    @app.route('/')
    def index():
        """Render the main UI page"""
        return render_template('index.html')
    
    @app.route('/api/agents', methods=['GET'])
    def get_agents():
        """Get the list of available agents"""
        return jsonify(system.agent_manager.agents)
    
    @app.route('/api/active-agents', methods=['GET'])
    def get_active_agents():
        """Get the list of currently active agents"""
        active_agents = system.active_agents or [agent['id'] for agent in system.agent_manager.agents]
        return jsonify(active_agents)
    
    @app.route('/api/active-agents', methods=['POST'])
    def set_active_agents():
        """Set the active agents"""
        active_agents = request.json.get('agents', [])
        
        # Update active agents in system
        system.active_agents = active_agents
        
        # Reinitialize components with new active agents
        system.initialize_components()
        
        return jsonify({"success": True, "active_agents": active_agents})
    
    @app.route('/api/status', methods=['GET'])
    def get_status():
        """Get the current system status"""
        status = {
            "running": system.running,
            "current_speaker": system.turn_manager.current_speaker,
            "is_audience_speaking": system.turn_manager.is_audience_speaking,
            "turn_statistics": system.turn_manager.get_turn_statistics()
        }
        return jsonify(status)
    
    @app.route('/api/start', methods=['POST'])
    def start_system():
        """Start the system"""
        if not system.running:
            # Start in a separate thread to not block the UI
            import threading
            threading.Thread(target=system.start).start()
            return jsonify({"success": True, "message": "System started"})
        else:
            return jsonify({"success": False, "message": "System is already running"})
    
    @app.route('/api/stop', methods=['POST'])
    def stop_system():
        """Stop the system"""
        if system.running:
            system.stop()
            return jsonify({"success": True, "message": "System stopped"})
        else:
            return jsonify({"success": False, "message": "System is not running"})
    
    @app.route('/api/test-agent', methods=['POST'])
    def test_agent():
        """Test an agent response"""
        agent_id = request.json.get('agent_id')
        prompt = request.json.get('prompt', 'Please introduce yourself and your expertise.')
        
        if not agent_id:
            return jsonify({"success": False, "message": "Agent ID is required"})
        
        response = system.agent_manager.generate_agent_response(agent_id, prompt)
        
        if response:
            return jsonify({
                "success": True, 
                "agent_id": agent_id, 
                "response": response
            })
        else:
            return jsonify({"success": False, "message": f"Failed to generate response for agent {agent_id}"})
    
    @app.route('/api/test-speech', methods=['POST'])
    def test_speech():
        """Test agent speech generation"""
        agent_id = request.json.get('agent_id')
        text = request.json.get('text')
        
        if not agent_id or not text:
            return jsonify({"success": False, "message": "Agent ID and text are required"})
        
        audio_path = system.agent_manager.speak_agent_response(agent_id, text)
        
        if audio_path:
            # Get relative path for serving
            rel_path = os.path.relpath(audio_path, start=os.getcwd())
            return jsonify({
                "success": True, 
                "agent_id": agent_id, 
                "audio_path": rel_path
            })
        else:
            return jsonify({"success": False, "message": f"Failed to generate speech for agent {agent_id}"})
    
    @app.route('/api/audio-devices', methods=['GET'])
    def get_audio_devices():
        """Get the list of available audio devices"""
        devices = system.audio_manager.list_audio_devices()
        return jsonify(devices)
    
    @app.route('/api/conversation-history', methods=['GET'])
    def get_conversation_history():
        """Get the conversation history"""
        agent_id = request.args.get('agent_id')
        
        if agent_id:
            # Get history for specific agent
            history = system.agent_manager.conversation_history.get(agent_id, [])
        else:
            # Get first agent's history as default
            agent_id = system.agent_manager.agents[0]['id'] if system.agent_manager.agents else None
            history = system.agent_manager.conversation_history.get(agent_id, [])
        
        return jsonify(history)
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        print('Client connected')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        print('Client disconnected')
    
    return app 