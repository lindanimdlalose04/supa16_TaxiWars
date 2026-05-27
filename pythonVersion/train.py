"""
train.py
========

Train the Q-learning agent via self-play on KZN Taxi Wars.

Run:
    python train.py                    # full training run (10,000 episodes)
    python train.py --episodes 1000    # short test run
    python train.py --quick            # very quick (500 ep) for smoke testing

What this script does
---------------------
1.  Initialises one QLearningAgent (one Q-table, shared between P1 and P2).
2.  For each training episode:
        - Resets the engine.
        - Plays the game move-by-move; the same agent decides for whichever
          player's turn it is. The state encoder presents the state from
          the current player's perspective so the shared Q-table works.
        - After every move, performs a Bellman update from the MOVER's
          perspective (Approach A — standard for tabular self-play).
        - Decays epsilon at episode end.

3.  Every EVAL_EVERY episodes, freezes the agent (ε=0) and plays:
        - 100 games vs RandomAgent (50 starting as P1, 50 starting as P2)
        - 100 games vs GreedyAgent  (50 starting as P1, 50 starting as P2)
      and logs win rate / avg episode length.

4.  Saves the trained Q-table to disk + a metrics log for plotting.

Design notes
------------
* Headless: forces SDL dummy driver so no window opens.
* No external ML libraries — just stdlib + the project files.
* All randomness can be seeded for reproducibility.
"""

import os
import sys
import time
import argparse
import json
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, "/home/claude")

from game_1 import GameEngine
from state_encoder import encode, compute_reward
from agent import QLearningAgent, RandomAgent, GreedyAgent


# ─────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────

MAX_MOVES_PER_EPISODE = 300   # episode cap (your original spec)
EVAL_GAMES_PER_OPPONENT = 100  # 50 as P1, 50 as P2
LOG_EVERY = 500                # also evaluate at these milestones


# ─────────────────────────────────────────────────────────────────────────
# Core training step: play one self-play episode
# ─────────────────────────────────────────────────────────────────────────

def play_training_episode(agent, engine, max_moves=MAX_MOVES_PER_EPISODE):
    """
    Play one episode of self-play, updating the agent after every move.

    Returns
    -------
    dict with episode statistics:
        - moves            : number of moves played
        - winner           : 1, 2, or 0 (timeout / no winner)
        - p1_score, p2_score
        - p1_total_reward, p2_total_reward  (cumulative shaped reward)
    """
    engine.reset()

    p1_total_reward = 0.0
    p2_total_reward = 0.0

    while not engine.game_over and engine.move_count < max_moves:
        cp = engine.current_player

        # Capture the state BEFORE the move from the mover's perspective.
        # This is the (s, a) that the update will use.
        prev_raw = engine.get_state()
        state_key = encode(prev_raw, perspective=cp)
        valid = engine.valid_moves

        if not valid:
            # Engine handles stalemate inside do_move() (any node id triggers it).
            engine.do_move(0)
            continue

        action = agent.choose_action(state_key, valid)
        result = engine.do_move(action)

        # After the move, get the new state. Note: current_player has now
        # switched (unless POLICE handling kept it the same). For the update
        # we want the next state FROM THE MOVER'S PERSPECTIVE, and the valid
        # actions there are the actions the mover would face on their NEXT
        # turn. In a two-player game this is somewhat fuzzy — the standard
        # tabular self-play approach is to just use the immediate next state.
        new_raw = engine.get_state()
        next_state_key = encode(new_raw, perspective=cp)

        # Compute the valid actions for the mover from the new state.
        # If the mover isn't the current player anymore (the usual case), we
        # need to recompute. We don't want to call engine.valid_moves because
        # that's for the player whose turn it currently is.
        if new_raw["current_player"] == cp:
            # Still mover's turn (e.g. opponent was police-blocked) — use engine's
            next_valid = engine.valid_moves
        else:
            # Compute mover's hypothetical valid moves from their position
            from game_1 import ROUTES_DATA, get_connected
            mover_pos = new_raw["p1_pos"] if cp == 1 else new_raw["p2_pos"]
            opp_pos   = new_raw["p2_pos"] if cp == 1 else new_raw["p1_pos"]
            next_valid = [
                c["to"] for c in get_connected(ROUTES_DATA, mover_pos)
                if c["to"] != opp_pos
            ]

        reward = compute_reward(result, perspective=cp,
                                prev_state=prev_raw, new_state=new_raw)

        done = engine.game_over
        agent.update(state_key, action, reward, next_state_key,
                     next_valid, done)

        if cp == 1:
            p1_total_reward += reward
        else:
            p2_total_reward += reward

    # End of episode
    agent.decay_epsilon()

    return {
        "moves": engine.move_count,
        "winner": engine.winner,
        "p1_score": engine.p1_score,
        "p2_score": engine.p2_score,
        "p1_total_reward": p1_total_reward,
        "p2_total_reward": p2_total_reward,
        "finished": engine.game_over,
    }


