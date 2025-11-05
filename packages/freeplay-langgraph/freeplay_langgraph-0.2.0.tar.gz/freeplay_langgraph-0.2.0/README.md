# Freeplay LangGraph Integration

Freeplay integration for LangGraph and LangChain, providing observability and prompt management for your AI applications.

## Installation

**Requirements:** Python 3.10 or higher

```bash
pip install freeplay-langgraph
```

## Features

- **🔍 Automatic Observability**: OpenTelemetry instrumentation for LangChain and LangGraph applications
- **📝 Prompt Management**: Call Freeplay-hosted prompts with version control and environment management
- **🤖 Auto-Model Instantiation**: Automatically create LangChain models based on Freeplay's configuration
- **🤖 Full Agent Support**: Create LangGraph agents with ReAct loops, tool calling, and state management
- **⚡ Complete Async Support**: All methods support async/await (ainvoke, astream, abatch, etc.)
- **💬 Conversation History**: Native support for multi-turn conversations with LangGraph MessagesState
- **🛠️ Tool Support**: Seamless integration with LangChain tools
- **🎛️ Middleware**: Support for custom middleware to extend agent behavior
- **📊 Structured Output**: ToolStrategy and ProviderStrategy for formatted responses
- **🌊 Streaming**: Stream agent execution step-by-step or token-by-token (both simple and agent modes)
- **🧪 Test Execution Tracking**: Track test runs and test cases for evaluation workflows
- **🎯 Multi-Provider Support**: Works with OpenAI, Anthropic, Vertex AI, and more
- **🔒 Type Safety**: Full generic typing support with proper IDE autocomplete

## Quick Start

### Configuration

Set up your environment variables:

```bash
export FREEPLAY_API_URL="https://app.freeplay.ai/api"
export FREEPLAY_API_KEY="fp-..."
export FREEPLAY_PROJECT_ID="..."
```

Or pass them directly when initializing:

```python
from freeplay_langgraph import FreeplayLangGraph

freeplay = FreeplayLangGraph(
    freeplay_api_url="https://api.freeplay.ai",
    freeplay_api_key="fp_...",
    project_id="proj_...",
)
```

#### Bundled Prompts

By default, FreeplayLangGraph uses the API-based template resolver to fetch prompts from Freeplay. If you need to use bundled prompts or custom prompt resolution logic, you can provide your own template resolver:

```python
from pathlib import Path
from freeplay.resources.prompts import FilesystemTemplateResolver
from freeplay_langgraph import FreeplayLangGraph

# Use filesystem-based prompts (e.g., bundled with your app)
freeplay = FreeplayLangGraph(
    template_resolver=FilesystemTemplateResolver(Path("bundled_prompts"))
)
```

## Usage

### Creating Agents with `create_agent`

The recommended way to use Freeplay with LangGraph is through the `create_agent` method, which uses Freeplay-hosted prompts via `prompt_name` and provides full support for LangGraph's agent capabilities including the ReAct loop, tool calling, middleware, structured output, and streaming.

```python
from freeplay_langgraph import FreeplayLangGraph
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"Weather in {city}: Sunny, 72°F"

freeplay = FreeplayLangGraph()

# Create an agent with Freeplay prompt
agent = freeplay.create_agent(
    prompt_name="weather-assistant",
    variables={"location": "San Francisco"},
    tools=[get_weather],
    checkpointer=MemorySaver(),  # Enable state persistence
    environment="production"
)

# Invoke the agent
result = agent.invoke({
    "messages": [HumanMessage(content="What's the weather in SF?")]
})

print(result["messages"][-1].content)
```

#### Streaming Agent Execution

Stream agent steps in real-time:

```python
agent = freeplay.create_agent(
    prompt_name="weather-assistant",
    variables={"city": "Seattle"},
    tools=[get_weather]
)

# Stream agent execution
for chunk in agent.stream(
    {"messages": [HumanMessage(content="What's the weather?")]},
    stream_mode="values"
):
    latest_message = chunk["messages"][-1]
    if hasattr(latest_message, "content") and latest_message.content:
        print(f"Agent: {latest_message.content}")
    elif hasattr(latest_message, "tool_calls") and latest_message.tool_calls:
        print(f"Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}")
```

#### Custom Middleware

