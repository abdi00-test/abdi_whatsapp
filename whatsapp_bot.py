import os
import hashlib
import time
import re
import logging
import json
import asyncio
import requests
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

# Import configuration
from config import (
    MAX_FILE_SIZE, DOWNLOADS_DIR, TEMP_DIR, DATA_DIR,
    PHONE_NUMBER_ID, WHATSAPP_TOKEN, VERIFY_TOKEN,
    INSTAGRAM_COOKIES_FILE, INSTAGRAM_REQUEST_DELAY,
    YOUTUBE_COOKIES_FILE, PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS
)

# Try to import required libraries
try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    yt_dlp = None
    YTDLP_AVAILABLE = False
    print("Warning: yt-dlp not available. Some features will be limited.")

try:
    import instaloader
    INSTALOADER_AVAILABLE = True
except ImportError:
    instaloader = None
    INSTALOADER_AVAILABLE = False
    print("Warning: instaloader not available. Instagram features will be limited.")

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    aiohttp = None
    AIOHTTP_AVAILABLE = False
    print("Warning: aiohttp not available. Some features will be limited.")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BeautifulSoup = None
    BS4_AVAILABLE = False
    print("Warning: BeautifulSoup not available. Some features will be limited.")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Track processed URLs to prevent duplicates
processed_urls = set()

