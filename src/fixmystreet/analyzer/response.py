"""Response time analysis measuring city performance."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

from fixmystreet.models import IssueCategory, PriorityLevel, Report, ReportStatus


@dataclass
class ResponseMetrics:
    """Metrics for city response performance."""

    total_resolved: int = 0
    total_open: int = 0
    avg_response_hours: float = 0.0
    median_response_hours: float = 0.0
    min_response_hours: float = 0.0
    max_response_hours: float = 0.0
    p90_response_hours: float = 0.0
    avg_acknowledgment_hours: float = 0.0
    on_time_percent: float = 0.0
    by_category: dict[str, float] = field(default_factory=dict)
    by_priority: dict[str, float] = field(default_factory=dict)


# Target response times in hours per priority level
_TARGET_HOURS: dict[PriorityLevel, float] = {
    PriorityLevel.CRITICAL: 24.0,
    PriorityLevel.HIGH: 72.0,
    PriorityLevel.MEDIUM: 168.0,  # 1 week
    PriorityLevel.LOW: 336.0,  # 2 weeks
}


class ResponseTimeAnalyzer:
    """Measures and evaluates city response performance.

    Tracks how quickly reports move through the lifecycle and
    evaluates performance against target response times.
    """

    def __init__(
        self, target_hours: dict[PriorityLevel, float] | None = None
    ) -> None:
        self._target_hours = target_hours or _TARGET_HOURS

    def analyze(self, reports: list[Report]) -> ResponseMetrics:
        """Compute response time metrics from reports.

        Args:
            reports: List of reports to analyze.

        Returns:
            ResponseMetrics with computed statistics.
        """
        resolved = [
            r for r in reports
            if r.status == ReportStatus.RESOLVED and r.resolution
        ]
        open_reports = [r for r in reports if r.status != ReportStatus.RESOLVED]

        metrics = ResponseMetrics(
            total_resolved=len(resolved),
            total_open=len(open_reports),
        )

        if not resolved:
            return metrics

        # Resolution times
        times = np.array(
            [r.resolution.resolution_time_hours for r in resolved]
        )
        metrics.avg_response_hours = round(float(np.mean(times)), 2)
        metrics.median_response_hours = round(float(np.median(times)), 2)
        metrics.min_response_hours = round(float(np.min(times)), 2)
        metrics.max_response_hours = round(float(np.max(times)), 2)
        metrics.p90_response_hours = round(float(np.percentile(times, 90)), 2)

        # Acknowledgment times
        ack_times = []
        for r in reports:
            if r.acknowledged_at and r.reported_at:
                hours = (r.acknowledged_at - r.reported_at).total_seconds() / 3600
                ack_times.append(hours)
        if ack_times:
            metrics.avg_acknowledgment_hours = round(float(np.mean(ack_times)), 2)

        # On-time percentage
        on_time = self._compute_on_time(resolved)
        metrics.on_time_percent = round(on_time, 1)

        # By category
        metrics.by_category = self._average_by_category(resolved)

        # By priority
        metrics.by_priority = self._average_by_priority(resolved)

        return metrics

    def _compute_on_time(self, resolved: list[Report]) -> float:
        """Compute percentage of reports resolved within target time."""
        if not resolved:
            return 0.0

        on_time_count = 0
        evaluated = 0

        for report in resolved:
            if report.priority and report.resolution:
                target = self._target_hours.get(report.priority, 168.0)
                if report.resolution.resolution_time_hours <= target:
                    on_time_count += 1
                evaluated += 1

        if evaluated == 0:
            return 0.0
        return (on_time_count / evaluated) * 100

    def _average_by_category(
        self, resolved: list[Report]
    ) -> dict[str, float]:
        """Average resolution time per issue category."""
        times_by_cat: dict[str, list[float]] = {}

        for report in resolved:
            if report.issue and report.resolution:
                cat = report.issue.category.value
                if cat not in times_by_cat:
                    times_by_cat[cat] = []
                times_by_cat[cat].append(report.resolution.resolution_time_hours)

        return {
            cat: round(float(np.mean(times)), 2)
            for cat, times in times_by_cat.items()
        }

    def _average_by_priority(
        self, resolved: list[Report]
    ) -> dict[str, float]:
        """Average resolution time per priority level."""
        times_by_pri: dict[str, list[float]] = {}

        for report in resolved:
            if report.priority and report.resolution:
                pri = report.priority.value
                if pri not in times_by_pri:
                    times_by_pri[pri] = []
                times_by_pri[pri].append(report.resolution.resolution_time_hours)

        return {
            pri: round(float(np.mean(times)), 2)
            for pri, times in times_by_pri.items()
        }

    def get_overdue_reports(self, reports: list[Report]) -> list[Report]:
        """Find open reports that have exceeded their target response time.

        Args:
            reports: List of reports to check.

        Returns:
            List of overdue reports sorted by age descending.
        """
        now = datetime.now()
        overdue: list[Report] = []

        for report in reports:
            if report.status == ReportStatus.RESOLVED:
                continue

            target = self._target_hours.get(
                report.priority or PriorityLevel.MEDIUM, 168.0
            )
            age_hours = (now - report.reported_at).total_seconds() / 3600

            if age_hours > target:
                overdue.append(report)

        overdue.sort(key=lambda r: r.reported_at)
        return overdue
