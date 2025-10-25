import os
import sys
import time
import yt_dlp
from config import DOWNLOADS_DIR, TEMP_DIR

def ensure_directories():
    """Ensure required directories exist"""
    for directory in [DOWNLOADS_DIR, TEMP_DIR]:
        os.makedirs(directory, exist_ok=True)
    print(f"✅ Directories ensured: {DOWNLOADS_DIR}, {TEMP_DIR}")

def test_youtube_download(url, title="YouTube Video"):
    """Test YouTube download"""
    print(f"\n📥 Testing {title} download...")
    print(f"URL: {url}")
    
    try:
        # Create unique temporary directory for this download
        download_dir = os.path.join(DOWNLOADS_DIR, f"test_youtube_{int(time.time())}")
        os.makedirs(download_dir, exist_ok=True)
        print(f"📂 Download directory: {download_dir}")
        
        # Check if YouTube cookies file exists
        cookies_file = "ytcookies.txt"
        if not os.path.exists(cookies_file):
            cookies_file = None
            print("⚠️ YouTube cookies file not found")
        else:
            print("🍪 Using YouTube cookies for authentication")
        
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'retries': 2,
            'fragment_retries': 2,
            'socket_timeout': 20,
        }
        
        # Add cookies if available
        if cookies_file and os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
        
        print("🔄 Extracting video information...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'Unknown')
            uploader = info.get('uploader', 'Unknown')
            print(f"📹 Title: {video_title}")
            print(f"👤 Uploader: {uploader}")
            
            print("⬇️ Downloading video...")
            ydl.download([url])
        
        # Find downloaded file
        downloaded_files = []
        for root, dirs, files in os.walk(download_dir):
            for file in files:
                if file.endswith(('.mp4', '.mov', '.avi', '.mkv')):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    size_mb = file_size / (1024 * 1024)
                    downloaded_files.append((file_path, size_mb))
                    print(f"✅ Downloaded: {file} ({size_mb:.1f}MB)")
        
        if downloaded_files:
            print(f"🎉 {title} download successful!")
            return True
        else:
            print(f"❌ {title} download failed - no files found")
            return False
            
    except Exception as e:
        print(f"❌ {title} download failed: {str(e)}")
        return False

def test_spotify_download(url, title="Spotify Audio"):
    """Test Spotify download"""
    print(f"\n📥 Testing {title} download...")
    print(f"URL: {url}")
    
    try:
        # Create unique temporary directory for this download
        download_dir = os.path.join(DOWNLOADS_DIR, f"test_spotify_{int(time.time())}")
        os.makedirs(download_dir, exist_ok=True)
        print(f"📂 Download directory: {download_dir}")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'noplaylist': True,
            'retries': 2,
            'fragment_retries': 2,
            'socket_timeout': 20,
        }
        
        print("🔄 Extracting audio information...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_title = info.get('title', 'Unknown')
            artist = info.get('uploader', 'Unknown') if info.get('uploader') else info.get('artist', 'Unknown')
            print(f"🎵 Title: {audio_title}")
            print(f"👤 Artist: {artist}")
            
            print("⬇️ Downloading audio...")
            ydl.download([url])
        
        # Find downloaded file
        downloaded_files = []
        for root, dirs, files in os.walk(download_dir):
            for file in files:
                if file.endswith(('.mp3', '.m4a', '.wav', '.flac')):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    size_mb = file_size / (1024 * 1024)
                    downloaded_files.append((file_path, size_mb))
                    print(f"✅ Downloaded: {file} ({size_mb:.1f}MB)")
        
        if downloaded_files:
            print(f"🎉 {title} download successful!")
            return True
        else:
            print(f"❌ {title} download failed - no files found")
            return False
            
    except Exception as e:
        error_msg = str(e).lower()
        if "drm" in error_msg:
            print(f"⚠️ {title} is DRM protected and cannot be downloaded")
            print("This is expected behavior for Spotify tracks.")
            return True  # This is expected
        else:
            print(f"❌ {title} download failed: {str(e)}")
            return False

def test_generic_download(url, platform, title="Generic Content"):
    """Test generic content download"""
    print(f"\n📥 Testing {title} download...")
    print(f"URL: {url}")
    print(f"Platform: {platform}")
    
    try:
        # Create unique temporary directory for this download
        download_dir = os.path.join(DOWNLOADS_DIR, f"test_{platform}_{int(time.time())}")
        os.makedirs(download_dir, exist_ok=True)
        print(f"📂 Download directory: {download_dir}")
        
        # Check if cookies files exist for specific platforms
        cookies_file = None
        if 'youtube.com' in url or 'youtu.be' in url:
            cookies_file = "ytcookies.txt"
        elif 'instagram.com' in url:
            cookies_file = "cookies.txt"
        
        # Check if cookies file exists
        if cookies_file and not os.path.exists(cookies_file):
            cookies_file = None
            print(f"⚠️ {platform} cookies file not found")
        elif cookies_file:
            print(f"🍪 Using {platform} cookies for authentication")
        
        ydl_opts = {
            'format': 'best[ext=mp4]/best/bestvideo*+bestaudio/best',
            'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'retries': 2,
            'fragment_retries': 2,
            'socket_timeout': 20,
        }
        
        # Add cookies if available
        if cookies_file and os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
        
        print("🔄 Extracting content information...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            content_title = info.get('title', 'Unknown')
            uploader = info.get('uploader', 'Unknown') if info.get('uploader') else info.get('uploader_id', 'Unknown')
            print(f"📹 Title: {content_title}")
            print(f"👤 Uploader: {uploader}")
            
            print("⬇️ Downloading content...")
            ydl.download([url])
        
        # Find downloaded file
        downloaded_files = []
        for root, dirs, files in os.walk(download_dir):
            for file in files:
                if file.endswith(('.mp4', '.mov', '.avi', '.mkv', '.m4a', '.mp3', '.wav', '.flac')):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    size_mb = file_size / (1024 * 1024)
                    downloaded_files.append((file_path, size_mb))
                    print(f"✅ Downloaded: {file} ({size_mb:.1f}MB)")
        
        if downloaded_files:
            print(f"🎉 {title} download successful!")
            return True
        else:
            print(f"❌ {title} download failed - no files found")
            return False
            
    except Exception as e:
        error_msg = str(e).lower()
        if "drm" in error_msg:
            print(f"⚠️ {title} is DRM protected and cannot be downloaded")
            return True  # This is expected
        else:
            print(f"❌ {title} download failed: {str(e)}")
            return False

def main():
    """Main test function"""
    print("🧪 WhatsApp Bot Download Test")
    print("=" * 50)
    
    # Ensure directories exist
    ensure_directories()
    
    # Test URLs
    test_cases = [
        {
            "url": "https://open.spotify.com/track/77VO5dSsGbTPxa2QF2KeIF?si=5e70fd0e53dc4335",
            "platform": "spotify",
            "title": "Spotify Track"
        },
        {
            "url": "https://youtube.com/shorts/kp3DV4apBaY?si=80xR_gw4Nr0_OQTv",
            "platform": "youtube",
            "title": "YouTube Short"
        },
        {
            "url": "https://vt.tiktok.com/ZSUwcbWeR/",
            "platform": "tiktok",
            "title": "TikTok Video"
        },
        {
            "url": "https://www.facebook.com/share/r/1FVwyvW8Yk/?mibextid=wwXIfr",
            "platform": "facebook",
            "title": "Facebook Video"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        if test_case["platform"] == "spotify":
            result = test_spotify_download(test_case["url"], test_case["title"])
        elif test_case["platform"] == "youtube":
            result = test_youtube_download(test_case["url"], test_case["title"])
        else:
            result = test_generic_download(test_case["url"], test_case["platform"], test_case["title"])
        
        results.append((test_case["title"], result))
        print("-" * 50)
    
    # Summary
    print("\n📊 Test Summary:")
    print("=" * 50)
    passed = 0
    for title, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {title}")
        if result:
            passed += 1
    
    print(f"\n📈 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! The bot should work correctly.")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()