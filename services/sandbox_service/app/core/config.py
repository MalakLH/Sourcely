from pydantic_settings import BaseSettings, SettingsConfigDict

class SandboxSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SANDBOX_",
        extra="ignore",
    )

    app_name: str = "Sourcely Sandbox Service"

    docker_image: str = "python:3.12-slim"

    cpu_limit: float = 0.5
    memory_limit: str = "128m"
    memory_swap_limit: str = "128m"
    pids_limit: int = 32

    execution_timeout: int = 5
    max_execution_timeout: int = 10

    max_code_size: int = 12_000

    output_limit: int = 16_384


settings = SandboxSettings()
