import os
import yt_dlp

# Ensure downloads directory exists
os.makedirs('downloads', exist_ok=True)

def test_download_with_cookies(url, platform):
    """Test download with cookies"""
    print(f"📥 Testing {platform} download...")
    print(f"URL: {url}")
    
    try:
        # Configure yt-dlp
        ydl_opts = {
            'format': 'best[height<=360][ext=mp4]/best[height<=360]',  # Low quality for fast test
            'outtmpl': 'downloads/test_%(extractor)s.%(ext)s',
            'quiet': False,
            'no_warnings': False,
            'noplaylist': True,
            'retries': 1,
            'socket_timeout': 15,
        }
        
        # Add cookies for specific platforms
        if 'youtube.com' in url or 'youtu.be' in url:
            if os.path.exists('ytcookies.txt'):
                ydl_opts['cookiefile'] = 'ytcookies.txt'
                print("🍪 Using YouTube cookies")
        elif 'instagram.com' in url:
            if os.path.exists('cookies.txt'):
                ydl_opts['cookiefile'] = 'cookies.txt'
                print("🍪 Using Instagram cookies")
        
        print("🔄 Extracting information...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            extractor = info.get('extractor', 'Unknown')
            print(f"📹 Title: {title}")
            print(f"🔧 Extractor: {extractor}")
            
            print("⬇️ Downloading...")
            ydl.download([url])
        
        # Check if file was downloaded
        for file in os.listdir('downloads'):
            if file.startswith('test_'):
                file_path = os.path.join('downloads', file)
                size = os.path.getsize(file_path)
                size_mb = size / (1024 * 1024)
                print(f"✅ Downloaded: {file} ({size_mb:.1f}MB)")
                return True
        
        print("❌ No file downloaded")
        return False
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

# Test URLs
test_cases = [
    {
        "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
        "platform": "YouTube (First Video)"
    }
]

print("🧪 Simple Download Test")
print("=" * 30)

for test_case in test_cases:
    success = test_download_with_cookies(test_case["url"], test_case["platform"])
    print("-" * 30)
    if success:
        print("🎉 Test completed successfully!")
    else:
        print("⚠️ Test failed!")