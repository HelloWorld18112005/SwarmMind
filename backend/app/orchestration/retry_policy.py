import asyncio
import logging
from typing import Any, Callable, Coroutine, TypeVar

T = TypeVar("T")
logger = logging.getLogger(__name__)


class RetryPolicy:
    """Configurable retry policy with exponential backoff for agent task executions."""

    def __init__(
        self,
        max_retries: int = 2,
        initial_backoff: float = 0.5,
        backoff_multiplier: float = 2.0,
    ) -> None:
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.backoff_multiplier = backoff_multiplier

    async def execute_with_retry(
        self,
        operation: Callable[[], Coroutine[Any, Any, T]],
        operation_name: str = "task_operation",
    ) -> T:
        retries = 0
        backoff = self.initial_backoff

        while True:
            try:
                return await operation()
            except Exception as e:
                retries += 1
                if retries > self.max_retries:
                    logger.error(f"Operation '{operation_name}' failed after {retries} attempts: {e}")
                    raise
                logger.warning(
                    f"Operation '{operation_name}' failed (attempt {retries}/{self.max_retries}). Retrying in {backoff:.2f}s: {e}"
                )
                await asyncio.sleep(backoff)
                backoff *= self.backoff_multiplier
