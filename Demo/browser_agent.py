"""
Simple Browser Automation Agent for Cisco Live Demo
Uses existing Chrome browser + Gemini for decision-making
"""

import os
import base64
import time
from typing import Optional, Dict, Any
from playwright.sync_api import sync_playwright, Page, Browser
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BrowserAgent:
    """
    A simple browser automation agent that can:
    1. Navigate to URLs
    2. Take screenshots
    3. Analyze screenshots with Gemini vision
    4. Extract text from pages
    5. Make decisions about next steps
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """Initialize the browser agent with Gemini"""
        # Setup Gemini
        api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found. Set it in .env file or pass it directly.")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-3-flash-preview')
        
        # Browser will be initialized when needed
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # Track agent state
        self.findings = []
        self.current_step = 0
        self.max_steps = 30  # Prevent infinite loops (increased for complex investigations)
        
        # Default credentials for Catalyst Center (can be overridden)
        self.default_username = os.getenv("CATALYST_USERNAME", "admin")
        self.default_password = os.getenv("CATALYST_PASSWORD", "C1sc0!123")
    
    def connect_to_existing_browser(self) -> None:
        """
        Connect to an existing Chrome browser.
        
        Instructions to start Chrome with debugging:
        
        macOS:
        /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222
        
        Windows:
        chrome.exe --remote-debugging-port=9222
        
        Linux:
        google-chrome --remote-debugging-port=9222
        """
        print("🔌 Connecting to existing Chrome browser on port 9222...")
        print("   (Make sure Chrome is running with --remote-debugging-port=9222)")
        
        self.playwright = sync_playwright().start()
        
        try:
            # Connect to existing browser
            self.browser = self.playwright.chromium.connect_over_cdp("http://localhost:9222")
            
            # Get the first context (usually the default browser context)
            contexts = self.browser.contexts
            if contexts:
                context = contexts[0]
                # Get the first page or create a new one
                if context.pages:
                    self.page = context.pages[0]
                else:
                    self.page = context.new_page()
            else:
                print("⚠️  No browser context found. Opening new tab...")
                context = self.browser.contexts[0] if self.browser.contexts else None
                if context:
                    self.page = context.new_page()
                else:
                    raise Exception("Could not access browser context")
            
            print("✅ Connected successfully!")
            
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            print("\n💡 Quick Fix:")
            print("   1. Close Chrome completely")
            print("   2. Run: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
            print("   3. Try again")
            raise
    
    def check_and_handle_login(self) -> bool:
        """
        Check if we're on a login page and handle authentication if needed.
        Returns True if login was performed, False otherwise.
        """
        if not self.page:
            return False
        
        print("   🔐 Checking for login page...")
        
        # Common login form indicators
        login_indicators = [
            'input[type="password"]',
            'input[name="password"]',
            'input[id*="password"]',
            'input[placeholder*="assword"]',
            '#password',
            '[data-testid="password"]',
        ]
        
        username_selectors = [
            'input[type="text"]:near(input[type="password"])',
            'input[name="username"]',
            'input[name="user"]',
            'input[id*="username"]',
            'input[id*="user"]',
            'input[placeholder*="sername"]',
            'input[placeholder*="mail"]',
            '#username',
            '#user',
            '[data-testid="username"]',
        ]
        
        password_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            '#password',
            '[data-testid="password"]',
        ]
        
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Log in")',
            'button:has-text("Login")',
            'button:has-text("Sign in")',
            'button:has-text("Submit")',
            '[data-testid="login-button"]',
        ]
        
        # Check if there's a password field (indicates login page)
        password_field = None
        for selector in password_selectors:
            try:
                elem = self.page.locator(selector).first
                if elem.is_visible(timeout=1000):
                    password_field = elem
                    print("   🔑 Login page detected!")
                    break
            except:
                continue
        
        if not password_field:
            print("   ✅ No login required")
            return False
        
        # Find username field
        username_field = None
        for selector in username_selectors:
            try:
                elem = self.page.locator(selector).first
                if elem.is_visible(timeout=1000):
                    username_field = elem
                    break
            except:
                continue
        
        if not username_field:
            # Try to find any text input before the password field
            try:
                username_field = self.page.locator('input[type="text"]').first
            except:
                print("   ⚠️  Could not find username field")
                return False
        
        # Fill in credentials
        print(f"   👤 Entering username: {self.default_username}")
        try:
            username_field.fill(self.default_username)
        except Exception as e:
            print(f"   ⚠️  Failed to fill username: {e}")
            return False
        
        print("   🔒 Entering password: ********")
        try:
            password_field.fill(self.default_password)
        except Exception as e:
            print(f"   ⚠️  Failed to fill password: {e}")
            return False
        
        # Find and click submit button
        time.sleep(0.5)  # Brief pause before submit
        
        for selector in submit_selectors:
            try:
                submit_btn = self.page.locator(selector).first
                if submit_btn.is_visible(timeout=1000):
                    print("   🚀 Clicking login button...")
                    submit_btn.click()
                    print("   ⏳ Waiting for login to complete (5 seconds)...")
                    time.sleep(5)  # Wait for login to process
                    print("   ✅ Login submitted!")
                    return True
            except:
                continue
        
        # Try pressing Enter as fallback
        try:
            print("   🚀 Pressing Enter to submit...")
            password_field.press("Enter")
            print("   ⏳ Waiting for login to complete (5 seconds)...")
            time.sleep(5)
            print("   ✅ Login submitted!")
            return True
        except Exception as e:
            print(f"   ⚠️  Failed to submit login: {e}")
            return False
    
    def wait_for_content(self, max_wait: int = 60) -> bool:
        """
        Wait for the page to have meaningful content (not blank).
        Returns True if content loaded, False if timed out.
        """
        if not self.page:
            return False
        
        print(f"   👀 Checking for page content (max {max_wait}s wait)...")
        
        start_time = time.time()
        check_interval = 3  # Check every 3 seconds
        
        while (time.time() - start_time) < max_wait:
            try:
                # Get the page text content
                body_text = self.page.inner_text("body", timeout=2000)
                text_length = len(body_text.strip())
                
                # Check for loading indicators
                is_loading = False
                loading_indicators = ['loading', 'please wait', 'spinner', 'initializing']
                body_lower = body_text.lower()
                for indicator in loading_indicators:
                    if indicator in body_lower and text_length < 500:
                        is_loading = True
                        break
                
                # If we have substantial content and not showing loading, we're good
                if text_length > 40 and not is_loading:
                    elapsed = int(time.time() - start_time)
                    print(f"   ✅ Content loaded ({text_length} chars, {elapsed}s)")
                    return True
                
                # Check if there are visible interactive elements
                has_buttons = self.page.locator("button").count() > 0
                has_links = self.page.locator("a").count() > 2
                has_inputs = self.page.locator("input").count() > 0
                
                if has_buttons or has_links or has_inputs:
                    if text_length > 40:
                        elapsed = int(time.time() - start_time)
                        print(f"   ✅ Interactive content detected ({elapsed}s)")
                        return True
                
                # Still blank/loading, wait and retry
                elapsed = int(time.time() - start_time)
                print(f"   ⏳ Page still loading... ({elapsed}s, {text_length} chars)")
                time.sleep(check_interval)
                
            except Exception as e:
                # Page might be in transition, wait and retry
                time.sleep(check_interval)
        
        print(f"   ⚠️  Timeout waiting for content after {max_wait}s")
        return False
    
    def navigate(self, url: str) -> str:
        """Navigate to a URL"""
        if not self.page:
            raise Exception("Browser not connected. Call connect_to_existing_browser() first.")
        
        print(f"\n🌐 Navigating to: {url}")
        try:
            # Try domcontentloaded first (faster, sufficient for most pages)
            print("   ⏳ Loading page (15s timeout)...")
            self.page.goto(url, wait_until="domcontentloaded", timeout=15000)
            print("   ✅ DOM loaded")
        except Exception as e:
            # Fallback to just load event
            print(f"   ⚠️  Timeout, using basic load (20s timeout)...")
            try:
                self.page.goto(url, wait_until="load", timeout=20000)
                print("   ✅ Page loaded (basic)")
            except Exception as e2:
                print(f"   ⚠️  Page still loading, continuing anyway...")
        
        # Wait for actual content to appear (handles blank screens)
        self.wait_for_content(max_wait=60)
        
        # Check if we landed on a login page and handle it
        if self.check_and_handle_login():
            print("   ⏳ Waiting for post-login page to load...")
            # After login, wait for content again
            self.wait_for_content(max_wait=60)
            # Check again in case there's a second login step or redirect
            self.check_and_handle_login()
        
        print("   ✅ Navigation complete")
        return f"Successfully navigated to {url}"
    
    def screenshot(self, description: str = "current page") -> str:
        """Take a screenshot and return the path"""
        if not self.page:
            raise Exception("Browser not connected.")
        
        # Create screenshots directory if it doesn't exist
        import os
        os.makedirs("screenshots", exist_ok=True)
        
        timestamp = int(time.time())
        filename = f"screenshots/screenshot_{timestamp}.png"
        
        print(f"📸 Taking screenshot: {description}")
        self.page.screenshot(path=filename, full_page=False)
        
        return filename
    
    def analyze_screenshot(self, screenshot_path: str, question: str) -> str:
        """
        Use Gemini Vision to analyze a screenshot and answer a question
        """
        print(f"\n🤔 Analyzing: {question}")
        
        # Read and encode image
        with open(screenshot_path, "rb") as img_file:
            image_data = img_file.read()
        
        # Create prompt for Gemini
        prompt = f"""
