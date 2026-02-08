"""
=============================================================================
DEMO 01: Hello World Graph
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 03 - LangGraph Deep Dive

Your first LangGraph! A simple graph that says "Hello World".
This demonstrates State, Nodes, and Edges.
=============================================================================
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# =============================================================================
# STEP 1: Define the State
# =============================================================================
# State is the shared memory that flows through all nodes

class State(TypedDict):
    """Simple state with just a text field."""
    text: str

print("=" * 60)
print("DEMO: Hello World Graph")
print("=" * 60)

print("\n📋 Step 1: Define State")
print("   class State(TypedDict):")
print("       text: str")

# =============================================================================
# STEP 2: Define Nodes
# =============================================================================
# Nodes are functions that:
#   - Receive the current State
#   - Return a partial State update

def node_hello(state: State) -> dict:
    """First node: Sets text to 'Hello'"""
    print("   🔄 node_hello executing...")
    return {"text": "Hello"}

def node_world(state: State) -> dict:
    """Second node: Appends ' World' to text"""
    print("   🔄 node_world executing...")
    current_text = state["text"]
    return {"text": current_text + " World"}

print("\n📋 Step 2: Define Nodes")
print("   node_hello: returns {'text': 'Hello'}")
print("   node_world: appends ' World' to text")

# =============================================================================
# STEP 3: Build the Graph
# =============================================================================

print("\n📋 Step 3: Build Graph")

# Create a StateGraph with our State type
builder = StateGraph(State)

# Add nodes to the graph
builder.add_node("hello", node_hello)
builder.add_node("world", node_world)
print("   ✓ Added nodes: hello, world")

# Add edges (the flow)
builder.add_edge(START, "hello")    # START → hello
builder.add_edge("hello", "world")  # hello → world
builder.add_edge("world", END)      # world → END
print("   ✓ Added edges: START → hello → world → END")

# =============================================================================
# STEP 4: Compile the Graph
# =============================================================================

print("\n📋 Step 4: Compile")

app = builder.compile()
print("   ✓ Graph compiled successfully!")

# =============================================================================
# STEP 5: Visualize the Graph (text representation)
# =============================================================================

print("\n📊 Graph Structure:")
print("""
    ┌─────────┐
    │  START  │
    └────┬────┘
         │
    ┌────▼────┐
    │  hello  │  → Sets text = "Hello"
    └────┬────┘
         │
    ┌────▼────┐
    │  world  │  → Appends " World"
    └────┬────┘
         │
    ┌────▼────┐
    │   END   │
    └─────────┘
""")

# =============================================================================
# STEP 6: Run the Graph
# =============================================================================

print("-" * 60)
print("🚀 Running the Graph...")
print("-" * 60)

# Invoke with initial state
initial_state = {"text": ""}
print(f"\n   Input: {initial_state}")

result = app.invoke(initial_state)

print(f"\n   Output: {result}")

# =============================================================================
# STEP 7: Understanding the Flow
# =============================================================================

print("\n" + "=" * 60)
print("💡 What Happened:")
print("=" * 60)
print("""
1. We started with: {"text": ""}

2. node_hello ran:
   - Received: {"text": ""}
   - Returned: {"text": "Hello"}
   - State became: {"text": "Hello"}

3. node_world ran:
   - Received: {"text": "Hello"}
   - Returned: {"text": "Hello World"}
   - State became: {"text": "Hello World"}

4. Reached END with final state!
""")

print("✅ Demo complete!")
