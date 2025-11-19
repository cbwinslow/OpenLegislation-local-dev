import asyncio


class _FakeConnection:
    async def close(self):
        return None


async def connect(*args, **kwargs):  # pragma: no cover - test stub
    return _FakeConnection()
