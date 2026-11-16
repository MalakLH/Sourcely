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
    logger.info(f"Created Python basics doc")

    # Python standard library - collections
    python_collections = """# Python Collections Module

## Overview

The `collections` module provides specialized container datatypes as alternatives to Python's general-purpose built-in containers.

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
    logger.info(f"Created Python collections doc")

    # Python - asyncio
    python_asyncio = """# Python Asyncio

## Overview

The `asyncio` module provides infrastructure for writing concurrent code using the async/await syntax.

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
    logger.info(f"Created Python asyncio doc")


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

A container is a lightweight, standalone, executable package that includes everything needed to run a piece of software:

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
    logger.info(f"Created Docker basics doc")

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
    logger.info(f"Created Docker networking doc")


def create_all_sample_docs(base_dir: Path) -> dict[str, Path]:
    """
    Create all sample documentation sets.

    Args:
        base_dir: Base directory for all documentation

    Returns:
        Dictionary mapping doc source to its directory path
    """
    docs_paths = {}

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
