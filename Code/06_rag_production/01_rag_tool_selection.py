"""
=============================================================================
DEMO 01: RAG for Tool Selection
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 08 - RAG & Production Patterns

When you have MANY tools, the LLM can get confused or waste tokens.
RAG retrieves only the RELEVANT tools for each query before calling
the agent — better accuracy, lower cost.
=============================================================================
"""

import os
import math
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

# =============================================================================
# STEP 1: Define Many Network Tools
# =============================================================================

@tool
def get_device_status(hostname: str) -> dict:
    """Check if a device is online and get its health status."""
    return {"hostname": hostname, "status": "online", "health": 95}

@tool
def get_interface_stats(hostname: str, interface: str) -> dict:
    """Get traffic statistics for a specific interface."""
    return {"interface": interface, "rx_mbps": 450, "tx_mbps": 230}

@tool
def get_cpu_utilization(hostname: str) -> dict:
    """Get current CPU usage percentage for a device."""
    return {"hostname": hostname, "cpu_percent": 45}

@tool
def get_memory_utilization(hostname: str) -> dict:
    """Get current memory usage for a device."""
    return {"hostname": hostname, "memory_percent": 62}

@tool
def configure_vlan(switch: str, vlan_id: int, name: str) -> str:
    """Create or modify a VLAN on a switch."""
    return f"VLAN {vlan_id} ({name}) configured on {switch}"

@tool
def configure_interface(hostname: str, interface: str, config: str) -> str:
    """Apply configuration to an interface."""
    return f"Config applied to {interface} on {hostname}"

@tool
def backup_config(hostname: str) -> str:
    """Backup the running configuration of a device."""
    return f"Configuration backed up for {hostname}"

@tool
def restore_config(hostname: str, backup_id: str) -> str:
    """Restore a device configuration from backup."""
    return f"Configuration {backup_id} restored to {hostname}"

@tool
def reboot_device(hostname: str) -> str:
    """Reboot a network device. Use with caution!"""
    return f"Rebooting {hostname}..."

@tool
def get_neighbors(hostname: str) -> list:
    """Get CDP/LLDP neighbor information for a device."""
    return [{"neighbor": "SW-02", "interface": "Gi0/1"}]

@tool
def run_ping(source: str, destination: str) -> dict:
    """Run a ping from one device to another."""
    return {"source": source, "dest": destination, "success": True}

@tool
def run_traceroute(source: str, destination: str) -> list:
    """Run a traceroute from one device to another."""
    return [{"hop": 1, "ip": "10.0.0.1"}, {"hop": 2, "ip": destination}]

@tool
def get_logs(hostname: str, severity: str = "error") -> list:
    """Get syslog entries from a device."""
    return [{"timestamp": "2026-02-03 10:00", "message": "Interface down"}]

@tool
def create_ticket(title: str, description: str, priority: str) -> str:
    """Create a support ticket in the ticketing system."""
    return f"Ticket created: {title} (Priority: {priority})"

@tool
def send_alert(channel: str, message: str) -> str:
    """Send an alert to a monitoring channel (Slack, Teams, etc.)."""
    return f"Alert sent to {channel}"

ALL_TOOLS = [
    get_device_status, get_interface_stats, get_cpu_utilization,
    get_memory_utilization, configure_vlan, configure_interface,
    backup_config, restore_config, reboot_device, get_neighbors,
    run_ping, run_traceroute, get_logs, create_ticket, send_alert,
]

# =============================================================================
# STEP 2: Embed Tool Descriptions
# =============================================================================

embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))

# Build description text and a lookup map
tool_descriptions = [f"{t.name}: {t.description}" for t in ALL_TOOLS]
tool_mapping = dict(zip(tool_descriptions, ALL_TOOLS))

# Pre-compute vectors for all tool descriptions
tool_vectors = embeddings.embed_documents(tool_descriptions)

# =============================================================================
# STEP 3: RAG Retrieval Function
# =============================================================================

def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b)


def get_relevant_tools(query: str, k: int = 4) -> list:
    """Retrieve the k most relevant tools for a query using embeddings."""
    query_vec = embeddings.embed_query(query)
    scored = [
        (cosine_similarity(query_vec, tv), desc)
        for tv, desc in zip(tool_vectors, tool_descriptions)
    ]
    scored.sort(reverse=True)
    return [tool_mapping[desc] for _, desc in scored[:k]]

# =============================================================================
# STEP 4: Run the Demo
# =============================================================================

if __name__ == "__main__":
    print("=" * 55)
    print("  RAG Demo — Tool Selection")
    print("=" * 55)
    print(f"\n  Total tools available: {len(ALL_TOOLS)}")

    # --- Test retrieval ---
    test_queries = [
        "Is router R1 online?",
        "What's the CPU on SW-01?",
        "Configure VLAN 100 on the core switch",
        "Something broke, create a ticket",
    ]

    print("\n--- RAG Tool Retrieval (top 3 per query) ---\n")
    for q in test_queries:
        relevant = get_relevant_tools(q, k=3)
        tools_str = ", ".join(t.name for t in relevant)
        print(f"  \"{q}\"")
        print(f"    → {tools_str}\n")

    # --- Full agent run with RAG-selected tools ---
    print("--- Agent with RAG-selected tools ---\n")

    llm = ChatOpenAI(
        model="gpt-5.2",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    query = "Check if R1 is online and get its CPU usage"
    relevant_tools = get_relevant_tools(query, k=4)

    print(f"  Query: \"{query}\"")
    print(f"  Tools given to agent ({len(relevant_tools)}/{len(ALL_TOOLS)}): "
          f"{[t.name for t in relevant_tools]}\n")

    agent = create_react_agent(llm, relevant_tools)
    result = agent.invoke({"messages": [("user", query)]})

    print(f"  Agent: {result['messages'][-1].content}")
    print(f"\n{'─' * 55}")
