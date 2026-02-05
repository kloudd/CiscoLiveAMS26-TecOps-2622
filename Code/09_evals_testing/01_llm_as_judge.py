"""
=============================================================================
DEMO 01: LLM-as-Judge Evaluation
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 09 - LLM Evals & Testing

Use an LLM to evaluate the quality of agent responses.
This is essential when outputs are subjective or complex!
=============================================================================
"""

import os
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List

# =============================================================================
# STEP 1: The Challenge of Testing LLM Outputs
# =============================================================================

print("=" * 60)
print("DEMO: LLM-as-Judge Evaluation")
print("=" * 60)

print("""
🤔 The Challenge:

How do you test this?

  Query: "Is R1 online?"
  
  Response A: "Router R1 is currently online with 45 days uptime."
  Response B: "Yes, R1 is up."
  Response C: "R1 shows a green status indicator."
  
  All three are CORRECT! But how do we automate testing?

💡 Solution: Use an LLM to judge response quality!
""")

# =============================================================================
# STEP 2: Define Evaluation Schema
# =============================================================================

class EvaluationResult(BaseModel):
    """Schema for LLM judge evaluation."""
    
    accuracy_score: int = Field(
        ge=1, le=5,
        description="How accurate is the information? (1-5)"
    )
    completeness_score: int = Field(
        ge=1, le=5,
        description="Does it fully answer the question? (1-5)"
    )
    clarity_score: int = Field(
        ge=1, le=5,
        description="Is it clear and easy to understand? (1-5)"
    )
    reasoning: str = Field(
        description="Brief explanation of the scores"
    )
    passed: bool = Field(
        description="Overall pass/fail (True if average >= 3)"
    )

print("\n📋 Evaluation Schema:")
print("   - accuracy_score: 1-5")
print("   - completeness_score: 1-5")
print("   - clarity_score: 1-5")
print("   - reasoning: explanation")
print("   - passed: True/False")

# =============================================================================
# STEP 3: Create the Judge
# =============================================================================

# Use a capable model as the judge
judge_llm = ChatOpenAI(
    model="gpt-5.2",
    temperature=0,  # Consistent judgments
    api_key=os.getenv("OPENAI_API_KEY")
)

# Bind to structured output
judge = judge_llm.with_structured_output(EvaluationResult)

def evaluate_response(
    query: str,
    response: str,
    expected_behavior: str
) -> EvaluationResult:
    """
    Use LLM to evaluate an agent's response.
    
    Args:
        query: The user's original question
        response: The agent's response to evaluate
        expected_behavior: Description of what a good response should include
    
    Returns:
        EvaluationResult with scores and reasoning
    """
    
    evaluation_prompt = f"""You are evaluating an AI agent's response.

QUERY: {query}

AGENT RESPONSE: {response}

EXPECTED BEHAVIOR: {expected_behavior}

Evaluate the response on:
1. Accuracy (1-5): Is the information correct?
2. Completeness (1-5): Does it fully answer the question?
3. Clarity (1-5): Is it clear and easy to understand?

A response passes if the average score is >= 3.

Provide your evaluation."""

    return judge.invoke(evaluation_prompt)

# =============================================================================
# STEP 4: Test Cases
# =============================================================================

print("\n" + "=" * 60)
print("🧪 Running Evaluations")
print("=" * 60)

test_cases = [
    {
        "name": "Good Response",
        "query": "Is router R1 online?",
        "response": "Router R1 is currently online. It has been up for 45 days with a health score of 95%. No issues detected.",
        "expected": "Should confirm online/offline status, may include additional health info"
    },
    {
        "name": "Minimal Response",
        "query": "Is router R1 online?",
        "response": "Yes.",
        "expected": "Should confirm online/offline status, may include additional health info"
    },
    {
        "name": "Wrong Information",
        "query": "Is router R1 online?",
        "response": "R1 is a switch, not a router. Please clarify your question.",
        "expected": "Should confirm online/offline status, may include additional health info"
    },
    {
        "name": "Verbose but Complete",
        "query": "What VLANs are on SW-01?",
        "response": "SW-01 has VLANs 10 (Users), 20 (Voice), 30 (Management), and 100 (Guest). VLAN 10 has the most traffic with 450 Mbps average throughput.",
        "expected": "Should list VLANs configured on the switch"
    }
]

results = []

for test in test_cases:
    print(f"\n📋 Test: {test['name']}")
    print(f"   Query: {test['query']}")
    print(f"   Response: {test['response'][:60]}...")
    
    result = evaluate_response(
        test["query"],
        test["response"],
        test["expected"]
    )
    
    avg_score = (result.accuracy_score + result.completeness_score + result.clarity_score) / 3
    
    print(f"\n   Scores:")
    print(f"      Accuracy: {result.accuracy_score}/5")
    print(f"      Completeness: {result.completeness_score}/5")
    print(f"      Clarity: {result.clarity_score}/5")
    print(f"      Average: {avg_score:.1f}")
    print(f"      Passed: {'✅' if result.passed else '❌'}")
    print(f"   Reasoning: {result.reasoning}")
    
    results.append({
        "name": test["name"],
        "passed": result.passed,
        "avg_score": avg_score
    })

# =============================================================================
# STEP 5: Summary
# =============================================================================

print("\n" + "=" * 60)
print("📊 Test Summary")
print("=" * 60)

passed = sum(1 for r in results if r["passed"])
total = len(results)

print(f"\n   Passed: {passed}/{total}")
print("\n   Details:")
for r in results:
    status = "✅ PASS" if r["passed"] else "❌ FAIL"
    print(f"      {status} - {r['name']} (avg: {r['avg_score']:.1f})")

# =============================================================================
# STEP 6: Integration with Test Framework
# =============================================================================

print("\n" + "=" * 60)
print("💡 Integration with pytest")
print("=" * 60)

print("""
# tests/test_agent_responses.py

import pytest
from eval_utils import evaluate_response

@pytest.mark.parametrize("query,response,expected", [
    (
        "Is R1 online?",
        get_agent_response("Is R1 online?"),
        "Should confirm online/offline status"
    ),
    # ... more test cases
])
def test_agent_response_quality(query, response, expected):
    result = evaluate_response(query, response, expected)
    
    assert result.accuracy_score >= 3, f"Accuracy too low: {result.reasoning}"
    assert result.completeness_score >= 3, f"Incomplete: {result.reasoning}"
    assert result.passed, f"Failed evaluation: {result.reasoning}"

# Run with: pytest tests/test_agent_responses.py
""")

print("✅ Demo complete!")
