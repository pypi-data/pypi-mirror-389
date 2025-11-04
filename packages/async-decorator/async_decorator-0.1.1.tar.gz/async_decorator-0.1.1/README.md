# Async Decorator

A flexible Python library for managing async/sync function execution with dedicated thread pools.

## Usage scenarios

- Ensure that the main process is not blocked
- Provide concurrency capability for certain functions
- At the same time, some functions cannot use concurrency
- Use EXCLUSIVE type isolation for non concurrent functionality
- Use SHARED_POOL type to ensure concurrency requirements for other features
- Multi functional use of one thread to ensure serial processing of data. Tip: Transformer Large Model Reasoning

## Features

- **Dedicated Thread Pools**: Isolate synchronous function execution
- **Shared Thread Pools**: Efficiently execute async functions in threads  
- **Flexible Execution Types**: EXCLUSIVE, SHARED_POOL
- **Thread Safety**: Managed thread pool lifecycle
- **Easy Integration**: Simple decorator-based API

## Installation

```bash
pip install async-decorator
```

## Quick Start

```python
import asyncio
import aiohttp
from async_decorator import async_decorator, ExecType

@async_decorator(ExecType.EXCLUSIVE)
def process_data(data):
    # CPU-intensive synchronous work
    return len(data)

@async_decorator(ExecType.SHARED_POOL)
async def fetch_data(url):
    # I/O-bound async work
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

async def main():
    # These run in appropriate thread pools
    result1 = process_data("hello world")
    result2 = await fetch_data("https://example.com")
    
    print(f"Processed: {result1}, Fetched: {len(result2)} bytes")

asyncio.run(main())
```

## Execution Types

- `EXCLUSIVE`: Sync functions in dedicated thread pools
- `SHARED_POOL`: Async functions in shared thread pool

## Advanced Usage

### Example 1 

```python
from async_decorator import ExecType, async_decorator

# Custom maximum workers for shared async pool
shared_pool_size = 200

@async_decorator(ExecType.SHARED_POOL, shared_pool_size=shared_pool_size)
def custom_processing():
    return "processed"

```

### Example 2

```python
from async_decorator import DedicatedThreadManager, ExecType, async_decorator

# Custom thread manager, but shared_pool_size will lose its effect
manager = DedicatedThreadManager(
    shared_pool_size=20,
    max_dedicated_pools=50
)

@async_decorator(ExecType.EXCLUSIVE, "my_exclusive", thread_manager=manager)
def custom_processing():
    return "processed"

# Cleanup
manager.shutdown()
```