class InstagramCookieManager:
    """Manages Instagram cookies for authentication and proxy support"""
    
    def __init__(self, cookies_file: str = INSTAGRAM_COOKIES_FILE):
        self.cookies_file = cookies_file
        self.cookies = {}
        self.session_cookies = None
        self.proxy_config = None
        self.last_request_time = 0
        self._setup_proxy()
        self._load_cookies()
    
    def _setup_proxy(self):
        """Setup proxy configuration if provided"""
        if PROXY_HOST and PROXY_PORT and PROXY_HOST.strip() and PROXY_PORT.strip():
            try:
                proxy_url = f"http://{PROXY_HOST}:{PROXY_PORT}"
                if PROXY_USER and PROXY_PASS and PROXY_USER.strip() and PROXY_PASS.strip():
                    proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
                
                self.proxy_config = {
                    'http': proxy_url,
                    'https': proxy_url
                }
                logger.info(f"✅ Proxy configured: {PROXY_HOST}:{PROXY_PORT}")
            except Exception as e:
                logger.warning(f"❌ Proxy configuration failed: {e}")
                self.proxy_config = None
        else:
            self.proxy_config = None
            logger.info("ℹ️ No proxy configuration found, using direct connection")
    
    def _load_cookies(self):
        """Load cookies from Netscape format cookies.txt file"""
        try:
            if not os.path.exists(self.cookies_file):
                logger.warning(f"❌ Instagram cookies file not found: {self.cookies_file}")
                logger.warning("⚠️ Instagram downloads may fail without proper authentication cookies")
                return
            
            self.cookies = {}
            with open(self.cookies_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or (line.startswith('#') and not line.startswith('#HttpOnly_')):
                        continue
                    
                    if line.startswith('#HttpOnly_'):
                        line = line[10:]
                    
                    parts = line.split('\t')
                    if len(parts) >= 7:
                        domain = parts[0]
                        name = parts[5]
                        value = parts[6]
                        
                        if '.instagram.com' in domain:
                            self.cookies[name] = value
            
            # Create a RequestsCookieJar for session cookies
            self.session_cookies = requests.cookies.RequestsCookieJar()
            for name, value in self.cookies.items():
                # Add cookie directly to the jar
                self.session_cookies.set(name, value, domain='.instagram.com')
            
            logger.info(f"✅ Loaded {len(self.cookies)} Instagram cookies from Netscape format")
            self._validate_loaded_cookies()
            
        except Exception as e:
            logger.error(f"❌ Failed to load Instagram cookies: {e}")
            self.cookies = {}
            self.session_cookies = None
    
    def _validate_loaded_cookies(self):
        """Validate loaded cookies and provide detailed warnings"""
        important_cookies = ['sessionid', 'ds_user_id', 'csrftoken', 'mid', 'datr']
        found_cookies = [name for name in important_cookies if name in self.cookies]
        missing_cookies = [name for name in important_cookies if name not in self.cookies]
        
        logger.info(f"🔑 Authentication cookies found: {', '.join(found_cookies)}")
        
        if missing_cookies:
            logger.warning(f"⚠️ Missing cookies: {', '.join(missing_cookies)}")
        
        if 'sessionid' not in self.cookies:
            logger.error("❌ CRITICAL: sessionid cookie is missing!")
            logger.error("⚠️ Instagram downloads will likely fail without a valid sessionid")
            logger.error("📝 Please update your cookies.txt file with a fresh sessionid from your browser")
            return False
        
        if 'ds_user_id' not in self.cookies:
            logger.warning("⚠️ WARNING: ds_user_id cookie is missing - this may cause authentication issues")
        
        sessionid = self.cookies.get('sessionid', '')
        if sessionid:
            if '%3A' in sessionid or ':' in sessionid:
                logger.info("✅ sessionid format appears valid")
                
                try:
                    if '%3A' in sessionid:
                        user_id_from_session = sessionid.split('%3A')[0]
                    else:
                        user_id_from_session = sessionid.split(':')[0]
                    
                    ds_user_id = self.cookies.get('ds_user_id', '')
                    if ds_user_id and user_id_from_session == ds_user_id:
                        logger.info("✅ sessionid and ds_user_id are consistent")
                    elif ds_user_id:
                        logger.warning("⚠️ sessionid and ds_user_id do not match - cookies may be inconsistent")
                        
                except Exception as e:
                    logger.debug(f"Could not validate sessionid format: {e}")
            else:
                logger.warning("⚠️ sessionid format looks unusual - authentication may fail")
        
        return True
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for Instagram requests with proper authentication"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        if 'csrftoken' in self.cookies:
            headers['X-CSRFToken'] = self.cookies['csrftoken']
        
        return headers
    
    def rate_limit(self):
        """Implement rate limiting for Instagram requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < INSTAGRAM_REQUEST_DELAY:
            sleep_time = INSTAGRAM_REQUEST_DELAY - time_since_last
            logger.debug(f"⏱️ Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def is_authenticated(self) -> bool:
        """Check if we have valid authentication cookies"""
        return bool(self.cookies and 'sessionid' in self.cookies and 'ds_user_id' in self.cookies)
    
    def get_ytdl_opts(self, base_opts: Optional[Dict] = None) -> Dict:
        """Get yt-dlp options with Instagram authentication and proxy support"""
        opts = base_opts.copy() if base_opts else {}
        
        if os.path.exists(self.cookies_file):
            opts['cookiefile'] = self.cookies_file
            logger.info(f"🍪 Using Netscape cookies file: {self.cookies_file}")
            
            if self.cookies and 'sessionid' in self.cookies:
                logger.info("🔑 Instagram authentication cookies detected for yt-dlp")
            else:
                logger.warning("⚠️ No sessionid found in cookies - Instagram access may be limited")
        
        if self.proxy_config:
            opts['proxy'] = self.proxy_config.get('https', self.proxy_config.get('http'))
            logger.info(f"🌐 Using proxy for yt-dlp: {opts['proxy']}")
        elif PROXY_HOST and PROXY_PORT:
            if PROXY_HOST.strip() and PROXY_PORT.strip():
                proxy_url = f"http://{PROXY_HOST}:{PROXY_PORT}"
                if PROXY_USER and PROXY_PASS and PROXY_USER.strip() and PROXY_PASS.strip():
                    proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
                opts['proxy'] = proxy_url
                logger.info(f"🌐 Using proxy for yt-dlp: {proxy_url}")
        
        opts['http_headers'] = opts.get('http_headers', {})
        instagram_headers = self.get_headers()
        
        def error_hook(d):
            if d['status'] == 'error':
                error_msg = str(d.get('error', '')).lower()
                if 'login' in error_msg or 'unauthorized' in error_msg or '401' in error_msg:
                    logger.error("🔒 Instagram authentication failed - cookies may be expired")
                elif '403' in error_msg or 'forbidden' in error_msg:
                    logger.error("🚫 Instagram access forbidden - possible rate limiting or invalid cookies")
                elif 'private' in error_msg:
                    logger.error("🔒 Instagram content is private - authentication may be required")
        
        opts['progress_hooks'] = opts.get('progress_hooks', [])
        opts['progress_hooks'].append(error_hook)
        instagram_headers.pop('Cookie', None)
        opts['http_headers'].update(instagram_headers)
        
        return opts

# Initialize Instagram cookie manager
instagram_auth = InstagramCookieManager()

# WhatsApp Business API client
class WhatsAppBusiness:
    def __init__(self, access_token: str, phone_number_id: str):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.api_url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        # Track sent messages to prevent duplicates
        self.sent_messages = set()
    
    def send_message(self, message: str, recipient_id: str) -> Dict[str, Any]:
        """Send a text message via WhatsApp API"""
        # Create a unique key for this message
        message_key = f"{recipient_id}:{hashlib.md5(message.encode()).hexdigest()}"
        
        # Check if we've already sent this message
        if message_key in self.sent_messages:
            logger.debug(f"Skipping duplicate message to {recipient_id}: {message[:50]}...")
            return {"success": True}
        
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "text": {
                "body": message
            }
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            if response.status_code == 200:
                logger.info(f"✅ Message sent successfully to {recipient_id}")
                # Add to sent messages set
                self.sent_messages.add(message_key)
                return {"success": True}
            else:
                logger.error(f"❌ Failed to send message to {recipient_id}: {response.text}")
                return {"success": False, "error": response.text}
        except Exception as e:
            logger.error(f"❌ Error sending message to {recipient_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def send_media(self, media_path: str, recipient_id: str, media_type: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """Send media (image/video/audio) via WhatsApp API"""
        try:
            # Check if file exists
            if not os.path.exists(media_path):
                logger.error(f"❌ Media file not found: {media_path}")
                return {"success": False, "error": "File not found"}
            
            # Create a unique key for this media
            file_hash = hashlib.md5(open(media_path, 'rb').read()).hexdigest()
            media_key = f"{recipient_id}:{file_hash}"
            
            # Check if we've already sent this media
            if media_key in self.sent_messages:
                logger.debug(f"Skipping duplicate media to {recipient_id}: {media_path}")
                return {"success": True}
            
            # Determine MIME type based on file extension
            file_extension = media_path.lower().split('.')[-1]
            mime_types = {
                'mp4': 'video/mp4',
                'mov': 'video/quicktime',
                'avi': 'video/x-msvideo',
                'mkv': 'video/x-matroska',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'mp3': 'audio/mpeg',
                'wav': 'audio/wav',
                'ogg': 'audio/ogg'
            }
            mime_type = mime_types.get(file_extension, 'application/octet-stream')
            
            # Read file data
            with open(media_path, 'rb') as f:
                file_data = f.read()
            
            # Upload the media to WhatsApp servers
            files = {
                'file': (os.path.basename(media_path), file_data, mime_type),
                'type': (None, media_type),
                'messaging_product': (None, 'whatsapp')
            }
            
            upload_response = requests.post(
                f"https://graph.facebook.com/v17.0/{self.phone_number_id}/media",
                files=files,
                headers={
                    "Authorization": f"Bearer {self.access_token}"
                }
            )
            
            if upload_response.status_code == 200:
                upload_data = upload_response.json()
                media_id = upload_data.get('id')
                
                if media_id:
                    # Now send the uploaded media
                    if media_type == 'video':
                        payload = {
                            "messaging_product": "whatsapp",
                            "to": recipient_id,
                            "type": "video",
                            "video": {
                                "id": media_id,
                                "caption": caption or "Here's your downloaded video!"
                            }
                        }
                    elif media_type == 'image':
                        payload = {
                            "messaging_product": "whatsapp",
                            "to": recipient_id,
                            "type": "image",
                            "image": {
                                "id": media_id,
                                "caption": caption or "Here's your downloaded image!"
                            }
                        }
                    elif media_type == 'audio':
                        payload = {
                            "messaging_product": "whatsapp",
                            "to": recipient_id,
                            "type": "audio",
                            "audio": {
                                "id": media_id
                            }
                        }
                    else:  # document
                        payload = {
                            "messaging_product": "whatsapp",
                            "to": recipient_id,
                            "type": "document",
                            "document": {
                                "id": media_id,
                                "caption": caption or "Here's your downloaded file!"
                            }
                        }
                    
                    send_response = requests.post(self.api_url, json=payload, headers=self.headers)
                    if send_response.status_code == 200:
                        logger.info(f"✅ {media_type.title()} sent successfully to {recipient_id}")
                        # Add to sent messages set
                        self.sent_messages.add(media_key)
                        return {"success": True}
                    else:
                        error_msg = send_response.json() if send_response.content else "Unknown error"
                        logger.error(f"❌ Failed to send {media_type} to {recipient_id}: {error_msg}")
                        return {"success": False, "error": str(error_msg)}
                else:
                    logger.error(f"❌ Failed to get media ID from upload response: {upload_data}")
                    return {"success": False, "error": "Failed to get media ID"}
            else:
                error_msg = upload_response.json() if upload_response.content else "Unknown error"
                logger.error(f"❌ Failed to upload media: {error_msg}")
                return {"success": False, "error": str(error_msg)}
                
        except Exception as e:
            logger.error(f"❌ Error sending media to {recipient_id}: {e}")
            return {"success": False, "error": str(e)}

# Initialize WhatsApp client
messenger = WhatsAppBusiness(WHATSAPP_TOKEN, PHONE_NUMBER_ID)

# Platform patterns with enhanced detection
PLATFORM_PATTERNS = {
    'youtube': r'(?:youtube\.com|youtu\.be|music\.youtube\.com)',
    'pinterest': r'(?:pinterest\.com|pin\.it)',
    'instagram': r'(?:instagram\.com|instagr\.am)',
    'threads': r'(?:threads\.net)',
    'tiktok': r'(?:tiktok\.com|vm\.tiktok\.com)',
    'facebook': r'(?:facebook\.com|fb\.watch|fb\.me)',
    'spotify': r'(?:spotify\.com|open\.spotify\.com)',
    'twitter': r'(?:twitter\.com|x\.com|t\.co)'
}

# Image file extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'}

# User agents for different platforms
USER_AGENTS = {
    'default': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'pinterest': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'instagram': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
    'facebook': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    'tiktok': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def ensure_directories():
    """Ensure required directories exist"""
    for directory in [DOWNLOADS_DIR, TEMP_DIR, DATA_DIR]:
        os.makedirs(directory, exist_ok=True)

def get_url_hash(url: str) -> str:
    """Generate hash for URL to use as cache key"""
    return hashlib.md5(url.encode()).hexdigest()

def sanitize_filename(title: str, max_length: int = 100) -> str:
    """Sanitize title for use as filename"""
    if not title or not title.strip():
        return f"audio_{int(time.time())}"
    
    try:
        import unicodedata
        safe_title = unicodedata.normalize('NFKD', title)
        safe_title = safe_title.encode('ascii', 'ignore').decode('ascii')
    except:
        safe_title = title
    
    safe_title = re.sub(r'[<>:"/\\|?*]', '', safe_title)
    safe_title = re.sub(r'\.{2,}', '.', safe_title)
    safe_title = re.sub(r'\s+', ' ', safe_title).strip()
    safe_title = safe_title.strip('. ')
    
    safe_title = safe_title.replace('&', 'and')
    safe_title = safe_title.replace('#', 'no')
    safe_title = safe_title.replace('%', 'percent')
    safe_title = safe_title.replace('(', '')
    safe_title = safe_title.replace(')', '')
    safe_title = safe_title.replace('[', '')
    safe_title = safe_title.replace(']', '')
    
    safe_title = re.sub(r'[^\w\s\-_.]', '', safe_title)
    
    if len(safe_title) > max_length:
        truncated = safe_title[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.7:
            safe_title = truncated[:last_space]
        else:
            safe_title = truncated
    
    safe_title = safe_title.rstrip('.,!?;:-_ ')
    
    if not safe_title or safe_title.isspace() or len(safe_title) < 3:
        safe_title = f"audio_{int(time.time())}"
    
    logger.debug(f"🎵 Sanitized filename: '{title}' -> '{safe_title}'")
    return safe_title

def detect_platform(url: str) -> Optional[str]:
    """Detect platform from URL"""
    url_lower = url.lower()
    logger.debug(f"🔍 Platform detection for URL: {url}")
    
    # Handle YouTube Shorts by converting to standard YouTube URL
    if 'youtube.com/shorts/' in url_lower:
        logger.info(f"🔄 Converting YouTube Shorts URL to standard format: {url}")
        return 'youtube'
    
    # Treat yt-dlp search queries (ytsearch, ytsearch1, etc.) as YouTube
    if url_lower.startswith('ytsearch'):
        logger.info(f"🎯 Detected platform: youtube for URL: {url}")
        return 'youtube'

    for platform, pattern in PLATFORM_PATTERNS.items():
        if re.search(pattern, url_lower):
            logger.info(f"🎯 Detected platform: {platform} for URL: {url}")
            return platform
    
    logger.warning(f"❓ Unknown platform for URL: {url}")
    return None

def normalize_youtube_shorts_url(url: str) -> str:
    """Convert YouTube Shorts URL to standard watch URL with proper ID extraction"""
    if 'youtube.com/shorts/' in url:
        # Extract video ID from Shorts URL - fix the truncation issue
        match = re.search(r'youtube\.com/shorts/([^/?&#]+)', url)
        if match:
            video_id = match.group(1)
            # Ensure we have a complete video ID (should be 11 characters)
            if len(video_id) >= 11:
                # Take only the first 11 characters to ensure proper ID
                video_id = video_id[:11]
                normalized_url = f"https://www.youtube.com/watch?v={video_id}"
                logger.info(f"✅ Normalized YouTube Shorts URL: {url} -> {normalized_url}")
                return normalized_url
            else:
                logger.warning(f"⚠️ Incomplete YouTube ID detected: {video_id}")
                # Try to extract a longer ID if available
                match_full = re.search(r'youtube\.com/shorts/([a-zA-Z0-9_-]+)', url)
                if match_full:
                    full_id = match_full.group(1)
                    if len(full_id) >= 11:
                        full_id = full_id[:11]
                        normalized_url = f"https://www.youtube.com/watch?v={full_id}"
                        logger.info(f"✅ Normalized YouTube Shorts URL (full ID): {url} -> {normalized_url}")
                        return normalized_url
    return url

def is_supported_url(url: str) -> bool:
    """Check if URL is from supported platform"""
    return detect_platform(url) is not None

def detect_content_type(url: str, info: Optional[Dict] = None) -> str:
    """Enhanced content type detection"""
    url_lower = url.lower()
    
    if any(ext in url_lower for ext in IMAGE_EXTENSIONS):
        return 'image'
    
    image_domains = ['imgur.com', 'i.redd.it', 'pbs.twimg.com', 'scontent', 'cdninstagram', 'pinimg.com']
    if any(domain in url_lower for domain in image_domains):
        return 'image'
    
    if 'instagram.com' in url_lower:
        if '/p/' in url_lower:
            return 'mixed'
        elif '/reel/' in url_lower or '/reels/' in url_lower:
            return 'video'
        elif '/stories/' in url_lower:
            return 'mixed'
    
    if 'threads.net' in url_lower:
        return 'mixed'
    
    if 'pinterest.com' in url_lower or 'pin.it' in url_lower:
        return 'mixed'
    
    if 'facebook.com' in url_lower:
        if 'photo.php' in url_lower or '/photos/' in url_lower:
            return 'image'
        elif 'video.php' in url_lower or '/videos/' in url_lower:
            return 'video'
        else:
            return 'mixed'
    
    if 'twitter.com' in url_lower or 'x.com' in url_lower:
        if '/photo/' in url_lower:
            return 'image'
        elif '/video/' in url_lower:
            return 'video'
        else:
            return 'mixed'
    
    if info:
        formats = info.get('formats', [])
        has_video = any(f.get('vcodec', 'none') != 'none' for f in formats)
        has_audio = any(f.get('acodec', 'none') != 'none' for f in formats)
        
        if has_video:
            return 'video'
        elif has_audio:
            return 'audio'
        else:
            return 'image'
    
    return 'mixed'

async def download_media(url: str, quality: Optional[str] = None, audio_only: bool = False, info: Optional[Dict] = None) -> Optional[str]:
    """Download media with enhanced fallback mechanisms"""
    if not YTDLP_AVAILABLE or yt_dlp is None:
        raise Exception("yt-dlp not available")
    
    try:
        platform = detect_platform(url)
        
        if info and info.get('source') == 'direct' and info.get('direct_url'):
            return await download_direct_media(info['direct_url'], platform)
        
        temp_dir = os.path.join(TEMP_DIR, f"download_{int(time.time())}")
        os.makedirs(temp_dir, exist_ok=True)
        
        if audio_only:
            title = None
            if info:
                if info.get('title'):
                    title = info['title']
                    logger.debug(f"🎵 Found title in info: '{title}'")
                elif info.get('yt_dlp_info') and info['yt_dlp_info'].get('title'):
                    title = info['yt_dlp_info']['title']
                    logger.debug(f"🎵 Found title in yt_dlp_info: '{title}'")
                else:
                    logger.debug(f"🎵 No title found in info object: {info}")
            else:
                logger.debug("🎵 No info object provided for audio download")
            
            if not title and platform:
                logger.info(f"🎵 Attempting to extract title for {platform} URL: {url}")
                try:
                    extracted_info = await get_media_info(url)
                    if extracted_info and extracted_info.get('title'):
                        title = extracted_info['title']
                        logger.info(f"🎵 Successfully extracted title: '{title}'")
                except Exception as e:
                    logger.debug(f"🎵 Failed to extract info for filename: {e}")
            
            if title and title.strip():
                filename = sanitize_filename(title)
                logger.info(f"🎵 Generated audio filename from title: '{title}' -> '{filename}'")
            else:
                filename = f"audio_{get_url_hash(url)[:8]}_{int(time.time())}"
                logger.warning(f"🎵 No title available for {platform} URL, using fallback filename: {filename}")
        else:
            filename = f"media_{get_url_hash(url)[:8]}_{int(time.time())}"
        
        if audio_only:
            output_template = os.path.join(temp_dir, f"{filename}.%(ext)s")
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': output_template,
                'extractaudio': True,
                'audioformat': 'mp3',
                'audioquality': '320K',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True
            }
            # Use YouTube cookies if available for audio downloads (especially for Spotify conversions)
            try:
                if platform == 'youtube' or audio_only:
                    if os.path.exists(YOUTUBE_COOKIES_FILE):
                        ydl_opts['cookiefile'] = YOUTUBE_COOKIES_FILE
                        logger.info("🍪 Using YouTube cookies for audio download")
            except Exception:
                pass
        else:
            output_template = os.path.join(temp_dir, f"{filename}.%(ext)s")
            
            if quality:
                format_selector = {
                    "1080p": "best[height<=1080][height>720][ext=mp4]/best[height<=1080][height>720]/bestvideo[height<=1080][height>720]+bestaudio/best[height<=1080]",
                    "720p": "best[height<=720][height>480][ext=mp4]/best[height<=720][height>480]/bestvideo[height<=720][height>480]+bestaudio/best[height<=720]",
                    "480p": "best[height<=480][height>360][ext=mp4]/best[height<=480][height>360]/bestvideo[height<=480][height>360]+bestaudio/best[height<=480]",
                    "360p": "best[height<=360][height>240][ext=mp4]/best[height<=360][height>240]/bestvideo[height<=360][height>240]+bestaudio/best[height<=360]",
                    "240p": "best[height<=240][height>144][ext=mp4]/best[height<=240][height>144]/bestvideo[height<=240][height>144]+bestaudio/best[height<=240]",
                    "144p": "worst[height<=144][ext=mp4]/worst[height<=144]/bestvideo[height<=144]+bestaudio/worst"
                }.get(quality, 'best[ext=mp4]/best')
            else:
                format_selector = 'best[ext=mp4]/best'
            
            ydl_opts = {
                'format': format_selector,
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True,
                'merge_output_format': 'mp4',
                'noplaylist': True
            }
            try:
                if platform == 'youtube' and os.path.exists(YOUTUBE_COOKIES_FILE):
                    ydl_opts['cookiefile'] = YOUTUBE_COOKIES_FILE
            except Exception:
                pass
        
        ydl_opts.update({
            'retries': 2,
            'fragment_retries': 2,
            'socket_timeout': 20,
            'http_chunk_size': 16777216,
            'concurrent_fragment_downloads': 6,
            'ignoreerrors': False,
            'geo_bypass': True,
            'no_check_certificate': True
        })
        
        if platform == 'pinterest':
            ydl_opts['http_headers'] = {
                'User-Agent': USER_AGENTS['pinterest'],
                'Referer': 'https://www.pinterest.com/'
            }
        elif platform == 'instagram':
            if info and info.get('no_auth'):
                logger.info("⚠️ Using non-authenticated Instagram download (fallback mode)")
                ydl_opts['http_headers'] = {
                    'User-Agent': USER_AGENTS.get('instagram', USER_AGENTS['default'])
                }
            else:
                ydl_opts = instagram_auth.get_ytdl_opts(ydl_opts)
                logger.info("🔑 Using authenticated Instagram download")
        elif platform == 'threads':
            if info and info.get('no_auth'):
                logger.info("⚠️ Using non-authenticated Threads download (fallback mode)")
                ydl_opts['http_headers'] = {
                    'User-Agent': USER_AGENTS.get('instagram', USER_AGENTS['default'])
                }
            else:
                ydl_opts = instagram_auth.get_ytdl_opts(ydl_opts)
                logger.info("🔑 Using authenticated Threads download")
        elif platform == 'facebook':
            ydl_opts['http_headers'] = {
                'User-Agent': USER_AGENTS['facebook']
            }
        elif platform == 'tiktok':
            ydl_opts['http_headers'] = {
                'User-Agent': USER_AGENTS['tiktok'],
                'Referer': 'https://www.tiktok.com/'
            }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                if os.path.isfile(file_path) and file.startswith(filename):
                    return file_path
            
        except Exception as ytdlp_error:
            error_str = str(ytdlp_error).lower()
            
            if platform in ['instagram', 'threads']:
                if any(err in error_str for err in ['no video formats found', 'no formats found', 'unable to extract', 'private video']):
                    logger.debug(f"{platform.title()} yt-dlp expected failure (likely image-only post): {ytdlp_error}")
                    return await attempt_fallback_download(url, platform, temp_dir, filename, audio_only, silent_fallback=True)
                else:
                    logger.warning(f"{platform.title()} yt-dlp download failed: {ytdlp_error}")
            else:
                logger.warning(f"yt-dlp download failed: {ytdlp_error}")
            
            return await attempt_fallback_download(url, platform, temp_dir, filename, audio_only)
        
        return None
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        error_str = str(e).lower()
        
        if any(term in error_str for term in ['drm', 'protected', 'copyright']):
            raise Exception("DRM_PROTECTED")
        elif any(term in error_str for term in ['private', 'unavailable', 'access denied']):
            raise Exception("ACCESS_DENIED")
        elif any(term in error_str for term in ['age restricted', 'age-restricted']):
            raise Exception("AGE_RESTRICTED")
        else:
            raise Exception("DOWNLOAD_FAILED")

async def download_direct_media(url: str, platform: Optional[str] = None) -> Optional[str]:
    """Download media directly using requests"""
    try:
        headers = {
            'User-Agent': USER_AGENTS.get(platform, USER_AGENTS['default']),
            'Referer': url if platform != 'pinterest' else 'https://www.pinterest.com/',
        }
        
        temp_dir = os.path.join(TEMP_DIR, f"direct_{int(time.time())}")
        os.makedirs(temp_dir, exist_ok=True)
        
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', '')
        file_ext = '.jpg'
        
        if 'video' in content_type:
            file_ext = '.mp4'
        elif 'image' in content_type:
            if 'png' in content_type:
                file_ext = '.png'
            elif 'gif' in content_type:
                file_ext = '.gif'
            elif 'webp' in content_type:
                file_ext = '.webp'
        elif 'audio' in content_type:
            file_ext = '.mp3'
        
        filename = f"{get_url_hash(url)[:8]}_{int(time.time())}{file_ext}"
        file_path = os.path.join(temp_dir, filename)
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return file_path
    
    except Exception as e:
        logger.error(f"Direct download failed: {e}")
        return None

async def attempt_fallback_download(url: str, platform: str, temp_dir: str, filename: str, audio_only: bool = False, silent_fallback: bool = False) -> Optional[str]:
    """Attempt fallback download methods"""
    try:
        if platform in ['pinterest', 'instagram', 'threads', 'facebook', 'twitter']:
            if platform in ['instagram', 'threads'] and INSTALOADER_AVAILABLE:
                try:
                    instagram_data = await download_instagram_media(url)
                    if instagram_data and instagram_data.get('media_files'):
                        if not silent_fallback:
                            logger.info(f"✅ {platform.title()} fallback download successful")
                        else:
                            logger.debug(f"✅ {platform.title()} silent fallback download successful")
                        return instagram_data['media_files'][0]['path']
                except Exception as e:
                    if not silent_fallback:
                        logger.debug(f"Instagram instaloader fallback failed: {e}")
                    else:
                        logger.debug(f"Instagram silent instaloader fallback failed: {e}")
            
            media_info = await extract_direct_media_url(url, platform)
            if media_info and media_info.get('url'):
                return await download_direct_media(media_info['url'], platform)
        
        if platform in ['instagram', 'facebook', 'twitter']:
            image_url = await extract_image_from_page(url, platform)
            if image_url:
                return await download_direct_media(image_url, platform)
        
        extractors_to_try = []
        if platform == 'pinterest':
            extractors_to_try = ['pinterest', 'generic']
        elif platform == 'instagram':
            extractors_to_try = ['instagram', 'generic']
        elif platform == 'threads':
            extractors_to_try = ['instagram', 'generic']
        elif platform == 'facebook':
            extractors_to_try = ['facebook', 'generic']
        
        for extractor in extractors_to_try:
            try:
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': os.path.join(temp_dir, f"{filename}_fallback.%(ext)s"),
                    'quiet': True,
                    'no_warnings': True,
                    'extractor': extractor,
                    'retries': 1,
                    'socket_timeout': 10
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                for file in os.listdir(temp_dir):
                    if file.startswith(f"{filename}_fallback"):
                        return os.path.join(temp_dir, file)
                        
            except Exception as e:
                logger.debug(f"Extractor {extractor} failed: {e}")
                continue
        
        return None
        
    except Exception as e:
        logger.error(f"Fallback download failed: {e}")
        return None

async def download_instagram_media(url: str) -> Optional[Dict]:
    """Download Instagram media using authenticated instaloader"""
    if not INSTALOADER_AVAILABLE or instaloader is None:
        return None
    
    try:
        instagram_auth.rate_limit()
        
        shortcode = extract_instagram_shortcode(url)
        if not shortcode:
            logger.error("Could not extract shortcode from Instagram URL")
            return None

        temp_dir = f"{TEMP_DIR}/instagram_{int(time.time())}"
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            loader = instaloader.Instaloader(
                download_videos=True,
                download_video_thumbnails=False,
                download_comments=False,
                save_metadata=False,
                compress_json=False,
                post_metadata_txt_pattern="",
                quiet=True
            )
            
            if instagram_auth.is_authenticated() and instagram_auth.session_cookies:
                loader.context._session.cookies.update(instagram_auth.session_cookies)
                logger.info("✅ Instagram session loaded with cookies")
            
            loader.dirname_pattern = temp_dir
            
            logger.info(f"🔄 Downloading Instagram post with shortcode: {shortcode}")
            
            if instagram_auth.is_authenticated():
                logger.info("🔑 Using authenticated Instagram session")
            else:
                logger.warning("⚠️ No Instagram authentication - may fail on private/restricted content")
            
            post = instaloader.Post.from_shortcode(loader.context, shortcode)
            loader.download_post(post, target=shortcode)
            
            media_files = []
            for root, _, files in os.walk(temp_dir):
                for file in sorted(files):
                    full_path = os.path.join(root, file)
                    if file.endswith((".jpg", ".jpeg", ".png", ".mp4", ".webp")):
                        media_files.append({
                            'path': full_path,
                            'type': 'video' if file.endswith('.mp4') else 'image',
                            'filename': file
                        })
            
            if not media_files:
                logger.error("No media files found after download")
                return None
            
            logger.info(f"✅ Downloaded {len(media_files)} Instagram media file(s)")
            
            return {
                'media_files': media_files,
                'temp_dir': temp_dir,
                'title': post.caption[:100] + "..." if post.caption and len(post.caption) > 100 else (post.caption or "Instagram Post"),
                'owner': post.owner_username,
                'is_video': post.is_video,
                'is_carousel': len(media_files) > 1,
                'media_count': len(media_files)
            }
            
        except Exception as e:
            logger.error(f"Instaloader download error: {e}")
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            return None
            
    except Exception as e:
        logger.error(f"Instagram download error: {e}")
        return None

def extract_instagram_shortcode(url: str) -> Optional[str]:
    """Extract Instagram shortcode from URL"""
    try:
        parts = url.strip('/').split('/')
        if 'p' in parts:
            return parts[parts.index('p') + 1]
        elif 'reel' in parts:
            return parts[parts.index('reel') + 1]
        elif 'tv' in parts:
            return parts[parts.index('tv') + 1]
        elif 'stories' in parts:
            return None
    except Exception as e:
        logger.error(f"Shortcode extraction error: {e}")
        return None

async def extract_direct_media_url(url: str, platform: str) -> Optional[Dict]:
    """Extract direct media URLs using custom scrapers"""
    try:
        headers = {
            'User-Agent': USER_AGENTS.get(platform, USER_AGENTS['default']),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        if platform == 'pinterest':
            return await extract_pinterest_media(url, headers)
        elif platform == 'instagram':
            return await extract_instagram_media_fallback(url, headers)
        elif platform == 'threads':
            logger.info("🧵 Extracting Threads media using Instagram fallback method")
            return await extract_instagram_media_fallback(url, headers)
        elif platform == 'facebook':
            return await extract_facebook_media(url, headers)
        
        return None
    except Exception as e:
        logger.error(f"Direct extraction failed for {platform}: {e}")
        return None

async def extract_pinterest_media(url: str, headers: Dict) -> Optional[Dict]:
    """Extract Pinterest media URLs"""
    try:
        if 'pin.it' in url:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, allow_redirects=True) as response:
                    url = str(response.url)
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                scripts = soup.find_all('script', string=re.compile(r'pinData|__PWS_DATA__'))
                for script in scripts:
                    script_content = script.string
                    if not script_content:
                        continue
                    
                    patterns = [
                        r'pinData\s*=\s*({.*?});',
                        r'__PWS_DATA__\s*=\s*({.*?});',
                        r'bootstrapData\s*=\s*({.*?});'
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, script_content, re.DOTALL)
                        if match:
                            try:
                                pin_data = json.loads(match.group(1))
                                result = extract_pinterest_urls_from_data(pin_data)
                                if result:
                                    return result
                            except Exception as e:
                                logger.debug(f"JSON parsing failed: {e}")
                                continue
                
                video_tag = soup.find('video')
                if video_tag:
                    source_tag = video_tag.find('source')
                    if source_tag and source_tag.get('src'):
                        return {
                            'type': 'video',
                            'url': source_tag['src'],
                            'title': 'Pinterest Video'
                        }
                
                img_tag = soup.find('img', {'data-pin-media': True})
                if img_tag and img_tag.get('data-pin-media'):
                    return {
                        'type': 'image',
                        'url': img_tag['data-pin-media'],
                        'title': 'Pinterest Image'
                    }
                
                img_tag = soup.find('img', {'srcset': True})
                if img_tag and img_tag.get('srcset'):
                    srcset = img_tag['srcset']
                    urls = srcset.split(',')
                    if urls:
                        best_url = urls[-1].split()[0]
                        return {
                            'type': 'image',
                            'url': best_url,
                            'title': 'Pinterest Image'
                        }
        
        return None
    except Exception as e:
        logger.error(f"Pinterest extraction error: {e}")
        return None

def extract_pinterest_urls_from_data(data: Dict) -> Optional[Dict]:
    """Extract media URLs from Pinterest data"""
    try:
        if isinstance(data, dict):
            # Try to find media data in various possible locations
            media_data = None
            
            # Check for media data in different possible paths
            if 'props' in data and 'initialReduxState' in data['props']:
                redux_state = data['props']['initialReduxState']
                if 'pins' in redux_state:
                    pins = list(redux_state['pins'].values())
                    if pins:
                        media_data = pins[0]
            elif 'resourceResponses' in data:
                for response in data['resourceResponses']:
                    if 'response' in response and 'data' in response['response']:
                        media_data = response['response']['data']
                        break
            elif 'data' in data:
                media_data = data['data']
            
            if media_data:
                # Extract video URL
                if 'videos' in media_data and media_data['videos']:
                    videos = media_data['videos']
                    if isinstance(videos, dict) and 'video_list' in videos:
                        video_list = videos['video_list']
                        if video_list:
                            # Get the highest quality video
                            best_video = None
                            best_quality = 0
                            for key, video_info in video_list.items():
                                if isinstance(video_info, dict) and 'url' in video_info:
                                    quality = video_info.get('width', 0) * video_info.get('height', 0)
                                    if quality > best_quality:
                                        best_quality = quality
                                        best_video = video_info['url']
                            if best_video:
                                return {
                                    'type': 'video',
                                    'url': best_video,
                                    'title': media_data.get('title', 'Pinterest Video')
                                }
                
                # Extract image URL
                if 'images' in media_data and media_data['images']:
                    images = media_data['images']
                    if isinstance(images, dict) and 'orig' in images:
                        orig_image = images['orig']
                        if isinstance(orig_image, dict) and 'url' in orig_image:
                            return {
                                'type': 'image',
                                'url': orig_image['url'],
                                'title': media_data.get('title', 'Pinterest Image')
                            }
                    elif isinstance(images, list) and images:
                        first_image = images[0]
                        if isinstance(first_image, dict) and 'url' in first_image:
                            return {
                                'type': 'image',
                                'url': first_image['url'],
                                'title': media_data.get('title', 'Pinterest Image')
                            }
        
        return None
    except Exception as e:
        logger.debug(f"Pinterest data extraction error: {e}")
        return None

async def extract_instagram_media_fallback(url: str, headers: Dict) -> Optional[Dict]:
    """Extract Instagram media URLs using fallback method"""
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                # Look for JSON data in script tags
                scripts = soup.find_all('script', string=re.compile(r'window\._sharedData'))
                for script in scripts:
                    script_content = script.string
                    if script_content:
                        # Extract JSON data
                        json_match = re.search(r'window\._sharedData\s*=\s*({.*?});', script_content, re.DOTALL)
                        if json_match:
                            try:
                                shared_data = json.loads(json_match.group(1))
                                # Extract media info from shared data
                                entry_data = shared_data.get('entry_data', {})
                                post_page = entry_data.get('PostPage', [])
                                if post_page and isinstance(post_page, list) and len(post_page) > 0:
                                    graphql = post_page[0].get('graphql', {})
                                    shortcode_media = graphql.get('shortcode_media', {})
                                    
                                    # Check if it's a carousel
                                    edge_sidecar_to_children = shortcode_media.get('edge_sidecar_to_children', {})
                                    edges = edge_sidecar_to_children.get('edges', [])
                                    
                                    if edges:
                                        # Carousel post
                                        media_items = []
                                        for edge in edges:
                                            node = edge.get('node', {})
                                            if node.get('__typename') == 'GraphVideo':
                                                video_url = node.get('video_url')
                                                if video_url:
                                                    media_items.append({
                                                        'type': 'video',
                                                        'url': video_url
                                                    })
                                            else:
                                                display_url = node.get('display_url')
                                                if display_url:
                                                    media_items.append({
                                                        'type': 'image',
                                                        'url': display_url
                                                    })
                                        
                                        if media_items:
                                            return {
                                                'type': 'mixed',
                                                'items': media_items,
                                                'title': shortcode_media.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', 'Instagram Post')[:100]
                                            }
                                    else:
                                        # Single media post
                                        if shortcode_media.get('is_video'):
                                            video_url = shortcode_media.get('video_url')
                                            if video_url:
                                                return {
                                                    'type': 'video',
                                                    'url': video_url,
                                                    'title': shortcode_media.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', 'Instagram Video')[:100]
                                                }
                                        else:
                                            display_url = shortcode_media.get('display_url')
                                            if display_url:
                                                return {
                                                    'type': 'image',
                                                    'url': display_url,
                                                    'title': shortcode_media.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', 'Instagram Image')[:100]
                                                }
                            except Exception as e:
                                logger.debug(f"JSON parsing failed: {e}")
                                continue
                
                # Fallback to meta tags
                og_image = soup.find('meta', property='og:image')
                og_video = soup.find('meta', property='og:video')
                
                if og_video and og_video.get('content'):
                    return {
                        'type': 'video',
                        'url': og_video['content'],
                        'title': 'Instagram Video'
                    }
                elif og_image and og_image.get('content'):
                    return {
                        'type': 'image',
                        'url': og_image['content'],
                        'title': 'Instagram Image'
                    }
        
        return None
    except Exception as e:
        logger.error(f"Instagram fallback extraction error: {e}")
        return None

async def extract_facebook_media(url: str, headers: Dict) -> Optional[Dict]:
    """Extract Facebook media URLs"""
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                og_video = soup.find('meta', property='og:video')
                og_image = soup.find('meta', property='og:image')
                
                if og_video and og_video.get('content'):
                    return {
                        'type': 'video',
                        'url': og_video['content'],
                        'title': 'Facebook Video'
                    }
                elif og_image and og_image.get('content'):
                    return {
                        'type': 'image',
                        'url': og_image['content'],
                        'title': 'Facebook Image'
                    }
        
        return None
    except Exception as e:
        logger.error(f"Facebook extraction error: {e}")
        return None

async def extract_image_from_page(url: str, platform: str) -> Optional[str]:
    """Extract image URL directly from page HTML"""
    try:
        headers = {
            'User-Agent': USER_AGENTS.get(platform, USER_AGENTS['default'])
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                selectors = [
                    'meta[property="og:image"]',
                    'meta[name="twitter:image"]',
                    'meta[property="og:image:url"]',
                    'img[data-src*="scontent"]',
                    'img[src*="twimg.com"]',
                    'img[src*="pinimg.com"]'
                ]
                
                for selector in selectors:
                    element = soup.select_one(selector)
                    if element:
                        image_url = element.get('content') or element.get('src') or element.get('data-src')
                        if image_url and any(ext in image_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                            return image_url
                
                return None
                
    except Exception as e:
        logger.error(f"Image extraction failed: {e}")
        return None

async def get_media_info(url: str) -> Optional[Dict]:
    """Extract media information with fallback to direct extraction"""
    if not YTDLP_AVAILABLE or yt_dlp is None:
        return None
    
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
            'socket_timeout': 20,
            'retries': 2,
            'noplaylist': True
        }
        
        platform = detect_platform(url)
        try:
            if platform == 'youtube' and os.path.exists(YOUTUBE_COOKIES_FILE):
                ydl_opts['cookiefile'] = YOUTUBE_COOKIES_FILE
        except Exception:
            pass
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                thumbnail_path = None
                if info.get('thumbnail'):
                    try:
                        response = requests.get(info['thumbnail'], timeout=10)
                        if response.status_code == 200:
                            thumbnail_path = f"{TEMP_DIR}/{info.get('id', 'temp')}_{int(time.time())}.jpg"
                            with open(thumbnail_path, 'wb') as f:
                                f.write(response.content)
                    except Exception as e:
                        logger.warning(f"Thumbnail download failed: {e}")
                
                content_type = detect_content_type(url, info)
                
                return {
                    'title': info.get('title', 'Unknown Title'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail'),
                    'local_thumbnail': thumbnail_path,
                    'uploader': info.get('uploader', 'Unknown'),
                    'id': info.get('id', ''),
                    'platform': platform,
                    'content_type': content_type,
                    'timestamp': time.time(),
                    'source': 'yt-dlp'
                }
        
        except Exception as ytdlp_error:
            logger.warning(f"yt-dlp failed: {ytdlp_error}")
            
            if platform in ['pinterest', 'instagram', 'threads', 'facebook']:
                media_info = await extract_direct_media_url(url, platform)
                if media_info:
                    return {
                        'title': media_info.get('title', f'{platform.title()} Media'),
                        'duration': 0,
                        'thumbnail': None,
                        'local_thumbnail': None,
                        'uploader': platform.title(),
                        'id': get_url_hash(url)[:8],
                        'platform': platform,
                        'content_type': media_info['type'],
                        'timestamp': time.time(),
                        'source': 'direct',
                        'direct_url': media_info['url']
                    }
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to extract info: {e}")
        return None

async def process_spotify_url(url: str) -> Optional[Dict]:
    """Process Spotify URL and return a YouTube search query and filename"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        url_lower = url.lower()

        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code != 200:
            return None

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        title_tag = soup.find('meta', property='og:title')
        desc_tag = soup.find('meta', property='og:description')

        title_text = (title_tag.get('content') if title_tag else '') or ''
        desc_text = (desc_tag.get('content') if desc_tag else '') or ''

        artist = ""
        track_name = ""
        search_query = None
        filename = None
        full_title = None

        def clean_text(text: str) -> str:
            t = re.sub(r'\s*\(.*?\)\s*', '', text or '').strip()
            t = re.sub(r'\s+', ' ', t)
            return t

        if '/track/' in url_lower:
            if ' • ' in title_text:
                track_name, artist = title_text.split(' • ', 1)
            elif ' - ' in title_text:
                temp_a, temp_t = title_text.split(' - ', 1)
                artist, track_name = temp_a, temp_t
            else:
                track_name = title_text

            if (not artist or not track_name):
                for script in soup.find_all('script', type='application/ld+json'):
                    try:
                        data = json.loads(script.string or '{}')
                        if data.get('@type') == 'MusicRecording':
                            track_name = track_name or data.get('name', '')
                            by_artist = data.get('byArtist')
                            if isinstance(by_artist, dict):
                                artist = artist or by_artist.get('name', '')
                            elif isinstance(by_artist, list) and by_artist:
                                artist = artist or by_artist[0].get('name', '')
                    except Exception:
                        continue

            artist = clean_text(artist)
            track_name = clean_text(track_name)

            if artist:
                search_query = f"ytsearch1:{track_name} {artist}"
                filename = f"{artist} - {track_name}"
                full_title = filename
            else:
                search_query = f"ytsearch1:{track_name}"
                filename = track_name or 'Spotify Track'
                full_title = filename

        elif '/artist/' in url_lower:
            artist = clean_text(title_text or desc_text.split(' · ')[0] if ' · ' in desc_text else title_text)
            if not artist:
                return None
            search_query = f"ytsearch1:best song {artist}"
            filename = f"{artist} - Best Of"
            full_title = filename

        elif '/album/' in url_lower:
            album_title = clean_text(title_text)
            possible_artist = desc_text.split(' · ')[0] if ' · ' in desc_text else ''
            artist = clean_text(possible_artist)
            if artist:
                search_query = f"ytsearch1:{album_title} {artist} full album"
                filename = f"{artist} - {album_title}"
                full_title = filename
            else:
                search_query = f"ytsearch1:{album_title} full album"
                filename = album_title
                full_title = filename

        elif '/playlist/' in url_lower:
            pl_title = clean_text(title_text or 'Spotify Playlist')
            search_query = f"ytsearch1:{pl_title} playlist"
            filename = pl_title
            full_title = pl_title

        else:
            return None

        return {
            'search_query': search_query,
            'artist': artist or 'Unknown Artist',
            'track_name': track_name or 'Unknown Track',
            'filename': filename or 'Spotify Audio',
            'full_title': full_title or filename or 'Spotify Audio'
        }

    except Exception as e:
        logger.error(f"Spotify processing error: {e}")
        return None

def cleanup_file(file_path: str):
    """Clean up downloaded files"""
    try:
        if file_path and os.path.exists(file_path):
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                import shutil
                shutil.rmtree(file_path)
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")

async def send_media_file(recipient_id: str, file_path: str, title: str, content_type: str):
    """Send media file to user"""
    try:
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            messenger.send_message("❌ File too large (max 50MB)", recipient_id)
            cleanup_file(file_path)
            return
        
        size_mb = file_size / (1024 * 1024)
        
        try:
            safe_title = re.sub(r'[^\w\s\-_.]', '', title)[:100]
            
            if content_type == 'image':
                caption = f"📷 {safe_title}\n\n✅ Image • {size_mb:.1f}MB"
                result = messenger.send_media(
                    media_path=file_path,
                    recipient_id=recipient_id,
                    media_type='image',
                    caption=caption
                )
            elif content_type == 'audio':
                caption = f"🎵 {safe_title}\n\n✅ Audio • {size_mb:.1f}MB"
                result = messenger.send_media(
                    media_path=file_path,
                    recipient_id=recipient_id,
                    media_type='audio',
                    caption=caption
                )
            else:
                caption = f"🎬 {safe_title}\n\n✅ Video • {size_mb:.1f}MB"
                result = messenger.send_media(
                    media_path=file_path,
                    recipient_id=recipient_id,
                    media_type='video',
                    caption=caption
                )
            
            if not result.get('success'):
                messenger.send_message(f"❌ Failed to send file: {result.get('error', 'Unknown error')}", recipient_id)
            
        except Exception as e:
            logger.error(f"Send file error: {e}")
            messenger.send_message("❌ Failed to send file", recipient_id)
        
        finally:
            cleanup_file(file_path)
            
    except Exception as e:
        logger.error(f"File send process error: {e}")
        cleanup_file(file_path)

async def send_instagram_media_group(recipient_id: str, media_data: Dict):
    """Send Instagram media as a single grouped message with proper deduplication"""
    try:
        media_files = media_data['media_files']
        title = media_data['title']
        
        # Track sent media to prevent duplicates using file hashes
        sent_media_hashes = set()
        media_to_send: List[Dict] = []
        
        # First, collect all unique media files
        for i, media_file in enumerate(media_files[:5]):  # Limit to 5 media files
            file_path = media_file['path']
            media_type = media_file['type']
            
            # Skip if file doesn't exist
            if not os.path.exists(file_path):
                logger.debug(f"Skipping non-existent media: {file_path}")
                continue
            
            # Check if we've already processed this file using file hash
            try:
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                if file_hash in sent_media_hashes:
                    logger.debug(f"Skipping duplicate media: {file_path}")
                    continue
                sent_media_hashes.add(file_hash)
            except Exception as e:
                logger.warning(f"Could not hash file {file_path}: {e}")
                # Continue anyway but with less reliable deduplication
            
            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE:
                logger.warning(f"Skipping large file: {file_path} ({file_size} bytes)")
                continue
                
            media_to_send.append({
                'path': file_path,
                'type': media_type,
                'size_mb': file_size / (1024 * 1024)
            })
        
        if not media_to_send:
            messenger.send_message("❌ No valid media files to send", recipient_id)
            return
        
        # Send all media files with a single introductory message for carousel posts
        if len(media_to_send) > 1:
            # For carousel posts, send a summary message first
            messenger.send_message(f"📸 Instagram Carousel: {title}\n\n✅ Sending {len(media_to_send)} media items...", recipient_id)
        elif len(media_to_send) == 1:
            # For single media, send a descriptive message
            media_type = media_to_send[0]['type']
            size_mb = media_to_send[0]['size_mb']
            messenger.send_message(f"📷 {title}\n\n✅ {media_type.title()} • {size_mb:.1f}MB", recipient_id)
        
        # Send each media file with minimal delay
        for i, media_item in enumerate(media_to_send):
            try:
                file_path = media_item['path']
                media_type = media_item['type']
                size_mb = media_item['size_mb']
                
                # For carousel posts, add part indicator only if there are multiple items
                if len(media_to_send) > 1:
                    caption = f"Part {i+1}/{len(media_to_send)}"
                else:
                    caption = f"📷 {title}\n\n✅ {media_type.title()} • {size_mb:.1f}MB"
                
                result = messenger.send_media(
                    media_path=file_path,
                    recipient_id=recipient_id,
                    media_type=media_type,
                    caption=caption
                )
                
                if not result.get('success'):
                    logger.error(f"Failed to send Instagram media {i+1}: {result.get('error', 'Unknown error')}")
                else:
                    logger.info(f"Successfully sent Instagram media {i+1}: {file_path}")
                
                # Small delay between sends to prevent rate limiting
                if i < len(media_to_send) - 1:  # No delay after the last item
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Error sending media {i+1}: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Instagram media group send error: {e}")
        messenger.send_message("❌ Failed to process media group", recipient_id)
    
    finally:
        # Clean up temporary files
        if 'temp_dir' in media_data and os.path.exists(media_data['temp_dir']):
            import shutil
            shutil.rmtree(media_data['temp_dir'], ignore_errors=True)

async def handle_link(recipient_id: str, url: str):
    """Handle incoming links with intelligent processing"""
    # Check if we've already processed this URL
    url_key = f"{recipient_id}:{get_url_hash(url)}"
    if url_key in processed_urls:
        logger.info(f"Skipping duplicate URL for user {recipient_id}: {url}")
        messenger.send_message("✅ This content has already been processed.", recipient_id)
        return
    
    # Add to processed URLs
    processed_urls.add(url_key)
    
    # Normalize YouTube Shorts URLs properly
    if 'youtube.com/shorts/' in url:
        normalized_url = normalize_youtube_shorts_url(url)
        logger.info(f"🔄 Normalized YouTube Shorts URL: {url} -> {normalized_url}")
        url = normalized_url
    
    if not url.startswith(('http://', 'https://')):
        messenger.send_message("❌ Invalid URL\n\nPlease send a valid link starting with http:// or https://", recipient_id)
        return
    
    if not is_supported_url(url):
        messenger.send_message(
            "❌ Unsupported Platform\n\nSupported platforms:\n🎬 YouTube\n📱 Instagram\n🧵 Threads\n🎵 Spotify\n🎪 TikTok\n🐦 Twitter/X\n📘 Facebook\n📌 Pinterest",
            recipient_id
        )
        return
    
    platform = detect_platform(url)
    url_hash = get_url_hash(url)
    
    logger.info(f"📥 Processing {platform} URL from user {recipient_id}: {url}")
    
    messenger.send_message(f"🔄 Processing {platform.title()} link...", recipient_id)
    
    try:
        if platform == 'spotify':
            messenger.send_message("🎵 Processing Spotify track...", recipient_id)
            spotify_metadata = await process_spotify_url(url)
            if spotify_metadata:
                messenger.send_message(f"🎵 Downloading: {spotify_metadata['full_title']}", recipient_id)
                await download_and_send_spotify(recipient_id, spotify_metadata)
            else:
                messenger.send_message("❌ Could not process Spotify link\n\nMake sure the link is a valid Spotify track.", recipient_id)
            return
        
        if platform == 'instagram':
            messenger.send_message("📷 Processing Instagram content...", recipient_id)
            
            # Track if we've already processed this Instagram content to prevent duplicate sends
            processed_content = False
            
            url_lower = url.lower()
            is_video_link = '/reel/' in url_lower or '/reels/' in url_lower
            is_post_link = '/p/' in url_lower
            
            if is_post_link:
                try:
                    messenger.send_message("🔍 Analyzing Instagram post...", recipient_id)
                    
                    if is_video_link:
                        try:
                            base_opts = {
                                'quiet': True,
                                'no_warnings': True,
                                'extract_flat': False,
                                'skip_download': True,
                                'socket_timeout': 10,
                                'retries': 1,
                                'http_headers': {
                                    'User-Agent': USER_AGENTS['instagram']
                                }
                            }
                            
                            ydl_opts = instagram_auth.get_ytdl_opts(base_opts)
                            logger.debug("🔄 Using authenticated yt-dlp for Instagram video metadata extraction")
                            
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                info = ydl.extract_info(url, download=False)
                                
                                messenger.send_message("⚡ Downloading Instagram video...", recipient_id)
                                file_path = await download_media(url, None, False, {'platform': 'instagram'})
                                if file_path:
                                    await send_media_file(recipient_id, file_path, info.get('title', 'Instagram Video'), 'video')
                                    processed_content = True
                                else:
                                    raise Exception("yt-dlp download failed")
                                return
                                
                        except Exception as e:
                            logger.debug(f"Instagram video link processing error: {e}")
                            if not processed_content:
                                messenger.send_message("🔄 Trying alternative download method...", recipient_id)
                            
                            try:
                                file_path = await download_media(url, None, False, {'platform': 'instagram'})
                                if file_path:
                                    await send_media_file(recipient_id, file_path, 'Instagram Video', 'video')
                                    processed_content = True
                                else:
                                    raise Exception("yt-dlp direct download failed")
                                return
                            except Exception as fallback_error:
                                logger.debug(f"Instagram yt-dlp fallback failed: {fallback_error}")
                                
                                if not processed_content:
                                    try:
                                        messenger.send_message("🔄 Trying alternative download method...", recipient_id)
                                        instagram_data = await download_instagram_media(url)
                                        if instagram_data:
                                            await send_instagram_media_group(recipient_id, instagram_data)
                                            processed_content = True
                                        else:
                                            messenger.send_message("❌ Could not download Instagram video\n\nThe content might be private or deleted.", recipient_id)
                                    except Exception as final_error:
                                        logger.debug(f"Instagram instaloader fallback failed: {final_error}")
                                        if not processed_content:
                                            messenger.send_message("❌ Instagram download failed\n\nThe content might be private or deleted.", recipient_id)
                                return
                    else:
                        try:
                            base_opts = {
                                'quiet': True,
                                'no_warnings': True,
                                'extract_flat': False,
                                'skip_download': True,
                                'socket_timeout': 10,
                                'retries': 1,
                                'http_headers': {
                                    'User-Agent': USER_AGENTS['instagram']
                                }
                            }
                            
                            ydl_opts = instagram_auth.get_ytdl_opts(base_opts)
                            logger.debug("🔄 Using authenticated yt-dlp for Instagram post metadata extraction")
                            
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                info = ydl.extract_info(url, download=False)
                                
                                formats = info.get('formats', [])
                                has_video = any(f.get('vcodec', 'none') != 'none' for f in formats)
                                
                                if has_video:
                                    messenger.send_message("⚡ Downloading Instagram video...", recipient_id)
                                    file_path = await download_media(url, None, False, {'platform': 'instagram'})
                                    if file_path:
                                        await send_media_file(recipient_id, file_path, info.get('title', 'Instagram Video'), 'video')
                                        processed_content = True
                                    else:
                                        raise Exception("yt-dlp download failed")
                                    return
                                else:
                                    messenger.send_message("📥 Downloading Instagram image...", recipient_id)
                                    file_path = await download_media(url, None, False, {'platform': 'instagram', 'silent': True})
                                    if file_path:
                                        await send_media_file(recipient_id, file_path, info.get('title', 'Instagram Image'), 'image')
                                        processed_content = True
                                    else:
                                        raise Exception("yt-dlp download failed")
                                    return
                                    
                        except Exception as e:
                            error_str = str(e).lower()
                            logger.debug(f"Instagram yt-dlp processing error: {e}")
                            
                            if not processed_content:
                                try:
                                    instagram_data = await download_instagram_media(url)
                                    if instagram_data:
                                        await send_instagram_media_group(recipient_id, instagram_data)
                                        processed_content = True
                                    else:
                                        try:
                                            file_path = await download_media(url, None, False, {'platform': 'instagram', 'no_auth': True})
                                            if file_path:
                                                await send_media_file(recipient_id, file_path, 'Instagram Content', 'mixed')
                                                processed_content = True
                                            else:
                                                messenger.send_message("❌ Could not download Instagram content\n\nThe content might be private or deleted.", recipient_id)
                                        except Exception as final_error:
                                            logger.debug(f"Instagram final fallback error: {final_error}")
                                            if not processed_content:
                                                messenger.send_message("❌ Could not download Instagram content\n\nThe content might be private or deleted.", recipient_id)
                                except Exception as fallback_error:
                                    logger.debug(f"Instagram instaloader fallback error: {fallback_error}")
                                    if not processed_content:
                                        try:
                                            file_path = await download_media(url, None, False, {'platform': 'instagram', 'no_auth': True})
                                            if file_path:
                                                await send_media_file(recipient_id, file_path, 'Instagram Content', 'mixed')
                                                processed_content = True
                                            else:
                                                messenger.send_message("❌ Instagram download failed\n\nThe content might be private or deleted.", recipient_id)
                                        except Exception as final_error:
                                            logger.debug(f"Instagram final fallback error: {final_error}")
                                            if not processed_content:
                                                messenger.send_message("❌ Instagram download failed\n\nThe content might be private or deleted.", recipient_id)
                            return
                except Exception as detection_error:
                    logger.debug(f"Post type detection failed, continuing with normal flow: {detection_error}")
            
            return
        
        if platform == 'threads':
            messenger.send_message("🧵 Processing Threads content...", recipient_id)
            
            try:
                base_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                    'skip_download': True,
                    'socket_timeout': 10,
                    'retries': 1,
                    'http_headers': {
                        'User-Agent': USER_AGENTS.get('instagram', USER_AGENTS['default'])
                    }
                }
                
                ydl_opts = instagram_auth.get_ytdl_opts(base_opts)
                logger.debug("🔄 Using Instagram authentication for Threads content extraction")
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    formats = info.get('formats', [])
                    has_video = any(f.get('vcodec', 'none') != 'none' for f in formats)
                    
                    if has_video:
                        messenger.send_message("⚡ Downloading Threads video...", recipient_id)
                        file_path = await download_media(url, None, False, {'platform': 'threads'})
                        if file_path:
                            await send_media_file(recipient_id, file_path, info.get('title', 'Threads Video'), 'video')
                        else:
                            raise Exception("yt-dlp download failed")
                        return
                    else:
                        messenger.send_message("⚡ Downloading Threads image...", recipient_id)
                        file_path = await download_media(url, None, False, {'platform': 'threads'})
                        if file_path:
                            await send_media_file(recipient_id, file_path, info.get('title', 'Threads Image'), 'image')
                        else:
                            raise Exception("yt-dlp download failed")
                        return
                        
            except Exception as e:
                logger.debug(f"Threads yt-dlp processing error: {e}")
                
                try:
                    messenger.send_message("🔄 Trying Instagram fallback method...", recipient_id)
                    logger.info("🧵 Attempting Threads fallback using Instagram downloader")
                    instagram_data = await download_instagram_media(url)
                    if instagram_data:
                        logger.info("🧵 Successfully downloaded Threads content using Instagram method")
                        await send_instagram_media_group(recipient_id, instagram_data)
                        return
                    logger.debug("🧵 Instagram fallback method failed for Threads")
                except Exception as instagram_fallback_error:
                    logger.debug(f"Threads Instagram fallback error: {instagram_fallback_error}")
                
                try:
                    messenger.send_message("🔄 Trying basic extraction...", recipient_id)
                    logger.info("🧵 Attempting Threads fallback using basic yt-dlp")
                    file_path = await download_media(url, None, False, {'platform': 'threads', 'no_auth': True})
                    if file_path:
                        logger.info("🧵 Successfully downloaded Threads content using basic method")
                        await send_media_file(recipient_id, file_path, 'Threads Content', 'mixed')
                        return
                    logger.debug("🧵 Basic yt-dlp method failed for Threads")
                except Exception as basic_fallback_error:
                    logger.debug(f"Threads basic fallback error: {basic_fallback_error}")
                
                try:
                    messenger.send_message("🔄 Trying direct extraction...", recipient_id)
                    logger.info("🧵 Attempting Threads fallback using direct extraction")
                    media_info = await extract_direct_media_url(url, 'threads')
                    if media_info:
                        file_path = await download_direct_media(media_info['url'], 'threads')
                        if file_path:
                            logger.info("🧵 Successfully downloaded Threads content using direct method")
                            await send_media_file(recipient_id, file_path, media_info.get('title', 'Threads Content'), media_info.get('type', 'mixed'))
                            return
                    logger.debug("🧵 Direct extraction method failed for Threads")
                except Exception as direct_fallback_error:
                    logger.debug(f"Threads direct fallback error: {direct_fallback_error}")
                
                logger.warning(f"🧵 All Threads fallback methods failed for URL: {url}")
                messenger.send_message("❌ Could not download Threads content\n\nThe content might be private, deleted, or not supported. Threads content sometimes requires being logged in to the platform.", recipient_id)
            return
        
        info = await get_media_info(url)
        
        if not info:
            messenger.send_message(
                f"⚠️ Could not fetch media info from {platform.title()}\n\nTrying direct download method...",
                recipient_id
            )
            
            media_info = await extract_direct_media_url(url, platform)
            if media_info:
                messenger.send_message("⚡ Downloading content directly...", recipient_id)
                file_path = await download_direct_media(media_info['url'], platform)
                if file_path:
                    await send_media_file(recipient_id, file_path, media_info['title'], media_info['type'])
                else:
                    messenger.send_message(f"❌ Download failed\n\nCould not download content from {platform.title()}.", recipient_id)
            else:
                messenger.send_message(f"❌ Could not process this {platform.title()} link\n\nThe content might be private or unsupported.", recipient_id)
            return
        
        content_type = info.get('content_type', 'mixed')
        
        if content_type == 'image':
            messenger.send_message("📥 Downloading image...", recipient_id)
            file_path = await download_media(url, info=info)
            if file_path:
                await send_media_file(recipient_id, file_path, info['title'], 'image')
            else:
                messenger.send_message("❌ Download failed", recipient_id)
        elif content_type == 'audio':
            messenger.send_message("🎵 Downloading audio...", recipient_id)
            file_path = await download_media(url, audio_only=True, info=info)
            if file_path:
                await send_media_file(recipient_id, file_path, info['title'], 'audio')
            else:
                messenger.send_message("❌ Download failed", recipient_id)
        else:
            messenger.send_message("⚡ Downloading video...", recipient_id)
            file_path = await download_media(url, info=info)
            if file_path:
                await send_media_file(recipient_id, file_path, info['title'], 'video')
            else:
                messenger.send_message("❌ Download failed", recipient_id)
    
    except Exception as e:
        logger.error(f"Link processing error: {e}")
        error_msg = f"❌ Processing failed\n\nError processing {platform.title()} link. Please try again or use a different link."
        messenger.send_message(error_msg, recipient_id)

