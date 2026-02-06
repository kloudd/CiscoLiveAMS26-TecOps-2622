# Browser Agent Project

This project uses LangGraph and FastMCP to control a browser for automation tasks.

## Prerequisites

1.  **Chrome with Debug Port**:
    Run the `restart_chrome.sh` script in the `Demo` folder:
    ```bash
    cd ../Demo
    ./restart_chrome.sh
    ```

2.  **MCP Server**:
    Run the MCP server in a separate terminal:
    ```bash
    cd ../Demo
    python 01_browser_mcp_server.py
    ```

## Running the Agent

Run the agent as a module from the root of the workspace:

```bash
python -m BrowserAgentProject.main --task "Go to google.com and search for 'LangGraph'"
```

## Structure

*   `agent.py`: Defines the agent node and system prompt.
*   `tools.py`: Wraps the MCP server tools for the agent.
*   `graph.py`: Defines the LangGraph workflow.
*   `state.py`: Defines the agent state.
*   `main.py`: Entry point.

## Features

*   **Multi-step execution**: The agent runs in a loop until the task is done.
*   **Auto-scrolling**: The system prompt explicitly encourages scrolling to find elements.
*   **Resilience**: The agent can analyze the page and retry if clicks fail.
