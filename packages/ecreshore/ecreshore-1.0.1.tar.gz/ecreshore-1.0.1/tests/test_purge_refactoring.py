"""Unit tests for purge() refactoring - service layer only (NO Click testing).

Following brain/patterns:
- fixture-pattern.xml for reusable fixtures
- factory-fixture-pattern.xml for factory fixtures
- pure-function-extraction-pattern.xml for PurgeOptions tests
- test-refactoring-pattern.xml for overall strategy

NOTE: We test extracted helpers, NOT the Click command itself.
"""

import pytest
from unittest.mock import Mock, patch, call
from src.ecreshore.cli.repository.purge import (
    PurgeOptions,
    _validate_purge_options,
    _execute_dry_run,
    _execute_with_confirmation,
)


# Factory Fixtures following brain/patterns/factory-fixture-pattern.xml

@pytest.fixture
def make_purge_options():
    """Factory for PurgeOptions with customizable fields.

    Follows brain pattern: factory-fixture-pattern for flexible test data creation.
    """
    def _factory(**kwargs):
        defaults = {
            'repository_name': None,
            'all_repositories': True,
            'region': 'us-west-2',
            'registry_id': '123456789012',
            'name_filter': None,
            'exclude_repositories': set(),
            'keep_latest': False,
            'dry_run': True,
        }
        defaults.update(kwargs)
        return PurgeOptions(**defaults)
    return _factory


@pytest.fixture
def mock_purge_service():
    """Mock ECRPurgeService for testing."""
    service = Mock()
    # Default: return result with repositories_processed > 0
    mock_result = Mock()
    mock_result.repositories_processed = 1
    mock_result.success_results = []
    mock_result.failed_results = []
    service.purge.return_value = mock_result
    return service


@pytest.fixture
def mock_reporter():
    """Mock ProgressReporter for testing."""
    reporter = Mock()
    # Make status() return a context manager
    reporter.status.return_value.__enter__ = Mock()
    reporter.status.return_value.__exit__ = Mock()
    return reporter


# Tests for _validate_purge_options() - Pure Function Tests

class TestValidatePurgeOptions:
    """Pure function tests for purge options validation."""

    def test_valid_single_repository(self):
        """Valid single repository purge."""
        options = _validate_purge_options(
            repository_name='my-repo',
            all_repositories=False,
            name_filter=None,
            exclude=(),
            region='us-west-2',
            registry_id='123456789012',
            keep_latest=True,
            dry_run=True,
        )

        assert options.repository_name == 'my-repo'
        assert options.all_repositories is False
        assert options.keep_latest is True
        assert options.dry_run is True
        assert options.exclude_repositories == set()

    def test_valid_all_repositories(self):
        """Valid all repositories purge."""
        options = _validate_purge_options(
            repository_name=None,
            all_repositories=True,
            name_filter=None,
            exclude=(),
            region='us-east-1',
            registry_id=None,
            keep_latest=False,
            dry_run=False,
        )

        assert options.repository_name is None
        assert options.all_repositories is True
        assert options.region == 'us-east-1'
        assert options.registry_id is None

    def test_valid_with_filter_and_exclude(self):
        """Valid all repositories with filter and exclude."""
        options = _validate_purge_options(
            repository_name=None,
            all_repositories=True,
            name_filter='my-app-*',
            exclude=('prod-repo', 'staging-repo'),
            region='us-west-2',
            registry_id='123456789012',
            keep_latest=True,
            dry_run=True,
        )

        assert options.name_filter == 'my-app-*'
        assert options.exclude_repositories == {'prod-repo', 'staging-repo'}

    def test_error_neither_repo_nor_all(self):
        """Error: Neither repository name nor --all specified."""
        with pytest.raises(ValueError, match="Must specify either a repository name or -A/--all"):
            _validate_purge_options(
                repository_name=None,
                all_repositories=False,
                name_filter=None,
                exclude=(),
                region='us-west-2',
                registry_id=None,
                keep_latest=False,
                dry_run=True,
            )

    def test_error_both_repo_and_all(self):
        """Error: Both repository name and --all specified."""
        with pytest.raises(ValueError, match="Cannot specify both repository name and -A/--all"):
            _validate_purge_options(
                repository_name='my-repo',
                all_repositories=True,
                name_filter=None,
                exclude=(),
                region='us-west-2',
                registry_id=None,
                keep_latest=False,
                dry_run=True,
            )

    def test_error_filter_with_single_repo(self):
        """Error: Filter specified with single repository."""
        with pytest.raises(ValueError, match="--filter and --exclude can only be used with -A/--all"):
            _validate_purge_options(
                repository_name='my-repo',
                all_repositories=False,
                name_filter='pattern',
                exclude=(),
                region='us-west-2',
                registry_id=None,
                keep_latest=False,
                dry_run=True,
            )

    def test_error_exclude_with_single_repo(self):
        """Error: Exclude specified with single repository."""
        with pytest.raises(ValueError, match="--filter and --exclude can only be used with -A/--all"):
            _validate_purge_options(
                repository_name='my-repo',
                all_repositories=False,
                name_filter=None,
                exclude=('other-repo',),
                region='us-west-2',
                registry_id=None,
                keep_latest=False,
                dry_run=True,
            )

    def test_empty_exclude_creates_empty_set(self):
        """Empty exclude tuple creates empty set."""
        options = _validate_purge_options(
            repository_name=None,
            all_repositories=True,
            name_filter=None,
            exclude=(),
            region='us-west-2',
            registry_id=None,
            keep_latest=False,
            dry_run=True,
        )

        assert options.exclude_repositories == set()
        assert isinstance(options.exclude_repositories, set)

    def test_exclude_tuple_converted_to_set(self):
        """Exclude tuple properly converted to set."""
        options = _validate_purge_options(
            repository_name=None,
            all_repositories=True,
            name_filter=None,
            exclude=('repo1', 'repo2', 'repo3'),
            region='us-west-2',
            registry_id=None,
            keep_latest=False,
            dry_run=True,
        )

        assert options.exclude_repositories == {'repo1', 'repo2', 'repo3'}


