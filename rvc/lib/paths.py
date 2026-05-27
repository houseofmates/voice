"""path resolution for voice — handles appimage read-only fs."""

import os


def data_path(subdir: str = "") -> str:
    """return a writable path under the voice data directory.

    when running from AppImage, os.getcwd() points to a read-only mount.
    this redirects writable storage to ~/.voice/.
    """
    base = os.environ.get("VOICE_DATA_DIR", os.getcwd())
    if subdir:
        path = os.path.join(base, subdir)
        os.makedirs(path, exist_ok=True)
        return path
    return base


def app_path(subdir: str = "") -> str:
    """return a path under the voice application directory.

    use this for reading bundled assets/models that ship with the app.
    """
    base = os.environ.get("VOICE_APP_DIR", os.getcwd())
    if subdir:
        return os.path.join(base, subdir)
    return base


def embedder_root() -> str:
    """return the custom embedder directory (writable, for downloaded embedders)."""
    return data_path(os.path.join("rvc", "models", "embedders", "embedders_custom"))


def models_root() -> str:
    """return the models/logs directory (writable, for trained models)."""
    return data_path("logs")


def init_dirs() -> None:
    """create all required writable directories at ~/.voice/."""
    voice_home = os.path.join(os.path.expanduser("~"), ".voice")
    os.environ.setdefault("VOICE_DATA_DIR", voice_home)
    dirs = [
        os.path.join(voice_home, "logs", "zips"),
        os.path.join(voice_home, "models"),
        os.path.join(voice_home, "assets", "audios"),
        os.path.join(voice_home, "assets", "presets"),
        os.path.join(voice_home, "rvc", "models", "embedders", "embedders_custom"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
