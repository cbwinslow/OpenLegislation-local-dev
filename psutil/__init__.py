class _VirtualMemory:
    percent = 0


def cpu_percent(interval=None):  # pragma: no cover - stub
    return 0.0


def virtual_memory():  # pragma: no cover - stub
    return _VirtualMemory()


class _NetIO:
    bytes_sent = 0
    bytes_recv = 0


def net_io_counters():  # pragma: no cover - stub
    return _NetIO()


def cpu_count(logical=True):  # pragma: no cover - stub
    return 4
