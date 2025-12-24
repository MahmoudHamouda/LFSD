# Provider Authentication Guide

## Your Question: How Do We Book Rides Without Authenticating?

**Excellent question!** You're absolutely right - real bookings require authentication with each provider. Here's how it works:

## Current Implementation (Development/Mock)

Right now, the system uses **mock data** for safety and development:
- ✅ No real API calls
- ✅ No charges
- ✅ No authentication needed
- ✅ Perfect for testing the architecture

## Production Implementation - Authentication Flow

### Overview
Each provider (Uber, Careem, Bolt) requires **OAuth 2.0** authentication to book rides on behalf of users.

### How It Works

#### 1. **User Connects Provider (One-Time Setup)**

```
User → "Connect Uber" button
  ↓
Redirect to Uber OAuth
  ↓
User logs in to Uber
  ↓
User grants permissions
  ↓
Uber redirects back with auth code
  ↓
Backend exchanges code for tokens
  ↓
Store tokens in DBConnection (encrypted)
```

#### 2. **Booking Flow (After Connected)**

```
User → "Book ride to Marina"
  ↓
Backend checks DBConnection for Uber tokens
  ↓
If tokens exist and valid:
  → Use access_token to call Uber API
  → Book ride
  → Return confirmation
  ↓
If tokens expired:
  → Use refresh_token to get new access_token
  → Retry booking
  ↓
If no tokens or refresh fails:
  → Ask user to reconnect Uber
```

## Implementation Details

### Database Schema (Already Exists!)

The `DBConnection` model already supports this:

```python
class DBConnection(Base):
    __tablename__ = "connections"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    provider = Column(String, nullable=False)  # "uber", "careem", etc.
    status = Column(String, nullable=False)     # "connected", "expired"
    access_token = Column(String)               # OAuth access token
    refresh_token = Column(String)              # OAuth refresh token
    expires_at = Column(DateTime)               # Token expiration
    metadata = Column(JSON)                     # Provider-specific data
```

### Code Changes Needed for Production

#### 1. Add OAuth Routes

```python
# oauth_routes.py (NEW FILE)

@router.get("/oauth/{provider}/connect")
async def connect_provider(provider: str, user_id: str):
    """Redirect user to provider's OAuth page"""
    if provider == "uber":
        auth_url = f"https://login.uber.com/oauth/v2/authorize"
        params = {
            "client_id": settings.UBER_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": f"{settings.BASE_URL}/oauth/uber/callback",
            "scope": "request profile"
        }
        return RedirectResponse(f"{auth_url}?{urlencode(params)}")

@router.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, code: str, db: Session):
    """Handle OAuth callback and store tokens"""
    if provider == "uber":
        # Exchange code for tokens
        response = await httpx.post(
            "https://login.uber.com/oauth/v2/token",
            data={
                "client_id": settings.UBER_CLIENT_ID,
                "client_secret": settings.UBER_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"{settings.BASE_URL}/oauth/uber/callback"
            }
        )
        
        tokens = response.json()
        
        # Store in database
        connection = DBConnection(
            id=str(uuid.uuid4()),
            user_id=current_user_id,
            provider="uber",
            status="connected",
            access_token=encrypt(tokens["access_token"]),
            refresh_token=encrypt(tokens["refresh_token"]),
            expires_at=datetime.now() + timedelta(seconds=tokens["expires_in"])
        )
        db.add(connection)
        db.commit()
        
        return {"success": True, "message": "Uber connected!"}
```

#### 2. Update Services to Use Real Tokens

```python
# services/mobility/uber_service.py

async def get_price_estimates(self, ...):
    # Get user's Uber connection
    connection = self.db.query(DBConnection).filter(
        DBConnection.user_id == user_id,
        DBConnection.provider == "uber",
        DBConnection.status == "connected"
    ).first()
    
    if not connection:
        return {"error": "Please connect your Uber account first"}
    
    # Check if token expired
    if connection.expires_at < datetime.now():
        # Refresh token
        await self._refresh_token(connection)
    
    # Use real API with access token
    headers = {
        "Authorization": f"Bearer {decrypt(connection.access_token)}",
        "Content-Type": "application/json"
    }
    
    response = await httpx.get(
        "https://api.uber.com/v1.2/estimates/price",
        headers=headers,
        params={...}
    )
    
    return response.json()
```

