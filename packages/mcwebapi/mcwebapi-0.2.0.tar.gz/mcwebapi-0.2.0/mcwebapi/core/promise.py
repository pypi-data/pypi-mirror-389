import time
from typing import Any, Callable, Optional, List


class Promise:
    """
    A simple Promise implementation for handling async operations.

    Similar to JavaScript promises, allows chaining callbacks and waiting
    for async operations to complete.
    """

    def __init__(self, timeout: float = 10.0):
        self.result: Optional[Any] = None
        self.error: Optional[Exception] = None
        self._completed = False
        self._callbacks: List[Callable] = []
        self._timeout = timeout
        self._timed_out = False

    def then(self, callback: Callable) -> "Promise":
        """
        Add a callback to be called when the promise is resolved.

        Args:
            callback: Function to call with the result

        Returns:
            Self for chaining
        """
        if self._completed:
            callback(self.result)
        else:
            self._callbacks.append(callback)
        return self

    def wait(self) -> Any:
        """
        Wait synchronously for the promise to complete.

        Returns:
            The result of the operation

        Raises:
            TimeoutError: If the operation times out
            Exception: If the operation fails
        """
        start_time = time.time()
        while not self._completed and not self._timed_out:
            if time.time() - start_time > self._timeout:
                self._timed_out = True
                raise TimeoutError("Promise timeout exceeded")
            time.sleep(0.01)

        if self.error:
            raise self.error
        return self.result

    def resolve(self, result: Any) -> None:
        """Resolve the promise with a result."""
        self.result = result
        self._completed = True
        for callback in self._callbacks:
            callback(result)

    def reject(self, error: Exception) -> None:
        """Reject the promise with an error."""
        self.error = error
        self._completed = True

    def is_completed(self) -> bool:
        """Check if the promise has been completed."""
        return self._completed

    def is_successful(self) -> bool:
        """Check if the promise was resolved successfully."""
        return self._completed and self.error is None