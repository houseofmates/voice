#!/data/data/com.termux/files/usr/bin/bash
# voice on android — termux setup script
# run this inside termux to install dependencies and start voice
set -e

echo "==> voice android setup (termux)"
echo ""

# update packages
pkg update -y && pkg upgrade -y

# install core deps
pkg install -y python portaudio python-numpy python-scipy python-librosa \
    python-pillow build-essential binutils rust

# install pip deps
pip install --break-system-packages gradio requests tqdm edge-tts \
    beautifulsoup4 psutil soundfile sounddevice noisereduce

echo ""
echo "==> dependencies installed!"
echo "==> to start voice, run:"
echo ""
echo "    python app.py --server-name 0.0.0.0"
echo ""
echo "==> then open http://localhost:8765 in any browser on your device"
echo "==> or use another device on the same network: http://$(ip -4 addr show wlan0 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1):8765"
echo ""