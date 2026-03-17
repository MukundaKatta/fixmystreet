"""Pydantic data models for infrastructure reports."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class IssueCategory(str, Enum):
    """Categories of infrastructure issues."""

    POTHOLE = "pothole"
    BROKEN_LIGHT = "broken_light"
    GRAFFITI = "graffiti"
    DAMAGED_SIGN = "damaged_sign"
    FLOODING = "flooding"
    SIDEWALK_CRACK = "sidewalk_crack"
    FALLEN_TREE = "fallen_tree"
    ILLEGAL_DUMPING = "illegal_dumping"


class ReportStatus(str, Enum):
    """Lifecycle states of a report."""

    REPORTED = "reported"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class PriorityLevel(str, Enum):
    """Priority levels for issues."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Location(BaseModel):
    """Geographic location of an issue."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: str = Field(default="")
    neighborhood: str = Field(default="")

    @property
    def coordinates(self) -> tuple[float, float]:
        """Return (lat, lon) tuple."""
        return (self.latitude, self.longitude)


class Issue(BaseModel):
    """A classified infrastructure issue."""

    category: IssueCategory
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    description: str = Field(default="")
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    keywords_matched: list[str] = Field(default_factory=list)


class Resolution(BaseModel):
    """Resolution details for a completed report."""

    resolved_at: datetime
    resolution_notes: str = Field(default="")
    resolution_time_hours: float = Field(default=0.0, ge=0.0)
    cost_estimate: Optional[float] = Field(default=None, ge=0.0)
    crew_size: int = Field(default=1, ge=1)


class Report(BaseModel):
    """A full infrastructure issue report."""

    report_id: str = Field(..., pattern=r"^RPT-\d+$")
    description: str
    location: Location
    issue: Optional[Issue] = None
    status: ReportStatus = Field(default=ReportStatus.REPORTED)
    priority: Optional[PriorityLevel] = None
    priority_score: float = Field(default=0.0, ge=0.0, le=1.0)
    reported_at: datetime = Field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution: Optional[Resolution] = None
    reporter_name: str = Field(default="Anonymous")
    photos: list[str] = Field(default_factory=list)

    @property
    def is_resolved(self) -> bool:
        """Check if the report has been resolved."""
        return self.status == ReportStatus.RESOLVED

    @property
    def age_hours(self) -> float:
        """Hours since the report was filed."""
        delta = datetime.now() - self.reported_at
        return delta.total_seconds() / 3600
