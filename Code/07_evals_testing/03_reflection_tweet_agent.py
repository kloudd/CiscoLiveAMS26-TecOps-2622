"""
=============================================================================
DEMO 03: Reflection Tweet Agent
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam
Section: 09 - LLM Evals & Testing

A tweet-writing agent that uses self-reflection to iteratively
improve generated tweets. Demonstrates the reflection pattern
using LangGraph with generate → reflect loops.
=============================================================================
"""

import os
from typing import List, Sequence

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import END, MessageGraph

load_dotenv()

# =============================================================================
# STEP 1: Define Prompts
# =============================================================================

reflection_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a viral Twitter influencer grading a tweet. "
            "Every time you review a tweet you MUST:\n"
            "1. Give an overall rating out of 5 (format: 'Rating: X/5')\n"
            "2. Explain WHY you gave that rating, covering:\n"
            "   - Virality potential\n"
            "   - Clarity & readability\n"
            "   - Engagement factor (hooks, CTAs, emotion)\n"
            "   - Length & conciseness\n"
            "   - Style & tone\n"
            "3. Provide specific, actionable recommendations to improve the tweet.\n\n"
            "Always start your response with the rating line, then the explanation, then recommendations.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ],
)

generation_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a Twitter techie influencer assistant whose job is to come up with great Twitter posts. "
            "Create the best possible Twitter post for the user's request. "
            "If the user gives feedback, return an improved version of your earlier attempts.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# =============================================================================
# STEP 2: Create LLM and Chains
# =============================================================================

llm = ChatOpenAI(
    model="gpt-5.2",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY"),
)

generate_chain = generation_prompt | llm
reflect_chain = reflection_prompt | llm

# =============================================================================
# STEP 3: Define Graph Nodes
# =============================================================================

REFLECT = "reflect"
GENERATE = "generate"


generation_count = 0

def generation_node(state: Sequence[BaseMessage]):
    """Generate or improve a tweet based on current state."""
    global generation_count
    generation_count += 1

    print(f"\n{'=' * 50}", flush=True)
    print(f"  GENERATION Round {generation_count}", flush=True)
    print(f"{'=' * 50}", flush=True)

    prompt_value = generation_prompt.format_prompt(messages=state)
    for chunk in llm.stream(prompt_value.to_messages()):
        if hasattr(chunk, "content"):
            print(chunk.content, end="", flush=True)

    print(f"\n{'=' * 50}\n", flush=True)

    return generate_chain.invoke({"messages": state})


reflection_count = 0

def reflection_node(messages: Sequence[BaseMessage]) -> List[BaseMessage]:
    """Reflect on and critique the generated tweet with a rating out of 5."""
    global reflection_count
    reflection_count += 1

    print(f"\n{'=' * 50}", flush=True)
    print(f"  CRITIQUE Round {reflection_count}", flush=True)
    print(f"{'=' * 50}", flush=True)

    prompt_value = reflection_prompt.format_prompt(messages=messages)
    for chunk in llm.stream(prompt_value.to_messages()):
        if hasattr(chunk, "content"):
            print(chunk.content, end="", flush=True)

    print(f"\n{'=' * 50}\n", flush=True)

    res = reflect_chain.invoke({"messages": messages})
    return [HumanMessage(content=res.content)]


# =============================================================================
# STEP 4: Build the Graph
# =============================================================================

builder = MessageGraph()
builder.add_node(GENERATE, generation_node)
builder.add_node(REFLECT, reflection_node)
builder.set_entry_point(GENERATE)


def should_continue(state: List[BaseMessage]):
    """Stop after 3 reflection cycles (6 messages)."""
    if len(state) > 6:
        return END
    return REFLECT


builder.add_conditional_edges(GENERATE, should_continue)
builder.add_edge(REFLECT, GENERATE)

graph = builder.compile()

print(graph.get_graph().draw_mermaid())
graph.get_graph().print_ascii()

# =============================================================================
# STEP 5: Run the Agent
# =============================================================================

if __name__ == "__main__":
    print("Hello LangGraph")
    inputs = HumanMessage(
        content="""Make this tweet better:
@CiscoLive was a awesome! It created a lot of buzz and we had a lot of fun around AI Agents
"""
    )
    response = graph.invoke(inputs)
    for msg in response:
        if hasattr(msg, "content"):
            print(msg.content)
