"""Cluster scanning and inspection commands module.

This module contains commands for Kubernetes cluster operations:

- **scan**: Scan Kubernetes cluster for non-ECR container images
  - Supports namespace filtering and exclusions
  - Multiple output formats (report, JSON, YAML, batch-config)
  - Export capabilities to files
  - Detailed workload analysis and image usage reporting

- **inspect**: Inspect container image architecture information
  - Multi-architecture image support
  - Platform details (OS, architecture, variant)
  - Multiple output formats (table, JSON, platforms)

The scan command is particularly complex and has been broken down into:
- scan.py: Main command interface
- scan_helpers.py: Utility functions for initialization and validation
- scan_formatters.py: Output formatting and display functions
"""
