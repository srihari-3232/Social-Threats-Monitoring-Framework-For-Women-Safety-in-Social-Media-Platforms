#!/usr/bin/env python3
"""
Social Threat Monitor - Flask API + Authentication System
Individual endpoints for each service with fresh data fetching
"""

from flask import Flask, jsonify, request, session, redirect
from flask_cors import CORS
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

import json
import traceback
import sys
from datetime import datetime
from typing import Dict, Any

from services.reddit_service import RedditService
from services.twitter_service import TwitterService
from services.youtube_service import YouTubeService
from services.gnews_service import GNewsService
from services.newsapi_service import NewsAPIService
from utils.logger import setup_logger

# --------------------------------------------------------------------
# FLASK APP SETUP
# --------------------------------------------------------------------

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

app.secret_key = "sameer-super-secret-key"  # change if you want

logger = setup_logger("flask_app")

# --------------------------------------------------------------------
# SQLITE AUTH SETUP
# --------------------------------------------------------------------

DB_NAME = "users.db"


def init_db():
    """Create users table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def create_user(name: str, email: str, password: str) -> bool:
    """Create a new user. Returns True if success, False if email exists."""
    hashed_pw = generate_password_hash(password)

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, hashed_pw),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # Email already exists
        return False


def validate_user(email: str, password: str):
    """
    Validate login credentials.
    Returns (True, name, user_id) if valid, else (False, None, None)
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, password FROM users WHERE email = ?", (email,)
    )
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[2], password):
        return True, user[1], user[0]
    return False, None, None


# Initialize DB at startup
init_db()

# --------------------------------------------------------------------
# AUTH ROUTES
# --------------------------------------------------------------------

@app.route("/signup", methods=["POST"])
def signup():
    """
    Sign up a new user.
    Expects form-data:
    - name
    - email
    - password
    """
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")

    if not name or not email or not password:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    if create_user(name, email, password):
        return jsonify({"success": True, "message": "Account created successfully"})
    else:
        return jsonify({"success": False, "message": "Email already registered"}), 409


@app.route("/login", methods=["POST"])
def login():
    """
    Login user.
    Expects form-data:
    - email
    - password
    """
    email = request.form.get("email")
    password = request.form.get("password")

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password required"}), 400

    status, user_name, user_id = validate_user(email, password)

    if status:
        session["user_id"] = user_id
        session["name"] = user_name
        return jsonify({"success": True, "redirect": "/dashboard"})
    else:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401


@app.route("/dashboard", methods=["GET"])
def dashboard():
    """
    Protected dashboard route.
    Only accessible if logged in.
    """
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    return jsonify({
        "success": True,
        "message": f"Welcome {session['name']} to the Social Threat Dashboard!"
    })


@app.route("/logout", methods=["GET"])
def logout():
    """Clear session and log out."""
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"})


# --------------------------------------------------------------------
# ORIGINAL THREAT MONITOR API
# --------------------------------------------------------------------

# Service instances cache
service_instances = {}


def get_service_instance(service_name: str):
    """Get or create service instance with error handling"""
    if service_name not in service_instances:
        try:
            if service_name == "reddit":
                service_instances[service_name] = RedditService()
            elif service_name == "twitter":
                service_instances[service_name] = TwitterService()
            elif service_name == "youtube":
                service_instances[service_name] = YouTubeService()
            elif service_name == "gnews":
                service_instances[service_name] = GNewsService()
            elif service_name == "newsapi":
                service_instances[service_name] = NewsAPIService()
            else:
                raise ValueError(f"Unknown service: {service_name}")

            logger.info(f"✅ {service_name.capitalize()} service initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize {service_name}: {e}")
            return None

    return service_instances[service_name]


@app.route('/api/reddit/scan', methods=['GET'])
def scan_reddit():
    """
    Scan Reddit for threats
    Query parameters:
    - subreddit: subreddit name (default: TwoXChromosomes)
    - limit: number of posts to scan (default: 10)
    """
    try:
        subreddit = request.args.get('subreddit', 'TwoXChromosomes')
        limit = request.args.get('limit', 10, type=int)

        service = get_service_instance('reddit')
        if not service:
            return jsonify({
                "success": False,
                "error": "Reddit service unavailable",
                "service": "reddit",
                "timestamp": datetime.utcnow().isoformat()
            }), 503

        logger.info(f"🔍 Reddit scan requested: r/{subreddit}, limit={limit}")
        result = service.fetch_data(subreddit_name=subreddit, limit=limit)

        return jsonify(result)

    except Exception as e:
        logger.error(f"❌ Reddit scan error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
            "service": "reddit",
            "timestamp": datetime.utcnow().isoformat()
        }), 500


