# Using Real Sandbox APIs - Implementation Plan

## Why This Is Better

✅ **Real API behavior** - Actual Uber responses  
✅ **No development overhead** - Use their sandbox  
✅ **Accurate testing** - Same as production  
✅ **Better AI training** - Real data patterns  
✅ **Free** - No charges in sandbox mode  

## Uber Sandbox API

### Setup (5 minutes)

1. **Register for Uber Developer Account**
   - Go to: https://developer.uber.com/
   - Create account
   - Create a new app

2. **Get Credentials**
   ```env
   UBER_CLIENT_ID=your_client_id
   UBER_CLIENT_SECRET=your_client_secret
   UBER_SERVER_TOKEN=your_server_token  # For sandbox
   ```

3. **Enable Sandbox Mode**
   - In Uber Dashboard → Settings
   - Toggle "Sandbox Mode" ON
   - Use sandbox endpoints

### API Endpoints

**Sandbox Base URL:**
```
https://sandbox-api.uber.com/v1.2/
```

**Production Base URL:**
```
https://api.uber.com/v1.2/
```

### Implementation Changes

#### Update `uber_service.py`

```python
class UberService(BaseMobilityService):
    def __init__(self):
        self.settings = get_settings()
        self.server_token = self.settings.UBER_SERVER_TOKEN
        
        # Use sandbox in development
        if self.settings.ENV == "dev":
            self.base_url = "https://sandbox-api.uber.com/v1.2"
        else:
            self.base_url = "https://api.uber.com/v1.2"
    
    async def get_price_estimates(self, start_lat, start_lng, end_lat, end_lng, user_id=None):
        """Get REAL price estimates from Uber Sandbox"""
        
        headers = {
            "Authorization": f"Token {self.server_token}",
            "Accept-Language": "en_US",
            "Content-Type": "application/json"
        }
        
        params = {
            "start_latitude": start_lat,
            "start_longitude": start_lng,
            "end_latitude": end_lat,
            "end_longitude": end_lng
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/estimates/price",
                headers=headers,
                params=params,
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Log to database
                if user_id:
                    self.log_interaction(user_id, "price_check", {
                        "start": {"lat": start_lat, "lng": start_lng},
                        "end": {"lat": end_lat, "lng": end_lng},
                        "num_options": len(data.get("prices", [])),
                        "sandbox": self.settings.ENV == "dev"
                    })
                    
                    self.log_price_history(
                        user_id,
                        data.get("prices", []),
                        {"lat": start_lat, "lng": start_lng},
                        {"lat": end_lat, "lng": end_lng}
                    )
                
                return {
                    "success": True,
                    "prices": data.get("prices", []),
                    "sandbox": self.settings.ENV == "dev"
                }
            else:
                # Fallback to mock only if API fails
                return {
                    "success": False,
                    "error": f"Uber API error: {response.status_code}",
                    "prices": self._get_mock_prices()
                }
```

### Sandbox Features

#### 1. **Realistic Price Estimates**
- Actual Uber pricing algorithm
- Surge pricing simulation
- Multiple product types (UberX, UberXL, etc.)

#### 2. **Ride Requests**
```python
async def request_ride(self, product_id, start_lat, start_lng, end_lat, end_lng):
    """Request a ride in sandbox mode"""
    
    headers = {
        "Authorization": f"Bearer {access_token}",  # OAuth token
        "Content-Type": "application/json"
    }
    
    payload = {
        "product_id": product_id,
        "start_latitude": start_lat,
        "start_longitude": start_lng,
        "end_latitude": end_lat,
        "end_longitude": end_lng
    }
    
    response = await client.post(
        f"{self.base_url}/requests",
        headers=headers,
        json=payload
    )
    
    return response.json()
```

#### 3. **Sandbox Testing Scenarios**

Uber Sandbox supports special test cases:

```python
# Test surge pricing
start_lat = 37.7749  # San Francisco (has surge data)
start_lng = -122.4194

# Test no drivers available
start_lat = 37.7860
start_lng = -122.4025

# Test specific product types
product_id = "a1111c8c-c720-46c3-8534-2fcdd730040d"  # UberX
```

## Other Providers

### Careem
- Check if they have sandbox: https://developers.careem.com/
- If not, use mock data temporarily

### Bolt  
- Check: https://docs.bolt.eu/
- If no sandbox, use mock

### RTA
- Public API might not need sandbox
- Check: https://www.rta.ae/wps/portal/rta/ae/public-transport

## Implementation Steps

### Phase 1: Uber Sandbox (Today - 1 hour)
1. ✅ Register Uber Developer account
2. ✅ Get server token
3. ✅ Update `uber_service.py` to use sandbox
4. ✅ Test with real coordinates
5. ✅ Verify AI responses improve

### Phase 2: OAuth for Booking (Next)
1. Get OAuth credentials
2. Implement OAuth flow
3. Test ride requests in sandbox
4. Add booking UI

### Phase 3: Other Providers
1. Check for sandbox APIs
2. Implement if available
3. Keep mocks for providers without sandbox

## Configuration

```python
# config.py
class Settings(BaseSettings):
    ENV: str = Field("dev", description="dev/staging/prod")
    
    # Uber
    UBER_SERVER_TOKEN: str = Field("", description="Uber Server Token")
    UBER_CLIENT_ID: str = Field("", description="Uber OAuth Client ID")
    UBER_CLIENT_SECRET: str = Field("", description="Uber OAuth Secret")
    
    # Use sandbox in dev
    @property
    def UBER_BASE_URL(self) -> str:
        if self.ENV == "dev":
            return "https://sandbox-api.uber.com/v1.2"
        return "https://api.uber.com/v1.2"
```

## Benefits

### For Development
- ✅ Real API responses
- ✅ Test edge cases (surge, no drivers, etc.)
- ✅ No charges
- ✅ Same code for dev and prod

### For AI (Gemini)
- ✅ Learns from real data
- ✅ Better price explanations
- ✅ Accurate surge pricing info
- ✅ Realistic ETAs

### For Users
- ✅ Accurate testing experience
- ✅ See real product types
- ✅ Understand actual pricing
- ✅ Smooth transition to production

## Next Steps

1. **Get Uber credentials** (you or me can do this)
2. **Update uber_service.py** (I can do this now)
3. **Test with sandbox** (verify it works)
4. **Update documentation**
5. **Check other providers for sandbox APIs**

Would you like me to:
1. Update the Uber service to use sandbox API right now?
2. Create a guide for getting Uber developer credentials?
3. Both?
