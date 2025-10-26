#!/usr/bin/env python3
"""
Test script for WhatsApp bot functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from whatsapp_bot import process_message

def test_whatsapp_bot():
    """Test the WhatsApp bot with sample inputs"""
    print("🧪 Testing WhatsApp Bot Implementation")
    print("=" * 50)
    
    # Test help command
    print("\n1. Testing help command:")
    process_message("test_user_1", "help")
    
    # Test Instagram reel URL (from the logs)
    print("\n2. Testing Instagram reel URL:")
    instagram_url = "https://www.instagram.com/reel/DOL69CdDPbm/?igsh=a2IxcHUwd3gwcG11"
    process_message("test_user_2", instagram_url)
    
    # Test regular Instagram post
    print("\n3. Testing Instagram post URL:")
    instagram_post_url = "https://www.instagram.com/p/C7djuNouD1H/"
    process_message("test_user_3", instagram_post_url)
    
    # Test YouTube URL
    print("\n4. Testing YouTube URL:")
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    process_message("test_user_4", youtube_url)
    
    # Test Spotify URL
    print("\n5. Testing Spotify URL:")
    spotify_url = "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQ3"
    process_message("test_user_5", spotify_url)
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print("Note: This is a simulation. Actual WhatsApp API calls require a valid token and phone number ID.")

if __name__ == "__main__":
    test_whatsapp_bot()