Add custom behavior to your agent with middleware (requires LangChain 1.0+):

```python
from langchain.agents.middleware import AgentMiddleware

class LoggingMiddleware(AgentMiddleware):
    """Custom middleware that logs before model calls."""
    
    def before_model(self, state, runtime):
        message_count = len(state.get("messages", []))
        print(f"About to call model with {message_count} messages")
        return None
    
    def after_model(self, state, runtime):
        return None
    
    def wrap_tool_call(self, request, handler):
        return handler(request)

agent = freeplay.create_agent(
    prompt_name="weather-assistant",
    variables={"city": "Boston"},
    tools=[get_weather],
    middleware=[LoggingMiddleware()]
)
```

#### Structured Output

Get structured responses using `ToolStrategy` or `ProviderStrategy`:

```python
from pydantic import BaseModel
from langchain.agents.structured_output import ToolStrategy

class WeatherReport(BaseModel):
    city: str
    temperature: float
    conditions: str

agent = freeplay.create_agent(
    prompt_name="weather-assistant",
    variables={"city": "NYC"},
    tools=[get_weather],
    response_format=ToolStrategy(WeatherReport)
)

result = agent.invoke({
    "messages": [HumanMessage(content="Get weather for NYC")]
})

# Access structured output
weather_report = result["structured_response"]
print(f"{weather_report.city}: {weather_report.temperature}°F, {weather_report.conditions}")
```

### Prompt Management with Auto-Model Instantiation

For simple use cases without the full agent loop, use the `invoke` method:

Call a Freeplay-hosted prompt and let the SDK automatically instantiate the correct model:

```python
from freeplay_langgraph import FreeplayLangGraph

freeplay = FreeplayLangGraph()

# Invoke a prompt - model is automatically created based on Freeplay's config
response = freeplay.invoke(
    prompt_name="weather-assistant",
    variables={"city": "San Francisco"},
    environment="production"
)

```

#### Async Support

All methods support async/await for better performance in async applications:

```python
# Async invocation
response = await freeplay.ainvoke(
    prompt_name="weather-assistant",
    variables={"city": "San Francisco"}
)

# Async streaming
async for chunk in freeplay.astream(
    prompt_name="weather-assistant",
    variables={"city": "San Francisco"}
):
    print(chunk.content, end="", flush=True)
```

#### Streaming Simple Invocations

Stream model responses without the full agent loop:

```python
# Synchronous streaming
for chunk in freeplay.stream(
    prompt_name="weather-assistant",
    variables={"city": "San Francisco"}
):
    print(chunk.content, end="", flush=True)

# Async streaming
async for chunk in freeplay.astream(
    prompt_name="weather-assistant",
    variables={"city": "San Francisco"}
):
    print(chunk.content, end="", flush=True)
```

### Using Custom Models

You can also provide your own pre-configured model:

```python
from langchain_openai import ChatOpenAI
from freeplay_langgraph import FreeplayLangGraph

freeplay = FreeplayLangGraph()
model = ChatOpenAI(model="gpt-4", temperature=0.7)

response = freeplay.invoke(
    prompt_name="weather-assistant",
    variables={"city": "New York"},
    model=model
)
```

### Conversation History (Multi-turn Chat)

Maintain conversation context with history:

```python
from langchain_core.messages import HumanMessage, AIMessage
from freeplay_langgraph import FreeplayLangGraph

freeplay = FreeplayLangGraph()

# Build conversation history
history = [
    HumanMessage(content="What's the weather in Paris?"),
    AIMessage(content="It's sunny and 22°C in Paris."),
    HumanMessage(content="What about in winter?")
]

response = freeplay.invoke(
    prompt_name="weather-assistant",
    variables={"city": "Paris"},
    history=history
)
```

### Tool Calling

Bind LangChain tools to your prompts:

```python
from langchain_core.tools import tool
from freeplay_langgraph import FreeplayLangGraph

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    # Your weather API logic here
    return f"Weather in {city}: Sunny, 22°C"

freeplay = FreeplayLangGraph()

response = freeplay.invoke(
    prompt_name="weather-assistant",
    variables={"city": "London"},
    tools=[get_weather]
)
```

### Test Execution Tracking

Track test runs for evaluation workflows (works with both `create_agent` and `invoke`):

