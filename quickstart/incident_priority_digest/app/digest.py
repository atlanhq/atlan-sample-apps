"""Pure functions for building incident priority digests.

All functions operate on plain Python data structures and have no SDK dependencies,
making them straightforward to unit-test.
"""

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List


def build_severity_counts(records: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count incidents by severity level.

    Args:
        records: List of incident dicts, each with a ``severity`` key.

    Returns:
        Mapping of severity -> count, sorted descending by count.
    """
    counts = Counter(r.get("severity", "unknown") for r in records)
    return dict(counts.most_common())


def build_status_counts(records: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count incidents by status.

    Args:
        records: List of incident dicts, each with a ``status`` key.

    Returns:
        Mapping of status -> count, sorted descending by count.
    """
    counts = Counter(r.get("status", "unknown") for r in records)
    return dict(counts.most_common())


def get_top_unresolved(
    records: List[Dict[str, Any]], limit: int = 10
) -> List[Dict[str, Any]]:
    """Return the top *limit* unresolved incidents ordered by severity.

    Unresolved means ``status`` is not ``resolved`` or ``closed``.
    Severity ordering: critical > high > medium > low > unknown.

    Args:
        records: Full incident list.
        limit: Maximum number of results (default 10).

    Returns:
        Up to *limit* incident dicts.
    """
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "unknown": 4}
    resolved_statuses = {"resolved", "closed"}

    unresolved = [
        r for r in records if r.get("status", "").lower() not in resolved_statuses
    ]
    unresolved.sort(key=lambda r: severity_order.get(r.get("severity", "unknown"), 4))
    return unresolved[:limit]


def group_by_team(records: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group incidents by owning team.

    Args:
        records: Full incident list; each should have an ``owning_team`` key.

    Returns:
        Mapping of team name -> list of incidents belonging to that team.
    """
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in records:
        team = r.get("owning_team", "unassigned")
        groups.setdefault(team, []).append(r)
    return groups


def build_digest(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build the full daily digest from incident records.

    Args:
        records: Raw incident records.

    Returns:
        A dict with ``generated_at``, ``total_incidents``,
        ``severity_counts``, ``status_counts``, ``top_unresolved``,
        and ``by_team`` sections.
    """
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_incidents": len(records),
        "severity_counts": build_severity_counts(records),
        "status_counts": build_status_counts(records),
        "top_unresolved": get_top_unresolved(records),
        "by_team": {
            team: {
                "count": len(incidents),
                "severity_counts": build_severity_counts(incidents),
            }
            for team, incidents in group_by_team(records).items()
        },
    }
