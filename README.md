<div align="center">

<h2>voice</h2>

<p>feel like you. sound like home.</p>

<br>

<p>a real-time voice changer that actually feels good to use.</p>
<p>forked from <a href="https://github.com/IAHispano/Applio">applio</a>, rebuilt from the ground up.</p>

<br>
<br>

<hr>

<h2>what makes this different from applio</h2>

<p>applio is a research tool. voice is a <strong>home</strong>.</p>

<br>

<table align="center">
<tr><th></th><th>applio</th><th>voice</th></tr>
<tr><td><strong>philosophy</strong></td><td>expose every parameter</td><td>progressive disclosure — big buttons, clean dropdowns, popups for advanced stuff</td></tr>
<tr><td><strong>presets</strong></td><td>none</td><td>save/load/delete named configs. switch between "discord" and "stream" in two clicks</td></tr>
<tr><td><strong>one-click resume</strong></td><td>none</td><td>pick up exactly where you left off</td></tr>
<tr><td><strong>comfort shield</strong></td><td>none</td><td>real-time audio smoothing + harmonic warmth. reduces dysphoria-triggering robotic artifacts</td></tr>
<tr><td><strong>voice library</strong></td><td>file browser</td><td>visual grid with thumbnails, favorites, metadata</td></tr>
<tr><td><strong>mic test</strong></td><td>none</td><td>record 5 seconds, process through your pipeline, play it back</td></tr>
<tr><td><strong>pitch guide</strong></td><td>none</td><td>real-time hz + note display. toggleable</td></tr>
<tr><td><strong>voice analyzer</strong></td><td>none</td><td>analyze your mic input and get suggested starting settings</td></tr>
<tr><td><strong>soundboard</strong></td><td>none</td><td>record processed clips, play them back from a grid</td></tr>
<tr><td><strong>smart model downloader</strong></td><td>static urls</td><td>detects your cpu/gpu/ram/vram, recommends models, downloads to this device or remote</td></tr>
<tr><td><strong>ui language</strong></td><td>technical</td><td>simple words. every label is lowercase. no jargon</td></tr>
<tr><td><strong>visual design</strong></td><td>default gradio</td><td>solid #050505, varela round, yellow + blue palette. no gradients, no shadows, no noise</td></tr>
<tr><td><strong>updates</strong></td><td>"has all features it needs"</td><td>always adding anything that makes voice changing better</td></tr>
</table>

<br>

<hr>

<h2>what voice keeps from applio</h2>

<p>the core rvc engine is untouched — all the real-time voice conversion quality is still there. we didn't rewrite the audio pipeline, we built a better house around it.</p>

