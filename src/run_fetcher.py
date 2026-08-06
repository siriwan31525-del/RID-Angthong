#!/usr/bin/env python
import sys
import time
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import Config
from src.fetcher import DataFetcher
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/fetcher.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("="*60)
    logger.info("🚀 Starting Water Data Fetcher Bot")
    logger.info(f"📡 Tracking: {', '.join(Config.STATIONS)}")
    logger.info(f"⏱️  Interval: Every {Config.FETCH_INTERVAL_MINUTES} minute(s)")
    logger.info(f"📁 Database: {Config.DB_PATH}")
    logger.info("="*60)
    
    fetcher = DataFetcher()
    
    def fetch_job():
        """Job function"""
        fetcher.run_once()
    
    # Run immediately on start
    fetch_job()
    
    # Schedule periodic runs
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        fetch_job,
        trigger=IntervalTrigger(minutes=Config.FETCH_INTERVAL_MINUTES),
        id='fetch_job',
        replace_existing=True
    )
    scheduler.start()
    
    try:
        # Keep the script running
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("🛑 Stopping fetcher bot...")
        scheduler.shutdown()
        logger.info("✅ Bot stopped")

if __name__ == "__main__":
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)
    main()
