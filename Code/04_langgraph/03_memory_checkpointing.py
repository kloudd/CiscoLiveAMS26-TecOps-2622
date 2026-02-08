"""
=============================================================================
DEMO 03: Memory & Checkpointing — Conversation History
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 03 - LangGraph Deep Dive

Checkpointing gives your graph MEMORY across invocations.
Same thread_id = same conversation.  Different thread_id = fresh start.

Example: two NOC operators (Alice & Bob) each have their own
conversation history with a network assistant. The graph remembers
who said what, and each operator's chat is independent.
=============================================================================
"""

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import operator

# =============================================================================
# STEP 1: State — conversation history that grows over time
# =============================================================================

class State(TypedDict):
    # operator.add reducer → new messages are APPENDED, never replaced
    messages: Annotated[List[str], operator.add]
    user_name: str
    user_input: str
    response: str

# =============================================================================
# STEP 2: Node — a simple network assistant that responds to queries
# =============================================================================

def assistant(state: State) -> dict:
    """Respond to the user's message and update the conversation."""
    name = state["user_name"]
    query = state["user_input"]

    # Simple rule-based responses (replace with LLM in production)
    q = query.lower()
    if "status" in q or "online" in q:
        reply = "All core devices are online. No alerts at this time."
    elif "cpu" in q:
        reply = "R1-CORE CPU is at 42%, SW-DIST-02 is at 78% (elevated)."
    elif "interface" in q or "errors" in q:
        reply = "Gi0/1 on SW-DIST-02 shows 12 CRC errors in the last hour."
    elif "ticket" in q or "incident" in q:
        reply = "Incident INC-4021 is open for SW-DIST-02 high CPU. Assigned to NetOps."
    else:
        reply = f"I can help with device status, CPU, interface errors, and tickets."

    return {
        "messages": [f"{name}: {query}", f"Assistant: {reply}"],
        "response": reply,
    }

# =============================================================================
# STEP 3: Build the Graph
# =============================================================================

builder = StateGraph(State)
builder.add_node("assistant", assistant)
builder.add_edge(START, "assistant")
builder.add_edge("assistant", END)

# =============================================================================
# STEP 4: Compile — without and with memory
# =============================================================================

graph_no_memory = builder.compile()

memory = MemorySaver()
graph_with_memory = builder.compile(checkpointer=memory)

# Helper to invoke cleanly
def ask(graph, name, message, config=None):
    state = {"messages": [], "user_name": name, "user_input": message, "response": ""}
    res = graph.invoke(state, config=config) if config else graph.invoke(state)
    return res

# =============================================================================
# STEP 5: Run the Demo
# =============================================================================

if __name__ == "__main__":
    print("=" * 55)
    print("  LangGraph Demo — Memory & Checkpointing")
    print("=" * 55)

    # --- Visualise the graph ---
    print("\nGraph (Mermaid):\n")
    print(graph_with_memory.get_graph().draw_mermaid())

    # ---- Part A: Without memory -------------------------------------------
    print("\n--- Part A: WITHOUT memory ---")
    ask(graph_no_memory, "Alice", "What is the device status?")
    res = ask(graph_no_memory, "Alice", "How about CPU?")
    print(f"  Conversation length: {len(res['messages'])} messages")
    print("  (Always 2 — no history carried over)\n")

    # ---- Part B: With memory (Alice) --------------------------------------
    print("--- Part B: WITH memory (Alice's session) ---")
    alice_cfg = {"configurable": {"thread_id": "alice-shift-001"}}

    conversations = [
        "What is the device status?",
        "How about CPU usage?",
        "Any interface errors?",
    ]
    for msg in conversations:
        res = ask(graph_with_memory, "Alice", msg, config=alice_cfg)
        print(f"  Alice: {msg}")
        print(f"    → {res['response']}")
        print(f"    (history: {len(res['messages'])} messages)")

    # ---- Part C: Bob gets a fresh session ---------------------------------
    print("\n--- Part C: Bob's session (separate history) ---")
    bob_cfg = {"configurable": {"thread_id": "bob-shift-002"}}

    res = ask(graph_with_memory, "Bob", "Any open tickets?", config=bob_cfg)
    print(f"  Bob: Any open tickets?")
    print(f"    → {res['response']}")
    print(f"    (history: {len(res['messages'])} messages — fresh start)")

    # ---- Part D: Inspect full conversation histories ----------------------
    print("\n--- Part D: Full conversation histories ---")

    print("\n  Alice's session:")
    alice_state = graph_with_memory.get_state(alice_cfg)
    for i, msg in enumerate(alice_state.values["messages"], 1):
        print(f"    {i}. {msg}")

    print(f"\n  Bob's session:")
    bob_state = graph_with_memory.get_state(bob_cfg)
    for i, msg in enumerate(bob_state.values["messages"], 1):
        print(f"    {i}. {msg}")

    print(f"\n  Alice has {len(alice_state.values['messages'])} messages.")
    print(f"  Bob has {len(bob_state.values['messages'])} messages.")
    print("  Each thread_id keeps its own conversation.\n")
    print("=" * 55)
