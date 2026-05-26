"""Voice - A Cozy All-in-One Voice Changer
A warm, safe, real-time voice changer for voice dysphoria support.
Fork of Applio (https://github.com/IAHispano/Applio), redesigned for comfort.
Core RVC voice conversion functionality is preserved.
"""

from rvc.lib.platform import platform_config
platform_config()

from rvc.lib import paths as _paths
from rvc.lib.appimage_bootstrap import init as _appimage_init
_appimage_init()

import gradio as gr
import sys
import os
import pathlib
import logging
import json
from typing import Any

DEFAULT_SERVER_NAME = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_PORT_ATTEMPTS = 10

logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

now_dir = os.getcwd()
sys.path.append(now_dir)

# -- appimage writable path fix (handled by AppRun symlinks) --
import logging

if sys.platform == "win32":
    import asyncio.proactor_events as _pe
    _orig_ccl = _pe._ProactorBasePipeTransport._call_connection_lost
    def _ccl_patched(self, exc):
        try:
            _orig_ccl(self, exc)
        except ConnectionResetError:
            pass
    _pe._ProactorBasePipeTransport._call_connection_lost = _ccl_patched

GRADIO_6 = int(gr.__version__.split(".")[0]) >= 6
import rvc.lib.zluda

# Import ALL existing tab functions
from tabs.inference.inference import inference_tab
from tabs.train.train import train_tab
from tabs.extra.extra import extra_tab
from tabs.report.report import report_tab
from tabs.download.download import download_tab
from tabs.tts.tts import tts_tab
from tabs.voice_blender.voice_blender import voice_blender_tab
from tabs.plugins.plugins import plugins_tab
from tabs.settings.settings import settings_tab
from tabs.realtime.realtime import realtime_tab

# Import realtime helpers
from tabs.realtime.realtime import (
    get_files, get_audio_devices_formatted, load_realtime_settings,
    save_realtime_settings, start_realtime, stop_realtime,
    get_safe_dropdown_value, extract_model_and_epoch,
    match_index, default_weight,
)
from core import run_prerequisites_script

# Import new feature modules
from rvc.lib.comfort_shield import get_comfort_shield, ComfortShield
from rvc.lib.pitch_detection import detect_pitch, mic_test as pitch_mic_test
from rvc.lib.presets import list_presets, save_preset, load_preset, delete_preset, save_last_session, load_last_session, clear_last_session
from rvc.lib.system_info import get_full_system_info, get_remote_system_info, estimate_model_performance
from rvc.lib.voice_analyzer import analyze_voice
from rvc.lib.soundboard import list_slots, save_slot, load_slot, delete_slot, next_id as sb_next_id

run_prerequisites_script(pretraineds_hifigan=True, models=True, exe=True)

from assets.i18n.i18n import I18nAuto
i18n = I18nAuto()

from tabs.settings.sections.presence import load_config_presence
if load_config_presence():
    from assets.discord_presence import RPCManager
    RPCManager.start_presence()

import assets.installation_checker as installation_checker
installation_checker.check_installation()

import assets.themes.loadThemes as loadThemes
# for gradio 6, use default theme + custom css to avoid theme serialization bugs
my_voice_theme = None

# monkey-patch gradio 6's json serialization bug
# hf_gradio/cli.py's generate_cli_snippet fails when an endpoint param default
# is a non-JSON-serializable type like a class object
try:
    import hf_gradio.cli as _hf_cli
    import json as _json
    _orig_generate = _hf_cli.generate_cli_snippet
    def _patched_generate(original_info):
        import logging as _log
        try:
            return _orig_generate(original_info)
        except TypeError as _e:
            _log.warning(f"gradio cli snippet generation failed (non-serializable param): {_e}")
            return {}
    _hf_cli.generate_cli_snippet = _patched_generate
except ImportError:
    pass
client_mode = "--client" in sys.argv

# === CUSTOM CSS ===
css_path = os.path.join(now_dir, "assets", "css", "voice.css")
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        CUSTOM_CSS = f.read()
else:
    CUSTOM_CSS = "footer{display:none !important}"
CUSTOM_CSS += "\nfooter{display:none !important}"


# === HELPER: get device choice lists ===
def get_device_choices():
    """Return (input_choices, output_choices) formatted for Dropdowns."""
    try:
        inputs, outputs = get_audio_devices_formatted()
        in_choices = list(inputs.keys())
        out_choices = list(outputs.keys())
        return in_choices, out_choices
    except Exception:
        return [], []


