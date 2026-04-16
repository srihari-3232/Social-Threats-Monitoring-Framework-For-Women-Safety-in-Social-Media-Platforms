import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any
from services.base_service import BaseService
from services.threat_detector import ThreatDetector
from config.settings import Config

class GNewsService(BaseService):
    def __init__(self):
        super().__init__("GNews")
        self.detector = ThreatDetector()
        self.api_key = Config.GNEWS_API_KEY
        self.base_url = "https://gnews.io/api/v4/search"

        if not self.api_key:
            raise ValueError("GNEWS_API_KEY not configured")

    def fetch_data(self, query: str = None, max_articles: int = 20) -> Dict[str, Any]:
        """Fetch fresh GNews data for women harassment/abuse detection"""
        if not query:
            query = "women harassment OR women abuse OR sexual harassment OR gender violence OR domestic violence"

        results = {
            "query": query,
            "articles_scanned": 0,
            "threats_found": 0,
            "detections": [],
            "source_info": {
                "platform": "GNews",
                "query": query,
                "scan_time": datetime.utcnow().isoformat(),
                "focus": "women_harassment_abuse"
            }
        }

        try:
            self.logger.info(f"Fetching fresh GNews articles for women harassment/abuse (max: {max_articles})")

            # Get articles from last 7 days for freshness
            from_date = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')

            params = {
                "q": query,
                "lang": "en",
                "max": min(100, max_articles),
                "token": self.api_key,
                "sortby": "publishedAt",
                "from": from_date
            }

            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if "articles" not in data:
                if "errors" in data:
                    error_msg = f"GNews API error: {data['errors']}"
                else:
                    error_msg = f"Unexpected GNews response: {data}"

                self.logger.error(error_msg)
                return self.format_response(results, success=False, message=error_msg)

            for article in data["articles"]:
                try:
                    results["articles_scanned"] += 1

                    # Analyze article content for women harassment/abuse
                    title = article.get("title", "")
                    description = article.get("description", "")
                    content = f"{title} {description}".strip()

                    if not content:
                        continue

                    analysis = self.detector.analyze(content)

                    if analysis["is_threat"]:
                        results["threats_found"] += 1

                        source_info = article.get("source", {})

                        results["detections"].append({
                            "type": "news_article",
                            "title": title,
                            "description": description,
                            "url": article.get("url", ""),
                            "source_name": source_info.get("name", "Unknown Source"),
                            "source_url": source_info.get("url", ""),
                            "author": "GNews Source",
                            "published_at": article.get("publishedAt", ""),
                            "image_url": article.get("image", ""),
                            "confidence": analysis["confidence"],
                            "keywords_found": analysis["keywords_found"],
                            "category": analysis["category"],
                            "content_preview": analysis["text_preview"],
                            "is_fresh_data": True
                        })

                except Exception as article_error:
                    self.logger.warning(f"Error processing GNews article: {article_error}")
                    continue

            message = f"Fresh GNews scan completed: {results['articles_scanned']} articles, {results['threats_found']} harassment/abuse cases found"
            self.logger.info(message)

            return self.format_response(results, success=True, message=message)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                error_msg = "GNews API access forbidden - check API key"
            elif e.response.status_code == 429:
                error_msg = "GNews API rate limit exceeded"
            else:
                error_msg = f"GNews HTTP error {e.response.status_code}"

            self.logger.error(error_msg)
            return self.format_response(results, success=False, error=e, message=error_msg)

        except Exception as e:
            error_msg = f"Error fetching fresh GNews data: {e}"
            self.logger.error(error_msg)
            return self.format_response(results, success=False, error=e, message=error_msg)
