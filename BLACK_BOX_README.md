# JARVIS Black Box System

The JARVIS Black Box is a comprehensive state and activity tracking system that enables **cross-agent awareness** and **state transfer** between different AI agents (Claude Code, GitHub Copilot, JARVIS Core, etc.).

## Overview

The Black Box system consists of two main sections:

### Section 1: Universal Activity Log
- **Stores ALL messages, tasks, successes/failures, everything**
- Every action taken by any AI agent gets logged here
- Enables future agents to understand what previous agents did and where they got stuck

### Section 2: Agent Modification Tracker
- **Stores summaries of what each agent did/modified**
- Tracks code changes, file modifications, and key decisions
- Allows agents to understand the evolution of the codebase

## Key Features

- **Cross-Agent State Transfer**: Any AI agent can understand what previous agents accomplished
- **Comprehensive Logging**: Everything gets logged - successes, failures, modifications, decisions
- **Session Management**: Tracks agent sessions with start/end times and success rates
- **Search & Query**: Agents can search historical activities and get context
- **REST API**: External agents can integrate via HTTP endpoints
- **Thread-Safe**: Handles concurrent access from multiple agents

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Claude Code   │    │  GitHub Copilot  │    │   JARVIS Core   │
│                 │    │                  │    │                 │
│  ┌──────────┐   │    │  ┌──────────┐    │    │  ┌──────────┐   │
│  │ Agent    │   │    │  │ Agent    │    │    │  │ Agent    │   │
│  │Integrator│◄─►│    │  │Integrator│◄─► │    │  │ Loop     │   │
│  └──────────┘   │    │  └──────────┘    │    │  └──────────┘   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                         ┌────────▼────────┐
                         │                 │
                         │   BLACK BOX     │
                         │                 │
                         │ ┌─────────────┐ │
                         │ │Activities   │ │
                         │ │Log          │ │
                         │ └─────────────┘ │
                         │                 │
                         │ ┌─────────────┐ │
                         │ │Agent        │ │
                         │ │Summaries    │ │
                         │ └─────────────┘ │
                         │                 │
                         │ ┌─────────────┐ │
                         │ │Current      │ │
                         │ │State        │ │
                         │ └─────────────┘ │
                         └─────────────────┘
```

## Files

- `Core/black_box.py` - Main Black Box system
- `Core/agent_integration.py` - Integration layer for external agents
- `Core/black_box_api.py` - Standalone REST API server (optional)
- `Core/main.py` - Integrated API endpoints in main JARVIS server

## API Endpoints

### Health & State
- `GET /blackbox/health` - Health check
- `GET /blackbox/state` - Get current global state
- `GET /blackbox/context/{agent_type}` - Get context for agent type

### Agent Session Management
- `POST /blackbox/agent/start` - Start agent session
- `POST /blackbox/agent/{agent_id}/end` - End agent session

### Activity Logging
- `POST /blackbox/agent/{agent_id}/activity` - Log general activity
- `POST /blackbox/agent/{agent_id}/modification` - Log code/file modification
- `POST /blackbox/agent/{agent_id}/task/start` - Log task start
- `POST /blackbox/agent/{agent_id}/task/complete` - Log task completion

### State Transfer
- `POST /blackbox/agent/{agent_id}/transfer/{target_type}/{target_id}` - Transfer state to another agent

### Querying
- `GET /blackbox/activities/recent/{agent_type}` - Get recent activities
- `GET /blackbox/activities/search/{agent_type}?q=query` - Search activities
- `GET /blackbox/session/{session_id}/summary` - Get session summary

## Usage Examples

### For External Agents (Claude Code, Copilot, etc.)

```python
import requests

# Start session
response = requests.post('http://localhost:8001/blackbox/agent/start', json={
    'agent_type': 'CLAUDE_CODE',
    'agent_id': 'session_123',
    'agent_name': 'Claude Code Assistant'
})
session_data = response.json()

# Log activities
requests.post(f'/blackbox/agent/session_123/activity', json={
    'activity_type': 'TASK_START',
    'content': 'Implementing user authentication',
    'metadata': {'priority': 'high'}
})

# Log modifications
requests.post(f'/blackbox/agent/session_123/modification', json={
    'description': 'Added login endpoint to auth.py',
    'file_path': 'auth.py'
})

# Get context from previous agents
context = requests.get('/blackbox/context/claude_code').json()

# Transfer to another agent
transfer = requests.post('/blackbox/agent/session_123/transfer/copilot/copilot_session_456')

# End session
requests.post(f'/blackbox/agent/session_123/end', json={
    'summary': 'Successfully implemented authentication system'
})
```

### For JARVIS Internal Use

```python
from Core.black_box import get_black_box, AgentType
from Core.agent_integration import ClaudeCodeIntegrator

# Get global black box instance
black_box = get_black_box()

# Create integrator for external agent
integrator = ClaudeCodeIntegrator("external_session_123")
integrator.start_session()

# Log activities
integrator.log_task_start("Refactoring authentication module")
integrator.log_modification("Refactored auth.py to use dependency injection", "auth.py")

# Get context
context = integrator.get_context()

# Transfer state
transfer_data = integrator.transfer_to_agent(AgentType.COPILOT, "copilot_456")

integrator.end_session("Completed authentication refactoring")
```

## Data Storage

The Black Box stores data in JSON Lines format for efficient append-only logging:

- `data/black_box/activities.jsonl` - All activities
- `data/black_box/agent_summaries.jsonl` - Agent session summaries
- `data/black_box/current_state.json` - Current global state

## Agent Types Supported

- `JARVIS_CORE` - Main JARVIS agent loop
- `CLAUDE_CODE` - Anthropic Claude Code
- `COPILOT` - GitHub Copilot
- `CODEX` - OpenAI Codex
- `GEMINI` - Google Gemini
- `OLLAMA` - Local Ollama models
- `CUSTOM_AGENT` - Any other agent

## Integration with JARVIS Agent Loop

The agent loop automatically logs all activities:

- Task start/completion
- Tool executions (success/failure)
- LLM decisions
- Error conditions

This ensures that even if external agents aren't integrated, JARVIS maintains a complete activity log.

## Benefits

1. **No More Lost Context**: Agents always know what previous agents did
2. **Faster Debugging**: Historical activities help identify where things went wrong
3. **Better Collaboration**: Multiple agents can work together more effectively
4. **Learning**: JARVIS can learn from successful/failed agent patterns
5. **Transparency**: Complete audit trail of all AI activities

## Future Extensions

- Integration with VS Code API for real-time agent coordination
- Machine learning on activity patterns to predict agent success
- Automatic agent handoff based on task requirements
- Visual dashboard for monitoring agent activities
- Export capabilities for sharing agent workflows</content>
<parameter name="filePath">c:\Users\mtm\Desktop\mark0/BLACK_BOX_README.md