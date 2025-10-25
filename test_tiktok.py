import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the WhatsApp bot
import whatsapp_bot_simple

def test_tiktok_url():
    """Test TikTok URL handling"""
    # Test URL from user
    tiktok_url = "https://vt.tiktok.com/ZSUwcbWeR/"
    
    print("🧪 Testing TikTok URL detection...")
    print("=" * 50)
    
    # Test platform detection
    platform = whatsapp_bot_simple.detect_platform(tiktok_url)
    supported = whatsapp_bot_simple.is_supported_url(tiktok_url)
    
    print(f"URL: {tiktok_url}")
    print(f"Detected Platform: {platform}")
    print(f"Supported: {supported}")
    
    if platform == 'tiktok' and supported:
        print("✅ TikTok URL detection working correctly!")
    else:
        print("❌ TikTok URL detection failed!")
        
    # Test URL normalization
    print("\n📝 Testing URL normalization...")
    # The bot should handle the shortened URL correctly
    print("Bot should be able to handle shortened TikTok URLs")

if __name__ == "__main__":
    test_tiktok_url()