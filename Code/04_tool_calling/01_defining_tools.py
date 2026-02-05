"""
=============================================================================
DEMO 01: Defining Tools
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 04 - Tool Calling & Agent Brain

Learn how to define tools using the @tool decorator.
Good tool definitions = smart tool selection by the LLM!
=============================================================================
"""

from langchain_core.tools import tool
from typing import List

# =============================================================================
# STEP 1: Simple Tool Definition
# =============================================================================

print("=" * 60)
print("DEMO: Defining Tools")
print("=" * 60)

@tool
def multiply(a: int, b: int) -> int:
    """
    Multiply two numbers together.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        The product of a and b
    """
    return a * b

print("\n📋 Tool 1: multiply")
print(f"   Name: {multiply.name}")
print(f"   Description: {multiply.description}")

# =============================================================================
# STEP 2: Tool with Complex Types
# =============================================================================

@tool
def get_device_status(hostname: str, include_interfaces: bool = False) -> dict:
    """
    Check the operational status of a network device.
    
    Use this tool when you need to know:
    - If a device is online or offline
    - The device's current health metrics
    - Interface status (if include_interfaces is True)
    
    Args:
        hostname: The device hostname (e.g., "SW-CORE-01", "R1")
        include_interfaces: Whether to include interface details
    
    Returns:
        Dictionary with device status information
    """
    # Simulated response (in real code, this would call an API)
    result = {
        "hostname": hostname,
        "status": "online",
        "uptime_hours": 720,
        "health_score": 95
    }
    
    if include_interfaces:
        result["interfaces"] = [
            {"name": "Gi0/1", "status": "up"},
            {"name": "Gi0/2", "status": "down"}
        ]
    
    return result

print("\n📋 Tool 2: get_device_status")
print(f"   Name: {get_device_status.name}")
print(f"   Description: {get_device_status.description[:50]}...")

# =============================================================================
# STEP 3: View Tool Schema (What LLM Sees)
# =============================================================================

print("\n" + "-" * 60)
print("🔍 Tool Schema (What the LLM Receives):")
print("-" * 60)

# The LLM sees this JSON schema to understand how to call the tool
schema = get_device_status.args_schema.schema()
print(f"""
{{
  "name": "{get_device_status.name}",
  "description": "{get_device_status.description[:60]}...",
  "parameters": {{
    "type": "object",
    "properties": {{
      "hostname": {{"type": "string", "description": "The device hostname..."}},
      "include_interfaces": {{"type": "boolean", "default": false}}
    }},
    "required": ["hostname"]
  }}
}}
""")

# =============================================================================
# STEP 4: Calling Tools Directly
# =============================================================================

print("-" * 60)
print("🔧 Calling Tools Directly:")
print("-" * 60)

# You can call tools like normal functions
result1 = multiply.invoke({"a": 5, "b": 6})
print(f"\n   multiply(5, 6) = {result1}")

result2 = get_device_status.invoke({
    "hostname": "SW-CORE-01",
    "include_interfaces": True
})
print(f"\n   get_device_status('SW-CORE-01'):")
print(f"      Status: {result2['status']}")
print(f"      Health: {result2['health_score']}%")
print(f"      Interfaces: {len(result2['interfaces'])} found")

# =============================================================================
# STEP 5: Why Good Docstrings Matter
# =============================================================================

print("\n" + "=" * 60)
print("💡 Why Docstrings Matter:")
print("=" * 60)

print("""
The LLM READS your docstring to decide WHEN to use a tool!

❌ Bad:
   @tool
   def check(x):
       \"\"\"Check something.\"\"\"
   
   → LLM doesn't know when to use this!

✅ Good:
   @tool
   def get_device_status(hostname: str):
       \"\"\"
       Check if a network device is online.
       
       Use when the user asks about:
       - Device health or status
       - Whether something is reachable
       - Uptime information
       
       Do NOT use for:
       - Configuration changes
       - Historical data
       \"\"\"
   
   → LLM knows exactly when to use this!
""")

print("✅ Demo complete!")
