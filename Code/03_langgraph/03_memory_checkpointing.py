"""
=============================================================================
DEMO 03: Memory and Checkpointing
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 03 - LangGraph Deep Dive

Checkpointing gives your agent MEMORY across conversations.
Each thread_id maintains its own conversation history.
=============================================================================
"""

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import operator

# =============================================================================
# STEP 1: Define State with History
# =============================================================================

class State(TypedDict):
    """State that tracks conversation history."""
    # Messages will be APPENDED (not replaced) thanks to the reducer
    messages: Annotated[List[str], operator.add]
    
    # Current response (replaced each time)
    response: str

print("=" * 60)
print("DEMO: Memory and Checkpointing")
print("=" * 60)

# =============================================================================
# STEP 2: Define a Simple Echo Node
# =============================================================================

def echo_node(state: State) -> dict:
    """
    Echoes the last message and shows conversation history.
    """
    messages = state["messages"]
    last_message = messages[-1] if messages else "No message"
    
    # Create response showing history
    history_count = len(messages)
    response = f"Echo: '{last_message}' (Message #{history_count} in this conversation)"
    
    return {"response": response}

# =============================================================================
# STEP 3: Build the Graph
# =============================================================================

builder = StateGraph(State)
builder.add_node("echo", echo_node)
builder.add_edge(START, "echo")
builder.add_edge("echo", END)

# =============================================================================
# STEP 4: Compile WITHOUT Memory (for comparison)
# =============================================================================

print("\n📋 Part 1: Without Memory")
print("-" * 60)

app_no_memory = builder.compile()

# First call
result1 = app_no_memory.invoke({
    "messages": ["Hello!"],
    "response": ""
})
print(f"Call 1: {result1['response']}")

# Second call - no memory of first call!
result2 = app_no_memory.invoke({
    "messages": ["How are you?"],
    "response": ""
})
print(f"Call 2: {result2['response']}")

print("\n❌ Notice: Each call starts fresh. No memory!")

# =============================================================================
# STEP 5: Compile WITH Memory
# =============================================================================

print("\n" + "=" * 60)
print("📋 Part 2: With Memory (Checkpointing)")
print("-" * 60)

# Create a memory checkpointer
memory = MemorySaver()

# Compile with checkpointing enabled
app_with_memory = builder.compile(checkpointer=memory)

# Define a thread ID - this identifies the conversation
config = {"configurable": {"thread_id": "user-alice-123"}}

# First call
result1 = app_with_memory.invoke(
    {"messages": ["Hello!"], "response": ""},
    config=config  # Pass the config!
)
print(f"Call 1: {result1['response']}")

# Second call - SAME thread_id, so it remembers!
result2 = app_with_memory.invoke(
    {"messages": ["How are you?"], "response": ""},
    config=config
)
print(f"Call 2: {result2['response']}")

# Third call
result3 = app_with_memory.invoke(
    {"messages": ["What's the weather?"], "response": ""},
    config=config
)
print(f"Call 3: {result3['response']}")

print("\n✅ Notice: Message count increases! Memory works!")

# =============================================================================
# STEP 6: Different Thread = Different Memory
# =============================================================================

print("\n" + "-" * 60)
print("📋 Part 3: Different Users = Different Memory")
print("-" * 60)

# New user with different thread_id
config_bob = {"configurable": {"thread_id": "user-bob-456"}}

result_bob = app_with_memory.invoke(
    {"messages": ["Hi, I'm Bob!"], "response": ""},
    config=config_bob
)
print(f"Bob's Call 1: {result_bob['response']}")

# Back to Alice - still has her history!
result_alice = app_with_memory.invoke(
    {"messages": ["Remember me?"], "response": ""},
    config  # Alice's config
)
print(f"Alice's Call 4: {result_alice['response']}")

# =============================================================================
# STEP 7: Inspecting State
# =============================================================================

print("\n" + "-" * 60)
print("📋 Part 4: Inspecting Saved State")
print("-" * 60)

# Get current state for Alice
alice_state = app_with_memory.get_state(config)
print(f"Alice's full message history:")
for i, msg in enumerate(alice_state.values["messages"], 1):
    print(f"   {i}. {msg}")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 60)
print("💡 Key Takeaways:")
print("=" * 60)
print("""
1. MemorySaver stores state after each step
2. thread_id identifies unique conversations
3. Same thread_id = same conversation history
4. Different thread_id = fresh start

Usage Pattern:

   memory = MemorySaver()
   app = workflow.compile(checkpointer=memory)
   
   config = {"configurable": {"thread_id": "unique-id"}}
   app.invoke(input, config=config)

For Production:
   Use SqliteSaver or PostgresSaver for persistence!
""")

print("✅ Demo complete!")
