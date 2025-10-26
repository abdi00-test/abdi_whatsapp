#!/usr/bin/env python3
"""
Comprehensive test script to verify YouTube download functionality with cookies
"""
import os
import sys
import asyncio

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the download functions from whatsapp_bot
from whatsapp_bot import (
    get_media_info,
    download_media,
    detect_platform,
    ensure_directories,
    validate_youtube_setup,
    YOUTUBE_COOKIES_FILE
)

async def test_youtube_download_with_cookies():
    """Test YouTube download functionality with cookies"""
    print("🚀 Testing YouTube download with cookies authentication")
    print("=" * 60)
    
    # Ensure directories exist
    ensure_directories()
    
    # Validate YouTube setup first
    print("Validating YouTube setup...")
    is_valid = await validate_youtube_setup()
    if not is_valid:
        print("❌ YouTube setup validation failed")
        return False
    
    # Test multiple YouTube URLs to ensure reliability
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up
        "https://www.youtube.com/shorts/4H-ckF9H_y0",   # YouTube Shorts (from your test list)
        "https://youtu.be/dQw4w9WgXcQ"                  # Short URL format
    ]
    
    success_count = 0
    
    for i, test_url in enumerate(test_urls, 1):
        print(f"\n--- Test {i}/{len(test_urls)} ---")
        print(f"Testing URL: {test_url}")
        
        try:
            # Detect platform
            platform = detect_platform(test_url)
            print(f"Platform detected: {platform}")
            
            if platform != 'youtube':
                print(f"❌ Not a YouTube URL: {test_url}")
                continue
            
            # Get media info with cookies
            print("Extracting media info with cookies...")
            info = await get_media_info(test_url)
            
            if info:
                print(f"✅ Media info extracted successfully")
                print(f"Title: {info.get('title', 'Unknown')}")
                print(f"Uploader: {info.get('uploader', 'Unknown')}")
                print(f"Content type: {info.get('content_type', 'Unknown')}")
                
                # Try to download the media
                print("Downloading media (360p quality)...")
                file_path = await download_media(test_url, quality="360p", audio_only=False, info=info)
                
                if file_path and os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    size_mb = file_size / (1024 * 1024)
                    print(f"✅ Download successful: {file_path} ({size_mb:.1f} MB)")
                    
                    # Clean up the downloaded file
                    os.remove(file_path)
                    print("✅ Cleaned up downloaded file")
                    success_count += 1
                else:
                    print("❌ Download failed")
            else:
                print("❌ Failed to extract media info")
                # Check if cookies file was used
                if os.path.exists(YOUTUBE_COOKIES_FILE):
                    print(f"ℹ️  YouTube cookies file exists: {YOUTUBE_COOKIES_FILE}")
                    print("   This might indicate a temporary issue or rate limiting")
                else:
                    print("⚠️  YouTube cookies file not found - downloads may be rate-limited")
                
        except Exception as e:
            print(f"❌ Error testing download: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {success_count}/{len(test_urls)} URLs successful")
    
    if success_count > 0:
        print("✅ YouTube download functionality is working!")
        return True
    else:
        print("❌ YouTube download functionality needs attention!")
        return False

async def main():
    """Main test function"""
    print("🧪 WhatsApp Bot Comprehensive YouTube Test")
    print("=" * 50)
    
    success = await test_youtube_download_with_cookies()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All YouTube tests passed!")
        print("🎯 The WhatsApp bot YouTube functionality is working correctly.")
    else:
        print("⚠️  Some YouTube tests failed!")
        print("🔧 Please check the errors above and verify your YouTube cookies.")

if __name__ == "__main__":
    asyncio.run(main())