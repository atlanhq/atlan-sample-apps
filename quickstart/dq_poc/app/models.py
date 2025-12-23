"""Data models for the bulk metadata scaler app."""

from dataclasses import dataclass


@dataclass
class DqPocResult:
    """Final result of the dq poc sample application."""

    result: int = 0