# Tests for _execute_dry_run()

class TestExecuteDryRun:
    """Tests for dry run execution helper."""

    @patch('src.ecreshore.cli.repository.purge._display_purge_preview')
    def test_successful_dry_run(self, mock_display, mock_purge_service, make_purge_options, mock_reporter):
        """Successful dry run with results."""
        options = make_purge_options(dry_run=True)

        _execute_dry_run(mock_purge_service, options, mock_reporter)

        # Verify service called with correct parameters
        mock_purge_service.purge.assert_called_once_with(
            repository_name=options.repository_name,
            all_repositories=options.all_repositories,
            keep_latest=options.keep_latest,
            dry_run=True,
            name_filter=options.name_filter,
            exclude_repositories=options.exclude_repositories,
        )

        # Verify display called
        mock_display.assert_called_once()
        mock_reporter.info.assert_called_once_with("Getting purge preview...")

    def test_no_repositories_found(self, mock_purge_service, make_purge_options, mock_reporter):
        """No repositories found - early return."""
        options = make_purge_options(dry_run=True)

        # Mock empty result
        mock_result = Mock()
        mock_result.repositories_processed = 0
        mock_purge_service.purge.return_value = mock_result

        _execute_dry_run(mock_purge_service, options, mock_reporter)

        # Verify info message
        assert mock_reporter.info.call_count == 2
        mock_reporter.info.assert_any_call("No repositories found to purge")

    @patch('src.ecreshore.cli.repository.purge._display_purge_preview')
    def test_service_parameters_single_repo(self, mock_display, mock_purge_service, make_purge_options, mock_reporter):
        """Service called with correct params for single repo."""
        options = make_purge_options(
            repository_name='my-repo',
            all_repositories=False,
            keep_latest=True,
            dry_run=True,
        )

        _execute_dry_run(mock_purge_service, options, mock_reporter)

        call_kwargs = mock_purge_service.purge.call_args[1]
        assert call_kwargs['repository_name'] == 'my-repo'
        assert call_kwargs['all_repositories'] is False
        assert call_kwargs['keep_latest'] is True
        assert call_kwargs['dry_run'] is True

    @patch('src.ecreshore.cli.repository.purge._display_purge_preview')
    def test_display_preview_called_with_correct_args(self, mock_display, mock_purge_service, make_purge_options, mock_reporter):
        """Display preview called with result, reporter, and keep_latest."""
        options = make_purge_options(keep_latest=True)

        _execute_dry_run(mock_purge_service, options, mock_reporter)

        result = mock_purge_service.purge.return_value
        mock_display.assert_called_once_with(result, mock_reporter, True)


# Tests for _execute_with_confirmation()

