class ClientSession:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):  # pragma: no cover - stub
        return self

    async def __aexit__(self, exc_type, exc, tb):  # pragma: no cover - stub
        return False

    async def get(self, *args, **kwargs):  # pragma: no cover - stub
        raise RuntimeError("aiohttp stub does not support network calls")

    async def close(self):  # pragma: no cover - stub
        return None


class TCPConnector:
    def __init__(self, *args, **kwargs):
        pass
