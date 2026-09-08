from src.analyzer.comparison_prompts import build_comparison_user_prompt


def test_wraps_both_versions_in_delimiter_tags():
    prompt = build_comparison_user_prompt("text A", "text B")

    assert "<version_a>" in prompt and "</version_a>" in prompt
    assert "<version_b>" in prompt and "</version_b>" in prompt
    assert prompt.index("<version_a>") < prompt.index("text A") < prompt.index("</version_a>")
    assert prompt.index("<version_b>") < prompt.index("text B") < prompt.index("</version_b>")