class TestExecuteWithConfirmation:
    """Tests for confirmation execution helper."""

    def test_no_repositories_found_early_return(self, mock_purge_service, make_purge_options, mock_reporter):
        """No repositories found - early return before confirmation."""
        options = make_purge_options(dry_run=False)

        # Mock empty result
        mock_result = Mock()
        mock_result.repositories_processed = 0
        mock_purge_service.purge.return_value = mock_result

        _execute_with_confirmation(mock_purge_service, options, mock_reporter)

        # Verify only one purge call (preview), not actual execution
        assert mock_purge_service.purge.call_count == 1
        mock_reporter.info.assert_called_once_with("No repositories found to purge")

    @patch('src.ecreshore.cli.repository.purge.click.confirm', return_value=True)
    @patch('src.ecreshore.cli.repository.purge._display_purge_summary')
    @patch('src.ecreshore.cli.repository.purge._display_purge_results')
    @patch('src.ecreshore.cli.repository.purge._should_display_repository', return_value=True)
    def test_user_confirms_executes_purge(
        self, mock_should_display, mock_display_results, mock_display_summary,
        mock_confirm, mock_purge_service, make_purge_options, mock_reporter
    ):
        """User confirms - executes actual purge."""
        options = make_purge_options(dry_run=False)

        # Mock preview with actionable repos
        preview_result = Mock()
        preview_result.repositories_processed = 1
        preview_result.success_results = [Mock()]
        preview_result.failed_results = []

        # Mock actual result
        actual_result = Mock()

        mock_purge_service.purge.side_effect = [preview_result, actual_result]

        _execute_with_confirmation(mock_purge_service, options, mock_reporter)

        # Verify two purge calls: preview + actual
        assert mock_purge_service.purge.call_count == 2

        # Verify preview call (dry_run=True)
        preview_call = mock_purge_service.purge.call_args_list[0][1]
        assert preview_call['dry_run'] is True

        # Verify actual call (dry_run=False)
        actual_call = mock_purge_service.purge.call_args_list[1][1]
        assert actual_call['dry_run'] is False

        # Verify results displayed
        mock_display_results.assert_called_once()

    @patch('src.ecreshore.cli.repository.purge.click.confirm', return_value=False)
    @patch('src.ecreshore.cli.repository.purge._display_purge_summary')
    @patch('src.ecreshore.cli.repository.purge._should_display_repository', return_value=True)
    def test_user_cancels_aborts(
        self, mock_should_display, mock_display_summary, mock_confirm,
        mock_purge_service, make_purge_options, mock_reporter
    ):
        """User cancels - aborts without executing."""
        options = make_purge_options(dry_run=False)

        # Mock preview
        preview_result = Mock()
        preview_result.repositories_processed = 1
        preview_result.success_results = [Mock()]
        preview_result.failed_results = []
        mock_purge_service.purge.return_value = preview_result

        _execute_with_confirmation(mock_purge_service, options, mock_reporter)

        # Verify only preview call, no actual execution
        assert mock_purge_service.purge.call_count == 1
        mock_reporter.info.assert_called_once_with("Purge cancelled by user")

    @patch('src.ecreshore.cli.repository.purge.click.confirm', return_value=True)
    @patch('src.ecreshore.cli.repository.purge._display_purge_summary')
    @patch('src.ecreshore.cli.repository.purge._display_purge_results')
    @patch('src.ecreshore.cli.repository.purge._should_display_repository', return_value=True)
    @patch('src.ecreshore.cli.repository.purge.console')
    def test_confirmation_prompt_displayed(
        self, mock_console, mock_should_display, mock_display_results,
        mock_display_summary, mock_confirm, mock_purge_service,
        make_purge_options, mock_reporter
    ):
        """Confirmation prompt with destructive warning displayed."""
        options = make_purge_options(repository_name='my-repo', dry_run=False, all_repositories=False)

        # Mock preview
        preview_result = Mock()
        preview_result.repositories_processed = 1
        preview_result.success_results = [Mock()]
        preview_result.failed_results = []
        mock_purge_service.purge.return_value = preview_result

        _execute_with_confirmation(mock_purge_service, options, mock_reporter)

        # Verify warning displayed
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        assert any('DESTRUCTIVE' in str(call) for call in print_calls)

        # Verify repository name displayed
        assert any('my-repo' in str(call) for call in print_calls)

    @patch('src.ecreshore.cli.repository.purge.click.confirm', return_value=True)
    @patch('src.ecreshore.cli.repository.purge._display_purge_summary')
    @patch('src.ecreshore.cli.repository.purge._display_purge_results')
    @patch('src.ecreshore.cli.repository.purge._should_display_repository', return_value=True)
    def test_keep_latest_message_displayed(
        self, mock_should_display, mock_display_results, mock_display_summary,
        mock_confirm, mock_purge_service, make_purge_options, mock_reporter
    ):
        """Keep-latest message displayed when enabled."""
        with patch('src.ecreshore.cli.repository.purge.console') as mock_console:
            options = make_purge_options(keep_latest=True, dry_run=False)

            # Mock preview
            preview_result = Mock()
            preview_result.repositories_processed = 1
            preview_result.success_results = [Mock()]
            preview_result.failed_results = []
            mock_purge_service.purge.return_value = preview_result

            _execute_with_confirmation(mock_purge_service, options, mock_reporter)

            # Verify keep-latest message
            print_calls = [str(call) for call in mock_console.print.call_args_list]
            assert any('most recent image' in str(call) for call in print_calls)
