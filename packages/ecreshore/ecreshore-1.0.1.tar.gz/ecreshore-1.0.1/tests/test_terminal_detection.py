"""Tests for terminal detection utilities."""

import os
import sys
from unittest.mock import patch, Mock
import pytest

from src.ecreshore.terminal_detection import (
    supports_ansi_colors,
    should_use_rich_ui,
    get_terminal_info,
    _check_explicit_overrides,
    _check_tty_status,
    _check_ci_environment,
    _check_term_variable,
    _check_platform_specific,
)


class TestCheckExplicitOverrides:
    """Tests for _check_explicit_overrides helper function."""

    @patch.dict(os.environ, {'FORCE_COLOR': '1'}, clear=False)
    def test_force_color_returns_true(self):
        """Test that FORCE_COLOR returns True."""
        result = _check_explicit_overrides()
        assert result is True

    @patch.dict(os.environ, {'FORCE_COLOR': 'true'}, clear=False)
    def test_force_color_string_returns_true(self):
        """Test that FORCE_COLOR with any value returns True."""
        result = _check_explicit_overrides()
        assert result is True

    @patch.dict(os.environ, {'NO_COLOR': '1'}, clear=False)
    def test_no_color_returns_false(self):
        """Test that NO_COLOR returns False."""
        result = _check_explicit_overrides()
        assert result is False

    @patch.dict(os.environ, {'FORCE_COLOR': '1', 'NO_COLOR': '1'}, clear=False)
    def test_force_color_takes_precedence(self):
        """Test that FORCE_COLOR is checked before NO_COLOR."""
        result = _check_explicit_overrides()
        assert result is True

    @patch.dict(os.environ, {}, clear=True)
    def test_no_overrides_returns_none(self):
        """Test that no overrides returns None to continue decision chain."""
        result = _check_explicit_overrides()
        assert result is None


class TestCheckTtyStatus:
    """Tests for _check_tty_status helper function."""

    @patch('sys.stdout')
    def test_not_tty_returns_false(self, mock_stdout):
        """Test that non-TTY returns False."""
        mock_stdout.isatty.return_value = False
        result = _check_tty_status()
        assert result is False

    @patch('sys.stdout')
    def test_is_tty_returns_none(self, mock_stdout):
        """Test that TTY returns None to continue decision chain."""
        mock_stdout.isatty.return_value = True
        result = _check_tty_status()
        assert result is None


class TestCheckCiEnvironment:
    """Tests for _check_ci_environment helper function."""

    @patch.dict(os.environ, {'CI': '1'}, clear=False)
    def test_ci_returns_false(self):
        """Test that CI environment returns False."""
        result = _check_ci_environment()
        assert result is False

    @patch.dict(os.environ, {'GITHUB_ACTIONS': 'true'}, clear=False)
    def test_github_actions_returns_false(self):
        """Test that GitHub Actions returns False."""
        result = _check_ci_environment()
        assert result is False

    @patch.dict(os.environ, {'GITLAB_CI': '1'}, clear=False)
    def test_gitlab_ci_returns_false(self):
        """Test that GitLab CI returns False."""
        result = _check_ci_environment()
        assert result is False

    @patch.dict(os.environ, {'JENKINS_URL': 'http://jenkins'}, clear=False)
    def test_jenkins_returns_false(self):
        """Test that Jenkins returns False."""
        result = _check_ci_environment()
        assert result is False

    @patch.dict(os.environ, {'BUILDKITE': '1'}, clear=False)
    def test_buildkite_returns_false(self):
        """Test that Buildkite returns False."""
        result = _check_ci_environment()
        assert result is False

    @patch.dict(os.environ, {'CIRCLECI': 'true'}, clear=False)
    def test_circleci_returns_false(self):
        """Test that CircleCI returns False."""
        result = _check_ci_environment()
        assert result is False

    @patch.dict(os.environ, {'TRAVIS': 'true'}, clear=False)
    def test_travis_returns_false(self):
        """Test that Travis CI returns False."""
        result = _check_ci_environment()
        assert result is False

    @patch.dict(os.environ, {}, clear=True)
    def test_no_ci_returns_none(self):
        """Test that non-CI environment returns None to continue decision chain."""
        result = _check_ci_environment()
        assert result is None


