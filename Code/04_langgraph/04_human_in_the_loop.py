"""
=============================================================================
DEMO 04: Human-in-the-Loop
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 03 - LangGraph Deep Dive

Pause execution before dangerous actions for human approval.
Essential for production agents that perform critical operations!
=============================================================================
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# =============================================================================
# STEP 1: Define State
# =============================================================================

class State(TypedDict):
    """State for a device management workflow."""
    device: str
    action: str
    status: str
    approved: bool

print("=" * 60)
print("DEMO: Human-in-the-Loop")
print("=" * 60)

# =============================================================================
# STEP 2: Define Nodes
# =============================================================================

def plan_action(state: State) -> dict:
    """Plan what action to take on the device."""
    device = state["device"]
    action = state["action"]
    print(f"   📋 Planning: {action} on {device}")
    return {"status": f"Ready to {action} {device}"}

def execute_action(state: State) -> dict:
    """
    Execute the planned action.
    ⚠️ This is the DANGEROUS node - we'll pause before this!
    """
    device = state["device"]
    action = state["action"]
    print(f"   ⚡ EXECUTING: {action} on {device}!")
    return {"status": f"Completed: {action} on {device}"}

def report_result(state: State) -> dict:
    """Report the final result."""
    print(f"   📊 Reporting: {state['status']}")
    return {}

# =============================================================================
# STEP 3: Build Graph with Interrupt
# =============================================================================

builder = StateGraph(State)

builder.add_node("plan", plan_action)
builder.add_node("execute", execute_action)  # ⚠️ Dangerous!
builder.add_node("report", report_result)

builder.add_edge(START, "plan")
builder.add_edge("plan", "execute")
builder.add_edge("execute", "report")
builder.add_edge("report", END)

# Compile with:
# 1. checkpointer - needed for interrupt/resume
# 2. interrupt_before - pause BEFORE this node

memory = MemorySaver()

app = builder.compile(
    checkpointer=memory,
    interrupt_before=["execute"]  # ⚠️ Pause before execute!
)

print("\n📊 Graph Structure:")
print("""
    ┌─────────┐
    │  START  │
    └────┬────┘
         │
    ┌────▼────┐
    │  plan   │
    └────┬────┘
         │
    ════════════  ← INTERRUPT HERE (human approval)
         │
    ┌────▼────┐
    │ execute │  ⚠️ Dangerous action
    └────┬────┘
         │
    ┌────▼────┐
    │ report  │
    └────┬────┘
         │
    ┌────▼────┐
    │   END   │
    └─────────┘
""")

# =============================================================================
# STEP 4: Run Until Interrupt
# =============================================================================

print("-" * 60)
print("🚀 Phase 1: Run until interrupt")
print("-" * 60)

config = {"configurable": {"thread_id": "reboot-request-001"}}

# Initial input
input_state = {
    "device": "SW-CORE-01",
    "action": "reboot",
    "status": "pending",
    "approved": False
}

# Run - will stop before "execute"
result = app.invoke(input_state, config=config)

print(f"\n📊 Current Status: {result['status']}")

# =============================================================================
# STEP 5: Check What's Next
# =============================================================================

print("\n" + "-" * 60)
print("🔍 Phase 2: Check pending action")
print("-" * 60)

state = app.get_state(config)
print(f"   Next node(s): {state.next}")
print(f"   Device: {state.values['device']}")
print(f"   Action: {state.values['action']}")

# =============================================================================
# STEP 6: Simulate Human Decision
# =============================================================================

print("\n" + "-" * 60)
print("👤 Phase 3: Human Decision")
print("-" * 60)

print("""
   ┌────────────────────────────────────────┐
   │  APPROVAL REQUIRED                     │
   │                                        │
   │  Action: REBOOT                        │
   │  Device: SW-CORE-01                    │
   │                                        │
   │  [APPROVE]  [REJECT]                   │
   └────────────────────────────────────────┘
""")

# Simulate approval (in real app, this would be user input)
approved = True  # Change to False to test rejection

if approved:
    print("   ✅ Human approved the action!")
    
    # Resume execution (pass None to continue from checkpoint)
    print("\n" + "-" * 60)
    print("🚀 Phase 4: Resuming execution")
    print("-" * 60)
    
    final_result = app.invoke(None, config=config)
    
    print(f"\n📊 Final Status: {final_result['status']}")
    
else:
    print("   ❌ Human rejected the action!")
    print("   Workflow cancelled. Device not rebooted.")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 60)
print("💡 Key Takeaways:")
print("=" * 60)
print("""
1. interrupt_before pauses BEFORE a specified node
2. Requires checkpointer to save state at pause point
3. Use get_state() to inspect what's pending
4. Resume with invoke(None, config) to continue

Use Cases:
   ✓ Dangerous actions (delete, shutdown, reboot)
   ✓ Expensive operations (external API calls)
   ✓ Sensitive data access
   ✓ Compliance requirements

Code Pattern:

   app = workflow.compile(
       checkpointer=memory,
       interrupt_before=["dangerous_node"]
   )
   
   # Run until pause
   result = app.invoke(input, config)
   
   # Review, then continue
   if human_approves():
       final = app.invoke(None, config)
""")

print("✅ Demo complete!")
