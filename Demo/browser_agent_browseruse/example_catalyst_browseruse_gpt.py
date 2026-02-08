"""
Demo: Cisco Catalyst Center - Using Browser-Use with GPT-4
A more reliable browser automation approach using the browser-use library.

Install first:
    pip install browser-use

Run Chrome with debug port first:
    ./restart_chrome.sh

Alternative: Use MCP Server (for Claude Desktop, Cursor integration):
    uvx browser-use --mcp
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env file")

# Catalyst Center credentials
CATALYST_URL = "https://10.48.81.206/dna/catalyst/home"
CATALYST_USERNAME = os.getenv("CATALYST_USERNAME", "admin")
CATALYST_PASSWORD = os.getenv("CATALYST_PASSWORD", "C1sc0!123")


async def investigate_catalyst():
    """
    Use Browser-Use with GPT-4 to investigate Catalyst Center health issues.
    This approach uses DOM/accessibility tree instead of vision-only,
    making it more reliable for clicking cards and complex UI elements.
    """
    
    # Import browser-use components
    from browser_use import Agent, Browser, ChatOpenAI
    
    print("\n" + "="*60)
    print("🔍 STARTING CATALYST CENTER INVESTIGATION (Browser-Use + GPT)")
    print("="*60)
    print(f"\nTarget: {CATALYST_URL}")
    print("Method: Browser-Use with DOM-based element detection")
    print("Model: GPT-4o")
    print("\n⏳ Connecting to Chrome debug port...")
    
    # Configure browser to connect to existing Chrome instance
    # Heavy enterprise apps like Catalyst Center need longer wait times
    browser = Browser(
        headless=False,
        cdp_url="http://localhost:9222",  # Connect to existing Chrome
        minimum_wait_page_load_time=20.0,  # Wait at least 20s for page to load
        wait_for_network_idle_page_load_time=30.0,  # Wait up to 30s for network idle
        wait_between_actions=8.0,  # Wait 8s between actions (for AJAX updates)
    )
    
    # Setup GPT-4 model using browser-use's native ChatOpenAI
    llm = ChatOpenAI(model="gpt-4o")
    
    # Define the investigation task
    task = f"""
You are a network troubleshooting agent investigating health issues in Cisco Catalyst Center.

AUTHENTICATION (if login page appears):
- Username: {CATALYST_USERNAME}
- Password: {CATALYST_PASSWORD}

MISSION: Find FAILING WIRELESS DEVICES, their IP addresses, locations, and root cause from Event Viewer/Syslog.

EXACT NAVIGATION STEPS:

STEP 1 - LOGIN & NAVIGATE TO HEALTH DASHBOARD:
1. Navigate to {CATALYST_URL}
2. If you see a login page, enter credentials and log in
3. From the LEFT MENU PANE, click on "Assurance"
4. Then click on "Dashboard" or "Health" (look for health-related option)

STEP 2 - FIND CRITICAL WIRELESS DEVICES:
5. Look for KEY PERFORMANCE INDICATOR section - find "Critical" with RED color
6. If "Critical" shows any number greater than 0, CLICK on "Critical" (RED)
7. This will filter/show only critical wireless devices
8. ONLY focus on Critical/RED - ignore Fair, Good, or other categories

STEP 3 - VIEW DEVICE TABLE:
9. A table will appear showing devices with columns:
   - Device Name
   - IP Address
   - Overall Health
