
import docker
import pytest
from docker.errors import DockerException

from app.sandbox.container import DockerContainerManager


@pytest.fixture
def docker_client():
    """Provide a Docker client or skip if Docker is unavailable."""
    try:
        client = docker.from_env()
        client.ping()
    except DockerException:
        pytest.skip("Docker Engine is not available.")

    yield client
    client.close()


@pytest.fixture
def container_manager():
    """Create and close a real sandbox container manager."""
    manager = DockerContainerManager()
    yield manager
    manager.close()


def assert_container_was_removed(docker_client, container_id):
    """Check that the execution container no longer exists."""
    containers = docker_client.containers.list(
        all=True,
        filters={"label": "service=sourcely-sandbox"},
    )

    matching_containers = [
        container
        for container in containers
        if container.id.startswith(container_id)
    ]

    assert matching_containers == []


def test_real_python_execution(
    docker_client,
    container_manager,
):
    result = container_manager.execute(
        code="print(1 + 1)",
        timeout=5,
    )

    assert result.status == "success"
    assert result.stdout == "2\n"
    assert result.exit_code == 0
    assert result.container_id is not None

    assert_container_was_removed(
        docker_client,
        result.container_id,
    )


def test_python_runtime_error(
    docker_client,
    container_manager,
):
    result = container_manager.execute(
        code="raise ValueError('intentional integration test error')",
        timeout=5,
    )

    assert result.status == "failed"
    assert "ValueError" in result.stderr
    assert result.exit_code != 0

    assert_container_was_removed(
        docker_client,
        result.container_id,
    )


def test_execution_timeout(
    docker_client,
    container_manager,
):
    result = container_manager.execute(
        code="import time; time.sleep(3)",
        timeout=1,
    )

    assert result.status == "timeout"
    assert result.exit_code != 0
    assert result.container_id is not None

    assert_container_was_removed(
        docker_client,
        result.container_id,
    )
