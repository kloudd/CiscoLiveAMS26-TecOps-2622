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

# =============================================================================
# STEP 1: A Simple Tool
# =============================================================================

@tool
def ping_device(hostname: str) -> str:
    """
    Ping a network device to check reachability.

    Args:
        hostname: The device hostname (e.g., "R1-CORE", "SW-DIST-02")

    Returns:
        A message indicating whether the device responded.
    """
    # Simulated (in production: subprocess or pyATS)
    reachable = hostname.upper() != "FW-EDGE-01"
    if reachable:
        return f"{hostname} is reachable (response time: 4ms)"
    return f"{hostname} is unreachable — request timed out"

# =============================================================================
# STEP 2: A Tool with Optional Parameters
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
    result = {
        "hostname": hostname,
        "status": "online",
        "uptime_hours": 720,
        "health_score": 95,
    }
    if include_interfaces:
        result["interfaces"] = [
            {"name": "Gi0/1", "status": "up", "speed": "1Gbps"},
            {"name": "Gi0/2", "status": "down", "speed": "—"},
        ]
    return result

# =============================================================================
# STEP 3: Inspect What the LLM Sees
# =============================================================================

if __name__ == "__main__":
    print("=" * 55)
    print("  Tool Calling Demo — Defining Tools")
    print("=" * 55)

    # -- Show tool metadata (this is what the LLM receives) --
    for t in [ping_device, get_device_status]:
        print(f"\nTool: {t.name}")
        print(f"  Description: {t.description[:80]}...")
        print(f"  Schema: {t.args_schema.schema()}")

    # -- Call the tools directly --
    print("\n" + "-" * 55)
    print("Calling tools directly:\n")

    print(f"  ping_device('R1-CORE')      → {ping_device.invoke({'hostname': 'R1-CORE'})}")
    print(f"  ping_device('FW-EDGE-01')   → {ping_device.invoke({'hostname': 'FW-EDGE-01'})}")

    status = get_device_status.invoke({"hostname": "SW-CORE-01", "include_interfaces": True})
    print(f"\n  get_device_status('SW-CORE-01', include_interfaces=True):")
    print(f"    status: {status['status']}, health: {status['health_score']}%")
    for iface in status["interfaces"]:
        print(f"    {iface['name']}: {iface['status']} ({iface['speed']})")
