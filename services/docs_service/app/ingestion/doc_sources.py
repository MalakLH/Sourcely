"""
Documentation source helpers for fetching and preparing various documentation sets.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def create_sample_python_docs(output_dir: Path) -> None:
    """
    Create sample Python standard library documentation.

    Args:
        output_dir: Directory to write sample docs
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Python basics
    python_basics = """# Python Basics

## Overview

Python is a high-level, interpreted programming language known for its clear syntax and readability.

## Data Types

Python has several built-in data types:

### Numeric Types

- **int**: Integer numbers (e.g., 42, -17)
- **float**: Floating point numbers (e.g., 3.14, -0.001)
- **complex**: Complex numbers (e.g., 3+4j)

### Sequence Types

- **list**: Mutable ordered sequence (e.g., [1, 2, 3])
- **tuple**: Immutable ordered sequence (e.g., (1, 2, 3))
- **range**: Immutable sequence of numbers

### Text Type

- **str**: String of characters (e.g., "Hello, World!")

### Mapping Type

- **dict**: Key-value pairs (e.g., {"name": "Alice", "age": 30})

### Set Types

- **set**: Unordered collection of unique elements
- **frozenset**: Immutable set

### Boolean Type

- **bool**: True or False values

## Control Flow

### If Statements

```python
if condition:
    # do something
elif other_condition:
    # do something else
else:
    # default action
```

### For Loops

```python
for item in iterable:
    # process item
```

### While Loops

```python
while condition:
    # do something
```

## Functions

Functions are defined using the `def` keyword:

```python
def greet(name):
    return f"Hello, {name}!"
```

### Lambda Functions

Anonymous functions can be created with `lambda`:

```python
square = lambda x: x ** 2
```

## Classes

Python supports object-oriented programming:

```python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def greet(self):
        return f"Hi, I'm {self.name}"
```

## Modules and Packages

Code can be organized into modules (single files) and packages (directories of modules).

Import syntax:
```python
import module
from module import function
from package.module import Class
```
"""

    (output_dir / "python_basics.md").write_text(python_basics)
    logger.info("Created Python basics doc")

    # Python standard library - collections
    python_collections = """# Python Collections Module

## Overview

The `collections` module provides specialized container datatypes as 
alternatives to Python's general-purpose built-in containers.

## namedtuple

Factory function for creating tuple subclasses with named fields:

```python
from collections import namedtuple

Point = namedtuple('Point', ['x', 'y'])
p = Point(11, y=22)
print(p.x, p.y)  # 11 22
```

### Use Cases

- Lightweight object types
- Self-documenting code
- Compatible with regular tuples

## deque

Double-ended queue with fast appends and pops from either end:

```python
from collections import deque

d = deque(['a', 'b', 'c'])
d.append('d')      # Add to right
d.appendleft('z')  # Add to left
d.pop()            # Remove from right
d.popleft()        # Remove from left
```

### Use Cases

- Queue implementations
- Ring buffers
- Recently-used lists

## Counter

Dict subclass for counting hashable objects:

```python
from collections import Counter

counts = Counter(['a', 'b', 'c', 'a', 'b', 'b'])
print(counts)  # Counter({'b': 3, 'a': 2, 'c': 1})
print(counts.most_common(2))  # [('b', 3), ('a', 2)]
```

### Methods

- `most_common(n)`: Return n most common elements
- `elements()`: Return iterator over elements
- `subtract(iterable)`: Subtract counts

## defaultdict

Dict subclass that calls a factory function for missing keys:

```python
from collections import defaultdict

dd = defaultdict(int)
dd['a'] += 1  # No KeyError, starts at 0
```

### Use Cases

- Grouping items
- Counting occurrences
- Building nested dictionaries

## OrderedDict

Dict subclass that remembers insertion order:

```python
from collections import OrderedDict

od = OrderedDict()
od['a'] = 1
od['b'] = 2
od['c'] = 3
```

Note: As of Python 3.7+, regular dicts maintain insertion order.

## ChainMap

Groups multiple dicts into a single view:

```python
from collections import ChainMap

dict1 = {'a': 1, 'b': 2}
dict2 = {'b': 3, 'c': 4}
chain = ChainMap(dict1, dict2)
print(chain['b'])  # 2 (from first dict)
```

### Use Cases

- Simulating nested scopes
- Command-line argument defaults
- Configuration management
"""

    (output_dir / "python_collections.md").write_text(python_collections)
    logger.info("Created Python collections doc")

    # Python - asyncio
    python_asyncio = """# Python Asyncio

## Overview

The `asyncio` module provides infrastructure for writing concurrent code 
using the async/await syntax.

## Basic Concepts

### Coroutines

Functions defined with `async def` are coroutines:

```python
async def main():
    print("Hello")
    await asyncio.sleep(1)
    print("World")
```

### Running Coroutines

Use `asyncio.run()` to execute the main coroutine:

```python
import asyncio

asyncio.run(main())
```

## Creating Tasks

Tasks are used to run coroutines concurrently:

```python
async def task1():
    await asyncio.sleep(1)
    return "Task 1 complete"

async def task2():
    await asyncio.sleep(2)
    return "Task 2 complete"

async def main():
    # Create tasks
    t1 = asyncio.create_task(task1())
    t2 = asyncio.create_task(task2())
    
    # Wait for both
    result1 = await t1
    result2 = await t2
    print(result1, result2)
```

## Gathering Multiple Coroutines

Use `asyncio.gather()` to run multiple coroutines concurrently:

```python
async def main():
    results = await asyncio.gather(
        task1(),
        task2(),
        task3()
    )
    print(results)
```

## Timeouts

Set timeouts for operations:

```python
async def main():
    try:
        await asyncio.wait_for(long_operation(), timeout=5.0)
    except asyncio.TimeoutError:
        print("Operation timed out")
```

## Event Loops

The event loop is the core of asyncio:

- Manages and distributes tasks
- Handles I/O operations
- Schedules callbacks

```python
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
```

## Async Context Managers

Use `async with` for async context managers:

```python
async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        data = await response.text()
```

## Async Iterators

Use `async for` to iterate over async iterators:

```python
async for item in async_generator():
    process(item)
```

## Common Patterns

### Concurrent API Requests

```python
async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.text()

async def main():
    async with aiohttp.ClientSession() as session:
        urls = ['http://example.com/1', 'http://example.com/2']
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
```

### Producer-Consumer Pattern

```python
async def producer(queue):
    for i in range(10):
        await queue.put(i)
        await asyncio.sleep(0.1)

async def consumer(queue):
    while True:
        item = await queue.get()
        print(f"Consumed: {item}")
        queue.task_done()
```
"""

    (output_dir / "python_asyncio.md").write_text(python_asyncio)
    logger.info("Created Python asyncio doc")


