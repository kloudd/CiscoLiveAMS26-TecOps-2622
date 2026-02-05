"""
=============================================================================
DEMO 02: MCP Concepts Explained
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 05 - Model Context Protocol (MCP)

This demo explains MCP concepts without requiring an actual server.
Great for understanding the architecture before running real servers.
=============================================================================
"""

# =============================================================================
# MCP Architecture Explanation
# =============================================================================

print("=" * 60)
print("DEMO: MCP Concepts Explained")
print("=" * 60)

print("""
┌─────────────────────────────────────────────────────────────┐
│                    MCP ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────┐
    │                     HOST                             │
    │              (Your Python Script)                    │
    │                                                      │
    │    ┌────────────────────────────────────────────┐   │
    │    │              MCP CLIENT                     │   │
    │    │    (Built into LangChain / Your Code)      │   │
    │    └─────────────────┬──────────────────────────┘   │
    └──────────────────────┼──────────────────────────────┘
                           │
                    MCP Protocol
                    (JSON-RPC)
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
    │ Browser │      │ Network │      │  SQLite │
    │ Server  │      │  Tools  │      │  Server │
    │         │      │ Server  │      │         │
    └─────────┘      └─────────┘      └─────────┘
    
    Each SERVER exposes TOOLS that the HOST can call.
""")

# =============================================================================
# Why MCP?
# =============================================================================

print("\n" + "=" * 60)
print("💡 Why MCP Exists")
print("=" * 60)

print("""
THE PROBLEM: Integration Hell
─────────────────────────────
Before MCP:
    
    10 AI Apps × 10 Tool Providers = 100 Custom Integrations! 😱
    
    App A ──┬── Custom code ──► Tool 1
            ├── Custom code ──► Tool 2
            └── Custom code ──► Tool 3
    
    App B ──┬── Different code ──► Tool 1
            ├── Different code ──► Tool 2
            └── Different code ──► Tool 3
    
    Every app needs custom code for every tool!


THE SOLUTION: MCP (One Protocol)
────────────────────────────────
With MCP:
    
    10 Apps + 10 Servers = 20 Implementations! ✅
    
    App A ──┐
    App B ──┼──► MCP Protocol ──┬──► Tool Server 1
    App C ──┘                   ├──► Tool Server 2
                                └──► Tool Server 3
    
    Write once, use everywhere!
""")

# =============================================================================
# MCP Components
# =============================================================================

print("\n" + "=" * 60)
print("📦 MCP Components")
print("=" * 60)

print("""
1. HOST
   ─────
   Your application that needs AI capabilities.
   
   Example: A Python script that uses GPT-5.2 for automation
   
   
2. CLIENT
   ──────
   The connector inside your Host that speaks MCP.
   
   Example: langchain_mcp.MCPClient
   
   
3. SERVER
   ──────
   A service that provides tools, resources, or prompts.
   
   Example: The NetworkTools server we created in Demo 01
   
   
4. TRANSPORT
   ─────────
   How Client and Server communicate:
   
   - stdio: Process communication (local)
   - SSE: Server-Sent Events (remote/web)
   - HTTP: REST-like (future)
""")

# =============================================================================
# What Servers Provide
# =============================================================================

print("\n" + "=" * 60)
print("🔧 What MCP Servers Provide")
print("=" * 60)

print("""
MCP Servers can expose three things:

1. TOOLS (Actions)
   ────────────────
   Functions the LLM can call to DO things.
   
   Examples:
   - ping_device(ip) → Check if device is reachable
   - send_email(to, subject, body) → Send an email
   - create_ticket(title, desc) → Create support ticket


2. RESOURCES (Data)
   ─────────────────
   Read-only data sources for context.
   
   Examples:
   - docs://network/vlan-guide → VLAN documentation
   - config://device/R1 → Device configuration
   - logs://syslog/today → Today's syslog entries


3. PROMPTS (Templates)
   ────────────────────
   Reusable prompt templates.
   
   Examples:
   - "network-diagnosis" → Template for troubleshooting
   - "device-summary" → Template for status reports
""")

# =============================================================================
# Code Example: Server
# =============================================================================

print("\n" + "=" * 60)
print("📝 Code Example: MCP Server")
print("=" * 60)

server_code = '''
from mcp.server.fastmcp import FastMCP

# Create server
mcp = FastMCP("MyServer")

# Define a tool
@mcp.tool()
def my_tool(arg: str) -> str:
    """Tool description for LLM."""
    return f"Result for {arg}"

# Define a resource
@mcp.resource("data://example/{item}")
def get_data(item: str) -> str:
    """Get data about an item."""
    return f"Data about {item}"

# Run the server
mcp.run()
'''

print(server_code)

# =============================================================================
# Code Example: Client
# =============================================================================

print("\n" + "=" * 60)
print("📝 Code Example: MCP Client")
print("=" * 60)

client_code = '''
from langchain_mcp import MCPClient

# Connect to server
client = MCPClient(
    transport="stdio",
    command="python",
    args=["my_server.py"]
)

# List available tools
tools = client.get_tools()
print([t.name for t in tools])

# Use tools with an LLM
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

llm = ChatOpenAI(model="gpt-5.2")
agent = create_react_agent(llm, tools)

# Now the agent can use MCP tools!
result = agent.invoke({"messages": [("user", "Use my_tool")]})
'''

print(client_code)

# =============================================================================
# Popular MCP Servers
# =============================================================================

print("\n" + "=" * 60)
print("🌐 Popular MCP Servers")
print("=" * 60)

print("""
Official Servers (from Anthropic/MCP):
─────────────────────────────────────
• @modelcontextprotocol/server-puppeteer
  → Browser automation (navigate, click, screenshot)

• @modelcontextprotocol/server-sqlite
  → Database queries (read, write, schema)

• @modelcontextprotocol/server-filesystem
  → File operations (read, write, list)

• @modelcontextprotocol/server-slack
  → Slack integration (messages, channels)


Community Servers:
─────────────────
• GitHub MCP Server → Repo, PR, issue management
• PostgreSQL Server → Production database queries
• Kubernetes Server → Cluster management
• And many more at: github.com/modelcontextprotocol/servers
""")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 60)
print("💡 Key Takeaways")
print("=" * 60)

print("""
1. MCP = "USB-C for AI" - One standard protocol

2. Components:
   - Host: Your app
   - Client: Connector (in your app)
   - Server: Tool provider (separate process)

3. Servers expose:
   - Tools (actions)
   - Resources (data)
   - Prompts (templates)

4. Benefits:
   ✅ Write server once, use from any MCP client
   ✅ Language agnostic (Python, JS, Go, etc.)
   ✅ Growing ecosystem of pre-built servers
   ✅ Decouples AI logic from tool implementation
""")

print("\n✅ Demo complete!")
