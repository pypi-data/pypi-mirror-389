"""Terminal capability detection utilities."""

import os
import sys
from typing import Optional


def _check_explicit_overrides() -> Optional[bool]:
    """Check for explicit user color preference overrides.

    Returns:
        True if FORCE_COLOR is set, False if NO_COLOR is set, None to continue checking
    """
    if os.environ.get("FORCE_COLOR"):
        return True

    if os.environ.get("NO_COLOR"):
        return False

    return None


def _check_tty_status() -> Optional[bool]:
    """Check if stdout is connected to a TTY.

    Returns:
        False if not a TTY (output redirected), None to continue checking
    """
    if not sys.stdout.isatty():
        return False

    return None


def _check_ci_environment() -> Optional[bool]:
    """Check if running in a CI/non-interactive environment.

    Returns:
        False if CI environment detected, None to continue checking
    """
    ci_environments = {
        "CI",
        "CONTINUOUS_INTEGRATION",
        "BUILD_NUMBER",
        "RUN_ID",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "JENKINS_URL",
        "BUILDKITE",
        "CIRCLECI",
        "TRAVIS",
        "TEAMCITY_VERSION",
        "TF_BUILD",
    }

    if any(env_var in os.environ for env_var in ci_environments):
        return False

    return None


def _check_term_variable() -> Optional[bool]:
    """Check TERM environment variable for ANSI support indicators.

    Returns:
        True if known ANSI-capable terminal, False if known incompatible,
        None to continue checking
    """
    term = os.environ.get("TERM", "").lower()

    # Known terminals that don't support ANSI
    if term in ("dumb", "unknown", ""):
        return False

    # Most modern terminals support ANSI
    modern_terminals = [
        "xterm", "vt100", "vt220", "rxvt", "color", "ansi",
        "cygwin", "linux", "screen", "tmux", "konsole", "gnome", "iterm",
    ]

    if any(term_type in term for term_type in modern_terminals):
        return True

    return None


def _check_platform_specific() -> Optional[bool]:
    """Check platform-specific ANSI support (Windows, COLORTERM).

    Returns:
        True if platform supports ANSI, False if not, None for default behavior
    """
    # Check for COLORTERM (indicates 256-color or truecolor support)
    if os.environ.get("COLORTERM") in ("truecolor", "24bit", "256color"):
        return True

    # Windows-specific checks
    if os.name == "nt":
        # Windows Terminal
        if os.environ.get("WT_SESSION"):
            return True

        # ConEmu
        if os.environ.get("ConEmuANSI") == "ON":
            return True

        # Windows 10+ built-in console with ANSI support
        try:
            import platform

            if platform.system() == "Windows":
                version = platform.version()
                # Windows 10 build 1511+ supports ANSI
                if version and int(version.split(".")[2]) >= 10586:
                    return True
        except (ValueError, IndexError, ImportError):
            pass

        # Default to False for older Windows
        return False

    return None


def supports_ansi_colors() -> bool:
    """Detect if the current terminal supports ANSI colors and rich formatting.

    This function checks various environment indicators to determine if the
    terminal can handle ANSI escape sequences for colors, progress bars, etc.

    The detection follows a decision chain:
    1. Explicit overrides (FORCE_COLOR/NO_COLOR)
    2. TTY status (piped output)
    3. CI environment detection
    4. TERM variable analysis
    5. Platform-specific checks (Windows, COLORTERM)
    6. Default based on platform

    Returns:
        True if terminal supports ANSI colors, False otherwise
    """
    # Decision chain: each check returns True/False (definitive) or None (continue)
    checks = [
        _check_explicit_overrides,
        _check_tty_status,
        _check_ci_environment,
        _check_term_variable,
        _check_platform_specific,
    ]

    for check in checks:
        result = check()
        if result is not None:
            return result

    # Default: True for Unix-like systems with a TTY, False for Windows
    return sys.platform != "win32"


def should_use_rich_ui() -> bool:
    """Determine if rich UI should be used by default.

    This considers ANSI support, terminal capabilities, and user preferences.

    Returns:
        True if rich UI should be used by default, False for simple mode
    """
    # Check for explicit user preference
    if os.environ.get("ECRESHORE_SIMPLE_MODE"):
        return False

    if os.environ.get("ECRESHORE_RICH_MODE"):
        return True

    # Use ANSI detection as primary decision factor
    return supports_ansi_colors()


def get_terminal_info() -> dict:
    """Get information about the current terminal environment.

    Useful for debugging terminal detection issues.

    Returns:
        Dictionary with terminal environment information
    """
    return {
        "is_tty": sys.stdout.isatty(),
        "term": os.environ.get("TERM", ""),
        "colorterm": os.environ.get("COLORTERM", ""),
        "platform": sys.platform,
        "ci_detected": any(
            env_var in os.environ
            for env_var in {
                "CI",
                "CONTINUOUS_INTEGRATION",
                "BUILD_NUMBER",
                "RUN_ID",
                "GITHUB_ACTIONS",
                "GITLAB_CI",
                "JENKINS_URL",
                "BUILDKITE",
                "CIRCLECI",
                "TRAVIS",
                "TEAMCITY_VERSION",
                "TF_BUILD",
            }
        ),
        "no_color": bool(os.environ.get("NO_COLOR")),
        "force_color": bool(os.environ.get("FORCE_COLOR")),
        "wt_session": bool(os.environ.get("WT_SESSION")),
        "conemu_ansi": os.environ.get("ConEmuANSI") == "ON",
        "supports_ansi": supports_ansi_colors(),
        "should_use_rich": should_use_rich_ui(),
    }
