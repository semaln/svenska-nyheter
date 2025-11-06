from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from bson import json_util
import json
from datetime import datetime, timezone
from scheduler import NewsScheduler
import os
import logging

# Konfigurera logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Hämta konfiguration från miljövariabler eller config.py
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.environ.get('DATABASE_NAME', 'swedish_news')
COLLECTION_NAME = os.environ.get('COLLECTION_NAME', 'articles')

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

# MongoDB connection
try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    logger.info("✅ MongoDB-anslutning lyckades!")
    
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
except Exception as e:
    logger.error(f"❌ MongoDB-anslutningsfel: {e}")
    collection = None

# Starta scheduler i bakgrunden
if not os.environ.get('TESTING'):
    try:
        scheduler = NewsScheduler()
        scheduler.start()
        logger.info("✅ Scheduler startad!")
    except Exception as e:
        logger.error(f"⚠️  Scheduler kunde inte startas: {e}")

def parse_json(data):
    """Konvertera MongoDB ObjectId till JSON"""
    return json.loads(json_util.dumps(data, json_options=json_util.RELAXED_JSON_OPTIONS))

@app.route('/')
def index():
    """Servera frontend"""
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Servera statiska filer"""
    return send_from_directory('static', filename)

@app.route('/api/articles', methods=['GET'])
def get_articles():
    """Hämta artiklar med filtrering och paginering (max 100 senaste artiklar)"""
    try:
        if collection is None:
            return jsonify({
                'error': 'Database not connected',
                'message': 'MongoDB är inte ansluten'
            }), 500
        
        category = request.args.get('category')
        source = request.args.get('source')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        query = {}
        if category and category != 'alla':
            query['category'] = category
        if source:
            query['source'] = source
        
        # Begränsa till max 100 senaste artiklar
        MAX_ARTICLES = 100
        
        # Hämta de 100 senaste artikel-ID:na först
        latest_articles = list(collection.find(query, {'_id': 1})
                              .sort('published_date', -1)
                              .limit(MAX_ARTICLES))
        
        latest_ids = [article['_id'] for article in latest_articles]
        total = min(len(latest_ids), MAX_ARTICLES)
        
        # Hämta artiklar för aktuell sida från de 100 senaste
        skip = (page - 1) * per_page
        
        if skip >= total:
            articles = []
        else:
            query_with_ids = query.copy()
            query_with_ids['_id'] = {'$in': latest_ids}
            
            articles = collection.find(query_with_ids).sort('published_date', -1).skip(skip).limit(per_page)
            articles = list(articles)
        
        return jsonify({
            'articles': parse_json(articles),
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        logger.error(f"Fel i /api/articles: {e}")
        return jsonify({
            'error': str(e),
            'message': 'Ett fel uppstod vid hämtning av artiklar'
        }), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Hämta alla tillgängliga kategorier"""
    try:
        if collection is None:
            return jsonify({
                'error': 'Database not connected',
                'message': 'MongoDB är inte ansluten'
            }), 500
            
        categories = collection.distinct('category')
        return jsonify({'categories': categories})
        
    except Exception as e:
        logger.error(f"Fel i /api/categories: {e}")
        return jsonify({
            'error': str(e),
            'message': 'Ett fel uppstod vid hämtning av kategorier'
        }), 500

