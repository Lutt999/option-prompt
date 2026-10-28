from dataclasses import dataclass, field
import time

import AppKit
import ApplicationServices as AX

from config import SETTINGS


def attribute(element, name):
    if element is None:
        return None
    try:
        error, value = AX.AXUIElementCopyAttributeValue(element, name, None)
        return value if error == AX.kAXErrorSuccess else None
    except Exception:
        return None


@dataclass
class Target:
    pid: int
    app: str
    bundle: str
    title: str
    text: str
    window: object = field(repr=False, compare=False)
    focused: object = field(repr=False, compare=False)

    def same_window(self, other):
        return other is not None and self.pid == other.pid and self.window is not None and self.window == other.window

    def same_conversation(self, other):
        return self.same_window(other) and self.title == other.title

    def same_field(self, other):
        return self.same_conversation(other) and self.focused is not None and self.focused == other.focused


def window_text(window, limit):
    stack = [(window, 0)]
    parts, seen = [], set()
    started = time.monotonic()
    visited = 0
    while stack and visited < 600 and time.monotonic() - started < 1.2:
        element, depth = stack.pop()
        visited += 1
        role = attribute(element, AX.kAXRoleAttribute)
        if attribute(element, AX.kAXSubroleAttribute) == 'AXSecureTextField':
            continue
        if role in (AX.kAXStaticTextRole, AX.kAXTextAreaRole, AX.kAXTextFieldRole):
            value = attribute(element, AX.kAXValueAttribute)
            if isinstance(value, str) and value.strip() and value not in seen:
                seen.add(value)
                parts.append(value)
        if depth < 24:
            children = attribute(element, AX.kAXChildrenAttribute) or []
            stack.extend((child, depth + 1) for child in reversed(children))
    return '\n'.join(parts)[-limit:]


def capture(read_text=True):
    running = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
    if running is None:
        return None
    application = AX.AXUIElementCreateApplication(running.processIdentifier())
    AX.AXUIElementSetMessagingTimeout(application, 0.15)
    focused = attribute(application, AX.kAXFocusedUIElementAttribute)
    if attribute(focused, AX.kAXSubroleAttribute) == 'AXSecureTextField':
        return None
    window = attribute(focused, AX.kAXWindowAttribute)
    if window is None:
        window = attribute(application, AX.kAXFocusedWindowAttribute)
    if window is None:
        return None
    return Target(
        pid=int(running.processIdentifier()),
        app=str(running.localizedName() or ''),
        bundle=str(running.bundleIdentifier() or ''),
        title=str(attribute(window, AX.kAXTitleAttribute) or ''),
        text=window_text(window, int(SETTINGS['context_chars'])) if read_text else '',
        window=window, focused=focused,
    )
