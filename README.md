# FIXMYSTREET

AI Infrastructure Reporter - an intelligent system for classifying, prioritizing, and tracking municipal infrastructure issues.

## Features

- **Issue Classification**: Automatically categorize reports into 8 infrastructure issue types (pothole, broken light, graffiti, damaged sign, flooding, sidewalk crack, fallen tree, illegal dumping)
- **Priority Scoring**: Score reports based on severity, location risk, and historical frequency
- **Lifecycle Tracking**: Manage reports through their full lifecycle (reported -> acknowledged -> in_progress -> resolved)
- **Hotspot Detection**: Identify geographic areas with high report density
- **Trend Analysis**: Track issue patterns over time to detect emerging problems
- **Response Time Analysis**: Measure and evaluate city response performance
- **Report Generation**: Produce comprehensive infrastructure health reports
- **Data Simulation**: Generate realistic sample data for testing and demos

## Installation

```bash
pip install -e .
```

## Usage

### CLI

```bash
# Generate sample reports
fixmystreet simulate --count 100

# Classify an issue from a description
fixmystreet classify "There's a large hole in the road on Main Street"

# Analyze hotspots in a dataset
fixmystreet analyze hotspots --radius 0.5

# Track report status
fixmystreet track --report-id RPT-001 --status in_progress

# Generate a full infrastructure report
fixmystreet report --days 30
```

### Python API

```python
from fixmystreet.models import Report, Location
from fixmystreet.reporter.classifier import IssueClassifier
from fixmystreet.reporter.priority import PriorityScorer

classifier = IssueClassifier()
category = classifier.classify("Large pothole on Oak Avenue causing flat tires")

scorer = PriorityScorer()
priority = scorer.score(report)
```

## Project Structure

```
src/fixmystreet/
    cli.py              # Click-based CLI interface
    models.py           # Pydantic data models
    simulator.py        # Sample data generator
    report.py           # Report generation
    reporter/
        classifier.py   # Issue classification
        priority.py     # Priority scoring
        tracker.py      # Report lifecycle management
    analyzer/
        hotspots.py     # Geographic hotspot detection
        trends.py       # Temporal trend analysis
        response.py     # Response time analytics
```

## Dependencies

- pydantic - Data validation and models
- click - CLI framework
- rich - Terminal formatting
- numpy - Numerical computations

## License

MIT
