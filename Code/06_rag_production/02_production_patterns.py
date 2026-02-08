"""
=============================================================================
DEMO 02: Production Patterns
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 08 - RAG & Production Patterns

Essential patterns for running agents in production:
  1. Cost tracking          — stay on budget
  2. Retry with backoff     — handle transient failures
  3. Tool sandboxing        — enforce permissions
  4. Structured logging     — observability
=============================================================================
"""

import os
import json
import logging
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from tenacity import retry, stop_after_attempt, wait_exponential

# =============================================================================
# PATTERN 1: Cost Tracking
# =============================================================================

class CostLimitExceeded(Exception):
    pass


class CostTracker:
    """Track API token usage and enforce a spending cap."""

    def __init__(self, max_cost: float = 1.0):
        self.max_cost = max_cost
        self.total_tokens = 0
        self.total_cost = 0.0
        self.calls = 0

    def add_usage(self, prompt_tokens: int, completion_tokens: int):
        self.calls += 1
        self.total_tokens += prompt_tokens + completion_tokens
        self.total_cost += prompt_tokens * 0.00001 + completion_tokens * 0.00003
        if self.total_cost > self.max_cost:
            raise CostLimitExceeded(
                f"Cost ${self.total_cost:.4f} exceeds limit ${self.max_cost}"
            )

    def report(self) -> str:
        return (f"Calls: {self.calls} | "
                f"Tokens: {self.total_tokens:,} | "
                f"Cost: ${self.total_cost:.4f}")

# =============================================================================
# PATTERN 2: Retry with Exponential Backoff
# =============================================================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
def call_with_retry(func, *args, **kwargs):
    """Call any function with automatic retry (3 attempts, exponential backoff)."""
    return func(*args, **kwargs)

# =============================================================================
# PATTERN 3: Tool Sandboxing / Permission Levels
# =============================================================================

class SandboxedToolExecutor:
    """Enforce permission-based access control on tools."""

    PERMISSIONS = {
        "read":  ["get_device_status", "get_cpu_utilization", "list_devices"],
        "write": ["configure_vlan", "backup_config"],
        "admin": ["reboot_device", "restore_config"],
    }

    DANGEROUS_PATTERNS = ["DELETE", "DROP", "shutdown", "reload", "format"]

    def __init__(self, level: str = "read"):
        self.level = level
        # Build allowed set: read ⊂ write ⊂ admin
        self.allowed = set()
        for lvl in ("read", "write", "admin"):
            self.allowed.update(self.PERMISSIONS[lvl])
            if lvl == self.level:
                break

    def can_execute(self, tool_name: str, args: dict) -> tuple[bool, str]:
        if tool_name not in self.allowed:
            return False, f"'{tool_name}' not allowed at level '{self.level}'"
        args_upper = str(args).upper()
        for pat in self.DANGEROUS_PATTERNS:
            if pat in args_upper:
                return False, f"Dangerous pattern '{pat}' in arguments"
        return True, "OK"

# =============================================================================
# PATTERN 4: Structured Logging
# =============================================================================

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        entry = {
            "ts": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "msg": record.getMessage(),
        }
        if hasattr(record, "extra"):
            entry.update(record.extra)
        return json.dumps(entry)


def get_logger(name: str = "agent") -> logging.Logger:
    lgr = logging.getLogger(name)
    lgr.setLevel(logging.INFO)
    if not lgr.handlers:
        h = logging.StreamHandler()
        h.setFormatter(StructuredFormatter())
        lgr.addHandler(h)
    return lgr

# =============================================================================
# STEP 5: Demo — putting it all together
# =============================================================================

# Simple tools for the demo
@tool
def get_device_status(hostname: str) -> dict:
    """Check if a device is online and get its health status."""
    return {"hostname": hostname, "status": "online", "health": 95}

@tool
def get_cpu_utilization(hostname: str) -> dict:
    """Get current CPU usage percentage for a device."""
    return {"hostname": hostname, "cpu_percent": 45}

@tool
def reboot_device(hostname: str) -> str:
    """Reboot a network device. Use with caution!"""
    return f"Rebooting {hostname}..."

tools = [get_device_status, get_cpu_utilization, reboot_device]


if __name__ == "__main__":
    print("=" * 55)
    print("  Production Patterns Demo")
    print("=" * 55)

    # --- Pattern 1: Cost Tracking ---
    print("\n--- Pattern 1: Cost Tracking ---")
    tracker = CostTracker(max_cost=0.50)
    tracker.add_usage(prompt_tokens=800, completion_tokens=120)
    tracker.add_usage(prompt_tokens=650, completion_tokens=90)
    print(f"  {tracker.report()}")

    # --- Pattern 2: Retry ---
    print("\n--- Pattern 2: Retry with Backoff ---")
    result = call_with_retry(get_device_status.invoke, {"hostname": "R1-CORE"})
    print(f"  call_with_retry(get_device_status, 'R1-CORE') → {result}")

    # --- Pattern 3: Sandboxing ---
    print("\n--- Pattern 3: Tool Sandboxing ---")
    for level in ("read", "write", "admin"):
        sandbox = SandboxedToolExecutor(level=level)
        checks = [
            ("get_device_status", {"hostname": "R1"}),
            ("configure_vlan",    {"vlan_id": 100}),
            ("reboot_device",     {"hostname": "R1"}),
        ]
        results = []
        for name, args in checks:
            ok, _ = sandbox.can_execute(name, args)
            results.append(f"{'Y' if ok else 'N'}")
        print(f"  level={level:5s} → status={results[0]}  vlan={results[1]}  reboot={results[2]}")

    # --- Pattern 4: Structured Logging ---
    print("\n--- Pattern 4: Structured Logging ---")
    logger = get_logger("demo")
    logger.info("Device checked", extra={"extra": {"tool": "get_device_status", "device": "R1-CORE"}})

    # --- Full agent run with cost tracking ---
    print("\n--- Putting it together: Agent + Cost Tracking ---")
    llm = ChatOpenAI(
        model="gpt-5.2",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    agent = create_react_agent(llm, tools)

    query = "Is R1-CORE online?"
    print(f"  Query: \"{query}\"")
    result = agent.invoke({"messages": [("user", query)]})

    final = result["messages"][-1]
    print(f"  Agent: {final.content}")

    # Track usage from response metadata if available
    if hasattr(final, "usage_metadata") and final.usage_metadata:
        meta = final.usage_metadata
        tracker.add_usage(meta.get("input_tokens", 0), meta.get("output_tokens", 0))
    print(f"  {tracker.report()}")

    print(f"\n{'─' * 55}")
