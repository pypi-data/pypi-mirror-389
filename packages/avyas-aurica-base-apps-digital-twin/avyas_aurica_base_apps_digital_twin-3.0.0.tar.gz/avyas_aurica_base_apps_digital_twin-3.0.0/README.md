# Digital Twin Agent

## Overview

The **Digital Twin Agent** is not just a chatbot or assistant - it is the user's **digital representation** and **first-class citizen** in the Aurica ecosystem. The Digital Twin (DT) owns all digital interactions on behalf of the user and has full access to the execution node (local machine) capabilities.

## Concept

### What is a Digital Twin?

A Digital Twin is the user's AI self that:
- **IS the user** in digital form, not just serves them
- **Owns everything** - all actions, decisions, and executions are its responsibility
- **Acts with user's authority** - uses the user's JWT and permissions
- **Has full execution node access** - can discover and use all local apps and resources
- **Maintains persistent state** - memory, preferences, and context across all sessions
- **Acts autonomously** - makes decisions and executes actions within defined boundaries

### Key Principles

1. **First-Class Citizen**: The DT is the primary entity, not a helper
2. **User Identity = DT Identity**: The DT acts WITH the user's credentials
3. **Autonomous by Default**: DT can act freely within autonomy boundaries
4. **Persistent & Learning**: DT maintains state and learns user preferences
5. **Execution Node Master**: Full access to local machine capabilities

## Architecture

```
Cloud (api.oneaurica.com)
         ↓ [Internet]
   Chat Interface
         ↓ [HTTP/WebSocket]
Digital Twin Agent (localhost) ← This App
         ↓
   Execution Node Interface
         ↓
   Local Apps + System Resources
```

## API Endpoints

### POST /api/think
Main DT reasoning and decision-making endpoint.

**Request:**
```json
{
  "input": "User message or request",
  "context": {
    "conversation_id": "uuid",
    "user_intent": "query|command|chat"
  },
  "history": [
    {"role": "user", "content": "previous message"},
    {"role": "assistant", "content": "previous response"}
  ]
}
```

**Response:**
```json
{
  "thought_process": "DT's reasoning",
  "decision": "respond|use_tool|ask_clarification",
  "action": {"tool": "tool_name", "parameters": {}},
  "response": "Response to user",
  "dt_confidence": 0.95
}
```

### POST /api/act
Execute a specific action autonomously.

**Request:**
```json
{
  "action": "execute_tool",
  "tool": "tool_name",
  "parameters": {},
  "on_behalf_of": "user_id"
}
```

### GET /api/state
Get current DT state and context.

**Response:**
```json
{
  "user_id": "user123",
  "dt_active": true,
  "current_context": {},
  "memory": {},
  "capabilities": {}
}
```

### GET /api/capabilities
List what the DT can do.

**Response:**
```json
{
  "dt_version": "1.0.0",
  "capabilities": {
    "tools": ["weather", "profile", "dashboard"],
    "execution_node": {"accessible": true},
    "autonomous_actions": true
  }
}
```

### GET /api/health
Health check endpoint.

## Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional
LLM_PROVIDER=openai              # openai, anthropic
LLM_MODEL=gpt-4                  # gpt-4, gpt-4-turbo, gpt-3.5-turbo
DT_MODE=autonomous               # autonomous, assisted, manual
DT_STATE_STORAGE=file            # file, s3, database
LLM_MAX_TOKENS=6000
LLM_TEMPERATURE=0.7
```

## Usage

### As a User
1. Access chat interface at api.oneaurica.com
2. Your Digital Twin automatically activates
3. Chat naturally - your DT understands and acts

### As a Developer
```python
# The DT is automatically loaded by the Aurica platform
# It discovers all local apps and capabilities
# No manual configuration needed
```

## Testing

```bash
# Health check
curl http://localhost:8000/digital-twin/api/health

# Think (requires JWT)
curl -X POST http://localhost:8000/digital-twin/api/think \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Who are you?",
    "context": {"user_intent": "introduction"}
  }'
```

## Development Status

- ✅ Core foundation
- 🟡 Tool discovery (Step 3)
- 🔴 Advanced autonomy (Step 5)
- 🔴 Persistent memory (Step 6)

## License

Part of the Aurica Platform
