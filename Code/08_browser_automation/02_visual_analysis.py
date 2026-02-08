#!/usr/bin/env python3
"""
=============================================================================
DEMO 04: Visual Analysis - Analyze Grafana Dashboard with GPT-4o
=============================================================================
TECOPS-2622 | Cisco Live 2026 | Amsterdam

Simple demo: Load a dashboard screenshot and send it to GPT-4o for analysis.

Usage:
    python 04_visual_analysis.py
    python 04_visual_analysis.py --image frontend-observability-grafana-dashboard.png
=============================================================================
"""

import os
import argparse
import base64
import warnings
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

load_dotenv()
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Default image
DEFAULT_IMAGE = "frontend-observability-grafana-dashboard.png"

# =============================================================================
# Analyze Screenshot with GPT-4o
# =============================================================================

def analyze_screenshot(image_base64: str) -> str:
    """Send screenshot to GPT-4o and get analysis."""
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    message = HumanMessage(content=[
        {"type": "text", "text": """Analyze this Grafana Frontend Observability dashboard and report:

1. CORE WEB VITALS - What are the current values for:
   - TTFB (Time to First Byte)
   - FCP (First Contentful Paint)
   - CLS (Cumulative Layout Shift)
   - LCP (Largest Contentful Paint)
   - FID (First Input Delay)

2. Are any metrics in CRITICAL state (red) or WARNING state (yellow)?

3. PAGE LOADS & ERRORS:
   - What does the "Page loads over time" chart show?
   - How many JavaScript errors are shown?
   - Any error spikes visible?

4. PERFORMANCE TRENDS:
   - Page Load p75 trend
   - Cumulative Layout Shift p75 trend
   - First Input Delay p75 trend

5. OVERALL ASSESSMENT:
   - Is this application healthy or degraded?
   - What needs immediate attention?

Be specific with numbers you can read from the dashboard."""},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
    ])
    
    response = llm.invoke([message])
    return response.content

# =============================================================================
# Main
# =============================================================================

def main(image_path: str = None):
    print("=" * 60)
    print("DEMO: Visual Analysis with GPT-4o")
    print("=" * 60)
    
    # Use default image if none provided
    if not image_path:
        image_path = DEFAULT_IMAGE
    
    print(f"\n📷 Loading image: {image_path}")
    
    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode()
    
    # Analyze
    print("\n🔍 Sending to GPT-4o for analysis...\n")
    print("-" * 40)
    
    analysis = analyze_screenshot(image_base64)
    print(analysis)
    
    print("-" * 40)
    print("\n✅ Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default=DEFAULT_IMAGE, help="Path to screenshot file")
    args = parser.parse_args()
    main(args.image)
