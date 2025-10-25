import os
import yt_dlp

def check_cookies():
    """Check if cookie files are valid"""
    print("🍪 Cookie File Validation")
    print("=" * 30)
    
    # Check YouTube cookies
    yt_cookies = "ytcookies.txt"
    if os.path.exists(yt_cookies):
        size = os.path.getsize(yt_cookies)
        print(f"✅ {yt_cookies} exists ({size} bytes)")
        
        # Try to read the file
        try:
            with open(yt_cookies, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.strip().split('\n')
                data_lines = [line for line in lines if line and not line.startswith('#')]
                print(f"📊 Contains {len(data_lines)} cookie entries")
                
                # Check for important cookies
                important_cookies = ['SID', 'SSID', 'APISID', 'SAPISID', 'LOGIN_INFO']
                found_cookies = []
                for line in data_lines:
                    parts = line.split('\t')
                    if len(parts) >= 7:
                        cookie_name = parts[5]
                        if cookie_name in important_cookies:
                            found_cookies.append(cookie_name)
                
                if found_cookies:
                    print(f"🔑 Found important cookies: {', '.join(found_cookies)}")
                else:
                    print("⚠️ No important cookies found - cookies may be expired")
                    
        except Exception as e:
            print(f"❌ Error reading {yt_cookies}: {e}")
    else:
        print(f"❌ {yt_cookies} not found")
    
    print()
    
    # Check Instagram cookies
    ig_cookies = "cookies.txt"
    if os.path.exists(ig_cookies):
        size = os.path.getsize(ig_cookies)
        print(f"✅ {ig_cookies} exists ({size} bytes)")
        
        # Try to read the file
        try:
            with open(ig_cookies, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.strip().split('\n')
                data_lines = [line for line in lines if line and not line.startswith('#')]
                print(f"📊 Contains {len(data_lines)} cookie entries")
                
                # Check for important cookies
                important_cookies = ['sessionid', 'ds_user_id', 'csrftoken']
                found_cookies = []
                for line in data_lines:
                    parts = line.split('\t')
                    if len(parts) >= 7:
                        cookie_name = parts[5]
                        if cookie_name in important_cookies:
                            found_cookies.append(cookie_name)
                
                if found_cookies:
                    print(f"🔑 Found important cookies: {', '.join(found_cookies)}")
                else:
                    print("⚠️ No important cookies found - cookies may be expired")
                    
        except Exception as e:
            print(f"❌ Error reading {ig_cookies}: {e}")
    else:
        print(f"❌ {ig_cookies} not found")

def test_simple_download():
    """Test a simple download without cookies"""
    print("\n📥 Simple Download Test")
    print("=" * 30)
    
    try:
        # Test with a simple video that doesn't require authentication
        test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # YouTube's first video
        
        ydl_opts = {
            'format': 'best[height<=360][ext=mp4]/best[height<=360]',  # Low quality for fast test
            'outtmpl': 'downloads/test_video.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }
        
        print("🔄 Testing simple YouTube download...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
            title = info.get('title', 'Unknown')
            print(f"📹 Title: {title}")
            
            print("⬇️ Downloading test video...")
            ydl.download([test_url])
            
        if os.path.exists('downloads/test_video.mp4'):
            size = os.path.getsize('downloads/test_video.mp4')
            size_mb = size / (1024 * 1024)
            print(f"✅ Test download successful ({size_mb:.1f}MB)")
            return True
        else:
            print("❌ Test download failed")
            return False
            
    except Exception as e:
        print(f"❌ Test download failed: {e}")
        return False

if __name__ == "__main__":
    check_cookies()
    test_simple_download()