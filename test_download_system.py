#!/usr/bin/env python3
"""
Test script for WhatsApp bot download system
"""
import sys
import os
import asyncio
import logging

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging to see detailed output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from whatsapp_bot import process_message

def test_download_system():
    """Test the WhatsApp bot download system with specific URLs"""
    print("🧪 Testing WhatsApp Bot Download System")
    print("=" * 50)
    
    # Test URLs provided by user
    test_cases = [
        {
            "name": "YouTube Shorts",
            "url": "https://youtube.com/shorts/4H-ckF9H_y0?si=Wa2MGFJJw6Ut9-Wn"
        },
        {
            "name": "Instagram Reel", 
            "url": "https://www.instagram.com/reel/DGDfJ3LzdEL/?igsh=MWtlc21yZWpyMzRocw=="
        },
        {
            "name": "Instagram Post",
            "url": "https://www.instagram.com/p/DK_2g5CzKwQ/?igsh=MTgyOXJqbmNicHl5dg=="
        },
        {
            "name": "TikTok",
            "url": "https://vt.tiktok.com/ZSUKPdCtm/"
        },
        {
            "name": "Spotify Track",
            "url": "https://open.spotify.com/track/2YUgUYAXNCrhF7t9Bk9qQH?si=cc631fd35bb441e4"
        }
    ]
    
    print(f"Testing {len(test_cases)} URLs...")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. Testing {test_case['name']}:")
        print(f"   URL: {test_case['url']}")
        
        try:
            # Process the message (this will simulate the download)
            process_message(f"test_user_{i}", test_case['url'])
            print(f"   ✅ Processing initiated successfully")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        print()
    
    print("=" * 50)
    print("✅ Test completed!")
    print("Note: This is a simulation. Actual WhatsApp API calls require valid credentials.")
    print("Check the logs above to see if the download process is working.")

if __name__ == "__main__":
    test_download_system()