You are analyzing a screenshot of a web dashboard.

Question: {question}

Provide a clear, concise answer based on what you see in the image.
If you see specific metrics, numbers, or status indicators, mention them.
If you cannot determine the answer from the image, say so clearly.
"""
        
        # Use Gemini to analyze
        response = self.model.generate_content([prompt, {"mime_type": "image/png", "data": image_data}])
        
        answer = response.text
        print(f"💡 Analysis: {answer[:200]}...")
        
        return answer
    
    def extract_text(self) -> str:
        """Extract visible text from the current page"""
        if not self.page:
            raise Exception("Browser not connected.")
        
        print("📄 Extracting text from page...")
        text = self.page.inner_text("body")
        return text[:1000]  # Return first 1000 chars to avoid overload
    
    def click_element(self, description: str) -> str:
        """
        Click an element on the page based on a text description
        Uses vision to find and click the element
        Handles blue text links, spans, and other clickable elements
        """
        if not self.page:
            raise Exception("Browser not connected.")
        
        print(f"\n🖱️  Looking for element to click: {description}")
        
        # Take a screenshot first to locate the element
        screenshot_path = self.screenshot(f"before_click_{description[:30]}")
        
        # Ask Gemini to identify what to click
        prompt = f"""
Look at this screenshot and identify the element: "{description}"

