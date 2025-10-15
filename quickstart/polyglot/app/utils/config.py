"""Configuration module for Java integration in the Polyglot app.

This module centralizes environment variable configuration and provides
default values for Java integration using JPype.
"""

import os
from pathlib import Path
from typing import List

from application_sdk.observability.logger_adaptor import get_logger

LOGGER = get_logger(__name__)


class JavaConfig:
    """Configuration class for Java integration settings.

    This class manages environment variables and provides sensible defaults
    for Java integration configuration in the Polyglot app.

    Attributes:
        JAVA_HOME: Path to Java installation directory.
        JAR_PATH: Path to the factorial calculator JAR file.
    """

    # Java Configuration
    JAVA_HOME: str = os.getenv(
        "POLYGLOT_JAVA_HOME",
        os.getenv(
            "JAVA_HOME",
            "/opt/homebrew/opt/openjdk@17",  # Default for macOS with Homebrew
        ),
    )

    # JAR Configuration
    _DEFAULT_JAR_PATH = str(
        Path(__file__).parent.parent / "libs" / "factorial-calculator.jar"
    )
    JAR_PATH: str = os.getenv("POLYGLOT_JAR_PATH", _DEFAULT_JAR_PATH)

    # JVM Configuration (optional, for advanced use cases)
    JVM_MAX_MEMORY: str = os.getenv("POLYGLOT_JVM_MAX_MEMORY", "512m")
    JVM_INITIAL_MEMORY: str = os.getenv("POLYGLOT_JVM_INITIAL_MEMORY", "256m")

    @classmethod
    def get_jvm_args(cls) -> List[str]:
        """Get JVM arguments for optimal performance.

        These arguments are optional and can be used when starting the JVM
        if you need to customize memory settings or garbage collection.

        Returns:
            List[str]: List of JVM arguments.
        """
        return [
            f"-Xmx{cls.JVM_MAX_MEMORY}",
            f"-Xms{cls.JVM_INITIAL_MEMORY}",
        ]

    @classmethod
    def validate_configuration(cls) -> bool:
        """Validate the current configuration.

        Checks if JAVA_HOME and JAR_PATH point to existing locations.

        Returns:
            bool: True if configuration is valid, False otherwise.
        """
        issues = []

        # Check Java Home
        if not Path(cls.JAVA_HOME).exists():
            issues.append(f"JAVA_HOME path does not exist: {cls.JAVA_HOME}")

        # Check JAR file
        if not Path(cls.JAR_PATH).exists():
            issues.append(f"JAR file does not exist: {cls.JAR_PATH}")

        if issues:
            for issue in issues:
                LOGGER.error(f"Configuration issue: {issue}")
            return False

        LOGGER.debug("Configuration validation passed")
        return True

    @classmethod
    def log_configuration(cls) -> None:
        """Log current configuration settings."""
        LOGGER.info("Polyglot Java Configuration:")
        LOGGER.info(f"  JAVA_HOME: {cls.JAVA_HOME}")
        LOGGER.info(f"  JAR_PATH: {cls.JAR_PATH}")
        LOGGER.info(f"  JVM_MAX_MEMORY: {cls.JVM_MAX_MEMORY}")
        LOGGER.info(f"  JVM_INITIAL_MEMORY: {cls.JVM_INITIAL_MEMORY}")
