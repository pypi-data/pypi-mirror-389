import time
import uvicorn
import asyncio
import threading
from fastapi import FastAPI
# import async_decorator
from async_decorator import ExecType, async_decorator

# 创建FastAPI应用
app = FastAPI(title="Simple API", version="1.0.0")


@app.get("/sync-endpoint-1")
@async_decorator(ExecType.EXCLUSIVE, "sync_endpoint_1")
async def sync_endpoint_1():
    thread_name = threading.current_thread().name
    time.sleep(5)
    return {
        "endpoint": "sync_endpoint_1",
        "thread": thread_name,
        "message": "This endpoint has its own dedicated thread pool",
        "pool_type": "dedicated"
    }


@app.get("/sync-endpoint-2")
@async_decorator(ExecType.EXCLUSIVE, "sync_endpoint_1")
async def sync_endpoint_2():
    thread_name = threading.current_thread().name
    time.sleep(5)
    return {
        "endpoint": "sync_endpoint_2",
        "thread": thread_name,
        "message": "This endpoint has its own dedicated thread pool",
        "pool_type": "dedicated"
    }


@app.get("/sync-endpoint-3")
@async_decorator(ExecType.EXCLUSIVE, "sync_endpoint_3")
def sync_endpoint_3():
    thread_name = threading.current_thread().name
    time.sleep(5)
    return {
        "endpoint": "sync_endpoint_3",
        "thread": thread_name,
        "message": "This endpoint has its own dedicated thread pool",
        "pool_type": "dedicated"
    }


@app.get("/async-threaded-endpoint-1")
@async_decorator(ExecType.SHARED_POOL)
def shared_pool_endpoint_1():
    thread_name = threading.current_thread().name
    time.sleep(5)
    return {
        "endpoint": "SHARED_POOL_endpoint_1",
        "thread": thread_name,
        "message": "This endpoint shares thread pool",
        "pool_type": "shared"
    }


@app.get("/async-threaded-endpoint-2")
@async_decorator(ExecType.SHARED_POOL)
def shared_pool_endpoint_2():
    thread_name = threading.current_thread().name
    time.sleep(5)
    return {
        "endpoint": "SHARED_POOL_endpoint_2",
        "thread": thread_name,
        "message": "This endpoint shares thread pool",
        "pool_type": "shared"
    }


@app.get("/pure-async-endpoint")
@async_decorator(ExecType.SHARED_POOL)
async def pure_async_endpoint():
    thread_name = threading.current_thread().name
    await asyncio.sleep(5)
    return {
        "endpoint": "pure_async_endpoint",
        "thread": thread_name,
        "message": "This endpoint runs in event loop",
        "pool_type": "event_loop"
    }


@app.get("/quick-test")
@async_decorator(ExecType.SHARED_POOL)
async def quick_test():
    await asyncio.sleep(0.1)
    return {
        "endpoint": "quick_test",
        "thread": threading.current_thread().name,
        "message": "Quick response"
    }


if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)
