"""
URL mappings for documentation sources.
Maps local file names to real, live official documentation URLs.
"""

# Kubernetes documentation URLs
KUBERNETES_URLS = {
    "pods.md": "https://kubernetes.io/docs/concepts/workloads/pods/",
    "services.md": "https://kubernetes.io/docs/concepts/services-networking/service/",
    "deployments.md": "https://kubernetes.io/docs/concepts/workloads/controllers/deployment/",
    "kubernetes_probes.md": "https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/",
}

# Python documentation URLs
PYTHON_URLS = {
    "python_basics.md": "https://docs.python.org/3/tutorial/index.html",
    "python_collections.md": "https://docs.python.org/3/library/collections.html",
    "python_asyncio.md": "https://docs.python.org/3/library/asyncio.html",
}

# Docker documentation URLs
DOCKER_URLS = {
    "docker_basics.md": "https://docs.docker.com/get-started/",
    "docker_networking.md": "https://docs.docker.com/network/",
    "dockerfile.md": "https://docs.docker.com/reference/dockerfile/",
}

# Combined mapping
URL_MAPPINGS = {
    **KUBERNETES_URLS,
    **PYTHON_URLS,
    **DOCKER_URLS,
}


def get_real_url(file_path_str: str) -> str:
    """
    Get the real documentation URL for a given file path.

    Args:
        file_path_str: File path as string (e.g., "kubernetes/pods.md")

    Returns:
        Real documentation URL or fallback URL with filename
    """
    # Extract just the filename
    filename = file_path_str.split("/")[-1] if "/" in file_path_str else file_path_str
    filename = filename.split("\\")[-1] if "\\" in filename else filename

    # Return mapped URL if exists
    return URL_MAPPINGS.get(filename, f"https://docs.sourcely.ai/{file_path_str}")
