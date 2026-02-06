"""
=============================================================================
Browser Automation MCP Server
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam

This MCP server exposes browser automation tools using FastMCP 3.0.
See: https://gofastmcp.com/getting-started/welcome

Uses Playwright ASYNC API (required since MCP server runs in asyncio).

Prerequisites:
    1. Chrome running with debug port:
       ./restart_chrome.sh

To run:
    python 01_browser_mcp_server.py
    python 01_browser_mcp_server.py --port 8080  (custom port)

Then in another terminal:
    python 03_browser_mcp_client.py
=============================================================================
"""

import os
import sys
import asyncio
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Parse arguments
parser = argparse.ArgumentParser(description="Browser Automation MCP Server")
parser.add_argument("--port", type=int, default=8000,
                    help="Port for server (default: 8000)")
args = parser.parse_args()

# FastMCP 3.0 - https://gofastmcp.com
from fastmcp import FastMCP

# Playwright ASYNC API (required inside asyncio event loop)
from playwright.async_api import async_playwright

# =============================================================================
# Logging Helper
# =============================================================================

def log(message: str):
    """Log messages visibly."""
    print(f"[SERVER] {message}", file=sys.stderr, flush=True)

# =============================================================================
# Browser State (Singleton - Async)
# =============================================================================

class BrowserState:
    """Singleton to manage async browser connection across tool calls"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.playwright = None
            cls._instance.browser = None
            cls._instance.page = None
            cls._instance.connected = False
        return cls._instance
    
    async def connect(self) -> str:
        """Connect to existing Chrome browser on debug port (async)"""
        if self.connected and self.page:
            return "Already connected to browser"
        
        try:
            log("Connecting to Chrome on port 9222...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.connect_over_cdp("http://localhost:9222")
            
            contexts = self.browser.contexts
            if contexts:
                context = contexts[0]
                if context.pages:
                    self.page = context.pages[0]
                else:
                    self.page = await context.new_page()
            else:
                raise Exception("No browser context found")
            
            self.connected = True
            log("✅ Connected to Chrome!")
            return "Successfully connected to Chrome browser"
        except Exception as e:
            error = f"Failed to connect: {e}. Run ./restart_chrome.sh first."
            log(f"❌ {error}")
            return error
    
    async def disconnect(self):
        """Disconnect from browser"""
        if self.playwright:
            await self.playwright.stop()
        self.playwright = None
        self.browser = None
        self.page = None
        self.connected = False

# Global browser instance
browser_state = BrowserState()

# =============================================================================
# Initialize MCP Server
# =============================================================================

os.environ["FASTMCP_PORT"] = str(args.port)

mcp = FastMCP("BrowserAgent")

log("=" * 50)
log("MCP Server: BrowserAgent initialized (FastMCP 3.0)")
log("=" * 50)

# =============================================================================
# Browser Tools (all async)
# =============================================================================

@mcp.tool()
async def connect_browser() -> dict:
    """
    Connect to an existing Chrome browser running with remote debugging.
    
    Chrome must be started with: --remote-debugging-port=9222
    Run ./restart_chrome.sh to start Chrome correctly.
    
    Returns:
        dict with connection status
    """
    log("🔧 TOOL CALLED: connect_browser()")
    result = await browser_state.connect()
    # "Already connected" is also a success
    is_ok = "Successfully" in result or "Already" in result
    response = {"status": "connected" if is_ok else "failed", "message": result}
    log(f"   → Result: {response}")
    return response


@mcp.tool()
async def navigate(url: str) -> dict:
    """
    Navigate the browser to a specified URL.
    Waits for page to load. Does NOT auto-login - use the login tool if needed.
    
    Args:
        url: The URL to navigate to (e.g., "https://example.com")
    
    Returns:
        dict with navigation status and whether a login page was detected
    """
    log(f"🔧 TOOL CALLED: navigate(url='{url}')")
    
    if not browser_state.page:
        connect_result = await browser_state.connect()
        if "Failed" in connect_result:
            return {"status": "error", "message": connect_result}
    
    try:
        await browser_state.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        log("   Page DOM loaded, waiting for content...")
        await asyncio.sleep(5)  # Wait for AJAX content to load
        
        # Check if there's a login page
        login_detected = await _detect_login_page()
        
        result = {
            "status": "success",
            "message": f"Navigated to {url}",
            "url": url,
            "login_page_detected": login_detected,
        }
        if login_detected:
            result["hint"] = "Login page detected! Call the login tool with username and password."
        
        log(f"   → Result: {result}")
        return result
    except Exception as e:
        result = {"status": "error", "message": f"Navigation failed: {e}"}
        log(f"   → Result: {result}")
        return result


@mcp.tool()
async def login(username: str = "", password: str = "") -> dict:
    """
    Handle login on the current page. Detects username/password fields and submits.
    If username/password not provided, uses CATALYST_USERNAME/CATALYST_PASSWORD from environment.
    
    Args:
        username: Username to enter (optional, uses env var CATALYST_USERNAME if empty)
        password: Password to enter (optional, uses env var CATALYST_PASSWORD if empty)
    
    Returns:
        dict with login status
    """
    log(f"🔧 TOOL CALLED: login(username='{username or '(from env)'}')")
    
    if not browser_state.page:
        return {"status": "error", "message": "Browser not connected. Call connect_browser first."}
    
    # Use env vars as defaults
    username = username or os.getenv("CATALYST_USERNAME", "admin")
    password = password or os.getenv("CATALYST_PASSWORD", "")
    
    try:
        page = browser_state.page
        
        # Wait a bit for page to fully render
        await asyncio.sleep(2)
        
        # Find password field
        password_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            '#password',
        ]
        
        password_field = None
        for selector in password_selectors:
            try:
                elem = page.locator(selector).first
                if await elem.is_visible(timeout=3000):
                    password_field = elem
                    log(f"   Found password field: {selector}")
                    break
            except:
                continue
        
        if not password_field:
            return {"status": "no_login", "message": "No login form detected on this page"}
        
        # Find username field
        username_selectors = [
            'input[name="username"]',
            'input[name="user"]',
            'input[id*="username"]',
            'input[id*="user"]',
            'input[type="text"]',
            '#username',
        ]
        
        username_field = None
        for selector in username_selectors:
            try:
                elem = page.locator(selector).first
                if await elem.is_visible(timeout=2000):
                    username_field = elem
                    log(f"   Found username field: {selector}")
                    break
            except:
                continue
        
        if not username_field:
            return {"status": "error", "message": "Found password field but no username field"}
        
        # Fill credentials
        log(f"   Entering username: {username}")
        await username_field.fill(username)
        await asyncio.sleep(0.5)
        
        log("   Entering password: ********")
        await password_field.fill(password)
        await asyncio.sleep(0.5)
        
        # Find and click submit
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Log in")',
            'button:has-text("Login")',
            'button:has-text("Sign in")',
            'button:has-text("Submit")',
        ]
        
        submitted = False
        for selector in submit_selectors:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=2000):
                    log(f"   Clicking submit: {selector}")
                    await btn.click()
                    submitted = True
                    break
            except:
                continue
        
        if not submitted:
            log("   No submit button found, pressing Enter")
            await password_field.press("Enter")
        
        # Wait for login to complete and page to load
        log("   Waiting for login to complete (10s)...")
        await asyncio.sleep(10)
        
        # Check if we're still on login page
        still_login = await _detect_login_page()
        
        if still_login:
            result = {"status": "login_failed", "message": "Login may have failed - still on login page. Check credentials."}
        else:
            result = {"status": "success", "message": "Login successful! Page loaded after login."}
        
        log(f"   → Result: {result}")
        return result
        
    except Exception as e:
        result = {"status": "error", "message": f"Login failed: {e}"}
        log(f"   → Result: {result}")
        return result


@mcp.tool()
async def take_screenshot(description: str = "current page") -> dict:
    """
    Take a screenshot of the current browser page.
    
    Args:
        description: Brief description of what's being captured
    
    Returns:
        dict with screenshot file path
    """
    log(f"🔧 TOOL CALLED: take_screenshot(description='{description}')")
    
    if not browser_state.page:
        return {"status": "error", "message": "Browser not connected. Call connect_browser first."}
    
    os.makedirs("screenshots", exist_ok=True)
    import time
    timestamp = int(time.time())
    filename = f"screenshots/screenshot_{timestamp}.png"
    
    await browser_state.page.screenshot(path=filename, full_page=False)
    
    result = {"status": "success", "file": filename, "description": description}
    log(f"   → Result: {result}")
    return result


@mcp.tool()
async def analyze_page(question: str) -> dict:
    """
    Take a screenshot and analyze it with Gemini Vision AI.
    
    Args:
        question: What you want to know about the current page
    
    Returns:
        dict with AI analysis of the page
    """
    log(f"🔧 TOOL CALLED: analyze_page(question='{question[:50]}...')")
    
    if not browser_state.page:
        return {"status": "error", "message": "Browser not connected. Call connect_browser first."}
    
    # Take screenshot
    os.makedirs("screenshots", exist_ok=True)
    import time
    timestamp = int(time.time())
    screenshot_path = f"screenshots/analysis_{timestamp}.png"
    await browser_state.page.screenshot(path=screenshot_path, full_page=False)
    
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"status": "error", "message": "GEMINI_API_KEY not set in environment"}
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        with open(screenshot_path, "rb") as img_file:
            image_data = img_file.read()
        
        prompt = f"""Analyze this screenshot and answer: {question}

