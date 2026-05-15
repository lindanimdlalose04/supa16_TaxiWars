
import pygame
import sys
import math
from collections import deque


# CONSTANTS & LAYOUT


WIN_W, WIN_H   = 1280, 720
SIDEBAR_W      = 270
MAP_W          = WIN_W - SIDEBAR_W
MAP_H          = WIN_H
TURN_TIME      = 15.0   # seconds per turn

#
# COLOUR PALETTE


C = {
    # Backgrounds 
    'bg':            (10,  8, 22),
    'panel':         (18, 14, 36),
    'panel_border':  (50, 42, 80),
    'panel_light':   (32, 26, 58),

    # Accent (hot pink magenta brand colour) 
    'accent':        (220,  20, 1),
    'accent_dim':    (110,  10,  90),
    'accent_glow':   (255,  60, 210),

    #  Players 
    'p1':            ( 40, 230,  90),   # green
    'p2':            (240,  90,  20),   # orange

    #  Node base colours 
    'node_fill':     (12,  10, 46),
    'node_border':   (80,  70,120),

    # Valid-move ring  (white)
    'valid_ring':    (255, 255, 255),   # <-- key fix: no longer magenta

    # Routes
    'route_active':  (180,  10,145),
    'route_used':    ( 55,  50, 80),

    # text of UI
    'white':         (255, 255, 255),
    'text_dim':      (180, 170, 210),
    'text_faint':    (100,  90,140),

    # Obstacle colours
    'nkabi':         (255, 210,  10),   # gold/yellow
    'super_nkabi':   (230,  40,  40),   # red
    'police':        ( 60, 150, 255),   # blue

    # Misc
    'gold':          (255, 200,   0),
    'timer_safe':    ( 40, 210,  80),
    'timer_warn':    (255, 190,   0),
    'timer_danger':  (230,  40,  40),
}


# REGIONS sections

