"""
=============================================================================
DEMO 01: Building an MCP Server
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 05 - Model Context Protocol (MCP)

This demo creates a custom MCP server that exposes network tools.

To run:
    python 01_mcp_server.py
    python 01_mcp_server.py --port 8080  (custom port)

Then in another terminal:
    python 03_mcp_client.py
=============================================================================
"""

import sys
import argparse

# Parse arguments to get the port
parser = argparse.ArgumentParser(description="MCP Network Tools Server")
parser.add_argument("--port", type=int, default=8000,
                    help="Port for server (default: 8000)")
args = parser.parse_args()

from mcp.server.fastmcp import FastMCP

# =============================================================================
# Logging Helper
# =============================================================================

def log(message: str):
    """Log messages visibly."""
    print(f"[SERVER] {message}", file=sys.stderr, flush=True)

# =============================================================================
# STEP 1: Initialize the MCP Server
# =============================================================================

# Create an MCP server with port configuration
mcp = FastMCP("NetworkTools", port=args.port)

log("=" * 50)
log("MCP Server: NetworkTools initialized")
log("=" * 50)

# =============================================================================
# STEP 2: Define Tools
# =============================================================================

@mcp.tool()
def ping_device(ip_address: str) -> dict:
    """
    Check if a network device is reachable.
    
    Use this tool when you need to:
    - Verify basic connectivity to a device
    - Check if an IP address is responding
    
    Args:
        ip_address: The IP address to ping (e.g., "192.168.1.1")
    
    Returns:
        dict with reachability status and latency
    """
    log(f"🔧 TOOL CALLED: ping_device(ip_address='{ip_address}')")
    
    import random
    
    reachable = random.choice([True, True, True, False])  # 75% success
    latency = random.randint(1, 50) if reachable else None
    
    result = {
        "ip_address": ip_address,
        "reachable": reachable,
        "latency_ms": latency,
        "message": "Host is up" if reachable else "Host unreachable"
    }
    log(f"   → Result: {result}")
    return result


@mcp.tool()
def get_device_info(hostname: str) -> dict:
    """
    Get detailed information about a network device.
    
    Use this tool when you need:
    - Device model and serial number
    - Software version
    - Management IP
    
    Args:
        hostname: The device hostname (e.g., "SW-CORE-01")
    
    Returns:
        dict with device information
    """
    log(f"🔧 TOOL CALLED: get_device_info(hostname='{hostname}')")
    
    # Simulated device database
    devices = {
        "SW-CORE-01": {
            "hostname": "SW-CORE-01",
            "model": "Catalyst 9300",
            "serial": "FCW2145L0FP",
            "software": "IOS-XE 17.9.3",
            "management_ip": "192.168.1.1",
            "uptime_days": 45,
            "health_score": 95
        },
        "R1": {
            "hostname": "R1",
            "model": "ISR 4451",
            "serial": "FTX1842AHN2",
            "software": "IOS-XE 17.6.4",
            "management_ip": "192.168.1.254",
            "uptime_days": 120,
            "health_score": 98
        }
    }
    
    if hostname in devices:
        result = devices[hostname]
    else:
        result = {
            "error": f"Device '{hostname}' not found",
            "available_devices": list(devices.keys())
        }
    
    log(f"   → Result: {result}")
    return result


@mcp.tool()
def list_devices(device_type: str = "all") -> list:
    """
    List all managed network devices.
    
    Use this tool to:
    - Get an inventory of devices
    - Filter by device type
    
    Args:
        device_type: Filter by type ("router", "switch", "ap", or "all")
    
    Returns:
        List of device names
    """
    log(f"🔧 TOOL CALLED: list_devices(device_type='{device_type}')")
    
    # Simulated inventory
    inventory = {
        "router": ["R1", "R2", "R-EDGE-01"],
        "switch": ["SW-CORE-01", "SW-CORE-02", "SW-DIST-01", "SW-ACCESS-01"],
        "ap": ["AP-FLOOR-1", "AP-FLOOR-2", "AP-CONF-01"]
    }
    
    if device_type.lower() == "all":
        all_devices = []
        for devices in inventory.values():
            all_devices.extend(devices)
        result = sorted(all_devices)
    else:
        result = inventory.get(device_type.lower(), [])
    
    log(f"   → Result: {result}")
    return result


@mcp.tool()
def check_interface(hostname: str, interface: str) -> dict:
    """
    Check the status of a specific interface on a device.
    
    Args:
        hostname: The device hostname
        interface: The interface name (e.g., "GigabitEthernet0/1")
    
    Returns:
        Interface status and statistics
    """
    log(f"🔧 TOOL CALLED: check_interface(hostname='{hostname}', interface='{interface}')")
    
    import random
    
    status = random.choice(["up", "up", "up", "down"])
    
    result = {
        "device": hostname,
        "interface": interface,
        "status": status,
        "speed": "1 Gbps" if status == "up" else "N/A",
        "duplex": "full" if status == "up" else "N/A",
        "rx_bytes": random.randint(1000000, 9999999) if status == "up" else 0,
        "tx_bytes": random.randint(1000000, 9999999) if status == "up" else 0,
        "errors": random.randint(0, 10)
    }
    log(f"   → Result: {result}")
    return result


# =============================================================================
# STEP 3: Run the Server
# =============================================================================

if __name__ == "__main__":
    log("")
    log("📋 Tools available:")
    log("   - ping_device(ip_address)")
    log("   - get_device_info(hostname)")
    log("   - list_devices(device_type)")
    log("   - check_interface(hostname, interface)")
    log("")
    log(f"🚀 Starting MCP server on port {args.port}...")
    log(f"   URL: http://localhost:{args.port}/sse")
    log("")
    log("   In another terminal, run:")
    log(f"   python 03_mcp_client.py --url http://localhost:{args.port}/sse")
    log("-" * 50)
    
    mcp.run(transport="sse")
