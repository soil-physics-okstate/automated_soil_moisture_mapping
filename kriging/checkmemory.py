def checkmemory(pred):
    """
    checkmemory(pred)
    -----------------
    Checks whether there is enough memory for a kriging routine, mirroring the MATLAB
    function's behavior.

    Input
    -----
    pred : sequence-like
        Array of points to be predicted in kriging.

    Output
    ------
    x : int
        1 if enough memory is available (or if not on Windows, to match original behavior),
        0 otherwise.

    Notes
    -----
    - On Windows, this approximates MATLAB's `memory().MaxPossibleArrayBytes` check by
      querying available virtual/physical memory via the Win32 API.
    - On non-Windows systems, returns 1 (to match the MATLAB code's behavior where it
      forces true so it can run in the cloud).
    """
    # Required bytes for an (len(pred) x len(pred)) double-precision array
    try:
        n = len(pred)
    except TypeError:
        # If pred isn't sized (e.g., a scalar), treat it as length 1
        n = 1
    required_bytes = (n ** 2) * 8  # 8 bytes per double

    import platform
    if platform.system().lower() == "windows":
        # Use Win32 GlobalMemoryStatusEx via ctypes (no external deps)
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ok = ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        if not ok:
            # If the API call fails, default to allowing (mirrors MATLAB's non-PC path).
            return 1

        # Approximate the largest allocatable block using available virtual or physical memory.
        # This is an approximation of MATLAB's MaxPossibleArrayBytes.
        max_possible_array_bytes = max(stat.ullAvailVirtual, stat.ullAvailPhys)

        return 1 if required_bytes <= max_possible_array_bytes else 0
    else:
        # Match MATLAB version: force true on non-Windows so it runs in the cloud.
        return 1