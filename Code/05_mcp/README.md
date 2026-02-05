# Demo 05: Model Context Protocol (MCP)

## Overview
MCP is a standard protocol that lets AI applications connect to tool servers.

## Demos

| File | Description |
|------|-------------|
| `01_mcp_server.py` | MCP server exposing network tools |
| `02_mcp_concepts.py` | MCP architecture explained (no deps needed) |
| `03_mcp_client.py` | Client that connects to server & uses tools |

## Running the Demos

```bash
# Terminal 1: Start the server
python 01_mcp_server.py

# Terminal 2: Run the client (connects to server)
python 03_mcp_client.py

# Conceptual demo (no server needed, good for screenshots)
python 03_mcp_client.py --simple
python 02_mcp_concepts.py
```

## Custom Port

```bash
# Server on custom port
python 01_mcp_server.py --port 9000

# Client connecting to custom port
python 03_mcp_client.py --url http://localhost:9000/sse
```

## Key Libraries Used

| Library | Purpose |
|---------|---------|
| `mcp` | Core MCP protocol (server & client) |
| `langchain_mcp` | Bridge: converts MCP tools → LangChain tools |
| `langgraph` | Creates the ReAct agent |
| `langchain_openai` | LLM integration |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  03_mcp_client.py                                           │
│                                                             │
│    sse_client(url)      ← Connect via SSE                   │
│         ↓                                                   │
│    ClientSession        ← MCP session                       │
│         ↓                                                   │
│    MCPToolkit           ← Converts MCP → LangChain tools    │
│         ↓                                                   │
│    create_react_agent   ← Agent uses the tools              │
└─────────────────────────────────────────────────────────────┘
                    ↕ MCP Protocol (SSE)
┌─────────────────────────────────────────────────────────────┐
│  01_mcp_server.py                                           │
│                                                             │
│    FastMCP("NetworkTools")                                  │
│         ↓                                                   │
│    @mcp.tool() decorated functions                          │
│    - ping_device()                                          │
│    - get_device_info()                                      │
│    - list_devices()                                         │
│    - check_interface()                                      │
└─────────────────────────────────────────────────────────────┘
```
