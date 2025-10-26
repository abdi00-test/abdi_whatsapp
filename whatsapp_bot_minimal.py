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

# Try to import BeautifulSoup
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BeautifulSoup = None
    BS4_AVAILABLE = False
    print("Warning: BeautifulSoup not available. Spotify processing will be limited.")

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

def process_message(recipient_id: str, text: str):
    """Process incoming WhatsApp messages"""
    print(f"Processing message from {recipient_id}: {text}")

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