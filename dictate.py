"""Right Option: contextual AI instructions. Right Command: corrected dictation."""

import io
import re
import subprocess
import threading
import time
import wave

import AppKit

import clean
import context
import numpy as np
import requests
import sounddevice as sd
from PyObjCTools import AppHelper
from pynput import keyboard
from config import SETTINGS

SERVER = SETTINGS['whisper_url']
RATE = 16000
START_SOUND = "/System/Library/Sounds/Ping.aiff"
STOP_SOUND = "/System/Library/Sounds/Pop.aiff"
ERROR_SOUND = "/System/Library/Sounds/Basso.aiff"

RED = (0.85, 0.15, 0.15)
ORANGE = (0.90, 0.50, 0.05)
GRAY = (0.35, 0.35, 0.35)

CJK = r"一-鿿"
PUNCT = {",": "，", "?": "？", "!": "！", ":": "：", ";": "；"}

kb = keyboard.Controller()
lock = threading.Lock()
recording = False
chunks = []
stream = None
started_at = 0.0
mode = "fix"

# 右 Command 必须是单独点按才算触发；按住它再按别的键（如 Cmd+C）不算。
cmd_r_down = False
cmd_r_combo = False
alt_r_down = False
alt_r_combo = False
pressed_at = {}
TAP_MAX = 0.5   # 按住超过这么久不算单独点按（防 Option/Command 加鼠标点击误触发）


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def play(path):
    subprocess.Popen(["afplay", "-v", "2", path])


class Overlay:
    """屏幕顶部居中的提示浮窗。所有方法只能在主线程调用。"""

    WIDTH, HEIGHT = 240, 56

    def __init__(self):
        style = AppKit.NSWindowStyleMaskBorderless | AppKit.NSWindowStyleMaskNonactivatingPanel
        self.panel = AppKit.NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            AppKit.NSMakeRect(0, 0, self.WIDTH, self.HEIGHT), style, AppKit.NSBackingStoreBuffered, False
        )
        self.panel.setLevel_(AppKit.NSStatusWindowLevel)
        self.panel.setOpaque_(False)
        self.panel.setBackgroundColor_(AppKit.NSColor.clearColor())
        self.panel.setIgnoresMouseEvents_(True)
        self.panel.setHasShadow_(True)
        self.panel.setCollectionBehavior_(
            AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
            | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
            | AppKit.NSWindowCollectionBehaviorStationary
        )

        view = self.panel.contentView()
        view.setWantsLayer_(True)
        view.layer().setCornerRadius_(self.HEIGHT / 2)

        self.label = AppKit.NSTextField.labelWithString_("")
        self.label.setFont_(AppKit.NSFont.boldSystemFontOfSize_(22))
        self.label.setTextColor_(AppKit.NSColor.whiteColor())
        self.label.setAlignment_(AppKit.NSTextAlignmentCenter)
        self.label.setFrame_(AppKit.NSMakeRect(0, (self.HEIGHT - 30) / 2, self.WIDTH, 30))
        view.addSubview_(self.label)

    def show(self, text, rgb):
        r, g, b = rgb
        color = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, 0.95)
        self.panel.contentView().layer().setBackgroundColor_(color.CGColor())
        self.label.setStringValue_(text)
        self.place()
        self.panel.orderFrontRegardless()

    def update_text(self, text):
        self.label.setStringValue_(text)

    def hide(self):
        self.panel.orderOut_(None)

    def place(self):
        # 放在鼠标所在屏幕的顶部正中
        mouse = AppKit.NSEvent.mouseLocation()
        screen = AppKit.NSScreen.mainScreen()
        for s in AppKit.NSScreen.screens():
            if AppKit.NSPointInRect(mouse, s.frame()):
                screen = s
                break
        vf = screen.visibleFrame()
        x = vf.origin.x + (vf.size.width - self.WIDTH) / 2
        y = vf.origin.y + vf.size.height - self.HEIGHT - 20
        self.panel.setFrameOrigin_((x, y))


overlay = None


def ui(fn, *args):
    AppHelper.callAfter(fn, *args)


def on_audio(indata, frames, t, status):
    chunks.append(indata.copy())


def tick():
    # 录音时每半秒刷新一次秒数
    while recording:
        secs = int(time.time() - started_at)
        ui(overlay.update_text, f"● {'Recording' if mode == 'fix' else 'Prompt'}  {secs // 60}:{secs % 60:02d}")
        time.sleep(0.5)


def start_recording():
    global recording, chunks, stream, started_at
    chunks = []
    # 插拔耳机/麦克风后 PortAudio 的设备列表会过期，每次录音前重新加载
    sd._terminate()
    sd._initialize()
    stream = sd.InputStream(samplerate=RATE, channels=1, dtype="int16", callback=on_audio)
    stream.start()
    recording = True
    started_at = time.time()
    ui(overlay.show, "● Recording  0:00" if mode == "fix" else "● Prompt  0:00", RED)
    play(START_SOUND)
    threading.Thread(target=tick, daemon=True).start()
    log("Recording started")


def stop_recording():
    global recording, stream
    try:
        target = context.capture(read_text=False)
    except Exception:
        target = None
    stream.stop()
    stream.close()
    stream = None
    recording = False
    play(STOP_SOUND)
    audio = np.concatenate(chunks) if chunks else np.zeros((0, 1), dtype="int16")
    if target is not None:
        target.text = context.window_text(target.window, int(SETTINGS['context_chars']))
    log(f"Recording stopped: {len(audio) / RATE:.1f}s")
    ui(overlay.show, "Transcribing…", ORANGE)
    threading.Thread(target=transcribe_and_paste, args=(audio, mode, target), daemon=True).start()


def to_wav(audio):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(audio.tobytes())
    return buf.getvalue()


