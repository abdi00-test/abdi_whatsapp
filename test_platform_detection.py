import re

def detect_platform(url: str) -> str:
    """Detect platform from URL"""
    url_lower = url.lower()
    
    if 'instagram.com/reel/' in url_lower:
        return 'instagram_reel'
    elif 'instagram.com/p/' in url_lower:
        return 'instagram_post'
    elif 'instagram.com' in url_lower:
        return 'instagram'
    elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    elif 'tiktok.com' in url_lower:
        return 'tiktok'
    elif 'facebook.com' in url_lower:
        return 'facebook'
    elif 'spotify.com' in url_lower:
        return 'spotify'
    elif 'twitter.com' in url_lower or 'x.com' in url_lower:
        return 'twitter'
    
    return 'unknown'

def test_urls():
    """Test URL detection for different Instagram URL types"""
    
    # Test URLs
    test_cases = [
        ("https://www.instagram.com/reel/DMK7pjHIXfO/", "instagram_reel"),
        ("https://www.instagram.com/p/DJeuZqsz5JT/", "instagram_post"),
        ("https://www.instagram.com/p/DK_2g5CzKwQ/?img_index=1", "instagram_post"),
        ("https://www.instagram.com/user/", "instagram"),
    ]
    
    print("Testing URL detection:")
    for url, expected in test_cases:
        result = detect_platform(url)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} {url} -> {result}")

if __name__ == "__main__":
    test_urls()