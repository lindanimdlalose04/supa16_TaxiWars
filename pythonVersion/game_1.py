import os
import random 
import pygame
import sys
import math
from collections import deque


# CONSTANTS & LAYOUT


WIN_W, WIN_H   = 1280, 720
SIDEBAR_W      = 270
MAP_W          = WIN_W - SIDEBAR_W
MAP_H          = WIN_H
TURN_TIME      = 30.0   # seconds per turn

#
# COLOUR PALETTE
#
# Brand pink is reserved for menu/title accents.
# In-game the map uses asphalt-grey roads with white lane-line dashes,
# coloured taxis for players, and saturated regional colours for grouping.


C = {
    # Backgrounds
    'bg':            ( 14,  16,  28),   # deep navy
    'bg_grid':       ( 28,  32,  48),
    'panel':         ( 22,  24,  42),
    'panel_border':  ( 60,  64,  96),
    'panel_light':   ( 36,  40,  64),

    # Accent (hot pink magenta brand colour) — menu only
    'accent':        (220,  20, 180),
    'accent_dim':    (110,  10,  90),
    'accent_glow':   (255,  60, 210),

    # Players (P1 = cyan cab, P2 = hot-pink cab)
    'p1':            ( 50, 200, 235),   # cyan
    'p1_dark':       ( 20, 120, 150),
    'p2':            (240,  90, 160),   # hot pink
    'p2_dark':       (150,  40,  95),

    # Node base
    'node_fill':     ( 30,  34,  56),
    'node_border':   ( 90, 100, 140),

    # Valid-move ring
    'valid_ring':    (250, 240, 130),   # soft yellow — readable on asphalt

    # Roads (replacing the magenta "route" lines)
    'road_edge':     ( 32,  34,  44),   # darker shoulder/border
    'road_fill':     ( 68,  72,  86),   # asphalt
    'road_line':     (235, 220, 130),   # warm yellow lane markings
    'road_used':     ( 44,  46,  58),   # darker dimmed used road
    'road_used_line':( 90,  86,  72),   # dim used lane line

    # Text
    'white':         (245, 245, 250),
    'text_dim':      (190, 190, 215),
    'text_faint':    (120, 120, 155),

    # Obstacle colours
    'nkabi':         (255, 200,  40),   # yellow
    'super_nkabi':   (235,  60,  60),   # red
    'police':        ( 70, 160, 255),   # blue

    # Misc
    'gold':          (255, 200,   0),
    'timer_safe':    ( 70, 220, 110),
    'timer_warn':    (255, 190,   0),
    'timer_danger':  (235,  60,  60),
    'taxi_window':   (180, 220, 255),
    'taxi_outline':  ( 12,  14,  22),
}


# REGIONS sections

REGIONS = [
    # Northern Natal — the inland north. Gains Newcastle, Dundee, Ladysmith,
    # Ulundi. A warm amber/ochre.
    {'key': 'northern_natal', 'name': 'Northern Natal',
     'colour': (224, 158,  58),
     'nodes': [1, 2, 3, 19, 18, 4, 5, 6, 16], 'lx': 300, 'ly': 130},

    # Midlands — the green agricultural belt. Gains Nongoma, Pietermaritzburg,
    # Hammersdale; loses the northern towns to Northern Natal.
    {'key': 'midlands',       'name': 'Midlands',
     'colour': ( 92, 178, 104),
     'nodes': [7, 8, 27, 28, 17, 9, 25], 'lx': 250, 'ly': 350},

    # North Coast — the coastal strip north of Durban. Gains Empangeni and
    # Richards Bay. A warm coral red.
    {'key': 'north_coast',    'name': 'North Coast',
     'colour': (214,  88,  92),
     'nodes': [14, 15, 11, 12, 13], 'lx': 560, 'ly': 360},

    # Durban Metro — the city. Gains Margate; loses PMB and Hammersdale to
    # Midlands. A muted violet.
    {'key': 'durban',         'name': 'Durban Metro',
     'colour': (146, 110, 214),
     'nodes': [29, 10, 21], 'lx': 600, 'ly': 540},

    # South Coast — the southern seaboard. Loses Margate.
    {'key': 'south_coast',    'name': 'South Coast',
     'colour': ( 70, 130, 210),
     'nodes': [30, 26, 23, 22, 24, 20], 'lx': 300, 'ly': 665},
]

NODE_REGION = {}
for _reg in REGIONS:
    for _nid in _reg['nodes']:
        NODE_REGION[_nid] = _reg


# NODES  (30 towns/nodes)


NODES_DATA = [
    # Northern Natal
    {'id':  1, 'name': 'Jozini',            'x': 710, 'y':  80, 'customers': 1},
    {'id':  2, 'name': 'Pongola',           'x': 560, 'y':  60, 'customers': 2},
    {'id':  3, 'name': 'Vryheid',           'x': 310, 'y':  80, 'customers': 5},
    {'id': 19, 'name': 'Mkuze',             'x': 730, 'y': 160, 'customers': 1},
    {'id': 18, 'name': 'Hluhluwe',          'x': 650, 'y': 200, 'customers': 2},
    {'id': 12, 'name': 'Empangeni',         'x': 640, 'y': 290, 'customers': 5},
    {'id': 13, 'name': 'Richards Bay',      'x': 750, 'y': 340, 'customers': 2},
    # Midlands
    {'id':  4, 'name': 'Newcastle',         'x':  90, 'y':  90, 'customers': 3},
    {'id':  5, 'name': 'Dundee',            'x': 190, 'y': 190, 'customers': 3},
    {'id':  6, 'name': 'Ladysmith',         'x':  60, 'y': 280, 'customers': 3},
    {'id': 27, 'name': 'Bergville',         'x': 170, 'y': 310, 'customers': 4},
    {'id':  7, 'name': 'Estcourt',          'x':  70, 'y': 450, 'customers': 2},
    {'id':  8, 'name': 'Mooi River',        'x': 290, 'y': 420, 'customers': 2},
    {'id': 28, 'name': 'Greytown',          'x': 310, 'y': 300, 'customers': 3},
    {'id': 16, 'name': 'Ulundi',            'x': 380, 'y': 170, 'customers': 3},
    # North Coast
    {'id': 14, 'name': 'Eshowe',            'x': 500, 'y': 210, 'customers': 3},
    {'id': 15, 'name': 'Melmoth',           'x': 500, 'y': 310, 'customers': 4},
    {'id': 17, 'name': 'Nongoma',           'x': 500, 'y': 400, 'customers': 3},
    {'id': 11, 'name': 'Stanger',           'x': 640, 'y': 430, 'customers': 4},
    # Durban Metro
    {'id': 25, 'name': 'Hammersdale',       'x': 210, 'y': 400, 'customers': 5},
    {'id':  9, 'name': 'Pietermaritzburg',  'x': 380, 'y': 500, 'customers': 5},
    {'id': 29, 'name': 'Pinetown',          'x': 540, 'y': 560, 'customers': 5},
    {'id': 10, 'name': 'Durban',            'x': 720, 'y': 510, 'customers': 5},
    # South Coast
    {'id': 30, 'name': 'Underberg',         'x': 230, 'y': 560, 'customers': 3},
    {'id': 26, 'name': 'iXopo',             'x': 160, 'y': 610, 'customers': 2},
    {'id': 23, 'name': 'Harding',           'x': 320, 'y': 620, 'customers': 3},
    {'id': 22, 'name': 'Port Edward',       'x': 410, 'y': 700, 'customers': 1},
    {'id': 24, 'name': 'Kokstad',           'x':  60, 'y': 700, 'customers': 1},
    {'id': 20, 'name': 'Port Shepstone',    'x': 590, 'y': 680, 'customers': 3},
    {'id': 21, 'name': 'Margate',           'x': 680, 'y': 610, 'customers': 1},
]

ORIGINAL_CUSTOMERS = {n['id']: n['customers'] for n in NODES_DATA}

# ROUTES


