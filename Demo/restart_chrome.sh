#!/bin/bash

echo "🔄 Restarting Chrome with debugging port..."
echo ""

# Kill all Chrome processes
echo "1️⃣  Stopping all Chrome processes..."
killall "Google Chrome" 2>/dev/null
sleep 2

# Verify Chrome is stopped
if pgrep "Google Chrome" > /dev/null; then
    echo "   ⚠️  Chrome still running, force killing..."
    killall -9 "Google Chrome" 2>/dev/null
    sleep 2
fi

echo "   ✅ Chrome stopped"
echo ""

# Start Chrome with debugging port (requires separate profile)
echo "2️⃣  Starting Chrome with debug port 9222..."
# Note: Remote debugging requires a non-default profile directory
mkdir -p "$HOME/chrome-debug-profile"
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
    --remote-debugging-port=9222 \
    --user-data-dir="$HOME/chrome-debug-profile" \
    > /dev/null 2>&1 &

sleep 3

# Test if port is open
echo ""
echo "3️⃣  Testing connection..."
if curl -s http://localhost:9222/json/version > /dev/null 2>&1; then
    echo "   ✅ Chrome debug port is responding!"
    echo ""
    echo "🎉 Success! Now run: python test_simple.py"
    echo ""
    echo "📝 Note: Sessions are saved in ~/chrome-debug-profile"
    echo "   Your logins will persist between restarts."
else
    echo "   ❌ Port 9222 not responding yet"
    echo ""
    echo "   💡 Try:"
    echo "      1. Wait a few more seconds for Chrome to fully start"
    echo "      2. Then run: python test_simple.py"
fi
