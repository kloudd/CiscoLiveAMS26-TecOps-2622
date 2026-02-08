"""
=============================================================================
Section 02: Python Typing Essentials - All Exercises
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam

This file contains all the exercises for Section 02:
  - TypedDict Basics
  - Annotated and Reducers
  - Pydantic Validation
=============================================================================
"""

# ---------------------------------------------------------------------
# EXERCISE 01: TypedDict Basics
# ---------------------------------------------------------------------
# TypedDict gives us structured dictionaries with type safety.
# This is ESSENTIAL for defining LangGraph State!

from typing import TypedDict, List, Optional

# STEP 1: The Problem - Regular Dictionaries
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

# STEP 2: The Solution - TypedDict

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

# STEP 3: TypedDict with Optional and List
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

# STEP 4: Why This Matters for LangGraph

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


# ---------------------------------------------------------------------
# EXERCISE 02: Annotated and Reducers
# ---------------------------------------------------------------------
# Annotated types and reducers - how LangGraph knows whether
# to REPLACE or APPEND state updates.

from typing import Annotated
import operator

# STEP 1: The Problem - State Updates
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

# STEP 2: Annotated - Adding Metadata to Types

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

# STEP 3: Common Reducers

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

# STEP 4: Complete State with Reducers

class AgentStateWithReducers(TypedDict):
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

# STEP 5: The add_messages Reducer (LangGraph built-in)

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


# ---------------------------------------------------------------------
# EXERCISE 03: Pydantic Validation
# ---------------------------------------------------------------------
# Pydantic validates data at RUNTIME - essential for catching
# LLM errors before they crash your code!

from pydantic import BaseModel, Field, ValidationError
from typing import Literal

# STEP 1: Define a Pydantic Model

print("=" * 60)
print("DEMO: Pydantic Validation")
print("=" * 60)

class NetworkDevice(BaseModel):
    """
    Schema for network device information.
    
    Pydantic will validate ALL data against this schema.
    Invalid data raises ValidationError immediately!
    """
    
    hostname: str = Field(
        description="Device hostname like SW-CORE-01"
    )
    
    device_type: Literal["switch", "router", "firewall", "ap"] = Field(
        description="Type of network device"
    )
    
    ip_address: str = Field(
        description="Management IP address"
    )
    
    port_count: int = Field(
        ge=1,  # Must be >= 1
        le=1000,  # Must be <= 1000
        description="Number of ports"
    )
    
    is_managed: bool = Field(
        default=True,
        description="Whether device is under management"
    )
    
    vlans: Optional[List[int]] = Field(
        default=None,
        description="List of configured VLAN IDs"
    )

print("\n🔧 Defined Schema: NetworkDevice")
print("   - hostname: str (required)")
print("   - device_type: 'switch'|'router'|'firewall'|'ap'")
print("   - ip_address: str (required)")
print("   - port_count: int (1-1000)")
print("   - is_managed: bool (default: True)")
print("   - vlans: Optional[List[int]]")

# STEP 2: Valid Data - Success!

print("\n" + "-" * 60)
print("TEST 1: Valid Data")
print("-" * 60)

valid_data = {
    "hostname": "SW-CORE-01",
    "device_type": "switch",
    "ip_address": "192.168.1.1",
    "port_count": 48,
    "vlans": [10, 20, 30]
}

device = NetworkDevice(**valid_data)

print("✅ Validation passed!")
print(f"   hostname: {device.hostname}")
print(f"   device_type: {device.device_type}")
print(f"   port_count: {device.port_count}")
print(f"   is_managed: {device.is_managed}  (default applied)")

# STEP 3: Invalid Data - Caught Immediately!

print("\n" + "-" * 60)
print("TEST 2: Invalid Data - Wrong Type")
print("-" * 60)

invalid_data_1 = {
    "hostname": "SW-01",
    "device_type": "switch",
    "ip_address": "192.168.1.1",
    "port_count": "not a number"  # ❌ Should be int!
}

try:
    device = NetworkDevice(**invalid_data_1)
except ValidationError as e:
    print("❌ ValidationError caught!")
    print(f"   Error: {e.errors()[0]['msg']}")
    print(f"   Field: {e.errors()[0]['loc']}")

# STEP 4: Invalid Data - Out of Range

print("\n" + "-" * 60)
print("TEST 3: Invalid Data - Out of Range")
print("-" * 60)

invalid_data_2 = {
    "hostname": "SW-01",
    "device_type": "switch",
    "ip_address": "192.168.1.1",
    "port_count": 5000  # ❌ Max is 1000!
}

try:
    device = NetworkDevice(**invalid_data_2)
except ValidationError as e:
    print("❌ ValidationError caught!")
    print(f"   Error: {e.errors()[0]['msg']}")
    print(f"   Value: 5000, Max allowed: 1000")

# STEP 5: Invalid Data - Invalid Literal

print("\n" + "-" * 60)
print("TEST 4: Invalid Data - Not in Allowed Values")
print("-" * 60)

invalid_data_3 = {
    "hostname": "SW-01",
    "device_type": "printer",  # ❌ Not in allowed types!
    "ip_address": "192.168.1.1",
    "port_count": 48
}

try:
    device = NetworkDevice(**invalid_data_3)
except ValidationError as e:
    print("❌ ValidationError caught!")
    print(f"   Error: 'printer' is not a valid device type")
    print(f"   Allowed: switch, router, firewall, ap")

# STEP 6: Why This Matters for Agents

print("\n" + "=" * 60)
print("💡 Why Pydantic Matters for AI Agents")
print("=" * 60)

print("""
LLMs sometimes return invalid data:
  - Wrong types ("48" instead of 48)
  - Missing fields
  - Invalid values

Without Pydantic:
  ❌ Code crashes somewhere unexpected
  ❌ Hard to debug
  ❌ User sees cryptic errors

With Pydantic:
  ✅ Invalid data caught IMMEDIATELY
  ✅ Clear error messages
  ✅ Can retry or handle gracefully

Example with LLM:
  structured_llm = llm.with_structured_output(NetworkDevice)
  
  # If LLM returns invalid data, you get a clear error
  # instead of a crash later in your code!
""")

print("✅ Demo complete!")