def create_sample_docker_docs(output_dir: Path) -> None:
    """
    Create sample Docker documentation.

    Args:
        output_dir: Directory to write sample docs
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Docker basics
    docker_basics = """# Docker Basics

## Overview

Docker is a platform for developing, shipping, and running applications in containers.

## What is a Container?

A container is a lightweight, standalone, executable package that includes 
everything needed to run a piece of software:

- Code
- Runtime
- System tools
- System libraries
- Settings

## Docker Architecture

### Docker Engine

The Docker Engine is the underlying technology that runs containers. It consists of:

- **Docker Daemon**: Listens for Docker API requests
- **Docker CLI**: Command-line interface for interacting with Docker
- **REST API**: Specification for programs to talk to the daemon

### Images

Images are read-only templates used to create containers. They contain:

- Application code
- Libraries and dependencies
- Environment variables
- Configuration files

### Containers

Containers are runnable instances of images. They are:

- Isolated from other containers
- Portable across environments
- Ephemeral by default

## Basic Commands

### Working with Images

```bash
# Pull an image from Docker Hub
docker pull ubuntu:22.04

# List images
docker images

# Build an image from a Dockerfile
docker build -t myapp:1.0 .

# Remove an image
docker rmi myapp:1.0
```

### Working with Containers

```bash
# Run a container
docker run ubuntu:22.04

# Run in detached mode
docker run -d nginx

# Run with port mapping
docker run -p 8080:80 nginx

# List running containers
docker ps

# List all containers
docker ps -a

# Stop a container
docker stop container_id

# Remove a container
docker rm container_id
```

### Container Management

```bash
# View container logs
docker logs container_id

# Execute command in running container
docker exec -it container_id /bin/bash

# View container resource usage
docker stats

# Inspect container details
docker inspect container_id
```

## Dockerfile

A Dockerfile is a text file containing instructions to build a Docker image.

### Common Instructions

- `FROM`: Base image
- `RUN`: Execute command during build
- `COPY`: Copy files from host to image
- `WORKDIR`: Set working directory
- `EXPOSE`: Document exposed ports
- `CMD`: Default command to run
- `ENTRYPOINT`: Configure container executable

