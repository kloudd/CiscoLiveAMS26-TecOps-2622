"""
=============================================================================
Section 03: LangChain Introduction - All Exercises
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam

This file contains all the exercises for Section 03:
  - Basic LangChain Chain (Prompt | LLM)
  - Chain with Output Parser (Prompt | LLM | OutputParser)
=============================================================================
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# ---------------------------------------------------------------------
# EXERCISE 01: Basic LangChain Chain
# ---------------------------------------------------------------------
# Chain a prompt template and an LLM together using the pipe operator

# Create components
llm = ChatOpenAI(model="gpt-4o")
prompt = ChatPromptTemplate.from_template("Tell me about {topic} in 1 line")

# Chain them together
chain = prompt | llm

# Run
result = chain.invoke({"topic": "network AI automation"})
print(result.content)


# # ---------------------------------------------------------------------
# # EXERCISE 02: Chain with Output Parser
# # ---------------------------------------------------------------------
# # Add an output parser to get a clean string instead of an AIMessage

# 1. Define the prompt
prompt = ChatPromptTemplate.from_template(
    "Explain {topic} in one sentence for a network engineer."
)

# 2. Create the LLM
llm = ChatOpenAI(model="gpt-4o")

# 3. Build the chain with StrOutputParser
chain = prompt | llm | StrOutputParser()

# 4. Run it
result = chain.invoke({"topic": "VXLAN"})
print(result)
# "VXLAN is a network virtualization technology that..."