class TestCheckTermVariable:
    """Tests for _check_term_variable helper function."""

    @patch.dict(os.environ, {'TERM': 'dumb'}, clear=False)
    def test_dumb_terminal_returns_false(self):
        """Test that dumb terminal returns False."""
        result = _check_term_variable()
        assert result is False

    @patch.dict(os.environ, {'TERM': 'unknown'}, clear=False)
    def test_unknown_terminal_returns_false(self):
        """Test that unknown terminal returns False."""
        result = _check_term_variable()
        assert result is False

    @patch.dict(os.environ, {'TERM': ''}, clear=False)
    def test_empty_term_returns_false(self):
        """Test that empty TERM returns False."""
        result = _check_term_variable()
        assert result is False

    @patch.dict(os.environ, {'TERM': 'xterm-256color'}, clear=False)
    def test_xterm_returns_true(self):
        """Test that xterm terminal returns True."""
        result = _check_term_variable()
        assert result is True

    @patch.dict(os.environ, {'TERM': 'screen'}, clear=False)
    def test_screen_returns_true(self):
        """Test that screen terminal returns True."""
        result = _check_term_variable()
        assert result is True

    @patch.dict(os.environ, {'TERM': 'tmux-256color'}, clear=False)
    def test_tmux_returns_true(self):
        """Test that tmux terminal returns True."""
        result = _check_term_variable()
        assert result is True

    @patch.dict(os.environ, {'TERM': 'linux'}, clear=False)
    def test_linux_console_returns_true(self):
        """Test that linux console returns True."""
        result = _check_term_variable()
        assert result is True

    @patch.dict(os.environ, {'TERM': 'vt100'}, clear=False)
    def test_vt100_returns_true(self):
        """Test that vt100 terminal returns True."""
        result = _check_term_variable()
        assert result is True

    @patch.dict(os.environ, {'TERM': 'rxvt-unicode'}, clear=False)
    def test_rxvt_returns_true(self):
        """Test that rxvt terminal returns True."""
        result = _check_term_variable()
        assert result is True

    @patch.dict(os.environ, {'TERM': 'ansi'}, clear=False)
    def test_ansi_returns_true(self):
        """Test that ansi terminal returns True."""
        result = _check_term_variable()
        assert result is True

    @patch.dict(os.environ, {'TERM': 'konsole'}, clear=False)
    def test_konsole_returns_true(self):
        """Test that konsole terminal returns True."""
        result = _check_term_variable()
        assert result is True

    @patch.dict(os.environ, {'TERM': 'gnome-terminal'}, clear=False)
    def test_gnome_returns_true(self):
        """Test that gnome terminal returns True."""
        result = _check_term_variable()
        assert result is True

    @patch.dict(os.environ, {'TERM': 'iterm2'}, clear=False)
    def test_iterm_returns_true(self):
        """Test that iTerm2 returns True."""
        result = _check_term_variable()
        assert result is True

    @patch.dict(os.environ, {'TERM': 'other-terminal'}, clear=False)
    def test_unknown_modern_terminal_returns_none(self):
        """Test that unrecognized terminal returns None to continue decision chain."""
        result = _check_term_variable()
        assert result is None

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_term_returns_false(self):
        """Test that missing TERM variable returns False."""
        result = _check_term_variable()
        assert result is False


