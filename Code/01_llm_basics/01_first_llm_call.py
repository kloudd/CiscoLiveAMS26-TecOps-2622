"""
=============================================================================
DEMO 01: Your First LLM Call
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 01 - LLM & GenAI Foundations

This demo shows how to make your first call to an LLM using LangChain.
=============================================================================
"""

import os
from langchain_openai import ChatOpenAI

# =============================================================================
# STEP 1: Initialize the LLM
# =============================================================================
# We create a ChatOpenAI instance pointing to GPT-5.2
# - model: The model name (gpt-5.2 is OpenAI's latest)
# - temperature: Controls randomness (0 = deterministic, 1 = creative)

llm = ChatOpenAI(
    model="gpt-5.2",
    temperature=0,  # Use 0 for consistent, repeatable outputs
    api_key=os.getenv("OPENAI_API_KEY")  # Reads from environment variable
)

# =============================================================================
# STEP 2: Make a Simple Call
# =============================================================================
# The invoke() method sends a prompt to the LLM and returns a response

print("=" * 60)
print("DEMO: Your First LLM Call")
print("=" * 60)

# Simple question
response = llm.invoke("What is OSPF in one sentence?")

# The response is an AIMessage object
print("\n📤 Question: What is OSPF in one sentence?")
print(f"\n📥 Response: {response.content}")

# =============================================================================
# STEP 3: Inspect the Response Object
# =============================================================================
# The response contains useful metadata

print("\n" + "-" * 60)
print("Response Metadata:")
print("-" * 60)
print(f"  Type: {type(response).__name__}")
print(f"  Model: {response.response_metadata.get('model_name', 'N/A')}")

# Token usage (cost tracking!)
usage = response.response_metadata.get('token_usage', {})
print(f"  Prompt Tokens: {usage.get('prompt_tokens', 'N/A')}")
print(f"  Completion Tokens: {usage.get('completion_tokens', 'N/A')}")
print(f"  Total Tokens: {usage.get('total_tokens', 'N/A')}")

print("\n✅ Demo complete!")
