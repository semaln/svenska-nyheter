import feedparser
from pymongo import MongoClient
from datetime import datetime
import hashlib
from config import FEEDS, MONGODB_URI, DATABASE_NAME, COLLECTION_NAME

class RSSFetcher:
    def __init__(self):
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        
        # Skapa index för snabbare sökningar
        self.collection.create_index('article_id', unique=True)
        self.collection.create_index('published_date')
        self.collection.create_index('source')
        self.collection.create_index('category')
    
    def generate_article_id(self, link):
        """Generera unikt ID baserat på artikel-URL"""
        return hashlib.md5(link.encode()).hexdigest()
    
    def parse_date(self, entry):
        """Extrahera publiceringsdatum från RSS-entry"""
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6])
        else:
            return datetime.now()
    
    def extract_image(self, entry):
        """Försök extrahera bild-URL från RSS-entry"""
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
        """Hämta och bearbeta ett RSS-flöde"""
        print(f"Hämtar: {feed_info['name']}...")
        
        try:
            feed = feedparser.parse(feed_info['url'])
            
            if feed.bozo:
                print(f"⚠️  Varning: Problem med {feed_info['name']}")
            
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
                    'image_url': self.extract_image(entry),
                    'fetched_at': datetime.now()
                }
                
                try:
                    self.collection.insert_one(article)
                    new_articles += 1
                except Exception as e:
                    # Artikel finns redan (duplicate key error)
                    pass
            
            print(f"✓ {feed_info['name']}: {new_articles} nya artiklar")
            return new_articles
            
        except Exception as e:
            print(f"✗ Fel vid hämtning av {feed_info['name']}: {str(e)}")
            return 0
    
    def fetch_all_feeds(self):
        """Hämta alla konfigurerade RSS-flöden"""
        print(f"\n{'='*50}")
        print(f"Börjar hämta nyheter - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")
        
        total_new = 0
        for feed in FEEDS:
            total_new += self.fetch_feed(feed)
        
        print(f"\n{'='*50}")
        print(f"Klart! Totalt {total_new} nya artiklar")
        print(f"{'='*50}\n")
        
        return total_new
    
    def get_recent_articles(self, limit=50, category=None):
        """Hämta senaste artiklarna från databasen"""
        query = {}
        if category:
            query['category'] = category
        
        articles = self.collection.find(query).sort('published_date', -1).limit(limit)
        return list(articles)
    
    def get_categories(self):
        """Hämta alla unika kategorier"""
        return self.collection.distinct('category')
    
    def get_sources(self):
        """Hämta alla unika källor"""
        return self.collection.distinct('source')

if __name__ == '__main__':
    # Testa att hämta nyheter
    fetcher = RSSFetcher()
    fetcher.fetch_all_feeds()
