"""
LangGraph Browser Agent with FastMCP Server

A browser automation agent built with LangGraph, exposed as an MCP server.
Provides tools for browser automation that can be called by MCP clients.

Start the server:
    python langgraph_browser_mcp.py

Or with uvx:
    uvx fastmcp run langgraph_browser_mcp.py
"""

import os
import time
import base64
from typing import Annotated, TypedDict, Literal, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

# LangChain imports
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

# FastMCP imports
from fastmcp import FastMCP

# Playwright for browser control
from playwright.sync_api import sync_playwright, Page, Browser as PlaywrightBrowser

# ============================================================================
# Global Browser State (singleton for the MCP server)
# ============================================================================

class BrowserState:
    """Singleton to manage browser connection across tool calls"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.playwright = None
            cls._instance.browser = None
            cls._instance.page = None
            cls._instance.connected = False
        return cls._instance
    
    def connect(self) -> str:
        """Connect to existing Chrome browser on debug port"""
        if self.connected and self.page:
            return "Already connected to browser"
        
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.connect_over_cdp("http://localhost:9222")
            
            contexts = self.browser.contexts
            if contexts:
                context = contexts[0]
                if context.pages:
                    self.page = context.pages[0]
                else:
                    self.page = context.new_page()
            else:
                raise Exception("No browser context found")
            
            self.connected = True
            return "Successfully connected to Chrome browser"
        except Exception as e:
            return f"Failed to connect: {e}. Make sure Chrome is running with --remote-debugging-port=9222"
    
    def disconnect(self):
        """Disconnect from browser"""
        if self.playwright:
            self.playwright.stop()
        self.playwright = None
        self.browser = None
        self.page = None
        self.connected = False

# Global browser instance
browser_state = BrowserState()

# ============================================================================
# Browser Tools (exposed via MCP)
# ============================================================================

@tool
def connect_browser() -> str:
    """
    Connect to an existing Chrome browser running with remote debugging enabled.
    Chrome must be started with: --remote-debugging-port=9222
    """
    print("🔌 [TOOL] connect_browser called")
    result = browser_state.connect()
    print(f"   Result: {result}")
    return result


@tool
def navigate(url: str) -> str:
    """
    Navigate the browser to a specified URL.
    
    Args:
        url: The URL to navigate to (e.g., "https://example.com")
    """
    print(f"🌐 [TOOL] navigate called: {url}")
    
    if not browser_state.page:
        print("   Browser not connected, connecting...")
        connect_result = browser_state.connect()
        print(f"   Connection result: {connect_result}")
        if "Failed" in connect_result:
            return connect_result
    
    try:
        print(f"   Loading page...")
        browser_state.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        
        # Wait for content to load
        time.sleep(3)
        
        # Check for login page
        login_handled = _check_and_handle_login()
        if login_handled:
            print("   Login handled, waiting...")
            time.sleep(5)
        
        result = f"Successfully navigated to {url}"
        print(f"   ✅ {result}")
        return result
    except Exception as e:
        result = f"Navigation failed: {e}"
        print(f"   ❌ {result}")
        return result


@tool
def take_screenshot(description: str = "current page") -> str:
    """
    Take a screenshot of the current browser page.
    
    Args:
        description: A brief description of what's being captured
        
    Returns:
        Path to the saved screenshot file
    """
    print(f"📸 [TOOL] take_screenshot: {description}")
    
    if not browser_state.page:
        result = "Error: Browser not connected. Call connect_browser first."
        print(f"   ❌ {result}")
        return result
    
    os.makedirs("screenshots", exist_ok=True)
    timestamp = int(time.time())
    filename = f"screenshots/screenshot_{timestamp}.png"
    
    browser_state.page.screenshot(path=filename, full_page=False)
    print(f"   ✅ Saved: {filename}")
    return f"Screenshot saved: {filename}"


@tool
def analyze_page(question: str) -> str:
    """
    Take a screenshot and analyze it with Gemini Vision to answer a question.
    
    Args:
        question: What you want to know about the current page
    """
    print(f"🔍 [TOOL] analyze_page: {question[:50]}...")
    
    if not browser_state.page:
        result = "Error: Browser not connected. Call connect_browser first."
        print(f"   ❌ {result}")
        return result
    
    # Take screenshot
    os.makedirs("screenshots", exist_ok=True)
    timestamp = int(time.time())
    screenshot_path = f"screenshots/screenshot_{timestamp}.png"
    browser_state.page.screenshot(path=screenshot_path, full_page=False)
    print(f"   📸 Screenshot: {screenshot_path}")
    
    # Analyze with Gemini
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        result = "Error: GEMINI_API_KEY not set"
        print(f"   ❌ {result}")
        return result
    
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    with open(screenshot_path, "rb") as img_file:
        image_data = img_file.read()
    
    prompt = f"""Analyze this screenshot and answer: {question}

