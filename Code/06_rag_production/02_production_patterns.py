"""
=============================================================================
DEMO 02: Production Patterns
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 08 - RAG & Production Patterns

Essential patterns for running agents in production:
- Error handling with retries
- Cost tracking
- Sandboxing/permissions
- Logging
=============================================================================
"""

import os
import time
from functools import wraps
from typing import TypedDict, Annotated, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from tenacity import retry, stop_after_attempt, wait_exponential

# =============================================================================
# PATTERN 1: Cost Tracking
# =============================================================================

print("=" * 60)
print("DEMO: Production Patterns")
print("=" * 60)

print("\n" + "-" * 60)
print("📊 PATTERN 1: Cost Tracking")
print("-" * 60)

class CostTracker:
    """Track API costs across multiple calls."""
    
    def __init__(self, max_cost: float = 1.0):
        self.max_cost = max_cost
        self.total_tokens = 0
        self.total_cost = 0.0
        self.calls = 0
    
    def add_usage(self, prompt_tokens: int, completion_tokens: int):
        """Add usage from an API call."""
        self.calls += 1
        self.total_tokens += prompt_tokens + completion_tokens
        
        # Approximate cost (GPT-4 pricing)
        input_cost = prompt_tokens * 0.00001  # $0.01 per 1K
        output_cost = completion_tokens * 0.00003  # $0.03 per 1K
        self.total_cost += input_cost + output_cost
        
        if self.total_cost > self.max_cost:
            raise CostLimitExceeded(
                f"Cost ${self.total_cost:.4f} exceeds limit ${self.max_cost}"
            )
    
    def report(self):
        """Print usage report."""
        print(f"\n📊 Cost Report:")
        print(f"   API Calls: {self.calls}")
        print(f"   Total Tokens: {self.total_tokens:,}")
        print(f"   Estimated Cost: ${self.total_cost:.4f}")

class CostLimitExceeded(Exception):
    pass

# Example usage
tracker = CostTracker(max_cost=0.50)  # $0.50 limit

print("""
class CostTracker:
    def __init__(self, max_cost=1.0):
        self.max_cost = max_cost
        self.total_cost = 0.0
    
    def add_usage(self, prompt_tokens, completion_tokens):
        # Calculate cost
        # Raise CostLimitExceeded if over budget
        pass
""")

# =============================================================================
# PATTERN 2: Retry with Backoff
# =============================================================================

print("\n" + "-" * 60)
print("🔄 PATTERN 2: Retry with Exponential Backoff")
print("-" * 60)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def call_with_retry(func, *args, **kwargs):
    """
    Call a function with automatic retry on failure.
    
    Uses exponential backoff:
    - Attempt 1: immediate
    - Attempt 2: wait 2 seconds
    - Attempt 3: wait 4 seconds
    - Give up after 3 attempts
    """
    return func(*args, **kwargs)

print("""
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),           # Max 3 attempts
    wait=wait_exponential(min=2, max=10)  # Exponential backoff
)
def call_with_retry(func, *args, **kwargs):
    return func(*args, **kwargs)
    
# Automatically retries on:
# - API rate limits
# - Temporary network issues
# - Server errors (500s)
""")

# =============================================================================
# PATTERN 3: Tool Sandboxing
# =============================================================================

print("\n" + "-" * 60)
print("🔒 PATTERN 3: Tool Sandboxing")
print("-" * 60)

