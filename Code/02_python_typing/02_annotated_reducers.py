"""
=============================================================================
DEMO 02: Annotated and Reducers
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 02 - Python Typing Essentials

This demo explains Annotated types and reducers - how LangGraph
knows whether to REPLACE or APPEND state updates.
=============================================================================
"""

from typing import TypedDict, Annotated, List
import operator

# =============================================================================
# STEP 1: The Problem - State Updates
# =============================================================================
# When multiple nodes update the same field, what happens?

print("=" * 60)
print("DEMO: Annotated and Reducers")
print("=" * 60)

print("""
🤔 The Problem:

Node A returns: {"messages": ["Hello"]}
Node B returns: {"messages": ["World"]}

What should the final state be?

Option 1 (REPLACE): {"messages": ["World"]}     ❌ Lost "Hello"!
Option 2 (APPEND):  {"messages": ["Hello", "World"]}  ✅ Kept both!
""")

# =============================================================================
# STEP 2: Annotated - Adding Metadata to Types
# =============================================================================
# Annotated lets us attach extra information to a type

print("-" * 60)
print("Solution: Annotated with Reducers")
print("-" * 60)

# Basic syntax
# Annotated[<base_type>, <metadata>]

# Example: A list that should be appended to (not replaced)
MessagesType = Annotated[List[str], operator.add]

print("""
Annotated[List[str], operator.add]
         ^^^^^^^^^   ^^^^^^^^^^^^
         Base type   Reducer function
         
The reducer tells LangGraph HOW to combine updates.
""")

# =============================================================================
# STEP 3: Common Reducers
# =============================================================================

print("-" * 60)
print("Common Reducers:")
print("-" * 60)

# Reducer 1: operator.add - Concatenate lists
print("""
1. operator.add - Concatenate lists
   
   existing = ["Hello"]
   new = ["World"]
   result = existing + new  →  ["Hello", "World"]
""")

# Reducer 2: Custom function
def merge_dicts(existing: dict, new: dict) -> dict:
    """Merge dictionaries, new values overwrite."""
    return {**existing, **new}

print("""
2. Custom reducer - Merge dictionaries
   
   existing = {"R1": "up"}
   new = {"R2": "down"}
   result = {**existing, **new}  →  {"R1": "up", "R2": "down"}
""")

# =============================================================================
# STEP 4: Complete State with Reducers
# =============================================================================

class AgentState(TypedDict):
    """State demonstrating different reducers."""
    
    # APPEND: New messages are added to the list
    messages: Annotated[List[str], operator.add]
    
    # APPEND: Counter increases
    step_count: Annotated[int, operator.add]
    
    # REPLACE: No reducer = simple replacement (default)
    current_task: str


print("-" * 60)
print("Example: State with Reducers")
print("-" * 60)

# Simulating how LangGraph processes updates

# Initial state
state = {
    "messages": ["User: Check R1"],
    "step_count": 0,
    "current_task": "starting"
}
print(f"Initial: {state}")

# Node 1 returns an update
update1 = {
    "messages": ["Agent: Checking R1..."],  # Will APPEND
    "step_count": 1,                         # Will ADD
    "current_task": "checking"               # Will REPLACE
}

# Simulate reducer application
state["messages"] = state["messages"] + update1["messages"]  # operator.add
state["step_count"] = state["step_count"] + update1["step_count"]  # operator.add
state["current_task"] = update1["current_task"]  # replace

print(f"After Node 1: {state}")

# Node 2 returns another update
update2 = {
    "messages": ["Agent: R1 is online!"],
    "step_count": 1,
    "current_task": "done"
}

state["messages"] = state["messages"] + update2["messages"]
state["step_count"] = state["step_count"] + update2["step_count"]
state["current_task"] = update2["current_task"]

print(f"After Node 2: {state}")

# =============================================================================
# STEP 5: The add_messages Reducer (LangGraph built-in)
# =============================================================================

print("\n" + "=" * 60)
print("💡 LangGraph's add_messages Reducer")
print("=" * 60)

print("""
LangGraph provides a special reducer for chat messages:

from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

This reducer:
  ✓ Appends new messages
  ✓ Handles message deduplication
  ✓ Works with LangChain message types
  
We'll use this in the LangGraph demos!
""")

print("✅ Demo complete!")