# === VOICE LIBRARY TAB (inline for simplicity) ===
def voice_library_tab():
    """Voice library manager - shows trained models in a visual grid."""
    model_dir = _paths.models_root()
    lib_path = os.path.join(_paths.data_path(), "models", "library.json")
    os.makedirs(os.path.join(_paths.data_path(), "models"), exist_ok=True)

    # Load or create library
    if os.path.exists(lib_path):
        with open(lib_path, "r") as f:
            library = json.load(f)
    else:
        library = {}

    # Find trained models
    trained = sorted(get_files("model"), key=extract_model_and_epoch)

    # Build HTML grid
    cards_html = '<div class="voice-library-grid">'
    if trained:
        for m in trained[:20]:  # Show up to 20
            name = os.path.basename(m).replace(".pth", "")
            thumb = library.get(name, {}).get("thumbnail", "")
            thumb_html = f'<img class="voice-model-thumb" src="{thumb}" />' if thumb else '<div class="voice-model-thumb" style="background:#050505;display:flex;align-items:center;justify-content:center;font-size:1.5em;color:#f6b012;">v</div>'
            cards_html += f"""
            <div class="voice-model-card" onclick="alert('selected: {name}')">
                {thumb_html}
                <div class="voice-model-name">{name}</div>
                <div class="voice-model-star">[{'x' if library.get(name, {}).get('favorite') else ' '}]</div>
            </div>"""
    cards_html += "</div>"
    if not trained:
        cards_html = '<p style="color:#666666;text-align:center;">no trained models yet. go to training to create one.</p>'

    gr.HTML(cards_html)

    with gr.Row():
        model_name = gr.Textbox(label="model name", placeholder="enter a name for your model", scale=2)
        refresh_lib = gr.Button("refresh library", variant="secondary", scale=1)

    gr.Markdown("")
    with gr.Row():
        thumbnail_upload = gr.File(label="upload thumbnail (optional)", file_types=["image"], scale=2)
        fav_toggle = gr.Checkbox(label="mark as favorite", value=False, scale=1)
        save_btn = gr.Button("save to library", variant="primary", scale=1)

    preview = gr.HTML("")

    def save_model(name, thumb_file, favorite):
        lib_path = os.path.join(_paths.data_path(), "models", "library.json")
        if os.path.exists(lib_path):
            with open(lib_path, "r") as f:
                lib = json.load(f)
        else:
            lib = {}
        if name:
            lib[name] = {
                "favorite": favorite,
                "thumbnail": thumb_file if thumb_file else "",
            }
            with open(lib_path, "w") as f:
                json.dump(lib, f, indent=2)
            return f'<p style="color:#3c9fdd;">saved {name} to library!</p>'
        return '<p style="color:#ffffff;">please enter a model name.</p>'

    save_btn.click(
        fn=save_model,
        inputs=[model_name, thumbnail_upload, fav_toggle],
        outputs=[preview],
    )

    refresh_lib.click(
        fn=lambda: gr.HTML(""),
        inputs=[],
        outputs=[preview],
    )