Provide the TEXT that I should search for to click on this element.
For example, if you see a button with "Submit" text, return: Submit
If you see a link with "data_centre_sfo", return: data_centre_sfo
If you see blue/colored clickable text, return the exact text shown.

Return ONLY the exact text to click on, nothing else. Keep it short and precise.
"""
        
        with open(screenshot_path, "rb") as img_file:
            image_data = img_file.read()
        
        response = self.model.generate_content([prompt, {"mime_type": "image/png", "data": image_data}])
        click_text = response.text.strip().strip('"').strip("'")
        
        print(f"   🎯 Identified text to click: {click_text}")
        
        # Fast timeout for all attempts
        timeout = 5000  # 5 seconds
        
        # Try multiple strategies to find and click the element
        strategies = [
            ("link", lambda: self.page.get_by_role("link", name=click_text).first.click(timeout=timeout)),
            ("button", lambda: self.page.get_by_role("button", name=click_text).first.click(timeout=timeout)),
            ("exact text", lambda: self.page.get_by_text(click_text, exact=True).first.click(timeout=timeout)),
            ("partial text", lambda: self.page.get_by_text(click_text).first.click(timeout=timeout)),
            ("locator text", lambda: self.page.locator(f"text={click_text}").first.click(timeout=timeout)),
            ("clickable span", lambda: self.page.locator(f"span:has-text('{click_text}')").first.click(timeout=timeout)),
            ("clickable div", lambda: self.page.locator(f"div:has-text('{click_text}')").first.click(timeout=timeout)),
            ("any element", lambda: self.page.locator(f"*:has-text('{click_text}')").first.click(timeout=timeout)),
            ("css selector a", lambda: self.page.locator(f"a:has-text('{click_text}')").first.click(timeout=timeout)),
        ]
        
        for strategy_name, strategy_fn in strategies:
            try:
                print(f"   ⏳ Trying {strategy_name}...")
                strategy_fn()
                print(f"   ✅ Clicked via {strategy_name}: {click_text}")
                time.sleep(2)  # Brief wait for page response
                return f"Successfully clicked on '{click_text}'"
            except Exception:
                continue
        
        # Last resort: try clicking at coordinates using vision
        print("   ⏳ Trying coordinate-based click...")
        try:
            coord_prompt = f"""
