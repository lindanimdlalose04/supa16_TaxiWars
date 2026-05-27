"""
agent.py
========

Three agent classes for the KZN Taxi Wars game:

  * QLearningAgent — tabular Q-learning with epsilon-greedy exploration
                     and optimistic initialisation
  * RandomAgent    — picks uniformly from valid moves (weakest baseline)
  * GreedyAgent    — always moves to the neighbour with the most customers
                     (a heuristic baseline — much stronger than random)

The Q-agent does NOT contain a training loop. Training happens in train.py
(checkpoint 3). Here we just provide:

    agent.choose_action(state_key, valid_actions) -> action
    agent.update(s, a, r, s_next, valid_next, done)

so that any external training loop can drive learning.

This separation lets us:
    - unit test each agent in isolation
    - swap agents freely (e.g. Q-agent vs Random for evaluation)
    - reuse the same agent class for training and for live play
"""

import random
import pickle
from collections import defaultdict

from game_1 import ROUTES_DATA, get_connected


# ─────────────────────────────────────────────────────────────────────────
# Hyperparameters (defaults — can be overridden when constructing the agent)
# ─────────────────────────────────────────────────────────────────────────

ALPHA_DEFAULT     = 0.15    # learning rate
GAMMA_DEFAULT     = 0.95    # discount factor
EPS_START_DEFAULT = 1.00    # initial exploration probability
EPS_END_DEFAULT   = 0.05    # minimum exploration probability
EPS_DECAY_DEFAULT = 0.9998  # multiplicative decay per episode
Q_INIT_DEFAULT    = 1.0     # optimistic initial Q-value


# ─────────────────────────────────────────────────────────────────────────
# QLearningAgent
# ─────────────────────────────────────────────────────────────────────────

