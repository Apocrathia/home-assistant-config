#!/usr/bin/env python3
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

import verify_checks

FIXTURE_FEE = "def fee(cents):\n    return int(cents * 0.03)\n"
REFERENCE_FEE = (
    "def fee(cents):\n"
    "    if cents <= 0:\n"
    "        return 0\n"
    "    return (cents * 3 + 50) // 100\n"
)
NAIVE_FEE = "def fee(cents):\n    return round(cents * 0.03)\n"

FEE_GRADER = '''import importlib.util, json, sys
from pathlib import Path

checks = []
def record(name, ok): checks.append((name, bool(ok)))

# Denominator is this list, not how far record() got. A crash leaves the
# rest unscored, and they still count.
probes = [
    ('base-rate-exact', 100_00, 300),
    ('half-cent-rounds-up', 150, 5),  # float path gives 4
    ('tiny-order-rounds-up', 17, 1),  # floor gives 0
    ('zero-order', 0, 0),
]

if Path('src/fee.py').is_file():
    spec = importlib.util.spec_from_file_location('fee', 'src/fee.py')
    fee = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(fee)
        for name, cents, want in probes:
            record(name, fee.fee(cents) == want)
    except Exception:
        pass  # a crash leaves the rest unscored, still in total
ok = sum(1 for _, passed in checks if passed)
score = ok / len(probes) if probes else 0
print(f'EVAL_SCORE {json.dumps({"score": score, "passed": ok, "total": len(probes)})}')
sys.exit(0)
'''


def write_fee_corpus(root, task_name="fee-task"):
    """Write the reference corpus from the skill doc: one task, four overlays."""
    task = Path(root) / task_name
    (task / "files/src").mkdir(parents=True)
    (task / "files/src/fee.py").write_text(FIXTURE_FEE)
    (task / "grader.py").write_text(FEE_GRADER)
    (task / "reference/src").mkdir(parents=True)
    (task / "reference/src/fee.py").write_text(REFERENCE_FEE)
    (task / "naive/src").mkdir(parents=True)
    (task / "naive/src/fee.py").write_text(NAIVE_FEE)
    (task / "decoy-docs/src").mkdir(parents=True)
    (task / "decoy-docs/src/fee.py").write_text(
        '"""3% fee, rounded half up."""\n' + FIXTURE_FEE
    )
    return task


def write_grader(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)


class VerifyChecksTest(unittest.TestCase):
    def run_gate(self, corpus, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = verify_checks.main([str(corpus), *args])
        return status, output.getvalue()

    def test_valid_corpus_passes(self):
        with tempfile.TemporaryDirectory() as root:
            write_fee_corpus(root)
            status, output = self.run_gate(root, "--timeout", "20")
            self.assertEqual(0, status)
            self.assertIn("ok - fee-task", output)
            self.assertIn("reference=1.000", output)
            self.assertIn("naive=0.750", output)

    def test_reference_below_one_fails(self):
        with tempfile.TemporaryDirectory() as root:
            task = write_fee_corpus(root)
            (task / "reference/src/fee.py").write_text(FIXTURE_FEE)
            status, output = self.run_gate(root, "--timeout", "20")
            self.assertEqual(1, status)
            self.assertIn("FAIL - fee-task", output)

    def test_fixture_passing_is_grader_rot(self):
        with tempfile.TemporaryDirectory() as root:
            task = write_fee_corpus(root)
            (task / "files/src/fee.py").write_text(REFERENCE_FEE)
            status, output = self.run_gate(root, "--timeout", "20")
            self.assertEqual(1, status)
            self.assertIn("FAIL - fee-task", output)

    def test_decoy_passing_fails_the_gate(self):
        with tempfile.TemporaryDirectory() as root:
            task = write_fee_corpus(root)
            (task / "decoy-docs/src/fee.py").write_text(REFERENCE_FEE)
            status, output = self.run_gate(root, "--timeout", "20")
            self.assertEqual(1, status)
            self.assertIn("FAIL - fee-task", output)

    def test_crash_after_early_pass_does_not_score_one(self):
        crashing = (
            "def fee(cents):\n"
            "    if cents < 100_00:\n"
            "        raise RuntimeError('boundary')\n"
            "    return 300\n"
        )
        with tempfile.TemporaryDirectory() as root:
            task = write_fee_corpus(root)
            (task / "reference/src/fee.py").write_text(crashing)
            status, output = self.run_gate(root, "--timeout", "20")
            self.assertEqual(1, status)
            self.assertIn("reference=0.250", output)

    def test_missing_corpus_dir_is_a_usage_error(self):
        with self.assertRaises(SystemExit):
            verify_checks.main(["/no/such/corpus-dir"])

    def test_corpus_without_tasks_fails(self):
        with tempfile.TemporaryDirectory() as root:
            status, _ = self.run_gate(root)
            self.assertEqual(1, status)


class ScoreTest(unittest.TestCase):
    def score_with(self, grader_body, timeout=20.0, plant=False):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            if plant:
                (workspace / verify_checks.GRADER_NAME).write_text("# planted")
            return verify_checks.score(workspace, grader_body, timeout)

    def test_sentinel_parse_and_partial_credit(self):
        body = '''import json, sys
print('EVAL_SCORE {"score": 0.5, "passed": 2, "total": 4}')
sys.exit(0)
'''
        self.assertEqual(0.5, self.score_with(body))

    def test_missing_sentinel_is_a_dead_grader(self):
        body = "print('all good here')\nimport sys; sys.exit(0)\n"
        self.assertEqual(0.0, self.score_with(body))

    def test_nonzero_exit_scores_zero_even_with_sentinel(self):
        body = '''import json, sys
print('EVAL_SCORE {"score": 1.0}')
sys.exit(1)
'''
        self.assertEqual(0.0, self.score_with(body))

    def test_score_outside_unit_interval_scores_zero(self):
        body = '''import json, sys
print('EVAL_SCORE {"score": 7}')
sys.exit(0)
'''
        self.assertEqual(0.0, self.score_with(body))

    def test_timeout_scores_zero(self):
        body = "import time\ntime.sleep(5)\n"
        self.assertEqual(0.0, self.score_with(body, timeout=0.2))

    def test_planted_grader_scores_zero(self):
        body = '''import json, sys
print('EVAL_SCORE {"score": 1.0}')
sys.exit(0)
'''
        self.assertEqual(0.0, self.score_with(body, plant=True))


if __name__ == "__main__":
    unittest.main()
