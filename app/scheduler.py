import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.config import get_settings
from app.database.session import SessionLocal
from app.services.product_service import refresh_all_products
from app.services.alert_service import send_price_alert

logger = logging.getLogger(__name__)
settings = get_settings()

_scheduler = BackgroundScheduler()


def _run_refresh():
    logger.info("[scheduler] Starting scheduled price refresh")
    db = SessionLocal()
    try:
        summary = refresh_all_products(db)

        # Fire email alerts for triggered products
        for alert in summary.get("alerts", []):
            # In a real multiuser setup you'd look up the user email here
            logger.info(
                f"[scheduler] ALERT: '{alert['product_name']}' "
                f"→ ${alert['price']} (target ${alert['alert_price']})"
            )
            # send_price_alert(user_email, ...) — wire up when you have user emails
    except Exception as e:
        logger.exception(f"[scheduler] Refresh job crashed: {e}")
    finally:
        db.close()


def start_scheduler():
    interval = settings.scrape_interval_minutes
    _scheduler.add_job(
        _run_refresh,
        trigger=IntervalTrigger(minutes=interval),
        id="price_refresh",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(f"[scheduler] Started — refresh every {interval} min")


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[scheduler] Stopped")
