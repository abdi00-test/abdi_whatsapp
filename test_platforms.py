import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from whatsapp_bot_simple import detect_platform, is_supported_url

def test_platform_detection():
    """Test platform detection for various URLs"""
    test_urls = [
        # Instagram
        ("https://www.instagram.com/reel/DMK7pjHIXfO", "instagram_reel"),
        ("https://www.instagram.com/p/Cd345XYZ123", "instagram"),
        
        # YouTube
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "youtube"),
        ("https://youtu.be/dQw4w9WgXcQ", "youtube"),
        ("https://www.youtube.com/shorts/1234567890", "youtube"),
        
        # TikTok
        ("https://www.tiktok.com/@user/video/1234567890", "tiktok"),
        ("https://vm.tiktok.com/abc123", "tiktok"),
        
        # Facebook
        ("https://www.facebook.com/user/videos/1234567890", "facebook"),
        ("https://fb.watch/abc123", "facebook"),
        
        # Twitter/X
        ("https://twitter.com/user/status/1234567890", "twitter"),
        ("https://x.com/user/status/1234567890", "twitter"),
        
        # Spotify
        ("https://open.spotify.com/track/1234567890", "spotify"),
        ("https://spotify.com/album/1234567890", "spotify"),
    ]
    
    print("🧪 Testing platform detection...")
    print("=" * 50)
    
    for url, expected_platform in test_urls:
        detected = detect_platform(url)
        supported = is_supported_url(url)
        status = "✅" if detected == expected_platform else "❌"
        print(f"{status} {url}")
        print(f"   Expected: {expected_platform}, Detected: {detected}, Supported: {supported}")
        print()

if __name__ == "__main__":
    test_platform_detection()