### Example Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
```

## Docker Compose

Docker Compose is a tool for defining and running multi-container applications.

### docker-compose.yml Example

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://db:5432/mydb
  
  db:
    image: postgres:14
    environment:
      POSTGRES_PASSWORD: secret
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Compose Commands

```bash
# Start services
docker-compose up

# Start in detached mode
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs

# Scale services
docker-compose up --scale web=3
```
"""

    (output_dir / "docker_basics.md").write_text(docker_basics)
    logger.info("Created Docker basics doc")

    # Docker networking
    docker_networking = """# Docker Networking

## Overview

Docker networking enables containers to communicate with each other and with external systems.

## Network Types

### Bridge Network

The default network type. Containers on the same bridge network can communicate with each other.

```bash
# Create a bridge network
docker network create my-bridge-network

# Run container on network
docker run --network=my-bridge-network nginx
```

### Host Network

Container shares the host's network stack. No network isolation.

```bash
docker run --network=host nginx
```

### None Network

Container has no network access.

```bash
docker run --network=none alpine
```

### Overlay Network

Enables communication between containers across multiple Docker hosts. Used in Swarm mode.

```bash
docker network create --driver overlay my-overlay
```

## Network Management

### List Networks

```bash
docker network ls
```

### Inspect Network

```bash
docker network inspect bridge
```

### Connect Container to Network

```bash
docker network connect my-network my-container
```

### Disconnect Container from Network

```bash
docker network disconnect my-network my-container
```

### Remove Network

```bash
docker network rm my-network
```

## Container Communication

### By Container Name

Containers on the same user-defined network can resolve each other by name:

```bash
# Create network
docker network create app-network

# Run database
docker run -d --name db --network app-network postgres

# Run app (can connect to 'db' by name)
docker run --network app-network myapp
```

### Port Publishing

Map container ports to host ports:

```bash
# Map port 80 in container to port 8080 on host
docker run -p 8080:80 nginx

# Map to random host port
docker run -P nginx

# Bind to specific host interface
docker run -p 127.0.0.1:8080:80 nginx
```

## DNS Resolution

Docker provides automatic DNS resolution for container names within user-defined networks.

### Example

```yaml
services:
  web:
    image: nginx
    networks:
      - frontend
  
  api:
    image: myapi
    networks:
      - frontend
      - backend
  
  db:
    image: postgres
    networks:
      - backend

networks:
  frontend:
  backend:
```

In this setup:
- `web` can reach `api` by name
- `api` can reach both `web` and `db`
- `web` cannot reach `db` directly

## Network Security

### Isolating Containers

Use separate networks to isolate groups of containers:

```bash
docker network create public-network
docker network create private-network

# Public-facing web server
docker run --network public-network web

# Backend database (not accessible from public)
docker run --network private-network db
```

### Firewall Rules

Docker automatically manages iptables rules for container networking.

## Best Practices

1. **Use user-defined networks** instead of the default bridge for better isolation and DNS
2. **Minimize exposed ports** - only publish necessary ports
3. **Use overlay networks** for multi-host communication in production
4. **Implement network policies** to control traffic flow between containers
5. **Monitor network traffic** for security and performance
"""

    (output_dir / "docker_networking.md").write_text(docker_networking)
    logger.info("Created Docker networking doc")


def create_sample_kubernetes_probes_docs(output_dir: Path) -> None:
    """
    Create comprehensive Kubernetes Probes documentation.

    Args:
        output_dir: Directory to write sample docs
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Kubernetes Liveness, Readiness, Startup Probes
    k8s_probes = """# Kubernetes Health Probes

## Overview

Kubernetes provides three types of health probes to ensure your applications are 
running correctly and can handle traffic. These probes are essential for 
maintaining application availability and reliability in a containerized environment.

## Liveness Probes

### What is a Liveness Probe?

A **liveness probe** determines if a container is running properly. If the liveness probe fails,
Kubernetes kills the container and restarts it according to the pod's restart policy.

### When to Use Liveness Probes

- Detect deadlocked applications that are still running but unable to make progress
- Detect applications stuck in infinite loops
- Force restart of unhealthy containers
- Recover from transient failures automatically

### Liveness Probe Configuration

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: liveness-example
spec:
  containers:
  - name: app
    image: myapp:1.0
    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
      initialDelaySeconds: 15
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
```

### Configuration Parameters

- **initialDelaySeconds**: Number of seconds after container starts before probe begins (default: 0)
- **periodSeconds**: How often to perform the probe (default: 10)
- **timeoutSeconds**: Seconds after which probe times out (default: 1)
- **successThreshold**: Minimum consecutive successes for probe to be 
considered successful (default: 1)
- **failureThreshold**: Number of consecutive failures before giving up and restarting (default: 3)

