from apscheduler.schedulers.background import BackgroundScheduler
from rss_fetcher import RSSFetcher
from config import FETCH_INTERVAL_MINUTES
import logging

# SÃ¤tt upp logging
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
        """Job som hÃ¤mtar nyheter"""
        try:
            logger.info("Startar automatisk nyhetshÃ¤mtning...")
            new_articles = self.fetcher.fetch_all_feeds()
            logger.info(f"NyhetshÃ¤mtning klar: {new_articles} nya artiklar")
        except Exception as e:
            logger.error(f"Fel vid nyhetshÃ¤mtning: {str(e)}")
    
    def start(self):
        """Starta schedulern"""
        # KÃ¶r jobbet direkt vid start
        self.fetch_news_job()
        
        # SchemalÃ¤gg att kÃ¶ra jobbet var X:e minut
        self.scheduler.add_job(
            self.fetch_news_job,
            'interval',
            minutes=FETCH_INTERVAL_MINUTES,
            id='fetch_news',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info(f"Scheduler startad - hÃ¤mtar nyheter var {FETCH_INTERVAL_MINUTES}:e minut")
    
    def stop(self):
        """Stoppa schedulern"""
        self.scheduler.shutdown()
        logger.info("Scheduler stoppad")

if __name__ == '__main__':
    # Testa schedulern
    scheduler = NewsScheduler()
    scheduler.start()
    
    try:
        # HÃ¥ll programmet igÃ¥ng
        import time
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.stop()
