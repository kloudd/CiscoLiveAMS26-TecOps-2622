"""
Demo: Cisco Catalyst Center - Using Browser-Use
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

# Check for API key - Browser-Use uses GOOGLE_API_KEY (not GEMINI_API_KEY)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY (or GEMINI_API_KEY) not found in .env file")

# Set the env var that browser-use expects
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# Catalyst Center credentials
CATALYST_URL = "https://10.48.81.206/dna/catalyst/home"
CATALYST_USERNAME = os.getenv("CATALYST_USERNAME", "admin")
CATALYST_PASSWORD = os.getenv("CATALYST_PASSWORD", "C1sc0!123")


async def investigate_catalyst():
    """
    Use Browser-Use to investigate Catalyst Center health issues.
    This approach uses DOM/accessibility tree instead of vision-only,
    making it more reliable for clicking cards and complex UI elements.
    """
    
    # Import browser-use components (native classes, not LangChain)
    from browser_use import Agent, Browser, ChatGoogle
    
    print("\n" + "="*60)
    print("🔍 STARTING CATALYST CENTER INVESTIGATION (Browser-Use)")
    print("="*60)
    print(f"\nTarget: {CATALYST_URL}")
    print("Method: Browser-Use with DOM-based element detection")
    print("\n⏳ Connecting to Chrome debug port...")
    
    # Configure browser to connect to existing Chrome instance
    # Heavy enterprise apps like Catalyst Center need longer wait times
    browser = Browser(
        headless=False,
        cdp_url="http://localhost:9222",  # Connect to existing Chrome
        minimum_wait_page_load_time=30.0,  # Wait at least 30s for page to load
        wait_for_network_idle_page_load_time=45.0,  # Wait up to 45s for network idle
        wait_between_actions=10.0,  # Wait 10s between actions (for AJAX updates)
    )
    
    # Setup Gemini model using browser-use's native ChatGoogle
    llm = ChatGoogle(model="gemini-3-flash-preview")
    
    # Define the investigation task
    task = f"""
You are a network troubleshooting agent investigating WIRELESS health issues in Cisco Catalyst Center.

AUTHENTICATION (if login page appears):
- Username: {CATALYST_USERNAME}
- Password: {CATALYST_PASSWORD}

MISSION: Find CRITICAL WIRELESS DEVICES (RED status), their IP addresses, locations, and root cause from Event Viewer/Syslog.

FOCUS: ONLY on WIRELESS devices. ONLY on CRITICAL (RED) status. IGNORE Fair, Good, or any other category.

EXACT NAVIGATION STEPS:

STEP 1 - LOGIN & NAVIGATE TO HEALTH DASHBOARD:
1. Navigate to {CATALYST_URL}
2. If you see a login page, enter credentials and log in
3. From the LEFT MENU PANE, click on "Assurance"
4. Then click on "Dashboard" or "Health" (look for health-related option)
5. Look for WIRELESS section specifically

STEP 2 - FIND CRITICAL WIRELESS DEVICES:
6. Look for "Wireless Controller" showing "0/1" with a RED BAR - this means 0 healthy out of 1
7. CLICK DIRECTLY on the RED BAR or "0/1" or "Wireless Controller" text
8. Also look for "Access Point" with unhealthy status (e.g., "1/2" means 1 healthy out of 2)
9. Click on any RED colored bar or unhealthy wireless device indicator
10. The RED bar IS the critical indicator - click on it to drill down

STEP 3 - VIEW DEVICE TABLE:
10. A table will appear showing wireless devices with columns:
    - Device Name
    - IP Address
    - Overall Health
11. CLICK on a Device Name (it's a clickable link)

STEP 4 - DEVICE DETAILS PAGE:
12. WAIT 30 seconds for the device page to fully load
13. SCROLL DOWN on the page to find "Event Viewer" section
14. Look on the RIGHT SIDE for any incidents or issues

STEP 5 - GET ROOT CAUSE:
15. In Event Viewer, look for:
    - Syslog messages
    - Error messages
    - Incident descriptions
16. Read the syslog message text - this contains the root cause

FINAL REPORT must include:
- Device Name (wireless controller or access point)
- IP Address
- Location/Site  
- Root Cause (from syslog/event viewer)
- Recommended fix

CRITICAL RULES:
- ONLY investigate WIRELESS devices (Wireless Controller, Access Point) - ignore switches, routers
- Look for RED BARS showing unhealthy status like "0/1" - CLICK on the RED BAR directly
- The RED colored bar IS the critical indicator - click on it
- DO NOT REFRESH or RE-NAVIGATE if page is blank - just WAIT
- After EVERY click, WAIT 30 seconds for content to update
- Catalyst Center uses AJAX - pages update WITHOUT full reload
- SCROLL DOWN to find Event Viewer (it's below the fold)
- NEVER navigate to the same URL twice
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
        
        # Print the history/results
        # if history:
        #     print("\n📊 Agent History:")
        #     for i, step in enumerate(history.history if hasattr(history, 'history') else [history]):
        #         print(f"\nStep {i+1}:")
        #         print(f"  {step}")
        
        return history
        
    except Exception as e:
        print(f"\n❌ Error during investigation: {e}")
        import traceback
        traceback.print_exc()
        raise


async def simple_test():
    """
    Quick test to verify browser-use can reach Catalyst Center.
    """
    from browser_use import Agent, Browser, ChatGoogle
    
    print("\n🧪 Running quick Catalyst Center test...")
    print(f"   Target: {CATALYST_URL}")
    
    browser = Browser(
        headless=False,
        cdp_url="http://localhost:9222",
        minimum_wait_page_load_time=30.0,  # Wait at least 30s for page to load
        wait_for_network_idle_page_load_time=45.0,  # Wait up to 45s for network idle
        wait_between_actions=10.0,  # Wait 10s between actions (for AJAX updates)
    )
    
    llm = ChatGoogle(model="gemini-2.0-flash")
    
    task = f"""
Navigate to {CATALYST_URL}

If you see a login page:
- Enter username: {CATALYST_USERNAME}
- Enter password: {CATALYST_PASSWORD}
- Click the login/sign in button

GOAL: Find CRITICAL WIRELESS DEVICES (RED only) with IP, location, and root cause.

FOCUS: ONLY WIRELESS devices. ONLY CRITICAL (RED) status. IGNORE Fair, Good, or others.

NAVIGATION:
1. From LEFT MENU, click "Assurance" then "Dashboard" or "Health"
2. Look for "Wireless Controller" or "Access Point" widgets
3. Find the RED BAR showing unhealthy status (e.g., "0/1" means 0 healthy out of 1)
4. CLICK DIRECTLY on the RED BAR or the "0/1" text or "Wireless Controller" label
5. A device table appears - click on a Device Name
6. WAIT 30 seconds for device page to load
7. SCROLL DOWN to find "Event Viewer" section
8. Look on RIGHT SIDE for incidents and syslog messages
9. Report: Device Name, IP, Location, Root Cause from syslog

CRITICAL RULES:
- ONLY WIRELESS devices (Wireless Controller, Access Point)
- CLICK on RED BARS directly - they show unhealthy devices
- DO NOT REFRESH if page is blank - just WAIT
- After EVERY click, WAIT 30 seconds
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
║     Catalyst Center Investigation - Browser-Use Edition      ║
╠══════════════════════════════════════════════════════════════╣
║  This version uses browser-use for more reliable automation  ║
║  - DOM-based element detection (not just vision)             ║
║  - Better handling of cards, spans, and complex UI           ║
║  - Indexed elements for precise clicking                     ║
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