class TestCheckPlatformSpecific:
    """Tests for _check_platform_specific helper function."""

    @patch.dict(os.environ, {'COLORTERM': 'truecolor'}, clear=False)
    def test_colorterm_truecolor_returns_true(self):
        """Test that COLORTERM=truecolor returns True."""
        result = _check_platform_specific()
        assert result is True

    @patch.dict(os.environ, {'COLORTERM': '24bit'}, clear=False)
    def test_colorterm_24bit_returns_true(self):
        """Test that COLORTERM=24bit returns True."""
        result = _check_platform_specific()
        assert result is True

    @patch.dict(os.environ, {'COLORTERM': '256color'}, clear=False)
    def test_colorterm_256color_returns_true(self):
        """Test that COLORTERM=256color returns True."""
        result = _check_platform_specific()
        assert result is True

    @patch('os.name', 'nt')
    @patch.dict(os.environ, {'WT_SESSION': '123'}, clear=False)
    def test_windows_terminal_returns_true(self):
        """Test that Windows Terminal returns True."""
        result = _check_platform_specific()
        assert result is True

    @patch('os.name', 'nt')
    @patch.dict(os.environ, {'ConEmuANSI': 'ON'}, clear=False)
    def test_conemu_ansi_returns_true(self):
        """Test that ConEmu with ANSI returns True."""
        result = _check_platform_specific()
        assert result is True

    @patch('os.name', 'nt')
    @patch.dict(os.environ, {}, clear=True)
    def test_windows_10_modern_returns_true(self):
        """Test that modern Windows 10 returns True."""
        with patch('platform.system', return_value='Windows'):
            with patch('platform.version', return_value='10.0.19041'):
                result = _check_platform_specific()
        assert result is True

    @patch('os.name', 'nt')
    @patch.dict(os.environ, {}, clear=True)
    def test_windows_7_returns_false(self):
        """Test that Windows 7 returns False."""
        with patch('platform.system', return_value='Windows'):
            with patch('platform.version', return_value='6.1.7601'):
                result = _check_platform_specific()
        assert result is False

    @patch('os.name', 'nt')
    @patch.dict(os.environ, {}, clear=True)
    def test_windows_platform_error_returns_false(self):
        """Test that Windows with platform error returns False."""
        with patch('platform.system', side_effect=ImportError):
            result = _check_platform_specific()
        assert result is False

    @patch('os.name', 'nt')
    @patch.dict(os.environ, {}, clear=True)
    def test_windows_version_parse_error_returns_false(self):
        """Test that Windows with version parse error returns False."""
        with patch('platform.system', return_value='Windows'):
            with patch('platform.version', return_value='invalid'):
                result = _check_platform_specific()
        assert result is False

    @patch('os.name', 'posix')
    @patch.dict(os.environ, {}, clear=True)
    def test_unix_returns_none(self):
        """Test that Unix systems return None for default behavior."""
        result = _check_platform_specific()
        assert result is None


