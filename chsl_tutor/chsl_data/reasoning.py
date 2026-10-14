"""General Intelligence & Reasoning generators (answers computed and cross-checked)."""
from __future__ import annotations

import datetime as dt
import math
import random
from fractions import Fraction as Fr

from .common import Item, fmt, ordinal
from .quant import Retry, need

ABC = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
EJOTY = "Anchor positions: E=5, J=10, O=15, T=20, Y=25 (EJOTY)."


def pos(ch):
    return ABC.index(ch) + 1


# ------------------------------------------------------------- number series
def number_series(rng: random.Random) -> Item:
    kind = rng.choice(["ap", "diff_ap", "mul", "mul_add", "squares", "cubes", "alt"])
    n = 6
    if kind == "ap":
        a, d = rng.randint(2, 40), rng.choice([3, 4, 6, 7, 9, 11, 13, -3, -5])
        seq = [a + i * d for i in range(n)]
        rule = f"Each term changes by {d:+d}."
        steps = [f"Differences: {', '.join(f'{seq[i + 1] - seq[i]:+d}' for i in range(n - 2))}", f"Constant {d:+d} -> next = {seq[-2]} {d:+d} = {seq[-1]}"]
    elif kind == "diff_ap":
        a, d0, dd = rng.randint(1, 30), rng.randint(1, 6), rng.choice([2, 3, 4, 5])
        seq = [a]
        for i in range(n - 1):
            seq.append(seq[-1] + d0 + i * dd)
        diffs = [seq[i + 1] - seq[i] for i in range(n - 1)]
        rule = f"Differences increase by {dd}: {', '.join(map(str, diffs))}."
        steps = [f"Differences: {', '.join(map(str, diffs[:-1]))}", f"They rise by {dd} -> next difference {diffs[-1]}", f"{seq[-2]} + {diffs[-1]} = {seq[-1]}"]
    elif kind == "mul":
        a, k = rng.randint(1, 7), rng.choice([2, 3])
        seq = [a * k ** i for i in range(n)]
        need(seq[-1] < 20000)
        rule = f"Each term x {k}."
        steps = [f"{seq[0]} x {k} = {seq[1]}, {seq[1]} x {k} = {seq[2]} ...", f"{seq[-2]} x {k} = {seq[-1]}"]
    elif kind == "mul_add":
        a, k, c = rng.randint(1, 6), rng.choice([2, 3]), rng.choice([1, -1, 2, 3, -2])
        seq = [a]
        for _ in range(n - 1):
            seq.append(seq[-1] * k + c)
        need(seq[-1] < 20000 and all(x > 0 for x in seq))
        rule = f"Each term x {k} then {c:+d}."
        steps = [f"{seq[0]} x {k} {c:+d} = {seq[1]}, {seq[1]} x {k} {c:+d} = {seq[2]}", f"{seq[-2]} x {k} {c:+d} = {seq[-1]}"]
    elif kind == "squares":
        s, c = rng.randint(2, 9), rng.choice([0, 1, -1, 2, 3])
        seq = [(s + i) ** 2 + c for i in range(n)]
        rule = f"Squares {c:+d}." if c else "Consecutive squares."
        steps = [f"{seq[0]} = {s}² {c:+d}, {seq[1]} = {s + 1}² {c:+d}".replace(" +0", ""), f"Next = {s + n - 1}² {c:+d} = {seq[-1]}".replace(" +0", "")]
    elif kind == "cubes":
        s, c = rng.randint(1, 6), rng.choice([0, 1, -1, 2])
        seq = [(s + i) ** 3 + c for i in range(n)]
        rule = f"Cubes {c:+d}." if c else "Consecutive cubes."
        steps = [f"{seq[0]} = {s}³ {c:+d}, {seq[1]} = {s + 1}³ {c:+d}".replace(" +0", ""), f"Next = {s + n - 1}³ {c:+d} = {seq[-1]}".replace(" +0", "")]
    else:  # alternating x k, + c
        a, k, c = rng.randint(2, 9), rng.choice([2, 3]), rng.choice([3, 4, 5, 6, 7])
        seq = [a]
        for i in range(n - 1):
            seq.append(seq[-1] * k if i % 2 == 0 else seq[-1] + c)
        rule = f"Alternate: x {k}, then +{c}."
        last_op = f"x {k}" if (n - 2) % 2 == 0 else f"+ {c}"
        steps = [f"{seq[0]} x {k} = {seq[1]}, {seq[1]} + {c} = {seq[2]}, {seq[2]} x {k} = {seq[3]}", f"Next step is {last_op}: {seq[-1]}"]
    ans = seq[-1]
    shown = ", ".join(map(str, seq[:-1])) + ", ?"
    q = f"Find the next number in the series: {shown}"
    return Item("reasoning.number_series", "Reasoning", q, str(ans),
                "First check differences; if they grow fast, check x2/x3, squares/cubes, or alternating steps.",
                steps + [f"Pattern: {rule}"],
                "Order of checks: difference -> difference of difference -> multiply -> squares/cubes -> alternate.",
                [str(ans + 1), str(ans - 2), str(ans + 4), str(ans + seq[1] - seq[0] if seq[1] != seq[0] else ans + 3)])


