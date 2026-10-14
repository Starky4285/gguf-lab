"""Quantitative Aptitude generators.

Each function builds one question, solves it with the exam shortcut, and then
re-solves it the long way. If the two disagree, an AssertionError is raised and
the build fails - so wrong answers cannot reach the training data.
Raise Retry when random numbers give an ugly (non exam-like) answer.
"""
from __future__ import annotations

import math
import random
from fractions import Fraction as Fr

from .common import Item, fmt, pct, rupees, is_nice, numeric_distractors


class Retry(Exception):
    pass


def need(cond):
    if not cond:
        raise Retry


def change_word(x):
    x = Fr(x)
    if x > 0:
        return f"{pct(x)} increase"
    if x < 0:
        return f"{pct(-x)} decrease"
    return "no change"


def pm(a, b):
    """'40 - 40' / '20 + 10' style for a + b with signs."""
    return f"{fmt(a)} {'-' if b < 0 else '+'} {fmt(abs(b))}"


def gain_loss(x):
    x = Fr(x)
    return "No profit no loss" if x == 0 else (f"{pct(x)} gain" if x > 0 else f"{pct(-x)} loss")


def signed(x):
    x = Fr(x)
    return f"+{fmt(x)}" if x >= 0 else f"-{fmt(-x)}"


# ---------------------------------------------------------------- percentage
def successive_percent(rng: random.Random) -> Item:
    a = rng.choice([10, 20, 25, 30, 40, 50, 60])
    b = rng.choice([-10, -20, -25, -30, -40, -50, 10, 20, 25, 30])
    net = Fr(a + b) + Fr(a * b, 100)
    assert net == (Fr(100 + a, 100) * Fr(100 + b, 100) - 1) * 100
    def word(x):
        return f"increased by {x}%" if x > 0 else f"decreased by {-x}%"
    ctx = rng.choice([
        f"The price of an article is first {word(a)} and then {word(b)}. Find the net percentage change in price.",
        f"The population of a town {word(a).replace('increased', 'increases').replace('decreased', 'decreases')} in the first year and {word(b).replace('increased', 'increases').replace('decreased', 'decreases')} in the second year. Find the net percentage change over two years.",
        f"A salary is {word(a)} and the new salary is then {word(b)}. What is the net change in salary?",
    ])
    return Item(
        "quant.successive_percent", "Quant", ctx, change_word(net),
        "Two successive changes a% and b%: net = a + b + ab/100 (use minus sign for decrease).",
        [f"a = {signed(a)}, b = {signed(b)}",
         f"{pm(a, b)} + ({a} x {b})/100",
         f"= {pm(a + b, Fr(a * b, 100))} = {fmt(net)}% -> {change_word(net)}"],
        "Net % = a + b + ab/100.",
        [change_word(a + b), change_word(-net), change_word(Fr(a + b) - Fr(a * b, 100)), change_word(net + 1)],
        why="Start with 100. After a% it is 100 + a. The second change b% acts on (100 + a), so it adds b + ab/100. Total extra = a + b + ab/100.",
    )


def consumption_adjust(rng):
    x = rng.choice([10, 20, 25, 30, 40, 50, 60, 75, 100])
    up = rng.random() < 0.65
    if not up:
        x = rng.choice([10, 20, 25, 40, 50])
    r = Fr(x * 100, 100 + x) if up else Fr(x * 100, 100 - x)
    need(is_nice(r))
    if up:
        assert Fr(100 + x, 100) * (1 - r / 100) == 1
        item = rng.choice(["sugar", "petrol", "rice", "milk"])
        q = f"The price of {item} rises by {x}%. By what percent should a family reduce its consumption so that the expenditure does not change?"
        steps = [f"Reduction = x/(100 + x) x 100", f"= {x}/{100 + x} x 100", f"= {pct(r)}"]
        trick = "Price up x% -> cut consumption by x/(100 + x) x 100 to keep spending same."
        rem = "Up x% -> reduce x/(100+x); down x% -> increase x/(100-x)."
    else:
        assert Fr(100 - x, 100) * (1 + r / 100) == 1
        q = f"The price of tea falls by {x}%. By what percent can a person increase consumption without increasing expenditure?"
        steps = [f"Increase = x/(100 - x) x 100", f"= {x}/{100 - x} x 100", f"= {pct(r)}"]
        trick = "Price down x% -> consumption can rise by x/(100 - x) x 100."
        rem = "Down x% -> increase x/(100-x); up x% -> reduce x/(100+x)."
    wrong = (Fr(x * 100, 100 - x) if x < 100 else Fr(x, 2)) if up else Fr(x * 100, 100 + x)
    return Item("quant.consumption", "Quant", q, pct(r), trick, steps, rem,
                [pct(x), pct(wrong)] + numeric_distractors(rng, r, pct),
                why="Expenditure = price x consumption must stay 100. New price is (100 + x), so consumption must become 100 x 100/(100 + x). The drop from 100 is 100x/(100 + x).")


def more_less_than(rng):
    more = rng.random() < 0.6
    x = Fr(rng.choice([10, 20, 25, 50, 60, 100, Fr(25, 2), Fr(100, 3)] if more else [10, 20, 25, 50, 60, 75, 80, Fr(25, 2), Fr(100, 3)]))
    r = x * 100 / (100 + x) if more else x * 100 / (100 - x)
    need(is_nice(r))
    a, b = rng.sample(["A", "Ravi", "Sita", "Mohan", "Priya", "Arjun"], 2)
    if more:
        q = f"{a}'s salary is {pct(x)} more than {b}'s. By what percent is {b}'s salary less than {a}'s?"
        assert (100 + x) * (1 - r / 100) == 100
        steps = [f"Less % = x/(100 + x) x 100", f"= {fmt(x)}/{fmt(100 + x)} x 100 = {pct(r)}"]
        trick = "If A is x% more than B, B is x/(100 + x) x 100 % less than A."
    else:
        q = f"{a}'s income is {pct(x)} less than {b}'s. By what percent is {b}'s income more than {a}'s?"
        assert (100 - x) * (1 + r / 100) == 100
        steps = [f"More % = x/(100 - x) x 100", f"= {fmt(x)}/{fmt(100 - x)} x 100 = {pct(r)}"]
        trick = "If A is x% less than B, B is x/(100 - x) x 100 % more than A."
    return Item("quant.more_less_than", "Quant", q, pct(r), trick, steps,
                "Base changes, so the % changes: divide by (100 + x) or (100 - x).",
                [pct(x)] + numeric_distractors(rng, r, pct))


def percent_equation(rng):
    x, y = rng.sample([10, 12, 15, 20, 25, 30, 40, 45, 50, 60, 75], 2)
    g = math.gcd(x, y)
    q = f"If {x}% of A = {y}% of B, then find A : B."
    assert Fr(x, 100) * y == Fr(y, 100) * x
    ans = f"{y // g} : {x // g}"
    return Item("quant.percent_equation", "Quant", q, ans,
                "x% of A = y% of B -> A : B = y : x (cross over).",
                [f"A x {x} = B x {y}", f"A : B = {y} : {x}", f"= {ans}"],
                "Percent on A goes under B: A : B = y : x.",
                [f"{x // g} : {y // g}", f"{y // g + 1} : {x // g}", f"{x // g} : {y // g + 1}", f"{y // g} : {x // g + 1}", f"{y // g + 2} : {x // g + 1}"])


