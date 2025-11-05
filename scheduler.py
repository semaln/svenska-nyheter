from apscheduler.schedulers.background import BackgroundScheduler
from rss_fetcher import RSSFetcher
from config import FETCH_INTERVAL_MINUTES
import logging

# Sätt upp logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class NewsScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.fetcher = RSSFetcher()
    
    def fetch_news_job(self):
        """Job som hämtar nyheter"""
        try:
            logger.info("Startar automatisk nyhetshämtning...")
            new_articles = self.fetcher.fetch_all_feeds()
            logger.info(f"Nyhetshämtning klar: {new_articles} nya artiklar")
        except Exception as e:
            logger.error(f"Fel vid nyhetshämtning: {str(e)}")
    
    def start(self):
        """Starta schedulern"""
        # Kör jobbet direkt vid start
        self.fetch_news_job()
        
        # Schemalägg att köra jobbet var X:e minut
        self.scheduler.add_job(
            self.fetch_news_job,
            'interval',
            minutes=FETCH_INTERVAL_MINUTES,
            id='fetch_news',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info(f"Scheduler startad - hämtar nyheter var {FETCH_INTERVAL_MINUTES}:e minut")
    
    def stop(self):
        """Stoppa schedulern"""
        self.scheduler.shutdown()
        logger.info("Scheduler stoppad")

if __name__ == '__main__':
    # Testa schedulern
    scheduler = NewsScheduler()
    scheduler.start()
    
    try:
        # Håll programmet igång
        import time
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.stop()