Provide a clear, concise answer based on what you see.
Include specific metrics, numbers, or status indicators if visible."""
        
        log("   Analyzing with Gemini Vision...")
        response = model.generate_content([prompt, {"mime_type": "image/png", "data": image_data}])
        
        result = {"status": "success", "analysis": response.text, "screenshot": screenshot_path}
        log(f"   → Analysis complete ({len(response.text)} chars)")
        return result
    except Exception as e:
        result = {"status": "error", "message": f"Analysis failed: {e}"}
        log(f"   → Result: {result}")
        return result


@mcp.tool()
async def click_element(description: str) -> dict:
    """
    Click on an element in the browser based on a text description.
    Uses AI vision to identify the element.
    
    Args:
        description: Description of what to click (e.g., "Login button", "Settings link")
    
    Returns:
        dict with click status
    """
    log(f"🔧 TOOL CALLED: click_element(description='{description}')")
    
    if not browser_state.page:
        return {"status": "error", "message": "Browser not connected. Call connect_browser first."}
    
    # Take screenshot to identify element
    os.makedirs("screenshots", exist_ok=True)
    import time
    timestamp = int(time.time())
    screenshot_path = f"screenshots/click_{timestamp}.png"
    await browser_state.page.screenshot(path=screenshot_path, full_page=False)
    
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"status": "error", "message": "GEMINI_API_KEY not set"}
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        with open(screenshot_path, "rb") as img_file:
            image_data = img_file.read()
        
        prompt = f"""Look at this screenshot and identify the element: "{description}"