# === HOME TAB ===
def home_tab():
    """Home tab — quick start with presets and one-click resume."""
    in_choices, out_choices = get_device_choices()
    preset_names = list_presets()
    last = load_last_session()

    with gr.Column(elem_classes="home-tab"):
        gr.HTML("""
        <div class="welcome-section">
            <h1>your voice, your home</h1>
            <p class="subtitle">a safe space for your voice to be you.</p>
        </div>
        """)

        # resume last session (prominent if available)
        resume_html = "resume last session" if last else ""
        resume_btn = gr.Button(resume_html, variant="primary", size="lg", visible=bool(last))
        
        with gr.Column(elem_classes="card"):
            gr.HTML('<div class="card-header">presets</div>')
            with gr.Row():
                preset_dropdown = gr.Dropdown(
                    label="saved configs",
                    choices=preset_names,
                    interactive=True,
                    scale=3,
                )
                load_preset_btn = gr.Button("load", variant="primary", scale=1)
                save_preset_btn = gr.Button("save current", variant="secondary", scale=1)
                delete_preset_btn = gr.Button("delete", variant="stop", scale=1)

            preset_name_input = gr.Textbox(
                label="preset name",
                placeholder="enter a name to save",
                visible=True,
                scale=1,
            )

        with gr.Column(elem_classes="card"):
            gr.HTML('<div class="card-header">devices</div>')
            with gr.Row():
                input_device = gr.Dropdown(
                    label="input device",
                    info="select your microphone",
                    choices=in_choices, interactive=True, scale=1,
                )
                output_device = gr.Dropdown(
                    label="output device",
                    info="select your headphones or speakers",
                    choices=out_choices, interactive=True, scale=1,
                )

        with gr.Column(elem_classes="card"):
            gr.HTML('<div class="card-header">voice model</div>')
            with gr.Row():
                model_file = gr.Dropdown(
                    label="model",
                    choices=sorted(get_files("model"), key=extract_model_and_epoch),
                    interactive=True, value=default_weight,
                    allow_custom_value=True, scale=2,
                )
                index_file = gr.Dropdown(
                    label="index",
                    choices=sorted(get_files("index")),
                    interactive=True, allow_custom_value=True, scale=1,
                )

            model_file.select(
                fn=lambda v: match_index(v),
                inputs=[model_file], outputs=[index_file],
            )

        with gr.Row():
            refresh_btn = gr.Button("refresh", variant="secondary", scale=1)
            start_btn = gr.Button("start voice", variant="primary", size="lg", scale=2)
            stop_btn = gr.Button("stop", variant="stop", scale=1)

        gr.HTML("""
        <div class="voice-meter-container">
            <div class="voice-meter-ring">
                <div class="voice-meter-inner">voice<br>ready</div>
            </div>
        </div>
        <p style="text-align:center; font-family:'Varela Round',sans-serif; font-weight:400;
                  font-size:1em; color:#f6b012; margin-top:10px;">
            you sound like you.
        </p>
        """)

        with gr.Accordion("advanced controls", open=False):
            realtime_tab()

        # --- callbacks ---

        # refresh all
        def refresh_all():
            in_ch, out_ch = get_device_choices()
            models = sorted(get_files("model"), key=extract_model_and_epoch)
            indexes = sorted(get_files("index"))
            return (
                gr.update(choices=in_ch), gr.update(choices=out_ch),
                gr.update(choices=models), gr.update(choices=indexes),
                gr.update(choices=list_presets()),
            )

        refresh_btn.click(
            fn=refresh_all,
            inputs=[],
            outputs=[input_device, output_device, model_file, index_file, preset_dropdown],
        )

        # start / stop
        start_btn.click(
            fn=lambda dev_in, dev_out, mdl, idx: (
                save_realtime_settings(dev_in, dev_out, None, mdl, idx),
                save_last_session({
                    "input_device": dev_in, "output_device": dev_out,
                    "model_file": mdl, "index_file": idx,
                }),
            ),
            inputs=[input_device, output_device, model_file, index_file],
            outputs=[],
        )
        stop_btn.click(fn=lambda: stop_realtime(), inputs=[], outputs=[])

        # resume
        if last:
            resume_btn.click(
                fn=lambda: (
                    gr.update(value=last.get("input_device", "")),
                    gr.update(value=last.get("output_device", "")),
                    gr.update(value=last.get("model_file", "")),
                    gr.update(value=last.get("index_file", "")),
                ),
                inputs=[],
                outputs=[input_device, output_device, model_file, index_file],
            )

        # preset save
        def do_save_preset(name, dev_in, dev_out, mdl, idx):
            if not name:
                return gr.update(), None
            cfg = {
                "input_device": dev_in, "output_device": dev_out,
                "model_file": mdl, "index_file": idx,
            }
            save_preset(name, cfg)
            return gr.update(choices=list_presets(), value=name), None

        save_preset_btn.click(
            fn=do_save_preset,
            inputs=[preset_name_input, input_device, output_device, model_file, index_file],
            outputs=[preset_dropdown, preset_name_input],
        )

        # preset load
        def do_load_preset(name):
            if not name:
                return [gr.update()] * 4
            cfg = load_preset(name)
            if not cfg:
                return [gr.update()] * 4
            return [
                gr.update(value=cfg.get("input_device", "")),
                gr.update(value=cfg.get("output_device", "")),
                gr.update(value=cfg.get("model_file", "")),
                gr.update(value=cfg.get("index_file", "")),
            ]

        load_preset_btn.click(
            fn=do_load_preset,
            inputs=[preset_dropdown],
            outputs=[input_device, output_device, model_file, index_file],
        )

        # preset delete
        def do_delete_preset(name):
            if name:
                delete_preset(name)
            return gr.update(choices=list_presets(), value=None)

        delete_preset_btn.click(
            fn=do_delete_preset,
            inputs=[preset_dropdown],
            outputs=[preset_dropdown],
        )


