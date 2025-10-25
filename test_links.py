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

def test_user_links():
    """Test the links provided by the user"""
    test_links = [
        "https://open.spotify.com/track/77VO5dSsGbTPxa2QF2KeIF?si=5e70fd0e53dc4335",
        "https://youtube.com/shorts/kp3DV4apBaY?si=80xR_gw4Nr0_OQTv",
        "https://vt.tiktok.com/ZSUwcbWeR/",
        "https://www.facebook.com/share/r/1FVwyvW8Yk/?mibextid=wwXIfr"
    ]
    
    print("🧪 Testing user-provided links...")
    print("=" * 60)
    
    all_passed = True
    for url in test_links:
        platform = detect_platform(url)
        supported = is_supported_url(url)
        status = "✅" if supported else "❌"
        if not supported:
            all_passed = False
        print(f"{status} {url}")
        print(f"   Detected Platform: {platform}, Supported: {supported}")
        print()
    
    if all_passed:
        print("🎉 All user links are supported!")
        print("The WhatsApp bot should now be able to handle these links correctly.")
    else:
        print("❌ Some links are not supported!")
        print("Please check the platform detection logic.")

if __name__ == "__main__":
    test_user_links()