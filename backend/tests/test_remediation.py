"""Remediation + syntax validation + predicted-after simulation tests."""
import unittest

from app.compliance.engine import evaluate_model
from app.compliance.rules_loader import load_rules
from app.remediation.remediator import apply_effects, attach_remediations, build_remediation
from app.remediation.validator import validate_commands
from tests.support import audit_for, finding_by


class TestRemediationTemplates(unittest.TestCase):
    def test_cisco_telnet_remediation_valid(self):
        rem = build_remediation("cisco", "NET-01")
        self.assertIsNotNone(rem)
        self.assertTrue(rem.validated)
        self.assertTrue(any("transport input ssh" in c for c in rem.commands))

    def test_no_template_returns_none(self):
        self.assertIsNone(build_remediation("cisco", "NET-99"))


class TestSyntaxValidator(unittest.TestCase):
    def test_fortinet_balanced_ok(self):
        ok, _ = validate_commands("fortinet", ["config system global", " set admintimeout 10", "end"])
        self.assertTrue(ok)

    def test_fortinet_unbalanced_detected(self):
        ok, note = validate_commands("fortinet", ["config system global", " set admintimeout 10"])
        self.assertFalse(ok)
        self.assertIn("unbalanced", note)

    def test_fortinet_next_without_edit(self):
        ok, _ = validate_commands("fortinet", ["config x", "next", "end"])
        self.assertFalse(ok)

    def test_juniper_requires_set_delete(self):
        self.assertTrue(validate_commands("juniper", ["set system services ssh"])[0])
        self.assertFalse(validate_commands("juniper", ["frobnicate everything"])[0])

    def test_empty_commands_invalid(self):
        self.assertFalse(validate_commands("cisco", [])[0])


class TestPredictedAfter(unittest.TestCase):
    def test_remediation_clears_all_criticals_and_improves_score(self):
        rules = load_rules()
        for name in ("cisco", "juniper", "fortinet"):
            model, findings, before = audit_for(name)
            remediated = attach_remediations(model.vendor, findings)
            self.assertTrue(remediated, f"{name} should have at least one remediation")
            after_model = apply_effects(model, model.vendor, remediated)
            _, after = evaluate_model(after_model, rules)
            self.assertGreater(after.score, before.score, f"{name} score should improve")
            self.assertEqual(after.critical, 0, f"{name} criticals should be cleared")
            # every attached remediation must be syntactically valid
            for f in findings:
                if f.remediation:
                    self.assertTrue(f.remediation.validated, f"{name}/{f.control_id} invalid syntax")

    def test_prediction_does_not_mutate_original_model(self):
        model, findings, _ = audit_for("cisco")
        original_telnet = model.telnet_enabled
        remediated = attach_remediations(model.vendor, findings)
        apply_effects(model, model.vendor, remediated)
        self.assertEqual(model.telnet_enabled, original_telnet)  # copy, not in-place


if __name__ == "__main__":
    unittest.main()
