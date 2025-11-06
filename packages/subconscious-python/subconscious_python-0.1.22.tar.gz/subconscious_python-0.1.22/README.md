# Subconscious Python SDK

A Python SDK for the Subconscious AI agent framework, providing structured reasoning and tool integration capabilities.

## Installation

Install the package using pip:

```bash
pip install subconscious-python
```

> **Note**: The package name is `subconscious-python` but you import it as `subconscious`:
> ```python
> import subconscious  # Import name remains clean and simple
> ```

For development installation:

```bash
pip install -e .
```

## Quick Start

```python
from subconscious import Client

# Initialize the client
client = Client(
    base_url="https://api.subconscious.dev/v1", # can be omitted
    api_key="your-api-key" # get it from https://subconscious.dev
)

# Define tools
tools = [
    {
        "type": "function",
        "name": "calculator",
        "url": "https://URL_TO_CALCULATOR_TOOL/ENDPOINT", # the server url of your own tool
        "method": "POST",
        "timeout": 5, # seconds
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {"type": "string"},
                "a": {"type": "number"},
                "b": {"type": "number"}
            },
            "required": ["operation", "a", "b"]
        }
    }
]

# Build toolkit
client.build_toolkit(tools, agent_name="math_agent")

# Run agent
messages = [{"role": "user", "content": "What is 2 + 3?"}]
response = client.agent.run(messages, agent_name="math_agent")
print(response)
```

The TIM language model will call the `calculator` tool as many times as necessary, handle excepts, compute the answer, and return the result. The agent is completed with one language model API call!

We also provide fine-grained control over the reasoning structure, tool use, and memory management. Check out the [deep research agent example](https://github.com/subconscious-systems/TIMRUN/tree/main/examples/deep_research) for more advanced usage.

## Features

- **Structured Reasoning**: Define complex reasoning patterns with hierarchical task structures
- **Tool Integration**: Seamlessly integrate external tools and APIs
- **Type Safety**: Full Pydantic integration for robust type checking
- **Streaming Support**: Real-time streaming responses
- **Grammar-Based Parsing**: Advanced grammar-driven response formatting

## API Reference

### Client

Main client class for interacting with the Subconscious API.

```python
client = Client(base_url="https://api.subconscious.dev", api_key="your-api-key")
```

### Agent

Core agent functionality for parsing and running structured reasoning tasks.

```python
response = client.agent.parse(messages, model="tim-large", tools=tools)
response = client.agent.run(messages, agent_name="default", thread_name="default")
```

### Tools and Tasks

Create custom tools and task structures:

```python
# Build a toolkit
client.build_toolkit(tools, agent_name="my_agent")

# Create custom tasks
task = client.create_task(
    task_name="analysis",
    agent_name="my_agent",
    thought="Analyze the data",
    tools=("tool1", "tool2")
)

# Create custom threads
thread = client.create_thread(
    reasoning_model=MyReasoningModel,
    answer_model=str,
    agent_name="my_agent",
    thread_name="custom"
)
```

## Requirements

- Python 3.8+
- pydantic>=2.0.0
- openai>=1.0.0
- requests>=2.25.0
- pyhumps>=3.0.0

## License

MIT License - see LICENSE file for details.

## Support

For support and questions:
- Documentation: https://docs.subconscious.dev
- Email: {hongyin,jack}@subconscious.dev