class QLearningAgent:
    """
    Tabular Q-learning with ε-greedy action selection and optimistic
    initialisation.

    The Q-table is a dict mapping (state_key, action) -> Q-value.
    Unseen (state, action) pairs return `q_init` when queried.

    State keys come from state_encoder.encode() and are tuples of 13 ints.
    Actions are integer node IDs (the destination of the move).
    """

    def __init__(
        self,
        alpha=ALPHA_DEFAULT,
        gamma=GAMMA_DEFAULT,
        eps_start=EPS_START_DEFAULT,
        eps_end=EPS_END_DEFAULT,
        eps_decay=EPS_DECAY_DEFAULT,
        q_init=Q_INIT_DEFAULT,
        seed=None,
    ):
        self.alpha = alpha
        self.gamma = gamma
        self.eps_start = eps_start
        self.eps_end = eps_end
        self.eps_decay = eps_decay
        self.q_init = q_init

        # Current exploration rate (decays during training)
        self.epsilon = eps_start

        # The Q-table itself.
        # Using a plain dict (not defaultdict) so that pickle/unpickle works
        # cleanly and so that .get() with a default gives us optimistic init
        # without polluting the table.
        self.Q = {}

        # Optional RNG for reproducibility
        self._rng = random.Random(seed) if seed is not None else random

        # Lightweight stats
        self.updates = 0
        self.episodes_trained = 0

    # ───── Q-value access ─────────────────────────────────────────────

    def q(self, state, action):
        """Get Q(s, a) — returns the optimistic default if unseen."""
        return self.Q.get((state, action), self.q_init)

    def _max_q_over(self, state, valid_actions):
        """Return max_a Q(state, a) over the given valid actions.
        If valid_actions is empty (terminal / stalemate), returns 0.0 so the
        Bellman target is just `r`."""
        if not valid_actions:
            return 0.0
        return max(self.q(state, a) for a in valid_actions)

    # ───── Action selection ───────────────────────────────────────────

    def choose_action(self, state, valid_actions, greedy=False):
        """
        Pick an action using ε-greedy over `valid_actions`.

        Parameters
        ----------
        state : tuple
            The state key from state_encoder.encode().
        valid_actions : list of int
            Currently-legal destination node IDs.
        greedy : bool
            If True, ignore epsilon and always pick the best action.
            (Used at evaluation time.)

        Returns
        -------
        int — the chosen action (destination node ID), or None if no valid moves.
        """
        if not valid_actions:
            return None

        # Exploration
        if not greedy and self._rng.random() < self.epsilon:
            return self._rng.choice(valid_actions)

        # Exploitation — pick the action with the highest Q-value.
        # Ties are broken randomly so the agent doesn't get stuck always
        # picking the lowest-numbered tied action.
        best_q = float("-inf")
        best_actions = []
        for a in valid_actions:
            qv = self.q(state, a)
            if qv > best_q:
                best_q = qv
                best_actions = [a]
            elif qv == best_q:
                best_actions.append(a)
        return self._rng.choice(best_actions)

    # ───── Learning ───────────────────────────────────────────────────

    def update(self, state, action, reward, next_state, next_valid_actions, done):
        """
        Apply the standard Q-learning Bellman update:

            target = r + (0 if done else γ · max_a' Q(s', a'))
            δ      = target − Q(s, a)
            Q(s, a) ← Q(s, a) + α · δ
        """
        current_q = self.q(state, action)

        if done:
            target = reward
        else:
            target = reward + self.gamma * self._max_q_over(
                next_state, next_valid_actions
            )

        new_q = current_q + self.alpha * (target - current_q)
        self.Q[(state, action)] = new_q
        self.updates += 1

    # ───── Epsilon decay ──────────────────────────────────────────────

    def decay_epsilon(self):
        """Call this once per episode to decay the exploration rate."""
        self.epsilon = max(self.eps_end, self.epsilon * self.eps_decay)
        self.episodes_trained += 1

    # ───── Persistence ────────────────────────────────────────────────

    def save(self, path):
        """Persist the Q-table and hyperparameters to disk."""
        with open(path, "wb") as f:
            pickle.dump({
                "Q": self.Q,
                "alpha": self.alpha,
                "gamma": self.gamma,
                "epsilon": self.epsilon,
                "eps_end": self.eps_end,
                "eps_decay": self.eps_decay,
                "q_init": self.q_init,
                "updates": self.updates,
                "episodes_trained": self.episodes_trained,
            }, f)

    @classmethod
    def load(cls, path):
        """Restore a saved agent from disk."""
        with open(path, "rb") as f:
            data = pickle.load(f)
        agent = cls(
            alpha=data["alpha"],
            gamma=data["gamma"],
            eps_start=data["epsilon"],   # resume at last epsilon
            eps_end=data["eps_end"],
            eps_decay=data["eps_decay"],
            q_init=data["q_init"],
        )
        agent.Q = data["Q"]
        agent.updates = data.get("updates", 0)
        agent.episodes_trained = data.get("episodes_trained", 0)
        return agent

    # ───── Diagnostics ────────────────────────────────────────────────

    def q_table_size(self):
        """Number of stored (state, action) entries."""
        return len(self.Q)

    def num_states_seen(self):
        """Number of distinct states stored."""
        return len({s for (s, _) in self.Q.keys()})


# ─────────────────────────────────────────────────────────────────────────
# RandomAgent — weakest baseline
# ─────────────────────────────────────────────────────────────────────────

class RandomAgent:
    """Picks a valid move uniformly at random. No learning."""

    def __init__(self, seed=None):
        self._rng = random.Random(seed) if seed is not None else random

    def choose_action(self, state, valid_actions, greedy=False):
        if not valid_actions:
            return None
        return self._rng.choice(valid_actions)

    def update(self, *args, **kwargs):
        pass  # no-op — doesn't learn

    def decay_epsilon(self):
        pass


# ─────────────────────────────────────────────────────────────────────────
# GreedyAgent — heuristic baseline
# ─────────────────────────────────────────────────────────────────────────

