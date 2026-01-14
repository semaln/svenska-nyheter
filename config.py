import os

# RSS-flöden att hämta AI-nyheter från
# Priority: 1 = Högsta prioritet (officiella företagsbloggar, forskningsinstitut)
#          2 = Hög prioritet (premium tech-media)
#          3 = Medel prioritet (allmänna tech-nyheter)
FEEDS = [
    # HÖGSTA PRIORITET - Officiella AI-företag & Forskningsinstitut
    {
        'name': 'OpenAI Blog',
        'url': 'https://openai.com/blog/rss/',
        'category': 'ai-companies',
        'priority': 1
    },
    {
        'name': 'DeepMind Blog',
        'url': 'https://deepmind.google/blog/rss.xml',
        'category': 'ai-research',
        'priority': 1
    },
    {
        'name': 'Anthropic Blog',
        'url': 'https://www.anthropic.com/news/rss.xml',
        'category': 'ai-companies',
        'priority': 1
    },
    {
        'name': 'Hugging Face Blog',
        'url': 'https://huggingface.co/blog/feed.xml',
        'category': 'ai-companies',
        'priority': 1
    },
    {
        'name': 'Google AI Blog',
        'url': 'https://blog.research.google/feeds/posts/default',
        'category': 'ai-research',
        'priority': 1
    },
    {
        'name': 'Meta AI Blog',
        'url': 'https://ai.meta.com/blog/rss/',
        'category': 'ai-research',
        'priority': 1
    },
    {
        'name': 'MIT Technology Review - AI',
        'url': 'https://www.technologyreview.com/topic/artificial-intelligence/feed',
        'category': 'ai-research',
        'priority': 1
    },
    {
        'name': 'Papers with Code',
        'url': 'https://paperswithcode.com/feeds/latest/',
        'category': 'ai-research',
        'priority': 1
    },
    
    # HÖG PRIORITET - Premium tech-media och AI-fokuserade källor
    {
        'name': 'The Verge AI',
        'url': 'https://www.theverge.com/ai-artificial-intelligence/rss/index.xml',
        'category': 'ai-news',
        'priority': 2
    },
    {
        'name': 'VentureBeat AI',
        'url': 'https://venturebeat.com/category/ai/feed/',
        'category': 'ai-business',
        'priority': 2
    },
    {
        'name': 'TechCrunch AI',
        'url': 'https://techcrunch.com/category/artificial-intelligence/feed/',
        'category': 'ai-business',
        'priority': 2
    },
    {
        'name': 'AI News',
        'url': 'https://artificialintelligence-news.com/feed/',
        'category': 'ai-news',
        'priority': 2
    },
    {
        'name': 'AI Weekly',
        'url': 'https://aiweekly.co/issues.rss',
        'category': 'ai-news',
        'priority': 2
    },
    {
        'name': 'Ars Technica AI',
        'url': 'https://feeds.arstechnica.com/arstechnica/technology-lab',
        'category': 'ai-news',
        'priority': 2
    },
    {
        'name': 'The Batch (Andrew Ng)',
        'url': 'https://www.deeplearning.ai/the-batch/feed/',
        'category': 'ai-research',
        'priority': 2
    },
    {
        'name': 'Machine Learning Mastery',
        'url': 'https://machinelearningmastery.com/feed/',
        'category': 'ai-research',
        'priority': 2
    },
    
    # MEDEL PRIORITET - Allmänna tech-källor & Svenska medier
    {
        'name': 'Wired AI',
        'url': 'https://www.wired.com/feed/tag/ai/latest/rss',
        'category': 'ai-news',
        'priority': 3
    },
    {
        'name': 'ReadWrite AI',
        'url': 'https://readwrite.com/category/ai/feed/',
        'category': 'ai-news',
        'priority': 3
    },
    {
        'name': 'Analytics India Magazine',
        'url': 'https://analyticsindiamag.com/feed/',
        'category': 'ai-news',
        'priority': 3
    },
    
    # Svenska AI & Tech-källor
    {
        'name': 'Breakit',
        'url': 'https://www.breakit.se/feed/artiklar',
        'category': 'svenska',
        'priority': 2
    },
    {
        'name': 'Computer Sweden',
        'url': 'https://www.idg.se/rss/csweden',
        'category': 'svenska',
        'priority': 3
    },
    {
        'name': 'Ny Teknik',
        'url': 'https://www.nyteknik.se/rss/senaste',
        'category': 'svenska',
        'priority': 3
    },
    {
        'name': 'Digital.se',
        'url': 'https://digital.se/feed/',
        'category': 'svenska',
        'priority': 3
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
