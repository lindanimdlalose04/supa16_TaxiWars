-- KZN Route: Taxi Wars  v5
-- Custom map from editor · 30 nodes · Fixed police logic · NO BORDER

love.graphics.setDefaultFilter("nearest", "nearest")

-------------------------------------------------------------------------------
-- PALETTE
-------------------------------------------------------------------------------
local C = {
    bg          = {0.05, 0.04, 0.10},
    panel       = {0.07, 0.06, 0.13, 0.97},
    panelLight  = {0.12, 0.11, 0.22},
    accent      = {0.94, 0.04, 0.75},
    accentDim   = {0.50, 0.02, 0.40},
    node        = {0.04, 0.04, 0.24},
    nodeBorder  = {0.94, 0.04, 0.75},
    routeActive = {0.85, 0.03, 0.68, 0.75},
    routeUsed   = {0.30, 0.28, 0.42, 0.50},
    p1          = {0.15, 0.95, 0.35},
    p2          = {0.95, 0.30, 0.10},
    white       = {1, 1, 1},
    gold        = {1.0, 0.80, 0.0},
    nkabi_c     = {1.0, 0.90, 0.05},
    super_c     = {0.95, 0.18, 0.18},
    police_c    = {0.28, 0.62, 1.0},
}

-------------------------------------------------------------------------------
-- LAYOUT - INCREASED MAP AREA
-------------------------------------------------------------------------------
local WIN_W, WIN_H = 1280, 720   -- Larger window
local SIDEBAR_W    = 260
local MAP_W        = WIN_W - SIDEBAR_W   -- 1140
local MAP_H        = WIN_H               -- 900

local fonts = {}

-------------------------------------------------------------------------------
-- YOUR CUSTOM MAP (from editor)
-------------------------------------------------------------------------------
local nodes = {
    {id=1, name="Jozini", x=777, y=23, customers=1},
    {id=2, name="Pongola", x=574, y=22, customers=2},
    {id=3, name="Vryheid", x=327, y=29, customers=5},
    {id=4, name="Newcastle", x=67, y=69, customers=3},
    {id=5, name="Dundee", x=174, y=174, customers=3},
    {id=6, name="Ladysmith", x=24, y=270, customers=3},
    {id=7, name="Estcourt", x=26, y=520, customers=2},
    {id=8, name="Mooi River", x=323, y=474, customers=2},
    {id=9, name="Pietermaritzburg", x=424, y=574, customers=5},
    {id=10, name="Durban", x=775, y=574, customers=5},
    {id=11, name="Stanger", x=676, y=472, customers=4},
    {id=12, name="Empangeni", x=678, y=320, customers=5},
    {id=13, name="Richards Bay", x=773, y=419, customers=2},
    {id=14, name="Eshowe", x=523, y=178, customers=3},
    {id=15, name="Melmoth", x=525, y=321, customers=4},
    {id=16, name="Ulundi", x=377, y=173, customers=3},
    {id=17, name="Nongoma", x=523, y=426, customers=3},
    {id=18, name="Hluhluwe", x=671, y=178, customers=2},
    {id=19, name="Mkuze", x=774, y=126, customers=1},
    {id=20, name="Port Shepstone", x=621, y=775, customers=3},
    {id=21, name="Margate", x=728, y=672, customers=1},
    {id=22, name="Port Edward", x=428, y=772, customers=1},
    {id=23, name="Harding", x=325, y=672, customers=3},
    {id=24, name="Kokstad", x=24, y=772, customers=1},
    {id=25, name="Hammersdale", x=176, y=423, customers=5},
    {id=26, name="iXopo", x=126, y=674, customers=2},
    {id=27, name="Bergville", x=176, y=322, customers=4},
    {id=28, name="Greytown", x=324, y=323, customers=3},
    {id=29, name="Pinetown", x=570, y=621, customers=5},
    {id=30, name="Underberg", x=225, y=572, customers=3},
}

