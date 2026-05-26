#!/bin/bash
# build voice appimage — bundles python + deps + app into a portable executable
set -e

cd "$(dirname "$0")"
APP_DIR="$(pwd)"
RELEASE_DIR="$APP_DIR/releases"
VERSION="${VERSION:-$(date +%Y%m%d)}"

echo "==> building voice appimage (v$VERSION)"

# 1. ensure pyinstaller
pip3 install --break-system-packages pyinstaller 2>/dev/null || true

# 2. create a bootstrap entry point that pyinstaller can follow
cat > /tmp/voice_entry.py << 'EOF'
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
EOF

cp /tmp/voice_entry.py "$APP_DIR/voice_entry.py"

# 3. run pyinstaller
echo "==> pyinstaller bundling (this takes a while with torch)..."
pyinstaller \
    --onedir \
    --name "voice" \
    --add-data "$APP_DIR/assets:assets" \
    --add-data "$APP_DIR/rvc:rvc" \
    --add-data "$APP_DIR/tabs:tabs" \
    --add-data "$APP_DIR/models:models" \
    --add-data "$APP_DIR/assets/pwa:assets/pwa" \
    --add-data "$APP_DIR/icon.png:." \
    --add-data "$APP_DIR/requirements.txt:." \
    --add-data "$APP_DIR/LICENSE:." \
    --add-data "$APP_DIR/TERMS_OF_USE.md:." \
    --hidden-import "gradio" \
    --hidden-import "sounddevice" \
    --hidden-import "soundfile" \
    --hidden-import "librosa" \
    --hidden-import "scipy" \
    --hidden-import "numpy" \
    --hidden-import "torch" \
    --hidden-import "torchaudio" \
    --hidden-import "einops" \
    --hidden-import "transformers" \
    --hidden-import "matplotlib" \
    --hidden-import "tensorboardX" \
    --hidden-import "edge_tts" \
    --hidden-import "pypresence" \
    --hidden-import "psutil" \
    --hidden-import "noisereduce" \
    --hidden-import "pedalboard" \
    --hidden-import "soxr" \
    --hidden-import "stftpitchshift" \
    --hidden-import "PIL" \
    --hidden-import "webrtcvad" \
    --hidden-import "requests" \
    --hidden-import "tqdm" \
    --collect-all "torch" \
    --collect-all "torchaudio" \
    --collect-all "gradio" \
    --collect-all "sounddevice" \
    --collect-all "transformers" \
    --exclude-module "webrtcvad" \
    --noconfirm \
    "$APP_DIR/voice_entry.py" >> "$APP_DIR/build.log" 2>&1

echo "==> pyinstaller done"

# 4. copy portaudio lib into the bundle (needed for sounddevice)
BUNDLE_DIR="$APP_DIR/dist/voice"
if [ -f "/usr/lib/x86_64-linux-gnu/libportaudio.so.2" ]; then
    cp /usr/lib/x86_64-linux-gnu/libportaudio.so.2 "$BUNDLE_DIR/"
elif [ -f "/usr/lib/libportaudio.so.2" ]; then
    cp /usr/lib/libportaudio.so.2 "$BUNDLE_DIR/"
fi
# also copy any other needed system libs
for lib in libsndfile.so.1 libstdc++.so.6; do
    find /usr/lib -name "$lib" -exec cp {} "$BUNDLE_DIR/" \; 2>/dev/null || true
done

# 5. create AppDir structure
APPDIR="$APP_DIR/dist/Voice.AppDir"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# move pyinstaller bundle into AppDir
cp -r "$BUNDLE_DIR"/* "$APPDIR/usr/bin/"
cp "$APP_DIR/icon.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/voice.png"

# create desktop file
cat > "$APPDIR/usr/share/applications/voice.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Voice
Comment=real-time voice changer — feel like you. sound like home.
Exec=voice
Icon=voice
Categories=Audio;Multimedia;
Terminal=false
EOF

# create AppRun
cat > "$APPDIR/AppRun" << 'APPRUN'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:$PATH"
export LD_LIBRARY_PATH="${HERE}/usr/bin:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/voice" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

# create .DirIcon
cp "$APP_DIR/icon.png" "$APPDIR/.DirIcon"
cp "$APP_DIR/icon.png" "$APPDIR/voice.png"

# 6. build the appimage
echo "==> building appimage..."
cp "$APPDIR/usr/share/applications/voice.desktop" "$APPDIR/voice.desktop"
ARCH=x86_64 /tmp/appimagetool --no-appstream "$APPDIR" "$RELEASE_DIR/Voice-${VERSION}-x86_64.AppImage" >> "$APP_DIR/build.log" 2>&1

# 7. cleanup
rm -f "$APP_DIR/voice_entry.py" "$APP_DIR/voice.spec"
rm -rf "$APP_DIR/build" "$APP_DIR/dist"

echo "==> done! appimage at: $RELEASE_DIR/Voice-${VERSION}-x86_64.AppImage"
ls -lh "$RELEASE_DIR/"