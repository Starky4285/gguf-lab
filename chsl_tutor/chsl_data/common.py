"""Shared helpers: exact number formatting, MCQ options, and the reply format.

Every generator returns an Item. The answer is always computed in Python (and
cross-checked a second way inside the generator), so the model is never trained
on a wrong answer.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Callable, Iterable, List, Optional, Sequence

LETTERS = "abcd"


def F(x) -> Fraction:
    return x if isinstance(x, Fraction) else Fraction(x)


def fmt(x, unit: str = "") -> str:
    """Exact, exam-style number: 24, 12.5, 16 2/3, -8."""
    x = F(x)
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x.denominator == 1:
        s = str(x.numerator)
    else:
        # terminating decimal with at most 2 places?
        d = x.denominator
        while d % 2 == 0:
            d //= 2
        while d % 5 == 0:
            d //= 5
        if d == 1 and (x * 100).denominator == 1:
            s = f"{float(x):.2f}".rstrip("0").rstrip(".")
        else:
            whole, rem = divmod(x.numerator, x.denominator)
            frac = f"{rem}/{x.denominator}"
            s = f"{whole} {frac}" if whole else frac
    return f"{sign}{s}{unit}"


def ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def pct(x) -> str:
    return fmt(x, "%")


def rupees(x) -> str:
    return "Rs " + fmt(x)


def is_nice(x, max_den: int = 12) -> bool:
    """Exam answers are integers, .5/.25 decimals or small fractions."""
    return F(x).denominator <= max_den


@dataclass
class Item:
    family: str          # e.g. "quant.successive_percent"
    section: str         # Quant / Reasoning / English / GK / Strategy
    question: str
    answer: str          # display form of the correct answer
    trick: str
    steps: List[str]
    remember: str
    distractors: List[str] = field(default_factory=list)
    why: Optional[str] = None   # optional: used for a follow-up "why does it work?" turn


def make_options(rng: random.Random, correct: str, distractors: Iterable[str]):
    """Return (options_text, letter) with 4 unique options, or (None, None) if not enough distractors."""
    seen, opts = {correct}, [correct]
    for d in distractors:
        if d not in seen:
            seen.add(d)
            opts.append(d)
        if len(opts) == 4:
            break
    if len(opts) < 4:
        return None, None
    rng.shuffle(opts)
    letter = LETTERS[opts.index(correct)]
    text = "  ".join(f"({LETTERS[i]}) {o}" for i, o in enumerate(opts))
    return text, letter


def numeric_distractors(rng: random.Random, value, unit_fmt: Callable = fmt, extra: Sequence = ()):
    """Common-mistake values first, then near misses."""
    v = F(value)
    near = []
    for delta in (1, 2, 5, 10):
        near += [v + delta, v - delta]
    near += [v * 2, v / 2, v * Fraction(3, 2)]
    rng.shuffle(near)
    out = []
    for c in list(extra) + near:
        c = F(c)
        if c != v and c > 0 and is_nice(c):
            out.append(unit_fmt(c))
    return out


def render_answer(item: Item, letter: Optional[str]) -> str:
    ans = f"({letter}) {item.answer}" if letter else item.answer
    steps = "\n".join(f"{i}. {s}" for i, s in enumerate(item.steps, 1))
    return (
        f"Answer: {ans}\n"
        f"Trick: {item.trick}\n"
        f"Steps:\n{steps}\n"
        f"Remember: {item.remember}"
    )


USER_WRAPPERS = [
    "{q}",
    "{q}",
    "{q}",
    "Solve fast: {q}",
    "Shortcut please. {q}",
    "How to solve this in seconds? {q}",
    "SSC CHSL question: {q}",
    "{q} Give me the quickest method.",
    "Explain the trick: {q}",
]

WHY_PROMPTS = [
    "Why does that trick work?",
    "Can you explain why the shortcut is correct?",
    "I didn't get why this works. Explain simply.",
]
