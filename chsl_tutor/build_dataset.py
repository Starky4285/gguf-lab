#!/usr/bin/env python3
"""Build the CHSL Coach fine-tuning dataset.

    python build_dataset.py                       # 6000 rows -> data/train.jsonl, data/val.jsonl, data/eval.jsonl
    python build_dataset.py --n 12000             # bigger
    python build_dataset.py --extra data/my_questions.jsonl   # add your own PYQs (see data/my_questions_template.jsonl)

Every generated answer is computed in Python and cross-checked, so the model
only ever sees correct answers. Output rows use the standard chat format
{"messages": [{"role": "system"|"user"|"assistant", "content": ...}]}.
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import sys
from pathlib import Path

from chsl_data import quant, reasoning, seeds
from chsl_data.common import Item, USER_WRAPPERS, WHY_PROMPTS, make_options, render_answer
from chsl_data.quant import Retry

HERE = Path(__file__).resolve().parent
SYSTEM_PROMPT = (HERE / "system_prompt.txt").read_text(encoding="utf-8").strip()

TOPICS = {
    "quant.successive_percent": "successive percentage change", "quant.consumption": "price rise and consumption",
    "quant.more_less_than": "'x% more than' / 'x% less than'", "quant.percent_equation": "x% of A = y% of B",
    "quant.percent_fraction": "percent to fraction conversion", "quant.false_weight": "false weight (dishonest dealer)",
    "quant.same_sp": "same selling price with equal profit and loss %", "quant.cp_sp_articles": "CP of x articles = SP of y articles",
    "quant.successive_discount": "successive discounts", "quant.mp_discount": "marked price and discount",
    "quant.loss_to_profit": "loss to profit swing questions", "quant.si_multiple": "simple interest 'sum becomes k times'",
    "quant.ci_si_diff": "difference between CI and SI", "quant.ci_two_year": "compound interest for 2 years",
    "quant.work_together": "time and work (working together)", "quant.work_one_from_together": "time and work (one person alone)",
    "quant.pipes": "pipes and cisterns", "quant.average_speed": "average speed", "quant.train_cross": "train crossing a pole or platform",
    "quant.trains_relative": "two trains crossing each other", "quant.boats": "boats and streams", "quant.ratio_combine": "combining ratios",
    "quant.partnership": "partnership", "quant.average_new": "average when a member is added or replaced",
    "quant.alligation": "alligation and mixtures", "quant.ages": "problems on ages", "quant.unit_digit": "unit digit of powers",
    "quant.divisors": "number of factors", "quant.remainder_9": "remainder when divided by 9", "quant.hcf_lcm": "HCF and LCM",
    "quant.square_trick": "fast squaring", "quant.x_plus_inverse": "x + 1/x identities", "quant.sum_product": "a + b and ab identities",
    "quant.trig_tan_ratio": "trigonometric ratios given tanθ", "quant.equilateral": "equilateral triangle formulas",
    "quant.area_change": "percentage change in area", "quant.avg_series": "average of natural/odd/even numbers",
    "reasoning.number_series": "number series", "reasoning.coding": "coding-decoding", "reasoning.letter_position": "alphabet positions",
    "reasoning.clock_angle": "angle between clock hands", "reasoning.mirror_clock": "mirror image of a clock",
    "reasoning.calendar": "calendar (odd days)", "reasoning.direction": "direction and distance", "reasoning.ranking": "ranking and order",
}
TEACH_PROMPTS = ["Teach me the shortcut for {t}.", "What is the trick for {t} questions?", "Explain {t} with one example."]


def sample_generated(rng: random.Random, n: int, seen: set):
    gens = quant.GENERATORS + reasoning.GENERATORS
    funcs, weights = zip(*gens)
    items, fails = [], collections.Counter()
    tries = 0
    while len(items) < n:
        tries += 1
        if tries > n * 60:
            sys.exit(f"Could not create enough unique questions (got {len(items)}). Lower --n.")
        f = rng.choices(funcs, weights)[0]
        try:
            it = f(rng)
        except Retry:
            fails[f.__name__] += 1
            continue
        if it.question in seen:
            continue
        seen.add(it.question)
        items.append(it)
    return items


def to_rows(rng: random.Random, it: Item, mcq_rate=0.65, why_rate=0.15, teach_rate=0.06):
    """One Item -> one chat example (sometimes MCQ, sometimes 2-turn)."""
    sys_msg = {"role": "system", "content": SYSTEM_PROMPT}
    if it.family in TOPICS and rng.random() < teach_rate:
        topic = TOPICS[it.family]
        user = rng.choice(TEACH_PROMPTS).format(t=topic)
        steps = "\n".join(f"{i}. {s}" for i, s in enumerate(it.steps, 1))
        reply = (f"Rule: {it.trick}\nExample: {it.question}\n"
                 f"Steps:\n{steps}\nResult: {it.answer}\nRemember: {it.remember}")
        return {"messages": [sys_msg, {"role": "user", "content": user}, {"role": "assistant", "content": reply}]}, None

    letter, q = None, it.question
    if it.distractors and it.section in ("Quant", "Reasoning", "English") and rng.random() < mcq_rate:
        opts, letter = make_options(rng, it.answer, it.distractors)
        if opts:
            q = f"{it.question}\n{opts}"
    wrap = rng.choice(USER_WRAPPERS) if it.section in ("Quant", "Reasoning") else "{q}"
    user = wrap.format(q=q)
    msgs = [sys_msg, {"role": "user", "content": user}, {"role": "assistant", "content": render_answer(it, letter)}]
    if it.why and rng.random() < why_rate:
        msgs += [{"role": "user", "content": rng.choice(WHY_PROMPTS)}, {"role": "assistant", "content": it.why}]
    gold = {"question": user, "answer": it.answer, "letter": letter, "family": it.family}
    return {"messages": msgs}, gold


def load_extra(path: Path):
    """Your own questions. One JSON object per line:
    {"question": "...", "options": ["..", "..", "..", ".."] (optional), "answer": "...",
     "trick": "...", "steps": ["..", ".."], "remember": "...", "section": "Quant"}"""
    items = []
    for ln, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError as e:
            sys.exit(f"{path}:{ln}: bad JSON ({e})")
        missing = [k for k in ("question", "answer", "trick", "steps", "remember") if not d.get(k)]
        if missing:
            sys.exit(f"{path}:{ln}: missing {missing}")
        steps = d["steps"] if isinstance(d["steps"], list) else [s.strip() for s in str(d["steps"]).split("\n") if s.strip()]
        q, letter = d["question"], None
        if d.get("options"):
            opts = d["options"]
            if d["answer"] not in opts:
                sys.exit(f"{path}:{ln}: answer must be exactly one of the options")
            letter = "abcd"[opts.index(d["answer"])]
            q += "\n" + "  ".join(f"({'abcd'[i]}) {o}" for i, o in enumerate(opts))
        it = Item("extra", d.get("section", "Quant"), q, d["answer"], d["trick"], steps, d["remember"])
        items.append((it, letter))
    return items


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=6000, help="number of generated Quant+Reasoning questions")
    ap.add_argument("--eval", type=int, default=300, help="held-out questions for eval_gguf.py")
    ap.add_argument("--val", type=float, default=0.03, help="validation fraction")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--extra", type=Path, action="append", default=[], help="your own JSONL questions (repeatable)")
    ap.add_argument("--extra-repeat", type=int, default=3, help="how many times to repeat your own questions (they are precious)")
    ap.add_argument("--out", type=Path, default=HERE / "data")
    a = ap.parse_args()

    rng = random.Random(a.seed)
    seen: set = set()
    gen_items = sample_generated(rng, a.n + a.eval, seen)
    eval_items, train_items = gen_items[:a.eval], gen_items[a.eval:]

    rows = []
    for it in train_items:
        rows.append(to_rows(rng, it)[0])
    seed_items = seeds.all_seed_items(rng)
    for it in seed_items:
        rows.append(to_rows(rng, it)[0])
    n_extra = 0
    for p in a.extra:
        for it, letter in load_extra(p):
            for _ in range(a.extra_repeat):
                rows.append({"messages": [{"role": "system", "content": SYSTEM_PROMPT},
                                          {"role": "user", "content": it.question},
                                          {"role": "assistant", "content": render_answer(it, letter)}]})
                n_extra += 1

    rng.shuffle(rows)
    n_val = max(1, int(len(rows) * a.val))
    val, train = rows[:n_val], rows[n_val:]

    evals = []
    erng = random.Random(a.seed + 1)
    for it in eval_items:
        _, gold = to_rows(erng, it, mcq_rate=0.5, why_rate=0, teach_rate=0)
        evals.append(gold)

    a.out.mkdir(parents=True, exist_ok=True)
    for name, data in (("train", train), ("val", val), ("eval", evals)):
        with open(a.out / f"{name}.jsonl", "w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    fam = collections.Counter(it.family.split(".")[0] for it in train_items + seed_items)
    print(f"train: {len(train)}  val: {len(val)}  eval: {len(evals)}  (your own rows: {n_extra})")
    print("by section:", dict(fam))
    print(f"written to {a.out}")


if __name__ == "__main__":
    main()
