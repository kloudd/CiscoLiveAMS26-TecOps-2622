# Demo 01: LLM & GenAI Foundations

## Overview
These demos cover the basics of working with Large Language Models using LangChain.

## Demos

| File | Description | Slide Reference |
|------|-------------|-----------------|
| `01_first_llm_call.py` | Your first LLM call | Slide: "Your First LLM Call" |
| `02_system_messages.py` | Using System/User messages | Slide: "Adding System Messages" |
| `03_structured_output.py` | Pydantic for structured output | Slide: "Structured Output" |

## Running the Demos

```bash
# Set your API key
export OPENAI_API_KEY="sk-..."

# Run each demo
python 01_first_llm_call.py
python 02_system_messages.py
python 03_structured_output.py
```

## Key Concepts

1. **LLM Initialization** - Creating a ChatOpenAI instance
2. **Temperature** - Control randomness (0=deterministic, 1=creative)
3. **Message Roles** - System, Human, Assistant
4. **Structured Output** - Using Pydantic for type-safe responses
