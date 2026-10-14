# CHSL Coach: a speed-solving SSC CHSL tutor that runs on your phone

This folder trains a small model (Qwen2.5-1.5B-Instruct) to reply to CHSL questions like this:

```
Answer: (c) 33 1/3%
Trick: Price up x% -> cut consumption by x/(100 + x) x 100 to keep spending same.
Steps:
1. Reduction = x/(100 + x) x 100
2. = 50/150 x 100
3. = 33 1/3%
Remember: Up x% -> reduce x/(100+x); down x% -> increase x/(100-x).
```

The model is exported as a GGUF and runs offline in the GGUF Lab Android app (the `app/` folder of this project).

## What's inside

| File | What it does |
|---|---|
| `build_dataset.py` | Builds the training data: ~6000 Quant and Reasoning questions plus English, strategy and GK examples |
| `chsl_data/quant.py` | 37 Quant question types (percent, P&L, SI/CI, work, pipes, trains, boats, ratio, ages, number system, algebra, trig, geometry...) |
| `chsl_data/reasoning.py` | 8 Reasoning types (series, coding-decoding, alphabet, clock, mirror, calendar, direction, ranking) |
| `chsl_data/seeds.py` | Hand-written English error rules, idioms, exam strategy, and GK behaviour |
| `system_prompt.txt` | The tutor's instructions. The app uses the same file in `app/src/main/assets/` |
| `train_chsl_coach.ipynb` | Colab notebook: fine-tune, test, score, export GGUF |
| `data/` | The generated `train/val/eval.jsonl` and a template for your own questions |

**Every generated answer is computed in Python and checked a second way.** For example, the shortcut result is compared with direct multiplication. If the two disagree, the build stops. The model never trains on a wrong answer.

## Step 1: (optional) add your own previous-year questions

Copy `data/my_questions_template.jsonl` to `data/my_questions.jsonl`. Put one question per line:

```json
{"section": "Quant", "question": "...", "options": ["..", "..", "..", ".."], "answer": "<exactly one of the options>", "trick": "...", "steps": ["..", ".."], "remember": "..."}
```

These are the most valuable rows, because they are real exam questions. Each one is repeated 3 times in training. Even 100–300 real PYQs with good tricks will noticeably improve the model.

## Step 2: train on free Colab (about 40–70 min)

1. Zip this `chsl_tutor` folder as `chsl_tutor.zip`.
2. Open `train_chsl_coach.ipynb` in Google Colab. Set **Runtime → Change runtime type → T4 GPU**.
3. Run all cells. Upload the zip when asked.
   - If you added your own questions, use the `--extra` line in cell 2.
4. Cell 8 prints accuracy on 300 held-out questions it never saw during training.
5. The last cell saves `chsl-coach-*.gguf` (~1 GB) to Google Drive → `chsl_coach/`.

## Step 3: run it in the app

1. Put an up-to-date llama.cpp in the project root:
   ```
   cd GGUF-main
   git clone https://github.com/ggml-org/llama.cpp
   ```
   If you already have it there, update it with `cd llama.cpp && git pull`.
2. Open the project in Android Studio and run it on your phone.
3. Copy the `.gguf` from Drive to your phone (Downloads). In the app, tap **Load model** and pick it. The app copies it once and loads it automatically next time.
4. Ask questions. Use **Why does it work?** for a follow-up explanation.

## What changed in the app

- `native-lib.cpp` now really runs the model. It loads the GGUF, uses the model's own chat template, streams the reply word by word, and has a working **Stop** button. It also shows prompt time and tokens/sec after each answer.
- llama.cpp is always compiled in **Release** mode, even for debug builds, with ARM dotprod/fp16 enabled. A debug (-O0) build of llama.cpp is many times slower.
- Uses 4 threads on 8-core phones (the performance cores).
- If the app crashes on launch on a very old phone, change `GGML_CPU_ARM_ARCH` in `app/src/main/cpp/CMakeLists.txt` to `armv8-a`.

## Know the limits

- A 1.5B model learns the **method and format** very well. It can still slip on arithmetic for unfamiliar numbers. Treat its Answer line as a guide and check the Steps.
- It is trained to **refuse current affairs**, because its knowledge is old. Use a monthly current-affairs source.
- The generated questions are templates. Real PYQs (Step 1) are what make it generalise to the actual exam.
- For better accuracy on a PC, train the 3B model (change `BASE_MODEL` in the notebook).

## Re-running locally

```
python build_dataset.py --n 6000            # needs only Python 3, no packages
python build_dataset.py --n 12000 --extra data/my_questions.jsonl
```
