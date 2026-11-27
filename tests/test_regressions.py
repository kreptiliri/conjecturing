"""Trust-boundary regressions; run with python3 -m unittest discover -s tests."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness import agents, gate, pipeline, repro


class Regressions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.w = Path(self.tmp.name)

    def verifier(self, output):
        p = self.w / 'verify.py'
        p.write_text('print(' + repr(output) + ')\n')
        return p

    def test_result_protocol(self):
        good = 'RESULT {"witness": 40, "conjecture_holds_at_witness": false}'
        for value in ['RESULT {}', 'RESULT null', 'RESULT []',
                      good + '\ntrailing text', good + '\n' + good,
                      'RESULT {"witness": NaN, "conjecture_holds_at_witness": false}',
                      'RESULT {"witness": 40, "witness": 41, "conjecture_holds_at_witness": false}',
                      'RESULT {"witness": 40, "conjecture_holds_at_witness": 0}']:
            with self.subTest(value=value), self.assertRaises((RuntimeError, ValueError)):
                repro.run_verifier(self.verifier(value), [])
        self.assertIs(repro.run_verifier(self.verifier(good), [])['conjecture_holds_at_witness'], False)

    def test_shared_file_cannot_replace_script(self):
        script = self.verifier('RESULT {}')
        with self.assertRaises(RuntimeError):
            repro.run_verifier(script, [script])

    def test_false_agreement(self):
        candidate = self.w / 'candidate.json'
        candidate.write_text('{"witness": 40}')
        for result in [dict(witness=40, conjecture_holds_at_witness=True),
                       dict(witness=41, conjecture_holds_at_witness=False)]:
            with self.subTest(result=result), patch.object(pipeline, 'problem_dir', return_value=self.w), \
                 patch.object(agents, 'make_workspace', return_value=self.w), \
                 patch.object(pipeline, '_run_agent'), patch.object(pipeline, 'mark'), \
                 patch.object(pipeline.shutil, 'copy'), \
                 patch.object(repro, 'compare', return_value=(True, result, result)):
                (self.w / 'verify_independent.py').touch()
                self.assertFalse(pipeline.reproduce('toy', 'fake', self.w))

    def test_verdict_protocol(self):
        p = self.w / 'report.md'
        for report in ['VERDICT: reject\nVERDICT: accept', '```\nVERDICT: accept\n```',
                       '```VERDICT: accept', 'VERDICT: accept # comment', 'VERDICT: anything',
                       'VERDICT: reject # comment\nVERDICT: accept']:
            p.write_text(report)
            self.assertEqual(pipeline.verdict(p), 'missing', report)
        p.write_text('# Report\n\nVERDICT: accept\n')
        self.assertEqual(pipeline.verdict(p), 'accept')

    def test_workspace_has_no_stale_outputs(self):
        dest = self.w / 'workspace'
        dest.mkdir()
        (dest / 'ELIGIBILITY.md').write_text('VERDICT: open')
        agents.make_workspace(dest, {})
        self.assertFalse((dest / 'ELIGIBILITY.md').exists())

    def test_readonly_replacement_detected(self):
        p = self.w / 'Challenge.lean'
        p.write_text('locked')
        p.chmod(0o444)
        def replace(*args, **kwargs):
            p.unlink()
            p.write_text('changed')
            return subprocess.CompletedProcess([], 0)
        cfg = {'agents': {'fake': {'cmd': ['fake']}}}
        with patch.object(agents, 'load_config', return_value=cfg), \
             patch.object(agents, 'render_prompt', return_value='prompt'), \
             patch.object(agents.subprocess, 'run', side_effect=replace):
            self.assertEqual(agents.run_agent('fake', 'hunter', self.w), 125)
        self.assertEqual(p.read_text(), 'locked')

    def test_readonly_chmod_detected(self):
        p = self.w / 'Challenge.lean'
        p.write_text('locked')
        p.chmod(0o444)
        def chmod(*args, **kwargs):
            p.chmod(0o644)
            return subprocess.CompletedProcess([], 0)
        cfg = {'agents': {'fake': {'cmd': ['fake']}}}
        with patch.object(agents, 'load_config', return_value=cfg), \
             patch.object(agents, 'render_prompt', return_value='prompt'), \
             patch.object(agents.subprocess, 'run', side_effect=chmod):
            self.assertEqual(agents.run_agent('fake', 'hunter', self.w), 125)
        self.assertEqual(p.stat().st_mode & 0o222, 0)

    def test_failed_agents_are_not_trusted(self):
        for code in [1, 124, 125, -9]:
            with patch.object(agents, 'run_agent', return_value=code), self.assertRaises(RuntimeError):
                pipeline._run_agent('fake', 'hunter', self.w)

    def test_process_failures(self):
        for outcome in [subprocess.TimeoutExpired(['lean'], 1), OSError('missing'),
                        subprocess.CompletedProcess(['lean'], -11, '', 'crashed')]:
            with self.subTest(outcome=outcome):
                opts = {'side_effect': outcome} if isinstance(outcome, Exception) else {'return_value': outcome}
                with patch.object(gate.subprocess, 'run', **opts), self.assertRaises(gate.GateFail):
                    gate._run(['lean'], self.w, {}, 1, 'compile')

    def test_audit_requires_exit_success_and_matching_token(self):
        problem = Path(__file__).resolve().parent.parent / 'problems/euler-41'
        solution = Path(__file__).resolve().parent.parent / 'examples/euler-41/Solution.lean'
        (self.w / 'leanchecker').touch()
        for mode in ['valid', 'missing', 'wrong-token', 'duplicate', 'failed-exit', 'failed-status']:
            def run(cmd, cwd, env, timeout, layer):
                if layer != 'axioms':
                    return ''
                self.assertEqual(cmd[2:4], ['--run', 'AuditMain.lean'])
                token = cmd[-1]
                self.assertEqual(len(token), 64)
                data = {'token': token, 'status': 'ok', 'axioms': []}
                if mode == 'wrong-token':
                    data['token'] = 'stale-token'
                if mode == 'failed-status':
                    data['status'] = 'axioms'
                log = 'GATE_AUDIT ' + json.dumps(data) + '\n'
                if mode == 'missing':
                    return 'GATE_AXIOMS []'
                if mode == 'duplicate':
                    return log + log
                if mode == 'failed-exit':
                    raise gate.GateFail('axioms', 'exit 1', log)
                return log
            with self.subTest(mode=mode), \
                 patch.object(gate, '_toolchain', return_value=(self.w, '')), \
                 patch.object(gate, '_run', side_effect=run):
                result = gate.run_gate(problem, solution, 'disproof')
            self.assertEqual(result.ok, mode == 'valid', result.to_json())
            if mode != 'valid':
                self.assertEqual(result.failed_layer, 'axioms', result.to_json())

    def test_lexer_preserves_boundaries(self):
        self.assertEqual(gate.strip_comments('a/- outer /- inner -/ -/b'), 'a  b')
        self.assertEqual(gate.strip_comments('«/-» axiom «-/»'), '«/-» axiom «-/»')
        self.assertEqual(gate.strip_comments('"-- sorry /-"'), '"-- sorry /-"')
        with self.assertRaises(gate.GateFail):
            gate.strip_comments('/- never closed')


if __name__ == '__main__':
    unittest.main()
