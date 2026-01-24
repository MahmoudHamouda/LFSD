from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from models.database import SessionLocal
from models.models import Connection
from services.integrations.google_fit_service import GoogleFitService
# from services.integrations.apple_health_service import AppleHealthService
import logging

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
    def start(self):
        """Start the scheduler."""
        # Run health sync every 6 hours
        self.scheduler.add_job(
            self.sync_health_data,
            trigger=IntervalTrigger(hours=6),
            id="sync_health_data",
            replace_existing=True
        )
        self.scheduler.start()
        logger.info("Scheduler started.")

    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped.")

    async def sync_health_data(self):
        """Job to sync health data for all connected users."""
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._sync_health_data_impl)

    def _sync_health_data_impl(self):
        """Synchronous implementation of health data sync."""
        logger.info("Starting scheduled health data sync...")
        db = SessionLocal()
        try:
            # 1. Google Fit
            google_connections = db.query(Connection).filter(
                Connection.provider == "google_fit",
                Connection.status == "connected"
            ).all()
            
            for conn in google_connections:
                try:
                    logger.info(f"Syncing Google Fit for user {conn.user_id}")
                    service = GoogleFitService(db)
                    # Fetch last 1 day of data for incremental updates
                    service.fetch_data(conn.user_id, days=1)
                except Exception as e:
                    logger.error(f"Failed to sync Google Fit for user {conn.user_id}: {e}")

            # 2. Apple Health (Placeholder for now as it requires push or middleware)
            # apple_connections = db.query(Connection).filter(
            #     Connection.provider == "apple_health",
            #     Connection.status == "connected"
            # ).all()
            # for conn in apple_connections:
            #     ...

        except Exception as e:
            logger.error(f"Error in health sync job: {e}")
        finally:
            db.close()
            logger.info("Health data sync job completed.")
