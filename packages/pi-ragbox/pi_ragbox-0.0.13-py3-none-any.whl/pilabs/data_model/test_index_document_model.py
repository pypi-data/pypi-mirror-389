import json

import pytest
from pydantic import ValidationError

from .index_document_model import IndexDocument


def test_index_document_preserves_dict_text() -> None:
    original = json.dumps({"foo": "bar"})

    document = IndexDocument(text=original)

    assert document.text == original
    assert document.structured_data is None
    assert document._get_structured_data() == {"foo": "bar"}


@pytest.mark.parametrize(
    ("raw_text", "should_wrap"),
    [
        ("plain text", True),
        ('["not", "a", "dict"]', False),
        ("café déjà vu ☕️", True),
    ],
)
def test_index_document_wraps_non_dict_text(raw_text: str, should_wrap: bool) -> None:
    document = IndexDocument(text=raw_text)

    assert document.structured_data is None
    if should_wrap:
        expected_text = json.dumps({"text": raw_text}, indent=2, ensure_ascii=False)
        expected_structured_data = {"text": raw_text}
    else:
        expected_text = raw_text
        expected_structured_data = json.loads(raw_text)

    assert document.text == expected_text
    assert document._get_structured_data() == expected_structured_data


def test_index_document_from_structured_data_populates_text() -> None:
    payload = {"alpha": 1}

    document = IndexDocument(structured_data=payload)

    assert document.structured_data == payload
    assert document.text is None
    assert json.loads(document._get_text()) == payload


def test_index_document_requires_single_content_source() -> None:
    with pytest.raises(ValidationError):
        IndexDocument()

    with pytest.raises(ValidationError):
        IndexDocument(text="{}", structured_data={"foo": "bar"})
