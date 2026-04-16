import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any
from services.base_service import BaseService
from services.threat_detector import ThreatDetector
from config.settings import Config

class NewsAPIService(BaseService):
    def __init__(self):
        super().__init__("NewsAPI")
        self.detector = ThreatDetector()
        self.api_key = Config.NEWSAPI_KEY
        self.base_url = "https://newsapi.org/v2/everything"

        if not self.api_key:
            raise ValueError("NEWSAPI_KEY not configured")

    def fetch_data(self, query: str = None, max_articles: int = 20) -> Dict[str, Any]:
        """Fetch fresh NewsAPI data for women harassment/abuse detection"""
        if not query:
            query = "women harassment OR women abuse OR sexual harassment OR gender violence OR domestic violence"

        results = {
            "query": query,
            "articles_scanned": 0,
            "threats_found": 0,
            "detections": [],
            "source_info": {
                "platform": "NewsAPI",
                "query": query,
                "scan_time": datetime.utcnow().isoformat(),
                "focus": "women_harassment_abuse"
            }
        }

        try:
            self.logger.info(f"Fetching fresh NewsAPI articles for women harassment/abuse (max: {max_articles})")

            # Get articles from last 7 days for freshness
            from_date = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')

            params = {
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": min(100, max_articles),
                "from": from_date,
                "apiKey": self.api_key
            }

            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != "ok":
                error_msg = f"NewsAPI error: {data.get('message', 'Unknown error')}"
                self.logger.error(error_msg)
                return self.format_response(results, success=False, message=error_msg)

            for article in data.get("articles", []):
                try:
                    results["articles_scanned"] += 1

                    # Analyze article content for women harassment/abuse
                    title = article.get("title", "") or ""
                    description = article.get("description", "") or ""
                    content_text = article.get("content", "") or ""

                    full_content = f"{title} {description} {content_text}".strip()

                    if not full_content:
                        continue

                    analysis = self.detector.analyze(full_content)

                    if analysis["is_threat"]:
                        results["threats_found"] += 1

                        source_info = article.get("source", {})

                        results["detections"].append({
                            "type": "news_article",
                            "title": title,
                            "description": description,
                            "author": article.get("author", "Unknown Author"),
                            "url": article.get("url", ""),
                            "source_name": source_info.get("name", "Unknown"),
                            "source_id": source_info.get("id", ""),
                            "published_at": article.get("publishedAt", ""),
                            "url_to_image": article.get("urlToImage", ""),
                            "confidence": analysis["confidence"],
                            "keywords_found": analysis["keywords_found"],
                            "category": analysis["category"],
                            "content_preview": analysis["text_preview"],
                            "is_fresh_data": True
                        })

                except Exception as article_error:
                    self.logger.warning(f"Error processing NewsAPI article: {article_error}")
                    continue

            message = f"Fresh NewsAPI scan completed: {results['articles_scanned']} articles, {results['threats_found']} harassment/abuse cases found"
            self.logger.info(message)

            return self.format_response(results, success=True, message=message)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                error_msg = "NewsAPI unauthorized - check API key"
            elif e.response.status_code == 429:
                error_msg = "NewsAPI rate limit exceeded"
            else:
                error_msg = f"NewsAPI HTTP error {e.response.status_code}"

            self.logger.error(error_msg)
            return self.format_response(results, success=False, error=e, message=error_msg)

        except Exception as e:
            error_msg = f"Error fetching fresh NewsAPI data: {e}"
            self.logger.error(error_msg)
            return self.format_response(results, success=False, error=e, message=error_msg)
