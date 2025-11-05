"""Tests for cli/core/batch.py helper functions.

Following cli-testing-pattern:
- Test business logic, not Click framework
- Test validation functions with pure assertions
- Test side-effect functions with mocks
- Fast execution, no CliRunner complexity
"""

import os
from unittest.mock import patch

import pytest

from ecreshore.cli.core.batch import (
    BatchExecutionConfig,
    _setup_skip_debug_environment,
    _validate_batch_flags,
)


# ============================================================================
# Tests for _validate_batch_flags()
# ============================================================================


class TestValidateBatchFlags:
    """Test batch command flag validation."""

    def test_valid_flags_console_no_debug(self):
        """Test valid flags with console output and no debug."""
        # Should not raise
        _validate_batch_flags(
            simple=False,
            rich=False,
            output="console",
            debug_skip_decisions=False,
            skip_audit_trail=False,
            explain_skips=False,
        )

    def test_valid_flags_log_output_no_debug(self):
        """Test valid flags with log output and no debug."""
        # Should not raise
        _validate_batch_flags(
            simple=False,
            rich=False,
            output="log",
            debug_skip_decisions=False,
            skip_audit_trail=False,
            explain_skips=False,
        )

    def test_valid_flags_with_simple_mode(self):
        """Test valid flags with simple mode enabled."""
        # Should not raise
        _validate_batch_flags(
            simple=True,
            rich=False,
            output="console",
            debug_skip_decisions=False,
            skip_audit_trail=False,
            explain_skips=False,
        )

    def test_valid_flags_with_rich_mode(self):
        """Test valid flags with rich mode enabled."""
        # Should not raise
        _validate_batch_flags(
            simple=False,
            rich=True,
            output="console",
            debug_skip_decisions=False,
            skip_audit_trail=False,
            explain_skips=False,
        )

    def test_valid_flags_with_debug_skip_decisions(self):
        """Test valid flags with debug skip decisions enabled."""
        # Should not raise
        _validate_batch_flags(
            simple=False,
            rich=False,
            output="console",
            debug_skip_decisions=True,
            skip_audit_trail=False,
            explain_skips=False,
        )

    def test_error_both_simple_and_rich(self):
        """Test error when both simple and rich flags are set."""
        with pytest.raises(ValueError, match="Cannot use both --simple and --rich"):
            _validate_batch_flags(
                simple=True,
                rich=True,
                output="console",
                debug_skip_decisions=False,
                skip_audit_trail=False,
                explain_skips=False,
            )

    def test_error_debug_skip_with_log_output_debug_decisions(self):
        """Test error when debug_skip_decisions used with log output."""
        with pytest.raises(
            ValueError, match="Skip debug flags are not compatible with --output log"
        ):
            _validate_batch_flags(
                simple=False,
                rich=False,
                output="log",
                debug_skip_decisions=True,
                skip_audit_trail=False,
                explain_skips=False,
            )

    def test_error_skip_audit_trail_with_log_output(self):
        """Test error when skip_audit_trail used with log output."""
        with pytest.raises(
            ValueError, match="Skip debug flags are not compatible with --output log"
        ):
            _validate_batch_flags(
                simple=False,
                rich=False,
                output="log",
                debug_skip_decisions=False,
                skip_audit_trail=True,
                explain_skips=False,
            )

    def test_error_explain_skips_with_log_output(self):
        """Test error when explain_skips used with log output."""
        with pytest.raises(
            ValueError, match="Skip debug flags are not compatible with --output log"
        ):
            _validate_batch_flags(
                simple=False,
                rich=False,
                output="log",
                debug_skip_decisions=False,
                skip_audit_trail=False,
                explain_skips=True,
            )

    def test_error_multiple_skip_debug_flags_with_log_output(self):
        """Test error when multiple skip debug flags used with log output."""
        with pytest.raises(
            ValueError, match="Skip debug flags are not compatible with --output log"
        ):
            _validate_batch_flags(
                simple=False,
                rich=False,
                output="log",
                debug_skip_decisions=True,
                skip_audit_trail=True,
                explain_skips=True,
            )

    def test_all_skip_debug_flags_with_console_valid(self):
        """Test all skip debug flags enabled with console output (valid)."""
        # Should not raise
        _validate_batch_flags(
            simple=False,
            rich=False,
            output="console",
            debug_skip_decisions=True,
            skip_audit_trail=True,
            explain_skips=True,
        )


