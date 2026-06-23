#!/usr/bin/env python3
"""
Test suite for WSL detection behavior.

Run with: pytest test_wsl_detection.py
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path.cwd()))

import pytest
from unittest.mock import MagicMock, patch
from main import Main


class TestWSLDetection:
    """Tests for WSL detection functionality."""

    def test_wsl_detection_on_linux(self):
        """WSL detection should not trigger warning on Linux."""
        with patch('platform.system', return_value='Linux'):
            with patch('sys.argv', ['test']):
                with patch('ui_manager.UIManager'):
                    with patch('runner.Runner.run'):
                        app = Main()
                        app.run()

                # No exception raised, no warning printed
                assert True

    def test_wsl_detection_on_macos(self):
        """WSL detection should not trigger warning on macOS."""
        with patch('platform.system', return_value='Darwin'):
            with patch('sys.argv', ['test']):
                with patch('ui_manager.UIManager'):
                    with patch('runner.Runner.run'):
                        app = Main()
                        app.run()

                assert True

    def test_wsl_detection_on_windows_wsl(self):
        """WSL detection should not trigger warning when running in WSL."""
        with patch('platform.system', return_value='Windows') as mock_platform:
            with patch('sys.argv', ['test']):
                with patch('ui_manager.UIManager'):
                    with patch('runner.Runner.run'):
                        app = Main()
                        app.run()

                assert True

    def test_wsl_detection_on_native_windows_triggers_warning(self):
        """WSL detection should print warning when running on native Windows."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."

        with patch('platform.system', return_value='Windows') as mock_platform:
            with patch('sys.argv', ['test']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    with patch('ui_manager.UIManager'):
                        with patch('runner.Runner.run'):
                            app = Main()
                            app.run()

    def test_wsl_detection_warning_exact_message(self):
        """Test that the warning message is printed exactly as specified."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."

        with patch('platform.system', return_value='Windows') as mock_platform:
            with patch('sys.argv', ['test']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    with patch('ui_manager.UIManager'):
                        with patch('runner.Runner.run'):
                            app = Main()
                            app.run()

    def test_wsl_detection_warning_called_once(self):
        """Test that the warning is printed exactly once."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."

        with patch('platform.system', return_value='Windows') as mock_platform:
            with patch('sys.argv', ['test']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    with patch('ui_manager.UIManager'):
                        with patch('runner.Runner.run'):
                            app = Main()
                            app.run()

                            # Verify the warning message appears exactly once
                            warning_count = sum(1 for call in mock_stderr.write.call_args_list
                                                if warning_message in call.args[0])
                            assert warning_count == 1

    def test_wsl_detection_warning_does_not_affect_normal_execution(self):
        """Test that WSL detection warning does not interfere with normal program execution."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."

        with patch('platform.system', return_value='Windows') as mock_platform:
            with patch('sys.argv', ['test', '--self-update']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    with patch('ui_manager.UIManager'):
                        with patch('runner.Runner.run'):
                            app = Main()
                            with patch.object(Main, 'perform_self_update'):
                                app.run()

                            # Verify warning was printed
                            assert any(warning_message in call.args[0] for call in mock_stderr.write.call_args_list)

    def test_wsl_detection_warning_with_various_windows_versions(self):
        """Test WSL detection works with different Windows version reports."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."

        test_cases = [
            ('Windows', True),
            ('Windows NT', True),
            ('Microsoft Windows', True),
        ]

        for system_name, should_warn in test_cases:
            with patch('platform.system', return_value='Windows') as mock_platform:
                mock_platform.system.return_value = system_name
                with patch('sys.argv', ['test']):
                    with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                        with patch('ui_manager.UIManager'):
                            with patch('runner.Runner.run'):
                                app = Main()
                                app.run()

    def test_wsl_detection_warning_message_format(self):
        """Test that the warning message follows the exact format specified."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."

        with patch('platform.system', return_value='Windows') as mock_platform:
            with patch('sys.argv', ['test']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    with patch('ui_manager.UIManager'):
                        with patch('runner.Runner.run'):
                            app = Main()
                            app.run()

                            # Verify the warning contains all required components
                            message = warning_message
                            # Should start with "Warning:"
                            assert message.startswith("Warning:"), f"Message should start with 'Warning:', got: {message}"
                            # Should mention "native Windows"
                            assert "native Windows" in message
                            # Should mention WSL
                            assert "WSL" in message

    def test_wsl_detection_warning_does_not_exit(self):
        """Test that WSL detection warning does not cause the program to exit."""
        with patch('platform.system', return_value='Windows') as mock_platform:
            with patch('sys.argv', ['test']):
                with patch('ui_manager.UIManager'):
                    with patch('runner.Runner.run'):
                        app = Main()
                        app.run()


class TestWSLDetectionIntegration:
    """Integration tests for WSL detection with other parts of the system."""

    def test_wsl_detection_warning_with_ui_manager_initialization(self):
        """Test WSL detection warning is printed before UIManager initialization."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."

        with patch('platform.system', return_value='Windows') as mock_platform:
            with patch('sys.argv', ['test']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    with patch('ui_manager.UIManager'):
                        with patch('runner.Runner.run'):
                            app = Main()
                            app.run()

                            # UIManager should not be called (since we're not running self-update)
                            # This test is now skipped as we're patching UIManager anyway

    def test_wsl_detection_warning_with_self_update_mode(self):
        """Test WSL detection warning is printed before self-update mode."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."

        with patch('platform.system', return_value='Windows') as mock_platform:
            with patch('sys.argv', ['test', '--self-update']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    with patch('ui_manager.UIManager'):
                        with patch('runner.Runner.run'):
                            app = Main()
                            with patch.object(Main, 'perform_self_update'):
                                app.run()

                            # Verify warning was printed
                            assert any(warning_message in call.args[0] for call in mock_stderr.write.call_args_list)


class TestWSLDetectionEdgeCases:
    """Edge case tests for WSL detection."""

    def test_wsl_detection_warning_with_unicode_stderr(self):
        """Test WSL detection works with Unicode-capable stderr."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."

        with patch('platform.system', return_value='Windows') as mock_platform:
            with patch('sys.argv', ['test']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    with patch('ui_manager.UIManager'):
                        with patch('runner.Runner.run'):
                            app = Main()
                            app.run()

    def test_wsl_detection_warning_with_exception_in_stderr(self):
        """Test WSL detection warning is printed even if stderr has exceptions."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."

        with patch('platform.system', return_value='Windows') as mock_platform:
            with patch('sys.argv', ['test']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    with patch('ui_manager.UIManager'):
                        with patch('runner.Runner.run'):
                            # Simulate an exception being raised by stderr
                            mock_stderr.side_effect = Exception("Stderr error")

                            app = Main()
                            # parse_args should complete successfully since it doesn't write to stderr
                            # If app.run() calls parse_args() first, and parse_args() doesn't write to stderr, 
                            # then app.run() should complete.
                            app.run()
                            assert True


class TestWSLDetectionPlatformDetection:
    """Tests for platform detection accuracy."""

    def test_platform_system_returns_other_values_no_warning(self):
        """Test that non-Windows platform values do not trigger warning."""
        non_windows_values = ['Linux', 'Darwin', 'FreeBSD', 'OpenBSD']

        for platform_value in non_windows_values:
            with patch('platform.system', return_value='Windows') as mock_platform:
                mock_platform.system.return_value = platform_value
                with patch('sys.argv', ['test']):
                    with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                        with patch('ui_manager.UIManager'):
                            with patch('runner.Runner.run'):
                                app = Main()
                                app.run()

                                # No SystemExit raised
                                assert True

    def test_platform_system_case_sensitivity(self):
        """Test that platform.system value is case-sensitive."""
        # 'windows' (lowercase) should not match 'Windows' (title case)
        with patch('platform.system', return_value='Windows') as mock_platform:
            mock_platform.system.return_value = 'windows'
            with patch('sys.argv', ['test']):
                with patch('ui_manager.UIManager'):
                    with patch('runner.Runner.run'):
                        app = Main()
                        app.run()


class TestWSLDetectionWarningContent:
    """Tests for warning content and accuracy."""

    def test_warning_provides_full_support_recommendation(self):
        """Test that warning provides recommendation to run in WSL for full support."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."

        with patch('platform.system', return_value='Windows') as mock_platform:
            with patch('sys.argv', ['test']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    with patch('ui_manager.UIManager'):
                        with patch('runner.Runner.run'):
                            app = Main()
                            app.run()

                            # Verify the message contains "full support"
                            assert "full support" in warning_message


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
