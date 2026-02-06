"""
Demo: Cisco Catalyst Center - Network Health Root Cause Analysis
This demonstrates autonomous troubleshooting capability of the agent
"""

from browser_agent import BrowserAgent


def main():
    """
    Use Case:
    The agent autonomously investigates network device health issues in Catalyst Center.
    It will:
    1. Navigate to Catalyst Center dashboard
    2. Identify devices with health issues
    3. Investigate root causes by exploring related dashboards
    4. Provide comprehensive troubleshooting analysis
    """
    
    # Initialize agent
    agent = BrowserAgent()
    
    # Define the goal - Let the agent figure out WHY devices are down
    goal = """
You are a network troubleshooting agent investigating health issues in Cisco Catalyst Center.

MISSION: Investigate why network device health is down and identify root causes.

STEP 1 - INITIAL ASSESSMENT:
1. Navigate to https://10.48.81.206/dna/catalyst/home
2. Take a screenshot and analyze the main dashboard
3. Look for:
   - Overall network health score
   - Number of devices with issues
   - Any critical alerts or warnings
   - Health indicators (red, yellow, green)

STEP 2 - IDENTIFY AFFECTED DEVICES:
4. If you see unhealthy devices, navigate to the appropriate section to see device details
   - Look for links like "Devices", "Inventory", "Network Health", or "Assurance"
   - Click on sections that show device status
5. Take screenshots and identify:
   - Which specific devices are down or unhealthy
   - Device names, IP addresses, and types
   - What health metrics are failing (reachability, CPU, memory, etc.)

STEP 3 - ROOT CAUSE INVESTIGATION:
6. For devices with issues, dig deeper by:
   - Clicking on device names to see detailed status
   - Checking recent events or alerts related to these devices
   - Looking for patterns (is it all switches? All in one location?)
   - Checking connectivity issues, interface status, or configuration problems
7. Explore related dashboards:
   - Issues/Alarms dashboard
   - Network topology or maps
   - Client health (if devices are access points)
   - Any "Why" or "Root Cause" analysis features

STEP 4 - ANALYSIS & CORRELATION:
8. Connect the dots:
   - Is there a common cause affecting multiple devices?
   - Did something change recently (configuration, firmware)?
   - Are there network connectivity issues upstream?
   - Is it a monitoring issue or actual device failure?

FINAL REPORT:
9. Provide a comprehensive troubleshooting report including:
   - Summary of network health status
   - List of affected devices with their issues
   - Root cause analysis (what's causing the problems)
   - Potential remediation steps
   - Your confidence level in the diagnosis

IMPORTANT NOTES:
- You may need to authenticate - the browser should already be logged in
- Use CLICK to navigate between sections
- Take screenshots at each major finding
- Be thorough but efficient - explore what's relevant
- If you can't find certain information, note that in your report
- Think like a network engineer troubleshooting a production issue
"""
    
    try:
        # Run the agent
        print("\n" + "="*60)
        print("🔍 STARTING NETWORK HEALTH INVESTIGATION")
        print("="*60)
        print("\nTarget: Cisco Catalyst Center")
        print("URL: https://10.50.222.153/dna/home")
        print("\nThe agent will autonomously:")
        print("  1. Assess overall network health")
        print("  2. Identify unhealthy devices")
        print("  3. Investigate root causes")
        print("  4. Provide troubleshooting recommendations")
        print("\n⚠️  NOTE: Make sure you're logged in to Catalyst Center")
        print("   in the debug Chrome window (run ./restart_chrome.sh first)")
        print("\n⏱️  Expected duration: 5-10 minutes for full investigation")
        print("   (Max 30 investigation steps allowed)")
        print("")
        
        report = agent.run(goal)
        
        print("\n" + "="*60)
        print("🎉 INVESTIGATION COMPLETE!")
        print("="*60)
        print("\nThe agent successfully:")
        print("✓ Analyzed Catalyst Center dashboard")
        print("✓ Identified devices with health issues")
        print("✓ Investigated root causes autonomously")
        print("✓ Provided troubleshooting analysis")
        print("\nCheck screenshots/ folder for visual evidence")
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Investigation interrupted by user")
    except Exception as e:
        print(f"\n❌ Investigation failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        agent.close()


if __name__ == "__main__":
    main()
