"""Sample report generator for testing and demos."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Optional

import numpy as np

from fixmystreet.models import (
    Issue,
    IssueCategory,
    Location,
    PriorityLevel,
    Report,
    ReportStatus,
    Resolution,
)


_NEIGHBORHOODS = [
    "Downtown", "Riverside", "Oak Park", "Hillcrest", "Midtown",
    "Westside", "Eastgate", "Northview", "Southfield", "Lakewood",
]

_STREETS = [
    "Main Street", "Oak Avenue", "Elm Street", "Broadway",
    "Park Road", "Cedar Lane", "Maple Drive", "Pine Street",
    "Washington Boulevard", "Lincoln Avenue", "School Road",
    "Hospital Drive", "Highway 101", "Bridge Street",
]

_REPORTER_NAMES = [
    "Anonymous", "John Smith", "Maria Garcia", "David Lee",
    "Sarah Johnson", "Raj Patel", "Emily Chen", "Michael Brown",
    "Aisha Mohammed", "James Wilson",
]

_DESCRIPTIONS: dict[IssueCategory, list[str]] = {
    IssueCategory.POTHOLE: [
        "Large pothole in the middle of the road, about 2 feet wide",
        "Deep hole in the asphalt near the intersection, causing flat tires",
        "Multiple small potholes along the road surface",
        "Dangerous crater forming on the road near the school",
        "Road damage after recent rain, hole getting bigger",
    ],
    IssueCategory.BROKEN_LIGHT: [
        "Street light has been out for a week, very dark at night",
        "Broken light on the corner, flickering on and off",
        "No light on the walkway, safety concern for pedestrians",
        "Streetlight buzzing and not illuminating properly",
        "Light out near the parking lot entrance",
    ],
    IssueCategory.GRAFFITI: [
        "Graffiti spray painted on the side of the community center",
        "Vandalism on the park bench with spray paint",
        "Tagged wall along the underpass, offensive content",
        "Graffiti on the bus stop shelter",
        "Building wall defaced with paint",
    ],
    IssueCategory.DAMAGED_SIGN: [
        "Stop sign bent at a 45 degree angle after a collision",
        "Street sign knocked over by wind, lying on the ground",
        "Missing sign at the intersection, confusing for drivers",
        "Road sign damaged and unreadable",
        "Broken signpost leaning dangerously over the sidewalk",
    ],
    IssueCategory.FLOODING: [
        "Standing water on the road after every rain, blocked drain",
        "Flooding in the underpass, water over a foot deep",
        "Drain overflow causing water to pool in the parking lot",
        "Sewer backup causing flooding on residential street",
        "Waterlogged road making it impassable during rain",
    ],
    IssueCategory.SIDEWALK_CRACK: [
        "Large crack in the sidewalk creating a trip hazard",
        "Uneven sidewalk panels, dangerous for elderly walkers",
        "Broken sidewalk near the school entrance",
        "Pavement crack widening, tree roots pushing up",
        "Cracked walkway in front of the library",
    ],
    IssueCategory.FALLEN_TREE: [
        "Large tree fell across the road blocking both lanes",
        "Dead tree leaning over the sidewalk about to fall",
        "Fallen branch blocking the bike path",
        "Uprooted tree from the storm, power lines at risk",
        "Tree limb hanging dangerously over the playground",
    ],
    IssueCategory.ILLEGAL_DUMPING: [
        "Someone dumped a mattress and furniture on the vacant lot",
        "Illegal trash dumping behind the warehouse",
        "Construction debris dumped on the roadside",
        "Garbage bags piled up at the end of the dead-end street",
        "Fly tipping of old appliances near the river",
    ],
}


class ReportSimulator:
    """Generates realistic sample infrastructure reports.

    Creates randomized but plausible reports with geographic clustering
    to simulate realistic urban issue patterns.
    """

    def __init__(
        self,
        center_lat: float = 40.7128,
        center_lon: float = -74.0060,
        seed: Optional[int] = None,
    ) -> None:
        """Initialize the simulator.

        Args:
            center_lat: Center latitude for generated locations.
            center_lon: Center longitude for generated locations.
            seed: Random seed for reproducibility.
        """
        self._center_lat = center_lat
        self._center_lon = center_lon
        self._rng = random.Random(seed)
        self._np_rng = np.random.default_rng(seed)
        self._report_counter = 0

    def generate(self, count: int = 50, days_back: int = 90) -> list[Report]:
        """Generate a batch of sample reports.

        Args:
            count: Number of reports to generate.
            days_back: How far back in time to spread reports.

        Returns:
            List of generated Report objects.
        """
        reports = []
        for _ in range(count):
            report = self._generate_single(days_back)
            reports.append(report)
        return reports

    def _generate_single(self, days_back: int) -> Report:
        """Generate a single random report."""
        self._report_counter += 1
        report_id = f"RPT-{self._report_counter:04d}"

        category = self._rng.choice(list(IssueCategory))
        location = self._generate_location()
        description = self._rng.choice(_DESCRIPTIONS[category])

        severity = self._np_rng.beta(2, 3)  # Skewed toward lower severity
        confidence = self._np_rng.beta(5, 2)  # Skewed toward higher confidence

        issue = Issue(
            category=category,
            confidence=round(float(confidence), 3),
            description=description,
            severity=round(float(severity), 3),
        )

        # Random timestamp within the time window
        reported_at = datetime.now() - timedelta(
            days=self._rng.uniform(0, days_back),
            hours=self._rng.uniform(0, 24),
        )

        # Determine status and resolution
        status, ack_at, resolved_at, resolution = self._generate_lifecycle(
            reported_at
        )

        # Assign priority
        priority_val = float(self._np_rng.beta(2, 3))
        if priority_val >= 0.75:
            priority = PriorityLevel.CRITICAL
        elif priority_val >= 0.55:
            priority = PriorityLevel.HIGH
        elif priority_val >= 0.35:
            priority = PriorityLevel.MEDIUM
        else:
            priority = PriorityLevel.LOW

        return Report(
            report_id=report_id,
            description=description,
            location=location,
            issue=issue,
            status=status,
            priority=priority,
            priority_score=round(priority_val, 3),
            reported_at=reported_at,
            acknowledged_at=ack_at,
            resolved_at=resolved_at,
            resolution=resolution,
            reporter_name=self._rng.choice(_REPORTER_NAMES),
        )

    def _generate_location(self) -> Location:
        """Generate a random location near the center point."""
        # Create clusters by using a mixture of normals
        cluster_offset_lat = self._np_rng.choice([-0.02, 0.0, 0.01, 0.015])
        cluster_offset_lon = self._np_rng.choice([-0.015, 0.0, 0.01, 0.02])

        lat = self._center_lat + cluster_offset_lat + float(
            self._np_rng.normal(0, 0.005)
        )
        lon = self._center_lon + cluster_offset_lon + float(
            self._np_rng.normal(0, 0.005)
        )

        street = self._rng.choice(_STREETS)
        number = self._rng.randint(100, 9999)
        neighborhood = self._rng.choice(_NEIGHBORHOODS)

        return Location(
            latitude=round(lat, 6),
            longitude=round(lon, 6),
            address=f"{number} {street}",
            neighborhood=neighborhood,
        )

    def _generate_lifecycle(
        self, reported_at: datetime
    ) -> tuple[ReportStatus, Optional[datetime], Optional[datetime], Optional[Resolution]]:
        """Generate a realistic lifecycle for a report."""
        age_hours = (datetime.now() - reported_at).total_seconds() / 3600

        # Newer reports are less likely to be resolved
        if age_hours < 24:
            status_weights = [0.7, 0.2, 0.1, 0.0]
        elif age_hours < 72:
            status_weights = [0.3, 0.3, 0.3, 0.1]
        elif age_hours < 168:
            status_weights = [0.1, 0.2, 0.3, 0.4]
        else:
            status_weights = [0.05, 0.1, 0.15, 0.7]

        statuses = list(ReportStatus)
        status = self._rng.choices(statuses, weights=status_weights, k=1)[0]

        ack_at = None
        resolved_at = None
        resolution = None

        if status in (
            ReportStatus.ACKNOWLEDGED,
            ReportStatus.IN_PROGRESS,
            ReportStatus.RESOLVED,
        ):
            ack_delay = self._rng.uniform(1, 48)
            ack_at = reported_at + timedelta(hours=ack_delay)

        if status == ReportStatus.RESOLVED:
            resolution_hours = self._rng.uniform(24, max(age_hours, 25))
            resolved_at = reported_at + timedelta(hours=resolution_hours)
            resolution = Resolution(
                resolved_at=resolved_at,
                resolution_notes="Issue addressed by maintenance crew.",
                resolution_time_hours=round(resolution_hours, 2),
                cost_estimate=round(self._rng.uniform(50, 5000), 2),
                crew_size=self._rng.randint(1, 5),
            )

        return status, ack_at, resolved_at, resolution
