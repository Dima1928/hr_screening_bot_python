from pathlib import Path


def load_system_prompt(path: str) -> str:
    """Загружает системный промпт из markdown-файла."""
    prompt_path = Path(path)
    if not prompt_path.is_absolute():
        prompt_path = Path.cwd() / prompt_path

    try:
        content = prompt_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as error:
        raise RuntimeError(f"SYSTEM_PROMPT_PATH file not found: {path}") from error

    if not content:
        raise RuntimeError(f"SYSTEM_PROMPT_PATH file is empty: {path}")

    return content
