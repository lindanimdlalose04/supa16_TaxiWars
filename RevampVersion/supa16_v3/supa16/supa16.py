"""
SUPA 16: TAXI WARS — full visual + gameplay redesign
=====================================================
Design language: Risk's map-as-scoreboard drawn with BTD5-style chunky
pieces on a warm paper board of KwaZulu-Natal.

What's new in this build
  GAMEPLAY
  - Route claiming: the first taxi to drive a road owns it (road tints
    your colour). Driving a rival's road pays them a 1-point toll.
    The map itself becomes the scoreboard.
  - Region control: collect from the MAJORITY of a region's towns to
    claim it permanently for +5. Progress is visible in the sidebar.
  - Customer respawn: every 4 full rounds, small fares (1-2) reappear
    in up to two empty towns, so the late game never goes dead.
  - Obstacles stay one-shot — but now eating one claims the route,
    so the first-mover tax became a first-mover investment.
  - Win target raised to 25 to fit the richer scoring.
  INTERFACE
  - Click to move. Hover a town for its name; hover a legal town to
    preview the road you'd take. No more typing node numbers.
  - Towns are houses: roof colour = region, big number on the wall =
    customers waiting. Collected towns shrink to small faded houses.
  - Taxis slide along roads; points float off the board as they change.
  - State-only sidebar; all rules live behind [H]elp.
  - Turn timer is OFF by default; toggle blitz mode with [T] in menu.

Run:  python supa16.py   (assets/ folder must sit next to this file)
"""

import os
import sys
import math
import copy
import random
from collections import deque

import pygame

# ----------------------------------------------------------------------------
# LAYOUT + PALETTE
# ----------------------------------------------------------------------------
WIN_W, WIN_H = 1280, 720
SIDEBAR_W    = 280
MAP_W, MAP_H = WIN_W - SIDEBAR_W, WIN_H
TURN_TIME    = 30.0
WIN_SCORE    = 25
HERE         = os.path.dirname(os.path.abspath(__file__))
ASSETS       = os.path.join(HERE, "assets")

PAL = {
    'paper':      (244, 240, 230),
    'paper_edge': (214, 207, 190),
    'panel':      (250, 247, 239),
    'ink':        (47, 44, 38),
    'ink_soft':   (122, 116, 104),
    'ink_faint':  (172, 165, 150),
    'road':       (185, 178, 163),
    'p1':         (15, 110, 86),
    'p1_bright':  (29, 158, 117),
    'p2':         (153, 53, 86),
    'p2_bright':  (212, 83, 126),
    'value':      (186, 117, 23),
    'value_brt':  (239, 159, 39),
    'danger':     (226, 75, 74),
    'danger_dk':  (121, 31, 31),
    'good':       (59, 109, 17),
}

