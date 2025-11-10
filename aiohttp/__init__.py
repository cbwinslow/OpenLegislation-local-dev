class ClientSession:
    def __init__(self, *args, **kwargs):
        """
        Initialize the stub object, accepting and ignoring any positional and keyword arguments.
        
        Parameters:
            *args: Positional arguments accepted for compatibility and ignored.
            **kwargs: Keyword arguments accepted for compatibility and ignored.
        """
        pass

    async def __aenter__(self):  # pragma: no cover - stub
        """
        Enter the asynchronous context and yield the session instance.
        
        Returns:
            self: The ClientSession instance to be used within the context.
        """
        return self

    async def __aexit__(self, exc_type, exc, tb):  # pragma: no cover - stub
        """
        Exit the context manager without suppressing exceptions.
        
        Returns:
            False: Indicates that any exception raised in the context should be propagated.
        """
        return False

    async def get(self, *args, **kwargs):  # pragma: no cover - stub
        """
        Attempting to perform an HTTP GET using this stub raises an error indicating network calls are unsupported.
        
        Raises:
            RuntimeError: Always raised with the message "aiohttp stub does not support network calls".
        """
        raise RuntimeError("aiohttp stub does not support network calls")

    async def close(self):  # pragma: no cover - stub
        """
        Close the client session.
        
        No-op in this stub implementation for API compatibility.
        """
        return None


class TCPConnector:
    def __init__(self, *args, **kwargs):
        """
        Initialize the stub object, accepting and ignoring any positional and keyword arguments.
        
        Parameters:
            *args: Positional arguments accepted for compatibility and ignored.
            **kwargs: Keyword arguments accepted for compatibility and ignored.
        """
        pass