
import time
from dataclasses import dataclass

import docker
from docker.errors import DockerException, ImageNotFound

from app.core.config import settings
from app.sandbox.security import get_container_security_config


@dataclass
class ContainerResult:
    status: str
    stdout: str
    stderr: str
    exit_code: int | None
    duration_ms: float
    container_id: str | None


class DockerContainerManager:

    def __init__(self):
        self.client = docker.from_env()

    def ensure_image(self) -> None:
        try:
            self.client.images.get(settings.docker_image)
        except ImageNotFound:
            self.client.images.pull(settings.docker_image)

    def execute(self, code: str, timeout: int) -> ContainerResult:
        container = None
        start_time = time.monotonic()

        try:
            self.ensure_image()

            container = self.client.containers.create(
                image=settings.docker_image,
                command=[
                    "python",
                    "-I",
                    "-B",
                    "-c",
                    code,
                ],
                detach=True,
                stdin_open=False,
                tty=False,
                labels={"service": "sourcely-sandbox"},
                **get_container_security_config(),
            )

            container.start()

            timed_out = False

            while True:
                container.reload()

                if container.status in ("exited", "dead"):
                    break

                elapsed = time.monotonic() - start_time

                if elapsed >= timeout:
                    timed_out = True
                    container.kill()
                    break

                time.sleep(0.1)

            container.reload()

            stdout = container.logs(
                stdout=True,
                stderr=False,
            ).decode("utf-8", errors="replace")

            stderr = container.logs(
                stdout=False,
                stderr=True,
            ).decode("utf-8", errors="replace")

            exit_code = container.attrs.get(
                "State", {}
            ).get("ExitCode")

            # Bound the response size.
            stdout = stdout[:settings.output_limit]
            stderr = stderr[:settings.output_limit]

            duration_ms = (
                time.monotonic() - start_time
            ) * 1000

            return ContainerResult(
                status="timeout" if timed_out else (
                    "success" if exit_code == 0 else "failed"
                ),
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                duration_ms=duration_ms,
                container_id=container.short_id,
            )

        except DockerException as exc:
            return ContainerResult(
                status="failed",
                stdout="",
                stderr=f"Container execution error: {exc}",
                exit_code=None,
                duration_ms=(
                    time.monotonic() - start_time
                ) * 1000,
                container_id=None,
            )

        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except DockerException:
                    pass

    def close(self) -> None:
        self.client.close()
