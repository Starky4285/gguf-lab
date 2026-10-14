"""Hand-written examples: English rules, exam strategy and safe-GK behaviour.

English items are classic error-spotting rules. Each one is turned into
several training rows with different wordings. Strategy items teach how to
attack the paper. GK items teach the model to give stable facts with a memory
hook and to REFUSE to guess current affairs.
"""
from __future__ import annotations

import random

from .common import Item

# (wrong sentence, corrected sentence, rule, remember)
ENGLISH_ERRORS = [
    ("One of my friend is a doctor.", "One of my friends is a doctor.", "'One of' takes a plural noun but a singular verb.", "One of + plural noun + singular verb."),
    ("He is senior than me.", "He is senior to me.", "Latin comparatives (senior, junior, superior, inferior, prior) take 'to', not 'than'.", "senior/junior/superior/inferior/prior + to."),
    ("Each of the boys have a book.", "Each of the boys has a book.", "'Each of' is singular, so the verb is singular.", "Each / every / either / neither + singular verb."),
    ("Neither the teacher nor the students was present.", "Neither the teacher nor the students were present.", "With 'neither...nor' / 'either...or', the verb agrees with the nearer subject.", "Neither A nor B -> verb follows B."),
    ("The scissors is on the table.", "The scissors are on the table.", "Paired-item nouns (scissors, trousers, spectacles) are plural.", "Scissors, trousers, spectacles, tongs -> plural verb."),
    ("I have been living here since five years.", "I have been living here for five years.", "'Since' is for a point of time, 'for' is for a period.", "Since 2019 / since Monday; for five years / for two hours."),
    ("He did not knew the answer.", "He did not know the answer.", "After do/does/did, use the base form (V1).", "did + V1, never did + V2."),
    ("She is more smarter than her sister.", "She is smarter than her sister.", "Never use a double comparative.", "more + adjective OR adjective-er, never both."),
    ("The news are true.", "The news is true.", "'News' is uncountable and singular.", "News, information, advice, furniture, luggage -> singular."),
    ("Hardly had I reached the station than the train left.", "Hardly had I reached the station when the train left.", "'Hardly/Scarcely' pair with 'when'.", "Hardly/Scarcely ... when; No sooner ... than."),
    ("No sooner did he arrive when it started raining.", "No sooner did he arrive than it started raining.", "'No sooner' always pairs with 'than'.", "No sooner ... than."),
    ("Unless you do not work hard, you will fail.", "Unless you work hard, you will fail.", "'Unless' already means 'if not', so do not add another 'not'.", "Unless = if not -> no extra negative."),
    ("He is one of the best player in the team.", "He is one of the best players in the team.", "'One of the + superlative' takes a plural noun.", "One of the best + plural noun."),
    ("I prefer tea than coffee.", "I prefer tea to coffee.", "'Prefer' takes 'to', not 'than'.", "prefer X to Y."),
    ("Though he is poor, but he is honest.", "Though he is poor, he is honest.", "'Though/Although' is never followed by 'but'.", "Though ... yet (optional), never though ... but."),
    ("Let he go.", "Let him go.", "After 'let', use the object pronoun.", "let me / him / her / them."),
    ("This is between you and I.", "This is between you and me.", "A preposition takes the object pronoun.", "Between you and me."),
    ("I am looking forward to meet you.", "I am looking forward to meeting you.", "In 'look forward to', 'to' is a preposition, so the verb takes -ing.", "look forward to / object to / used to (habit now) + V-ing."),
    ("He has returned back from Delhi.", "He has returned from Delhi.", "'Return' already means 'come back'; 'back' is redundant.", "Avoid redundancy: return back, repeat again, revert back."),
    ("The furniture are new.", "The furniture is new.", "'Furniture' is uncountable, so singular.", "Uncountables take singular verbs."),
    ("Mathematics are my favourite subject.", "Mathematics is my favourite subject.", "Subject names ending in -s (Mathematics, Physics, Economics) are singular.", "Subjects in -ics -> singular verb."),
    ("Each and every student were present.", "Each and every student was present.", "'Each and every' takes a singular verb.", "Each and every + singular."),
    ("If I was a bird, I would fly.", "If I were a bird, I would fly.", "Imaginary/unreal conditions use 'were' for all subjects.", "Unreal if / I wish -> were."),
    ("He avoided to meet me.", "He avoided meeting me.", "'Avoid' is followed by a gerund (-ing).", "avoid, enjoy, finish, mind, consider + V-ing."),
    ("The number of students are increasing.", "The number of students is increasing.", "'The number of' is singular; 'A number of' is plural.", "The number of -> is; A number of -> are."),
    ("The cattle is grazing in the field.", "The cattle are grazing in the field.", "'Cattle', 'police', 'people' are always plural.", "Cattle, police, people, poultry -> plural verb."),
    ("He was died last year.", "He died last year.", "'Die' is intransitive, so no passive 'was died'.", "died (event); was dead (state)."),
    ("I wish I am rich.", "I wish I were rich.", "'I wish' for a present unreal wish takes 'were'.", "I wish + were / V2 for present wishes."),
    ("Ten kilometres are a long distance.", "Ten kilometres is a long distance.", "An amount of distance, money or time taken as one unit is singular.", "Ten kilometres / Rs 500 / five hours (as one amount) -> is."),
    ("She is elder than me.", "She is older than me.", "'Elder' is not used with 'than'; use 'older than'.", "elder brother (before noun); older than (comparison)."),
]

