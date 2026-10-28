# Option Prompt

**Voice input for the AI conversation you already have open.**

Tap **Right Option**, speak, and tap again. Option Prompt uses text from the destination window to turn your spoken thoughts into a clearer prompt. References like "that file" can become the filename you were discussing. Uncertain words can stay as alternatives for you and the receiving AI to interpret.

The result lands in your input field for review. It never presses Send.

macOS · Local Whisper transcription · Claude text processing · [MIT license](LICENSE)

[Get started](#get-started) · [Usage and configuration](docs/usage.md) · [Report a problem](https://github.com/Lutt999/option-prompt/issues)

## What it changes

Suppose the conversation in your destination window is about removing duplicate logic from `parser.py`:

| Step | Text |
| --- | --- |
| Spoken input | "Clean up the repeated logic in that file. Keep the behavior the same." |
| Prompt output | "Clean up the repeated logic in parser.py. Keep the behavior the same." |

If a name remains ambiguous, the output can keep it inline: `Run it on 〔Savio / S3〕.` The cleanup prompt asks Claude to preserve your intent, tone, and constraints, and to leave references unresolved when the window does not supply enough context. Model output can still be wrong.

The parser example comes from a [recorded check](docs/example.json) using synthesized English audio and supplied conversation text. The alternatives illustrate the intended format. This single example does not establish accuracy across speakers or apps.

## Why I built it

I often have several AI conversations open for different projects. Speaking is easier than typing, but I naturally say things like "that file" or "finish what we discussed." I wanted voice input that could use the conversation I was replying to, while keeping ambiguous words visible.

Option Prompt grew out of that workflow. I'm sharing it for people who want to try the same approach or adapt the source to their own setup. It's an early personal project installed from source.

## Get started

You need macOS, [Homebrew](https://brew.sh), Python 3.10+, and a working [Claude Code CLI](https://code.claude.com/docs/en/setup) sign-in or supported API configuration. Apple Silicon is recommended. The app is free under MIT; Claude usage is subject to your account's billing and limits. Audio is transcribed locally by default; text processing uses Claude online.

### 1. Install the dependencies

Finish the Claude CLI's setup first, then run:

```sh
brew install python@3.12 portaudio whisper-cpp
git clone https://github.com/Lutt999/option-prompt.git
cd option-prompt
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
mkdir -p ~/.config/option-prompt
cp -n config.example.json ~/.config/option-prompt/config.json
```

The example config selects English (`"language": "en"`). Edit `~/.config/option-prompt/config.json` before starting if you want another language: use `zh` for Chinese or `auto` for Whisper's language detection. An existing config is preserved. Without a config file, the built-in default is `zh`.

### 2. Download the speech model

```sh
curl -fL --create-dirs \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin \
  -o ~/.local/share/option-prompt/models/ggml-large-v3-turbo-q5_0.bin
```

Already have this model? Set `whisper_model` in your config to its path and skip the download.

### 3. Start the app

```sh
.venv/bin/python start.py
```

In **System Settings > Privacy & Security**, grant **Microphone**, **Accessibility**, and **Input Monitoring** access to the terminal or Python process running the app. Restart it after changing permissions. Close any other dictation tool using the same shortcuts.

`start.py` starts a local Whisper server if needed. Keep the terminal open; press Ctrl+C there to quit. This preview is installed from source and has no signed app bundle or automatic startup installer.

## Use it

| Tap to start and stop | Mode | Use it for |
| --- | --- | --- |
| Right Option | AI prompt | Clarifying references using the destination conversation |
| Right Command | Dictation | Correcting transcription while keeping your wording |

1. Tap the shortcut once and speak. You will hear a start sound and see a recording indicator.
2. Put the cursor in the conversation's input field, then tap the same shortcut to finish. This fixes the destination and captures its accessible text.
3. Wait for transcription and cleanup. If that window and input field still have focus, the result is pasted there. If focus changed, paste it yourself with Cmd+V.
4. Review the text and send it when ready.

The shortcuts are taps, not keys to hold down. They are currently fixed in the source. For project terminology, multiple conversations, optional SenseVoice, and troubleshooting, see the [usage guide](docs/usage.md).

## Context and privacy

Whisper runs on your Mac at `127.0.0.1:8178` by default. Optional SenseVoice also runs locally. **The transcript and destination-window text are sent to Claude**, together with recent dictations for that window and any reference files you configure. A custom remote Whisper endpoint also receives your audio.

Context comes from text the destination window exposes through macOS Accessibility. Unloaded messages, hidden scrollback, or inaccessible app content may be missing. The tool does not read other windows, browser history, or agent-session logs. It skips secure password fields.

The app keeps audio and conversation snapshots in memory and does not write a dictation history to disk. The speech server may print recognition details, and Claude CLI and your provider have their own data policies. If Claude processing fails, the app falls back to the original transcript.

## Feedback and contributions

If you try it, I'd like to hear which app you used and where the result helped or missed the point. [Open an issue](https://github.com/Lutt999/option-prompt/issues) with a small invented example. Setup fixes, clearer documentation, and focused pull requests are welcome; see [contributing](CONTRIBUTING.md).

## Credits and license

Built on [whisper.cpp](https://github.com/ggml-org/whisper.cpp), with optional [SenseVoice](https://github.com/FunAudioLLM/SenseVoice) through [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx). The application code is [MIT licensed](LICENSE); models and dependencies retain their own licenses.

Other projects worth exploring include [VoiceInk](https://github.com/Beingpax/VoiceInk), [LocalFlow](https://github.com/azz1804/localflow), and [WhisperLocal](https://github.com/usingcolor/WhisperLocal).
