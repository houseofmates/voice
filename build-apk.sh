#!/bin/bash
# build voice apk for android using buildozer
# 
# STATUS: not currently buildable via python-for-android.
# gradio and its node-based dependencies don't have android arm64 wheels,
# and cross-compiling them is not feasible with current tooling.
#
# ALTERNATIVE: run voice on android via termux:
#   pkg install python portaudio
#   pip install -r requirements.txt
#   python app.py --server-name 0.0.0.0
#   then open http://localhost:8765 in any browser
#
# for a native android app, the gradio ui would need to be wrapped in a
# webview (which is what this apk would ultimately do), but the python
# backend with torch can't be cross-compiled for arm64 without
# significant android ndk + recipe work.

set -e

cd "$(dirname "$0")"
APP_DIR="$(pwd)"
RELEASE_DIR="$APP_DIR/releases"
VERSION="${VERSION:-$(date +%Y%m%d)}"

echo "==> voice apk build (v$VERSION)"
echo "==>"
echo "==> note: buildozer / python-for-android cannot cross-compile gradio"
echo "==> and its web dependencies for android arm64. this is a known"
echo "==> limitation of the toolchain, not of voice itself."
echo "==>"
echo "==> to run on android instead:"
echo "==>   1. install termux from f-droid"
echo "==>   2. pkg install python portaudio"
echo "==>   3. pip install -r requirements.txt"
echo "==>   4. python app.py --server-name 0.0.0.0"
echo "==>   5. open http://localhost:8765 in a browser"
echo "==>"
echo "==> creating placeholder documentation..."

mkdir -p "$RELEASE_DIR"
cat > "$RELEASE_DIR/ANDROID_RUN.md" << 'EOF'
# running voice on android

## option 1: termux (recommended)

install termux from f-droid (not google play — play store version is outdated):

```
pkg update && pkg upgrade
pkg install python portaudio
pip install --break-system-packages -r requirements.txt
python app.py --server-name 0.0.0.0
```

then open http://localhost:8765 in any browser on your device.

## option 2: local network

run on your desktop with `--share` to get a public gradio link,
then open that link on your phone:

```
python app.py --share
```

this works with the full torch/rvc pipeline since processing happens
on the desktop — your phone is just a remote control.

## limitations

- torch doesn't run on android (no arm64 wheels)
- real-time audio processing requires desktop hardware
- soundboard recording needs a microphone
EOF

echo "==> done. see $RELEASE_DIR/ANDROID_RUN.md for android instructions."