ROUTES_DATA = [
    {'from':  1, 'to':  2, 'obstacle': None,  'cleared': False},
    {'from':  2, 'to': 14, 'obstacle': 'NK',  'cleared': False},
    {'from':  1, 'to': 19, 'obstacle': None,  'cleared': False},
    {'from': 19, 'to': 18, 'obstacle': None,  'cleared': False},
    {'from':  4, 'to':  6, 'obstacle': 'SNK', 'cleared': False},
    {'from':  4, 'to':  5, 'obstacle': None,  'cleared': False},
    {'from':  3, 'to':  5, 'obstacle': None,  'cleared': False},
    {'from':  5, 'to': 27, 'obstacle': 'NK',  'cleared': False},
    {'from':  6, 'to': 25, 'obstacle': 'NK',  'cleared': False},
    {'from':  6, 'to':  7, 'obstacle': None,  'cleared': False},
    {'from':  2, 'to': 16, 'obstacle': None,  'cleared': False},
    {'from': 16, 'to': 27, 'obstacle': 'POL', 'cleared': False},
    {'from': 12, 'to': 15, 'obstacle': 'SNK', 'cleared': False},
    {'from': 18, 'to': 15, 'obstacle': 'NK',  'cleared': False},
    {'from': 14, 'to': 15, 'obstacle': None,  'cleared': False},
    {'from': 12, 'to': 13, 'obstacle': None,  'cleared': False},
    {'from': 12, 'to': 17, 'obstacle': None,  'cleared': False},
    {'from': 17, 'to':  9, 'obstacle': 'NK',  'cleared': False},
    {'from': 16, 'to': 28, 'obstacle': None,  'cleared': False},
    {'from': 28, 'to':  8, 'obstacle': 'SNK', 'cleared': False},
    {'from': 26, 'to': 24, 'obstacle': None,  'cleared': False},
    {'from': 26, 'to':  7, 'obstacle': None,  'cleared': False},
    {'from': 26, 'to': 23, 'obstacle': 'NK',  'cleared': False},
    {'from': 23, 'to':  8, 'obstacle': None,  'cleared': False},
    {'from':  8, 'to':  9, 'obstacle': None,  'cleared': False},
    {'from': 24, 'to': 22, 'obstacle': None,  'cleared': False},
    {'from': 20, 'to': 22, 'obstacle': None,  'cleared': False},
    {'from': 20, 'to': 29, 'obstacle': 'NK',  'cleared': False},
    {'from': 13, 'to': 11, 'obstacle': None,  'cleared': False},
    {'from':  9, 'to': 10, 'obstacle': 'POL', 'cleared': False},
    {'from': 21, 'to': 10, 'obstacle': None,  'cleared': False},
    {'from': 30, 'to':  7, 'obstacle': 'POL', 'cleared': False},
    {'from': 30, 'to':  8, 'obstacle': None,  'cleared': False},
]

# Game modes 
MODE_PVP      = 'pvp'        # Human vs Human
MODE_TRAINING = 'training'   # Headless ML training (no window)
MODE_ML_VS    = 'ml_vs'      # ML agent vs Human (future)
MODE_HUMAN_P1 = 'human_p1'   # Human plays as P1, AI plays as P2
MODE_HUMAN_P2 = 'human_p2'   # Human plays as P2, AI plays as P1


# HELPER FUNCTIONS

def find_node(nodes, node_id):
    for n in nodes:
        if n['id'] == node_id:
            return n
    return None


def get_connected(routes, node_id):
    connections = []
    for r in routes:
        if r['from'] == node_id:
            connections.append({'to': r['to'], 'obs': r['obstacle'], 'route': r})
        elif r['to'] == node_id:
            connections.append({'to': r['from'], 'obs': r['obstacle'], 'route': r})
    return connections


def is_connected(routes, a, b):
    for r in routes:
        if (r['from'] == a and r['to'] == b) or (r['from'] == b and r['to'] == a):
            return True, r
    return False, None


def compute_transform():
    min_x = min(n['x'] for n in NODES_DATA)
    max_x = max(n['x'] for n in NODES_DATA)
    min_y = min(n['y'] for n in NODES_DATA)
    max_y = max(n['y'] for n in NODES_DATA)
    rx = max_x - min_x
    ry = max_y - min_y
    px = rx + rx * 0.18
    py = ry + ry * 0.18
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    MAP_PAD = 50
    aw = MAP_W - MAP_PAD * 2
    ah = MAP_H - MAP_PAD * 2
    ms = min(aw / px, ah / py)
    mox = MAP_W / 2 - cx * ms
    moy = MAP_H / 2 - cy * ms
    return ms, mox, moy


def tp(x, y, ms, mox, moy):
    """Transform game coord → screen coord."""
    return x * ms + mox, y * ms + moy


def lerp_color(a, b, t):
    """Linear interpolate between two RGB tuples."""
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))



# MENU SCREEN

