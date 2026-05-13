"""
KZN Route: Taxi Wars - Python/PyGame Version
Complete translation of your LOVE2D game
"""

import pygame
import sys
import math
from collections import deque

# ===============================================================================
# CONSTANTS & COLORS
# ===============================================================================

WIN_W, WIN_H = 1280, 720
SIDEBAR_W = 260
MAP_W = WIN_W - SIDEBAR_W
MAP_H = WIN_H

# Colors (RGB, 0-255 format for PyGame)
C = {
    'bg': (13, 10, 26),
    'panel': (18, 15, 33, 247),
    'panel_light': (31, 28, 56),
    'accent': (240, 10, 191),
    'accent_dim': (128, 5, 102),
    'node': (10, 10, 61),
    'node_border': (240, 10, 191),
    'route_active': (217, 8, 173, 191),
    'route_used': (77, 71, 107, 128),
    'p1': (38, 242, 89),
    'p2': (242, 77, 26),
    'white': (255, 255, 255),
    'gold': (255, 204, 0),
    'nkabi_c': (255, 230, 13),
    'super_c': (242, 46, 46),
    'police_c': (71, 158, 255),
}

# ===============================================================================
# REGIONS (matching your KZN map)
# ===============================================================================

REGIONS = [
    {'key': 'northern_natal', 'name': 'Northern Natal', 'colour': (242, 153, 26),
     'nodes': [1, 2, 3, 19, 18, 12, 13], 'lx': 630, 'ly': 120},
    {'key': 'midlands', 'name': 'Midlands', 'colour': (64, 184, 71),
     'nodes': [4, 5, 6, 7, 8, 27, 28, 16], 'lx': 185, 'ly': 300},
    {'key': 'north_coast', 'name': 'North Coast', 'colour': (204, 26, 38),
     'nodes': [14, 15, 17, 11], 'lx': 555, 'ly': 350},
    {'key': 'durban', 'name': 'Durban', 'colour': (140, 97, 204),
     'nodes': [25, 9, 29, 10], 'lx': 510, 'ly': 510},
    {'key': 'south_coast', 'name': 'South Coast', 'colour': (38, 107, 217),
     'nodes': [30, 26, 23, 22, 24, 20, 21], 'lx': 370, 'ly': 665},
]

# Build node -> region lookup
NODE_REGION = {}
for reg in REGIONS:
    for nid in reg['nodes']:
        NODE_REGION[nid] = reg

# ===============================================================================
# NODES (30 locations)
# ===============================================================================

nodes = [
    # Northern Natal
    {'id': 1, 'name': 'Jozini', 'x': 710, 'y': 80, 'customers': 1},
    {'id': 2, 'name': 'Pongola', 'x': 560, 'y': 60, 'customers': 2},
    {'id': 3, 'name': 'Vryheid', 'x': 310, 'y': 80, 'customers': 5},
    {'id': 19, 'name': 'Mkuze', 'x': 730, 'y': 160, 'customers': 1},
    {'id': 18, 'name': 'Hluhluwe', 'x': 650, 'y': 200, 'customers': 2},
    {'id': 12, 'name': 'Empangeni', 'x': 640, 'y': 290, 'customers': 5},
    {'id': 13, 'name': 'Richards Bay', 'x': 750, 'y': 340, 'customers': 2},
    # Midlands
    {'id': 4, 'name': 'Newcastle', 'x': 90, 'y': 90, 'customers': 3},
    {'id': 5, 'name': 'Dundee', 'x': 190, 'y': 190, 'customers': 3},
    {'id': 6, 'name': 'Ladysmith', 'x': 60, 'y': 280, 'customers': 3},
    {'id': 27, 'name': 'Bergville', 'x': 170, 'y': 310, 'customers': 4},
    {'id': 7, 'name': 'Estcourt', 'x': 70, 'y': 450, 'customers': 2},
    {'id': 8, 'name': 'Mooi River', 'x': 290, 'y': 420, 'customers': 2},
    {'id': 28, 'name': 'Greytown', 'x': 310, 'y': 300, 'customers': 3},
    {'id': 16, 'name': 'Ulundi', 'x': 380, 'y': 170, 'customers': 3},
    # North Coast
    {'id': 14, 'name': 'Eshowe', 'x': 500, 'y': 210, 'customers': 3},
    {'id': 15, 'name': 'Melmoth', 'x': 500, 'y': 310, 'customers': 4},
    {'id': 17, 'name': 'Nongoma', 'x': 500, 'y': 400, 'customers': 3},
    {'id': 11, 'name': 'Stanger', 'x': 640, 'y': 430, 'customers': 4},
    # Durban
    {'id': 25, 'name': 'Hammersdale', 'x': 210, 'y': 400, 'customers': 5},
    {'id': 9, 'name': 'Pietermaritzburg', 'x': 380, 'y': 500, 'customers': 5},
    {'id': 29, 'name': 'Pinetown', 'x': 540, 'y': 560, 'customers': 5},
    {'id': 10, 'name': 'Durban', 'x': 720, 'y': 510, 'customers': 5},
    # South Coast
    {'id': 30, 'name': 'Underberg', 'x': 230, 'y': 560, 'customers': 3},
    {'id': 26, 'name': 'iXopo', 'x': 160, 'y': 610, 'customers': 2},
    {'id': 23, 'name': 'Harding', 'x': 320, 'y': 620, 'customers': 3},
    {'id': 22, 'name': 'Port Edward', 'x': 410, 'y': 700, 'customers': 1},
    {'id': 24, 'name': 'Kokstad', 'x': 60, 'y': 700, 'customers': 1},
    {'id': 20, 'name': 'Port Shepstone', 'x': 590, 'y': 680, 'customers': 3},
    {'id': 21, 'name': 'Margate', 'x': 680, 'y': 610, 'customers': 1},
]

