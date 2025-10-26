# Ultra-Fast Media Downloader - WhatsApp Bot

A professional, production-ready WhatsApp bot for downloading media from various social platforms.

## Features

- 🎬 **Multi-Platform Support**: YouTube, Instagram, TikTok, Spotify, Twitter, Facebook, Pinterest, Threads
- 📱 **High-Quality Downloads**: Up to 1080p video and 320kbps audio
- ⚡ **Fast Processing**: Optimized download and processing pipeline
- 🔐 **Authentication Support**: Instagram cookies for private content access
- 🔄 **Smart Fallbacks**: Multiple download methods for reliability
- 📦 **Media Group Support**: Carousel posts and multiple images
- 🛡️ **Error Handling**: Comprehensive error handling and user feedback

## Supported Platforms

| Platform    | Video | Audio | Images | Status |
|-------------|-------|-------|--------|--------|
| YouTube     | ✅    | ✅    | ❌     | ✅     |
| Instagram   | ✅    | ✅    | ✅     | ✅     |
| TikTok      | ✅    | ✅    | ❌     | ✅     |
| Spotify     | ❌    | ✅    | ❌     | ✅     |
| Twitter/X   | ✅    | ✅    | ✅     | ✅     |
| Facebook    | ✅    | ✅    | ✅     | ✅     |
| Pinterest   | ✅    | ✅    | ✅     | ✅     |
| Threads     | ✅    | ✅    | ✅     | ✅     |

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd "Whatsapp Version"
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:
```env
PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_TOKEN=your_whatsapp_token
VERIFY_TOKEN=your_verify_token
WABA_ID=your_business_account_id
```

4. Add authentication cookies:
- `cookies.txt` for Instagram
- `ytcookies.txt` for YouTube

## Usage

1. Start the webhook server:
```bash
python app.py
```

2. Configure your WhatsApp Business webhook to point to your server.

3. Send any supported social media link to the bot to download content.

## Technical Architecture

### Core Components

1. **WhatsApp Business API Client**: Handles all WhatsApp communication
2. **Media Download Engine**: Uses yt-dlp for primary downloads with fallbacks
3. **Platform-Specific Handlers**: Custom logic for each social platform
4. **Authentication Manager**: Handles Instagram cookies and proxy support
5. **File Management**: Temporary file handling and cleanup

### Download Process

1. **URL Detection**: Automatically detects platform from URL
2. **Content Analysis**: Determines content type (video/image/audio)
3. **Authentication**: Uses cookies for protected content
4. **Download**: Attempts primary method, falls back if needed
5. **Processing**: Formats and optimizes media
6. **Delivery**: Sends media via WhatsApp API

### Fallback Mechanisms

1. **yt-dlp → Direct Download**: If yt-dlp fails, tries direct HTTP
2. **Direct Download → Instaloader**: For Instagram, uses instaloader as last resort
3. **Single Method → Multiple Attempts**: Retries with different settings

## Configuration

### Environment Variables

| Variable         | Description              | Required |
|------------------|--------------------------|----------|
| PHONE_NUMBER_ID  | WhatsApp phone number ID | ✅       |
| WHATSAPP_TOKEN   | WhatsApp API token       | ✅       |
| VERIFY_TOKEN     | Webhook verification     | ✅       |
| WABA_ID          | Business account ID      | ✅       |
| PROXY_HOST       | Proxy server host        | ❌       |
| PROXY_PORT       | Proxy server port        | ❌       |
| PROXY_USER       | Proxy username           | ❌       |
| PROXY_PASS       | Proxy password           | ❌       |

### File Configuration

- `cookies.txt`: Instagram authentication cookies (Netscape format)
- `ytcookies.txt`: YouTube authentication cookies (Netscape format)
- `config.py`: Application settings and limits

## Error Handling

The bot handles various error conditions gracefully:

- **Network Issues**: Automatic retries with exponential backoff
- **Authentication Failures**: Clear error messages for expired cookies
- **Rate Limiting**: Built-in delays to prevent 403 errors
- **File Size Limits**: Checks against WhatsApp 50MB limit
- **Content Restrictions**: Detects DRM, private, and age-restricted content

## Testing

Run the test suite:
```bash
python test_whatsapp_bot.py
```

## Deployment

### Railway Deployment

1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically on push

### Docker Deployment

```bash
docker build -t whatsapp-bot .
docker run -p 8080:8080 whatsapp-bot
```

## Troubleshooting

### Common Issues

1. **Instagram Downloads Failing**
   - Update `cookies.txt` with fresh Instagram cookies
   - Check if content is private or deleted
   - Verify Instagram authentication is working

2. **YouTube Downloads Blocked**
   - Update `ytcookies.txt` with fresh YouTube cookies
   - Try using a proxy server

3. **Large Files Not Sending**
   - WhatsApp has a 50MB limit for media files
   - Try downloading in lower quality

### Logs

Check logs for detailed error information:
```bash
railway logs
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.

## Support

For support, contact the development team or check the documentation.