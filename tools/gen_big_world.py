"""Generator for data/big_world.txt (+ overlay): 200x200 tiles, 9 hand-planned regions.

Usage:  python tools/gen_big_world.py data/big_world.txt
Without a path it only prints stats (tile counts, connectivity from the @ start).
Deterministic: change SEED to get a different layout with the same plan.
"""
import math
import random
import sys
from collections import Counter, deque

W = H = 200
SEED = 20260914
rng = random.Random(SEED)

g = [['.'] * W for _ in range(H)]      # ground layer
o = [['.'] * W for _ in range(H)]      # overlay layer


def inb(x, y):
    return 0 <= x < W and 0 <= y < H


def put(x, y, ch, layer=None):
    layer = g if layer is None else layer
    if inb(x, y):
        layer[y][x] = ch


def rect(x0, y0, x1, y1, ch, layer=None):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(x, y, ch, layer)


def ring(x0, y0, x1, y1, ch, layer=None):
    for x in range(x0, x1 + 1):
        put(x, y0, ch, layer)
        put(x, y1, ch, layer)
    for y in range(y0, y1 + 1):
        put(x0, y, ch, layer)
        put(x1, y, ch, layer)


def ellipse(cx, cy, rx, ry, ch, layer=None, jitter=0.0):
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d <= 1.0 + (rng.uniform(-jitter, jitter) if jitter else 0):
                put(x, y, ch, layer)


def cellular(x0, y0, x1, y1, ch, fill_p, iters=4, background='.', birth=5, survive=4, feather=7):
    """Cellular-automata blob fill inside a rect.

    Sides of the rect that do not touch the map border are feathered: cells within
    `feather` tiles of such a side are thinned out with growing probability, so the
    biome fades into the neighbouring region instead of ending in a straight line.
    """
    w, h = x1 - x0 + 1, y1 - y0 + 1
    cells = [[rng.random() < fill_p for _ in range(w)] for _ in range(h)]
    for _ in range(iters):
        nxt = [[False] * w for _ in range(h)]
        for j in range(h):
            for i in range(w):
                n = 0
                for dj in (-1, 0, 1):
                    for di in (-1, 0, 1):
                        if di == 0 and dj == 0:
                            continue
                        ii, jj = i + di, j + dj
                        if 0 <= ii < w and 0 <= jj < h:
                            n += cells[jj][ii]
                        else:
                            n += 1  # edges count as filled -> blobs hug the region border
                nxt[j][i] = n >= birth if not cells[j][i] else n >= survive
        cells = nxt
    inner_left, inner_top = x0 > 1, y0 > 1
    inner_right, inner_bottom = x1 < W - 2, y1 < H - 2
    for j in range(h):
        for i in range(w):
            d = feather
            if inner_left:
                d = min(d, i)
            if inner_right:
                d = min(d, w - 1 - i)
            if inner_top:
                d = min(d, j)
            if inner_bottom:
                d = min(d, h - 1 - j)
            if d < feather and cells[j][i] and rng.random() > (d + 0.5) / feather:
                cells[j][i] = False
    for j in range(h):
        for i in range(w):
            put(x0 + i, y0 + j, ch if cells[j][i] else background)


def line(x0, y0, x1, y1, ch, width=1, layer=None, only_over=None):
    """Thick line. only_over: set of chars it may overwrite (None = any)."""
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for k in range(n + 1):
        t = k / n
        x = round(x0 + (x1 - x0) * t)
        y = round(y0 + (y1 - y0) * t)
        for dy in range(width):
            for dx in range(width):
                xx, yy = x + dx - width // 2, y + dy - width // 2
                if inb(xx, yy) and (only_over is None or g[yy][xx] in only_over):
                    put(xx, yy, ch, layer)


def path(points, ch, width=2, only_over=None, layer=None):
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        line(ax, ay, bx, by, ch, width, layer, only_over)