PCT_FRAC = [(Fr(25, 2), Fr(1, 8)), (Fr(75, 2), Fr(3, 8)), (Fr(125, 2), Fr(5, 8)), (Fr(175, 2), Fr(7, 8)),
            (Fr(50, 3), Fr(1, 6)), (Fr(100, 3), Fr(1, 3)), (Fr(200, 3), Fr(2, 3)), (Fr(250, 3), Fr(5, 6)),
            (Fr(100, 9), Fr(1, 9)), (Fr(100, 7), Fr(1, 7)), (Fr(100, 11), Fr(1, 11)), (Fr(25, 4), Fr(1, 16)),
            (Fr(20), Fr(1, 5)), (Fr(40), Fr(2, 5)), (Fr(60), Fr(3, 5)), (Fr(80), Fr(4, 5)), (Fr(125), Fr(5, 4))]


def percent_fraction(rng):
    p, f = rng.choice(PCT_FRAC)
    assert p / 100 == f
    n = f.denominator * rng.randint(3, 40)
    val = f * n
    q = f"Find {pct(p)} of {n}."
    return Item("quant.percent_fraction", "Quant", q, fmt(val),
                f"{pct(p)} = {f.numerator}/{f.denominator}. Multiply by the fraction instead of the percent.",
                [f"{pct(p)} = {f}", f"{n} / {f.denominator} = {n // f.denominator}",
                 f"{n // f.denominator} x {f.numerator} = {fmt(val)}"],
                "Learn the % <-> fraction table: 12.5=1/8, 16 2/3=1/6, 14 2/7=1/7, 11 1/9=1/9, 9 1/11=1/11.",
                numeric_distractors(rng, val, fmt, [val + f.numerator * 2, val * Fr(9, 10)]))


# ------------------------------------------------------------ profit & loss
def false_weight(rng):
    w = rng.choice([600, 625, 700, 750, 800, 840, 850, 875, 880, 900, 920, 940, 950, 960, 980, 990])
    x = rng.choice([0, 0, 0, 5, 10, 12, 15, 20, 25])
    p = (Fr(100 + x, 100) * Fr(1000, w) - 1) * 100
    need(is_nice(p))
    item = rng.choice(["rice", "sugar", "pulses", "tea", "wheat", "spices"])
    if x == 0:
        assert Fr(1000 - w, w) * 100 == p
        q = f"A shopkeeper claims to sell {item} at cost price but uses a weight of {w} g instead of 1 kg. Find his gain percent."
        return Item("quant.false_weight", "Quant", q, pct(p),
                    "Gain % = (error / weight actually given) x 100.",
                    [f"Error = 1000 - {w} = {1000 - w} g", f"Gain = {1000 - w}/{w} x 100", f"= {pct(p)}"],
                    "False weight: divide the error by what he actually GIVES, not by 1000.",
                    [pct(Fr(1000 - w, 10)), pct(p + 1), pct(p - 1) if p > 1 else pct(p + 3), pct(p * 2)])
    fw = Fr(1000 - w, w) * 100
    q = f"A dealer sells {item} at {x}% profit and also uses a weight of {w} g for 1 kg. Find his total gain percent."
    return Item("quant.false_weight", "Quant", q, pct(p),
                "Two gains act one after another: use successive % (a + b + ab/100).",
                [f"Weight gain = {1000 - w}/{w} x 100 = {pct(fw)}",
                 f"Total = {x} + {fmt(fw)} + ({x} x {fmt(fw)})/100", f"= {pct(p)}"],
                "Profit % and false-weight % combine like successive changes.",
                [pct(x + fw), pct(Fr(1000 - w, 10) + x), pct(p + 2), pct(p - 3)])


def same_sp_profit_loss(rng):
    x = rng.choice([5, 10, 15, 20, 25, 30, 40])
    s = rng.choice([990, 1200, 1500, 2400, 3000, 4800, 600])
    loss = Fr(x * x, 100)
    c1, c2 = Fr(s) / Fr(100 + x, 100), Fr(s) / Fr(100 - x, 100)
    assert (c1 + c2 - 2 * s) / (c1 + c2) * 100 == loss
    q = f"A man sells two watches at Rs {s} each. On one he gains {x}% and on the other he loses {x}%. Find his overall gain or loss percent."
    return Item("quant.same_sp", "Quant", q, f"{pct(loss)} loss",
                "Same SP, same x% gain and x% loss -> always a LOSS of x^2/100 %.",
                [f"Loss % = x^2/100", f"= {x}^2/100 = {x * x}/100", f"= {pct(loss)} loss"],
                "Same SP, +x% and -x% -> loss of (x/10)^2 %. The SP value does not matter.",
                ["No profit no loss", f"{pct(loss)} gain", f"{pct(x)} loss", f"{pct(loss * 2)} loss"],
                why="Equal % on equal SP: the loss-making item has a bigger CP than the profit-making one, so the loss amount is larger. Working it out always gives x^2/100 % loss.")


def cp_sp_articles(rng):
    x, y = rng.sample(range(5, 41), 2)
    p = Fr(x - y, y) * 100
    need(is_nice(p) and abs(p) <= 60)
    assert (Fr(x, y) - 1) * 100 == p
    q = f"The cost price of {x} articles is equal to the selling price of {y} articles. Find the gain or loss percent."
    word = "gain" if p > 0 else "loss"
    return Item("quant.cp_sp_articles", "Quant", q, f"{pct(abs(p))} {word}",
                "CP of x = SP of y -> profit % = (x - y)/y x 100 (negative = loss).",
                [f"(x - y)/y x 100 = ({x} - {y})/{y} x 100", f"= {pct(p)} -> {pct(abs(p))} {word}"],
                "Divide by the SP count (y), not the CP count.",
                [f"{pct(abs(Fr(x - y, x) * 100))} {word}", f"{pct(abs(p))} {'loss' if p > 0 else 'gain'}",
                 f"{pct(abs(p) + 5)} {word}", f"{pct(abs(p) * 2)} {word}"])


def successive_discount(rng):
    d1, d2 = rng.choice([10, 20, 25, 30, 40]), rng.choice([5, 10, 15, 20, 25])
    d = Fr(d1 + d2) - Fr(d1 * d2, 100)
    assert (1 - Fr(100 - d1, 100) * Fr(100 - d2, 100)) * 100 == d
    with_mp = rng.random() < 0.5
    if with_mp:
        mp = rng.choice([800, 1000, 1200, 2000, 2500, 4000, 5000])
        sp = Fr(mp) * (100 - d) / 100
        need(is_nice(sp, 2))
        q = f"An article marked at Rs {mp} is sold after two successive discounts of {d1}% and {d2}%. Find the selling price."
        return Item("quant.successive_discount", "Quant", q, rupees(sp),
                    "Convert two discounts into one: d1 + d2 - d1d2/100.",
                    [f"Single discount = {d1} + {d2} - {d1}x{d2}/100 = {pct(d)}",
                     f"SP = {mp} x {fmt(100 - d)}/100 = {rupees(sp)}"],
                    "Successive discounts are never added directly.",
                    [rupees(Fr(mp) * (100 - d1 - d2) / 100), rupees(sp + 10), rupees(sp - 20), rupees(sp + 50)])
    q = f"Find a single discount equivalent to two successive discounts of {d1}% and {d2}%."
    return Item("quant.successive_discount", "Quant", q, pct(d),
                "Single discount = d1 + d2 - d1d2/100.",
                [f"{d1} + {d2} - ({d1} x {d2})/100", f"= {d1 + d2} - {fmt(Fr(d1 * d2, 100))} = {pct(d)}"],
                "Successive discounts: same as successive % with both negative.",
                [pct(d1 + d2), pct(d + 1), pct(d - 2), pct(Fr(d1 + d2) + Fr(d1 * d2, 100))])