Return ONLY the exact text visible on the element to click.
Keep it short and precise. No explanation."""
        
        response = model.generate_content([prompt, {"mime_type": "image/png", "data": image_data}])
        click_text = response.text.strip().strip('"').strip("'")
        log(f"   Identified element text: '{click_text}'")
        
        # Try multiple click strategies (all async)
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
                log(f"   Trying {strategy_name}...")
                await strategy_fn()
                await asyncio.sleep(2)
                result = {"status": "success", "clicked": click_text, "strategy": strategy_name}
                log(f"   → Result: {result}")
                return result
            except Exception:
                continue
        
        result = {"status": "failed", "message": f"Could not click: {description}", "identified_as": click_text}
        log(f"   → Result: {result}")
        return result
        
    except Exception as e:
        result = {"status": "error", "message": f"Click failed: {e}"}
        log(f"   → Result: {result}")
        return result


@mcp.tool()
async def click_text(text: str, exact: bool = True) -> dict:
    """
    Click an element by visible text directly (no vision).
    Use this when you already know the exact visible text from analyze_page.
    
    Args:
        text: Visible text to click
        exact: Whether to match exact text (default True)
    
    Returns:
        dict with click status
    """
    log(f"🔧 TOOL CALLED: click_text(text='{text}', exact={exact})")
    
    if not browser_state.page:
        return {"status": "error", "message": "Browser not connected. Call connect_browser first."}
    
    try:
        page = browser_state.page
        timeout = 5000
        
        # --- Phase 1: Standard Playwright strategies ---
        strategies = [
            ("link", page.get_by_role("link", name=text).first),
            ("button", page.get_by_role("button", name=text).first),
            ("exact text", page.get_by_text(text, exact=True).first),
            ("partial text", page.get_by_text(text, exact=False).first),
            ("locator", page.locator(f"text={text}").first),
        ]
        
        for strategy_name, locator in strategies:
            try:
                if exact and strategy_name == "partial text":
                    continue
                log(f"   Trying {strategy_name}...")
                await locator.click(timeout=timeout)
                await asyncio.sleep(2)
                result = {"status": "success", "clicked": text, "strategy": strategy_name}
                log(f"   → Result: {result}")
                return result
            except Exception:
                continue
        
        # --- Phase 2: Container/parent click ---
        # The text may be inside a non-clickable element (span, div) whose
        # PARENT container (card, row, panel) is the actual clickable target.
        log(f"   Standard strategies failed. Trying container/parent click via JS...")
        try:
            clicked = await page.evaluate("""(searchText) => {
                // Find all elements containing the text
                const walker = document.createTreeWalker(
                    document.body, NodeFilter.SHOW_TEXT, null, false
                );
                let node;
                while (node = walker.nextNode()) {
                    if (node.textContent.includes(searchText)) {
                        // Walk up ancestors looking for a clickable one
                        let el = node.parentElement;
                        for (let i = 0; i < 8 && el; i++) {
                            const style = window.getComputedStyle(el);
                            const tag = el.tagName.toLowerCase();
                            const isClickable = (
                                tag === 'a' || tag === 'button' ||
                                el.getAttribute('role') === 'button' ||
                                el.getAttribute('role') === 'link' ||
                                el.getAttribute('role') === 'row' ||
                                el.hasAttribute('onclick') ||
                                el.hasAttribute('ng-click') ||
                                el.hasAttribute('data-click') ||
                                style.cursor === 'pointer' ||
                                el.classList.toString().match(/click|card|panel|row|item|link|btn/)
                            );
                            if (isClickable) {
                                el.click();
                                return {found: true, tag: tag, classes: el.className.substring(0, 80)};
                            }
                            el = el.parentElement;
                        }
                    }
                }
                return {found: false};
            }""", text)
            
            if clicked and clicked.get("found"):
                await asyncio.sleep(2)
                result = {"status": "success", "clicked": text, "strategy": f"container-js ({clicked.get('tag', '?')})"}
                log(f"   → Result: {result}")
                return result
            else:
                log(f"   Container click: no clickable ancestor found")
        except Exception as e:
            log(f"   Container click failed: {e}")
        
        result = {"status": "failed", "message": f"Could not click text: {text}"}
        log(f"   → Result: {result}")
        return result
    except Exception as e:
        result = {"status": "error", "message": f"Click failed: {e}"}
        log(f"   → Result: {result}")
        return result


@mcp.tool()
async def hover_element(description: str) -> dict:
    """
    Hover over an element to check if it's clickable or reveal tooltips.
    Uses AI vision to identify the element.
    
    Args:
        description: Description of what to hover (e.g., "Status icon", "Help button")
    
    Returns:
        dict with hover status and cursor style (pointer/default)
    """
    log(f"🔧 TOOL CALLED: hover_element(description='{description}')")
    
    if not browser_state.page:
        return {"status": "error", "message": "Browser not connected. Call connect_browser first."}
    
    # Reuse click logic to find element, but hover instead
    # Take screenshot to identify element
    os.makedirs("screenshots", exist_ok=True)
    import time
    timestamp = int(time.time())
    screenshot_path = f"screenshots/hover_{timestamp}.png"
    await browser_state.page.screenshot(path=screenshot_path, full_page=False)
    
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"status": "error", "message": "GEMINI_API_KEY not set"}
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        with open(screenshot_path, "rb") as img_file:
            image_data = img_file.read()
        
        prompt = f"""Look at this screenshot and identify the element: "{description}"

