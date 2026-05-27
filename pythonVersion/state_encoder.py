"""
state_encoder.py
================

Bridge between the game engine and the Q-learning agent.

Three responsibilities:
  1. encode_features(state, perspective)
        Take a raw state dict from GameEngine.get_state() and produce a
        13-dimensional feature vector from the perspective of one player.
        This is the agent's view of the world.

  2. discretise(features)
        Bin each continuous feature into one of 5 levels and return a tuple
        of 13 ints (the Q-table state key). Discretisation is necessary
        because a tabular Q-table needs a finite, hashable state space.

  3. compute_reward(result, perspective, ...)
        Compute the shaped reward for the move that was just played from
        the perspective of one player. Used to update the Q-table.

The 'perspective' argument (1 or 2) is what makes self-play work: the
same agent (one Q-table) can play either role because the encoder
always presents the state from the current player's point of view.
"""

from game_1 import NODES_DATA, ROUTES_DATA, REGIONS, NODE_REGION, get_connected


# ─────────────────────────────────────────────────────────────────────────
# Constants derived from the map (computed once, reused everywhere)
# ─────────────────────────────────────────────────────────────────────────

NUM_NODES = len(NODES_DATA)           # 30
MAX_CUSTOMERS = 5                     # highest possible customer count per node
WIN_SCORE = 20                        # for normalisation
NUM_REGIONS = len(REGIONS)            # 5

# Pre-compute the maximum out-degree of any node so we can normalise
# the "move freedom" feature. We do this once at import time so the
# encoder is fast to call inside the training loop.
_MAX_DEGREE = max(
    len(get_connected(ROUTES_DATA, n["id"])) for n in NODES_DATA
)

# Map each region key to an integer index 0..4 for feature 11/12
_REGION_INDEX = {reg["key"]: i for i, reg in enumerate(REGIONS)}


def _region_index_for_node(node_id):
    """Return the region index (0..4) for a given node, or 0 as a fallback."""
    reg = NODE_REGION.get(node_id)
    if reg is None:
        return 0
    return _REGION_INDEX[reg["key"]]


# ─────────────────────────────────────────────────────────────────────────
# 1. FEATURE ENCODING
# ─────────────────────────────────────────────────────────────────────────

def encode_features(state, perspective):
    """
    Encode the raw game state into a 13-element list of floats in [0, 1]
    (feature 5 is in [-1, 1]) from the perspective of `perspective` (1 or 2).

    Parameters
    ----------
    state : dict
        The dict returned by GameEngine.get_state().
    perspective : int
        Either 1 or 2 — whose point of view to encode from.

    Returns
    -------
    list of 13 floats
    """
    # Resolve "my" vs "opp" based on perspective
    if perspective == 1:
        my_pos, opp_pos = state["p1_pos"], state["p2_pos"]
        my_score, opp_score = state["p1_score"], state["p2_score"]
    else:
        my_pos, opp_pos = state["p2_pos"], state["p1_pos"]
        my_score, opp_score = state["p2_score"], state["p1_score"]

    my_blocked = 1 if state["turn_blocked"].get(perspective, False) else 0
    opp_player = 3 - perspective
    opp_blocked = 1 if state["turn_blocked"].get(opp_player, False) else 0

    # Neighbour info: we need valid_moves from MY perspective.
    # state["valid_moves"] is only valid for state["current_player"], so we
    # recompute connections from my_pos and filter out the opponent's node.
    my_connections = get_connected(ROUTES_DATA, my_pos)
    my_neighbours = [c for c in my_connections if c["to"] != opp_pos]
    n_valid = len(my_neighbours)

    customers = state["customers"]

    # Feature 6: customers at my current node (almost always 0 after collection,
    # but useful in transient states e.g. after SNK rollback)
    cust_here = customers.get(my_pos, 0) / MAX_CUSTOMERS

    # Feature 7: best customer count among neighbours (one-step lookahead)
    if n_valid > 0:
        best_neighbour_cust = max(
            customers.get(c["to"], 0) for c in my_neighbours
        ) / MAX_CUSTOMERS
    else:
        best_neighbour_cust = 0.0

    # Feature 8: obstacle pressure = fraction of valid moves that have an obstacle
    if n_valid > 0:
        obstacle_count = sum(
            1 for c in my_neighbours
            if c["obs"] is not None and not c["route"]["cleared"]
        )
        obstacle_pressure = obstacle_count / n_valid
    else:
        obstacle_pressure = 0.0

    # Feature 13: move freedom = fraction of max possible degree available
    move_freedom = n_valid / _MAX_DEGREE if _MAX_DEGREE > 0 else 0.0

    features = [
        (my_pos - 1) / (NUM_NODES - 1),                 # 1
        (opp_pos - 1) / (NUM_NODES - 1),                # 2
        min(my_score, WIN_SCORE) / WIN_SCORE,           # 3 (cap at 1.0)
        min(opp_score, WIN_SCORE) / WIN_SCORE,          # 4
        (my_score - opp_score) / WIN_SCORE,             # 5 in [-1, 1]
        cust_here,                                       # 6
        best_neighbour_cust,                            # 7
        obstacle_pressure,                              # 8
        float(my_blocked),                              # 9
        float(opp_blocked),                             # 10
        _region_index_for_node(my_pos) / (NUM_REGIONS - 1),   # 11
        _region_index_for_node(opp_pos) / (NUM_REGIONS - 1),  # 12
        move_freedom,                                   # 13
    ]
    return features


# ─────────────────────────────────────────────────────────────────────────
# 2. DISCRETISATION
# ─────────────────────────────────────────────────────────────────────────

NUM_BINS = 5  # 5 levels per feature → 5^13 ≈ 1.2B possible keys (sparse in practice)


