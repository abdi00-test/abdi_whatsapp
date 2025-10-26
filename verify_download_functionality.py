#!/usr/bin/env python3
"""
Verification script for WhatsApp bot download functionality
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

from whatsapp_bot import (
    download_media, 
    get_media_info,
    detect_platform,
    process_spotify_url
)

async def test_download_functionality():
    """Test the core download functionality"""
    print("🧪 Testing Core Download Functionality")
    print("=" * 50)
    
    # Test platform detection
    test_urls = [
        "https://www.instagram.com/reel/DGDfJ3LzdEL/?igsh=MWtlc21yZWpyMzRocw==",
        "https://www.instagram.com/p/DK_2g5CzKwQ/?igsh=MTgyOXJqbmNicHl5dg==",
        "https://vt.tiktok.com/ZSUKPdCtm/",
        "https://open.spotify.com/track/2YUgUYAXNCrhF7t9Bk9qQH?si=cc631fd35bb441e4"
    ]
    
    for url in test_urls:
        platform = detect_platform(url)
        print(f"URL: {url}")
        print(f"Detected Platform: {platform}")
        print()
    
    # Test Spotify processing
    print("Testing Spotify URL processing...")
    spotify_url = "https://open.spotify.com/track/2YUgUYAXNCrhF7t9Bk9qQH?si=cc631fd35bb441e4"
    try:
        spotify_info = await process_spotify_url(spotify_url)
        if spotify_info:
            print(f"✅ Spotify processing successful:")
            print(f"   Search Query: {spotify_info['search_query']}")
            print(f"   Full Title: {spotify_info['full_title']}")
        else:
            print("❌ Spotify processing failed")
    except Exception as e:
        print(f"❌ Spotify processing error: {e}")
    print()
    
    # Test media info extraction (this tests the download mechanism without actually downloading)
    print("Testing media info extraction...")
    instagram_url = "https://www.instagram.com/reel/DGDfJ3LzdEL/?igsh=MWtlc21yZWpyMzRocw=="
    try:
        print("Extracting Instagram media info...")
        info = await get_media_info(instagram_url)
        if info:
            print(f"✅ Media info extraction successful:")
            print(f"   Title: {info['title']}")
            print(f"   Platform: {info['platform']}")
            print(f"   Content Type: {info['content_type']}")
        else:
            print("❌ Media info extraction returned None")
    except Exception as e:
        print(f"❌ Media info extraction error: {e}")
    
    print()
    print("=" * 50)
    print("✅ Core functionality test completed!")

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_download_functionality())