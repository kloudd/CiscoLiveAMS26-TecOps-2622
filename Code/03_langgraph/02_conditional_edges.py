"""
=============================================================================
DEMO 02: Conditional Edges
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 03 - LangGraph Deep Dive

Conditional edges let you make DECISIONS in your graph.
"If X, go to Node A. Otherwise, go to Node B."
=============================================================================
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# =============================================================================
# STEP 1: Define State
# =============================================================================

class State(TypedDict):
    """State with a counter and status."""
    counter: int
    status: str

print("=" * 60)
print("DEMO: Conditional Edges")
print("=" * 60)

# =============================================================================
# STEP 2: Define Nodes
# =============================================================================

def increment(state: State) -> dict:
    """Increment the counter by 1."""
    current = state["counter"]
    new_value = current + 1
    print(f"   🔄 increment: {current} → {new_value}")
    return {"counter": new_value}

def finalize(state: State) -> dict:
    """Mark as complete."""
    print(f"   🏁 finalize: Reached target!")
    return {"status": "complete"}

# =============================================================================
# STEP 3: Define Conditional Function
# =============================================================================
# This function DECIDES where to go next

def should_continue(state: State) -> str:
    """
    Decide whether to continue incrementing or stop.
    
    Returns:
        "continue" - if counter < 5 (go back to increment)
        "stop" - if counter >= 5 (go to finalize)
    """
    if state["counter"] < 5:
        return "continue"
    else:
        return "stop"

print("\n📋 Conditional Logic:")
print("   if counter < 5: → go to 'increment' (loop)")
print("   if counter >= 5: → go to 'finalize' (done)")

# =============================================================================
# STEP 4: Build the Graph with Conditional Edges
# =============================================================================

builder = StateGraph(State)

# Add nodes
builder.add_node("increment", increment)
builder.add_node("finalize", finalize)

# Add edges
builder.add_edge(START, "increment")  # Start at increment

# CONDITIONAL EDGE: After increment, decide where to go
builder.add_conditional_edges(
    "increment",           # Source node
    should_continue,       # Function that returns "continue" or "stop"
    {
        "continue": "increment",  # Loop back to increment!
        "stop": "finalize"        # Or go to finalize
    }
)

builder.add_edge("finalize", END)  # finalize → END

# Compile
app = builder.compile()

# =============================================================================
# STEP 5: Visualize the Graph
# =============================================================================

print("\n📊 Graph Structure:")
print("""
    ┌─────────┐
    │  START  │
    └────┬────┘
         │
    ┌────▼────┐
    │increment│◄─────┐
    └────┬────┘      │
         │           │
    ┌────▼────┐      │
    │ check   │      │
    │counter<5│      │
    └────┬────┘      │
    Yes  │  No       │
    ┌────┘  └────┐   │
    │            │   │
    └────────────┘   │  (loop back)
                     │
              ┌──────▼─────┐
              │  finalize  │
              └──────┬─────┘
                     │
              ┌──────▼─────┐
              │    END     │
              └────────────┘
""")

# =============================================================================
# STEP 6: Run and Watch the Loop!
# =============================================================================

print("-" * 60)
print("🚀 Running the Graph (starting at counter=0)")
print("-" * 60)

result = app.invoke({"counter": 0, "status": "pending"})

print(f"\n📤 Final Result: {result}")

# =============================================================================
# STEP 7: Run with Different Starting Value
# =============================================================================

print("\n" + "-" * 60)
print("🚀 Running again (starting at counter=3)")
print("-" * 60)

result2 = app.invoke({"counter": 3, "status": "pending"})

print(f"\n📤 Final Result: {result2}")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 60)
print("💡 Key Takeaways:")
print("=" * 60)
print("""
1. Conditional edges use a FUNCTION to decide routing
2. The function returns a STRING (the edge name)
3. You map strings to node names in a dictionary
4. This enables LOOPS - essential for agents!

Common Pattern for Agents:
   
   def should_continue(state):
       if state["messages"][-1].tool_calls:
           return "tools"    # LLM wants to use tools
       return "end"          # LLM is done
""")

print("✅ Demo complete!")
