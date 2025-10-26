#!/usr/bin/env python3
"""
Test script to verify YouTube cookies loading and validation
"""
import os
import sys
import asyncio

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the YouTube validation function from whatsapp_bot
from whatsapp_bot import (
    YOUTUBE_COOKIES_FILE,
    validate_youtube_setup
)

async def test_youtube_cookies():
    """Test YouTube cookies loading and validation"""
    print("🚀 Testing YouTube cookies functionality")
    print("=" * 50)
    
    # Check if YouTube cookies file exists
    print(f"YouTube cookies file path: {YOUTUBE_COOKIES_FILE}")
    print(f"File exists: {os.path.exists(YOUTUBE_COOKIES_FILE)}")
    
    if os.path.exists(YOUTUBE_COOKIES_FILE):
        file_size = os.path.getsize(YOUTUBE_COOKIES_FILE)
        print(f"File size: {file_size} bytes")
        
        # Read first few lines to check format
        try:
            with open(YOUTUBE_COOKIES_FILE, 'r') as f:
                lines = f.readlines()
                print(f"Number of lines: {len(lines)}")
                
                # Show first 3 lines (but don't print actual cookie content)
                print("First 3 lines (headers/content):")
                for i, line in enumerate(lines[:3]):
                    if line.strip():
                        print(f"  Line {i+1}: {line[:50]}{'...' if len(line) > 50 else ''}")
        except Exception as e:
            print(f"Error reading file: {e}")
    
    print("\n" + "-" * 30)
    print("Validating YouTube setup...")
    
    # Test the validation function
    try:
        result = await validate_youtube_setup()
        if result:
            print("✅ YouTube cookies validation: SUCCESS")
        else:
            print("⚠️ YouTube cookies validation: FAILED or WARNING")
    except Exception as e:
        print(f"❌ Error during validation: {e}")

async def main():
    """Main test function"""
    print("🧪 WhatsApp Bot YouTube Cookies Test")
    print("=" * 40)
    
    await test_youtube_cookies()
    
    print("\n" + "=" * 40)
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(main())