ERROR_PROMPTS = [
    "Find the error in the sentence: \"{w}\"",
    "Spot the error: {w}",
    "Error detection (SSC CHSL): {w} Which part is wrong and why?",
    "Is this sentence correct? \"{w}\"",
    "Correct this sentence: {w}",
]

IDIOMS = [
    ("A piece of cake", "something very easy"),
    ("Once in a blue moon", "very rarely"),
    ("Burn the midnight oil", "to work or study late into the night"),
    ("Spill the beans", "to reveal a secret"),
    ("Hit the nail on the head", "to describe exactly what is right"),
    ("Bite the bullet", "to face something difficult bravely"),
    ("Cry over spilt milk", "to regret something that cannot be changed"),
    ("Beat around the bush", "to avoid coming to the main point"),
    ("Break the ice", "to start a conversation in an awkward situation"),
    ("At the eleventh hour", "at the last possible moment"),
    ("A blessing in disguise", "something that seems bad but turns out good"),
    ("Call it a day", "to stop working for the day"),
    ("Hold your horses", "wait, be patient"),
    ("Under the weather", "feeling slightly ill"),
    ("Cost an arm and a leg", "to be very expensive"),
]


def english_items(rng: random.Random):
    out = []
    for w, c, rule, rem in ENGLISH_ERRORS:
        for tmpl in ERROR_PROMPTS:
            out.append(Item("english.error_spotting", "English", tmpl.format(w=w), c,
                            "Check in this order: subject-verb agreement, tense, preposition, pronoun case, comparison, redundancy.",
                            [f"Error: {rule}", f"Correct: {c}"], rem))
    for idiom, meaning in IDIOMS:
        others = [m for _, m in IDIOMS if m != meaning]
        for tmpl in ["What is the meaning of the idiom '{i}'?", "Idiom meaning: {i}", "Choose the meaning of '{i}'."]:
            out.append(Item("english.idiom", "English", tmpl.format(i=idiom), meaning,
                            "Idioms are not literal. Picture the phrase, then pick the option that fits a real-life situation.",
                            [f"'{idiom}' = {meaning}."], f"{idiom} -> {meaning}.",
                            rng.sample(others, 3)))
    return out