Return ONLY the exact text visible on the element to hover.
Keep it short and precise. No explanation."""
        
        response = model.generate_content([prompt, {"mime_type": "image/png", "data": image_data}])
        hover_text = response.text.strip().strip('"').strip("'")
        log(f"   Identified element text for hover: '{hover_text}'")
        
        # Try to find and hover
        page = browser_state.page
        timeout = 5000
        
        strategies = [
            ("link", page.get_by_role("link", name=hover_text).first),
            ("button", page.get_by_role("button", name=hover_text).first),
            ("exact text", page.get_by_text(hover_text, exact=True).first),
            ("partial text", page.get_by_text(hover_text, exact=False).first),
            ("locator", page.locator(f"text={hover_text}").first),
        ]
        
        for strategy_name, locator in strategies:
            try:
                log(f"   Trying to hover using {strategy_name}...")
                if await locator.is_visible(timeout=2000):
                    await locator.hover(timeout=timeout)
                    await asyncio.sleep(0.5)
                    
                    # Check cursor style
                    cursor = await locator.evaluate("el => window.getComputedStyle(el).cursor")
                    is_clickable = cursor == "pointer"
                    
                    result = {
                        "status": "success", 
                        "hovered": hover_text, 
                        "strategy": strategy_name,
                        "cursor_style": cursor,
                        "likely_clickable": is_clickable
                    }
                    log(f"   → Result: {result}")
                    return result
            except Exception:
                continue
        
        result = {"status": "failed", "message": f"Could not find element to hover: {description}", "identified_as": hover_text}
        log(f"   → Result: {result}")
        return result
        
    except Exception as e:
        result = {"status": "error", "message": f"Hover failed: {e}"}
        log(f"   → Result: {result}")
        return result


@mcp.tool()
async def hover_text(text: str, exact: bool = True) -> dict:
    """
    Hover over visible text to check if it's clickable.
    
    Args:
        text: Visible text to hover
        exact: Whether to match exact text (default True)
    
    Returns:
        dict with hover status and cursor style
    """
    log(f"🔧 TOOL CALLED: hover_text(text='{text}', exact={exact})")
    
    if not browser_state.page:
        return {"status": "error", "message": "Browser not connected. Call connect_browser first."}
    
    try:
        page = browser_state.page
        timeout = 5000
        
        strategies = [
            ("link", page.get_by_role("link", name=text).first),
            ("button", page.get_by_role("button", name=text).first),
            ("exact text", page.get_by_text(text, exact=True).first),
            ("partial text", page.get_by_text(text, exact=False).first),
            ("locator", page.locator(f"text={text}").first),
        ]
        
        for strategy_name, locator in strategies:
            try:
                if exact and strategy_name == "partial text":
                    continue
                
                log(f"   Trying to hover using {strategy_name}...")
                if await locator.is_visible(timeout=2000):
                    await locator.hover(timeout=timeout)
                    await asyncio.sleep(0.5)
                    
                    # Check cursor style
                    cursor = await locator.evaluate("el => window.getComputedStyle(el).cursor")
                    is_clickable = cursor == "pointer"
                    
                    result = {
                        "status": "success", 
                        "hovered": text, 
                        "strategy": strategy_name,
                        "cursor_style": cursor,
                        "likely_clickable": is_clickable
                    }
                    log(f"   → Result: {result}")
                    return result
            except Exception:
                continue
        
        result = {"status": "failed", "message": f"Could not find text to hover: {text}"}
        log(f"   → Result: {result}")
        return result
    except Exception as e:
        result = {"status": "error", "message": f"Hover failed: {e}"}
        log(f"   → Result: {result}")
        return result


@mcp.tool()
async def list_clickable_elements(section_keyword: str = "") -> dict:
    """
    List all clickable elements on the page (links, buttons, clickable cards).
    Optionally filter to elements near a section keyword (e.g., "Wireless").
    
    Args:
        section_keyword: Optional keyword to focus on a specific section (e.g., "Wireless", "Critical")
    
    Returns:
        dict with list of clickable elements and their text
    """
    log(f"🔧 TOOL CALLED: list_clickable_elements(section_keyword='{section_keyword}')")
    
    if not browser_state.page:
        return {"status": "error", "message": "Browser not connected. Call connect_browser first."}
    
    try:
        page = browser_state.page
        
        # Find all potentially clickable elements
        clickable_selectors = [
            "a[href]",                    # Links
            "button",                     # Buttons
            "[role='button']",            # Role buttons
            "[onclick]",                  # Onclick handlers
            "[class*='clickable']",       # Clickable class
            "[class*='card']",            # Cards (often clickable)
            "[class*='panel']",           # Panels
            "[class*='link']",            # Link class
            "[class*='btn']",             # Button class
            "[tabindex]",                 # Focusable elements
        ]
        
        elements = []
        seen_texts = set()
        
        for selector in clickable_selectors:
            try:
                locators = page.locator(selector)
                count = await locators.count()
                for i in range(min(count, 50)):  # Limit to 50 per selector
                    try:
                        elem = locators.nth(i)
                        if await elem.is_visible(timeout=500):
                            text = (await elem.inner_text(timeout=500)).strip()
                            if text and len(text) < 200 and text not in seen_texts:
                                # If section_keyword specified, filter
                                if section_keyword:
                                    # Get surrounding context
                                    parent_text = ""
                                    try:
                                        parent = elem.locator("xpath=..")
                                        parent_text = (await parent.inner_text(timeout=500)).lower()
                                    except:
                                        pass
                                    
                                    if section_keyword.lower() not in text.lower() and section_keyword.lower() not in parent_text:
                                        continue
                                
                                seen_texts.add(text)
                                elements.append({
                                    "text": text[:100],
                                    "type": selector.split("[")[0] or "element"
                                })
                    except:
                        continue
            except:
                continue
        
        # Sort by relevance (prioritize items with numbers like "0/1", colors, "critical")
        def priority(elem):
            t = elem["text"].lower()
            score = 0
            if "/" in t and any(c.isdigit() for c in t):  # "0/1" patterns
                score -= 10
            if "critical" in t or "error" in t or "fail" in t:
                score -= 5
            if "wireless" in t or "controller" in t:
                score -= 3
            return score
        
        elements.sort(key=priority)
        
        result = {
            "status": "success",
            "count": len(elements),
            "section_filter": section_keyword or "none",
            "elements": elements[:30],  # Return top 30
            "hint": "Use click_text(text) to click. Use hover_text(text) to verify if it's clickable (check cursor)."
        }
        log(f"   → Found {len(elements)} clickable elements")
        return result
    except Exception as e:
        result = {"status": "error", "message": f"Failed to list elements: {e}"}
        log(f"   → Result: {result}")
        return result


@mcp.tool()
async def explore_section(section_name: str) -> dict:
    """
    Systematically explore a UI section by finding and describing all interactive elements.
    Good for understanding complex dashboards like Catalyst Center.
    
    Args:
        section_name: Name of section to explore (e.g., "Wireless", "Monitor", "Assurance")
    
    Returns:
        dict with section analysis including clickable items and their likely purpose
    """
    log(f"🔧 TOOL CALLED: explore_section(section_name='{section_name}')")
    
    if not browser_state.page:
        return {"status": "error", "message": "Browser not connected. Call connect_browser first."}
    
    try:
        page = browser_state.page
        
        # Take screenshot for AI analysis
        os.makedirs("screenshots", exist_ok=True)
        import time as _time
        screenshot_path = f"screenshots/explore_{int(_time.time())}.png"
        await page.screenshot(path=screenshot_path, full_page=False)
        
        # Get API key for Gemini analysis
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {"status": "error", "message": "GEMINI_API_KEY not set"}
        
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        with open(screenshot_path, "rb") as img_file:
            image_data = img_file.read()
        
        prompt = f"""Analyze this screenshot focusing on the "{section_name}" section.

