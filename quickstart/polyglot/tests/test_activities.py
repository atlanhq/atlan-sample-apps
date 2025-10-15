"""Unit tests for polyglot activities."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.activities import PolyglotActivities


class TestPolyglotActivities:
    """Test suite for PolyglotActivities."""

    @pytest.fixture
    def activities(self):
        """Create a PolyglotActivities instance for testing."""
        return PolyglotActivities()

    @pytest.mark.asyncio
    async def test_calculate_factorial_success(self, activities):
        """Test successful factorial calculation."""
        # Mock the FactorialProcessor
        mock_processor = MagicMock()
        mock_processor.__enter__ = MagicMock(return_value=mock_processor)
        mock_processor.__exit__ = MagicMock(return_value=None)
        mock_processor.calculate.return_value = {
            "result": 120,
            "input": 5,
            "success": True,
        }

        with patch("app.activities.FactorialProcessor", return_value=mock_processor):
            result = await activities.calculate_factorial(5)

            assert result["success"] is True
            assert result["result"] == 120
            assert result["input"] == 5

    @pytest.mark.asyncio
    async def test_calculate_factorial_error(self, activities):
        """Test factorial calculation with error."""
        # Mock the FactorialProcessor to raise an exception
        mock_processor = MagicMock()
        mock_processor.__enter__ = MagicMock(
            side_effect=Exception("JVM startup failed")
        )

        with patch("app.activities.FactorialProcessor", return_value=mock_processor):
            result = await activities.calculate_factorial(5)

            assert result["success"] is False
            assert result["input"] == 5
            assert "error" in result
            assert "JVM startup failed" in result["error"]

    @pytest.mark.asyncio
    async def test_save_result_to_json_success(self, activities):
        """Test successful JSON file save."""
        calculation_result = {
            "result": 120,
            "input": 5,
            "success": True,
        }

        # Mock JsonOutput with AsyncMock for async methods
        mock_stats = MagicMock()
        mock_stats.total_record_count = 1
        mock_stats.chunk_count = 1

        with patch("app.activities.JsonOutput") as mock_json_output:
            mock_instance = MagicMock()
            mock_instance.write_dataframe = AsyncMock()
            mock_instance.get_statistics = AsyncMock(return_value=mock_stats)
            mock_json_output.return_value = mock_instance

            result = await activities.save_result_to_json(
                calculation_result, "/tmp/test"
            )

            assert result["success"] is True
            assert result["record_count"] == 1
            assert result["chunk_count"] == 1
            assert "/tmp/test/results/factorial_result" in result["file_path"]

