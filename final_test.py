#!/usr/bin/env python3
"""
Final test script to verify all fixes are working
"""
import os
import sys
import asyncio

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the functions from whatsapp_bot
from whatsapp_bot import (
    validate_youtube_setup,
    get_media_info,
    detect_platform,
    ensure_directories
)

async def final_test():
    """Final comprehensive test"""
    print("🚀 Final Test - Verifying All Fixes")
    print("=" * 50)
    
    # Ensure directories exist
    ensure_directories()
    
    # Test 1: YouTube cookies validation
    print("Test 1: YouTube Cookies Validation")
    print("-" * 30)
    youtube_valid = await validate_youtube_setup()
    print(f"Result: {'✅ PASS' if youtube_valid else '⚠️  WARNING (but continuing)'}")
    
    # Test 2: Platform detection
    print("\nTest 2: Platform Detection")
    print("-" * 30)
    test_urls = [
        ("https://www.youtube.com/shorts/4H-ckF9H_y0", "youtube"),
        ("https://www.instagram.com/reel/DLP0StQz1Tq/", "instagram"),
        ("https://vt.tiktok.com/ZSUKPdCtm", "tiktok")
    ]
    
    detection_passed = True
    for url, expected_platform in test_urls:
        detected = detect_platform(url)
        status = "✅" if detected == expected_platform else "❌"
        print(f"{status} {url} -> {detected} (expected: {expected_platform})")
        if detected != expected_platform:
            detection_passed = False
    
    print(f"Result: {'✅ PASS' if detection_passed else '❌ FAIL'}")
    
    # Test 3: YouTube media info extraction
    print("\nTest 3: YouTube Media Info Extraction")
    print("-" * 30)
    youtube_url = "https://www.youtube.com/shorts/4H-ckF9H_y0"
    print(f"Testing URL: {youtube_url}")
    
    try:
        info = await get_media_info(youtube_url)
        if info:
            print(f"✅ PASS - Title: {info.get('title', 'Unknown')}")
            print(f"   Uploader: {info.get('uploader', 'Unknown')}")
            print(f"   Platform: {info.get('platform', 'Unknown')}")
            youtube_info_passed = True
        else:
            print("❌ FAIL - Could not extract media info")
            youtube_info_passed = False
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        youtube_info_passed = False
    
    # Summary
    print("\n" + "=" * 50)
    print("FINAL TEST RESULTS")
    print("=" * 50)
    print(f"1. YouTube Cookies: {'✅ PASS' if youtube_valid else '⚠️  WARNING'}")
    print(f"2. Platform Detection: {'✅ PASS' if detection_passed else '❌ FAIL'}")
    print(f"3. YouTube Info Extraction: {'✅ PASS' if youtube_info_passed else '❌ FAIL'}")
    
    overall_success = detection_passed and youtube_info_passed
    print("\n" + "=" * 50)
    if overall_success:
        print("🎉 ALL CRITICAL TESTS PASSED!")
        print("✅ WhatsApp bot is ready for deployment")
    else:
        print("❌ SOME TESTS FAILED!")
        print("⚠️  Please check the errors above")
    
    return overall_success

async def main():
    """Main test function"""
    print("🧪 WhatsApp Bot Final Verification Test")
    print("=" * 45)
    
    success = await final_test()
    
    print("\n" + "=" * 45)
    if success:
        print("✅ Final verification completed successfully!")
        print("🎯 All fixes have been implemented and tested.")
    else:
        print("❌ Final verification found issues!")
        print("🔧 Please review the test results above.")

if __name__ == "__main__":
    asyncio.run(main())