class MenuScreen:
    """Standalone main menu rendered before the game starts."""

    ITEMS = [
        ('Solo Play  (Human vs Human)',   MODE_PVP),
        ('Play vs AI  (you = P1)',        MODE_HUMAN_P1),
        ('Play vs AI  (you = P2)',        MODE_HUMAN_P2),
        ('ML Training  (headless)',       MODE_TRAINING),
        ('ML vs Human  (coming soon)',    MODE_ML_VS),
        ('Exit',                          'exit'),
    ]

    def __init__(self, screen, fonts):
        self.screen  = screen
        self.fonts   = fonts
        self.sel     = 0          # highlighted item index
        self.anim_t  = 0.0
        self.result  = None       # set when user confirms

    #  helpers 

    def _draw_text_centered(self, text, font, colour, cy):
        surf = font.render(text, True, colour)
        self.screen.blit(surf, (WIN_W // 2 - surf.get_width() // 2, cy))

    #  public 

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.sel = (self.sel - 1) % len(self.ITEMS)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.sel = (self.sel + 1) % len(self.ITEMS)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.result = self.ITEMS[self.sel][1]
            elif event.key == pygame.K_ESCAPE:
                self.result = 'exit'

        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            for i, rect in enumerate(self._item_rects()):
                if rect.collidepoint(mx, my):
                    self.sel = i

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for i, rect in enumerate(self._item_rects()):
                if rect.collidepoint(mx, my):
                    self.sel = i
                    self.result = self.ITEMS[i][1]

    def _item_rects(self):
        rects = []
        base_y = WIN_H // 2 - 40
        for i in range(len(self.ITEMS)):
            r = pygame.Rect(WIN_W // 2 - 220, base_y + i * 68, 440, 52)
            rects.append(r)
        return rects

    def update(self, dt):
        self.anim_t += dt

    def render(self):
        self.screen.fill(C['bg'])

        #  animated dot-grid background 
        for gx in range(0, WIN_W, 40):
            for gy in range(0, WIN_H, 40):
                pygame.draw.rect(self.screen, (40, 30, 70), (gx - 1, gy - 1, 2, 2))

        #  pulsing accent circle 
        pulse = (math.sin(self.anim_t * 1.4) + 1) / 2
        r_big = int(260 + pulse * 30)
        glow_surf = pygame.Surface((r_big * 2, r_big * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*C['accent'], int(18 + pulse * 12)),
                           (r_big, r_big), r_big)
        self.screen.blit(glow_surf, (WIN_W // 2 - r_big, WIN_H // 2 - r_big))

        #  title 
        title_col = lerp_color(C['accent'], C['accent_glow'], pulse)
        self._draw_text_centered("Yuppie Games",    self.fonts['menu_title'],    title_col,  120)
        self._draw_text_centered("SUPA 16 TAXI  WARS",   self.fonts['menu_subtitle'], C['white'], 184)
        self._draw_text_centered(
            "Use  \u2191\u2193  or mouse to select  \u00b7  Enter to confirm",
            self.fonts['menu_hint'], C['text_faint'], 260)

        #  menu items 
        rects = self._item_rects()
        for i, ((label, _mode), rect) in enumerate(zip(self.ITEMS, rects)):
            active = (i == self.sel)
            # Background tile
            bg_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            if active:
                bg_surf.fill((*C['accent'], 55))
            else:
                bg_surf.fill((*C['panel'], 180))
            self.screen.blit(bg_surf, rect.topleft)

            # Border
            border_col = C['accent'] if active else C['panel_border']
            pygame.draw.rect(self.screen, border_col, rect, 2, border_radius=10)

            # Disabled overlay for unimplemented items
            disabled = (_mode == MODE_ML_VS)

            # Label
            if disabled:
                col = C['text_faint']
            elif active:
                col = C['white']
            else:
                col = C['text_dim']

            txt_surf = self.fonts['menu_item'].render(label, True, col)
            self.screen.blit(txt_surf,
                             (rect.centerx - txt_surf.get_width() // 2,
                              rect.centery - txt_surf.get_height() // 2))

            # Selection arrow
            if active and not disabled:
                arr = self.fonts['menu_item'].render(">", True, C['accent_glow'])
                self.screen.blit(arr, (rect.left - 28, rect.centery - arr.get_height() // 2))

        #  version footer 
        self._draw_text_centered("v2.0  \u00b7  Yuppie ML Games",
                                 self.fonts['menu_hint'], C['text_faint'], WIN_H - 30)

        pygame.display.flip()


# 
# GAME ENGINE  (logic only) no pygame references
# 

class GameEngine:
    """
    Pure game logic.  Can be used headlessly for ML training.
    Rendering is handled by TaxiWarsGame.
    """

    WIN_SCORE = 20

    def __init__(self):
        import copy
        self.nodes  = copy.deepcopy(NODES_DATA)
        self.routes = copy.deepcopy(ROUTES_DATA)
        self.reset()

    def reset(self):
        for n in self.nodes:
            n['customers'] = ORIGINAL_CUSTOMERS[n['id']]
        for r in self.routes:
            r['cleared'] = False

        # Randomise starting positions: pick two distinct nodes uniformly at random.
        # This prevents the agent from memorising fixed opening sequences and
        # forces it to learn positional reasoning that generalises across games.
        self.p1_pos, self.p2_pos = random.sample([n['id'] for n in self.nodes], 2)
        
        self.p1_score     = 0
        self.p2_score     = 0
        self.current_player = 1
        self.turn_blocked = {1: False, 2: False}
        self.game_over    = False
        self.winner       = 0
        self.move_count   = 0
        self.trail_p1     = deque(maxlen=6)
        self.trail_p2     = deque(maxlen=6)

        # Region ownership tracking.
        # node_owner[node_id] = 0 (unclaimed), 1 (P1), or 2 (P2)
        #   — updated to current_player whenever that player collects > 0
        #     customers from a node.
        # region_owner[region_key] = 0 / 1 / 2
        #   — set to player N when ALL nodes in the region have node_owner == N,
        #     reset to 0 if any node in the region flips to the opponent.
        self.node_owner   = {n['id']: 0 for n in self.nodes}
        self.region_owner = {reg['key']: 0 for reg in REGIONS}

        self._update_valid_moves()
        return self.get_state()

    #  state  

    def get_state(self):
        return {
            'p1_pos':       self.p1_pos,
            'p2_pos':       self.p2_pos,
            'p1_score':     self.p1_score,
            'p2_score':     self.p2_score,
            'current_player': self.current_player,
            'turn_blocked': self.turn_blocked.copy(),
            'valid_moves':  self.valid_moves.copy(),
            'customers':    {n['id']: n['customers'] for n in self.nodes},
            'routes_cleared': {f"{r['from']}-{r['to']}": r['cleared'] for r in self.routes},
            'game_over':    self.game_over,
            'winner':       self.winner,
            'node_owner':   self.node_owner.copy(),
            'region_owner': self.region_owner.copy(),
        }

    def _update_valid_moves(self):
        pos = self.p1_pos if self.current_player == 1 else self.p2_pos
        opp = self.p2_pos if self.current_player == 1 else self.p1_pos
        self.valid_moves = [
            c['to'] for c in get_connected(self.routes, pos) if c['to'] != opp
        ]

    def is_valid_move(self, node_id):
        return node_id in self.valid_moves

    #  obstacle helpers 

    def _apply_nkabi(self, player):
        if player == 1:
            self.p1_score = max(0, self.p1_score - 2)
        else:
            self.p2_score = max(0, self.p2_score - 2)
        return f"NKABI! P{player} loses 2 points!"

    def _apply_super_nkabi(self, player, came_from):
        """
        Send the mover back along their trail.

        Intent: 'back 3 nodes' means three of the player's *prior* stops,
        NOT counting the square they just departed from (otherwise 'back 3'
        only feels like 'back 2' to a player — they expect to end up
        somewhere they remember being, not at their immediately-previous
        square).

        Fallback when there is no prior history: send them back to their
        starting town (Jozini for P1, Kokstad for P2). If a came_from
        exists but there's no deeper history, we use came_from as a last
        resort rather than teleporting to Jozini/Kokstad.
        """
        trail   = self.trail_p1 if player == 1 else self.trail_p2
        history = list(trail)  # newest-first, does NOT include came_from
        steps   = min(3, len(history))

        if steps > 0:
            target = history[steps - 1]
            msg    = f"SUPER NKABI! P{player} sent back {steps} stops"
        elif came_from is not None:
            # No prior history — just bounce back to where they came from.
            target = came_from
            msg    = f"SUPER NKABI! P{player} bounced back"
        else:
            # Truly nothing — fall back to canonical start.
            target = 1 if player == 1 else 24
            msg    = f"SUPER NKABI! P{player} sent back to start!"

        if player == 1:
            self.p1_pos   = target
            self.p1_score = max(0, self.p1_score - 1)
        else:
            self.p2_pos   = target
            self.p2_score = max(0, self.p2_score - 1)
        return msg, target

    def _apply_police(self, player):
        self.turn_blocked[player] = True
        return f"POLICE! P{player} skips next turn!"

    def _refresh_region_for_node(self, node_id):
        """
        Recompute region ownership for the region containing `node_id`.

        Returns the player number (1 or 2) if a region was *newly* claimed
        on this update, otherwise 0. "Newly claimed" means the region's
        owner changed from {0 or opponent} to the player who just collected.

        Implements the design-doc rule: a region is owned by player N when
        every node in that region has been collected by N. If the opponent
        collects from any node, ownership transfers (or is lost).
        """
        reg = NODE_REGION.get(node_id)
        if reg is None:
            return 0

        rkey = reg['key']
        owners = [self.node_owner[nid] for nid in reg['nodes']]
        previous = self.region_owner[rkey]

        # Region is owned iff all nodes share the same non-zero owner
        if owners and all(o == owners[0] and o != 0 for o in owners):
            new_owner = owners[0]
        else:
            new_owner = 0

        self.region_owner[rkey] = new_owner

        # Only count it as a "claim event" if ownership changed *to* a player
        if new_owner != 0 and new_owner != previous:
            return new_owner
        return 0

    def _check_win(self):
        if self.p1_score >= self.WIN_SCORE:
            self.game_over = True
            self.winner    = 1
        elif self.p2_score >= self.WIN_SCORE:
            self.game_over = True
            self.winner    = 2
        return self.game_over

    #  core move 

    def do_move(self, target_id):
        """
        Execute a move.  Returns a result dict:
          {
            'ok':       bool,
            'msg':      str,
            'msg_type': 'good'|'bad'|'warn'|'info',
            'flash':    node_id | None,
            'gained':   int,      # customers collected this move
            'obstacle': str|None, # 'NK'|'SNK'|'POL'|None
            'snk_target': int|None,  # node sent back to (SNK only)
          }
        """
        R = {'ok': False, 'msg': '', 'msg_type': 'info',
             'flash': None, 'gained': 0, 'obstacle': None, 'snk_target': None,
             'region_claimed_by': 0}

        if self.game_over:
            R['msg'] = "Game already over."
            return R

        # Blocked turn
        if self.turn_blocked[self.current_player]:
            R['ok'] = True
            R['msg'] = f"P{self.current_player} blocked — turn skipped."
            R['msg_type'] = 'warn'
            self.turn_blocked[self.current_player] = False
            self.current_player = 3 - self.current_player
            self._update_valid_moves()
            return R

        # Stalemate
        if not self.valid_moves:
            R['ok'] = True
            R['msg'] = f"STALEMATE — P{self.current_player} has no moves."
            R['msg_type'] = 'warn'
            self.current_player = 3 - self.current_player
            self._update_valid_moves()
            return R

        # Range check
        if target_id < 1 or target_id > 30:
            R['msg'] = "Choose a node number 1-30."
            R['msg_type'] = 'bad'
            return R

        cp  = self.current_player
        pos = self.p1_pos if cp == 1 else self.p2_pos
        opp = self.p2_pos if cp == 1 else self.p1_pos

        connected, route = is_connected(self.routes, pos, target_id)
        if not connected:
            R['msg'] = f"Node {target_id} is not connected here."
            R['msg_type'] = 'bad'
            return R
        if target_id == opp:
            R['msg'] = "That node is occupied by your opponent!"
            R['msg_type'] = 'bad'
            return R

        # Execute move (commit position change).
        # IMPORTANT: we do NOT add `pos` to the trail yet — SNK needs to know
        # where the player came from without it being double-counted, and if
        # SNK fires the player gets teleported away anyway. The trail is
        # updated at the end of this method once the final landing node
        # is known.
        if cp == 1:
            self.p1_pos = target_id
        else:
            self.p2_pos = target_id
        came_from = pos  # the node we stepped off of on this move

        route['cleared'] = True
        self.move_count += 1
        R['ok']    = True
        R['flash'] = target_id

        # Collect customers at the destination
        gained_msg = ""
        node = find_node(self.nodes, target_id)
        if node['customers'] > 0:
            gained = node['customers']
            node['customers'] = 0
            if cp == 1:
                self.p1_score += gained
            else:
                self.p2_score += gained
            R['gained'] = gained
            # Mark this node as owned by the collecting player
            self.node_owner[target_id] = cp
            reg   = NODE_REGION.get(target_id)
            rname = f" [{reg['name']}]" if reg else ""
            gained_msg     = f"P{cp} +{gained} pts \u00b7 {node['name']}{rname}"
            R['msg']       = gained_msg
            R['msg_type']  = 'good'

            # Re-evaluate region ownership for the region this node belongs to.
            # A region is "owned" by player N iff every node in the region has
            # node_owner == N. We also detect *changes* of ownership so the
            # reward function can give a one-off bonus.
            R['region_claimed_by'] = self._refresh_region_for_node(target_id)
        else:
            R['msg']      = f"P{cp} moved to {node['name']}"
            R['msg_type'] = 'info'

        # Obstacle resolution. If both a customer gain AND an obstacle happened
        # on the same move, combine them into one message so the player isn't
        # left thinking only the obstacle happened.
        obs = route['obstacle']
        R['obstacle'] = obs
        snk_fired = False
        if obs == 'NK':
            obs_msg       = self._apply_nkabi(cp)
            R['msg']      = f"{gained_msg}  \u2014  {obs_msg}" if gained_msg else obs_msg
            R['msg_type'] = 'bad'
        elif obs == 'SNK':
            obs_msg, snk_t = self._apply_super_nkabi(cp, came_from=came_from)
            R['msg']        = f"{gained_msg}  \u2014  {obs_msg}" if gained_msg else obs_msg
            R['msg_type']   = 'bad'
            R['flash']      = snk_t
            R['snk_target'] = snk_t
            snk_fired       = True
        elif obs == 'POL':
            obs_msg       = self._apply_police(cp)
            R['msg']      = f"{gained_msg}  \u2014  {obs_msg}" if gained_msg else obs_msg
            R['msg_type'] = 'warn'

        # Now update the trail. If SNK fired, the player got teleported
        # somewhere else entirely; their trail jumps from `came_from` to the
        # landing node without the intermediate hop. We still push
        # `came_from` so the trail reflects where they were standing before
        # this whole event.
        # If no SNK, the player is sitting at `target_id` and `came_from` is
        # the most recent step they came from.
        (self.trail_p1 if cp == 1 else self.trail_p2).appendleft(came_from)

        # Win check
        if self._check_win():
            R['msg']      = f"PLAYER {self.winner} WINS!"
            R['msg_type'] = 'good'
            return R

        # Switch turn
        next_p = 3 - cp
        if self.turn_blocked[next_p]:
            self.turn_blocked[next_p] = False
        else:
            self.current_player = next_p

        self._update_valid_moves()
        return R


# GAME SCREEN  (rendering + input)

class TaxiWarsGame:
    """Renders the game and forwards input to GameEngine."""

    def __init__(self, screen, fonts, mode=MODE_PVP, agent=None, human_player=None):
        self.screen  = screen
        self.fonts   = fonts
        self.mode    = mode
        self.engine  = GameEngine()
        self.ms, self.mox, self.moy = compute_transform()

        # AI opponent (None in pure PvP mode)
        # When set, `agent` is a trained QLearningAgent and `human_player`
        # is 1 or 2 — indicating which side the human controls.
        # The AI plays whichever side is NOT the human.
        self.agent        = agent
        self.human_player = human_player
        self.ai_player    = (3 - human_player) if human_player else None
        # Timestamp (in seconds since game start) of when the current AI
        # turn became "ready to move". Used to enforce a 1s thinking pause.
        self.ai_turn_started_at = None
        self.ai_think_delay     = 3.0   # seconds of "thinking" before the AI moves
        self._game_time         = 0.0   # accumulated dt for AI timing

        #  visual state 
        self.anim_t     = 0.0
        self.node_flash = {}      # node_id → remaining seconds
        self.message    = ""
        self.msg_type   = "info"
        self.msg_timer  = 0.0

        # input 
        self.number_input = ""
        self.input_timer  = 0.0

        #  countdown timer 
        self.turn_time_left = TURN_TIME
        self.timer_active   = True   # paused when game over / blocked

        if self.agent is not None:
            who = "P1" if self.human_player == 1 else "P2"
            self._show_msg(
                f"You are {who}.  AI thinks for ~1s before moving.", "info", 4.0)
        else:
            self._show_msg("P1 starts at Jozini  \u00b7  P2 starts at Kokstad",
                           "info", 4.0)

    #  internal helpers 

    def _show_msg(self, text, msg_type="info", dur=2.5):
        self.message   = text
        self.msg_type  = msg_type
        self.msg_timer = dur

    def _flash(self, node_id, dur=1.2):
        self.node_flash[node_id] = dur

    def _handle_result(self, R):
        """Process result dict from GameEngine.do_move()."""
        if not R['ok']:
            self._show_msg(R['msg'], R['msg_type'], 2.0)
            return
        if R['flash']:
            self._flash(R['flash'], 1.5 if R['obstacle'] == 'SNK' else 0.9)
        self._show_msg(R['msg'], R['msg_type'],
                       3.0 if R['msg_type'] in ('bad', 'warn') else 2.0)
        # Reset turn timer on successful move
        self.turn_time_left = TURN_TIME

    # public 

    def handle_event(self, event):
        """Return False to quit."""
        e = self.engine
        if event.type == pygame.QUIT:
            return False

        # Always-allowed keys (menu, restart) even on the AI's turn
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return 'menu'          # back to menu

            if event.key == pygame.K_r:
                e.reset()
                self.node_flash.clear()
                self.number_input   = ""
                self.turn_time_left = TURN_TIME
                self.ai_turn_started_at = None
                self._show_msg("New game!  P1 at Jozini  \u00b7  P2 at Kokstad", "info", 4.0)
                return True

            if e.game_over:
                return True

            # In PvAI mode, ignore move input while it's the AI's turn.
            # The human's keyboard should only affect their own turns.
            if self.agent is not None and e.current_player == self.ai_player:
                return True

            if event.unicode.isdigit():
                self.number_input += event.unicode
                self.input_timer   = 1.2
                return True

            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.number_input:
                    self._commit_input()
                return True

            if event.key == pygame.K_BACKSPACE and self.number_input:
                self.number_input = self.number_input[:-1]
                self.input_timer  = 0.8 if self.number_input else 0.0
                return True

        return True

    def _commit_input(self):
        try:
            n = int(self.number_input)
            self.number_input = ""
            self.input_timer  = 0.0
            R = self.engine.do_move(n)
            self._handle_result(R)
        except ValueError:
            self.number_input = ""
            self.input_timer  = 0.0

    def update(self, dt):
        self.anim_t      += dt
        self._game_time  += dt

        # Message fade
        if self.msg_timer > 0:
            self.msg_timer -= dt

        # Input auto-confirm
        if self.input_timer > 0:
            self.input_timer -= dt
            if self.input_timer <= 0 and self.number_input:
                self._commit_input()

        # Node flash decay
        to_del = [k for k, v in self.node_flash.items() if v - dt <= 0]
        for k in to_del:
            del self.node_flash[k]
        for k in list(self.node_flash):
            self.node_flash[k] -= dt

        e = self.engine

        # ── AI turn (PvAI only) ────────────────────────────────────────────
        # If we have an AI and it's its turn, count down the thinking delay
        # and then make a move. The countdown timer is paused while the
        # AI thinks so the human isn't punished for the AI's pause.
        if (self.agent is not None
                and not e.game_over
                and e.current_player == self.ai_player):
            if self.ai_turn_started_at is None:
                # First frame of this AI turn — start the thinking clock.
                self.ai_turn_started_at = self._game_time
            elif self._game_time - self.ai_turn_started_at >= self.ai_think_delay:
                # Enough time has passed — let the AI play.
                self._take_ai_turn()
                self.ai_turn_started_at = None
            # Don't run the countdown timer while the AI is thinking.
            return
        else:
            # Either we're in PvP, or it's the human's turn in PvAI.
            self.ai_turn_started_at = None

        # Countdown timer (human players only)
        if not e.game_over and self.timer_active:
            self.turn_time_left -= dt
            if self.turn_time_left <= 0:
                self.turn_time_left = TURN_TIME
                # Time expired → forfeit turn (pass)
                R = e.do_move(-1)   # invalid move forces a pass
                # Actually just force skip by switching player
                self._show_msg(
                    f"P{e.current_player} ran out of time — turn forfeited!",
                    "warn", 3.0)
                e.current_player = 3 - e.current_player
                e._update_valid_moves()
                self.turn_time_left = TURN_TIME

    def _take_ai_turn(self):
        """Ask the loaded Q-learning agent for a move and execute it."""
        # Local imports so this file still works if state_encoder isn't on
        # the path (e.g. pure PvP usage on a fresh checkout)
        from state_encoder import encode

        e = self.engine
        if e.game_over or not e.valid_moves:
            return

        # Encode the current state from the AI's perspective.
        state_dict = e.get_state()
        state_key  = encode(state_dict, perspective=self.ai_player)

        # Pick the best action (greedy — no exploration in play mode).
        try:
            action = self.agent.choose_action(state_key, e.valid_moves,
                                              greedy=True)
        except Exception as ex:
            self._show_msg(f"AI error: {ex}", "bad", 4.0)
            return

        if action is None:
            return  # no moves available — engine will handle stalemate

        # Apply the move just like a human turn would.
        R = e.do_move(action)
        self._handle_result(R)

    # ── rendering ─────────────────────────────────────────────────────────────

    def render(self):
        self.screen.fill(C['bg'])
        self._draw_grid()
        self._draw_region_labels()
        self._draw_routes()
        self._draw_nodes()
        self._draw_sidebar()
        self._draw_timer()
        self._draw_message()
        self._draw_game_over()
        pygame.display.flip()

    # ── grid background ───────────────────────────────────────────────────────

    def _draw_grid(self):
        for gx in range(0, MAP_W, 48):
            for gy in range(0, WIN_H, 48):
                pygame.draw.rect(self.screen, C['bg_grid'], (gx - 1, gy - 1, 2, 2))

    # ── region labels ─────────────────────────────────────────────────────────

    def _draw_region_labels(self):
        """
        Region labels are drawn beneath the nodes (in z-order) at a low
        alpha. We also skip labels that would overlap any node, so they
        never visually 'collide' with town circles.
        """
        font = self.fonts['region']
        # Pre-compute node screen positions so we can avoid drawing labels on top
        node_screen = [tp(n['x'], n['y'], self.ms, self.mox, self.moy)
                       for n in self.engine.nodes]

        for reg in REGIONS:
            sx, sy = tp(reg['lx'], reg['ly'], self.ms, self.mox, self.moy)
            if not (10 < sx < MAP_W - 10 and 10 < sy < WIN_H - 10):
                continue
            # Skip if any node is within 30px — keeps labels off taxi nodes
            too_close = any((sx - nx) ** 2 + (sy - ny) ** 2 < 30 ** 2
                            for nx, ny in node_screen)
            if too_close:
                continue
            surf = font.render(reg['name'].upper(), True, reg['colour'])
            surf.set_alpha(120)
            self.screen.blit(surf, (sx - surf.get_width() // 2, sy))

    # ── obstacle symbol on a route ────────────────────────────────────────────

    def _draw_obstacle(self, obs, cx, cy):
        """Draw a road-sign style obstacle marker at the midpoint of a road."""
        r = 11
        cx, cy = int(cx), int(cy)
        # Dark backing so the sign stands out against the asphalt
        pygame.draw.circle(self.screen, C['taxi_outline'], (cx, cy), r + 3)
        if obs == 'NK':
            col, sym = C['nkabi'], 'N'
            pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
            pygame.draw.polygon(self.screen, col, pts)
            pygame.draw.polygon(self.screen, C['taxi_outline'], pts, 2)
        elif obs == 'SNK':
            col, sym = C['super_nkabi'], 'S'
            pygame.draw.circle(self.screen, col, (cx, cy), r)
            pygame.draw.circle(self.screen, C['taxi_outline'], (cx, cy), r, 2)
        elif obs == 'POL':
            col, sym = C['police'], 'P'
            pygame.draw.rect(self.screen, col, (cx - r, cy - r, r * 2, r * 2),
                             border_radius=3)
            pygame.draw.rect(self.screen, C['taxi_outline'],
                             (cx - r, cy - r, r * 2, r * 2), 2, border_radius=3)
        else:
            return
        txt = self.fonts['obs'].render(sym, True, C['taxi_outline'])
        self.screen.blit(txt, (cx - txt.get_width() // 2,
                               cy - txt.get_height() // 2))

    # ── routes ────────────────────────────────────────────────────────────────

    def _draw_routes(self):
        """
        Render each route as a three-layer 'road':
          1. dark shoulder/edge stripe (slightly wider)
          2. asphalt fill (main width)
          3. dashed yellow centre line

        Cleared (used) routes use dimmed tones so the player can see at a
        glance which segments have already been driven.
        """
        ms = self.ms
        # Pre-compute screen positions for every node (small win)
        pos_cache = {}
        for n in self.engine.nodes:
            pos_cache[n['id']] = tp(n['x'], n['y'], ms, self.mox, self.moy)

        # Road widths scale gently with the map zoom so they look proportionate
        edge_w = max(8, int(10 * ms / 1.0))
        fill_w = max(6, edge_w - 2)

        for r in self.engine.routes:
            if r['from'] not in pos_cache or r['to'] not in pos_cache:
                continue
            x1, y1 = pos_cache[r['from']]
            x2, y2 = pos_cache[r['to']]
            p1 = (int(x1), int(y1))
            p2 = (int(x2), int(y2))

            if r['cleared']:
                edge_col = C['road_edge']
                fill_col = C['road_used']
                line_col = C['road_used_line']
            else:
                edge_col = C['road_edge']
                fill_col = C['road_fill']
                line_col = C['road_line']

            # Shoulder + asphalt
            pygame.draw.line(self.screen, edge_col, p1, p2, edge_w)
            pygame.draw.line(self.screen, fill_col, p1, p2, fill_w)

            # Dashed centre line — skip drawing the dashes near the endpoints
            # and around the obstacle marker so it doesn't look messy.
            dx, dy = (x2 - x1), (y2 - y1)
            length = math.hypot(dx, dy)
            if length < 8:
                continue
            ux, uy = dx / length, dy / length

            dash_len  = 9
            gap_len   = 7
            step      = dash_len + gap_len
            # Stay clear of the node circle on each end
            end_pad   = 18
            obs_clear = 16 if r['obstacle'] and not r['cleared'] else 0

            t = end_pad
            mid = length / 2
            while t + dash_len < length - end_pad:
                # Skip dashes that would overlap the obstacle marker
                if obs_clear and abs(t + dash_len / 2 - mid) < obs_clear:
                    t += step
                    continue
                ax = x1 + ux * t
                ay = y1 + uy * t
                bx = x1 + ux * (t + dash_len)
                by = y1 + uy * (t + dash_len)
                pygame.draw.line(self.screen, line_col,
                                 (int(ax), int(ay)), (int(bx), int(by)), 2)
                t += step

            # Obstacle marker on uncleared routes
            if r['obstacle'] and not r['cleared']:
                self._draw_obstacle(r['obstacle'],
                                    (x1 + x2) / 2, (y1 + y2) / 2)

    # ── nodes ─────────────────────────────────────────────────────────────────

    def _draw_taxi(self, cx, cy, body_col, body_dark, label):
        """
        Draw a small top-down taxi sprite centred at (cx, cy).

        The taxi has a coloured body with a slightly darker outline, two
        pale 'windows' (front/back), a yellow taxi sign on the roof, two
        dark wheel arches on the sides, and a centred number plate.
        Drawn on a per-call SRCALPHA surface so transparency works.
        """
        W, H = 30, 22
        surf = pygame.Surface((W + 4, H + 4), pygame.SRCALPHA)
        sx, sy = 2, 2  # padding inside the surface

        # Wheel arches (darker body colour, drawn first so the body covers them)
        pygame.draw.rect(surf, body_dark, (sx - 1, sy + 3, W + 2, 4))
        pygame.draw.rect(surf, body_dark, (sx - 1, sy + H - 7, W + 2, 4))

        # Body
        body_rect = pygame.Rect(sx, sy, W, H)
        pygame.draw.rect(surf, body_col, body_rect, border_radius=4)
        pygame.draw.rect(surf, C['taxi_outline'], body_rect, 1, border_radius=4)

        # Windows (front-left / back-right pair, top-down view)
        win_col = C['taxi_window']
        pygame.draw.rect(surf, win_col, (sx + 6, sy + 4, W - 12, 4), border_radius=1)
        pygame.draw.rect(surf, win_col, (sx + 6, sy + H - 8, W - 12, 4), border_radius=1)

        # Taxi roof sign (gold)
        sign_w = 8
        pygame.draw.rect(surf, C['gold'],
                         (sx + W // 2 - sign_w // 2, sy + H // 2 - 2, sign_w, 4))
        pygame.draw.rect(surf, C['taxi_outline'],
                         (sx + W // 2 - sign_w // 2, sy + H // 2 - 2, sign_w, 4), 1)

        # Player label (1 or 2) on the roof sign
        lbl = self.fonts['marker'].render(str(label), True, C['taxi_outline'])
        surf.blit(lbl,
                  (sx + W // 2 - lbl.get_width() // 2,
                   sy + H // 2 - lbl.get_height() // 2 - 1))

        self.screen.blit(surf,
                         (int(cx) - (W + 4) // 2,
                          int(cy) - (H + 4) // 2))

    def _draw_nodes(self):
        e  = self.engine
        NR = 16   # node radius — slightly larger so customer badges sit better
        font_id   = self.fonts['node_id']
        font_name = self.fonts['node_name']
        font_cust = self.fonts['node_cust']

        for node in e.nodes:
            sx, sy = tp(node['x'], node['y'], self.ms, self.mox, self.moy)
            sx, sy = int(sx), int(sy)
            nid     = node['id']
            is_p1   = (nid == e.p1_pos)
            is_p2   = (nid == e.p2_pos)
            is_valid = (nid in e.valid_moves and not e.game_over)

            reg        = NODE_REGION.get(nid)
            reg_colour = reg['colour'] if reg else (100, 100, 100)

            # ── flash effect (gold halo, fades) ───────────────────────────
            if nid in self.node_flash:
                fa = int((self.node_flash[nid] / 1.5) * 110)
                fl_surf = pygame.Surface(((NR + 16) * 2, (NR + 16) * 2),
                                         pygame.SRCALPHA)
                pygame.draw.circle(fl_surf, (*C['gold'], fa),
                                   (NR + 16, NR + 16), NR + 16)
                self.screen.blit(fl_surf, (sx - NR - 16, sy - NR - 16))

            # ── valid-move pulse glow (yellow ring) ───────────────────────
            if is_valid:
                pulse = (math.sin(self.anim_t * 4) + 1) / 2
                glow_r = NR + 9 + int(pulse * 3)
                glow_surf = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4),
                                           pygame.SRCALPHA)
                pygame.draw.circle(glow_surf,
                                   (*C['valid_ring'], int(40 + pulse * 50)),
                                   (glow_r + 2, glow_r + 2), glow_r)
                self.screen.blit(glow_surf,
                                 (sx - glow_r - 2, sy - glow_r - 2))

            # ── region ring (subtle on normal nodes, brighter when valid) ─
            ring_alpha = 220 if is_valid else 150
            ring_surf = pygame.Surface(((NR + 5) * 2, (NR + 5) * 2),
                                       pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (*reg_colour, ring_alpha),
                               (NR + 5, NR + 5), NR + 4, 2)
            self.screen.blit(ring_surf, (sx - NR - 5, sy - NR - 5))

            # ── node fill ─────────────────────────────────────────────────
            pygame.draw.circle(self.screen, C['node_fill'], (sx, sy), NR)

            # ── inner border ──────────────────────────────────────────────
            if is_valid:
                pygame.draw.circle(self.screen, C['valid_ring'],
                                   (sx, sy), NR, 2)
            else:
                pygame.draw.circle(self.screen, C['node_border'],
                                   (sx, sy), NR, 1)

            # ── node ID ───────────────────────────────────────────────────
            id_txt = font_id.render(str(nid), True, C['white'])
            self.screen.blit(id_txt, (sx - id_txt.get_width() // 2,
                                      sy - id_txt.get_height() // 2 + 1))

            # ── town name ─────────────────────────────────────────────────
            name = node['name']
            if len(name) > 12:
                name = name[:11] + '~'
            nm_txt = font_name.render(name, True, C['white'])
            nm_txt.set_alpha(210)
            # Soft dark backing for legibility on top of roads
            nm_bg = pygame.Surface(
                (nm_txt.get_width() + 6, nm_txt.get_height() + 2),
                pygame.SRCALPHA)
            nm_bg.fill((*C['bg'], 180))
            self.screen.blit(nm_bg,
                             (sx - nm_txt.get_width() // 2 - 3,
                              sy + NR + 4))
            self.screen.blit(nm_txt, (sx - nm_txt.get_width() // 2,
                                      sy + NR + 5))

            # ── customer badge ────────────────────────────────────────────
            if node['customers'] > 0:
                bx, by = sx + NR - 2, sy - NR + 2
                pygame.draw.circle(self.screen, C['gold'], (bx, by), 9)
                pygame.draw.circle(self.screen, C['taxi_outline'], (bx, by), 9, 1)
                ct = font_cust.render(str(node['customers']),
                                      True, C['taxi_outline'])
                self.screen.blit(ct, (bx - ct.get_width() // 2,
                                      by - ct.get_height() // 2))

            # ── taxi sprite for the occupying player ──────────────────────
            # Drawn AFTER the node so it sits visually on top of the town.
            if is_p1:
                self._draw_taxi(sx, sy - NR - 14, C['p1'], C['p1_dark'], 1)
            if is_p2:
                self._draw_taxi(sx, sy - NR - 14, C['p2'], C['p2_dark'], 2)

    # ── sidebar ───────────────────────────────────────────────────────────────

    def _draw_sidebar(self):
        e   = self.engine
        sx  = MAP_W
        px  = sx + 12
        pw  = SIDEBAR_W - 24

        # Panel background
        panel_surf = pygame.Surface((SIDEBAR_W, WIN_H), pygame.SRCALPHA)
        panel_surf.fill((*C['panel'], 245))
        self.screen.blit(panel_surf, (sx, 0))
        pygame.draw.line(self.screen, C['accent'], (sx, 0), (sx, WIN_H), 2)

        y = 14

        # Title
        t1 = self.fonts['sidebar_title'].render("KZN ROUTE", True, C['accent'])
        self.screen.blit(t1, (px + (pw - t1.get_width()) // 2, y));  y += 30
        t2 = self.fonts['sidebar_sub'].render("TAXI WARS", True, C['accent_dim'])
        self.screen.blit(t2, (px + (pw - t2.get_width()) // 2, y));  y += 18
        pygame.draw.rect(self.screen, C['accent'], (sx + 8, y, SIDEBAR_W - 16, 1)); y += 10

        # Current-turn banner
        if not e.game_over:
            cp   = e.current_player
            pcol = C['p1'] if cp == 1 else C['p2']
            bn   = pygame.Surface((pw, 28), pygame.SRCALPHA)
            bn.fill((*pcol, 40))
            self.screen.blit(bn, (px, y))
            pygame.draw.rect(self.screen, pcol, (px, y, pw, 28), 2, border_radius=5)
            bt = self.fonts['sidebar_turn'].render(f"PLAYER {cp}'S TURN", True, pcol)
            self.screen.blit(bt, (px + (pw - bt.get_width()) // 2, y + 6));  y += 40

        # Score cards
        def score_card(player, score, cy):
            pcol  = C['p1']      if player == 1 else C['p2']
            pdark = C['p1_dark'] if player == 1 else C['p2_dark']
            pos  = e.p1_pos if player == 1 else e.p2_pos
            pn   = find_node(e.nodes, pos)
            pname = pn['name'][:14] + '.' if pn and len(pn['name']) > 14 else (pn['name'] if pn else '?')
            preg  = NODE_REGION.get(pos)
            rc    = preg['colour'] if preg else C['white']
            rname = preg['name']   if preg else ''

            card = pygame.Surface((pw, 80), pygame.SRCALPHA)
            card.fill((*pcol, 20))
            self.screen.blit(card, (px, cy))
            pygame.draw.rect(self.screen, pcol, (px, cy, pw, 80), 2, border_radius=6)

            # Small taxi icon (top-right corner of the card)
            self._draw_taxi(px + pw - 22, cy + 16, pcol, pdark, player)

            pl = self.fonts['score_label'].render(f"PLAYER {player}", True, pcol)
            self.screen.blit(pl, (px + 8, cy + 7))

            sc = self.fonts['score_big'].render(f"{score} pts", True, C['white'])
            self.screen.blit(sc, (px + 8, cy + 24))

            loc = self.fonts['score_loc'].render(f"@ {pname}", True, C['text_dim'])
            self.screen.blit(loc, (px + 8, cy + 50))

            # Region pill
            rp = pygame.Surface((pw - 16, 12), pygame.SRCALPHA)
            rp.fill((*rc, 60))
            self.screen.blit(rp, (px + 8, cy + 64))
            rn = self.fonts['score_loc'].render(rname, True, rc)
            self.screen.blit(rn, (px + 8 + (pw - 16 - rn.get_width()) // 2, cy + 65))

            # Progress bar (win at 20)
            pct = min(score / 20, 1.0)
            bar_w = pw - 16
            pygame.draw.rect(self.screen, C['panel_light'], (px + 8, cy + 74, bar_w, 4), border_radius=2)
            if pct > 0:
                pygame.draw.rect(self.screen, pcol, (px + 8, cy + 74, int(bar_w * pct), 4), border_radius=2)

        score_card(1, e.p1_score, y);  y += 94
        score_card(2, e.p2_score, y);  y += 98

        wc = self.fonts['score_loc'].render("First to 20 points wins", True, C['text_faint'])
        self.screen.blit(wc, (px + (pw - wc.get_width()) // 2, y));  y += 18
        pygame.draw.rect(self.screen, C['accent'], (sx + 8, y, SIDEBAR_W - 16, 1)); y += 8

        # Region legend
        rl = self.fonts['section_head'].render("REGIONS", True, C['text_faint'])
        self.screen.blit(rl, (px + (pw - rl.get_width()) // 2, y)); y += 14
        for reg in REGIONS:
            pygame.draw.circle(self.screen, reg['colour'], (px + 6, y + 6), 5)
            rt = self.fonts['legend'].render(reg['name'], True, C['text_dim'])
            self.screen.blit(rt, (px + 16, y));  y += 14
        y += 4
        pygame.draw.rect(self.screen, C['accent'], (sx + 8, y, SIDEBAR_W - 16, 1)); y += 8

        # Input display
        rl2 = self.fonts['section_head'].render("OBSTACLES", True, C['text_faint'])
        self.screen.blit(rl2, (px + (pw - rl2.get_width()) // 2, y)); y += 14

        def obs_row(col, sym, label, desc, oy):
            pygame.draw.circle(self.screen, col, (px + 7, oy + 7), 7)
            st = self.fonts['obs_sym'].render(sym, True, (0, 0, 0))
            self.screen.blit(st, (px + 7 - st.get_width() // 2, oy + 7 - st.get_height() // 2))
            lt = self.fonts['legend'].render(label, True, C['white'])
            self.screen.blit(lt, (px + 18, oy))
            dt = self.fonts['legend'].render(desc, True, C['text_faint'])
            self.screen.blit(dt, (px + 18, oy + 12)); 

        obs_row(C['nkabi'],       'N', 'NKABI',       'lose 2 pts',    y); y += 28
        obs_row(C['super_nkabi'], 'S', 'SUPER NKABI', 'sent back 3',   y); y += 28
        obs_row(C['police'],      'P', 'POLICE',      'skip 1 turn',   y); y += 28

        # Mini road legend — show open vs used road samples
        # Open road
        pygame.draw.line(self.screen, C['road_edge'],
                         (px, y + 7), (px + 28, y + 7), 6)
        pygame.draw.line(self.screen, C['road_fill'],
                         (px, y + 7), (px + 28, y + 7), 4)
        pygame.draw.line(self.screen, C['road_line'],
                         (px + 6, y + 7), (px + 13, y + 7), 1)
        pygame.draw.line(self.screen, C['road_line'],
                         (px + 17, y + 7), (px + 24, y + 7), 1)
        ot = self.fonts['legend'].render("= open road", True, C['text_dim'])
        self.screen.blit(ot, (px + 33, y + 2)); y += 16
        # Used road (dimmed)
        pygame.draw.line(self.screen, C['road_edge'],
                         (px, y + 7), (px + 28, y + 7), 6)
        pygame.draw.line(self.screen, C['road_used'],
                         (px, y + 7), (px + 28, y + 7), 4)
        ut = self.fonts['legend'].render("= used road", True, C['text_faint'])
        self.screen.blit(ut, (px + 33, y + 2)); y += 18

        pygame.draw.rect(self.screen, C['accent'], (sx + 8, y, SIDEBAR_W - 16, 1)); y += 6

        # Input field
        if self.number_input:
            inf = pygame.Surface((pw, 30), pygame.SRCALPHA)
            inf.fill((*C['accent'], 30))
            self.screen.blit(inf, (px, y))
            pygame.draw.rect(self.screen, C['accent'], (px, y, pw, 30), 2, border_radius=4)
            it = self.fonts['sidebar_turn'].render(f"\u2192 {self.number_input}", True, C['accent'])
            self.screen.blit(it, (px + (pw - it.get_width()) // 2, y + 8)); y += 38
        else:
            ht = self.fonts['legend'].render("Type node # + Enter to move", True, C['text_faint'])
            self.screen.blit(ht, (px + (pw - ht.get_width()) // 2, y)); y += 22

        # Bottom controls
        y = WIN_H - 26
        pygame.draw.rect(self.screen, C['accent'], (sx + 8, y - 6, SIDEBAR_W - 16, 1))
        ct = self.fonts['legend'].render("[R] Restart   [ESC] Menu", True, C['text_faint'])
        self.screen.blit(ct, (px + (pw - ct.get_width()) // 2, y))

        # Move counter (top-left of map)
        mc = self.fonts['legend'].render(f"Round: {self.engine.move_count // 2}", True, C['text_faint'])
        self.screen.blit(mc, (10, 8))

    # ── countdown timer (top-RIGHT corner of map area) ────────────────────────

    def _draw_timer(self):
        e = self.engine
        if e.game_over:
            return

        t    = self.turn_time_left
        frac = t / TURN_TIME   # 1.0 → 0.0

        # Color: green → yellow → red
        if frac > 0.4:
            col = C['timer_safe']
        elif frac > 0.2:
            col = lerp_color(C['timer_warn'], C['timer_safe'],
                             (frac - 0.2) / 0.2)
        else:
            col = lerp_color(C['timer_danger'], C['timer_warn'],
                             frac / 0.2)

        # Arc background
        cx, cy = MAP_W - 44, 44
        r_out, r_in = 32, 22

        # Background ring
        pygame.draw.circle(self.screen, C['panel_light'], (cx, cy), r_out)
        pygame.draw.circle(self.screen, C['bg'],          (cx, cy), r_in)

        # Filled arc (pygame has no arc-fill, so we draw a pie and cut the centre)
        # We approximate with many small rectangles using a surface mask approach.
        # Simpler: draw a pygame.draw.arc for the border, and fill with segments.
        arc_w = 8
        # Bounding rect for arc
        arc_rect = pygame.Rect(cx - r_out + arc_w // 2,
                               cy - r_out + arc_w // 2,
                               (r_out - arc_w // 2) * 2,
                               (r_out - arc_w // 2) * 2)
        end_angle   = math.pi / 2               # top (12 o'clock in pygame coords)
        start_angle = end_angle - frac * 2 * math.pi
        pygame.draw.arc(self.screen, col, arc_rect, start_angle, end_angle, arc_w)

        # Seconds text inside ring
        secs = math.ceil(t)
        st   = self.fonts['timer'].render(str(secs), True, col)
        self.screen.blit(st, (cx - st.get_width() // 2,
                              cy - st.get_height() // 2))

        # Label below ring
        lb = self.fonts['legend'].render("secs", True, C['text_faint'])
        self.screen.blit(lb, (cx - lb.get_width() // 2, cy + r_out + 2))

        # Player indicator ring
        pcol = C['p1'] if e.current_player == 1 else C['p2']
        pygame.draw.circle(self.screen, pcol, (cx, cy), r_out + 4, 2)

    # ── message bar ───────────────────────────────────────────────────────────

    def _draw_message(self):
        if self.msg_timer <= 0:
            return
        alpha = min(self.msg_timer, 1.0)
        if self.msg_type == 'good':
            col = C['p1']
        elif self.msg_type == 'bad':
            col = C['super_nkabi']
        elif self.msg_type == 'warn':
            col = C['nkabi']
        else:
            col = C['accent']

        bw = MAP_W - 40
        # If the message contains a separator we put it on two lines so
        # combined customer-gain + obstacle messages stay readable.
        font = self.fonts['msg']
        sep = "  \u2014  "
        if sep in self.message:
            lines = [s.strip() for s in self.message.split(sep, 1)]
            bh    = 52
        else:
            lines = [self.message]
            bh    = 36

        bx, by = 20, WIN_H - bh - 12
        bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
        bg.fill((*C['bg'], int(alpha * 230)))
        self.screen.blit(bg, (bx, by))
        pygame.draw.rect(self.screen, (*col, int(alpha * 200)),
                         (bx, by, bw, bh), 2, border_radius=6)

        line_h = font.get_height()
        total_h = line_h * len(lines)
        top = by + (bh - total_h) // 2
        for i, line in enumerate(lines):
            txt = font.render(line, True, (*C['white'], int(alpha * 255)))
            self.screen.blit(txt,
                             (bx + (bw - txt.get_width()) // 2,
                              top + i * line_h))

    # ── game over overlay ─────────────────────────────────────────────────────

    def _draw_game_over(self):
        e = self.engine
        if not e.game_over:
            return
        pulse = (math.sin(self.anim_t * 2) + 1) / 2
        col   = C['p1'] if e.winner == 1 else C['p2']
        cx, cy = MAP_W // 2, WIN_H // 2

        ov = pygame.Surface((MAP_W, WIN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 200))
        self.screen.blit(ov, (0, 0))

        pw, ph = 500, 260
        ps = pygame.Surface((pw, ph), pygame.SRCALPHA)
        ps.fill((*C['panel'], 240))
        self.screen.blit(ps, (cx - pw // 2, cy - ph // 2))
        pygame.draw.rect(self.screen, (*col, int(120 + pulse * 80)),
                         (cx - pw // 2, cy - ph // 2, pw, ph), 3, border_radius=16)

        wt = self.fonts['win_title'].render(f"PLAYER {e.winner} WINS!", True, col)
        self.screen.blit(wt, (cx - wt.get_width() // 2, cy - 100))

        sc = self.fonts['sidebar_turn'].render(
            f"P1: {e.p1_score} pts   |   P2: {e.p2_score} pts", True, C['text_dim'])
        self.screen.blit(sc, (cx - sc.get_width() // 2, cy + 10))

        ra = int(100 + pulse * 60)
        rt = self.fonts['sidebar_sub'].render("Press  R  to play again   |   ESC for menu",
                                              True, (*C['white'], ra))
        self.screen.blit(rt, (cx - rt.get_width() // 2, cy + 70))


# ===============================================================================
# MAIN APPLICATION
# ===============================================================================

def build_fonts():
    """Create all font objects in one place."""
    return {
        # Menu
        'menu_title':    pygame.font.Font(None, 72),
        'menu_subtitle': pygame.font.Font(None, 36),
        'menu_item':     pygame.font.Font(None, 28),
        'menu_hint':     pygame.font.Font(None, 18),
        # Sidebar
        'sidebar_title': pygame.font.Font(None, 30),
        'sidebar_sub':   pygame.font.Font(None, 16),
        'sidebar_turn':  pygame.font.Font(None, 20),
        'score_label':   pygame.font.Font(None, 14),
        'score_big':     pygame.font.Font(None, 26),
        'score_loc':     pygame.font.Font(None, 13),
        'section_head':  pygame.font.Font(None, 13),
        'legend':        pygame.font.Font(None, 13),
        'obs_sym':       pygame.font.Font(None, 13),
        # Map
        'node_id':       pygame.font.Font(None, 14),
        'node_name':     pygame.font.Font(None, 11),
        'node_cust':     pygame.font.Font(None, 13),
        'marker':        pygame.font.Font(None, 13),
        'region':        pygame.font.Font(None, 13),
        'obs':           pygame.font.Font(None, 13),
        # HUD
        'timer':         pygame.font.Font(None, 22),
        'msg':           pygame.font.Font(None, 16),
        'win_title':     pygame.font.Font(None, 56),
    }


def _try_load_agent(screen, fonts, pkl_path=None):
    """
    Attempt to load a trained Q-learning agent from disk.

    Looks in a list of likely locations relative to the script so the same
    code works on Windows, macOS, and Linux without edits.
    On success: return the QLearningAgent instance.
    On failure: draw an on-screen error message for ~3 seconds, then
                return None so the caller stays in the menu.
    """
    try:
        from agent import QLearningAgent
    except Exception as ex:
        agent_class_err = ex
    else:
        agent_class_err = None

    # Candidate paths to try, in priority order.
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [pkl_path] if pkl_path else []
    candidates += [
        os.path.join(here, "runs", "run1", "agent.pkl"),
        os.path.join(os.getcwd(), "runs", "run1", "agent.pkl"),
        os.path.join(here, "agent.pkl"),
    ]
    candidates = [c for c in candidates if c]

    if agent_class_err is None:
        for path in candidates:
            if os.path.exists(path):
                try:
                    return QLearningAgent.load(path)
                except Exception as ex:
                    msg = [
                        "Failed to load trained agent:",
                        str(ex),
                        "",
                        "Try re-running training:",
                        "    python train.py --episodes 10000",
                    ]
                    break
        else:
            msg = [
                "Trained agent not found.  Looked in:",
            ] + [f"  {p}" for p in candidates] + [
                "",
                "Run training first:",
                "    python train.py --episodes 10000",
            ]
    else:
        msg = [
            "Could not import agent module:",
            str(agent_class_err),
        ]

    # Render the error message centred for ~5 seconds.
    clock = pygame.time.Clock()
    end_at = pygame.time.get_ticks() + 3000
    while pygame.time.get_ticks() < end_at:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return None
        screen.fill(C['bg'])
        title = fonts['win_title'].render("AI not available", True, (255, 200, 80))
        screen.blit(title, (WIN_W // 2 - title.get_width() // 2, WIN_H // 3))
        y = WIN_H // 3 + 90
        for line in msg:
            surf = fonts['menu_item'].render(line, True, C['text_faint'])
            screen.blit(surf, (WIN_W // 2 - surf.get_width() // 2, y))
            y += 36
        hint = fonts['menu_hint'].render(
            "(Returning to menu... press any key to skip)", True, C['text_dim'])
        screen.blit(hint, (WIN_W // 2 - hint.get_width() // 2, WIN_H - 60))
        pygame.display.flip()
        clock.tick(60)
    return None


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("KZN Route: Taxi Wars")
    clock  = pygame.time.Clock()
    fonts  = build_fonts()

    #state machine:
    state  = 'menu'
    menu   = MenuScreen(screen, fonts)
    game   = None

    while state != 'quit':
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                state = 'quit'
                break

            if state == 'menu':
                menu.handle_event(event)
                if menu.result == 'exit':
                    state = 'quit'
                elif menu.result == MODE_PVP:
                    game  = TaxiWarsGame(screen, fonts, mode=MODE_PVP)
                    state = 'game'
                    menu.result = None
                elif menu.result in (MODE_HUMAN_P1, MODE_HUMAN_P2):
                    # Load the trained agent before creating the game so that
                    # a missing/broken pkl doesn't leave us in a half-built
                    # state. On error we just stay in the menu and show a
                    # short message.
                    requested = menu.result
                    menu.result = None
                    human_player = 1 if requested == MODE_HUMAN_P1 else 2
                    agent_obj = _try_load_agent(screen, fonts)
                    if agent_obj is not None:
                        game = TaxiWarsGame(
                            screen, fonts, mode=requested,
                            agent=agent_obj, human_player=human_player)
                        state = 'game'
                elif menu.result == MODE_TRAINING:
                    # Headless training — placeholder message for now
                    # (the actual RL agent will plug in here in Part 2)
                    menu.result = None
                    print("[INFO] ML Training mode selected — agent not yet implemented.")
                    print("[INFO] Use GameEngine() directly in your training script.")
                elif menu.result is not None:
                    menu.result = None   # unimplemented, ignore

            elif state == 'game':
                result = game.handle_event(event)
                if result == 'menu':
                    state = 'menu'
                    menu  = MenuScreen(screen, fonts)
                elif result is False:
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
