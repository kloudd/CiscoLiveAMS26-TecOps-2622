"""
=============================================================================
DEMO 03: Structured Output with Pydantic
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 01 - LLM & GenAI Foundations

This demo shows how to get structured JSON output from an LLM
using Pydantic models - essential for building reliable agents!
=============================================================================
"""

import os
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional

# =============================================================================
# STEP 1: Define a Pydantic Model
# =============================================================================
# Pydantic models define the STRUCTURE of the output we expect.
# The LLM will be constrained to return data matching this schema.

class DeviceStatus(BaseModel):
    """Schema for network device status information."""
    
    hostname: str = Field(
        description="The device hostname (e.g., 'R1', 'SW-CORE-01')"
    )
    is_online: bool = Field(
        description="Whether the device is currently reachable"
    )
    ip_address: str = Field(
        description="The management IP address"
    )
    uptime_hours: Optional[int] = Field(
        default=None,
        description="Hours since last reboot, if known"
    )

# =============================================================================
# STEP 2: Create LLM with Structured Output
# =============================================================================

llm = ChatOpenAI(
    model="gpt-5.2",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Bind the Pydantic model to the LLM
# Now the LLM will ALWAYS return data matching DeviceStatus
structured_llm = llm.with_structured_output(DeviceStatus)

# =============================================================================
# STEP 3: Get Structured Response
# =============================================================================

print("=" * 60)
print("DEMO: Structured Output with Pydantic")
print("=" * 60)

# Ask about a device - the LLM will return structured data
query = "Router R1 at 192.168.1.1 has been online for 720 hours"

print(f"\n📤 Input: '{query}'")
print("\n🔧 Expected Schema: DeviceStatus")
print("   - hostname: str")
print("   - is_online: bool")
print("   - ip_address: str")
print("   - uptime_hours: Optional[int]")

print("\n" + "-" * 60)

# Make the call
result = structured_llm.invoke(query)

# =============================================================================
# STEP 4: Use the Structured Data
# =============================================================================

print("\n📂 Full JSON Output:")
print(result.model_dump_json(indent=4))  # Pretty-print the JSON representation

print("\n" + "-" * 60)

print("📥 Structured Response:")
print(f"\n   Type: {type(result).__name__}")
print(f"   hostname: {result.hostname}")
print(f"   is_online: {result.is_online}")
print(f"   ip_address: {result.ip_address}")
print(f"   uptime_hours: {result.uptime_hours}")

# You can now use this data programmatically!
print("\n" + "-" * 60)
print("💡 Benefits of Structured Output:")
print("   ✓ Type-safe access to fields")
print("   ✓ Automatic validation")
print("   ✓ IDE autocomplete works!")
print("   ✓ No parsing needed")
print("-" * 60)

# Example: Using the structured data
if result.is_online:
    print(f"\n✅ {result.hostname} is healthy!")
    if result.uptime_hours and result.uptime_hours > 168:  # > 1 week
        print(f"   Uptime: {result.uptime_hours // 24} days")
else:
    print(f"\n⚠️  {result.hostname} is OFFLINE - investigate!")

print("\n✅ Demo complete!")