def meander(points, ch, width=3, amp=3, freq=0.25, only_over=None):
    """Polyline with a sine wobble - rivers and forest roads."""
    pts = []
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        n = max(abs(bx - ax), abs(by - ay), 1)
        for k in range(n + 1):
            t = k / n
            x = ax + (bx - ax) * t
            y = ay + (by - ay) * t
            length = math.hypot(bx - ax, by - ay) or 1
            nx, ny = -(by - ay) / length, (bx - ax) / length
            s = math.sin(len(pts) * freq) * amp
            pts.append((round(x + nx * s), round(y + ny * s)))
    for (x, y) in pts:
        for dy in range(width):
            for dx in range(width):
                xx, yy = x + dx - width // 2, y + dy - width // 2
                if inb(xx, yy) and (only_over is None or g[yy][xx] in only_over):
                    put(xx, yy, ch)
    return pts


def house(x, y, w=8, h=7, door='S', npc=True, dialogue=True, roof=True, wall='B'):
    """Walled house: B ring, 2-wide door gap, NPC inside, D outside the door, R roof on overlay."""
    ring(x, y, x + w - 1, y + h - 1, wall)
    rect(x + 1, y + 1, x + w - 2, y + h - 2, '.')
    mx, my = x + w // 2 - 1, y + h // 2 - 1
    if door == 'S':
        rect(mx, y + h - 1, mx + 1, y + h - 1, '.'); ox, oy = mx, y + h
    elif door == 'N':
        rect(mx, y, mx + 1, y, '.'); ox, oy = mx, y - 1
    elif door == 'E':
        rect(x + w - 1, my, x + w - 1, my + 1, '.'); ox, oy = x + w, my
    else:
        rect(x, my, x, my + 1, '.'); ox, oy = x - 1, my
    if dialogue:
        put(ox, oy, 'D')
    if npc:
        put(x + w // 2, y + h // 2, 'N')
    if roof:
        rect(x + 1, y + 1, x + w - 2, y + h - 2, 'R', o)


def stall(x, y):
    """Market stall: 3x2 roof over an NPC, no walls."""
    rect(x, y, x + 2, y + 1, 'R', o)
    put(x + 1, y, 'N')


def hill(cx, cy, rx, ry):
    """Hill: solid H roots on ground, H cap on overlay shifted one row down (like main_world)."""
    ellipse(cx, cy, rx, ry, 'H', jitter=0.15)
    ellipse(cx, cy + 1, rx, ry, 'H', layer=o)


def field(x0, y0, x1, y1):
    """Crop field: alternating rows of bushes and bare soil."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(x, y, '^' if (y - y0) % 2 == 0 else '.')


# ---------------------------------------------------------------------------
# 1. Base biome fills (later fills overwrite earlier ones)
# ---------------------------------------------------------------------------

# --- NW: Highland massif (rows 1-58, cols 1-62) --------------------------
cellular(1, 1, 62, 58, '#', 0.50, iters=5)
for _ in range(400):
    x, y = rng.randint(2, 61), rng.randint(2, 57)
    if g[y][x] == '.' and rng.random() < 0.35:
        put(x, y, '^')

# --- N: Ancient forest (rows 1-48, cols 63-138) --------------------------
cellular(63, 1, 138, 48, '^', 0.62, iters=3)
ellipse(100, 12, 9, 7, '.')              # shore
ellipse(100, 12, 7, 5, '~', jitter=0.1)  # spring lake - river source
for (cx, cy, r) in [(80, 30, 5), (122, 22, 5), (70, 12, 4), (128, 40, 4)]:
    ellipse(cx, cy, r, r * 0.75, '.')

# --- NE: Mire (rows 1-60, cols 140-198) ----------------------------------
cellular(140, 1, 198, 60, 'M', 0.58, iters=3)
for _ in range(14):
    cx, cy = rng.randint(146, 194), rng.randint(5, 56)
    ellipse(cx, cy, rng.randint(2, 4), rng.randint(1, 3), '~', jitter=0.2)
for _ in range(10):
    cx, cy = rng.randint(146, 194), rng.randint(5, 56)
    ellipse(cx, cy, rng.randint(2, 4), rng.randint(2, 3), '.')
    ellipse(cx, cy, 1.5, 1.2, '^')

# --- W: Green hills & farmland (rows 62-135, cols 1-62) ------------------
rect(1, 59, 62, 61, '.')
for (cx, cy, rx, ry) in [(14, 72, 7, 4), (32, 70, 6, 3), (12, 96, 6, 4),
                         (30, 92, 8, 4), (50, 84, 5, 3), (20, 118, 7, 4),
                         (44, 112, 6, 3)]:
    hill(cx, cy, rx, ry)
field(40, 96, 56, 102)
field(40, 122, 60, 128)
field(6, 128, 22, 134)
for _ in range(120):
    x, y = rng.randint(2, 61), rng.randint(62, 135)
    if g[y][x] == '.':
        put(x, y, '^')

# --- E: Great Lake district (rows 62-135, cols 138-198) ------------------
ellipse(168, 98, 24, 20, '~', jitter=0.08)
for _ in range(90):
    x, y = rng.randint(140, 197), rng.randint(63, 134)
    if g[y][x] == '.' and any(inb(x + dx, y + dy) and g[y + dy][x + dx] == '~'
                              for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
        put(x, y, '^')
ellipse(160, 92, 4, 3, '.')
ellipse(160, 92, 2, 1.5, '^')
ellipse(178, 108, 5, 3, '.')
ring(176, 107, 180, 109, '+')
put(178, 108, 'Q')                   # island shrine

# --- SW: Sunscar desert (rows 138-183, cols 1-72) ------------------------
cellular(1, 138, 72, 183, 'S', 0.70, iters=2)
for _ in range(8):
    cx, cy = rng.randint(6, 66), rng.randint(142, 178)
    ellipse(cx, cy, rng.randint(1, 3), rng.randint(1, 2), '#', jitter=0.2)
ellipse(30, 160, 7, 5, '.')           # oasis
ellipse(30, 160, 4, 2.5, '~')
for (dx, dy) in [(-6, -3), (6, -3), (-6, 3), (6, 3), (0, -5), (0, 5), (-7, 0), (7, 0)]:
    put(30 + dx, 160 + dy, '^')
put(24, 158, 'N')
put(24, 159, 'D')
put(36, 162, 'O')

# --- S: Coast (rows 138-183, cols 74-136) --------------------------------
for _ in range(60):
    x, y = rng.randint(74, 136), rng.randint(138, 178)
    if g[y][x] == '.':
        put(x, y, '^')

# --- SE: Ashen fortress grounds (rows 138-183, cols 138-198) -------------
cellular(138, 138, 198, 183, '#', 0.42, iters=4)
rect(148, 145, 192, 178, '.')

# --- Ocean & beach (rows ~181-198) ---------------------------------------
for x in range(1, W - 1):
    shore = 184 + round(1.5 * math.sin(x * 0.11) + math.sin(x * 0.05))
    for y in range(shore - 3, shore):
        put(x, y, 'S')
    for y in range(shore, H - 1):
        put(x, y, '~')

# ---------------------------------------------------------------------------
# 2. River: spring lake -> south past the village -> ocean; branch into the lake
# ---------------------------------------------------------------------------
meander([(100, 18), (112, 40), (128, 60), (132, 80), (130, 110),
         (128, 140), (126, 165), (124, 190)], '~', width=4, amp=2, freq=0.18)
meander([(132, 84), (146, 90)], '~', width=3, amp=1, freq=0.3)

# ---------------------------------------------------------------------------
# 3. Structures
# ---------------------------------------------------------------------------

# --- Village of Greenhollow (center) -------------------------------------
VX0, VY0, VX1, VY1 = 78, 74, 122, 120
rect(VX0 - 1, VY0 - 1, VX1 + 1, VY1 + 1, '.')
ring(VX0, VY0, VX1, VY1, 'B')
for gx in range(99, 102):
    put(gx, VY0, '.')
    put(gx, VY1, '.')
for gy in range(96, 99):
    put(VX0, gy, '.')
    put(VX1, gy, '.')
ring(96, 93, 104, 101, '+')          # square rim
rect(97, 94, 103, 100, '.')
rect(99, 96, 100, 97, '~')           # fountain
put(100, 91, '@')                    # player start
put(100, 103, 'Q')                   # quest board
put(96, 97, 'T')                     # lever by the fountain
for (hx, hy, d) in [(82, 78, 'S'), (91, 78, 'S'), (108, 78, 'S'), (113, 78, 'S'),
                    (82, 112, 'N'), (91, 112, 'N'), (108, 112, 'N'), (113, 112, 'N'),
                    (82, 92, 'E'), (82, 100, 'E'), (113, 92, 'W'), (113, 100, 'W')]:
    house(hx, hy, door=d)
for sx in (92, 96, 100, 104):
    stall(sx, 106)
for (tx, ty) in [(90, 86), (92, 88), (110, 86), (108, 88), (110, 108),
                 (88, 104), (112, 104), (91, 90), (109, 90)]:
    put(tx, ty, '^')

# --- Mountain dungeon (NW) ------------------------------------------------
DX0, DY0 = 10, 10
rect(DX0 - 2, DY0 - 2, DX0 + 32, DY0 + 32, '#')
rect(DX0, DY0, DX0 + 30, DY0 + 30, 'B')
rooms = {}
for ry in range(3):
    for rx in range(3):
        x0 = DX0 + 1 + rx * 10
        y0 = DY0 + 1 + ry * 10
        rect(x0, y0, x0 + 7, y0 + 7, '.')
        rooms[(rx, ry)] = (x0, y0)


def door_h(a):
    (x0, y0) = rooms[a]
    rect(x0 + 8, y0 + 3, x0 + 9, y0 + 4, '.')


def door_v(a):
    (x0, y0) = rooms[a]
    rect(x0 + 3, y0 + 8, x0 + 4, y0 + 9, '.')


door_v((1, 1)); door_h((0, 2)); door_h((1, 2))
door_v((0, 1)); door_v((2, 1)); door_h((0, 1))
door_v((0, 0)); door_h((0, 0)); door_h((1, 0))
cx, cy = rooms[(1, 1)]
rect(cx + 2, cy + 2, cx + 5, cy + 5, '+')
put(cx + 3, cy + 3, 'Q')
put(cx + 4, cy + 4, 'Q')
for k in [(0, 0), (2, 0), (0, 2), (2, 2)]:
    x0, y0 = rooms[k]
    put(x0 + 3, y0 + 3, 'T')
for k in [(1, 0), (0, 1), (2, 1)]:
    x0, y0 = rooms[k]
    rect(x0 + 2, y0 + 2, x0 + 5, y0 + 5, 'M')
x0, y0 = rooms[(2, 0)]
put(x0 + 6, y0 + 1, 'N')
ex, ey = rooms[(1, 2)]
for y in range(ey + 8, DY0 + 33):
    put(ex + 3, y, '.')
    put(ex + 4, y, '.')
put(ex + 3, DY0 + 33, 'D')
put(ex + 4, DY0 + 33, 'D')
DUNGEON_MOUTH = (ex + 3, DY0 + 34)

# --- Swamp witch hut (NE) -------------------------------------------------
rect(163, 20, 175, 30, '.')
house(166, 22, door='S')
put(171, 27, 'T')
path([(184, 53), (184, 58), (150, 58), (150, 57)], 'U', width=2)
put(184, 52, 'O')
put(150, 56, 'O')

# --- Hillside burrows (W) --------------------------------------------------
path([(22, 73), (22, 82), (26, 82), (26, 91)], 'U', width=2)
put(22, 72, 'O'); put(26, 92, 'O')
path([(6, 97), (6, 108), (13, 108), (13, 117)], 'U', width=2)
put(6, 96, 'O'); put(13, 118, 'O')
house(46, 88, door='S')
put(50, 95, 'T')

# --- Lakeside hamlet (E) ---------------------------------------------------
rect(140, 92, 152, 106, '.')
house(141, 94, door='E')
house(141, 101, door='E')
stall(149, 96)
path([(150, 99), (157, 99), (157, 93)], 'U', width=2)
put(160, 90, 'N'); put(160, 91, 'D')
path([(161, 93), (161, 108), (174, 108)], 'U', width=2)

# --- Desert temple (SW) ---------------------------------------------------
rect(50, 150, 66, 166, '.')
ring(52, 152, 64, 164, 'B'); ring(54, 154, 62, 162, 'B')
rect(55, 155, 61, 161, '+')
put(58, 158, 'Q')
put(58, 164, '.'); put(58, 162, '.')
put(52, 158, '.'); put(54, 158, '.')
put(57, 154, 'M'); put(59, 154, 'M')
put(58, 166, 'D')

# --- Harbor town (S) -------------------------------------------------------
rect(88, 160, 116, 181, '.')
house(90, 162, door='S'); house(98, 162, door='S'); house(106, 162, door='S')
house(94, 172, door='N'); house(104, 172, door='N')
for sx in (92, 100, 108):
    stall(sx, 169)
put(102, 170, 'Q')
path([(112, 180), (112, 192)], 'U', width=2)
rect(110, 192, 114, 193, 'U')
put(112, 193, 'N')

# --- Ashen fortress (SE) ---------------------------------------------------
FX0, FY0, FX1, FY1 = 154, 150, 186, 174
ring(FX0 - 3, FY0 - 3, FX1 + 3, FY1 + 3, '~')
ring(FX0 - 2, FY0 - 2, FX1 + 2, FY1 + 2, '~')
ring(FX0, FY0, FX1, FY1, '#'); ring(FX0 + 1, FY0 + 1, FX1 - 1, FY1 - 1, '#')
rect(FX0 + 2, FY0 + 2, FX1 - 2, FY1 - 2, '.')
for gy in range(161, 164):
    put(FX0, gy, '.'); put(FX0 + 1, gy, '.')
    for bx in (FX0 - 1, FX0 - 2, FX0 - 3):
        put(bx, gy, 'U')
    put(FX0 - 4, gy, '.')
ring(166, 156, 180, 168, 'B')
rect(167, 157, 179, 167, '.')
put(166, 162, '.')
rect(170, 159, 176, 165, '+')
put(173, 162, 'Q')
put(168, 158, 'T'); put(178, 158, 'T'); put(168, 166, 'T'); put(178, 166, 'T')
put(178, 160, 'N')
rect(167, 157, 179, 167, 'R', o)
house(156, 152, w=7, h=6, door='S', dialogue=False)
house(178, 152, w=7, h=6, door='S', dialogue=False)
put(160, 170, 'D')

# --- Forest shrine (N) -----------------------------------------------------
rect(96, 3, 104, 9, '.')
ring(97, 4, 103, 8, '+')
put(100, 6, 'Q'); put(99, 6, 'N')
put(100, 9, 'D')

# ---------------------------------------------------------------------------
# 4. Roads (carve through passable stuff; never through water/rock unless valley)
# ---------------------------------------------------------------------------
ROAD_OVER = set('.^MS')
VALLEY = ROAD_OVER | {'#'}

path([(100, 73), (100, 60), (104, 50), (98, 40), (104, 30), (100, 22)], '.', 2, ROAD_OVER)   # north
path([(100, 22), (92, 14), (92, 10), (100, 10)], '.', 2, ROAD_OVER)                           # around spring lake to shrine
path([(100, 121), (100, 140), (102, 160)], '.', 2, ROAD_OVER)                                  # south -> harbor
path([(77, 97), (66, 97), (58, 90), (52, 92)], '.', 2, ROAD_OVER)                              # west -> farm
path([(52, 92), (40, 90), (38, 80), (44, 66), (44, 60)], '.', 2, ROAD_OVER)                    # farm -> foothills
path([(44, 60), (44, 52), (34, 46), (34, 44)], '.', 3, VALLEY)                                 # valley to dungeon
path([(34, 44), DUNGEON_MOUTH], '.', 3, VALLEY)
path([(40, 90), (30, 104), (30, 118), (34, 136), (34, 150), (37, 160)], '.', 2, ROAD_OVER)     # hills -> desert -> oasis
path([(37, 160), (50, 158)], '.', 2, ROAD_OVER)                                                # oasis -> temple
path([(123, 97), (128, 97)], '.', 2, ROAD_OVER)                                                # east gate -> river
path([(136, 97), (140, 97)], '.', 2, ROAD_OVER)                                                # river -> hamlet
path([(146, 92), (146, 70), (150, 62), (160, 40), (170, 32)], '.', 2, ROAD_OVER)               # hamlet -> mire -> witch
path([(116, 172), (130, 172), (140, 162), (149, 162)], '.', 3, VALLEY)                         # harbor -> fortress
path([(116, 160), (128, 150), (150, 150), (150, 140), (150, 136)], '.', 2, VALLEY)             # fortress -> lake road
path([(150, 136), (146, 130), (146, 106)], '.', 2, ROAD_OVER)


def bridge_h(y, x_from, x_to):
    for x in range(x_from, x_to + 1):
        for yy in (y, y + 1):
            if g[yy][x] == '~':
                put(x, yy, 'U')
            elif g[yy][x] in ('.', '^'):
                put(x, yy, '.')


bridge_h(96, 126, 140)      # east road over the river
bridge_h(149, 120, 140)     # fortress/lake road over the river
bridge_h(172, 120, 140)     # harbor -> fortress road over the river
for y in range(84, 96):     # stepping stones across the feeder stream
    for xx in (146, 147):
        if g[y][xx] == '~':
            put(xx, y, 'U')

# ---------------------------------------------------------------------------
# 5. Border and cleanup
# ---------------------------------------------------------------------------
ring(0, 0, W - 1, H - 1, '#')
put(100, 91, '@')

# ---------------------------------------------------------------------------
# 6. Connectivity check (BFS over passable tiles from '@')
# ---------------------------------------------------------------------------
SOLID = set('#~BH')
start = next((x, y) for y in range(H) for x in range(W) if g[y][x] == '@')
seen = [[False] * W for _ in range(H)]
dq = deque([start])
seen[start[1]][start[0]] = True
while dq:
    x, y = dq.popleft()
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if inb(nx, ny) and not seen[ny][nx] and g[ny][nx] not in SOLID:
            seen[ny][nx] = True
            dq.append((nx, ny))
passable = sum(g[y][x] not in SOLID for y in range(H) for x in range(W))
reached = sum(seen[y][x] for y in range(H) for x in range(W))
poi_missing = [(g[y][x], x, y) for y in range(H) for x in range(W)
               if g[y][x] in 'NQTDO' and not seen[y][x]]
print(f"size {W}x{H}, passable {passable}, reachable from start {reached} ({reached / passable:.1%})")
print("unreachable POIs:", poi_missing)
print("ground chars:", dict(Counter(ch for row in g for ch in row)))
print("overlay chars:", dict(Counter(ch for row in o for ch in row)))

out = sys.argv[1] if len(sys.argv) > 1 else None
if out:
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(''.join(r) for r in g) + '\n')
    base = out[:-4]
    with open(base + '_overlay.txt', 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(''.join(r) for r in o) + '\n')
    print("written", out, "and", base + '_overlay.txt')
