"""
Browser Agent MCP Client

A client script to send instructions to the LangGraph Browser Agent MCP server.

Usage:
    # Interactive mode
    python browser_client.py
    
    # With a specific task
    python browser_client.py "Navigate to google.com and tell me what you see"
    
    # Using a prompt file
    python browser_client.py --file prompts/catalyst_investigation.txt
"""

import os
import sys
import asyncio
import argparse
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# MCP Client using fastmcp
# ============================================================================

async def run_with_mcp_client(task: str):
    """
    Connect to the MCP server and run a browser task.
    Uses fastmcp's Client to connect to the server.
    """
    from fastmcp import Client
    
    print(f"\n{'='*60}")
    print("🔗 Connecting to Browser Agent MCP Server...")
    print(f"{'='*60}")
    
    # Connect to the MCP server (running as subprocess)
    async with Client("langgraph_browser_mcp.py") as client:
        print("✅ Connected to MCP server")
        
        # List available tools
        tools = await client.list_tools()
        print(f"\n📦 Available tools: {[t.name for t in tools]}")
        
        print(f"\n{'='*60}")
        print(f"🎯 TASK: {task}")
        print(f"{'='*60}\n")
        
        # Run the task using browser_run_task
        result = await client.call_tool("browser_run_task", {"task": task})
        
        print(f"\n{'='*60}")
        print("📊 RESULT")
        print(f"{'='*60}")
        
        # Extract text from TextContent if needed
        if isinstance(result, list) and len(result) > 0:
            first_item = result[0]
            if hasattr(first_item, 'text'):
                print(first_item.text)
            else:
                print(result)
        else:
            print(result)
        
        return result


# ============================================================================
# Direct Mode (without MCP, for testing)
# ============================================================================

def run_direct(task: str):
    """
    Run the browser agent directly without MCP.
    Useful for testing and debugging.
    """
    print(f"\n{'='*60}")
    print("🚀 Running Browser Agent Directly (no MCP)")
    print(f"{'='*60}")
    print(f"\n🎯 TASK: {task}\n")
    
    # Import and run the agent directly
    from langgraph_browser_mcp import browser_run_task
    
    result = browser_run_task(task)
    
    print(f"\n{'='*60}")
    print("📊 RESULT")
    print(f"{'='*60}")
    print(result)
    
    return result


# ============================================================================
# Step-by-Step Mode (manual control)
# ============================================================================

def run_interactive():
    """
    Interactive mode - manually call individual tools.
    Great for debugging and step-by-step exploration.
    """
    from langgraph_browser_mcp import (
        browser_state,
        navigate,
        take_screenshot,
        analyze_page,
        click_element,
        extract_text,
        scroll_page,
        wait_seconds,
    )
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║          Browser Agent - Interactive Mode                    ║
╠══════════════════════════════════════════════════════════════╣
║  Commands:                                                   ║
║    connect              - Connect to Chrome                  ║
║    go <url>             - Navigate to URL                    ║
║    screenshot           - Take screenshot                    ║
║    analyze <question>   - Analyze page with AI               ║
║    click <description>  - Click an element                   ║
║    text                 - Extract page text                  ║
║    scroll <up|down>     - Scroll page                        ║
║    wait <seconds>       - Wait                               ║
║    task <description>   - Run full autonomous task           ║
║    quit                 - Exit                               ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    while True:
        try:
            cmd = input("\n🤖 > ").strip()
            
            if not cmd:
                continue
            
            parts = cmd.split(maxsplit=1)
            action = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""
            
            if action in ("quit", "exit", "q"):
                print("👋 Goodbye!")
                break
            
            elif action == "connect":
                result = browser_state.connect()
                print(f"   {result}")
            
            elif action == "go":
                if not arg:
                    print("   ❌ Usage: go <url>")
                    continue
                result = navigate.invoke({"url": arg})
                print(f"   {result}")
            
            elif action == "screenshot":
                result = take_screenshot.invoke({"description": arg or "interactive"})
                print(f"   {result}")
            
            elif action == "analyze":
                if not arg:
                    arg = "What do you see on this page?"
                result = analyze_page.invoke({"question": arg})
                print(f"\n   📊 Analysis:\n   {result}")
            
            elif action == "click":
                if not arg:
                    print("   ❌ Usage: click <element description>")
                    continue
                result = click_element.invoke({"description": arg})
                print(f"   {result}")
            
            elif action == "text":
                result = extract_text.invoke({})
                print(f"\n   📄 Page text:\n   {result[:500]}...")
            
            elif action == "scroll":
                direction = arg if arg in ("up", "down") else "down"
                result = scroll_page.invoke({"direction": direction})
                print(f"   {result}")
            
            elif action == "wait":
                try:
                    seconds = int(arg) if arg else 5
                except ValueError:
                    seconds = 5
                result = wait_seconds.invoke({"seconds": seconds})
                print(f"   {result}")
            
            elif action == "task":
                if not arg:
                    print("   ❌ Usage: task <description of what to do>")
                    continue
                from langgraph_browser_mcp import browser_run_task
                print(f"\n   🚀 Running task: {arg}\n")
                result = browser_run_task(arg)
                print(f"\n   📊 Result:\n   {result}")
            
            else:
                print(f"   ❌ Unknown command: {action}")
                print("   Try: connect, go, screenshot, analyze, click, text, scroll, wait, task, quit")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"   ❌ Error: {e}")


