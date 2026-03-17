"""Issue classification engine using keyword matching and scoring."""

from __future__ import annotations

from fixmystreet.models import Issue, IssueCategory


# Keyword mappings for each issue category with weights
_CATEGORY_KEYWORDS: dict[IssueCategory, dict[str, float]] = {
    IssueCategory.POTHOLE: {
        "pothole": 1.0,
        "hole": 0.7,
        "crater": 0.8,
        "road damage": 0.9,
        "pavement": 0.5,
        "asphalt": 0.6,
        "road surface": 0.7,
        "bump": 0.4,
        "dip": 0.4,
        "flat tire": 0.6,
    },
    IssueCategory.BROKEN_LIGHT: {
        "broken light": 1.0,
        "street light": 0.8,
        "lamp": 0.6,
        "streetlight": 0.9,
        "dark": 0.4,
        "no light": 0.7,
        "light out": 0.9,
        "flickering": 0.7,
        "bulb": 0.5,
        "illumination": 0.4,
    },
    IssueCategory.GRAFFITI: {
        "graffiti": 1.0,
        "spray paint": 0.9,
        "vandalism": 0.7,
        "tagged": 0.6,
        "mural": 0.3,
        "defaced": 0.8,
        "paint": 0.4,
        "writing on wall": 0.8,
        "marker": 0.3,
    },
    IssueCategory.DAMAGED_SIGN: {
        "damaged sign": 1.0,
        "sign": 0.6,
        "stop sign": 0.8,
        "bent sign": 0.9,
        "missing sign": 0.9,
        "broken sign": 1.0,
        "road sign": 0.7,
        "street sign": 0.7,
        "signpost": 0.7,
        "knocked over": 0.5,
    },
    IssueCategory.FLOODING: {
        "flooding": 1.0,
        "flood": 0.9,
        "water": 0.4,
        "puddle": 0.6,
        "drain": 0.6,
        "blocked drain": 0.9,
        "standing water": 0.8,
        "waterlogged": 0.9,
        "overflow": 0.7,
        "sewer": 0.6,
    },
    IssueCategory.SIDEWALK_CRACK: {
        "sidewalk crack": 1.0,
        "sidewalk": 0.6,
        "cracked": 0.5,
        "uneven": 0.5,
        "trip hazard": 0.8,
        "pavement crack": 0.9,
        "broken sidewalk": 0.9,
        "footpath": 0.6,
        "walkway": 0.5,
        "curb": 0.4,
    },
    IssueCategory.FALLEN_TREE: {
        "fallen tree": 1.0,
        "tree down": 0.9,
        "tree fell": 0.9,
        "branch": 0.5,
        "fallen branch": 0.8,
        "uprooted": 0.9,
        "tree blocking": 0.8,
        "dead tree": 0.7,
        "leaning tree": 0.7,
        "tree limb": 0.6,
    },
    IssueCategory.ILLEGAL_DUMPING: {
        "illegal dumping": 1.0,
        "dumping": 0.8,
        "trash": 0.5,
        "garbage": 0.5,
        "waste": 0.5,
        "abandoned": 0.4,
        "fly tipping": 0.9,
        "junk": 0.6,
        "debris": 0.5,
        "litter": 0.5,
        "mattress": 0.7,
    },
}

# Base severity for each category
_CATEGORY_SEVERITY: dict[IssueCategory, float] = {
    IssueCategory.POTHOLE: 0.7,
    IssueCategory.BROKEN_LIGHT: 0.6,
    IssueCategory.GRAFFITI: 0.3,
    IssueCategory.DAMAGED_SIGN: 0.6,
    IssueCategory.FLOODING: 0.8,
    IssueCategory.SIDEWALK_CRACK: 0.5,
    IssueCategory.FALLEN_TREE: 0.8,
    IssueCategory.ILLEGAL_DUMPING: 0.5,
}


class IssueClassifier:
    """Classifies infrastructure issue reports into categories.

    Uses keyword matching with weighted scoring to determine the most
    likely issue category from a text description.
    """

    def __init__(self) -> None:
        self._keywords = _CATEGORY_KEYWORDS
        self._severity = _CATEGORY_SEVERITY

    def classify(self, description: str) -> Issue:
        """Classify a text description into an infrastructure issue.

        Args:
            description: Free-text description of the issue.

        Returns:
            An Issue with the best-matching category and confidence score.
        """
        scores = self._compute_scores(description)

        if not scores:
            return Issue(
                category=IssueCategory.POTHOLE,
                confidence=0.0,
                description=description,
                severity=0.3,
                keywords_matched=[],
            )

        best_category = max(scores, key=lambda c: scores[c][0])
        best_score, matched_keywords = scores[best_category]

        # Normalize confidence to 0-1 range
        max_possible = sum(
            sorted(self._keywords[best_category].values(), reverse=True)[:3]
        )
        confidence = min(best_score / max(max_possible, 1.0), 1.0)

        severity = self._compute_severity(best_category, description)

        return Issue(
            category=best_category,
            confidence=round(confidence, 3),
            description=description,
            severity=round(severity, 3),
            keywords_matched=matched_keywords,
        )

    def classify_batch(self, descriptions: list[str]) -> list[Issue]:
        """Classify multiple descriptions at once.

        Args:
            descriptions: List of text descriptions.

        Returns:
            List of classified Issues.
        """
        return [self.classify(desc) for desc in descriptions]

    def _compute_scores(
        self, description: str
    ) -> dict[IssueCategory, tuple[float, list[str]]]:
        """Compute matching scores for each category."""
        text_lower = description.lower()
        scores: dict[IssueCategory, tuple[float, list[str]]] = {}

        for category, keywords in self._keywords.items():
            total_score = 0.0
            matched: list[str] = []

            for keyword, weight in keywords.items():
                if keyword in text_lower:
                    total_score += weight
                    matched.append(keyword)

            if matched:
                scores[category] = (total_score, matched)

        return scores

    def _compute_severity(self, category: IssueCategory, description: str) -> float:
        """Compute severity based on category and description modifiers."""
        base = self._severity.get(category, 0.5)
        text_lower = description.lower()

        # Severity modifiers based on description keywords
        if any(w in text_lower for w in ["large", "big", "major", "severe", "dangerous"]):
            base = min(base + 0.2, 1.0)
        if any(w in text_lower for w in ["small", "minor", "tiny", "slight"]):
            base = max(base - 0.2, 0.1)
        if any(w in text_lower for w in ["urgent", "emergency", "immediate"]):
            base = min(base + 0.3, 1.0)
        if any(w in text_lower for w in ["school", "hospital", "elderly", "children"]):
            base = min(base + 0.15, 1.0)

        return base

    @property
    def categories(self) -> list[IssueCategory]:
        """Return all supported categories."""
        return list(IssueCategory)
