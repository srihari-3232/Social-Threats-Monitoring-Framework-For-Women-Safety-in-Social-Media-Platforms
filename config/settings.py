import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Reddit API
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
    REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
    REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")

    # Twitter API
    TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

    # YouTube API
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

    # News APIs
    GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
    NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

    # Threat Detection
    THREAT_KEYWORDS = os.getenv("KEYWORDS", "harass,creep,stalker,abuse,threat,violence,assault")

    # Limits
    REDDIT_POST_LIMIT = int(os.getenv("REDDIT_POST_LIMIT", "10"))
    TWITTER_MAX_TWEETS = int(os.getenv("TWITTER_MAX_TWEETS", "50"))
    YOUTUBE_MAX_RESULTS = int(os.getenv("YOUTUBE_MAX_RESULTS", "20"))
    NEWS_MAX_ARTICLES = int(os.getenv("NEWS_MAX_ARTICLES", "20"))
    GNEWS_MAX_ARTICLES = int(os.getenv("GNEWS_MAX_ARTICLES", "20"))