# ============================================================================
# Tests for BatchExecutionConfig
# ============================================================================


class TestBatchExecutionConfig:
    """Test BatchExecutionConfig dataclass."""

    def test_config_creation_minimal(self):
        """Test creating config with minimal fields."""
        config = BatchExecutionConfig(
            config_file="test.yml",
            dry_run=False,
            output="console",
            use_rich_ui=True,
            force=False,
            verbose=0,
            debug_skip_decisions=False,
            skip_audit_trail=False,
            explain_skips=False,
        )

        assert config.config_file == "test.yml"
        assert config.dry_run is False
        assert config.skip_debug_enabled is False

    def test_config_skip_debug_enabled_property_no_flags(self):
        """Test skip_debug_enabled property with no flags."""
        config = BatchExecutionConfig(
            config_file="test.yml",
            dry_run=False,
            output="console",
            use_rich_ui=True,
            force=False,
            verbose=0,
            debug_skip_decisions=False,
            skip_audit_trail=False,
            explain_skips=False,
        )

        assert config.skip_debug_enabled is False

    def test_config_skip_debug_enabled_property_debug_decisions(self):
        """Test skip_debug_enabled property with debug_skip_decisions."""
        config = BatchExecutionConfig(
            config_file="test.yml",
            dry_run=False,
            output="console",
            use_rich_ui=True,
            force=False,
            verbose=0,
            debug_skip_decisions=True,
            skip_audit_trail=False,
            explain_skips=False,
        )

        assert config.skip_debug_enabled is True

    def test_config_skip_debug_enabled_property_audit_trail(self):
        """Test skip_debug_enabled property with skip_audit_trail."""
        config = BatchExecutionConfig(
            config_file="test.yml",
            dry_run=False,
            output="console",
            use_rich_ui=True,
            force=False,
            verbose=0,
            debug_skip_decisions=False,
            skip_audit_trail=True,
            explain_skips=False,
        )

        assert config.skip_debug_enabled is True

    def test_config_skip_debug_enabled_property_explain_skips(self):
        """Test skip_debug_enabled property with explain_skips."""
        config = BatchExecutionConfig(
            config_file="test.yml",
            dry_run=False,
            output="console",
            use_rich_ui=True,
            force=False,
            verbose=0,
            debug_skip_decisions=False,
            skip_audit_trail=False,
            explain_skips=True,
        )

        assert config.skip_debug_enabled is True

    def test_config_skip_debug_enabled_property_all_flags(self):
        """Test skip_debug_enabled property with all flags enabled."""
        config = BatchExecutionConfig(
            config_file="test.yml",
            dry_run=False,
            output="console",
            use_rich_ui=True,
            force=False,
            verbose=0,
            debug_skip_decisions=True,
            skip_audit_trail=True,
            explain_skips=True,
        )

        assert config.skip_debug_enabled is True


# ============================================================================
# Tests for _setup_skip_debug_environment()
# ============================================================================