REGIONS = [
    {'key': 'northern_natal', 'name': 'Northern Natal',
     'colour': (210, 130,  20),
     'nodes': [1, 2, 3, 19, 18, 12, 13], 'lx': 630, 'ly': 120},

    {'key': 'midlands',       'name': 'Midlands',
     'colour': ( 50, 160,  60),
     'nodes': [4, 5, 6, 7, 8, 27, 28, 16], 'lx': 185, 'ly': 300},

    {'key': 'north_coast',    'name': 'North Coast',
     'colour': (190,  35,  50),
     'nodes': [14, 15, 17, 11], 'lx': 555, 'ly': 350},

    {'key': 'durban',         'name': 'Durban Metro',
     'colour': (120,  80, 200),
     'nodes': [25, 9, 29, 10], 'lx': 510, 'ly': 510},

    {'key': 'south_coast',    'name': 'South Coast',
     'colour': ( 30,  90, 200),
     'nodes': [30, 26, 23, 22, 24, 20, 21], 'lx': 370, 'ly': 665},
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
        ('Solo Play  (Human vs Human)',  MODE_PVP),
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

        self.p1_pos       = 1
        self.p2_pos       = 24
        self.p1_score     = 0
        self.p2_score     = 0
        self.current_player = 1
        self.turn_blocked = {1: False, 2: False}
        self.game_over    = False
        self.winner       = 0
        self.move_count   = 0
        self.trail_p1     = deque(maxlen=6)
        self.trail_p2     = deque(maxlen=6)

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

    def _apply_super_nkabi(self, player):
        trail  = self.trail_p1 if player == 1 else self.trail_p2
        steps  = min(3, len(trail))
        if steps == 0:
            target = 1 if player == 1 else 24
            msg    = f"SUPER NKABI! P{player} sent back to start!"
        else:
            target = trail[steps - 1]
            msg    = f"SUPER NKABI! P{player} sent back {steps} nodes"
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
             'flash': None, 'gained': 0, 'obstacle': None, 'snk_target': None}

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

        # execute move
        (self.trail_p1 if cp == 1 else self.trail_p2).appendleft(pos)
        if cp == 1:
            self.p1_pos = target_id
        else:
            self.p2_pos = target_id

        route['cleared'] = True
        self.move_count += 1
        R['ok']    = True
        R['flash'] = target_id

        # Collect customers
        node = find_node(self.nodes, target_id)
        if node['customers'] > 0:
            gained = node['customers']
            node['customers'] = 0
            if cp == 1:
                self.p1_score += gained
            else:
                self.p2_score += gained
            R['gained'] = gained
            reg   = NODE_REGION.get(target_id)
            rname = f" [{reg['name']}]" if reg else ""
            R['msg']      = f"P{cp} +{gained} pts \u00b7 {node['name']}{rname}"
            R['msg_type'] = 'good'
        else:
            R['msg']      = f"P{cp} moved to {node['name']}"
            R['msg_type'] = 'info'

        # Obstacle
        obs = route['obstacle']
        R['obstacle'] = obs
        if obs == 'NK':
            obs_msg       = self._apply_nkabi(cp)
            R['msg']      = obs_msg
            R['msg_type'] = 'bad'
        elif obs == 'SNK':
            obs_msg, snk_t = self._apply_super_nkabi(cp)
            R['msg']        = obs_msg
            R['msg_type']   = 'bad'
            R['flash']      = snk_t
            R['snk_target'] = snk_t
        elif obs == 'POL':
            obs_msg       = self._apply_police(cp)
            R['msg']      = obs_msg
            R['msg_type'] = 'warn'

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

    def __init__(self, screen, fonts, mode=MODE_PVP):
        self.screen  = screen
        self.fonts   = fonts
        self.mode    = mode
        self.engine  = GameEngine()
        self.ms, self.mox, self.moy = compute_transform()

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

        self._show_msg("P1 starts at Jozini  \u00b7  P2 starts at Kokstad", "info", 4.0)

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

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return 'menu'          # back to menu

            if event.key == pygame.K_r:
                e.reset()
                self.node_flash.clear()
                self.number_input  = ""
                self.turn_time_left = TURN_TIME
                self._show_msg("New game!  P1 at Jozini  \u00b7  P2 at Kokstad", "info", 4.0)
                return True

            if e.game_over:
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
        self.anim_t += dt

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

        # Countdown timer
        e = self.engine
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
        for gx in range(0, MAP_W, 40):
            for gy in range(0, WIN_H, 40):
                pygame.draw.rect(self.screen, (40, 32, 72), (gx - 1, gy - 1, 2, 2))

    # ── region labels ─────────────────────────────────────────────────────────

    def _draw_region_labels(self):
        font = self.fonts['region']
        for reg in REGIONS:
            sx, sy = tp(reg['lx'], reg['ly'], self.ms, self.mox, self.moy)
            if 10 < sx < MAP_W - 10 and 10 < sy < WIN_H - 10:
                surf = font.render(reg['name'].upper(), True, reg['colour'])
                surf.set_alpha(130)
                self.screen.blit(surf, (sx - surf.get_width() // 2, sy))

    # ── obstacle symbol on a route ────────────────────────────────────────────

    def _draw_obstacle(self, obs, cx, cy):
        r = 9
        cx, cy = int(cx), int(cy)
        pygame.draw.circle(self.screen, C['bg'], (cx, cy), r + 2)
        if obs == 'NK':
            col  = C['nkabi']
            sym  = 'N'
            pts  = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
            pygame.draw.polygon(self.screen, col, pts)
            pygame.draw.polygon(self.screen, (0, 0, 0), pts, 1)
        elif obs == 'SNK':
            col = C['super_nkabi']
            sym = 'S'
            pygame.draw.circle(self.screen, col, (cx, cy), r)
        elif obs == 'POL':
            col = C['police']
            sym = 'P'
            pygame.draw.rect(self.screen, col, (cx - r, cy - r, r * 2, r * 2))
        else:
            return
        txt = self.fonts['obs'].render(sym, True, (0, 0, 0))
        self.screen.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))

    # ── routes ────────────────────────────────────────────────────────────────

    def _draw_routes(self):
        for r in self.engine.routes:
            a = find_node(self.engine.nodes, r['from'])
            b = find_node(self.engine.nodes, r['to'])
            if not a or not b:
                continue
            x1, y1 = tp(a['x'], a['y'], self.ms, self.mox, self.moy)
            x2, y2 = tp(b['x'], b['y'], self.ms, self.mox, self.moy)
            col = C['route_used'] if r['cleared'] else C['route_active']
            pygame.draw.line(self.screen, col, (int(x1), int(y1)), (int(x2), int(y2)), 3)
            if r['obstacle'] and not r['cleared']:
                mx = (x1 + x2) / 2
                my = (y1 + y2) / 2
                self._draw_obstacle(r['obstacle'], mx, my)

    # ── nodes ─────────────────────────────────────────────────────────────────

    def _draw_nodes(self):
        e  = self.engine
        NR = 15   # node radius
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

            # ── valid-move pulse glow (white, alpha-based) ────────────────
            if is_valid:
                pulse = (math.sin(self.anim_t * 4) + 1) / 2
                glow_r = NR + 8 + int(pulse * 4)
                glow_surf = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*C['valid_ring'], int(30 + pulse * 30)),
                                   (glow_r + 2, glow_r + 2), glow_r)
                self.screen.blit(glow_surf, (sx - glow_r - 2, sy - glow_r - 2))

            # ── flash effect ──────────────────────────────────────────────
            if nid in self.node_flash:
                fa = int((self.node_flash[nid] / 1.5) * 110)
                fl_surf = pygame.Surface(((NR + 14) * 2, (NR + 14) * 2), pygame.SRCALPHA)
                pygame.draw.circle(fl_surf, (*C['gold'], fa),
                                   (NR + 14, NR + 14), NR + 14)
                self.screen.blit(fl_surf, (sx - NR - 14, sy - NR - 14))

            # ── region outer ring (always drawn) ──────────────────────────
            pygame.draw.circle(self.screen, reg_colour, (sx, sy), NR + 4, 2)

            # ── node fill ─────────────────────────────────────────────────
            if is_p1:
                fill_surf = pygame.Surface((NR * 2, NR * 2), pygame.SRCALPHA)
                pygame.draw.circle(fill_surf, (*C['p1'], 60),
                                   (NR, NR), NR)
                self.screen.blit(fill_surf, (sx - NR, sy - NR))
            elif is_p2:
                fill_surf = pygame.Surface((NR * 2, NR * 2), pygame.SRCALPHA)
                pygame.draw.circle(fill_surf, (*C['p2'], 60),
                                   (NR, NR), NR)
                self.screen.blit(fill_surf, (sx - NR, sy - NR))
            else:
                pygame.draw.circle(self.screen, C['node_fill'], (sx, sy), NR)

            # ── inner border ──────────────────────────────────────────────
            # Player occupying → player colour ring
            # Valid move        → bright white ring (distinct from region colour)
            # Normal            → region colour ring (faint)
            if is_p1:
                pygame.draw.circle(self.screen, C['p1'], (sx, sy), NR, 3)
            elif is_p2:
                pygame.draw.circle(self.screen, C['p2'], (sx, sy), NR, 3)
            elif is_valid:
                # White dashed-look: two overlapping circles (thick white, thin bg)
                pygame.draw.circle(self.screen, C['valid_ring'], (sx, sy), NR, 2)
                pygame.draw.circle(self.screen, C['node_fill'],  (sx, sy), NR - 3, 1)
            else:
                pygame.draw.circle(self.screen, reg_colour, (sx, sy), NR, 1)

            # ── node ID ───────────────────────────────────────────────────
            id_txt = font_id.render(str(nid), True, C['white'])
            self.screen.blit(id_txt, (sx - id_txt.get_width() // 2,
                                      sy - id_txt.get_height() // 2 + 1))

            # ── town name ─────────────────────────────────────────────────
            name = node['name']
            if len(name) > 11:
                name = name[:10] + '~'
            nm_txt = font_name.render(name, True, C['white'])
            nm_txt.set_alpha(200)
            self.screen.blit(nm_txt, (sx - nm_txt.get_width() // 2,
                                      sy + NR + 4))

            # ── customer badge ────────────────────────────────────────────
            if node['customers'] > 0:
                bx, by = sx + NR - 1, sy - NR + 2
                pygame.draw.circle(self.screen, C['gold'], (bx, by), 9)
                ct = font_cust.render(str(node['customers']), True, (0, 0, 0))
                self.screen.blit(ct, (bx - ct.get_width() // 2,
                                      by - ct.get_height() // 2))

            # ── player markers (dot above node) ───────────────────────────
            if is_p1:
                pygame.draw.circle(self.screen, C['p1'],
                                   (sx - 6, sy - NR - 10), 7)
                mk = self.fonts['marker'].render("1", True, (0, 0, 0))
                self.screen.blit(mk, (sx - 10, sy - NR - 17))
            if is_p2:
                pygame.draw.circle(self.screen, C['p2'],
                                   (sx + 6, sy - NR - 10), 7)
                mk = self.fonts['marker'].render("2", True, (0, 0, 0))
                self.screen.blit(mk, (sx + 2, sy - NR - 17))

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
            pcol = C['p1'] if player == 1 else C['p2']
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
        obs_row(C['super_nkabi'], 'S', 'SUPER NKABI', 'back 3 nodes',  y); y += 28
        obs_row(C['police'],      'P', 'POLICE',       'skip 1 turn',   y); y += 28

        # Used route line
        pygame.draw.line(self.screen, C['route_used'], (px, y + 8), (px + 28, y + 8), 3)
        ut = self.fonts['legend'].render("= used route", True, C['text_faint'])
        self.screen.blit(ut, (px + 33, y + 3)); y += 22

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
        bx, by = 20, WIN_H - 52
        bw = MAP_W - 40
        bg = pygame.Surface((bw, 36), pygame.SRCALPHA)
        bg.fill((*C['bg'], int(alpha * 230)))
        self.screen.blit(bg, (bx, by))
        pygame.draw.rect(self.screen, (*col, int(alpha * 180)),
                         (bx, by, bw, 36), 2, border_radius=6)
        txt = self.fonts['msg'].render(self.message, True,
                                       (*C['white'], int(alpha * 255)))
        self.screen.blit(txt, (bx + (bw - txt.get_width()) // 2, by + 10))

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
