"""
=============================================================================
DEMO 01: Hello World Graph — Device Ping Check
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 03 - LangGraph Deep Dive

Your first LangGraph! A two-node graph that pings a network device
and reports the result. Demonstrates State, Nodes, and Edges.
=============================================================================
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# =============================================================================
# STEP 1: Define the State
# =============================================================================
# State = the shared data that flows through every node in the graph.

class State(TypedDict):
    device: str
    ip: str
    reachable: bool
    message: str

# =============================================================================
# STEP 2: Define the Nodes
# =============================================================================
# Each node is a plain function:  receives State → returns partial update.

def ping_device(state: State) -> dict:
    """Simulate pinging the device."""
    ip = state["ip"]
    print(f"  Pinging {state['device']} ({ip}) ...")
    # Simulated result (in real life: subprocess ping / netmiko / pyATS)
    reachable = not ip.startswith("10.0.99")   # .99 subnet = unreachable for demo
    return {"reachable": reachable}

def report_status(state: State) -> dict:
    """Build a human-readable status message."""
    if state["reachable"]:
        msg = f"{state['device']} ({state['ip']}) is UP and reachable."
    else:
        msg = f"{state['device']} ({state['ip']}) is DOWN — no response."
    print(f"  Result: {msg}")
    return {"message": msg}

# =============================================================================
# STEP 3: Build & Compile the Graph
# =============================================================================
#   START  →  ping_device  →  report_status  →  END

builder = StateGraph(State)
builder.add_node("ping_device", ping_device)
builder.add_node("report_status", report_status)

builder.add_edge(START, "ping_device")
builder.add_edge("ping_device", "report_status")
builder.add_edge("report_status", END)

graph = builder.compile()

# =============================================================================
# STEP 4: Run the Graph
# =============================================================================

if __name__ == "__main__":
    print("=" * 55)
    print("  LangGraph Demo — Device Ping Check")
    print("=" * 55)

    # --- Visualise the graph ---
    print("\nGraph (Mermaid):\n")
    print(graph.get_graph().draw_mermaid())

    # --- Test 1: reachable device ---
    print("\n--- Test 1: Core Router ---")
    result = graph.invoke({
        "device": "R1-CORE",
        "ip": "10.0.1.1",
        "reachable": False,
        "message": "",
    })
    print(f"  Final state → {result['message']}\n")

    # --- Test 2: unreachable device ---
    print("--- Test 2: Unreachable Switch ---")
    result = graph.invoke({
        "device": "SW-BRANCH-07",
        "ip": "10.0.99.7",
        "reachable": False,
        "message": "",
    })
    print(f"  Final state → {result['message']}")
