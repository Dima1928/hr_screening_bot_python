import pytest

from app.core.prompt_loader import load_system_prompt


def test_load_system_prompt_reads_markdown_file(tmp_path):
    prompt_file = tmp_path / "system_prompt.md"
    prompt_file.write_text("# Prompt\n\nТекст системного промпта", encoding="utf-8")

    assert load_system_prompt(str(prompt_file)) == "# Prompt\n\nТекст системного промпта"


def test_load_system_prompt_rejects_empty_file(tmp_path):
    prompt_file = tmp_path / "empty.md"
    prompt_file.write_text("   ", encoding="utf-8")

    with pytest.raises(RuntimeError, match="file is empty"):
        load_system_prompt(str(prompt_file))
