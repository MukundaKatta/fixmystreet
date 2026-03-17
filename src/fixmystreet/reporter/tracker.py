"""Report lifecycle tracker managing status transitions."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fixmystreet.models import Report, ReportStatus, Resolution


# Valid status transitions
_VALID_TRANSITIONS: dict[ReportStatus, list[ReportStatus]] = {
    ReportStatus.REPORTED: [ReportStatus.ACKNOWLEDGED],
    ReportStatus.ACKNOWLEDGED: [ReportStatus.IN_PROGRESS, ReportStatus.REPORTED],
    ReportStatus.IN_PROGRESS: [ReportStatus.RESOLVED, ReportStatus.ACKNOWLEDGED],
    ReportStatus.RESOLVED: [],  # Terminal state
}


class InvalidTransitionError(Exception):
    """Raised when an invalid status transition is attempted."""


class ReportNotFoundError(Exception):
    """Raised when a report ID is not found."""


class IssueTracker:
    """Manages the lifecycle of infrastructure reports.

    Tracks reports through their lifecycle:
    reported -> acknowledged -> in_progress -> resolved
    """

    def __init__(self) -> None:
        self._reports: dict[str, Report] = {}

    def add_report(self, report: Report) -> None:
        """Add a report to the tracker.

        Args:
            report: The report to track.
        """
        self._reports[report.report_id] = report

    def get_report(self, report_id: str) -> Report:
        """Retrieve a report by ID.

        Args:
            report_id: The report identifier.

        Returns:
            The matching Report.

        Raises:
            ReportNotFoundError: If report_id is not found.
        """
        if report_id not in self._reports:
            raise ReportNotFoundError(f"Report {report_id} not found")
        return self._reports[report_id]

    def transition(
        self,
        report_id: str,
        new_status: ReportStatus,
        resolution_notes: str = "",
    ) -> Report:
        """Transition a report to a new status.

        Args:
            report_id: The report to transition.
            new_status: The target status.
            resolution_notes: Notes for resolution (used when resolving).

        Returns:
            The updated Report.

        Raises:
            ReportNotFoundError: If report_id is not found.
            InvalidTransitionError: If the transition is not valid.
        """
        report = self.get_report(report_id)
        current = report.status
        valid_next = _VALID_TRANSITIONS.get(current, [])

        if new_status not in valid_next:
            raise InvalidTransitionError(
                f"Cannot transition from {current.value} to {new_status.value}. "
                f"Valid transitions: {[s.value for s in valid_next]}"
            )

        report.status = new_status
        now = datetime.now()

        if new_status == ReportStatus.ACKNOWLEDGED:
            report.acknowledged_at = now
        elif new_status == ReportStatus.RESOLVED:
            report.resolved_at = now
            resolution_time = (now - report.reported_at).total_seconds() / 3600
            report.resolution = Resolution(
                resolved_at=now,
                resolution_notes=resolution_notes,
                resolution_time_hours=round(resolution_time, 2),
            )

        return report

    def get_reports_by_status(self, status: ReportStatus) -> list[Report]:
        """Get all reports with a given status.

        Args:
            status: The status to filter by.

        Returns:
            List of matching reports.
        """
        return [r for r in self._reports.values() if r.status == status]

    def get_all_reports(self) -> list[Report]:
        """Get all tracked reports."""
        return list(self._reports.values())

    def get_open_reports(self) -> list[Report]:
        """Get all reports that are not yet resolved."""
        return [r for r in self._reports.values() if not r.is_resolved]

    def get_stats(self) -> dict[str, int]:
        """Get counts by status.

        Returns:
            Dictionary mapping status names to counts.
        """
        stats: dict[str, int] = {}
        for status in ReportStatus:
            count = len(self.get_reports_by_status(status))
            stats[status.value] = count
        stats["total"] = len(self._reports)
        return stats

    @property
    def total_reports(self) -> int:
        """Total number of tracked reports."""
        return len(self._reports)

    def search(
        self,
        category: Optional[str] = None,
        neighborhood: Optional[str] = None,
        status: Optional[ReportStatus] = None,
    ) -> list[Report]:
        """Search reports by criteria.

        Args:
            category: Filter by issue category value.
            neighborhood: Filter by neighborhood name (case-insensitive).
            status: Filter by report status.

        Returns:
            List of matching reports.
        """
        results = list(self._reports.values())

        if status is not None:
            results = [r for r in results if r.status == status]

        if category is not None:
            results = [
                r for r in results
                if r.issue and r.issue.category.value == category
            ]

        if neighborhood is not None:
            neighborhood_lower = neighborhood.lower()
            results = [
                r for r in results
                if neighborhood_lower in r.location.neighborhood.lower()
            ]

        return results
