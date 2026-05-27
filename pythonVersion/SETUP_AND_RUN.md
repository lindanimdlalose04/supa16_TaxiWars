# KZN Taxi Wars — Setup & Run Guide

This is a step-by-step guide to running everything on your own machine. Follow it in order.

---

## What you'll have when you're done

1. The game playable on your computer (Human vs Human)
2. A trained AI agent that has played itself 100,000 times
3. Four plots showing the agent's learning curve
4. The ability to play **against** the trained AI

---

## Step 0 — Prerequisites

You need **Python 3.10 or newer**.

Open a terminal (PowerShell on Windows, Terminal on Mac, your usual terminal on Linux) and type:

```
python --version
```

If `python --version` doesn't work but `python3 --version` does, use `python3` everywhere this guide says `python`.

---

## Step 1 — Put all the project files in one folder

Create a new folder anywhere on your computer — let's call it `kzn-taxi-wars`. Inside it, place these files (download from the chat outputs):

```
supa16-taxi-wars/
├── game_1.py
├── state_encoder.py
├── agent.py
├── train.py
└── plot_metrics.py
```

**Do not download `agent.pkl` or `metrics.json` yet** , those are *outputs* from running training, and you want to generate them yourself so you actually see the training happen.

---

## Step 2 — Install the two libraries

Open your terminal and **navigate into that folder**:

```
cd path/to/supa16-taxi-wars
```

On Windows that might look like `cd C:\Users\You\Documents\kzn-taxi-wars`. On Mac/Linux something like `cd ~/Documents/kzn-taxi-wars`.

Then install the two libraries the project needs:

```
pip install pygame matplotlib
```

If that command fails with "pip not found", try:

```
python -m pip install pygame matplotlib
```

You should see a bunch of "Downloading..." and "Installing..." messages, then a "Successfully installed" line.

---

## Step 3 — Play the game yourself (sanity check)

Before involving any AI, make sure the game itself runs:

```
python game_1.py
```

A window titled "KZN Route: Taxi Wars" should open with a main menu. Use the arrow keys (or mouse) to navigate, hit Enter on "Solo Play (Human vs Human)", and play a few turns.

**To make a move**: type a number (1–30) and press Enter. The number is the node ID you want to move to. Only directly-connected nodes are valid.

If the window opens and the game works, you're set. **Press Escape to return to the menu, then close the window.**

### If this doesn't work

- **"No module named pygame"** — Step 2 didn't work. Re-run `pip install pygame`.
- **Window appears for a split second and closes** — there's a crash. Run from a terminal so you can see the error message. Copy/paste it back to me.
- **Game window is too big / off-screen** — your monitor is small. Open `game_1.py`, find the line `WIN_W, WIN_H = 1400, 900` (near the top), and try smaller numbers like `1000, 700`.

---

## Step 4 — Train the AI agent

This is the heart of the project. Run:

```
python train.py --episodes 10000 --log-every 500
```

You'll see something like this start scrolling:

```
Training 100,000 episodes, evaluating every 500
Output dir: runs/run1
============================================================
 episode    eps   Q-size  states  finished  vs Rand  vs Greedy   time
------------------------------------------------------------
     500  0.905  20,241  11,841   62/100    79.0%      64.0%    2.4s
   1,000  0.819  27,654  14,953   71/100    80.0%     100.0%    4.6s
   1,500  0.741  31,802  16,710   81/100    86.0%     100.0%    7.1s
   ...
```

**What to watch:** the `vs Rand` and `vs Greedy` columns. These are the win rates against the baseline opponents. They should climb over time — that's the agent learning.

**How long it takes:** about 45–90 seconds on most laptops. If it's much slower (like 5+ minutes), something else is hogging your CPU.

When it finishes, you'll see:

```
Done in 46.2s (4.6 ms/episode)
Final Q-table: 40,977 entries, 19,823 distinct states
Saved agent  → runs/run1/agent.pkl
Saved metrics → runs/run1/metrics.json
```

There's now a `runs/run1/` subfolder inside your project folder containing the trained agent.

---

## Step 5 — Generate the learning curves

```
python plot_metrics.py
```

This reads `runs/run1/metrics.json` and produces four PNG files in `runs/run1/`:

- `learning_curves.png` — win rates over training
- `q_growth.png` — Q-table size over training
- `reward_curve.png` — average shaped reward over training
- `combined.png` — all four panels in one figure (use this for your report)

Open `runs/run1/combined.png` in your file browser to see the result.

---

## Step 6 — Play against the trained AI

Now the fun part. Run the game again:

```
python game_1.py
```

In the menu you should now see two new options:

- **Play vs AI (you = P1)** — you start at Jozini, AI starts at Kokstad
- **Play vs AI (you = P2)** — AI starts at Jozini, you start at Kokstad

Pick one and play. Notice:

- When it's the AI's turn, there's about a 1-second pause before it moves
- The countdown timer pauses during the AI's turn (you only have a deadline on *your* turn)
- Your number-input is ignored when it's the AI's turn (so you can't accidentally type for the AI)

**Heads up:** the agent has trained against random and greedy opponents for ~9 minutes of game-time. It's *good*. You will probably lose your first few games. That's actually the point — if it beat random play 98% of the time and you only beat random play, statistically the AI should win.

### If "AI not available" appears

The game can't find `runs/run1/agent.pkl`. Make sure you ran Step 4 successfully and that you're running `python game_1.py` from the *same folder* that contains the `runs/` subfolder.

---

## Common commands cheat-sheet

From inside the `kzn-taxi-wars` folder:

| What you want to do | Command |
|---|---|
| Play the game (any mode) | `python game_1.py` |
| Train the agent (10k episodes, ~1 min) | `python train.py --episodes 10000 --log-every 500` |
| Quick training smoke test (~5s) | `python train.py --quick` |
| Train with more episodes (for a stronger AI) | `python train.py --episodes 50000` |
| Re-generate plots from the latest training | `python plot_metrics.py` |
| Run the engine self-test | `python state_encoder.py` |
| Run the agent self-test | `python agent.py` |

---

## Folder layout after everything is done

```
kzn-taxi-wars/
├── game_1.py            ← game + UI + new PvAI mode
├── state_encoder.py     ← turns game state into agent input
├── agent.py             ← QLearningAgent class
├── train.py             ← runs the training loop
├── plot_metrics.py      ← generates the learning curve figures
└── runs/
    └── run1/
        ├── agent.pkl          ← your trained agent (loaded by game_1.py)
        ├── metrics.json       ← raw training stats
        ├── combined.png       ← four-panel learning curve
        ├── learning_curves.png
        ├── q_growth.png
        └── reward_curve.png
```

---

## In-game controls reference

| Key | What it does |
|---|---|
| `1`–`9`, `0` | Type a node number to move to |
| `Enter` | Confirm the typed number |
| `Backspace` | Delete the last typed digit |
| `R` | Restart the current game |
| `Esc` | Return to main menu |

---

## If something goes wrong

Try these in order:

1. **Read the error message carefully.** Python errors look scary but the last line usually tells you what's actually wrong.
2. **Make sure you're in the right folder.** `cd path/to/kzn-taxi-wars` before running anything.
3. **Make sure libraries installed.** `python -c "import pygame, matplotlib; print('ok')"` should print `ok`.
4. **Restart your terminal.** Sometimes path changes need a fresh shell.

If you're stuck, copy the **exact** error text into a message and I'll help.