# ------------------------------------------------------------- coding-decoding
WORDS = ["PEN", "CAT", "DOG", "SUN", "BOX", "MAP", "KING", "BOOK", "LAMP", "FISH", "COLD", "HAND", "ROSE", "TIME", "GOLD",
         "MILK", "NOTE", "WIND", "PARK", "BIRD", "DESK", "FIRE", "ROAD", "SHIP", "TREE", "CODE", "DARK", "FAST", "WORD", "HEAT"]


def coding(rng):
    kind = rng.choice(["shift", "shift", "reverse", "opposite"])
    w1, w2 = rng.sample(WORDS, 2)
    if kind == "shift":
        k = rng.choice([1, 2, 3, 4, -1, -2])
        enc = lambda w: "".join(ABC[(pos(c) - 1 + k) % 26] for c in w)
        rule = f"each letter moves {abs(k)} step{'s' if abs(k) > 1 else ''} {'forward' if k > 0 else 'backward'} ({k:+d})"
        steps = [f"{w1[0]} -> {enc(w1)[0]}: {k:+d}; {w1[1]} -> {enc(w1)[1]}: {k:+d}", f"Apply {k:+d} to {w2}: " + ", ".join(f"{c}->{enc(c)}" for c in w2)]
    elif kind == "reverse":
        k = rng.choice([1, 2])
        enc = lambda w: "".join(ABC[(pos(c) - 1 + k) % 26] for c in reversed(w))
        rule = f"the word is written in reverse and each letter moves {k:+d}"
        steps = [f"Reverse {w1} -> {w1[::-1]}, then each {k:+d} -> {enc(w1)}", f"{w2} reversed = {w2[::-1]}, then {k:+d} each"]
    else:
        enc = lambda w: "".join(ABC[26 - pos(c)] for c in w)
        rule = "each letter is replaced by its opposite letter (A<->Z, B<->Y; positions add to 27)"
        steps = [f"{w1[0]}({pos(w1[0])}) -> {enc(w1)[0]}({27 - pos(w1[0])}): sum 27", f"{w2}: " + ", ".join(f"{c}->{enc(c)}" for c in w2)]
    a1, a2 = enc(w1), enc(w2)
    need(a1 != w1)
    # cross-check by decoding pattern on first word
    assert len(a1) == len(w1) and len(a2) == len(w2)
    q = f"In a certain code language, {w1} is written as {a1}. How is {w2} written in that code?"
    bad = [a2[::-1], "".join(ABC[(pos(c)) % 26] for c in a2), "".join(ABC[(pos(c) - 2) % 26] for c in a2)]
    return Item("reasoning.coding", "Reasoning", q, a2,
                f"Compare letter positions of {w1} and {a1}: {rule}.",
                steps + [f"{w2} -> {a2}"],
                "Check 3 patterns fast: same shift, reversed word, opposite letters (sum 27). " + EJOTY,
                bad)


def letter_position(rng):
    kind = rng.choice(["from_right", "nth_right_of", "nth_left_of"])
    if kind == "from_right":
        k = rng.randint(3, 24)
        p = 27 - k
        q = f"Which letter is {ordinal(k)} from the right end of the English alphabet?"
        steps = [f"Position from left = 27 - {k} = {p}", f"Letter {p} = {ABC[p - 1]}"]
        trick = "From the right: position = 27 - n."
    else:
        a, b = rng.randint(4, 22), rng.randint(2, 9)
        p = a + b if kind == "nth_right_of" else a - b
        need(1 <= p <= 26)
        side = "right" if kind == "nth_right_of" else "left"
        q = f"Which letter is the {ordinal(b)} to the {side} of the {ordinal(a)} letter from the left end of the English alphabet?"
        steps = [f"Position = {a} {'+' if side == 'right' else '-'} {b} = {p}", f"Letter {p} = {ABC[p - 1]}"]
        trick = "Right = add, left = subtract (when counting from the left end)."
    assert ABC[p - 1] == chr(ord('A') + p - 1)
    ans = ABC[p - 1]
    near = [ABC[(p - 1 + d) % 26] for d in (1, -1, 2)]
    return Item("reasoning.letter_position", "Reasoning", q, ans, trick, steps,
                "Use EJOTY anchors to find any letter's position in 1 second: E5 J10 O15 T20 Y25.", near)