### Liveness Probe Types

#### 1. HTTP GET Probe

Most common for web applications:

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
    httpHeaders:
    - name: Custom-Header
      value: Awesome
  initialDelaySeconds: 3
  periodSeconds: 3
```

Returns success if HTTP status code is between 200-399.

#### 2. TCP Socket Probe

Checks if a TCP connection can be established:

```yaml
livenessProbe:
  tcpSocket:
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 20
```

#### 3. Exec Probe

Runs a command inside the container:

```yaml
livenessProbe:
  exec:
    command:
    - cat
    - /tmp/healthy
  initialDelaySeconds: 5
  periodSeconds: 5
```

Returns success if exit code is 0.

## Readiness Probes

### What is a Readiness Probe?

A **readiness probe** determines if a container is ready to accept traffic. 
If the readiness probe fails, Kubernetes removes the pod's IP address 
from the endpoints of all Services matching the pod.

### When to Use Readiness Probes

- Prevent sending traffic to pods that are still initializing
- Handle temporary unavailability (e.g., loading large data, connecting to database)
- Gracefully handle backend dependencies being unavailable
- Control when a pod receives traffic from a Service

### Readiness vs Liveness

| Aspect | Liveness Probe | Readiness Probe |
|--------|---------------|-----------------|
| Purpose | Is container alive? | Is container ready for traffic? |
| Failure Action | Restart container | Remove from Service endpoints |
| During Startup | May fail safely | Should fail until ready |
| During Operation | Should always pass | May fail temporarily |

### Readiness Probe Configuration

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: readiness-example
spec:
  containers:
  - name: app
    image: myapp:1.0
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
      failureThreshold: 3
    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
      initialDelaySeconds: 15
      periodSeconds: 10
```

### Common Readiness Patterns

#### Database Connection Check

```python
# Python Flask example
@app.route('/ready')
def readiness():
    try:
        # Check database connection
        db.execute('SELECT 1')
        return 'OK', 200
    except Exception:
        return 'Not Ready', 503
```

#### Dependency Check

```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
  successThreshold: 1
  failureThreshold: 3
```

## Startup Probes

### What is a Startup Probe?

A **startup probe** checks if the application within a container has started. 
It's designed for slow-starting containers.

### When to Use Startup Probes

- Applications with long initialization times
- Legacy applications that need extra startup time
- Prevent liveness probes from interfering with slow startup
- Protect slow-starting containers from premature termination

### How Startup Probes Work

1. Startup probe runs until it succeeds
2. All other probes are disabled during startup
3. Once startup succeeds, liveness and readiness probes take over
4. If startup probe fails after failureThreshold attempts, container is killed

### Startup Probe Configuration

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: startup-example
spec:
  containers:
  - name: slow-app
    image: myapp:1.0
    startupProbe:
      httpGet:
        path: /startup
        port: 8080
      failureThreshold: 30  # Allow up to 5 minutes (30 * 10s)
      periodSeconds: 10
    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
      periodSeconds: 10
```

### Startup Probe Benefits

- **Prevents premature liveness failures** during initialization
- **Flexible failure threshold** for variable startup times
- **Isolated from liveness checks** so they don't conflict

## Best Practices

### 1. Always Use Both Liveness and Readiness

```yaml
containers:
- name: app
  livenessProbe:
    httpGet:
      path: /healthz
      port: 8080
    initialDelaySeconds: 30
    periodSeconds: 10
  readinessProbe:
    httpGet:
      path: /ready
      port: 8080
    initialDelaySeconds: 5
    periodSeconds: 5
```

### 2. Set Appropriate Timeouts

- **initialDelaySeconds**: Should exceed typical startup time
- **periodSeconds**: Balance between responsiveness and resource usage (5-10s typical)
- **failureThreshold**: Allow for transient failures (3-5 failures typical)

### 3. Implement Lightweight Health Endpoints

```python
# Fast health check endpoint
@app.route('/healthz')
def liveness():
    return 'OK', 200

# More thorough readiness check
@app.route('/ready')
def readiness():
    checks = [
        check_database(),
        check_cache(),
        check_dependencies()
    ]
    if all(checks):
        return 'Ready', 200
    return 'Not Ready', 503
```

### 4. Avoid Expensive Operations in Probes

❌ **Bad:**
```python
@app.route('/healthz')
def health():
    # Heavy database query
    results = db.query('SELECT * FROM large_table')
    return 'OK', 200