@app.route('/api/twitter/scan', methods=['GET'])
def scan_twitter():
    """
    Scan Twitter for threats
    Query parameters:
    - query: search query (default: harassment OR abuse)
    - limit: max tweets to scan (default: 50)
    """
    try:
        query = request.args.get('query', 'harassment OR abuse OR threat')
        limit = request.args.get('limit', 50, type=int)

        service = get_service_instance('twitter')
        if not service:
            return jsonify({
                "success": False,
                "error": "Twitter service unavailable",
                "service": "twitter",
                "timestamp": datetime.utcnow().isoformat()
            }), 503

        logger.info(f"🔍 Twitter scan requested: query='{query}', limit={limit}")
        result = service.fetch_data(query=query, max_tweets=limit)

        return jsonify(result)

    except Exception as e:
        logger.error(f"❌ Twitter scan error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
            "service": "twitter",
            "timestamp": datetime.utcnow().isoformat()
        }), 500


@app.route('/api/youtube/scan', methods=['GET'])
def scan_youtube():
    """
    Scan YouTube for threats
    Query parameters:
    - query: search query (default: women harassment)
    - limit: max videos to scan (default: 20)
    """
    try:
        query = request.args.get('query', 'women harassment')
        limit = request.args.get('limit', 20, type=int)

        service = get_service_instance('youtube')
        if not service:
            return jsonify({
                "success": False,
                "error": "YouTube service unavailable",
                "service": "youtube",
                "timestamp": datetime.utcnow().isoformat()
            }), 503

        logger.info(f"🔍 YouTube scan requested: query='{query}', limit={limit}")
        result = service.fetch_data(query=query, max_results=limit)

        return jsonify(result)

    except Exception as e:
        logger.error(f"❌ YouTube scan error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
            "service": "youtube",
            "timestamp": datetime.utcnow().isoformat()
        }), 500


@app.route('/api/gnews/scan', methods=['GET'])
def scan_gnews():
    """
    Scan GNews for threats
    Query parameters:
    - query: search query (default: women harassment OR gender violence)
    - limit: max articles to scan (default: 20)
    """
    try:
        query = request.args.get('query', 'women harassment OR gender violence OR sexual harassment')
        limit = request.args.get('limit', 20, type=int)

        service = get_service_instance('gnews')
        if not service:
            return jsonify({
                "success": False,
                "error": "GNews service unavailable",
                "service": "gnews",
                "timestamp": datetime.utcnow().isoformat()
            }), 503

        logger.info(f"🔍 GNews scan requested: query='{query}', limit={limit}")
        result = service.fetch_data(query=query, max_articles=limit)

        return jsonify(result)

    except Exception as e:
        logger.error(f"❌ GNews scan error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
            "service": "gnews",
            "timestamp": datetime.utcnow().isoformat()
        }), 500


@app.route('/api/newsapi/scan', methods=['GET'])
def scan_newsapi():
    """
    Scan NewsAPI for threats
    Query parameters:
    - query: search query (default: women harassment OR abuse)
    - limit: max articles to scan (default: 20)
    """
    try:
        query = request.args.get('query', 'women harassment OR women abuse OR sexual harassment')
        limit = request.args.get('limit', 20, type=int)

        service = get_service_instance('newsapi')
        if not service:
            return jsonify({
                "success": False,
                "error": "NewsAPI service unavailable",
                "service": "newsapi",
                "timestamp": datetime.utcnow().isoformat()
            }), 503

        logger.info(f"🔍 NewsAPI scan requested: query='{query}', limit={limit}")
        result = service.fetch_data(query=query, max_articles=limit)

        return jsonify(result)

    except Exception as e:
        logger.error(f"❌ NewsAPI scan error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
            "service": "newsapi",
            "timestamp": datetime.utcnow().isoformat()
        }), 500