# === STUDIO TAB ===
def studio_tab():
    """Studio tab - Voice training and voice library."""
    with gr.Column(elem_classes="studio-tab"):
        gr.HTML("""
        <div style="margin-bottom:16px;">
            <h2 style="color:#ffffff; font-family:'Varela Round',sans-serif; font-weight:400; font-size:1.4em;">studio</h2>
            <p style="color:#666666; font-family:'Varela Round',sans-serif;">train and manage your voice models.</p>
        </div>
        """)

        with gr.Tabs():
            with gr.TabItem("voice library"):
                voice_library_tab()
            with gr.TabItem("quick clone"):
                gr.Markdown("upload a short audio sample (30-60 seconds) and we'll handle the rest.")
                with gr.Column(elem_classes="card"):
                    gr.HTML('<div class="card-header">quick clone</div>')
                    qc_name = gr.Textbox(label="model name", placeholder="name your voice")
                    qc_audio = gr.Audio(label="upload a sample", type="filepath")
                    qc_quality = gr.Dropdown(
                        label="quality",
                        choices=["fast (lower quality)", "balanced", "best (takes longer)"],
                        value="balanced",
                    )
                    qc_btn = gr.Button("clone this voice", variant="primary", size="lg")
                    qc_status = gr.HTML("")
                    
                    def quick_clone(name, audio_path, quality):
                        if not name or not audio_path:
                            return '<p style="color:#ffffff;">please provide a name and audio sample.</p>'
                        # In a full implementation this would trigger the training pipeline
                        # with simplified parameters. For now, guide the user to the training tab.
                        return '<p style="color:#3c9fdd;">audio received. go to the training tab for full control, or use a preset for instant results.</p>'
                    
                    qc_btn.click(fn=quick_clone, inputs=[qc_name, qc_audio, qc_quality], outputs=[qc_status])
            with gr.TabItem("training"):
                train_tab()
            with gr.TabItem("voice blender"):
                voice_blender_tab()
            with gr.TabItem("download models"):
                download_tab()
                with gr.Accordion("smart model finder", open=False):
                    with gr.Column(elem_classes="card"):
                        gr.HTML('<div class="card-header">smart model finder</div>')
                        gr.Markdown("check system specs and download models tailored to your hardware.")
                        
                        with gr.Row():
                            device_toggle = gr.Radio(
                                label="download to:",
                                choices=["this device", "remote (.250)"],
                                value="this device",
                                interactive=True,
                            )
                            check_specs_btn = gr.Button("check specs", variant="primary")
                        
                        specs_display = gr.HTML('<p style="color:#666666;">press "check specs" to see system information.</p>')
                        perf_estimate = gr.HTML("")
                        
                        # model selection area
                        with gr.Row():
                            model_to_download = gr.Dropdown(
                                label="model to download",
                                choices=[
                                    "titan (32k — lightweight, cpu-friendly)",
                                    "titan (40k — balanced)",
                                    "titan (48k — high quality)",
                                ],
                                value="titan (40k — balanced)",
                                interactive=True,
                                scale=2,
                            )
                            download_model_btn = gr.Button("download", variant="primary", scale=1)
                        
                        download_status = gr.HTML('<p style="color:#666666;">select a model and press download.</p>')
                        
                        def do_check_specs(device_choice):
                            if "remote" in device_choice.lower():
                                info = get_remote_system_info()
                                if "error" in info:
                                    return f'<p style="color:#ffffff;">remote check failed: {info["error"]}</p>', ""
                            else:
                                info = get_full_system_info()
                            
                            cpu = info.get("cpu", {})
                            ram = info.get("ram", {})
                            gpu = info.get("gpu", {})
                            os_info = info.get("os", {})
                            hostname = info.get("hostname", "unknown")
                            perf = estimate_model_performance(info)
                            
                            spec_html = f"""
                            <div>
                                <p><strong style="color:#f6b012;">{hostname}</strong>
                                <span style="color:#666666;"> — {os_info.get('name', 'unknown')}</span></p>
                                <p><strong style="color:#f6b012;">cpu:</strong> <span style="color:#ffffff;">{cpu.get('model', 'unknown')[:50]}</span>
                                <span style="color:#666666;"> ({cpu.get('cores', '?')}c/{cpu.get('threads', '?')}t)</span></p>
                                <p><strong style="color:#f6b012;">ram:</strong> <span style="color:#ffffff;">{ram.get('total_gb', '?')} gb</span>
                                <span style="color:#666666;"> ({ram.get('available_gb', '?')} gb free)</span></p>
                                <p><strong style="color:#f6b012;">gpu:</strong> <span style="color:#ffffff;">{gpu.get('model', 'none')[:50]}</span>
                                <span style="color:#666666;"> — {gpu.get('vram_gb', '?')} gb</span></p>
                            </div>
                            """
                            
                            perf_html = f"""
                            <div style="margin-top:8px;padding:8px;border:1px solid #1a1a1a;">
                                <p><strong style="color:#3c9fdd;">performance tier:</strong> <span style="color:#ffffff;">{perf.get('tier', 'unknown')}</span></p>
                                <p><strong style="color:#3c9fdd;">recommended sample rate:</strong> <span style="color:#ffffff;">{perf.get('max_sample_rate', '?')} hz</span></p>
                                <p><strong style="color:#3c9fdd;">recommended f0:</strong> <span style="color:#ffffff;">{perf.get('recommended_f0', '?')}</span></p>
                                <p style="color:#666666;font-size:0.85em;">{perf.get('notes', '')}</p>
                            </div>
                            """
                            return spec_html, perf_html
                        
                        check_specs_btn.click(fn=do_check_specs, inputs=[device_toggle], outputs=[specs_display, perf_estimate])
                        
                        # download to selected device
                        def do_download_model(model_choice, device_choice):
                            try:
                                # parse model name and sample rate from choice
                                model_name = model_choice.split("(")[0].strip().lower()
                                sr_part = model_choice.split("(")[1].split(")")[0].strip().lower()
                                sample_rate = sr_part.split("k")[0]
                                
                                # hugginface paths from the original download system
                                hf_base = "https://huggingface.co/IAHispano/Applio/resolve/main/pretraineds"
                                model_dir = f"{model_name}-{sample_rate}k"
                                file_g = f"G_{model_name}-{sample_rate}k.pth"
                                file_d = f"D_{model_name}-{sample_rate}k.pth"
                                url_g = f"{hf_base}/{model_dir}/{file_g}"
                                url_d = f"{hf_base}/{model_dir}/{file_d}"
                                
                                local_models_dir = os.path.join(_paths.data_path(), "rvc", "models", "pretraineds", "custom")
                                os.makedirs(local_models_dir, exist_ok=True)
                                
                                import requests
                                from tqdm import tqdm
                                
                                def download_file(url, dst):
                                    r = requests.get(url, stream=True, timeout=30)
                                    r.raise_for_status()
                                    total = int(r.headers.get("content-length", 0))
                                    with open(dst, "wb") as f:
                                        with tqdm(total=total, unit="B", unit_scale=True, desc=os.path.basename(dst)) as pbar:
                                            for chunk in r.iter_content(chunk_size=8192):
                                                if chunk:
                                                    f.write(chunk)
                                                    pbar.update(len(chunk))
                                    return dst
                                
                                if "remote" in device_choice.lower():
                                    # download locally first, then scp to remote
                                    import tempfile, uuid
                                    tag = uuid.uuid4().hex[:8]
                                    tmp_dir = f"/tmp/voice_dl_{tag}"
                                    os.makedirs(tmp_dir, exist_ok=True)
                                    
                                    local_g = os.path.join(tmp_dir, file_g)
                                    local_d = os.path.join(tmp_dir, file_d)
                                    
                                    download_file(url_g, local_g)
                                    download_file(url_d, local_d)
                                    
                                    # scp to remote
                                    remote_dir = f"house@192.168.4.250:voice/rvc/models/pretraineds/custom/"
                                    import subprocess
                                    subprocess.run(["ssh", "house@192.168.4.250", "mkdir", "-p", "voice/rvc/models/pretraineds/custom"], capture_output=True, timeout=10)
                                    subprocess.run(["scp", local_g, f"{remote_dir}{file_g}"], capture_output=True, timeout=60)
                                    subprocess.run(["scp", local_d, f"{remote_dir}{file_d}"], capture_output=True, timeout=60)
                                    
                                    # cleanup
                                    import shutil
                                    shutil.rmtree(tmp_dir)
                                    
                                    return f'<p style="color:#3c9fdd;">downloaded {model_name} {sample_rate}k to .250 successfully.</p>'
                                else:
                                    local_g = os.path.join(local_models_dir, file_g)
                                    local_d = os.path.join(local_models_dir, file_d)
                                    download_file(url_g, local_g)
                                    download_file(url_d, local_d)
                                    return f'<p style="color:#3c9fdd;">downloaded {model_name} {sample_rate}k to this device.</p>'
                            except Exception as e:
                                return f'<p style="color:#ffffff;">download failed: {str(e)[:100]}</p>'
                        
                        download_model_btn.click(fn=do_download_model, inputs=[model_to_download, device_toggle], outputs=[download_status])
            with gr.TabItem("extra tools"):
                extra_tab()