def mp_discount_profit(rng):
    m = rng.choice(range(10, 81, 5))
    d = rng.choice(range(5, 41, 5))
    p = Fr(m - d) - Fr(m * d, 100)
    assert (Fr(100 + m, 100) * Fr(100 - d, 100) - 1) * 100 == p
    q = f"A trader marks his goods {m}% above cost price and allows a discount of {d}%. Find his gain or loss percent."
    ans = gain_loss(p)
    return Item("quant.mp_discount", "Quant", q, ans,
                "Mark-up m% then discount d%: profit % = m - d - md/100.",
                [f"{m} - {d} - ({m} x {d})/100", f"= {m - d} - {fmt(Fr(m * d, 100))} = {pct(p)} -> {gain_loss(p)}"],
                "Mark-up and discount are successive changes (+m, -d).",
                [gain_loss(m - d), gain_loss(p + 2), gain_loss(p - 5), gain_loss(-p) if p else gain_loss(5), gain_loss(m)])


def loss_to_profit(rng):
    x, z = rng.choice([5, 8, 10, 12, 15, 20]), rng.choice([5, 10, 12, 15, 20, 25])
    cp = rng.choice([400, 500, 600, 800, 1000, 1200, 1500, 2000, 2500])
    diff = Fr(cp * (x + z), 100)
    need(diff.denominator == 1)
    assert diff / (x + z) * 100 == cp
    q = f"A man sells an article at a loss of {x}%. If he had sold it for Rs {fmt(diff)} more, he would have gained {z}%. Find the cost price."
    return Item("quant.loss_to_profit", "Quant", q, rupees(cp),
                "Loss x% to gain z% is a swing of (x + z)% of CP = the extra money.",
                [f"Swing = {x}% + {z}% = {x + z}% of CP", f"{x + z}% of CP = {fmt(diff)}",
                 f"CP = {fmt(diff)} x 100/{x + z} = {rupees(cp)}"],
                "Loss -> gain: ADD the percents. Gain -> more gain: SUBTRACT them.",
                [rupees(Fr(diff * 100, abs(z - x) or 1)), rupees(cp + 100), rupees(cp - 100), rupees(cp * 2)])


# -------------------------------------------------------- interest
def si_multiple(rng):
    k = rng.choice([2, 3])
    n = rng.choice([4, 5, 8, 10, 12, 16, 20])
    j = rng.choice([x for x in (3, 4, 5, 6, 7) if x != k])
    rate = Fr((k - 1) * 100, n)
    years = Fr(j - 1, k - 1) * n
    assert 1 + rate * years / 100 == j
    times = {2: "double", 3: "three times"}[k]
    q = f"A sum of money becomes {times} itself in {n} years at simple interest. In how many years will it become {j} times itself?"
    return Item("quant.si_multiple", "Quant", q, f"{fmt(years)} years",
                "At SI, interest grows in equal steps: years are proportional to (times - 1).",
                [f"{k} times -> interest = {k - 1} P in {n} years", f"{j} times -> interest = {j - 1} P",
                 f"Years = {j - 1}/{k - 1} x {n} = {fmt(years)}"],
                "SI: 'k times' means (k - 1) parts of interest. Rate = (k - 1) x 100 / n.",
                [f"{fmt(Fr(j, k) * n)} years", f"{fmt(years + n)} years", f"{fmt(years - n // 2)} years", f"{fmt(n * j)} years",
                 f"{fmt(years + 2)} years", f"{fmt(years * 2)} years", f"{fmt(years + 1)} years"])


