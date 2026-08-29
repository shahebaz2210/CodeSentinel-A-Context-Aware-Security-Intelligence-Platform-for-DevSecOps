"""Unit tests for Finding Differ (Security Memory) — T-019."""

import pytest
from app.services.finding_differ import FindingDiffer


@pytest.fixture
def differ() -> FindingDiffer:
    return FindingDiffer()


def test_all_new_on_first_scan(differ: FindingDiffer) -> None:
    """All findings should be 'new' when there's no previous scan."""
    current = {"key1", "key2", "key3"}
    result = differ.compute_diff(current, set())
    assert all(v == "new" for v in result.values())
    assert set(result.keys()) == current


def test_resolved_findings_detected(differ: FindingDiffer) -> None:
    """Findings from previous scan not in current should be 'resolved'."""
    current = {"key1", "key2"}
    previous = {"key1", "key2", "key3"}
    result = differ.compute_diff(current, previous)
    assert result.get("key3") == "resolved"


def test_recurring_findings_detected(differ: FindingDiffer) -> None:
    """Findings in both scans should be 'recurring'."""
    current = {"key1", "key2"}
    previous = {"key1", "key3"}
    result = differ.compute_diff(current, previous)
    assert result.get("key1") == "recurring"
    assert result.get("key2") == "new"
    assert result.get("key3") == "resolved"


def test_empty_current_all_resolved(differ: FindingDiffer) -> None:
    """When current scan has no findings, all previous are 'resolved'."""
    previous = {"key1", "key2"}
    result = differ.compute_diff(set(), previous)
    assert all(v == "resolved" for v in result.values())


def test_no_overlap_produces_all_new_and_resolved(differ: FindingDiffer) -> None:
    """No overlapping keys should have all current as new and all previous as resolved."""
    current = {"new1", "new2"}
    previous = {"old1", "old2"}
    result = differ.compute_diff(current, previous)
    assert result.get("new1") == "new"
    assert result.get("new2") == "new"
    assert result.get("old1") == "resolved"
    assert result.get("old2") == "resolved"
