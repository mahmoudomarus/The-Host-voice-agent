document.addEventListener('DOMContentLoaded', function() {
    // Initialize Socket.IO
    const socket = io();
    
    // Initialize tabs
    initTabs();
    
    // Load initial data
    loadAgents();
    loadAudioDevices();
    loadStatus();
    
    // Set up event listeners
    document.getElementById('start-system').addEventListener('click', startSystem);
    document.getElementById('stop-system').addEventListener('click', stopSystem);
    document.getElementById('update-agents').addEventListener('click', updateAgents);
    document.getElementById('test-response').addEventListener('click', testAgentResponse);
    document.getElementById('generate-speech').addEventListener('click', generateSpeech);
    
    // Set up periodic status updates
    setInterval(loadStatus, 5000);
    
    // Socket.IO event handlers
    socket.on('connect', function() {
        console.log('Connected to server');
    });
    
    socket.on('status_update', function(data) {
        updateStatus(data);
    });
    
    socket.on('new_message', function(data) {
        addMessageToConversation(data);
    });
});

// Initialize tab navigation
function initTabs() {
    const tabLinks = document.querySelectorAll('.sidebar .nav-link');
    
    tabLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            
            // Hide all tab panes
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('active');
            });
            
            // Remove active class from all links
            tabLinks.forEach(link => {
                link.classList.remove('active');
            });
            
            // Show the target tab pane
            const targetId = this.getAttribute('href').substring(1);
            document.getElementById(targetId).classList.add('active');
            
            // Set this link as active
            this.classList.add('active');
        });
    });
}

// Load agents from API
function loadAgents() {
    fetch('/api/agents')
        .then(response => response.json())
        .then(agents => {
            populateAgentLists(agents);
            
            // Load active agents
            return fetch('/api/active-agents');
        })
        .then(response => response.json())
        .then(activeAgents => {
            updateAgentSelections(activeAgents);
        })
        .catch(error => {
            console.error('Error loading agents:', error);
        });
}

// Populate agent lists in the UI
function populateAgentLists(agents) {
    // Main agent list for selection
    const agentList = document.getElementById('agent-list');
    agentList.innerHTML = '';
    
    agents.forEach(agent => {
        const item = document.createElement('div');
        item.className = 'list-group-item agent-item';
        item.innerHTML = `
            <input type="checkbox" class="form-check-input agent-checkbox" id="agent-${agent.id}" value="${agent.id}">
            <div class="agent-info">
                <div class="agent-name">${agent.name}</div>
                <div class="agent-role">${agent.role}</div>
            </div>
        `;
        agentList.appendChild(item);
    });
    
    // Dropdowns for testing
    const testAgentSelect = document.getElementById('test-agent');
    const speechAgentSelect = document.getElementById('speech-agent');
    
    testAgentSelect.innerHTML = '';
    speechAgentSelect.innerHTML = '';
    
    agents.forEach(agent => {
        const option = document.createElement('option');
        option.value = agent.id;
        option.textContent = `${agent.name} (${agent.role})`;
        
        testAgentSelect.appendChild(option.cloneNode(true));
        speechAgentSelect.appendChild(option);
    });
}

// Update agent checkboxes based on active agents
function updateAgentSelections(activeAgents) {
    document.querySelectorAll('.agent-checkbox').forEach(checkbox => {
        checkbox.checked = activeAgents.includes(checkbox.value);
    });
    
    document.getElementById('active-agent-count').textContent = activeAgents.length;
}

// Load audio devices from API
function loadAudioDevices() {
    fetch('/api/audio-devices')
        .then(response => response.json())
        .then(devices => {
            const inputSelect = document.getElementById('input-devices');
            const outputSelect = document.getElementById('output-devices');
            
            inputSelect.innerHTML = '';
            outputSelect.innerHTML = '';
            
            devices.forEach(device => {
                const option = document.createElement('option');
                option.value = device.index;
                option.textContent = device.name;
                
                if (device.input_channels > 0) {
                    inputSelect.appendChild(option.cloneNode(true));
                }
                
                if (device.output_channels > 0) {
                    outputSelect.appendChild(option);
                }
            });
        })
        .catch(error => {
            console.error('Error loading audio devices:', error);
        });
}

// Load system status
function loadStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(status => {
            updateStatus(status);
        })
        .catch(error => {
            console.error('Error loading status:', error);
        });
        
    // Also load conversation history
    loadConversationHistory();
}

