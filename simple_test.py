#!/usr/bin/env python3
"""
Simple test to verify YouTube cookies are working
"""
import os
import sys
import asyncio

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the functions from whatsapp_bot
from whatsapp_bot import (
    detect_platform,
    YOUTUBE_COOKIES_FILE
)

def simple_test():
    """Simple test function"""
    print("🚀 Simple YouTube Test")
    print("=" * 30)
    
    # Test URL
    test_url = "https://www.youtube.com/shorts/4H-ckF9H_y0"
    
    print(f"Testing URL: {test_url}")
    
    # Detect platform
    platform = detect_platform(test_url)
    print(f"Platform detected: {platform}")
    
    # Check YouTube cookies
    print(f"YouTube cookies file: {YOUTUBE_COOKIES_FILE}")
    print(f"File exists: {os.path.exists(YOUTUBE_COOKIES_FILE)}")
    
    if os.path.exists(YOUTUBE_COOKIES_FILE):
        size = os.path.getsize(YOUTUBE_COOKIES_FILE)
        print(f"File size: {size} bytes")
    
    print("\n✅ Simple test completed!")

if __name__ == "__main__":
    simple_test()
