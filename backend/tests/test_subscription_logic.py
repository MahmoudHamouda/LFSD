import sys
import os
import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add roots to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "backend"))

from backend.models.database import Base
from backend.models.models import User
from backend.models.growth_models import Subscription, TierConfig, UserLimitOverride
from backend.services.growth_service import GrowthService
from backend.models.growth_schemas import PlanId


class TestSubscriptionLogic(unittest.TestCase):
    def setUp(self):
        # Use a temporary SQLite database for logic testing
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        # Create a test user
        self.test_user = User(id="test_user_id", email="test@example.com", role="user")
        self.db.add(self.test_user)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)

    def test_default_entitlements_no_config(self):
        """Test that GrowthService returns hardcoded defaults if no DB config exists."""
        entitlements = GrowthService.get_entitlements(self.test_user.id, self.db)

        self.assertEqual(entitlements.plan, "tier_free")
        self.assertEqual(entitlements.limits["goals"], 5)
        self.assertEqual(
            entitlements.limits["ai_chat_calls"], 100
        )  # Updated from 5 because of PLAN_CONFIGS in GrowthService

    def test_tier_config_override_defaults(self):
        """Test that DB-driven TierConfig is respected."""
        # Seeding a global free tier with higher limits
        tier = TierConfig(
            id="free_id",
            plan_id="tier_free",
            name="Global Free",
            config_json={
                "features": ["basic"],
                "limits": {"goals": 10, "ai_chat_calls": 20},
            },
        )
        self.db.add(tier)
        self.db.commit()

        entitlements = GrowthService.get_entitlements(self.test_user.id, self.db)
        self.assertEqual(entitlements.limits["goals"], 10)
        self.assertEqual(entitlements.limits["ai_chat_calls"], 20)

    def test_user_specific_limit_overrides(self):
        """Test that UserLimitOverride merges correctly with TierConfig."""
        # Global Config
        tier = TierConfig(
            id="free_id",
            plan_id="tier_free",
            name="Global Free",
            config_json={"limits": {"goals": 5, "ai_chat_calls": 5}},
        )
        # User Override
        override = UserLimitOverride(
            id="override_id",
            user_id=self.test_user.id,
            overrides_json={"ai_chat_calls": 100},
        )
        self.db.add(tier)
        self.db.add(override)
        self.db.commit()

        entitlements = GrowthService.get_entitlements(self.test_user.id, self.db)

        # Goals should stay 5 (from tier), but queries should be 100 (from override)
        self.assertEqual(entitlements.limits["goals"], 5)
        self.assertEqual(entitlements.limits["ai_chat_calls"], 100)

    def test_subscription_upgrade_change_limits(self):
        """Test that changing a user's subscription updates their entitlements."""
        # Seed Pro tier
        pro_tier = TierConfig(
            id="pro_id",
            plan_id="tier_pro",
            name="Pro Tier",
            config_json={"limits": {"goals": -1, "ai_queries_per_day": -1}},
        )
        self.db.add(pro_tier)

        # Grant Pro subscription
        GrowthService.create_or_upgrade_subscription(
            self.test_user.id, "tier_pro", self.db
        )

        entitlements = GrowthService.get_entitlements(self.test_user.id, self.db)
        self.assertEqual(entitlements.plan, "tier_pro")
        self.assertEqual(entitlements.limits["goals"], -1)


if __name__ == "__main__":
    unittest.main()
