"""Build trust-boundary checks against the installed Lean toolchain."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness import gate

ROOT = Path(__file__).resolve().parent.parent
PROBLEM = ROOT / 'problems/euler-41'
HONEST = ROOT / 'examples/euler-41/Solution.lean'


@unittest.skipUnless(shutil.which('lean'), 'requires Lean')
class BuildBoundaries(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.w = Path(self.tmp.name)
        self.bindir, self.base = gate._toolchain(None)

    def test_lean_path_ordering(self):
        (self.w / 'Challenge.lean').write_text('namespace Challenge\ndef Conjecture := False\nend Challenge\n')
        subprocess.run([str(self.bindir / 'lean'), '-o', 'Challenge.olean', 'Challenge.lean'], cwd=self.w, check=True, capture_output=True)
        sol = self.w / 'Solution.lean'
        sol.write_text('import Challenge\nnamespace Solution\ntheorem main : ¬ False := not_false\nend Solution\n')
        with patch.object(gate, '_toolchain', return_value=(self.bindir, str(self.w) + os.pathsep + self.base)):
            r = gate.run_gate(PROBLEM, sol, 'disproof')
        self.assertFalse(r.ok, r.to_json())
        self.assertEqual(r.failed_layer, 'pin', r.to_json())

    def test_missing_checker_fails_closed(self):
        (self.w / 'lean').symlink_to(self.bindir / 'lean')
        with patch.object(gate, '_toolchain', return_value=(self.w, self.base)):
            r = gate.run_gate(PROBLEM, HONEST, 'disproof')
        self.assertEqual(r.failed_layer, 'recheck', r.to_json())
        self.assertFalse(r.ok)

    def test_missing_audit_report_fails_closed(self):
        original = gate._run
        def run(cmd, cwd, env, timeout, layer):
            if layer == 'axioms':
                return ''
            return original(cmd, cwd, env, timeout, layer)
        with patch.object(gate, '_run', side_effect=run):
            r = gate.run_gate(PROBLEM, HONEST, 'disproof')
        self.assertFalse(r.ok)
        self.assertEqual(r.failed_layer, 'axioms', r.to_json())

    def test_checked_bytes_are_compiled(self):
        pd = self.w / 'problem'
        shutil.copytree(PROBLEM, pd)
        sol = self.w / 'Solution.lean'
        shutil.copy(HONEST, sol)
        def mutate(_):
            (pd / 'Challenge.lean').write_text('broken after hashing')
            sol.write_text('broken after hashing')
            return self.bindir, self.base
        with patch.object(gate, '_toolchain', side_effect=mutate):
            r = gate.run_gate(pd, sol, 'disproof')
        self.assertTrue(r.ok, r.to_json())
        self.assertIn('recheck', r.layers_passed)