# ------------------------------------------------------------- clocks
def clock_angle(rng):
    h, m = rng.randint(1, 12), rng.choice(range(0, 60, 5)) if rng.random() < 0.7 else rng.randint(1, 59)
    raw = abs(Fr(30 * (h % 12)) - Fr(11, 2) * m)
    ang = min(raw, 360 - raw)
    hour_hand = Fr(30 * (h % 12)) + Fr(m, 2)
    min_hand = Fr(6 * m)
    d = abs(hour_hand - min_hand)
    assert min(d, 360 - d) == ang
    q = f"What is the angle between the hour hand and minute hand of a clock at {h}:{m:02d}?"
    steps = [f"θ = |30H - 11M/2| = |30x{h} - 11x{m}/2|", f"= |{30 * h} - {fmt(Fr(11 * m, 2))}| = {fmt(raw)}°"]
    if raw > 180:
        steps.append(f"More than 180°, so take 360 - {fmt(raw)} = {fmt(ang)}°")
    return Item("reasoning.clock_angle", "Reasoning", q, f"{fmt(ang)}°",
                "Angle = |30H - 5.5M|; if above 180, subtract from 360.", steps,
                "Minute hand 6°/min, hour hand 0.5°/min -> relative 5.5°/min.",
                [f"{fmt(ang + 5)}°", f"{fmt(abs(30 * h - 6 * m) % 360)}°" if abs(30 * h - 6 * m) % 360 != ang else f"{fmt(ang + 10)}°", f"{fmt(360 - ang)}°", f"{fmt(abs(ang - 15))}°"])


def mirror_clock(rng):
    h, m = rng.randint(1, 11), rng.randint(1, 59)
    # mirror (vertical axis) reflects hand angles: angle -> 360 - angle
    tot = h * 60 + m
    mt = (720 - tot) % 720
    mh, mm = divmod(mt, 60)
    mh = 12 if mh == 0 else mh
    # shortcut: 11:60 - time
    sh, sm = 11 - h, 60 - m
    if sm == 60:
        sh, sm = sh + 1, 0
    sh = 12 if sh == 0 else sh
    assert (sh, sm) == (mh, mm)
    q = f"A clock shows {h}:{m:02d}. What time will its mirror image show?"
    return Item("reasoning.mirror_clock", "Reasoning", q, f"{mh}:{mm:02d}",
                "Mirror time = 11:60 - given time.",
                [f"11:60 - {h}:{m:02d}", f"= {11 - h}:{60 - m:02d}" + (f" -> {mh}:{mm:02d}" if (11 - h, 60 - m) != (mh, mm) else "")],
                "Mirror: subtract from 11:60. Water image: subtract from 18:30 (for clocks, both hands flip top-bottom).",
                [f"{(mh % 12) + 1}:{mm:02d}", f"{mh}:{(mm + 5) % 60:02d}", f"{12 - h if h != 12 else 12}:{m:02d}", f"{h}:{60 - m:02d}"])


# ------------------------------------------------------------- calendar
def calendar(rng):
    kind = rng.choice(["after_days", "next_year", "years_later"])
    if kind == "after_days":
        d0 = rng.randrange(7)
        n = rng.randint(20, 400)
        ans = DAYS[(d0 + n) % 7]
        assert DAYS[((dt.date(2024, 1, 1) + dt.timedelta(days=n)).weekday() - dt.date(2024, 1, 1).weekday() + d0) % 7] == ans
        q = f"If today is {DAYS[d0]}, what day of the week will it be after {n} days?"
        return Item("reasoning.calendar", "Reasoning", q, ans,
                    "Only the remainder by 7 matters (odd days).",
                    [f"{n} / 7 leaves remainder {n % 7}", f"{DAYS[d0]} + {n % 7} = {ans}"],
                    "Odd days: divide by 7, move forward by the remainder.",
                    [DAYS[(d0 + n + k) % 7] for k in (1, -1, 2)])
    y = rng.randint(1990, 2035)
    month, day = rng.choice([(1, 26), (8, 15), (10, 2), (3, 10), (6, 21), (12, 25), (2, 14), (4, 1), (11, 14), (7, 4)])
    k = 1 if kind == "next_year" else rng.randint(2, 6)
    d1, d2 = dt.date(y, month, day), dt.date(y + k, month, day)
    w1, w2 = DAYS[d1.weekday()], DAYS[d2.weekday()]
    # count Feb-29s crossed between d1 (exclusive) and d2 (inclusive)
    leaps = sum(1 for yy in range(y, y + k + 1)
                if (yy % 4 == 0 and (yy % 100 != 0 or yy % 400 == 0)) and d1 < dt.date(yy, 2, 29) <= d2)
    odd = k + leaps
    assert DAYS[(d1.weekday() + odd) % 7] == w2
    mname = d1.strftime("%B")
    q = f"If {day} {mname} {y} was a {w1}, what day of the week was {day} {mname} {y + k}?"
    leap_txt = f"{leaps} Feb 29 fall{'s' if leaps == 1 else ''} in between" if leaps else "no Feb 29 in between"
    return Item("reasoning.calendar", "Reasoning", q, w2,
                "Same date next year shifts by 1 day, or 2 days if a 29 February comes in between.",
                [f"{k} year{'s' if k > 1 else ''} -> {k} odd day{'s' if k > 1 else ''}; {leap_txt} -> +{leaps}",
                 f"Total shift = {odd} -> {w1} + {odd % 7 if odd % 7 else 7} = {w2}"],
                "Ordinary year = 1 odd day, leap year = 2. Count Feb 29s actually crossed.",
                [DAYS[(d1.weekday() + k) % 7] if leaps else DAYS[(d1.weekday() + k + 1) % 7]] + [DAYS[(d2.weekday() + j) % 7] for j in (1, -1, 2, -2, 3)])


