"""
=============================================================================
Browser Automation MCP Client
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam

This client connects to the Browser MCP server using FastMCP 3.0 Client.
See: https://gofastmcp.com/getting-started/welcome

Prerequisites:
    1. Chrome running with debug port:
       ./restart_chrome.sh
    
    2. MCP server running:
       python 01_browser_mcp_server.py

To run:
    python 03_browser_mcp_client.py
    python 03_browser_mcp_client.py --task "Navigate to google.com"
    python 03_browser_mcp_client.py --prompt catalyst
=============================================================================
"""

import os
import asyncio
import argparse
from dotenv import load_dotenv

load_dotenv()

# FastMCP 3.0 Client
from fastmcp import Client

# =============================================================================
# Predefined Prompts
# =============================================================================

PROMPTS = {
    "catalyst": """
You are an SRE (Site Reliability Engineer) investigating wireless Controller issues in Cisco Catalyst Center.

URL: https://10.48.81.206/dna/catalyst/home

YOUR MISSION: Find the root cause of the "Critical" wireless issue.

STRATEGY:
1. DASHBOARD: Wait for panels to load. If you see "0/1" or "Critical", CLICK IT.
2. DRILL DOWN: Follow the red indicators.
3. FIND EVENTS: The root cause is in the EVENTS or LOGS.
   - These are often at the BOTTOM of the page.
   - SCROLL DOWN if you don't see them immediately!
   - DO NOT stare at the top of the page repeatedly.

4. REPORT: Device name, IP, and the specific ERROR MESSAGE from the event log.

RULES:
- If you don't see what you need, SCROLL DOWN.
- If you've analyzed the same view twice, SCROLL DOWN.
- Be aggressive: Click the problem, scroll to the logs, find the error.
- VERIFY CLICKABILITY: If unsure if something is clickable, use hover_text("text") to check if the cursor changes to "pointer".
""",
    
    "grafana": """
Check Grafana dashboards for alerts.

Steps:
1. Connect to the browser
2. Navigate to https://sumitkanwal.grafana.net/dashboards
3. Take a screenshot and analyze what dashboards are available
4. Look for any dashboards showing alerts or warnings
5. Report any alerts, errors, or anomalies found
""",
    
    "test": """
Simple browser test.

Steps:
1. Connect to the browser
2. Navigate to https://www.google.com
3. Take a screenshot
4. Analyze what you see on the page
5. Report the result
""",
}

# =============================================================================
# Main Client Function
# =============================================================================

def _extract_result_text(result) -> str:
    """Extract text from MCP tool result (handles TextContent objects)"""
    if isinstance(result, str):
        return result
    if hasattr(result, '__iter__') and not isinstance(result, (str, dict)):
        texts = []
        for item in result:
            if hasattr(item, 'text'):
                texts.append(item.text)
            else:
                texts.append(str(item))
        return "\n".join(texts)
    return str(result)


def _try_parse_json(text: str) -> dict | None:
    """Best-effort JSON parsing for tool responses."""
    try:
        return json.loads(text)
    except Exception:
        return None


def _missing_required_args(tool_name: str, args: dict) -> list[str]:
    """Return list of missing required args for known tools."""
    required = {
        "navigate": ["url"],
        "analyze_page": ["question"],
        "click_element": ["description"],
        "click_text": ["text"],
        "hover_element": ["description"],
        "hover_text": ["text"],
        "wait_for_text": ["text"],
        "wait_for_selector": ["selector"],
        "explore_section": ["section_name"],
    }
    required_args = required.get(tool_name, [])
    return [name for name in required_args if not args.get(name)]