# === LIVE TAB ===
def live_tab():
    """Live tab - Real-time voice changing with Comfort Shield."""
    comfort_shield_instance = get_comfort_shield()
    
    with gr.Column(elem_classes="live-tab"):
        gr.HTML("""
        <div style="margin-bottom:16px;">
            <h2 style="color:#ffffff; font-family:'Varela Round',sans-serif; font-weight:400; font-size:1.4em;">live voice</h2>
            <p style="color:#666666; font-family:'Varela Round',sans-serif;">real-time voice changing with comfort features.</p>
        </div>
        """)

        with gr.Row():
            with gr.Column(scale=1):
                with gr.Column(elem_classes="card"):
                    gr.HTML('<div class="card-header">comfort shield</div>')
                    comfort_shield = gr.Checkbox(
                        label="enable comfort shield",
                        info="makes your voice feel softer and more natural.",
                        value=False, interactive=True,
                    )
                    gr.HTML("""
                    <p style="font-size:0.85em; color:#666666; margin-top:8px;">
                        when enabled, applies gentle smoothing and warmth to reduce
                        robotic artifacts in your transformed voice.
                    </p>""")
                    warmth_slider = gr.Slider(
                        minimum=0, maximum=100, step=1,
                        label="warmth", value=50,
                        info="how much warmth to add to your voice",
                        interactive=True,
                    )

                with gr.Column(elem_classes="card"):
                    gr.HTML('<div class="card-header">voice controls</div>')
                    pitch_shift = gr.Slider(minimum=-24, maximum=24, step=1, label="pitch shift", value=0, info="semitones up or down", interactive=True)
                    formant = gr.Slider(minimum=0.5, maximum=2.0, step=0.05, label="formant", value=1.0, info="shift formant frequencies", interactive=True)
                    breathiness = gr.Slider(minimum=0, maximum=1, step=0.05, label="breathiness", value=0, info="add breath to your voice", interactive=True)
                    expression = gr.Slider(minimum=-1, maximum=1, step=0.05, label="expression tone", value=0, info="adjust the tonal quality of your voice", interactive=True)

                with gr.Column(elem_classes="card"):
                    gr.HTML('<div class="card-header">mic test</div>')
                    mic_test_device = gr.Dropdown(
                        label="test device",
                        choices=[],
                        interactive=True,
                        visible=False,
                    )
                    mic_test_btn = gr.Button("record 5s & play back", variant="secondary")
                    mic_test_output = gr.Audio(label="test recording", type="numpy")

            with gr.Column(scale=2):
                with gr.Column(elem_classes="card"):
                    gr.HTML('<div class="card-header">real-time processing</div>')
                    show_pitch = gr.Checkbox(
                        label="show pitch indicator",
                        info="display your current vocal pitch in hz",
                        value=False, interactive=True,
                    )
                    pitch_display = gr.HTML('<div class="pitch-display">-- hz<br><span style="font-size:0.5em;color:#666666;">--</span></div>', visible=True)
                    realtime_tab()

        # --- voice analyzer section ---
        with gr.Accordion("voice analyzer", open=False):
            with gr.Column(elem_classes="card"):
                gr.HTML('<div class="card-header">analyze your voice</div>')
                gr.Markdown("record a short sample and we'll suggest starting settings for your voice type.")
                analyze_btn = gr.Button("record 3s & analyze", variant="secondary")
                analyze_status = gr.HTML('<p style="color:#666666;">press the button to analyze.</p>')
                analyze_results = gr.HTML("")

                def do_analyze():
                    try:
                        import sounddevice as sd
                        audio = sd.rec(int(3 * 48000), samplerate=48000, channels=1, dtype='float32')
                        sd.wait()
                        audio = audio.flatten()
                        result = analyze_voice(audio, 48000)
                        if result["confidence"] < 0.2:
                            return '<p style="color:#ffffff;">couldn\'t detect enough voice. try speaking clearly for 3 seconds.</p>', ""
                        html = f"""
                        <div style="margin-top:10px;">
                            <p><strong style="color:#f6b012;">pitch:</strong> <span style="color:#ffffff;">{result['pitch_mean']} hz</span>
                            <span style="color:#666666;"> (range: {result['pitch_min']}-{result['pitch_max']} hz, {result['pitch_range']})</span></p>
                            <p><strong style="color:#f6b012;">timbre:</strong> <span style="color:#ffffff;">{result['timbre']}</span></p>
                            <p><strong style="color:#f6b012;">voice type:</strong> <span style="color:#ffffff;">{result['suggested_model_type']}</span></p>
                            <hr style="border-color:#1a1a1a;margin:12px 0;">
                            <p style="color:#3c9fdd;">suggested starting settings:</p>
                            <p><span style="color:#666666;">pitch shift:</span> <span style="color:#ffffff;">{result['suggested_pitch_shift']:+d}</span>
                            <span style="color:#666666;">  formant:</span> <span style="color:#ffffff;">{result['suggested_formant']}</span>
                            <span style="color:#666666;">  warmth:</span> <span style="color:#ffffff;">{result['suggested_warmth']}</span>
                            <span style="color:#666666;">  expression:</span> <span style="color:#ffffff;">{result['suggested_expression']:+.2f}</span></p>
                        </div>
                        """
                        return html, ""
                    except Exception as e:
                        return f'<p style="color:#ffffff;">error: {e}</p>', ""

                analyze_btn.click(fn=do_analyze, inputs=[], outputs=[analyze_status, analyze_results])
        
        # Comfort Shield toggle handler
        def on_comfort(enabled, warmth_val):
            comfort_shield_instance.set_enabled(enabled)
            comfort_shield_instance.set_warmth(warmth_val / 100.0)
            return None  # no info message, just process silently

        comfort_shield.change(
            fn=on_comfort,
            inputs=[comfort_shield, warmth_slider],
            outputs=[],
        )
        
        warmth_slider.change(
            fn=lambda v: (
                comfort_shield_instance.set_warmth(v / 100.0),
                None
            )[1],
            inputs=[warmth_slider],
            outputs=[],
        )

        # Mic Test with actual audio recording
        def do_mic_test(device_str):
            try:
                audio = pitch_mic_test(device_str or "", duration=5.0)
                # Apply comfort shield if active
                processed = get_comfort_shield().process(audio)
                return (48000, processed)
            except Exception as e:
                print(f"Mic test error: {e}")
                import numpy as np
                return (48000, np.zeros(int(5 * 48000)))
        
        mic_test_btn.click(
            fn=do_mic_test,
            inputs=[mic_test_device],
            outputs=[mic_test_output],
        )


