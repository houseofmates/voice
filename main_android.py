"""lightweight android entry point.
torch/rvc not available on android — this provides tts, soundboard, and settings only.
"""

import os, sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

# patch out torch imports at module level before app.py tries to load them
import builtins

_original_import = builtins.__import__


def _no_torch_import(name, *args, **kwargs):
    if name.startswith(
        ("torch", "torchaudio", "torchvision", "torchcrepe", "torchfcpe")
    ):
        raise ImportError(f"{name} not available on android")
    return _original_import(name, *args, **kwargs)


builtins.__import__ = _no_torch_import

# stub out modules app.py tries to import
import types

for stub_name in ["rvc.lib.zluda", "rvc.lib.platform"]:
    sys.modules[stub_name] = types.ModuleType(stub_name)

# disable prerequisites download (no torch needed)
os.environ["VOICE_NO_TORCH"] = "1"

print("voice android — starting server...")
import gradio as gr

# import the app module (will handle torch absence gracefully)
from app import VoiceApp

VoiceApp.launch(server_name="0.0.0.0", server_port=8765, share=False)