async def main(url: str, task: str):
    """
    Connect to MCP server and use an adaptive ReAct agent loop.
    The agent observes tool results and decides the next step dynamically.
    """
    import json
    
    print("=" * 60)
    print("Browser Automation MCP Client (FastMCP 3.0)")
    print("=" * 60)
    
    # =========================================================================
    # STEP 1: Connect to MCP Server
    # =========================================================================
    print(f"\n📋 Step 1: Connecting to MCP Server at {url}...")
    
    async with Client(url) as client:
        print("   ✅ Connected to BrowserAgent server!")
        
        # =================================================================
        # STEP 2: Discover Available Tools
        # =================================================================
        print("\n📋 Step 2: Discovering tools...")
        
        tools = await client.list_tools()
        tool_names = [t.name for t in tools]
        
        print(f"   Found {len(tools)} tools:")
        for tool in tools:
            desc = tool.description[:60] if tool.description else "No description"
            print(f"      - {tool.name}: {desc}...")
        
        # =================================================================
        # STEP 3: Setup Gemini for adaptive agent loop
        # =================================================================
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("❌ Error: GEMINI_API_KEY not set")
            return
        
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Build tool descriptions
        tool_descriptions = "\n".join([
            f"- {t.name}: {t.description}" for t in tools
        ])
        
        # =================================================================
        # STEP 4: Adaptive Agent Loop (ReAct pattern)
        # =================================================================
        print("\n" + "=" * 60)
        print("🚀 Running Browser Automation Task")
        print("=" * 60)
        print(f"\n📤 Task: {task}")
        print("-" * 40)
        
        max_steps = 100
        history = []  # Track what happened
        actions_taken = 0
        
        # Track state to prevent redundant actions
        state = {
            "connected": False,
            "current_url": None,
            "logged_in": False,
            "dashboard_ready": False,
        }
        
        # Track repeated actions to detect when stuck
        recent_tools = []  # Last N tool calls
        analyze_count = 0  # How many times we've analyzed without clicking/scrolling
        
        while actions_taken < max_steps:
            step = actions_taken + 1
            print(f"\n{'─'*40}")
            print(f"Step {step}/{max_steps}")
            print(f"{'─'*40}")
            
            # Build the prompt for Gemini
            history_text = "\n".join(history[-10:]) if history else "No actions taken yet."
            
            # Build state summary
            state_summary = f"""CURRENT STATE:
- Connected: {state['connected']}
- Current URL: {state['current_url'] or 'None'}
- Logged in: {state['logged_in']}
- Dashboard ready: {state['dashboard_ready']}"""
            
            agent_prompt = f"""You are a browser automation agent. You must decide the NEXT SINGLE action to take.

AVAILABLE TOOLS:
{tool_descriptions}

TASK: {task}

{state_summary}

ACTION HISTORY (most recent last):
{history_text}

CRITICAL RULES:
- Return EXACTLY ONE tool call for the next step.
- DO NOT repeat actions! Check CURRENT STATE above:
  - If connected=True, do NOT call connect_browser again.
  - If already at the URL, do NOT call navigate again.
  - If dashboard_ready=True, do NOT call wait_for_dashboard again - START INVESTIGATING!

PAGE LOADING (screenshot comparison):
- wait_for_page uses SCREENSHOT COMPARISON - it compares before/after screenshots.
- If screenshots keep changing, the page is STILL LOADING - be patient!
- For dashboards with panels, use wait_for_dashboard(max_wait=60) - it waits for actual data.
- If wait_for_page/wait_for_dashboard returns "timeout", the page may still be loading.
  Call it again with longer timeout before clicking anything!
- If result shows "login_required", call login() first.

DASHBOARD LOADING SEQUENCE:
1. navigate(url)
2. wait_for_page(max_wait=30) - for initial page load
3. If login required: login() then wait_for_page(max_wait=30) again
4. wait_for_dashboard(max_wait=60) - CRITICAL: wait for panels to populate with data!
5. ONLY THEN explore or click

EXPLORATION (SRE approach):
- Use explore_section("Wireless") to understand a section before clicking.
- Use list_clickable_elements("Wireless") to see all clickable items.
- These help you DISCOVER what to click instead of guessing blindly.

CLICKING RULES:
- NEVER click until wait_for_dashboard returns "ready" - panels must be loaded!
- PRIORITY: red indicators (0/X, Critical) > blue links > numbered items > panels.
- "0/1" = 0 healthy out of 1 = PROBLEM. Click it!
- Use click_text(text) when you have exact text, click_element(desc) otherwise.
- HOVER FIRST: If you suspect an element is clickable but aren't sure, use hover_text(text).
  - If cursor_style="pointer", it IS clickable.
- After each click, call wait_for_page(max_wait=30) before analyzing.

SCROLLING - CRITICAL:
- If you don't see "Events", "Logs", or "Syslog", SCROLL DOWN immediately.
- If you have analyzed the page twice and haven't found the issue, SCROLL DOWN.
- Device details are long - the important stuff is often at the bottom.

COMPLETION:
- Report: device name, IP, location, ROOT CAUSE from events/syslog.
- Return DONE with detailed summary when investigation is complete.

RESPONSE FORMAT (pick one):
  TOOL: tool_name
  ARGS: {{"arg1": "value1", "arg2": "value2"}}
  REASON: why you're doing this

  OR

  DONE: <summary of findings>
"""
            
            print("🤖 Thinking...")
            response = model.generate_content(agent_prompt)
            decision = response.text.strip()
            
            # Check if agent says DONE
            if decision.upper().startswith("DONE:"):
                summary = decision[5:].strip()
                print(f"\n✅ Agent completed task!")
                print(f"\n{'='*60}")
                print("📊 FINAL REPORT")
                print(f"{'='*60}")
                print(summary)
                history.append(f"DONE: {summary}")
                break
            
            # Parse tool call - handle multiple formats Gemini might use
            tool_name = None
            tool_args = {}
            reason = ""
            
            # Clean up response - remove code blocks
            cleaned = decision.replace("```tool_code", "").replace("```", "").strip()
            
            for line in cleaned.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Format 1: TOOL: tool_name
                if line.upper().startswith("TOOL:"):
                    tool_name = line.split(":", 1)[1].strip()
                # Format 2: Just the tool name on first non-empty line
                elif tool_name is None and line in tool_names:
                    tool_name = line
                # ARGS parsing
                elif line.upper().startswith("ARGS:"):
                    args_str = line.split(":", 1)[1].strip()
                    try:
                        tool_args = json.loads(args_str)
                    except json.JSONDecodeError:
                        # Try Python dict format (single quotes)
                        try:
                            import ast
                            tool_args = ast.literal_eval(args_str)
                        except:
                            tool_args = {}
                elif line.upper().startswith("REASON:"):
                    reason = line.split(":", 1)[1].strip()
            
            if not tool_name or tool_name not in tool_names:
                print(f"   ⚠️  Invalid tool: {tool_name}")
                print(f"   Raw response: {decision[:200]}")
                history.append(f"Step {step}: ERROR - invalid tool '{tool_name}'")
                continue

            missing_args = _missing_required_args(tool_name, tool_args)
            if missing_args:
                print(f"   ⚠️  Missing required args for {tool_name}: {missing_args}")
                history.append(
                    f"Step {step}: ERROR - missing args {missing_args} for {tool_name}. "
                    f"Ask for required args and retry."
                )
                continue
            
            # Skip redundant actions
            if tool_name == "connect_browser" and state["connected"]:
                print(f"   ⏭️  Skipping - already connected")
                history.append(f"Step {step}: SKIPPED connect_browser - already connected. DO SOMETHING ELSE.")
                continue
            
            if tool_name == "navigate" and tool_args.get("url") == state["current_url"]:
                print(f"   ⏭️  Skipping - already at this URL")
                history.append(f"Step {step}: SKIPPED navigate - already at {state['current_url']}. Use wait_for_dashboard or explore_section instead.")
                continue
            
            # Track recent tools for stuck detection
            recent_tools.append(tool_name)
            if len(recent_tools) > 10:
                recent_tools.pop(0)
            
            # Detect if stuck in analysis loop (3+ analyze/explore/list without click/scroll)
            analysis_tools = {"analyze_page", "explore_section", "list_clickable_elements", "wait_for_page", "wait_for_dashboard"}
            progress_tools = {"click_element", "click_text", "scroll_page"}
            
            if tool_name in analysis_tools:
                analyze_count += 1
            elif tool_name in progress_tools:
                analyze_count = 0  # Reset on actual progress
            
            # AUTO-SCROLL: If stuck analyzing 3+ times without progress, force scroll
            if analyze_count >= 3:
                print(f"   🔄 STUCK DETECTED! {analyze_count} analyses without progress. AUTO-SCROLLING...")
                try:
                    scroll_result = await client.call_tool("scroll_page", {"direction": "down"})
                    scroll_text = _extract_result_text(scroll_result)
                    print(f"   → Auto-scroll: {scroll_text}")
                    history.append(f"Step {step}: AUTO-SCROLL (stuck detection) → {scroll_text}")
                    analyze_count = 0  # Reset counter
                    actions_taken += 1
                    continue  # Skip the original tool call, let agent analyze new content
                except Exception as e:
                    print(f"   ⚠️ Auto-scroll failed: {e}")
            
            # Execute the tool
            print(f"🔧 {tool_name}({tool_args})")
            if reason:
                print(f"   💡 {reason}")
            
            try:
                result = await client.call_tool(tool_name, tool_args)
                result_text = _extract_result_text(result)
                
                # Show result (truncated for readability)
                display = result_text[:300] + "..." if len(result_text) > 300 else result_text
                print(f"   → {display}")
                
                history.append(f"Step {step}: {tool_name}({tool_args}) → {result_text[:200]}")
                actions_taken += 1
                
                # Update state based on tool results
                parsed_result = _try_parse_json(result_text)
                if tool_name == "connect_browser":
                    if isinstance(parsed_result, dict) and parsed_result.get("status") == "connected":
                        state["connected"] = True
                elif tool_name == "navigate":
                    if isinstance(parsed_result, dict) and parsed_result.get("status") == "success":
                        state["current_url"] = tool_args.get("url")
                        state["dashboard_ready"] = False  # Reset - need to wait for dashboard
                elif tool_name == "login":
                    if isinstance(parsed_result, dict) and parsed_result.get("status") == "success":
                        state["logged_in"] = True
                        state["dashboard_ready"] = False  # Reset - need to wait for dashboard
                elif tool_name == "wait_for_dashboard":
                    if isinstance(parsed_result, dict) and parsed_result.get("status") == "ready":
                        state["dashboard_ready"] = True

                # Auto-recovery: if a click failed, analyze the page for alternatives
                if tool_name in ("click_element", "click_text"):
                    parsed = _try_parse_json(result_text)
                    status = parsed.get("status") if isinstance(parsed, dict) else None
                    if status in ("failed", "error"):
                        print("   ↪️  Click failed. Re-analyzing to find clickable alternatives...")
                        analysis = await client.call_tool("analyze_page", {
                            "question": (
                                "Based on the current page, list clickable items in the UI and panels. "
                                "Provide a prioritized sequence of what to click next to find wireless "
                                "controller issues. Include exact visible text for each item."
                            )
                        })
                        analysis_text = _extract_result_text(analysis)
                        print(f"   → {analysis_text[:400]}...")
                        history.append(f"Auto-analysis after click failure: {analysis_text[:300]}")
                
            except Exception as e:
                error_msg = str(e)
                print(f"   ❌ Error: {error_msg}")
                history.append(f"Step {step}: {tool_name}({tool_args}) → ERROR: {error_msg}")
                actions_taken += 1
        
        if actions_taken >= max_steps:
            # Reached max steps
            print(f"\n⚠️  Reached max steps ({max_steps})")
            print("Getting final analysis...")
            try:
                result = await client.call_tool("analyze_page", {
                    "question": f"Summarize what you see on this page for the task: {task}"
                })
                print(f"\n{_extract_result_text(result)}")
            except Exception as e:
                print(f"Could not get final analysis: {e}")
    
    print("\n✅ Task complete!")


