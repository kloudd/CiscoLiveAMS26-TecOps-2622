# Demo 09: LLM Evals & Testing

## Overview
How to test and evaluate AI agents - essential for production deployments.

## Demos

| File | Description | Slide Reference |
|------|-------------|-----------------|
| `01_llm_as_judge.py` | Use LLM to evaluate responses | Slide: "LLM-as-Judge" |
| `02_regression_testing.py` | Track performance over time | Slide: "Regression Testing" |

## Running the Demos

```bash
# Set your API key
export OPENAI_API_KEY="sk-..."

# Run demos
python 01_llm_as_judge.py
python 02_regression_testing.py
```

## Key Concepts

### Why LLM Evals are Different

Traditional testing:
```python
assert response == "Router R1 is online"  # Too brittle!
```

LLM testing:
```python
# Multiple correct answers:
# - "Router R1 is online"
# - "Yes, R1 is up"
# - "R1 shows green status"
# All are correct!
```

### LLM-as-Judge Pattern

```python
class EvaluationResult(BaseModel):
    accuracy_score: int  # 1-5
    completeness_score: int  # 1-5
    clarity_score: int  # 1-5
    reasoning: str
    passed: bool

judge = llm.with_structured_output(EvaluationResult)
result = judge.invoke(f"Evaluate this response: {response}")
```

### Regression Testing

```python
# Define test cases
tests = [
    {"query": "Is R1 online?", "expected_tool": "get_status"},
    {"query": "CPU on R1?", "expected_tool": "get_cpu"},
]

# Run tests, compare to baseline
# Alert on regressions!
```

### Testing Checklist

- [ ] Unit tests for individual tools
- [ ] Integration tests for agent flows
- [ ] LLM-as-Judge for response quality
- [ ] Regression suite run on every change
- [ ] Baseline tracking for comparison
