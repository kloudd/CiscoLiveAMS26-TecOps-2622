"""
=============================================================================
Section 01: LLM & GenAI Foundations - All Exercises
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam

This file contains all the exercises for Section 01:
  - Tokenization & Embeddings
  - Your First LLM Call
  - System Messages
  - Structured Output
=============================================================================
"""

# # ---------------------------------------------------------------------
# # EXERCISE 00: Tokenization & Embeddings
# # ---------------------------------------------------------------------
# # Learn how LLMs break text into tokens and represent them as vectors

# from transformers import AutoTokenizer

# # Load a tokenizer (e.g., BERT)
# tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')

# # Tokenize a sentence
# text = "Hello, how are you?"
# tokens = tokenizer.tokenize(text)
# print(tokens)
# # Output: ['hello', ',', 'how', 'are', 'you', '?']

# # ---------------------------------------------------------------------
# # Encoding text

# input_ids = tokenizer.encode(text)
# print(input_ids)

# # ---------------------------------------------------------------------

# # Decoding text
# decoded_text = tokenizer.decode(input_ids)
# print(decoded_text)

# # =====================================================================
# # Embeddings
# # pip install transformers torch scipy

# from transformers import AutoTokenizer, AutoModel
# import torch
# import numpy as np
# from scipy.spatial.distance import cosine

# # Load the pre-trained embedding model and tokenizer
# model_name = "sentence-transformers/all-MiniLM-L6-v2"
# # Showcase huggingface.co models.
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModel.from_pretrained(model_name)


# def get_embedding(text):
#     # Tokenize and convert text to input tensor
#     inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
#     with torch.no_grad():
#         outputs = model(**inputs)
    
#     # Mean pooling of the embeddings
#     embeddings = outputs.last_hidden_state.mean(dim=1)
#     return embeddings


# sentence1 = "I like programming"
# sentence2 = "I like programming"
# embedding1 = get_embedding(sentence1)
# embedding2 = get_embedding(sentence2)
# print(embedding1, embedding2)

# # ---------------------------------------------------------------------

# # Function to calculate cosine similarity
# def cosine_similarity(embedding1, embedding2):
#     embedding1_np = embedding1.numpy().flatten()
#     embedding2_np = embedding2.numpy().flatten()
#     return 1 - cosine(embedding1_np, embedding2_np)

# # Calculate similarity
# similarity = cosine_similarity(embedding1, embedding2)
# print(f"Cosine Similarity between the two sentences: {similarity:.4f}")

# # =====================================================================


# # ---------------------------------------------------------------------
# # EXERCISE 01: Your First LLM Call
# # ---------------------------------------------------------------------
# # Make your first call to an LLM using LangChain

# import os
# from langchain_openai import ChatOpenAI

# # STEP 1: Initialize the LLM
# # We create a ChatOpenAI instance pointing to GPT-5.2
# # - model: The model name (gpt-5.2 is OpenAI's latest)
# # - temperature: Controls randomness (0 = deterministic, 1 = creative)

# llm = ChatOpenAI(
#     model="gpt-5.2",
#     temperature=0,  # Use 0 for consistent, repeatable outputs
#     api_key=os.getenv("OPENAI_API_KEY")  # Reads from environment variable
# )

# # STEP 2: Make a Simple Call
# # The invoke() method sends a prompt to the LLM and returns a response

# print("=" * 60)
# print("DEMO: Your First LLM Call")
# print("=" * 60)

# # Simple question
# response = llm.invoke("What is OSPF in one sentence?")

# # The response is an AIMessage object
# print("\n📤 Question: What is OSPF in one sentence?")
# print(f"\n📥 Response: {response.content}")

# # # ---------------------------------------------------------------------


# # STEP 3: Inspect the Response Object
# # The response contains useful metadata

# print("\n" + "-" * 60)
# print("Response Metadata:")
# print("-" * 60)
# print(f"  Type: {type(response).__name__}")
# print(f"  Model: {response.response_metadata.get('model_name', 'N/A')}")

# # Token usage (cost tracking!)
# usage = response.response_metadata.get('token_usage', {})
# print(f"  Prompt Tokens: {usage.get('prompt_tokens', 'N/A')}")
# print(f"  Completion Tokens: {usage.get('completion_tokens', 'N/A')}")
# print(f"  Total Tokens: {usage.get('total_tokens', 'N/A')}")

# print("\n✅ Demo complete!")


# # =====================================================================

# # ---------------------------------------------------------------------
# # EXERCISE 02: System Messages
# # ---------------------------------------------------------------------
# # Use System, User, and Assistant messages to control LLM behavior
# import os
# from langchain_core.messages import SystemMessage, HumanMessage
# from langchain_openai import ChatOpenAI

# # STEP 1: Create Messages with Different Roles
# # - SystemMessage: Sets the AI's personality and rules
# # - HumanMessage: The user's input (you)
# # - AIMessage: The assistant's response (used for history

# llm = ChatOpenAI(
#     model="gpt-5.2",
#     temperature=0,  # Use 0 for consistent, repeatable outputs
#     api_key=os.getenv("OPENAI_API_KEY")  # Reads from environment variable
# )


# messages = [
#     # System message: Tell the AI who it is and how to behave
#     SystemMessage(content="""You are a Cisco network expert.
    
# When answering questions, always:
# 1. Give a brief explanation (1-2 sentences)
# 2. Provide a configuration example if applicable
# 3. Mention one common gotcha or mistake to avoid

# Keep responses concise and practical."""),
    
#     # Human message: The user's question
#     HumanMessage(content="Explain VLAN trunking")
# ]

# # STEP 2: Invoke with Messages

# print("=" * 60)
# print("DEMO: System Messages")
# print("=" * 60)

# print("\n🔧 System Prompt:")
# print("   'You are a Cisco network expert...'")

# print("\n📤 User Question: Explain VLAN trunking")
# print("\n" + "-" * 60)

# response = llm.invoke(messages)

# print("📥 Response:")
# print(response.content)

# # STEP 3: Compare Without System Message

# print("\n" + "=" * 60)
# print("COMPARISON: Same question WITHOUT system message")
# print("=" * 60)

# # Without system message - just the question
# response_no_system = llm.invoke("Explain VLAN trunking")

# print("\n📥 Response (no system message):")
# print(response_no_system.content[:500] + "..." if len(response_no_system.content) > 500 else response_no_system.content)

# print("\n" + "-" * 60)
# print("💡 Notice: With a system message, the response is more")
# print("   structured and follows our specified format!")
# print("-" * 60)

# print("\n✅ Demo complete!")


# # =====================================================================

# # ---------------------------------------------------------------------
# # EXERCISE 03: Create LLM with Structured Output
# # ---------------------------------------------------------------------

# from langchain_openai import ChatOpenAI 
# from pydantic import BaseModel 
# class DeviceStatus(BaseModel): 
#     hostname: str 
#     status: str  # "online" or "offline"
#     uptime_hours: int 
# llm = ChatOpenAI(model="gpt-4o")
# structured_llm = llm.with_structured_output(DeviceStatus) 
# result = structured_llm.invoke("Router R1 has been up for 72 hours") 

# # DeviceStatus(hostname='R1', status='online', uptime_hours=72)
# print(result.model_dump_json())

# # =====================================================================
