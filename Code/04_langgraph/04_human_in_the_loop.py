"""
=============================================================================
DEMO 04: Human-in-the-Loop — Config Push Approval
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 03 - LangGraph Deep Dive

Before pushing a config change to a network device, the graph pauses
and asks the operator for approval via real input().
Only if the operator types 'yes' does execution continue.
=============================================================================
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# =============================================================================
# STEP 1: State
# =============================================================================

class State(TypedDict):
    device: str
    config_lines: str     # config commands to push
    status: str

# =============================================================================
# STEP 2: Nodes
# =============================================================================

def validate_config(state: State) -> dict:
    """Validate the proposed config change (syntax check, etc.)."""
    device = state["device"]
    lines = state["config_lines"]
    line_count = len(lines.strip().splitlines())
    print(f"\n  Validating config for {device} ({line_count} lines) ... OK")
    return {"status": f"validated — {line_count} lines ready for {device}"}


def push_config(state: State) -> dict:
    """
    Push the config to the device.
    This is the DANGEROUS step — interrupt_before pauses here.
    """
    device = state["device"]
    print(f"  Pushing config to {device} ...")
    print(f"  ---")
    for line in state["config_lines"].strip().splitlines():
        print(f"    {device}(config)# {line}")
    print(f"  ---")
    return {"status": f"config pushed to {device} successfully"}


def confirm_result(state: State) -> dict:
    """Verify the push and report."""
    print(f"  Verification complete: {state['status']}")
    return {}

# =============================================================================
# STEP 3: Build Graph with interrupt_before
# =============================================================================
#
#  START → validate_config ──── INTERRUPT ──── push_config → confirm_result → END
#                                  ↑
#                         operator must approve

builder = StateGraph(State)
builder.add_node("validate_config", validate_config)
builder.add_node("push_config", push_config)
builder.add_node("confirm_result", confirm_result)

builder.add_edge(START, "validate_config")
builder.add_edge("validate_config", "push_config")
builder.add_edge("push_config", "confirm_result")
builder.add_edge("confirm_result", END)

memory = MemorySaver()
graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["push_config"],   # pause before the dangerous step
)

# =============================================================================
# STEP 4: Run the Demo
# =============================================================================

if __name__ == "__main__":
    print("=" * 55)
    print("  LangGraph Demo — Human-in-the-Loop Config Push")
    print("=" * 55)

    # --- Visualise the graph ---
    print("\nGraph (Mermaid):\n")
    print(graph.get_graph().draw_mermaid())

    config = {"configurable": {"thread_id": "change-request-4021"}}

    proposed_config = """\
interface GigabitEthernet0/1
 description Uplink to R2-CORE
 ip address 10.0.12.1 255.255.255.252
 no shutdown"""

    initial_state = {
        "device": "R1-CORE",
        "config_lines": proposed_config,
        "status": "pending",
    }

    # --- Phase 1: run until interrupt ---
    print("\n[Phase 1] Validating config ...")
    result = graph.invoke(initial_state, config=config)
    print(f"  Status: {result['status']}")

    # --- Phase 2: show what's pending ---
    pending = graph.get_state(config)
    print(f"\n  Graph is paused before: {pending.next}")
    print(f"  Device : {pending.values['device']}")
    print(f"  Config :")
    for line in pending.values["config_lines"].strip().splitlines():
        print(f"    {line}")

    # --- Phase 3: ask the operator ---
    print("\n" + "-" * 55)
    answer = input("  Approve this config push? (yes/no): ").strip().lower()
    print("-" * 55)

    if answer == "yes":
        # Resume from checkpoint — pass None to continue where we left off
        print("\n[Phase 2] Operator approved — pushing config ...")
        final = graph.invoke(None, config=config)
        print(f"\n  Final status: {final['status']}")
    else:
        print("\n  Operator rejected the change. Config was NOT pushed.")

    print("\n" + "=" * 55)
