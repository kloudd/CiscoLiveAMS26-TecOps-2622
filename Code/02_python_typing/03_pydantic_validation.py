"""
=============================================================================
DEMO 03: Pydantic Validation
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 02 - Python Typing Essentials

This demo shows how Pydantic validates data at RUNTIME.
Essential for catching LLM errors before they crash your code!
=============================================================================
"""

from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Literal

# =============================================================================
# STEP 1: Define a Pydantic Model
# =============================================================================

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

# =============================================================================
# STEP 2: Valid Data - Success!
# =============================================================================

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

# =============================================================================
# STEP 3: Invalid Data - Caught Immediately!
# =============================================================================

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

# =============================================================================
# STEP 4: Invalid Data - Out of Range
# =============================================================================

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

# =============================================================================
# STEP 5: Invalid Data - Invalid Literal
# =============================================================================

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

# =============================================================================
# STEP 6: Why This Matters for Agents
# =============================================================================

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
