# WhatsApp Bot Deployment Guide

## Prerequisites

Before deploying, ensure you have:

1. **Valid WhatsApp Business API Credentials**:
   - `PHONE_NUMBER_ID`
   - `WHATSAPP_TOKEN`
   - `VERIFY_TOKEN`
   - `WABA_ID`

2. **Cookie Files**:
   - `ytcookies.txt` (YouTube cookies for premium content access)
   - `cookies.txt` (Instagram cookies for private content access)

3. **Railway or Hosting Platform Account**

## Deployment Steps

### 1. Prepare Environment Variables

Set these environment variables in your Railway project:

```bash
PHONE_NUMBER_ID=your_whatsapp_phone_number_id
WHATSAPP_TOKEN=your_whatsapp_api_token
VERIFY_TOKEN=your_webhook_verification_token
WABA_ID=your_whatsapp_business_account_id
```

### 2. Upload Files

Upload all files from the `Whatsapp Version` folder to your Railway project:
- `app.py` (main Flask application)
- `whatsapp_bot.py` (core bot logic)
- `config.py` (configuration)
- `ytcookies.txt` (YouTube cookies)
- `cookies.txt` (Instagram cookies)
- `requirements.txt` (dependencies)

### 3. Configure Webhook

Set your Railway app URL as the webhook in your WhatsApp Business API settings:
```
https://your-app-name.up.railway.app/webhook
```

### 4. Deploy

Click "Deploy" in Railway to deploy your application.

## Testing After Deployment

### 1. YouTube Shorts
Send: `https://youtube.com/shorts/4H-ckF9H_y0?si=Wa2MGFJJw6Ut9-Wn`
Expected: Video should download and send back

### 2. Spotify Track
Send: `https://open.spotify.com/track/2YUgUYAXNCrhF7t9Bk9qQH?si=d09d73121a6549fb`
Expected: Audio should download and send back as MP3

### 3. Instagram Reel
Send: `https://www.instagram.com/reel/DGDfJ3LzdEL/?igsh=MWtlc21yZWpyMzRocw==`
Expected: Video should download and send back

### 4. Instagram Carousel Post
Send: `https://www.instagram.com/p/DK_2g5CzKwQ/?igsh=MTgyOXJqbmNicHl5dg==`
Expected: All images should download and send back without duplicates

### 5. TikTok Video
Send: `https://vt.tiktok.com/ZSUKPdCtm/`
Expected: Video should download and send back

## Monitoring in Railway Logs

You should see these messages in your Railway deploy logs:

### Successful Download Indicators
```
📥 Processing youtube URL from user XXX: https://youtube.com/shorts/...
[download]  25.0% of 10.50MiB at 2.10MiB/s ETA 00:05
✅ Downloaded YouTube video
```

### Instagram Carousel Processing
```
📥 Processing instagram URL from user XXX: https://www.instagram.com/p/...
✅ Downloaded 3 Instagram media files
📷 Processing Instagram carousel (Part 1)
📷 Processing Instagram carousel (Part 2)
📷 Processing Instagram carousel (Part 3)
```

### Error Handling
```
❌ Could not fetch media info from YouTube
🔄 Trying direct download method...
✅ Successfully downloaded using fallback method
```

## Troubleshooting

### Common Issues

1. **"Unsupported post request" Errors**:
   - Cause: Invalid WhatsApp API credentials
   - Solution: Verify all environment variables are set correctly

2. **Download Failures**:
   - Cause: Missing or invalid cookie files
   - Solution: Ensure `ytcookies.txt` and `cookies.txt` are properly formatted

3. **Duplicate Sends**:
   - Cause: Multiple fallback paths being triggered
   - Solution: Already fixed in the code with duplicate detection

4. **Instagram Private Content**:
   - Cause: Insufficient Instagram authentication
   - Solution: Ensure `cookies.txt` contains valid session cookies

### Log Monitoring

Monitor these key log messages:

- `📥 Processing [platform] URL from user` - Request received
- `[download] XX.X% of X.XXMiB` - Download progress
- `✅ Downloaded [X] Instagram media files` - Successful carousel download
- `📤 Sending...` - About to send media
- `✅ Successfully sent media` - Media sent successfully

## Expected Behavior

After deployment with valid credentials, the bot will:

1. **Download any supported platform content** when a user sends a link
2. **Show download progress** in Railway logs with percentage indicators
3. **Automatically send** the downloaded content back to the user who sent the link
4. **Handle errors gracefully** with user-friendly messages
5. **Prevent duplicate sends** for carousel posts
6. **Use cookies properly** for authenticated downloads

## Support

If you encounter any issues after deployment:

1. Check Railway logs for specific error messages
2. Verify all environment variables are set correctly
3. Ensure cookie files are properly formatted
4. Test with different content URLs to isolate the issue

The bot is now production-ready and should work exactly as described in your requirements.