"""Unit tests for Generic Connector contracts.

Verifies that all Input/Output classes have correct defaults and survive
a JSON round-trip (required for Temporal serialization).
"""

import json

from app.contracts import (
    ExtractInput,
    ExtractOutput,
    GenericConnectorInput,
    GenericConnectorOutput,
    TransformInput,
    TransformOutput,
)


def _round_trip(obj, cls):
    """Encode to JSON and decode back — simulates Temporal serialization."""
    return cls.model_validate(json.loads(obj.model_dump_json()))


class TestGenericConnectorInput:
    def test_defaults(self):
        obj = GenericConnectorInput()
        assert obj.source == ""
        assert obj.load_to_atlan is True
        assert obj.connection is None
        assert obj.output_dir == ""

    def test_round_trip_with_values(self):
        original = GenericConnectorInput(
            source="https://example.com/data",
            load_to_atlan=False,
        )
        decoded = _round_trip(original, GenericConnectorInput)
        assert decoded.source == "https://example.com/data"
        assert decoded.load_to_atlan is False


class TestGenericConnectorOutput:
    def test_defaults(self):
        obj = GenericConnectorOutput()
        assert obj.connection_qualified_name == ""
        assert obj.record_count == 0
        assert obj.output_file is None
        assert obj.atlan_errors == []

    def test_round_trip(self):
        original = GenericConnectorOutput(
            connection_qualified_name="default/generic/test",
            record_count=42,
        )
        decoded = _round_trip(original, GenericConnectorOutput)
        assert decoded.connection_qualified_name == "default/generic/test"
        assert decoded.record_count == 42


class TestExtractInputOutput:
    def test_input_defaults(self):
        obj = ExtractInput()
        assert obj.source == ""
        assert obj.output_dir == ""

    def test_output_defaults(self):
        obj = ExtractOutput()
        assert obj.record_count == 0
        assert obj.output_file is None


class TestTransformInputOutput:
    def test_input_defaults(self):
        obj = TransformInput()
        assert obj.connection_qualified_name == ""
        assert obj.workflow_id == ""
        assert obj.raw_file is None

    def test_output_defaults(self):
        obj = TransformOutput()
        assert obj.record_count == 0
        assert obj.output_file is None
