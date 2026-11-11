from app.core.config import settings


def get_container_security_config() -> dict:
    return {
        # Resource restrictions
        "nano_cpus": int(settings.cpu_limit * 1_000_000_000),
        "mem_limit": settings.memory_limit,
        "memswap_limit": settings.memory_swap_limit,
        "pids_limit": settings.pids_limit,
        # Privilege restrictions
        "user": "65534:65534",
        "privileged": False,
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges:true"],
        # Filesystem restrictions
        "read_only": True,
        "working_dir": "/tmp",
        "tmpfs": {"/tmp": ("rw,noexec,nosuid,nodev,size=16m,uid=65534,gid=65534")},
        # Network isolation
        "network_mode": "none",
        # No host filesystem mounts
        "volumes": {},
    }