def ci_si_diff(rng):
    r = rng.choice([4, 5, 8, 10, 12, 15, 20])
    p = rng.choice([1000, 2000, 2500, 5000, 8000, 10000, 12500, 15000, 20000])
    d = p * Fr(r, 100) ** 2
    need(is_nice(d, 4))
    ci = p * ((1 + Fr(r, 100)) ** 2 - 1)
    si = p * Fr(2 * r, 100)
    assert ci - si == d
    if rng.random() < 0.5:
        q = f"Find the difference between compound interest and simple interest on Rs {p} for 2 years at {r}% per annum."
        return Item("quant.ci_si_diff", "Quant", q, rupees(d),
                    "2-year CI - SI = P (r/100)^2.",
                    [f"P (r/100)^2 = {p} x ({r}/100)^2", f"= {p} x {r * r}/10000 = {rupees(d)}"],
                    "2 years: diff = P(r/100)^2. 3 years: diff = P(r/100)^2 (3 + r/100).",
                    numeric_distractors(rng, d, rupees, [d * 2, Fr(p * r, 100)]),
                    why="In year 2, CI earns interest on the first year's interest (P x r/100) as well. That extra is (P x r/100) x r/100 = P(r/100)^2. SI has no such extra.")
    q = f"The difference between compound interest and simple interest on a sum for 2 years at {r}% per annum is Rs {fmt(d)}. Find the sum."
    return Item("quant.ci_si_diff", "Quant", q, rupees(p),
                "P = difference x (100/r)^2 for 2 years.",
                [f"P = {fmt(d)} x (100/{r})^2", f"= {fmt(d)} x {fmt(Fr(10000, r * r))} = {rupees(p)}"],
                "2-year CI - SI = P (r/100)^2, so P = D (100/r)^2.",
                [rupees(p * 2), rupees(p // 2), rupees(p + 1000), rupees(Fr(p * 3, 2))])


def ci_two_year(rng):
    r = rng.choice([5, 10, 20, 4, 8, 15])
    p = rng.choice([2000, 4000, 5000, 8000, 10000, 12000, 16000, 20000])
    eff = Fr(2 * r) + Fr(r * r, 100)
    ci = p * eff / 100
    assert ci == p * ((1 + Fr(r, 100)) ** 2 - 1)
    need(is_nice(ci, 4))
    q = f"Find the compound interest on Rs {p} for 2 years at {r}% per annum, compounded annually."
    return Item("quant.ci_two_year", "Quant", q, rupees(ci),
                "2-year CI rate = 2r + r^2/100 (successive % with a = b = r).",
                [f"Effective % = {2 * r} + {r}^2/100 = {pct(eff)}", f"CI = {p} x {fmt(eff)}/100 = {rupees(ci)}"],
                "CI 2 years: 10% -> 21%, 20% -> 44%, 5% -> 10.25%.",
                [rupees(p * Fr(2 * r, 100)), rupees(ci + 100), rupees(ci - 50), rupees(ci * 2)])


# -------------------------------------------------------- time & work
def lcm(*xs):
    out = 1
    for x in xs:
        out = out * x // math.gcd(out, x)
    return out


def work_together(rng):
    three = rng.random() < 0.3
    if three:
        days = rng.sample([6, 8, 10, 12, 15, 18, 20, 24, 30, 36, 40, 60], 3)
    else:
        days = rng.sample([4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 21, 24, 28, 30, 36, 40, 45, 60], 2)
    t = 1 / sum(Fr(1, d) for d in days)
    need(is_nice(t, 8))
    L = lcm(*days)
    eff = [L // d for d in days]
    assert Fr(L, sum(eff)) == t
    names = ["A", "B", "C"][:len(days)]
    if three:
        q = f"A can do a piece of work in {days[0]} days, B in {days[1]} days and C in {days[2]} days. In how many days will A, B and C together finish it?"
    else:
        q = f"A can do a work in {days[0]} days and B can do it in {days[1]} days. In how many days will they finish it together?"
    steps = [f"Total work = LCM({', '.join(map(str, days))}) = {L} units",
             "Per day: " + ", ".join(f"{n} = {e}" for n, e in zip(names, eff)) + f" -> together {sum(eff)} units/day",
             f"Time = {L}/{sum(eff)} = {fmt(t)} days"]
    if not three:
        steps.append(f"Check: ab/(a+b) = {days[0] * days[1]}/{sum(days)} = {fmt(t)}")
    return Item("quant.work_together", "Quant", q, f"{fmt(t)} days",
                "LCM method: take total work = LCM of days, find units per day, then divide." + ("" if three else " For two people: ab/(a + b)."),
                steps, "Never add days. Add per-day work (efficiency).",
                [f"{fmt(Fr(sum(days), len(days)))} days", f"{fmt(t + 1)} days", f"{fmt(t + 2)} days", f"{fmt(sum(days))} days"],
                why="If total work is LCM units, each person's daily units are whole numbers. Efficiencies add when people work together, so time = total units / combined units per day.")


def work_one_from_together(rng):
    a, b = rng.sample([6, 8, 10, 12, 15, 18, 20, 24, 30, 36, 40, 60], 2)
    t = Fr(a * b, a + b)
    need(is_nice(t, 1))
    L = lcm(a, int(t))
    q = f"A and B together can finish a work in {fmt(t)} days. A alone can do it in {a} days. In how many days can B alone do it?"
    assert 1 / (Fr(1, t) - Fr(1, a)) == b
    return Item("quant.work_one_from_together", "Quant", q, f"{b} days",
                "B alone = (A x T)/(A - T), where T is the together time.",
                [f"Total = LCM({a}, {fmt(t)}) = {L} units", f"A + B = {L // int(t)}/day, A = {L // a}/day -> B = {L // int(t) - L // a}/day",
                 f"B alone = {L}/{L // int(t) - L // a} = {b} days"],
                "Subtract efficiencies, never days.",
                [f"{a - int(t)} days", f"{b + 2} days", f"{b * 2} days", f"{b + 5} days"])


def pipes(rng):
    a, b = rng.sample([2, 3, 4, 5, 6, 8, 10, 12, 15, 18, 20, 24, 30], 2)
    a, b = min(a, b), max(a, b)
    t = Fr(a * b, b - a)
    need(is_nice(t, 4))
    assert 1 / (Fr(1, a) - Fr(1, b)) == t
    L = lcm(a, b)
    q = f"Pipe A can fill a tank in {a} hours and pipe B can empty it in {b} hours. If both are opened together, in how much time will the empty tank be filled?"
    return Item("quant.pipes", "Quant", q, f"{fmt(t)} hours",
                "Filling pipe +, emptying pipe -. Net time = ab/(b - a).",
                [f"Tank = LCM({a}, {b}) = {L} units", f"A = +{L // a}/h, B = -{L // b}/h -> net {L // a - L // b}/h",
                 f"Time = {L}/{L // a - L // b} = {fmt(t)} hours"],
                "Leak/emptying pipe = negative efficiency.",
                [f"{fmt(Fr(a * b, a + b))} hours", f"{b - a} hours", f"{fmt(t + 2)} hours", f"{fmt(t * 2)} hours"])


# -------------------------------------------------------- speed, trains, boats
def average_speed(rng):
    x, y = rng.sample([20, 24, 30, 36, 40, 45, 48, 50, 60, 72, 80, 90], 2)
    v = Fr(2 * x * y, x + y)
    need(is_nice(v, 4))
    d = lcm(x, y)
    assert Fr(2 * d) / (Fr(d, x) + Fr(d, y)) == v
    q = f"A car goes from P to Q at {x} km/h and returns from Q to P at {y} km/h. Find the average speed for the whole journey."
    return Item("quant.average_speed", "Quant", q, f"{fmt(v)} km/h",
                "Equal distances: average speed = 2xy/(x + y), NOT (x + y)/2.",
                [f"2 x {x} x {y} / ({x} + {y})", f"= {2 * x * y}/{x + y} = {fmt(v)} km/h"],
                "Same distance -> 2xy/(x+y). Same time -> (x+y)/2.",
                [f"{fmt(Fr(x + y, 2))} km/h", f"{fmt(v + 2)} km/h", f"{fmt(v - 2)} km/h", f"{fmt(v + 5)} km/h"],
                why="Average speed = total distance / total time. Take distance d each way: time = d/x + d/y. So 2d / (d/x + d/y) = 2xy/(x + y). The slower leg takes more time, so the average leans towards the slower speed.")


def train_cross(rng):
    s = rng.choice([36, 45, 54, 72, 90, 108, 60, 48])
    v = Fr(s * 5, 18)
    L = rng.choice([100, 120, 150, 180, 200, 240, 250, 300, 360])
    platform = rng.random() < 0.5
    P = rng.choice([100, 150, 200, 250, 300]) if platform else 0
    t = (L + P) / v
    need(is_nice(t, 2))
    assert t * v == L + P
    if platform:
        q = f"A train {L} m long running at {s} km/h crosses a platform {P} m long. How much time does it take?"
        steps = [f"Speed = {s} x 5/18 = {fmt(v)} m/s", f"Distance = train + platform = {L} + {P} = {L + P} m",
                 f"Time = {L + P}/{fmt(v)} = {fmt(t)} s"]
    else:
        q = f"A train {L} m long is running at {s} km/h. In how much time will it cross a pole?"
        steps = [f"Speed = {s} x 5/18 = {fmt(v)} m/s", f"Distance = train length = {L} m", f"Time = {L}/{fmt(v)} = {fmt(t)} s"]
    return Item("quant.train_cross", "Quant", q, f"{fmt(t)} seconds",
                "km/h to m/s: x 5/18. Pole/man: distance = train length. Platform/bridge: add its length.",
                steps, "Learn: 36 km/h = 10 m/s, 54 = 15, 72 = 20, 90 = 25, 108 = 30.",
                [f"{fmt(Fr(L, v))} seconds" if platform else f"{fmt((L + 100) / v)} seconds",
                 f"{fmt(t + 2)} seconds", f"{fmt(t * 2)} seconds", f"{fmt((L + P) / s)} seconds"])


def trains_relative(rng):
    s1, s2 = rng.sample([36, 45, 54, 60, 72, 90, 108], 2)
    L1, L2 = rng.choice([100, 120, 150, 200, 250]), rng.choice([100, 150, 200, 250, 300])
    opp = rng.random() < 0.5
    rel = (s1 + s2) if opp else abs(s1 - s2)
    v = Fr(rel * 5, 18)
    t = Fr(L1 + L2) / v
    need(is_nice(t, 2))
    assert t * Fr(rel * 5, 18) == L1 + L2
    dirn = "opposite directions" if opp else "the same direction"
    wrong_rel = abs(s1 - s2) if opp else s1 + s2
    wrong = f"{fmt(Fr(L1 + L2) / Fr(wrong_rel * 5, 18))} seconds" if wrong_rel else f"{fmt(t + 3)} seconds"
    q = f"Two trains of lengths {L1} m and {L2} m are running in {dirn} at {s1} km/h and {s2} km/h. In how much time will they cross each other?"
    return Item("quant.trains_relative", "Quant", q, f"{fmt(t)} seconds",
                "Opposite: add speeds. Same direction: subtract. Distance = sum of both lengths.",
                [f"Relative speed = {max(s1, s2)} {'+' if opp else '-'} {min(s1, s2)} = {rel} km/h = {fmt(v)} m/s",
                 f"Distance = {L1} + {L2} = {L1 + L2} m", f"Time = {L1 + L2}/{fmt(v)} = {fmt(t)} s"],
                "Opposite -> add, same -> subtract, lengths always add.",
                [wrong, f"{fmt(t + 2)} seconds", f"{fmt(t * 2)} seconds", f"{fmt(t + 5)} seconds"])


def boats(rng):
    b, c = rng.choice([(9, 3), (10, 2), (12, 4), (15, 3), (8, 2), (14, 4), (11, 1), (13, 3), (16, 4), (18, 2)])
    D, U = b + c, b - c
    td, tu = rng.choice([1, 2, 3, 4]), rng.choice([2, 3, 4, 5])
    dd, du = D * td, U * tu
    assert Fr(dd, td) + Fr(du, tu) == 2 * b and Fr(dd, td) - Fr(du, tu) == 2 * c
    ask_boat = rng.random() < 0.5
    q = (f"A boat goes {dd} km downstream in {td} hours and {du} km upstream in {tu} hours. "
         f"Find the {'speed of the boat in still water' if ask_boat else 'speed of the stream'}.")
    ans = b if ask_boat else c
    return Item("quant.boats", "Quant", q, f"{ans} km/h",
                "Boat = (down + up)/2, Stream = (down - up)/2.",
                [f"Downstream = {dd}/{td} = {D} km/h, Upstream = {du}/{tu} = {U} km/h",
                 f"{'Boat = (' + str(D) + ' + ' + str(U) + ')/2' if ask_boat else 'Stream = (' + str(D) + ' - ' + str(U) + ')/2'} = {ans} km/h"],
                "Down = B + S, Up = B - S. Half the sum = boat, half the difference = stream.",
                [f"{c if ask_boat else b} km/h", f"{D} km/h", f"{U} km/h", f"{ans + 1} km/h", f"{ans + 2} km/h"])


# -------------------------------------------------------- ratio, average, mixture
def ratio_combine(rng):
    a, b, c, d = [rng.randint(2, 9) for _ in range(4)]
    need(math.gcd(a, b) == 1 and math.gcd(c, d) == 1 and b != c)
    A, B, C = a * c, b * c, b * d
    g = math.gcd(math.gcd(A, B), C)
    A, B, C = A // g, B // g, C // g
    assert Fr(A, B) == Fr(a, b) and Fr(B, C) == Fr(c, d)
    q = f"If A : B = {a} : {b} and B : C = {c} : {d}, find A : B : C."
    return Item("quant.ratio_combine", "Quant", q, f"{A} : {B} : {C}",
                "Make B equal: multiply first ratio by B's value in the second, and the second by B's value in the first.",
                [f"A : B = {a} : {b} -> x {c} -> {a * c} : {b * c}", f"B : C = {c} : {d} -> x {b} -> {b * c} : {b * d}",
                 f"A : B : C = {a * c} : {b * c} : {b * d}" + (f" = {A} : {B} : {C}" if g > 1 else "")],
                "N-shape multiply: A = a x c, B = b x c, C = b x d.",
                [f"{a} : {b} : {d}", f"{a * d} : {b * c} : {b * d}", f"{C} : {B} : {A}", f"{A} : {C} : {B}"])


def partnership(rng):
    x, y = rng.choice([3, 4, 5, 6, 8, 10, 12]), rng.choice([2, 4, 5, 6, 9, 15])
    m, n = rng.choice([12, 6, 8, 9, 10]), rng.choice([12, 6, 4, 8, 3])
    ra, rb = x * m, y * n
    g = math.gcd(ra, rb)
    ra, rb = ra // g, rb // g
    total = (ra + rb) * rng.randint(200, 1200)
    share = Fr(total * ra, ra + rb)
    assert share.denominator == 1
    q = (f"A invests Rs {x * 1000} for {m} months and B invests Rs {y * 1000} for {n} months in a business. "
         f"Out of a total profit of Rs {total}, find A's share.")
    return Item("quant.partnership", "Quant", q, rupees(share),
                "Profit ratio = capital x time.",
                [f"A : B = {x * 1000} x {m} : {y * 1000} x {n} = {ra} : {rb}",
                 f"A's share = {total} x {ra}/{ra + rb} = {rupees(share)}"],
                "Cancel the zeros first: work with capital in thousands.",
                [rupees(total - share), rupees(Fr(total * x, x + y)), rupees(share + 100), rupees(share - 200)])


def average_new(rng):
    n = rng.choice([5, 8, 10, 12, 15, 20, 24, 30])
    avg = rng.randint(20, 60)
    dlt = rng.choice([Fr(1), Fr(2), Fr(1, 2), Fr(3), Fr(3, 2)])
    mode = rng.choice(["add", "replace"])
    if mode == "add":
        new = avg + (n + 1) * dlt
        need(new.denominator == 1)
        assert (n * avg + new) / (n + 1) == avg + dlt
        q = (f"The average age of {n} students is {avg} years. When the teacher's age is included, the average increases by {fmt(dlt)} year{'s' if dlt != 1 else ''}. "
             f"Find the teacher's age.")
        return Item("quant.average_new", "Quant", q, f"{fmt(new)} years",
                    "New member = old average + (new count x increase).",
                    [f"New count = {n + 1}", f"Teacher = {avg} + {n + 1} x {fmt(dlt)}", f"= {fmt(new)} years"],
                    "Added person brings the old average plus enough to raise everyone by the increase.",
                    [f"{fmt(avg + n * dlt)} years", f"{fmt(new + 1)} years", f"{fmt(new + dlt * 2)} years", f"{fmt(avg + dlt)} years"])
    old = rng.randint(30, 70)
    new = old + n * dlt
    need(new.denominator == 1)
    assert (n * avg - old + new) / n == avg + dlt
    q = (f"The average weight of {n} persons increases by {fmt(dlt)} kg when a person weighing {old} kg is replaced by a new person. "
         f"Find the weight of the new person.")
    return Item("quant.average_new", "Quant", q, f"{fmt(new)} kg",
                "Replacement: new = old + (count x change in average).",
                [f"Increase in total = {n} x {fmt(dlt)} = {fmt(n * dlt)} kg", f"New person = {old} + {fmt(n * dlt)} = {fmt(new)} kg"],
                "Replace: new = old + n x change (minus if average falls).",
                [f"{fmt(old + (n + 1) * dlt)} kg", f"{fmt(old - n * dlt)} kg" if old - n * dlt > 0 else f"{fmt(new + 5)} kg", f"{fmt(new + 2)} kg", f"{fmt(old + dlt)} kg"])


def alligation(rng):
    c, d = sorted(rng.sample([20, 25, 30, 32, 36, 40, 45, 48, 50, 60, 64, 70, 80], 2))
    m = rng.randint(c + 1, d - 1)
    r1, r2 = d - m, m - c
    g = math.gcd(r1, r2)
    r1, r2 = r1 // g, r2 // g
    assert Fr(c * r1 + d * r2, r1 + r2) == m
    q = f"In what ratio must rice at Rs {c}/kg be mixed with rice at Rs {d}/kg so that the mixture costs Rs {m}/kg?"
    return Item("quant.alligation", "Quant", q, f"{r1} : {r2}",
                "Alligation cross: (dearer - mean) : (mean - cheaper).",
                [f"Cheaper : Dearer = ({d} - {m}) : ({m} - {c})", f"= {d - m} : {m - c} = {r1} : {r2}"],
                "Write the two prices, mean in the middle, subtract crosswise.",
                [f"{r2} : {r1}", f"{r1 + 1} : {r2}", f"{r1} : {r2 + 1}", f"{c} : {d}"])


def ages(rng):
    k = rng.randint(2, 9)
    a, b = rng.choice([(3, 4), (2, 3), (4, 5), (5, 7), (3, 5), (5, 6), (4, 7), (2, 5), (1, 2), (3, 7)])
    A, B = a * k, b * k
    n = rng.choice([3, 4, 5, 6, 8, 10])
    c, d = A + n, B + n
    g = math.gcd(c, d)
    c, d = c // g, d // g
    need((c, d) != (a, b))
    # ratio-difference method
    D = lcm(b - a, d - c)
    s1, s2 = D // (b - a), D // (d - c)
    unit_change = c * s2 - a * s1
    need(unit_change > 0)
    per_unit = Fr(n, unit_change)
    assert a * s1 * per_unit == A
    q = f"The present ages of A and B are in the ratio {a} : {b}. After {n} years the ratio will be {c} : {d}. Find A's present age."
    return Item("quant.ages", "Quant", q, f"{A} years",
                "Age difference never changes: make the ratio differences equal, then compare.",
                [f"Now {a} : {b} (diff {b - a}) -> x{s1} -> {a * s1} : {b * s1}",
                 f"Later {c} : {d} (diff {d - c}) -> x{s2} -> {c * s2} : {d * s2}",
                 f"{c * s2 - a * s1} unit{'s' if unit_change > 1 else ''} = {n} years -> 1 unit = {fmt(per_unit)} years",
                 f"A now = {a * s1} x {fmt(per_unit)} = {A} years"],
                "Equalise the difference of ratio terms; the change in units = years passed.",
                [f"{B} years", f"{A + n} years", f"{A + 2} years", f"{A * 2} years"])


# -------------------------------------------------------- number system
CYCLE = {0: [0], 1: [1], 2: [2, 4, 8, 6], 3: [3, 9, 7, 1], 4: [4, 6], 5: [5], 6: [6], 7: [7, 9, 3, 1], 8: [8, 4, 2, 6], 9: [9, 1]}


def unit_digit(rng):
    base = rng.choice([2, 3, 7, 8, 12, 13, 17, 18, 22, 23, 27, 28, 33, 37, 4, 9, 14, 19, 24, 29])
    e = rng.randint(21, 199)
    u = base % 10
    cyc = CYCLE[u]
    r = e % len(cyc)
    idx = len(cyc) if r == 0 else r
    ans = cyc[idx - 1]
    assert pow(base, e, 10) == ans
    q = f"Find the unit digit of {base}^{e}."
    return Item("quant.unit_digit", "Quant", q, str(ans),
                f"Only the last digit {u} matters. Its powers repeat in a cycle of {len(cyc)}: {', '.join(map(str, cyc))}.",
                [f"Last digit = {u}, cycle length {len(cyc)}",
                 f"{e} / {len(cyc)} leaves remainder {r}" + (f" -> treat as {len(cyc)}" if r == 0 else ""),
                 f"{u}^{idx} ends in {ans}"],
                "Cycles: 2,3,7,8 -> 4; 4,9 -> 2; 0,1,5,6 -> 1. Remainder 0 means the last in the cycle.",
                [str(x) for x in sorted(set(range(10)) - {ans}, key=lambda _: rng.random())])


def divisors_count(rng):
    primes = rng.sample([2, 3, 5, 7], rng.choice([2, 3]))
    exps = [rng.randint(1, 4) for _ in primes]
    n = 1
    for p, e in zip(primes, exps):
        n *= p ** e
    need(n <= 20000)
    cnt = 1
    for e in exps:
        cnt *= e + 1
    assert cnt == sum(1 for i in range(1, n + 1) if n % i == 0)
    fac = " x ".join(f"{p}^{e}" for p, e in zip(primes, exps))
    q = f"How many factors (divisors) does {n} have?"
    return Item("quant.divisors", "Quant", q, str(cnt),
                "n = p^a x q^b x ... -> number of factors = (a+1)(b+1)...",
                [f"{n} = {fac}", " x ".join(f"({e}+1)" for e in exps) + f" = {cnt}"],
                "Prime-factorise, add 1 to each power, multiply.",
                [str(sum(exps)), str(cnt + 2), str(cnt - 2), str(cnt * 2)])


def remainder_9(rng):
    n = rng.randint(10 ** 6, 10 ** 9)
    ds = sum(map(int, str(n)))
    r = n % 9
    assert ds % 9 == r
    q = f"What is the remainder when {n} is divided by 9?"
    return Item("quant.remainder_9", "Quant", q, str(r),
                "Remainder by 9 = remainder of the digit sum by 9.",
                [f"Digit sum = {' + '.join(str(n))} = {ds}", f"{ds} / 9 leaves {r}"],
                "Divisibility by 9 or 3: just add the digits.",
                [str((r + k) % 9) for k in (1, 2, 4, 5)])


def hcf_lcm(rng):
    h = rng.choice([4, 5, 6, 7, 8, 9, 11, 12, 13, 15, 16, 18])
    p, q_ = rng.sample([2, 3, 4, 5, 7, 9, 11], 2)
    need(math.gcd(p, q_) == 1)
    a, b = h * p, h * q_
    L = h * p * q_
    assert math.gcd(a, b) == h and a * b // math.gcd(a, b) == L
    q = f"The HCF and LCM of two numbers are {h} and {L}. If one number is {a}, find the other."
    return Item("quant.hcf_lcm", "Quant", q, str(b),
                "Product of two numbers = HCF x LCM.",
                [f"Other = HCF x LCM / given", f"= {h} x {L}/{a} = {b}"],
                "Only for TWO numbers: a x b = HCF x LCM.",
                [str(L // h), str(b + h), str(b * 2), str(L // p + 1)])


# -------------------------------------------------------- fast calculation
def square_trick(rng):
    mode = rng.choice(["100", "50", "5"])
    if mode == "100":
        n = rng.choice([x for x in range(88, 113) if x != 100])
        d = n - 100
        left, right = n + d, d * d
        ans = left * 100 + right
        steps = [f"{n} is {'+' if d > 0 else '-'}{abs(d)} from 100", f"Left part = {n} {'+' if d > 0 else '-'} {abs(d)} = {left}",
                 f"Right part = {abs(d)}^2 = {right:02d} (2 digits)", f"{n}^2 = {ans}"]
        trick = "Base 100: (number +/- its distance) | distance^2 in 2 digits."
    elif mode == "50":
        n = rng.choice([x for x in range(41, 60) if x != 50])
        d = n - 50
        left, right = 25 + d, d * d
        ans = left * 100 + right
        steps = [f"{n} is {'+' if d > 0 else '-'}{abs(d)} from 50", f"Left part = 25 {'+' if d > 0 else '-'} {abs(d)} = {left}",
                 f"Right part = {abs(d)}^2 = {right:02d}", f"{n}^2 = {ans}"]
        trick = "Base 50: (25 +/- distance) | distance^2 in 2 digits."
    else:
        k = rng.randint(1, 19)
        n = 10 * k + 5
        ans = k * (k + 1) * 100 + 25
        steps = [f"Tens part = {k}", f"{k} x {k + 1} = {k * (k + 1)}", f"Write 25 after it: {ans}"]
        trick = "Ending in 5: n x (n+1) then write 25."
    assert ans == n * n
    q = f"Find {n}^2 quickly."
    return Item("quant.square_trick", "Quant", q, str(ans), trick, steps,
                "Base 100 for 88-112, base 50 for 41-59, ending-5 rule for x5.",
                [str(ans + 100), str(ans - 10), str(ans + 20), str(ans - 100)])


# -------------------------------------------------------- algebra & trig
def x_plus_inverse(rng):
    k = rng.randint(2, 12)
    minus = rng.random() < 0.35
    which = rng.choice([2, 3, 4])
    if not minus:
        need(k >= 3)
    sg = -1 if minus else 1
    s2 = k * k + 2 if minus else k * k - 2
    val = {2: s2, 3: k ** 3 + 3 * k if minus else k ** 3 - 3 * k, 4: s2 * s2 - 2}[which]
    x = (k + math.sqrt(k * k + 4)) / 2 if minus else (k + math.sqrt(k * k - 4)) / 2
    real = x ** which + sg ** which * x ** -which if which != 4 else x ** 4 + x ** -4
    if minus and which == 3:
        real = x ** 3 - x ** -3
    assert abs(real - val) < 1e-6 * max(1, abs(val))
    op = "-" if minus else "+"
    op3 = "-" if minus else "+"
    lhs = {2: "x^2 + 1/x^2", 3: f"x^3 {op3} 1/x^3", 4: "x^4 + 1/x^4"}[which]
    q = f"If x {op} 1/x = {k}, find {lhs}."
    if minus:
        steps = {2: [f"Square: x^2 + 1/x^2 - 2 = {k * k}", f"x^2 + 1/x^2 = {k * k} + 2 = {val}"],
                 3: [f"x^3 - 1/x^3 = k^3 + 3k", f"= {k ** 3} + {3 * k} = {val}"],
                 4: [f"x^2 + 1/x^2 = {k}^2 + 2 = {s2}", f"x^4 + 1/x^4 = {s2}^2 - 2 = {val}"]}[which]
        trick = {2: "x - 1/x = k -> x^2 + 1/x^2 = k^2 + 2.", 3: "x - 1/x = k -> x^3 - 1/x^3 = k^3 + 3k.",
                 4: "k -> k^2 + 2 -> (k^2 + 2)^2 - 2."}[which]
    else:
        steps = {2: [f"Square both sides: x^2 + 1/x^2 + 2 = {k * k}", f"x^2 + 1/x^2 = {k * k} - 2 = {val}"],
                 3: [f"x^3 + 1/x^3 = k^3 - 3k", f"= {k ** 3} - {3 * k} = {val}"],
                 4: [f"x^2 + 1/x^2 = {k}^2 - 2 = {s2}", f"x^4 + 1/x^4 = {s2}^2 - 2 = {val}"]}[which]
        trick = {2: "x + 1/x = k -> x^2 + 1/x^2 = k^2 - 2.", 3: "x + 1/x = k -> x^3 + 1/x^3 = k^3 - 3k.",
                 4: "Square twice: k -> k^2 - 2 -> (k^2 - 2)^2 - 2."}[which]
    return Item("quant.x_plus_inverse", "Quant", q, str(val), trick, steps,
                "x + 1/x = k: square -> k^2 - 2, cube -> k^3 - 3k. x - 1/x = k: square -> k^2 + 2, cube -> k^3 + 3k.",
                [str(val + 2), str(val - 1), str(val + 4), str(k ** which), str(val - 4)])


def sum_product(rng):
    a, b = rng.sample(range(1, 12), 2)
    s, p = a + b, a * b
    which = rng.choice(["sq", "cube"])
    if which == "sq":
        val = s * s - 2 * p
        assert val == a * a + b * b
        q = f"If a + b = {s} and ab = {p}, find a^2 + b^2."
        steps = [f"a^2 + b^2 = (a + b)^2 - 2ab", f"= {s * s} - {2 * p} = {val}"]
        trick = "a^2 + b^2 = (a + b)^2 - 2ab."
    else:
        val = s ** 3 - 3 * p * s
        assert val == a ** 3 + b ** 3
        q = f"If a + b = {s} and ab = {p}, find a^3 + b^3."
        steps = [f"a^3 + b^3 = (a + b)^3 - 3ab(a + b)", f"= {s ** 3} - 3 x {p} x {s} = {s ** 3} - {3 * p * s} = {val}"]
        trick = "a^3 + b^3 = (a + b)^3 - 3ab(a + b)."
    return Item("quant.sum_product", "Quant", q, str(val), trick, steps,
                "Never solve for a and b separately - use the identity.",
                [str(val + 2 * p), str(val - p), str(s * s + 2 * p if which == 'sq' else s ** 3), str(val + 10)])


def trig_tan_ratio(rng):
    p, q_ = rng.sample(range(1, 10), 2)
    need(math.gcd(p, q_) == 1)
    a, b, c, d = rng.choice([(1, -1, 1, 1), (1, 1, 1, -1), (2, 3, 3, 2), (3, -2, 3, 2), (4, -5, 4, 5), (2, 1, 1, 2), (5, 3, 5, -3)])
    num, den = a * p + b * q_, c * p + d * q_
    need(den != 0 and num != 0)
    val = Fr(num, den)
    th = math.atan2(p, q_)
    real = (a * math.sin(th) + b * math.cos(th)) / (c * math.sin(th) + d * math.cos(th))
    assert abs(real - float(val)) < 1e-9

    def expr(x, y):
        s = f"{'' if x == 1 else x}sinθ" if x > 0 else f"-{'' if x == -1 else -x}sinθ"
        t = f"{'' if abs(y) == 1 else abs(y)}cosθ"
        return f"{s} {'+' if y > 0 else '-'} {t}"
    q = f"If tanθ = {p}/{q_}, find ({expr(a, b)}) / ({expr(c, d)})."
    return Item("quant.trig_tan_ratio", "Quant", q, fmt(val),
                "Divide top and bottom by cosθ, then put tanθ = p/q (or simply sinθ = p, cosθ = q).",
                [f"Put sinθ -> {p}, cosθ -> {q_}", f"Top = {a}x{p} {'+' if b > 0 else '-'} {abs(b)}x{q_} = {num}",
                 f"Bottom = {c}x{p} {'+' if d > 0 else '-'} {abs(d)}x{q_} = {den}", f"Answer = {num}/{den} = {fmt(val)}"],
                "Ratio of sin & cos terms with tanθ = p/q: replace sin by p and cos by q.",
                [fmt(1 / val), fmt(-val), fmt(val + 1), fmt(Fr(p, q_))],
                why="Dividing numerator and denominator by cosθ turns every sinθ/cosθ into tanθ = p/q. Multiplying top and bottom by q gives the same as using sin = p, cos = q directly.")


# -------------------------------------------------------- geometry & mensuration
def equilateral(rng):
    a = rng.choice(range(6, 73, 6))
    ask = rng.choice(["area", "height", "inradius", "circumradius"])
    coef = {"area": Fr(a * a, 4), "height": Fr(a, 2), "inradius": Fr(a, 6), "circumradius": Fr(a, 3)}[ask]
    real = {"area": math.sqrt(3) / 4 * a * a, "height": math.sqrt(3) / 2 * a,
            "inradius": a / (2 * math.sqrt(3)), "circumradius": a / math.sqrt(3)}[ask]
    assert abs(float(coef) * math.sqrt(3) - real) < 1e-9
    unit = "cm²" if ask == "area" else "cm"
    formula = {"area": "√3/4 x a²", "height": "√3/2 x a", "inradius": "a/(2√3) = a√3/6", "circumradius": "a/√3 = a√3/3"}[ask]
    names = {"area": "area", "height": "height", "inradius": "radius of the incircle", "circumradius": "radius of the circumcircle"}
    q = f"Find the {names[ask]} of an equilateral triangle of side {a} cm."
    ans = f"{fmt(coef)}√3 {unit}"
    return Item("quant.equilateral", "Quant", q, ans,
                f"Equilateral triangle: {names[ask]} = {formula}.",
                [f"{formula} with a = {a}", f"= {fmt(coef)}√3 {unit}"],
                "Equilateral: h = √3a/2, inradius = h/3, circumradius = 2h/3, area = √3a²/4.",
                [f"{fmt(coef * 2)}√3 {unit}", f"{fmt(coef / 2)}√3 {unit}", f"{fmt(coef)}√2 {unit}", f"{fmt(coef + 1)}√3 {unit}"])


def area_change(rng):
    x = rng.choice([10, 20, 25, 30, 40, 50])
    shape = rng.choice(["circle", "square", "rect"])
    if shape == "rect":
        y = rng.choice([-10, -20, 10, 20, 25])
        net = Fr(x + y) + Fr(x * y, 100)
        assert (Fr(100 + x, 100) * Fr(100 + y, 100) - 1) * 100 == net
        q = f"The length of a rectangle is increased by {x}% and the breadth is {'increased' if y > 0 else 'decreased'} by {abs(y)}%. Find the percentage change in area."
        steps = [f"{pm(x, y)} + ({x} x {y})/100", f"= {pm(x + y, Fr(x * y, 100))} = {fmt(net)}% -> {change_word(net)}"]
        trick = "Area = l x b, so use successive %: a + b + ab/100."
    else:
        net = Fr(2 * x) + Fr(x * x, 100)
        assert (Fr(100 + x, 100) ** 2 - 1) * 100 == net
        part = "radius of a circle" if shape == "circle" else "side of a square"
        q = f"If the {part} is increased by {x}%, by what percent does its area increase?"
        steps = [f"Area depends on the square, so a = b = {x}", f"{x} + {x} + {x}x{x}/100 = {fmt(net)}%"]
        trick = "Square of a length: area change = 2x + x²/100."
    return Item("quant.area_change", "Quant", q, change_word(net), trick, steps,
                "Area changes like two successive % changes; volume (cube) like three.",
                [change_word(2 * x if shape != 'rect' else x + y), change_word(net + 1), change_word(net * 2), change_word(x)])


def avg_series(rng):
    n = rng.randint(8, 150)
    kind = rng.choice(["natural", "odd", "even"])
    if kind == "natural":
        v = Fr(n + 1, 2); seq = list(range(1, n + 1)); txt = f"the first {n} natural numbers"; rule = "(n + 1)/2"
    elif kind == "odd":
        v = Fr(n); seq = list(range(1, 2 * n, 2)); txt = f"the first {n} odd numbers"; rule = "n"
    else:
        v = Fr(n + 1); seq = list(range(2, 2 * n + 1, 2)); txt = f"the first {n} even numbers"; rule = "n + 1"
    assert Fr(sum(seq), len(seq)) == v
    q = f"Find the average of {txt}."
    return Item("quant.avg_series", "Quant", q, fmt(v),
                f"Average of {txt.replace(str(n), 'n')} = {rule}.",
                [f"Rule: {rule}", f"n = {n} -> {fmt(v)}"],
                "First n natural: (n+1)/2. First n odd: n. First n even: n+1.",
                [fmt(Fr(n, 2)), fmt(v + 1), fmt(n + 2), fmt(v * 2)])


GENERATORS = [
    (successive_percent, 3), (consumption_adjust, 2), (more_less_than, 2), (percent_equation, 1), (percent_fraction, 2),
    (false_weight, 2), (same_sp_profit_loss, 2), (cp_sp_articles, 2), (successive_discount, 2), (mp_discount_profit, 2),
    (loss_to_profit, 2), (si_multiple, 2), (ci_si_diff, 2), (ci_two_year, 2), (work_together, 3), (work_one_from_together, 2),
    (pipes, 2), (average_speed, 2), (train_cross, 2), (trains_relative, 2), (boats, 2), (ratio_combine, 2), (partnership, 2),
    (average_new, 2), (alligation, 2), (ages, 2), (unit_digit, 2), (divisors_count, 1), (remainder_9, 1), (hcf_lcm, 1),
    (square_trick, 2), (x_plus_inverse, 2), (sum_product, 2), (trig_tan_ratio, 2), (equilateral, 2), (area_change, 2),
    (avg_series, 1),
]
