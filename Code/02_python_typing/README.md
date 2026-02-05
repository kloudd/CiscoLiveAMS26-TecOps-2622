# Demo 02: Python Typing Essentials

## Overview
These demos cover Python typing concepts essential for building LangGraph agents.

## Demos

| File | Description | Slide Reference |
|------|-------------|-----------------|
| `01_typeddict_basics.py` | TypedDict for structured dicts | Slide: "TypedDict: Structured Dictionaries" |
| `02_annotated_reducers.py` | Annotated types and reducers | Slide: "Annotated: Adding Metadata" |
| `03_pydantic_validation.py` | Pydantic runtime validation | Slide: "Pydantic: The Schema Enforcer" |

## Running the Demos

```bash
# These demos don't require API keys!
python 01_typeddict_basics.py
python 02_annotated_reducers.py
python 03_pydantic_validation.py
```

## Key Concepts

1. **TypedDict** - Define structure for dictionaries (used for LangGraph State)
2. **Annotated** - Attach metadata to types (used for reducers)
3. **Reducers** - Control how state updates are merged (APPEND vs REPLACE)
4. **Pydantic** - Runtime validation (catches LLM errors immediately)

## Connection to LangGraph

```python
from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Annotated + add_messages = messages are APPENDED
    messages: Annotated[List, add_messages]
    
    # No annotation = values are REPLACED
    current_task: str
```
