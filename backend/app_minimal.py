"""
Minimal FastAPI application for Cloud Run deployment
Now with database connection to test SQLAlchemy
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

# Database setup
from google.cloud.sql.connector import Connector
import pg8000

from pydantic import BaseModel
from fastapi.responses import JSONResponse
import requests

# Initialize Cloud SQL Connector
connector = Connector()

def getconn():
    """Create database connection using Cloud SQL Connector"""
    conn = connector.connect(
        "newprojectlfsd:us-central1:lfsd-postgres-prod",
        "pg8000",  # Revert to pg8000
        user="postgres",
        password="LfsdSecure2024!",
        db="lfsd"
    )
    return conn

# Create engine with Cloud SQL Connector
engine = create_engine(
    "postgresql+pg8000://",
    creator=getconn,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Simple User model
class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    auth0_id = Column(String, unique=True, index=True, nullable=True)

# DON'T create tables at import time - do it on app startup
# Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create FastAPI app
app = FastAPI(title="LFSD Backend", debug=True)

# Startup Event to Fix Schema
@app.on_event("startup")
async def startup_fix_schema():
    print("STARTUP: Attempting to fix schema (add auth0_id)...")
    try:
        conn = getconn()
        cursor = conn.cursor()
        
        # 1. Add column
        print("STARTUP: Executing ALTER TABLE...")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS auth0_id VARCHAR;")
        
        # 2. Add index
        print("STARTUP: Executing CREATE INDEX...")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_auth0_id ON users(auth0_id);")
        
        # 3. Fix hashed_password constraint (make it nullable)
        print("STARTUP: Fixing hashed_password constraint...")
        cursor.execute("ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL;")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("STARTUP: Schema fix completed successfully!")
    except Exception as e:
        print(f"STARTUP ERROR: {e}")

# CORS - allow all origins for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instead of creating tables at startup, we'll create them on first access
# Tables will be created automatically when first query is made

# Simple health check endpoint
@app.get("/")
async def root():
    return {"status": "ok", "message": "LFSD Backend is running"}

@app.get("/api/test/ping")
async def ping():
    return {"status": "ok", "message": "Ping successful"}

@app.get("/api/test/db")
async def test_db(db: Session = Depends(get_db)):
    """Test database connectivity"""
    try:
        # Simple query to test connection
        # Tables verify: users table should exist
        user_count = db.query(User).count()
        return {
            "status": "ok",
            "message": "Database connected",
            "user_count": user_count
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Database error: {e}")
        print(error_details)
        return {
            "status": "error",
            "message": str(e),
            "details": error_details[:500]  # First 500 chars of traceback
        }

@app.get("/api/auth/config")
async def auth0_config():
    """Return Auth0 configuration"""
    return {
        "domain": "dev-lmc05ou12e7ep05p.eu.auth0.com",
        "clientId": "VVw94DZQITVcARsNlp4JEZkyzMjsgioF",
        "audience": "https://dev-lmc05ou12e7ep05p.eu.auth0.com/api/v2/"
    }

# Auth0 Server-Side Config
AUTH0_DOMAIN = "dev-lmc05ou12e7ep05p.eu.auth0.com"
AUTH0_CLIENT_ID = "VVw94DZQITVcARsNlp4JEZkyzMjsgioF"
AUTH0_CLIENT_SECRET = "vfMd6SgVMU3HYeQvFvjU4Au0i2mbpHYR_lepVuDYvdepslGRyQR1AS235hsqcHMj"

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str | None = None

import requests

@app.post("/api/auth/register")
async def register(data: RegisterRequest):
    """Register a new user via Auth0 Database Connection"""
    url = f"https://{AUTH0_DOMAIN}/dbconnections/signup"
    payload = {
        "client_id": AUTH0_CLIENT_ID,
        "email": data.email,
        "password": data.password,
        "connection": "Username-Password-Authentication",
        "name": data.name
    }
    
    resp = requests.post(url, json=payload)
    if not resp.ok:
        return JSONResponse(status_code=resp.status_code, content=resp.json())
    
    return resp.json()

@app.post("/api/auth/login")
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Login via Auth0 Resource Owner Password Grant"""
    url = f"https://{AUTH0_DOMAIN}/oauth/token"
    payload = {
        "grant_type": "password",
        "username": data.email,
        "password": data.password,
        "client_id": AUTH0_CLIENT_ID,
        "client_secret": AUTH0_CLIENT_SECRET,
        "scope": "openid profile email offline_access"
    }
    
    print(f"Attempting login for {data.email}...")
    resp = requests.post(url, json=payload)
    
    if not resp.ok:
        print(f"Auth0 Login Failed: {resp.text}")
        return JSONResponse(status_code=resp.status_code, content=resp.json())
        
    token_data = resp.json()
    access_token = token_data.get("access_token")
    
    # Verify/Sync User in CloudSQL immediately
    try:
        # Fetch user profile from Auth0 to get the 'sub' (Auth0 ID)
        user_info_resp = requests.get(f"https://{AUTH0_DOMAIN}/userinfo", headers={"Authorization": f"Bearer {access_token}"})
        if user_info_resp.ok:
            user_info = user_info_resp.json()
            auth0_id = user_info.get("sub")
            email = user_info.get("email")
            
            # Sync to Database
            if auth0_id and email:
                user = db.query(User).filter(User.auth0_id == auth0_id).first()
                if not user:
                    user = db.query(User).filter(User.email == email).first()
                    if user:
                        user.auth0_id = auth0_id
                        print(f"Linked user {email}")
                    else:
                        import uuid
                        new_id = str(uuid.uuid4())
                        user = User(id=new_id, email=email, auth0_id=auth0_id)
                        db.add(user)
                        print(f"Created user {email}")
                db.commit()
    except Exception as e:
        print(f"Background Sync Error: {e}")
        # Don't fail the login if sync usually happens later, 
        # but better to do it now so /me works immediately
    
    return token_data

