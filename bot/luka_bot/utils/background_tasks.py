"""
Background Task Utilities - Fire-and-forget async task management.

This module provides utilities for running truly parallel background tasks
without blocking the main execution flow. Key for moderation V2 architecture.

Key Features:
- Fire-and-forget task execution
- Error handling and logging
- Task tracking (optional)
- Graceful shutdown support
"""

import asyncio
from typing import Callable, Coroutine, Any, Optional, Set
from loguru import logger


# Global set of background tasks (prevents garbage collection)
_background_tasks: Set[asyncio.Task] = set()


def create_background_task(
    coro: Coroutine,
    name: Optional[str] = None,
    track: bool = True
) -> asyncio.Task:
    """
    Create a background task that runs independently.
    
    Args:
        coro: Coroutine to run in background
        name: Optional task name for logging
        track: If True, track task to prevent garbage collection
        
    Returns:
        asyncio.Task instance
        
    Example:
        # Fire and forget - no waiting!
        task = create_background_task(
            process_moderation_in_background(message_id, ...),
            name="moderation_user_123"
        )
        # Main flow continues immediately
        
    Note:
        - Task runs independently, doesn't block caller
        - Errors are logged but don't crash main flow
        - Task is automatically removed from tracking when done
    """
    task = asyncio.create_task(coro, name=name)
    
    if track:
        # Add to global set to prevent garbage collection
        _background_tasks.add(task)
        logger.debug(f"🔥 Created background task: {name or 'unnamed'} (total: {len(_background_tasks)})")
        
        # Remove from set when done (auto-cleanup)
        task.add_done_callback(_background_tasks.discard)
        
        # Add error handler
        task.add_done_callback(_handle_task_completion)
    else:
        logger.debug(f"🔥 Created untracked background task: {name or 'unnamed'}")
    
    return task


def _handle_task_completion(task: asyncio.Task) -> None:
    """
    Handle background task completion (success or error).
    
    Args:
        task: Completed task
        
    Note:
        This is called automatically when task finishes.
        Logs errors but doesn't re-raise them (fire-and-forget).
    """
    try:
        # Check if task raised an exception
        if task.exception() is not None:
            exc = task.exception()
            task_name = task.get_name() if hasattr(task, 'get_name') else 'unnamed'
            logger.error(f"❌ Background task failed: {task_name}", exc_info=exc)
        else:
            task_name = task.get_name() if hasattr(task, 'get_name') else 'unnamed'
            logger.debug(f"✅ Background task completed: {task_name}")
    except asyncio.CancelledError:
        task_name = task.get_name() if hasattr(task, 'get_name') else 'unnamed'
        logger.debug(f"🛑 Background task cancelled: {task_name}")
    except Exception as e:
        logger.error(f"❌ Error handling task completion: {e}")


async def cancel_all_background_tasks() -> None:
    """
    Cancel all tracked background tasks.
    
    Use Case:
        Call during bot shutdown to gracefully stop all background work.
        
    Example:
        # In bot shutdown handler:
        await cancel_all_background_tasks()
        
    Note:
        - Waits for tasks to complete or cancel (max 5 seconds)
        - Logs any tasks that timeout
    """
    if not _background_tasks:
        logger.info("✅ No background tasks to cancel")
        return
    
    logger.info(f"🛑 Cancelling {len(_background_tasks)} background tasks...")
    
    # Cancel all tasks
    for task in _background_tasks:
        if not task.done():
            task.cancel()
    
    # Wait for cancellation (with timeout)
    try:
        await asyncio.wait_for(
            asyncio.gather(*_background_tasks, return_exceptions=True),
            timeout=5.0
        )
        logger.info("✅ All background tasks cancelled")
    except asyncio.TimeoutError:
        logger.warning(f"⚠️ Some background tasks didn't cancel in time: {len(_background_tasks)}")


def get_background_task_count() -> int:
    """
    Get count of currently running background tasks.
    
    Returns:
        Number of tracked background tasks
        
    Use Case:
        Monitoring and debugging
    """
    return len(_background_tasks)


def get_background_task_names() -> list[str]:
    """
    Get names of all running background tasks.
    
    Returns:
        List of task names
        
    Use Case:
        Debugging and monitoring
    """
    names = []
    for task in _background_tasks:
        if hasattr(task, 'get_name'):
            names.append(task.get_name())
        else:
            names.append('unnamed')
    return names


async def run_with_timeout(
    coro: Coroutine,
    timeout: float,
    name: Optional[str] = None,
    default: Any = None
) -> Any:
    """
    Run a coroutine with timeout, return default if times out.
    
    Args:
        coro: Coroutine to run
        timeout: Timeout in seconds
        name: Optional name for logging
        default: Default value to return on timeout
        
    Returns:
        Result from coroutine, or default if timeout
        
    Example:
        result = await run_with_timeout(
            slow_llm_call(...),
            timeout=5.0,
            name="moderation_check",
            default={"action": "none"}
        )
        
    Note:
        This is useful for operations that might hang.
        Unlike asyncio.wait_for(), this returns a default instead of raising.
    """
    try:
        result = await asyncio.wait_for(coro, timeout=timeout)
        return result
    except asyncio.TimeoutError:
        logger.warning(f"⏱️ Task timed out after {timeout}s: {name or 'unnamed'}")
        return default
    except Exception as e:
        logger.error(f"❌ Task failed: {name or 'unnamed'}: {e}")
        return default

