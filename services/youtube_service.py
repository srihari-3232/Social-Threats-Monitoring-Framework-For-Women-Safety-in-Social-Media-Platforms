from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
from typing import Dict, List, Any
from services.base_service import BaseService
from services.threat_detector import ThreatDetector
from config.settings import Config

class YouTubeService(BaseService):
    def __init__(self):
        super().__init__("YouTube")
        self.detector = ThreatDetector()
        self.youtube = None
        self._connect()

    def _connect(self):
        """Connect to YouTube API with error handling"""
        try:
            if not Config.YOUTUBE_API_KEY:
                raise ValueError("YOUTUBE_API_KEY not configured")

            self.youtube = build("youtube", "v3", developerKey=Config.YOUTUBE_API_KEY)
            self.logger.info("Successfully connected to YouTube API")

        except Exception as e:
            self.logger.error(f"Failed to connect to YouTube: {e}")
            raise ConnectionError(f"YouTube API connection failed: {e}")

    def fetch_data(self, query: str = None, max_results: int = 20) -> Dict[str, Any]:
        """Fetch fresh YouTube data for women harassment/abuse detection"""
        if not query:
            query = "women harassment OR sexual harassment OR gender violence OR women abuse"

        results = {
            "query": query,
            "videos_scanned": 0,
            "threats_found": 0,
            "detections": [],
            "source_info": {
                "platform": "YouTube",
                "query": query,
                "scan_time": datetime.utcnow().isoformat(),
                "focus": "women_harassment_abuse"
            }
        }

        try:
            if not self.youtube:
                raise ConnectionError("YouTube client not initialized")

            self.logger.info(f"Fetching fresh YouTube videos for women harassment/abuse (max: {max_results})")

            # Search for fresh videos (published in last week for freshness)
            published_after = (datetime.utcnow() - timedelta(days=7)).isoformat() + 'Z'

            search_request = self.youtube.search().list(
                q=query,
                part="snippet",
                order="date",  # Get most recent first
                maxResults=min(50, max_results),
                type="video",
                publishedAfter=published_after,
                regionCode="US"
            )
            search_response = search_request.execute()

            for item in search_response.get("items", []):
                try:
                    results["videos_scanned"] += 1

                    # Analyze video title and description
                    title = item["snippet"]["title"]
                    description = item["snippet"]["description"]
                    content = f"{title} {description}"

                    analysis = self.detector.analyze(content)

                    if analysis["is_threat"]:
                        results["threats_found"] += 1

                        detection = {
                            "type": "video",
                            "title": title,
                            "description": description[:300] + "..." if len(description) > 300 else description,
                            "channel_title": item["snippet"]["channelTitle"],
                            "channel_id": item["snippet"]["channelId"],
                            "video_id": item["id"]["videoId"],
                            "video_url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                            "published_at": item["snippet"]["publishedAt"],
                            "confidence": analysis["confidence"],
                            "keywords_found": analysis["keywords_found"],
                            "category": analysis["category"],
                            "thumbnails": item["snippet"].get("thumbnails", {}),
                            "is_fresh_data": True
                        }

                        results["detections"].append(detection)

                        # Get fresh comments for videos with harassment content
                        try:
                            comments_request = self.youtube.commentThreads().list(
                                videoId=item["id"]["videoId"],
                                part="snippet",
                                maxResults=10,
                                order="time"  # Get most recent comments
                            )
                            comments_response = comments_request.execute()

                            for comment_item in comments_response.get("items", []):
                                comment_text = comment_item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                                comment_analysis = self.detector.analyze(comment_text)

                                if comment_analysis["is_threat"]:
                                    results["threats_found"] += 1
                                    results["detections"].append({
                                        "type": "comment",
                                        "video_title": title,
                                        "video_url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                                        "comment_text": comment_analysis["text_preview"],
                                        "author": comment_item["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
                                        "author_channel_id": comment_item["snippet"]["topLevelComment"]["snippet"].get("authorChannelId", ""),
                                        "published_at": comment_item["snippet"]["topLevelComment"]["snippet"]["publishedAt"],
                                        "confidence": comment_analysis["confidence"],
                                        "keywords_found": comment_analysis["keywords_found"],
                                        "category": comment_analysis["category"],
                                        "is_fresh_data": True
                                    })

                        except HttpError as comment_error:
                            if comment_error.resp.status == 403:
                                self.logger.warning(f"Comments disabled for video {item['id']['videoId']}")
                            else:
                                self.logger.warning(f"Error fetching comments: {comment_error}")

                except Exception as video_error:
                    self.logger.warning(f"Error processing video: {video_error}")
                    continue

            message = f"Fresh YouTube scan completed: {results['videos_scanned']} videos, {results['threats_found']} harassment/abuse cases found"
            self.logger.info(message)

            return self.format_response(results, success=True, message=message)

        except Exception as e:
            error_msg = f"Error fetching fresh YouTube data: {e}"
            self.logger.error(error_msg)
            return self.format_response(results, success=False, error=e, message=error_msg)
