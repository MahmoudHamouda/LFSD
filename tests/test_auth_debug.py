import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from core.authentication import create_access_token, jwt
    print(f"JWT Module: {jwt}")
except Exception as e:
    print(f"Import Error: {e}")
    # Try direct import
    try:
        import jwt as j
        print(f"Direct import jwt: {j}")
    except:
        print("Direct import jwt failed")
    
    exit(1)

try:
    token = create_access_token({"sub": "test@test.com"})
    print(f"Generated Token: {token}")

    if jwt:
        from core.config import get_settings
        settings = get_settings()
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALG])
            print(f"Decoded Payload: {payload}")
        except Exception as e:
            print(f"Decode Failed: {e}")
    else:
        print("JWT is None, using fallback.")

except Exception as e:
    print(f"Runtime Error: {e}")
