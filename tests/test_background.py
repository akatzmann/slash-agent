import unittest
import os
import sys
import time
import shutil
import tempfile
import asyncio

# Setup path so tests can run
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from slash_agent.tools import (
    session_state,
    execute_command,
    list_background_tasks,
    get_task_logs,
    kill_background_task,
    teardown_tasks,
    wait_seconds
)

class TestBackgroundTaskExecution(unittest.TestCase):
    def setUp(self):
        # Backup active_tasks
        self.original_tasks = session_state.active_tasks.copy()
        session_state.active_tasks = {}
        session_state.task_counter = 0
        
        # Setup test temporary directory
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        # Clean up any remaining tasks
        teardown_tasks()
        session_state.active_tasks = self.original_tasks
        
        # Clean test dir
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
    def run_async(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)
        
    def test_background_spawn_returns_task_id(self):
        session_state.auto_confirm = True
        
        result = self.run_async(execute_command("echo 'hello world'", background=True, risk_level="safe"))
        self.assertTrue("Success: Command spawned in the background" in result)
        self.assertTrue("Task ID: task_1" in result)
        self.assertIn("task_1", session_state.active_tasks)
        
        time.sleep(0.5)
        
    def test_background_log_redirection(self):
        session_state.auto_confirm = True
        
        self.run_async(execute_command("echo 'async_test_log_output'", background=True, risk_level="safe"))
        
        task = session_state.active_tasks["task_1"]
        log_path = task["log_path"]
        
        time.sleep(0.5)
        
        self.assertTrue(os.path.exists(log_path))
        with open(log_path, "r") as f:
            content = f.read()
        self.assertTrue("async_test_log_output" in content)
        
    def test_list_background_tasks(self):
        session_state.auto_confirm = True
        
        self.run_async(execute_command("sleep 10", background=True, risk_level="safe"))
        list_output = self.run_async(list_background_tasks())
        
        self.assertTrue("Active Background Tasks:" in list_output)
        self.assertTrue("task_1" in list_output)
        self.assertTrue("running" in list_output)
        
    def test_get_task_logs(self):
        session_state.auto_confirm = True
        
        self.run_async(execute_command("echo 'line1'\necho 'line2'", background=True, risk_level="safe"))
        
        time.sleep(0.5)
        
        logs = self.run_async(get_task_logs("task_1", tail_lines=2))
        self.assertTrue("line1" in logs)
        self.assertTrue("line2" in logs)
        self.assertTrue("Logs for Task 'task_1'" in logs)
        
    def test_kill_background_task(self):
        session_state.auto_confirm = True
        
        self.run_async(execute_command("sleep 100", background=True, risk_level="safe"))
        task = session_state.active_tasks["task_1"]
        proc = task["proc"]
        
        self.assertIsNone(proc.poll())
        
        kill_result = self.run_async(kill_background_task("task_1"))
        self.assertTrue("Success: Forcefully terminated background task" in kill_result)
        self.assertNotIn("task_1", session_state.active_tasks)
        self.assertIsNotNone(proc.poll())
        
    def test_teardown_tasks_cleanup(self):
        session_state.auto_confirm = True
        
        self.run_async(execute_command("sleep 100", background=True, risk_level="safe"))
        self.run_async(execute_command("sleep 200", background=True, risk_level="safe"))
        
        p1 = session_state.active_tasks["task_1"]["proc"]
        p2 = session_state.active_tasks["task_2"]["proc"]
        
        self.assertIsNone(p1.poll())
        self.assertIsNone(p2.poll())
        
        teardown_tasks()
        
        self.assertIsNotNone(p1.poll())
        self.assertIsNotNone(p2.poll())
        self.assertNotIn("task_1", session_state.active_tasks)
        self.assertNotIn("task_2", session_state.active_tasks)

    def test_wait_seconds(self):
        t0 = time.time()
        res = self.run_async(wait_seconds(1))
        t1 = time.time()
        self.assertTrue("Success: Waited for" in res)
        self.assertGreaterEqual(t1 - t0, 0.9)

if __name__ == "__main__":
    unittest.main()
