#!/usr/bin/env python3
"""
Test suite for graceful shutdown functionality.

Run with: pytest test_graceful_shutdown.py
"""

import sys
import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add current directory to path
sys.path.insert(0, str(Path.cwd()))

import pytest
from runner import stop_server
from runner import PID_FILE

class TestGracefulShutdown:
    """Tests for graceful shutdown of llama-server."""

    def test_stop_server_no_pid_file(self):
        """Test that stop_server returns 1 if no PID file exists."""
        if PID_FILE.exists():
            PID_FILE.unlink()
        
        result = stop_server()
        assert result == 1

    def test_stop_server_clean_shutdown(self):
        """Test that stop_server performs a clean shutdown (SIGTERM)."""
        # Mock os.kill: first call (SIGTERM) succeeds, subsequent checks (os.kill(pid, 0)) raise OSError
        with patch('os.kill') as mock_os_kill:
            call_count = [0]
            
            def mock_kill(pid, sig):
                call_count[0] += 1
                if call_count[0] == 1:  # First call is SIGTERM
                    return
                else:  # Subsequent calls are process checks - raise OSError to simulate process exit
                    raise OSError('Process not found')
            
            mock_os_kill.side_effect = mock_kill
            
            # Write a PID file
            with open(PID_FILE, "w") as f:
                f.write("12345")
            
            # Mock time.sleep to speed up the 60s wait
            with patch('time.sleep', side_effect=lambda x: None):
                result = stop_server()
            
            assert result == 0

    def test_stop_server_force_kill(self):
        """Test that stop_server performs a force kill if process persists."""
        # Create a script that ignores SIGTERM
        script_path = Path("/tmp/dummy_ignore_term.py")
        script_path.write_text("""
import signal
import sys
import time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
while True:
    time.sleep(1)
""")
        
        proc = subprocess.Popen(['python3', str(script_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        try:
            with open(PID_FILE, "w") as f:
                f.write(str(proc.pid))
            
            # Mock time.sleep to speed up the 60s wait
            with patch('time.sleep', side_effect=lambda x: None):
                result = stop_server()
            
            assert result == 1
            assert proc.poll() is not None
        finally:
            if PID_FILE.exists():
                PID_FILE.unlink()
            if script_path.exists():
                script_path.unlink()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])

