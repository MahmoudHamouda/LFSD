# logging.py

import logging
from logging.handlers import RotatingFileHandler
import json
from flask import request, g

# Set up a default logger for generic events
logger = logging.getLogger("lfsd")
logger.setLevel(logging.INFO)

def log_event(event_type: str, details: dict | None = None, level: str = "info"):
    """
    Generic event logger. Records an event type and optional details using the specified level.
    """
    msg = {"event": event_type, "details": details or {}}
    # Use getattr to fetch the appropriate logging method; default to logger.info
    getattr(logger, level, logger.info)(msg)
from datetime import datetime


# Configure the logger
def get_logger(service_name):
    logger = logging.getLogger(service_name)
    logger.setLevel(
        logging.DEBUG
    )  # Set to DEBUG for detailed logs; adjust as needed

    # Create handlers
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        f"/var/log/{service_name}_app.log", maxBytes=10**6, backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)

    # Create a custom JSON formatter
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "pathname": record.pathname,
                "lineno": record.lineno,
            }
            if hasattr(record, "extra"):
                log_record.update(record.extra)
            return json.dumps(log_record)

    formatter = JSONFormatter()
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to the logger
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger


# Flask integration
def setup_logging(app, service_name):
    logger = get_logger(service_name)

    @app.before_request
    def log_request_info():
        g.start_time = datetime.utcnow()
        logger.info(
            "Request received",
            extra={
                "extra": {
                    "service_name": service_name,
                    "method": request.method,
                    "url": request.url,
                    "remote_addr": request.remote_addr,
                    "user_agent": request.user_agent.string,
                }
            },
        )

    @app.after_request
    def log_response_info(response):
        duration = (datetime.utcnow() - g.start_time).total_seconds()
        logger.info(
            "Request completed",
            extra={
                "extra": {
                    "service_name": service_name,
                    "status_code": response.status_code,
                    "response_time_ms": int(duration * 1000),
                }
            },
        )
        return response

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(
            "Unhandled Exception",
            extra={
                "extra": {
                    "service_name": service_name,
                    "exception": str(e),
                    "path": request.path,
                    "method": request.method,
                    "remote_addr": request.remote_addr,
                }
            },
        )
        return {
            "status": "error",
            "message": "An internal error occurred.",
        }, 500

    @app.route("/logs/user-events", methods=["POST"])
    def log_user_event():
        data = request.json
        user_id = data.get("user_id")
        event = data.get("event")
        details = data.get("details", {})

        if not user_id or not event:
            return {
                "status": "error",
                "message": "user_id and event are required.",
            }, 400

        logger.info(
            "User Event",
            extra={
                "extra": {
                    "service_name": service_name,
                    "user_id": user_id,
                    "event": event,
                    "details": details,
                }
            },
        )
        return {"status": "success", "message": "Event logged."}, 200

    @app.route("/logs/order-event", methods=["POST"])
    def log_order_event():
        data = request.json
        user_id = data.get("user_id")
        order_id = data.get("order_id")
        status = data.get("status")
        provider_id = data.get("provider_id")

        if not user_id or not order_id or not status:
            return {
                "status": "error",
                "message": "user_id, order_id, and status are required.",
            }, 400

        logger.info(
            "Order Event",
            extra={
                "extra": {
                    "service_name": service_name,
                    "user_id": user_id,
                    "order_id": order_id,
                    "status": status,
                    "provider_id": provider_id,
                }
            },
        )
        return {"status": "success", "message": "Order event logged."}, 200

    @app.route("/logs/affordability-analysis", methods=["POST"])
    def log_affordability_analysis():
        data = request.json
        user_id = data.get("user_id")
        item = data.get("item")
        price = data.get("price")
        result = data.get("result")

        if not user_id or not item or not price:
            return {
                "status": "error",
                "message": "user_id, item, and price are required.",
            }, 400

        logger.info(
            "Affordability Analysis",
            extra={
                "extra": {
                    "service_name": service_name,
                    "user_id": user_id,
                    "item": item,
                    "price": price,
                    "result": result,
                }
            },
        )
        return {
            "status": "success",
            "message": "Affordability analysis logged.",
        }, 200