# =============================================================================
# Interactive Mode
# =============================================================================

async def interactive_mode(url: str):
    """
    Interactive mode - call tools directly via MCP.
    """
    print("=" * 60)
    print("Browser Automation - Interactive Mode (FastMCP 3.0)")
    print("=" * 60)
    print(f"\nConnecting to {url}...")
    
    async with Client(url) as client:
        tools = await client.list_tools()
        tool_names = [t.name for t in tools]
        print(f"✅ Connected! Found {len(tools)} tools:")
        for t in tools:
            print(f"   - {t.name}")
        
        print("\n" + "=" * 60)
        print("Commands:")
        print("   <tool_name> [args]  - Call a tool directly")
        print("   tools               - List available tools")
        print("   quit                - Exit")
        print("=" * 60)
        
        while True:
            try:
                cmd = input("\n🤖 > ").strip()
                
                if not cmd:
                    continue
                
                if cmd.lower() in ("quit", "exit", "q"):
                    print("👋 Goodbye!")
                    break
                
                if cmd.lower() == "tools":
                    for t in tools:
                        print(f"   - {t.name}: {t.description[:60]}...")
                    continue
                
                # Parse command as tool call
                parts = cmd.split(maxsplit=1)
                tool_name = parts[0]
                
                if tool_name not in tool_names:
                    print(f"❌ Unknown tool: {tool_name}")
                    print(f"   Available: {', '.join(tool_names)}")
                    continue
                
                # Parse arguments
                args = {}
                if len(parts) > 1:
                    arg_str = parts[1]
                    # Handle simple key=value or just a value
                    if "=" in arg_str:
                        for pair in arg_str.split():
                            if "=" in pair:
                                k, v = pair.split("=", 1)
                                args[k] = v.strip('"\'')
                    else:
                        # Guess the first argument name based on tool
                        if tool_name == "navigate":
                            args["url"] = arg_str
                        elif tool_name == "analyze_page":
                            args["question"] = arg_str
                        elif tool_name == "click_element":
                            args["description"] = arg_str
                        elif tool_name == "scroll_page":
                            args["direction"] = arg_str
                        elif tool_name == "wait_seconds":
                            args["seconds"] = int(arg_str)
                        elif tool_name == "take_screenshot":
                            args["description"] = arg_str
                
                print(f"⏳ Calling {tool_name}({args})...")
                result = await client.call_tool(tool_name, args)
                
                # Extract and print result
                if hasattr(result, '__iter__') and not isinstance(result, (str, dict)):
                    for item in result:
                        if hasattr(item, 'text'):
                            print(f"📥 {item.text}")
                        else:
                            print(f"📥 {item}")
                else:
                    print(f"📥 {result}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


# =============================================================================
# Conceptual Example
# =============================================================================

def show_example():
    """Show the concept without running anything."""
    
    print("=" * 60)
    print("Browser MCP Client - FastMCP 3.0 Example")
    print("=" * 60)
    
    print("""
┌─────────────────────────────────────────────────────────────┐
│              BROWSER MCP CLIENT FLOW (FastMCP 3.0)           │
│              https://gofastmcp.com                           │
└─────────────────────────────────────────────────────────────┘

Terminal 1: Start Chrome with debug port
──────────────────────────────────────────
  $ ./restart_chrome.sh

Terminal 2: Start the MCP server
──────────────────────────────────────────
  $ python 01_browser_mcp_server.py
  [SERVER] Starting BrowserAgent (FastMCP 3.0)
  [SERVER] Tools: connect_browser, navigate, analyze_page, click_element...

Terminal 3: Run the client
──────────────────────────────────────────
  $ python 03_browser_mcp_client.py --task "Go to google.com and describe it"


FASTMCP 3.0 CLIENT CODE:
────────────────────────

from fastmcp import Client

async with Client("http://localhost:8000/sse") as client:
    # List available tools
    tools = await client.list_tools()
    
    # Call tools directly
    result = await client.call_tool("connect_browser", {})
    result = await client.call_tool("navigate", {"url": "https://google.com"})
    result = await client.call_tool("analyze_page", {"question": "What do you see?"})


INTERACTION FLOW:
─────────────────

[FastMCP Client → Server]
  await client.call_tool("connect_browser", {})

[Server Response]
  {"status": "connected", "message": "Successfully connected"}

[FastMCP Client → Server]
  await client.call_tool("navigate", {"url": "https://google.com"})

[Server Response]
  {"status": "success", "url": "https://google.com"}

[FastMCP Client → Server]
  await client.call_tool("analyze_page", {"question": "Describe what you see"})

[Server Response]
  {"status": "success", "analysis": "This is Google's homepage..."}
""")
    
    print("\n📋 Predefined prompts available:")
    for name, prompt in PROMPTS.items():
        first_line = prompt.strip().split('\n')[0]
        print(f"   • {name}: {first_line}")
    
    print("\n✅ Conceptual demo complete!")


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Browser Automation MCP Client")
    parser.add_argument("--url", type=str, default="http://localhost:8000/sse",
                        help="MCP server URL (default: http://localhost:8000/sse)")
    parser.add_argument("--task", "-t", type=str,
                        help="Task to execute")
    parser.add_argument("--prompt", "-p", choices=list(PROMPTS.keys()),
                        help="Use a predefined prompt")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Interactive mode")
    parser.add_argument("--example", action="store_true",
                        help="Show conceptual example")
    args = parser.parse_args()
    
    # Show example
    if args.example:
        show_example()
        exit(0)
    
    # Determine task
    task = None
    if args.prompt:
        task = PROMPTS[args.prompt]
    elif args.task:
        task = args.task
    
    print("Browser Automation MCP Client")
    print(f"Server: {args.url}")
    print()
    print("Prerequisites:")
    print("  1. ./restart_chrome.sh  (Chrome with debug port)")
    print("  2. python 01_browser_mcp_server.py  (MCP server)")
    print()
    
    try:
        if args.interactive:
            asyncio.run(interactive_mode(args.url))
        elif task:
            asyncio.run(main(args.url, task))
        else:
            # Default: run test task
            print("No task specified. Running test task...")
            print("(Use --task, --prompt, or --interactive for other options)")
            print()
            asyncio.run(main(args.url, PROMPTS["test"]))
            
    except ConnectionRefusedError:
        print("\n⚠️  Error: Could not connect to MCP server")
        print("\nMake sure the server is running:")
        print("  python 01_browser_mcp_server.py")
    except Exception as e:
        print(f"\n⚠️  Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Is Chrome running? ./restart_chrome.sh")
        print("  2. Is server running? python 01_browser_mcp_server.py")
        print("  3. Is GEMINI_API_KEY set in .env?")
