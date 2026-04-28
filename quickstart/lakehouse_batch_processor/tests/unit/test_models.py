"""Tests for models and the random classifier."""

import random
import unittest

from app.models import EventRecord, OutcomeRecord, RandomClassifier


class TestEventRecord(unittest.TestCase):
    def test_fields(self):
        e = EventRecord(event_id="e1", payload="hello")
        self.assertEqual(e.event_id, "e1")
        self.assertEqual(e.payload, "hello")


class TestOutcomeRecord(unittest.TestCase):
    def test_success(self):
        o = OutcomeRecord(
            event_id="e1", status="SUCCESS", api_status_code=200, error_message=None
        )
        self.assertEqual(o.status, "SUCCESS")
        self.assertIsNone(o.error_message)

    def test_failure(self):
        o = OutcomeRecord(
            event_id="e2",
            status="FAILED",
            api_status_code=500,
            error_message="boom",
        )
        self.assertEqual(o.status, "FAILED")
        self.assertEqual(o.error_message, "boom")


class TestRandomClassifier(unittest.TestCase):
    def test_returns_one_of_known_statuses(self):
        rng = random.Random(42)
        for _ in range(50):
            outcome = RandomClassifier.classify("e", 200, rng=rng)
            self.assertIn(outcome.status, {"SUCCESS", "RETRY", "FAILED"})

    def test_success_has_no_error_message(self):
        rng = random.Random(42)
        for _ in range(50):
            outcome = RandomClassifier.classify("e", 200, rng=rng)
            if outcome.status == "SUCCESS":
                self.assertIsNone(outcome.error_message)
            else:
                self.assertIsNotNone(outcome.error_message)

    def test_event_id_preserved(self):
        outcome = RandomClassifier.classify("my-id", 200)
        self.assertEqual(outcome.event_id, "my-id")

    def test_api_status_code_preserved(self):
        outcome = RandomClassifier.classify("e", 418)
        self.assertEqual(outcome.api_status_code, 418)

    def test_distribution_roughly_matches_weights(self):
        # Seeded RNG → deterministic check that the classifier honours the
        # 50/30/20 weighting (within a generous tolerance for sample size).
        rng = random.Random(0)
        counts = {"SUCCESS": 0, "RETRY": 0, "FAILED": 0}
        n = 5000
        for _ in range(n):
            counts[RandomClassifier.classify("e", 200, rng=rng).status] += 1
        self.assertGreater(counts["SUCCESS"] / n, 0.40)
        self.assertLess(counts["SUCCESS"] / n, 0.60)
        self.assertGreater(counts["FAILED"] / n, 0.10)
        self.assertLess(counts["FAILED"] / n, 0.30)


if __name__ == "__main__":
    unittest.main()
