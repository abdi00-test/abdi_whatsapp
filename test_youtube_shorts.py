#!/usr/bin/env python3
"""
Test YouTube Shorts URL handling
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from whatsapp_bot import detect_platform

def test_youtube_shorts():
    """Test YouTube Shorts URL handling"""
    print("Testing YouTube Shorts URL handling")
    print("=" * 40)
    
    # Test the problematic URL
    url = "https://youtube.com/shorts/4H-ckF9H_y0?si=Wa2MGFJJw6Ut9-Wn"
    platform = detect_platform(url)
    print(f"URL: {url}")
    print(f"Detected Platform: {platform}")
    
    # Test a normalized version
    normalized_url = "https://www.youtube.com/shorts/4H-ckF9H_y0"
    platform2 = detect_platform(normalized_url)
    print(f"\nNormalized URL: {normalized_url}")
    print(f"Detected Platform: {platform2}")
    
    # Test YouTube standard URL
    standard_url = "https://www.youtube.com/watch?v=4H-ckF9H_y0"
    platform3 = detect_platform(standard_url)
    print(f"\nStandard URL: {standard_url}")
    print(f"Detected Platform: {platform3}")

if __name__ == "__main__":
    test_youtube_shorts()