```python
from freeplay_langgraph import FreeplayLangGraph

freeplay = FreeplayLangGraph()

# With create_agent
agent = freeplay.create_agent(
    prompt_name="my-prompt",
    variables={"input": "test input"},
    tools=[get_weather],
    test_run_id="test_run_123",
    test_case_id="test_case_456"
)

# Or with invoke
response = freeplay.invoke(
    prompt_name="my-prompt",
    variables={"input": "test input"},
    test_run_id="test_run_123",
    test_case_id="test_case_456"
)
```

## API Reference

### `create_agent()`

Create a LangGraph agent with Freeplay-hosted prompt and full observability.

**Parameters:**
- `prompt_name` (str): Name of the prompt in Freeplay
- `variables` (dict): Variables to render the prompt template
- `tools` (list, optional): List of tools for the agent to use
- `environment` (str, optional): Environment to use (default: "latest")
- `model` (BaseChatModel, optional): Pre-instantiated model (auto-created if not provided)
- `state_schema` (type, optional): Custom state schema (TypedDict)
- `context_schema` (type, optional): Context schema for runtime context
- `middleware` (list, optional): List of middleware to apply
- `response_format` (optional): Structured output format (ToolStrategy or ProviderStrategy)
- `checkpointer` (BaseCheckpointSaver, optional): Checkpointer for state persistence
- `test_run_id` (str, optional): Test run ID for tracking
- `test_case_id` (str, optional): Test case ID for tracking

**Returns:** `FreeplayAgent` - A wrapper around the compiled LangGraph agent that injects Freeplay metadata

**Note:** The returned `FreeplayAgent` is fully compatible with LangGraph agents. All invocation methods (invoke, ainvoke, stream, astream, batch, abatch, astream_events) are supported with automatic metadata injection. For state management methods, use `unwrap()` - see [State Management](#state-management) below.

### `invoke()` / `ainvoke()`

Invoke a model with a Freeplay-hosted prompt (simple use cases).

**Parameters:**
- `prompt_name` (str): Name of the prompt in Freeplay
- `variables` (dict): Variables to render the prompt template
- `environment` (str, optional): Environment to use (default: "latest")
- `model` (BaseChatModel, optional): Pre-instantiated model
- `history` (list, optional): Conversation history
- `tools` (list, optional): Tools to bind to the model
- `test_run_id` (str, optional): Test run ID for tracking
- `test_case_id` (str, optional): Test case ID for tracking

**Returns:** The model's response message

**Async:** Use `ainvoke()` with the same parameters for async execution.

### `stream()` / `astream()`

Stream model responses with a Freeplay-hosted prompt (simple use cases).

**Parameters:** Same as `invoke()`

**Yields:** Chunks from the model's streaming response

**Async:** Use `astream()` with the same parameters for async streaming.

## State Management

When using agents with checkpointers, you can access LangGraph's state management features via the `unwrap()` method. This is necessary because `FreeplayAgent` extends `RunnableBindingBase` (LangChain's official wrapper pattern) which provides automatic metadata injection but doesn't directly expose CompiledStateGraph-specific methods.

### Core Invocation (Works Directly)

All standard invocation methods work without `unwrap()`:

```python
agent = freeplay.create_agent(
    prompt_name="assistant",
    variables={"task": "help users"},
    checkpointer=MemorySaver()
)

# ✅ All of these work directly - no unwrap needed
result = agent.invoke({"messages": [...]})
stream = agent.stream({"messages": [...]})
batched = agent.batch([...])
graph = agent.get_graph()
```

### State Management (Requires unwrap())

For CompiledStateGraph-specific methods, use `unwrap()`:

#### Inspecting Agent State

```python
from langgraph.checkpoint.memory import MemorySaver

agent = freeplay.create_agent(
    prompt_name="assistant",
    variables={"city": "SF"},
    checkpointer=MemorySaver()
)

config = {"configurable": {"thread_id": "user-123"}}

# Run agent
agent.invoke(
    {"messages": [HumanMessage(content="Hello")]},
    config=config
)

# Inspect state via unwrap()
state = agent.unwrap().get_state(config)
print(f"Current messages: {state.values['messages']}")
print(f"Next steps: {state.next}")
```

#### Human-in-the-Loop Workflows

