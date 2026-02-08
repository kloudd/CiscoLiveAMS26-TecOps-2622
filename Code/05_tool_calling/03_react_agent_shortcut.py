"""
=============================================================================
DEMO 03: create_react_agent (The Easy Way)
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 04 - Tool Calling & Agent Brain

LangGraph's create_react_agent() builds a full ReAct agent in one call —
no manual state, nodes, or edges required.
=============================================================================
"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

# =============================================================================
# STEP 1: Define Tools
# =============================================================================

@tool
def get_device_count(device_type: str) -> int:
    """
    Get the count of devices of a specific type.

    Args:
        device_type: Type of device (router, switch, ap, firewall)
    """
    counts = {"router": 12, "switch": 45, "ap": 128, "firewall": 4}
    return counts.get(device_type.lower(), 0)


@tool
def get_device_status(hostname: str) -> dict:
    """
    Get the status of a specific network device.

    Args:
        hostname: The device hostname
    """
    return {
        "hostname": hostname,
        "status": "online",
        "uptime": "45 days",
        "health": 95,
    }


@tool
def calculate_health_score(scores: list[int]) -> float:
    """
    Calculate the average health score from a list of scores.

    Args:
        scores: List of individual health scores
    """
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


tools = [get_device_count, get_device_status, calculate_health_score]

# =============================================================================
# STEP 2: Create the Agent — one line
# =============================================================================

llm = ChatOpenAI(
    model="gpt-5.2",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY"),
)

agent = create_react_agent(model=llm, tools=tools)

# =============================================================================
# STEP 3: With a System Prompt
# =============================================================================

system_prompt = """You are a helpful network operations assistant.
When reporting device information:
- Be concise
- Use bullet points for multiple items
- Flag any health scores below 90%
"""

agent_with_prompt = create_react_agent(model=llm, tools=tools, prompt=system_prompt)

# =============================================================================
# STEP 4: Run the Agent
# =============================================================================

if __name__ == "__main__":
    print("=" * 55)
    print("  Tool Calling Demo — create_react_agent()")
    print("=" * 55)

    # --- Visualise the graph ---
    print("\nGraph (Mermaid):\n")
    print(agent.get_graph().draw_mermaid())

    # --- Basic agent ---
    queries = [
        "How many switches do we have?",
        "What's the status of router R1?",
        "Calculate the average health for scores 90, 85, and 95",
    ]

    for query in queries:
        print(f"\n{'─' * 55}")
        print(f"User: {query}")
        result = agent.invoke({"messages": [("user", query)]})
        print(f"Agent: {result['messages'][-1].content}")

    # --- Agent with system prompt ---
    print(f"\n{'─' * 55}")
    print("(with system prompt)")
    print(f"User: Give me a summary of R1's status")
    result = agent_with_prompt.invoke({
        "messages": [("user", "Give me a summary of R1's status")]
    })
    print(f"Agent: {result['messages'][-1].content}")

    print(f"\n{'─' * 55}")
