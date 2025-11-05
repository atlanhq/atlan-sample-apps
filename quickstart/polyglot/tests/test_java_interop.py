"""Integration tests for Java integration in the Polyglot app.

Note: These tests require Java to be installed and the JAR file to be built.
They are integration tests that actually start the JVM and call Java methods.
"""

import pytest
from app.utils.config import JavaConfig
from app.utils.processor import FactorialProcessor


class TestJavaConfig:
    """Test suite for JavaConfig."""

    def test_config_attributes(self):
        """Test that config has required attributes."""
        config = JavaConfig()

        assert hasattr(config, "JAVA_HOME")
        assert hasattr(config, "JAR_PATH")
        assert hasattr(config, "JVM_MAX_MEMORY")
        assert hasattr(config, "JVM_INITIAL_MEMORY")

    def test_get_jvm_args(self):
        """Test JVM arguments generation."""
        args = JavaConfig.get_jvm_args()

        assert isinstance(args, list)
        assert len(args) > 0
        assert any("-Xmx" in arg for arg in args)
        assert any("-Xms" in arg for arg in args)

    def test_log_configuration(self):
        """Test configuration logging."""
        # Should not raise any exceptions
        JavaConfig.log_configuration()


class TestFactorialProcessor:
    """Test suite for FactorialProcessor.

    Note: These are integration tests that require:
    1. Java JDK 11+ installed
    2. JAR file built (run: cd java_src && ./build.sh)
    """

    @pytest.mark.skipif(
        not JavaConfig().validate_configuration(),
        reason="Java not configured or JAR not built",
    )
    def test_calculate_factorial_success(self):
        """Test successful factorial calculation using real Java."""
        processor = FactorialProcessor(number=5)

        with processor:
            result = processor.calculate()

            assert result["success"] is True
            assert result["result"] == 120
            assert result["input"] == 5

    @pytest.mark.skipif(
        not JavaConfig().validate_configuration(),
        reason="Java not configured or JAR not built",
    )
    def test_calculate_factorial_zero(self):
        """Test factorial of zero."""
        processor = FactorialProcessor(number=0)

        with processor:
            result = processor.calculate()

            assert result["success"] is True
            assert result["result"] == 1
            assert result["input"] == 0

    @pytest.mark.skipif(
        not JavaConfig().validate_configuration(),
        reason="Java not configured or JAR not built",
    )
    def test_calculate_factorial_large_number(self):
        """Test factorial of large number (20)."""
        processor = FactorialProcessor(number=20)

        with processor:
            result = processor.calculate()

            assert result["success"] is True
            assert result["result"] == 2432902008176640000
            assert result["input"] == 20

    @pytest.mark.skipif(
        not JavaConfig().validate_configuration(),
        reason="Java not configured or JAR not built",
    )
    def test_calculate_factorial_too_large(self):
        """Test factorial of number larger than 20 (should fail)."""
        processor = FactorialProcessor(number=25)

        with processor:
            result = processor.calculate()

            # Java should throw an exception for numbers > 20
            assert result["success"] is False
            assert "error" in result

    @pytest.mark.skipif(
        not JavaConfig().validate_configuration(),
        reason="Java not configured or JAR not built",
    )
    def test_calculate_factorial_negative(self):
        """Test factorial of negative number (should fail)."""
        processor = FactorialProcessor(number=-5)

        with processor:
            result = processor.calculate()

            # Java should throw an exception for negative numbers
            assert result["success"] is False
            assert "error" in result

    @pytest.mark.skipif(
        not JavaConfig().validate_configuration(),
        reason="Java not configured or JAR not built",
    )
    def test_get_version(self):
        """Test getting Java calculator version."""
        processor = FactorialProcessor(number=0)

        with processor:
            version = processor.get_version()

            assert isinstance(version, str)
            assert len(version) > 0
            assert version == "1.0.0"

    @pytest.mark.skipif(
        not JavaConfig().validate_configuration(),
        reason="Java not configured or JAR not built",
    )
    def test_get_description(self):
        """Test getting Java calculator description."""
        processor = FactorialProcessor(number=0)

        with processor:
            description = processor.get_description()

            assert isinstance(description, str)
            assert len(description) > 0
            assert "Factorial" in description

    @pytest.mark.skipif(
        not JavaConfig().validate_configuration(),
        reason="Java not configured or JAR not built",
    )
    def test_multiple_calculations(self):
        """Test multiple calculations in sequence."""
        test_cases = [
            (0, 1),
            (1, 1),
            (5, 120),
            (10, 3628800),
        ]

        for number, expected in test_cases:
            processor = FactorialProcessor(number=number)

            with processor:
                result = processor.calculate()

                assert result["success"] is True
                assert result["result"] == expected
                assert result["input"] == number


# Run tests with: pytest tests/utils.py -v
# Skip integration tests: pytest tests/utils.py -v -m "not skipif"
