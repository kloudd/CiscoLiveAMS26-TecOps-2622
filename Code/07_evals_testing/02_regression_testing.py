"""
=============================================================================
DEMO 02: Regression Testing for Agents
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 09 - LLM Evals & Testing

Track agent performance over time and catch regressions early.
Essential when updating models, prompts, or tools!
=============================================================================
"""

import os
import json
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass, asdict
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

# =============================================================================
# STEP 1: Define Test Dataset
# =============================================================================

print("=" * 60)
print("DEMO: Regression Testing for Agents")
print("=" * 60)

@dataclass
class TestCase:
    """A single test case for regression testing."""
    id: str
    query: str
    expected_tool: str  # Which tool should be called
    expected_contains: List[str]  # What the response should contain
    category: str  # For grouping tests

# Create a test dataset
TEST_SUITE = [
    TestCase(
        id="device_status_01",
        query="Is R1 online?",
        expected_tool="get_device_status",
        expected_contains=["R1", "online"],
        category="status"
    ),
    TestCase(
        id="device_status_02",
        query="Check the health of SW-CORE-01",
        expected_tool="get_device_status",
        expected_contains=["SW-CORE-01", "health"],
        category="status"
    ),
    TestCase(
        id="cpu_01",
        query="What's the CPU usage on R1?",
        expected_tool="get_cpu_utilization",
        expected_contains=["CPU", "R1"],
        category="performance"
    ),
    TestCase(
        id="interface_01",
        query="Show traffic on interface Gi0/1",
        expected_tool="get_interface_stats",
        expected_contains=["Gi0/1"],
        category="interface"
    ),
    TestCase(
        id="list_01",
        query="List all routers",
        expected_tool="list_devices",
        expected_contains=["router"],
        category="inventory"
    ),
]

print(f"\n📋 Test Suite: {len(TEST_SUITE)} test cases")
for tc in TEST_SUITE:
    print(f"   - [{tc.category}] {tc.id}: {tc.query[:40]}...")

# =============================================================================
# STEP 2: Define Tools (Same as before)
# =============================================================================

@tool
def get_device_status(hostname: str) -> dict:
    """Get the online/offline status and health of a device."""
    return {"hostname": hostname, "status": "online", "health": 95}

@tool
def get_cpu_utilization(hostname: str) -> dict:
    """Get CPU usage percentage for a device."""
    return {"hostname": hostname, "cpu_percent": 45}

@tool
def get_interface_stats(hostname: str, interface: str) -> dict:
    """Get traffic statistics for an interface."""
    return {"interface": interface, "rx_mbps": 450, "tx_mbps": 230}

@tool
def list_devices(device_type: str = "all") -> list:
    """List devices, optionally filtered by type."""
    inventory = {"router": ["R1", "R2"], "switch": ["SW-01", "SW-02"]}
    if device_type == "all":
        return [d for devices in inventory.values() for d in devices]
    return inventory.get(device_type, [])

tools = [get_device_status, get_cpu_utilization, get_interface_stats, list_devices]

# =============================================================================
# STEP 3: Create Agent
# =============================================================================