// Update UI with system status
function updateStatus(status) {
    const badge = document.getElementById('status-badge');
    
    if (status.running) {
        badge.textContent = 'Running';
        badge.className = 'badge bg-success';
        document.getElementById('start-system').disabled = true;
        document.getElementById('stop-system').disabled = false;
    } else {
        badge.textContent = 'Stopped';
        badge.className = 'badge bg-danger';
        document.getElementById('start-system').disabled = false;
        document.getElementById('stop-system').disabled = true;
    }
    
    // Update current speaker
    const speakerElement = document.getElementById('current-speaker');
    if (status.current_speaker) {
        speakerElement.textContent = status.current_speaker;
    } else {
        speakerElement.textContent = 'None';
    }
    
    // Update turn statistics
    const stats = status.turn_statistics;
    document.getElementById('total-turns').textContent = stats.total_turns;
    
    // Update turn chart
    updateTurnChart(stats);
}

// Update turn distribution chart
function updateTurnChart(stats) {
    const ctx = document.getElementById('turn-chart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (window.turnChart) {
        window.turnChart.destroy();
    }
    
    // Extract data for chart
    const labels = Object.keys(stats.turns_by_agent);
    const data = Object.values(stats.turns_by_agent);
    
    // Create new chart
    window.turnChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Turns by Agent',
                data: data,
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

// Load conversation history
function loadConversationHistory() {
    fetch('/api/conversation-history')
        .then(response => response.json())
        .then(history => {
            const container = document.getElementById('conversation-history');
            container.innerHTML = '';
            
            history.forEach(message => {
                addMessageToConversation(message, false);
            });
            
            // Scroll to bottom
            container.scrollTop = container.scrollHeight;
        })
        .catch(error => {
            console.error('Error loading conversation history:', error);
        });
}

// Add a message to the conversation display
function addMessageToConversation(message, scrollToBottom = true) {
    const container = document.getElementById('conversation-history');
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${message.is_audience ? 'message-audience' : 'message-agent'}`;
    
    const time = new Date(message.timestamp * 1000).toLocaleTimeString();
    
    messageElement.innerHTML = `
        <div class="message-header">
            <span class="message-speaker">${message.speaker}</span>
            <span class="message-time">${time}</span>
        </div>
        <p class="message-text">${message.text}</p>
    `;
    
    container.appendChild(messageElement);
    
    if (scrollToBottom) {
        container.scrollTop = container.scrollHeight;
    }
}

// Start the system
function startSystem() {
    fetch('/api/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadStatus();
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error starting system:', error);
    });
}

// Stop the system
function stopSystem() {
    fetch('/api/stop', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadStatus();
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error stopping system:', error);
    });
}

// Update active agents
function updateAgents() {
    const checkboxes = document.querySelectorAll('.agent-checkbox:checked');
    const activeAgents = Array.from(checkboxes).map(checkbox => checkbox.value);
    
    fetch('/api/active-agents', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            agents: activeAgents
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadStatus();
            alert(`Active agents updated: ${activeAgents.join(', ')}`);
        }
    })
    .catch(error => {
        console.error('Error updating agents:', error);
    });
}

// Test agent response
function testAgentResponse() {
    const agentId = document.getElementById('test-agent').value;
    const prompt = document.getElementById('test-prompt').value;
    
    if (!agentId) {
        alert('Please select an agent');
        return;
    }
    
    fetch('/api/test-agent', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            agent_id: agentId,
            prompt: prompt
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const resultElement = document.getElementById('test-response-result');
            resultElement.classList.remove('d-none');
            
            document.getElementById('test-response-text').textContent = data.response;
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error testing agent:', error);
    });
}

// Generate speech
function generateSpeech() {
    const agentId = document.getElementById('speech-agent').value;
    const text = document.getElementById('speech-text').value;
    
    if (!agentId || !text) {
        alert('Please select an agent and enter text');
        return;
    }
    
    fetch('/api/test-speech', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            agent_id: agentId,
            text: text
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const resultElement = document.getElementById('speech-result');
            resultElement.classList.remove('d-none');
            
            const audioElement = document.getElementById('speech-audio');
            audioElement.src = data.audio_path;
            audioElement.play();
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error generating speech:', error);
    });
} 