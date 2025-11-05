"""Tests for batch configuration service."""

import pytest
import yaml
from pathlib import Path
from tempfile import NamedTemporaryFile

from src.ecreshore.services.batch_config import (
    BatchConfigService,
    BatchRequest,
    BatchTransferRequest, 
    BatchSettings,
    DEFAULT_CONCURRENT_TRANSFERS,
    DEFAULT_RETRY_ATTEMPTS,
    DEFAULT_VERIFY_DIGESTS
)
from src.ecreshore.services.error_handler import ConfigurationError


class TestBatchTransferRequest:
    """Tests for BatchTransferRequest dataclass."""
    
    def test_basic_transfer_request(self):
        """Test basic transfer request creation."""
        request = BatchTransferRequest(source="nginx", target="my-nginx")
        
        assert request.source == "nginx"
        assert request.target == "my-nginx"
        assert request.source_tag == "latest"
        assert request.target_tag == "latest"
        assert request.verify_digest is None
    
    def test_transfer_request_with_tags(self):
        """Test transfer request with explicit tags."""
        request = BatchTransferRequest(
            source="nginx",
            target="my-nginx",
            source_tag="1.21",
            target_tag="stable"
        )
        
        assert request.source == "nginx"
        assert request.target == "my-nginx"
        assert request.source_tag == "1.21"
        assert request.target_tag == "stable"
    
    def test_transfer_request_colon_notation_source(self):
        """Test source image with colon notation."""
        request = BatchTransferRequest(source="nginx:1.21", target="my-nginx")
        
        assert request.source == "nginx"
        assert request.source_tag == "1.21"
        assert request.target == "my-nginx"
        assert request.target_tag == "1.21"
    
    def test_transfer_request_colon_notation_both(self):
        """Test both source and target with colon notation."""
        request = BatchTransferRequest(source="nginx:1.21", target="my-nginx:stable")
        
        assert request.source == "nginx"
        assert request.source_tag == "1.21"
        assert request.target == "my-nginx"
        assert request.target_tag == "stable"
    
    def test_transfer_request_explicit_tag_overrides_colon(self):
        """Test explicit tags override colon notation."""
        request = BatchTransferRequest(
            source="nginx:1.21",
            target="my-nginx:stable",
            source_tag="1.20",
            target_tag="production"
        )
        
        # When explicit tags are provided, colon notation is ignored
        assert request.source == "nginx:1.21"  # colon notation ignored for source
        assert request.source_tag == "1.20"  # explicit tag used
        assert request.target == "my-nginx:stable"  # colon notation ignored for target
        assert request.target_tag == "production"  # explicit tag used


class TestBatchSettings:
    """Tests for BatchSettings dataclass."""
    
    def test_default_settings(self):
        """Test default settings values."""
        settings = BatchSettings()
        
        assert settings.concurrent_transfers == DEFAULT_CONCURRENT_TRANSFERS
        assert settings.retry_attempts == DEFAULT_RETRY_ATTEMPTS
        assert settings.verify_digests == DEFAULT_VERIFY_DIGESTS
        assert settings.region is None
        assert settings.registry_id is None
    
    def test_custom_settings(self):
        """Test custom settings values."""
        settings = BatchSettings(
            concurrent_transfers=5,
            retry_attempts=10,
            verify_digests=False,
            region="us-west-2",
            registry_id="123456789012"
        )
        
        assert settings.concurrent_transfers == 5
        assert settings.retry_attempts == 10
        assert settings.verify_digests is False
        assert settings.region == "us-west-2"
        assert settings.registry_id == "123456789012"