# ─────────────────────────────────────────────────────────────────────────
# Evaluation: agent vs a non-learning opponent
# ─────────────────────────────────────────────────────────────────────────

def evaluate_against(agent, opponent, n_games, opponent_uses_raw_state=False, seed=0):
    """
    Evaluate `agent` (Q-learning) against `opponent` (Random or Greedy).
    Plays n_games games total, half with agent as P1 and half as P2.

    `opponent_uses_raw_state`: if True, the opponent is passed the raw state
    dict instead of the encoded tuple. GreedyAgent needs this; RandomAgent
    doesn't care.

    Returns a dict with win counts and average length.
    """
    half = n_games // 2
    games = [(1, i) for i in range(half)] + [(2, i + half) for i in range(half)]

    wins = losses = draws = 0
    total_moves = 0
    total_reward = 0.0

    # Save agent's epsilon and force greedy evaluation
    saved_eps = agent.epsilon
    agent.epsilon = 0.0  # pure exploitation during evaluation

    try:
        for agent_role, game_seed in games:
            random.seed(seed * 10000 + game_seed)
            engine = GameEngine()
            engine.reset()

            ep_reward = 0.0

            while not engine.game_over and engine.move_count < MAX_MOVES_PER_EPISODE:
                cp = engine.current_player
                raw = engine.get_state()
                valid = engine.valid_moves

                if not valid:
                    engine.do_move(0)
                    continue

                if cp == agent_role:
                    # Agent's turn — use Q-table
                    state_key = encode(raw, perspective=cp)
                    action = agent.choose_action(state_key, valid, greedy=True)
                else:
                    # Opponent's turn
                    if opponent_uses_raw_state:
                        action = opponent.choose_action(raw, valid)
                    else:
                        action = opponent.choose_action(None, valid)

                prev_raw = raw
                result = engine.do_move(action)
                new_raw = engine.get_state()

                # Track agent's reward (for logging only — no updates during eval)
                if cp == agent_role:
                    ep_reward += compute_reward(result, perspective=agent_role,
                                                prev_state=prev_raw,
                                                new_state=new_raw)

            total_moves += engine.move_count
            total_reward += ep_reward

            if engine.winner == agent_role:
                wins += 1
            elif engine.winner != 0:
                losses += 1
            else:
                draws += 1
    finally:
        agent.epsilon = saved_eps  # restore exploration

    return {
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "n": n_games,
        "win_rate": wins / n_games,
        "decisive_win_rate": wins / max(1, wins + losses),
        "avg_moves": total_moves / n_games,
        "avg_reward": total_reward / n_games,
    }


# ─────────────────────────────────────────────────────────────────────────
# Main training loop
# ─────────────────────────────────────────────────────────────────────────

