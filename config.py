import json
import os
from pathlib import Path


CONFIG_DIR = Path(os.environ.get('OPTION_PROMPT_CONFIG_DIR', '~/.config/option-prompt')).expanduser()
MODEL_DIR = Path('~/.local/share/option-prompt/models').expanduser()
DEFAULTS = {
    'whisper_url': 'http://127.0.0.1:8178/inference',
    'whisper_model': str(MODEL_DIR / 'ggml-large-v3-turbo-q5_0.bin'),
    'language': 'zh',
    'fix_model': 'haiku',
    'prompt_model': 'sonnet',
    'fix_timeout': 20,
    'prompt_timeout': 45,
    'low_probability': 0.6,
    'context_chars': 12000,
    'background_file': '',
    'glossary_files': [],
    'sensevoice_dir': '',
}
path = CONFIG_DIR / 'config.json'
SETTINGS = DEFAULTS | (json.loads(path.read_text()) if path.exists() else {})


def reference_text():
    paths = [SETTINGS['background_file'], *SETTINGS['glossary_files']]
    parts = []
    for name in paths:
        if name:
            try:
                parts.append(Path(name).expanduser().read_text(encoding='utf-8'))
            except OSError:
                pass
    return '\n'.join(parts)[:16000]
