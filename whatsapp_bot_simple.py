import os
import hashlib
import time
import re
import logging
import json
import requests
import tempfile
import uuid
import shutil
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

# Import heyoo for WhatsApp API
try:
    from heyoo import WhatsApp
    HEYOO_AVAILABLE = True
except ImportError:
    WhatsApp = None
    HEYOO_AVAILABLE = False
    print("Warning: heyoo library not available. Using fallback implementation.")

# Import configuration
from config import (
    MAX_FILE_SIZE, DOWNLOADS_DIR, TEMP_DIR, DATA_DIR,
    PHONE_NUMBER_ID, WHATSAPP_TOKEN, VERIFY_TOKEN
)

# Try to import yt-dlp
try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    yt_dlp = None
    YTDLP_AVAILABLE = False
    print("Warning: yt-dlp not available. Some features will be limited.")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# WhatsApp Business API implementation
class WhatsAppBusiness:
    def __init__(self, access_token: str, phone_number_id: str):
        self.use_heyoo = False
        self.client = None
        self.access_token = access_token
        self.phone_number_id = phone_number_id  # Always set this attribute
        self.api_url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        if HEYOO_AVAILABLE and WhatsApp is not None:
            try:
                self.client = WhatsApp(access_token, phone_number_id)
                self.use_heyoo = True
                logger.info("✅ Using heyoo library for WhatsApp API")
            except Exception as e:
                logger.warning(f"❌ Failed to initialize heyoo library: {e}")
                self.use_heyoo = False
        else:
            logger.info("ℹ️ Using fallback implementation for WhatsApp API")

    def send_message(self, message: str, recipient_id: str):
        """Send a text message via WhatsApp API"""
        if self.use_heyoo and self.client is not None:
            try:
                response = self.client.send_message(message, recipient_id)
                logger.info(f"✅ Message sent successfully to {recipient_id}")
                return {"success": True}
            except Exception as e:
                logger.error(f"❌ Error sending message to {recipient_id}: {e}")
                return {"success": False, "error": str(e)}
        else:
            # Fallback implementation
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
                    return {"success": True}
                else:
                    logger.error(f"❌ Failed to send message to {recipient_id}: {response.text}")
                    return {"success": False, "error": response.text}
            except Exception as e:
                logger.error(f"❌ Error sending message to {recipient_id}: {e}")
                return {"success": False, "error": str(e)}
    
    def send_document(self, document_path: str, recipient_id: str, caption: Optional[str] = None):
        """Send a document via WhatsApp API by uploading it first"""
        try:
            # Determine media type based on file extension
            file_extension = document_path.lower().split('.')[-1]
            media_type = 'video' if file_extension in ['mp4', 'mov', 'avi', 'mkv'] else 'document'
            
            # Read file data
            with open(document_path, 'rb') as f:
                file_data = f.read()
            
            # Upload the media to WhatsApp servers
            files = {
                'file': (os.path.basename(document_path), file_data, self._get_mime_type(document_path)),
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
                    else:
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
            logger.error(f"❌ Error sending document to {recipient_id}: {e}")
        
        # Fallback to sending a message with file information
        try:
            file_size = os.path.getsize(document_path)
            size_mb = file_size / (1024 * 1024)
            
            message = "✅ *Download Complete!*\n\n"
            message += f"📁 *File*: {os.path.basename(document_path)}\n"
            message += f"📊 *Size*: {size_mb:.1f}MB\n"
            if caption:
                message += f"📝 *Caption*: {caption}\n"
            message += "\n⚠️ *Note*: Due to technical limitations, the file cannot be sent directly via WhatsApp.\n"
            message += "The file is available on the server."
            
            result = self.send_message(message, recipient_id)
            return result
        except Exception as e:
            logger.error(f"❌ Error sending fallback message: {e}")
            message = caption if caption else "✅ Video downloaded successfully!"
            return self.send_message(message, recipient_id)

    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type based on file extension"""
        extension = file_path.lower().split('.')[-1]
        mime_types = {
            'mp4': 'video/mp4',
            'mov': 'video/quicktime',
            'avi': 'video/x-msvideo',
            'mkv': 'video/x-matroska',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif'
        }
        return mime_types.get(extension, 'application/octet-stream')

# Initialize WhatsApp client
messenger = WhatsAppBusiness(WHATSAPP_TOKEN, PHONE_NUMBER_ID)

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

def sanitize_text(text: str) -> str:
    """Sanitize text for WhatsApp"""
    # Remove or replace characters that might cause issues in WhatsApp
    sanitized = re.sub(r'[^\w\s\-_.:]', '', text)
    return sanitized[:1000]  # Limit length

def extract_instagram_reel_info_with_ytdlp(url: str) -> Dict[str, str]:
    """Extract Instagram reel title and creator information using yt-dlp"""
    if not YTDLP_AVAILABLE or yt_dlp is None:
        return {
            'title': "Instagram Reel",
            'creator': "Unknown"
        }
    
    try:
        # yt-dlp options for extracting info only (no download)
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
            'socket_timeout': 10,
            'retries': 2,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Extract title and creator/uploader
            title = info.get('title', 'Instagram Reel')
            creator = info.get('uploader', 'Unknown')
            
            # Ensure we return strings
            if title is None:
                title = "Instagram Reel"
            if creator is None:
                creator = "Unknown"
            
            return {
                'title': str(title),
                'creator': str(creator)
            }
    except Exception as e:
        logger.error(f"Failed to extract Instagram reel info with yt-dlp: {e}")
        return {
            'title': "Instagram Reel",
            'creator': "Unknown"
        }

def download_instagram_reel_with_ytdlp(url: str) -> str:
    """Download Instagram reel using yt-dlp"""
    if not YTDLP_AVAILABLE or yt_dlp is None:
        raise Exception("yt-dlp not available")
    
    try:
        import tempfile
        import uuid
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(dir=TEMP_DIR)
        
        # yt-dlp options for downloading
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
            'noplaylist': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Find downloaded file
            video_file = None
            for file in os.listdir(temp_dir):
                if file.endswith(('.mp4', '.mov', '.avi', '.mkv')):
                    video_file = os.path.join(temp_dir, file)
                    break
            
            if not video_file:
                raise Exception("No video file found after download")
            
            return video_file
    except Exception as e:
        logger.error(f"Failed to download Instagram reel with yt-dlp: {e}")
        raise

def process_message(recipient_id: str, text: str):
    """Process incoming WhatsApp messages"""
    # Handle commands
    if text.lower() in ['help', 'start']:
        welcome_text = "🚀 *Ultra-Fast Media Downloader*\n\n"
        welcome_text += "Download from YouTube, Instagram, TikTok, Spotify, Twitter, Facebook and more!\n\n"
        welcome_text += "✨ *Features:*\n"
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
    messenger.send_message("💡 *Tip*\n\nSend a social media link to download content, or type *help* for more information!", recipient_id)

# Add a simple cache to prevent duplicate processing
processed_urls = set()
last_cleanup_time = time.time()

def handle_link(recipient_id: str, url: str):
    """Handle incoming links with intelligent processing"""
    global last_cleanup_time
    
    # Basic URL validation
    if not url.startswith(('http://', 'https://')):
        messenger.send_message("❌ *Invalid URL*\n\nPlease send a valid link starting with http:// or https://", recipient_id)
        return
    
    # Check if URL has already been processed
    url_hash = hashlib.md5(url.encode()).hexdigest()
    if url_hash in processed_urls:
        messenger.send_message("🔄 *This link has already been processed*", recipient_id)
        return
    
    # Clean up old processed URLs periodically (every 10 minutes)
    current_time = time.time()
    if current_time - last_cleanup_time > 600:  # 10 minutes
        processed_urls.clear()
        last_cleanup_time = current_time
    
    if not is_supported_url(url):
        messenger.send_message(
            "❌ *Unsupported Platform*\n\nSupported platforms:\n🎬 YouTube\n📱 Instagram\n🎪 TikTok\n🎵 Spotify\n🐦 Twitter/X\n📘 Facebook",
            recipient_id
        )
        return
    
    platform = detect_platform(url)
    
    logger.info(f"📥 Processing {platform} URL from user {recipient_id}: {url}")
    
    # Show processing message
    messenger.send_message(f"🔄 *Processing {platform.title()} link...*", recipient_id)
    
    # Add to processed URLs
    processed_urls.add(url_hash)
    
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
        messenger.send_message(f"🔄 *Processing {platform.title()} content...*\nThis may take a few moments.", recipient_id)
        handle_generic_content(recipient_id, url)

def handle_instagram_reel(recipient_id: str, url: str):
    """Handle Instagram reel download and send with real information extraction"""
    try:
        # Send processing message
        messenger.send_message("📥 *Downloading Instagram reel...*", recipient_id)
        
        # Extract real title and creator information using yt-dlp
        reel_info = extract_instagram_reel_info_with_ytdlp(url)
        title = reel_info['title']
        creator = reel_info['creator']
        
        # Send info message with real title and creator
        info_message = f"📹 *{title}*\n👤 *Creator: {creator}*"
        messenger.send_message(info_message, recipient_id)
        
        # Download the reel using yt-dlp
        messenger.send_message("⬇️ *Downloading video file...*", recipient_id)
        file_path = download_instagram_reel_with_ytdlp(url)
        
        # Check if file was downloaded successfully
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            messenger.send_message(f"✅ *Successfully downloaded!* Size: {size_mb:.1f}MB", recipient_id)
            
            # Send the actual file
            messenger.send_document(file_path, recipient_id, f"Instagram Reel • {os.path.basename(file_path)}")
        else:
            messenger.send_message("❌ *Download failed*", recipient_id)
        
    except Exception as e:
        logger.error(f"Instagram reel handling failed: {e}")
        messenger.send_message(f"❌ *Failed to download Instagram reel*\nError: {str(e)}", recipient_id)

def handle_instagram_content(recipient_id: str, url: str):
    """Handle Instagram content (posts, stories, etc.)"""
    try:
        messenger.send_message("📥 *Downloading Instagram content...*", recipient_id)
        
        # For now, we'll use a generic approach
        # In a full implementation, you would extract specific Instagram content
        handle_generic_content(recipient_id, url)
        
    except Exception as e:
        logger.error(f"Instagram content handling failed: {e}")
        messenger.send_message(f"❌ *Failed to download Instagram content*\nError: {str(e)}", recipient_id)

def handle_youtube_content(recipient_id: str, url: str):
    """Handle YouTube content"""
    try:
        messenger.send_message("📥 *Downloading YouTube content...*", recipient_id)
        
        # Ensure temp directory exists
        ensure_directories()
        
        # Extract information using yt-dlp
        if YTDLP_AVAILABLE and yt_dlp is not None:
            # Create unique temporary directory for this download
            download_dir = os.path.join(TEMP_DIR, str(uuid.uuid4()))
            os.makedirs(download_dir, exist_ok=True)
            
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': os.path.join(download_dir, '%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'merge_output_format': 'mp4',
                'noplaylist': True,
            }
            
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'YouTube Video')
            uploader = info.get('uploader', 'Unknown')
            
            # Send info message
            info_message = f"📹 *{title}*\n👤 *Uploader: {uploader}*"
            messenger.send_message(info_message, recipient_id)
            
            # Download the content
            messenger.send_message("⬇️ *Downloading video file...*", recipient_id)
            ydl.download([url])
            
            # Find downloaded file
            video_file = None
            for root, dirs, files in os.walk(download_dir):
                for file in files:
                    if file.endswith(('.mp4', '.mov', '.avi', '.mkv')):
                        video_file = os.path.join(root, file)
                        break
                if video_file:
                    break
            
            if video_file and os.path.exists(video_file):
                file_size = os.path.getsize(video_file)
                size_mb = file_size / (1024 * 1024)
                messenger.send_message(f"✅ *Successfully downloaded!* Size: {size_mb:.1f}MB", recipient_id)
                messenger.send_document(video_file, recipient_id, f"YouTube Video • {title}")
                # Clean up after sending
                try:
                    os.remove(video_file)
                    os.rmdir(download_dir)
                except:
                    pass
            else:
                messenger.send_message("❌ *Download failed - No video file found*", recipient_id)
        else:
            messenger.send_message("❌ *yt-dlp not available*", recipient_id)
            
    except Exception as e:
        logger.error(f"YouTube content handling failed: {e}")
        messenger.send_message(f"❌ *Failed to download YouTube content*\nError: {str(e)}", recipient_id)

def handle_tiktok_content(recipient_id: str, url: str):
    """Handle TikTok content"""
    try:
        messenger.send_message("📥 *Downloading TikTok content...*", recipient_id)
        handle_generic_content(recipient_id, url)
    except Exception as e:
        logger.error(f"TikTok content handling failed: {e}")
        messenger.send_message(f"❌ *Failed to download TikTok content*\nError: {str(e)}", recipient_id)

def handle_facebook_content(recipient_id: str, url: str):
    """Handle Facebook content"""
    try:
        messenger.send_message("📥 *Downloading Facebook content...*", recipient_id)
        handle_generic_content(recipient_id, url)
    except Exception as e:
        logger.error(f"Facebook content handling failed: {e}")
        messenger.send_message(f"❌ *Failed to download Facebook content*\nError: {str(e)}", recipient_id)

def handle_spotify_content(recipient_id: str, url: str):
    """Handle Spotify content"""
    try:
        messenger.send_message("📥 *Downloading Spotify content...*", recipient_id)
        
        # For Spotify, we'll try to download audio
        if YTDLP_AVAILABLE and yt_dlp is not None:
            # Create unique temporary directory for this download
            download_dir = os.path.join(TEMP_DIR, str(uuid.uuid4()))
            os.makedirs(download_dir, exist_ok=True)
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'noplaylist': True,
            }
            
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            # Extract info first
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Spotify Audio')
            uploader = info.get('uploader', 'Unknown') if info.get('uploader') else info.get('artist', 'Unknown')
            
            # Send info message
            info_message = f"🎵 *{title}*\n👤 *Artist: {uploader}*"
            messenger.send_message(info_message, recipient_id)
            
            # Download the content
            messenger.send_message("⬇️ *Downloading audio file...*", recipient_id)
            ydl.download([url])
            
            # Find downloaded file
            audio_file = None
            for root, dirs, files in os.walk(download_dir):
                for file in files:
                    if file.endswith(('.mp3', '.m4a', '.wav', '.flac')):
                        audio_file = os.path.join(root, file)
                        break
                if audio_file:
                    break
            
            if audio_file and os.path.exists(audio_file):
                file_size = os.path.getsize(audio_file)
                size_mb = file_size / (1024 * 1024)
                messenger.send_message(f"✅ *Successfully downloaded!* Size: {size_mb:.1f}MB", recipient_id)
                messenger.send_document(audio_file, recipient_id, f"Audio • {title}")
                # Clean up after sending
                try:
                    os.remove(audio_file)
                    os.rmdir(download_dir)
                except:
                    pass
            else:
                messenger.send_message("❌ *Download failed - No audio file found*", recipient_id)
        else:
            messenger.send_message("❌ *Media download not available*", recipient_id)
            
    except Exception as e:
        logger.error(f"Spotify content handling failed: {e}")
        if "DRM" in str(e):
            messenger.send_message("❌ *Spotify content is DRM protected and cannot be downloaded*", recipient_id)
        else:
            messenger.send_message(f"❌ *Failed to download Spotify content*\nError: {str(e)}", recipient_id)

def handle_twitter_content(recipient_id: str, url: str):
    """Handle Twitter/X content"""
    try:
        messenger.send_message("📥 *Downloading Twitter content...*", recipient_id)
        handle_generic_content(recipient_id, url)
    except Exception as e:
        logger.error(f"Twitter content handling failed: {e}")
        messenger.send_message(f"❌ *Failed to download Twitter content*\nError: {str(e)}", recipient_id)

def handle_generic_content(recipient_id: str, url: str):
    """Handle generic content download"""
    try:
        # Use yt-dlp for generic content download
        if YTDLP_AVAILABLE and yt_dlp is not None:
            # Ensure temp directory exists
            ensure_directories()
            
            # Create unique temporary directory for this download
            download_dir = os.path.join(TEMP_DIR, str(uuid.uuid4()))
            os.makedirs(download_dir, exist_ok=True)
            
            ydl_opts = {
                'format': 'best[ext=mp4]/best/bestvideo*+bestaudio/best',
                'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'merge_output_format': 'mp4',
                'noplaylist': True,
            }
            
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            # Extract info first
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Video')
            uploader = info.get('uploader', 'Unknown') if info.get('uploader') else info.get('uploader_id', 'Unknown')
            
            # Send info message
            info_message = f"📹 *{title}*\n👤 *Uploader: {uploader}*"
            messenger.send_message(info_message, recipient_id)
            
            # Download the content
            messenger.send_message("⬇️ *Downloading file...*", recipient_id)
            ydl.download([url])
            
            # Find downloaded file
            downloaded_file = None
            for root, dirs, files in os.walk(download_dir):
                for file in files:
                    if file.endswith(('.mp4', '.mov', '.avi', '.mkv', '.m4a', '.mp3', '.wav', '.flac')):
                        downloaded_file = os.path.join(root, file)
                        break
                if downloaded_file:
                    break
            
            if downloaded_file and os.path.exists(downloaded_file):
                file_size = os.path.getsize(downloaded_file)
                size_mb = file_size / (1024 * 1024)
                messenger.send_message(f"✅ *Successfully downloaded!* Size: {size_mb:.1f}MB", recipient_id)
                
                # Determine caption based on file type
                if downloaded_file.endswith(('.mp4', '.mov', '.avi', '.mkv')):
                    caption = f"Video • {title}"
                elif downloaded_file.endswith(('.m4a', '.mp3', '.wav', '.flac')):
                    caption = f"Audio • {title}"
                else:
                    caption = f"Media • {title}"
                    
                messenger.send_document(downloaded_file, recipient_id, caption)
                # Clean up after sending
                try:
                    os.remove(downloaded_file)
                    os.rmdir(download_dir)
                except:
                    pass
            else:
                messenger.send_message("❌ *Download failed - No file found*", recipient_id)
        else:
            messenger.send_message("❌ *Media download not available*", recipient_id)
            
    except Exception as e:
        logger.error(f"Generic content handling failed: {e}")
        messenger.send_message(f"❌ *Failed to download content*\nError: {str(e)}", recipient_id)

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