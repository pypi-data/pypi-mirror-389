from .imports import *


# --- Base remote checker -----------------------------------------------------
def _remote_test(path: str, test_flag: str, user_at_host: str, timeout: int = 5) -> bool:
    """
    Run a remote shell test (e.g. -f, -d) via SSH.
    Returns True if test succeeds, False otherwise.
    """
    cmd = f"[ {test_flag} {shlex.quote(path)} ] && echo 1 || echo 0"
    try:
        result = subprocess.check_output(
            ["ssh", user_at_host, cmd],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=timeout
        ).strip()
        return result == "1"
    except Exception:
        return False


# --- Individual path checks --------------------------------------------------
def is_remote_file(path: str, user_at_host: str) -> bool:
    """True if remote path is a file."""
    return _remote_test(path, "-f", user_at_host)


def is_remote_dir(path: str, user_at_host: str) -> bool:
    """True if remote path is a directory."""
    return _remote_test(path, "-d", user_at_host)


def is_local_file(path: str) -> bool:
    """True if local path is a file."""
    return os.path.isfile(path)


def is_local_dir(path: str) -> bool:
    """True if local path is a directory."""
    return os.path.isdir(path)


# --- Unified interface -------------------------------------------------------
def is_file(path: str,*args, user_at_host: Optional[str] = None,**kwargs) -> bool:
    """Determine if path is a file (works local or remote)."""
    if user_at_host:
        return is_remote_file(path, user_at_host)
    return is_local_file(path)


def is_dir(path: str, *args,user_at_host: Optional[str] = None,**kwargs) -> bool:
    """Determine if path is a directory (works local or remote)."""
    if user_at_host:
        return is_remote_dir(path, user_at_host)
    return is_local_dir(path)


# --- Optional: keep your original all-in-one wrapper ------------------------
def check_path_type(
    path: str,
    user_at_host: Optional[str] = None,
) -> str:
    """
    Return 'file', 'directory', 'missing', or 'unknown'.
    Uses isolated is_file/is_dir functions.
    """
    if user_at_host:
        if is_remote_file(path, user_at_host):
            return "file"
        elif is_remote_dir(path, user_at_host):
            return "directory"
        else:
            return "missing"
    else:
        if os.path.isfile(path):
            return "file"
        elif os.path.isdir(path):
            return "directory"
        elif not os.path.exists(path):
            return "missing"
        return "unknown"