# ============================================================================
# Predefined Prompts
# ============================================================================

PROMPTS = {
    "catalyst_wireless": """
Investigate WIRELESS health issues in Cisco Catalyst Center.

1. Connect to the browser
2. Navigate to https://10.48.81.206/dna/catalyst/home
3. From the left menu, click on "Assurance" then "Dashboard"
4. Find WIRELESS section - look for "Wireless Controller" or "Access Point"
5. Look for RED status bars showing unhealthy devices (e.g., "0/1" means 0 healthy)
6. Click on the RED bar to drill down
7. Find device details: Name, IP Address, Location
8. Scroll down to find "Event Viewer" section
9. Look for syslog messages that explain the root cause
10. Report: Device Name, IP, Location, Root Cause, Recommended Fix
""",
    
    "grafana_alerts": """
Check Grafana dashboards for alerts.

1. Connect to the browser
2. Navigate to https://sumitkanwal.grafana.net/dashboards
3. Take a screenshot and analyze what dashboards are available
4. Look for any dashboards showing alerts or warnings
5. Click on each dashboard and check for issues
6. Report any alerts, errors, or anomalies found
""",
    
    "simple_test": """
Simple browser test.

1. Connect to the browser
2. Navigate to https://www.google.com
3. Take a screenshot
4. Analyze what you see on the page
5. Report the result
""",
}


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Browser Agent MCP Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python browser_client.py                              # Interactive mode
    python browser_client.py "Go to google.com"           # Run a task
    python browser_client.py --direct "Go to google.com"  # Direct mode (no MCP)
    python browser_client.py --prompt catalyst_wireless   # Use predefined prompt
    python browser_client.py --list-prompts               # List available prompts
        """
    )
    
    parser.add_argument("task", nargs="?", help="Task to execute")
    parser.add_argument("--direct", "-d", action="store_true", 
                        help="Run directly without MCP server")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Interactive step-by-step mode")
    parser.add_argument("--prompt", "-p", choices=list(PROMPTS.keys()),
                        help="Use a predefined prompt")
    parser.add_argument("--list-prompts", action="store_true",
                        help="List available predefined prompts")
    parser.add_argument("--file", "-f", help="Read task from a file")
    
    args = parser.parse_args()
    
    # List prompts
    if args.list_prompts:
        print("\n📋 Available Predefined Prompts:\n")
        for name, prompt in PROMPTS.items():
            first_line = prompt.strip().split('\n')[0]
            print(f"  • {name}: {first_line}")
        print("\nUsage: python browser_client.py --prompt <name>")
        return
    
    # Interactive mode
    if args.interactive or (not args.task and not args.prompt and not args.file):
        run_interactive()
        return
    
    # Get task from various sources
    task = None
    
    if args.prompt:
        task = PROMPTS[args.prompt]
    elif args.file:
        with open(args.file, "r") as f:
            task = f.read()
    elif args.task:
        task = args.task
    
    if not task:
        parser.print_help()
        return
    
    # Run the task
    if args.direct:
        run_direct(task)
    else:
        asyncio.run(run_with_mcp_client(task))


if __name__ == "__main__":
    main()
