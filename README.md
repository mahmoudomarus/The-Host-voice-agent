# Hosty (The Host Voice Agent)

A multi-voice agent system for Twitter Spaces that enables AI agents to converse with each other and respond to audience members.

## Features

- Multiple AI agents with distinct personalities and voices
- Text-to-Speech with natural speech patterns (pauses, interjections)
- Speech-to-Text for transcribing audience input
- Audio routing between your system and Twitter Spaces
- Turn-taking logic for natural conversation flow
- Web UI for managing agents and system configuration
- Local hosting to minimize costs and ensure data privacy

## Prerequisites

- Python 3.8+
- [Blackhole](https://existential.audio/blackhole/) audio routing software
- [Bluestack](https://www.bluestacks.com/) (if you want to use the mobile Twitter app)
- Virtual environment (optional but recommended)

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/twitter-spaces-agents.git
   cd twitter-spaces-agents
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up API keys:
   - Copy `.env.example` to `.env`
   - Add your API keys to the `.env` file (see "API Keys" section below)

5. Install audio routing software:
   - [Blackhole](https://existential.audio/blackhole/) for macOS
   - [VB-Audio Virtual Cable](https://vb-audio.com/Cable/) for Windows

## API Keys

The system uses several APIs that require keys. Add the following to your `.env` file:

```
# LLM API Keys
MISTRAL_API_KEY=your_mistral_key
OPENROUTER_API_KEY=your_openrouter_key

# TTS API Keys (if using cloud services)
ELEVENLABS_API_KEY=your_elevenlabs_key
```

## Audio Setup

1. Configure Blackhole as a multi-output device:
   - Open "Audio MIDI Setup" on macOS
   - Create a multi-output device with both Blackhole and your speakers/headphones
   - Set this as your default output device

2. Configure input device:
   - Set Blackhole as the input device for your Twitter Spaces session

## Usage

### Running with Default Settings

```
./run.sh
```

### Running the Web UI

```
./run.sh --ui
```

The UI will be available at http://localhost:5000

### Running with One or Multiple Agents

- For a single agent:
  ```
  ./run.sh --agent alex
  ```

- For multiple specific agents:
  ```
  ./run.sh --agents alex,jordan
  ```

- For all agents:
  ```
  ./run.sh --all-agents
  ```

### Testing Components

- Test audio devices:
  ```
  ./run.sh --test-audio
  ```

- Test agent responses (without audio):
  ```
  ./run.sh --test-agents
  ```

## Web UI Features

The web UI allows you to:

- Start/stop the system
- Select which agents to activate
- Configure audio devices
- Edit agent personalities and voices
- View conversation logs
- Adjust turn-taking parameters
- Test agent responses and voices

## Configuration

All configuration files are in the `config/` directory:

- `agent_config.json`: Agent personalities and behaviors
- `audio_config.json`: Audio device settings
- `llm_config.json`: LLM API settings
- `stt_config.json`: Speech-to-Text settings
- `tts_config.json`: Text-to-Speech voice profiles

## Troubleshooting

- **Audio routing issues**: Ensure Blackhole is properly set up as both an input and output device
- **API key errors**: Check that all required API keys are correctly set in your `.env` file
- **LLM not responding**: Try switching to a different LLM provider in the config
- **Voice quality issues**: Adjust TTS settings or try a different TTS engine

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 