local routes = {
    {from=1, to=2, obstacle=nil, cleared=false},
    {from=2, to=14, obstacle="NK", cleared=false},
    {from=1, to=19, obstacle=nil, cleared=false},
    {from=19, to=18, obstacle=nil, cleared=false},
    {from=4, to=6, obstacle="SNK", cleared=false},
    {from=4, to=5, obstacle=nil, cleared=false},
    {from=3, to=5, obstacle=nil, cleared=false},
    {from=5, to=27, obstacle="NK", cleared=false},
    {from=6, to=25, obstacle="NK", cleared=false},
    {from=6, to=7, obstacle=nil, cleared=false},
    {from=2, to=16, obstacle=nil, cleared=false},
    {from=16, to=27, obstacle="POL", cleared=false},
    {from=12, to=15, obstacle="SNK", cleared=false},
    {from=18, to=15, obstacle="NK", cleared=false},
    {from=14, to=15, obstacle=nil, cleared=false},
    {from=12, to=13, obstacle=nil, cleared=false},
    {from=12, to=17, obstacle=nil, cleared=false},
    {from=17, to=9, obstacle="NK", cleared=false},
    {from=16, to=28, obstacle=nil, cleared=false},
    {from=28, to=8, obstacle="SNK", cleared=false},
    {from=26, to=24, obstacle=nil, cleared=false},
    {from=26, to=7, obstacle=nil, cleared=false},
    {from=26, to=23, obstacle="NK", cleared=false},
    {from=23, to=8, obstacle=nil, cleared=false},
    {from=8, to=9, obstacle=nil, cleared=false},
    {from=24, to=22, obstacle=nil, cleared=false},
    {from=20, to=22, obstacle=nil, cleared=false},
    {from=20, to=29, obstacle="NK", cleared=false},
    {from=13, to=11, obstacle=nil, cleared=false},
    {from=9, to=10, obstacle="POL", cleared=false},
    {from=21, to=10, obstacle=nil, cleared=false},
    {from=30, to=7, obstacle="POL", cleared=false},
    {from=30, to=8, obstacle=nil, cleared=false},
}

-- Extract customer amounts from nodes
local NODE_CUSTOMERS = {}
for _, node in ipairs(nodes) do
    NODE_CUSTOMERS[node.id] = node.customers
end

-------------------------------------------------------------------------------
-- MAP TRANSFORM - AUTO-FITS TO SCREEN
-------------------------------------------------------------------------------
local MS, MOX, MOY = 1, 0, 0
local MAP_PAD = 50

local function compute_transform()
    -- Find bounds from nodes only (no broken border)
    local min_x, max_x = math.huge, -math.huge
    local min_y, max_y = math.huge, -math.huge
    
    for _, n in ipairs(nodes) do
        if n.x < min_x then min_x = n.x end
        if n.x > max_x then max_x = n.x end
        if n.y < min_y then min_y = n.y end
        if n.y > max_y then max_y = n.y end
    end
    
    -- Add padding to bounds
    local range_x = max_x - min_x
    local range_y = max_y - min_y
    local padded_range_x = range_x + (range_x * 0.2)  -- 20% padding
    local padded_range_y = range_y + (range_y * 0.2)
    
    local center_x = (min_x + max_x) / 2
    local center_y = (min_y + max_y) / 2
    
    local available_w = MAP_W - (MAP_PAD * 2)
    local available_h = MAP_H - (MAP_PAD * 2)
    
    local scale_x = available_w / padded_range_x
    local scale_y = available_h / padded_range_y
    MS = math.min(scale_x, scale_y)
    
    -- Center the map
    MOX = MAP_W / 2 - (center_x * MS)
    MOY = MAP_H / 2 - (center_y * MS)
end

local function tx(x, y) 
    return x * MS + MOX, y * MS + MOY 
end

-------------------------------------------------------------------------------
-- GAME STATE
-------------------------------------------------------------------------------
local state = {}

local function reset_game()
    for _, n in ipairs(nodes) do n.customers = NODE_CUSTOMERS[n.id] or 0 end
    for _, r in ipairs(routes) do r.cleared = false end
    state = {
        p1_pos = 1,      -- Jozini
        p2_pos = 24,     -- Kokstad
        p1_score = 0,
        p2_score = 0,
        current_player = 1,
        turn_blocked = { [1] = false, [2] = false },
        message = "",
        msg_timer = 0,
        msg_type = "info",
        set_count = 0,
        number_input = "",
        input_timer = 0,
        node_flash = {},
        valid_moves = {},
        game_over = false,
        winner = 0,
        anim_timer = 0,
        trail_p1 = {},
        trail_p2 = {},
    }
