"""Tests for issue classifier."""

import pytest

from fixmystreet.models import IssueCategory
from fixmystreet.reporter.classifier import IssueClassifier


@pytest.fixture
def classifier():
    return IssueClassifier()


class TestIssueClassifier:
    def test_classify_pothole(self, classifier):
        issue = classifier.classify("Large pothole in the road causing damage")
        assert issue.category == IssueCategory.POTHOLE
        assert issue.confidence > 0

    def test_classify_broken_light(self, classifier):
        issue = classifier.classify("Street light has been out for days, very dark")
        assert issue.category == IssueCategory.BROKEN_LIGHT

    def test_classify_graffiti(self, classifier):
        issue = classifier.classify("Someone spray painted graffiti on the wall")
        assert issue.category == IssueCategory.GRAFFITI

    def test_classify_damaged_sign(self, classifier):
        issue = classifier.classify("Stop sign is bent and broken at the intersection")
        assert issue.category == IssueCategory.DAMAGED_SIGN

    def test_classify_flooding(self, classifier):
        issue = classifier.classify("Road flooding from blocked drain, standing water")
        assert issue.category == IssueCategory.FLOODING

    def test_classify_sidewalk_crack(self, classifier):
        issue = classifier.classify("Sidewalk crack creating a trip hazard")
        assert issue.category == IssueCategory.SIDEWALK_CRACK

    def test_classify_fallen_tree(self, classifier):
        issue = classifier.classify("Large tree fell and is blocking the road")
        assert issue.category == IssueCategory.FALLEN_TREE

    def test_classify_illegal_dumping(self, classifier):
        issue = classifier.classify("Illegal dumping of garbage and a mattress on the lot")
        assert issue.category == IssueCategory.ILLEGAL_DUMPING

    def test_classify_no_match(self, classifier):
        issue = classifier.classify("Something completely unrelated to infrastructure")
        assert issue.confidence == 0.0

    def test_severity_increased_by_urgent(self, classifier):
        normal = classifier.classify("Pothole on the road")
        urgent = classifier.classify("Urgent pothole on the road near school")
        assert urgent.severity > normal.severity

    def test_severity_decreased_by_minor(self, classifier):
        normal = classifier.classify("Pothole on the road")
        minor = classifier.classify("Small minor pothole on the road")
        assert minor.severity < normal.severity

    def test_classify_batch(self, classifier):
        descriptions = [
            "Pothole on Main Street",
            "Broken street light",
            "Graffiti on the bridge",
        ]
        issues = classifier.classify_batch(descriptions)
        assert len(issues) == 3
        assert issues[0].category == IssueCategory.POTHOLE
        assert issues[1].category == IssueCategory.BROKEN_LIGHT
        assert issues[2].category == IssueCategory.GRAFFITI

    def test_categories_property(self, classifier):
        cats = classifier.categories
        assert len(cats) == 8
        assert IssueCategory.POTHOLE in cats

    def test_keywords_matched(self, classifier):
        issue = classifier.classify("Large pothole in the asphalt road surface")
        assert "pothole" in issue.keywords_matched
        assert len(issue.keywords_matched) >= 1
