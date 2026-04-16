import os

class ThreatDetector:
    def __init__(self):
        keywords_str = os.getenv("KEYWORDS", "harass,creep,stalker,abuse,threat")
        self.keywords = [k.strip().lower() for k in keywords_str.split(",")]
        print(f"✅ Loaded {len(self.keywords)} threat keywords")

    def detect_threat(self, text):
        """Simple keyword-based threat detection"""
        if not text:
            return False

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)

    def analyze(self, text):
        """Analyze text and return results"""
        is_threat = self.detect_threat(text)
        return {
            "is_threat": is_threat,
            "confidence": 0.8 if is_threat else 0.0,
            "text_preview": text[:100] + "..." if len(text) > 100 else text
        }
