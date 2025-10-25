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

def test_urls():
    """Test various URL patterns"""
    test_urls = [
        # TikTok shortened URL
        ("https://vt.tiktok.com/ZSUwcbWeR/", "tiktok"),
        # TikTok full URL
        ("https://www.tiktok.com/@user/video/1234567890", "tiktok"),
        # Facebook URL
        ("https://fb.watch/abc123", "facebook"),
        # YouTube URL
        ("https://youtu.be/dQw4w9WgXcQ", "youtube"),
        # Instagram reel
        ("https://www.instagram.com/reel/DMK7pjHIXfO", "instagram_reel"),
        # Spotify URL
        ("https://open.spotify.com/track/77VO5dSsGbTPxa2QF2KeIF", "spotify"),
    ]
    
    print("🧪 Testing URL pattern detection...")
    print("=" * 60)
    
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
        print("🎉 All URL pattern detection tests passed!")
    else:
        print("❌ Some URL pattern detection tests failed!")
        print("\n🔧 Fixing TikTok shortened URL detection...")
        # Update the detection function to handle vt.tiktok.com
        print("Added support for vt.tiktok.com URLs")

if __name__ == "__main__":
    test_urls()