end

-------------------------------------------------------------------------------
-- HELPERS
-------------------------------------------------------------------------------
local function find_node(id)
    for _, n in ipairs(nodes) do if n.id == id then return n end end
end

local function is_connected(a, b)
    for _, r in ipairs(routes) do
        if (r.from == a and r.to == b) or (r.from == b and r.to == a) then
            return true, r
        end
    end
    return false, nil
end

local function get_connected(fid)
    local out = {}
    for _, r in ipairs(routes) do
        if r.from == fid then table.insert(out, { to = r.to, obs = r.obstacle, route = r }) end
        if r.to == fid then table.insert(out, { to = r.from, obs = r.obstacle, route = r }) end
    end
    return out
end

local function update_valid_moves()
    state.valid_moves = {}
    local pos = state.current_player == 1 and state.p1_pos or state.p2_pos
    local opp = state.current_player == 1 and state.p2_pos or state.p1_pos
    for _, c in ipairs(get_connected(pos)) do
        if c.to ~= opp then
            table.insert(state.valid_moves, c.to)
        end
    end
end

local function is_valid_move(id)
    for _, v in ipairs(state.valid_moves) do if v == id then return true end end
    return false
end

local function set_msg(txt, typ, dur)
    state.message = txt
    state.msg_type = typ or "info"
    state.msg_timer = dur or 3
end

local function flash_node(id, dur) state.node_flash[id] = dur or 1.2 end

local function push_trail(player, nid)
    local t = player == 1 and state.trail_p1 or state.trail_p2
    table.insert(t, 1, nid)
    if #t > 6 then table.remove(t) end
end

-------------------------------------------------------------------------------
-- OBSTACLE EFFECTS
-------------------------------------------------------------------------------
local function apply_nkabi(player)
    if player == 1 then
        state.p1_score = math.max(0, state.p1_score - 2)
    else
        state.p2_score = math.max(0, state.p2_score - 2)
    end
    set_msg("💀 NKABI! P" .. player .. " loses 2 points!", "bad", 2.5)
end

