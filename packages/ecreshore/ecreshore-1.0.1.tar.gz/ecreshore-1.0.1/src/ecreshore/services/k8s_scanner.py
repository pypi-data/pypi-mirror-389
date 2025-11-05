"""Kubernetes cluster scanner for identifying non-ECR container images."""

import logging
from datetime import datetime
from typing import List, Optional

from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

from .k8s_models import ClusterScanResult, WorkloadImageInfo, ImageReference

logger = logging.getLogger(__name__)


class KubernetesImageExtractor:
    """Extracts container images from Kubernetes workload objects."""

    # Define extraction paths for each workload type
    WORKLOAD_IMAGE_PATHS = {
        "Deployment": [
            "spec.template.spec.containers",
            "spec.template.spec.initContainers",
            "spec.template.spec.ephemeralContainers",
        ],
        "DaemonSet": [
            "spec.template.spec.containers",
            "spec.template.spec.initContainers",
            "spec.template.spec.ephemeralContainers",
        ],
        "StatefulSet": [
            "spec.template.spec.containers",
            "spec.template.spec.initContainers",
            "spec.template.spec.ephemeralContainers",
        ],
        "Job": [
            "spec.template.spec.containers",
            "spec.template.spec.initContainers",
            "spec.template.spec.ephemeralContainers",
        ],
        "CronJob": [
            "spec.jobTemplate.spec.template.spec.containers",
            "spec.jobTemplate.spec.template.spec.initContainers",
            "spec.jobTemplate.spec.template.spec.ephemeralContainers",
        ],
        "Pod": ["spec.containers", "spec.initContainers", "spec.ephemeralContainers"],
    }

    def extract_images_from_workload(
        self, workload_obj, workload_type: str
    ) -> List[ImageReference]:
        """Extract all image references from a workload object."""
        images = []
        paths = self.WORKLOAD_IMAGE_PATHS.get(workload_type, [])

        for path in paths:
            containers = self._get_nested_attribute(workload_obj, path)
            if containers:
                for container in containers:
                    if hasattr(container, "image") and container.image:
                        images.append(ImageReference.parse(container.image))

        return images

    def _get_nested_attribute(self, obj, path: str):
        """Get nested attribute using dot notation path."""
        try:
            current = obj
            for part in path.split("."):
                if part.endswith("[]"):
                    # Handle array notation
                    attr_name = part[:-2]
                    current = getattr(current, attr_name, None)
                    break
                else:
                    current = getattr(current, part, None)
                    if current is None:
                        return None
            return current
        except (AttributeError, TypeError):
            return None