<ul>
<li>real-time rvc voice conversion</li>
<li>model training (now with a quick clone shortcut)</li>
<li>voice blending</li>
<li>edge tts integration</li>
<li>plugin system</li>
<li>all the advanced controls (tucked behind accordions so they don't clutter your day)</li>
</ul>

<br>

<hr>

<h2>features at a glance</h2>

<br>

<table align="center">
<tr><th>tab</th><th>what it does</th></tr>
<tr><td><strong>home</strong></td><td>presets, resume last session, pick mic + model, start/stop. that's it.</td></tr>
<tr><td><strong>studio</strong></td><td>voice library grid, quick clone, full training, voice blender, download models with smart system check, extra tools</td></tr>
<tr><td><strong>live</strong></td><td>comfort shield toggle, voice controls (pitch, formant, breathiness, expression), mic test, pitch guide, voice analyzer, real-time processing</td></tr>
<tr><td><strong>soundboard</strong></td><td>record processed clips, browse them in a grid, play or delete</td></tr>
<tr><td><strong>tts</strong></td><td>text-to-speech through your trained voice models</td></tr>
<tr><td><strong>settings</strong></td><td>audio device config, dark/light toggle, language, version info</td></tr>
</table>

<br>

<hr>

<h2>what voice adds that applio doesn't</h2>

<ul>
<li><strong>preset system</strong> — save/load/delete named configs as json. share them with friends.</li>
<li><strong>one-click resume</strong> — last session is auto-saved. one button to restore it.</li>
<li><strong>comfort shield</strong> — formant smoothing + harmonic saturation. toggleable, adjustable.</li>
<li><strong>voice library</strong> — visual grid of your trained models with thumbnails and favorites.</li>
<li><strong>mic test</strong> — record 5 seconds through your full pipeline.</li>
<li><strong>pitch guide</strong> — real-time fundamental frequency display in hz + note name.</li>
<li><strong>voice analyzer</strong> — record 3 seconds, get suggested pitch shift, formant, warmth, and expression based on your voice's characteristics.</li>
<li><strong>soundboard</strong> — record audio processed through your current voice, save it, play it back from a grid. great for streaming reactions.</li>
<li><strong>smart model downloader</strong> — checks your cpu cores, ram, gpu model, and vram. toggle between this device and remote machine (.250). recommends which sample rates and f0 methods will work. press download and it goes to whichever device the toggle is on.</li>
<li><strong>quick clone wizard</strong> — minimal-parameter training for fast results.</li>
<li><strong>dark/light theme</strong> — both comfortable, pick your mood.</li>
<li><strong>full ui redesign</strong> — solid #050505, varela round, yellow + blue, no gradients, no shadows, strict lowercase.</li>
</ul>

<br>

<hr>

<h2>quick start</h2>

<pre><code># system deps (ubuntu / debian / pop)
sudo apt-get install -y portaudio19-dev libportaudio2

# python deps
pip install -r requirements.txt

# launch
python app.py
</code></pre>

<p>opens at <strong>http://127.0.0.1:8765</strong></p>

<br>

<h3>first run</h3>

<ol>
<li>pick your microphone from the dropdown on <strong>home</strong></li>
<li>select a voice model (download one from <strong>studio > download models</strong>, or train your own)</li>
<li>click <strong>start voice</strong> — your last session auto-saves</li>
<li>next time, click <strong>resume last session</strong> and you're back in 1 click</li>
</ol>

<br>

<h3>options</h3>

<table align="center">
<tr><th>flag</th><th>what it does</th></tr>
<tr><td><code>--share</code></td><td>public gradio share link</td></tr>
<tr><td><code>--open</code></td><td>open browser automatically</td></tr>
<tr><td><code>--port 8765</code></td><td>custom port</td></tr>
<tr><td><code>--server-name 0.0.0.0</code></td><td>bind to all interfaces</td></tr>
<tr><td><code>--client</code></td><td>client mode for external audio routing</td></tr>
</table>

<br>

<hr>

<h2>preset system</h2>

<p>your configs live in <code>~/voice/models/presets.json</code> as plain json. share them with friends by copying the file.</p>

<p>to save a preset:</p>
<ol>
<li>set up your devices, model, and controls how you like them</li>
<li>type a name in the "preset name" box on home</li>
<li>click <strong>save current</strong></li>
</ol>

<p>to load: pick from the dropdown, click <strong>load</strong>.</p>
<p>to delete: pick from the dropdown, click <strong>delete</strong>.</p>

<br>

<hr>

<h2>smart model finder</h2>

<p>on the studio tab, open <strong>smart model finder</strong>. press "check specs" and it reads:</p>

<ul>
<li>cpu model, cores, threads</li>
<li>total and available ram</li>
<li>gpu model and vram</li>
<li>os name and version</li>
</ul>

<p>toggle between <strong>"this device"</strong> and <strong>"remote (.250)"</strong> to see specs for either machine. the remote check runs over ssh to 192.168.4.250 and returns the same data.</p>

<p>when you download a model, it goes to whichever device the toggle shows.</p>

<br>

<hr>

<h2>voice analyzer</h2>

<p>on the live tab, open <strong>voice analyzer</strong>. press "record 3s & analyze". it records a short sample and measures:</p>

<ul>
<li>pitch mean, min, max, range</li>
<li>timbre (bright, neutral, warm, breathy)</li>
<li>voice type classification</li>
</ul>

<p>then suggests starting values for pitch shift, formant, warmth, and expression. use these as a starting point, then tweak from there.</p>

<br>

<hr>

<h2>soundboard</h2>

<p>the soundboard tab lets you record audio clips processed through your current voice settings and play them back.</p>

<p>to record: name your clip, press "record 5s (processed)". the recording runs through the comfort shield if it's enabled.</p>
<p>to play: select a clip from the dropdown and it loads into the audio player.</p>
<p>to delete: select a clip, press "delete selected".</p>

<p>clips are stored as wav files in <code>~/voice/models/soundboard/</code>.</p>

<br>

<hr>

<h2>the comfort shield</h2>

<p>this is the feature that makes voice different. when enabled, it applies two things to your transformed audio:</p>

<ol>
<li><strong>formant smoothing</strong> — a gentle low-pass filter at 8khz that softens harsh robotic artifacts</li>
<li><strong>harmonic warmth</strong> — soft tube-style saturation that adds body and presence</li>
</ol>

<p>adjustable from 0-100 on the live tab. designed to add under 5ms of latency.</p>
<p>it's not magic — it can't fix a bad model or extreme pitch shifts. but it makes the good stuff feel better.</p>

<br>

<hr>

<h2>voice dysphoria</h2>

<p>this tool exists because voice changing shouldn't feel clinical or technical. the home screen says "you sound like you" because that's the goal — not to hide your voice, but to let you hear the version that feels right.</p>

<p>if you're using this for gender-affirming voice practice:</p>
<ul>
<li>start with comfort shield on</li>
<li>use the pitch guide to track your range</li>
<li>use the voice analyzer to find good starting settings</li>
<li>train models on your own voice at different pitches for the most natural results</li>
<li>save presets for different moods / contexts</li>
<li>use the soundboard for common phrases you want to hear in your voice</li>
</ul>

<br>

<hr>

<h2>project structure</h2>

<pre><code>~/voice/
├── app.py                  # main entry — the whole ui
├── core.py                 # core rvc pipeline
├── rvc/                    # voice conversion engine (mostly untouched)
│   └── lib/
│       ├── comfort_shield.py  # the comfort processing
│       ├── pitch_detection.py # real-time pitch detection
│       ├── presets.py         # preset save/load/delete
│       ├── system_info.py     # cpu/ram/gpu/vram detection
│       ├── voice_analyzer.py  # voice analysis & suggestions
│       └── soundboard.py      # soundboard clip storage
├── tabs/                   # individual tab implementations
├── assets/
│   ├── css/voice.css       # the whole visual identity
│   └── themes/Voice.py     # gradio theme variables
├── models/                 # presets.json, last_session.json, library.json, soundboard/ live here
├── icon.png
└── requirements.txt
</code></pre>

<br>

<hr>

<h2>credits</h2>

<ul>
<li><strong>rvc engine</strong>: <a href="https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI">rvc-project</a></li>
<li><strong>forked from</strong>: <a href="https://github.com/IAHispano/Applio">applio</a> by iahispano</li>
<li><strong>redesigned for</strong>: feeling at home in your own voice</li>
</ul>

<br>
<br>

<p><em>you sound like you.</em></p>

</div>