from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from bson import json_util
import json
from datetime import datetime, timezone
from scheduler import NewsScheduler
import os
import logging
import traceback

# Konfigurera logging fÃ¶r att se alla fel
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# HÃ¤mta konfiguration frÃ¥n miljÃ¶variabler eller config.py
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.environ.get('DATABASE_NAME', 'swedish_news')
COLLECTION_NAME = os.environ.get('COLLECTION_NAME', 'articles')

logger.info(f"ðŸ”§ MONGODB_URI Ã¤r satt till: {MONGODB_URI[:20]}...")  # Visa bara bÃ¶rjan av URI

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

# MongoDB connection med bÃ¤ttre felhantering
try:
    logger.info("ðŸ”— FÃ¶rsÃ¶ker ansluta till MongoDB...")
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    # Testa anslutning
    client.admin.command('ping')
    logger.info("âœ… MongoDB-anslutning lyckades!")
    
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
except Exception as e:
    logger.error(f"âŒ MongoDB-anslutningsfel: {e}")
    logger.error(f"âŒ FullstÃ¤ndigt fel: {traceback.format_exc()}")
    logger.error("âš ï¸  Servern startar men databas-operationer kommer att misslyckas")
    # SÃ¤tt collection till None sÃ¥ vi kan kolla det senare
    collection = None