async def download_and_send_spotify(recipient_id: str, spotify_metadata: Dict):
    """Handle Spotify download and send with proper filename"""
    try:
        # Fix the function call - remove the filename parameter which doesn't exist
        file_path = await download_media(
            spotify_metadata['search_query'], 
            audio_only=True
        )
        
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE:
                messenger.send_message("❌ File too large (max 50MB)", recipient_id)
                cleanup_file(file_path)
                return
            
            messenger.send_message("📤 Sending...", recipient_id)
            
            try:
                safe_title = re.sub(r'[^\w\s\-_.]', '', spotify_metadata['full_title'])[:100]
                size_mb = file_size / (1024 * 1024)
                caption = f"🎵 {safe_title}\n\n✅ 320kbps MP3 • {size_mb:.1f}MB"
                result = messenger.send_media(
                    media_path=file_path,
                    recipient_id=recipient_id,
                    media_type='audio',
                    caption=caption
                )
                
                if not result.get('success'):
                    messenger.send_message(f"❌ Failed to send file: {result.get('error', 'Unknown error')}", recipient_id)
                    
            except Exception:
                messenger.send_message("❌ Failed to send file", recipient_id)
            finally:
                cleanup_file(file_path)
        else:
            messenger.send_message("❌ Download failed", recipient_id)
    except Exception as e:
        logger.error(f"Spotify download error: {e}")
        messenger.send_message("❌ Download failed", recipient_id)

