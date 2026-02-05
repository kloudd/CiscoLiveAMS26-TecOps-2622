# Demo 03: LangGraph Deep Dive

## Overview
These demos cover the core concepts of LangGraph - the framework for building stateful agents.

## Demos

| File | Description | Slide Reference |
|------|-------------|-----------------|
| `01_hello_world_graph.py` | Your first graph | Slide: "Hello World Graph" |
| `02_conditional_edges.py` | Decision points and loops | Slide: "Conditional Edges" |
| `03_memory_checkpointing.py` | Persistent memory | Slide: "Checkpointing" |
| `04_human_in_the_loop.py` | Pause for approval | Slide: "Human-in-the-Loop" |

## Running the Demos

```bash
# These demos don't require API keys!
python 01_hello_world_graph.py
python 02_conditional_edges.py
python 03_memory_checkpointing.py
python 04_human_in_the_loop.py
```

## Key Concepts

### Core Elements
1. **State** - TypedDict that holds all data
2. **Nodes** - Functions that process and update state
3. **Edges** - Connections between nodes

### Advanced Features
4. **Conditional Edges** - Dynamic routing based on state
5. **Checkpointing** - Memory across conversations
6. **Human-in-the-Loop** - Pause for approval

## The Agent Pattern (Preview)

```
START → Agent → Has Tools? → Yes → Execute Tools → Back to Agent
                    ↓
                   No
                    ↓
                  END
```

This loop is implemented in Demo 04: Tool Calling!