# ===============================================================================
# ROUTES (connections between nodes)
# ===============================================================================

routes = [
    {'from': 1, 'to': 2, 'obstacle': None, 'cleared': False},
    {'from': 2, 'to': 14, 'obstacle': 'NK', 'cleared': False},
    {'from': 1, 'to': 19, 'obstacle': None, 'cleared': False},
    {'from': 19, 'to': 18, 'obstacle': None, 'cleared': False},
    {'from': 4, 'to': 6, 'obstacle': 'SNK', 'cleared': False},
    {'from': 4, 'to': 5, 'obstacle': None, 'cleared': False},
    {'from': 3, 'to': 5, 'obstacle': None, 'cleared': False},
    {'from': 5, 'to': 27, 'obstacle': 'NK', 'cleared': False},
    {'from': 6, 'to': 25, 'obstacle': 'NK', 'cleared': False},
    {'from': 6, 'to': 7, 'obstacle': None, 'cleared': False},
    {'from': 2, 'to': 16, 'obstacle': None, 'cleared': False},
    {'from': 16, 'to': 27, 'obstacle': 'POL', 'cleared': False},
    {'from': 12, 'to': 15, 'obstacle': 'SNK', 'cleared': False},
    {'from': 18, 'to': 15, 'obstacle': 'NK', 'cleared': False},
    {'from': 14, 'to': 15, 'obstacle': None, 'cleared': False},
    {'from': 12, 'to': 13, 'obstacle': None, 'cleared': False},
    {'from': 12, 'to': 17, 'obstacle': None, 'cleared': False},
    {'from': 17, 'to': 9, 'obstacle': 'NK', 'cleared': False},
    {'from': 16, 'to': 28, 'obstacle': None, 'cleared': False},
    {'from': 28, 'to': 8, 'obstacle': 'SNK', 'cleared': False},
    {'from': 26, 'to': 24, 'obstacle': None, 'cleared': False},
    {'from': 26, 'to': 7, 'obstacle': None, 'cleared': False},
    {'from': 26, 'to': 23, 'obstacle': 'NK', 'cleared': False},
    {'from': 23, 'to': 8, 'obstacle': None, 'cleared': False},
    {'from': 8, 'to': 9, 'obstacle': None, 'cleared': False},
    {'from': 24, 'to': 22, 'obstacle': None, 'cleared': False},
    {'from': 20, 'to': 22, 'obstacle': None, 'cleared': False},
    {'from': 20, 'to': 29, 'obstacle': 'NK', 'cleared': False},
    {'from': 13, 'to': 11, 'obstacle': None, 'cleared': False},
    {'from': 9, 'to': 10, 'obstacle': 'POL', 'cleared': False},
    {'from': 21, 'to': 10, 'obstacle': None, 'cleared': False},
    {'from': 30, 'to': 7, 'obstacle': 'POL', 'cleared': False},
    {'from': 30, 'to': 8, 'obstacle': None, 'cleared': False},
]

# Store original customer counts for reset
ORIGINAL_CUSTOMERS = {n['id']: n['customers'] for n in nodes}


# ===============================================================================
# HELPER FUNCTIONS
# ===============================================================================

def find_node(node_id):
    """Find node by ID"""
    for n in nodes:
        if n['id'] == node_id:
            return n
    return None


def get_connected(node_id):
    """Get all nodes connected to given node"""
    connections = []
    for r in routes:
        if r['from'] == node_id:
            connections.append({'to': r['to'], 'obs': r['obstacle'], 'route': r})
        elif r['to'] == node_id:
            connections.append({'to': r['from'], 'obs': r['obstacle'], 'route': r})
    return connections


def is_connected(a, b):
    """Check if two nodes are connected, return (bool, route)"""
    for r in routes:
        if (r['from'] == a and r['to'] == b) or (r['from'] == b and r['to'] == a):
            return True, r
    return False, None


def compute_transform():
    """Calculate scaling and offset for map coordinates"""
    min_x = min(n['x'] for n in nodes)
    max_x = max(n['x'] for n in nodes)
    min_y = min(n['y'] for n in nodes)
    max_y = max(n['y'] for n in nodes)
    
    rx = max_x - min_x
    ry = max_y - min_y
    
    px = rx + rx * 0.18
    py = ry + ry * 0.18
    
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    
    MAP_PAD = 45
    aw = MAP_W - MAP_PAD * 2
    ah = MAP_H - MAP_PAD * 2
    
    ms = min(aw / px, ah / py)
    mox = MAP_W / 2 - cx * ms
    moy = MAP_H / 2 - cy * ms
    
    return ms, mox, moy