# === MAIN APP ===
with gr.Blocks(
    title="voice - your voice, your home",
    css=CUSTOM_CSS,
    js=(
        ("() => {\n"
         + "// register pwa service worker\n"
         + "if ('serviceWorker' in navigator) {\n"
         + "  navigator.serviceWorker.register('assets/pwa/sw.js');\n"
         + "}\n"
         + "// inject manifest link\n"
         + "const link = document.createElement('link');\n"
         + "link.rel = 'manifest';\n"
         + "link.href = 'assets/pwa/manifest.json';\n"
         + "document.head.appendChild(link);\n"
         + pathlib.Path(os.path.join(now_dir, "tabs", "realtime", "main.js")).read_text()
         + "\n}")
        if client_mode and not GRADIO_6
        else None
    ),
) as VoiceApp:
    # Header
    gr.HTML("""
    <div class="app-header">
        <div class="app-title">voice</div>
        <div class="app-tagline">feel like you. sound like home.</div>
    </div>
    """)

    with gr.Tab("home"):
        home_tab()
    with gr.Tab("studio"):
        studio_tab()
    with gr.Tab("live"):
        live_tab()
    with gr.Tab("soundboard"):
        with gr.Column(elem_classes="card"):
            gr.HTML('<div class="card-header">soundboard</div>')
            gr.Markdown("record processed voice clips and play them back.")

            sb_grid = gr.HTML('<p style="color:#666666;">no clips yet. record one below.</p>')
            sb_name = gr.Textbox(label="clip name", placeholder="name your clip")
            with gr.Row():
                sb_record = gr.Button("record 5s (processed)", variant="primary")
                sb_refresh = gr.Button("refresh", variant="secondary")
                sb_delete = gr.Button("delete selected", variant="stop")

            sb_dropdown = gr.Dropdown(label="select clip to play or delete", choices=[])
            sb_output = gr.Audio(label="playback")

            def refresh_sb():
                slots = list_slots()
                if not slots:
                    return '<p style="color:#666666;">no clips yet. record one below.</p>', gr.update(choices=[])
                grid = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px;">'
                for s in slots:
                    grid += f'<div style="background:#000000;border:1px solid #1a1a1a;padding:12px;text-align:center;"><div style="color:#ffffff;">{s["name"]}</div><div style="color:#666666;font-size:0.75em;">{s["duration_sec"]}s</div></div>'
                grid += "</div>"
                return grid, gr.update(choices=[f'{s["id"]}: {s["name"]}' for s in slots])

            def do_record(name):
                try:
                    import sounddevice as sd
                    audio = sd.rec(int(5 * 48000), samplerate=48000, channels=1, dtype='float32')
                    sd.wait()
                    audio = audio.flatten()
                    processed = get_comfort_shield().process(audio)
                    sid = sb_next_id()
                    save_slot(sid, name or f"clip {sid}", processed, 48000)
                    grid, dd = refresh_sb()
                    return grid, dd, (48000, processed)
                except Exception as e:
                    return f'<p style="color:#ffffff;">error: {e}</p>', gr.update(), None

            def do_load(dropdown_val):
                if not dropdown_val:
                    return None
                slot_id = dropdown_val.split(":")[0].strip()
                audio, sr = load_slot(slot_id)
                if audio is not None:
                    return (sr, audio)
                return None

            def do_delete(dropdown_val):
                if dropdown_val:
                    slot_id = dropdown_val.split(":")[0].strip()
                    delete_slot(slot_id)
                return refresh_sb()

            sb_record.click(fn=do_record, inputs=[sb_name], outputs=[sb_grid, sb_dropdown, sb_output])
            sb_refresh.click(fn=refresh_sb, inputs=[], outputs=[sb_grid, sb_dropdown])
            sb_delete.click(fn=do_delete, inputs=[sb_dropdown], outputs=[sb_grid, sb_dropdown])
            sb_dropdown.change(fn=do_load, inputs=[sb_dropdown], outputs=[sb_output])
    with gr.Tab("tts"):
        with gr.Column(elem_classes="card"):
            gr.HTML('<div class="card-header">text-to-speech</div>')
            gr.Markdown("generate voice clips from text. not real-time, but great for creating voiceovers or clips with your trained voice models.")
            tts_tab()
    with gr.Tab("settings"):
        with gr.Column(elem_classes="card"):
            gr.HTML('<div class="card-header">settings</div>')
            settings_tab()
        with gr.Column(elem_classes="card"):
            gr.HTML('<div class="card-header">appearance</div>')
            gr.Markdown("toggle between dark mode and soft light mode.")
            theme_toggle = gr.Radio(
                label="theme",
                choices=["dark", "light"],
                value="dark", interactive=True,
            )
            def switch_theme(choice):
                if choice == "light":
                    return gr.HTML("""<style>
                    body { background: #f5f0eb !important; }
                    </style>""")
                return gr.HTML("")
            theme_toggle.change(fn=switch_theme, inputs=[theme_toggle], outputs=[gr.HTML()])

    gr.HTML("""
    <div style="text-align:center; font-size:0.85em; color:#444444; padding:20px 0; font-family:'Varela Round',sans-serif;">
        voice — a fork of applio, redesigned for comfort.<br>
        by using voice, you agree to ethical and legal standards.
    </div>
    """)