class SandboxedToolExecutor:
    """Execute tools with permission checks."""
    
    # Define permission levels
    ALLOWED_TOOLS = {
        "read": ["get_device_status", "get_cpu_utilization", "list_devices"],
        "write": ["configure_vlan", "backup_config"],
        "admin": ["reboot_device", "restore_config"]
    }
    
    DANGEROUS_PATTERNS = ["DELETE", "DROP", "shutdown", "reload", "format"]
    
    def __init__(self, permission_level: str = "read"):
        self.permission_level = permission_level
    
    def can_execute(self, tool_name: str, args: dict) -> tuple[bool, str]:
        """Check if tool execution is allowed."""
        
        # Check tool allowlist based on permission level
        allowed = set()
        if self.permission_level in ["read", "write", "admin"]:
            allowed.update(self.ALLOWED_TOOLS["read"])
        if self.permission_level in ["write", "admin"]:
            allowed.update(self.ALLOWED_TOOLS["write"])
        if self.permission_level == "admin":
            allowed.update(self.ALLOWED_TOOLS["admin"])
        
        if tool_name not in allowed:
            return False, f"Tool '{tool_name}' not allowed for permission level '{self.permission_level}'"
        
        # Check for dangerous patterns in arguments
        args_str = str(args).upper()
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in args_str:
                return False, f"Dangerous pattern '{pattern}' detected in arguments"
        
        return True, "OK"

sandbox = SandboxedToolExecutor(permission_level="read")

# Test permissions
tests = [
    ("get_device_status", {"hostname": "R1"}),
    ("reboot_device", {"hostname": "R1"}),
    ("configure_vlan", {"vlan_id": 100}),
]

print("\n   Permission Level: 'read'")
print("\n   Testing tool permissions:")
for tool_name, args in tests:
    allowed, reason = sandbox.can_execute(tool_name, args)
    status = "✅" if allowed else "❌"
    print(f"      {status} {tool_name}: {reason}")

# =============================================================================
# PATTERN 4: Structured Logging
# =============================================================================

print("\n" + "-" * 60)
print("📝 PATTERN 4: Structured Logging")
print("-" * 60)

import logging
import json
from datetime import datetime

# Configure structured logging
class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module
        }
        # Add extra fields if present
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        return json.dumps(log_data)

# Setup logger
logger = logging.getLogger("agent")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(StructuredFormatter())
# Uncomment to enable: logger.addHandler(handler)

print("""
import logging
import json

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "tool": getattr(record, 'tool', None),
            "duration_ms": getattr(record, 'duration_ms', None)
        })

# Usage in agent:
logger.info("Tool executed", extra={
    "tool": "get_device_status",
    "duration_ms": 245,
    "success": True
})
""")

# =============================================================================
# PATTERN 5: Complete Production Agent
# =============================================================================

print("\n" + "-" * 60)
print("🏭 PATTERN 5: Production-Ready Agent")
print("-" * 60)

print("""
Combining all patterns:

class ProductionAgent:
    def __init__(self, 
                 model: str = "gpt-5.2",
                 max_cost: float = 1.0,
                 permission_level: str = "read",
                 max_retries: int = 3):
        
        self.llm = ChatOpenAI(model=model)
        self.cost_tracker = CostTracker(max_cost)
        self.sandbox = SandboxedToolExecutor(permission_level)
        self.max_retries = max_retries
        self.logger = setup_logger()
    
    def invoke(self, query: str):
        try:
            # 1. Log the query
            self.logger.info(f"Query received: {query}")
            
            # 2. Run with retry
            result = self._invoke_with_retry(query)
            
            # 3. Track cost
            self.cost_tracker.add_usage(...)
            
            # 4. Log success
            self.logger.info("Query completed", extra={
                "tokens": self.cost_tracker.total_tokens,
                "cost": self.cost_tracker.total_cost
            })
            
            return result
            
        except CostLimitExceeded as e:
            self.logger.error(f"Cost limit exceeded: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Agent error: {e}")
            raise
""")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 60)
print("💡 Production Checklist")
print("=" * 60)

print("""
Before deploying your agent:

☐ Cost Tracking
  - Set budget limits
  - Track token usage
  - Alert on overspend

☐ Error Handling
  - Retry with backoff
  - Graceful degradation
  - Human escalation

☐ Security
  - Tool allowlists
  - Input validation
  - Dangerous pattern detection

☐ Observability
  - Structured logging
  - LangSmith tracing
  - Metrics collection

☐ Testing
  - Unit tests for tools
  - Integration tests
  - Regression testing
""")

print("✅ Demo complete!")
