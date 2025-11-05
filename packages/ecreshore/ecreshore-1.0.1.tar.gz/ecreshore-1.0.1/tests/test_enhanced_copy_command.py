"""Integration tests for the enhanced copy command with tag and repository inference."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from click.testing import CliRunner
from src.ecreshore.cli import cli


def test_copy_command_with_tag_in_url():
    """Test copy command with tag specified in URL."""
    runner = CliRunner()

    # Mock the async transfer to avoid actual ECR operations
    with patch('src.ecreshore.cli.core.copy._async_copy_image_enhanced') as mock_async_copy:
        # Setup mock to return successful result
        mock_result = Mock()
        mock_result.success = True
        mock_async_copy.return_value = mock_result

        result = runner.invoke(cli, ['copy', 'nginx:latest'])

        # Should succeed without repository argument
        assert result.exit_code == 0

        # Verify the mock was called with correct parsed arguments
        mock_async_copy.assert_called_once()
        args, kwargs = mock_async_copy.call_args
        request = args[2]  # Third argument is the TransferRequest

        assert request.source_image == 'nginx'  # Without tag
        assert request.target_repository == 'nginx'  # Inferred
        assert request.source_tag == 'latest'  # From URL
        assert request.target_tag == 'latest'  # Defaults to source


def test_copy_command_with_complex_registry_url():
    """Test copy command with complex registry URL and tag."""
    runner = CliRunner()

    with patch('src.ecreshore.cli.core.copy._async_copy_image_enhanced') as mock_async_copy:
        mock_result = Mock()
        mock_result.success = True
        mock_async_copy.return_value = mock_result

        result = runner.invoke(cli, ['copy', 'ghcr.io/fluxcd/helm-controller:v1.3.0'])

        assert result.exit_code == 0

        args, kwargs = mock_async_copy.call_args
        request = args[2]

        assert request.source_image == 'ghcr.io/fluxcd/helm-controller'
        assert request.target_repository == 'helm-controller'  # Last path component
        assert request.source_tag == 'v1.3.0'
        assert request.target_tag == 'v1.3.0'


def test_copy_command_with_explicit_target_repository():
    """Test that explicit target repository is still respected."""
    runner = CliRunner()

    with patch('src.ecreshore.cli.core.copy._async_copy_image_enhanced') as mock_async_copy:
        mock_result = Mock()
        mock_result.success = True
        mock_async_copy.return_value = mock_result

        result = runner.invoke(cli, ['copy', 'nginx:alpine', 'custom-nginx'])

        assert result.exit_code == 0

        args, kwargs = mock_async_copy.call_args
        request = args[2]

        assert request.source_image == 'nginx'
        assert request.target_repository == 'custom-nginx'  # Explicitly provided
        assert request.source_tag == 'alpine'
        assert request.target_tag == 'alpine'


def test_copy_command_with_custom_target_tag():
    """Test copy command with custom target tag."""
    runner = CliRunner()

    with patch('src.ecreshore.cli.core.copy._async_copy_image_enhanced') as mock_async_copy:
        mock_result = Mock()
        mock_result.success = True
        mock_async_copy.return_value = mock_result

        result = runner.invoke(cli, ['copy', 'nginx:1.21', '--target-tag', 'stable'])

        assert result.exit_code == 0

        args, kwargs = mock_async_copy.call_args
        request = args[2]

        assert request.source_image == 'nginx'
        assert request.target_repository == 'nginx'
        assert request.source_tag == '1.21'
        assert request.target_tag == 'stable'  # Custom target tag


def test_copy_command_tag_conflict_validation():
    """Test that conflicting tag specifications are rejected."""
    runner = CliRunner()

    # Should fail when both URL tag and --source-tag are provided
    result = runner.invoke(cli, ['copy', 'nginx:latest', '--source-tag', 'v1.20'])

    assert result.exit_code == 1
    assert "Cannot use both image:tag syntax" in result.output
    assert "simultaneously" in result.output


def test_copy_command_original_syntax_still_works():
    """Test that the original CLI syntax still works."""
    runner = CliRunner()

    with patch('src.ecreshore.cli.core.copy._async_copy_image_enhanced') as mock_async_copy:
        mock_result = Mock()
        mock_result.success = True
        mock_async_copy.return_value = mock_result

        # Original syntax: source_image target_repo --source-tag tag
        result = runner.invoke(cli, ['copy', 'nginx', 'my-nginx', '--source-tag', '1.21'])

        assert result.exit_code == 0

        args, kwargs = mock_async_copy.call_args
        request = args[2]

        assert request.source_image == 'nginx'
        assert request.target_repository == 'my-nginx'
        assert request.source_tag == '1.21'
        assert request.target_tag == '1.21'


def test_copy_command_with_registry_port():
    """Test copy command with registry that has port number."""
    runner = CliRunner()

    with patch('src.ecreshore.cli.core.copy._async_copy_image_enhanced') as mock_async_copy:
        mock_result = Mock()
        mock_result.success = True
        mock_async_copy.return_value = mock_result

        result = runner.invoke(cli, ['copy', 'localhost:5000/myapp:v1.0'])

        assert result.exit_code == 0

        args, kwargs = mock_async_copy.call_args
        request = args[2]

        assert request.source_image == 'localhost:5000/myapp'
        assert request.target_repository == 'myapp'
        assert request.source_tag == 'v1.0'


def test_copy_command_no_tag_uses_explicit_source_tag():
    """Test that when no tag in URL, explicit --source-tag is used."""
    runner = CliRunner()

    with patch('src.ecreshore.cli.core.copy._async_copy_image_enhanced') as mock_async_copy:
        mock_result = Mock()
        mock_result.success = True
        mock_async_copy.return_value = mock_result

        result = runner.invoke(cli, ['copy', 'nginx', '--source-tag', 'alpine'])

        assert result.exit_code == 0

        args, kwargs = mock_async_copy.call_args
        request = args[2]

        assert request.source_image == 'nginx'
        assert request.target_repository == 'nginx'  # Inferred
        assert request.source_tag == 'alpine'  # From --source-tag
        assert request.target_tag == 'alpine'


def test_copy_command_no_tag_defaults_to_latest():
    """Test that when no tag specified anywhere, defaults to latest."""
    runner = CliRunner()

    with patch('src.ecreshore.cli.core.copy._async_copy_image_enhanced') as mock_async_copy:
        mock_result = Mock()
        mock_result.success = True
        mock_async_copy.return_value = mock_result

        result = runner.invoke(cli, ['copy', 'postgres'])

        assert result.exit_code == 0

        args, kwargs = mock_async_copy.call_args
        request = args[2]

        assert request.source_image == 'postgres'
        assert request.target_repository == 'postgres'
        assert request.source_tag == 'latest'  # Default
        assert request.target_tag == 'latest'


def test_copy_command_with_multi_arch_flags():
    """Test copy command with multi-architecture flags."""
    runner = CliRunner()

    with patch('src.ecreshore.cli.core.copy._async_copy_image_enhanced') as mock_async_copy:
        mock_result = Mock()
        mock_result.success = True
        mock_async_copy.return_value = mock_result

        result = runner.invoke(cli, ['copy', 'nginx:alpine', '-A'])

        assert result.exit_code == 0

        args, kwargs = mock_async_copy.call_args
        request = args[2]

        assert request.source_image == 'nginx'
        assert request.target_repository == 'nginx'
        assert request.source_tag == 'alpine'
        assert request.preserve_architectures is True


def test_copy_command_with_platforms():
    """Test copy command with specific platforms."""
    runner = CliRunner()

    with patch('src.ecreshore.cli.core.copy._async_copy_image_enhanced') as mock_async_copy:
        mock_result = Mock()
        mock_result.success = True
        mock_async_copy.return_value = mock_result

        result = runner.invoke(cli, ['copy', 'nginx:latest', '--platforms', 'linux/amd64,linux/arm64'])

        assert result.exit_code == 0

        args, kwargs = mock_async_copy.call_args
        request = args[2]

        assert request.source_image == 'nginx'
        assert request.target_repository == 'nginx'
        assert request.source_tag == 'latest'
        assert request.target_platforms == ['linux/amd64', 'linux/arm64']


def test_copy_command_platform_conflicts_still_validated():
    """Test that platform conflicts are still properly validated."""
    runner = CliRunner()

    # Should fail when both --platforms and -A are used
    result = runner.invoke(cli, ['copy', 'nginx:latest', '--platforms', 'linux/amd64', '-A'])

    assert result.exit_code == 1
    assert "Cannot use both --platforms and -A/--all-architectures flags together" in result.output


def test_copy_command_deep_repository_inference():
    """Test repository inference with deep registry paths."""
    runner = CliRunner()

    with patch('src.ecreshore.cli.core.copy._async_copy_image_enhanced') as mock_async_copy:
        mock_result = Mock()
        mock_result.success = True
        mock_async_copy.return_value = mock_result

        result = runner.invoke(cli, ['copy', 'registry.company.com/team/division/project:v2.1'])

        assert result.exit_code == 0

        args, kwargs = mock_async_copy.call_args
        request = args[2]

        assert request.source_image == 'registry.company.com/team/division/project'
        assert request.target_repository == 'project'  # Last component
        assert request.source_tag == 'v2.1'