@app.route('/api/sources', methods=['GET'])
def get_sources():
    """Hämta alla tillgängliga källor"""
    try:
        if collection is None:
            return jsonify({
                'error': 'Database not connected',
                'message': 'MongoDB är inte ansluten'
            }), 500
            
        sources = collection.distinct('source')
        return jsonify({'sources': sources})
        
    except Exception as e:
        logger.error(f"Fel i /api/sources: {e}")
        return jsonify({
            'error': str(e),
            'message': 'Ett fel uppstod vid hämtning av källor'
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Hämta statistik om innehållet (baserat på max 100 senaste artiklar)"""
    try:
        if collection is None:
            return jsonify({
                'error': 'Database not connected',
                'message': 'MongoDB är inte ansluten'
            }), 500
        
        # Begränsa statistik till de 100 senaste artiklarna
        MAX_ARTICLES = 100
        
        # Hämta de 100 senaste artikel-ID:na
        latest_articles = list(collection.find({}, {'_id': 1})
                              .sort('published_date', -1)
                              .limit(MAX_ARTICLES))
        
        latest_ids = [article['_id'] for article in latest_articles]
        total_articles = len(latest_ids)
        
        # Statistik per källa
        pipeline = [
            {'$match': {'_id': {'$in': latest_ids}}},
            {'$group': {'_id': '$source', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        sources_stats = list(collection.aggregate(pipeline))
        
        # Statistik per kategori
        pipeline = [
            {'$match': {'_id': {'$in': latest_ids}}},
            {'$group': {'_id': '$category', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        category_stats = list(collection.aggregate(pipeline))
        
        latest = collection.find_one(sort=[('fetched_at', -1)])
        last_update = latest['fetched_at'] if latest else None

        if last_update and last_update.tzinfo is None:
            last_update = last_update.replace(tzinfo=timezone.utc)
        
        return jsonify({
            'total_articles': total_articles,
            'sources': parse_json(sources_stats),
            'categories': parse_json(category_stats),
            'last_update': last_update.isoformat() if last_update else None
        })
        
    except Exception as e:
        logger.error(f"Fel i /api/stats: {e}")
        return jsonify({
            'error': str(e),
            'message': 'Ett fel uppstod vid hämtning av statistik'
        }), 500

@app.route('/api/search', methods=['GET'])
def search_articles():
    """Sök bland artiklar (max 100 senaste)"""
    try:
        if collection is None:
            return jsonify({
                'error': 'Database not connected',
                'message': 'MongoDB är inte ansluten'
            }), 500
            
        query_text = request.args.get('q', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        if not query_text:
            return jsonify({'articles': [], 'total': 0})
        
        # Begränsa sökning till de 100 senaste artiklarna
        MAX_ARTICLES = 100
        
        latest_articles = list(collection.find({}, {'_id': 1})
                              .sort('published_date', -1)
                              .limit(MAX_ARTICLES))
        
        latest_ids = [article['_id'] for article in latest_articles]
        
        query = {
            '_id': {'$in': latest_ids},
            '$or': [
                {'title': {'$regex': query_text, '$options': 'i'}},
                {'description': {'$regex': query_text, '$options': 'i'}}
            ]
        }
        
        total = collection.count_documents(query)
        skip = (page - 1) * per_page
        articles = collection.find(query).sort('published_date', -1).skip(skip).limit(per_page)
        
        return jsonify({
            'articles': parse_json(list(articles)),
            'total': total,
            'page': page,
            'per_page': per_page,
            'query': query_text
        })
        
    except Exception as e:
        logger.error(f"Fel i /api/search: {e}")
        return jsonify({
            'error': str(e),
            'message': 'Ett fel uppstod vid sökning'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Kontrollera att API:et fungerar"""
    try:
        if collection is None:
            return jsonify({
                'status': 'error',
                'message': 'MongoDB är inte ansluten',
                'mongodb': 'disconnected'
            }), 500
            
        client.admin.command('ping')
        
        # Räkna artiklar (från de 100 senaste)
        MAX_ARTICLES = 100
        latest_articles = list(collection.find({}, {'_id': 1})
                              .sort('published_date', -1)
                              .limit(MAX_ARTICLES))
        article_count = len(latest_articles)
        
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'mongodb': 'connected',
            'articles': article_count,
            'max_articles_shown': MAX_ARTICLES
        })
        
    except Exception as e:
        logger.error(f"Health check misslyckades: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'mongodb': 'disconnected'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    logger.info(f"""
    ╔══════════════════════════════════════════════════╗
    ║     Svenska Nyheter - Flipboard Clone            ║
    ║                                                  ║
    ║  Server körs på: http://0.0.0.0:{port:<4}        ║
    ║  Max artiklar: 100 senaste                       ║
    ║                                                  ║
    ║  Tryck Ctrl+C för att stoppa                     ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    try:
        app.run(debug=debug, host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        if 'scheduler' in locals():
            scheduler.stop()
        logger.info("\n✋ Server stoppad")
