"""Compliance engine tests: control outcomes, summary math, and rule semantics."""
import unittest

from app.compliance.engine import evaluate_control, evaluate_model
from app.compliance.rules_loader import Rule, load_rules
from app.core.types import Severity, Status
from app.normalization.model import SecurityModel
from tests.support import audit_for, finding_by


class TestRuleset(unittest.TestCase):
    def test_ruleset_loads_and_has_absence_controls(self):
        rules = load_rules()
        self.assertGreaterEqual(len(rules), 14)
        absence = [r for r in rules if r.op == "is_false"]
        self.assertGreaterEqual(len(absence), 2)  # spec: >= 2 absence-based controls

    def test_unique_ids(self):
        ids = [r.id for r in load_rules()]
        self.assertEqual(len(ids), len(set(ids)))


class TestCiscoCompliance(unittest.TestCase):
    def setUp(self):
        self.model, self.findings, self.summary = audit_for("cisco")

    def test_counts(self):
        self.assertEqual(self.summary.passed, 5)
        self.assertEqual(self.summary.failed, 6)
        self.assertEqual(self.summary.warnings, 3)
        self.assertEqual(self.summary.critical, 2)
        self.assertEqual(self.summary.total, 14)

    def test_score(self):
        self.assertAlmostEqual(self.summary.score, 35.7, places=1)

    def test_telnet_is_critical_fail(self):
        f = finding_by(self.findings, "NET-01")
        self.assertEqual(f.status, Status.FAIL)
        self.assertEqual(f.severity, Severity.CRITICAL)
        self.assertTrue(f.evidence)  # cites the offending line

    def test_missing_logging_is_warning(self):
        f = finding_by(self.findings, "NET-13")
        self.assertEqual(f.status, Status.WARNING)


class TestFortinetCompliance(unittest.TestCase):
    def setUp(self):
        self.model, self.findings, self.summary = audit_for("fortinet")

    def test_counts(self):
        self.assertEqual(self.summary.passed, 2)
        self.assertEqual(self.summary.failed, 5)
        self.assertEqual(self.summary.warnings, 7)
        self.assertEqual(self.summary.critical, 2)

    def test_logging_disabled_is_fail(self):
        self.assertEqual(finding_by(self.findings, "NET-13").status, Status.FAIL)

    def test_absence_control_passes_when_field_missing(self):
        # weak_plaintext_credentials is None (ENC hash) -> NET-09 on_missing PASS
        self.assertEqual(finding_by(self.findings, "NET-09").status, Status.PASS)


class TestRuleSemantics(unittest.TestCase):
    def _rule(self, **kw):
        base = dict(
            id="T", title="t", category="c", framework="CIS",
            field="telnet_enabled", op="is_false",
            severity=Severity.CRITICAL, on_missing=Status.PASS, value=None,
        )
        base.update(kw)
        return Rule(**base)

    def test_range_operator(self):
        rule = self._rule(field="idle_timeout_minutes", op="range", value=[1, 10],
                          severity=Severity.MEDIUM, on_missing=Status.WARNING)
        self.assertEqual(evaluate_control(SecurityModel(idle_timeout_minutes=5), rule).status, Status.PASS)
        self.assertEqual(evaluate_control(SecurityModel(idle_timeout_minutes=30), rule).status, Status.FAIL)
        self.assertEqual(evaluate_control(SecurityModel(idle_timeout_minutes=0), rule).status, Status.FAIL)

    def test_on_missing_pass_vs_warning(self):
        r_pass = self._rule(on_missing=Status.PASS)
        r_warn = self._rule(on_missing=Status.WARNING)
        self.assertEqual(evaluate_control(SecurityModel(), r_pass).status, Status.PASS)
        self.assertEqual(evaluate_control(SecurityModel(), r_warn).status, Status.WARNING)

    def test_min_operator(self):
        rule = self._rule(field="password_min_length", op="min", value=8,
                          severity=Severity.MEDIUM, on_missing=Status.WARNING)
        self.assertEqual(evaluate_control(SecurityModel(password_min_length=12), rule).status, Status.PASS)
        self.assertEqual(evaluate_control(SecurityModel(password_min_length=6), rule).status, Status.FAIL)


if __name__ == "__main__":
    unittest.main()
