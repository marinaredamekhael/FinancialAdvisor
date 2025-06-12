"""
Script to fetch and store historical data for all stocks in the database and schedule regular updates.
"""
import os
import logging
import time
import schedule
from dotenv import load_dotenv
from app import app
from historical_data_fetcher_av import get_all_stocks_and_update_history

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_all_stocks():
    with app.app_context():
        logger.info("Starting update for all stocks...")
        results = get_all_stocks_and_update_history()
        logger.info("Update Results:")
        for symbol, success in results.items():
            logger.info(f"{symbol}: {'Success' if success else 'Failed'}")


def schedule_updates():
    # Schedule the update to run daily at 5:00 AM
    schedule.every().day.at("05:00").do(update_all_stocks)
    logger.info("Scheduled daily updates at 05:00 AM")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    # Run an initial update
    update_all_stocks()
    # Start the scheduler
    schedule_updates() 