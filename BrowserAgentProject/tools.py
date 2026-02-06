import os
import json
from typing import Any
from langchain_core.tools import tool
from fastmcp import Client

# Global configuration
MCP_SERVER_URL = "http://localhost:8000/sse"

# =============================================================================
# Persistent MCP Client Connection
# =============================================================================
# Instead of creating a new SSE connection per tool call (slow!),
# we maintain a single persistent connection and reconnect only on failure.

_mcp_client: Client | None = None

async def _get_client() -> Client:
    """Get or create a persistent MCP client connection."""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = Client(MCP_SERVER_URL)
        await _mcp_client.__aenter__()
    return _mcp_client


async def _reset_client():
    """Reset the client connection (for reconnection on error)."""
    global _mcp_client
    if _mcp_client is not None:
        try:
            await _mcp_client.__aexit__(None, None, None)
        except Exception:
            pass
    _mcp_client = None


async def call_mcp_tool(tool_name: str, args: dict) -> Any:
    """Call an MCP tool via the persistent FastMCP client connection.
    Auto-reconnects once if the connection has dropped."""
    try:
        client = await _get_client()
        result = await client.call_tool(tool_name, args)
        return result
    except Exception as e:
        # Connection may have dropped — reconnect once and retry
        await _reset_client()
        try:
            client = await _get_client()
            result = await client.call_tool(tool_name, args)
            return result
        except Exception as e2:
            return f"Error calling tool {tool_name}: {str(e2)}"


# =============================================================================
# Browser Connection & Navigation
# =============================================================================

@tool
async def connect_browser():
    """Connect to the browser."""
    return await call_mcp_tool("connect_browser", {})

@tool
async def navigate(url: str):
    """Navigate the browser to a specified URL."""
    return await call_mcp_tool("navigate", {"url": url})

@tool
async def login(username: str = "", password: str = ""):
    """Handle login on the current page."""
    return await call_mcp_tool("login", {"username": username, "password": password})

# =============================================================================
# Clicking & Hovering
# =============================================================================

@tool
async def click_element(description: str):
    """Click on an element based on a text description using AI vision."""
    return await call_mcp_tool("click_element", {"description": description})

@tool
async def click_text(text: str, exact: bool = True):
    """Click an element by visible text directly."""
    return await call_mcp_tool("click_text", {"text": text, "exact": exact})

@tool
async def hover_text(text: str, exact: bool = True):
    """Hover over visible text to check if it's clickable (returns cursor style)."""
    return await call_mcp_tool("hover_text", {"text": text, "exact": exact})

# =============================================================================
# Page Analysis & Exploration
# =============================================================================

@tool
async def analyze_page(question: str):
    """Take a screenshot and analyze it with AI to answer a question."""
    return await call_mcp_tool("analyze_page", {"question": question})

@tool
async def explore_section(section_name: str):
    """Systematically explore a UI section by finding and describing all interactive elements."""
    return await call_mcp_tool("explore_section", {"section_name": section_name})

@tool
async def list_clickable_elements(section_keyword: str = ""):
    """List all clickable elements on the page. Optionally filter by section keyword."""
    return await call_mcp_tool("list_clickable_elements", {"section_keyword": section_keyword})

@tool
async def take_screenshot(description: str = "current page"):
    """Take a screenshot of the current browser page."""
    return await call_mcp_tool("take_screenshot", {"description": description})

@tool
async def extract_text():
    """Extract visible text content from the current page (up to 3000 chars)."""
    return await call_mcp_tool("extract_text", {})

# =============================================================================
# Scrolling & Metrics
# =============================================================================

@tool
async def scroll_page(direction: str = "down"):
    """Scroll the page up or down. direction can be 'up' or 'down'."""
    return await call_mcp_tool("scroll_page", {"direction": direction})

@tool
async def get_page_metrics():
    """Get page and viewport metrics (scroll height, viewport height, scroll position)."""
    return await call_mcp_tool("get_page_metrics", {})

# =============================================================================
# Waiting
# =============================================================================

@tool
async def wait_for_dashboard(max_wait: int = 45):
    """Wait specifically for DASHBOARD PANELS to fully load with data."""
    return await call_mcp_tool("wait_for_dashboard", {"max_wait": max_wait})

@tool
async def wait_for_page(max_wait: int = 30):
    """Smart wait using screenshot comparison to detect when page has fully loaded."""
    return await call_mcp_tool("wait_for_page", {"max_wait": max_wait})

@tool
async def wait_seconds(seconds: int = 5):
    """Simple wait for a specified number of seconds (max 60)."""
    return await call_mcp_tool("wait_seconds", {"seconds": seconds})


# =============================================================================
# Tool List - All tools available to the agent
# =============================================================================

ALL_TOOLS = [
    # Connection & Navigation
    connect_browser,
    navigate,
    login,
    # Clicking & Hovering
    click_element,
    click_text,
    hover_text,
    # Analysis & Exploration
    analyze_page,
    explore_section,
    list_clickable_elements,
    take_screenshot,
    extract_text,
    # Scrolling & Metrics
    scroll_page,
    get_page_metrics,
    # Waiting
    wait_for_dashboard,
    wait_for_page,
    wait_seconds,
]
