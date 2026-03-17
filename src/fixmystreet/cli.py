"""CLI interface for FIXMYSTREET using Click and Rich."""

from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="fixmystreet")
def cli() -> None:
    """FIXMYSTREET - AI Infrastructure Reporter.

    Classify, prioritize, and track municipal infrastructure issues.
    """


@cli.command()
@click.argument("description")
def classify(description: str) -> None:
    """Classify an infrastructure issue from a text description."""
    from fixmystreet.reporter.classifier import IssueClassifier

    classifier = IssueClassifier()
    issue = classifier.classify(description)

    table = Table(title="Classification Result")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Category", issue.category.value)
    table.add_row("Confidence", f"{issue.confidence:.1%}")
    table.add_row("Severity", f"{issue.severity:.2f}")
    table.add_row("Keywords Matched", ", ".join(issue.keywords_matched) or "none")

    console.print(table)


@cli.command()
@click.option("--count", default=50, help="Number of reports to generate.")
@click.option("--days", default=90, help="Days back to spread reports.")
@click.option("--seed", default=None, type=int, help="Random seed.")
def simulate(count: int, days: int, seed: int | None) -> None:
    """Generate sample infrastructure reports."""
    from fixmystreet.simulator import ReportSimulator

    sim = ReportSimulator(seed=seed)
    reports = sim.generate(count=count, days_back=days)

    console.print(f"[green]Generated {len(reports)} reports.[/green]\n")

    table = Table(title=f"Sample Reports (showing first 10 of {len(reports)})")
    table.add_column("ID", style="cyan")
    table.add_column("Category", style="yellow")
    table.add_column("Priority")
    table.add_column("Status")
    table.add_column("Neighborhood")

    for report in reports[:10]:
        cat = report.issue.category.value if report.issue else "unknown"
        pri = report.priority.value if report.priority else "unset"
        table.add_row(
            report.report_id,
            cat,
            pri,
            report.status.value,
            report.location.neighborhood,
        )

    console.print(table)


@cli.group()
def analyze() -> None:
    """Run analysis on infrastructure reports."""


@analyze.command()
@click.option("--count", default=100, help="Number of sample reports.")
@click.option("--radius", default=0.5, type=float, help="Hotspot radius in km.")
@click.option("--seed", default=42, type=int, help="Random seed.")
def hotspots(count: int, radius: float, seed: int) -> None:
    """Detect geographic hotspots in report data."""
    from fixmystreet.analyzer.hotspots import HotspotDetector
    from fixmystreet.simulator import ReportSimulator

    sim = ReportSimulator(seed=seed)
    reports = sim.generate(count=count)

    detector = HotspotDetector(radius_km=radius)
    results = detector.detect(reports)

    if not results:
        console.print("[yellow]No hotspots detected.[/yellow]")
        return

    table = Table(title=f"Detected Hotspots ({len(results)} found)")
    table.add_column("Location", style="cyan")
    table.add_column("Reports", justify="right")
    table.add_column("Density", justify="right", style="red")

    for hs in results:
        table.add_row(
            f"({hs.center_lat:.4f}, {hs.center_lon:.4f})",
            str(hs.report_count),
            f"{hs.density_score:.3f}",
        )

    console.print(table)


@analyze.command()
@click.option("--count", default=100, help="Number of sample reports.")
@click.option("--period", default=7, type=int, help="Period length in days.")
@click.option("--seed", default=42, type=int, help="Random seed.")
def trends(count: int, period: int, seed: int) -> None:
    """Analyze issue trends over time."""
    from fixmystreet.analyzer.trends import TrendAnalyzer
    from fixmystreet.simulator import ReportSimulator

    sim = ReportSimulator(seed=seed)
    reports = sim.generate(count=count)

    analyzer = TrendAnalyzer()
    summary = analyzer.analyze(reports, period_days=period)

    info_table = Table(title="Trend Summary")
    info_table.add_column("Metric", style="cyan")
    info_table.add_column("Value", style="green")

    info_table.add_row("Total Reports", str(summary.total_reports))
    info_table.add_row("Busiest Day", summary.busiest_day)
    info_table.add_row("Most Common Issue", summary.most_common_category)
    info_table.add_row("Growth Rate", f"{summary.growth_rate:+.1f}%")

    console.print(info_table)

    if summary.trends:
        trend_table = Table(title="Category Trends")
        trend_table.add_column("Category")
        trend_table.add_column("Count", justify="right")
        trend_table.add_column("Change", justify="right")
        trend_table.add_column("Direction")

        for t in summary.trends:
            trend_table.add_row(
                t.category, str(t.count), f"{t.change_percent:+.1f}%", t.direction
            )

        console.print(trend_table)


@analyze.command()
@click.option("--count", default=100, help="Number of sample reports.")
@click.option("--seed", default=42, type=int, help="Random seed.")
def response(count: int, seed: int) -> None:
    """Analyze city response time performance."""
    from fixmystreet.analyzer.response import ResponseTimeAnalyzer
    from fixmystreet.simulator import ReportSimulator

    sim = ReportSimulator(seed=seed)
    reports = sim.generate(count=count)

    analyzer = ResponseTimeAnalyzer()
    metrics = analyzer.analyze(reports)

    table = Table(title="Response Time Analysis")
    table.add_column("Metric", style="magenta")
    table.add_column("Value", justify="right")

    table.add_row("Total Resolved", str(metrics.total_resolved))
    table.add_row("Total Open", str(metrics.total_open))
    table.add_row("Avg Response (hrs)", f"{metrics.avg_response_hours:.1f}")
    table.add_row("Median Response (hrs)", f"{metrics.median_response_hours:.1f}")
    table.add_row("P90 Response (hrs)", f"{metrics.p90_response_hours:.1f}")
    table.add_row("On-Time %", f"{metrics.on_time_percent:.1f}%")

    console.print(table)


@cli.command()
@click.option("--report-id", required=True, help="Report ID to track.")
@click.option(
    "--status",
    type=click.Choice(["reported", "acknowledged", "in_progress", "resolved"]),
    required=True,
    help="New status for the report.",
)
def track(report_id: str, status: str) -> None:
    """Update a report's status in its lifecycle."""
    from fixmystreet.models import ReportStatus

    console.print(
        Panel(
            f"[bold]Report:[/bold] {report_id}\n"
            f"[bold]New Status:[/bold] {status}",
            title="Status Update",
            style="green",
        )
    )
    console.print(
        f"[dim]In a production system, this would update report {report_id} "
        f"to status '{status}' in the database.[/dim]"
    )


@cli.command()
@click.option("--days", default=30, help="Number of days to cover.")
@click.option("--count", default=100, help="Number of sample reports.")
@click.option("--seed", default=42, type=int, help="Random seed.")
def report(days: int, count: int, seed: int) -> None:
    """Generate a full infrastructure health report."""
    from fixmystreet.report import InfrastructureReport
    from fixmystreet.simulator import ReportSimulator

    sim = ReportSimulator(seed=seed)
    reports = sim.generate(count=count, days_back=days)

    infra_report = InfrastructureReport(reports)
    infra_report.generate(days=days)


if __name__ == "__main__":
    cli()