```

✅ **Good:**
```python
@app.route('/healthz')
def health():
    # Lightweight check
    if app.is_running:
        return 'OK', 200
    return 'Not OK', 503
```

### 5. Use Startup Probes for Slow Applications

```yaml
startupProbe:
  httpGet:
    path: /startup
    port: 8080
  failureThreshold: 60  # 10 minutes max startup (60 * 10s)
  periodSeconds: 10
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  periodSeconds: 10
  failureThreshold: 3
```

## Common Pitfalls

### 1. Liveness Probe Too Aggressive

❌ Problem: Probe fails during high load, causing unnecessary restarts

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  periodSeconds: 5
  timeoutSeconds: 1  # Too short!
  failureThreshold: 1  # Too aggressive!
```

✅ Solution: Allow for transient failures

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### 2. Readiness and Liveness Are Identical

❌ Problem: Pod restarts when it should just stop receiving traffic

```yaml
# Both probes check the same thing
livenessProbe:
  httpGet:
    path: /health
readinessProbe:
  httpGet:
    path: /health
```

✅ Solution: Use different endpoints with different purposes

```yaml
livenessProbe:
  httpGet:
    path: /healthz  # Basic "is alive?"
readinessProbe:
  httpGet:
    path: /ready    # "Can handle traffic?"
```

### 3. Missing initialDelaySeconds

❌ Problem: Probes fail during container startup

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  # Missing initialDelaySeconds!
```

✅ Solution: Add appropriate startup delay

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 30  # Allow time to start
```

## Real-World Examples

### Example 1: Python FastAPI Application

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: myapi:1.0
        ports:
        - containerPort: 8000
        startupProbe:
          httpGet:
            path: /startup
            port: 8000
          failureThreshold: 30
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 15
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 2
```

### Example 2: Database Container

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: postgres
spec:
  containers:
  - name: db
    image: postgres:14
    livenessProbe:
      exec:
        command:
        - pg_isready
        - -U
        - postgres
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      exec:
        command:
        - pg_isready
        - -U
        - postgres
      initialDelaySeconds: 5
      periodSeconds: 5
```

### Example 3: gRPC Service

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: grpc-service
spec:
  containers:
  - name: server
    image: mygrpc:1.0
    livenessProbe:
      grpc:
        port: 50051
      initialDelaySeconds: 10
      periodSeconds: 10
    readinessProbe:
      grpc:
        port: 50051
        service: myservice.health.v1.Health
      initialDelaySeconds: 5
      periodSeconds: 5
```

## Monitoring and Debugging

### Check Probe Status

```bash
# Get pod events
kubectl describe pod <pod-name>

# Watch probe failures
kubectl get events --watch | grep -i probe

# Check container logs
kubectl logs <pod-name> -c <container-name>
```

### Probe Failure Indicators

```
Events:
  Type     Reason     Age   Message
  ----     ------     ----  -------
  Warning  Unhealthy  2m    Liveness probe failed: HTTP probe failed with statuscode: 500
  Warning  Unhealthy  1m    Readiness probe failed: Get http://10.1.0.4:8080/ready: 
  dial tcp 10.1.0.4:8080: connect: connection refused
```

## Summary

| Probe Type | Purpose | Failure Action | Use Case |
|------------|---------|----------------|----------|
| **Liveness** | Is container alive? | Restart container | Detect deadlocks, force restarts |
| **Readiness** | Ready for traffic? | Remove from Service | Control traffic routing |
| **Startup** | Has container started? | Kill after threshold | Protect slow-starting apps |

Choose the right combination of probes based on your application's needs to 
ensure high availability and reliability in Kubernetes.
"""

    (output_dir / "kubernetes_probes.md").write_text(k8s_probes)
    logger.info("Created Kubernetes Probes documentation")


def create_all_sample_docs(base_dir: Path) -> dict[str, Path]:
    """
    Create all sample documentation sets.

    Args:
        base_dir: Base directory for all documentation

    Returns:
        Dictionary mapping doc source to its directory path
    """
    docs_paths = {}

    # Create Kubernetes docs
    k8s_dir = base_dir / "kubernetes"
    create_sample_kubernetes_probes_docs(k8s_dir)
    docs_paths["kubernetes"] = k8s_dir

    # Create Python docs
    python_dir = base_dir / "python"
    create_sample_python_docs(python_dir)
    docs_paths["python"] = python_dir

    # Create Docker docs
    docker_dir = base_dir / "docker"
    create_sample_docker_docs(docker_dir)
    docs_paths["docker"] = docker_dir

    logger.info(f"Created all sample documentation in {base_dir}")
    return docs_paths
