import re

def detect_platform(url: str) -> str:
    """Detect platform from URL"""
    url_lower = url.lower()
    
    if 'instagram.com/reel/' in url_lower:
        return 'instagram_reel'
    elif 'instagram.com' in url_lower:
        return 'instagram'
    elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    elif 'tiktok.com' in url_lower:
        return 'tiktok'
    elif 'facebook.com' in url_lower or 'fb.watch' in url_lower or 'fb.me' in url_lower:
        return 'facebook'
    elif 'spotify.com' in url_lower:
        return 'spotify'
    elif 'twitter.com' in url_lower or 'x.com' in url_lower:
        return 'twitter'
    
    return 'unknown'

def is_supported_url(url: str) -> bool:
    """Check if URL is from supported platform"""
    return detect_platform(url) != 'unknown'

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
    
    all_passed = True
    for url, expected_platform in test_urls:
        detected = detect_platform(url)
        supported = is_supported_url(url)
        status = "✅" if detected == expected_platform else "❌"
        if detected != expected_platform:
            all_passed = False
        print(f"{status} {url}")
        print(f"   Expected: {expected_platform}, Detected: {detected}, Supported: {supported}")
        print()
    
    if all_passed:
        print("🎉 All platform detection tests passed!")
    else:
        print("❌ Some platform detection tests failed!")

if __name__ == "__main__":
    test_platform_detection()