10. CLICK on a Device Name (it's a clickable link)

STEP 4 - DEVICE DETAILS PAGE:
11. WAIT 15-20 seconds for the device page to fully load
12. SCROLL DOWN on the page to find "Event Viewer" section
13. Look on the RIGHT SIDE for any incidents or issues

STEP 5 - GET ROOT CAUSE:
14. In Event Viewer, look for:
    - Syslog messages
    - Error messages
    - Incident descriptions
15. Read the syslog message text - this contains the root cause

FINAL REPORT must include:
- Device Name
- IP Address
- Location/Site  
- Root Cause (from syslog/event viewer)
- Recommended fix

CRITICAL RULES:
- DO NOT REFRESH or RE-NAVIGATE if page is blank - just WAIT
- After EVERY click, WAIT 15-20 seconds for content to update
- Catalyst Center uses AJAX - pages update WITHOUT full reload
- SCROLL DOWN to find Event Viewer (it's below the fold)
- NEVER navigate to the same URL twice
- ONLY focus on CRITICAL (RED) wireless devices - ignore Fair/Good
"""
    
    # Create the agent with higher max_steps for complex investigations
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        max_steps=50,  # Default is ~10-20, increase for deep drilling
    )
    
    print("✅ Connected! Starting investigation...\n")
    
    try:
        # Run the agent
        history = await agent.run()
        
        print("\n" + "="*60)
        print("🎉 INVESTIGATION COMPLETE!")
        print("="*60)
        
        # Print only the final result (not full history with page source)
        if history:
            if hasattr(history, 'final_result') and history.final_result:
                print("\n📊 FINAL RESULT:")
                print(history.final_result)
            elif hasattr(history, 'result') and history.result:
                print("\n📊 FINAL RESULT:")
                print(history.result)
            else:
                print(f"\n📊 Completed in {len(history.history) if hasattr(history, 'history') else 1} steps")
        
        return history
        
    except Exception as e:
        print(f"\n❌ Error during investigation: {e}")
        import traceback
        traceback.print_exc()
        raise


async def simple_test():
    """
    Quick test to verify browser-use with GPT can reach Catalyst Center.
    """
    from browser_use import Agent, Browser, ChatOpenAI
    
    print("\n🧪 Running quick Catalyst Center test (GPT-4o)...")
    print(f"   Target: {CATALYST_URL}")
    
    browser = Browser(
        headless=False,
        cdp_url="http://localhost:9222",
        minimum_wait_page_load_time=20.0,  # Wait at least 20s for page to load
        wait_for_network_idle_page_load_time=30.0,  # Wait up to 30s for network idle
        wait_between_actions=8.0,  # Wait 8s between actions (for AJAX updates)
    )
    
    llm = ChatOpenAI(model="gpt-4o")
    
    task = f"""
Navigate to {CATALYST_URL}

If you see a login page:
- Enter username: {CATALYST_USERNAME}
- Enter password: {CATALYST_PASSWORD}
- Click the login/sign in button

GOAL: Find FAILING WIRELESS DEVICES with IP, location, and root cause from Event Viewer.

NAVIGATION:
1. From LEFT MENU, click "Assurance" then "Dashboard" or "Health"
2. Look for KEY PERFORMANCE INDICATOR - find "Critical" (RED color)
3. Click on "Critical" (RED) if it shows any number > 0 - ONLY focus on Critical
4. A device table appears - click on a Device Name
5. WAIT 15-20 seconds for device page to load
6. SCROLL DOWN to find "Event Viewer" section
7. Look on RIGHT SIDE for incidents and syslog messages
8. Report: Device Name, IP, Location, Root Cause from syslog

CRITICAL RULES:
- DO NOT REFRESH if page is blank - just WAIT
- After EVERY click, WAIT 15-20 seconds
- SCROLL DOWN to find Event Viewer
- NEVER navigate to same URL twice
"""
    
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        max_steps=50,  # Enough steps to drill down and find device details
    )
    
    try:
        result = await agent.run()
        print(f"\n✅ Test successful!")
        return result
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


def main():
    """Main entry point"""
    import sys
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║   Catalyst Center Investigation - Browser-Use + GPT-4 Edition ║
╠══════════════════════════════════════════════════════════════╣
║  This version uses browser-use for more reliable automation  ║
║  - DOM-based element detection (not just vision)             ║
║  - Better handling of cards, spans, and complex UI           ║
║  - Powered by GPT-4o                                         ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # Check if Chrome is running with debug port
    import subprocess
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:9222/json/version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            raise Exception("Chrome not responding")
        print("✅ Chrome debug port detected\n")
    except:
        print("❌ Chrome is not running with debug port!")
        print("\n💡 Fix: Run ./restart_chrome.sh first")
        print("   Or manually: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 --user-data-dir=$HOME/chrome-debug-profile")
        sys.exit(1)
    
    # Run investigation
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        asyncio.run(simple_test())
    else:
        asyncio.run(investigate_catalyst())


if __name__ == "__main__":
    main()
