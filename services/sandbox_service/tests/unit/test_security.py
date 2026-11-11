from app.sandbox.security import get_container_security_config


def test_container_runs_as_non_root():
    config = get_container_security_config()

    assert config["user"] == "65534:65534"


def test_container_has_resource_limits():
    config = get_container_security_config()

    assert config["nano_cpus"] == 500_000_000
    assert config["mem_limit"] == "128m"
    assert config["memswap_limit"] == "128m"
    assert config["pids_limit"] == 32


def test_container_filesystem_is_restricted():
    config = get_container_security_config()

    assert config["read_only"] is True
    assert "/tmp" in config["tmpfs"]


def test_container_capabilities_are_dropped():
    config = get_container_security_config()

    assert config["cap_drop"] == ["ALL"]
    assert "no-new-privileges:true" in config["security_opt"]


def test_container_network_is_disabled():
    config = get_container_security_config()

    assert config["network_mode"] == "none"
