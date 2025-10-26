#!/usr/bin/env python3
"""
Quick test to verify WhatsApp bot functionality
"""
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from whatsapp_bot import detect_platform, process_spotify_url

async def quick_test():
    """Quick test of core functionality"""
    print("🚀 Quick Functionality Test")
    print("=" * 30)
    
    # Test URLs
    test_cases = [
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
            "name": "Spotify",
            "url": "https://open.spotify.com/track/2YUgUYAXNCrhF7t9Bk9qQH?si=cc631fd35bb441e4"
        }
    ]
    
    print("1. Platform Detection:")
    for test_case in test_cases:
        platform = detect_platform(test_case['url'])
        print(f"   {test_case['name']}: {platform}")
    
    print("\n2. Spotify Processing:")
    spotify_info = await process_spotify_url(test_cases[3]['url'])
    if spotify_info:
        print(f"   ✅ Success")
        print(f"   Search Query: {spotify_info['search_query']}")
        print(f"   Title: {spotify_info['full_title']}")
    else:
        print("   ❌ Failed")
    
    print("\n" + "=" * 30)
    print("✅ Quick test completed!")

if __name__ == "__main__":
    asyncio.run(quick_test())