class TestSetupSkipDebugEnvironment:
    """Test skip debug environment variable setup."""

    @patch.dict(os.environ, {}, clear=True)
    def test_no_flags_enabled_no_env_vars_set(self):
        """Test that no env vars are set when no flags enabled."""
        config = BatchExecutionConfig(
            config_file="test.yml",
            dry_run=False,
            output="console",
            use_rich_ui=True,
            force=False,
            verbose=0,
            debug_skip_decisions=False,
            skip_audit_trail=False,
            explain_skips=False,
        )

        _setup_skip_debug_environment(config)

        assert "ECRESHORE_DEBUG_SKIP_DECISIONS" not in os.environ
        assert "ECRESHORE_SKIP_AUDIT_TRAIL" not in os.environ
        assert "ECRESHORE_EXPLAIN_SKIPS" not in os.environ

    @patch.dict(os.environ, {}, clear=True)
    def test_debug_skip_decisions_sets_env_var(self):
        """Test that debug_skip_decisions flag sets correct env var."""
        config = BatchExecutionConfig(
            config_file="test.yml",
            dry_run=False,
            output="console",
            use_rich_ui=True,
            force=False,
            verbose=0,
            debug_skip_decisions=True,
            skip_audit_trail=False,
            explain_skips=False,
        )

        _setup_skip_debug_environment(config)

        assert os.environ.get("ECRESHORE_DEBUG_SKIP_DECISIONS") == "1"
        assert "ECRESHORE_SKIP_AUDIT_TRAIL" not in os.environ
        assert "ECRESHORE_EXPLAIN_SKIPS" not in os.environ

    @patch.dict(os.environ, {}, clear=True)
    def test_skip_audit_trail_sets_env_var(self):
        """Test that skip_audit_trail flag sets correct env var."""
        config = BatchExecutionConfig(
            config_file="test.yml",
            dry_run=False,
            output="console",
            use_rich_ui=True,
            force=False,
            verbose=0,
            debug_skip_decisions=False,
            skip_audit_trail=True,
            explain_skips=False,
        )

        _setup_skip_debug_environment(config)

        assert "ECRESHORE_DEBUG_SKIP_DECISIONS" not in os.environ
        assert os.environ.get("ECRESHORE_SKIP_AUDIT_TRAIL") == "1"
        assert "ECRESHORE_EXPLAIN_SKIPS" not in os.environ

    @patch.dict(os.environ, {}, clear=True)
    def test_explain_skips_sets_env_var(self):
        """Test that explain_skips flag sets correct env var."""
        config = BatchExecutionConfig(
            config_file="test.yml",
            dry_run=False,
            output="console",
            use_rich_ui=True,
            force=False,
            verbose=0,
            debug_skip_decisions=False,
            skip_audit_trail=False,
            explain_skips=True,
        )

        _setup_skip_debug_environment(config)

        assert "ECRESHORE_DEBUG_SKIP_DECISIONS" not in os.environ
        assert "ECRESHORE_SKIP_AUDIT_TRAIL" not in os.environ
        assert os.environ.get("ECRESHORE_EXPLAIN_SKIPS") == "1"

    @patch.dict(os.environ, {}, clear=True)
    def test_all_flags_set_all_env_vars(self):
        """Test that all flags enabled sets all env vars."""
        config = BatchExecutionConfig(
            config_file="test.yml",
            dry_run=False,
            output="console",
            use_rich_ui=True,
            force=False,
            verbose=0,
            debug_skip_decisions=True,
            skip_audit_trail=True,
            explain_skips=True,
        )

        _setup_skip_debug_environment(config)

        assert os.environ.get("ECRESHORE_DEBUG_SKIP_DECISIONS") == "1"
        assert os.environ.get("ECRESHORE_SKIP_AUDIT_TRAIL") == "1"
        assert os.environ.get("ECRESHORE_EXPLAIN_SKIPS") == "1"

    @patch.dict(os.environ, {}, clear=True)
    def test_idempotent_multiple_calls(self):
        """Test that calling setup multiple times is safe (idempotent)."""
        config = BatchExecutionConfig(
            config_file="test.yml",
            dry_run=False,
            output="console",
            use_rich_ui=True,
            force=False,
            verbose=0,
            debug_skip_decisions=True,
            skip_audit_trail=False,
            explain_skips=False,
        )

        _setup_skip_debug_environment(config)
        _setup_skip_debug_environment(config)  # Call again

        # Should still be set correctly
        assert os.environ.get("ECRESHORE_DEBUG_SKIP_DECISIONS") == "1"
        assert "ECRESHORE_SKIP_AUDIT_TRAIL" not in os.environ
