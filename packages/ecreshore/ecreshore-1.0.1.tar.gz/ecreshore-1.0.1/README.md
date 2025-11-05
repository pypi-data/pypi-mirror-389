# ECReshore - Container Image Migration Tool

ECReshore is a CLI tool for copying container images to AWS ECR registries with intelligent multi-architecture support and batch processing capabilities.

## Core Commands

### `copy` - Copy Single Images

Copy container images to ECR with automatic multi-architecture detection.

**Basic Usage:**
```bash
# Copy with automatic repository inference
ecreshore copy nginx:latest

# Copy with custom target repository
ecreshore copy nginx:latest my-nginx-repo

# Copy with specific platforms
ecreshore copy nginx:latest --platforms linux/amd64,linux/arm64

# Copy all architectures
ecreshore copy nginx:latest -A
```

**Key Features:**
- **Smart repository inference** - Automatically determines target repository name
- **Multi-architecture support** - Preserves all platforms when Docker Buildx available
- **Skip-if-present** - Automatically skips if target image already exists with matching content
- **Force override** - Use `--force` to transfer even if target exists

### `scan` - Kubernetes Cluster Scanning

Scan Kubernetes clusters to identify non-ECR container images.

**Basic Usage:**
```bash
# Scan current cluster and generate batch config
ecreshore scan --export batch-config.yaml

# Scan specific namespace
ecreshore scan -n production

# Scan all namespaces
ecreshore scan -A

# Generate report format
ecreshore scan --output report
```

**Key Features:**
- **Workload discovery** - Scans Deployments, DaemonSets, StatefulSets, Jobs, CronJobs, Pods
- **ECR filtering** - Only identifies non-ECR images that need migration
- **Batch config generation** - Creates ready-to-use configuration files
- **Namespace targeting** - Include/exclude specific namespaces

### `batch` - Batch Processing

Execute multiple image transfers from YAML configuration files.

**Basic Usage:**
```bash
# Execute batch transfers
ecreshore batch config.yaml

# Preview without executing
ecreshore batch config.yaml --dry-run

# Force rich UI display
ecreshore batch config.yaml --rich

# Output structured logs
ecreshore batch config.yaml --output log
```

**Configuration Format:**
```yaml
settings:
  concurrent_transfers: 3    # Parallel transfers
  retry_attempts: 3          # Retry attempts per transfer
  verify_digests: true       # Verify image integrity
  region: us-east-2         # AWS region

transfers:
  - source: nginx:latest
    target: my-nginx
    source_tag: latest
    target_tag: latest
```

**Key Features:**
- **Concurrent processing** - Configurable parallel transfers (default: 3)
- **Progress tracking** - Rich UI with real-time transfer status
- **Error handling** - Automatic retries with configurable attempts
- **Skip detection** - Automatically skips existing images with matching content

### `purge` - Repository Cleanup

Remove images from ECR repositories with safety controls.

**Basic Usage:**
```bash
# Preview deletion for specific repository
ecreshore purge my-repo --dry-run

# Purge repository, keeping latest image
ecreshore purge my-repo --keep-latest

# Preview deletion for all repositories
ecreshore purge -A --dry-run

# Purge with pattern matching
ecreshore purge -A --filter my-app-* --keep-latest
```

**Key Features:**
- **Safety first** - Always use `--dry-run` to preview deletions
- **Selective deletion** - Target specific repositories or use patterns
- **Latest preservation** - `--keep-latest` protects most recent images
- **Bulk operations** - Process all repositories with filtering options

## Common Workflow

1. **Discovery**: Scan your cluster to identify images needing migration
   ```bash
   ecreshore scan --export migration-plan.yaml
   ```

2. **Preview**: Review the generated configuration and preview the batch operation
   ```bash
   ecreshore batch migration-plan.yaml --dry-run
   ```

3. **Execute**: Run the batch migration
   ```bash
   ecreshore batch migration-plan.yaml
   ```

4. **Cleanup**: Optionally purge old/unused images
   ```bash
   ecreshore purge old-repo --dry-run
   ecreshore purge old-repo --keep-latest
   ```

## Global Options

- **`-v, --verbose`** - Increase verbosity (`-v` for INFO, `-vv` for DEBUG)
- **`--region`** - AWS region (respects `AWS_DEFAULT_REGION`, `AWS_REGION`, `~/.aws/config`)
- **`--registry-id`** - AWS account ID for ECR registry
- **`--simple/--rich`** - Force specific UI modes (auto-detected by default)

## UI Modes

ECReshore automatically detects your terminal capabilities and chooses the best display mode:

- **Rich UI** - Full-featured progress bars, colors, and real-time updates
- **Simple UI** - Text-based progress suitable for basic terminals
- **Log output** - Structured JSON logs for automation and monitoring

Use `ecreshore terminal-info` to see your terminal's detected capabilities.

## Authentication

ECReshore uses your existing AWS credentials. Ensure you have:
- AWS CLI configured (`aws configure`)
- Appropriate ECR permissions (`ecr:*` or specific ECR actions)
- Docker daemon running for image operations

Test authentication with:
```bash
ecreshore auth-test
```

---

For additional commands and advanced options, run `ecreshore --help` or `ecreshore COMMAND --help`.
