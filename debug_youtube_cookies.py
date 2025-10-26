#!/usr/bin/env python3
"""
Debug script to check YouTube cookies loading and application
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import configuration
from whatsapp_bot import YOUTUBE_COOKIES_FILE

def debug_youtube_cookies():
    """Debug YouTube cookies file"""
    print("🔍 Debugging YouTube cookies")
    print("=" * 40)
    
    # Check if file exists
    print(f"File path: {YOUTUBE_COOKIES_FILE}")
    print(f"File exists: {os.path.exists(YOUTUBE_COOKIES_FILE)}")
    
    if os.path.exists(YOUTUBE_COOKIES_FILE):
        file_size = os.path.getsize(YOUTUBE_COOKIES_FILE)
        print(f"File size: {file_size} bytes")
        
        # Read and analyze the file
        try:
            with open(YOUTUBE_COOKIES_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            print(f"Total lines: {len(lines)}")
            
            # Check for Netscape format header
            if lines and lines[0].startswith("# Netscape HTTP Cookie File"):
                print("✅ File format: Netscape HTTP Cookie File (correct)")
            else:
                print("⚠️  File format: Unknown or missing header")
            
            # Look for YouTube cookies
            youtube_cookies = []
            for i, line in enumerate(lines):
                if '.youtube.com' in line or 'youtube.com' in line:
                    youtube_cookies.append((i+1, line.strip()))
            
            print(f"YouTube cookies found: {len(youtube_cookies)}")
            
            # Show first few YouTube cookies
            if youtube_cookies:
                print("First YouTube cookies:")
                for line_num, cookie_line in youtube_cookies[:3]:
                    # Don't print the actual cookie values
                    parts = cookie_line.split('\t')
                    if len(parts) >= 6:
                        domain = parts[0]
                        name = parts[5]
                        print(f"  Line {line_num}: {domain} -> {name}")
                    else:
                        print(f"  Line {line_num}: {cookie_line[:50]}...")
            else:
                print("⚠️  No YouTube cookies found in file")
                
                # Show first few lines of file for debugging
                print("First 5 lines of file:")
                for i, line in enumerate(lines[:5], 1):
                    print(f"  {i}: {line.strip()}")
                
        except Exception as e:
            print(f"❌ Error reading file: {e}")
    else:
        print("❌ YouTube cookies file not found!")

if __name__ == "__main__":
    debug_youtube_cookies()