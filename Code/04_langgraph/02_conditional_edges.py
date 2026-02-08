"""
=============================================================================
DEMO 02: Conditional Edges — Device Health Triage
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 03 - LangGraph Deep Dive

Conditional edges let the graph make DECISIONS.
Here a device health check routes to different actions
depending on severity: healthy → log, warning → alert, critical → escalate.
=============================================================================
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# =============================================================================
# STEP 1: Define the State
# =============================================================================

class State(TypedDict):
    device: str
    cpu: int          # CPU utilisation %
    severity: str     # healthy / warning / critical
    action_taken: str

# =============================================================================
# STEP 2: Define the Nodes
# =============================================================================

def check_health(state: State) -> dict:
    """Evaluate CPU and assign a severity level."""
    cpu = state["cpu"]
    if cpu >= 90:
        severity = "critical"
    elif cpu >= 70:
        severity = "warning"
    else:
        severity = "healthy"
    print(f"  [{state['device']}] CPU {cpu}% → severity: {severity}")
    return {"severity": severity}


def log_ok(state: State) -> dict:
    """Device is fine — just log it."""
    msg = f"{state['device']} is healthy (CPU {state['cpu']}%). No action needed."
    print(f"  LOG: {msg}")
    return {"action_taken": msg}


def send_alert(state: State) -> dict:
    """CPU is elevated — send a warning alert."""
    msg = f"ALERT: {state['device']} CPU at {state['cpu']}%. Monitor closely."
    print(f"  ALERT: {msg}")
    return {"action_taken": msg}


def escalate(state: State) -> dict:
    """CPU is critical — page the on-call engineer."""
    msg = f"PAGE ON-CALL: {state['device']} CPU at {state['cpu']}%! Immediate action required."
    print(f"  ESCALATE: {msg}")
    return {"action_taken": msg}

# =============================================================================
# STEP 3: Routing Function
# =============================================================================
# Returns a string that maps to the next node.

def route_by_severity(state: State) -> str:
    return state["severity"]      # "healthy" | "warning" | "critical"

# =============================================================================
# STEP 4: Build the Graph
# =============================================================================

builder = StateGraph(State)

builder.add_node("check_health", check_health)
builder.add_node("healthy", log_ok)
builder.add_node("warning", send_alert)
builder.add_node("critical", escalate)

builder.add_edge(START, "check_health")

# Conditional edge: route to different nodes based on severity
builder.add_conditional_edges(
    "check_health",
    route_by_severity,
    {
        "healthy": "healthy",
        "warning": "warning",
        "critical": "critical",
    },
)

builder.add_edge("healthy", END)
builder.add_edge("warning", END)
builder.add_edge("critical", END)

graph = builder.compile()

# =============================================================================
# STEP 5: Run with Different Scenarios
# =============================================================================

if __name__ == "__main__":
    print("=" * 55)
    print("  LangGraph Demo — Device Health Triage")
    print("=" * 55)

    # --- Visualise the graph ---
    print("\nGraph (Mermaid):\n")
    print(graph.get_graph().draw_mermaid())

    scenarios = [
        {"device": "R1-CORE",      "cpu": 35, "severity": "", "action_taken": ""},
        {"device": "SW-DIST-02",   "cpu": 78, "severity": "", "action_taken": ""},
        {"device": "FW-EDGE-01",   "cpu": 95, "severity": "", "action_taken": ""},
    ]

    for scenario in scenarios:
        print(f"\n--- {scenario['device']}  (CPU {scenario['cpu']}%) ---")
        result = graph.invoke(scenario)
        print(f"  Final → {result['action_taken']}")
