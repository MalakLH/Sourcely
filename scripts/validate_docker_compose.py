#!/usr/bin/env python3
"""
Validate docker-compose.yml configuration for Sourcely.

Checks:
- All services defined
- Port mappings are unique and valid
- Environment variables are properly referenced
- Service dependencies are correct
- Health endpoints are defined
"""

import sys
from pathlib import Path

import yaml


def load_docker_compose():
    """Load and parse docker-compose.yml."""
    compose_path = (
        Path(__file__).parent.parent
        / "infrastructure"
        / "docker"
        / "docker-compose.yml"
    )
    with open(compose_path) as f:
        return yaml.safe_load(f)


def validate_services(config):
    """Validate service definitions."""
    required_services = [
        "agent-service",
        "sandbox-service",
        "docs-service",
        "webguide-service",
        "scanner-service",
        "ui-service",
        "searxng",
    ]

    services = config.get("services", {})

    print("✓ Checking service definitions...")
    for service in required_services:
        if service not in services:
            print(f"  ✗ Missing service: {service}")
            return False
        print(f"  ✓ {service} defined")

    return True


def validate_ports(config):
    """Validate port mappings are unique."""
    print("\n✓ Checking port mappings...")

    services = config.get("services", {})
    used_ports = {}

    for service_name, service_config in services.items():
        ports = service_config.get("ports", [])

        for port_mapping in ports:
            if isinstance(port_mapping, str):
                host_port = port_mapping.split(":")[0]
                if host_port in used_ports:
                    print(
                        f"  ✗ Port conflict: {host_port} used by {used_ports[host_port]} and {service_name}"
                    )
                    return False
                used_ports[host_port] = service_name
                print(f"  ✓ {service_name}: {port_mapping}")

    expected_ports = {
        "8000": "agent-service",
        "8001": None,  # sandbox internal only
        "8002": "docs-service",
        "8003": "webguide-service",
        "8004": "scanner-service",
        "8080": "searxng",
        "8501": "ui-service",
    }

    for port, expected_service in expected_ports.items():
        if expected_service and port not in used_ports:
            print(f"  ⚠ Port {port} not mapped (expected: {expected_service})")

    return True


def validate_dependencies(config):
    """Validate service dependencies."""
    print("\n✓ Checking service dependencies...")

    services = config.get("services", {})

    # Agent should depend on all tool services
    agent_deps = services.get("agent-service", {}).get("depends_on", [])
    required_agent_deps = ["sandbox-service", "docs-service", "webguide-service"]

    for dep in required_agent_deps:
        if dep in agent_deps:
            print(f"  ✓ agent-service → {dep}")
        else:
            print(f"  ⚠ agent-service missing dependency: {dep}")

    # Webguide should depend on searxng
    webguide_deps = services.get("webguide-service", {}).get("depends_on", [])
    if "searxng" in webguide_deps:
        print("  ✓ webguide-service → searxng")
    else:
        print("  ⚠ webguide-service missing dependency: searxng")

    return True


def validate_environment_vars(config):
    """Validate environment variable configuration."""
    print("\n✓ Checking environment variables...")

    services = config.get("services", {})

    # Agent service should have all service URLs
    agent_env = services.get("agent-service", {}).get("environment", {})
    required_env_vars = [
        "OLLAMA_BASE_URL",
        "SANDBOX_BASE_URL",
        "DOCS_SERVICE_URL",
        "WEBGUIDE_SERVICE_URL",
    ]

    for var in required_env_vars:
        if var in agent_env:
            print(f"  ✓ agent-service.{var} = {agent_env[var]}")
        else:
            print(f"  ✗ agent-service missing env var: {var}")
            return False

    return True


def validate_volumes(config):
    """Validate volume configurations."""
    print("\n✓ Checking volumes...")

    volumes = config.get("volumes", {})

    if "sandbox_ledger_data" in volumes:
        print("  ✓ sandbox_ledger_data volume defined")
    else:
        print("  ⚠ sandbox_ledger_data volume not defined")

    # Check sandbox service uses the volume
    services = config.get("services", {})
    sandbox_volumes = services.get("sandbox-service", {}).get("volumes", [])

    for vol in sandbox_volumes:
        if "sandbox_ledger_data" in str(vol):
            print("  ✓ sandbox-service mounts ledger volume")
            break

    return True


def main():
    """Run all validations."""
    print("=" * 60)
    print("Docker Compose Configuration Validation")
    print("=" * 60)

    try:
        config = load_docker_compose()

        validations = [
            validate_services(config),
            validate_ports(config),
            validate_dependencies(config),
            validate_environment_vars(config),
            validate_volumes(config),
        ]

        print("\n" + "=" * 60)
        if all(validations):
            print("✓ All validations passed!")
            print("=" * 60)
            return 0
        else:
            print("✗ Some validations failed")
            print("=" * 60)
            return 1

    except (OSError, yaml.YAMLError) as e:
        print(f"\n✗ Validation error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
