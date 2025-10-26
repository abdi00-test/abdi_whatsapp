import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from whatsapp_bot_simple import process_message

def test_instagram_urls():
    """Test different types of Instagram URLs"""
    
    # Test Instagram reel URL
    print("Testing Instagram Reel URL...")
    reel_url = "https://www.instagram.com/reel/DMK7pjHIXfO/"
    process_message("test_user", reel_url)
    
    # Test Instagram post URL
    print("\nTesting Instagram Post URL...")
    post_url = "https://www.instagram.com/p/DJeuZqsz5JT/"
    process_message("test_user", post_url)
    
    # Test Instagram carousel post URL
    print("\nTesting Instagram Carousel Post URL...")
    carousel_url = "https://www.instagram.com/p/DK_2g5CzKwQ/?img_index=1"
    process_message("test_user", carousel_url)
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    test_instagram_urls()