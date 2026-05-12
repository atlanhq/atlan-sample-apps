"""Data models + random classifier for the batch processor sample."""

from __future__ import annotations

import random
from dataclasses import dataclass

# Demo distribution: 50% success, 30% retry, 20% fail
_STATUSES = ("SUCCESS", "RETRY", "FAILED")
_WEIGHTS = (0.5, 0.3, 0.2)


@dataclass
class EventRecord:
    event_id: str
    payload: str


@dataclass
class ResultRecord:
    """One processing result row written back to the lakehouse."""

    event_id: str
    status: str  # "SUCCESS" | "RETRY" | "FAILED"
    api_status_code: int | None
    error_message: str | None


class RandomClassifier:
    """Randomly classifies a result — demo only.

    Returns one of SUCCESS / RETRY / FAILED with the weights above. Real apps
    would inspect the API response and use deterministic rules.
    """

    @staticmethod
    def classify(
        event_id: str, api_status_code: int | None, rng: random.Random | None = None
    ) -> ResultRecord:
        r = rng or random
        status = r.choices(_STATUSES, weights=_WEIGHTS, k=1)[0]
        return ResultRecord(
            event_id=event_id,
            status=status,
            api_status_code=api_status_code,
            error_message=None if status == "SUCCESS" else f"random {status.lower()}",
        )