def process_message(recipient_id: str, text: str):
    """Process incoming WhatsApp messages"""
    if text.lower() in ['help', 'start']:
        welcome_text = "🚀 Ultra-Fast Media Downloader\n\n"
        welcome_text += "Download from YouTube, Instagram, TikTok, Spotify, Twitter, Facebook and more!\n\n"
        welcome_text += "✨ Features:\n"
        welcome_text += "• HD Video Quality (up to 1080p)\n"
        welcome_text += "• High-Quality Audio (320kbps)\n"
        welcome_text += "• Image & Post Download\n"
        welcome_text += "• No Watermarks\n"
        welcome_text += "• Lightning Fast Download\n\n"
        welcome_text += "Just send any social media link and I'll handle the rest automatically! ✨"
        messenger.send_message(welcome_text, recipient_id)
        return
    
    url_pattern = re.compile(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?')
    urls = url_pattern.findall(text)
    
    if urls:
        url = urls[0]
        asyncio.run(handle_link(recipient_id, url))
        return
    
    messenger.send_message("💡 Tip\n\nSend a social media link to download content, or type *help* for more information!", recipient_id)

def verify_webhook(mode: str, token: str, challenge: str):
    """Verify webhook subscription"""
    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info('✅ Webhook verified successfully!')
            return challenge
        else:
            logger.error('❌ Webhook verification failed!')
            return 'Verification failed', 403
    return 'Bad Request', 400

def main():
    """Main function to test the WhatsApp bot"""
    logger.info("🚀 Starting Ultra-Fast Media Downloader WhatsApp Bot...")
    
    ensure_directories()
    
    logger.info("✅ WhatsApp Bot is ready!")
    logger.info("📱 Supported: YouTube, Instagram, TikTok, Spotify, Twitter, Facebook")
    
    test_url = "https://www.instagram.com/reel/DOL69CdDPbm/?igsh=a2IxcHUwd3gwcG11"
    logger.info("🧪 Testing with Instagram reel URL...")
    process_message("test_user", test_url)

if __name__ == "__main__":
    main()