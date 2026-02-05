# TECOPS-2622: AI Agents in Action
## Demo Code - Cisco Live Amsterdam 2026

This folder contains all the demo code from the presentation.
Each section has its own folder with standalone, well-commented Python files.

---

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your API key
export OPENAI_API_KEY="sk-..."

# 4. Run any demo!
cd 01_llm_basics
python 01_first_llm_call.py
```

---

## Demo Sections

| Section | Description | API Key? |
|---------|-------------|----------|
| `01_llm_basics/` | First LLM calls, system messages, structured output | Yes |
| `02_python_typing/` | TypedDict, Annotated, Pydantic | No |
| `03_langgraph/` | State, nodes, edges, checkpointing | No* |
| `04_tool_calling/` | Tools, ReAct agent, math agent | Yes |
| `05_mcp/` | MCP server, architecture concepts | Yes** |
| `08_rag_production/` | RAG tool selection, production patterns | Yes |
| `09_evals_testing/` | LLM-as-judge, regression testing | Yes |

*Some LangGraph demos require API key when using LLM nodes
**MCP concepts demo doesn't require API key

---

## Demo Files Quick Reference

### 01_llm_basics/
- `01_first_llm_call.py` - Your first call to GPT-5.2
- `02_system_messages.py` - Controlling LLM behavior
- `03_structured_output.py` - Pydantic + LLM = type-safe responses

### 02_python_typing/
- `01_typeddict_basics.py` - Why TypedDict matters for LangGraph
- `02_annotated_reducers.py` - How state updates work
- `03_pydantic_validation.py` - Runtime validation for LLM outputs

### 03_langgraph/
- `01_hello_world_graph.py` - Your first graph
- `02_conditional_edges.py` - Decision points and loops
- `03_memory_checkpointing.py` - Persistent memory
- `04_human_in_the_loop.py` - Pause for approval

### 04_tool_calling/
- `01_defining_tools.py` - Creating tools with @tool
- `02_math_agent.py` - Full ReAct agent from scratch
- `03_react_agent_shortcut.py` - Using create_react_agent()

### 05_mcp/
- `01_mcp_server.py` - Build a custom MCP server
- `02_mcp_concepts.py` - Architecture explained (no API needed)
- `03_mcp_client.py` - Connect to server & use tools with agent

### 08_rag_production/
- `01_rag_tool_selection.py` - RAG to select relevant tools
- `02_production_patterns.py` - Error handling, cost tracking

### 09_evals_testing/
- `01_llm_as_judge.py` - Use LLM to evaluate responses
- `02_regression_testing.py` - Track performance over time

---

## Environment Setup

### Required Environment Variables

```bash
# OpenAI API Key (required for most demos)
export OPENAI_API_KEY="sk-..."

# Optional: Anthropic for Claude models
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional: LangSmith for tracing
export LANGCHAIN_TRACING_V2="true"
export LANGCHAIN_API_KEY="ls-..."
```

### Creating a .env File

```bash
# Create .env file in the code/ directory
cat > .env << EOF
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
EOF

# Load in Python:
from dotenv import load_dotenv
load_dotenv()
```

---

## Tips for Presenters

1. **Run demos in order** - Each section builds on the previous
2. **Use `temperature=0`** - Consistent outputs during presentation
3. **Have fallback slides** - In case of API issues
4. **Test API access beforehand** - Ensure keys work in venue network

---

## Model Used

All demos use **GPT-5.2** (`gpt-5.2` in code).

To use a different model, change the model parameter:
```python
llm = ChatOpenAI(model="gpt-5.2")  # Current
llm = ChatOpenAI(model="gpt-4o")   # Alternative
```

---

## Support

For questions during/after the session:
- Sumit Kan - Principal Architect
- Abhay - Software Consulting Engineer

Happy coding! 🚀
