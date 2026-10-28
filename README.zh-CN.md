# Option Prompt

[English](README.md)

点一下**右 Option** 开始说话，再点一下结束。它根据结束时光标所在窗口的对话，把口述整理成给 AI 的指令。拿不准的词保留为 `〔Savio / S3〕` 这样的候选。

**右 Command** 是普通纠错输入，尽量保留原话。

这是从个人日用语音工具整理出来的小型 macOS 源码项目。语音识别默认在本机进行，文字整理通过你自己的 Claude CLI 完成。

## 使用方式

1. 点一下右 Option，开始录音。
2. 说完后，把光标放在你要回复的对话输入框，再点右 Option 结束。
3. 程序在结束时记录那个窗口，读取它通过 macOS 辅助功能暴露的文本。
4. Whisper 识别语音；可以选配 SenseVoice 提供第二份识别结果。
5. AI 结合该窗口的对话纠错、补清楚省略的对象。高置信内容直接写，拿不准的保留候选。
6. 同一个窗口和输入框仍有焦点时自动粘贴；否则放到剪贴板，由你粘贴。不会自动按回车发送。

窗口上下文在**结束录音时**固定下来。同一窗口的近期口述只在内存里保留，不混用其他窗口的历史。

例如，当前对话在讨论 `parser.py` 时，“把那个文件里的重复逻辑整理一下”可以整理成“把 parser.py 里的重复逻辑整理一下。”这是说明用的例子，不是实录结果。

## 安装

需要 macOS、Python 3.10 以上、麦克风，以及已完成登录或 API 配置的 [Claude CLI](https://code.claude.com/docs/en/setup)。建议使用 Apple Silicon Mac。

```sh
brew install python@3.12 portaudio whisper-cpp
git clone https://github.com/Lutt999/option-prompt.git
cd option-prompt
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
mkdir -p ~/.config/option-prompt
cp config.example.json ~/.config/option-prompt/config.json
curl -fL --create-dirs \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin \
  -o ~/.local/share/option-prompt/models/ggml-large-v3-turbo-q5_0.bin
.venv/bin/python start.py
```

按 macOS 提示，为启动它的终端或 Python 进程开启麦克风、辅助功能和输入监控权限。不要同时运行另一份使用相同快捷键的工具。Ctrl+C 退出。这版提供源码，没有签名安装包或开机启动安装器。

## 配置

编辑 `~/.config/option-prompt/config.json`，修改后重启。完整设置见 [英文说明](README.md#configuration)，默认值见 [config.py](config.py)。

主要设置：

- `language`：识别语言，默认中文 `zh`。
- `fix_model`、`prompt_model`：普通纠错和指令模式使用的 Claude 模型，默认 `haiku`、`sonnet`。
- `low_probability`：Whisper 词级概率低于此值时提醒 AI 留意，默认 `0.6`。
- `background_file`、`glossary_files`：可选的个人背景和术语表路径，不需要把私人内容放进仓库。
- `sensevoice_dir`：可选的 SenseVoice ONNX 模型目录。
- `whisper_model`：已有 whisper.cpp 模型文件的路径。

SenseVoice 可按需安装：`.venv/bin/python -m pip install sherpa-onnx`，然后按 [sherpa-onnx 官方说明](https://k2-fsa.github.io/sherpa/onnx/sense-voice/index.html)取得兼容模型，将包含 `model.int8.onnx` 和 `tokens.txt` 的目录填入配置。

## 上下文范围

只能读取目标窗口通过辅助功能暴露的文本，不能保证拿到整段历史。未加载的消息、隐藏的终端滚动记录、没有开放相关文本的应用可能读不到。读不到时不猜对话，也不会拿“最近修改的另一个项目日志”替代。

识别器的词级概率只是提示；候选由文字模型生成，仍可能出错。输出不附模型臆测的百分比。

## 数据去向

默认情况下，音频只交给本机 Whisper；选配的 SenseVoice 也在本机运行。**文字整理需要联网**：本次转写、目标窗口文本、该窗口近期口述和你配置的参考资料会通过 Claude CLI 发给模型。

程序自身不把录音、转写或窗口对话写到磁盘。模型服务和 Claude CLI 有各自的数据政策；Whisper 服务可能在终端输出识别内容。密码输入框会跳过。文字整理失败时保留原始转写。

## 相近项目

[LocalFlow](https://github.com/azz1804/localflow)、[ReadyType](https://github.com/whnnick/readytype) 已有语音转 AI 指令；[VoiceInk](https://github.com/Beingpax/VoiceInk)、[WhisperLocal](https://github.com/usingcolor/WhisperLocal)、[HoldSpeak](https://github.com/karolswdev/HoldSpeak) 已有不同形式的上下文能力。

这个项目不宣称首创，保留的重点是：结束时定位目标窗口、区分普通转写和 AI 指令、拿不准时原位保留候选。公开版本从个人代码整理而来，不作准确率或速度优于其他项目的承诺。

使用 [whisper.cpp](https://github.com/ggml-org/whisper.cpp)，可选 [SenseVoice](https://github.com/FunAudioLLM/SenseVoice) 与 [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx)。应用源码采用 MIT 许可证，模型和依赖沿用各自许可证。
