# Demo 08: RAG & Production Patterns

## Overview
Patterns for running agents reliably in production environments.

## Demos

| File | Description | Slide Reference |
|------|-------------|-----------------|
| `01_rag_tool_selection.py` | RAG to select relevant tools | Slide: "RAG for Tool Selection" |
| `02_production_patterns.py` | Error handling, cost tracking | Slide: "Production Patterns" |

## Running the Demos

```bash
# Set your API key
export OPENAI_API_KEY="sk-..."

# Run demos
python 01_rag_tool_selection.py
python 02_production_patterns.py
```

## Key Patterns

### 1. RAG Tool Selection
```python
# Instead of giving LLM ALL tools:
agent = create_react_agent(llm, all_50_tools)  # Bad!

# Use RAG to select relevant ones:
relevant = get_relevant_tools(query, k=5)
agent = create_react_agent(llm, relevant)  # Good!
```

### 2. Cost Tracking
```python
class CostTracker:
    def add_usage(self, tokens):
        if self.total_cost > self.max_cost:
            raise CostLimitExceeded()
```

### 3. Retry with Backoff
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential())
def call_api():
    return llm.invoke(messages)
```

### 4. Tool Sandboxing
```python
ALLOWED_TOOLS = {"read": [...], "write": [...], "admin": [...]}

def can_execute(tool_name, permission_level):
    return tool_name in ALLOWED_TOOLS[permission_level]
```