# === LAUNCH LOGIC ===
def launch_gradio(server_name: str, server_port: int) -> None:
    # patch gradio 6's cli snippet generation right before launch
    try:
        import hf_gradio.cli as _hf_cli
        import gradio.routes as _gr_routes
        _orig_gen = _hf_cli.generate_cli_snippet
        def _safe_gen(original_info):
            import logging as _log
            try:
                result = _orig_gen(original_info)
                # verify all keys exist before returning
                for ep in original_info:
                    if ep not in result:
                        result[ep] = ""
                return result
            except Exception as _e:
                _log.warning(f"cli snippet generation failed: {_e}")
                # return a fully populated dict matching the input keys
                return {ep: "" for ep in original_info}
        _hf_cli.generate_cli_snippet = _safe_gen
        _gr_routes.generate_cli_snippet = _safe_gen
    except ImportError:
        pass
    app, _, _ = VoiceApp.launch(
        favicon_path="assets/ICON.ico",
        share="--share" in sys.argv,
        inbrowser="--open" in sys.argv,
        server_name=server_name,
        server_port=server_port,
        prevent_thread_lock=client_mode,
    )
    if client_mode:
        import time
        from rvc.realtime.client import app as fastapi_app
        app.mount("/api", fastapi_app)
        while True:
            time.sleep(5)


def get_value_from_args(key: str, default: Any = None) -> Any:
    if key in sys.argv:
        index = sys.argv.index(key) + 1
        if index < len(sys.argv):
            return sys.argv[index]
    return default


if __name__ == "__main__":
    port = int(get_value_from_args("--port", DEFAULT_PORT))
    server = get_value_from_args("--server-name", DEFAULT_SERVER_NAME)
    for _ in range(MAX_PORT_ATTEMPTS):
        try:
            launch_gradio(server, port)
            break
        except OSError:
            print(f"Failed to launch on port {port}, trying again on port {port - 1}...")
            port -= 1
        except Exception as error:
            print(f"An error occurred launching Gradio: {error}")
            break
