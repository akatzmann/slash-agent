import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Import the functions to test
from slash_agent.tools import read_file_content, format_execution_result, session_state

class TestSafetyAndErgonomics(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
        
    def test_read_file_content_no_truncation(self):
        file_path = os.path.join(self.test_dir, "small.txt")
        lines = [f"Line {i}\n" for i in range(1, 51)]
        with open(file_path, "w") as f:
            f.writelines(lines)
            
        content = read_file_content(file_path)
        self.assertEqual(content, "".join(lines))
        
    def test_read_file_content_default_truncation(self):
        file_path = os.path.join(self.test_dir, "large.txt")
        lines = [f"Line {i}\n" for i in range(1, 1001)]
        with open(file_path, "w") as f:
            f.writelines(lines)
            
        with patch.dict(os.environ, {"AGENT_READ_LINE_LIMIT": "800"}):
            content = read_file_content(file_path)
            self.assertTrue("File Truncated: Read lines 1-800" in content)
            self.assertTrue(content.startswith("Line 1\n"))
            self.assertTrue(content.split("\n")[799] == "Line 800")
            
    def test_read_file_content_custom_truncation(self):
        file_path = os.path.join(self.test_dir, "medium.txt")
        lines = [f"Line {i}\n" for i in range(1, 101)]
        with open(file_path, "w") as f:
            f.writelines(lines)
            
        with patch.dict(os.environ, {"AGENT_READ_LINE_LIMIT": "20"}):
            content = read_file_content(file_path)
            self.assertTrue("File Truncated: Read lines 1-20" in content)
            self.assertTrue(content.startswith("Line 1\n"))
            self.assertTrue(content.split("\n")[19] == "Line 20")
            
    def test_read_file_content_with_bounds(self):
        file_path = os.path.join(self.test_dir, "medium.txt")
        lines = [f"Line {i}\n" for i in range(1, 101)]
        with open(file_path, "w") as f:
            f.writelines(lines)
            
        content = read_file_content(file_path, start_line=10, end_line=20)
        self.assertEqual(content, "".join(lines[9:20]))
        
    def test_read_file_content_range_overflow_limit(self):
        file_path = os.path.join(self.test_dir, "huge.txt")
        lines = [f"Line {i}\n" for i in range(1, 2001)]
        with open(file_path, "w") as f:
            f.writelines(lines)
            
        content = read_file_content(file_path, start_line=1, end_line=1500)
        self.assertTrue("Requested range exceeded the maximum limit of 1000 lines" in content)
        self.assertTrue(content.split("\n")[999] == "Line 1000")
        
    def test_format_execution_result_truncation(self):
        large_output = "a\n" * 250
        result = format_execution_result(0, large_output, "/tmp/dummy.log")
        self.assertTrue("[Output Truncated: Size" in result)
        self.assertTrue("Full logs written to" in result)
        self.assertTrue("--- LOG PREVIEW" in result)

    def test_log_cleanup_on_exit(self):
        dummy_log = os.path.join(self.test_dir, "dummy_cmd.log")
        with open(dummy_log, "w") as f:
            f.write("Log content")
        session_state.session_logs = [dummy_log]
        self.assertTrue(os.path.exists(dummy_log))
        for log_path in session_state.session_logs:
            if os.path.exists(log_path):
                os.remove(log_path)
        self.assertFalse(os.path.exists(dummy_log))

if __name__ == "__main__":
    unittest.main()
