import pytest
from pydantic import BaseModel

from app.providers.llm.base import LLMError, complete_json, extract_json
from tests.fakes import FakeLLM


class Out(BaseModel):
    value: int


def test_extract_json_handles_fences_think_and_prose() -> None:
    assert extract_json('```json\n{"value": 1}\n```') == {"value": 1}
    assert extract_json('<think>hmm</think>{"value": 2}') == {"value": 2}
    assert extract_json('İşte sonuç: {"value": 3} umarım olur') == {"value": 3}


async def test_complete_json_retries_once_on_invalid_output() -> None:
    llm = FakeLLM({"t": ["bozuk", '{"value": 5}']})
    assert (await complete_json(llm, [], Out, purpose="t")).value == 5
    assert llm.count("t") == 2


async def test_complete_json_raises_after_retries() -> None:
    llm = FakeLLM({"t": ["bozuk", '{"value": "x"}']})
    with pytest.raises(LLMError):
        await complete_json(llm, [], Out, purpose="t")
