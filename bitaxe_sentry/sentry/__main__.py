import sys
import time
import logging
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from .poller import poll_once
from .cleaner import clean_old
from .config import POLL_INTERVAL
from .db import init_db
from .notifier import send_startup_notification

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the Bitaxe Sentry application."""
    logger.info("Starting Bitaxe Sentry")
    
    # Initialize database
    init_db()
    
    # Create scheduler with explicit timezone
    scheduler = BackgroundScheduler()
    
    # Calculate next run time (current time + interval)
    now = datetime.datetime.now()
    next_run = now + datetime.timedelta(minutes=POLL_INTERVAL)
    
    # Log scheduling information
    logger.info(f"Current time: {now}")
    logger.info(f"Next scheduled poll: {next_run}")
    logger.info(f"Poll interval: {POLL_INTERVAL} minutes")
    
    # Add jobs with explicit next_run_time
    scheduler.add_job(
        poll_once, 
        'interval', 
        minutes=POLL_INTERVAL, 
        id='poller',
        next_run_time=next_run
    )
    scheduler.add_job(clean_old, 'cron', hour=0, id='cleaner')
    
    # Start the scheduler
    scheduler.start()
    logger.info(f"Scheduler started. Polling every {POLL_INTERVAL} minutes")
    
    # Send startup notification to Discord
    notification_status = send_startup_notification()
    if notification_status:
        logger.info("Discord webhook verified")
    else:
        logger.warning("Discord notifications may not be working correctly")
    
    try:
        # Run initial poll immediately
        logger.info("Running initial poll now")
        poll_once()
        logger.info("Initial poll completed")
        
        # Keep the main thread running
        while True:
            time.sleep(60)  # Check every minute
            logger.debug(f"Main thread alive. Next poll at: {next_run}")
    except KeyboardInterrupt:
        logger.info("Shutting down Bitaxe Sentry")
        scheduler.shutdown()
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        scheduler.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main() 