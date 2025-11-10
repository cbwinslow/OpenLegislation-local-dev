import asyncio


class _FakeConnection:
    async def close(self):
        """
        Close the fake connection without performing any I/O or modifying internal state.
        """
        return None


async def connect(*args, **kwargs):  # pragma: no cover - test stub
    """
    Provide a minimal fake connection object intended for testing.
    
    Any positional and keyword arguments are accepted but ignored; this function always returns a fresh _FakeConnection instance that implements a no-op async close() method.
    
    Returns:
        _FakeConnection: A test stub connection whose `close()` coroutine performs no operation.
    """
    return _FakeConnection()