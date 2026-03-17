"""Trend analysis for tracking issue patterns over time."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import numpy as np

from fixmystreet.models import IssueCategory, Report


@dataclass
class TrendResult:
    """Result of a trend analysis."""

    category: str
    period_label: str
    count: int
    change_percent: float  # Compared to previous period
    direction: str  # "increasing", "decreasing", "stable"


@dataclass
class TrendSummary:
    """Overall trend summary across all categories."""

    total_reports: int
    period_days: int
    trends: list[TrendResult] = field(default_factory=list)
    busiest_day: str = ""
    most_common_category: str = ""
    growth_rate: float = 0.0  # Overall reports growth rate


class TrendAnalyzer:
    """Tracks issue patterns and trends over time.

    Analyzes how report volumes change across time periods,
    identifies emerging issue types, and detects seasonal patterns.
    """

    def analyze(
        self,
        reports: list[Report],
        period_days: int = 7,
    ) -> TrendSummary:
        """Analyze trends in a set of reports.

        Args:
            reports: List of reports to analyze.
            period_days: Number of days per analysis period.

        Returns:
            TrendSummary with detailed results.
        """
        if not reports:
            return TrendSummary(total_reports=0, period_days=period_days)

        sorted_reports = sorted(reports, key=lambda r: r.reported_at)
        earliest = sorted_reports[0].reported_at
        latest = sorted_reports[-1].reported_at

        # Divide into periods
        periods = self._split_into_periods(sorted_reports, earliest, period_days)

        # Compute per-category trends
        trends = self._compute_category_trends(periods, period_days)

        # Find busiest day
        day_counts = Counter(r.reported_at.strftime("%A") for r in reports)
        busiest_day = day_counts.most_common(1)[0][0] if day_counts else ""

        # Most common category
        cat_counts = Counter(
            r.issue.category.value for r in reports if r.issue
        )
        most_common = cat_counts.most_common(1)[0][0] if cat_counts else ""

        # Overall growth rate
        growth_rate = self._compute_growth_rate(periods)

        return TrendSummary(
            total_reports=len(reports),
            period_days=period_days,
            trends=trends,
            busiest_day=busiest_day,
            most_common_category=most_common,
            growth_rate=round(growth_rate, 2),
        )

    def category_breakdown(
        self, reports: list[Report]
    ) -> dict[str, int]:
        """Count reports by category.

        Args:
            reports: List of reports.

        Returns:
            Dictionary mapping category names to counts.
        """
        counts: dict[str, int] = {}
        for category in IssueCategory:
            counts[category.value] = 0
        for report in reports:
            if report.issue:
                counts[report.issue.category.value] += 1
        return counts

    def daily_volume(
        self, reports: list[Report], days: int = 30
    ) -> dict[str, int]:
        """Compute daily report volumes.

        Args:
            reports: List of reports.
            days: Number of days to look back.

        Returns:
            Dictionary mapping date strings to report counts.
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent = [r for r in reports if r.reported_at >= cutoff]

        volume: dict[str, int] = {}
        for report in recent:
            date_str = report.reported_at.strftime("%Y-%m-%d")
            volume[date_str] = volume.get(date_str, 0) + 1

        return dict(sorted(volume.items()))

    def _split_into_periods(
        self,
        reports: list[Report],
        start: datetime,
        period_days: int,
    ) -> list[list[Report]]:
        """Split reports into time periods."""
        periods: list[list[Report]] = []
        current_period: list[Report] = []
        period_end = start + timedelta(days=period_days)

        for report in reports:
            while report.reported_at >= period_end:
                periods.append(current_period)
                current_period = []
                period_end += timedelta(days=period_days)
            current_period.append(report)

        if current_period:
            periods.append(current_period)

        return periods

    def _compute_category_trends(
        self,
        periods: list[list[Report]],
        period_days: int,
    ) -> list[TrendResult]:
        """Compute per-category trends across periods."""
        if len(periods) < 2:
            return []

        current = periods[-1]
        previous = periods[-2]

        current_counts = Counter(
            r.issue.category.value for r in current if r.issue
        )
        previous_counts = Counter(
            r.issue.category.value for r in previous if r.issue
        )

        trends = []
        for category in IssueCategory:
            curr = current_counts.get(category.value, 0)
            prev = previous_counts.get(category.value, 0)

            if prev > 0:
                change = ((curr - prev) / prev) * 100
            elif curr > 0:
                change = 100.0
            else:
                change = 0.0

            if change > 10:
                direction = "increasing"
            elif change < -10:
                direction = "decreasing"
            else:
                direction = "stable"

            trends.append(
                TrendResult(
                    category=category.value,
                    period_label=f"last_{period_days}_days",
                    count=curr,
                    change_percent=round(change, 1),
                    direction=direction,
                )
            )

        return trends

    def _compute_growth_rate(self, periods: list[list[Report]]) -> float:
        """Compute overall growth rate using period counts."""
        if len(periods) < 2:
            return 0.0

        counts = np.array([len(p) for p in periods], dtype=float)
        if len(counts) < 2 or counts[0] == 0:
            return 0.0

        # Simple average growth rate
        rates = np.diff(counts) / np.maximum(counts[:-1], 1.0)
        return float(np.mean(rates) * 100)