class GreedyAgent:
    """
    Always moves to the neighbour with the most customers.
    Ties are broken by preferring neighbours without active obstacles,
    then randomly.

    This needs the live game state (not the encoded features) because it
    queries customer counts directly. So `state` passed to choose_action
    must be the raw state dict, NOT the encoded tuple.

    Important: this is a different signature from QLearningAgent, so we
    keep them separate. The training/eval loop will pass the right kind
    of state to each.
    """

    def __init__(self, seed=None):
        self._rng = random.Random(seed) if seed is not None else random

    def choose_action(self, raw_state, valid_actions, greedy=False):
        if not valid_actions:
            return None

        customers = raw_state["customers"]

        # Score each candidate: (customers there, no-obstacle bonus)
        best_score = (-1, -1)   # (customers, no_obstacle)
        best_actions = []

        # Determine which node "we" are at — i.e. whose turn it is in raw_state
        cp = raw_state["current_player"]
        my_pos = raw_state["p1_pos"] if cp == 1 else raw_state["p2_pos"]

        # Look up obstacle info from the routes
        connections = {c["to"]: c for c in get_connected(ROUTES_DATA, my_pos)}

        for a in valid_actions:
            cust = customers.get(a, 0)
            conn = connections.get(a)
            has_obstacle = (
                conn is not None
                and conn["obs"] is not None
                and not conn["route"]["cleared"]
            )
            score = (cust, 0 if has_obstacle else 1)
            if score > best_score:
                best_score = score
                best_actions = [a]
            elif score == best_score:
                best_actions.append(a)

        return self._rng.choice(best_actions)

    def update(self, *args, **kwargs):
        pass

    def decay_epsilon(self):
        pass


