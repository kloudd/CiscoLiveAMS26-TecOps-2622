"""
=============================================================================
DEMO 02: Adding System Messages
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 01 - LLM & GenAI Foundations

This demo shows how to use System, User, and Assistant messages
to control the LLM's behavior and personality.
=============================================================================
"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# =============================================================================
# STEP 1: Initialize the LLM
# =============================================================================

llm = ChatOpenAI(
    model="gpt-5.2",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# =============================================================================
# STEP 2: Create Messages with Different Roles
# =============================================================================
# - SystemMessage: Sets the AI's personality and rules
# - HumanMessage: The user's input (you)
# - AIMessage: The assistant's response (used for history)

messages = [
    # System message: Tell the AI who it is and how to behave
    SystemMessage(content="""You are a Cisco network expert.
    
When answering questions, always:
1. Give a brief explanation (1-2 sentences)
2. Provide a configuration example if applicable
3. Mention one common gotcha or mistake to avoid

Keep responses concise and practical."""),
    
    # Human message: The user's question
    HumanMessage(content="Explain VLAN trunking")
]

# =============================================================================
# STEP 3: Invoke with Messages
# =============================================================================

print("=" * 60)
print("DEMO: System Messages")
print("=" * 60)

print("\n🔧 System Prompt:")
print("   'You are a Cisco network expert...'")

print("\n📤 User Question: Explain VLAN trunking")
print("\n" + "-" * 60)

response = llm.invoke(messages)

print("📥 Response:")
print(response.content)

# =============================================================================
# STEP 4: Compare Without System Message
# =============================================================================

print("\n" + "=" * 60)
print("COMPARISON: Same question WITHOUT system message")
print("=" * 60)

# Without system message - just the question
response_no_system = llm.invoke("Explain VLAN trunking")

print("\n📥 Response (no system message):")
print(response_no_system.content[:500] + "..." if len(response_no_system.content) > 500 else response_no_system.content)

print("\n" + "-" * 60)
print("💡 Notice: With a system message, the response is more")
print("   structured and follows our specified format!")
print("-" * 60)

print("\n✅ Demo complete!")
