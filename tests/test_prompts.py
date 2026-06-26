from __future__ import annotations

from netagent.prompts import SYSTEM_PROMPT_FULL_ACCESS, get_system_prompt


def test_full_access_prompt_exists():
    prompt = get_system_prompt("full_access")
    assert prompt == SYSTEM_PROMPT_FULL_ACCESS
    assert "call the relevant MCP tool" in prompt
    assert "Do not invent" in prompt
    assert "CML" in prompt


def test_unknown_phase_raises():
    try:
        get_system_prompt("bogus")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "bogus" in str(e)
