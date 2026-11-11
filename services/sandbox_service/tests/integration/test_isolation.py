import docker
import pytest
from docker.errors import DockerException

from app.core.config import settings
from app.sandbox.container import DockerContainerManager
from app.sandbox.security import get_container_security_config


@pytest.fixture
def docker_client():
    """Connect to Docker or skip if the Engine is unavailable."""
    try:
        client = docker.from_env()
        client.ping()
    except DockerException:
        pytest.skip("Docker Engine is not available.")

    yield client
    client.close()


@pytest.fixture
def container_manager():
    manager = DockerContainerManager()
    yield manager
    manager.close()


def test_execution_uses_non_root_user(container_manager):
    result = container_manager.execute(
        code="import os; print(os.getuid())",
        timeout=5,
    )

    assert result.status == "success"
    assert result.stdout.strip() == "65534"


def test_root_filesystem_is_read_only_and_tmp_is_writable(
    container_manager,
):
    code = """
from pathlib import Path

try:
    Path("/sourcely-test-file").write_text("test")
    print("root_writable=True")
except OSError:
    print("root_writable=False")

try:
    Path("/tmp/sourcely-test-file").write_text("test")
    print("tmp_writable=True")
except OSError:
    print("tmp_writable=False")
"""

    result = container_manager.execute(code=code, timeout=5)

    assert result.status == "success"
    assert "root_writable=False" in result.stdout
    assert "tmp_writable=True" in result.stdout


def test_docker_applies_isolation_and_resource_configuration(
    docker_client,
):
    container = None

    try:
        container = docker_client.containers.create(
            image=settings.docker_image,
            command=["python", "-I", "-B", "-c", "pass"],
            detach=True,
            labels={"service": "sourcely-isolation-test"},
            **get_container_security_config(),
        )

        container.reload()
        attrs = container.attrs

        config = attrs["Config"]
        host_config = attrs["HostConfig"]

        # Identity and privilege restrictions.
        assert config["User"] == "65534:65534"
        assert host_config["Privileged"] is False
        assert host_config["CapDrop"] == ["ALL"]
        assert "no-new-privileges:true" in host_config["SecurityOpt"]

        # Filesystem and network restrictions.
        assert host_config["ReadonlyRootfs"] is True
        assert host_config["NetworkMode"] == "none"
        assert "/tmp" in host_config["Tmpfs"]

        # Resource limits.
        assert host_config["NanoCpus"] == int(settings.cpu_limit * 1_000_000_000)
        assert host_config["Memory"] == 128 * 1024 * 1024
        assert host_config["MemorySwap"] == 128 * 1024 * 1024
        assert host_config["PidsLimit"] == settings.pids_limit

    finally:
        if container is not None:
            container.remove(force=True)
