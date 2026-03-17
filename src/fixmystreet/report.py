"""Infrastructure health report generation."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from fixmystreet.analyzer.hotspots import HotspotDetector
from fixmystreet.analyzer.response import ResponseTimeAnalyzer
from fixmystreet.analyzer.trends import TrendAnalyzer
from fixmystreet.models import Report


class InfrastructureReport:
    """Generates comprehensive infrastructure health reports.

    Combines analysis from hotspot detection, trend analysis, and
    response time metrics into a formatted report.
    """

    def __init__(self, reports: list[Report]) -> None:
        self._reports = reports
        self._console = Console()

    def generate(self, days: int = 30) -> None:
        """Generate and print a full infrastructure report.

        Args:
            days: Number of days to cover in the report.
        """
        self._print_header(days)
        self._print_summary()
        self._print_category_breakdown()
        self._print_response_metrics()
        self._print_hotspots()
        self._print_trends(days)

    def _print_header(self, days: int) -> None:
        """Print report header."""
        header = Panel(
            f"[bold]FIXMYSTREET Infrastructure Health Report[/bold]\n"
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"Period: Last {days} days | Total Reports: {len(self._reports)}",
            style="blue",
        )
        self._console.print(header)

    def _print_summary(self) -> None:
        """Print report summary statistics."""
        from fixmystreet.models import ReportStatus

        table = Table(title="Report Status Summary")
        table.add_column("Status", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")

        total = len(self._reports)
        for status in ReportStatus:
            count = sum(1 for r in self._reports if r.status == status)
            pct = (count / total * 100) if total > 0 else 0
            table.add_row(status.value, str(count), f"{pct:.1f}%")

        self._console.print(table)

    def _print_category_breakdown(self) -> None:
        """Print issue category breakdown."""
        analyzer = TrendAnalyzer()
        breakdown = analyzer.category_breakdown(self._reports)

        table = Table(title="Issues by Category")
        table.add_column("Category", style="green")
        table.add_column("Count", justify="right")
        table.add_column("Bar", style="yellow")

        max_count = max(breakdown.values()) if breakdown else 1
        for cat, count in sorted(breakdown.items(), key=lambda x: -x[1]):
            bar_len = int((count / max(max_count, 1)) * 20)
            bar = "#" * bar_len
            table.add_row(cat, str(count), bar)

        self._console.print(table)

    def _print_response_metrics(self) -> None:
        """Print response time metrics."""
        analyzer = ResponseTimeAnalyzer()
        metrics = analyzer.analyze(self._reports)

        table = Table(title="Response Time Metrics")
        table.add_column("Metric", style="magenta")
        table.add_column("Value", justify="right")

        table.add_row("Total Resolved", str(metrics.total_resolved))
        table.add_row("Total Open", str(metrics.total_open))
        table.add_row("Avg Response (hrs)", f"{metrics.avg_response_hours:.1f}")
        table.add_row("Median Response (hrs)", f"{metrics.median_response_hours:.1f}")
        table.add_row("P90 Response (hrs)", f"{metrics.p90_response_hours:.1f}")
        table.add_row("Avg Acknowledgment (hrs)", f"{metrics.avg_acknowledgment_hours:.1f}")
        table.add_row("On-Time %", f"{metrics.on_time_percent:.1f}%")

        self._console.print(table)

    def _print_hotspots(self) -> None:
        """Print detected hotspots."""
        detector = HotspotDetector()
        hotspots = detector.detect(self._reports)

        if not hotspots:
            self._console.print("[dim]No hotspots detected.[/dim]")
            return

        table = Table(title="Top Hotspots")
        table.add_column("Location", style="red")
        table.add_column("Reports", justify="right")
        table.add_column("Density", justify="right")

        for hs in hotspots[:5]:
            table.add_row(
                f"({hs.center_lat:.4f}, {hs.center_lon:.4f})",
                str(hs.report_count),
                f"{hs.density_score:.2f}",
            )

        self._console.print(table)

    def _print_trends(self, days: int) -> None:
        """Print trend analysis."""
        analyzer = TrendAnalyzer()
        summary = analyzer.analyze(self._reports, period_days=7)

        table = Table(title="Trend Analysis")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")

        table.add_row("Busiest Day", summary.busiest_day)
        table.add_row("Most Common Issue", summary.most_common_category)
        table.add_row("Growth Rate", f"{summary.growth_rate:+.1f}%")

        self._console.print(table)

        if summary.trends:
            trend_table = Table(title="Category Trends (vs Previous Period)")
            trend_table.add_column("Category", style="green")
            trend_table.add_column("Count", justify="right")
            trend_table.add_column("Change", justify="right")
            trend_table.add_column("Direction")

            for trend in summary.trends:
                direction_style = {
                    "increasing": "[red]",
                    "decreasing": "[green]",
                    "stable": "[dim]",
                }.get(trend.direction, "")
                trend_table.add_row(
                    trend.category,
                    str(trend.count),
                    f"{trend.change_percent:+.1f}%",
                    f"{direction_style}{trend.direction}",
                )

            self._console.print(trend_table)