class TestSupportsAnsiColors:
    """Tests for ANSI color support detection."""

    @patch('sys.stdout')
    def test_not_tty_returns_false(self, mock_stdout):
        """Test that non-TTY output returns False."""
        mock_stdout.isatty.return_value = False

        result = supports_ansi_colors()

        assert result is False

    @patch.dict(os.environ, {'CI': '1'}, clear=False)
    @patch('sys.stdout')
    def test_ci_environment_returns_false(self, mock_stdout):
        """Test that CI environments return False."""
        mock_stdout.isatty.return_value = True

        result = supports_ansi_colors()

        assert result is False

    @patch.dict(os.environ, {'GITHUB_ACTIONS': 'true'}, clear=False)
    @patch('sys.stdout')
    def test_github_actions_returns_false(self, mock_stdout):
        """Test that GitHub Actions environment returns False."""
        mock_stdout.isatty.return_value = True

        result = supports_ansi_colors()

        assert result is False

    @patch.dict(os.environ, {'TERM': 'dumb'}, clear=False)
    @patch('sys.stdout')
    def test_dumb_terminal_returns_false(self, mock_stdout):
        """Test that dumb terminal returns False."""
        mock_stdout.isatty.return_value = True

        result = supports_ansi_colors()

        assert result is False

    @patch.dict(os.environ, {'TERM': 'xterm-256color'}, clear=False)
    @patch('sys.stdout')
    def test_xterm_terminal_returns_true(self, mock_stdout):
        """Test that xterm terminal returns True."""
        mock_stdout.isatty.return_value = True

        result = supports_ansi_colors()

        assert result is True

    @patch.dict(os.environ, {'TERM': 'screen'}, clear=False)
    @patch('sys.stdout')
    def test_screen_terminal_returns_true(self, mock_stdout):
        """Test that screen terminal returns True."""
        mock_stdout.isatty.return_value = True

        result = supports_ansi_colors()

        assert result is True

    @patch('os.name', 'nt')
    @patch.dict(os.environ, {'WT_SESSION': '123'}, clear=False)
    @patch('sys.stdout')
    def test_windows_terminal_returns_true(self, mock_stdout):
        """Test that Windows Terminal returns True."""
        mock_stdout.isatty.return_value = True

        result = supports_ansi_colors()

        assert result is True

    @patch('os.name', 'nt')
    @patch.dict(os.environ, {'ConEmuANSI': 'ON'}, clear=False)
    @patch('sys.stdout')
    def test_conemu_ansi_returns_true(self, mock_stdout):
        """Test that ConEmu with ANSI returns True."""
        mock_stdout.isatty.return_value = True

        result = supports_ansi_colors()

        assert result is True

    @patch('os.name', 'nt')
    @patch('sys.platform', 'win32')
    @patch('sys.stdout')
    def test_windows_10_modern_returns_true(self, mock_stdout):
        """Test that modern Windows 10 returns True."""
        mock_stdout.isatty.return_value = True

        with patch('platform.system', return_value='Windows'):
            with patch('platform.version', return_value='10.0.19041'):
                result = supports_ansi_colors()

        assert result is True

    @patch.dict(os.environ, {
        'TERM': '',  # Clear term
        'COLORTERM': '',  # Clear colorterm
        'FORCE_COLOR': '',  # Clear force color
        'NO_COLOR': '',  # Clear no color
        'CI': '',  # Clear CI
        'WT_SESSION': '',  # Clear Windows Terminal
        'ConEmuANSI': ''  # Clear ConEmu
    }, clear=True)
    @patch('os.name', 'nt')
    @patch('sys.platform', 'win32')
    @patch('sys.stdout')
    def test_windows_7_returns_false(self, mock_stdout):
        """Test that Windows 7 returns False."""
        mock_stdout.isatty.return_value = True

        with patch('platform.system', return_value='Windows'):
            with patch('platform.version', return_value='6.1.7601'):
                result = supports_ansi_colors()

        assert result is False

    @patch.dict(os.environ, {'COLORTERM': 'truecolor'}, clear=False)
    @patch('sys.stdout')
    def test_truecolor_support_returns_true(self, mock_stdout):
        """Test that truecolor support returns True."""
        mock_stdout.isatty.return_value = True

        result = supports_ansi_colors()

        assert result is True

    @patch.dict(os.environ, {
        'NO_COLOR': '1',
        'TERM': 'linux',  # Would normally support colors
        'COLORTERM': '',
        'FORCE_COLOR': '',
        'CI': '',
        'WT_SESSION': '',
        'ConEmuANSI': ''
    }, clear=True)
    @patch('sys.stdout')
    def test_no_color_returns_false(self, mock_stdout):
        """Test that NO_COLOR environment variable returns False."""
        mock_stdout.isatty.return_value = True

        result = supports_ansi_colors()

        assert result is False

    @patch.dict(os.environ, {'FORCE_COLOR': '1'}, clear=False)
    @patch('sys.stdout')
    def test_force_color_returns_true(self, mock_stdout):
        """Test that FORCE_COLOR environment variable returns True."""
        mock_stdout.isatty.return_value = True

        result = supports_ansi_colors()

        assert result is True

    @patch('sys.platform', 'linux')
    @patch('sys.stdout')
    def test_unix_with_tty_returns_true(self, mock_stdout):
        """Test that Unix-like systems with TTY return True."""
        mock_stdout.isatty.return_value = True

        result = supports_ansi_colors()

        assert result is True

    @patch.dict(os.environ, {'TERM': 'unknown-terminal'}, clear=True)
    @patch('sys.platform', 'linux')
    @patch('sys.stdout')
    def test_default_unix_fallback_returns_true(self, mock_stdout):
        """Test default fallback for Unix when all checks return None."""
        mock_stdout.isatty.return_value = True

        result = supports_ansi_colors()

        assert result is True

    @patch.dict(os.environ, {'TERM': 'unknown-terminal'}, clear=True)
    @patch('sys.platform', 'win32')
    @patch('os.name', 'nt')
    @patch('sys.stdout')
    def test_default_windows_fallback_returns_false(self, mock_stdout):
        """Test default fallback for Windows when all checks return None."""
        mock_stdout.isatty.return_value = True

        with patch('platform.system', return_value='Windows'):
            with patch('platform.version', side_effect=ValueError):
                result = supports_ansi_colors()

        assert result is False