def transform_point(x, y, ms, mox, moy):
    """Transform game coordinates to screen coordinates"""
    return x * ms + mox, y * ms + moy


# ===============================================================================
# GAME CLASS
# ===============================================================================

class TaxiWarsGame:
    """Main game class - handles both gameplay and rendering"""
    
    def __init__(self, training_mode=False):
        self.training_mode = training_mode
        
        if not training_mode:
            pygame.init()
            self.screen = pygame.display.set_mode((WIN_W, WIN_H))
            pygame.display.set_caption("KZN Route: Taxi Wars")
            self.clock = pygame.time.Clock()
            
            # Fonts
            self.fonts = {
                'tiny': pygame.font.Font(None, 10),
                'small': pygame.font.Font(None, 12),
                'normal': pygame.font.Font(None, 14),
                'medium': pygame.font.Font(None, 18),
                'large': pygame.font.Font(None, 24),
                'title': pygame.font.Font(None, 28),
                'huge': pygame.font.Font(None, 48),
                'region': pygame.font.Font(None, 13),
            }
        
        # Map transform
        self.ms, self.mox, self.moy = compute_transform()
        
        # Game state
        self.reset()
    
    def reset(self):
        """Reset game to starting state"""
        # Reset node customers
        for n in nodes:
            n['customers'] = ORIGINAL_CUSTOMERS[n['id']]
        
        # Reset routes
        for r in routes:
            r['cleared'] = False
        
        # Player positions (P1: Jozini node 1, P2: Kokstad node 24)
        self.p1_pos = 1
        self.p2_pos = 24
        
        # Scores
        self.p1_score = 0
        self.p2_score = 0
        
        # Turn management
        self.current_player = 1
        self.turn_blocked = {1: False, 2: False}
        
        # Game state
        self.game_over = False
        self.winner = 0
        
        # UI state
        self.message = ""
        self.msg_type = "info"
        self.msg_timer = 0
        self.move_count = 0
        
        # Trail for each player (last 6 positions)
        self.trail_p1 = deque(maxlen=6)
        self.trail_p2 = deque(maxlen=6)
        
        # Visual effects
        self.node_flash = {}
        self.anim_timer = 0
        
        # Input handling
        self.number_input = ""
        self.input_timer = 0
        
        # Valid moves for current player
        self.update_valid_moves()
        
        return self.get_state()
    
    def get_state(self):
        """Return current game state for AI agent"""
        return {
            'p1_pos': self.p1_pos,
            'p2_pos': self.p2_pos,
            'p1_score': self.p1_score,
            'p2_score': self.p2_score,
            'current_player': self.current_player,
            'turn_blocked': self.turn_blocked.copy(),
            'valid_moves': self.valid_moves.copy(),
            'customers': {n['id']: n['customers'] for n in nodes},
            'routes_cleared': {f"{r['from']}-{r['to']}": r['cleared'] for r in routes},
            'game_over': self.game_over,
            'winner': self.winner,
        }
    
    def update_valid_moves(self):
        """Update list of valid moves for current player"""
        pos = self.p1_pos if self.current_player == 1 else self.p2_pos
        opp = self.p2_pos if self.current_player == 1 else self.p1_pos
        
        self.valid_moves = []
        for conn in get_connected(pos):
            if conn['to'] != opp:
                self.valid_moves.append(conn['to'])
    
    def is_valid_move(self, node_id):
        """Check if a move is valid"""
        return node_id in self.valid_moves
    
    def set_message(self, text, msg_type="info", duration=3.0):
        """Set a message to display"""
        self.message = text
        self.msg_type = msg_type
        self.msg_timer = duration
    
    def flash_node(self, node_id, duration=1.2):
        """Flash a node for visual feedback"""
        self.node_flash[node_id] = duration
    
    def push_trail(self, player, node_id):
        """Add node to player's trail"""
        if player == 1:
            self.trail_p1.appendleft(node_id)
        else:
            self.trail_p2.appendleft(node_id)
    
    def apply_nkabi(self, player):
        """Apply NKABI obstacle effect"""
        if player == 1:
            self.p1_score = max(0, self.p1_score - 2)
        else:
            self.p2_score = max(0, self.p2_score - 2)
        self.set_message(f"💀 NKABI! P{player} loses 2 points!", "bad", 2.5)
    
    def apply_super_nkabi(self, player):
        """Apply SUPER NKABI obstacle effect"""
        trail = self.trail_p1 if player == 1 else self.trail_p2
        steps = min(3, len(trail))
        
        if steps == 0:
            start_pos = 1 if player == 1 else 24
            if player == 1:
                self.p1_pos = start_pos
            else:
                self.p2_pos = start_pos
            self.flash_node(start_pos, 1.5)
            self.set_message(f"💀💀 SUPER NKABI! P{player} sent back to start!", "bad", 2.5)
        else:
            target = trail[steps - 1]
            if player == 1:
                self.p1_pos = target
            else:
                self.p2_pos = target
            self.flash_node(target, 1.5)
            self.set_message(f"💀💀 SUPER NKABI! P{player} sent back {steps} nodes", "bad", 2.5)
        
        if player == 1:
            self.p1_score = max(0, self.p1_score - 1)
        else:
            self.p2_score = max(0, self.p2_score - 1)
    
    def apply_police(self, player):
        """Apply POLICE obstacle effect"""
        self.turn_blocked[player] = True
        self.set_message(f"👮 POLICE! P{player} skips next turn!", "warn", 3)
    
    def check_win(self):
        """Check if game is over"""
        WIN_SCORE = 20
        if self.p1_score >= WIN_SCORE:
            self.game_over = True
            self.winner = 1
        elif self.p2_score >= WIN_SCORE:
            self.game_over = True
            self.winner = 2
        return self.game_over
    
    def do_move(self, target_id):
        """Execute a move for the current player"""
        if self.game_over:
            return False
        
        # Check if player is blocked
        if self.turn_blocked[self.current_player]:
            self.set_message(f"⛔ P{self.current_player} is blocked! Turn skipped.", "warn", 2)
            self.turn_blocked[self.current_player] = False
            self.current_player = 3 - self.current_player  # Switch player
            self.update_valid_moves()
            return True
        
        # Check valid moves
        if len(self.valid_moves) == 0:
            self.set_message(f"STALEMATE! P{self.current_player} has no moves.", "warn", 2)
            self.current_player = 3 - self.current_player
            self.update_valid_moves()
            return True
        
        # Validate target
        if target_id < 1 or target_id > 30:
            self.set_message("Invalid — choose node 1-30", "bad", 2)
            return False
        
        # Check connection
        cp = self.current_player
        pos = self.p1_pos if cp == 1 else self.p2_pos
        opp = self.p2_pos if cp == 1 else self.p1_pos
        
        connected, route = is_connected(pos, target_id)
        if not connected:
            self.set_message(f"Node {target_id} not connected!", "bad", 2)
            return False
        
        if target_id == opp:
            self.set_message("Node occupied by opponent!", "bad", 2)
            return False
        
        # Execute move
        self.push_trail(cp, pos)
        
        if cp == 1:
            self.p1_pos = target_id
        else:
            self.p2_pos = target_id
        
        self.flash_node(target_id, 0.9)
        route['cleared'] = True
        self.move_count += 1
        
        # Collect customers
        node = find_node(target_id)
        if node['customers'] > 0:
            gained = node['customers']
            node['customers'] = 0
            if cp == 1:
                self.p1_score += gained
            else:
                self.p2_score += gained
            
            reg = NODE_REGION.get(target_id)
            rname = f" [{reg['name']}]" if reg else ""
            self.set_message(f"P{cp} +{gained} pts · {node['name']}{rname}", "good", 2.5)
        else:
            self.set_message(f"P{cp} moved to {node['name']}", "info", 1.5)
        
        # Apply obstacle effects
        if route['obstacle'] == "NK":
            self.apply_nkabi(cp)
        elif route['obstacle'] == "SNK":
            self.apply_super_nkabi(cp)
        elif route['obstacle'] == "POL":
            self.apply_police(cp)
        
        # Check win
        if self.check_win():
            self.set_message(f"PLAYER {self.winner} WINS!", "good", 5)
            return True
        
        # Switch turn
        next_player = 3 - cp
        if self.turn_blocked[next_player]:
            self.turn_blocked[next_player] = False
            self.set_message(f"P{next_player} was blocked! P{cp} moves again.", "warn", 2.5)
        else:
            self.current_player = next_player
        
        self.update_valid_moves()
        return True
    
    def update(self, dt):
        """Update game logic (called each frame)"""
        self.anim_timer += dt
        
        if self.msg_timer > 0:
            self.msg_timer -= dt
        
        if self.input_timer > 0:
            self.input_timer -= dt
            if self.input_timer <= 0 and self.number_input:
                self.confirm_input()
        
        # Update node flashes
        to_remove = []
        for node_id, timer in self.node_flash.items():
            self.node_flash[node_id] -= dt
            if self.node_flash[node_id] <= 0:
                to_remove.append(node_id)
        for node_id in to_remove:
            del self.node_flash[node_id]
    
    def confirm_input(self):
        """Confirm numeric input and execute move"""
        if self.number_input:
            try:
                n = int(self.number_input)
                self.number_input = ""
                self.input_timer = 0
                self.do_move(n)
            except ValueError:
                self.number_input = ""
                self.input_timer = 0
    
    def handle_event(self, event):
        """Handle pygame events"""
        if event.type == pygame.QUIT:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            
            if event.key == pygame.K_r:
                self.reset()
                self.set_message("New game! P1 at Jozini · P2 at Kokstad", "info", 4)
                return True
            
            if self.game_over:
                return True
            
            # Number input (0-9)
            if event.unicode.isdigit():
                self.number_input += event.unicode
                self.input_timer = 1.2
                return True
            
            # Enter key
            if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                if self.number_input:
                    self.confirm_input()
                return True
            
            # Backspace
            if event.key == pygame.K_BACKSPACE and self.number_input:
                self.number_input = self.number_input[:-1]
                self.input_timer = 0.8 if self.number_input else 0
                return True
        
        return True
    
    # ===========================================================================
    # RENDERING METHODS
    # ===========================================================================
    
    def draw_region_labels(self):
        """Draw region name labels on map"""
        font = self.fonts['region']
        for reg in REGIONS:
            sx, sy = transform_point(reg['lx'], reg['ly'], self.ms, self.mox, self.moy)
            if 10 < sx < MAP_W - 10 and 10 < sy < WIN_H - 10:
                text = font.render(reg['name'].upper(), True, reg['colour'])
                text.set_alpha(184)  # 0.72 * 255
                tw = text.get_width()
                self.screen.blit(text, (sx - tw // 2, sy))
    
    def draw_route_obstacle(self, obs, cx, cy):
        """Draw obstacle symbol on a route"""
        r = 8
        if obs == "NK":
            pygame.draw.polygon(self.screen, C['nkabi_c'], [
                (cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)
            ])
            font = self.fonts['tiny']
            text = font.render("N", True, (0, 0, 0))
            self.screen.blit(text, (cx - 4, cy - 5))
        elif obs == "SNK":
            pygame.draw.circle(self.screen, C['super_c'], (cx, cy), r)
            font = self.fonts['tiny']
            text = font.render("S", True, (255, 255, 255))
            self.screen.blit(text, (cx - 3, cy - 5))
        elif obs == "POL":
            pygame.draw.rect(self.screen, C['police_c'], (cx - r, cy - r, r * 2, r * 2))
            font = self.fonts['tiny']
            text = font.render("P", True, (255, 255, 255))
            self.screen.blit(text, (cx - 3, cy - 5))
    
    def draw_routes(self):
        """Draw all routes between nodes"""
        for r in routes:
            a = find_node(r['from'])
            b = find_node(r['to'])
            if not a or not b:
                continue
            
            x1, y1 = transform_point(a['x'], a['y'], self.ms, self.mox, self.moy)
            x2, y2 = transform_point(b['x'], b['y'], self.ms, self.mox, self.moy)
            
            if r['cleared']:
                color = C['route_used']
            else:
                color = C['route_active']
            
            pygame.draw.line(self.screen, color[:3], (x1, y1), (x2, y2), 3)
            
            # Draw obstacle on un-cleared routes
            if r['obstacle'] and not r['cleared']:
                mx = (x1 + x2) // 2
                my = (y1 + y2) // 2
                # Background circle
                pygame.draw.circle(self.screen, C['bg'], (mx, my), 11)
                self.draw_route_obstacle(r['obstacle'], mx, my)
    
    def draw_nodes(self):
        """Draw all nodes (towns/cities)"""
        NODE_RADIUS = 15
        
        for node in nodes:
            sx, sy = transform_point(node['x'], node['y'], self.ms, self.mox, self.moy)
            
            is_p1 = node['id'] == self.p1_pos
            is_p2 = node['id'] == self.p2_pos
            is_valid = node['id'] in self.valid_moves and not self.game_over
            is_flashing = node['id'] in self.node_flash
            
            reg = NODE_REGION.get(node['id'])
            region_color = reg['colour'] if reg else (140, 140, 140)
            
            # Valid move pulse
            if is_valid:
                pulse = (math.sin(self.anim_timer * 4) + 1) / 2
                alpha = int(36 + pulse * 41)  # 0.14 + g*0.16 = ~36-77
                glow_surface = pygame.Surface((NODE_RADIUS * 2 + 20, NODE_RADIUS * 2 + 20), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (*C['accent'], alpha), 
                                 (NODE_RADIUS + 10, NODE_RADIUS + 10), NODE_RADIUS + 6 + pulse * 3)
                self.screen.blit(glow_surface, (sx - NODE_RADIUS - 10, sy - NODE_RADIUS - 10))
            
            # Flash effect
            if is_flashing:
                flash_alpha = int((self.node_flash[node['id']] / 1.2) * 102)  # 0.40 * 255
                flash_surface = pygame.Surface((NODE_RADIUS * 2 + 20, NODE_RADIUS * 2 + 20), pygame.SRCALPHA)
                pygame.draw.circle(flash_surface, (*C['gold'], flash_alpha),
                                 (NODE_RADIUS + 10, NODE_RADIUS + 10), NODE_RADIUS + 10)
                self.screen.blit(flash_surface, (sx - NODE_RADIUS - 10, sy - NODE_RADIUS - 10))
            
            # Region color outer ring
            pygame.draw.circle(self.screen, region_color, (int(sx), int(sy)), NODE_RADIUS + 4, 3)
            
            # Node fill
            if is_p1:
                fill_color = (*C['p1'], 56)  # alpha 0.22 = 56
                fill_surface = pygame.Surface((NODE_RADIUS * 2, NODE_RADIUS * 2), pygame.SRCALPHA)
                pygame.draw.circle(fill_surface, fill_color, (NODE_RADIUS, NODE_RADIUS), NODE_RADIUS)
                self.screen.blit(fill_surface, (sx - NODE_RADIUS, sy - NODE_RADIUS))
            elif is_p2:
                fill_color = (*C['p2'], 56)
                fill_surface = pygame.Surface((NODE_RADIUS * 2, NODE_RADIUS * 2), pygame.SRCALPHA)
                pygame.draw.circle(fill_surface, fill_color, (NODE_RADIUS, NODE_RADIUS), NODE_RADIUS)
                self.screen.blit(fill_surface, (sx - NODE_RADIUS, sy - NODE_RADIUS))
            else:
                pygame.draw.circle(self.screen, C['node'], (int(sx), int(sy)), NODE_RADIUS)
            
            # Inner border
            if is_p1 or is_p2:
                border_color = C['p1'] if is_p1 else C['p2']
                pygame.draw.circle(self.screen, border_color, (int(sx), int(sy)), NODE_RADIUS, 3)
            elif is_valid:
                pygame.draw.circle(self.screen, C['accent'], (int(sx), int(sy)), NODE_RADIUS, 2)
            else:
                pygame.draw.circle(self.screen, region_color, (int(sx), int(sy)), NODE_RADIUS, 2)
            
            # Node ID
            font = self.fonts['small']
            id_text = font.render(str(node['id']), True, C['white'])
            self.screen.blit(id_text, (sx - id_text.get_width() // 2, sy - 9))
            
            # Node name
            font = self.fonts['tiny']
            name = node['name'][:10] + "~" if len(node['name']) > 10 else node['name']
            name_text = font.render(name, True, C['white'])
            name_text.set_alpha(217)  # 0.85 * 255
            self.screen.blit(name_text, (sx - name_text.get_width() // 2, sy + NODE_RADIUS + 3))
            
            # Customer badge
            if node['customers'] > 0:
                bx, by = sx + NODE_RADIUS - 2, sy - NODE_RADIUS + 2
                pygame.draw.circle(self.screen, C['gold'], (bx, by), 9)
                font = self.fonts['small']
                cust_text = font.render(str(node['customers']), True, (0, 0, 0))
                self.screen.blit(cust_text, (bx - cust_text.get_width() // 2, by - 6))
            
            # Player markers
            if is_p1:
                pygame.draw.circle(self.screen, C['p1'], (int(sx - 5), int(sy - NODE_RADIUS - 8)), 6)
                marker = self.fonts['tiny'].render("1", True, (0, 0, 0))
                self.screen.blit(marker, (sx - 8, sy - NODE_RADIUS - 13))
            if is_p2:
                pygame.draw.circle(self.screen, C['p2'], (int(sx + 5), int(sy - NODE_RADIUS - 8)), 6)
                marker = self.fonts['tiny'].render("2", True, (0, 0, 0))
                self.screen.blit(marker, (sx + 2, sy - NODE_RADIUS - 13))
    
    def draw_sidebar(self):
        """Draw the right sidebar with scores and info"""
        sx = MAP_W
        px = sx + 12
        pw = SIDEBAR_W - 24
        
        # Panel background
        panel_surface = pygame.Surface((SIDEBAR_W, WIN_H), pygame.SRCALPHA)
        panel_surface.fill(C['panel'])
        self.screen.blit(panel_surface, (sx, 0))
        
        # Divider line
        pygame.draw.line(self.screen, C['accent'], (sx, 0), (sx, WIN_H), 2)
        
        y = 16
        
        # Title
        font = self.fonts['title']
        title = font.render("KZN ROUTE", True, C['accent'])
        self.screen.blit(title, (px + (pw - title.get_width()) // 2, y))
        y += 34
        
        font = self.fonts['small']
        subtitle = font.render("TAXI WARS", True, C['accent_dim'])
        self.screen.blit(subtitle, (px + (pw - subtitle.get_width()) // 2, y))
        y += 24
        
        # Separator
        pygame.draw.rect(self.screen, C['accent'], (sx + 8, y, SIDEBAR_W - 16, 2))
        y += 12
        
        # Turn banner
        if not self.game_over:
            cp = self.current_player
            col = C['p1'] if cp == 1 else C['p2']
            banner_surface = pygame.Surface((pw, 30), pygame.SRCALPHA)
            banner_surface.fill((*col, 43))  # alpha 0.17 = 43
            self.screen.blit(banner_surface, (px, y))
            pygame.draw.rect(self.screen, col, (px, y, pw, 30), 2, border_radius=4)
            
            font = self.fonts['medium']
            turn_text = font.render(f"PLAYER {cp}'S TURN", True, col)
            self.screen.blit(turn_text, (px + (pw - turn_text.get_width()) // 2, y + 8))
            y += 42
        
        # Score card helper
        def draw_score_card(player, score, py):
            col = C['p1'] if player == 1 else C['p2']
            pos = self.p1_pos if player == 1 else self.p2_pos
            pn = find_node(pos)
            pname = pn['name'][:13] + "." if len(pn['name']) > 13 else pn['name']
            preg = NODE_REGION.get(pos)
            rcol = preg['colour'] if preg else C['white']
            rname = preg['name'] if preg else ""
            
            # Card background
            card_surface = pygame.Surface((pw, 78), pygame.SRCALPHA)
            card_surface.fill((*col, 23))  # alpha 0.09 = 23
            self.screen.blit(card_surface, (px, py))
            pygame.draw.rect(self.screen, col, (px, py, pw, 78), 2, border_radius=5)
            
            font = self.fonts['small']
            player_text = font.render(f"PLAYER {player}", True, col)
            self.screen.blit(player_text, (px + 8, py + 7))
            
            font = self.fonts['large']
            score_text = font.render(f"{score} pts", True, C['white'])
            self.screen.blit(score_text, (px + 8, py + 24))
            
            font = self.fonts['tiny']
            location_text = font.render(f"@ {pname}", True, (255, 255, 255, 133))
            self.screen.blit(location_text, (px + 8, py + 48))
            
            # Region pill
            pygame.draw.rect(self.screen, (*rcol, 77), (px + 8, py + 60, pw - 16, 11), border_radius=3)
            region_text = self.fonts['tiny'].render(rname, True, rcol)
            self.screen.blit(region_text, (px + 8 + (pw - 16 - region_text.get_width()) // 2, py + 62))
            
            # Progress bar
            pct = max(0, min(score / 20, 1))
            pygame.draw.rect(self.screen, C['panel_light'], (px + 8, py + 66, pw - 16, 7), border_radius=3)
            if pct > 0:
                pygame.draw.rect(self.screen, col, (px + 8, py + 66, (pw - 16) * pct, 7), border_radius=3)
        
        draw_score_card(1, self.p1_score, y)
        y += 92
        draw_score_card(2, self.p2_score, y)
        y += 96
        
        # Win condition text
        font = self.fonts['tiny']
        win_text = font.render("First to 20 points wins", True, (255, 255, 255, 84))
        self.screen.blit(win_text, (px + (pw - win_text.get_width()) // 2, y))
        y += 16
        
        pygame.draw.rect(self.screen, C['accent'], (sx + 8, y, SIDEBAR_W - 16, 2))
        y += 10
        
        # Region legend
        legend_title = self.fonts['tiny'].render("REGIONS", True, (255, 255, 255, 128))
        self.screen.blit(legend_title, (px + (pw - legend_title.get_width()) // 2, y))
        y += 14
        
        for reg in REGIONS:
            pygame.draw.circle(self.screen, reg['colour'], (px + 6, y + 5), 5)
            reg_text = self.fonts['tiny'].render(reg['name'], True, (255, 255, 255, 173))
            self.screen.blit(reg_text, (px + 15, y))
            y += 13
        y += 4
        
        pygame.draw.rect(self.screen, C['accent'], (sx + 8, y, SIDEBAR_W - 16, 2))
        y += 8
        
        # Input display
        if self.number_input:
            input_surface = pygame.Surface((pw, 32), pygame.SRCALPHA)
            input_surface.fill((*C['accent'], 36))
            self.screen.blit(input_surface, (px, y))
            pygame.draw.rect(self.screen, C['accent'], (px, y, pw, 32), 2, border_radius=4)
            
            input_text = self.fonts['medium'].render(f"→ {self.number_input}", True, C['accent'])
            self.screen.blit(input_text, (px + (pw - input_text.get_width()) // 2, y + 9))
            y += 42
        else:
            hint_text = self.fonts['tiny'].render("Type node # + Enter", True, (255, 255, 255, 92))
            self.screen.blit(hint_text, (px + (pw - hint_text.get_width()) // 2, y))
            y += 22
        
        pygame.draw.rect(self.screen, C['accent'], (sx + 8, y, SIDEBAR_W - 16, 2))
        y += 8
        
        # Obstacles legend
        obs_title = self.fonts['small'].render("OBSTACLES", True, (255, 255, 255, 115))
        self.screen.blit(obs_title, (px + (pw - obs_title.get_width()) // 2, y))
        y += 16
        
        def draw_legend(col, sym, label, desc, py):
            pygame.draw.circle(self.screen, col, (px + 7, py + 7), 7)
            sym_text = self.fonts['tiny'].render(sym, True, (0, 0, 0))
            self.screen.blit(sym_text, (px + 3, py + 3))
            label_text = self.fonts['tiny'].render(label, True, (255, 255, 255, 209))
            self.screen.blit(label_text, (px + 18, py + 1))
            desc_text = self.fonts['tiny'].render(desc, True, (255, 255, 255, 102))
            self.screen.blit(desc_text, (px + 18, py + 12))
        
        draw_legend(C['nkabi_c'], "N", "NKABI", "lose 2 pts", y)
        y += 28
        draw_legend(C['super_c'], "S", "SUPER NKABI", "back 3 nodes", y)
        y += 28
        draw_legend(C['police_c'], "P", "POLICE", "skip next turn", y)
        y += 28
        
        # Used route indicator
        pygame.draw.line(self.screen, C['route_used'][:3], (px, y + 8), (px + 28, y + 8), 3)
        used_text = self.fonts['tiny'].render("= used route", True, (255, 255, 255, 97))
        self.screen.blit(used_text, (px + 33, y + 3))
        y += 20
        
        # Controls hint
        y = WIN_H - 28
        pygame.draw.rect(self.screen, C['accent'], (sx + 8, y - 8, SIDEBAR_W - 16, 2))
        controls_text = self.fonts['tiny'].render("[R] Restart   [ESC] Quit", True, (255, 255, 255, 61))
        self.screen.blit(controls_text, (px + (pw - controls_text.get_width()) // 2, y))
    
    def draw_message(self):
        """Draw the message bar"""
        if self.msg_timer <= 0:
            return
        
        alpha = min(self.msg_timer, 1.0)
        
        if self.msg_type == "good":
            col = C['p1']
        elif self.msg_type == "bad":
            col = C['super_c']
        elif self.msg_type == "warn":
            col = C['nkabi_c']
        else:
            col = C['accent']
        
        bx, by = 20, WIN_H - 50
        bw = MAP_W - 40
        
        # Background
        bg_surface = pygame.Surface((bw, 38), pygame.SRCALPHA)
        bg_surface.fill((*C['bg'], int(alpha * 242)))  # 0.95 * 255
        self.screen.blit(bg_surface, (bx, by))
        
        # Border
        pygame.draw.rect(self.screen, (*col, int(alpha * 184)), (bx, by, bw, 38), 2, border_radius=6)
        
        # Text
        font = self.fonts['normal']
        text = font.render(self.message, True, (255, 255, 255, int(alpha * 255)))
        self.screen.blit(text, (bx + (bw - text.get_width()) // 2, by + 12))
    
    def draw_game_over(self):
        """Draw game over overlay"""
        if not self.game_over:
            return
        
        pulse = (math.sin(self.anim_timer * 2) + 1) / 2
        col = C['p1'] if self.winner == 1 else C['p2']
        cx, cy = MAP_W // 2, WIN_H // 2
        
        # Dark overlay
        overlay = pygame.Surface((MAP_W, WIN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 209))  # 0.82 * 255
        self.screen.blit(overlay, (0, 0))
        
        # Glow circle
        glow_alpha = int(18 + pulse * 13)  # 0.07 + pulse*0.05 = ~18-31
        pygame.draw.circle(self.screen, (*col, glow_alpha), (cx, cy), int(200 + pulse * 35))
        
        # Panel
        panel_rect = pygame.Rect(cx - 240, cy - 120, 480, 240)
        panel_surface = pygame.Surface((480, 240), pygame.SRCALPHA)
        panel_surface.fill(C['panel'])
        self.screen.blit(panel_surface, (cx - 240, cy - 120))
        pygame.draw.rect(self.screen, (*col, 133), panel_rect, 3, border_radius=16)
        
        # Winner text
        font = self.fonts['huge']
        win_text = font.render(f"PLAYER {self.winner} WINS!", True, col)
        self.screen.blit(win_text, (cx - win_text.get_width() // 2, cy - 100))
        
        # Score text
        font = self.fonts['medium']
        score_text = font.render(f"P1: {self.p1_score}  |  P2: {self.p2_score}", True, (255, 255, 255, 199))
        self.screen.blit(score_text, (cx - score_text.get_width() // 2, cy + 20))
        
        # Restart hint
        font = self.fonts['small']
        restart_alpha = int(107 + pulse * 61)  # 0.42 + pulse*0.24 = ~107-168
        restart_text = font.render("Press  R  to play again", True, (255, 255, 255, restart_alpha))
        self.screen.blit(restart_text, (cx - restart_text.get_width() // 2, cy + 70))
    
    def render(self):
        """Render the entire game"""
        if self.training_mode:
            return
        
        # Clear screen
        self.screen.fill(C['bg'])
        
        # Draw map background (simple grid)
        for gx in range(0, MAP_W, 40):
            for gy in range(0, WIN_H, 40):
                pygame.draw.rect(self.screen, (255, 255, 255, 6), (gx - 1, gy - 1, 2, 2))
        
        # Draw region labels
        self.draw_region_labels()
        
        # Draw routes and nodes
        self.draw_routes()
        self.draw_nodes()
        
        # Draw UI
        self.draw_sidebar()
        self.draw_message()
        self.draw_game_over()
        
        # Move counter
        font = self.fonts['tiny']
        move_text = font.render(f"Moves: {self.move_count // 2}", True, (255, 255, 255, 64))
        self.screen.blit(move_text, (10, 8))
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        clock = pygame.time.Clock()
        running = True
        
        while running:
            dt = clock.tick(60) / 1000.0
            
            for event in pygame.event.get():
                if not self.handle_event(event):
                    running = False
            
            self.update(dt)
            self.render()
        
        pygame.quit()
        sys.exit()



if __name__ == "__main__":
    game = TaxiWarsGame(training_mode=False)
    game.run()