def train(episodes, log_every, out_dir, seed=0, verbose=True):
    os.makedirs(out_dir, exist_ok=True)

    agent  = QLearningAgent(seed=seed)
    engine = GameEngine()

    metrics = {
        "episode":        [],
        "epsilon":        [],
        "q_table_size":   [],
        "states_seen":    [],
        "train_winner_p1": [],  # rolling P1 win count since last log
        "train_winner_p2": [],
        "train_finished":  [],  # rolling finished count
        "vs_random_wr":    [],
        "vs_random_dwr":   [],  # decisive (excluding draws/timeouts)
        "vs_greedy_wr":    [],
        "vs_greedy_dwr":   [],
        "avg_train_reward": [],
    }

    if verbose:
        print(f"Training {episodes:,} episodes, evaluating every {log_every:,}")
        print(f"Output dir: {out_dir}")
        print("=" * 76)
        print(f"{'episode':>8}  {'eps':>5}  {'Q-size':>7}  {'states':>7}  "
              f"{'finished':>8}  {'vs Rand':>8}  {'vs Greedy':>9}  {'time':>6}")
        print("-" * 76)

    rolling_p1 = rolling_p2 = rolling_finished = 0
    rolling_reward_sum = 0.0
    rolling_count = 0
    t_start = time.time()

    for ep in range(1, episodes + 1):
        result = play_training_episode(agent, engine)
        rolling_count += 1
        if result["winner"] == 1: rolling_p1 += 1
        elif result["winner"] == 2: rolling_p2 += 1
        if result["finished"]: rolling_finished += 1
        # Average across both perspectives (since the agent is both sides)
        rolling_reward_sum += (result["p1_total_reward"] + result["p2_total_reward"]) / 2.0

        if ep % log_every == 0 or ep == episodes:
            random_seed_for_eval = ep
            eval_rand = evaluate_against(
                agent, RandomAgent(seed=random_seed_for_eval),
                EVAL_GAMES_PER_OPPONENT,
                opponent_uses_raw_state=False, seed=random_seed_for_eval,
            )
            eval_greedy = evaluate_against(
                agent, GreedyAgent(seed=random_seed_for_eval),
                EVAL_GAMES_PER_OPPONENT,
                opponent_uses_raw_state=True, seed=random_seed_for_eval,
            )

            elapsed = time.time() - t_start

            metrics["episode"].append(ep)
            metrics["epsilon"].append(agent.epsilon)
            metrics["q_table_size"].append(agent.q_table_size())
            metrics["states_seen"].append(agent.num_states_seen())
            metrics["train_winner_p1"].append(rolling_p1)
            metrics["train_winner_p2"].append(rolling_p2)
            metrics["train_finished"].append(rolling_finished)
            metrics["vs_random_wr"].append(eval_rand["win_rate"])
            metrics["vs_random_dwr"].append(eval_rand["decisive_win_rate"])
            metrics["vs_greedy_wr"].append(eval_greedy["win_rate"])
            metrics["vs_greedy_dwr"].append(eval_greedy["decisive_win_rate"])
            metrics["avg_train_reward"].append(rolling_reward_sum / rolling_count)

            if verbose:
                print(f"{ep:>8,}  {agent.epsilon:>5.3f}  "
                      f"{agent.q_table_size():>7,}  "
                      f"{agent.num_states_seen():>7,}  "
                      f"{rolling_finished:>4}/{rolling_count:<3}  "
                      f"{eval_rand['win_rate']*100:>6.1f}%  "
                      f"{eval_greedy['win_rate']*100:>7.1f}%  "
                      f"{elapsed:>5.1f}s")

            rolling_p1 = rolling_p2 = rolling_finished = 0
            rolling_reward_sum = 0.0
            rolling_count = 0

    elapsed = time.time() - t_start
    if verbose:
        print("-" * 76)
        print(f"Done in {elapsed:.1f}s ({elapsed / max(1, episodes) * 1000:.1f} ms/episode)")
        print(f"Final Q-table: {agent.q_table_size():,} entries, "
              f"{agent.num_states_seen():,} distinct states")

    # Persist agent and metrics
    agent_path  = os.path.join(out_dir, "agent.pkl")
    metrics_path = os.path.join(out_dir, "metrics.json")
    agent.save(agent_path)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    if verbose:
        print(f"Saved agent  → {agent_path}")
        print(f"Saved metrics → {metrics_path}")

    return agent, metrics


# ─────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=100_000)
    parser.add_argument("--log-every", type=int, default=LOG_EVERY)
    parser.add_argument("--out-dir", default="/home/claude/runs/run1")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--quick", action="store_true",
                        help="500-episode smoke test (overrides --episodes)")
    args = parser.parse_args()

    if args.quick:
        args.episodes = 500
        args.log_every = 100

    train(args.episodes, args.log_every, args.out_dir, seed=args.seed)


if __name__ == "__main__":
    main()
