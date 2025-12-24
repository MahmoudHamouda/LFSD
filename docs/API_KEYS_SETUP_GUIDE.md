# API Keys Setup Guide

This guide will walk you through obtaining API keys for all integrated services.

## 1. Google Maps API Key

### Steps:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - **Geocoding API**
   - **Distance Matrix API**
   - **Places API** (optional)
4. Go to **Credentials** → **Create Credentials** → **API Key**
5. Copy the API key
6. (Recommended) Restrict the key to only the APIs you enabled

### Add to `.env`:
```env
GOOGLE_MAPS_API_KEY=your_api_key_here
```

**Free Tier**: $200 credit per month (covers ~40,000 geocoding requests)

---

## 2. Google Calendar API (OAuth)

### Steps:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Use the same project as Google Maps (or create new)
3. Enable **Google Calendar API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Configure OAuth consent screen:
   - User Type: **External** (for testing)
   - Add your email as a test user
6. Create OAuth Client ID:
   - Application type: **Web application**
   - Authorized redirect URIs: `http://localhost:8002/auth/google/callback`
7. Copy **Client ID** and **Client Secret**

### Add to `.env`:
```env
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
```

**Free Tier**: Unlimited for personal use

---

## 3. Microsoft Graph API (Outlook Calendar)

### Steps:
1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**:
   - Name: `LFSD App`
   - Supported account types: **Accounts in any organizational directory and personal Microsoft accounts**
   - Redirect URI: `http://localhost:8002/auth/microsoft/callback`
4. After creation, copy the **Application (client) ID**
5. Go to **Certificates & secrets** → **New client secret**
6. Copy the **secret value** (you won't see it again!)
7. Go to **API permissions** → **Add a permission**:
   - Microsoft Graph → Delegated permissions
   - Add: `Calendars.ReadWrite`, `User.Read`

### Add to `.env`:
```env
MICROSOFT_CLIENT_ID=your_client_id
MICROSOFT_CLIENT_SECRET=your_client_secret
MICROSOFT_TENANT_ID=common
```

**Free Tier**: Unlimited for personal use

---

## 4. Skyscanner API (via RapidAPI)

### Steps:
1. Go to [RapidAPI](https://rapidapi.com/)
2. Create a free account
3. Search for **"Skyscanner API"**
4. Subscribe to the **Basic (Free)** plan
5. Go to **Endpoints** tab
6. Copy your **X-RapidAPI-Key** from the code snippets

### Add to `.env`:
```env
RAPIDAPI_KEY=your_rapidapi_key
```

**Free Tier**: 100 requests/month

**Alternative**: Direct Skyscanner API
- Apply at [Skyscanner Partners](https://partners.skyscanner.net/)
- More complex approval process

---

## 5. Careem API

### Steps:
1. Go to [Careem Developer Portal](https://developer.careem.com/)
2. Create a developer account
3. Submit an application for API access
4. Wait for approval (can take 1-2 weeks)
5. Once approved, you'll receive:
   - API Key
   - API Secret

### Add to `.env`:
```env
CAREEM_API_KEY=your_api_key
CAREEM_API_SECRET=your_api_secret
```

**Note**: Careem API is not publicly available. You need to be a registered partner.

**Alternative for Testing**: Continue using mock data until partnership is established.

---

## 6. Bolt API

### Steps:
1. Go to [Bolt Business](https://bolt.eu/en/business/)
2. Contact their business development team
3. Request API access for your application
4. Wait for approval and credentials

### Add to `.env`:
```env
BOLT_API_KEY=your_api_key
```

**Note**: Bolt API requires a business partnership agreement.

**Alternative for Testing**: Continue using mock data until partnership is established.

---

## Quick Start: Easiest APIs First

### Priority 1: Can Get Immediately (5-10 minutes each)
1. ✅ **Google Maps** - Instant, free tier available
2. ✅ **Google Calendar** - Instant, free tier available
3. ✅ **Skyscanner (RapidAPI)** - Instant, free tier available

### Priority 2: Requires Application (1-2 days)
4. ⏳ **Microsoft Graph** - Instant setup, but may need verification for production

### Priority 3: Requires Partnership (1-4 weeks)
5. 🤝 **Careem** - Requires business partnership
6. 🤝 **Bolt** - Requires business partnership

---

## Recommended Next Steps

### Today: Get the Easy Ones
Start with Google Maps, Google Calendar, and Skyscanner since they're instant and free:

1. **Google Maps** - Most impactful for location features
2. **Google Calendar** - Enables scheduling features
3. **Skyscanner** - Adds real flight data

### This Week: Apply for Microsoft
Set up Microsoft Graph for Outlook integration (good for business users)

### Long Term: Partner APIs
For Careem and Bolt, you'll need to:
- Prepare a business proposal
- Show traction/user base
- Negotiate partnership terms

---

## Testing Your Keys

After adding keys to `.env`, restart your backend and run:

```bash
# Test Google Maps
python test_google_maps.py

# Test Google Calendar
python test_google_calendar.py

# Test Skyscanner
python test_skyscanner.py
```

You should see real data instead of "Using mock data" warnings!

---

## Need Help?

If you encounter issues:
1. Check that keys are correctly added to `.env`
2. Restart the backend server
3. Check API quotas in respective consoles
4. Review error messages in test scripts
