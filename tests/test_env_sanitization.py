import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from slash_agent.tools import parse_pty_result, session_state
from slash_agent.main import get_env_diff, STARTING_ENV

class TestEnvSanitization(unittest.TestCase):
    def setUp(self):
        self.original_env = session_state.env_vars.copy()
        session_state.env_vars = {}

    def tearDown(self):
        session_state.env_vars = self.original_env

    def test_parse_pty_result_filters_internal_keys(self):
        # Simulate env -0 buffer with internal Windows drive variables and normal variables
        state_buffer = b"token\nexit_code=0\npwd=/tmp\n=C:=C:\\Users\\test\x00NORMAL_VAR=hello\x00=ExitCode=00000000\x00\x00=::=::\\\x00"
        exit_code, output = parse_pty_result(b"test output", state_buffer)
        
        self.assertEqual(exit_code, 0)
        self.assertIn("NORMAL_VAR", session_state.env_vars)
        self.assertEqual(session_state.env_vars["NORMAL_VAR"], "hello")
        self.assertNotIn("", session_state.env_vars)
        self.assertNotIn("=C:", session_state.env_vars)
        self.assertNotIn("=ExitCode", session_state.env_vars)

    def test_get_env_diff_sanitizes_powershell_output(self):
        session_state.env_vars = {
            "": "invalid_empty_key",
            "=C:": "C:\\Users\\test",
            "TEST_PWSH_VAR": "valid_value"
        }
        
        diff = get_env_diff("powershell")
        self.assertIn("$env:TEST_PWSH_VAR = 'valid_value'", diff)
        self.assertNotIn("$env: =", diff)
        self.assertNotIn("=C:", diff)

if __name__ == "__main__":
    unittest.main()