class TestBatchRequest:
    """Tests for BatchRequest dataclass."""
    
    def test_valid_batch_request(self):
        """Test valid batch request creation."""
        transfers = [
            BatchTransferRequest(source="nginx", target="my-nginx"),
            BatchTransferRequest(source="redis", target="my-redis")
        ]
        
        batch = BatchRequest(transfers=transfers)
        
        assert len(batch.transfers) == 2
        assert isinstance(batch.settings, BatchSettings)
        assert batch.settings.concurrent_transfers == DEFAULT_CONCURRENT_TRANSFERS
    
    def test_batch_request_with_settings(self):
        """Test batch request with custom settings."""
        transfers = [BatchTransferRequest(source="nginx", target="my-nginx")]
        settings = BatchSettings(concurrent_transfers=5)
        
        batch = BatchRequest(transfers=transfers, settings=settings)
        
        assert len(batch.transfers) == 1
        assert batch.settings.concurrent_transfers == 5
    
    def test_empty_transfers_validation(self):
        """Test validation fails for empty transfers list."""
        with pytest.raises(ConfigurationError, match="must contain at least one transfer"):
            BatchRequest(transfers=[])
    
    def test_invalid_concurrent_transfers_validation(self):
        """Test validation fails for invalid concurrent_transfers."""
        transfers = [BatchTransferRequest(source="nginx", target="my-nginx")]
        settings = BatchSettings(concurrent_transfers=0)
        
        with pytest.raises(ConfigurationError, match="concurrent_transfers must be at least 1"):
            BatchRequest(transfers=transfers, settings=settings)
    
    def test_invalid_retry_attempts_validation(self):
        """Test validation fails for negative retry_attempts."""
        transfers = [BatchTransferRequest(source="nginx", target="my-nginx")]
        settings = BatchSettings(retry_attempts=-1)
        
        with pytest.raises(ConfigurationError, match="retry_attempts must be non-negative"):
            BatchRequest(transfers=transfers, settings=settings)


