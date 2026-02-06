import json

import pytest
from app.activities import IncidentDigestActivities
from app.digest import (
    build_digest,
    build_severity_counts,
    build_status_counts,
    get_top_unresolved,
    group_by_team,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_RECORDS = [
    {"id": "INC-001", "severity": "critical", "status": "open", "owning_team": "platform", "title": "DB down"},
    {"id": "INC-002", "severity": "high", "status": "investigating", "owning_team": "backend", "title": "Slow API"},
    {"id": "INC-003", "severity": "medium", "status": "resolved", "owning_team": "platform", "title": "Disk warning"},
    {"id": "INC-004", "severity": "low", "status": "closed", "owning_team": "frontend", "title": "UI glitch"},
    {"id": "INC-005", "severity": "critical", "status": "open", "owning_team": "platform", "title": "Memory leak"},
    {"id": "INC-006", "severity": "high", "status": "open", "owning_team": "backend", "title": "Auth timeout"},
]


# ---------------------------------------------------------------------------
# Digest pure-function tests
# ---------------------------------------------------------------------------


class TestBuildSeverityCounts:
    def test_counts_all_severities(self):
        counts = build_severity_counts(SAMPLE_RECORDS)
        assert counts["critical"] == 2
        assert counts["high"] == 2
        assert counts["medium"] == 1
        assert counts["low"] == 1

    def test_empty_records(self):
        assert build_severity_counts([]) == {}

    def test_missing_severity_defaults_to_unknown(self):
        counts = build_severity_counts([{"id": "X"}])
        assert counts == {"unknown": 1}


class TestBuildStatusCounts:
    def test_counts_all_statuses(self):
        counts = build_status_counts(SAMPLE_RECORDS)
        assert counts["open"] == 3
        assert counts["investigating"] == 1
        assert counts["resolved"] == 1
        assert counts["closed"] == 1

    def test_empty_records(self):
        assert build_status_counts([]) == {}


class TestGetTopUnresolved:
    def test_excludes_resolved_and_closed(self):
        top = get_top_unresolved(SAMPLE_RECORDS)
        ids = {r["id"] for r in top}
        assert "INC-003" not in ids  # resolved
        assert "INC-004" not in ids  # closed

    def test_ordered_by_severity(self):
        top = get_top_unresolved(SAMPLE_RECORDS)
        severities = [r["severity"] for r in top]
        # criticals first, then highs, etc.
        assert severities == ["critical", "critical", "high", "high"]

    def test_limit(self):
        top = get_top_unresolved(SAMPLE_RECORDS, limit=2)
        assert len(top) == 2

    def test_empty_records(self):
        assert get_top_unresolved([]) == []


class TestGroupByTeam:
    def test_groups_correctly(self):
        groups = group_by_team(SAMPLE_RECORDS)
        assert len(groups["platform"]) == 3
        assert len(groups["backend"]) == 2
        assert len(groups["frontend"]) == 1

    def test_missing_team_defaults_to_unassigned(self):
        groups = group_by_team([{"id": "X"}])
        assert "unassigned" in groups

    def test_empty_records(self):
        assert group_by_team([]) == {}


class TestBuildDigest:
    def test_digest_shape(self):
        digest = build_digest(SAMPLE_RECORDS)
        assert "generated_at" in digest
        assert digest["total_incidents"] == 6
        assert isinstance(digest["severity_counts"], dict)
        assert isinstance(digest["status_counts"], dict)
        assert isinstance(digest["top_unresolved"], list)
        assert isinstance(digest["by_team"], dict)

    def test_by_team_has_nested_counts(self):
        digest = build_digest(SAMPLE_RECORDS)
        for team_data in digest["by_team"].values():
            assert "count" in team_data
            assert "severity_counts" in team_data

    def test_empty_records(self):
        digest = build_digest([])
        assert digest["total_incidents"] == 0
        assert digest["top_unresolved"] == []
        assert digest["by_team"] == {}


# ---------------------------------------------------------------------------
# Activity tests (no Temporal/Dapr needed)
# ---------------------------------------------------------------------------


class TestParseRecordsActivity:
    @pytest.fixture()
    def activities(self) -> IncidentDigestActivities:
        return IncidentDigestActivities()

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_json_string(activities: IncidentDigestActivities):
        result = await activities.parse_records({"records_json": json.dumps(SAMPLE_RECORDS)})
        assert len(result) == 6
        assert result[0]["id"] == "INC-001"

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_already_list(activities: IncidentDigestActivities):
        result = await activities.parse_records({"records_json": SAMPLE_RECORDS})
        assert len(result) == 6

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_missing_field(activities: IncidentDigestActivities):
        result = await activities.parse_records({})
        assert result == []


class TestWriteRawOutputActivity:
    @pytest.fixture()
    def activities(self) -> IncidentDigestActivities:
        return IncidentDigestActivities()

    @staticmethod
    @pytest.mark.asyncio
    async def test_writes_raw_file(activities: IncidentDigestActivities, tmp_path):
        args = {"output_path": str(tmp_path), "records": SAMPLE_RECORDS}
        path = await activities.write_raw_output(args)
        assert path.endswith("incidents.json")
        with open(path) as f:
            data = json.load(f)
        assert len(data) == 6


class TestGenerateAndWriteDigestActivity:
    @pytest.fixture()
    def activities(self) -> IncidentDigestActivities:
        return IncidentDigestActivities()

    @staticmethod
    @pytest.mark.asyncio
    async def test_writes_digest_file(activities: IncidentDigestActivities, tmp_path):
        args = {"output_path": str(tmp_path), "records": SAMPLE_RECORDS}
        digest = await activities.generate_and_write_digest(args)
        assert digest["total_incidents"] == 6

        digest_file = tmp_path / "transformed" / "digest" / "digest.json"
        assert digest_file.exists()
        with open(digest_file) as f:
            data = json.load(f)
        assert data["total_incidents"] == 6
