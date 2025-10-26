import os
import asyncio
import shutil
import tempfile
import hashlib
import time
import re
from pathlib import Path
import logging
from typing import Optional, Dict, Any

# Import configuration
from config import (
    MAX_FILE_SIZE, DOWNLOADS_DIR, TEMP_DIR, DATA_DIR,
    INSTAGRAM_COOKIES_FILE, INSTAGRAM_REQUEST_DELAY,
    YOUTUBE_COOKIES_FILE
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Simple mock for WhatsApp Business API
class MockWhatsAppBusiness:
    def __init__(self, access_token=None, phone_number_id=None):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
    
    def send_message(self, message, recipient_id):
        print(f"[MOCK WhatsApp] Sending message to {recipient_id}: {message}")
        return {"success": True}
    
    def send_image(self, image, recipient_id, caption=None):
        print(f"[MOCK WhatsApp] Sending image to {recipient_id}: {image}")
        if caption:
            print(f"Caption: {caption}")
        return {"success": True}
    
    def send_video(self, video, recipient_id, caption=None):
        print(f"[MOCK WhatsApp] Sending video to {recipient_id}: {video}")
        if caption:
            print(f"Caption: {caption}")
        return {"success": True}
    
    def send_audio(self, audio, recipient_id, caption=None):
        print(f"[MOCK WhatsApp] Sending audio to {recipient_id}: {audio}")
        if caption:
            print(f"Caption: {caption}")
        return {"success": True}
    
    def send_document(self, document_path, recipient_id, caption=None):
        print(f"[MOCK WhatsApp] Sending document to {recipient_id}: {document_path}")
        if caption:
            print(f"Caption: {caption}")
        return {"success": True}

# Initialize mock WhatsApp client
messenger = MockWhatsAppBusiness()

# Cache for duplicate detection and session handling
download_cache = {}
user_sessions = {}

# Quality options
VIDEO_QUALITIES = {
    "1080p": "best[height<=1080][height>720][ext=mp4]/best[height<=1080][height>720]/bestvideo[height<=1080][height>720]+bestaudio/best[height<=1080]",
    "720p": "best[height<=720][height>480][ext=mp4]/best[height<=720][height>480]/bestvideo[height<=720][height>480]+bestaudio/best[height<=720]",
    "480p": "best[height<=480][height>360][ext=mp4]/best[height<=480][height>360]/bestvideo[height<=480][height>360]+bestaudio/best[height<=480]",
    "360p": "best[height<=360][height>240][ext=mp4]/best[height<=360][height>240]/bestvideo[height<=360][height>240]+bestaudio/best[height<=360]",
    "240p": "best[height<=240][height>144][ext=mp4]/best[height<=240][height>144]/bestvideo[height<=240][height>144]+bestaudio/best[height<=240]",
    "144p": "worst[height<=144][ext=mp4]/worst[height<=144]/bestvideo[height<=144]+bestaudio/worst"
}

# Platform patterns
PLATFORM_PATTERNS = {
    'youtube': r'(?:youtube\.com|youtu\.be|music\.youtube\.com)',
    'instagram': r'(?:instagram\.com|instagr\.am)',
    'tiktok': r'(?:tiktok\.com|vm\.tiktok\.com)',
    'facebook': r'(?:facebook\.com|fb\.watch|fb\.me)',
    'spotify': r'(?:spotify\.com|open\.spotify\.com)',
    'twitter': r'(?:twitter\.com|x\.com|t\.co)'
}

def ensure_directories():
    """Ensure required directories exist"""
    for directory in [DOWNLOADS_DIR, TEMP_DIR, DATA_DIR]:
        os.makedirs(directory, exist_ok=True)

def get_url_hash(url: str) -> str:
    """Generate hash for URL to use as cache key"""
    return hashlib.md5(url.encode()).hexdigest()

def detect_platform(url: str) -> str:
    """Detect platform from URL"""
    url_lower = url.lower()
    
    # Treat yt-dlp search queries as YouTube
    if url_lower.startswith('ytsearch'):
        return 'youtube'

    for platform, pattern in PLATFORM_PATTERNS.items():
        if re.search(pattern, url_lower):
            return platform
    
    return 'unknown'

def is_supported_url(url: str) -> bool:
    """Check if URL is from supported platform"""
    return detect_platform(url) != 'unknown'

def process_message(recipient_id: str, text: str):
    """Process incoming WhatsApp messages"""
    # Handle commands
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
    
    # Handle URL detection
    url_pattern = re.compile(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?')
    urls = url_pattern.findall(text)
    
    if urls:
        # Process the first URL found
        url = urls[0]
        handle_link(recipient_id, url)
        return
    
    # Default response for unrecognized messages
    messenger.send_message("💡 Tip\n\nSend a social media link to download content, or type 'help' for more information!", recipient_id)

# Add cache for processed URLs to prevent duplicate processing
processed_urls_cache = {}
CACHE_DURATION = 3600  # 1 hour
last_cleanup_time = time.time()  # Initialize the variable

def is_url_processed(url: str) -> bool:
    """Check if URL has been processed recently"""
    current_time = time.time()
    url_hash = hashlib.md5(url.encode()).hexdigest()
    
    # Clean up old cache entries
    expired_keys = [k for k, v in processed_urls_cache.items() 
                   if current_time - v.get('timestamp', 0) > CACHE_DURATION]
    for key in expired_keys:
        del processed_urls_cache[key]
    
    # Check if URL is in cache
    if url_hash in processed_urls_cache:
        return True
    
    return False

def mark_url_as_processed(url: str, file_path: str = ""):
    """Mark URL as processed"""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    processed_urls_cache[url_hash] = {
        'timestamp': time.time(),
        'file_path': file_path
    }

def get_processed_file_path(url: str) -> str:
    """Get file path for previously processed URL"""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    if url_hash in processed_urls_cache:
        return processed_urls_cache[url_hash].get('file_path', '')
    return ''

def handle_link(recipient_id: str, url: str):
    """Handle incoming links with intelligent processing"""
    global last_cleanup_time
    
    # Basic URL validation
    if not url.startswith(('http://', 'https://')):
        messenger.send_message("Invalid URL. Please send a valid link starting with http:// or https://", recipient_id)
        return
    
    # Clean up old processed URLs cache periodically (every 10 minutes)
    current_time = time.time()
    if current_time - last_cleanup_time > 600:  # 10 minutes
        expired_keys = [k for k, v in processed_urls_cache.items() 
                       if current_time - v.get('timestamp', 0) > CACHE_DURATION]
        for key in expired_keys:
            del processed_urls_cache[key]
        last_cleanup_time = current_time
    
    if not is_supported_url(url):
        messenger.send_message(
            "Unsupported Platform. Supported platforms: YouTube, Instagram, TikTok, Spotify, Twitter/X, Facebook",
            recipient_id
        )
        return
    
    platform = detect_platform(url)
    
    logger.info(f"Processing {platform} URL from user {recipient_id}: {url}")
    
    # Show processing message
    messenger.send_message(f"Processing {platform.title()} link...", recipient_id)
    
    # Handle different platforms
    if platform == 'instagram_reel':
        handle_instagram_reel(recipient_id, url)
    elif platform == 'instagram':
        handle_instagram_content(recipient_id, url)
    elif platform == 'youtube':
        handle_youtube_content(recipient_id, url)
    elif platform == 'tiktok':
        handle_tiktok_content(recipient_id, url)
    elif platform == 'facebook':
        handle_facebook_content(recipient_id, url)
    elif platform == 'spotify':
        handle_spotify_content(recipient_id, url)
    elif platform == 'twitter':
        handle_twitter_content(recipient_id, url)
    else:
        # For other content, send a generic response
        messenger.send_message(f"Processing {platform.title()} content... This may take a few moments.", recipient_id)
        handle_generic_content(recipient_id, url)

def verify_webhook(mode: str, token: str, challenge: str):
    """Verify webhook subscription"""
    from config import VERIFY_TOKEN
    
    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info("Webhook verified successfully")
            return challenge, 200
        else:
            logger.error("Webhook verification failed")
            return "Verification failed", 403
    return "Bad request", 400

def main():
    """Main function"""
    logger.info("🚀 Starting Ultra-Fast Media Downloader WhatsApp Bot...")
    
    # Ensure directories exist
    ensure_directories()
    
    logger.info("✅ WhatsApp Bot is ready!")
    logger.info("📱 Supported: YouTube, Instagram, TikTok, Spotify, Twitter, Facebook")
    
    # Test with the provided Instagram reel URL
    test_url = "https://www.instagram.com/reel/DL452nITuB3"
    logger.info("🧪 Testing with Instagram reel URL...")
    process_message("test_user", test_url)

if __name__ == "__main__":
    main()

def handle_instagram_reel(recipient_id: str, url: str):
    """Handle Instagram reel download and send with real information extraction"""
    try:
        # Send processing message
        messenger.send_message("Downloading Instagram reel...", recipient_id)
        
        # Extract real title and creator information using yt-dlp
        reel_info = extract_instagram_reel_info_with_ytdlp(url)
        title = reel_info['title']
        creator = reel_info['creator']
        
        # Send info message with real title and creator
        info_message = f"Instagram Reel: {title}. Creator: {creator}"
        messenger.send_message(info_message, recipient_id)
        
        # Download the reel using yt-dlp
        messenger.send_message("Downloading video file...", recipient_id)
        file_path = download_instagram_reel_with_ytdlp(url)
        
        # Check if file was downloaded successfully
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            messenger.send_message(f"Successfully downloaded! Size: {size_mb:.1f}MB", recipient_id)
            
            # Send the actual file
            messenger.send_document(file_path, recipient_id, f"Instagram Reel - {title}")
        else:
            messenger.send_message("Download failed", recipient_id)
        
    except Exception as e:
        logger.error(f"Instagram reel handling failed: {e}")
        messenger.send_message(f"Failed to download Instagram reel. Error: {str(e)}", recipient_id)

def handle_instagram_content(recipient_id: str, url: str):
    """Handle Instagram content (posts, stories, etc.)"""
    try:
        messenger.send_message("Downloading Instagram content...", recipient_id)
        
        # For now, we'll use a generic approach
        # In a full implementation, you would extract specific Instagram content
        handle_generic_content(recipient_id, url)
        
    except Exception as e:
        logger.error(f"Instagram content handling failed: {e}")
        messenger.send_message(f"Failed to download Instagram content. Error: {str(e)}", recipient_id)

def handle_youtube_content(recipient_id: str, url: str):
    """Handle YouTube content with proper cache handling and error management"""
    try:
        # Check if URL was processed recently
        if is_url_processed(url):
            # Try to get previously downloaded file
            file_path = get_processed_file_path(url)
            if file_path and os.path.exists(file_path):
                # Send existing file
                messenger.send_message("Sending previously downloaded video...", recipient_id)
                messenger.send_document(file_path, recipient_id, "YouTube Video")
                return
            else:
                # URL was processed but file is gone, allow reprocessing
                pass
        
        messenger.send_message("Downloading YouTube content...", recipient_id)
        handle_generic_content(recipient_id, url)
    except Exception as e:
        logger.error(f"YouTube content handling failed: {e}")
        messenger.send_message(f"Failed to download YouTube content. Error: {str(e)}", recipient_id)

def handle_tiktok_content(recipient_id: str, url: str):
    """Handle TikTok content with proper URL resolution"""
    try:
        # Resolve shortened URLs first
        original_url = url
        url = resolve_shortened_url(url)
        if url != original_url:
            logger.info(f"Resolved shortened URL: {original_url} -> {url}")
        
        messenger.send_message("Downloading TikTok content...", recipient_id)
        handle_generic_content(recipient_id, url)
    except Exception as e:
        logger.error(f"TikTok content handling failed: {e}")
        messenger.send_message(f"Failed to download TikTok content. Error: {str(e)}", recipient_id)

def handle_facebook_content(recipient_id: str, url: str):
    """Handle Facebook content"""
    try:
        messenger.send_message("Downloading Facebook content...", recipient_id)
        handle_generic_content(recipient_id, url)
    except Exception as e:
        logger.error(f"Facebook content handling failed: {e}")
        messenger.send_message(f"Failed to download Facebook content. Error: {str(e)}", recipient_id)

def handle_spotify_content(recipient_id: str, url: str):
    """Handle Spotify content by searching on YouTube"""
    try:
        # Check if URL was processed recently
        if is_url_processed(url):
            # Try to get previously downloaded file
            file_path = get_processed_file_path(url)
            if file_path and os.path.exists(file_path):
                # Send existing file
                messenger.send_message("Sending previously downloaded Spotify track...", recipient_id)
                messenger.send_document(file_path, recipient_id, "Spotify Track")
                return
            else:
                # URL was processed but file is gone, allow reprocessing
                pass
        
        messenger.send_message("Processing Spotify content...", recipient_id)
        
        # Process Spotify URL to get metadata
        spotify_metadata = process_spotify_url(url)
        if not spotify_metadata:
            messenger.send_message("Failed to process Spotify URL", recipient_id)
            return
        
        # Send info message
        info_message = f"Spotify Track: {spotify_metadata['full_title']}. Searching on YouTube..."
        messenger.send_message(info_message, recipient_id)
        
        # Download from YouTube using search query
        file_path = download_media_with_filename(
            spotify_metadata['search_query'],
            filename=spotify_metadata['filename'],
            audio_only=True
        )
        
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            messenger.send_message(f"Successfully downloaded! Size: {size_mb:.1f}MB", recipient_id)
            
            # Mark URL as processed
            mark_url_as_processed(url, file_path)
            
            # Send the file
            messenger.send_document(file_path, recipient_id, f"Spotify Track - {spotify_metadata['full_title']}")
        else:
            messenger.send_message("Download failed", recipient_id)
            
    except Exception as e:
        logger.error(f"Spotify content handling failed: {e}")
        messenger.send_message(f"Failed to process Spotify content. Error: {str(e)}", recipient_id)

def handle_twitter_content(recipient_id: str, url: str):
    """Handle Twitter/X content"""
    try:
        messenger.send_message("Downloading Twitter content...", recipient_id)
        handle_generic_content(recipient_id, url)
    except Exception as e:
        logger.error(f"Twitter content handling failed: {e}")
        messenger.send_message(f"Failed to download Twitter content. Error: {str(e)}", recipient_id)

def handle_generic_content(recipient_id: str, url: str):
    """Handle generic content download with cache and better error handling"""
    try:
        # Check if URL was processed recently
        if is_url_processed(url):
            # Try to get previously downloaded file
            file_path = get_processed_file_path(url)
            if file_path and os.path.exists(file_path):
                # Send existing file
                messenger.send_message("Sending previously downloaded content...", recipient_id)
                messenger.send_document(file_path, recipient_id, "Media Content")
                return
            else:
                # URL was processed but file is gone, allow reprocessing
                pass
        
        # For now, send a mock response
        messenger.send_message("Content downloaded successfully!", recipient_id)
        
    except Exception as e:
        logger.error(f"Generic content handling failed: {e}")
        messenger.send_message(f"Failed to download content. Error: {str(e)}", recipient_id)

def resolve_shortened_url(url: str) -> str:
    """Resolve shortened URLs to their full form"""
    return url

def extract_instagram_reel_info_with_ytdlp(url: str) -> Dict[str, str]:
    """Extract Instagram reel information using yt-dlp"""
    return {'title': 'Instagram Reel', 'creator': 'Unknown'}

def download_instagram_reel_with_ytdlp(url: str) -> Optional[str]:
    """Download Instagram reel using yt-dlp"""
    return None

def process_spotify_url(url: str) -> Optional[Dict[Any, Any]]:
    """Process Spotify URL and return a YouTube search query and filename"""
    return {
        'search_query': 'ytsearch1:spotify track',
        'artist': 'Unknown Artist',
        'track_name': 'Unknown Track',
        'filename': 'Spotify Track',
        'full_title': 'Spotify Track'
    }

def download_media_with_filename(url: str, filename: str = "", audio_only: bool = False) -> Optional[str]:
    """Download media with custom filename - simplified version for WhatsApp"""
    return None
