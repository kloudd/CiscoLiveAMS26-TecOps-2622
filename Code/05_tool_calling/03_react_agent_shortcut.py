"""
=============================================================================
DEMO 03: create_react_agent (The Easy Way)
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 04 - Tool Calling & Agent Brain

LangGraph provides create_react_agent() - a one-liner to create
a full ReAct agent without manually building the graph!
=============================================================================
"""

import os
import warnings
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent  # Correct import from langgraph

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# =============================================================================
# STEP 1: Define Tools
# =============================================================================

print("=" * 60)
print("DEMO: create_react_agent (The Easy Way)")
print("=" * 60)

@tool
def get_device_count(device_type: str) -> int:
    """
    Get the count of devices of a specific type.
    
    Args:
        device_type: Type of device (router, switch, ap, firewall)
    
    Returns:
        Number of devices of that type
    """
    # Simulated data
    counts = {
        "router": 12,
        "switch": 45,
        "ap": 128,
        "firewall": 4
    }
    return counts.get(device_type.lower(), 0)

@tool
def get_device_status(hostname: str) -> dict:
    """
    Get the status of a specific device.
    
    Args:
        hostname: The device hostname
    
    Returns:
        Device status information
    """
    # Simulated data
    return {
        "hostname": hostname,
        "status": "online",
        "uptime": "45 days",
        "health": 95
    }

@tool
def calculate_health_score(scores: list[int]) -> float:
    """
    Calculate average health score from a list of scores.
    
    Args:
        scores: List of individual health scores
    
    Returns:
        Average health score
    """
    if not scores:
        return 0.0
    return sum(scores) / len(scores)

tools = [get_device_count, get_device_status, calculate_health_score]

print("\n📋 Tools defined:")
for t in tools:
    print(f"   - {t.name}")

# =============================================================================
# STEP 2: Create Agent with ONE LINE!
# =============================================================================

print("\n" + "-" * 60)
print("🚀 Creating agent with create_react_agent()")
print("-" * 60)

llm = ChatOpenAI(
    model="gpt-5.2",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# This ONE line creates a complete ReAct agent!
agent = create_react_agent(
    model=llm,
    tools=tools
)

print("""
agent = create_react_agent(
    model=llm,
    tools=tools
)

That's it! No need to:
  ❌ Manually define State
  ❌ Create agent_node function
  ❌ Build conditional edges
  ❌ Wire up the loop

create_react_agent() does it all!
""")

# =============================================================================
# STEP 3: Run the Agent
# =============================================================================

print("=" * 60)
print("🚀 Running the Agent")
print("=" * 60)

queries = [
    "How many switches do we have?",
    "What's the status of router R1?",
    "Calculate the average health if we have scores of 90, 85, and 95"
]

for query in queries:
    print(f"\n📤 User: {query}")
    
    result = agent.invoke({
        "messages": [("user", query)]
    })
    
    # Get final response
    final = result["messages"][-1].content
    print(f"📥 Agent: {final}")
    print("-" * 40)

# =============================================================================
# STEP 4: With System Message
# =============================================================================

print("\n" + "=" * 60)
print("📋 Adding a System Message")
print("=" * 60)

# You can add a system message to customize behavior
system_prompt = """You are a helpful network operations assistant.

When reporting device information:
- Always be concise
- Use bullet points for multiple items
- Mention any concerns if health is below 90%
"""


agent_with_system = create_react_agent(
    model=llm,
    tools=tools,
    prompt=system_prompt  # Use prompt argument for system message
)

result = agent_with_system.invoke({
    "messages": [("user", "Give me a summary of R1's status")]
})

print(f"\n📤 User: Give me a summary of R1's status")
print(f"📥 Agent: {result['messages'][-1].content}")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 60)
print("💡 When to Use create_react_agent():")
print("=" * 60)
print("""
✅ Use create_react_agent() when:
   - You want a standard ReAct agent
   - You don't need custom state fields
   - You want to get started quickly

❌ Build custom graph when:
   - You need special state fields
   - You want human-in-the-loop
   - You need complex routing logic
   - You want subgraphs

Both approaches use the same underlying LangGraph!
""")

print("✅ Demo complete!")