Provide a clear, concise answer based on what you see.
Include specific metrics, numbers, or status indicators if visible."""
    
    print("   🤖 Analyzing with Gemini...")
    response = model.generate_content([prompt, {"mime_type": "image/png", "data": image_data}])
    print(f"   ✅ Analysis complete")
    return response.text


@tool
def click_element(description: str) -> str:
    """
    Click on an element in the browser based on a text description.
    
    Args:
        description: Description of the element to click (e.g., "Login button", "Settings link")
    """
    print(f"🖱️  [TOOL] click_element: {description}")
    
    if not browser_state.page:
        result = "Error: Browser not connected. Call connect_browser first."
        print(f"   ❌ {result}")
        return result
    
    # Take screenshot to identify element
    os.makedirs("screenshots", exist_ok=True)
    timestamp = int(time.time())
    screenshot_path = f"screenshots/click_{timestamp}.png"
    browser_state.page.screenshot(path=screenshot_path, full_page=False)
    
    # Use Gemini to identify what text to click
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        result = "Error: GEMINI_API_KEY not set"
        print(f"   ❌ {result}")
        return result
    
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    with open(screenshot_path, "rb") as img_file:
        image_data = img_file.read()
    
    prompt = f"""Look at this screenshot and identify the element: "{description}"

Return ONLY the exact text visible on the element to click.
Keep it short and precise. No explanation."""
    
    print("   🤖 Identifying element with Gemini...")
    response = model.generate_content([prompt, {"mime_type": "image/png", "data": image_data}])
    click_text = response.text.strip().strip('"').strip("'")
    print(f"   🎯 Identified: '{click_text}'")
    
    # Try multiple click strategies
    timeout = 5000
    strategies = [
        ("link", lambda: browser_state.page.get_by_role("link", name=click_text).first.click(timeout=timeout)),
        ("button", lambda: browser_state.page.get_by_role("button", name=click_text).first.click(timeout=timeout)),
        ("exact text", lambda: browser_state.page.get_by_text(click_text, exact=True).first.click(timeout=timeout)),
        ("partial text", lambda: browser_state.page.get_by_text(click_text).first.click(timeout=timeout)),
        ("locator", lambda: browser_state.page.locator(f"text={click_text}").first.click(timeout=timeout)),
    ]
    
    for strategy_name, strategy_fn in strategies:
        try:
            print(f"   Trying {strategy_name}...")
            strategy_fn()
            time.sleep(2)
            result = f"Successfully clicked '{click_text}' via {strategy_name}"
            print(f"   ✅ {result}")
            return result
        except Exception:
            continue
    
    result = f"Failed to click element: {description} (identified as '{click_text}')"
    print(f"   ❌ {result}")
    return result


@tool
def extract_text() -> str:
    """
    Extract visible text content from the current page.
    Returns up to 2000 characters of text.
    """
    if not browser_state.page:
        return "Error: Browser not connected. Call connect_browser first."
    
    try:
        text = browser_state.page.inner_text("body")
        return text[:2000] if len(text) > 2000 else text
    except Exception as e:
        return f"Failed to extract text: {e}"


@tool
def scroll_page(direction: str = "down") -> str:
    """
    Scroll the page up or down.
    
    Args:
        direction: "up" or "down"
    """
    if not browser_state.page:
        return "Error: Browser not connected. Call connect_browser first."
    
    try:
        if direction.lower() == "down":
            browser_state.page.keyboard.press("PageDown")
        else:
            browser_state.page.keyboard.press("PageUp")
        time.sleep(1)
        return f"Scrolled {direction}"
    except Exception as e:
        return f"Scroll failed: {e}"


@tool
def wait_seconds(seconds: int) -> str:
    """
    Wait for a specified number of seconds. Useful for pages that load dynamically.
    
    Args:
        seconds: Number of seconds to wait (max 60)
    """
    seconds = min(seconds, 60)
    time.sleep(seconds)
    return f"Waited {seconds} seconds"


def _check_and_handle_login() -> bool:
    """Internal function to handle login pages"""
    if not browser_state.page:
        return False
    
    username = os.getenv("CATALYST_USERNAME", "admin")
    password = os.getenv("CATALYST_PASSWORD", "")
    
    password_selectors = [
        'input[type="password"]',
        'input[name="password"]',
        '#password',
    ]
    
    # Check for password field
    password_field = None
    for selector in password_selectors:
        try:
            elem = browser_state.page.locator(selector).first
            if elem.is_visible(timeout=1000):
                password_field = elem
                break
        except:
            continue
    
    if not password_field:
        return False
    
    # Find username field
    username_selectors = [
        'input[name="username"]',
        'input[type="text"]',
        '#username',
    ]
    
    username_field = None
    for selector in username_selectors:
        try:
            elem = browser_state.page.locator(selector).first
            if elem.is_visible(timeout=1000):
                username_field = elem
                break
        except:
            continue
    
    if not username_field:
        return False
    
    # Fill credentials
    try:
        username_field.fill(username)
        password_field.fill(password)
        
        # Try to submit
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Log in")',
            'button:has-text("Login")',
        ]
        
        for selector in submit_selectors:
            try:
                btn = browser_state.page.locator(selector).first
                if btn.is_visible(timeout=1000):
                    btn.click()
                    return True
            except:
                continue
        
        # Fallback: press Enter
        password_field.press("Enter")
        return True
    except:
        return False


# ============================================================================
# LangGraph Agent State and Graph
# ============================================================================

class AgentState(TypedDict):
    """State for the LangGraph agent"""
    messages: Annotated[list, add_messages]
    task: str
    findings: list[str]
    step_count: int
    max_steps: int


# All available tools
TOOLS = [
    connect_browser,
    navigate,
    take_screenshot,
    analyze_page,
    click_element,
    extract_text,
    scroll_page,
    wait_seconds,
]


def create_agent_graph():
    """Create the LangGraph agent with tools"""
    
    # Initialize LLM with tools
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=api_key,
    ).bind_tools(TOOLS)
    
    # Define nodes
    def agent_node(state: AgentState) -> AgentState:
        """The agent decides what to do next"""
        messages = state["messages"]
        response = llm.invoke(messages)
        return {"messages": [response]}
    
    def should_continue(state: AgentState) -> Literal["tools", "end"]:
        """Check if we should continue or end"""
        last_message = state["messages"][-1]
        
        # If no tool calls, we're done
        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            return "end"
        
        return "tools"
    
    # Create tool node
    tool_node = ToolNode(TOOLS)
    
    # Build the graph
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    
    workflow.set_entry_point("agent")
    
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "end": END}
    )
    
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()


# ============================================================================
# FastMCP Server
# ============================================================================

# Create MCP server
mcp = FastMCP("Browser Agent")


@mcp.tool()
def browser_connect() -> str:
    """Connect to Chrome browser running with remote debugging on port 9222"""
    return browser_state.connect()


@mcp.tool()
def browser_navigate(url: str) -> str:
    """Navigate browser to a URL"""
    return navigate.invoke({"url": url})


@mcp.tool()
def browser_screenshot(description: str = "current page") -> str:
    """Take a screenshot of the current page"""
    return take_screenshot.invoke({"description": description})


@mcp.tool()
def browser_analyze(question: str) -> str:
    """Analyze the current page with vision AI and answer a question"""
    return analyze_page.invoke({"question": question})


@mcp.tool()
def browser_click(element_description: str) -> str:
    """Click on an element described in natural language"""
    return click_element.invoke({"description": element_description})


@mcp.tool()
def browser_extract_text() -> str:
    """Extract visible text from the current page"""
    return extract_text.invoke({})


@mcp.tool()
def browser_scroll(direction: str = "down") -> str:
    """Scroll the page up or down"""
    return scroll_page.invoke({"direction": direction})


@mcp.tool()
def browser_wait(seconds: int = 5) -> str:
    """Wait for specified seconds"""
    return wait_seconds.invoke({"seconds": seconds})


@mcp.tool()
def browser_run_task(task: str, max_steps: int = 20) -> str:
    """
    Run an autonomous browser task using the LangGraph agent.
    The agent will navigate, click, and analyze pages to complete the task.
    
    Args:
        task: Natural language description of what to accomplish
        max_steps: Maximum number of steps (default 20)
    """
    import subprocess
    
    print("\n" + "="*60)
    print("🚀 STARTING BROWSER TASK")
    print("="*60)
    print(f"Task: {task[:100]}...")
    
    # Check if Chrome is running with debug port
    print("\n🔍 Checking Chrome debug port...")
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:9222/json/version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            error = "Chrome is not running with debug port 9222. Run: ./restart_chrome.sh"
            print(f"❌ {error}")
            return error
        print("✅ Chrome debug port is available")
    except Exception as e:
        error = f"Cannot check Chrome: {e}. Make sure Chrome is running with --remote-debugging-port=9222"
        print(f"❌ {error}")
        return error
    
    try:
        print("\n📊 Creating LangGraph agent...")
        graph = create_agent_graph()
        
        system_prompt = """You are a browser automation agent. You have tools to:
