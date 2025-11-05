"""Tests for ECR purge service."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch, call
import pytest

from src.ecreshore.ecr_auth import ECRAuthenticationError
from src.ecreshore.services.purge_service import ECRPurgeService, PurgeResult, PurgeSummary
from src.ecreshore.services.ecr_repository import ECRRepository, ECRImage


class TestECRPurgeService:
    """Test ECR purge service functionality."""

    def test_init(self):
        """Test purge service initialization."""
        service = ECRPurgeService(region_name="us-east-1", registry_id="123456789012")
        assert service.region_name == "us-east-1"
        assert service.registry_id == "123456789012"
        assert service._ecr_service is not None

    @patch('src.ecreshore.services.purge_service.ECRRepositoryService')
    def test_get_purge_preview_empty(self, mock_service_class):
        """Test purge preview with no repositories."""
        mock_service = Mock()
        mock_service.list_repositories.return_value = []
        mock_service_class.return_value = mock_service

        service = ECRPurgeService()
        preview = service.get_purge_preview()

        assert preview == {}
        mock_service.list_repositories.assert_called_once_with(
            name_filter=None, max_results=1000
        )

    @patch('src.ecreshore.services.purge_service.ECRRepositoryService')
    def test_get_purge_preview_with_repos(self, mock_service_class):
        """Test purge preview with repositories."""
        # Create test repositories
        repo1 = ECRRepository(
            name="repo1",
            uri="123456789012.dkr.ecr.us-east-1.amazonaws.com/repo1",
            created_at=datetime.now(timezone.utc),
            image_count=5,
            size_bytes=1024,
            registry_id="123456789012",
            region="us-east-1"
        )
        repo2 = ECRRepository(
            name="repo2",
            uri="123456789012.dkr.ecr.us-east-1.amazonaws.com/repo2",
            created_at=datetime.now(timezone.utc),
            image_count=3,
            size_bytes=2048,
            registry_id="123456789012",
            region="us-east-1"
        )

        mock_service = Mock()
        mock_service.list_repositories.return_value = [repo1, repo2]
        mock_service_class.return_value = mock_service

        service = ECRPurgeService()
        preview = service.get_purge_preview()

        expected = {
            "repo1": 5,
            "repo2": 3
        }
        assert preview == expected

    @patch('src.ecreshore.services.purge_service.ECRRepositoryService')
    def test_get_purge_preview_with_exclusions(self, mock_service_class):
        """Test purge preview with exclusions."""
        repo1 = ECRRepository(
            name="repo1",
            uri="123456789012.dkr.ecr.us-east-1.amazonaws.com/repo1",
            created_at=datetime.now(timezone.utc),
            image_count=5,
            size_bytes=1024,
            registry_id="123456789012",
            region="us-east-1"
        )
        repo2 = ECRRepository(
            name="important-repo",
            uri="123456789012.dkr.ecr.us-east-1.amazonaws.com/important-repo",
            created_at=datetime.now(timezone.utc),
            image_count=3,
            size_bytes=2048,
            registry_id="123456789012",
            region="us-east-1"
        )

        mock_service = Mock()
        mock_service.list_repositories.return_value = [repo1, repo2]
        mock_service_class.return_value = mock_service

        service = ECRPurgeService()
        preview = service.get_purge_preview(exclude_repositories={"important-repo"})

        expected = {
            "repo1": 5
        }
        assert preview == expected

    @patch('src.ecreshore.services.purge_service.ECRRepositoryService')
    def test_purge_repository_empty(self, mock_service_class):
        """Test purging an empty repository."""
        mock_service = Mock()
        mock_service.list_images.return_value = []
        mock_service_class.return_value = mock_service

        service = ECRPurgeService()
        result = service.purge_repository("empty-repo")

        assert result.repository_name == "empty-repo"
        assert result.images_deleted == 0
        assert result.images_kept == 0
        assert result.images_failed == 0
        assert result.success is True
        assert result.kept_latest is False
        assert result.error_message is None

    @patch('src.ecreshore.services.purge_service.ECRRepositoryService')
    def test_purge_repository_dry_run(self, mock_service_class):
        """Test dry run purge of repository."""
        # Create test images
        images = [
            ECRImage(
                repository_name="test-repo",
                image_tags=["tag1"],
                image_digest="sha256:abcd1234",
                size_bytes=1024,
                pushed_at=datetime.now(timezone.utc),
                registry_id="123456789012",
                region="us-east-1"
            ),
            ECRImage(
                repository_name="test-repo",
                image_tags=["tag2"],
                image_digest="sha256:efgh5678",
                size_bytes=2048,
                pushed_at=datetime.now(timezone.utc),
                registry_id="123456789012",
                region="us-east-1"
            )
        ]

        mock_service = Mock()
        mock_service.list_images.return_value = images
        mock_service_class.return_value = mock_service

        service = ECRPurgeService()
        result = service.purge_repository("test-repo", dry_run=True)

        assert result.repository_name == "test-repo"
        assert result.images_deleted == 2  # Would delete 2 images
        assert result.images_failed == 0
        assert result.success is True
        assert result.error_message is None

    @patch('src.ecreshore.services.purge_service.ECRRepositoryService')
    def test_purge_repository_success(self, mock_service_class):
        """Test successful repository purge."""
        # Create test images
        images = [
            ECRImage(
                repository_name="test-repo",
                image_tags=["tag1"],
                image_digest="sha256:abcd1234",
                size_bytes=1024,
                pushed_at=datetime.now(timezone.utc),
                registry_id="123456789012",
                region="us-east-1"
            )
        ]

        mock_ecr_client = Mock()
        mock_ecr_client.batch_delete_image.return_value = {
            'imageIds': [{'imageDigest': 'sha256:abcd1234'}],
            'failures': []
        }

        mock_service = Mock()
        mock_service.list_images.return_value = images
        mock_service.ecr_client = mock_ecr_client
        mock_service_class.return_value = mock_service

        service = ECRPurgeService()
        result = service.purge_repository("test-repo")

        assert result.repository_name == "test-repo"
        assert result.images_deleted == 1
        assert result.images_failed == 0
        assert result.success is True
        assert result.error_message is None

        mock_ecr_client.batch_delete_image.assert_called_once_with(
            repositoryName="test-repo",
            imageIds=[{'imageDigest': 'sha256:abcd1234'}]
        )

    @patch('src.ecreshore.services.purge_service.ECRRepositoryService')
    def test_purge_repository_with_failures(self, mock_service_class):
        """Test repository purge with some failures."""
        images = [
            ECRImage(
                repository_name="test-repo",
                image_tags=["tag1"],
                image_digest="sha256:abcd1234",
                size_bytes=1024,
                pushed_at=datetime.now(timezone.utc),
                registry_id="123456789012",
                region="us-east-1"
            ),
            ECRImage(
                repository_name="test-repo",
                image_tags=["tag2"],
                image_digest="sha256:efgh5678",
                size_bytes=2048,
                pushed_at=datetime.now(timezone.utc),
                registry_id="123456789012",
                region="us-east-1"
            )
        ]

        mock_ecr_client = Mock()
        mock_ecr_client.batch_delete_image.return_value = {
            'imageIds': [{'imageDigest': 'sha256:abcd1234'}],
            'failures': [
                {
                    'imageId': {'imageDigest': 'sha256:efgh5678'},
                    'failureReason': 'Image in use'
                }
            ]
        }

        mock_service = Mock()
        mock_service.list_images.return_value = images
        mock_service.ecr_client = mock_ecr_client
        mock_service_class.return_value = mock_service

        service = ECRPurgeService()
        result = service.purge_repository("test-repo")

        assert result.repository_name == "test-repo"
        assert result.images_deleted == 1
        assert result.images_failed == 1
        assert result.success is False  # Has failures
        assert result.error_message is None

    @patch('src.ecreshore.services.purge_service.ECRRepositoryService')
    def test_delete_image_batch_large_batch(self, mock_service_class):
        """Test batching behavior with large number of images."""
        # Create 150 test images (more than batch size of 100)
        images = []
        for i in range(150):
            images.append(
                ECRImage(
                    repository_name="test-repo",
                    image_tags=[f"tag{i}"],
                    image_digest=f"sha256:digest{i:04d}",
                    size_bytes=1024,
                    pushed_at=datetime.now(timezone.utc),
                    registry_id="123456789012",
                    region="us-east-1"
                )
            )

        mock_ecr_client = Mock()
        # Mock successful deletion of all images
        mock_ecr_client.batch_delete_image.side_effect = [
            {
                'imageIds': [{'imageDigest': f'sha256:digest{i:04d}'} for i in range(100)],
                'failures': []
            },
            {
                'imageIds': [{'imageDigest': f'sha256:digest{i:04d}'} for i in range(100, 150)],
                'failures': []
            }
        ]

        mock_service = Mock()
        mock_service.list_images.return_value = images
        mock_service.ecr_client = mock_ecr_client
        mock_service_class.return_value = mock_service

        service = ECRPurgeService()
        result = service.purge_repository("test-repo")

        assert result.repository_name == "test-repo"
        assert result.images_deleted == 150
        assert result.images_failed == 0
        assert result.success is True

        # Should be called twice due to batching
        assert mock_ecr_client.batch_delete_image.call_count == 2

    @patch('src.ecreshore.services.purge_service.ECRRepositoryService')
    def test_purge_all_repositories_success(self, mock_service_class):
        """Test successful purge of all repositories."""
        # Create test repositories
        repos = [
            ECRRepository(
                name="repo1",
                uri="123456789012.dkr.ecr.us-east-1.amazonaws.com/repo1",
                created_at=datetime.now(timezone.utc),
                image_count=2,
                size_bytes=1024,
                registry_id="123456789012",
                region="us-east-1"
            ),
            ECRRepository(
                name="repo2",
                uri="123456789012.dkr.ecr.us-east-1.amazonaws.com/repo2",
                created_at=datetime.now(timezone.utc),
                image_count=1,
                size_bytes=2048,
                registry_id="123456789012",
                region="us-east-1"
            )
        ]

        # Mock images for each repository
        repo1_images = [
            ECRImage("repo1", ["tag1"], "sha256:abcd1", 1024, datetime.now(timezone.utc), "123456789012", "us-east-1"),
            ECRImage("repo1", ["tag2"], "sha256:abcd2", 1024, datetime.now(timezone.utc), "123456789012", "us-east-1")
        ]
        repo2_images = [
            ECRImage("repo2", ["tag1"], "sha256:efgh1", 2048, datetime.now(timezone.utc), "123456789012", "us-east-1")
        ]

        mock_ecr_client = Mock()
        mock_ecr_client.batch_delete_image.side_effect = [
            {'imageIds': [{'imageDigest': 'sha256:abcd1'}, {'imageDigest': 'sha256:abcd2'}], 'failures': []},
            {'imageIds': [{'imageDigest': 'sha256:efgh1'}], 'failures': []}
        ]

        mock_service = Mock()
        mock_service.list_repositories.return_value = repos
        mock_service.list_images.side_effect = [repo1_images, repo2_images]
        mock_service.ecr_client = mock_ecr_client
        mock_service_class.return_value = mock_service

        service = ECRPurgeService()
        result = service.purge_all_repositories()

        assert result.repositories_processed == 2
        assert result.total_images_deleted == 3
        assert result.total_images_failed == 0
        assert result.repositories_failed == 0
        assert result.overall_success is True
        assert len(result.success_results) == 2
        assert len(result.failed_results) == 0

    @patch('src.ecreshore.services.purge_service.ECRRepositoryService')
    def test_purge_all_repositories_dry_run(self, mock_service_class):
        """Test dry run of purge all repositories."""
        repos = [
            ECRRepository(
                name="repo1",
                uri="123456789012.dkr.ecr.us-east-1.amazonaws.com/repo1",
                created_at=datetime.now(timezone.utc),
                image_count=2,
                size_bytes=1024,
                registry_id="123456789012",
                region="us-east-1"
            )
        ]

        images = [
            ECRImage("repo1", ["tag1"], "sha256:abcd1", 1024, datetime.now(timezone.utc), "123456789012", "us-east-1"),
            ECRImage("repo1", ["tag2"], "sha256:abcd2", 1024, datetime.now(timezone.utc), "123456789012", "us-east-1")
        ]

        mock_service = Mock()
        mock_service.list_repositories.return_value = repos
        mock_service.list_images.return_value = images
        mock_service_class.return_value = mock_service

        service = ECRPurgeService()
        result = service.purge_all_repositories(dry_run=True)

        assert result.repositories_processed == 1
        assert result.total_images_deleted == 2  # Would delete
        assert result.total_images_failed == 0
        assert result.repositories_failed == 0
        assert result.overall_success is True

        # ECR client should not be called in dry run
        mock_service.list_images.assert_called_once()

    @patch('src.ecreshore.services.purge_service.ECRRepositoryService')
    def test_purge_all_repositories_with_filter(self, mock_service_class):
        """Test purge all with name filter."""
        repos = [
            ECRRepository(
                name="app-repo",
                uri="123456789012.dkr.ecr.us-east-1.amazonaws.com/app-repo",
                created_at=datetime.now(timezone.utc),
                image_count=1,
                size_bytes=1024,
                registry_id="123456789012",
                region="us-east-1"
            ),
            ECRRepository(
                name="other-repo",
                uri="123456789012.dkr.ecr.us-east-1.amazonaws.com/other-repo",
                created_at=datetime.now(timezone.utc),
                image_count=1,
                size_bytes=2048,
                registry_id="123456789012",
                region="us-east-1"
            )
        ]

        mock_service = Mock()
        # The name filter is applied by list_repositories, so we simulate that
        mock_service.list_repositories.return_value = [repos[0]]  # Only returns filtered results
        mock_service.list_images.return_value = []  # Empty for simplicity
        mock_service_class.return_value = mock_service

        service = ECRPurgeService()
        result = service.purge_all_repositories(name_filter="app")

        mock_service.list_repositories.assert_called_once_with(
            name_filter="app", max_results=1000
        )
        assert result.repositories_processed == 1

    @patch('src.ecreshore.services.purge_service.ECRRepositoryService')
    def test_purge_all_repositories_with_exclusions(self, mock_service_class):
        """Test purge all with excluded repositories."""
        repos = [
            ECRRepository(
                name="app-repo",
                uri="123456789012.dkr.ecr.us-east-1.amazonaws.com/app-repo",
                created_at=datetime.now(timezone.utc),
                image_count=1,
                size_bytes=1024,
                registry_id="123456789012",
                region="us-east-1"
            ),
            ECRRepository(
                name="important-repo",
                uri="123456789012.dkr.ecr.us-east-1.amazonaws.com/important-repo",
                created_at=datetime.now(timezone.utc),
                image_count=1,
                size_bytes=2048,
                registry_id="123456789012",
                region="us-east-1"
            )
        ]

        mock_service = Mock()
        mock_service.list_repositories.return_value = repos
        mock_service.list_images.return_value = []  # Empty for simplicity
        mock_service_class.return_value = mock_service

        service = ECRPurgeService()
        result = service.purge_all_repositories(exclude_repositories={"important-repo"})

        # Only app-repo should be processed
        assert result.repositories_processed == 1
        mock_service.list_images.assert_called_once_with("app-repo", max_results=10000)

    @patch('src.ecreshore.services.purge_service.ECRRepositoryService')
    def test_purge_service_error_handling(self, mock_service_class):
        """Test error handling in purge service."""
        mock_service = Mock()
        mock_service.list_repositories.side_effect = Exception("AWS error")
        mock_service_class.return_value = mock_service

        service = ECRPurgeService()
        
        with pytest.raises(ECRAuthenticationError) as exc_info:
            service.purge_all_repositories()
        
        assert "Purge operation failed" in str(exc_info.value)

    @patch('src.ecreshore.services.purge_service.ECRRepositoryService')
    def test_get_purge_preview_error_handling(self, mock_service_class):
        """Test error handling in get purge preview."""
        mock_service = Mock()
        mock_service.list_repositories.side_effect = Exception("AWS error")
        mock_service_class.return_value = mock_service

        service = ECRPurgeService()
        
        with pytest.raises(ECRAuthenticationError) as exc_info:
            service.get_purge_preview()
        
        assert "Preview failed" in str(exc_info.value)

    @patch('src.ecreshore.services.purge_service.ECRRepositoryService')
    def test_purge_repository_keep_latest(self, mock_service_class):
        """Test purging repository with keep_latest flag."""
        # Create test images with different push times
        older_image = ECRImage(
            repository_name="test-repo",
            image_tags=["old-tag"],
            image_digest="sha256:older123",
            size_bytes=1024,
            pushed_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
            registry_id="123456789012",
            region="us-east-1"
        )
        newer_image = ECRImage(
            repository_name="test-repo",
            image_tags=["latest"],
            image_digest="sha256:newer456",
            size_bytes=2048,
            pushed_at=datetime(2023, 12, 31, tzinfo=timezone.utc),
            registry_id="123456789012",
            region="us-east-1"
        )
        
        mock_ecr_client = Mock()
        mock_ecr_client.batch_delete_image.return_value = {
            'imageIds': [{'imageDigest': 'sha256:older123'}],
            'failures': []
        }

        mock_service = Mock()
        mock_service.list_images.return_value = [older_image, newer_image]
        mock_service.ecr_client = mock_ecr_client
        mock_service_class.return_value = mock_service

        service = ECRPurgeService()
        result = service.purge_repository("test-repo", keep_latest=True)

        assert result.repository_name == "test-repo"
        assert result.images_deleted == 1  # Only older image deleted
        assert result.images_kept == 1     # Newer image kept
        assert result.images_failed == 0
        assert result.success is True
        assert result.kept_latest is True

        # Verify only the older image was deleted
        mock_ecr_client.batch_delete_image.assert_called_once_with(
            repositoryName="test-repo",
            imageIds=[{'imageDigest': 'sha256:older123'}]
        )

    @patch('src.ecreshore.services.purge_service.ECRRepositoryService')
    def test_purge_repository_keep_latest_only_one_image(self, mock_service_class):
        """Test keep_latest with only one image - should keep it."""
        single_image = ECRImage(
            repository_name="test-repo",
            image_tags=["only-tag"],
            image_digest="sha256:only123",
            size_bytes=1024,
            pushed_at=datetime.now(timezone.utc),
            registry_id="123456789012",
            region="us-east-1"
        )

        mock_service = Mock()
        mock_service.list_images.return_value = [single_image]
        mock_service_class.return_value = mock_service

        service = ECRPurgeService()
        result = service.purge_repository("test-repo", keep_latest=True)

        assert result.repository_name == "test-repo"
        assert result.images_deleted == 0  # Nothing deleted
        assert result.images_kept == 1     # One image kept
        assert result.images_failed == 0
        assert result.success is True
        assert result.kept_latest is True

    @patch('src.ecreshore.services.purge_service.ECRRepositoryService')
    def test_purge_single_repository(self, mock_service_class):
        """Test main purge method with single repository."""
        images = [
            ECRImage("test-repo", ["tag1"], "sha256:abcd1", 1024, datetime.now(timezone.utc), "123456789012", "us-east-1")
        ]

        mock_ecr_client = Mock()
        mock_ecr_client.batch_delete_image.return_value = {
            'imageIds': [{'imageDigest': 'sha256:abcd1'}],
            'failures': []
        }

        mock_service = Mock()
        mock_service.list_images.return_value = images
        mock_service.ecr_client = mock_ecr_client
        mock_service_class.return_value = mock_service

        service = ECRPurgeService()
        result = service.purge(repository_name="test-repo")

        assert result.repositories_processed == 1
        assert result.total_images_deleted == 1
        assert result.total_images_kept == 0
        assert result.total_images_failed == 0
        assert result.repositories_failed == 0
        assert result.overall_success is True

    @patch('src.ecreshore.services.purge_service.ECRRepositoryService')
    def test_purge_validation_errors(self, mock_service_class):
        """Test purge method validation."""
        service = ECRPurgeService()
        
        # Test no repository name and not all
        with pytest.raises(ValueError, match="Must specify either repository_name or all_repositories=True"):
            service.purge()
        
        # Test both repository name and all
        with pytest.raises(ValueError, match="Cannot specify both repository_name and all_repositories=True"):
            service.purge(repository_name="test", all_repositories=True)

    @patch('src.ecreshore.services.purge_service.ECRRepositoryService')
    def test_purge_all_with_keep_latest(self, mock_service_class):
        """Test purge all repositories with keep_latest."""
        repos = [
            ECRRepository("repo1", "uri1", datetime.now(timezone.utc), 2, 1024, "123456789012", "us-east-1")
        ]

        images = [
            ECRImage("repo1", ["old"], "sha256:old", 1024, datetime(2023, 1, 1, tzinfo=timezone.utc), "123456789012", "us-east-1"),
            ECRImage("repo1", ["new"], "sha256:new", 1024, datetime(2023, 12, 31, tzinfo=timezone.utc), "123456789012", "us-east-1")
        ]

        mock_ecr_client = Mock()
        mock_ecr_client.batch_delete_image.return_value = {
            'imageIds': [{'imageDigest': 'sha256:old'}],
            'failures': []
        }

        mock_service = Mock()
        mock_service.list_repositories.return_value = repos
        mock_service.list_images.return_value = images
        mock_service.ecr_client = mock_ecr_client
        mock_service_class.return_value = mock_service

        service = ECRPurgeService()
        result = service.purge(all_repositories=True, keep_latest=True)

        assert result.repositories_processed == 1
        assert result.total_images_deleted == 1  # One deleted
        assert result.total_images_kept == 1     # One kept
        assert result.total_images_failed == 0
        assert result.overall_success is True


class TestPurgeDataClasses:
    """Test purge service data classes."""

    def test_purge_result_creation(self):
        """Test PurgeResult creation."""
        result = PurgeResult(
            repository_name="test-repo",
            images_deleted=5,
            images_kept=2,
            images_failed=1,
            success=False,
            kept_latest=True,
            error_message="Some error"
        )

        assert result.repository_name == "test-repo"
        assert result.images_deleted == 5
        assert result.images_kept == 2
        assert result.images_failed == 1
        assert result.success is False
        assert result.kept_latest is True
        assert result.error_message == "Some error"

    def test_purge_summary_overall_success(self):
        """Test PurgeSummary overall_success property."""
        # Test successful case
        success_summary = PurgeSummary(
            repositories_processed=2,
            total_images_deleted=10,
            total_images_kept=2,
            total_images_failed=0,
            repositories_failed=0,
            success_results=[],
            failed_results=[]
        )
        assert success_summary.overall_success is True

        # Test with failed images
        failed_images_summary = PurgeSummary(
            repositories_processed=2,
            total_images_deleted=8,
            total_images_kept=1,
            total_images_failed=2,
            repositories_failed=0,
            success_results=[],
            failed_results=[]
        )
        assert failed_images_summary.overall_success is False

        # Test with failed repositories
        failed_repos_summary = PurgeSummary(
            repositories_processed=2,
            total_images_deleted=5,
            total_images_kept=0,
            total_images_failed=0,
            repositories_failed=1,
            success_results=[],
            failed_results=[]
        )
        assert failed_repos_summary.overall_success is False