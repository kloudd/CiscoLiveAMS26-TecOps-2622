import os
import time
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage

from .state import AgentState
from .tools import ALL_TOOLS

logger = logging.getLogger(__name__)

# Maximum number of agent loop iterations before forcing a stop
MAX_LOOP_STEPS = 50

# Retry settings for transient Gemini API errors (connection resets, timeouts)
LLM_MAX_RETRIES = 3
LLM_RETRY_BASE_DELAY = 5  # seconds

# Initialize the model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    convert_system_message_to_human=True
)

# Bind tools to the model
llm_with_tools = llm.bind_tools(ALL_TOOLS)

SYSTEM_PROMPT = """You are an expert SRE (Site Reliability Engineer) Browser Automation Agent.
Your goal is to complete the user's task by controlling a web browser via tools.

### ====== WORKFLOW FOR EVERY NEW PAGE ======

After EVERY navigation or click that loads a new page:
  1. wait_for_page(max_wait=30) — wait for the page to stabilize
  2. list_clickable_elements() — discover ALL clickable items on the page
  3. click_text("exact text") — click using EXACT text from list_clickable_elements

list_clickable_elements already returns only clickable items. Trust its results and click directly.
Do NOT call hover_text before clicking — it wastes time. Only use hover_text as a last resort.
NEVER use click_element() — it uses AI vision and often misclicks to the wrong element.

### ====== TEXT FROM list_clickable_elements ======

list_clickable_elements returns multi-line text like "Wireless controllers\n0 / 1".
When clicking, try the SHORTEST unique part of that text, e.g.:
  - From "Wireless controllers\n0 / 1" → click_text("0 / 1") or click_text("Wireless controllers")
  - From "Link Errors\n1 device link errors > 1 %" → click_text("Link Errors")
  - From "Critical (1)" → click_text("Critical (1)")
If click_text fails with the short text, try extract_text() to see the exact visible text on the page.

### ====== PAGE LOADING ======

- wait_for_page uses SCREENSHOT COMPARISON. If it returns "timeout", call it again with longer timeout.
- For dashboards, use wait_for_dashboard(max_wait=60) to wait for panels to populate.
- If result shows "login_required", call login() first, then wait again.

### ====== CLICKING RULES ======

- ALWAYS use click_text() with text from list_clickable_elements or extract_text.
- PRIORITY: red indicators (0/X, Critical) > blue links > numbered items > panels.
- "0/1" = 0 healthy out of 1 = PROBLEM. Click it!
- If click_text fails, try with exact=False: click_text("text", exact=False)
- If still fails, use extract_text() to see what text is actually on the page, then retry.
- ONLY as a very last resort, use click_element(description) for AI-vision clicking.

### ====== DRILL DOWN — NEVER NAVIGATE AWAY ======

- Once you click into a detail page (e.g., Wireless Controllers), STAY ON IT.
- Do NOT navigate back to the dashboard or to a different section.
- DRILL DEEPER: list_clickable_elements → click the specific device or issue.
- If you can't find details, SCROLL DOWN — device info and events are at the bottom.
- If you still can't find it, use extract_text() to read ALL text on the page.

### ====== SCROLLING IS MANDATORY ======

- If you cannot find an element or details, **SCROLL DOWN**.
- Events, Logs, Syslog, error messages are almost always at the BOTTOM.
- If you've analyzed the same view twice without new info, SCROLL DOWN.
- Device details pages are very long — scroll multiple times.
- If scroll_page fails, try extract_text() to read page content directly.

### ====== RESILIENCE ======

- If a click fails, try click_text with exact=False.
- If that fails, use extract_text() to see the actual text, then click with corrected text.
- If a tool errors, try a different approach — do not repeat the same failing call.
- Do NOT call analyze_page repeatedly — it's slow (calls AI vision). Prefer extract_text + list_clickable_elements.

### ====== COMPLETION ======

Report: device name, IP, location, and the ROOT CAUSE from events/syslog.
Provide a clear, detailed summary when the investigation is complete.
"""

def _invoke_with_retry(runnable, messages):
    """
    Invoke the LLM with retry + exponential backoff for transient network errors
    (e.g. 'Connection reset by peer', timeouts, 503s).
    """
    last_error = None
    for attempt in range(1, LLM_MAX_RETRIES + 1):
        try:
            return runnable.invoke(messages)
        except Exception as exc:
            last_error = exc
            error_str = str(exc).lower()
            # Only retry on transient / network errors
            transient = any(keyword in error_str for keyword in [
                "connection reset",
                "connection error",
                "connect error",
                "timed out",
                "timeout",
                "503",
                "429",
                "rate limit",
                "server error",
                "service unavailable",
                "temporary failure",
            ])
            if not transient or attempt == LLM_MAX_RETRIES:
                raise
            delay = LLM_RETRY_BASE_DELAY * (2 ** (attempt - 1))  # 5s, 10s, 20s
            print(f"  [retry] Gemini API error (attempt {attempt}/{LLM_MAX_RETRIES}): {exc}")
            print(f"  [retry] Retrying in {delay}s...")
            time.sleep(delay)
    raise last_error  # should not reach here


def agent_node(state: AgentState):
    """
    The main agent node that invokes the LLM.
    Includes retry logic for transient Gemini API network errors.
    """
    messages = state['messages']

    # If this is the first message, prepend the system prompt
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    # Invoke the model with retry for transient errors
    response = _invoke_with_retry(llm_with_tools, messages)

    # Update loop step
    return {"messages": [response], "loop_step": state.get("loop_step", 0) + 1}


def should_continue(state: AgentState):
    """
    Determine if the agent should continue or stop.
    Includes a max step safety limit.
    """
    messages = state['messages']
    last_message = messages[-1]
    loop_step = state.get("loop_step", 0)

    # Safety: stop if we've hit max loop steps
    if loop_step >= MAX_LOOP_STEPS:
        return "end"

    # If the LLM called a tool, continue to the tool node
    if last_message.tool_calls:
        return "tools"

    # Otherwise, stop (the LLM has finished or provided a final answer)
    return "end"