- connect_browser: Connect to Chrome (MUST call this first!)
- navigate: Go to URLs
- take_screenshot: Capture the screen
- analyze_page: Use vision AI to understand what's on screen
- click_element: Click buttons, links, etc.
- extract_text: Get page text
- scroll_page: Scroll up/down
- wait_seconds: Wait for page loads

IMPORTANT: Always call connect_browser FIRST before any other tool!
Then navigate to the target URL.
Take screenshots and analyze them to understand the page.
Click elements to interact. Report your findings clearly."""
        
        initial_state = {
            "messages": [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Task: {task}")
            ],
            "task": task,
            "findings": [],
            "step_count": 0,
            "max_steps": max_steps,
        }
        
        print("🏃 Running agent...")
        print("-"*60)
        
        # Run the graph
        result = graph.invoke(initial_state)
        
        print("-"*60)
        print("✅ Agent completed")
        
        # Extract final response
        final_message = result["messages"][-1]
        return final_message.content if hasattr(final_message, "content") else str(final_message)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Task failed: {e}")
        print(error_details)
        return f"Task failed: {e}\n\nDetails:\n{error_details}"


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║         LangGraph Browser Agent - FastMCP Server             ║
╠══════════════════════════════════════════════════════════════╣
║  Available tools:                                            ║
║  - browser_connect      : Connect to Chrome                  ║
║  - browser_navigate     : Go to URL                          ║
║  - browser_screenshot   : Take screenshot                    ║
║  - browser_analyze      : Analyze page with AI               ║
║  - browser_click        : Click element                      ║
║  - browser_extract_text : Get page text                      ║
║  - browser_scroll       : Scroll page                        ║
║  - browser_wait         : Wait for page load                 ║
║  - browser_run_task     : Run autonomous task                ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # Run the MCP server
    mcp.run()
