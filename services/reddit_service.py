import praw
from datetime import datetime
from typing import Dict, List, Any
from services.base_service import BaseService
from services.threat_detector import ThreatDetector
from config.settings import Config

class RedditService(BaseService):
    def __init__(self):
        super().__init__("Reddit")
        self.detector = ThreatDetector()
        self.reddit = None
        self._connect()

    def _connect(self):
        """Connect to Reddit API with error handling"""
        try:
            self.reddit = praw.Reddit(
                client_id=Config.REDDIT_CLIENT_ID,
                client_secret=Config.REDDIT_CLIENT_SECRET,
                username=Config.REDDIT_USERNAME,
                password=Config.REDDIT_PASSWORD,
                user_agent="WomenHarassmentMonitor/2.0"
            )
            # Test connection
            self.reddit.user.me()
            self.logger.info("Successfully connected to Reddit API")
        except Exception as e:
            self.logger.error(f"Failed to connect to Reddit: {e}")
            raise ConnectionError(f"Reddit API connection failed: {e}")

    def fetch_data(self, subreddit_name: str = "TwoXChromosomes", limit: int = 10) -> Dict[str, Any]:
        """Fetch fresh Reddit data for women harassment/abuse detection"""
        results = {
            "subreddit": subreddit_name,
            "posts_scanned": 0,
            "threats_found": 0,
            "detections": [],
            "source_info": {
                "platform": "Reddit",
                "subreddit": f"r/{subreddit_name}",
                "scan_time": datetime.utcnow().isoformat(),
                "focus": "women_harassment_abuse"
            }
        }

        try:
            if not self.reddit:
                raise ConnectionError("Reddit client not initialized")

            subreddit = self.reddit.subreddit(subreddit_name)
            self.logger.info(f"Fetching fresh data from r/{subreddit_name} (limit: {limit})")

            # Get fresh posts using 'new' to ensure latest content
            for post in subreddit.new(limit=limit):
                try:
                    results["posts_scanned"] += 1

                    # Analyze post content
                    content = f"{post.title} {post.selftext or ''}".strip()
                    if content:
                        analysis = self.detector.analyze(content)

                        if analysis["is_threat"]:
                            results["threats_found"] += 1
                            results["detections"].append({
                                "type": "post",
                                "title": post.title,
                                "author": str(post.author) if post.author else "[deleted]",
                                "content": analysis["text_preview"],
                                "post_url": f"https://reddit.com{post.permalink}",
                                "confidence": analysis["confidence"],
                                "keywords_found": analysis["keywords_found"],
                                "created_utc": datetime.fromtimestamp(post.created_utc).isoformat(),
                                "score": post.score,
                                "num_comments": post.num_comments,
                                "category": analysis["category"]
                            })

                    # Analyze fresh comments
                    try:
                        post.comments.replace_more(limit=0)
                        for comment in post.comments.list()[:5]:
                            if hasattr(comment, 'body') and comment.body and comment.body != '[deleted]':
                                analysis = self.detector.analyze(comment.body)
                                if analysis["is_threat"]:
                                    results["threats_found"] += 1
                                    results["detections"].append({
                                        "type": "comment",
                                        "post_title": post.title,
                                        "author": str(comment.author) if comment.author else "[deleted]",
                                        "content": analysis["text_preview"],
                                        "comment_url": f"https://reddit.com{comment.permalink}",
                                        "confidence": analysis["confidence"],
                                        "keywords_found": analysis["keywords_found"],
                                        "created_utc": datetime.fromtimestamp(comment.created_utc).isoformat(),
                                        "score": comment.score,
                                        "category": analysis["category"]
                                    })
                    except Exception as comment_error:
                        self.logger.warning(f"Error processing comments: {comment_error}")

                except Exception as post_error:
                    self.logger.warning(f"Error processing post: {post_error}")
                    continue

            message = f"Fresh Reddit scan completed: {results['posts_scanned']} posts, {results['threats_found']} harassment/abuse cases found"
            self.logger.info(message)

            return self.format_response(results, success=True, message=message)

        except Exception as e:
            error_msg = f"Error fetching fresh Reddit data: {e}"
            self.logger.error(error_msg)
            return self.format_response(results, success=False, error=e, message=error_msg)
