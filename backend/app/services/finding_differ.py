"""
Security Memory — Finding Differ — T-090, T-091, T-094.

Compares findings between scans to classify as new/recurring/unchanged/resolved.
This is how CodeSentinel tracks security improvements and regressions over time.
"""

from dataclasses import dataclass
from app.models.finding_history import HistoryStatus
import structlog

logger = structlog.get_logger()


@dataclass
class DiffResult:
    """Result of comparing two scans' findings."""
    new: list[str]           # finding_keys in current but not previous
    recurring: list[str]     # finding_keys in both, same severity
    unchanged: list[str]     # finding_keys in both, same severity (alias: recurring = multi-scan)
    resolved: list[str]      # finding_keys in previous but not current


class FindingDiffer:
    """T-090: Computes finding diff between current and previous scan."""

    def compute_diff(
        self,
        current_finding_keys: set[str],
        previous_finding_keys: set[str],
    ) -> dict[str, str]:
        """
        T-090: Compare two sets of finding keys and return classification dict.
        Returns: {finding_key: "new"|"recurring"|"unchanged"|"resolved"}

        Note: "unchanged" and "recurring" are semantically equivalent here —
        a finding appearing in ≥2 scans is "recurring". We use "recurring" for active
        findings and "resolved" for findings that disappeared.
        """
        result: dict[str, str] = {}

        for key in current_finding_keys:
            if key in previous_finding_keys:
                result[key] = HistoryStatus.RECURRING.value
            else:
                result[key] = HistoryStatus.NEW.value

        for key in previous_finding_keys:
            if key not in current_finding_keys:
                result[key] = HistoryStatus.RESOLVED.value

        logger.info(
            "Finding diff computed",
            new=sum(1 for v in result.values() if v == "new"),
            recurring=sum(1 for v in result.values() if v == "recurring"),
            resolved=sum(1 for v in result.values() if v == "resolved"),
        )
        return result


# Singleton instance
finding_differ = FindingDiffer()