```python
agent = freeplay.create_agent(
    prompt_name="booking-assistant",
    variables={"service": "flights"},
    tools=[book_flight],
    checkpointer=MemorySaver()
)

config = {"configurable": {"thread_id": "booking-456"}}

# Agent runs and stops before booking (if configured with interrupt_before)
result = agent.invoke(
    {"messages": [HumanMessage(content="Book flight to Paris")]},
    config={**config, "interrupt_before": ["book_flight"]}
)

# Review and approve
print("Agent wants to book flight. Approve? (y/n)")
if input() == "y":
    # Update state to continue
    agent.unwrap().update_state(
        config,
        {"approval": "granted"},
        as_node="human"
    )
    
    # Resume execution
    result = agent.invoke(None, config=config)
```

#### Multi-Agent Systems

```python
# For agents with nested subgraphs
coordinator_agent = freeplay.create_agent(
    prompt_name="coordinator",
    variables={"role": "orchestrator"}
)

# Access subgraph information
subgraphs = coordinator_agent.unwrap().get_subgraphs(recurse=True)
print(f"Available sub-agents: {list(subgraphs.keys())}")
```

#### State History

```python
# View execution history
config = {"configurable": {"thread_id": "thread-123"}}

for state in agent.unwrap().get_state_history(config, limit=5):
    print(f"Checkpoint: {state.config['configurable']['checkpoint_id']}")
    print(f"Messages: {len(state.values['messages'])}")
```

### Methods Requiring unwrap()

**State Access:**
- `get_state(config)` / `aget_state(config)` - Get current state snapshot
- `get_state_history(config)` / `aget_state_history(config)` - View history

**State Modification:**
- `update_state(config, values)` / `aupdate_state(config, values)` - Manual state updates
- `bulk_update_state(config, updates)` / `abulk_update_state(config, updates)` - Batch updates

**Advanced Features:**
- `get_subgraphs()` / `aget_subgraphs()` - Access nested agents
- `clear_cache()` / `aclear_cache()` - Clear LLM response cache

### Type Safety with unwrap()

For full type hints when using state methods:

```python
from typing import cast
from langgraph.graph.state import CompiledStateGraph

agent = freeplay.create_agent(...)

# Option 1: Direct unwrap (works at runtime)
state = agent.unwrap().get_state(config)

# Option 2: Cast for full type hints
compiled = cast(CompiledStateGraph, agent.unwrap())
state = compiled.get_state(config)  # ✅ Full IDE autocomplete
```

## Observability

The SDK automatically instruments your LangChain and LangGraph applications with OpenTelemetry. All traces are sent to Freeplay with the following metadata:

- Input variables
- Prompt template version ID
- Environment name
- Test run and test case IDs (if provided)

All metadata is injected automatically without requiring extra configuration or manual instrumentation.

## Architecture

The library uses LangChain's official `RunnableBindingBase` pattern to inject Freeplay metadata into all agent invocations. This provides:

- **LangChain-Idiomatic**: Uses the same pattern as `.bind()`, `.with_config()`, `.with_retry()` throughout LangChain
- **Automatic Coverage**: ALL Runnable methods work automatically (invoke, ainvoke, stream, astream, batch, abatch, astream_events, transform, atransform, etc.)
- **Type Safety**: Generic typing with proper IDE autocomplete for invocation methods
- **No Config Mutation**: User configurations are never modified
- **Future-Proof**: New LangChain methods automatically supported via inheritance
- **State Management via unwrap()**: Access to CompiledStateGraph-specific methods for checkpointing and state operations

**Key Points:**
- `FreeplayAgent` extends `RunnableBindingBase` and uses `config_factories` for metadata injection
- Client methods (`invoke`, `stream`, etc.) use `.with_config()` to bind metadata (LangChain's official pattern)
- Both approaches follow LangChain's patterns used throughout the ecosystem

## Provider Support

The SDK supports automatic model instantiation for the following providers:

- **OpenAI**: Requires `langchain-openai` package
- **Anthropic**: Requires `langchain-anthropic` package
- **Vertex AI**: Requires `langchain-google-vertexai` package

Install the required provider package:

```bash
pip install langchain-openai
# or
pip install langchain-anthropic
# or
pip install langchain-google-vertexai
```
