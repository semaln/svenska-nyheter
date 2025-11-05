import os

# RSS-flöden att hämta nyheter från
FEEDS = [
    {
        'name': 'SVT Nyheter',
        'url': 'https://www.svt.se/nyheter/rss.xml',
        'category': 'allmänt'
    },
    {
        'name': 'Aftonbladet',
        'url': 'https://rss.aftonbladet.se/rss2/small/pages/sections/senastenytt/',
        'category': 'allmänt'
    },
    {
        'name': 'Expressen',
        'url': 'https://feeds.expressen.se/nyheter/',
        'category': 'allmänt'
    },
    {
        'name': 'Dagens Nyheter',
        'url': 'https://www.dn.se/rss/',
        'category': 'allmänt'
    },
    {
        'name': 'Svenska Dagbladet',
        'url': 'https://www.svd.se/?service=rss',
        'category': 'allmänt'
    },
    {
        'name': 'Omni',
        'url': 'https://omni.se/rss/nyheter',
        'category': 'allmänt'
    },
    {
        'name': 'Breakit',
        'url': 'https://www.breakit.se/feed/artiklar',
        'category': 'tech'
    },
    {
        'name': 'Computer Sweden',
        'url': 'https://www.idg.se/rss/csweden',
        'category': 'tech'
    }
]

# MongoDB-konfiguration (använd miljövariabel i produktion)
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.environ.get('DATABASE_NAME', 'swedish_news')
COLLECTION_NAME = os.environ.get('COLLECTION_NAME', 'articles')

# Scheduler-konfiguration
# Hämta nyheter var X:e minut
FETCH_INTERVAL_MINUTES = int(os.environ.get('FETCH_INTERVAL_MINUTES', 15))

# Flask-konfiguration
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Port (för deployment)
PORT = int(os.environ.get('PORT', 5000))
