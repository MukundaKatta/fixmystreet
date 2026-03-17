"""Priority scoring engine for infrastructure reports."""

from __future__ import annotations

from fixmystreet.models import IssueCategory, PriorityLevel, Report


# Weight factors for priority calculation
_SEVERITY_WEIGHT = 0.4
_LOCATION_WEIGHT = 0.3
_FREQUENCY_WEIGHT = 0.3

# Location risk factors by neighborhood type keywords
_HIGH_RISK_LOCATIONS = {
    "school": 0.9,
    "hospital": 0.95,
    "downtown": 0.7,
    "highway": 0.85,
    "intersection": 0.8,
    "bridge": 0.9,
    "playground": 0.85,
    "main street": 0.7,
    "avenue": 0.6,
    "residential": 0.5,
}

# Category-based urgency multipliers
_CATEGORY_URGENCY: dict[IssueCategory, float] = {
    IssueCategory.POTHOLE: 0.7,
    IssueCategory.BROKEN_LIGHT: 0.65,
    IssueCategory.GRAFFITI: 0.25,
    IssueCategory.DAMAGED_SIGN: 0.6,
    IssueCategory.FLOODING: 0.9,
    IssueCategory.SIDEWALK_CRACK: 0.45,
    IssueCategory.FALLEN_TREE: 0.85,
    IssueCategory.ILLEGAL_DUMPING: 0.4,
}


class PriorityScorer:
    """Scores report priority based on severity, location, and frequency.

    The final score is a weighted combination of:
    - Severity: How dangerous or impactful the issue is
    - Location: Risk factor of the area (near schools, hospitals, etc.)
    - Frequency: How many similar reports exist in the area
    """

    def __init__(
        self,
        severity_weight: float = _SEVERITY_WEIGHT,
        location_weight: float = _LOCATION_WEIGHT,
        frequency_weight: float = _FREQUENCY_WEIGHT,
    ) -> None:
        self._severity_weight = severity_weight
        self._location_weight = location_weight
        self._frequency_weight = frequency_weight
        self._report_history: list[Report] = []

    def score(self, report: Report) -> float:
        """Compute a priority score for a report (0.0 to 1.0).

        Args:
            report: The report to score.

        Returns:
            Priority score between 0.0 and 1.0.
        """
        severity_score = self._compute_severity_score(report)
        location_score = self._compute_location_score(report)
        frequency_score = self._compute_frequency_score(report)

        total = (
            self._severity_weight * severity_score
            + self._location_weight * location_score
            + self._frequency_weight * frequency_score
        )

        return round(min(max(total, 0.0), 1.0), 3)

    def assign_priority(self, report: Report) -> PriorityLevel:
        """Assign a priority level to a report based on its score.

        Args:
            report: The report to prioritize.

        Returns:
            PriorityLevel enum value.
        """
        score = self.score(report)
        report.priority_score = score

        if score >= 0.75:
            level = PriorityLevel.CRITICAL
        elif score >= 0.55:
            level = PriorityLevel.HIGH
        elif score >= 0.35:
            level = PriorityLevel.MEDIUM
        else:
            level = PriorityLevel.LOW

        report.priority = level
        return level

    def add_to_history(self, report: Report) -> None:
        """Add a report to the history for frequency analysis."""
        self._report_history.append(report)

    def _compute_severity_score(self, report: Report) -> float:
        """Score based on issue severity and category urgency."""
        if report.issue is None:
            return 0.3

        base_severity = report.issue.severity
        category_urgency = _CATEGORY_URGENCY.get(report.issue.category, 0.5)

        return (base_severity + category_urgency) / 2.0

    def _compute_location_score(self, report: Report) -> float:
        """Score based on location risk factors."""
        address_lower = report.location.address.lower()
        neighborhood_lower = report.location.neighborhood.lower()
        combined = f"{address_lower} {neighborhood_lower}"

        max_risk = 0.3  # default baseline
        for keyword, risk in _HIGH_RISK_LOCATIONS.items():
            if keyword in combined:
                max_risk = max(max_risk, risk)

        return max_risk

    def _compute_frequency_score(self, report: Report) -> float:
        """Score based on similar reports in the same area."""
        if not self._report_history or report.issue is None:
            return 0.2

        nearby_count = 0
        same_category_count = 0

        for past_report in self._report_history:
            if past_report.report_id == report.report_id:
                continue

            # Check if in similar location (within ~500m approximation)
            lat_diff = abs(
                past_report.location.latitude - report.location.latitude
            )
            lon_diff = abs(
                past_report.location.longitude - report.location.longitude
            )

            if lat_diff < 0.005 and lon_diff < 0.005:
                nearby_count += 1
                if (
                    past_report.issue
                    and past_report.issue.category == report.issue.category
                ):
                    same_category_count += 1

        # More nearby same-category reports -> higher frequency score
        frequency = min((same_category_count * 0.2) + (nearby_count * 0.05), 1.0)
        return frequency
