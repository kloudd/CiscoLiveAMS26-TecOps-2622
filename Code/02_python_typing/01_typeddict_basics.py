"""
=============================================================================
DEMO 01: TypedDict Basics
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 02 - Python Typing Essentials

This demo shows how to use TypedDict for structured dictionaries.
TypedDict is ESSENTIAL for defining LangGraph State!
=============================================================================
"""

from typing import TypedDict, List, Optional

# =============================================================================
# STEP 1: The Problem - Regular Dictionaries
# =============================================================================
# Regular dicts have no type safety - typos cause bugs!

print("=" * 60)
print("DEMO: TypedDict Basics")
print("=" * 60)

# Without TypedDict - no autocomplete, no type checking
regular_dict = {
    "hostname": "SW-01",
    "ip_address": "192.168.1.1",
    "status": "online"
}

# Easy to make typos - no error until runtime!
# regular_dict["statsu"]  # Typo! Would crash at runtime

print("\n❌ Problem with regular dicts:")
print("   - No autocomplete in IDE")
print("   - Typos not caught until runtime")
print("   - No documentation of expected keys")

# =============================================================================
# STEP 2: The Solution - TypedDict
# =============================================================================
# TypedDict gives us structure AND type hints

class DeviceInfo(TypedDict):
    """A network device with typed fields."""
    hostname: str
    ip_address: str
    status: str
    port_count: int

# Now we get autocomplete and type checking!
device: DeviceInfo = {
    "hostname": "SW-01",
    "ip_address": "192.168.1.1",
    "status": "online",
    "port_count": 48
}

print("\n✅ With TypedDict:")
print("   - IDE autocomplete works")
print("   - Type checker catches errors")
print("   - Self-documenting code")

print("\n" + "-" * 60)
print("Device Info:")
print(f"   Hostname: {device['hostname']}")
print(f"   IP: {device['ip_address']}")
print(f"   Status: {device['status']}")
print(f"   Ports: {device['port_count']}")

# =============================================================================
# STEP 3: TypedDict with Optional and List
# =============================================================================
# Real-world example: LangGraph Agent State

class AgentState(TypedDict):
    """State for a network automation agent."""
    
    # Required fields
    query: str                      # The user's question
    devices: List[str]              # List of device names to check
    
    # Optional fields (might be None)
    results: Optional[dict]         # Results from checking devices
    error: Optional[str]            # Any error message
    
    # List of messages (for conversation history)
    messages: List[str]

# Example state
state: AgentState = {
    "query": "Check health of all core switches",
    "devices": ["SW-CORE-01", "SW-CORE-02"],
    "results": None,      # Not yet populated
    "error": None,        # No errors
    "messages": ["User asked about core switches"]
}

print("\n" + "-" * 60)
print("Agent State Example:")
print(f"   Query: {state['query']}")
print(f"   Devices: {state['devices']}")
print(f"   Results: {state['results']}")
print(f"   Messages: {len(state['messages'])} message(s)")

# =============================================================================
# STEP 4: Why This Matters for LangGraph
# =============================================================================

print("\n" + "=" * 60)
print("💡 Why TypedDict Matters for LangGraph:")
print("=" * 60)
print("""
LangGraph uses TypedDict to define the STATE of your agent.

Every node in your graph:
  1. Receives the current State as input
  2. Returns a partial State update as output

TypedDict ensures:
  ✓ All nodes agree on the state structure
  ✓ Type checker catches mismatches
  ✓ IDE helps you write correct code
""")

print("✅ Demo complete!")
