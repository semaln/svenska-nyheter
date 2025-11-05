from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from bson import json_util
import json
from datetime import datetime
from scheduler import NewsScheduler
import os

# Hämta konfiguration från miljövariabler eller config.py
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.environ.get('DATABASE_NAME', 'swedish_news')
COLLECTION_NAME = os.environ.get('COLLECTION_NAME', 'articles')

app = Flask(__name__, static_folder='static')
CORS(app)

# MongoDB connection
try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    # Testa anslutning
    client.admin.command('ping')
    print("✅ MongoDB-anslutning lyckades!")
except Exception as e:
    print(f"❌ MongoDB-anslutningsfel: {e}")
    print("⚠️  Servern startar men databas-operationer kommer att misslyckas")

db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Starta scheduler i bakgrunden (endast om inte i test-miljö)
if not os.environ.get('TESTING'):
    try:
        scheduler = NewsScheduler()
        scheduler.start()
        print("✅ Scheduler startad!")
    except Exception as e:
        print(f"⚠️  Scheduler kunde inte startas: {e}")

def parse_json(data):
    """Konvertera MongoDB ObjectId till JSON"""
    return json.loads(json_util.dumps(data))

@app.route('/')
def index():
    """Servera frontend"""
    return send_from_directory('static', 'index.html')

@app.route('/api/articles', methods=['GET'])
def get_articles():
    """Hämta artiklar med filtrering och paginering"""
    try:
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
        articles = collection.find(query).sort('published_date', -1).skip(skip).limit(per_page)
        
        return jsonify({
            'articles': parse_json(list(articles)),
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Hämta alla tillgängliga kategorier"""
    try:
        categories = collection.distinct('category')
        return jsonify({'categories': categories})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sources', methods=['GET'])
def get_sources():
    """Hämta alla tillgängliga källor"""
    try:
        sources = collection.distinct('source')
        return jsonify({'sources': sources})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Hämta statistik om innehållet"""
    try:
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
        
        return jsonify({
            'total_articles': total_articles,
            'sources': parse_json(sources_stats),
            'categories': parse_json(category_stats),
            'last_update': last_update.isoformat() if last_update else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_articles():
    """Sök bland artiklar"""
    try:
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
        articles = collection.find(query).sort('published_date', -1).skip(skip).limit(per_page)
        
        return jsonify({
            'articles': parse_json(list(articles)),
            'total': total,
            'page': page,
            'per_page': per_page,
            'query': query_text
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Kontrollera att API:et fungerar"""
    try:
        # Testa MongoDB-anslutning
        client.admin.command('ping')
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'mongodb': 'connected'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'mongodb': 'disconnected'
        }), 500

if __name__ == '__main__':
    # Hämta port från miljövariabel (för Heroku, Railway, etc.)
    port = int(os.environ.get('PORT', 5000))
    
    # Debug-läge endast lokalt
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print(f"""
    ╔══════════════════════════════════════════════════╗
    ║     Svenska Nyheter - Flipboard Clone            ║
    ║                                                  ║
    ║  Server körs på: http://0.0.0.0:{port:<4}          ║
    ║  API: http://0.0.0.0:{port}/api/articles        ║
    ║  Debug: {debug}                                    ║
    ║                                                  ║
    ║  Tryck Ctrl+C för att stoppa                    ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    try:
        app.run(debug=debug, host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        if 'scheduler' in locals():
            scheduler.stop()
        print("\n✋ Server stoppad")