Look at this screenshot. Find the element with text "{click_text}" or related to "{description}".
Give me the approximate X,Y pixel coordinates of the CENTER of that element.
The screenshot is approximately 1280x800 pixels.
Return ONLY in format: X,Y (e.g., 640,400)
"""
            response = self.model.generate_content([coord_prompt, {"mime_type": "image/png", "data": image_data}])
            coords = response.text.strip()
            if ',' in coords:
                x, y = map(int, coords.replace(' ', '').split(',')[:2])
                self.page.mouse.click(x, y)
                print(f"   ✅ Clicked at coordinates ({x}, {y})")
                time.sleep(2)
                return f"Successfully clicked at coordinates ({x}, {y}) for '{click_text}'"
        except Exception as e:
            pass
        
        error_msg = f"Failed to click '{click_text}' - element not found or not clickable"
        print(f"   ❌ {error_msg}")
        return error_msg
    
    def decide_next_step(self, goal: str, current_context: str) -> Dict[str, Any]:
        """
        Use Gemini to decide what to do next based on the goal and current findings
        """
        print(f"\n🧠 Thinking about next step...")
        
        # Build context from findings
        findings_text = "\n".join([f"- {f}" for f in self.findings]) if self.findings else "None yet"
        
        prompt = f"""
You are a browser automation agent. Your goal is:
{goal}

Current findings so far:
{findings_text}

Current context/analysis:
{current_context}

Based on the above, what should be the NEXT STEP?

AVAILABLE ACTIONS:
- navigate: Go to a specific URL (use ONLY for initial navigation or returning to dashboard list)
- screenshot_and_analyze: Take a screenshot and analyze it
- click: Click on an element like a link or button (PREFERRED for opening dashboards)
- done: Goal is complete

IMPORTANT RULES:
- Use CLICK to open dashboards, NOT navigate
- After analyzing a dashboard, use navigate to go back to https://sumitkanwal.grafana.net/dashboards
- Don't repeat the same action multiple times

Respond in this EXACT format:
ACTION: <navigate|screenshot_and_analyze|click|done>
URL: <url if navigating, otherwise N/A>
QUESTION: <question to ask about screenshot, or N/A>
CLICK_TARGET: <description of element to click, or N/A>
REASONING: <brief explanation>

