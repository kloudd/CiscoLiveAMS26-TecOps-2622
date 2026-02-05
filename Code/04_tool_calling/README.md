# Demo 04: Tool Calling & Agent Brain

## Overview
These demos show how to give LLMs the ability to call external functions (tools).

## Demos

| File | Description | Slide Reference |
|------|-------------|-----------------|
| `01_defining_tools.py` | Creating tools with @tool | Slide: "The @tool Decorator" |
| `02_math_agent.py` | Full ReAct agent from scratch | Slide: "Math Agent Example" |
| `03_react_agent_shortcut.py` | Using create_react_agent() | Slide: "create_react_agent" |

## Running the Demos

```bash
# Set your API key
export OPENAI_API_KEY="sk-..."

# Run each demo
python 01_defining_tools.py      # No API key needed
python 02_math_agent.py          # Requires API key
python 03_react_agent_shortcut.py  # Requires API key
```

## Key Concepts

### The ReAct Loop
```
User Query → Agent (LLM) → Tool Call → Execute Tool → Result → Agent → Response
                ↑                                              │
                └──────────────────────────────────────────────┘
```

### Tool Definition
```python
@tool
def my_tool(arg: str) -> str:
    """
    Description for the LLM.
    
    Use when: [conditions]
    Do NOT use for: [exceptions]
    """
    return result
```

### Two Ways to Build Agents

1. **Manual (Demo 02):** Full control, custom state
2. **create_react_agent (Demo 03):** Quick setup, standard behavior
