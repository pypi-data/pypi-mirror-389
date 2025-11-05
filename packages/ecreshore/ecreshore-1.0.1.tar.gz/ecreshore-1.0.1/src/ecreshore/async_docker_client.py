"""Async Docker client wrapper for container image operations using aiodocker."""

import base64
import json
import logging
from pathlib import Path
from typing import Dict, AsyncGenerator, List, Optional

import aiodocker
from aiodocker.exceptions import DockerError

logger = logging.getLogger(__name__)


class AsyncDockerClientError(Exception):
    """Raised when async Docker operations fail."""

    pass


class AsyncDockerImageClient:
    """Async wrapper for Docker client with image-specific operations using aiodocker."""

    def __init__(self):
        """Initialize async Docker client."""
        self._docker: Optional[aiodocker.Docker] = None
        self._docker_config: Optional[Dict] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._docker = aiodocker.Docker()
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Async context manager exit."""
        if self._docker:
            await self._docker.close()

    @property
    def docker(self) -> aiodocker.Docker:
        """Get Docker client instance."""
        if self._docker is None:
            raise AsyncDockerClientError(
                "Docker client not initialized. Use async context manager."
            )
        return self._docker

    def _load_docker_config(self) -> Dict:
        """Load Docker configuration from ~/.docker/config.json.

        Returns:
            Docker configuration dictionary
        """
        if self._docker_config is not None:
            return self._docker_config

        config_path = Path.home() / ".docker" / "config.json"
        if not config_path.exists():
            logger.debug("No Docker config file found at ~/.docker/config.json")
            self._docker_config = {}
            return self._docker_config

        try:
            with open(config_path, "r") as f:
                self._docker_config = json.load(f)
                logger.debug(f"Loaded Docker config from {config_path}")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load Docker config from {config_path}: {e}")
            self._docker_config = {}

        return self._docker_config

    def _get_registry_auth(self, registry_host: str) -> Optional[Dict[str, str]]:
        """Get authentication credentials for a registry.

        Args:
            registry_host: Registry hostname (e.g., 'registry.revsys.com')

        Returns:
            Auth config dict with username/password, or None if no auth found
        """
        config = self._load_docker_config()
        auths = config.get("auths", {})

        # Try exact match first
        if registry_host in auths:
            auth_data = auths[registry_host]
        # Try with https:// prefix
        elif f"https://{registry_host}" in auths:
            auth_data = auths[f"https://{registry_host}"]
        # Try with different common variations
        elif f"{registry_host}/v2/" in auths:
            auth_data = auths[f"{registry_host}/v2/"]
        else:
            logger.debug(f"No auth found for registry {registry_host}")
            return None

        # Extract auth token
        if "auth" in auth_data:
            try:
                # Decode base64 auth token
                auth_token = auth_data["auth"]
                decoded = base64.b64decode(auth_token).decode("utf-8")
                if ":" in decoded:
                    username, password = decoded.split(":", 1)
                    logger.debug(f"Found auth credentials for {registry_host}")
                    return {"username": username, "password": password}
            except Exception as e:
                logger.warning(f"Failed to decode auth token for {registry_host}: {e}")

        return None

    def _extract_registry_host(self, repository: str) -> str:
        """Extract registry hostname from repository string.

        Args:
            repository: Repository string (e.g., 'registry.revsys.com/images/misc')

        Returns:
            Registry hostname
        """
        # If no slash, assume Docker Hub
        if "/" not in repository:
            return "index.docker.io"

        # If only one slash and no dots, assume Docker Hub (e.g., 'nginx/nginx')
        parts = repository.split("/")
        if len(parts) == 2 and "." not in parts[0]:
            return "index.docker.io"

        # Otherwise, first part is the registry
        return parts[0]

    async def pull_image(self, repository: str, tag: str = "latest") -> str:
        """Pull image from registry asynchronously.

        Args:
            repository: Image repository name
            tag: Image tag

        Returns:
            Image ID of pulled image

        Raises:
            AsyncDockerClientError: If pull operation fails
        """
        image_name = f"{repository}:{tag}"

        try:
            logger.info(f"Pulling image: {image_name}")

            # Get authentication for the registry if available
            registry_host = self._extract_registry_host(repository)
            auth_config = self._get_registry_auth(registry_host)

            if auth_config:
                logger.debug(f"Using stored credentials for {registry_host}")
            else:
                logger.debug(f"No stored credentials found for {registry_host}")

            image_data = await self.docker.images.pull(
                from_image=repository, tag=tag, auth=auth_config
            )

            # Handle different response formats from aiodocker
            if isinstance(image_data, list) and image_data:
                # If it's a list, get the last item (final status)
                final_status = image_data[-1]
                if isinstance(final_status, dict):
                    image_id = final_status.get("Id", final_status.get("status", ""))
                else:
                    image_id = str(final_status)
            elif isinstance(image_data, dict):
                image_id = image_data.get("Id", image_data.get("status", ""))
            else:
                image_id = str(image_data) if image_data else ""

            logger.info(f"Successfully pulled {image_name} -> {image_id}")
            return image_id
        except DockerError as e:
            raise AsyncDockerClientError(f"Failed to pull image {image_name}: {e}")
        except Exception as e:
            raise AsyncDockerClientError(f"Failed to pull image {image_name}: {e}")

    async def tag_image(
        self, source_image: str, target_repository: str, target_tag: str = "latest"
    ) -> bool:
        """Tag an image with new repository and tag asynchronously.

        Args:
            source_image: Source image name or ID
            target_repository: Target repository name
            target_tag: Target tag

        Returns:
            True if tagging succeeded

        Raises:
            AsyncDockerClientError: If tagging fails
        """
        target_name = f"{target_repository}:{target_tag}"

        try:
            success = await self.docker.images.tag(
                name=source_image, repo=target_repository, tag=target_tag
            )
            if not success:
                raise AsyncDockerClientError(
                    f"Failed to tag image {source_image} as {target_name}"
                )

            logger.info(f"Tagged {source_image} -> {target_name}")
            return True
        except DockerError as e:
            raise AsyncDockerClientError(
                f"Failed to tag image {source_image} as {target_name}: {e}"
            )
        except Exception as e:
            raise AsyncDockerClientError(
                f"Failed to tag image {source_image} as {target_name}: {e}"
            )

    async def push_image_stream(
        self,
        repository: str,
        tag: str = "latest",
        auth_config: Optional[Dict[str, str]] = None,
    ) -> AsyncGenerator[Dict, None]:
        """Push image to registry with streaming output (O(1) memory usage).

        Args:
            repository: Repository to push to
            tag: Image tag
            auth_config: Registry authentication config

        Yields:
            Push progress information

        Raises:
            AsyncDockerClientError: If push operation fails
        """
        image_name = f"{repository}:{tag}"

        try:
            logger.info(f"Pushing image: {image_name}")

            async for log_entry in self.docker.images.push(
                repository, tag=tag, auth=auth_config, stream=True
            ):
                yield log_entry

                if "error" in log_entry:
                    raise AsyncDockerClientError(f"Push failed: {log_entry['error']}")

            logger.info(f"Successfully pushed {image_name}")

        except DockerError as e:
            raise AsyncDockerClientError(f"Failed to push image {image_name}: {e}")
        except Exception as e:
            raise AsyncDockerClientError(f"Failed to push image {image_name}: {e}")

    async def push_image(
        self,
        repository: str,
        tag: str = "latest",
        auth_config: Optional[Dict[str, str]] = None,
    ) -> Dict:
        """Push image to registry (non-streaming version for compatibility).

        Args:
            repository: Repository to push to
            tag: Image tag
            auth_config: Registry authentication config

        Returns:
            Push result information

        Raises:
            AsyncDockerClientError: If push operation fails
        """
        image_name = f"{repository}:{tag}"

        try:
            logger.info(f"Pushing image: {image_name}")

            result = await self.docker.images.push(
                repository, tag=tag, auth=auth_config, stream=False
            )

            logger.info(f"Successfully pushed {image_name}")
            return result

        except DockerError as e:
            raise AsyncDockerClientError(f"Failed to push image {image_name}: {e}")
        except Exception as e:
            raise AsyncDockerClientError(f"Failed to push image {image_name}: {e}")

    async def get_image_digest(
        self, repository: str, tag: str = "latest"
    ) -> Optional[str]:
        """Get image digest (sha256) for verification.

        This method now uses enhanced digest retrieval with fallback strategies
        for improved reliability. Prefers RepoDigests over Image ID.

        Args:
            repository: Image repository
            tag: Image tag

        Returns:
            Image content digest for consistent comparison
        """
        from .services.digest_verification import get_enhanced_digest

        try:
            # Use enhanced digest retrieval for better reliability
            return await get_enhanced_digest(self, repository, tag)
        except Exception as e:
            logger.warning(
                f"Enhanced digest retrieval failed for {repository}:{tag}: {e}"
            )
            # Fallback to original implementation for compatibility
            return await self._get_image_digest_fallback(repository, tag)

    async def _get_image_digest_fallback(
        self, repository: str, tag: str = "latest"
    ) -> Optional[str]:
        """Fallback digest retrieval using original Image ID method.

        This maintains backward compatibility if enhanced method fails.
        """
        image_name = f"{repository}:{tag}"

        try:
            image_data = await self.docker.images.get(image_name)
            # Extract image ID from the response
            image_id = image_data.get("Id", "")
            if image_id.startswith("sha256:"):
                return image_id.replace("sha256:", "")
            return image_id

        except DockerError as e:
            logger.warning(f"Could not get digest for {image_name}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Could not get digest for {image_name}: {e}")
            return None

    async def list_images(
        self, repository_filter: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """List available images asynchronously.

        Args:
            repository_filter: Filter by repository name pattern

        Returns:
            List of image info dictionaries
        """
        try:
            images = await self.docker.images.list()

            image_list = []
            for image in images:
                repo_tags = image.get("RepoTags", [])
                if not repo_tags:
                    continue

                for repo_tag in repo_tags:
                    if repository_filter and repository_filter not in repo_tag:
                        continue

                    if ":" in repo_tag:
                        repo, tag_name = repo_tag.rsplit(":", 1)
                    else:
                        repo, tag_name = repo_tag, "latest"

                    image_list.append(
                        {
                            "repository": repo,
                            "tag": tag_name,
                            "id": image.get("Id", "")[:12],  # Short ID
                            "size": str(image.get("Size", 0)),
                        }
                    )

            return image_list

        except DockerError as e:
            raise AsyncDockerClientError(f"Failed to list images: {e}")
        except Exception as e:
            raise AsyncDockerClientError(f"Failed to list images: {e}")

    async def image_exists(self, repository: str, tag: str = "latest") -> bool:
        """Check if image exists locally.

        Args:
            repository: Image repository
            tag: Image tag

        Returns:
            True if image exists locally
        """
        image_name = f"{repository}:{tag}"

        try:
            await self.docker.images.get(image_name)
            return True
        except DockerError:
            return False
        except Exception as e:
            logger.warning(f"Error checking if image {image_name} exists: {e}")
            return False

    async def remove_image(self, image_name: str, force: bool = False) -> bool:
        """Remove image from local storage.

        Args:
            image_name: Image name or ID to remove
            force: Force removal even if image is in use

        Returns:
            True if removal succeeded
        """
        try:
            await self.docker.images.remove(image_name, force=force)
            logger.info(f"Removed image: {image_name}")
            return True
        except DockerError as e:
            logger.error(f"Failed to remove image {image_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to remove image {image_name}: {e}")
            return False
