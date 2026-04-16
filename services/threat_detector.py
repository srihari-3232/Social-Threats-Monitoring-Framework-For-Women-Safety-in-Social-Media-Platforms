import re
from typing import List, Dict, Any
from datetime import datetime
from config.settings import Config
from utils.logger import setup_logger

class ThreatDetector:
    def __init__(self):
        self.logger = setup_logger("threat_detector")
        # Women harassment/abuse specific keywords
        self.keywords = [
            # Core harassment
            "harassment", "harass", "abuse", "abused", "abusing", "stalker", "stalking",
            "creep", "creepy", "threat", "violence", "assault", "rape", "sexual harassment",
            "domestic violence", "gender violence", "intimidate", "molest", "grope",
            "catcall", "victim", "predator",

            # Misogynistic slurs (high frequency on social media)
            "slut", "whore", "bitch", "cunt", "hoe", "thot", "skank", "tramp", "slag",
            "loose", "desperate", "golddigger", "feminazi", "feminism",

            # Online threats & doxxing
            "doxx", "doxxed", "swatting", "revenge porn", "deepfake", "nonconsensual",
            "following me", "watching me", "know where you live", "find you", "track you",

            # Violence & suicide threats
            "kill you", "hurt your family", "die", "suicide", "jump", "cut yourself",
            "bullet in head", "beat you", "gangbang", "forced", "trafficked",

            # Sexual violence specifics
            "pedophile", "incest", "child abuse", "underage", "grooming", "sextortion",
            "unsolicited dick pic", "nudes or else",

            # Body/appearance shaming
            "fat pig", "ugly", "butterface", "manface", "tits", "ass", "objectify",

            # Professional/workplace
            "HR complaint", "hostile environment", "quid pro quo", "glass ceiling",
            "mansplaining", "not like other girls",

            # Cyber-specific attacks
            "cyberbullying", "trolling", "flaming", "griefing", "shock trolling",
            "mob attack", "pile on", "cancel her",

            # Relationship abuse
            "cheater", "homewrecker", "mistress", "side chick", "baby mama drama",

            # Dehumanization terms
            "thing", "object", "vermin", "prostitute", "psychopath", "lying bitch",

            # Intersectional threats
            "race traitor", "blasphemy", "deadnaming", "TERF", "handmaid"
        ]
        self.logger.info(f"Loaded {len(self.keywords)} women harassment/abuse keywords")  # ← FIXED: 8 spaces indent

    def detect_threat(self, text: str) -> bool:
        """Enhanced threat detection focused on women harassment/abuse"""
        if not text:
            return False

        try:
            text_lower = text.lower()

            # Direct keyword matching for women harassment/abuse
            keyword_match = any(keyword in text_lower for keyword in self.keywords)

            # Specific patterns for women harassment/abuse
            harassment_patterns = [
                r'\b(women?|girls?|female)\s+(harassment|abuse|violence|assault)',
                r'\b(sexual|domestic)\s+(harassment|abuse|violence|assault)',
                r'\b(stalking|harassing|abusing)\s+(women?|girls?|female)',
                r'\b(gender\s+based|gender)\s+(violence|harassment|abuse)',
                r'\b(workplace|street)\s+(harassment|abuse)',
                r'\b(catcalling|groping|molesting)',
                r'\b(victim\s+of|survivor\s+of)\s+(harassment|abuse|assault)'
            ]

            pattern_match = any(re.search(pattern, text_lower) for pattern in harassment_patterns)

            return keyword_match or pattern_match

        except Exception as e:
            self.logger.error(f"Error in threat detection: {e}")
            return False

    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze text for women harassment/abuse content"""
        try:
            is_threat = self.detect_threat(text)
            confidence = 0.0
            keywords_found = []

            if is_threat:
                # Find specific keywords in text
                text_lower = text.lower()
                keywords_found = [kw for kw in self.keywords if kw in text_lower]

                # Calculate confidence based on keyword matches and context
                base_confidence = 0.4
                keyword_bonus = len(keywords_found) * 0.1

                # Higher confidence for specific women harassment terms
                high_priority_terms = ["sexual harassment", "domestic violence", "gender violence", "stalking"]
                if any(term in text_lower for term in high_priority_terms):
                    base_confidence += 0.3

                confidence = min(base_confidence + keyword_bonus, 0.95)

            return {
                "is_threat": is_threat,
                "confidence": round(confidence, 2),
                "text_preview": text[:200] + "..." if len(text) > 200 else text,
                "keywords_found": keywords_found,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "category": "women_harassment_abuse" if is_threat else "safe"
            }

        except Exception as e:
            self.logger.error(f"Error analyzing text: {e}")
            return {
                "is_threat": False,
                "confidence": 0.0,
                "text_preview": "Error analyzing text",
                "keywords_found": [],
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "category": "error"
            }
