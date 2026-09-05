"""Exact source segmentation shared by extractors and the offline model lab."""

import re

# A period between digits belongs to the amount, including unsupported precision.
_SENTENCE = re.compile(r"(?:[^\n.!?]|(?<=\d)\.(?=\d))+[.!?]?")


def sentences(text: str) -> tuple[str, ...]:
    return tuple(part for match in _SENTENCE.finditer(text) if (part := match[0].strip()))
