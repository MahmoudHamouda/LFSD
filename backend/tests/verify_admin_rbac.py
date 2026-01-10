import sys
import os
import unittest
from unittest.mock import MagicMock

# Mock problematic modules before imports
import types
g = types.ModuleType("google")
g.cloud = types.ModuleType("google.cloud")
g.generativeai = MagicMock()
sys.modules["google"] = g
sys.modules["google.cloud"] = g.cloud
sys.modules["google.cloud.sql"] = MagicMock()
sys.modules["google.cloud.sql.connector"] = MagicMock()
sys.modules["google.generativeai"] = g.generativeai
sys.modules["pg8000"] = MagicMock()
sys.modules["redis"] = MagicMock()

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(root_dir, "backend")
sys.path.insert(0, backend_dir)

from app import create_app
from models.database import Base, get_db
from models.models import User
from core.authentication import get_current_user

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestAdminRBAC(unittest.TestCase):
    def setUp(self):
        # Patch database before app creation
        from models import database
        database.engine = engine
        database.SessionLocal = TestingSessionLocal
        
        Base.metadata.create_all(bind=engine)
        self.app = create_app()
        
        # Helper to get DB session
        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        # Dependency override to control "current_user"
        self.mock_user = None
        async def override_get_current_user():
            if self.mock_user is None:
                from fastapi import HTTPException
                raise HTTPException(status_code=401, detail="Unauthorized")
            return self.mock_user

        self.app.dependency_overrides[get_current_user] = override_get_current_user
        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)
        self.db = TestingSessionLocal()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=engine)
        self.app.dependency_overrides = {}

    def test_admin_route_denies_regular_user(self):
        """Verify that a user with role='user' gets 403 on admin routes."""
        self.mock_user = User(id="u1", email="user@test.com", role="user")
        self.db.add(self.mock_user)
        self.db.commit()

        response = self.client.get("/api/admin/users")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Not authorized")

    def test_admin_route_allows_admin_user(self):
        """Verify that a user with role='admin' can access admin routes."""
        self.mock_user = User(id="a1", email="admin@test.com", role="admin")
        self.db.add(self.mock_user)
        self.db.commit()

        response = self.client.get("/api/admin/users")
        self.assertEqual(response.status_code, 200)
        # Should return list of users (at least the one we just added)
        users = response.json()
        self.assertIsInstance(users, list)
        self.assertTrue(len(users) >= 1)

    def test_admin_route_denies_unauthenticated(self):
        """Verify that no user results in 401 (via our override)."""
        self.mock_user = None
        response = self.client.get("/api/admin/users")
        self.assertEqual(response.status_code, 401)

if __name__ == "__main__":
    unittest.main()