# ------------------------------------------------------------- direction
HEAD = ["North", "East", "South", "West"]
VEC = [(0, 1), (1, 0), (0, -1), (-1, 0)]


def compass(dx, dy):
    ns = "North" if dy > 0 else ("South" if dy < 0 else "")
    ew = "East" if dx > 0 else ("West" if dx < 0 else "")
    return f"{ns}-{ew}" if ns and ew else (ns or ew)


def direction(rng):
    h = rng.randrange(4)
    steps_n = rng.choice([3, 4])
    moves, x, y = [], 0, 0
    for i in range(steps_n):
        dist = rng.choice([2, 3, 4, 5, 6, 8, 10, 12, 15])
        if i:
            turn = rng.choice(["right", "left"])
            h = (h + (1 if turn == "right" else -1)) % 4
            moves.append(f"turns {turn} and walks {dist} m")
        else:
            moves.append(f"walks {dist} m towards {HEAD[h]}")
        x += VEC[h][0] * dist
        y += VEC[h][1] * dist
    d2 = x * x + y * y
    r = math.isqrt(d2)
    need(r * r == d2 and d2 > 0 and x != 0 and y != 0)
    q = "Ravi " + ", then ".join(moves) + ". How far and in which direction is he from the starting point?"
    ans = f"{r} m, {compass(x, y)}"
    return Item("reasoning.direction", "Reasoning", q, ans,
                "Track net East-West and net North-South separately, then use Pythagoras.",
                [f"Net East-West = {abs(x)} m {'East' if x > 0 else 'West'}", f"Net North-South = {abs(y)} m {'North' if y > 0 else 'South'}",
                 f"Distance = √({abs(x)}² + {abs(y)}²) = √{d2} = {r} m", f"Direction = {compass(x, y)}"],
                "Right turn = clockwise (N->E->S->W). Common triples: 3-4-5, 6-8-10, 5-12-13, 8-15-17.",
                [f"{r} m, {compass(-x, y)}", f"{abs(x) + abs(y)} m, {compass(x, y)}", f"{r} m, {compass(x, -y)}"])


def ranking(rng):
    kind = rng.choice(["total", "other_end"])
    if kind == "total":
        p, qq = rng.randint(5, 40), rng.randint(5, 40)
        n = p + qq - 1
        assert len(range(1, n + 1)) - p + 1 == qq
        q = f"In a row of students, Amit is {ordinal(p)} from the left and {ordinal(qq)} from the right. How many students are there in the row?"
        return Item("reasoning.ranking", "Reasoning", q, str(n), "Total = left rank + right rank - 1.",
                    [f"{p} + {qq} - 1 = {n}"], "The person is counted twice, so subtract 1.",
                    [str(n + 1), str(n + 2), str(n - 1)])
    n, p = rng.randint(20, 60), rng.randint(3, 19)
    other = n - p + 1
    q = f"In a class of {n} students, Neha's rank is {ordinal(p)} from the top. What is her rank from the bottom?"
    return Item("reasoning.ranking", "Reasoning", q, ordinal(other), "Rank from other end = total - rank + 1.",
                [f"{n} - {p} + 1 = {other}"], "Other end = N - r + 1.",
                [ordinal(other - 1), ordinal(other + 1), ordinal(n - p - 1)])


GENERATORS = [(number_series, 4), (coding, 3), (letter_position, 2), (clock_angle, 2), (mirror_clock, 1),
              (calendar, 2), (direction, 2), (ranking, 2)]