class KubernetesClusterScanner:
    """Main service for scanning Kubernetes clusters for non-ECR images."""

    DEFAULT_EXCLUDE_NAMESPACES = ["kube-system", "kube-public", "kube-node-lease"]

    def __init__(self):
        """Initialize the scanner with Kubernetes configuration."""
        self.image_extractor = KubernetesImageExtractor()
        self._setup_k8s_client()

    def _setup_k8s_client(self):
        """Setup Kubernetes client configuration."""
        try:
            # Try in-cluster config first, then default kubeconfig
            try:
                config.load_incluster_config()
                logger.debug("Using in-cluster Kubernetes configuration")
            except config.ConfigException:
                config.load_kube_config()
                logger.debug("Using kubeconfig file")

            self.apps_v1 = client.AppsV1Api()
            self.batch_v1 = client.BatchV1Api()
            self.core_v1 = client.CoreV1Api()

        except Exception as e:
            raise RuntimeError(f"Failed to setup Kubernetes client: {e}")

    def scan_cluster(
        self,
        namespaces: Optional[List[str]] = None,
        exclude_namespaces: Optional[List[str]] = None,
    ) -> ClusterScanResult:
        """Scan the cluster for workloads with non-ECR images."""

        if exclude_namespaces is None:
            exclude_namespaces = self.DEFAULT_EXCLUDE_NAMESPACES

        # Get target namespaces
        target_namespaces = self._get_target_namespaces(namespaces, exclude_namespaces)
        logger.info(f"Scanning {len(target_namespaces)} namespaces")

        # Generator-based workload scanning for memory efficiency
        def scan_all_workloads():
            """Generator that yields workloads from all namespaces and types."""
            for namespace in target_namespaces:
                logger.debug(f"Scanning namespace: {namespace}")
                # Yield workloads from each type as they're found
                yield from self._scan_deployments(namespace)
                yield from self._scan_daemonsets(namespace)
                yield from self._scan_statefulsets(namespace)
                yield from self._scan_jobs(namespace)
                yield from self._scan_cronjobs(namespace)
                yield from self._scan_pods(namespace)

        # Process workloads as generator - only materialize non-ECR ones
        workload_details = list(scan_all_workloads())
        workloads_with_non_ecr = [w for w in workload_details if w.non_ecr_images]

        return ClusterScanResult(
            cluster_name=self._get_cluster_name(),
            scan_timestamp=datetime.now(),
            total_workloads_scanned=len(workload_details),
            workloads_with_non_ecr_images=len(workloads_with_non_ecr),
            total_unique_non_ecr_images=0,  # Calculated in __post_init__
            workload_details=workloads_with_non_ecr,
        )

    def _get_target_namespaces(
        self, include_namespaces: Optional[List[str]], exclude_namespaces: List[str]
    ) -> List[str]:
        """Get list of namespaces to scan."""
        if include_namespaces:
            return include_namespaces

        # Get all namespaces and filter
        all_namespaces = self.core_v1.list_namespace()
        namespace_names = [ns.metadata.name for ns in all_namespaces.items]

        return [ns for ns in namespace_names if ns not in exclude_namespaces]

    def _scan_deployments(self, namespace: str) -> List[WorkloadImageInfo]:
        """Scan Deployments in a namespace."""
        try:
            deployments = self.apps_v1.list_namespaced_deployment(namespace)
            # Generator expression for memory efficiency - only materialize workloads with images
            return [
                WorkloadImageInfo(
                    name=deployment.metadata.name,
                    namespace=deployment.metadata.namespace,
                    workload_type="Deployment",
                    labels=deployment.metadata.labels or {},
                    annotations=deployment.metadata.annotations or {},
                    images=images,
                )
                for deployment in deployments.items
                for images in [
                    self.image_extractor.extract_images_from_workload(
                        deployment, "Deployment"
                    )
                ]
                if images  # Only include if it has images
            ]
        except ApiException as e:
            logger.warning(f"Error scanning Deployments in {namespace}: {e}")
            return []

    def _scan_daemonsets(self, namespace: str) -> List[WorkloadImageInfo]:
        """Scan DaemonSets in a namespace."""
        try:
            daemonsets = self.apps_v1.list_namespaced_daemon_set(namespace)
            return [
                WorkloadImageInfo(
                    name=daemonset.metadata.name,
                    namespace=daemonset.metadata.namespace,
                    workload_type="DaemonSet",
                    labels=daemonset.metadata.labels or {},
                    annotations=daemonset.metadata.annotations or {},
                    images=images,
                )
                for daemonset in daemonsets.items
                for images in [
                    self.image_extractor.extract_images_from_workload(
                        daemonset, "DaemonSet"
                    )
                ]
                if images
            ]
        except ApiException as e:
            logger.warning(f"Error scanning DaemonSets in {namespace}: {e}")
            return []

    def _scan_statefulsets(self, namespace: str) -> List[WorkloadImageInfo]:
        """Scan StatefulSets in a namespace."""
        try:
            statefulsets = self.apps_v1.list_namespaced_stateful_set(namespace)
            return [
                WorkloadImageInfo(
                    name=statefulset.metadata.name,
                    namespace=statefulset.metadata.namespace,
                    workload_type="StatefulSet",
                    labels=statefulset.metadata.labels or {},
                    annotations=statefulset.metadata.annotations or {},
                    images=images,
                )
                for statefulset in statefulsets.items
                for images in [
                    self.image_extractor.extract_images_from_workload(
                        statefulset, "StatefulSet"
                    )
                ]
                if images
            ]
        except ApiException as e:
            logger.warning(f"Error scanning StatefulSets in {namespace}: {e}")
            return []

    def _scan_jobs(self, namespace: str) -> List[WorkloadImageInfo]:
        """Scan Jobs in a namespace."""
        try:
            jobs = self.batch_v1.list_namespaced_job(namespace)
            return [
                WorkloadImageInfo(
                    name=job.metadata.name,
                    namespace=job.metadata.namespace,
                    workload_type="Job",
                    labels=job.metadata.labels or {},
                    annotations=job.metadata.annotations or {},
                    images=images,
                )
                for job in jobs.items
                for images in [
                    self.image_extractor.extract_images_from_workload(job, "Job")
                ]
                if images
            ]
        except ApiException as e:
            logger.warning(f"Error scanning Jobs in {namespace}: {e}")
            return []

    def _scan_cronjobs(self, namespace: str) -> List[WorkloadImageInfo]:
        """Scan CronJobs in a namespace."""
        try:
            cronjobs = self.batch_v1.list_namespaced_cron_job(namespace)
            return [
                WorkloadImageInfo(
                    name=cronjob.metadata.name,
                    namespace=cronjob.metadata.namespace,
                    workload_type="CronJob",
                    labels=cronjob.metadata.labels or {},
                    annotations=cronjob.metadata.annotations or {},
                    images=images,
                )
                for cronjob in cronjobs.items
                for images in [
                    self.image_extractor.extract_images_from_workload(
                        cronjob, "CronJob"
                    )
                ]
                if images
            ]
        except ApiException as e:
            logger.warning(f"Error scanning CronJobs in {namespace}: {e}")
            return []

    def _scan_pods(self, namespace: str) -> List[WorkloadImageInfo]:
        """Scan standalone Pods (not managed by other controllers)."""
        try:
            pods = self.core_v1.list_namespaced_pod(namespace)
            return [
                WorkloadImageInfo(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                    workload_type="Pod",
                    labels=pod.metadata.labels or {},
                    annotations=pod.metadata.annotations or {},
                    images=images,
                )
                for pod in pods.items
                if not self._is_pod_managed_by_controller(pod)
                for images in [
                    self.image_extractor.extract_images_from_workload(pod, "Pod")
                ]
                if images
            ]
        except ApiException as e:
            logger.warning(f"Error scanning Pods in {namespace}: {e}")
            return []

    def _is_pod_managed_by_controller(self, pod) -> bool:
        """Check if pod is managed by a controller (Deployment, ReplicaSet, etc)."""
        if not pod.metadata.owner_references:
            return False

        managed_kinds = {"ReplicaSet", "DaemonSet", "StatefulSet", "Job", "CronJob"}

        for owner_ref in pod.metadata.owner_references:
            if owner_ref.kind in managed_kinds:
                return True

        return False

    def _get_cluster_name(self) -> Optional[str]:
        """Attempt to get cluster name from context."""
        try:
            contexts, current_context = config.list_kube_config_contexts()
            if current_context:
                return current_context["name"]
        except Exception:
            pass
        return None
