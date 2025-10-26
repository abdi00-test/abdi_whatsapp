import requests
from bs4 import BeautifulSoup
import json
import re

def process_spotify_url(url: str):
    """Process Spotify URL and return a YouTube search query and filename"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Fetch page
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code != 200:
            return None
        
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
        
        # Helpers
        def clean_text(text: str) -> str:
            t = re.sub(r'\s*\(.*?\)\s*', '', text or '').strip()
            t = re.sub(r'\s+', ' ', t)
            return t
        
        # Track processing
        if '/track/' in url.lower():
            # Try title like "Track • Artist" or "Artist - Track"
            if ' • ' in title_text:
                track_name, artist = title_text.split(' • ', 1)
            elif ' - ' in title_text:
                temp_a, temp_t = title_text.split(' - ', 1)
                # Often appears as "Artist - Track"
                artist, track_name = temp_a, temp_t
            else:
                track_name = title_text
            
            # Fallback parse from JSON-LD
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
        
        # For other Spotify content types, use generic search
        else:
            # Extract title for other Spotify content
            title = clean_text(title_text or 'Spotify Content')
            search_query = f"ytsearch1:{title}"
            filename = title
            full_title = title
        
        return {
            'search_query': search_query,
            'artist': artist or 'Unknown Artist',
            'track_name': track_name or 'Unknown Track',
            'filename': filename or 'Spotify Audio',
            'full_title': full_title or filename or 'Spotify Audio'
        }
    
    except Exception as e:
        print(f"Spotify processing error: {e}")
        return None

def test_spotify_url():
    """Test Spotify URL processing"""
    # Test URL from user
    test_url = "https://open.spotify.com/track/77VO5dSsGbTPxa2QF2KeIF?si=c762306e90e741d6"
    
    print("🧪 Testing Spotify URL processing...")
    print("=" * 50)
    print(f"URL: {test_url}")
    
    result = process_spotify_url(test_url)
    
    if result:
        print("✅ Spotify URL processed successfully!")
        print(f"Search Query: {result['search_query']}")
        print(f"Artist: {result['artist']}")
        print(f"Track Name: {result['track_name']}")
        print(f"Filename: {result['filename']}")
        print(f"Full Title: {result['full_title']}")
        print()
        print("This means the WhatsApp bot will now:")
        print("1. Extract metadata from Spotify")
        print("2. Search YouTube for the same track")
        print("3. Download the YouTube version")
        print("4. Send it with proper artist and track name")
    else:
        print("❌ Failed to process Spotify URL")

if __name__ == "__main__":
    test_spotify_url()