@app.route('/api/scan/all', methods=['GET'])
def scan_all_services():
    """
    Scan all available services
    Query parameters:
    - query: search query for Twitter, YouTube, and news services
    - subreddit: Reddit subreddit to scan
    - limit: limit for each service
    """
    try:
        query = request.args.get('query', 'harassment OR abuse')
        subreddit = request.args.get('subreddit', 'TwoXChromosomes')
        limit = request.args.get('limit', 20, type=int)

        results = {
            "scan_timestamp": datetime.utcnow().isoformat(),
            "total_threats_found": 0,
            "services_scanned": 0,
            "services": {}
        }

        # Define service configurations
        gnews_query = request.args.get(
            'gnews_query',
            'women harassment OR gender violence OR sexual harassment')

        service_configs = [
        ("reddit", {"subreddit_name": subreddit, "limit": limit}),
        ("twitter", {"query": query, "max_tweets": limit}),
        ("youtube", {"query": query, "max_results": limit}),
        ("gnews", {"query": gnews_query, "max_articles": limit}),
        ("newsapi", {"query": query, "max_articles": limit})
          ]

# service_configs = [
        #     ("reddit", {"subreddit_name": subreddit, "limit": limit}),
        #     ("twitter", {"query": query, "max_tweets": limit}),
        #     ("youtube", {"query": query, "max_results": limit}),
        #     ("gnews", {"query": query, "max_articles": limit}),
        #     ("newsapi", {"query": query, "max_articles": limit})
        # ]

        for service_name, config in service_configs:
            try:
                service = get_service_instance(service_name)
                if service:
                    logger.info(f"🔍 Scanning {service_name}")
                    result = service.fetch_data(**config)
                    results["services"][service_name] = result

                    if result.get("success"):
                        threats_found = result.get("data", {}).get("threats_found", 0)
                        results["total_threats_found"] += threats_found
                        results["services_scanned"] += 1
                else:
                    results["services"][service_name] = {
                        "success": False,
                        "error": f"{service_name} service unavailable",
                        "timestamp": datetime.utcnow().isoformat()
                    }

            except Exception as e:
                logger.error(f"❌ Error scanning {service_name}: {e}")
                results["services"][service_name] = {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }

        results["scan_completed"] = datetime.utcnow().isoformat()
        logger.info(f"✅ All services scan completed: {results['total_threats_found']} total threats found")

        return jsonify(results)

    except Exception as e:
        logger.error(f"❌ All services scan error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        services_status = {}

        for service_name in ["reddit", "twitter", "youtube", "gnews", "newsapi"]:
            try:
                service = get_service_instance(service_name)
                services_status[service_name] = "available" if service else "unavailable"
            except Exception:
                services_status[service_name] = "error"

        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": services_status,
            "endpoints": [
                "/api/reddit/scan",
                "/api/twitter/scan",
                "/api/youtube/scan",
                "/api/gnews/scan",
                "/api/newsapi/scan",
                "/api/scan/all",
                "/api/health"
            ]
        })

    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500


# --------------------------------------------------------------------
# ERROR HANDLERS
# --------------------------------------------------------------------

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "GET /api/reddit/scan?subreddit=<name>&limit=<num>",
            "GET /api/twitter/scan?query=<text>&limit=<num>",
            "GET /api/youtube/scan?query=<text>&limit=<num>",
            "GET /api/gnews/scan?query=<text>&limit=<num>",
            "GET /api/newsapi/scan?query=<text>&limit=<num>",
            "GET /api/scan/all",
            "GET /api/health",
            "POST /signup",
            "POST /login",
            "GET /dashboard",
            "GET /logout"
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "timestamp": datetime.utcnow().isoformat()
    }), 500


# --------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------

if __name__ == '__main__':
    logger.info("🚀 Starting Social Threat Monitor API Server with Auth")
    logger.info("📋 Available endpoints:")
    logger.info("   POST /signup")
    logger.info("   POST /login")
    logger.info("   GET  /dashboard")
    logger.info("   GET  /logout")
    logger.info("   GET /api/reddit/scan?subreddit=<name>&limit=<num>")
    logger.info("   GET /api/twitter/scan?query=<text>&limit=<num>")
    logger.info("   GET /api/youtube/scan?query=<text>&limit=<num>")
    logger.info("   GET /api/gnews/scan?query=<text>&limit=<num>")
    logger.info("   GET /api/newsapi/scan?query=<text>&limit=<num>")
    logger.info("   GET /api/scan/all?query=<text>&subreddit=<name>&limit=<num>")
    logger.info("   GET /api/health")

    app.run(debug=True, host='0.0.0.0', port=5000)