def discretise(features):
    """
    Convert the 13 continuous features into a tuple of 13 ints in 0..4.
    Each feature is binned independently.

    Feature 5 ('score difference') lives in [-1, 1]; all others in [0, 1].
    We shift feature 5 by +1 then divide by 2 so it ends up in [0, 1] before binning.
    """
    bins = []
    for i, x in enumerate(features):
        if i == 4:  # score difference: [-1, 1] → [0, 1]
            x = (x + 1.0) / 2.0
        # Clamp into [0, 1] defensively
        x = max(0.0, min(1.0, x))
        # Map to 0..NUM_BINS-1
        b = int(x * NUM_BINS)
        if b == NUM_BINS:
            b = NUM_BINS - 1
        bins.append(b)
    return tuple(bins)


def encode(state, perspective):
    """Convenience: features + discretise in one call. This is what the agent calls."""
    return discretise(encode_features(state, perspective))


# ─────────────────────────────────────────────────────────────────────────
# 3. REWARD SHAPING
# ─────────────────────────────────────────────────────────────────────────

# Reward weights (the "shape" of the reward signal)
R_CUSTOMER       = +2.0   # per customer collected on this move
R_REGION_CLAIM   = +7.0   # one-off bonus for completing a region/district
R_NKABI          = -3.0   # triggered NKABI
R_SUPER_NKABI    = -6.0   # triggered SUPER NKABI (roll back 3 + lose 1)
R_POLICE         = -2.0   # triggered POLICE (skip next turn)
R_STEP           = -0.1   # per step penalty — encourages winning quickly
R_WIN            = +20.0  # agent won the game
R_LOSE           = -20.0  # opponent won the game
R_INVALID        = -0.05  # invalid move attempted (defensive)


def compute_reward(result, perspective, prev_state, new_state):
    """
    Compute the shaped reward for the move that was just executed,
    from the point of view of `perspective` (1 or 2).

    Parameters
    ----------
    result : dict
        The dict returned by GameEngine.do_move().
    perspective : int
        Player whose perspective we want the reward from.
    prev_state, new_state : dict
        State before and after the move.

    Returns
    -------
    float
    """
    # Was the move attempted by `perspective`?
    mover = prev_state["current_player"]
    moved_by_me = (mover == perspective)

    r = 0.0

    # Step penalty applies on every step
    r += R_STEP

    # Invalid move (only possible if move was attempted by `perspective`)
    if moved_by_me and not result.get("ok", False):
        r += R_INVALID
        return r  # nothing else happens on a failed move

    if moved_by_me:
        # Customer reward
        r += R_CUSTOMER * result.get("gained", 0)

        # Region-claim bonus — only if this move *newly* claimed a region for me
        if result.get("region_claimed_by", 0) == perspective:
            r += R_REGION_CLAIM

        # Obstacle penalties — only the mover suffers
        obs = result.get("obstacle")
        if obs == "NK":
            r += R_NKABI
        elif obs == "SNK":
            r += R_SUPER_NKABI
        elif obs == "POL":
            r += R_POLICE

    # Terminal reward — applies to both perspectives
    if new_state.get("game_over"):
        winner = new_state.get("winner")
        if winner == perspective:
            r += R_WIN
        elif winner == (3 - perspective):
            r += R_LOSE
        # else: draw / no winner — no terminal reward

    return r


# ─────────────────────────────────────────────────────────────────────────
# 4. SELF-TEST (run this file directly to sanity-check the encoder)
# ─────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    from game_1 import GameEngine

    print("state_encoder.py self-test")
    print("=" * 60)

    engine = GameEngine()
    state = engine.reset()

    print(f"\nMap stats:")
    print(f"  Nodes:       {NUM_NODES}")
    print(f"  Regions:     {NUM_REGIONS}")
    print(f"  Max degree:  {_MAX_DEGREE}")
    print(f"  Bins:        {NUM_BINS}")
    print(f"  Theoretical state space: {NUM_BINS}^13 = {NUM_BINS**13:,}")

    print("\nInitial state, P1 perspective:")
    f1 = encode_features(state, perspective=1)
    k1 = discretise(f1)
    names = [
        "my_pos", "opp_pos", "my_score", "opp_score", "score_diff",
        "cust_here", "best_neighbour", "obstacle_pressure",
        "my_blocked", "opp_blocked", "my_region", "opp_region", "move_freedom"
    ]
    for n, fv, kv in zip(names, f1, k1):
        print(f"  {n:20s} = {fv:+.3f}   bin={kv}")
    print(f"\n  state key (tuple): {k1}")

    print("\nInitial state, P2 perspective (should differ from P1):")
    f2 = encode_features(state, perspective=2)
    k2 = discretise(f2)
    print(f"  my_pos (P2's pos):  {f2[0]:.3f}  → bin {k2[0]}")
    print(f"  opp_pos (P1's pos): {f2[1]:.3f}  → bin {k2[1]}")
    print(f"  state key:          {k2}")
    assert k1 != k2, "P1 and P2 perspectives must produce different state keys!"
    print("  PASS: P1 and P2 keys differ")

    # Play a few moves and check rewards
    print("\nPlaying 5 random moves and computing rewards (P1 perspective):")
    import random
    random.seed(7)
    for i in range(5):
        prev = engine.get_state()
        if not engine.valid_moves:
            break
        choice = random.choice(engine.valid_moves)
        result = engine.do_move(choice)
        new = engine.get_state()
        r = compute_reward(result, perspective=1, prev_state=prev, new_state=new)
        print(f"  move {i+1}: P{prev['current_player']} -> {choice:2d}  "
              f"reward_for_P1 = {r:+.2f}  | {result['msg']}")

    print("\nAll self-tests passed.")