# ─────────────────────────────────────────────────────────────────────────
# Self-test
# ─────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    from game_1 import GameEngine
    from state_encoder import encode

    print("agent.py self-test")
    print("=" * 60)

    # ── Test 1: QLearningAgent basic mechanics ──────────────────────────
    print("\nTest 1: QLearningAgent — optimistic init + update + epsilon decay")
    print("-" * 60)
    agent = QLearningAgent(seed=42)
    fake_state = (0, 1, 2, 3, 4, 0, 1, 2, 0, 0, 1, 2, 3)
    fake_actions = [5, 10, 15]

    # Before any updates, all Q-values should equal q_init
    initial_qs = [agent.q(fake_state, a) for a in fake_actions]
    print(f"  Initial Q-values (should all be {agent.q_init}): {initial_qs}")
    assert all(q == agent.q_init for q in initial_qs)
    print(f"  Q-table size before update: {agent.q_table_size()}  (should be 0)")
    assert agent.q_table_size() == 0

    # Do one update with reward=2.0
    next_state = (1, 2, 3, 4, 0, 1, 2, 0, 0, 0, 2, 3, 4)
    agent.update(fake_state, 5, reward=2.0, next_state=next_state,
                 next_valid_actions=[6, 7], done=False)
    new_q = agent.q(fake_state, 5)
    # target = 2.0 + 0.95 * 1.0 (max over optimistic neighbours) = 2.95
    # new_q  = 1.0 + 0.15 * (2.95 - 1.0) = 1.2925
    expected = 1.0 + 0.15 * (2.0 + 0.95 * 1.0 - 1.0)
    print(f"  After 1 update: Q(s,5) = {new_q:.4f}  (expected {expected:.4f})")
    assert abs(new_q - expected) < 1e-9
    print(f"  Q-table size after update: {agent.q_table_size()}  (should be 1)")

    # Epsilon decay
    eps_before = agent.epsilon
    for _ in range(100):
        agent.decay_epsilon()
    eps_after = agent.epsilon
    print(f"  Epsilon after 100 decay steps: {eps_before:.4f} → {eps_after:.4f}")
    assert eps_after < eps_before
    assert eps_after >= agent.eps_end

    # ── Test 2: action selection respects valid_actions ─────────────────
    print("\nTest 2: action selection only returns valid actions")
    print("-" * 60)
    agent = QLearningAgent(seed=42)
    valid = [3, 7, 11]
    picks = set()
    for _ in range(200):
        a = agent.choose_action(fake_state, valid)
        assert a in valid
        picks.add(a)
    print(f"  Over 200 picks (eps=1.0), distinct actions chosen: {sorted(picks)}")
    print(f"  All in valid set {valid}: {picks.issubset(set(valid))}")

    # ── Test 3: greedy mode exploits highest Q-value ────────────────────
    print("\nTest 3: greedy=True always picks the best action")
    print("-" * 60)
    agent = QLearningAgent(seed=42)
    # Manually set Q-values
    agent.Q[(fake_state, 3)] = 0.5
    agent.Q[(fake_state, 7)] = 2.5
    agent.Q[(fake_state, 11)] = 1.0
    for _ in range(50):
        a = agent.choose_action(fake_state, [3, 7, 11], greedy=True)
        assert a == 7, f"Greedy should pick action 7 (Q=2.5), got {a}"
    print("  PASS: greedy always picked the highest-Q action")

    # ── Test 4: play a game with three different agents ─────────────────
    print("\nTest 4: Q-agent vs Random vs Greedy — play one game each")
    print("-" * 60)

    def play_game(p1_agent, p2_agent, p1_uses_encoder, p2_uses_encoder):
        engine = GameEngine()
        engine.reset()
        moves = 0
        while not engine.game_over and moves < 300:
            cp = engine.current_player
            if cp == 1:
                ag, uses_enc = p1_agent, p1_uses_encoder
            else:
                ag, uses_enc = p2_agent, p2_uses_encoder
            raw = engine.get_state()
            state_for_agent = encode(raw, perspective=cp) if uses_enc else raw
            action = ag.choose_action(state_for_agent, engine.valid_moves)
            if action is None:
                # Force the engine through its stalemate branch
                engine.do_move(0)
            else:
                engine.do_move(action)
            moves += 1
        return engine.winner, engine.p1_score, engine.p2_score, moves

    # Random vs Random (sanity)
    w, s1, s2, m = play_game(RandomAgent(seed=1), RandomAgent(seed=2), False, False)
    print(f"  Random vs Random:  winner={w}  P1={s1}  P2={s2}  moves={m}")

    # Greedy vs Random
    w, s1, s2, m = play_game(GreedyAgent(seed=1), RandomAgent(seed=2), False, False)
    print(f"  Greedy vs Random:  winner={w}  P1={s1}  P2={s2}  moves={m}")

    # Untrained Q-agent vs Random (Q is just optimistic init → near-random)
    q = QLearningAgent(seed=3)
    w, s1, s2, m = play_game(q, RandomAgent(seed=4), True, False)
    print(f"  Untrained Q vs Random:  winner={w}  P1={s1}  P2={s2}  moves={m}")

    # ── Test 5: Greedy beats Random in a small tournament ───────────────
    print("\nTest 5: Greedy should beat Random over 30 games (sanity check)")
    print("-" * 60)
    greedy_wins = random_wins = draws = 0
    for seed in range(30):
        # Alternate which side Greedy plays to remove starting-position bias
        if seed % 2 == 0:
            w, *_ = play_game(GreedyAgent(seed=seed), RandomAgent(seed=seed + 100),
                              False, False)
            if w == 1: greedy_wins += 1
            elif w == 2: random_wins += 1
            else: draws += 1
        else:
            w, *_ = play_game(RandomAgent(seed=seed + 100), GreedyAgent(seed=seed),
                              False, False)
            if w == 2: greedy_wins += 1
            elif w == 1: random_wins += 1
            else: draws += 1
    print(f"  Greedy wins: {greedy_wins}/30   Random wins: {random_wins}/30   "
          f"Draws: {draws}/30")
    print(f"  Greedy win rate (excluding draws): "
          f"{greedy_wins / max(1, greedy_wins + random_wins) * 100:.1f}%")

    print("\nAll agent self-tests passed.")
