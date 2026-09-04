from __future__ import annotations

import re
from itertools import pairwise
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
SCRIPT_PATH = REPO_ROOT / "DEMO-SCRIPT.md"


def _seconds(value: str) -> int:
    minutes, seconds = value.split(":")
    return int(minutes) * 60 + int(seconds)


def _timeline(markdown: str, heading: str, next_heading: str) -> list[tuple[int, int]]:
    section = markdown.split(heading, maxsplit=1)[1].split(next_heading, maxsplit=1)[0]
    return [
        (_seconds(start), _seconds(end))
        for start, end in re.findall(r"\| (\d{2}:\d{2})-(\d{2}:\d{2}) \|", section)
    ]


def test_demo_timelines_are_contiguous_and_exact() -> None:
    markdown = SCRIPT_PATH.read_text(encoding="utf-8")

    two_minute = _timeline(markdown, "## Two-minute golden demo", "## Five-minute")
    five_minute = _timeline(markdown, "## Five-minute video/pitch", "## Technical")

    assert two_minute[0][0] == 0
    assert two_minute[-1][1] == 120
    assert five_minute[0][0] == 0
    assert five_minute[-1][1] == 300
    assert all(left[1] == right[0] for left, right in pairwise(two_minute))
    assert all(left[1] == right[0] for left, right in pairwise(five_minute))


def test_pitch_discloses_saved_metrics_and_boundaries() -> None:
    markdown = SCRIPT_PATH.read_text(encoding="utf-8")

    for required in (
        "15349fd24f2fbceb1c6a38edafee92d5953f22af2e9611efcda17ba20f1992b8",
        "60 balanced cases",
        "precision is 10/10",
        "recall is 10/20",
        "false BLOCK is 0",
        "false PASS is 10",
        "partial_full_amount` slice is 0/10 correct",
        "no model-backed B1 is claimed",
        "not a legal verdict",
        "not a win probability",
        "makes no Razorpay writes",
    ):
        assert required in markdown

    lower = markdown.lower()
    assert "production-grade" not in lower
    assert "pci compliant" not in lower
    assert "guaranteed savings" not in lower