# #!/usr/bin/env python3
# """
# Social Threat Monitor - Flask API
# Individual endpoints for each service with fresh data fetching
# """
#
# from flask import Flask, jsonify, request
# from flask_cors import CORS
# import json
# import traceback
# import sys
# from datetime import datetime
# from typing import Dict, Any
#
# from services.reddit_service import RedditService
# from services.twitter_service import TwitterService
# from services.youtube_service import YouTubeService
# from services.gnews_service import GNewsService
# from services.newsapi_service import NewsAPIService
# from utils.logger import setup_logger
#
# app = Flask(__name__)
# CORS(app)  # Enable CORS for frontend integration
#
# logger = setup_logger("flask_app")
#
# # Service instances cache
# service_instances = {}
#
# def get_service_instance(service_name: str):
#     """Get or create service instance with error handling"""
#     if service_name not in service_instances:
#         try:
#             if service_name == "reddit":
#                 service_instances[service_name] = RedditService()
#             elif service_name == "twitter":
#                 service_instances[service_name] = TwitterService()
#             elif service_name == "youtube":
#                 service_instances[service_name] = YouTubeService()
#             elif service_name == "gnews":
#                 service_instances[service_name] = GNewsService()
#             elif service_name == "newsapi":
#                 service_instances[service_name] = NewsAPIService()
#             else:
#                 raise ValueError(f"Unknown service: {service_name}")
#
#             logger.info(f"✅ {service_name.capitalize()} service initialized")
#
#         except Exception as e:
#             logger.error(f"❌ Failed to initialize {service_name}: {e}")
#             return None
#
#     return service_instances[service_name]
#
# @app.route('/api/reddit/scan', methods=['GET'])
# def scan_reddit():
#     """
#     Scan Reddit for threats
#     Query parameters:
#     - subreddit: subreddit name (default: TwoXChromosomes)
#     - limit: number of posts to scan (default: 10)
#     """
#     try:
#         subreddit = request.args.get('subreddit', 'TwoXChromosomes')
#         limit = request.args.get('limit', 10, type=int)
#
#         service = get_service_instance('reddit')
#         if not service:
#             return jsonify({
#                 "success": False,
#                 "error": "Reddit service unavailable",
#                 "service": "reddit",
#                 "timestamp": datetime.utcnow().isoformat()
#             }), 503
#
#         logger.info(f"🔍 Reddit scan requested: r/{subreddit}, limit={limit}")
#         result = service.fetch_data(subreddit_name=subreddit, limit=limit)
#
#         return jsonify(result)
#
#     except Exception as e:
#         logger.error(f"❌ Reddit scan error: {e}")
#         logger.error(traceback.format_exc())
#         return jsonify({
#             "success": False,
#             "error": str(e),
#             "service": "reddit",
#             "timestamp": datetime.utcnow().isoformat()
#         }), 500
#
# @app.route('/api/twitter/scan', methods=['GET'])
# def scan_twitter():
#     """
#     Scan Twitter for threats
#     Query parameters:
#     - query: search query (default: harassment OR abuse)
#     - limit: max tweets to scan (default: 50)
#     """
#     try:
#         query = request.args.get('query', 'harassment OR abuse OR threat')
#         limit = request.args.get('limit', 50, type=int)
#
#         service = get_service_instance('twitter')
#         if not service:
#             return jsonify({
#                 "success": False,
#                 "error": "Twitter service unavailable",
#                 "service": "twitter",
#                 "timestamp": datetime.utcnow().isoformat()
#             }), 503
#
#         logger.info(f"🔍 Twitter scan requested: query='{query}', limit={limit}")
#         result = service.fetch_data(query=query, max_tweets=limit)
#
#         return jsonify(result)
#
#     except Exception as e:
#         logger.error(f"❌ Twitter scan error: {e}")
#         logger.error(traceback.format_exc())
#         return jsonify({
#             "success": False,
#             "error": str(e),
#             "service": "twitter",
#             "timestamp": datetime.utcnow().isoformat()
#         }), 500
#
# @app.route('/api/youtube/scan', methods=['GET'])
# def scan_youtube():
#     """
#     Scan YouTube for threats
#     Query parameters:
#     - query: search query (default: women harassment)
#     - limit: max videos to scan (default: 20)
#     """
#     try:
#         query = request.args.get('query', 'women harassment')
#         limit = request.args.get('limit', 20, type=int)
#
#         service = get_service_instance('youtube')
#         if not service:
#             return jsonify({
#                 "success": False,
#                 "error": "YouTube service unavailable",
#                 "service": "youtube",
#                 "timestamp": datetime.utcnow().isoformat()
#             }), 503
#
#         logger.info(f"🔍 YouTube scan requested: query='{query}', limit={limit}")
#         result = service.fetch_data(query=query, max_results=limit)
#
#         return jsonify(result)
#
#     except Exception as e:
#         logger.error(f"❌ YouTube scan error: {e}")
#         logger.error(traceback.format_exc())
#         return jsonify({
#             "success": False,
#             "error": str(e),
#             "service": "youtube",
#             "timestamp": datetime.utcnow().isoformat()
#         }), 500
#
# @app.route('/api/gnews/scan', methods=['GET'])
# def scan_gnews():
#     """
#     Scan GNews for threats
#     Query parameters:
#     - query: search query (default: women harassment OR gender violence)
#     - limit: max articles to scan (default: 20)
#     """
#     try:
#         query = request.args.get('query', 'women harassment OR gender violence OR sexual harassment')
#         limit = request.args.get('limit', 20, type=int)
#
#         service = get_service_instance('gnews')
#         if not service:
#             return jsonify({
#                 "success": False,
#                 "error": "GNews service unavailable",
#                 "service": "gnews",
#                 "timestamp": datetime.utcnow().isoformat()
#             }), 503
#
#         logger.info(f"🔍 GNews scan requested: query='{query}', limit={limit}")
#         result = service.fetch_data(query=query, max_articles=limit)
#
#         return jsonify(result)
#
#     except Exception as e:
#         logger.error(f"❌ GNews scan error: {e}")
#         logger.error(traceback.format_exc())
#         return jsonify({
#             "success": False,
#             "error": str(e),
#             "service": "gnews",
#             "timestamp": datetime.utcnow().isoformat()
#         }), 500
#
# @app.route('/api/newsapi/scan', methods=['GET'])
# def scan_newsapi():
#     """
#     Scan NewsAPI for threats
#     Query parameters:
#     - query: search query (default: women harassment OR abuse)
#     - limit: max articles to scan (default: 20)
#     """
#     try:
#         query = request.args.get('query', 'women harassment OR women abuse OR sexual harassment')
#         limit = request.args.get('limit', 20, type=int)
#
#         service = get_service_instance('newsapi')
#         if not service:
#             return jsonify({
#                 "success": False,
#                 "error": "NewsAPI service unavailable",
#                 "service": "newsapi",
#                 "timestamp": datetime.utcnow().isoformat()
#             }), 503
#
#         logger.info(f"🔍 NewsAPI scan requested: query='{query}', limit={limit}")
#         result = service.fetch_data(query=query, max_articles=limit)
#
#         return jsonify(result)
#
#     except Exception as e:
#         logger.error(f"❌ NewsAPI scan error: {e}")
#         logger.error(traceback.format_exc())
#         return jsonify({
#             "success": False,
#             "error": str(e),
#             "service": "newsapi",
#             "timestamp": datetime.utcnow().isoformat()
#         }), 500
#
# @app.route('/api/scan/all', methods=['GET'])
# def scan_all_services():
#     """
#     Scan all available services
#     Query parameters:
#     - query: search query for Twitter, YouTube, and news services
#     - subreddit: Reddit subreddit to scan
#     - limit: limit for each service
#     """
#     try:
#         query = request.args.get('query', 'harassment OR abuse')
#         subreddit = request.args.get('subreddit', 'TwoXChromosomes')
#         limit = request.args.get('limit', 20, type=int)
#
#         results = {
#             "scan_timestamp": datetime.utcnow().isoformat(),
#             "total_threats_found": 0,
#             "services_scanned": 0,
#             "services": {}
#         }
#
#         # Define service configurations
#         service_configs = [
#             ("reddit", {"subreddit_name": subreddit, "limit": limit}),
#             ("twitter", {"query": query, "max_tweets": limit}),
#             ("youtube", {"query": query, "max_results": limit}),
#             ("gnews", {"query": query, "max_articles": limit}),
#             ("newsapi", {"query": query, "max_articles": limit})
#         ]
#
#         for service_name, config in service_configs:
#             try:
#                 service = get_service_instance(service_name)
#                 if service:
#                     logger.info(f"🔍 Scanning {service_name}")
#                     result = service.fetch_data(**config)
#                     results["services"][service_name] = result
#
#                     if result.get("success"):
#                         threats_found = result.get("data", {}).get("threats_found", 0)
#                         results["total_threats_found"] += threats_found
#                         results["services_scanned"] += 1
#                 else:
#                     results["services"][service_name] = {
#                         "success": False,
#                         "error": f"{service_name} service unavailable",
#                         "timestamp": datetime.utcnow().isoformat()
#                     }
#
#             except Exception as e:
#                 logger.error(f"❌ Error scanning {service_name}: {e}")
#                 results["services"][service_name] = {
#                     "success": False,
#                     "error": str(e),
#                     "timestamp": datetime.utcnow().isoformat()
#                 }
#
#         results["scan_completed"] = datetime.utcnow().isoformat()
#         logger.info(f"✅ All services scan completed: {results['total_threats_found']} total threats found")
#
#         return jsonify(results)
#
#     except Exception as e:
#         logger.error(f"❌ All services scan error: {e}")
#         logger.error(traceback.format_exc())
#         return jsonify({
#             "success": False,
#             "error": str(e),
#             "timestamp": datetime.utcnow().isoformat()
#         }), 500
#
# @app.route('/api/health', methods=['GET'])
# def health_check():
#     """Health check endpoint"""
#     try:
#         services_status = {}
#
#         for service_name in ["reddit", "twitter", "youtube", "gnews", "newsapi"]:
#             try:
#                 service = get_service_instance(service_name)
#                 services_status[service_name] = "available" if service else "unavailable"
#             except Exception:
#                 services_status[service_name] = "error"
#
#         return jsonify({
#             "status": "healthy",
#             "timestamp": datetime.utcnow().isoformat(),
#             "services": services_status,
#             "endpoints": [
#                 "/api/reddit/scan",
#                 "/api/twitter/scan",
#                 "/api/youtube/scan",
#                 "/api/gnews/scan",
#                 "/api/newsapi/scan",
#                 "/api/scan/all",
#                 "/api/health"
#             ]
#         })
#
#     except Exception as e:
#         return jsonify({
#             "status": "unhealthy",
#             "error": str(e),
#             "timestamp": datetime.utcnow().isoformat()
#         }), 500
#
# @app.errorhandler(404)
# def not_found(error):
#     return jsonify({
#         "error": "Endpoint not found",
#         "available_endpoints": [
#             "GET /api/reddit/scan?subreddit=<name>&limit=<num>",
#             "GET /api/twitter/scan?query=<text>&limit=<num>",
#             "GET /api/youtube/scan?query=<text>&limit=<num>",
#             "GET /api/gnews/scan?query=<text>&limit=<num>",
#             "GET /api/newsapi/scan?query=<text>&limit=<num>",
#             "GET /api/scan/all",
#             "GET /api/health"
#         ]
#     }), 404
#
# @app.errorhandler(500)
# def internal_error(error):
#     return jsonify({
#         "error": "Internal server error",
#         "timestamp": datetime.utcnow().isoformat()
#     }), 500
#
# if __name__ == '__main__':
#     logger.info("🚀 Starting Social Threat Monitor API Server")
#     logger.info("📋 Available endpoints:")
#     logger.info("   GET /api/reddit/scan?subreddit=<name>&limit=<num>")
#     logger.info("   GET /api/twitter/scan?query=<text>&limit=<num>")
#     logger.info("   GET /api/youtube/scan?query=<text>&limit=<num>")
#     logger.info("   GET /api/gnews/scan?query=<text>&limit=<num>")
#     logger.info("   GET /api/newsapi/scan?query=<text>&limit=<num>")
#     logger.info("   GET /api/scan/all?query=<text>&subreddit=<name>&limit=<num>")
#     logger.info("   GET /api/health")
#
#     app.run(debug=True, host='0.0.0.0', port=5000)
#
