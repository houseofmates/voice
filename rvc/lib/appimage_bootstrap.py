"""
appimage bootstrap — redirects writable paths when running from read-only fs.

gradio apps typically run from read-only appimage mounts.
this module intercepts os.makedirs and os.open to redirect writes to ~/.voice/.
"""
import os
import functools

# throwaway import to prevent cycles
_original_makedirs = os.makedirs
_original_open = open

# cache: once we determine cwd is readonly, all subsequent calls skip the check
_cwd_is_readonly = None


def _voice_home():
    return os.environ.get("VOICE_DATA_DIR") or os.path.join(
        os.path.expanduser("~"), ".voice"
    )


def _is_readonly():
    global _cwd_is_readonly
    if _cwd_is_readonly is None:
        try:
            _cwd_is_readonly = not os.access(os.getcwd(), os.W_OK)
        except OSError:
            _cwd_is_readonly = True
    return _cwd_is_readonly


def _relocate(path):
    """relocate a writable path from read-only fs to ~/.voice/."""
    if not _is_readonly():
        return path
    home = _voice_home()
    cwd = os.getcwd()
    try:
        rel = os.path.relpath(path, cwd)
        if not rel.startswith(".."):
            return os.path.normpath(os.path.join(home, rel))
    except (ValueError, OSError):
        pass
    return path


def _patched_makedirs(path, mode=0o777, exist_ok=False):
    redirected = _relocate(path)
    if redirected != path:
        # when redirecting, always exist_ok=True since the dir might
        # have been pre-created by the AppRun
        return _original_makedirs(redirected, mode, exist_ok=True)
    return _original_makedirs(path, mode, exist_ok=exist_ok)


def init():
    """call this at the very start of app.py (before any app imports)."""
    # only activate when running from read-only fs (appimage mode)
    if _is_readonly():
        global _original_open
        voice_home = _voice_home()
        os.makedirs = _patched_makedirs

        # also intercept builtins.open for paths on the readonly mount
        import builtins
        _original_open = builtins.open

        def _patched_open(file, mode="r", *args, **kwargs):
            if "w" in mode or "a" in mode or "x" in mode or "+" in mode:
                redirected = _relocate(file)
                if redirected != file:
                    os.makedirs(os.path.dirname(redirected), exist_ok=True)
                    return _original_open(redirected, mode, *args, **kwargs)
            return _original_open(file, mode, *args, **kwargs)

        builtins.open = _patched_open