import feedparser
from pymongo import MongoClient
from datetime import datetime, timezone
import hashlib
from config import FEEDS, MONGODB_URI, DATABASE_NAME, COLLECTION_NAME

class RSSFetcher:
    def __init__(self):
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        
        # Skapa index fÃ¶r snabbare sÃ¶kningar
        self.collection.create_index('article_id', unique=True)
        self.collection.create_index('published_date')
        self.collection.create_index('source')
        self.collection.create_index('category')
        self.collection.create_index('priority')
    
    def generate_article_id(self, link):
        """Generera unikt ID baserat pÃ¥ artikel-URL"""
        return hashlib.md5(link.encode()).hexdigest()
    
    def parse_date(self, entry):
        """
        Extrahera publiceringsdatum frÃ¥n RSS-entry.
        Ser till att datumet Ã¤r "aware" och satt till UTC.
        """
        dt = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            # feedparser ger en UTC-baserad tuple. Skapa datetime-objekt med UTC-tidszon.
            # <-- Ã„NDRING 2: LÃ¤gg till tzinfo=timezone.utc
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            # Samma sak fÃ¶r 'updated'
            # <-- Ã„NDRING 3: LÃ¤gg till tzinfo=timezone.utc
            dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        else:
            # Fallback: anvÃ¤nd nuvarande tid, men se till att den Ã¤r UTC-medveten
            # <-- Ã„NDRING 4: AnvÃ¤nd datetime.now(timezone.utc)
            dt = datetime.now(timezone.utc)
        return dt
    
    def extract_image(self, entry):
        """FÃ¶rsÃ¶k extrahera bild-URL frÃ¥n RSS-entry"""
        # Kolla efter media:content eller media:thumbnail
        if hasattr(entry, 'media_content') and entry.media_content:
            return entry.media_content[0].get('url')
        
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            return entry.media_thumbnail[0].get('url')
        
        # Kolla efter enclosures (ofta bilder)
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if enclosure.get('type', '').startswith('image'):
                    return enclosure.get('href')
        
        # Kolla i beskrivningen efter img-taggar
        if hasattr(entry, 'description'):
            import re
            img_match = re.search(r'<img[^>]+src="([^"]+)"', entry.description)
            if img_match:
                return img_match.group(1)
        
        return None
    
    def fetch_feed(self, feed_info):
        """HÃ¤mta och bearbeta ett RSS-flÃ¶de"""
        print(f"HÃ¤mtar: {feed_info['name']}...")
        
        try:
            feed = feedparser.parse(feed_info['url'])
            
            if feed.bozo:
                print(f"âš ï¸  Varning: Problem med {feed_info['name']}")
            
            new_articles = 0
            
            for entry in feed.entries:
                article = {
                    'article_id': self.generate_article_id(entry.link),
                    'title': entry.get('title', 'Ingen titel'),
                    'link': entry.link,
                    'description': entry.get('summary', entry.get('description', '')),
                    'published_date': self.parse_date(entry),
                    'source': feed_info['name'],
                    'category': feed_info['category'],
                    'priority': feed_info.get('priority', 3),
                    'image_url': self.extract_image(entry),
                    'fetched_at': datetime.now(timezone.utc)
                }
                
                try:
                    self.collection.insert_one(article)
                    new_articles += 1
                except Exception as e:
                    # Artikel finns redan (duplicate key error)
                    pass
            
            print(f"âœ“ {feed_info['name']}: {new_articles} nya artiklar")
            return new_articles
            
        except Exception as e:
            print(f"âœ— Fel vid hÃ¤mtning av {feed_info['name']}: {str(e)}")
            return 0
    
    def fetch_all_feeds(self):
        """HÃ¤mta alla konfigurerade RSS-flÃ¶den"""
        print(f"\n{'='*50}")
        print(f"BÃ¶rjar hÃ¤mta nyheter - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"{'='*50}\n")
        
        total_new = 0
        for feed in FEEDS:
            total_new += self.fetch_feed(feed)
        
        print(f"\n{'='*50}")
        print(f"Klart! Totalt {total_new} nya artiklar")
        print(f"{'='*50}\n")
        
        return total_new
    
    def get_recent_articles(self, limit=50, category=None):
        """HÃ¤mta senaste artiklarna frÃ¥n databasen"""
        query = {}
        if category:
            query['category'] = category
        
        articles = self.collection.find(query).sort('published_date', -1).limit(limit)
        return list(articles)
    
    def get_categories(self):
        """HÃ¤mta alla unika kategorier"""
        return self.collection.distinct('category')
    
    def get_sources(self):
        """HÃ¤mta alla unika kÃ¤llor"""
        return self.collection.distinct('source')

if __name__ == '__main__':
    # Testa att hÃ¤mta nyheter
    fetcher = RSSFetcher()
    fetcher.fetch_all_feeds()
