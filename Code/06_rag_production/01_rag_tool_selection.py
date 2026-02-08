"""
=============================================================================
DEMO 01: RAG for Tool Selection
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 08 - RAG & Production Patterns

When you have MANY tools, the LLM can get confused.
RAG helps by retrieving only the RELEVANT tools for each query!
=============================================================================
"""

import os
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

# =============================================================================
# STEP 1: Define MANY Tools (The Problem)
# =============================================================================

print("=" * 60)
print("DEMO: RAG for Tool Selection")
print("=" * 60)

# Let's create a bunch of tools to simulate a real scenario
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

# All our tools
ALL_TOOLS = [
    get_device_status, get_interface_stats, get_cpu_utilization,
    get_memory_utilization, configure_vlan, configure_interface,
    backup_config, restore_config, reboot_device, get_neighbors,
    run_ping, run_traceroute, get_logs, create_ticket, send_alert
]

print(f"\n📋 Total tools defined: {len(ALL_TOOLS)}")
print("\nTools:")
for t in ALL_TOOLS:
    print(f"   - {t.name}")

# =============================================================================
# STEP 2: The Problem - Too Many Tools!
# =============================================================================

print("\n" + "=" * 60)
print("❌ THE PROBLEM: Too Many Tools")
print("=" * 60)

print("""
When you give the LLM ALL 15 tools:

1. Context window fills up with tool schemas
2. LLM may pick wrong tools
3. Higher token costs
4. Slower responses

Example confusion:
  User: "Is R1 online?"
  
  LLM sees 15 tools and might pick:
  - get_device_status ✓ (correct)
  - run_ping ✗ (wrong approach)
  - get_cpu_utilization ✗ (not what user asked)
""")

# =============================================================================
# STEP 3: The Solution - RAG for Tools
# =============================================================================

print("\n" + "=" * 60)
print("✅ THE SOLUTION: RAG for Tool Selection")
print("=" * 60)

print("""
Instead of giving ALL tools, we:

1. Embed tool descriptions into a vector store
2. When query comes in, search for relevant tools
3. Only pass relevant tools (3-5) to the LLM

Result:
- Better tool selection accuracy
- Lower token costs
- Faster responses
""")

# =============================================================================
# STEP 4: Implement RAG Tool Selection
# =============================================================================

print("\n" + "-" * 60)
print("🔧 Implementing RAG Tool Selection")
print("-" * 60)

# Create embeddings
embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))

# Create tool descriptions for embedding
tool_descriptions = []
tool_mapping = {}

for t in ALL_TOOLS:
    # Combine name and description for better matching
    text = f"{t.name}: {t.description}"
    tool_descriptions.append(text)
    tool_mapping[text] = t

print(f"\n   Created embeddings for {len(tool_descriptions)} tools")

# Simple in-memory vector search (using cosine similarity)
# In production, use FAISS or ChromaDB

# Embed all tool descriptions
print("   Embedding tool descriptions...")
tool_vectors = embeddings.embed_documents(tool_descriptions)
print("   ✓ Embeddings created")

def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors."""
    import math
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b)

def get_relevant_tools(query: str, k: int = 5) -> list:
    """
    Retrieve the k most relevant tools for a query.
    """
    # Embed the query
    query_vector = embeddings.embed_query(query)
    
    # Calculate similarities
    similarities = []
    for i, tool_vec in enumerate(tool_vectors):
        sim = cosine_similarity(query_vector, tool_vec)
        similarities.append((sim, tool_descriptions[i]))
    
    # Sort by similarity (highest first)
    similarities.sort(reverse=True)
    
    # Get top k tools
    relevant_tools = []
    for sim, desc in similarities[:k]:
        relevant_tools.append(tool_mapping[desc])
    
    return relevant_tools

# =============================================================================
# STEP 5: Test RAG Tool Selection
# =============================================================================

print("\n" + "=" * 60)
print("🧪 Testing RAG Tool Selection")
print("=" * 60)

test_queries = [
    "Is router R1 online?",
    "What's the CPU usage on SW-01?",
    "Configure VLAN 100 on the core switch",
    "Something is wrong, create a ticket"
]

for query in test_queries:
    print(f"\n📤 Query: '{query}'")
    
    relevant = get_relevant_tools(query, k=3)
    
    print("   Top 3 relevant tools:")
    for t in relevant:
        print(f"      - {t.name}")

# =============================================================================
# STEP 6: Use with Agent
# =============================================================================

print("\n" + "=" * 60)
print("🤖 Using RAG Tool Selection with Agent")
print("=" * 60)

# Create LLM
llm = ChatOpenAI(
    model="gpt-5.2",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Test with a specific query
query = "Check if R1 is online and get its CPU usage"

print(f"\n📤 Query: '{query}'")

# Get relevant tools using RAG
relevant_tools = get_relevant_tools(query, k=4)

print(f"\n🔍 RAG selected {len(relevant_tools)} tools:")
for t in relevant_tools:
    print(f"      - {t.name}")

# Create agent with ONLY relevant tools
agent = create_react_agent(llm, relevant_tools)

print("\n🚀 Running agent with selected tools...")
result = agent.invoke({"messages": [("user", query)]})

print(f"\n📥 Agent response: {result['messages'][-1].content}")

# =============================================================================
# STEP 7: Compare Costs
# =============================================================================

print("\n" + "=" * 60)
print("💰 Cost Comparison")
print("=" * 60)

print("""
Estimated token usage per request:

Without RAG (15 tools):
   - Tool schemas: ~3,000 tokens
   - Query + response: ~500 tokens
   - Total: ~3,500 tokens

With RAG (4 tools):
   - Tool schemas: ~800 tokens
   - Query + response: ~500 tokens
   - Total: ~1,300 tokens

Savings: ~63% fewer tokens! 💵
""")

print("✅ Demo complete!")