# Strategy / coaching conversations (no exam-notice numbers - those change)
STRATEGY = [
    ("How can I increase my speed in the Quant section?",
     "Learn shortcuts by topic, then drill them under a timer.",
     "Speed comes from recall, not from calculating faster.",
     ["Memorise squares to 30, cubes to 15, tables to 20 and the %-fraction table.",
      "Learn one formula per topic: successive % (a + b + ab/100), LCM method for work, 2xy/(x+y) for average speed.",
      "Daily: 30 questions of one topic with a 20-second target each; redo every wrong one next day.",
      "Use options: check unit digit, divisibility or approximate value to eliminate choices."],
     "Recall beats calculation: memorise tables, then practise with a timer."),
    ("Which section should I attempt first in the exam?",
     "Start with your strongest section to bank marks and confidence; keep Quant for when your mind is fresh but do not get stuck.",
     "Two-round method: attempt every easy question first, mark the rest, then come back.",
     ["Round 1: answer only questions you can solve in under 30 seconds.",
      "Round 2: return to marked questions in order of confidence.",
      "Never spend more than about a minute on one question in round 1.",
      "Practise your order in mocks before exam day; do not change it on the day."],
     "Easy questions first, everywhere. Skipping is a skill."),
    ("How do I deal with negative marking?",
     "Attempt questions where you can eliminate at least two options; skip blind guesses.",
     "Elimination turns a guess into a good bet.",
     ["If you are sure: answer.", "If you can cut two options: a 50-50 guess is usually worth it.",
      "If you cannot cut any option: skip.", "Check the official notice for the exact negative mark per question."],
     "Guess only after eliminating; never guess blind."),
    ("How should I analyse a mock test?",
     "Spend as much time analysing as taking the mock.",
     "Sort every mistake into: concept gap, silly mistake, or time pressure.",
     ["Concept gap -> revise that topic and do 20 fresh questions.",
      "Silly mistake -> note the trap in an error notebook.",
      "Time pressure -> find the faster method for that question type.",
      "Re-solve all wrong and skipped questions without a timer."],
     "An unanalysed mock is a wasted mock."),
    ("Give me a daily study plan for CHSL.",
     "A balanced daily cycle covering all four sections plus one revision block.",
     "Short daily practice of every section beats long sessions on one.",
     ["Quant: 1 topic, learn the shortcut, 30 timed questions.",
      "Reasoning: 2 topics, 25 questions each with a timer.",
      "English: 20 error-spotting + 10 vocab/idioms + 1 reading passage.",
      "GK: 30-45 minutes of static GK and current affairs from a trusted monthly source.",
      "Night: 15-minute revision of formulas and your error notebook. Weekly: one full mock + analysis."],
     "Every section, every day; mock every week."),
    ("Which tables and values should I memorise for fast calculation?",
     "Squares 1-30, cubes 1-15, tables up to 20, the percent-fraction table and key speed conversions.",
     "Memorised values remove whole steps from calculations.",
     ["% -> fraction: 12.5 = 1/8, 16 2/3 = 1/6, 14 2/7 = 1/7, 11 1/9 = 1/9, 9 1/11 = 1/11, 6.25 = 1/16.",
      "km/h -> m/s: x 5/18 (36 = 10, 54 = 15, 72 = 20, 90 = 25).",
      "Pythagorean triples: 3-4-5, 5-12-13, 8-15-17, 7-24-25.",
      "Trig values for 0°, 30°, 45°, 60°, 90°."],
     "Know these cold and many questions become one-line problems."),
    ("I always run out of time. What should I do?",
     "Run out of time = spending too long on hard questions. Fix it with a per-question limit.",
     "Skip fast, return later.",
     ["Set a personal limit (for example 40 seconds) and move on when it passes.",
      "Do sectional tests with a strict timer.",
      "Track which question types eat your time; learn their shortcuts first.",
      "Do not re-check every answer during the first round."],
     "The clock, not difficulty, decides what you skip."),
    ("How do I solve reading comprehension faster?",
     "Read the questions first, then read the passage with those questions in mind.",
     "Questions tell you what to look for.",
     ["Skim the questions (not the options) first.", "Read the passage once, marking where each answer sits.",
      "For vocabulary questions, read the full sentence around the word.",
      "Prefer the option closest to the passage, not to your own opinion."],
     "Questions first, passage second."),
    ("What is the exam pattern and the date of SSC CHSL this year?",
     "I can't confirm current dates or pattern changes; check the latest notice on the official SSC website (ssc.gov.in).",
     "Exam pattern, dates, vacancies and cut-offs change. Use the official notification as the only source.",
     ["Open ssc.gov.in -> Notices / Latest News.", "Download the CHSL notification PDF for the current year.",
      "Note the scheme of examination, marking scheme and syllabus sections from it."],
     "For dates and patterns, trust only the official notice."),
    ("How do I remember static GK?",
     "Use spaced revision and memory hooks, not long reading sessions.",
     "Small chunks revised many times beat one long read.",
     ["Make one-line notes per fact.", "Revise the same notes after 1 day, 3 days, 7 days and 21 days.",
      "Use mnemonics and link facts to things you know.", "Solve previous-year GK questions to see what is asked."],
     "Revise in cycles: 1-3-7-21 days."),
]

