import tweepy
from datetime import datetime, timedelta
from typing import Dict, List, Any
from services.base_service import BaseService
from services.threat_detector import ThreatDetector
from config.settings import Config

class TwitterService(BaseService):
    def __init__(self):
        super().__init__("Twitter")
        self.detector = ThreatDetector()
        self.client = None
        self._connect()

    def _connect(self):
        """Connect to Twitter API with error handling"""
        try:
            if not Config.TWITTER_BEARER_TOKEN:
                raise ValueError("TWITTER_BEARER_TOKEN not configured")

            self.client = tweepy.Client(bearer_token=Config.TWITTER_BEARER_TOKEN)
            self.logger.info("Successfully connected to Twitter API")

        except Exception as e:
            self.logger.error(f"Failed to connect to Twitter: {e}")
            raise ConnectionError(f"Twitter API connection failed: {e}")

    def fetch_data(self, query: str = None, max_tweets: int = 50) -> Dict[str, Any]:
        """Fetch fresh Twitter data for women harassment/abuse detection"""
        if not query:
            # Default query focused on women harassment/abuse
            query = "(women harassment OR women abuse OR sexual harassment OR gender violence OR domestic violence OR stalking women) -is:retweet lang:en"

        results = {
            "query": query,
            "tweets_scanned": 0,
            "threats_found": 0,
            "detections": [],
            "source_info": {
                "platform": "Twitter",
                "query": query,
                "scan_time": datetime.utcnow().isoformat(),
                "focus": "women_harassment_abuse"
            }
        }

        try:
            if not self.client:
                raise ConnectionError("Twitter client not initialized")

            self.logger.info(f"Fetching fresh tweets for women harassment/abuse (max: {max_tweets})")

            # Get fresh tweets from last 7 days to ensure new content
            start_time = datetime.utcnow() - timedelta(days=7)

            # Use Paginator to get fresh tweets
            tweets = tweepy.Paginator(
                self.client.search_recent_tweets,
                query=query,
                tweet_fields=["text", "author_id", "created_at", "public_metrics", "context_annotations"],
                user_fields=["username", "name", "verified", "public_metrics"],
                expansions=["author_id"],
                start_time=start_time,
                max_results=min(100, max_tweets)
            ).flatten(limit=max_tweets)

            # Build user lookup dictionary
            users_dict = {}

            for tweet in tweets:
                try:
                    results["tweets_scanned"] += 1

                    # Get username for better source attribution
                    username = "unknown_user"
                    if hasattr(tweet, 'author_id') and tweet.author_id:
                        if tweet.author_id not in users_dict:
                            try:
                                user = self.client.get_user(id=tweet.author_id)
                                users_dict[tweet.author_id] = user.data.username if user.data else "unknown_user"
                            except:
                                users_dict[tweet.author_id] = "unknown_user"
                        username = users_dict[tweet.author_id]

                    # Analyze tweet for women harassment/abuse content
                    analysis = self.detector.analyze(tweet.text)

                    if analysis["is_threat"]:
                        results["threats_found"] += 1
                        results["detections"].append({
                            "type": "tweet",
                            "content": analysis["text_preview"],
                            "tweet_id": str(tweet.id),
                            "author_id": str(tweet.author_id) if tweet.author_id else "unknown",
                            "username": username,
                            "tweet_url": f"https://twitter.com/{username}/status/{tweet.id}",
                            "created_at": tweet.created_at.isoformat() if tweet.created_at else datetime.utcnow().isoformat(),
                            "confidence": analysis["confidence"],
                            "keywords_found": analysis["keywords_found"],
                            "category": analysis["category"],
                            "public_metrics": getattr(tweet, 'public_metrics', {}),
                            "is_fresh_data": True  # Flag to indicate this is fresh data
                        })

                except Exception as tweet_error:
                    self.logger.warning(f"Error processing tweet: {tweet_error}")
                    continue

            message = f"Fresh Twitter scan completed: {results['tweets_scanned']} tweets, {results['threats_found']} harassment/abuse cases found"
            self.logger.info(message)

            return self.format_response(results, success=True, message=message)

        except Exception as e:
            error_msg = f"Error fetching fresh Twitter data: {e}"
            self.logger.error(error_msg)
            return self.format_response(results, success=False, error=e, message=error_msg)
