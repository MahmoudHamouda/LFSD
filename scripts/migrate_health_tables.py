"""
Database migration script to add health-related tables.

Run this script to create the new tables for health integrations:
- health_connections
- health_metrics
- user_indexes
- health_insights
- health_settings
"""

from database import engine, Base
from models_health import (
    DBHealthConnection,
    DBHealthMetric,
    DBUserIndex,
    DBHealthInsight,
    DBHealthSettings
)

def run_migration():
    """Create all health-related tables."""
    print("Creating health-related tables...")
    
    # Create ALL tables (this will create base tables if they don't exist)
    Base.metadata.create_all(bind=engine)
    
    print("✓ All tables created successfully!")
    print("  - users")
    print("  - financials")
    print("  - transactions")
    print("  - orders")
    print("  - notifications")
    print("  - activity_feed")
    print("  - interactions")
    print("  - connections")
    print("  - price_history")
    print("  - conversations")
    print("  - messages")
    print("  - health_connections")
    print("  - health_metrics")
    print("  - user_indexes")
    print("  - health_insights")
    print("  - health_settings")

if __name__ == "____main__":
    run_migration()
