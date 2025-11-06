# Agent CLI

Command execution interface for the Digital Twin to run commands on the execution node.

## Features

- **Command Execution**: Run shell commands safely
- **Working Directory**: Control execution context
- **Output Capture**: Get stdout, stderr, and exit codes
- **Async Operations**: Run long-running commands
- **Security**: Command validation and restrictions

## API Endpoints

### Command Execution
- `POST /api/execute` - Execute a command synchronously
- `POST /api/execute-async` - Execute a command in background
- `GET /api/status` - Check command status
- `GET /api/output` - Get command output

### System Information
- `GET /api/system-info` - Get system information
- `GET /api/env` - Get environment variables

## Usage Examples

```python
# Execute a command
POST /agent-cli/api/execute
{
  "command": "ls -la",
  "cwd": "/Users/amit/aurica/code/apps"
}

# Get system info
GET /agent-cli/api/system-info
```

## Security

- Command validation and sanitization
- Restricted command list (configurable)
- Working directory restrictions
- User authentication required
- All commands are audited
