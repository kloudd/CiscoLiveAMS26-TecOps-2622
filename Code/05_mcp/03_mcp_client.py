"""
=============================================================================
DEMO 03: MCP Client - Connecting to an MCP Server
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 05 - Model Context Protocol (MCP)

This demo shows how to connect to an MCP server and use its tools.

To run:
    Terminal 1: python 01_mcp_server.py
    Terminal 2: python 03_mcp_client.py
=============================================================================
"""

import os
import asyncio
import argparse
from langchain_openai import ChatOpenAI
from langchain_mcp import MCPToolkit  # Bridge between MCP and LangChain
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession
from mcp.client.sse import sse_client

# =============================================================================
# Main Function
# =============================================================================

async def main(url: str):
    """
    Connect to MCP server and use tools with an LLM agent.
    """
    print("=" * 60)
    print("DEMO: MCP Client")
    print("=" * 60)
    
    # =========================================================================
    # STEP 1: Connect to MCP Server
    # =========================================================================
    print(f"\n📋 Step 1: Connecting to MCP Server at {url}...")
    
    async with sse_client(url) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the MCP session
            await session.initialize()
            
            # MCPToolkit converts MCP tools → LangChain tools
            toolkit = MCPToolkit(session=session)
            await toolkit.initialize()
            
            print("   ✅ Connected to NetworkTools server!")
            
            # =================================================================
            # STEP 2: Discover Available Tools
            # =================================================================
            print("\n📋 Step 2: Discovering tools...")
            
            # Get LangChain-compatible tools from MCP server
            tools = toolkit.get_tools()
            
            print(f"   Found {len(tools)} tools:")
            for tool in tools:
                desc = tool.description[:50] if tool.description else "No description"
                print(f"      - {tool.name}: {desc}...")
            
            # =================================================================
            # STEP 3: Create Agent with MCP Tools
            # =================================================================
            print("\n📋 Step 3: Creating agent with MCP tools...")
            
            llm = ChatOpenAI(
                model="gpt-5.2",
                temperature=0,
                api_key=os.getenv("OPENAI_API_KEY")
            )
            
            # Create a ReAct agent - it can now use MCP tools!
            agent = create_react_agent(llm, tools)
            print("   ✅ Agent created!")
            
            # =================================================================
            # STEP 4: Use the Agent
            # =================================================================
            print("\n" + "=" * 60)
            print("🚀 Running Agent with MCP Tools")
            print("=" * 60)
            
            queries = [
                "List all routers in the network",
                "What's the status of SW-CORE-01?",
                "Ping 192.168.1.1 and tell me if it's reachable",
            ]
            
            for query in queries:
                print(f"\n📤 User: {query}")
                print("-" * 40)
                
                result = await agent.ainvoke({
                    "messages": [("user", query)]
                })
                
                final_message = result["messages"][-1].content
                print(f"📥 Agent: {final_message}")
            
            # =================================================================
            # STEP 5: Cleanup
            # =================================================================
            print("\n" + "=" * 60)
            print("🧹 Cleaning up...")
    
    print("   ✅ Connection closed")
    print("\n✅ Demo complete!")


# =============================================================================
# Conceptual Example (no server needed, good for screenshots)
# =============================================================================

def simple_example():
    """Show the concept without running anything."""
    
    print("=" * 60)
    print("DEMO: MCP Client (Conceptual Example)")
    print("=" * 60)
    
    print("""
┌─────────────────────────────────────────────────────────────┐
│                    MCP CLIENT FLOW                           │
└─────────────────────────────────────────────────────────────┘

Terminal 1: Start the server
──────────────────────────────
  $ python 01_mcp_server.py
  [SERVER] Starting on http://localhost:8000/sse

Terminal 2: Run the client
──────────────────────────────
  $ python 03_mcp_client.py
  Connecting to http://localhost:8000/sse...


CODE FLOW:
──────────

1. Connect to MCP server via SSE
   async with sse_client(url) as (read, write):
       session = ClientSession(read, write)

2. Use MCPToolkit to get LangChain-compatible tools
   toolkit = MCPToolkit(session=session)
   tools = toolkit.get_tools()
   # Returns: ping_device, get_device_info, list_devices, check_interface

3. Create agent with MCP tools
   agent = create_react_agent(llm, tools)

4. Use the agent
   result = await agent.ainvoke({"messages": [("user", query)]})
""")

    print("\n" + "=" * 60)
    print("📝 Example Interaction")
    print("=" * 60)
    
    print("""
User: "Check if router R1 is online"

Agent thinking: "I should use get_device_info"

[MCP Request to Server]
  → Tool: get_device_info
  → Args: {"hostname": "R1"}

[Server Logs - Terminal 1]
  🔧 TOOL CALLED: get_device_info(hostname='R1')
  → Result: {"hostname": "R1", "status": "online"...}

[MCP Response to Client]
  ← {"hostname": "R1", "model": "ISR 4451", "health_score": 98}

Agent: "Router R1 is online with a health score of 98%."
""")

    print("✅ Conceptual demo complete!")


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP Client Demo")
    parser.add_argument("--url", type=str, default="http://localhost:8000/sse",
                        help="MCP server URL (default: http://localhost:8000/sse)")
    parser.add_argument("--simple", action="store_true",
                        help="Show conceptual example without running")
    args = parser.parse_args()
    
    if args.simple:
        simple_example()
    else:
        print("MCP Client Demo")
        print(f"Connecting to: {args.url}")
        print()
        print("Make sure server is running:")
        print("  python 01_mcp_server.py")
        print()
        
        try:
            asyncio.run(main(args.url))
        except ConnectionRefusedError:
            print("\n⚠️  Error: Could not connect to server")
            print("\nMake sure the server is running:")
            print("  python 01_mcp_server.py")
        except Exception as e:
            print(f"\n⚠️  Error: {e}")
            print("\nMake sure the server is running:")
            print("  python 01_mcp_server.py")
