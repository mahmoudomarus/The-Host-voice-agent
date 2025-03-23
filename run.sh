#!/bin/bash

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated"
else
    echo "No virtual environment found. Consider creating one with 'python -m venv venv'"
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
    echo "Environment variables loaded from .env file"
else
    echo "Warning: .env file not found. You may need to set up API keys."
fi

# Parse command line arguments
ARGS=""

# Check for UI flag
if [[ "$*" == *"--ui"* ]]; then
    ARGS="$ARGS --ui"
    echo "Starting with web UI..."
fi

# Check for agent selection
if [[ "$*" == *"--agent "* ]]; then
    AGENT=$(echo $* | grep -o '\--agent [^ ]*' | cut -d' ' -f2)
    ARGS="$ARGS --agent $AGENT"
    echo "Starting with agent: $AGENT"
fi

# Check for multiple agents
if [[ "$*" == *"--agents "* ]]; then
    AGENTS=$(echo $* | grep -o '\--agents [^ ]*' | cut -d' ' -f2)
    ARGS="$ARGS --agents $AGENTS"
    echo "Starting with agents: $AGENTS"
fi

# Check for all agents
if [[ "$*" == *"--all-agents"* ]]; then
    ARGS="$ARGS --all-agents"
    echo "Starting with all agents"
fi

# Pass through other arguments
for arg in "$@"; do
    if [[ "$arg" != "--ui" && "$arg" != "--agent"* && "$arg" != "--agents"* && "$arg" != "--all-agents" ]]; then
        ARGS="$ARGS $arg"
    fi
done

# Run the main application
echo "Running: python src/main.py $ARGS"
python src/main.py $ARGS