# whisper 在静音/噪声上凭空编出的句子（日志里反复出现）；整句是这些就当没说话，句尾带的就删掉
HALLUCINATIONS = ["请不吝点赞 订阅 转发 打赏支持明镜与点点栏目", "请不吝点赞订阅转发打赏支持明镜与点点栏目",
                  "字幕由Amara.org社区提供", "谢谢观看", "感谢观看", "谢谢大家收看"]


def drop_hallucinations(text):
    t = text.strip()
    for h in HALLUCINATIONS:
        if t.endswith(h):
            t = t[: -len(h)].rstrip(" ，。,.")
    return t


def fix_punctuation(text):
    # whisper 常在中文后面输出半角标点，换成全角
    for half, full in PUNCT.items():
        text = re.sub(rf"(?<=[{CJK}])\s*{re.escape(half)}\s*", full, text)
    return text.strip()


def flash_then_hide(text, rgb, secs=1.2):
    ui(overlay.show, text, rgb)
    time.sleep(secs)
    if not recording:
        ui(overlay.hide)


paste_lock = threading.Lock()   # 一次只处理一段，粘贴按录音先后顺序


def transcribe_and_paste(audio, m, target):
    with paste_lock:
        _transcribe_and_paste(audio, m, target)


def _transcribe_and_paste(audio, m, target):
    if len(audio) < RATE * 0.3:
        log("Recording too short; ignored")
        flash_then_hide("Recording too short", GRAY)
        return
    try:
        r = requests.post(
            SERVER,
            files={"file": ("a.wav", to_wav(audio), "audio/wav")},
            data={"response_format": "verbose_json", "language": SETTINGS['language']},
            timeout=120,
        )
        r.raise_for_status()
        d = r.json()
        text = drop_hallucinations(fix_punctuation(d.get("text", "")))
        words = [w for seg in d.get("segments", []) for w in seg.get("words", [])]
        marked = (clean.mark_low(words) if words else "") or text
    except Exception as e:
        log(f"Transcription failed: {e}")
        play(ERROR_SOUND)
        flash_then_hide("Transcription failed", GRAY, 2)
        return
    log("Transcription complete")
    if not text:
        flash_then_hide("No speech detected", GRAY)
        return
    raw = text
    try:
        ui(overlay.show, "Cleaning up…" if m == "fix" else "Writing prompt…", ORANGE)
        alt = clean.sensevoice(audio, RATE)
        text, note = clean.run(raw, marked, m, target, alt)
        log(f"Cleanup complete ({m}, {note})")
        clean.remember(target, text)
    except Exception as e:
        text = raw
        log(f"Cleanup failed; using transcript: {e!r}")
    ui(deliver, text, target)


def deliver(text, target):
    board = AppKit.NSPasteboard.generalPasteboard()
    previous = [{kind: item.dataForType_(kind) for kind in item.types()}
                for item in board.pasteboardItems() or []]
    board.clearContents()
    board.setString_forType_(text, AppKit.NSPasteboardTypeString)
    our_change = board.changeCount()
    try:
        current = context.capture(read_text=False)
    except Exception:
        current = None
    if target is None or not target.same_field(current):
        overlay.show('Copied · Cmd+V', GRAY)
        threading.Thread(target=flash_then_hide, args=('Copied · Cmd+V', GRAY, 2), daemon=True).start()
        return
    with kb.pressed(keyboard.Key.cmd):
        kb.press('v')
        kb.release('v')
    time.sleep(0.4)
    if board.changeCount() == our_change:
        board.clearContents()
        items = []
        for values in previous:
            item = AppKit.NSPasteboardItem.alloc().init()
            for kind, data in values.items():
                if data is not None:
                    item.setData_forType_(data, kind)
            items.append(item)
        if items:
            board.writeObjects_(items)
    if not recording:
        overlay.hide()


def toggle(m="fix"):
    global mode
    with lock:
        if recording:
            stop_recording()
        else:
            mode = m
            start_recording()


def on_press(key):
    global cmd_r_down, cmd_r_combo, alt_r_down, alt_r_combo
    if key in (keyboard.Key.cmd_r, keyboard.Key.alt_r) and key not in pressed_at:
        pressed_at[key] = time.time()
    if key == keyboard.Key.cmd_r:
        cmd_r_down = True
        cmd_r_combo = False
    elif key == keyboard.Key.alt_r:
        alt_r_down = True
        alt_r_combo = False
    else:
        if cmd_r_down:
            cmd_r_combo = True
        if alt_r_down:
            alt_r_combo = True


def on_release(key):
    global cmd_r_down, alt_r_down
    held = time.time() - pressed_at.pop(key, time.time())
    if held > TAP_MAX:
        cmd_r_down = cmd_r_down and key != keyboard.Key.cmd_r
        alt_r_down = alt_r_down and key != keyboard.Key.alt_r
        return
    if key == keyboard.Key.cmd_r:
        clean_tap = cmd_r_down and not cmd_r_combo
        cmd_r_down = False
        if clean_tap:
            ui(toggle, 'fix')
    elif key == keyboard.Key.alt_r:
        clean_tap = alt_r_down and not alt_r_combo
        alt_r_down = False
        if clean_tap:
            ui(toggle, 'prompt')


if __name__ == "__main__":
    app = AppKit.NSApplication.sharedApplication()
    # 不在 Dock 显示图标，也不抢焦点
    app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
    overlay = Overlay()
    threading.Thread(target=clean.sensevoice, args=(np.zeros(RATE // 2, dtype="int16"),), daemon=True).start()   # 预载第二识别器
    keyboard.Listener(on_press=on_press, on_release=on_release).start()
    log("Ready: Right Command = dictation; Right Option = AI prompt")
    AppHelper.runEventLoop()