#### 3. Token Refresh Logic

```python
async def _refresh_token(self, connection: DBConnection):
    """Refresh expired OAuth token"""
    response = await httpx.post(
        "https://login.uber.com/oauth/v2/token",
        data={
            "client_id": settings.UBER_CLIENT_ID,
            "client_secret": settings.UBER_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": decrypt(connection.refresh_token)
        }
    )
    
    tokens = response.json()
    
    # Update connection
    connection.access_token = encrypt(tokens["access_token"])
    connection.expires_at = datetime.now() + timedelta(seconds=tokens["expires_in"])
    self.db.commit()
```

## Frontend Changes Needed

### 1. Provider Connection UI

```typescript
// Add "Connect" buttons for each provider
<button onClick={() => connectProvider('uber')}>
  Connect Uber Account
</button>

const connectProvider = (provider: string) => {
  // Redirect to OAuth flow
  window.location.href = `/oauth/${provider}/connect`;
};
```

### 2. Show Connection Status

```typescript
// Display which providers are connected
const [connections, setConnections] = useState([]);

useEffect(() => {
  fetch('/api/connections')
    .then(res => res.json())
    .then(data => setConnections(data));
}, []);

// Show badges
{connections.map(conn => (
  <Badge key={conn.provider}>
    {conn.provider} ✓ Connected
  </Badge>
))}
```

## Security Considerations

### 1. Token Encryption
```python
# Use Fernet for symmetric encryption
from cryptography.fernet import Fernet

def encrypt(token: str) -> str:
    f = Fernet(settings.ENCRYPTION_KEY)
    return f.encrypt(token.encode()).decode()

def decrypt(encrypted: str) -> str:
    f = Fernet(settings.ENCRYPTION_KEY)
    return f.decrypt(encrypted.encode()).decode()
```

### 2. Environment Variables
```env
# .env
UBER_CLIENT_ID=your_uber_client_id
UBER_CLIENT_SECRET=your_uber_client_secret
CAREEM_CLIENT_ID=your_careem_client_id
CAREEM_CLIENT_SECRET=your_careem_client_secret
BOLT_CLIENT_ID=your_bolt_client_id
BOLT_CLIENT_SECRET=your_bolt_client_secret
ENCRYPTION_KEY=your_fernet_key_here
```

## Provider-Specific Details

### Uber
- **OAuth URL**: https://login.uber.com/oauth/v2/authorize
- **Scopes**: `request`, `profile`
- **Docs**: https://developer.uber.com/docs/riders/guides/authentication

### Careem
- **OAuth URL**: https://api.careem.com/oauth/authorize
- **Scopes**: `rides.request`, `profile`
- **Docs**: https://developers.careem.com/

### Bolt
- **OAuth URL**: https://api.bolt.eu/oauth/authorize
- **Scopes**: `rides`, `profile`
- **Docs**: https://docs.bolt.eu/

## Migration Path

### Phase 1: Current (Mock Data) ✅
- No authentication
- Safe for development
- Test architecture

### Phase 2: Add OAuth (Next)
1. Register apps with each provider
2. Get client IDs and secrets
3. Add OAuth routes
4. Update services to use tokens
5. Add connection UI

### Phase 3: Production
1. Enable real API calls
2. Add error handling
3. Implement token refresh
4. Add connection management UI
5. Monitor API usage

## Why Mock Data First?

1. **Safety**: No accidental charges during development
2. **Speed**: No API rate limits or delays
3. **Testing**: Predictable responses
4. **Architecture**: Build the system first, add auth later
5. **Cost**: No API fees during development

## Summary

**Current State:**
- ✅ Architecture complete
- ✅ All providers integrated (mock)
- ✅ Database ready for tokens
- ✅ Safe for testing

**To Enable Real Bookings:**
1. Register OAuth apps with providers
2. Add OAuth routes (1-2 days)
3. Update services to use tokens (1 day)
4. Add connection UI (1 day)
5. Test with real accounts (1 day)

**Total Effort:** ~1 week to go from mock to production

---

**The beauty of the current architecture:** It's designed to support OAuth from day one. The `DBConnection` model, service abstraction, and aggregator pattern make adding authentication straightforward!