class TestBatchConfigService:
    """Tests for BatchConfigService."""
    
    def test_load_from_string_basic(self):
        """Test loading basic configuration from YAML string."""
        yaml_config = """
        transfers:
          - source: nginx
            target: my-nginx
          - source: redis
            target: my-redis
        """
        
        batch = BatchConfigService.load_from_string(yaml_config)
        
        assert len(batch.transfers) == 2
        assert batch.transfers[0].source == "nginx"
        assert batch.transfers[0].target == "my-nginx"
        assert batch.transfers[1].source == "redis"
        assert batch.transfers[1].target == "my-redis"
    
    def test_load_from_string_with_settings(self):
        """Test loading configuration with settings."""
        yaml_config = """
        transfers:
          - source: nginx
            target: my-nginx
        settings:
          concurrent_transfers: 5
          retry_attempts: 10
          verify_digests: false
          region: us-west-2
          registry_id: "123456789012"
        """
        
        batch = BatchConfigService.load_from_string(yaml_config)
        
        assert len(batch.transfers) == 1
        assert batch.settings.concurrent_transfers == 5
        assert batch.settings.retry_attempts == 10
        assert batch.settings.verify_digests is False
        assert batch.settings.region == "us-west-2"
        assert batch.settings.registry_id == "123456789012"
    
    def test_load_from_string_with_tags(self):
        """Test loading configuration with explicit tags."""
        yaml_config = """
        transfers:
          - source: nginx
            source_tag: "1.21"
            target: my-nginx
            target_tag: stable
            verify_digest: false
        """
        
        batch = BatchConfigService.load_from_string(yaml_config)
        
        assert len(batch.transfers) == 1
        transfer = batch.transfers[0]
        assert transfer.source == "nginx"
        assert transfer.source_tag == "1.21"
        assert transfer.target == "my-nginx"
        assert transfer.target_tag == "stable"
        assert transfer.verify_digest is False
    
    def test_load_from_string_colon_notation(self):
        """Test loading configuration with colon notation."""
        yaml_config = """
        transfers:
          - source: nginx:1.21
            target: my-nginx:stable
        """
        
        batch = BatchConfigService.load_from_string(yaml_config)
        
        assert len(batch.transfers) == 1
        transfer = batch.transfers[0]
        assert transfer.source == "nginx"
        assert transfer.source_tag == "1.21"
        assert transfer.target == "my-nginx"
        assert transfer.target_tag == "stable"
    
    def test_load_from_file(self):
        """Test loading configuration from file."""
        yaml_content = """
        transfers:
          - source: nginx
            target: my-nginx
        settings:
          concurrent_transfers: 2
        """
        
        with NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            try:
                batch = BatchConfigService.load_from_file(f.name)
                
                assert len(batch.transfers) == 1
                assert batch.settings.concurrent_transfers == 2
            finally:
                Path(f.name).unlink()
    
    def test_load_from_nonexistent_file(self):
        """Test loading from nonexistent file raises error."""
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            BatchConfigService.load_from_file("/nonexistent/file.yml")
    
    def test_invalid_yaml_format(self):
        """Test invalid YAML format raises error."""
        invalid_yaml = """
        transfers:
          - source: nginx
            target: my-nginx
          invalid: [unclosed list
        """
        
        with pytest.raises(ConfigurationError, match="Invalid YAML format"):
            BatchConfigService.load_from_string(invalid_yaml)
    
    def test_non_dict_yaml(self):
        """Test non-dictionary YAML raises error."""
        invalid_yaml = """
        - just a list
        - not a dict
        """
        
        with pytest.raises(ConfigurationError, match="must be a YAML object/dictionary"):
            BatchConfigService.load_from_string(invalid_yaml)
    
    def test_missing_transfers(self):
        """Test missing transfers section raises error."""
        yaml_config = """
        settings:
          concurrent_transfers: 5
        """
        
        with pytest.raises(ConfigurationError, match="'transfers' list cannot be empty"):
            BatchConfigService.load_from_string(yaml_config)
    
    def test_empty_transfers_list(self):
        """Test empty transfers list raises error."""
        yaml_config = """
        transfers: []
        """
        
        with pytest.raises(ConfigurationError, match="'transfers' list cannot be empty"):
            BatchConfigService.load_from_string(yaml_config)
    
    def test_transfers_not_list(self):
        """Test transfers not being a list raises error."""
        yaml_config = """
        transfers:
          source: nginx
          target: my-nginx
        """
        
        with pytest.raises(ConfigurationError, match="'transfers' must be a list"):
            BatchConfigService.load_from_string(yaml_config)
    
    def test_transfer_missing_source(self):
        """Test transfer missing source field raises error."""
        yaml_config = """
        transfers:
          - target: my-nginx
        """
        
        with pytest.raises(ConfigurationError, match="Invalid transfer 0.*Missing required field 'source'"):
            BatchConfigService.load_from_string(yaml_config)
    
    def test_transfer_missing_target(self):
        """Test transfer missing target field raises error."""
        yaml_config = """
        transfers:
          - source: nginx
        """
        
        with pytest.raises(ConfigurationError, match="Invalid transfer 0.*Missing required field 'target'"):
            BatchConfigService.load_from_string(yaml_config)
    
    def test_transfer_empty_source(self):
        """Test transfer with empty source raises error."""
        yaml_config = """
        transfers:
          - source: ""
            target: my-nginx
        """
        
        with pytest.raises(ConfigurationError, match="Invalid transfer 0.*Field 'source' cannot be empty"):
            BatchConfigService.load_from_string(yaml_config)
    
    def test_transfer_non_string_source_tag(self):
        """Test transfer with non-string source_tag raises error."""
        yaml_config = """
        transfers:
          - source: nginx
            target: my-nginx
            source_tag: 123
        """
        
        with pytest.raises(ConfigurationError, match="Invalid transfer 0.*'source_tag' must be a string"):
            BatchConfigService.load_from_string(yaml_config)
    
    def test_transfer_non_boolean_verify_digest(self):
        """Test transfer with non-boolean verify_digest raises error."""
        yaml_config = """
        transfers:
          - source: nginx
            target: my-nginx
            verify_digest: "yes"
        """
        
        with pytest.raises(ConfigurationError, match="Invalid transfer 0.*'verify_digest' must be a boolean"):
            BatchConfigService.load_from_string(yaml_config)
    
    def test_settings_not_dict(self):
        """Test settings not being a dictionary raises error."""
        yaml_config = """
        transfers:
          - source: nginx
            target: my-nginx
        settings: "invalid"
        """
        
        with pytest.raises(ConfigurationError, match="'settings' must be an object"):
            BatchConfigService.load_from_string(yaml_config)
    
    def test_settings_invalid_concurrent_transfers(self):
        """Test settings with invalid concurrent_transfers raises error."""
        yaml_config = """
        transfers:
          - source: nginx
            target: my-nginx
        settings:
          concurrent_transfers: "not a number"
        """
        
        with pytest.raises(ConfigurationError, match="'concurrent_transfers' must be an integer"):
            BatchConfigService.load_from_string(yaml_config)
    
    def test_settings_invalid_retry_attempts(self):
        """Test settings with invalid retry_attempts raises error."""
        yaml_config = """
        transfers:
          - source: nginx
            target: my-nginx
        settings:
          retry_attempts: 3.5
        """
        
        with pytest.raises(ConfigurationError, match="'retry_attempts' must be an integer"):
            BatchConfigService.load_from_string(yaml_config)
    
    def test_settings_invalid_verify_digests(self):
        """Test settings with invalid verify_digests raises error."""
        yaml_config = """
        transfers:
          - source: nginx
            target: my-nginx
        settings:
          verify_digests: "true"
        """
        
        with pytest.raises(ConfigurationError, match="'verify_digests' must be a boolean"):
            BatchConfigService.load_from_string(yaml_config)
    
    def test_settings_invalid_region(self):
        """Test settings with invalid region raises error."""
        yaml_config = """
        transfers:
          - source: nginx
            target: my-nginx
        settings:
          region: 123
        """
        
        with pytest.raises(ConfigurationError, match="'region' must be a string"):
            BatchConfigService.load_from_string(yaml_config)
    
    def test_validate_config_schema_valid(self):
        """Test schema validation for valid configuration."""
        yaml_content = """
        transfers:
          - source: nginx
            target: my-nginx
        """
        
        with NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            try:
                assert BatchConfigService.validate_config_schema(f.name) is True
            finally:
                Path(f.name).unlink()
    
    def test_validate_config_schema_invalid(self):
        """Test schema validation for invalid configuration."""
        yaml_content = """
        transfers: []
        """
        
        with NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            try:
                with pytest.raises(ConfigurationError):
                    BatchConfigService.validate_config_schema(f.name)
            finally:
                Path(f.name).unlink()
    
    def test_generate_example_config(self):
        """Test generating example configuration."""
        example = BatchConfigService.generate_example_config()
        
        assert isinstance(example, str)
        assert "transfers:" in example
        assert "settings:" in example
        assert "nginx" in example
        assert "concurrent_transfers" in example
        
        # Ensure generated example is valid YAML
        parsed = yaml.safe_load(example)
        assert isinstance(parsed, dict)
        assert "transfers" in parsed
        assert "settings" in parsed
        
        # Ensure generated example is valid configuration
        batch = BatchConfigService.load_from_string(example)
        assert len(batch.transfers) > 0
    
    def test_complex_configuration(self):
        """Test loading complex configuration with all features."""
        yaml_config = """
        transfers:
          # Basic transfer
          - source: nginx
            target: my-nginx
          
          # Transfer with tags
          - source: redis
            source_tag: "6.2"
            target: my-redis
            target_tag: stable
          
          # Transfer with colon notation
          - source: postgres:13
            target: my-postgres:production
          
          # Transfer with custom verification
          - source: alpine
            target: my-alpine
            verify_digest: false

        settings:
          concurrent_transfers: 4
          retry_attempts: 5
          verify_digests: true
          region: eu-west-1
          registry_id: "987654321098"
        """
        
        batch = BatchConfigService.load_from_string(yaml_config)
        
        # Verify transfers
        assert len(batch.transfers) == 4
        
        # Basic transfer
        assert batch.transfers[0].source == "nginx"
        assert batch.transfers[0].target == "my-nginx"
        assert batch.transfers[0].source_tag == "latest"
        assert batch.transfers[0].target_tag == "latest"
        
        # Transfer with tags
        assert batch.transfers[1].source == "redis"
        assert batch.transfers[1].source_tag == "6.2"
        assert batch.transfers[1].target == "my-redis"
        assert batch.transfers[1].target_tag == "stable"
        
        # Transfer with colon notation
        assert batch.transfers[2].source == "postgres"
        assert batch.transfers[2].source_tag == "13"
        assert batch.transfers[2].target == "my-postgres"
        assert batch.transfers[2].target_tag == "production"
        
        # Transfer with custom verification
        assert batch.transfers[3].source == "alpine"
        assert batch.transfers[3].target == "my-alpine"
        assert batch.transfers[3].verify_digest is False
        
        # Verify settings
        assert batch.settings.concurrent_transfers == 4
        assert batch.settings.retry_attempts == 5
        assert batch.settings.verify_digests is True
        assert batch.settings.region == "eu-west-1"
        assert batch.settings.registry_id == "987654321098"


def test_import_paths():
    """Test that all imports work correctly."""
    from src.ecreshore.services.batch_config import BatchConfigService
    from src.ecreshore.services.error_handler import ConfigurationError
    
    assert BatchConfigService is not None
    assert ConfigurationError is not None