@app.post("/api/auth/callback")
async def auth0_callback(token: dict, db: Session = Depends(get_db)):
    """
    Handle Auth0 callback - create or link user
    Expects: {"token": "jwt_token_here", "email": "user@example.com", "auth0_id": "auth0|123"}
    """
    try:
        # Extract user info from request
        auth0_id = token.get("auth0_id") or token.get("sub")
        email = token.get("email")
        
        if not auth0_id or not email:
            return {
                "status": "error",
                "message": "Missing auth0_id or email"
            }
        
        # Check if user exists by auth0_id
        user = db.query(User).filter(User.auth0_id == auth0_id).first()
        
        if not user:
            # Check if user exists by email (for linking existing accounts)
            user = db.query(User).filter(User.email == email).first()
            if user:
                # Link existing user to Auth0
                user.auth0_id = auth0_id
                print(f"Linked existing user {email} to Auth0 ID {auth0_id}")
            else:
                # Create new user
                import uuid
                user = User(
                    id=str(uuid.uuid4()),
                    email=email,
                    auth0_id=auth0_id
                )
                db.add(user)
                print(f"Created new user {email} with Auth0 ID {auth0_id}")
        
        db.commit()
        db.refresh(user)
        
        return {
            "status": "ok",
            "message": "User created/linked successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "auth0_id": user.auth0_id
            }
        }
        
    except Exception as e:
        db.rollback()
        import traceback
        error_details = traceback.format_exc()
        print(f"Auth0 callback error: {e}")
        print(error_details)
        return {
            "status": "error",
            "message": str(e),
            "details": error_details[:500]
        }

@app.get("/api/auth/me")
async def get_current_user(auth0_id: str, db: Session = Depends(get_db)):
    """
    Get current user by auth0_id
    Usage: /api/auth/me?auth0_id=auth0|123
    """
    try:
        user = db.query(User).filter(User.auth0_id == auth0_id).first()
        if not user:
            return {
                "status": "error",
                "message": "User not found"
            }
        
        return {
            "status": "ok",
            "user": {
                "id": user.id,
                "email": user.email,
                "auth0_id": user.auth0_id
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }




@app.get("/api/debug/schema")
async def debug_schema():
    """Debug endpoint to inspect database schema"""
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        
        tables = inspector.get_table_names()
        columns = {}
        
        if "users" in tables:
            columns["users"] = [
                {"name": c["name"], "type": str(c["type"])} 
                for c in inspector.get_columns("users")
            ]
            
        return {
            "status": "ok",
            "tables": tables,
            "columns": columns
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }

@app.post("/admin/fix-schema")
async def fix_schema():
    """
    Force add auth0_id column using raw connection
    """
    try:
        conn = getconn()
        cursor = conn.cursor()
        
        # 1. Add column
        print("Adding auth0_id column...")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS auth0_id VARCHAR;")
        
        # 2. Add index
        print("Adding index...")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_auth0_id ON users(auth0_id);")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"status": "ok", "message": "Schema patched successfully"}
    except Exception as e:
        import traceback
        return {
            "status": "error", 
            "message": str(e),
            "traceback": traceback.format_exc()
        }