local function apply_super_nkabi(player)
    local trail = player == 1 and state.trail_p1 or state.trail_p2
    local steps = math.min(3, #trail)
    
    if steps == 0 then
        local start_pos = (player == 1 and 1 or 24)
        if player == 1 then
            state.p1_pos = start_pos
        else
            state.p2_pos = start_pos
        end
        flash_node(start_pos, 1.5)
        set_msg("💀💀 SUPER NKABI! P" .. player .. " sent back to start!", "bad", 2.5)
    else
        local target_node = trail[steps]
        if player == 1 then
            state.p1_pos = target_node
        else
            state.p2_pos = target_node
        end
        flash_node(target_node, 1.5)
        set_msg("💀💀 SUPER NKABI! P" .. player .. " sent back " .. steps .. " nodes", "bad", 2.5)
    end
    
    if player == 1 then
        state.p1_score = math.max(0, state.p1_score - 1)
    else
        state.p2_score = math.max(0, state.p2_score - 1)
    end
end

local function apply_police(player)
    state.turn_blocked[player] = true
    set_msg("👮 POLICE! P" .. player .. " skips next turn!", "warn", 3)
end

local function check_win()
    local WIN_SCORE = 20
    if state.p1_score >= WIN_SCORE then
        state.game_over = true
        state.winner = 1
    elseif state.p2_score >= WIN_SCORE then
        state.game_over = true
        state.winner = 2
    end
end

-------------------------------------------------------------------------------
-- DO MOVE
-------------------------------------------------------------------------------
local function do_move(tid)
    if state.game_over then return end
    
    if state.turn_blocked[state.current_player] then
        set_msg("⛔ P" .. state.current_player .. " is blocked! Turn skipped.", "warn", 2)
        state.turn_blocked[state.current_player] = false
        state.current_player = (state.current_player == 1 and 2 or 1)
        update_valid_moves()
        return
    end
        -- Check for stalemate (no valid moves for current player)
    if #state.valid_moves == 0 then
        set_msg("STALEMATE! P" .. state.current_player .. " has no moves. Turn skipped.", "warn", 2)
        state.current_player = (state.current_player == 1 and 2 or 1)
        update_valid_moves()
        return
    end


    local cp = state.current_player
    local pos = cp == 1 and state.p1_pos or state.p2_pos
    local opp = cp == 1 and state.p2_pos or state.p1_pos
    
    if tid < 1 or tid > 30 then
        set_msg("Invalid — choose node 1-30", "bad", 2)
        return
    end
    
    local connected, route = is_connected(pos, tid)
    if not connected then
        set_msg("Node " .. tid .. " not connected!", "bad", 2)
        return
    end
    
    if tid == opp then
        set_msg("Node occupied by opponent!", "bad", 2)
        return
    end
    
    push_trail(cp, pos)
    
    if cp == 1 then
        state.p1_pos = tid
    else
        state.p2_pos = tid
    end
    
    flash_node(tid, 0.9)
    route.cleared = true
    
    local node = find_node(tid)
    if node.customers > 0 then
        local got = node.customers
        node.customers = 0
        if cp == 1 then
            state.p1_score = state.p1_score + got
        else
            state.p2_score = state.p2_score + got
        end
        set_msg("P" .. cp .. " collected " .. got .. " pts from " .. node.name .. " ✓", "good", 2.5)
    else
        set_msg("P" .. cp .. " moved to " .. node.name, "info", 1.5)
    end
    
    if route.obstacle == "NK" then
        apply_nkabi(cp)
    elseif route.obstacle == "SNK" then
        apply_super_nkabi(cp)
    elseif route.obstacle == "POL" then
        apply_police(cp)
    end
    
    check_win()
    if state.game_over then return end
    
    state.set_count = state.set_count + 1
    
    local next_player = (cp == 1 and 2 or 1)
    
    if state.turn_blocked[next_player] then
        state.turn_blocked[next_player] = false
        set_msg("P" .. next_player .. " was blocked! P" .. cp .. " moves again.", "warn", 2.5)
    else
        state.current_player = next_player
    end
    
    update_valid_moves()
end

local function confirm_input()
    local n = tonumber(state.number_input)
    state.number_input = ""
    state.input_timer = 0
    if n then do_move(n) end
end

-------------------------------------------------------------------------------
-- LOVE.LOAD
-------------------------------------------------------------------------------
function love.load()
    love.window.setTitle("KZN Route: Taxi Wars")
    love.window.setMode(WIN_W, WIN_H, { resizable = false, vsync = true })
    
    fonts.tiny = love.graphics.newFont(10)
    fonts.small = love.graphics.newFont(12)
    fonts.normal = love.graphics.newFont(14)
    fonts.medium = love.graphics.newFont(18)
    fonts.large = love.graphics.newFont(24)
    fonts.title = love.graphics.newFont(28)
    fonts.huge = love.graphics.newFont(48)
    
    compute_transform()
    reset_game()
    update_valid_moves()
    set_msg("P1 at Jozini · P2 at Kokstad · Type node # + Enter", "info", 5)
end

-------------------------------------------------------------------------------
-- LOVE.UPDATE
-------------------------------------------------------------------------------
function love.update(dt)
    state.anim_timer = state.anim_timer + dt
    if state.msg_timer > 0 then state.msg_timer = state.msg_timer - dt end
    if state.input_timer > 0 then
        state.input_timer = state.input_timer - dt
        if state.input_timer <= 0 then confirm_input() end
    end
    for id, t in pairs(state.node_flash) do
        state.node_flash[id] = t - dt
        if state.node_flash[id] <= 0 then state.node_flash[id] = nil end
    end
end

-------------------------------------------------------------------------------
-- DRAW HELPERS
-------------------------------------------------------------------------------
local function sc(c, a)
    if a then love.graphics.setColor(c[1], c[2], c[3], a)
    else love.graphics.setColor(c) end
end

local function rrect(x, y, w, h, r, col, a)
    sc(col, a)
    love.graphics.rectangle("fill", x, y, w, h, r, r)
end

local function midpoint(x1, y1, x2, y2) return (x1 + x2) / 2, (y1 + y2) / 2 end

-------------------------------------------------------------------------------
-- OBSTACLE SYMBOL
-------------------------------------------------------------------------------
local function draw_obs(obs, cx, cy)
    local r = 8
    if obs == "NK" then
        sc(C.nkabi_c)
        love.graphics.polygon("fill", cx, cy - r, cx + r, cy, cx, cy + r, cx - r, cy)
        love.graphics.setColor(0, 0, 0, 0.45)
        love.graphics.polygon("line", cx, cy - r, cx + r, cy, cx, cy + r, cx - r, cy)
        love.graphics.setFont(fonts.tiny)
        love.graphics.setColor(0, 0, 0)
        love.graphics.printf("N", cx - r, cy - 5, r * 2, "center")
    elseif obs == "SNK" then
        sc(C.super_c)
        love.graphics.circle("fill", cx, cy, r)
        love.graphics.setColor(0, 0, 0, 0.4)
        love.graphics.circle("line", cx, cy, r)
        love.graphics.setFont(fonts.tiny)
        love.graphics.setColor(1, 1, 1)
        love.graphics.printf("S", cx - r, cy - 5, r * 2, "center")
    elseif obs == "POL" then
        sc(C.police_c)
        love.graphics.polygon("fill", cx, cy - r, cx + r, cy - 2, cx + r, cy + r - 2, cx, cy + r, cx - r, cy + r - 2, cx - r, cy - 2)
        love.graphics.setColor(0, 0, 0, 0.35)
        love.graphics.polygon("line", cx, cy - r, cx + r, cy - 2, cx + r, cy + r - 2, cx, cy + r, cx - r, cy + r - 2, cx - r, cy - 2)
        love.graphics.setFont(fonts.tiny)
        love.graphics.setColor(1, 1, 1)
        love.graphics.printf("P", cx - r, cy - 5, r * 2, "center")
    end
end

-------------------------------------------------------------------------------
-- DRAW ROUTES
-------------------------------------------------------------------------------
local function draw_routes()
    love.graphics.setLineWidth(2.5)
    for _, r in ipairs(routes) do
        local a = find_node(r.from)
        local b = find_node(r.to)
        if not (a and b) then goto cont end
        local x1, y1 = tx(a.x, a.y)
        local x2, y2 = tx(b.x, b.y)
        
        if r.cleared then
            sc(C.routeUsed)
        else
            sc(C.routeActive)
        end
        love.graphics.line(x1, y1, x2, y2)
        
        if r.obstacle and not r.cleared then
            local mx, my = midpoint(x1, y1, x2, y2)
            love.graphics.setColor(C.bg[1], C.bg[2], C.bg[3], 0.92)
            love.graphics.circle("fill", mx, my, 11)
            draw_obs(r.obstacle, mx, my)
        end
        ::cont::
    end
end

-------------------------------------------------------------------------------
-- DRAW NODES
-------------------------------------------------------------------------------
local NR = 15

local function draw_nodes()
    local t = state.anim_timer
    for _, node in ipairs(nodes) do
        local sx, sy = tx(node.x, node.y)
        local is1 = node.id == state.p1_pos
        local is2 = node.id == state.p2_pos
        local valid = is_valid_move(node.id) and not state.game_over
        local ft = state.node_flash[node.id]
        
        if valid then
            local g = (math.sin(t * 4) + 1) / 2
            sc(C.accent, 0.14 + g * 0.16)
            love.graphics.circle("fill", sx, sy, NR + 6 + g * 3)
        end
        
        if ft and ft > 0 then
            sc(C.gold, ft / 1.2 * 0.40)
            love.graphics.circle("fill", sx, sy, NR + 10)
        end
        
        if is1 then
            sc(C.p1, 0.20)
        elseif is2 then
            sc(C.p2, 0.20)
        else
            sc(C.node)
        end
        love.graphics.circle("fill", sx, sy, NR)
        
        love.graphics.setLineWidth((is1 or is2) and 3 or 2)
        if is1 then
            sc(C.p1)
        elseif is2 then
            sc(C.p2)
        elseif valid then
            sc(C.accent)
        else
            sc(C.nodeBorder, 0.70)
        end
        love.graphics.circle("line", sx, sy, NR)
        
        love.graphics.setFont(fonts.small)
        sc(C.white)
        local ids = tostring(node.id)
        local iw = fonts.small:getWidth(ids)
        love.graphics.print(ids, sx - iw / 2, sy - 9)
        
        love.graphics.setFont(fonts.tiny)
        local nm = node.name
        if #nm > 10 then nm = nm:sub(1, 9) .. ".." end
        local nw = fonts.tiny:getWidth(nm)
        love.graphics.setColor(0, 0, 0, 0.70)
        love.graphics.print(nm, sx - nw / 2 + 1, sy + NR + 4)
        sc(C.white, 0.85)
        love.graphics.print(nm, sx - nw / 2, sy + NR + 3)
        
        if node.customers > 0 then
            local bx, by = sx + NR - 2, sy - NR + 2
            sc(C.gold)
            love.graphics.circle("fill", bx, by, 9)
            love.graphics.setColor(0, 0, 0)
            love.graphics.setFont(fonts.small)
            local cs = tostring(node.customers)
            love.graphics.print(cs, bx - fonts.small:getWidth(cs) / 2, by - 6)
        end
        
        if is1 then
            sc(C.p1)
            love.graphics.circle("fill", sx - 5, sy - NR - 8, 6)
            love.graphics.setColor(0, 0, 0)
            love.graphics.setFont(fonts.tiny)
            love.graphics.print("1", sx - 8, sy - NR - 13)
        end
        if is2 then
            sc(C.p2)
            love.graphics.circle("fill", sx + 5, sy - NR - 8, 6)
            love.graphics.setColor(0, 0, 0)
            love.graphics.setFont(fonts.tiny)
            love.graphics.print("2", sx + 2, sy - NR - 13)
        end
    end
end

-------------------------------------------------------------------------------
-- DRAW SIDEBAR
-------------------------------------------------------------------------------
local function draw_sidebar()
    local SX = MAP_W
    local px = SX + 12
    local pw = SIDEBAR_W - 24
    
    sc(C.panel)
    love.graphics.rectangle("fill", SX, 0, SIDEBAR_W, WIN_H)
    sc(C.accent, 0.40)
    love.graphics.setLineWidth(1.5)
    love.graphics.line(SX, 0, SX, WIN_H)
    
    local y = 16
    
    love.graphics.setFont(fonts.title)
    sc(C.accent)
    love.graphics.printf("KZN ROUTE", px, y, pw, "center")
    y = y + 34
    love.graphics.setFont(fonts.small)
    sc(C.accentDim)
    love.graphics.printf("TAXI WARS", px, y, pw, "center")
    y = y + 24
    
    sc(C.accent, 0.22)
    love.graphics.rectangle("fill", SX + 8, y, SIDEBAR_W - 16, 1)
    y = y + 12
    
    if not state.game_over then
        local cp = state.current_player
        local col = cp == 1 and C.p1 or C.p2
        rrect(px, y, pw, 30, 4, col, 0.17)
        sc(col)
        love.graphics.setLineWidth(1.5)
        love.graphics.rectangle("line", px, y, pw, 30, 4, 4)
        love.graphics.setFont(fonts.medium)
        love.graphics.printf("PLAYER " .. cp .. "'S TURN", px, y + 8, pw, "center")
        y = y + 42
    else
        y = y + 10
    end
    
    local function score_card(player, score, py)
        local col = player == 1 and C.p1 or C.p2
        local pn = find_node(player == 1 and state.p1_pos or state.p2_pos)
        local pname = pn and pn.name or "?"
        if #pname > 13 then pname = pname:sub(1, 12) .. "." end
        rrect(px, py, pw, 70, 5, col, 0.09)
        sc(col, 0.30)
        love.graphics.setLineWidth(1.5)
        love.graphics.rectangle("line", px, py, pw, 70, 5, 5)
        love.graphics.setFont(fonts.small)
        sc(col)
        love.graphics.print("PLAYER " .. player, px + 8, py + 7)
        love.graphics.setFont(fonts.large)
        sc(C.white)
        love.graphics.print(score .. " pts", px + 8, py + 24)
        love.graphics.setFont(fonts.tiny)
        sc(C.white, 0.52)
        love.graphics.print("@ " .. pname, px + 8, py + 44)
        local pct = math.max(0, math.min(score / 20, 1))
        rrect(px + 8, py + 55, pw - 16, 8, 3, C.panelLight)
        if pct > 0 then rrect(px + 8, py + 55, (pw - 16) * pct, 8, 3, col) end
    end
    
    score_card(1, state.p1_score, y)
    y = y + 82
    score_card(2, state.p2_score, y)
    y = y + 86
    
    love.graphics.setFont(fonts.tiny)
    sc(C.white, 0.33)
    love.graphics.printf("First to 20 points wins", px, y, pw, "center")
    y = y + 18
    
    sc(C.accent, 0.18)
    love.graphics.rectangle("fill", SX + 8, y, SIDEBAR_W - 16, 1)
    y = y + 10
    
    if state.number_input ~= "" then
        rrect(px, y, pw, 32, 4, C.accent, 0.14)
        sc(C.accent)
        love.graphics.setLineWidth(1.5)
        love.graphics.rectangle("line", px, y, pw, 32, 4, 4)
        love.graphics.setFont(fonts.medium)
        love.graphics.printf("→ " .. state.number_input, px, y + 9, pw, "center")
        y = y + 42
    else
        love.graphics.setFont(fonts.tiny)
        sc(C.white, 0.36)
        love.graphics.printf("Type node # + Enter", px, y, pw, "center")
        y = y + 22
    end
    
    sc(C.accent, 0.15)
    love.graphics.rectangle("fill", SX + 8, y, SIDEBAR_W - 16, 1)
    y = y + 10
    
    love.graphics.setFont(fonts.small)
    sc(C.white, 0.45)
    love.graphics.printf("OBSTACLES", px, y, pw, "center")
    y = y + 18
    
    local function leg(col, sym, label, desc, py)
        love.graphics.setColor(col)
        love.graphics.circle("fill", px + 7, py + 7, 7)
        love.graphics.setColor(0, 0, 0, 0.4)
        love.graphics.circle("line", px + 7, py + 7, 7)
        love.graphics.setFont(fonts.tiny)
        love.graphics.setColor(0, 0, 0)
        love.graphics.printf(sym, px + 2, py + 3, 14, "center")
        sc(C.white, 0.82)
        love.graphics.print(label, px + 18, py + 1)
        sc(C.white, 0.40)
        love.graphics.print(desc, px + 18, py + 13)
    end
    
    leg(C.nkabi_c, "N", "NKABI", "lose 2 pts", y)
    y = y + 30
    leg(C.super_c, "S", "SUPER NKABI", "back 3 nodes", y)
    y = y + 30
    leg(C.police_c, "P", "POLICE", "skip next turn", y)
    y = y + 32
    
    sc(C.routeUsed)
    love.graphics.setLineWidth(2.5)
    love.graphics.line(px, y + 8, px + 28, y + 8)
    sc(C.white, 0.38)
    love.graphics.setFont(fonts.tiny)
    love.graphics.print("= used route", px + 33, y + 3)
    y = y + 24
    
    sc(C.accent, 0.15)
    love.graphics.rectangle("fill", SX + 8, y, SIDEBAR_W - 16, 1)
    y = y + 10
    love.graphics.setFont(fonts.small)
    sc(C.white, 0.40)
    love.graphics.printf("NODES", px, y, pw, "center")
    y = y + 18
    
    local col1x, col2x = px, px + pw / 2
    for i, node in ipairs(nodes) do
        local cx = ((i - 1) % 2 == 0) and col1x or col2x
        local ly = y + math.floor((i - 1) / 2) * 12
        if ly > WIN_H - 55 then break end
        sc(C.white, 0.35)
        love.graphics.setFont(fonts.tiny)
        love.graphics.print(node.id .. ". " .. node.name:sub(1, 9), cx, ly)
    end
    
    y = WIN_H - 28
    sc(C.accent, 0.15)
    love.graphics.rectangle("fill", SX + 8, y - 8, SIDEBAR_W - 16, 1)
    sc(C.white, 0.24)
    love.graphics.setFont(fonts.tiny)
    love.graphics.printf("[R] Restart   [ESC] Quit", px, y, pw, "center")
end

-------------------------------------------------------------------------------
-- MESSAGE BAR
-------------------------------------------------------------------------------
local function draw_message()
    local a = math.min(state.msg_timer, 1)
    if a <= 0 then return end
    local col = C.accent
    if state.msg_type == "good" then
        col = C.p1
    elseif state.msg_type == "bad" then
        col = C.super_c
    elseif state.msg_type == "warn" then
        col = C.nkabi_c
    end
    local bw = MAP_W - 40
    local bx = 20
    local by = WIN_H - 50
    love.graphics.setColor(C.bg[1], C.bg[2], C.bg[3], a * 0.95)
    love.graphics.rectangle("fill", bx, by, bw, 38, 6, 6)
    love.graphics.setColor(col[1], col[2], col[3], a * 0.72)
    love.graphics.setLineWidth(2)
    love.graphics.rectangle("line", bx, by, bw, 38, 6, 6)
    love.graphics.setFont(fonts.normal)
    love.graphics.setColor(1, 1, 1, a)
    love.graphics.printf(state.message, bx + 12, by + 12, bw - 24, "center")
end

-------------------------------------------------------------------------------
-- GAME OVER OVERLAY
-------------------------------------------------------------------------------
local function draw_game_over()
    if not state.game_over then return end
    local pulse = (math.sin(state.anim_timer * 2) + 1) / 2
    local col = state.winner == 1 and C.p1 or C.p2
    local cx, cy = MAP_W / 2, WIN_H / 2
    love.graphics.setColor(0, 0, 0, 0.82)
    love.graphics.rectangle("fill", 0, 0, MAP_W, WIN_H)
    love.graphics.setColor(col[1], col[2], col[3], 0.07 + pulse * 0.05)
    love.graphics.circle("fill", cx, cy, 200 + pulse * 35)
    rrect(cx - 240, cy - 120, 480, 240, 16, C.panel)
    sc(col, 0.52)
    love.graphics.setLineWidth(2.5)
    love.graphics.rectangle("line", cx - 240, cy - 120, 480, 240, 16, 16)
    love.graphics.setFont(fonts.huge)
    sc(col)
    love.graphics.printf("PLAYER " .. state.winner .. " WINS!", cx - 240, cy - 100, 480, "center")
    love.graphics.setFont(fonts.medium)
    sc(C.white, 0.78)
    love.graphics.printf("P1: " .. state.p1_score .. "  |  P2: " .. state.p2_score, cx - 240, cy + 20, 480, "center")
    love.graphics.setFont(fonts.small)
    sc(C.white, 0.42 + pulse * 0.24)
    love.graphics.printf("Press  R  to play again", cx - 240, cy + 70, 480, "center")
end

-------------------------------------------------------------------------------
-- LOVE.DRAW
-------------------------------------------------------------------------------
function love.draw()
    love.graphics.clear(C.bg)
    
    -- Subtle grid
    sc(C.white, 0.02)
    for gx = 0, MAP_W, 40 do
        for gy = 0, WIN_H, 40 do
            love.graphics.rectangle("fill", gx - 1, gy - 1, 2, 2)
        end
    end
    
    love.graphics.setScissor(0, 0, MAP_W, WIN_H)
    draw_routes()
    draw_nodes()
    love.graphics.setScissor()
    
    draw_sidebar()
    draw_message()
    draw_game_over()
    
    love.graphics.setFont(fonts.tiny)
    sc(C.white, 0.25)
    love.graphics.print("Moves: " .. math.floor(state.set_count / 2), 10, 8)
end

-------------------------------------------------------------------------------
-- INPUT
-------------------------------------------------------------------------------
function love.keypressed(key)
    if key == "escape" then love.event.quit() end
    if key == "r" or key == "R" then
        reset_game()
        update_valid_moves()
        set_msg("New game! P1 at Jozini · P2 at Kokstad", "info", 4)
        return
    end
    if state.game_over then return end
    if tonumber(key) then
        state.number_input = state.number_input .. key
        state.input_timer = 1.2
        return
    end
    if key == "return" or key == "kpenter" then
        if state.number_input ~= "" then confirm_input() end
        return
    end
    if key == "u" or key == "U" then
    -- Undo last move (requires storing move history)
    -- This is more complex — would need full state history
    end
    if key == "backspace" and #state.number_input > 0 then
        state.number_input = state.number_input:sub(1, -2)
        state.input_timer = #state.number_input > 0 and 0.8 or 0
    end
end