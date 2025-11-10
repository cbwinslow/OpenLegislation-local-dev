class _VirtualMemory:
    percent = 0


def cpu_percent(interval=None):  # pragma: no cover - stub
    """
    Report system CPU utilization as a percentage.
    
    Parameters:
        interval (float | None): Sampling interval in seconds; accepted but ignored by this implementation.
    
    Returns:
        float: `0.0`, representing the CPU utilization percentage.
    """
    return 0.0


def virtual_memory():  # pragma: no cover - stub
    """
    Provide a _VirtualMemory object representing current virtual memory usage.
    
    Returns:
        _VirtualMemory: A new instance with default attributes (percent initialized to 0).
    """
    return _VirtualMemory()


class _NetIO:
    bytes_sent = 0
    bytes_recv = 0


def net_io_counters():  # pragma: no cover - stub
    """
    Return a simple network I/O counters snapshot.
    
    Returns:
        _NetIO: Object with attributes `bytes_sent` and `bytes_recv`, both initialized to 0.
    """
    return _NetIO()


def cpu_count(logical=True):  # pragma: no cover - stub
    """
    Report the number of CPUs available on the system.
    
    Parameters:
        logical (bool): If True, return the count of logical (including hyperthreaded) CPUs;
            if False, return the count of physical CPU cores.
    
    Returns:
        int: The CPU count. This implementation returns 4.
    """
    return 4