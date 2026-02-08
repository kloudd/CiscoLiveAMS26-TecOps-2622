#!/usr/bin/env python3
"""
=============================================================================
DEMO 03: Browser Navigation - Open, Navigate, Screenshot
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam

Simple demo: Open Chrome, navigate to URL, take screenshot.

Usage:
    python 03_browser_navigate.py
    python 03_browser_navigate.py --url "https://developer.cisco.com"
=============================================================================
"""

import os
import argparse
import warnings
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

# Load environment variables
load_dotenv()

# =============================================================================
# Browser Tools
# =============================================================================

_browser = None

def get_browser():
    global _browser
    if _browser is None:
        options = Options()
        options.add_argument("--window-size=1920,1080")
        service = Service(ChromeDriverManager().install())
        _browser = webdriver.Chrome(service=service, options=options)
    return _browser

@tool
def open_browser() -> str:
    """Open Chrome browser."""
    get_browser()
    return "Browser opened successfully."

@tool
def navigate(url: str) -> str:
    """Navigate to a URL."""
    browser = get_browser()
    browser.get(url)
    return f"Navigated to {url}. Page title: {browser.title}"

@tool
def screenshot(filename: str = "screenshot.png") -> str:
    """Take a screenshot and save it."""
    browser = get_browser()
    browser.save_screenshot(filename)
    return f"Screenshot saved to {filename}"

# =============================================================================
# Main
# =============================================================================

def main(url: str):
    print("=" * 60)
    print("DEMO: Browser Navigation")
    print("=" * 60)
    
    tools = [open_browser, navigate, screenshot]
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    agent = create_react_agent(llm, tools)
    
    prompt = f"""
    1. Open the browser
    2. Navigate to {url}
    3. Take a screenshot
    4. Describe what you did
    """
    
    print(f"\n📤 Task: Navigate to {url} and take screenshot\n")
    
    result = agent.invoke({"messages": [("user", prompt)]})
    print(f"📥 Result: {result['messages'][-1].content}")
    
    # Cleanup
    if _browser:
        _browser.quit()
    
    print("\n✅ Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://www.cisco.com")
    args = parser.parse_args()
    main(args.url)