STRATEGY_REWORDS = ["{q}", "{q}", "Coach, {q_lower}", "Quick tip: {q_lower}"]

# GK: stable constitutional facts with a hook, plus refusal for current affairs
GK_FACTS = [
    ("Which Part of the Indian Constitution deals with Fundamental Rights?", "Part III (Articles 12-35)",
     "Part III = Rights, Part IV = Directive Principles, Part IVA = Fundamental Duties.", "Rights 3, Directives 4, Duties 4A."),
    ("Which Article lists the Fundamental Duties?", "Article 51A (Part IVA)",
     "Duties come right after the Directive Principles (Articles 36-51), so they are 51A.", "DPSP ends at 51 -> duties are 51A."),
    ("Which Articles of the Constitution contain the Directive Principles of State Policy?", "Articles 36-51 (Part IV)",
     "Part III ends at 35, so Part IV starts at 36.", "Rights 12-35, Directives 36-51."),
    ("How many Fundamental Duties are there in the Indian Constitution?", "11",
     "10 were added by the 42nd Amendment (1976); the 11th (education of children 6-14) by the 86th Amendment (2002).", "42nd gave 10, 86th gave 1 -> 11."),
]

CURRENT_AFFAIRS_Q = [
    "Who won the most recent Nobel Peace Prize?",
    "What is the current repo rate set by RBI?",
    "Who is the current Chief Election Commissioner of India?",
    "Which country hosted the latest G20 summit?",
    "What is the latest GDP growth rate of India?",
]


def strategy_items(rng: random.Random):
    out = []
    for q, ans, trick, steps, rem in STRATEGY:
        for tmpl in STRATEGY_REWORDS:
            text = tmpl.format(q=q, q_lower=q[0].lower() + q[1:])
            out.append(Item("strategy", "Strategy", text, ans, trick, steps, rem))
    return out


def gk_items(rng: random.Random):
    out = []
    for q, ans, trick, rem in GK_FACTS:
        for tmpl in ["{q}", "GK: {q}", "{q} Give me a way to remember it."]:
            out.append(Item("gk.static", "GK", tmpl.format(q=q), ans, trick, [trick], rem))
    for q in CURRENT_AFFAIRS_Q:
        for tmpl in ["{q}", "Current affairs: {q}"]:
            out.append(Item("gk.current_refuse", "GK", tmpl.format(q=q),
                            "I can't give this reliably - it changes and my knowledge may be out of date.",
                            "For current affairs, use a recent monthly current-affairs compilation or official sources (PIB, RBI, government websites).",
                            ["Check the latest official source.", "Add it to your current-affairs notes with the date.",
                             "Revise those notes weekly."],
                            "Never trust an AI's memory for current affairs - verify."))
    return out


def all_seed_items(rng: random.Random):
    return english_items(rng) + strategy_items(rng) + gk_items(rng)
