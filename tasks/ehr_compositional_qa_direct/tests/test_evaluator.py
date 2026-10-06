"""Regression tests for the all-correct benchmark contract."""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from evaluator import NOT_APPLICABLE, is_correct, score_submission


def wrong(answer):
    """An answer that is incorrect for the given gold answer."""
    return 0 if answer == NOT_APPLICABLE else answer + 100


class EvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.key = Path(__file__).with_name("answer_key.json")
        self.answers = [
            {"question_id": r["question_id"], "answer": r["gt_answer"]}
            for r in json.loads(self.key.read_text())
        ]
        self.submission = self.root / "submission.json"
        self.n = len(self.answers)

    def score(self, answers):
        self.submission.write_text(json.dumps(answers))
        return score_submission(self.submission, self.key)

    def test_all_correct_passes(self):
        metrics = self.score(self.answers)
        self.assertTrue(metrics["passed"])
        self.assertEqual(metrics["correct"], self.n)
        self.assertTrue(all("expected" not in row and "gt_answer" not in row
                            for row in metrics["per_question"]))

    def test_each_single_wrong_answer_fails(self):
        for index in range(self.n):
            with self.subTest(index=index):
                answers = copy.deepcopy(self.answers)
                answers[index]["answer"] = wrong(answers[index]["answer"])
                metrics = self.score(answers)
                self.assertFalse(metrics["passed"])
                self.assertEqual(metrics["correct"], self.n - 1)
                self.assertAlmostEqual(metrics["pass_rate_overall"], (self.n - 1) / self.n)

    def test_invalid_submission_fails(self):
        for answers in [self.answers[:-1], self.answers + [self.answers[0]], {}, [],
                        self.answers + [{"question_id": [], "answer": 0}]]:
            with self.subTest(answers_type=type(answers)):
                self.assertFalse(self.score(answers)["passed"])

    def test_missing_and_malformed_file_fail(self):
        self.assertFalse(score_submission(self.submission, self.key)["passed"])
        self.submission.write_text("{")
        self.assertFalse(score_submission(self.submission, self.key)["passed"])

    def test_non_numeric_and_non_finite_answers_fail(self):
        for index in range(self.n):
            for value in [None, True, False, "2", "N/A", "Not_Applicable", [], {},
                          float("nan"), float("inf")]:
                with self.subTest(index=index, value=value):
                    answers = copy.deepcopy(self.answers)
                    answers[index]["answer"] = value
                    self.assertFalse(self.score(answers)["passed"])

    def test_not_applicable_token(self):
        for tol in [{"kind": "integer"}, {"kind": "continuous", "rel": 0.01, "abs": 0.001}]:
            with self.subTest(tol=tol):
                self.assertTrue(is_correct(NOT_APPLICABLE, NOT_APPLICABLE, tol))
                for pred in [0, 0.0, None, "", "N/A", "not applicable", "NOT_APPLICABLE"]:
                    self.assertFalse(is_correct(pred, NOT_APPLICABLE, tol))
                self.assertFalse(is_correct(NOT_APPLICABLE, 0.0, tol))
                self.assertFalse(is_correct(NOT_APPLICABLE, 3.0, tol))

    def test_constant_answers_fail(self):
        for value in [NOT_APPLICABLE, 0]:
            with self.subTest(value=value):
                metrics = self.score([{"question_id": a["question_id"], "answer": value}
                                      for a in self.answers])
                self.assertFalse(metrics["passed"])
                self.assertLess(metrics["correct"], self.n)

    def test_integer_tolerance_boundaries(self):
        tol = {"kind": "integer"}
        self.assertTrue(is_correct(2, 2.0, tol))
        self.assertTrue(is_correct(2.49, 2.0, tol))
        # A half-integer must not match both neighbouring integers.
        self.assertFalse(is_correct(2.5, 2.0, tol))
        self.assertFalse(is_correct(2.5, 3.0, tol))
        self.assertFalse(is_correct(-2.5, -3.0, tol))

    def test_continuous_tolerance_boundaries(self):
        tol = {"kind": "continuous", "rel": 0.01, "abs": 0.001}
        self.assertTrue(is_correct(0.1514, 0.15, tol))
        self.assertFalse(is_correct(0.1516, 0.15, tol))
        self.assertTrue(is_correct(0.001, 0.0, tol))
        self.assertFalse(is_correct(0.0011, 0.0, tol))
        self.assertTrue(is_correct(101, 100.0, tol))
        self.assertFalse(is_correct(101.01, 100.0, tol))

    def test_invalid_tolerance_in_key_raises(self):
        key = json.loads(self.key.read_text())
        bad_key = self.root / "bad_key.json"
        for tol in [None, {}, {"kind": "loose"}, {"kind": "continuous", "rel": 0.01},
                    {"kind": "continuous", "rel": -1, "abs": 0.001}]:
            with self.subTest(tol=tol):
                broken = copy.deepcopy(key)
                broken[0]["tolerance"] = tol
                bad_key.write_text(json.dumps(broken))
                self.submission.write_text(json.dumps(self.answers))
                with self.assertRaises(ValueError):
                    score_submission(self.submission, bad_key)

    def test_invalid_gt_answer_in_key_raises(self):
        key = json.loads(self.key.read_text())
        bad_key = self.root / "bad_key.json"
        for gt in [None, True, "N/A", "2", float("inf")]:
            with self.subTest(gt=gt):
                broken = copy.deepcopy(key)
                broken[0]["gt_answer"] = gt
                bad_key.write_text(json.dumps(broken))
                self.submission.write_text(json.dumps(self.answers))
                with self.assertRaises(ValueError):
                    score_submission(self.submission, bad_key)

    def test_cli_writes_binary_reward(self):
        for corrupt, expected in [(False, 1.0), (True, 0.0)]:
            answers = copy.deepcopy(self.answers)
            if corrupt:
                answers[0]["answer"] = wrong(answers[0]["answer"])
            self.score(answers)
            subprocess.run([
                sys.executable, str(Path(__file__).with_name("evaluator.py")),
                "--submission", str(self.submission), "--answer-key", str(self.key),
                "--metrics-out", str(self.root / "metrics.json"),
                "--reward-out", str(self.root / "reward.json"),
            ], check=True, capture_output=True)
            self.assertEqual(json.loads((self.root / "reward.json").read_text()),
                             {"reward": expected})


if __name__ == "__main__":
    unittest.main()
