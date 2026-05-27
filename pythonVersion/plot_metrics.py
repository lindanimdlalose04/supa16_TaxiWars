"""
plot_metrics.py — produce learning curves from a training run.

Reads metrics.json from a run directory and produces:
  - learning_curves.png : win-rate vs episode against both baselines
  - q_growth.png        : Q-table size and distinct states over time
  - reward_curve.png    : average training reward (rolling)
  - combined.png        : 2x2 grid of all four for the report

Run:
    python plot_metrics.py [run_dir]
"""

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")          # headless backend
import matplotlib.pyplot as plt


def main(run_dir):
    metrics_path = os.path.join(run_dir, "metrics.json")
    with open(metrics_path) as f:
        m = json.load(f)

    eps      = m["episode"]
    eps_curr = m["epsilon"]
    qsize    = m["q_table_size"]
    states   = m["states_seen"]
    finished = [f / 500 * 100 for f in m["train_finished"]]
    vs_rand_wr  = [w * 100 for w in m["vs_random_wr"]]
    vs_rand_dwr = [w * 100 for w in m["vs_random_dwr"]]
    vs_grd_wr   = [w * 100 for w in m["vs_greedy_wr"]]
    vs_grd_dwr  = [w * 100 for w in m["vs_greedy_dwr"]]
    avg_reward  = m["avg_train_reward"]

    # ── 1. learning curves ────────────────────────────────────────────────
    plt.figure(figsize=(9, 5.5))
    plt.plot(eps, vs_rand_wr, marker="o", lw=2, label="vs Random (win %)",
             color="#1f77b4")
    plt.plot(eps, vs_grd_wr,  marker="s", lw=2, label="vs Greedy (win %)",
             color="#d62728")
    plt.axhline(70, color="gray", linestyle="--", lw=0.8,
                label="Target vs Random (70%)")
    plt.axhline(50, color="lightgray", linestyle=":", lw=0.8)
    plt.xlabel("Training episode")
    plt.ylabel("Evaluation win rate (%)")
    plt.title("Q-learning agent — win rate vs baselines over training")
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)
    plt.ylim(0, 105)
    plt.tight_layout()
    plt.savefig(os.path.join(run_dir, "learning_curves.png"), dpi=150)
    plt.close()

    # ── 2. Q-table growth ─────────────────────────────────────────────────
    plt.figure(figsize=(9, 5.5))
    plt.plot(eps, qsize,  marker="o", lw=2, label="Q-table entries (state, action)",
             color="#2ca02c")
    plt.plot(eps, states, marker="s", lw=2, label="Distinct states seen",
             color="#9467bd")
    plt.xlabel("Training episode")
    plt.ylabel("Count")
    plt.title("Q-table growth — saturation indicates exhaustive exploration")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(run_dir, "q_growth.png"), dpi=150)
    plt.close()

    # ── 3. reward + epsilon ───────────────────────────────────────────────
    fig, ax1 = plt.subplots(figsize=(9, 5.5))
    color1 = "#ff7f0e"
    ax1.plot(eps, avg_reward, marker="o", lw=2, color=color1,
             label="Avg shaped reward (rolling)")
    ax1.set_xlabel("Training episode")
    ax1.set_ylabel("Average shaped reward per episode", color=color1)
    ax1.tick_params(axis="y", labelcolor=color1)
    ax1.grid(alpha=0.3)

    ax2 = ax1.twinx()
    color2 = "#1f77b4"
    ax2.plot(eps, eps_curr, marker="s", lw=2, color=color2, label="ε (exploration)")
    ax2.set_ylabel("ε (exploration rate)", color=color2)
    ax2.tick_params(axis="y", labelcolor=color2)
    ax2.set_ylim(0, 1.05)

    plt.title("Reward and exploration over training")
    fig.tight_layout()
    plt.savefig(os.path.join(run_dir, "reward_curve.png"), dpi=150)
    plt.close()

    # ── 4. combined 2x2 figure for the report ─────────────────────────────
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))

    # (a) Learning curves
    ax = axes[0, 0]
    ax.plot(eps, vs_rand_wr, marker="o", lw=2, label="vs Random", color="#1f77b4")
    ax.plot(eps, vs_grd_wr,  marker="s", lw=2, label="vs Greedy", color="#d62728")
    ax.axhline(70, color="gray", linestyle="--", lw=0.8)
    ax.axhline(50, color="lightgray", linestyle=":", lw=0.8)
    ax.set_xlabel("Episode"); ax.set_ylabel("Win rate (%)")
    ax.set_title("(a) Win rate vs baselines")
    ax.legend(loc="lower right"); ax.grid(alpha=0.3); ax.set_ylim(0, 105)

    # (b) Q-growth
    ax = axes[0, 1]
    ax.plot(eps, qsize,  marker="o", lw=2, color="#2ca02c", label="Q-entries")
    ax.plot(eps, states, marker="s", lw=2, color="#9467bd", label="Distinct states")
    ax.set_xlabel("Episode"); ax.set_ylabel("Count")
    ax.set_title("(b) Q-table growth")
    ax.legend(); ax.grid(alpha=0.3)

    # (c) Reward
    ax = axes[1, 0]
    ax.plot(eps, avg_reward, marker="o", lw=2, color="#ff7f0e")
    ax.set_xlabel("Episode"); ax.set_ylabel("Avg shaped reward")
    ax.set_title("(c) Average shaped reward per episode")
    ax.grid(alpha=0.3)

    # (d) Epsilon + finish rate
    ax = axes[1, 1]
    ax.plot(eps, eps_curr,    marker="o", lw=2, color="#1f77b4", label="ε")
    ax.plot(eps, [f / 100 for f in finished], marker="s", lw=2,
            color="#8c564b", label="Train finish rate")
    ax.set_xlabel("Episode")
    ax.set_ylabel("Fraction"); ax.set_ylim(0, 1.05)
    ax.set_title("(d) Exploration ε and training-game finish rate")
    ax.legend(); ax.grid(alpha=0.3)

    plt.suptitle("KZN Taxi Wars — Q-learning training metrics "
                 f"(10 000 episodes, eval every 500)",
                 fontsize=13, y=1.00)
    plt.tight_layout()
    plt.savefig(os.path.join(run_dir, "combined.png"), dpi=150)
    plt.close()

    print(f"Plots saved to {run_dir}/")
    for fname in ("learning_curves.png", "q_growth.png", "reward_curve.png",
                  "combined.png"):
        path = os.path.join(run_dir, fname)
        size = os.path.getsize(path) / 1024
        print(f"  {fname:25s}  {size:6.1f} KB")


if __name__ == "__main__":
    run_dir = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/runs/run1"
    main(run_dir)
