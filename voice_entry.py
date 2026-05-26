"""entry point for pyinstaller build — starts the voice app."""
import sys, os

# ensure the app dir is in the path
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

# patch sounddevice portaudio path for bundled lib
import sounddevice as sd
# add bundled portaudio to LD path if present
bundled_pa = os.path.join(os.getcwd(), "libportaudio.so.2")
if os.path.exists(bundled_pa):
    os.environ["LD_LIBRARY_PATH"] = os.getcwd() + ":" + os.environ.get("LD_LIBRARY_PATH", "")

# import and run the app
from app import launch_gradio, get_value_from_args, DEFAULT_SERVER_NAME, DEFAULT_PORT

if __name__ == "__main__":
    port = int(get_value_from_args("--port", DEFAULT_PORT))
    server = get_value_from_args("--server-name", DEFAULT_SERVER_NAME)
    launch_gradio(server, port)