class TestShouldUseRichUi:
    """Tests for rich UI decision logic."""

    @patch.dict(os.environ, {'ECRESHORE_SIMPLE_MODE': '1'}, clear=False)
    def test_simple_mode_override_returns_false(self):
        """Test that ECRESHORE_SIMPLE_MODE returns False."""
        result = should_use_rich_ui()

        assert result is False

    @patch.dict(os.environ, {'ECRESHORE_RICH_MODE': '1'}, clear=False)
    def test_rich_mode_override_returns_true(self):
        """Test that ECRESHORE_RICH_MODE returns True."""
        result = should_use_rich_ui()

        assert result is True

    @patch('src.ecreshore.terminal_detection.supports_ansi_colors', return_value=True)
    def test_follows_ansi_detection_true(self, mock_supports_ansi):
        """Test that it follows ANSI detection when True."""
        result = should_use_rich_ui()

        assert result is True

    @patch('src.ecreshore.terminal_detection.supports_ansi_colors', return_value=False)
    def test_follows_ansi_detection_false(self, mock_supports_ansi):
        """Test that it follows ANSI detection when False."""
        result = should_use_rich_ui()

        assert result is False


class TestGetTerminalInfo:
    """Tests for terminal information gathering."""

    @patch('sys.stdout')
    @patch.dict(os.environ, {
        'TERM': 'xterm-256color',
        'COLORTERM': 'truecolor',
        'WT_SESSION': '123',
        'NO_COLOR': '',
        'FORCE_COLOR': '1'
    }, clear=False)
    def test_gathers_comprehensive_info(self, mock_stdout):
        """Test that terminal info gathering works correctly."""
        mock_stdout.isatty.return_value = True

        with patch('sys.platform', 'win32'):
            with patch('src.ecreshore.terminal_detection.supports_ansi_colors', return_value=True):
                with patch('src.ecreshore.terminal_detection.should_use_rich_ui', return_value=True):
                    info = get_terminal_info()

        expected_keys = {
            'is_tty', 'term', 'colorterm', 'platform', 'ci_detected',
            'no_color', 'force_color', 'wt_session', 'conemu_ansi',
            'supports_ansi', 'should_use_rich'
        }

        assert set(info.keys()) == expected_keys
        assert info['is_tty'] is True
        assert info['term'] == 'xterm-256color'
        assert info['colorterm'] == 'truecolor'
        assert info['platform'] == 'win32'
        assert info['wt_session'] is True
        assert info['force_color'] is True
        assert info['supports_ansi'] is True
        assert info['should_use_rich'] is True

    @patch('sys.stdout')
    @patch.dict(os.environ, {
        'CI': '1',
        'GITHUB_ACTIONS': 'true'
    }, clear=False)
    def test_detects_ci_environment(self, mock_stdout):
        """Test that CI environment detection works."""
        mock_stdout.isatty.return_value = False

        info = get_terminal_info()

        assert info['ci_detected'] is True
        assert info['is_tty'] is False

    @patch('sys.stdout')
    @patch.dict(os.environ, {
        'ConEmuANSI': 'ON'
    }, clear=False)
    def test_detects_conemu_ansi(self, mock_stdout):
        """Test that ConEmu ANSI detection works."""
        mock_stdout.isatty.return_value = True

        info = get_terminal_info()

        assert info['conemu_ansi'] is True

    @patch('sys.stdout')
    @patch.dict(os.environ, {}, clear=True)
    def test_handles_missing_env_vars(self, mock_stdout):
        """Test that missing environment variables are handled gracefully."""
        mock_stdout.isatty.return_value = True

        info = get_terminal_info()

        assert info['term'] == ''
        assert info['colorterm'] == ''
        assert info['no_color'] is False
        assert info['force_color'] is False
        assert info['wt_session'] is False
        assert info['conemu_ansi'] is False


def test_import_paths():
    """Test that all imports work correctly."""
    from src.ecreshore.terminal_detection import (
        supports_ansi_colors,
        should_use_rich_ui,
        get_terminal_info
    )

    assert supports_ansi_colors is not None
    assert should_use_rich_ui is not None
    assert get_terminal_info is not None