llm = ChatOpenAI(
    model="gpt-5.2",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

agent = create_react_agent(llm, tools)

# =============================================================================
# STEP 4: Run Tests and Collect Results
# =============================================================================

@dataclass
class TestResult:
    """Result of running a single test."""
    test_id: str
    passed: bool
    tool_correct: bool
    contains_expected: bool
    response: str
    actual_tool: str
    error: str = None

def run_test(test_case: TestCase) -> TestResult:
    """Run a single test case and return the result."""
    try:
        # Invoke agent
        result = agent.invoke({"messages": [("user", test_case.query)]})
        messages = result["messages"]
        
        # Find which tool was called
        actual_tool = None
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                actual_tool = msg.tool_calls[0]["name"]
                break
        
        # Get final response
        response = messages[-1].content.lower()
        
        # Check if correct tool was used
        tool_correct = actual_tool == test_case.expected_tool
        
        # Check if response contains expected content
        contains_expected = all(
            keyword.lower() in response 
            for keyword in test_case.expected_contains
        )
        
        passed = tool_correct and contains_expected
        
        return TestResult(
            test_id=test_case.id,
            passed=passed,
            tool_correct=tool_correct,
            contains_expected=contains_expected,
            response=response[:100],
            actual_tool=actual_tool or "none"
        )
        
    except Exception as e:
        return TestResult(
            test_id=test_case.id,
            passed=False,
            tool_correct=False,
            contains_expected=False,
            response="",
            actual_tool="error",
            error=str(e)
        )

print("\n" + "=" * 60)
print("🧪 Running Regression Tests")
print("=" * 60)

results = []
for test_case in TEST_SUITE:
    print(f"\n   Running: {test_case.id}...")
    result = run_test(test_case)
    results.append(result)
    
    status = "✅ PASS" if result.passed else "❌ FAIL"
    print(f"   {status}")
    
    if not result.passed:
        print(f"      Tool expected: {test_case.expected_tool}, got: {result.actual_tool}")
        if result.error:
            print(f"      Error: {result.error}")

# =============================================================================
# STEP 5: Generate Report
# =============================================================================

print("\n" + "=" * 60)
print("📊 Regression Test Report")
print("=" * 60)

passed = sum(1 for r in results if r.passed)
total = len(results)
pass_rate = (passed / total) * 100

print(f"""
Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Model: gpt-5.2

Results: {passed}/{total} passed ({pass_rate:.1f}%)
""")

# Group by category
categories = {}
for tc, result in zip(TEST_SUITE, results):
    if tc.category not in categories:
        categories[tc.category] = {"passed": 0, "total": 0}
    categories[tc.category]["total"] += 1
    if result.passed:
        categories[tc.category]["passed"] += 1

print("By Category:")
for cat, stats in categories.items():
    rate = (stats["passed"] / stats["total"]) * 100
    print(f"   {cat}: {stats['passed']}/{stats['total']} ({rate:.0f}%)")

# =============================================================================
# STEP 6: Compare with Baseline
# =============================================================================

print("\n" + "-" * 60)
print("📈 Regression Detection")
print("-" * 60)

# Simulated baseline (in real code, load from file/database)
BASELINE = {
    "device_status_01": True,
    "device_status_02": True,
    "cpu_01": True,
    "interface_01": True,
    "list_01": True,
}

regressions = []
improvements = []

for result in results:
    baseline_passed = BASELINE.get(result.test_id, False)
    
    if baseline_passed and not result.passed:
        regressions.append(result.test_id)
    elif not baseline_passed and result.passed:
        improvements.append(result.test_id)

if regressions:
    print(f"\n⚠️  REGRESSIONS DETECTED: {len(regressions)}")
    for test_id in regressions:
        print(f"      - {test_id}")
else:
    print("\n✅ No regressions detected!")

if improvements:
    print(f"\n🎉 IMPROVEMENTS: {len(improvements)}")
    for test_id in improvements:
        print(f"      - {test_id}")

# =============================================================================
# STEP 7: Save Results for Future Comparison
# =============================================================================

print("\n" + "-" * 60)
print("💾 Saving Results")
print("-" * 60)

report = {
    "timestamp": datetime.now().isoformat(),
    "model": "gpt-5.2",
    "total_tests": total,
    "passed": passed,
    "pass_rate": pass_rate,
    "results": [asdict(r) for r in results]
}

print("""
# Save to file for tracking over time:

with open(f"reports/regression_{timestamp}.json", "w") as f:
    json.dump(report, f, indent=2)

# Compare with previous runs to detect regressions!
""")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 60)
print("💡 Best Practices")
print("=" * 60)

print("""
1. Create a comprehensive test suite
   - Cover all tools
   - Include edge cases
   - Group by category

2. Run tests on every change
   - Model updates
   - Prompt changes
   - Tool modifications

3. Track metrics over time
   - Pass rate
   - Tool selection accuracy
   - Response quality scores

4. Set up CI/CD integration
   - Run on pull requests
   - Block merges on regressions
   - Alert on failures

5. Maintain baselines
   - Save "known good" results
   - Compare new runs to baseline
   - Update baseline deliberately
""")

print("✅ Demo complete!")
