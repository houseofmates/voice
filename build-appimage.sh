#!/bin/bash
# build voice appimage — bundles a complete python venv + app into a portable appimage
# uses venv-bundling instead of pyinstaller (gradio 6's dynamic imports don't work with pyinstaller)
set -e

cd "$(dirname "$0")"
APP_DIR="$(pwd)"
RELEASE_DIR="$APP_DIR/releases"
VERSION="${VERSION:-$(date +%Y%m%d)}"
VENV_DIR="/tmp/voice-appimage-venv-$VERSION"
APPDIR="$APP_DIR/dist/Voice.AppDir"

echo "==> building voice appimage (v$VERSION)"

# 1. create a fresh venv
rm -rf "$VENV_DIR"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# 2. install deps — includes torch for RVC voice conversion
echo "==> installing dependencies..."
pip install --quiet --upgrade pip wheel setuptools
pip install --quiet gradio numpy scipy soundfile sounddevice librosa \
    requests tqdm wget edge-tts beautifulsoup4 psutil noisereduce \
    pedalboard stftpitchshift soxr einops transformers \
    matplotlib tensorboard tensorboardX pypresence Pillow \
    torch torchaudio torchvision \
    resampy pandas faiss-cpu torchcrepe torchfcpe webrtcvad

echo "==> dependencies installed ($(du -sh $VENV_DIR | cut -f1))"

# 3. strip the venv to reduce size
echo "==> stripping..."
find "$VENV_DIR" -name "*.pyc" -delete
# keep torch — needed for RVC voice conversion
# only strip test dirs and cache
find "$VENV_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$VENV_DIR/lib" -name "test" -type d -exec rm -rf {} + 2>/dev/null || true
find "$VENV_DIR/lib" -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true

echo "==> stripped ($(du -sh $VENV_DIR | cut -f1))"

# 4. build AppDir
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# copy venv
cp -r "$VENV_DIR" "$APPDIR/usr/venv"

# copy app files (everything except .git, __pycache__, etc.)
rsync -a --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='build.log' --exclude='dist' --exclude='releases' \
    --exclude='.buildozer' --exclude='*.AppImage' \
    "$APP_DIR/" "$APPDIR/usr/voice/"

# create launcher script
mkdir -p "$APPDIR/usr/bin"
cat > "$APPDIR/usr/bin/voice" << 'LAUNCHER'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
# use PYTHONPATH to point to bundled packages, system python3 for the interpreter
export PYTHONPATH="${HERE}/../venv/lib/python3.14/site-packages:${PYTHONPATH}"
export LD_LIBRARY_PATH="${HERE}/../venv/lib:${LD_LIBRARY_PATH}"
cd "${HERE}/../voice"
exec python3 app.py "$@"
LAUNCHER
chmod +x "$APPDIR/usr/bin/voice"

# copy portaudio — try system first, fallback to compiling from source
PORTAUDIO_SRC=""
for pa in /usr/lib/x86_64-linux-gnu/libportaudio.so.2 /usr/lib/libportaudio.so.2; do
    if [ -f "$pa" ]; then
        PORTAUDIO_SRC="$pa"
        break
    fi
done
if [ -n "$PORTAUDIO_SRC" ]; then
    cp "$PORTAUDIO_SRC" "$APPDIR/usr/venv/lib/"
    echo "==> portaudio bundled (system)"
else
    echo "==> portaudio not found in system, compiling from source..."
    mkdir -p /tmp/portaudio-build
    cd /tmp/portaudio-build
    # download portaudio source — wget to local file, not external url (use embedded)
    # bundling a pre-compiled .so is simpler than requiring a full build chain
    # since build tools may not be available on all systems, skip compilation
    echo "==> portaudio compilation skipped — install portaudio19-dev for audio support"
    echo "    audio will degrade gracefully without libportaudio"
    cd "$APP_DIR"
    rm -rf /tmp/portaudio-build
fi

# copy system libs needed for audio
for lib in libsndfile.so.1; do
    found=$(find /usr/lib -name "$lib" 2>/dev/null | head -1)
    if [ -n "$found" ]; then
        cp "$found" "$APPDIR/usr/venv/lib/"
    fi
done

# create desktop file
cat > "$APPDIR/usr/share/applications/voice.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Voice
Comment=real-time voice changer — feel like you. sound like home.
Exec=voice
Icon=voice
Categories=AudioVideo;
Terminal=false
EOF

# create icons
cp "$APP_DIR/icon.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/voice.png"
cp "$APP_DIR/icon.png" "$APPDIR/.DirIcon"
cp "$APP_DIR/icon.png" "$APPDIR/voice.png"
cp "$APPDIR/usr/share/applications/voice.desktop" "$APPDIR/"

# create AppRun
cat > "$APPDIR/AppRun" << 'APPRUN'
#!/bin/bash
set -e
HERE="$(dirname "$(readlink -f "${0}")")"
HOME="${HOME:?}"
VOICE_HOME="${HOME}/.voice"

# create all writable data dirs ahead of time
mkdir -p "${VOICE_HOME}/logs/zips" "${VOICE_HOME}/logs/weights"
mkdir -p "${VOICE_HOME}/models"
mkdir -p "${VOICE_HOME}/assets/audios" "${VOICE_HOME}/assets/datasets" "${VOICE_HOME}/assets/presets"
mkdir -p "${VOICE_HOME}/rvc/models/embedders/embedders_custom"
mkdir -p "${VOICE_HOME}/rvc/models/pretraineds/custom"

# tell the appimage bootstrap where to redirect writes
export VOICE_DATA_DIR="${VOICE_HOME}"

# set up python and library paths
export PYTHONPATH="${HERE}/usr/venv/lib/python3.14/site-packages:${PYTHONPATH}"
export LD_LIBRARY_PATH="${HERE}/usr/venv/lib:${LD_LIBRARY_PATH}"

# run from the app mount (needed for import resolution)
cd "${HERE}/usr/voice"
exec python3 app.py "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

# 5. build appimage
echo "==> building appimage (this compresses the venv — may take a minute)..."
/tmp/appimagetool --no-appstream "$APPDIR" "$RELEASE_DIR/Voice-${VERSION}-x86_64.AppImage" 2>&1

# 6. cleanup
rm -rf "$VENV_DIR" "$APPDIR"

echo "==> done!"
ls -lh "$RELEASE_DIR/Voice-${VERSION}-x86_64.AppImage"