REGIONS = [
    {'key': 'northern_natal', 'name': 'Northern Natal',
     'colour': (217, 140, 46),
     'nodes': [1, 2, 3, 19, 18, 4, 5, 6, 16]},
    {'key': 'midlands', 'name': 'Midlands',
     'colour': (109, 158, 74),
     'nodes': [7, 8, 27, 28, 17, 9, 25]},
    {'key': 'north_coast', 'name': 'North Coast',
     'colour': (216, 106, 82),
     'nodes': [14, 15, 11, 12, 13]},
    {'key': 'durban', 'name': 'Durban Metro',
     'colour': (134, 108, 196),
     'nodes': [29, 10, 21]},
    {'key': 'south_coast', 'name': 'South Coast',
     'colour': (74, 128, 196),
     'nodes': [30, 26, 23, 22, 24, 20]},
]
NODE_REGION = {nid: reg for reg in REGIONS for nid in reg['nodes']}
REGION_MAJORITY = {r['key']: len(r['nodes']) // 2 + 1 for r in REGIONS}

# Optimised layout: zero road crossings, >=92px node spacing,
# KZN cardinal geography preserved.
NODES_DATA = [
    {'id': 1,  'name': 'Jozini',           'x': 724, 'y':  86, 'customers': 1},
    {'id': 2,  'name': 'Pongola',          'x': 576, 'y':  58, 'customers': 2},
    {'id': 3,  'name': 'Vryheid',          'x': 268, 'y':  77, 'customers': 5},
    {'id': 19, 'name': 'Mkuze',            'x': 770, 'y': 188, 'customers': 1},
    {'id': 18, 'name': 'Hluhluwe',         'x': 545, 'y': 171, 'customers': 2},
    {'id': 12, 'name': 'Empangeni',        'x': 707, 'y': 255, 'customers': 5},
    {'id': 13, 'name': 'Richards Bay',     'x': 769, 'y': 389, 'customers': 2},
    {'id': 4,  'name': 'Newcastle',        'x':  51, 'y': 109, 'customers': 3},
    {'id': 5,  'name': 'Dundee',           'x': 159, 'y':  90, 'customers': 3},
    {'id': 6,  'name': 'Ladysmith',        'x':  50, 'y': 311, 'customers': 3},
    {'id': 27, 'name': 'Bergville',        'x': 127, 'y': 228, 'customers': 4},
    {'id': 7,  'name': 'Estcourt',         'x':  50, 'y': 434, 'customers': 2},
    {'id': 8,  'name': 'Mooi River',       'x': 306, 'y': 517, 'customers': 2},
    {'id': 28, 'name': 'Greytown',         'x': 314, 'y': 408, 'customers': 3},
    {'id': 16, 'name': 'Ulundi',           'x': 301, 'y': 190, 'customers': 3},
    {'id': 14, 'name': 'Eshowe',           'x': 432, 'y': 209, 'customers': 3},
    {'id': 15, 'name': 'Melmoth',          'x': 494, 'y': 284, 'customers': 4},
    {'id': 17, 'name': 'Nongoma',          'x': 588, 'y': 354, 'customers': 3},
    {'id': 11, 'name': 'Stanger',          'x': 674, 'y': 418, 'customers': 4},
    {'id': 25, 'name': 'Hammersdale',      'x': 185, 'y': 370, 'customers': 5},
    {'id': 9,  'name': 'Pietermaritzburg', 'x': 449, 'y': 549, 'customers': 5},
    {'id': 29, 'name': 'Pinetown',         'x': 554, 'y': 601, 'customers': 5},
    {'id': 10, 'name': 'Durban',           'x': 618, 'y': 514, 'customers': 5},
    {'id': 30, 'name': 'Underberg',        'x': 149, 'y': 488, 'customers': 3},
    {'id': 26, 'name': 'iXopo',            'x':  54, 'y': 613, 'customers': 2},
    {'id': 23, 'name': 'Harding',          'x': 213, 'y': 608, 'customers': 3},
    {'id': 22, 'name': 'Port Edward',      'x': 346, 'y': 613, 'customers': 1},
    {'id': 24, 'name': 'Kokstad',          'x': 152, 'y': 710, 'customers': 1},
    {'id': 20, 'name': 'Port Shepstone',   'x': 487, 'y': 710, 'customers': 3},
    {'id': 21, 'name': 'Margate',          'x': 644, 'y': 691, 'customers': 1},
]
ORIGINAL_CUSTOMERS = {n['id']: n['customers'] for n in NODES_DATA}

ROUTES_DATA = [
    {'from': 1,  'to': 2,  'obstacle': None},
    {'from': 2,  'to': 14, 'obstacle': 'NK'},
    {'from': 1,  'to': 19, 'obstacle': None},
    {'from': 19, 'to': 18, 'obstacle': None},
    {'from': 4,  'to': 6,  'obstacle': 'SNK'},
    {'from': 4,  'to': 5,  'obstacle': None},
    {'from': 3,  'to': 5,  'obstacle': None},
    {'from': 5,  'to': 27, 'obstacle': 'NK'},
    {'from': 6,  'to': 25, 'obstacle': 'NK'},
    {'from': 6,  'to': 7,  'obstacle': None},
    {'from': 2,  'to': 16, 'obstacle': None},
    {'from': 16, 'to': 27, 'obstacle': 'POL'},
    {'from': 12, 'to': 15, 'obstacle': 'SNK'},
    {'from': 18, 'to': 15, 'obstacle': 'NK'},
    {'from': 14, 'to': 15, 'obstacle': None},
    {'from': 12, 'to': 13, 'obstacle': None},
    {'from': 12, 'to': 17, 'obstacle': None},
    {'from': 17, 'to': 9,  'obstacle': 'NK'},
    {'from': 16, 'to': 28, 'obstacle': None},
    {'from': 28, 'to': 8,  'obstacle': 'SNK'},
    {'from': 26, 'to': 24, 'obstacle': None},
    {'from': 26, 'to': 7,  'obstacle': None},
    {'from': 26, 'to': 23, 'obstacle': 'NK'},
    {'from': 23, 'to': 8,  'obstacle': None},
    {'from': 8,  'to': 9,  'obstacle': None},
    {'from': 24, 'to': 22, 'obstacle': None},
    {'from': 20, 'to': 22, 'obstacle': None},
    {'from': 20, 'to': 29, 'obstacle': 'NK'},
    {'from': 13, 'to': 11, 'obstacle': None},
    {'from': 9,  'to': 10, 'obstacle': 'POL'},
    {'from': 21, 'to': 10, 'obstacle': None},
    {'from': 30, 'to': 7,  'obstacle': 'POL'},
    {'from': 30, 'to': 8,  'obstacle': None},
]
for _r in ROUTES_DATA:
    _r['cleared'] = False
    _r['owner']   = 0

MODE_PVP      = 'pvp'
MODE_HUMAN_P1 = 'human_p1'
MODE_HUMAN_P2 = 'human_p2'

OBSTACLE_INFO = {
    'NK':  ('Nkabi',       'hitmen on the road: lose 2 points'),
    'SNK': ('Super Nkabi', 'ambush: sent back along your trail, lose 1'),
    'POL': ('Police',      'roadblock: skip your next turn'),
}


# ----------------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------------
def find_node(nodes, node_id):
    for n in nodes:
        if n['id'] == node_id:
            return n
    return None


def get_connected(routes, node_id):
    out = []
    for r in routes:
        if r['from'] == node_id:
            out.append({'to': r['to'], 'route': r})
        elif r['to'] == node_id:
            out.append({'to': r['from'], 'route': r})
    return out


def is_connected(routes, a, b):
    for r in routes:
        if (r['from'] == a and r['to'] == b) or (r['from'] == b and r['to'] == a):
            return True, r
    return False, None


def compute_transform():
    min_x = min(n['x'] for n in NODES_DATA); max_x = max(n['x'] for n in NODES_DATA)
    min_y = min(n['y'] for n in NODES_DATA); max_y = max(n['y'] for n in NODES_DATA)
    pad = 64
    sx = (MAP_W - 2 * pad) / (max_x - min_x)
    sy = (MAP_H - 2 * pad - 30) / (max_y - min_y)
    ms = min(sx, sy)
    mox = pad - min_x * ms + (MAP_W - 2 * pad - (max_x - min_x) * ms) / 2
    moy = pad + 14 - min_y * ms
    return ms, mox, moy


def lerp(a, b, t):
    return a + (b - a) * t


def ease_out(t):
    return 1 - (1 - t) ** 3


# ----------------------------------------------------------------------------
# GAME ENGINE (logic only — no pygame references; headless-safe for training)
# ----------------------------------------------------------------------------
class GameEngine:
    WIN_SCORE = WIN_SCORE
    RESPAWN_EVERY_MOVES = 8        # every 4 full rounds
    NON_MOVE_LIMIT = 4

    def __init__(self):
        self.nodes  = copy.deepcopy(NODES_DATA)
        self.routes = copy.deepcopy(ROUTES_DATA)
        self.reset()

    def reset(self):
        for n in self.nodes:
            n['customers'] = ORIGINAL_CUSTOMERS[n['id']]
        for r in self.routes:
            r['cleared'] = False
            r['owner']   = 0
        self.p1_pos, self.p2_pos = random.sample([n['id'] for n in self.nodes], 2)
        self.p1_score = 0
        self.p2_score = 0
        self.current_player = 1
        self.turn_blocked = {1: False, 2: False}
        self.game_over = False
        self.winner = 0
        self.move_count = 0
        self.trail_p1 = deque(maxlen=6)
        self.trail_p2 = deque(maxlen=6)
        self.node_owner = {n['id']: 0 for n in self.nodes}
        self.region_claimed = {reg['key']: 0 for reg in REGIONS}
        self.consecutive_non_moves = 0
        self._update_valid_moves()
        return self.get_state()

    # ---- state ----
    def get_state(self):
        return {
            'p1_pos': self.p1_pos, 'p2_pos': self.p2_pos,
            'p1_score': self.p1_score, 'p2_score': self.p2_score,
            'current_player': self.current_player,
            'turn_blocked': self.turn_blocked.copy(),
            'valid_moves': self.valid_moves.copy(),
            'customers': {n['id']: n['customers'] for n in self.nodes},
            'routes_cleared': {f"{r['from']}-{r['to']}": r['cleared'] for r in self.routes},
            'route_owner': {f"{r['from']}-{r['to']}": r['owner'] for r in self.routes},
            'node_owner': self.node_owner.copy(),
            'region_claimed': self.region_claimed.copy(),
            'game_over': self.game_over, 'winner': self.winner,
        }

    def _update_valid_moves(self):
        pos = self.p1_pos if self.current_player == 1 else self.p2_pos
        opp = self.p2_pos if self.current_player == 1 else self.p1_pos
        self.valid_moves = [c['to'] for c in get_connected(self.routes, pos)
                            if c['to'] != opp]

    def region_progress(self, key):
        reg = next(r for r in REGIONS if r['key'] == key)
        c1 = sum(1 for nid in reg['nodes'] if self.node_owner[nid] == 1)
        c2 = sum(1 for nid in reg['nodes'] if self.node_owner[nid] == 2)
        return c1, c2, len(reg['nodes'])

    def routes_owned(self, player):
        return sum(1 for r in self.routes if r['owner'] == player)

    # ---- obstacle effects ----
    def _apply_nkabi(self, player):
        if player == 1:
            self.p1_score = max(0, self.p1_score - 2)
        else:
            self.p2_score = max(0, self.p2_score - 2)
        return f"Nkabi! P{player} loses 2 points"

    def _apply_super_nkabi(self, player, came_from):
        trail = self.trail_p1 if player == 1 else self.trail_p2
        history = list(trail)
        opp_pos = self.p2_pos if player == 1 else self.p1_pos
        target = None
        steps = 0
        if history:
            start_i = min(3, len(history)) - 1
            for i in range(start_i, len(history)):
                if history[i] != opp_pos:
                    target = history[i]
                    steps = i + 1
                    break
        if target is not None:
            msg = f"Super Nkabi! P{player} sent back {steps} stops"
        elif came_from is not None and came_from != opp_pos:
            target = came_from
            msg = f"Super Nkabi! P{player} bounced back"
        else:
            if player == 1:
                self.p1_score = max(0, self.p1_score - 1)
            else:
                self.p2_score = max(0, self.p2_score - 1)
            return f"Super Nkabi! P{player} loses 1 point", None
        if player == 1:
            self.p1_pos = target
            self.p1_score = max(0, self.p1_score - 1)
        else:
            self.p2_pos = target
            self.p2_score = max(0, self.p2_score - 1)
        return msg, target

    def _apply_police(self, player):
        self.turn_blocked[player] = True
        return f"Police! P{player} skips next turn"

    # ---- region majority claim ----
    def _check_region_claim(self, node_id, player):
        reg = NODE_REGION.get(node_id)
        if reg is None:
            return None
        key = reg['key']
        if self.region_claimed[key] != 0:
            return None
        count = sum(1 for nid in reg['nodes'] if self.node_owner[nid] == player)
        if count >= REGION_MAJORITY[key]:
            self.region_claimed[key] = player
            return reg
        return None

    def _check_win(self):
        if self.p1_score >= self.WIN_SCORE:
            self.game_over, self.winner = True, 1
        elif self.p2_score >= self.WIN_SCORE:
            self.game_over, self.winner = True, 2
        return self.game_over

    def _respawn_tick(self):
        """Every RESPAWN_EVERY_MOVES real moves, regrow small fares."""
        if self.move_count == 0 or self.move_count % self.RESPAWN_EVERY_MOVES:
            return []
        empty = [n for n in self.nodes
                 if n['customers'] == 0
                 and n['id'] not in (self.p1_pos, self.p2_pos)]
        random.shuffle(empty)
        spawned = []
        for n in empty[:2]:
            n['customers'] = random.randint(1, 2)
            spawned.append((n['id'], n['customers']))
        return spawned

    def record_non_move(self):
        """A turn passed without a real move (timeout / stalemate / block)."""
        self.consecutive_non_moves += 1
        if self.consecutive_non_moves >= self.NON_MOVE_LIMIT:
            self.game_over = True
            self.winner = 0
            return True
        return False

    # ---- the core move ----
    def do_move(self, target_id):
        R = {'ok': False, 'msg': '', 'msg_type': 'info', 'gained': 0,
             'obstacle': None, 'snk_target': None, 'toll': 0, 'toll_to': 0,
             'claimed_route': None, 'region': None, 'respawned': [],
             'from': None, 'to': None}

        if self.game_over:
            R['msg'] = "Game over"
            return R

        cp = self.current_player

        # blocked turn (police)
        if self.turn_blocked[cp]:
            R['ok'] = True
            R['msg'] = f"P{cp} is held at the roadblock — turn skipped"
            R['msg_type'] = 'warn'
            self.turn_blocked[cp] = False
            self.current_player = 3 - cp
            self._update_valid_moves()
            if self.record_non_move():
                R['msg'] = "Draw — the rank went quiet"
            return R

        # stalemate
        if not self.valid_moves:
            R['ok'] = True
            R['msg'] = f"P{cp} is boxed in — turn passes"
            R['msg_type'] = 'warn'
            self.current_player = 3 - cp
            if self.turn_blocked[self.current_player]:
                self.turn_blocked[self.current_player] = False
            self._update_valid_moves()
            if self.record_non_move():
                R['msg'] = "Draw — the rank went quiet"
            return R

        pos = self.p1_pos if cp == 1 else self.p2_pos
        opp = self.p2_pos if cp == 1 else self.p1_pos
        connected, route = is_connected(self.routes, pos, target_id)
        if not connected:
            R['msg'] = "No road goes there from here"
            R['msg_type'] = 'bad'
            return R
        if target_id == opp:
            R['msg'] = "Your rival is parked there"
            R['msg_type'] = 'bad'
            return R

        # ---- commit the move ----
        if cp == 1:
            self.p1_pos = target_id
        else:
            self.p2_pos = target_id
        came_from = pos
        route_was_cleared = route['cleared']
        route['cleared'] = True
        self.move_count += 1
        self.consecutive_non_moves = 0
        R['ok'] = True
        R['from'], R['to'] = came_from, target_id

        parts = []

        # ---- route economy: toll or claim ----
        if route['owner'] == 0:
            route['owner'] = cp
            R['claimed_route'] = (route['from'], route['to'])
            parts.append(f"route claimed")
        elif route['owner'] != cp:
            payer_score = self.p1_score if cp == 1 else self.p2_score
            pay = min(1, payer_score)
            if pay:
                if cp == 1:
                    self.p1_score -= pay
                    self.p2_score += pay
                else:
                    self.p2_score -= pay
                    self.p1_score += pay
                R['toll'] = pay
                R['toll_to'] = route['owner']
                parts.append(f"toll paid to P{route['owner']}")

        # ---- collect customers ----
        node = find_node(self.nodes, target_id)
        if node['customers'] > 0:
            gained = node['customers']
            node['customers'] = 0
            if cp == 1:
                self.p1_score += gained
            else:
                self.p2_score += gained
            R['gained'] = gained
            self.node_owner[target_id] = cp
            parts.insert(0, f"P{cp} +{gained} at {node['name']}")
            R['msg_type'] = 'good'
            reg = self._check_region_claim(target_id, cp)
            if reg is not None:
                bonus = 5
                if cp == 1:
                    self.p1_score += bonus
                else:
                    self.p2_score += bonus
                R['region'] = {'name': reg['name'], 'nodes': list(reg['nodes']),
                               'bonus': bonus, 'colour': reg['colour']}
                parts.append(f"{reg['name']} claimed +{bonus}")
        else:
            parts.insert(0, f"P{cp} drives to {node['name']}")

        # ---- obstacle (first traversal only) ----
        obs = route['obstacle'] if not route_was_cleared else None
        R['obstacle'] = obs
        snk_fired = False
        if obs == 'NK':
            parts.append(self._apply_nkabi(cp))
            R['msg_type'] = 'bad'
        elif obs == 'SNK':
            m, snk_t = self._apply_super_nkabi(cp, came_from)
            parts.append(m)
            R['msg_type'] = 'bad'
            R['snk_target'] = snk_t
            snk_fired = True
        elif obs == 'POL':
            parts.append(self._apply_police(cp))
            R['msg_type'] = 'warn'

        if not snk_fired:
            (self.trail_p1 if cp == 1 else self.trail_p2).appendleft(came_from)

        R['msg'] = "  ·  ".join(parts)

        if self._check_win():
            R['msg'] = f"Player {self.winner} runs the province!"
            R['msg_type'] = 'good'
            return R

        # ---- respawn small fares ----
        R['respawned'] = self._respawn_tick()

        # ---- next turn ----
        nxt = 3 - cp
        if self.turn_blocked[nxt]:
            self.turn_blocked[nxt] = False
            parts.append(f"P{nxt} held at roadblock")
            R['msg'] = "  ·  ".join(parts)
        else:
            self.current_player = nxt
        self._update_valid_moves()
        return R


# ----------------------------------------------------------------------------
# ASSETS
# ----------------------------------------------------------------------------
class Assets:
    def __init__(self):
        self.img = {}
        self.sfx = {}
        self.muted = False
        for reg in REGIONS:
            self.img[f"house_{reg['key']}"] = self._load(f"house_{reg['key']}.png")
            self.img[f"done_{reg['key']}"]  = self._load(f"house_{reg['key']}_done.png")
        self.img['taxi1'] = self._load('taxi_p1.png')
        self.img['taxi2'] = self._load('taxi_p2.png')
        # hover-enlarged variants
        for k in list(self.img):
            im = self.img[k]
            if im is not None and k.startswith('house'):
                self.img[k + '_big'] = pygame.transform.smoothscale(
                    im, (int(im.get_width() * 1.12), int(im.get_height() * 1.12)))
        for name in ('click', 'move', 'coin', 'danger', 'toll', 'claim', 'win'):
            self.sfx[name] = self._load_sfx(f"sfx_{name}.wav")

    def _load(self, fname):
        path = os.path.join(ASSETS, fname)
        try:
            return pygame.image.load(path).convert_alpha()
        except Exception:
            return None

    def _load_sfx(self, fname):
        path = os.path.join(ASSETS, fname)
        try:
            return pygame.mixer.Sound(path)
        except Exception:
            return None

    def play(self, name):
        if self.muted:
            return
        s = self.sfx.get(name)
        if s is not None:
            try:
                s.play()
            except Exception:
                pass


def build_fonts():
    def F(name, size):
        path = os.path.join(ASSETS, name)
        try:
            return pygame.font.Font(path, size)
        except Exception:
            return pygame.font.Font(None, size + 4)
    bold, med, reg = 'Poppins-Bold.ttf', 'Poppins-Medium.ttf', 'Poppins-Regular.ttf'
    return {
        'title':    F(bold, 54),
        'subtitle': F(med, 22),
        'menu':     F(med, 22),
        'hint':     F(reg, 15),
        'h1':       F(bold, 24),
        'h2':       F(bold, 17),
        'body':     F(reg, 15),
        'small':    F(med, 13),
        'tiny':     F(med, 11),
        'value':    F(bold, 22),
        'value_sm': F(bold, 14),
        'score':    F(bold, 30),
        'msg':      F(med, 16),
        'float':    F(bold, 18),
        'win':      F(bold, 44),
        'obs':      F(bold, 13),
    }


# ----------------------------------------------------------------------------
# SMALL DRAW UTILITIES
# ----------------------------------------------------------------------------
def draw_round_line(surf, col, p1, p2, w):
    pygame.draw.line(surf, col, p1, p2, w)
    pygame.draw.circle(surf, col, (int(p1[0]), int(p1[1])), w // 2)
    pygame.draw.circle(surf, col, (int(p2[0]), int(p2[1])), w // 2)


def draw_chip(surf, font, text, cx, cy, fg, bg, pad=10):
    t = font.render(text, True, fg)
    w, h = t.get_width() + pad * 2, t.get_height() + 8
    r = pygame.Rect(int(cx - w / 2), int(cy - h / 2), w, h)
    chip = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(chip, bg, chip.get_rect(), border_radius=h // 2)
    surf.blit(chip, r.topleft)
    surf.blit(t, (r.x + pad, r.y + 4))
    return r


def draw_obstacle_sign(surf, fonts, obs, cx, cy):
    cx, cy = int(cx), int(cy)
    col, dk = PAL['danger'], PAL['danger_dk']
    if obs == 'NK':
        pts = [(cx, cy - 12), (cx + 12, cy), (cx, cy + 12), (cx - 12, cy)]
        pygame.draw.polygon(surf, col, pts)
        pygame.draw.polygon(surf, dk, pts, 3)
        sym = 'N'
    elif obs == 'SNK':
        pygame.draw.circle(surf, col, (cx, cy), 12)
        pygame.draw.circle(surf, dk, (cx, cy), 12, 3)
        pygame.draw.circle(surf, dk, (cx, cy), 6, 2)
        sym = ''
    else:  # POL
        r = pygame.Rect(cx - 11, cy - 11, 22, 22)
        pygame.draw.rect(surf, col, r, border_radius=5)
        pygame.draw.rect(surf, dk, r, 3, border_radius=5)
        sym = 'P'
    if sym:
        t = fonts['obs'].render(sym, True, (252, 235, 235))
        surf.blit(t, (cx - t.get_width() // 2, cy - t.get_height() // 2))


# ----------------------------------------------------------------------------
# MENU
# ----------------------------------------------------------------------------
class MenuScreen:
    def __init__(self, screen, fonts, assets, settings):
        self.screen = screen
        self.fonts = fonts
        self.assets = assets
        self.settings = settings
        self.sel = 0
        self.anim_t = 0.0
        self.result = None
        self.ms, self.mox, self.moy = compute_transform()
        self.items = [
            ('2 players — same screen', MODE_PVP),
            ('Play vs AI  (you are P1)', MODE_HUMAN_P1),
            ('Play vs AI  (you are P2)', MODE_HUMAN_P2),
            ('Exit', 'exit'),
        ]

    def _item_rects(self):
        base_y = 330
        return [pygame.Rect(WIN_W // 2 - 230, base_y + i * 70, 460, 54)
                for i in range(len(self.items))]

    def handle_event(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_UP, pygame.K_w):
                self.sel = (self.sel - 1) % len(self.items)
            elif ev.key in (pygame.K_DOWN, pygame.K_s):
                self.sel = (self.sel + 1) % len(self.items)
            elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.assets.play('click')
                self.result = self.items[self.sel][1]
            elif ev.key == pygame.K_t:
                self.settings['timer'] = not self.settings['timer']
                self.assets.play('click')
            elif ev.key == pygame.K_m:
                self.assets.muted = not self.assets.muted
            elif ev.key == pygame.K_ESCAPE:
                self.result = 'exit'
        if ev.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self._item_rects()):
                if r.collidepoint(ev.pos):
                    self.sel = i
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for i, r in enumerate(self._item_rects()):
                if r.collidepoint(ev.pos):
                    self.sel = i
                    self.assets.play('click')
                    self.result = self.items[i][1]

    def update(self, dt):
        self.anim_t += dt

    def _draw_map_preview(self):
        """Faint live map behind the menu — the game previews itself."""
        ghost = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        off_x = SIDEBAR_W // 2
        for r in ROUTES_DATA:
            a = find_node(NODES_DATA, r['from'])
            b = find_node(NODES_DATA, r['to'])
            p1 = (a['x'] * self.ms + self.mox + off_x, a['y'] * self.ms + self.moy)
            p2 = (b['x'] * self.ms + self.mox + off_x, b['y'] * self.ms + self.moy)
            pygame.draw.line(ghost, (*PAL['road'], 70), p1, p2, 3)
        for n in NODES_DATA:
            reg = NODE_REGION[n['id']]
            p = (int(n['x'] * self.ms + self.mox + off_x),
                 int(n['y'] * self.ms + self.moy))
            pygame.draw.circle(ghost, (*reg['colour'], 60), p, 10)
        self.screen.blit(ghost, (0, 0))

    def render(self):
        self.screen.fill(PAL['paper'])
        self._draw_map_preview()

        t = self.fonts['title'].render("SUPA 16", True, PAL['ink'])
        self.screen.blit(t, (WIN_W // 2 - t.get_width() // 2, 96))
        # two-colour underline: the two rival associations
        uw, uy = 220, 162
        pygame.draw.rect(self.screen, PAL['p1_bright'],
                         (WIN_W // 2 - uw // 2, uy, uw // 2, 6), border_radius=3)
        pygame.draw.rect(self.screen, PAL['p2_bright'],
                         (WIN_W // 2, uy, uw // 2, 6), border_radius=3)
        s = self.fonts['subtitle'].render("TAXI WARS", True, PAL['ink_soft'])
        self.screen.blit(s, (WIN_W // 2 - s.get_width() // 2, 176))
        h = self.fonts['hint'].render(
            "Two taxi associations. One province. First to 25 runs KZN.",
            True, PAL['ink_soft'])
        self.screen.blit(h, (WIN_W // 2 - h.get_width() // 2, 216))

        for i, ((label, _), r) in enumerate(zip(self.items, self._item_rects())):
            active = (i == self.sel)
            card = pygame.Surface(r.size, pygame.SRCALPHA)
            pygame.draw.rect(card, (*PAL['panel'], 235), card.get_rect(),
                             border_radius=14)
            self.screen.blit(card, r.topleft)
            edge = PAL['ink'] if active else PAL['paper_edge']
            pygame.draw.rect(self.screen, edge, r, 3 if active else 2,
                             border_radius=14)
            col = PAL['ink'] if active else PAL['ink_soft']
            txt = self.fonts['menu'].render(label, True, col)
            self.screen.blit(txt, (r.centerx - txt.get_width() // 2,
                                   r.centery - txt.get_height() // 2))
            if active:
                tx = self.assets.img['taxi1']
                if tx:
                    self.screen.blit(tx, (r.x - 60,
                                          r.centery - tx.get_height() // 2))

        timer_state = "ON · 30s turns" if self.settings['timer'] else "OFF"
        mute_state = "muted" if self.assets.muted else "on"
        f = self.fonts['hint'].render(
            f"[T] turn timer: {timer_state}      [M] sound: {mute_state}      "
            f"[Enter] select  ·  arrows or mouse",
            True, PAL['ink_faint'])
        self.screen.blit(f, (WIN_W // 2 - f.get_width() // 2, WIN_H - 56))
        v = self.fonts['hint'].render("Yuppie Games  ·  v3.0", True, PAL['ink_faint'])
        self.screen.blit(v, (WIN_W // 2 - v.get_width() // 2, WIN_H - 30))
        pygame.display.flip()


# ----------------------------------------------------------------------------
# AI LOADER (kept compatible with the training project)
# ----------------------------------------------------------------------------
def try_load_agent(screen, fonts, pkl_path=None):
    try:
        from agent import QLearningAgent
        err = None
    except Exception as ex:
        QLearningAgent, err = None, ex
    candidates = [pkl_path] if pkl_path else []
    candidates += [os.path.join(HERE, "runs", "run1", "agent.pkl"),
                   os.path.join(os.getcwd(), "runs", "run1", "agent.pkl"),
                   os.path.join(HERE, "agent.pkl")]
    msg = None
    if err is None:
        for p in candidates:
            if p and os.path.exists(p):
                try:
                    return QLearningAgent.load(p)
                except Exception as ex:
                    msg = ["Could not load the trained agent:", str(ex)]
                    break
        if msg is None:
            msg = ["No trained agent found.",
                   "The new rules need a retrain anyway:",
                   "python train.py --episodes 100000"]
    else:
        msg = ["Could not import the agent module:", str(err)]

    clock = pygame.time.Clock()
    end_at = pygame.time.get_ticks() + 2600
    while pygame.time.get_ticks() < end_at:
        for ev in pygame.event.get():
            if ev.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return None
        screen.fill(PAL['paper'])
        t = fonts['h1'].render("AI not available", True, PAL['danger'])
        screen.blit(t, (WIN_W // 2 - t.get_width() // 2, WIN_H // 3))
        y = WIN_H // 3 + 60
        for line in msg:
            s = fonts['body'].render(line, True, PAL['ink_soft'])
            screen.blit(s, (WIN_W // 2 - s.get_width() // 2, y))
            y += 26
        pygame.display.flip()
        clock.tick(60)
    return None


# ----------------------------------------------------------------------------
# GAME SCREEN
# ----------------------------------------------------------------------------
class TaxiWarsGame:
    HOUSE_HIT_R = 36

    def __init__(self, screen, fonts, assets, settings,
                 mode=MODE_PVP, agent=None, human_player=None,
                 show_intro=True):
        self.screen = screen
        self.fonts = fonts
        self.assets = assets
        self.settings = settings
        self.mode = mode
        self.engine = GameEngine()
        self.ms, self.mox, self.moy = compute_transform()

        self.agent = agent
        self.human_player = human_player
        self.ai_player = (3 - human_player) if human_player else None
        self.ai_wait = 0.0

        self.anim_t = 0.0
        self.hover_node = None
        self.help_open = show_intro
        self.intro = show_intro

        # taxi render positions (screen coords) + animation queue
        self.taxi_pos = {1: self._np(self.engine.p1_pos),
                         2: self._np(self.engine.p2_pos)}
        self.anims = []          # list of dicts: player, from, to, t, dur, on_done
        self.floats = []         # floating score texts
        self.flash = {}          # node_id -> ttl
        self.feed = deque(maxlen=3)
        self.shake_node = None
        self.shake_t = 0.0

        self.turn_time_left = TURN_TIME
        self._game_time = 0.0

        p1n = find_node(self.engine.nodes, self.engine.p1_pos)['name']
        p2n = find_node(self.engine.nodes, self.engine.p2_pos)['name']
        self._feed(f"P1 starts at {p1n}", PAL['p1'])
        self._feed(f"P2 starts at {p2n}", PAL['p2'])

    # ---- coordinate helpers ----
    def _np(self, node_id):
        n = find_node(self.engine.nodes, node_id)
        return [n['x'] * self.ms + self.mox, n['y'] * self.ms + self.moy]

    def _node_at(self, mx, my):
        best, bd = None, 1e9
        for n in self.engine.nodes:
            x, y = n['x'] * self.ms + self.mox, n['y'] * self.ms + self.moy
            d = math.hypot(mx - x, my - y)
            if d < self.HOUSE_HIT_R and d < bd:
                best, bd = n['id'], d
        return best

    # ---- feedback helpers ----
    def _feed(self, text, colour):
        self.feed.appendleft((text, colour))

    def _float(self, node_id, text, colour, dy=0):
        x, y = self._np(node_id)
        self.floats.append({'x': x, 'y': y - 34 + dy, 'text': text,
                            'col': colour, 'ttl': 1.3})

    def _do_flash(self, node_id, dur=1.0):
        self.flash[node_id] = dur

    # ---- executing a move with animation + effects ----
    def _execute(self, target_id):
        e = self.engine
        cp = e.current_player
        R = e.do_move(target_id)
        if not R['ok']:
            self._feed(R['msg'], PAL['danger'])
            self.shake_node = target_id
            self.shake_t = 0.32
            self.assets.play('danger')
            return
        if R['from'] is None:
            # pass / skip — no movement happened
            self._feed(R['msg'], PAL['ink_soft'])
            self.turn_time_left = TURN_TIME
            return

        self.assets.play('move')
        self.turn_time_left = TURN_TIME

        def after_arrival():
            if R['claimed_route']:
                self.assets.play('click')
            if R['toll']:
                self.assets.play('toll')
                self._float(R['to'], f"-{R['toll']} toll",
                            PAL['p1'] if R['toll_to'] == 1 else PAL['p2'])
            if R['gained']:
                self.assets.play('coin')
                self._float(R['to'], f"+{R['gained']}",
                            PAL['p1_bright'] if cp == 1 else PAL['p2_bright'],
                            dy=-16 if R['toll'] else 0)
                self._do_flash(R['to'])
            if R['region']:
                self.assets.play('claim')
                for nid in R['region']['nodes']:
                    self._do_flash(nid, 1.8)
                self._float(R['to'], f"+{R['region']['bonus']} region",
                            PAL['value'], dy=-34)
            if R['obstacle'] == 'NK':
                self.assets.play('danger')
                self._float(R['to'], "-2", PAL['danger'], dy=-16)
            elif R['obstacle'] == 'POL':
                self.assets.play('danger')
                self._float(R['to'], "roadblock", PAL['danger'], dy=-16)
            elif R['obstacle'] == 'SNK':
                self.assets.play('danger')
                self._float(R['to'], "-1 ambush", PAL['danger'], dy=-16)
                if R['snk_target'] is not None:
                    self.anims.append({
                        'player': cp, 'frm': self._np(R['to']),
                        'to': self._np(R['snk_target']),
                        't': 0.0, 'dur': 0.4, 'on_done': None})
            for nid, val in R['respawned']:
                self._do_flash(nid, 1.4)
                self._float(nid, f"+{val} fare", PAL['value'])
            self._feed(R['msg'], {
                'good': PAL['good'], 'bad': PAL['danger'],
                'warn': PAL['value'], 'info': PAL['ink_soft']}[R['msg_type']])
            if e.game_over and e.winner:
                self.assets.play('win')

        self.anims.append({'player': cp, 'frm': self._np(R['from']),
                           'to': self._np(R['to']), 't': 0.0, 'dur': 0.34,
                           'on_done': after_arrival})

    # ---- events ----
    def handle_event(self, ev):
        e = self.engine
        if ev.type == pygame.QUIT:
            return False
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                if self.help_open:
                    self.help_open = False
                    self.intro = False
                    return True
                return 'menu'
            if ev.key == pygame.K_h:
                self.help_open = not self.help_open
                self.intro = False
                return True
            if ev.key == pygame.K_m:
                self.assets.muted = not self.assets.muted
                return True
            if ev.key == pygame.K_r:
                self.__init__(self.screen, self.fonts, self.assets,
                              self.settings, mode=self.mode, agent=self.agent,
                              human_player=self.human_player, show_intro=False)
                return True
        if self.help_open:
            if ev.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                self.help_open = False
                self.intro = False
            return True
        if ev.type == pygame.MOUSEMOTION:
            self.hover_node = self._node_at(*ev.pos) if ev.pos[0] < MAP_W else None
            return True
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if e.game_over or self.anims:
                return True
            if self.agent is not None and e.current_player == self.ai_player:
                return True
            nid = self._node_at(*ev.pos)
            if nid is None:
                return True
            if nid in e.valid_moves:
                self._execute(nid)
            else:
                self._feed("No road goes there from here", PAL['danger'])
                self.shake_node = nid
                self.shake_t = 0.32
                self.assets.play('danger')
        return True

    # ---- update ----
    def update(self, dt):
        self.anim_t += dt
        self._game_time += dt
        e = self.engine

        # animations
        for a in self.anims[:1]:   # run one at a time, in order
            a['t'] += dt
            t = min(1.0, a['t'] / a['dur'])
            k = ease_out(t)
            self.taxi_pos[a['player']] = [lerp(a['frm'][0], a['to'][0], k),
                                          lerp(a['frm'][1], a['to'][1], k)]
            if t >= 1.0:
                if a['on_done']:
                    a['on_done']()
                self.anims.pop(0)
        # keep idle taxis pinned to their nodes
        if not self.anims:
            self.taxi_pos[1] = self._np(e.p1_pos)
            self.taxi_pos[2] = self._np(e.p2_pos)

        # floats / flash / shake decay
        for f in self.floats:
            f['ttl'] -= dt
            f['y'] -= 26 * dt
        self.floats = [f for f in self.floats if f['ttl'] > 0]
        for k in list(self.flash):
            self.flash[k] -= dt
            if self.flash[k] <= 0:
                del self.flash[k]
        if self.shake_t > 0:
            self.shake_t -= dt

        if self.help_open or e.game_over or self.anims:
            return

        # AI turn
        if self.agent is not None and e.current_player == self.ai_player:
            self.ai_wait += dt
            if self.ai_wait >= 1.2:
                self.ai_wait = 0.0
                self._take_ai_turn()
            return
        self.ai_wait = 0.0

        # auto-resolve forced passes (police block / stalemate)
        if e.turn_blocked[e.current_player] or not e.valid_moves:
            self._execute(-1)
            return

        # optional blitz timer
        if self.settings['timer']:
            self.turn_time_left -= dt
            if self.turn_time_left <= 0:
                cp = e.current_player
                self._feed(f"P{cp} ran out of time — turn passes", PAL['value'])
                e.current_player = 3 - cp
                e._update_valid_moves()
                ended = e.record_non_move()
                if ended:
                    self._feed("Draw — the rank went quiet", PAL['value'])
                self.turn_time_left = TURN_TIME

    def _take_ai_turn(self):
        e = self.engine
        if e.game_over or not e.valid_moves:
            self._execute(-1)
            return
        try:
            from state_encoder import encode
            key = encode(e.get_state(), perspective=self.ai_player)
            action = self.agent.choose_action(key, e.valid_moves, greedy=True)
        except Exception:
            action = None
        if action is None or action not in e.valid_moves:
            action = random.choice(e.valid_moves)
        self._execute(action)

    # =========================================================================
    # RENDER
    # =========================================================================
    def render(self):
        self.screen.fill(PAL['paper'])
        self._draw_board_frame()
        self._draw_routes()
        self._draw_houses()
        self._draw_taxis()
        self._draw_floats()
        self._draw_turn_chip()
        if self.settings['timer'] and not self.engine.game_over:
            self._draw_timer()
        self._draw_sidebar()
        self._draw_tooltip()
        if self.engine.game_over:
            self._draw_game_over()
        if self.help_open:
            self._draw_help()
        pygame.display.flip()

    def _draw_board_frame(self):
        pygame.draw.rect(self.screen, PAL['paper_edge'],
                         (10, 10, MAP_W - 20, WIN_H - 20), 2, border_radius=18)

    # ---- roads ----
    def _draw_routes(self):
        e = self.engine
        hover_route = None
        if (self.hover_node in e.valid_moves and not e.game_over
                and not self.anims and not self.help_open):
            pos = e.p1_pos if e.current_player == 1 else e.p2_pos
            _, hover_route = is_connected(e.routes, pos, self.hover_node)

        for r in e.routes:
            a = find_node(e.nodes, r['from'])
            b = find_node(e.nodes, r['to'])
            p1 = (a['x'] * self.ms + self.mox, a['y'] * self.ms + self.moy)
            p2 = (b['x'] * self.ms + self.mox, b['y'] * self.ms + self.moy)
            if r['owner'] == 1:
                draw_round_line(self.screen, PAL['p1_bright'], p1, p2, 7)
            elif r['owner'] == 2:
                draw_round_line(self.screen, PAL['p2_bright'], p1, p2, 7)
            else:
                draw_round_line(self.screen, PAL['road'], p1, p2, 4)
            if r is hover_route:
                draw_round_line(self.screen, PAL['ink'], p1, p2, 2)
            if r['obstacle'] and not r['cleared']:
                draw_obstacle_sign(self.screen, self.fonts, r['obstacle'],
                                   (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)

    # ---- houses ----
    def _draw_houses(self):
        e = self.engine
        cur_col = PAL['p1_bright'] if e.current_player == 1 else PAL['p2_bright']
        pulse = (math.sin(self.anim_t * 4) + 1) / 2

        for n in e.nodes:
            nid = n['id']
            x = n['x'] * self.ms + self.mox
            y = n['y'] * self.ms + self.moy
            if nid == self.shake_node and self.shake_t > 0:
                x += math.sin(self.shake_t * 60) * 4
            reg = NODE_REGION[nid]
            hovered = (nid == self.hover_node)
            valid = (nid in e.valid_moves and not e.game_over
                     and not self.anims)

            # flash halo
            if nid in self.flash:
                a = int(self.flash[nid] / 1.8 * 120) + 30
                halo = pygame.Surface((96, 96), pygame.SRCALPHA)
                pygame.draw.circle(halo, (*PAL['value_brt'], min(150, a)),
                                   (48, 48), 46)
                self.screen.blit(halo, (x - 48, y - 48))

            if n['customers'] > 0:
                key = f"house_{reg['key']}" + ('_big' if hovered else '')
                img = self.assets.img.get(key)
                if valid:
                    w = (img.get_width() if img else 66) + 16
                    h = (img.get_height() if img else 62) + 16
                    box = pygame.Surface((w + 8, h + 8), pygame.SRCALPHA)
                    pygame.draw.rect(box, (*cur_col, int(140 + pulse * 90)),
                                     box.get_rect(), 4, border_radius=14)
                    self.screen.blit(box, (x - (w + 8) / 2, y - (h + 8) / 2 - 2))
                if img:
                    self.screen.blit(img, (x - img.get_width() / 2,
                                           y - img.get_height() / 2))
                val = self.fonts['value'].render(str(n['customers']), True,
                                                 PAL['ink'])
                self.screen.blit(val, (x - val.get_width() / 2, y - 2))
            else:
                img = self.assets.img.get(f"done_{reg['key']}")
                if valid:
                    box = pygame.Surface((52, 50), pygame.SRCALPHA)
                    pygame.draw.rect(box, (*cur_col, int(140 + pulse * 90)),
                                     box.get_rect(), 3, border_radius=10)
                    self.screen.blit(box, (x - 26, y - 25))
                if img:
                    self.screen.blit(img, (x - img.get_width() / 2,
                                           y - img.get_height() / 2))
                # tiny owner tick under collected towns
                owner = e.node_owner[nid]
                if owner:
                    c = PAL['p1_bright'] if owner == 1 else PAL['p2_bright']
                    pygame.draw.circle(self.screen, c,
                                       (int(x), int(y + 22)), 4)

    # ---- taxis ----
    def _draw_taxis(self):
        e = self.engine
        for p in (1, 2):
            img = self.assets.img.get(f'taxi{p}')
            x, y = self.taxi_pos[p]
            y -= 38   # hover above the house
            if img:
                self.screen.blit(img, (x - img.get_width() / 2,
                                       y - img.get_height() / 2))
                badge = self.fonts['tiny'].render(str(p), True, (250, 247, 239))
                bx, by = int(x), int(y - img.get_height() / 2 - 8)
                col = PAL['p1'] if p == 1 else PAL['p2']
                pygame.draw.circle(self.screen, col, (bx, by), 9)
                self.screen.blit(badge, (bx - badge.get_width() / 2,
                                         by - badge.get_height() / 2))

    # ---- floats ----
    def _draw_floats(self):
        for f in self.floats:
            a = min(1.0, f['ttl'] / 0.5)
            t = self.fonts['float'].render(f['text'], True, f['col'])
            t.set_alpha(int(a * 255))
            self.screen.blit(t, (f['x'] - t.get_width() / 2, f['y']))

    # ---- turn chip / timer ----
    def _draw_turn_chip(self):
        e = self.engine
        if e.game_over:
            return
        cp = e.current_player
        col = PAL['p1'] if cp == 1 else PAL['p2']
        is_ai = self.agent is not None and cp == self.ai_player
        label = f"P{cp} — AI thinking" if is_ai else f"Player {cp}'s turn"
        draw_chip(self.screen, self.fonts['h2'], label, 110, 34,
                  (250, 247, 239), (*col, 235))

    def _draw_timer(self):
        t = max(0.0, self.turn_time_left)
        frac = t / TURN_TIME
        col = PAL['good'] if frac > 0.4 else (PAL['value'] if frac > 0.2
                                              else PAL['danger'])
        cx, cy, r = MAP_W - 46, 40, 24
        pygame.draw.circle(self.screen, PAL['paper_edge'], (cx, cy), r, 5)
        end_a = -math.pi / 2 + frac * 2 * math.pi
        steps = max(2, int(40 * frac))
        pts = [(cx + r * math.cos(-math.pi / 2 + (end_a + math.pi / 2) * i / steps),
                cy + r * math.sin(-math.pi / 2 + (end_a + math.pi / 2) * i / steps))
               for i in range(steps + 1)]
        if len(pts) > 1:
            pygame.draw.lines(self.screen, col, False, pts, 5)
        s = self.fonts['h2'].render(str(int(math.ceil(t))), True, col)
        self.screen.blit(s, (cx - s.get_width() / 2, cy - s.get_height() / 2))

    # ---- tooltip ----
    def _draw_tooltip(self):
        if self.hover_node is None or self.help_open:
            return
        n = find_node(self.engine.nodes, self.hover_node)
        reg = NODE_REGION[n['id']]
        x = n['x'] * self.ms + self.mox
        y = n['y'] * self.ms + self.moy
        text = f"{n['name']}  ·  {reg['name']}"
        t = self.fonts['small'].render(text, True, (250, 247, 239))
        w, h = t.get_width() + 18, t.get_height() + 10
        tx = min(max(10, x - w / 2), MAP_W - w - 10)
        ty = y - 64 - h if y - 64 - h > 14 else y + 44
        tip = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(tip, (*PAL['ink'], 235), tip.get_rect(),
                         border_radius=8)
        self.screen.blit(tip, (tx, ty))
        self.screen.blit(t, (tx + 9, ty + 5))

    # ---- sidebar ----
    def _draw_sidebar(self):
        e = self.engine
        sx = MAP_W
        pygame.draw.rect(self.screen, PAL['panel'], (sx, 0, SIDEBAR_W, WIN_H))
        pygame.draw.line(self.screen, PAL['paper_edge'], (sx, 0), (sx, WIN_H), 2)
        px, pw = sx + 16, SIDEBAR_W - 32
        y = 18

        t = self.fonts['h2'].render("SUPA 16 · TAXI WARS", True, PAL['ink'])
        self.screen.blit(t, (px + (pw - t.get_width()) // 2, y))
        y += 30
        pygame.draw.rect(self.screen, PAL['p1_bright'],
                         (px + pw // 2 - 40, y, 40, 4), border_radius=2)
        pygame.draw.rect(self.screen, PAL['p2_bright'],
                         (px + pw // 2, y, 40, 4), border_radius=2)
        y += 16

        # score cards
        for p in (1, 2):
            col = PAL['p1'] if p == 1 else PAL['p2']
            bright = PAL['p1_bright'] if p == 1 else PAL['p2_bright']
            score = e.p1_score if p == 1 else e.p2_score
            pos = e.p1_pos if p == 1 else e.p2_pos
            name = find_node(e.nodes, pos)['name']
            card = pygame.Rect(px, y, pw, 86)
            cs = pygame.Surface(card.size, pygame.SRCALPHA)
            pygame.draw.rect(cs, (*bright, 26), cs.get_rect(), border_radius=12)
            self.screen.blit(cs, card.topleft)
            active = (e.current_player == p and not e.game_over)
            pygame.draw.rect(self.screen, col if active else PAL['paper_edge'],
                             card, 3 if active else 2, border_radius=12)
            lab = self.fonts['small'].render(f"PLAYER {p}", True, col)
            self.screen.blit(lab, (px + 12, y + 9))
            sc = self.fonts['score'].render(str(score), True, PAL['ink'])
            self.screen.blit(sc, (px + 12, y + 24))
            tgt = self.fonts['small'].render(f"/ {WIN_SCORE}", True,
                                             PAL['ink_faint'])
            self.screen.blit(tgt, (px + 16 + sc.get_width(), y + 38))
            loc = self.fonts['small'].render(name, True, PAL['ink_soft'])
            self.screen.blit(loc, (px + 12, y + 58))
            img = self.assets.img.get(f'taxi{p}')
            if img:
                self.screen.blit(img, (px + pw - img.get_width() - 10, y + 12))
            rt = self.fonts['tiny'].render(
                f"{e.routes_owned(p)} routes", True, col)
            self.screen.blit(rt, (px + pw - rt.get_width() - 12, y + 50))
            bw = pw - 24
            pygame.draw.rect(self.screen, PAL['paper_edge'],
                             (px + 12, y + 76, bw, 5), border_radius=3)
            fillw = int(bw * min(1.0, score / WIN_SCORE))
            if fillw > 0:
                pygame.draw.rect(self.screen, col,
                                 (px + 12, y + 76, fillw, 5), border_radius=3)
            y += 96

        y += 4
        h = self.fonts['small'].render("REGION CONTROL", True, PAL['ink_faint'])
        self.screen.blit(h, (px, y))
        y += 20
        for reg in REGIONS:
            c1, c2, total = e.region_progress(reg['key'])
            claimed = e.region_claimed[reg['key']]
            pygame.draw.circle(self.screen, reg['colour'], (px + 7, y + 8), 6)
            nm = self.fonts['tiny'].render(reg['name'], True, PAL['ink_soft'])
            self.screen.blit(nm, (px + 20, y + 1))
            if claimed:
                ccol = PAL['p1'] if claimed == 1 else PAL['p2']
                tick = self.fonts['tiny'].render(f"P{claimed}", True, ccol)
                tx = px + pw - tick.get_width() - 14
                self.screen.blit(tick, (tx, y + 1))
                cx0 = px + pw - 10
                pygame.draw.lines(self.screen, ccol, False,
                                  [(cx0 - 4, y + 8), (cx0 - 1, y + 11),
                                   (cx0 + 4, y + 4)], 2)
            else:
                need = REGION_MAJORITY[reg['key']]
                tick = self.fonts['tiny'].render(f"{need} to claim", True,
                                                 PAL['ink_faint'])
                self.screen.blit(tick, (px + pw - tick.get_width(), y + 1))
            # segmented bar
            seg_w = (pw - 20) / total
            for i in range(total):
                rx = px + 20 + i * seg_w
                rect = pygame.Rect(int(rx), y + 16, int(seg_w) - 2, 6)
                if i < c1:
                    pygame.draw.rect(self.screen, PAL['p1_bright'], rect,
                                     border_radius=2)
                elif i < c1 + c2:
                    pygame.draw.rect(self.screen, PAL['p2_bright'], rect,
                                     border_radius=2)
                else:
                    pygame.draw.rect(self.screen, PAL['paper_edge'], rect,
                                     border_radius=2)
            y += 30

        y += 6
        h = self.fonts['small'].render("LATEST", True, PAL['ink_faint'])
        self.screen.blit(h, (px, y))
        y += 19
        for text, colour in self.feed:
            words = text
            if len(words) > 38:
                words = words[:36] + '…'
            s = self.fonts['tiny'].render(words, True, colour)
            self.screen.blit(s, (px, y))
            y += 17

        f = self.fonts['tiny'].render("[H] help   [R] restart   [M] sound   [ESC] menu",
                                      True, PAL['ink_faint'])
        self.screen.blit(f, (px + (pw - f.get_width()) // 2, WIN_H - 26))

    # ---- help overlay ----
    def _draw_help(self):
        ov = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        ov.fill((30, 28, 24, 210))
        self.screen.blit(ov, (0, 0))
        pw, ph = 760, 560
        panel = pygame.Rect(WIN_W // 2 - pw // 2, WIN_H // 2 - ph // 2, pw, ph)
        pygame.draw.rect(self.screen, PAL['panel'], panel, border_radius=20)
        pygame.draw.rect(self.screen, PAL['paper_edge'], panel, 3,
                         border_radius=20)
        x, y = panel.x + 36, panel.y + 26

        title = "How to run the province" if not self.intro else "Welcome to the rank"
        t = self.fonts['h1'].render(title, True, PAL['ink'])
        self.screen.blit(t, (x, y))
        y += 44

        def line(txt, col=PAL['ink_soft'], dy=24, font='body'):
            nonlocal y
            s = self.fonts[font].render(txt, True, col)
            self.screen.blit(s, (x, y))
            y += dy

        line(f"Goal — first association to {WIN_SCORE} points runs KZN.",
             PAL['ink'], 30, 'h2')
        line("Click a highlighted town to drive there. Hover any town for its name.")
        line("The number on a house is the customers waiting — land there to collect.")
        y += 8
        line("Routes — first taxi on a road owns it (it tints your colour).",
             PAL['ink'], 26, 'h2')
        line("Driving a rival's road pays them a 1-point toll. Own the roads they need.")
        y += 8
        line("Regions — collect from most towns in a region to claim it: +5, permanent.",
             PAL['ink'], 26, 'h2')
        line("The sidebar shows every region race. Fresh fares respawn every 4 rounds.")
        y += 10
        line("Hazards fire once, on the first taxi through — then the road is clear:",
             PAL['ink'], 30, 'h2')
        oy = y
        for i, (key, (nm, desc)) in enumerate(OBSTACLE_INFO.items()):
            cy = oy + i * 38
            draw_obstacle_sign(self.screen, self.fonts, key, x + 14, cy + 10)
            s = self.fonts['body'].render(f"{nm} — {desc}", True, PAL['ink_soft'])
            self.screen.blit(s, (x + 40, cy))
        y = oy + 3 * 38 + 8
        line("Eat a hazard, keep the road: crossing first still claims the route.",
             PAL['ink_soft'])
        y += 4
        hint = "click anywhere to start" if self.intro else "click anywhere to close · [H] reopens this"
        s = self.fonts['small'].render(hint, True, PAL['ink_faint'])
        self.screen.blit(s, (panel.centerx - s.get_width() // 2,
                             panel.bottom - 36))

    # ---- game over ----
    def _draw_game_over(self):
        e = self.engine
        ov = pygame.Surface((MAP_W, WIN_H), pygame.SRCALPHA)
        ov.fill((30, 28, 24, 200))
        self.screen.blit(ov, (0, 0))
        pw, ph = 540, 320
        cx = MAP_W // 2
        panel = pygame.Rect(cx - pw // 2, WIN_H // 2 - ph // 2, pw, ph)
        pygame.draw.rect(self.screen, PAL['panel'], panel, border_radius=20)
        if e.winner:
            col = PAL['p1'] if e.winner == 1 else PAL['p2']
            pygame.draw.rect(self.screen, col, panel, 4, border_radius=20)
            t = self.fonts['win'].render(f"PLAYER {e.winner} WINS", True, col)
            sub = "They run the province now."
        else:
            col = PAL['ink_soft']
            pygame.draw.rect(self.screen, col, panel, 4, border_radius=20)
            t = self.fonts['win'].render("DRAW", True, col)
            sub = "The rank went quiet."
        self.screen.blit(t, (cx - t.get_width() // 2, panel.y + 36))
        s = self.fonts['body'].render(sub, True, PAL['ink_soft'])
        self.screen.blit(s, (cx - s.get_width() // 2, panel.y + 96))

        stats = [
            ("points", e.p1_score, e.p2_score),
            ("routes owned", e.routes_owned(1), e.routes_owned(2)),
            ("regions", sum(1 for v in e.region_claimed.values() if v == 1),
                        sum(1 for v in e.region_claimed.values() if v == 2)),
        ]
        sy = panel.y + 140
        for label, a, b in stats:
            l1 = self.fonts['h2'].render(str(a), True, PAL['p1'])
            l2 = self.fonts['small'].render(label, True, PAL['ink_faint'])
            l3 = self.fonts['h2'].render(str(b), True, PAL['p2'])
            self.screen.blit(l1, (cx - 140 - l1.get_width() / 2, sy))
            self.screen.blit(l2, (cx - l2.get_width() / 2, sy + 4))
            self.screen.blit(l3, (cx + 140 - l3.get_width() / 2, sy))
            sy += 36
        s = self.fonts['small'].render("[R] rematch      [ESC] menu", True,
                                       PAL['ink_soft'])
        self.screen.blit(s, (cx - s.get_width() // 2, panel.bottom - 40))


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------
def main():
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Supa 16: Taxi Wars")
    clock = pygame.time.Clock()
    fonts = build_fonts()
    assets = Assets()
    settings = {'timer': False}

    state = 'menu'
    menu = MenuScreen(screen, fonts, assets, settings)
    game = None
    seen_intro = False

    while state != 'quit':
        dt = clock.tick(60) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                state = 'quit'
                break
            if state == 'menu':
                menu.handle_event(ev)
                if menu.result == 'exit':
                    state = 'quit'
                elif menu.result == MODE_PVP:
                    game = TaxiWarsGame(screen, fonts, assets, settings,
                                        mode=MODE_PVP,
                                        show_intro=not seen_intro)
                    seen_intro = True
                    state = 'game'
                    menu.result = None
                elif menu.result in (MODE_HUMAN_P1, MODE_HUMAN_P2):
                    req = menu.result
                    menu.result = None
                    hp = 1 if req == MODE_HUMAN_P1 else 2
                    agent = try_load_agent(screen, fonts)
                    if agent is not None:
                        game = TaxiWarsGame(screen, fonts, assets, settings,
                                            mode=req, agent=agent,
                                            human_player=hp,
                                            show_intro=not seen_intro)
                        seen_intro = True
                        state = 'game'
                elif menu.result is not None:
                    menu.result = None
            elif state == 'game':
                res = game.handle_event(ev)
                if res == 'menu':
                    state = 'menu'
                    menu = MenuScreen(screen, fonts, assets, settings)
                elif res is False:
                    state = 'quit'
        if state == 'menu':
            menu.update(dt)
            menu.render()
        elif state == 'game':
            game.update(dt)
            game.render()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
