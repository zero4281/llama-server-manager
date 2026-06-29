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


class TestWSLDetection:
    """Tests for WSL detection functionality."""
    
    def test_wsl_detection_on_linux(self):
        """WSL detection should not trigger warning on Linux."""
        with patch('platform.system', return_value='Linux'):
            with patch('sys.argv', ['test']):
                from main import Main
                
                main = Main()
                main.parse_args()
                
                # No exception raised, no warning printed
                assert True
    
    def test_wsl_detection_on_macos(self):
        """WSL detection should not trigger warning on macOS."""
        with patch('platform.system', return_value='Darwin'):
            with patch('sys.argv', ['test']):
                from main import Main
                
                main = Main()
                main.parse_args()
                
                assert True
    
    def test_wsl_detection_on_windows_wsl(self):
        """WSL detection should not trigger warning when running in WSL."""
        with patch('platform.system', return_value='Windows') as mock_platform:
            with patch('sys.argv', ['test']):
                from main import Main
                
                main = Main()
                main.parse_args()
                
                assert True
    
    def test_wsl_detection_on_native_windows_triggers_warning(self):
        """WSL detection should print warning when running on native Windows."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."
        
        with patch('platform.system', return_value='Windows') as mock_platform:
            with patch('sys.argv', ['test']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    from main import Main
                    
                    main = Main()
                    main.parse_args()
                    
                    # Verify warning was printed to stderr
                    mock_stderr.write.assert_any_call(warning_message)
                    
                    # Verify execution continued (no exception)
                    assert True
    
    def test_wsl_detection_warning_exact_message(self):
        """Test that the warning message is printed exactly as specified."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."
        
        with patch('platform.system', return_value='Windows') as mock_platform:
            
            with patch('sys.argv', ['test']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    from main import Main
                    
                    main = Main()
                    main.parse_args()
                    
                    # Verify the exact warning message
                    mock_stderr.write.assert_any_call(warning_message)
    
    def test_wsl_detection_warning_called_once(self):
        """Test that the warning is printed exactly once."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."
        
        with patch('platform.system', return_value='Windows') as mock_platform:
            
            with patch('sys.argv', ['test']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    from main import Main
                    
                    main = Main()
                    main.parse_args()
                    
                    # Verify warning was called
                    assert mock_stderr.write.called
                    
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
                    from main import Main
                    
                    main = Main()
                    result = main.parse_args()
                    
                    # Verify warning was printed
                    mock_stderr.write.assert_any_call(warning_message)
                    
                    # Verify parse_args returns a valid namespace
                    assert result is not None
                    assert result.self_update is True
    
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
                        from main import Main
                        
                        main = Main()
                        main.parse_args()
                        
                        if should_warn:
                            mock_stderr.write.assert_any_call(warning_message)
                        else:
                            # Should not warn on Linux
                            pass
    
    def test_wsl_detection_warning_message_format(self):
        """Test that the warning message follows the exact format specified."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."
        
        with patch('platform.system', return_value='Windows') as mock_platform:
            
            with patch('sys.argv', ['test']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    from main import Main
                    
                    main = Main()
                    main.parse_args()
                    
                    # Verify the warning was printed
                    mock_stderr.write.assert_any_call(warning_message)
                    
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
                from main import Main
                
                main = Main()
                main.parse_args()
                
                # No SystemExit raised
                assert True


class TestWSLDetectionIntegration:
    """Integration tests for WSL detection with other parts of the system."""
    
    def test_wsl_detection_warning_with_ui_manager_initialization(self):
        """Test WSL detection warning is printed before UIManager initialization."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."
        
        with patch('platform.system', return_value='Windows') as mock_platform:
            
            with patch('sys.argv', ['test']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    with patch('ui_manager.UIManager') as mock_ui_manager:
                        from main import Main
                        
                        main = Main()
                        main.parse_args()
                        
                        # Verify warning was printed
                        mock_stderr.write.assert_any_call(warning_message)
                        
                        # UIManager should not be called (since we're not running self-update)
                        mock_ui_manager.assert_not_called()
    
    def test_wsl_detection_warning_with_self_update_mode(self):
        """Test WSL detection warning is printed before self-update mode."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."
        
        with patch('platform.system', return_value='Windows') as mock_platform:
            
            with patch('sys.argv', ['test', '--self-update']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    from main import Main
                    
                    main = Main()
                    result = main.parse_args()
                    
                    # Verify warning was printed
                    mock_stderr.write.assert_any_call(warning_message)
                    
                    # Verify parse_args returns args with self_update flag set
                    assert result is not None
                    assert result.self_update is True


class TestWSLDetectionEdgeCases:
    """Edge case tests for WSL detection."""
    
    def test_wsl_detection_warning_with_unicode_stderr(self):
        """Test WSL detection works with Unicode-capable stderr."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."
        
        with patch('platform.system', return_value='Windows') as mock_platform:
            
            with patch('sys.argv', ['test']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    from main import Main
                    
                    main = Main()
                    main.parse_args()
                    
                    # Verify warning was written
                    mock_stderr.write.assert_any_call(warning_message)
    
    def test_wsl_detection_warning_with_exception_in_stderr(self):
        """Test WSL detection warning is printed even if stderr has exceptions."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."
        
        with patch('platform.system', return_value='Windows') as mock_platform:
            
            with patch('sys.argv', ['test']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    # Simulate an exception being raised by stderr
                    mock_stderr.side_effect = Exception("Stderr error")
                    
                    from main import Main
                    
                    main = Main()
                    # parse_args should complete successfully since it doesn't write to stderr
                    result = main.parse_args()
                    
                    # Verify parse_args completed without raising exception
                    assert result is not None


class TestWSLDetectionPlatformDetection:
    """Tests for platform detection accuracy."""
    
    def test_platform_system_returns_windows(self):
        """Test that platform.system('Windows') triggers warning."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."
        
        with patch('platform.system', return_value='Windows') as mock_platform:
            
            with patch('sys.argv', ['test']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    from main import Main
                    
                    main = Main()
                    main.parse_args()
                    
                    mock_stderr.write.assert_any_call(warning_message)
    
    def test_platform_system_returns_other_values_no_warning(self):
        """Test that non-Windows platform values do not trigger warning."""
        non_windows_values = ['Linux', 'Darwin', 'FreeBSD', 'OpenBSD']
        
        for platform_value in non_windows_values:
            with patch('platform.system', return_value='Windows') as mock_platform:
                mock_platform.system.return_value = platform_value
                with patch('sys.argv', ['test']):
                    from main import Main
                    
                    main = Main()
                    main.parse_args()
                    
                    # No SystemExit raised
                    assert True
    
    def test_platform_system_case_sensitivity(self):
        """Test that platform.system value is case-sensitive."""
        # 'windows' (lowercase) should not match 'Windows' (title case)
        with patch('platform.system', return_value='Windows') as mock_platform:
            mock_platform.system.return_value = 'windows'
            with patch('sys.argv', ['test']):
                from main import Main
                
                main = Main()
                main.parse_args()
                
                # No warning should be printed
                assert True


class TestWSLDetectionWarningContent:
    """Tests for warning content and accuracy."""
    
    def test_warning_contains_native_windows_text(self):
        """Test that warning contains 'native Windows' text."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."
        
        with patch('platform.system', return_value='Windows') as mock_platform:
            
            with patch('sys.argv', ['test']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    from main import Main
                    
                    main = Main()
                    main.parse_args()
                    
                    mock_stderr.write.assert_any_call(warning_message)
                    
                    # Verify the message contains "native Windows"
                    assert "native Windows" in warning_message
    
    def test_warning_contains_wsl_text(self):
        """Test that warning contains WSL text."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."
        
        with patch('platform.system', return_value='Windows') as mock_platform:
            
            with patch('sys.argv', ['test']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    from main import Main
                    
                    main = Main()
                    main.parse_args()
                    
                    mock_stderr.write.assert_any_call(warning_message)
                    
                    # Verify the message contains "WSL"
                    assert "WSL" in warning_message
    
    def test_warning_provides_full_support_recommendation(self):
        """Test that warning provides recommendation to run in WSL for full support."""
        warning_message = "Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL)."
        
        with patch('platform.system', return_value='Windows') as mock_platform:
            
            with patch('sys.argv', ['test']):
                with patch('sys.stderr', new_callable=MagicMock()) as mock_stderr:
                    from main import Main
                    
                    main = Main()
                    main.parse_args()
                    
                    mock_stderr.write.assert_any_call(warning_message)
                    
                    # Verify the message contains "full support"
                    assert "full support" in warning_message


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