Examples:
- Open a dashboard: ACTION: click, URL: N/A, QUESTION: N/A, CLICK_TARGET: time_successarte, REASONING: Need to open the time_successarte dashboard
- Go back to list: ACTION: navigate, URL: https://sumitkanwal.grafana.net/dashboards, QUESTION: N/A, CLICK_TARGET: N/A, REASONING: Returning to dashboard list
- Analyze page: ACTION: screenshot_and_analyze, URL: N/A, QUESTION: Are there any alerts?, CLICK_TARGET: N/A, REASONING: Need to check for alerts
- Complete: ACTION: done, URL: N/A, QUESTION: N/A, CLICK_TARGET: N/A, REASONING: All checks complete
"""
        
        response = self.model.generate_content(prompt)
        decision_text = response.text
        
        # Parse the response
        decision = self._parse_decision(decision_text)
        
        print(f"   Action: {decision['action']}")
        print(f"   Reasoning: {decision['reasoning']}")
        
        return decision
    
    def _parse_decision(self, text: str) -> Dict[str, Any]:
        """Parse Gemini's decision response"""
        decision = {
            "action": "done",
            "url": None,
            "question": None,
            "click_target": None,
            "reasoning": "Could not parse decision"
        }
        
        lines = text.strip().split("\n")
        for line in lines:
            if line.startswith("ACTION:"):
                decision["action"] = line.replace("ACTION:", "").strip().lower()
            elif line.startswith("URL:"):
                url = line.replace("URL:", "").strip()
                decision["url"] = url if url != "N/A" else None
            elif line.startswith("QUESTION:"):
                q = line.replace("QUESTION:", "").strip()
                decision["question"] = q if q != "N/A" else None
            elif line.startswith("CLICK_TARGET:"):
                ct = line.replace("CLICK_TARGET:", "").strip()
                decision["click_target"] = ct if ct != "N/A" else None
            elif line.startswith("REASONING:"):
                decision["reasoning"] = line.replace("REASONING:", "").strip()
        
        return decision
    
    def run(self, goal: str) -> str:
        """
        Main agent loop: Given a goal, iteratively work towards it
        """
        print("="*60)
        print(f"🎯 GOAL: {goal}")
        print("="*60)
        
        if not self.page:
            self.connect_to_existing_browser()
        
        current_context = "Just started. No information yet."
        
        while self.current_step < self.max_steps:
            self.current_step += 1
            print(f"\n{'='*60}")
            print(f"STEP {self.current_step}/{self.max_steps}")
            print(f"{'='*60}")
            
            # Decide next action
            decision = self.decide_next_step(goal, current_context)
            
            action = decision["action"]
            
            if action == "done":
                print("\n✅ GOAL COMPLETE!")
                break
            
            elif action == "navigate":
                if decision["url"]:
                    self.navigate(decision["url"])
                    current_context = f"Navigated to {decision['url']}"
                else:
                    print("⚠️  No URL provided for navigation")
                    current_context = "Navigation failed - no URL"
            
            elif action == "screenshot_and_analyze":
                screenshot_path = self.screenshot(f"step_{self.current_step}")
                
                question = decision["question"] or "What do you see on this page?"
                analysis = self.analyze_screenshot(screenshot_path, question)
                
                self.findings.append(f"Step {self.current_step}: {analysis}")
                current_context = analysis
            
            elif action == "click":
                if decision["click_target"]:
                    result = self.click_element(decision["click_target"])
                    current_context = result
                else:
                    print("⚠️  No click target provided")
                    current_context = "Click failed - no target specified"
            
            else:
                print(f"⚠️  Unknown action: {action}")
                current_context = f"Unknown action: {action}"
        
        # Generate final report
        print("\n" + "="*60)
        print("📊 FINAL REPORT")
        print("="*60)
        
        report = "\n".join([f"{i+1}. {finding}" for i, finding in enumerate(self.findings)])
        print(report)
        
        return report
    
    def close(self):
        """Clean up resources"""
        if self.playwright:
            self.playwright.stop()
            print("\n🔌 Disconnected from browser")


# Simple test function
if __name__ == "__main__":
    # Example usage
    agent = BrowserAgent()
    
    try:
        # Simple test: Navigate to Google and take a screenshot
        agent.connect_to_existing_browser()
        agent.navigate("https://www.google.com")
        
        screenshot = agent.screenshot("Google homepage")
        result = agent.analyze_screenshot(screenshot, "What search engine is this?")
        
        print(f"\n✅ Test Result: {result}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        agent.close()
