"""Unit tests for rules.py. Run: python3 -m unittest census/test_census.py

Every example sentence below was written by hand for this test; none is taken from a real pull request.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules  # noqa: E402

CLAIMS = [
    ("All tests pass.", "P9"),
    ("All 42 unit tests pass locally", "P9"),
    ("all the existing tests still pass", "P9"),
    ("All tests are passing", "P9"),
    ("Tests pass", "P11"),
    ("**Tests:** passing", "P11"),
    ("The new test passes", "P11"),
    ("Test suite passes with the change", "P11"),
    ("CI is green", "P10"),
    ("All checks pass", "P10"),
    ("- ✅ `pytest -q`", "P4"),
    ("- ✅ `python -m pytest tests/`", "P4"),
    ("✅ npm run test:unit", "P4"),
    ("- `pytest` ✅", "P5"),
    ("Tests: ✅", "P5"),
    ("Tests added and passing", "P6"),
    ("Added unit tests and they pass", "P6"),
    ("=== 42 passed in 3.10s ===", "P3"),
    ("128 tests passed, 0 failed", "P3"),
    ("42/42 tests passing", "P1"),
    ("The change passes all existing tests", "P7"),
    ("Green CI on the last commit", "P8"),
    ("Added 5 new passing tests", "P2"),
    ("- [x] Ensure all tests pass", "P9"),
    ("All tests pass with no regressions", "P9"),
    ("Verified that all tests pass", "P9"),
    ("- Tests: 15/15 ✅", "P5"),
    ("pytest: 41 passed, 1 xfailed", "P3"),
]

NOT_CLAIMS = [
    "Make sure all tests pass",
    "- [ ] All tests pass",
    "All tests should pass",
    "Do all tests pass?",
    "Tests do not pass yet",
    "Most tests pass",
    "All tests pass except test_parse",
    "Fix the failing test; all tests now pass",
    "3 failed, 39 passed",
    "40/42 tests passing",
    "40 of 42 tests pass",
    "Added tests for the parser",
    "- ✅ Added tests for edge cases",
    "Tests passing a null value now raise",
    "- ⚠️ `npm test` (fails: missing module)",
    "Once CI passes this can be merged",
    "> All tests pass",
    "Testing: npm test",
    "CI pending",
    "Run the tests to confirm",
    "<!-- Ensure all tests pass before requesting review -->",
    "Timeout increased; all tests pass",
    "Last run 10/20: all tests pass",
    "The workflow passes the token to the step",
]


class ClaimRules(unittest.TestCase):
    def test_claims(self):
        for text, rule in CLAIMS:
            with self.subTest(text=text):
                got = rules.find_claim("", text)
                self.assertIsNotNone(got, text)
                self.assertEqual(got["rule"], rule, text)

    def test_not_claims(self):
        for text in NOT_CLAIMS:
            with self.subTest(text=text):
                self.assertIsNone(rules.find_claim("", text), text)

    def test_quoted_task_removed(self):
        body = ("Implements the parser.\n<details><summary>Original prompt</summary>\n\n"
                "All tests pass on main.\n</details>\n")
        self.assertIsNone(rules.find_claim("", body))

    def test_snippet_masks_mentions_and_is_short(self):
        body = "Thanks @someone-else. " + "x " * 150 + "All tests pass after the refactor."
        got = rules.find_claim("", body)
        self.assertIsNotNone(got)
        self.assertLessEqual(len(got["snippet"]), rules.SNIPPET_MAX)
        self.assertIn("All tests pass", got["snippet"])
        self.assertNotIn("someone", rules.find_claim("", "@someone: all tests pass")["snippet"])

    def test_first_line_and_count(self):
        got = rules.find_claim("Title", "Tests pass\nnothing\nCI is green")
        self.assertEqual((got["rule"], got["n_lines"]), ("P11", 2))


class CiMapping(unittest.TestCase):
    def run_item(self, conclusion, status="completed", app="github-actions", name="test"):
        return ["run", app, name, status, conclusion, ""]

    def status_item(self, state, context="ci/build"):
        return ["status", "", context, state, "", ""]

    def test_states(self):
        self.assertEqual(rules.item_state(self.run_item("success")), "success")
        self.assertEqual(rules.item_state(self.run_item("timed_out")), "failure")
        self.assertEqual(rules.item_state(self.run_item("cancelled")), "neutral")
        self.assertEqual(rules.item_state(self.run_item(None, status="in_progress")), "pending")
        self.assertEqual(rules.item_state(self.status_item("error")), "failure")
        self.assertEqual(rules.item_state(self.status_item("pending")), "pending")

    def test_rollup(self):
        r = self.run_item
        self.assertEqual(rules.rollup([]), "none")
        self.assertEqual(rules.rollup([r("skipped"), r("neutral")]), "none")
        self.assertEqual(rules.rollup([r("success"), r(None, status="queued")]), "pending")
        self.assertEqual(rules.rollup([r("success"), r(None, status="queued"), r("failure")]), "failure")
        self.assertEqual(rules.rollup([r("success"), r("skipped")]), "success")

    def test_core_ci_drops_non_test_checks(self):
        items = [self.run_item("success", name="build (ubuntu)"),
                 self.status_item("failure", context="license/cla"),
                 self.run_item("failure", app="vercel", name="Vercel Preview Comments")]
        self.assertEqual(rules.ci_of(items), ("failure", "success"))
        lint = [self.run_item("failure", name="lint"), self.run_item("success", name="pytest")]
        self.assertEqual(rules.ci_of(lint), ("failure", "failure"))


class Stats(unittest.TestCase):
    def test_wilson_known_values(self):
        lo, hi = rules.wilson(0, 30)
        self.assertAlmostEqual(lo, 0.0, places=6)
        self.assertAlmostEqual(hi, 0.11352, places=4)
        self.assertAlmostEqual(rules.wilson(0, 75)[1], 0.04870, places=4)
        self.assertGreater(rules.wilson(0, 72)[1], 0.05)
        self.assertLess(rules.wilson(0, 73)[1], 0.05)
        lo, hi = rules.wilson(1, 10)
        self.assertAlmostEqual(lo, 0.01788, places=4)
        self.assertAlmostEqual(hi, 0.40415, places=4)

    def test_agent_labels(self):
        self.assertEqual(rules.agent_of("OpenAI_Codex"), "codex")
        self.assertEqual(rules.agent_of("Claude_Code"), "claude_code")
        self.assertEqual(rules.agent_of("Copilot"), "copilot")
        self.assertIsNone(rules.agent_of("Jules"))


def synthetic_rows(failures, n, agent="devin"):
    """Rows for one agent with n CI verdicts, `failures` of them failures. Synthetic, for tests only."""
    out = []
    for i in range(n):
        state = "failure" if i < failures else "success"
        items = [["run", "github-actions", "test", "completed", state, "2025-01-01T00:00:00Z"]]
        out.append({
            "row_id": f"{agent}:example/repo{i}#1", "agent": agent, "repo": f"example/repo{i}", "pr_number": "1",
            "pr_url": f"https://github.com/example/repo{i}/pull/1", "pr_state": "closed", "merged": "0",
            "author_type": "Bot", "pr_created_at": "2025-01-01T00:00:00Z", "pr_closed_at": "",
            "body_last_edited_at": "", "edit_info": "unavailable", "head_sha": "0" * 40,
            "head_committed_at": "2024-12-31T00:00:00Z", "claim_rule": "P9", "claim_snippet": "All tests pass",
            "n_claim_lines": "1", "ci": state, "ci_core": state, "n_checks": "1", "ci_last_completed_at": "",
            "claim_aligned": "", "checks_json": rules.checks_json(items), "frame": "synthetic",
            "collected_at": "2026-01-01T00:00:00Z", "hand_label": "", "hand_note": "",
        })
    return out


class Verify(unittest.TestCase):
    def test_render_and_kill_condition(self):
        import verify
        rows = synthetic_rows(0, 75, "devin") + synthetic_rows(0, 75, "codex")
        self.assertEqual(verify.check_rows(rows), ([], []))
        block = verify.render(rows)
        self.assertIn("| Devin | 75 | 75 | 0 | 0 | 0 | 75 | 0 | 0.0% | 0.0% to 4.9% |", block)
        self.assertIn("Met:", block)
        rows += synthetic_rows(1, 75, "cursor")
        self.assertIn("Not met: the Wilson upper bound is 5% or more for Cursor.", verify.render(rows))
        self.assertIn("Inconclusive", verify.render(synthetic_rows(3, 40)))
        self.assertIn("not reported (n < 30)", verify.render(synthetic_rows(1, 29)))

    def test_tampering_is_caught(self):
        import verify
        rows = synthetic_rows(2, 40)
        rows[5]["ci"] = "failure"
        rows[6]["claim_snippet"] = "Refactor only"
        rows[7]["hand_label"] = "claim"
        rows[8]["hand_label"] = "maybe"
        errors, _ = verify.check_rows(rows)
        text = "\n".join(errors)
        self.assertIn("re-derived", text)
        self.assertIn("does not match the snippet", text)
        self.assertIn("hand_label must be", text)
        rows = synthetic_rows(0, 3) + [dict(synthetic_rows(0, 1)[0], row_id="devin:example/repo0#2",
                                             pr_number="2")] * 2
        self.assertTrue(any("cap is 2" in e for e in verify.check_rows(rows)[0]))

    def test_hand_sample_is_fixed(self):
        import verify
        rows = synthetic_rows(0, 50)
        sample = verify.hand_sample(rows)
        self.assertEqual(len(sample), 30)
        self.assertEqual(sample, verify.hand_sample(list(reversed(rows))))


if __name__ == "__main__":
    unittest.main()
