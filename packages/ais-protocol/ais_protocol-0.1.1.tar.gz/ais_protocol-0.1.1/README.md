# AIS Protocol - Python SDK

**Agent Interface Standard (AIS)** is a protocol for AI agent-to-agent communication. Think "HTTP for AI agents" or "MCP for agent collaboration."

## Features

- 🚀 **Production-ready** - Battle-tested, type-safe, fully async
- 🔌 **Transport agnostic** - HTTP, WebSocket, or bring your own
- 🔐 **Secure by default** - JWT/API key auth, input validation, rate limiting
- 📦 **Easy to use** - <50 lines to create a basic agent
- 🔄 **Session management** - Stateful multi-turn interactions
- 📊 **Observable** - Structured logging and metrics built-in

## Quick Start

### Installation

```bash
pip install ais-protocol
```

### Create Your First Agent

```python
from ais import AISAgent

# Create agent
agent = AISAgent(
    agent_id="agent://example.com/my-agent",
    agent_name="My First Agent"
)

# Register a capability
@agent.capability(
    name="greet",
    description="Greet someone by name"
)
async def greet_handler(parameters, context, session):
    name = parameters.get("name", "World")
    return {"message": f"Hello, {name}!"}

# Start the agent
agent.start_sync(port=8000)
```

### Connect to an Agent

```python
from ais import AISClient

# Create client
client = AISClient(
    client_agent_id="agent://example.com/my-client"
)

# Connect to remote agent
session_id = await client.connect(
    server_url="http://localhost:8000",
    server_agent_id="agent://example.com/my-agent"
)

# Call a capability
result = await client.call(
    session_id=session_id,
    capability="greet",
    parameters={"name": "Alice"}
)

print(result)  # {"message": "Hello, Alice!"}
```

## Documentation

- [API Reference](docs/api/)
- [User Guide](docs/guides/)
- [Examples](examples/)
- [Protocol Specification](docs/protocol-spec.md)

## Status

**Version:** 0.1.0 (Alpha)
**Python:** 3.9+
**License:** Apache 2.0

## Development

### Setup

```bash
# Clone monorepo
git clone https://mercola-consulting-services.ghe.com/MCS/A2A-Protocol-AIS.git
cd A2A-Protocol-AIS/packages/python

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src tests
ruff check src tests

# Type check
mypy src
```

## Contributing

This project is in active development. We welcome contributions!

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Links

- [GitHub](https://github.com/ais-protocol/ais-python)
- [Documentation](https://docs.ais-protocol.org)
- [Issues](https://github.com/ais-protocol/ais-python/issues)
