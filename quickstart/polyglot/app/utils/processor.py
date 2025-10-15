"""Java processor module for Python-Java integration using JPype.

This module handles JVM lifecycle management and provides a clean interface
for calling Java methods from Python code.
"""

import os
from typing import Any, Dict

import jpype
import jpype.imports
from app.utils.config import JavaConfig
from application_sdk.observability.logger_adaptor import get_logger

LOGGER = get_logger(__name__)

# Global flag to track JVM state across the application
JVM_STARTED_GLOBAL = False


def start_jvm(config: JavaConfig, jar_path: str) -> None:
    """Start the Java Virtual Machine with the specified configuration.

    The JVM can only be started once per process. This function checks if
    the JVM is already running and reuses it if so.

    Args:
        config: JavaConfig instance with configuration settings.
        jar_path: Path to the JAR file to add to classpath.

    Raises:
        RuntimeError: If configuration validation fails or JVM startup fails.
    """
    global JVM_STARTED_GLOBAL

    # Check if already started
    if JVM_STARTED_GLOBAL:
        LOGGER.debug("JVM already started (global flag set)")
        return

    if jpype.isJVMStarted():
        LOGGER.debug("JVM already started (jpype check)")
        JVM_STARTED_GLOBAL = True
        return

    # Validate configuration before starting
    if not config.validate_configuration():
        raise RuntimeError("Configuration validation failed")

    # Set JAVA_HOME if not already set
    if not os.environ.get("JAVA_HOME"):
        os.environ["JAVA_HOME"] = config.JAVA_HOME
        LOGGER.info(f"Set JAVA_HOME to: {config.JAVA_HOME}")

    LOGGER.info(f"Starting JVM with classpath: {jar_path}")
    try:
        jpype.startJVM(classpath=[jar_path])
        JVM_STARTED_GLOBAL = True
        LOGGER.info("JVM started successfully")
    except Exception as e:
        LOGGER.error(f"Failed to start JVM: {e}", exc_info=True)
        raise RuntimeError(f"JVM startup failed: {e}")


def shutdown_jvm() -> None:
    """Shutdown the Java Virtual Machine.

    Note: In production, you typically don't need to shutdown the JVM
    as it will be cleaned up when the process exits. This is mainly
    useful for testing scenarios.
    """
    global JVM_STARTED_GLOBAL
    if JVM_STARTED_GLOBAL and jpype.isJVMStarted():
        jpype.shutdownJVM()
        JVM_STARTED_GLOBAL = False
        LOGGER.info("JVM shutdown successfully")


class FactorialProcessor:
    """Processor for calculating factorials using Java implementation.

    This class provides a Python interface to the Java FactorialCalculator
    class. It handles JVM lifecycle management using a context manager pattern.

    Example:
        >>> with FactorialProcessor(number=5) as processor:
        ...     result = processor.calculate()
        ...     print(result)
        {'result': 120, 'input': 5, 'success': True}
    """

    def __init__(self, number: int):
        """Initialize the factorial processor.

        Args:
            number: The number to calculate factorial for.
        """
        self.number = number
        self.config = JavaConfig()
        self.jar_path = self.config.JAR_PATH
        LOGGER.debug(f"Initialized FactorialProcessor with number: {number}")

    def __enter__(self):
        """Context manager entry point.

        Starts the JVM with the configured classpath if not already running.

        Returns:
            self: The processor instance for use in context manager.

        Raises:
            RuntimeError: If JVM startup fails.
        """
        try:
            start_jvm(self.config, self.jar_path)
            return self
        except Exception as e:
            LOGGER.error(f"Failed to initialize processor: {e}", exc_info=True)
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point.

        Note: We don't shutdown the JVM here as it can only be started once
        per process. The JVM will be cleaned up when the process exits.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.
        """
        # JVM is kept running for reuse by other operations
        pass

    def calculate(self) -> Dict[str, Any]:
        """Calculate the factorial of the configured number using Java.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - result: The factorial result (int)
                - input: The input number (int)
                - success: Whether the calculation succeeded (bool)
                - error: Error message if success is False (str, optional)

        Example:
            >>> processor = FactorialProcessor(5)
            >>> with processor:
            ...     result = processor.calculate()
            >>> print(result)
            {'result': 120, 'input': 5, 'success': True}
        """
        LOGGER.debug(f"Calculating factorial of {self.number} using Java")

        try:
            # Load the Java class using jpype.JClass
            # This is the proper way to import Java classes after JVM is started
            FactorialCalculator = jpype.JClass("FactorialCalculator")

            # Call the static method
            result = FactorialCalculator.calculateFactorial(self.number)

            LOGGER.info(f"Successfully calculated factorial: {self.number}! = {result}")

            return {
                "result": int(result),
                "input": self.number,
                "success": True,
            }

        except Exception as e:
            error_msg = str(e)
            LOGGER.error(f"Failed to calculate factorial: {error_msg}", exc_info=True)

            return {
                "result": None,
                "input": self.number,
                "success": False,
                "error": error_msg,
            }

    @staticmethod
    def get_version() -> str:
        """Get the version of the Java calculator.

        Returns:
            str: Version string from the Java class.

        Raises:
            RuntimeError: If JVM is not started or class cannot be loaded.
        """
        try:
            if not jpype.isJVMStarted():
                raise RuntimeError("JVM is not started")

            # Load the Java class using jpype.JClass
            FactorialCalculator = jpype.JClass("FactorialCalculator")

            version = FactorialCalculator.getVersion()
            LOGGER.debug(f"Java calculator version: {version}")
            return str(version)

        except Exception as e:
            LOGGER.error(f"Failed to get version: {e}", exc_info=True)
            raise

    @staticmethod
    def get_description() -> str:
        """Get the description of the Java calculator.

        Returns:
            str: Description string from the Java class.

        Raises:
            RuntimeError: If JVM is not started or class cannot be loaded.
        """
        try:
            if not jpype.isJVMStarted():
                raise RuntimeError("JVM is not started")

            # Load the Java class using jpype.JClass
            FactorialCalculator = jpype.JClass("FactorialCalculator")

            description = FactorialCalculator.getDescription()
            LOGGER.debug(f"Java calculator description: {description}")
            return str(description)

        except Exception as e:
            LOGGER.error(f"Failed to get description: {e}", exc_info=True)
            raise
