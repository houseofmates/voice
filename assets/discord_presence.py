from pypresence import Presence
import datetime as dt


class RichPresenceManager:
    def __init__(self):
        self.client_id = "1144714449563955302"
        self.rpc = None
        self.running = False

    def start_presence(self):
        if not self.running:
            self.running = True
            self.rpc = Presence(self.client_id)
            try:
                self.rpc.connect()
                self.update_presence()
            except KeyboardInterrupt as error:
                print(error)
                self.rpc = None
                self.running = False
            except FileNotFoundError:
                print("Discord/Equicord not found — presence disabled.")
                self.rpc = None
                self.running = False
            except ConnectionRefusedError:
                print("Discord/Equicord IPC refused — presence disabled.")
                self.rpc = None
                self.running = False
            except Exception as error:
                print(f"Could not detect Discord or Equicord running: {error}")
                self.rpc = None
                self.running = False

    def update_presence(self):
        if self.rpc:
            self.rpc.update(
                state="voice — your voice, your home",
                details="real-time voice changer",
                buttons=[
                    {"label": "github", "url": "https://github.com/houseofmates/voice"},
                ],
                large_image="logo",
                large_text="voice changer",
                start=dt.datetime.now().timestamp(),
            )

    def stop_presence(self):
        self.running = False
        if self.rpc:
            self.rpc.close()
            self.rpc = None


RPCManager = RichPresenceManager()
