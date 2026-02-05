"""
=============================================================================
DEMO 02: Math Agent (Tool Calling in Action)
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 04 - Tool Calling & Agent Brain

A complete agent that uses tools to solve math problems.
This demonstrates the full ReAct loop: Reason → Act → Observe → Repeat
=============================================================================
"""

import os
from typing import TypedDict, Annotated, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# =============================================================================
# STEP 1: Define Tools
# =============================================================================

print("=" * 60)
print("DEMO: Math Agent")
print("=" * 60)

@tool
def multiply(a: int, b: int) -> int:
    """
    Multiply two numbers together.
    Use this when you need to calculate a product.
    """
    print(f"   🔧 Tool called: multiply({a}, {b})")
    return a * b

@tool
def add(a: int, b: int) -> int:
    """
    Add two numbers together.
    Use this when you need to calculate a sum.
    """
    print(f"   🔧 Tool called: add({a}, {b})")
    return a + b

@tool
def divide(a: int, b: int) -> float:
    """
    Divide the first number by the second.
    Use this when you need to calculate a quotient.
    """
    print(f"   🔧 Tool called: divide({a}, {b})")
    if b == 0:
        return "Error: Cannot divide by zero"
    return a / b

tools = [multiply, add, divide]

print("\n📋 Tools defined:")
for t in tools:
    print(f"   - {t.name}: {t.description.split('.')[0]}")

# =============================================================================
# STEP 2: Create LLM with Tools
# =============================================================================

llm = ChatOpenAI(
    model="gpt-5.2",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Bind tools to the LLM
llm_with_tools = llm.bind_tools(tools)

print("\n✅ LLM created and tools bound")

# =============================================================================
# STEP 3: Define State
# =============================================================================

class State(TypedDict):
    """Agent state with message history."""
    # Messages with add_messages reducer (appends, doesn't replace)
    messages: Annotated[List[BaseMessage], add_messages]

# =============================================================================
# STEP 4: Define Nodes
# =============================================================================

def agent_node(state: State) -> dict:
    """
    The 'brain' - calls the LLM with tools.
    LLM decides whether to use a tool or respond directly.
    """
    print("\n   🧠 Agent thinking...")
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    
    # Check what the LLM decided
    if response.tool_calls:
        print(f"   🧠 Agent decided to use tool(s): {[tc['name'] for tc in response.tool_calls]}")
    else:
        print("   🧠 Agent decided to respond directly")
    
    return {"messages": [response]}

# ToolNode is pre-built - it executes tool calls and returns results
tool_node = ToolNode(tools)

# =============================================================================
# STEP 5: Define Routing Logic
# =============================================================================

def should_continue(state: State) -> str:
    """
    Decide: Should we execute tools or finish?
    
    If the LLM's last message has tool_calls → go to tools
    Otherwise → we're done (END)
    """
    last_message = state["messages"][-1]
    
    # Check if LLM wants to use tools
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    # No tool calls = LLM is done, go to END
    return END

# =============================================================================
# STEP 6: Build the Graph
# =============================================================================

print("\n📋 Building the agent graph...")

builder = StateGraph(State)

# Add nodes
builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)

# Add edges
builder.add_edge(START, "agent")  # Start at agent

# Conditional edge: after agent, check if we need tools
builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",  # Go to tools if needed
        END: END           # Otherwise, finish
    }
)

# After tools execute, go back to agent (THE LOOP!)
builder.add_edge("tools", "agent")

# Compile
app = builder.compile()

print("✅ Agent graph compiled!")

# =============================================================================
# STEP 7: Visualize the Graph
# =============================================================================

print("\n📊 Agent Graph Structure:")
print("""
    ┌─────────┐
    │  START  │
    └────┬────┘
         │
    ┌────▼────┐
    │  agent  │◄─────────────┐
    │ (LLM)   │              │
    └────┬────┘              │
         │                   │
    ┌────▼────┐              │
    │  has    │              │
    │ tools?  │              │
    └────┬────┘              │
    Yes  │  No               │
    ┌────┘  └────┐           │
    │            │           │
    ▼            ▼           │
┌───────┐    ┌──────┐        │
│ tools │    │ END  │        │
│(exec) │    └──────┘        │
└───┬───┘                    │
    │                        │
    └────────────────────────┘
""")

# =============================================================================
# STEP 8: Run the Agent!
# =============================================================================

print("=" * 60)
print("🚀 Running the Agent")
print("=" * 60)

# Test query
query = "What is 23 times 47, then add 100?"

print(f"\n📤 User: {query}")
print("\n" + "-" * 60)

result = app.invoke({
    "messages": [HumanMessage(content=query)]
})

# Get the final response
final_message = result["messages"][-1]
print("\n" + "-" * 60)
print(f"\n📥 Agent: {final_message.content}")

# =============================================================================
# STEP 9: Show the Full Conversation
# =============================================================================

print("\n" + "=" * 60)
print("📜 Full Conversation History:")
print("=" * 60)

for i, msg in enumerate(result["messages"]):
    msg_type = type(msg).__name__
    
    if msg_type == "HumanMessage":
        print(f"\n{i+1}. 👤 User: {msg.content}")
    elif msg_type == "AIMessage":
        if msg.tool_calls:
            print(f"\n{i+1}. 🤖 Agent: [Calling tools: {[tc['name'] for tc in msg.tool_calls]}]")
        else:
            print(f"\n{i+1}. 🤖 Agent: {msg.content}")
    elif msg_type == "ToolMessage":
        print(f"\n{i+1}. 🔧 Tool ({msg.name}): {msg.content}")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 60)
print("💡 Key Takeaways:")
print("=" * 60)
print("""
The ReAct Loop:
1. Agent REASONS about the query
2. Agent ACTS by calling tools (or responding)
3. Tool results are OBSERVED by the agent
4. Agent REASONS again with new information
5. Repeat until done!

This pattern works for ANY tools:
- Network device APIs
- Database queries  
- Browser automation
- File operations
- And more!
""")

print("✅ Demo complete!")