# Starta scheduler i bakgrunden (endast om inte i test-miljÃ¶)
if not os.environ.get('TESTING'):
    try:
        scheduler = NewsScheduler()
        scheduler.start()
        logger.info("âœ… Scheduler startad!")
    except Exception as e:
        logger.error(f"âš ï¸  Scheduler kunde inte startas: {e}")

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
    """HÃ¤mta artiklar med filtrering och paginering"""
    try:
        # Kolla om MongoDB Ã¤r anslutet
        if collection is None:
            logger.error("âŒ MongoDB collection Ã¤r None!")
            return jsonify({
                'error': 'Database not connected',
                'message': 'MongoDB Ã¤r inte ansluten. Kolla MONGODB_URI miljÃ¶variabel.'
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
        
        total = collection.count_documents(query)
        skip = (page - 1) * per_page
        # Sortera först efter prioritet (lägre nummer = högre prioritet), sedan efter datum
        articles = collection.find(query).sort([
            ('priority', 1),           # Prioritet: 1, 2, 3 (lägre = bättre)
            ('published_date', -1)     # Nyast först
        ]).skip(skip).limit(per_page)
        
        return jsonify({
            'articles': parse_json(list(articles)),
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        logger.error(f"âŒ Fel i /api/articles: {e}")
        logger.error(f"âŒ FullstÃ¤ndigt fel: {traceback.format_exc()}")
        return jsonify({
            'error': str(e),
            'message': 'Ett fel uppstod vid hÃ¤mtning av artiklar'
        }), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """HÃ¤mta alla tillgÃ¤ngliga kategorier"""
    try:
        if collection is None:
            logger.error("âŒ MongoDB collection Ã¤r None!")
            return jsonify({
                'error': 'Database not connected',
                'message': 'MongoDB Ã¤r inte ansluten'
            }), 500
            
        categories = collection.distinct('category')
        logger.info(f"âœ“ Hittade {len(categories)} kategorier")
        return jsonify({'categories': categories})
    except Exception as e:
        logger.error(f"âŒ Fel i /api/categories: {e}")
        logger.error(f"âŒ FullstÃ¤ndigt fel: {traceback.format_exc()}")
        return jsonify({
            'error': str(e),
            'message': 'Ett fel uppstod vid hÃ¤mtning av kategorier'
        }), 500

@app.route('/api/sources', methods=['GET'])
def get_sources():
    """HÃ¤mta alla tillgÃ¤ngliga kÃ¤llor"""
    try:
        if collection is None:
            logger.error("âŒ MongoDB collection Ã¤r None!")
            return jsonify({
                'error': 'Database not connected',
                'message': 'MongoDB Ã¤r inte ansluten'
            }), 500
            
        sources = collection.distinct('source')
        logger.info(f"âœ“ Hittade {len(sources)} kÃ¤llor")
        return jsonify({'sources': sources})
    except Exception as e:
        logger.error(f"âŒ Fel i /api/sources: {e}")
        logger.error(f"âŒ FullstÃ¤ndigt fel: {traceback.format_exc()}")
        return jsonify({
            'error': str(e),
            'message': 'Ett fel uppstod vid hÃ¤mtning av kÃ¤llor'
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """HÃ¤mta statistik om innehÃ¥llet"""
    try:
        if collection is None:
            logger.error("âŒ MongoDB collection Ã¤r None!")
            return jsonify({
                'error': 'Database not connected',
                'message': 'MongoDB Ã¤r inte ansluten'
            }), 500
            
        total_articles = collection.count_documents({})
        
        pipeline = [
            {'$group': {'_id': '$source', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        sources_stats = list(collection.aggregate(pipeline))
        
        pipeline = [
            {'$group': {'_id': '$category', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        category_stats = list(collection.aggregate(pipeline))
        
        latest = collection.find_one(sort=[('fetched_at', -1)])
        last_update = latest['fetched_at'] if latest else None

        if last_update and last_update.tzinfo is None:
            # Antag att naiva datum frÃ¥n databasen Ã¤r UTC och lÃ¤gg till tidszonsinfo
            last_update = last_update.replace(tzinfo=timezone.utc)
        
        return jsonify({
            'total_articles': total_articles,
            'sources': parse_json(sources_stats),
            'categories': parse_json(category_stats),
            'last_update': last_update.isoformat() if last_update else None
        })
    except Exception as e:
        logger.error(f"âŒ Fel i /api/stats: {e}")
        logger.error(f"âŒ FullstÃ¤ndigt fel: {traceback.format_exc()}")
        return jsonify({
            'error': str(e),
            'message': 'Ett fel uppstod vid hÃ¤mtning av statistik'
        }), 500

@app.route('/api/search', methods=['GET'])
def search_articles():
    """SÃ¶k bland artiklar"""
    try:
        if collection is None:
            return jsonify({
                'error': 'Database not connected',
                'message': 'MongoDB Ã¤r inte ansluten'
            }), 500
            
        query_text = request.args.get('q', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        if not query_text:
            return jsonify({'articles': [], 'total': 0})
        
        query = {
            '$or': [
                {'title': {'$regex': query_text, '$options': 'i'}},
                {'description': {'$regex': query_text, '$options': 'i'}}
            ]
        }
        
        total = collection.count_documents(query)
        skip = (page - 1) * per_page
        # Sortera sökresultat efter prioritet och datum
        articles = collection.find(query).sort([
            ('priority', 1),
            ('published_date', -1)
        ]).skip(skip).limit(per_page)
        
        return jsonify({
            'articles': parse_json(list(articles)),
            'total': total,
            'page': page,
            'per_page': per_page,
            'query': query_text
        })
    except Exception as e:
        logger.error(f"âŒ Fel i /api/search: {e}")
        logger.error(f"âŒ FullstÃ¤ndigt fel: {traceback.format_exc()}")
        return jsonify({
            'error': str(e),
            'message': 'Ett fel uppstod vid sÃ¶kning'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Kontrollera att API:et fungerar"""
    try:
        # Testa MongoDB-anslutning
        if collection is None:
            return jsonify({
                'status': 'error',
                'message': 'MongoDB collection Ã¤r None',
                'mongodb': 'disconnected',
                'mongodb_uri': MONGODB_URI[:20] + '...'
            }), 500
            
        client.admin.command('ping')
        
        # RÃ¤kna artiklar
        article_count = collection.count_documents({})
        
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'mongodb': 'connected',
            'articles': article_count,
            'database': DATABASE_NAME,
            'collection': COLLECTION_NAME
        })
    except Exception as e:
        logger.error(f"âŒ Health check misslyckades: {e}")
        logger.error(f"âŒ FullstÃ¤ndigt fel: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'mongodb': 'disconnected',
            'mongodb_uri': MONGODB_URI[:20] + '...'
        }), 500

if __name__ == '__main__':
    # HÃ¤mta port frÃ¥n miljÃ¶variabel (fÃ¶r Heroku, Railway, etc.)
    port = int(os.environ.get('PORT', 5000))
    
    # Debug-lÃ¤ge endast lokalt
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    logger.info(f"""
    â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    â•‘     AI Nyheter - AI News Aggregator            â•‘
    â•‘                                                  â•‘
    â•‘  Server kÃ¶rs pÃ¥: http://0.0.0.0:{port:<4}        â•‘
    â•‘  API: http://0.0.0.0:{port}/api/articles         â•‘
    â•‘  MongoDB: {MONGODB_URI[:30]}...                  â•‘
    â•‘  Debug: {debug}                                  â•‘
    â•‘                                                  â•‘
    â•‘  Tryck Ctrl+C fÃ¶r att stoppa                     â•‘
    â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    """)
    
    try:
        app.run(debug=debug, host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        if 'scheduler' in locals():
            scheduler.stop()
        logger.info("\nâœ‹ Server stoppad")