Provide a detailed breakdown:

1. SECTION LOCATION: Where is the "{section_name}" section on the screen?

2. CLICKABLE ELEMENTS in or near this section (list ALL):
   - Blue text links (exact text)
   - Buttons
   - Cards/panels with numbers (e.g., "0/1", "3/3")
   - Status indicators (red/yellow/green)
   - Any items showing issues (0 healthy, Critical, Error)

3. PRIORITY ORDER: List what to click FIRST to find issues, in order:
   1. [exact text to click] - why
   2. [exact text to click] - why
   3. ...

4. RED FLAGS: Any indicators showing problems (red icons, "0/X" patterns, "Critical")

Be specific with exact visible text for clicking."""
        
        log("   Analyzing section with Gemini...")
        response = model.generate_content([prompt, {"mime_type": "image/png", "data": image_data}])
        
        result = {
            "status": "success",
            "section": section_name,
            "analysis": response.text,
            "screenshot": screenshot_path,
            "hint": "Use click_text(text) with exact text from the analysis to click elements."
        }
        log(f"   → Section analysis complete")
        return result
    except Exception as e:
        result = {"status": "error", "message": f"Explore failed: {e}"}
        log(f"   → Result: {result}")
        return result


@mcp.tool()
async def extract_text() -> dict:
    """
    Extract visible text content from the current page.
    
    Returns:
        dict with page text (up to 3000 characters)
    """
    log("🔧 TOOL CALLED: extract_text()")
    
    if not browser_state.page:
        return {"status": "error", "message": "Browser not connected. Call connect_browser first."}
    
    try:
        text = await browser_state.page.inner_text("body")
        text = text[:3000] if len(text) > 3000 else text
        result = {"status": "success", "text": text, "length": len(text)}
        log(f"   → Extracted {len(text)} characters")
        return result
    except Exception as e:
        result = {"status": "error", "message": f"Extract failed: {e}"}
        log(f"   → Result: {result}")
        return result


@mcp.tool()
async def scroll_page(direction: str = "down") -> dict:
    """
    Scroll the page up or down.
    Returns metrics to show if scrolling actually happened.
    
    Args:
        direction: "up" or "down"
    
    Returns:
        dict with scroll status and position change
    """
    log(f"🔧 TOOL CALLED: scroll_page(direction='{direction}')")
    
    if not browser_state.page:
        return {"status": "error", "message": "Browser not connected. Call connect_browser first."}
    
    try:
        page = browser_state.page
        
        # Try to get start scroll position (may fail if page is in a special state)
        start_y = 0
        try:
            start_metrics = await page.evaluate("() => ({ y: window.scrollY, h: document.documentElement.scrollHeight })")
            if start_metrics:
                start_y = start_metrics.get("y", 0)
        except Exception:
            pass
        
        # Try keyboard-based scroll first
        try:
            if direction.lower() == "down":
                await page.keyboard.press("PageDown")
            else:
                await page.keyboard.press("PageUp")
        except Exception:
            # Fallback: use JavaScript scroll
            scroll_amount = 600 if direction.lower() == "down" else -600
            try:
                await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            except Exception:
                # Last resort: try scrolling the main scrollable container
                await page.evaluate(f"""() => {{
                    const el = document.querySelector('main') || document.querySelector('[class*="content"]') || document.scrollingElement || document.body;
                    el.scrollBy(0, {scroll_amount});
                }}""")
            
        await asyncio.sleep(1)
        
        # Try to get end scroll position
        end_y = start_y
        total_height = 0
        try:
            end_metrics = await page.evaluate("() => ({ y: window.scrollY, h: document.documentElement.scrollHeight })")
            if end_metrics:
                end_y = end_metrics.get("y", start_y)
                total_height = end_metrics.get("h", 0)
        except Exception:
            pass
        
        scrolled_amount = abs(end_y - start_y)
        did_scroll = scrolled_amount > 0
        
        result = {
            "status": "success", 
            "direction": direction,
            "scrolled_pixels": scrolled_amount,
            "new_scroll_top": end_y,
            "total_height": total_height,
            "did_scroll": did_scroll,
            "message": f"Scrolled {direction} {scrolled_amount}px" if did_scroll else f"Scroll {direction} executed (position may not have changed)"
        }
        log(f"   → Result: {result}")
        return result
    except Exception as e:
        result = {"status": "error", "message": f"Scroll failed: {e}"}
        log(f"   → Result: {result}")
        return result


@mcp.tool()
async def get_page_metrics() -> dict:
    """
    Get page and viewport metrics to decide whether scrolling is needed.
    
    Returns:
        dict with scroll height, viewport height, and current scroll position
    """
    log("🔧 TOOL CALLED: get_page_metrics()")
    
    if not browser_state.page:
        return {"status": "error", "message": "Browser not connected. Call connect_browser first."}
    
    try:
        metrics = await browser_state.page.evaluate(
            """() => ({
                scrollHeight: document.documentElement.scrollHeight,
                clientHeight: document.documentElement.clientHeight,
                scrollTop: document.documentElement.scrollTop || window.scrollY || 0
            })"""
        )
        result = {
            "status": "success",
            "scroll_height": metrics.get("scrollHeight"),
            "viewport_height": metrics.get("clientHeight"),
            "scroll_top": metrics.get("scrollTop"),
        }
        log(f"   → Result: {result}")
        return result
    except Exception as e:
        result = {"status": "error", "message": f"Failed to get metrics: {e}"}
        log(f"   → Result: {result}")
        return result


@mcp.tool()
async def wait_for_text(text: str, max_wait: int = 30) -> dict:
    """
    Wait until specific visible text appears on the page.
    Useful for slow-loading panels or menus.
    
    Args:
        text: Text to wait for (case-insensitive substring match)
        max_wait: Maximum seconds to wait (default 30, max 120)
    
    Returns:
        dict with wait status and elapsed time
    """
    log(f"🔧 TOOL CALLED: wait_for_text(text='{text}', max_wait={max_wait})")
    
    if not browser_state.page:
        return {"status": "error", "message": "Browser not connected. Call connect_browser first."}
    
    import time as _time
    max_wait = min(max_wait, 120)
    start = _time.time()
    check_interval = 2
    target = text.lower().strip()
    
    while (_time.time() - start) < max_wait:
        try:
            body_text = await browser_state.page.inner_text("body", timeout=3000)
            if target in body_text.lower():
                elapsed = int(_time.time() - start)
                result = {
                    "status": "found",
                    "message": f"Found text '{text}' after {elapsed}s",
                    "elapsed_seconds": elapsed,
                }
                log(f"   → {result}")
                return result
        except Exception:
            pass
        
        await asyncio.sleep(check_interval)
    
    elapsed = int(_time.time() - start)
    result = {
        "status": "timeout",
        "message": f"Text '{text}' not found after {elapsed}s",
        "elapsed_seconds": elapsed,
    }
    log(f"   → {result}")
    return result


@mcp.tool()
async def wait_for_selector(selector: str, max_wait: int = 30) -> dict:
    """
    Wait until a specific CSS selector appears on the page.
    Use this for panels or widgets that render late.
    
    Args:
        selector: CSS selector to wait for (e.g., \"div.dashboard-panel\")
        max_wait: Maximum seconds to wait (default 30, max 120)
    
    Returns:
        dict with wait status and elapsed time
    """
    log(f"🔧 TOOL CALLED: wait_for_selector(selector='{selector}', max_wait={max_wait})")
    
    if not browser_state.page:
        return {"status": "error", "message": "Browser not connected. Call connect_browser first."}
    
    import time as _time
    max_wait = min(max_wait, 120)
    start = _time.time()
    check_interval = 2
    
    while (_time.time() - start) < max_wait:
        try:
            locator = browser_state.page.locator(selector).first
            if await locator.is_visible(timeout=2000):
                elapsed = int(_time.time() - start)
                result = {
                    "status": "found",
                    "message": f"Selector '{selector}' visible after {elapsed}s",
                    "elapsed_seconds": elapsed,
                }
                log(f"   → {result}")
                return result
        except Exception:
            pass
        
        await asyncio.sleep(check_interval)
    
    elapsed = int(_time.time() - start)
    result = {
        "status": "timeout",
        "message": f"Selector '{selector}' not visible after {elapsed}s",
        "elapsed_seconds": elapsed,
    }
    log(f"   → {result}")
    return result


def _compute_image_hash(image_bytes: bytes) -> str:
    """Compute a simple hash of image bytes for comparison."""
    import hashlib
    return hashlib.md5(image_bytes).hexdigest()


async def _take_comparison_screenshot() -> tuple[bytes, str]:
    """Take a screenshot and return (bytes, hash)."""
    if not browser_state.page:
        return b"", ""
    try:
        screenshot_bytes = await browser_state.page.screenshot(full_page=False)
        return screenshot_bytes, _compute_image_hash(screenshot_bytes)
    except:
        return b"", ""


@mcp.tool()
async def wait_for_page(max_wait: int = 30) -> dict:
    """
    Smart wait using SCREENSHOT COMPARISON to detect when page has fully loaded.
    Takes periodic screenshots and waits until they match (page stabilized).
    Also checks for loading indicators, login pages, and panel content.
    
    Args:
        max_wait: Maximum seconds to wait (default 30, max 120)
    
    Returns:
        dict with page load status and stability info
    """
    log(f"🔧 TOOL CALLED: wait_for_page(max_wait={max_wait})")
    
    if not browser_state.page:
        return {"status": "error", "message": "Browser not connected. Call connect_browser first."}
    
    import time as _time
    max_wait = min(max_wait, 120)
    start = _time.time()
    check_interval = 3  # Check every 3 seconds
    
    last_screenshot_hash = ""
    stable_count = 0  # Number of times screenshot matched
    required_stable = 2  # Need 2 consecutive matches = 6 seconds of stability
    
    while (_time.time() - start) < max_wait:
        try:
            # Take screenshot and compute hash
            _, current_hash = await _take_comparison_screenshot()
            
            # Get page text for additional checks
            body_text = await browser_state.page.inner_text("body", timeout=3000)
            text_length = len(body_text.strip())
            body_lower = body_text.lower()
            
            # Check for loading indicators in text
            loading_indicators = ['loading', 'please wait', 'spinner', 'initializing', 'fetching']
            is_loading = any(indicator in body_lower for indicator in loading_indicators)
            
            # Check for common dashboard loading states
            has_panels = any(x in body_lower for x in ['health', 'devices', 'network', 'wireless', 'critical', 'issues'])
            
            # Check for login page
            login_detected = await _detect_login_page()
            if login_detected:
                elapsed = int(_time.time() - start)
                result = {
                    "status": "login_required",
                    "message": f"Login page detected after {elapsed}s. Call login() to authenticate.",
                    "content_length": text_length,
                    "elapsed_seconds": elapsed,
                }
                log(f"   → {result}")
                return result
            
            # Compare with last screenshot
            if current_hash and current_hash == last_screenshot_hash:
                stable_count += 1
                log(f"   Screenshot stable ({stable_count}/{required_stable})")
                
                # Page is stable if:
                # - Screenshots match for required_stable intervals AND
                # - Not showing loading indicators AND
                # - Has some meaningful content
                if stable_count >= required_stable and not is_loading and (text_length > 200 or has_panels):
                    elapsed = int(_time.time() - start)
                    result = {
                        "status": "loaded",
                        "message": f"Page fully loaded and stable after {elapsed}s",
                        "content_length": text_length,
                        "elapsed_seconds": elapsed,
                        "has_panels": has_panels,
                        "screenshot_stable": True,
                    }
                    log(f"   → {result}")
                    return result
            else:
                # Screenshot changed, reset stability counter
                stable_count = 0
                log(f"   Screenshot changed (content still loading...)")
            
            last_screenshot_hash = current_hash
            elapsed = int(_time.time() - start)
            log(f"   Waiting... ({elapsed}s, {text_length} chars, loading={is_loading}, panels={has_panels})")
            
        except Exception as e:
            log(f"   Wait check error: {e}")
        
        await asyncio.sleep(check_interval)
    
    # Timeout - but provide useful info
    elapsed = int(_time.time() - start)
    result = {
        "status": "timeout",
        "message": f"Page may still be loading after {elapsed}s. Screenshots not stable. Try wait_for_page(max_wait=60) or analyze_page to check current state.",
        "elapsed_seconds": elapsed,
        "stable_count": stable_count,
        "hint": "Dashboard panels may still be loading. Call wait_for_page again with longer timeout.",
    }
    log(f"   → {result}")
    return result


@mcp.tool()
async def wait_for_dashboard(max_wait: int = 45) -> dict:
    """
    Wait specifically for DASHBOARD PANELS to fully load with data.
    Uses screenshot comparison + checks for panel content like numbers, percentages, charts.
    Designed for monitoring dashboards like Cisco Catalyst Center.
    
    Args:
        max_wait: Maximum seconds to wait (default 45, max 120)
    
    Returns:
        dict with dashboard load status and panel detection info
    """
    log(f"🔧 TOOL CALLED: wait_for_dashboard(max_wait={max_wait})")
    
    if not browser_state.page:
        return {"status": "error", "message": "Browser not connected. Call connect_browser first."}
    
    import time as _time
    import re
    
    max_wait = min(max_wait, 120)
    start = _time.time()
    check_interval = 4  # Check every 4 seconds
    
    last_screenshot_hash = ""
    stable_count = 0
    required_stable = 2  # Need 2 consecutive matches
    
    while (_time.time() - start) < max_wait:
        try:
            # Take screenshot for comparison
            _, current_hash = await _take_comparison_screenshot()
            
            # Get page text
            body_text = await browser_state.page.inner_text("body", timeout=5000)
            body_lower = body_text.lower()
            
            # Dashboard-specific content detection
            # Look for numbers, percentages, fractions like "0/1", "33%", "3 devices"
            has_numbers = bool(re.search(r'\d+/\d+|\d+%|\d+\s*(devices?|total|healthy|critical|issues?)', body_lower))
            has_panels = any(x in body_lower for x in ['health', 'devices', 'network', 'wireless', 'controller', 'access point'])
            
            # Loading detection
            loading_patterns = ['loading', 'please wait', 'fetching', 'initializing']
            is_loading = any(p in body_lower for p in loading_patterns)
            
            # Check for login
            login_detected = await _detect_login_page()
            if login_detected:
                elapsed = int(_time.time() - start)
                return {
                    "status": "login_required",
                    "message": f"Login page detected after {elapsed}s. Call login() first.",
                    "elapsed_seconds": elapsed,
                }
            
            # Screenshot stability check
            if current_hash and current_hash == last_screenshot_hash:
                stable_count += 1
                log(f"   Dashboard stable ({stable_count}/{required_stable}), numbers={has_numbers}, panels={has_panels}")
                
                # Dashboard is ready when:
                # 1. Screenshots are stable AND Has panel content (numbers, percentages) AND Not loading
                # OR
                # 2. Screenshots are VERY stable (3+ matches) even if regex missed (fallback)
                
                is_ready = False
                ready_reason = ""
                
                if stable_count >= required_stable and has_numbers and has_panels and not is_loading:
                    is_ready = True
                    ready_reason = "panels detected and stable"
                elif stable_count >= 3 and not is_loading:
                    is_ready = True
                    ready_reason = "page very stable (fallback)"
                
                if is_ready:
                    elapsed = int(_time.time() - start)
                    result = {
                        "status": "ready",
                        "message": f"Dashboard loaded: {ready_reason} after {elapsed}s",
                        "elapsed_seconds": elapsed,
                        "has_numbers": has_numbers,
                        "has_panels": has_panels,
                        "screenshot_stable": True,
                        "hint": "Dashboard is ready. Use explore_section() or analyze_page().",
                    }
                    log(f"   → {result}")
                    return result
            else:
                stable_count = 0
                log(f"   Dashboard still rendering...")
            
            last_screenshot_hash = current_hash
            elapsed = int(_time.time() - start)
            log(f"   Waiting... ({elapsed}s, loading={is_loading}, numbers={has_numbers}, panels={has_panels})")
            
        except Exception as e:
            log(f"   Dashboard check error: {e}")
        
        await asyncio.sleep(check_interval)
    
    # Timeout
    elapsed = int(_time.time() - start)
    result = {
        "status": "timeout",
        "message": f"Dashboard panels may still be loading after {elapsed}s",
        "elapsed_seconds": elapsed,
        "hint": "Try wait_for_dashboard(max_wait=90) or proceed with analyze_page() to check current state.",
    }
    log(f"   → {result}")
    return result


@mcp.tool()
async def wait_seconds(seconds: int = 5) -> dict:
    """
    Simple wait for a specified number of seconds.
    Prefer wait_for_page or wait_for_dashboard for smarter waiting.
    
    Args:
        seconds: Number of seconds to wait (max 60)
    
    Returns:
        dict with wait status
    """
    log(f"🔧 TOOL CALLED: wait_seconds(seconds={seconds})")
    
    seconds = min(seconds, 60)
    await asyncio.sleep(seconds)
    result = {"status": "success", "waited_seconds": seconds}
    log(f"   → Result: {result}")
    return result


# =============================================================================
# Helper Functions (async)
# =============================================================================

async def _detect_login_page() -> bool:
    """Check if the current page has a login form"""
    if not browser_state.page:
        return False
    
    try:
        password_field = browser_state.page.locator('input[type="password"]').first
        return await password_field.is_visible(timeout=2000)
    except:
        return False


# =============================================================================
# Run the Server
# =============================================================================

if __name__ == "__main__":
    log("")
    log("📋 Tools available:")
    log("   - connect_browser()         : Connect to Chrome")
    log("   - navigate(url)             : Go to URL")
    log("   - login(user, pass)         : Handle login pages")
    log("   - take_screenshot(desc)     : Capture screenshot")
    log("   - analyze_page(question)    : AI vision analysis")
    log("   - click_element(description): Click element (vision)")
    log("   - click_text(text)          : Click known text (direct)")
    log("   - hover_element(desc)       : Hover to check clickability")
    log("   - hover_text(text)          : Hover text to check cursor")
    log("   - list_clickable_elements() : List all clickable items")
    log("   - explore_section(name)     : Deep-analyze a section")
    log("   - extract_text()            : Get page text")
    log("   - scroll_page(direction)    : Scroll up/down")
    log("   - get_page_metrics()        : Page/viewport heights")
    log("   - wait_for_text(text)       : Wait for visible text")
    log("   - wait_for_selector(sel)    : Wait for CSS selector")
    log("   - wait_for_page(max_wait)   : Smart wait (screenshot compare)")
    log("   - wait_for_dashboard(max)   : Wait for dashboard panels")
    log("   - wait_seconds(seconds)     : Simple timer wait")
    log("")
    log(f"🚀 Starting MCP server on port {args.port}...")
    log(f"   URL: http://localhost:{args.port}/sse")
    log("")
    log("   Prerequisites:")
    log("      ./restart_chrome.sh  (start Chrome with debug port)")
    log("")
    log("   In another terminal, run:")
    log(f"   python 03_browser_mcp_client.py --url http://localhost:{args.port}/sse")
    log("-" * 50)
    
    mcp.run(transport="sse")
