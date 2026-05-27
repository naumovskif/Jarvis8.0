"""
Priority request queue for API calls with fairness scheduling.
Prevents request storms and ensures important requests get through.
"""

import time
import threading
from queue import PriorityQueue, Queue, Empty
from typing import Any, Callable, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid


class RequestPriority(Enum):
    """Request priority levels."""
    CRITICAL = 0  # User-facing, immediate
    HIGH = 1      # Important operations
    NORMAL = 2    # Regular API calls
    LOW = 3       # Background, can wait
    DEFERRED = 4  # Can retry later


@dataclass(order=True)
class QueuedRequest:
    """Request to be executed."""
    priority: int = field(compare=True)
    timestamp: float = field(compare=True)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()), compare=False)
    model: str = field(default="", compare=False)
    executor: Callable = field(default=None, compare=False)
    timeout: float = field(default=30.0, compare=False)
    max_retries: int = field(default=3, compare=False)


class RequestQueue:
    """
    Priority queue for API requests with:
    - Priority levels (critical > high > normal > low > deferred)
    - Fairness scheduling (prevents starving lower priorities)
    - Timeout handling
    - Retry management
    - Request tracking
    """

    def __init__(
        self,
        max_queue_size: int = 1000,
        worker_threads: int = 3,
        fairness_interval: int = 10,
    ):
        """
        Args:
            max_queue_size: Max queued requests
            worker_threads: Concurrent worker threads
            fairness_interval: Process some low-priority after N high-priority
        """
        self._queue: PriorityQueue[QueuedRequest] = PriorityQueue(maxsize=max_queue_size)
        self._max_queue = max_queue_size
        self._workers_count = worker_threads
        self._fairness_interval = fairness_interval
        self._running = False
        self._workers = []
        self._results: dict[str, Any] = {}
        self._in_progress: set[str] = set()
        self._failed: dict[str, Tuple[int, str]] = {}  # id -> (attempts, error)
        self._stats = {
            "queued": 0,
            "processed": 0,
            "failed": 0,
            "retried": 0,
        }
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start worker threads."""
        if self._running:
            return
        self._running = True
        for i in range(self._workers_count):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"RequestQueueWorker-{i}",
                daemon=True
            )
            worker.start()
            self._workers.append(worker)
        print(f"[RequestQueue] ✅ Started {self._workers_count} workers")

    def stop(self, timeout: float = 5.0) -> None:
        """Stop worker threads gracefully."""
        self._running = False
        for worker in self._workers:
            worker.join(timeout=timeout / len(self._workers))
        self._workers.clear()
        print("[RequestQueue] ⏹️  Stopped all workers")

    def enqueue(
        self,
        executor: Callable,
        model: str = "default",
        priority: RequestPriority = RequestPriority.NORMAL,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> str:
        """
        Enqueue request for execution.
        Returns: request_id for tracking
        """
        request = QueuedRequest(
            priority=priority.value,
            timestamp=time.time(),
            model=model,
            executor=executor,
            timeout=timeout,
            max_retries=max_retries,
        )

        try:
            self._queue.put_nowait(request)
            with self._lock:
                self._stats["queued"] += 1
            return request.request_id
        except Exception as e:
            print(f"[RequestQueue] ❌ Enqueue failed: {e}")
            raise

    def _worker_loop(self) -> None:
        """Main worker loop."""
        low_priority_count = 0

        while self._running:
            try:
                # Fairness: occasionally process low priority
                process_low = (low_priority_count % self._fairness_interval) == 0
                timeout = 0.5 if not process_low else 0.1

                request = self._queue.get(timeout=timeout)

                # Skip low priority if fairness not due
                if not process_low and request.priority > RequestPriority.NORMAL.value:
                    self._queue.put(request)
                    low_priority_count += 1
                    continue

                self._execute_request(request)
                low_priority_count = 0

            except Empty:
                low_priority_count = 0
                continue
            except Exception as e:
                print(f"[RequestQueue] ⚠️ Worker error: {e}")

    def _execute_request(self, request: QueuedRequest) -> None:
        """Execute a single request with retry logic."""
        with self._lock:
            if request.request_id in self._in_progress:
                # Prevent duplicate execution
                self._queue.put(request)
                return
            self._in_progress.add(request.request_id)

        attempt = 0
        last_error = None

        while attempt < request.max_retries:
            attempt += 1
            try:
                result = request.executor()
                with self._lock:
                    self._results[request.request_id] = result
                    self._in_progress.discard(request.request_id)
                    self._stats["processed"] += 1
                return

            except Exception as e:
                last_error = str(e)
                if attempt < request.max_retries:
                    wait = 2 ** (attempt - 1)  # Exponential backoff
                    time.sleep(min(wait, 30))
                with self._lock:
                    self._stats["retried"] += 1

        # All retries failed
        with self._lock:
            self._failed[request.request_id] = (attempt, last_error)
            self._in_progress.discard(request.request_id)
            self._stats["failed"] += 1
            print(
                f"[RequestQueue] ❌ Request {request.request_id[:8]} failed after "
                f"{attempt} attempts: {last_error}"
            )

    def wait_for_result(
        self,
        request_id: str,
        timeout: float = 30.0,
    ) -> Optional[Any]:
        """
        Block until result is available.
        Returns: result or None if timeout/failed
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                if request_id in self._results:
                    return self._results.pop(request_id)
                if request_id in self._failed:
                    attempt, error = self._failed.pop(request_id)
                    raise RuntimeError(f"Request failed after {attempt} attempts: {error}")

            time.sleep(0.1)

        raise TimeoutError(f"Request {request_id[:8]} timed out")

    def try_result(self, request_id: str) -> Optional[Any]:
        """Get result if available (non-blocking)."""
        with self._lock:
            return self._results.pop(request_id, None)

    def cancel(self, request_id: str) -> bool:
        """Try to cancel queued request."""
        with self._lock:
            if request_id in self._in_progress:
                return False  # Already executing
            return True

    def queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    def get_stats(self) -> dict:
        """Get queue statistics."""
        with self._lock:
            return {
                "queue_size": self._queue.qsize(),
                "max_size": self._max_queue,
                "in_progress": len(self._in_progress),
                "workers": self._workers_count,
                "stats": self._stats.copy(),
            }

    def reset_stats(self) -> None:
        """Reset statistics."""
        with self._lock:
            for key in self._stats:
                self._stats[key] = 0


# Global instance
_request_queue: Optional[RequestQueue] = None
_queue_lock = threading.Lock()


def get_request_queue() -> RequestQueue:
    """Get or create global request queue."""
    global _request_queue
    if _request_queue is None:
        with _queue_lock:
            if _request_queue is None:
                _request_queue = RequestQueue()
                _request_queue.start()
    return _request_queue
