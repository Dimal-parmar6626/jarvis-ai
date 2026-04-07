"""NLP engine: intent recognition, entity extraction, context management."""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Intent definitions
# ---------------------------------------------------------------------------

INTENT_PATTERNS: Dict[str, List[str]] = {
    "greeting": [r"\b(hello|hi|hey|good morning|good afternoon|good evening|howdy)\b"],
    "farewell": [r"\b(bye|goodbye|see you|cya|later|quit|exit)\b"],
    "weather": [r"\b(weather|temperature|forecast|rain|sunny|cloudy|snow|humidity|wind)\b"],
    "news": [r"\b(news|headlines|latest|breaking|top stories)\b"],
    "search": [r"\b(search|look up|find|google|what is|who is|tell me about)\b"],
    "calendar": [r"\b(calendar|schedule|event|appointment|meeting|reminder|remind)\b"],
    "email": [r"\b(email|mail|send|compose|inbox|message)\b"],
    "music": [r"\b(music|play|song|artist|playlist|spotify|pause|stop|skip)\b"],
    "time": [r"\b(time|what time|clock|date|today|day)\b"],
    "timer": [r"\b(timer|alarm|stopwatch|countdown)\b"],
    "smart_home": [r"\b(light|lights|thermostat|temperature|lock|unlock|fan|switch)\b"],
    "system": [r"\b(open|launch|start|close|minimize|maximize|screenshot)\b"],
    "file": [r"\b(file|folder|create|delete|move|copy|read|write|list)\b"],
    "calculate": [r"\b(calculate|compute|math|add|subtract|multiply|divide|percent)\b"],
    "joke": [r"\b(joke|funny|laugh|humor|hilarious)\b"],
    "help": [r"\b(help|assist|support|what can you do|commands)\b"],
    "unknown": [],
}

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    """Extracted named entity."""

    text: str
    label: str
    start: int
    end: int


@dataclass
class NLPResult:
    """Result of NLP processing."""

    text: str
    intent: str
    confidence: float
    entities: List[Entity] = field(default_factory=list)
    sentiment: str = "neutral"
    keywords: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# NLP Engine
# ---------------------------------------------------------------------------


class NLPEngine:
    """Lightweight NLP engine with rule-based intent classification and spaCy entities."""

    def __init__(self, model_name: str = "en_core_web_sm"):
        self.model_name = model_name
        self._nlp = None
        self._context: List[NLPResult] = []
        self._max_context = 10

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, text: str) -> NLPResult:
        """Process user text and return NLP result."""
        clean = text.strip().lower()
        intent, confidence = self._classify_intent(clean)
        entities = self._extract_entities(text)
        sentiment = self._analyze_sentiment(clean)
        keywords = self._extract_keywords(clean)

        result = NLPResult(
            text=text,
            intent=intent,
            confidence=confidence,
            entities=entities,
            sentiment=sentiment,
            keywords=keywords,
        )
        self._update_context(result)
        return result

    def get_context(self) -> List[NLPResult]:
        """Return recent NLP context."""
        return list(self._context)

    def clear_context(self) -> None:
        """Clear conversation context."""
        self._context.clear()

    # ------------------------------------------------------------------
    # Intent classification
    # ------------------------------------------------------------------

    def _classify_intent(self, text: str) -> Tuple[str, float]:
        """Rule-based intent classification using regex patterns."""
        matches: Dict[str, int] = {}
        for intent, patterns in INTENT_PATTERNS.items():
            if not patterns:
                continue
            count = 0
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    count += 1
            if count:
                matches[intent] = count

        if not matches:
            return "unknown", 0.5

        best = max(matches, key=lambda k: matches[k])
        total = sum(matches.values())
        confidence = round(matches[best] / (total + 1e-9), 2)
        confidence = min(0.99, max(0.51, confidence))
        return best, confidence

    # ------------------------------------------------------------------
    # Entity extraction
    # ------------------------------------------------------------------

    def _extract_entities(self, text: str) -> List[Entity]:
        """Extract named entities using spaCy if available."""
        entities: List[Entity] = []
        nlp = self._get_nlp()
        if nlp is None:
            return self._rule_based_entities(text)
        try:
            doc = nlp(text)
            for ent in doc.ents:
                entities.append(
                    Entity(text=ent.text, label=ent.label_, start=ent.start_char, end=ent.end_char)
                )
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("spaCy entity extraction failed: %s", exc)
        return entities

    def _rule_based_entities(self, text: str) -> List[Entity]:
        """Simple rule-based entity extraction as fallback."""
        entities: List[Entity] = []
        # Dates
        date_pattern = r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|today|tomorrow|yesterday|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b"
        for m in re.finditer(date_pattern, text, re.IGNORECASE):
            entities.append(Entity(text=m.group(), label="DATE", start=m.start(), end=m.end()))
        # Times
        time_pattern = r"\b\d{1,2}:\d{2}(?:\s?[ap]m)?\b"
        for m in re.finditer(time_pattern, text, re.IGNORECASE):
            entities.append(Entity(text=m.group(), label="TIME", start=m.start(), end=m.end()))
        # Numbers
        num_pattern = r"\b\d+(?:\.\d+)?\b"
        for m in re.finditer(num_pattern, text):
            entities.append(Entity(text=m.group(), label="CARDINAL", start=m.start(), end=m.end()))
        return entities

    # ------------------------------------------------------------------
    # Sentiment analysis
    # ------------------------------------------------------------------

    def _analyze_sentiment(self, text: str) -> str:
        """Very simple lexicon-based sentiment analysis."""
        positive_words = {"good", "great", "awesome", "excellent", "happy", "love", "nice", "wonderful", "fantastic", "best"}
        negative_words = {"bad", "terrible", "awful", "hate", "worst", "horrible", "poor", "disappointed", "sad", "angry"}
        words = set(text.lower().split())
        pos = len(words & positive_words)
        neg = len(words & negative_words)
        if pos > neg:
            return "positive"
        if neg > pos:
            return "negative"
        return "neutral"

    # ------------------------------------------------------------------
    # Keyword extraction
    # ------------------------------------------------------------------

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords by removing stop words."""
        stop_words = {
            "i", "me", "my", "we", "you", "he", "she", "it", "they", "a", "an",
            "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "is",
            "are", "was", "were", "be", "been", "being", "have", "has", "had",
            "do", "does", "did", "will", "would", "could", "should", "may", "might",
            "can", "please", "that", "this", "what", "how", "when", "where", "who",
        }
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        return [w for w in words if w not in stop_words]

    # ------------------------------------------------------------------
    # Context management
    # ------------------------------------------------------------------

    def _update_context(self, result: NLPResult) -> None:
        self._context.append(result)
        if len(self._context) > self._max_context:
            self._context.pop(0)

    # ------------------------------------------------------------------
    # spaCy lazy loader
    # ------------------------------------------------------------------

    def _get_nlp(self):
        if self._nlp is False:
            return None
        if self._nlp is not None:
            return self._nlp
        try:
            import spacy  # type: ignore

            self._nlp = spacy.load(self.model_name)
        except Exception:  # pylint: disable=broad-except
            logger.warning("spaCy model '%s' not available. Using rule-based NLP.", self.model_name)
            self._nlp = False
            return None
        return self._nlp
