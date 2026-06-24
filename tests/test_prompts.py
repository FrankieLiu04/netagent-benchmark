from __future__ import annotations

from fyp_agent.prompts import SYSTEM_PROMPT_READ_ONLY, get_system_prompt


def test_read_only_prompt_exists():
    prompt = get_system_prompt("read_only")
    assert prompt == SYSTEM_PROMPT_READ_ONLY
    assert "read-only" in prompt.lower()
    assert "CML" in prompt


def test_unknown_phase_raises():
    try:
        get_system_prompt("bogus")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "bogus" in str(e)
