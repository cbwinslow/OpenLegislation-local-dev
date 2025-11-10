class _Connection:
    def cursor(self):
        return None


def connect(*args, **kwargs):  # pragma: no cover - test stub
    return _Connection()
