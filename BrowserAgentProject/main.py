import asyncio
import argparse
import os
from dotenv import load_dotenv

# Load environment variables from the package directory's .env file
# This is needed because the module is run from the workspace root via:
#   python -m BrowserAgentProject.main
# but the .env file lives inside BrowserAgentProject/
_package_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_package_dir, ".env"))

from langchain_core.messages import HumanMessage
from .graph import app

# =============================================================================
# Predefined Prompts
# =============================================================================

PROMPTS = {
    "catalyst": """
You are an SRE investigating wireless Controller issues in Cisco Catalyst Center.

URL: https://10.48.81.206/dna/catalyst/home

YOUR MISSION: Find the root cause of the "Critical" wireless issue.

=== STEP-BY-STEP PLAN ===

PHASE 1 — Connect and Load Dashboard:
1. connect_browser()
2. navigate("https://10.48.81.206/dna/catalyst/home")
3. wait_for_page(max_wait=30)
4. If login required → login() → wait_for_page(max_wait=30)
5. wait_for_dashboard(max_wait=60)

PHASE 2 — Find and Click the Wireless Issue:
6. list_clickable_elements() — find all clickable elements
7. click_text("0 / 1") or click_text("Wireless controllers") — click the critical indicator
8. wait_for_page(max_wait=30)

PHASE 3 — Drill Into Wireless Controller Detail:
9.  list_clickable_elements() — see what's on the new page
10. extract_text() — read the page to find device names, IPs
11. click_text("device name or Critical link") — drill deeper
12. wait_for_page(max_wait=30)

PHASE 4 — Find Root Cause:
13. list_clickable_elements() — look for Events/Issues/Logs links
14. scroll_page(direction="down") — events are at the BOTTOM
15. scroll_page(direction="down") — keep scrolling
16. extract_text() — read the events/error messages
17. If needed, scroll more and extract_text again

PHASE 5 — Report:
18. Report: device name, IP, and the specific ERROR MESSAGE

=== RULES ===
- Use list_clickable_elements() before clicking on a new page
- Use click_text() with SHORT text from the list (e.g. "0 / 1" not the full multi-line text)
- If click_text fails, try click_text("text", exact=False)
- If that fails, use extract_text() to see actual visible text, then retry
- NEVER navigate away from the wireless detail page — DRILL DEEPER
- NEVER use click_element() — it misclicks. Use list_clickable_elements + click_text
- If you can't find info, SCROLL DOWN — the page is very long
- If scroll fails, use extract_text() instead
- Do NOT call analyze_page repeatedly — it's slow. Prefer extract_text + list_clickable_elements
""",

    "test": """
Simple browser test.

Steps:
1. Connect to the browser
2. Navigate to https://www.google.com
3. Wait for the page to load
4. Take a screenshot and analyze what you see
5. Report the result
""",
}


async def main():
    parser = argparse.ArgumentParser(description="Browser Agent Project (LangGraph)")
    parser.add_argument("--task", "-t", type=str,
                        help="The task for the agent to perform")
    parser.add_argument("--prompt", "-p", choices=list(PROMPTS.keys()),
                        help=f"Use a predefined prompt ({', '.join(PROMPTS.keys())})")
    args = parser.parse_args()

    # Determine the task
    if args.prompt:
        task = PROMPTS[args.prompt]
    elif args.task:
        task = args.task
    else:
        # Default to catalyst
        print("No task specified. Defaulting to 'catalyst' prompt.")
        print("(Use --task 'your task' or --prompt catalyst|test)\n")
        task = PROMPTS["catalyst"]

    print("=" * 60)
    print("Browser Agent (LangGraph + MCP)")
    print("=" * 60)
    print(f"\nTask: {task.strip()[:200]}...")
    print("-" * 60)

    # Initial state
    initial_state = {
        "messages": [HumanMessage(content=task)],
        "loop_step": 0,
        "task": task,
        "current_url": "",
        "screenshot_path": ""
    }

    # Run the graph with streaming
    async for event in app.astream(initial_state):
        for key, value in event.items():
            if key == "agent":
                last_msg = value["messages"][-1]
                step = value.get("loop_step", "?")
                print(f"\n{'─'*40}")
                print(f"Step {step} | Agent")
                print(f"{'─'*40}")

                # Print agent's reasoning (if any text content)
                if last_msg.content:
                    content = last_msg.content if len(last_msg.content) <= 500 else last_msg.content[:500] + "..."
                    print(f"  {content}")

                # Print tool calls
                if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                    for tc in last_msg.tool_calls:
                        args_str = str(tc['args'])
                        if len(args_str) > 150:
                            args_str = args_str[:150] + "..."
                        print(f"  Tool: {tc['name']}({args_str})")

            elif key == "tools":
                print(f"\n  Tool Results:")
                for msg in value["messages"]:
                    content = msg.content
                    display = content[:300] + "..." if len(content) > 300 else content
                    print(f"    -> {display}")

    print(f"\n{'='*60}")
    print("Task complete!")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
