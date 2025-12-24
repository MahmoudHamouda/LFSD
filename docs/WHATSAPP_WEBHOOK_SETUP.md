# WhatsApp Webhook Configuration

## Webhook Details

To configure the WhatsApp webhook in the Facebook Developer Console, use these values:

### Callback URL
```
https://your-domain.com/whatsapp/webhook
```

**Note:** Replace `your-domain.com` with your actual domain. For local development, you can use:
- **ngrok**: `https://your-ngrok-url.ngrok.io/whatsapp/webhook`
- **localtunnel**: `https://your-subdomain.loca.lt/whatsapp/webhook`

### Verify Token
```
lfsd_webhook_secure_token_2024
```

This token is configured in your `.env` file as `WHATSAPP_VERIFY_TOKEN`.

## Setup Steps

1. **Start your backend server** (make sure it's running on the correct port)
   ```bash
   python app.py
   ```

2. **Expose your local server** (for development):
   ```bash
   # Using ngrok
   ngrok http 8002
   
   # Or using localtunnel
   npx localtunnel --port 8002
   ```

3. **Configure webhook in Facebook Developer Console**:
   - Go to: https://developers.facebook.com/apps/1543578189999927/whatsapp-business/wa-settings/
   - Click "Configure" next to "Webhook"
   - Enter the **Callback URL** (your ngrok/public URL + `/whatsapp/webhook`)
   - Enter the **Verify Token**: `lfsd_webhook_secure_token_2024`
   - Click "Verify and Save"

4. **Subscribe to webhook fields**:
   - Check "messages" to receive incoming messages
   - Check "message_status" to receive delivery/read receipts

## Testing

Once configured, you can test by:
1. Sending a message to your WhatsApp test number
2. Check your backend logs to see the incoming webhook event
3. The webhook endpoint will log: `Received WhatsApp webhook: {...}`

## Webhook Endpoints

- **GET `/whatsapp/webhook`**: Verification endpoint (Facebook calls this to verify your webhook)
- **POST `/whatsapp/webhook`**: Receives incoming messages and events

## Security

The verify token ensures that only Facebook can verify your webhook. Keep this token secret and don't share it publicly.
