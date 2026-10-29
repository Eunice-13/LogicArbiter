"""Clean up the layout of Arbiter-9-upgraded.json -> Arbiter-9_v3_clean.json.

Logic / netlist is preserved exactly; only board + component positions and the
paths + endpoints of the NEW wires change (each new wire endpoint is moved to a
free hole of the same 5-hole strip, so no wire endpoint sits in a component
pin's hole and no two wire endpoints share a hole).

Only the components approved for moving (the two rank DIP switches and their
pull-downs) plus the previously-added new components are repositioned.  Original
arbiter boards, LEDs, comparator, gates, resistors, Turn switches and all 307
original connections are left untouched.
"""
import json
import copy

SRC = 'Arbiter-9-upgraded.json'
DST = 'Arbiter-9_v3_clean.json'
N_ORIG_CONN = 307          # original connection count (unchanged)

OFF = {0: 72, 1: 96, 2: 120, 3: 144, 4: 168, 5: 216, 6: 240, 7: 264, 8: 288, 9: 312}

# wire colours (rule 6)
C_VCC = '#e53e3e'
C_GND = '#1a1a1a'
C_RANK_A = '#3182ce'      # A rank bus
C_RANK_B = '#805ad5'      # B rank bus
C_CTRL = '#d69e2e'        # Submit / Clock / Reset
C_STATUS = '#38a169'      # A_Done / B_Done / Display_Enable
C_GAMEOVER = '#dd6b20'    # Game_Over / Final
C_DISPLAY = '#ed8936'     # gated display outputs

d = json.load(open(SRC, encoding='utf-8'))
pins = json.load(open('_pins.json', encoding='utf-8'))

# the three new boards get their v3 positions immediately, so every coordinate
# computed below already refers to the clean layout.
V3_NEW_BOARDS = [
    {"index": 5, "cols": 63, "x": -1600, "y": 1300, "locked": False, "angle": 0, "sizeKey": "full", "rails": True},
    {"index": 6, "cols": 63, "x": 1900, "y": 1300, "locked": False, "angle": 0, "sizeKey": "full", "rails": True},
    {"index": 7, "cols": 63, "x": 288, "y": 1300, "locked": False, "angle": 0, "sizeKey": "full", "rails": True},
]

# --------------------------------------------------------------------------
# geometry helpers
# --------------------------------------------------------------------------
boards = {b['index']: b for b in d['boards'] if b['index'] <= 4}
for b in V3_NEW_BOARDS:
    boards[b['index']] = b


def coord(board, col, row):
    b = boards[board]
    return (b['x'] + 24 * col, b['y'] + OFF[row])


def half_of_row(row):
    return 0 if row <= 4 else 1


def locate(x, y):
    """(board, col, row) for a coordinate, or None."""
    x, y = int(round(x)), int(round(y))
    for bi, b in boards.items():
        if (x - b['x']) % 24:
            continue
        col = (x - b['x']) // 24
        if not (0 <= col <= b['cols']):
            continue
        for r, off in OFF.items():
            if b['y'] + off == y:
                return (bi, col, r)
    return None


def strip_of_coord(x, y):
    h = locate(x, y)
    if not h:
        return None
    return (h[0], h[1], half_of_row(h[2]))


def strip_holes(strip):
    b, c, half = strip
    rows = range(0, 5) if half == 0 else range(5, 10)
    return [(b, c, r) for r in rows]


# --------------------------------------------------------------------------
# placement (translate each part so a chosen reference pin lands on a target hole)
# --------------------------------------------------------------------------
orig_pos = {cid: (p['x'], p['y']) for cid, p in pins.items()}

# id -> (target_board, ref_pin, target_col, target_row)
PLACE = {
    # ---- PLAYER A board (5) at x=168, y=640 ----
    'c2':  (5, 'S1', 2, 2),
    'c4':  (5, 'A', 2, 4), 'c5': (5, 'A', 3, 4), 'c6': (5, 'A', 4, 4), 'c7': (5, 'A', 5, 4),
    'bA':  (5, 'OUT', 6, 2),
    'pA':  (5, 'A', 6, 4),
    'uA1': (5, '1', 9, 5),
    'uA2': (5, '1', 19, 5),
    'uA3': (5, '1', 28, 5),
    'rLA': (5, 'A', 37, 4),
    'LA':  (5, 'anode', 41, 4),
    # ---- PLAYER B board (6) at x=1800, y=640 (same order as A) ----
    'c3':  (6, 'S1', 2, 2),
    # on board 0 the B pull-downs sit under their own switch bit:
    # c9->S1, c10->S2, c11->S3, c8->S4
    'c8':  (6, 'A', 5, 4), 'c9': (6, 'A', 2, 4), 'c10': (6, 'A', 3, 4), 'c11': (6, 'A', 4, 4),
    'bB':  (6, 'OUT', 6, 2),
    'pB':  (6, 'A', 6, 4),
    'uB1': (6, '1', 9, 5),
    'uB2': (6, '1', 19, 5),
    'uB3': (6, '1', 28, 5),
    'rLB': (6, 'A', 37, 4),
    'LB':  (6, 'anode', 41, 4),
    # ---- SHARED CONTROL board (7) at x=984, y=1240 ----
    'bR':  (7, 'OUT', 2, 2),
    'pR':  (7, 'A', 2, 4),
    'uS1': (7, '1', 5, 5),
    'uS2': (7, '1', 15, 5),
    'uS3': (7, '1', 25, 5),
    'uS4': (7, '1', 35, 5),
    # indicator LEDs on their own row so they never share a strip with an IC pin
    'rGO': (7, 'A', 42, 2), 'LGO': (7, 'anode', 55, 7),
    'rLD1': (7, 'A', 45, 2), 'LD1': (7, 'anode', 57, 7),
    'rLD2': (7, 'A', 48, 2), 'LD2': (7, 'anode', 59, 7),
    'rLD3': (7, 'A', 51, 2), 'LD3': (7, 'anode', 61, 7),
}

new_pos = {}
for cid, (tb, ref, tcol, trow) in PLACE.items():
    px, py = pins[cid]['pins'][ref]
    tx, ty = coord(tb, tcol, trow)
    dx, dy = tx - px, ty - py
    new_pos[cid] = (orig_pos[cid][0] + dx, orig_pos[cid][1] + dy)

MOVED = set(PLACE)
print('repositioned', len(MOVED), 'components')


def pin_xy(cid, label):
    """Coordinate of a pin after repositioning."""
    x, y = pins[cid]['pins'][label]
    if cid in new_pos:
        ox, oy = orig_pos[cid]
        nx, ny = new_pos[cid]
        x, y = x + (nx - ox), y + (ny - oy)
    return (int(round(x)), int(round(y)))


# --------------------------------------------------------------------------
# occupancy
# --------------------------------------------------------------------------
pin_holes = set()
for cid, p in pins.items():
    for label in p['pins']:
        h = locate(*pin_xy(cid, label))
        if h:
            pin_holes.add(h)

used_holes = set()
for conn in d['connections']:
    for e in (conn['a'], conn['b']):
        if e['type'] == 'hole':
            used_holes.add((e['board'], e['col'], e['row']))

tape = {}   # (strip) -> next free-hole cursor


def free_hole(strip):
    for h in strip_holes(strip):
        if h in pin_holes or h in used_holes:
            continue
        used_holes.add(h)
        return {'type': 'hole', 'board': h[0], 'col': h[1], 'row': h[2]}
    raise RuntimeError('no free hole in strip ' + str(strip))


# --------------------------------------------------------------------------
# rebuild the NEW connections (index >= N_ORIG_CONN) with hole endpoints
# --------------------------------------------------------------------------
# taps that used to land in an original pin's hole are re-pointed at the rank
# DIP switch's own strip on the player board.  The correct switch bit for each
# old tap is derived from the ORIGINAL connectivity (never assumed).
def strip_root_map(path):
    dd = json.load(open(path, encoding='utf-8'))
    par = {}

    def find(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            par[ra] = rb

    def node(e):
        if e['type'] == 'pin':
            return ('P', e['partId'], e['pin'])
        if e['type'] == 'hole':
            return ('S', e['board'], e['col'], 0 if e['row'] <= 4 else 1)
        if e['type'] == 'bus':
            return ('R', e['board'], e['bus'])
        return ('?', json.dumps(e, sort_keys=True))

    for c in dd['connections']:
        union(node(c['a']), node(c['b']))
    return find

before_find = strip_root_map(SRC)


def switch_strip_for(tap_key):
    root = before_find(('S', tap_key[0], tap_key[1], 0 if tap_key[2] <= 4 else 1))
    for col in list(range(1, 5)) + list(range(25, 29)):
        if before_find(('S', 0, col, 0)) == root:
            if col <= 4:
                return (5, col + 1, 0)      # PLAYER A board
            return (6, col - 23, 0)         # PLAYER B board
    return None


TAP_REMAP = {}
for conn in d['connections'][N_ORIG_CONN:]:
    for e in (conn['a'], conn['b']):
        if e['type'] == 'hole':
            k = (e['board'], e['col'], e['row'])
            s = switch_strip_for(k)
            if s:
                TAP_REMAP[k] = s
print('rank-bit taps re-pointed to switch strips:', len(TAP_REMAP))

new_conns = []
for conn in d['connections'][N_ORIG_CONN:]:
    a, b = conn['a'], conn['b']
    out = {'color': conn['color'], 'locked': False, 'pivots': []}

    def convert(e):
        if e['type'] == 'pin':
            xy = pin_xy(e['partId'], e['pin'])
            s = strip_of_coord(*xy)
            if s is None:
                raise RuntimeError('pin off-board: %s:%s at %s' % (e['partId'], e['pin'], xy))
            return free_hole(s)
        if e['type'] == 'hole':
            key = (e['board'], e['col'], e['row'])
            if key in TAP_REMAP:
                return free_hole(TAP_REMAP[key])
            return free_hole(strip_of_coord(*coord(e['board'], e['col'], e['row'])))
        if e['type'] == 'bus' and e['board'] == 1:
            # feed the new boards from board 0's supply rails (same nets, shorter run)
            return {'type': 'bus', 'board': 0, 'bus': 'TP' if e['bus'] == 'TP' else 'BN', 'col': 1}
        return dict(e)

    out['a'] = convert(a)
    out['b'] = convert(b)
    new_conns.append(out)

# --------------------------------------------------------------------------
# bridges: keep the moved DIP switches + pull-downs wired to the original
# board-0 strips that still carry the original feed / GND wires.
# --------------------------------------------------------------------------
BRIDGES = [
    # A rank bits: new switch strip -> old board-0 strip (0, col, 0)
    ((5, 2, 0), (0, 1, 0)), ((5, 3, 0), (0, 2, 0)),
    ((5, 4, 0), (0, 3, 0)), ((5, 5, 0), (0, 4, 0)),
    # B rank bits
    ((6, 2, 0), (0, 25, 0)), ((6, 3, 0), (0, 26, 0)),
    ((6, 4, 0), (0, 27, 0)), ((6, 5, 0), (0, 28, 0)),
    # A pull-down bottoms -> old board-0 GND strips
    ((5, 2, 1), (0, 1, 1)), ((5, 3, 1), (0, 2, 1)),
    ((5, 4, 1), (0, 3, 1)), ((5, 5, 1), (0, 4, 1)),
    # B pull-down bottoms
    ((6, 2, 1), (0, 25, 1)), ((6, 3, 1), (0, 26, 1)),
    ((6, 4, 1), (0, 27, 1)), ((6, 5, 1), (0, 28, 1)),
]
for src, dst in BRIDGES:
    new_conns.append({'a': free_hole(src), 'b': free_hole(dst),
                      'color': C_RANK_A if src[0] == 5 else C_RANK_B,
                      'locked': False, 'pivots': []})

print('new connections:', len(new_conns))

# --------------------------------------------------------------------------
# colours (rule 6)
# --------------------------------------------------------------------------
for conn in new_conns:
    eps = [conn['a'], conn['b']]
    kinds = set()
    for e in eps:
        if e['type'] == 'pin':
            kinds.add(e['partId'])
        elif e['type'] == 'bus':
            kinds.add('BUS' + e['bus'])
    # power
    if any(e['type'] == 'bus' and e['bus'] in ('TP', 'BP') for e in eps):
        conn['color'] = C_VCC
    elif any(e['type'] == 'bus' and e['bus'] in ('TN', 'BN') for e in eps):
        conn['color'] = C_GND

# --------------------------------------------------------------------------
# orthogonal pivots (rule 3)
# --------------------------------------------------------------------------
RAIL_OFF = {'TP': 0, 'TN': 24, 'BP': 360, 'BN': 384}


def pixel(e):
    if e['type'] == 'hole':
        return coord(e['board'], e['col'], e['row'])
    if e['type'] == 'bus':
        b = boards[e['board']]
        return (b['x'] + 24 * e['col'], b['y'] + RAIL_OFF[e['bus']])
    return None


board_y = {bi: (b['y'], b['y'] + 384) for bi, b in boards.items()}


# --------------------------------------------------------------------------
# orthogonal routing through reserved free bands / corridors
# --------------------------------------------------------------------------
# free horizontal bands and vertical corridors in the canvas (no board, no
# original wire lane lives there), each with its own parallel-lane allocator
BAND_A = ('bandA', 528, 24, 1, 1272)     # below board0, above the new row
BAND_B = ('bandB', -1224, 24, -1, -1600)  # above board4 (unlimited upward)
CORR_L = ('corrL', 156, 24, -1, 108)     # between board3 (max x 96) and board0
CORR_R = ('corrR', 1824, 24, 1, 1872)    # between board4 (max 1800) and player B

lane_lists = {}


def alloc(spec, lo, hi):
    key, base, step, direction, limit = spec
    used = lane_lists.setdefault(key, [])
    i = 0
    while True:
        v = base + direction * step * i
        if direction > 0 and v > limit:
            raise RuntimeError('lane %s exhausted' % key)
        if direction < 0 and v < limit:
            raise RuntimeError('lane %s exhausted' % key)
        if not any(j == i and not (hi <= a or b <= lo) for j, (a, b) in used):
            used.append((i, (lo, hi)))
            return v
        i += 1


def jog(P, Q):
    """same-board wire: step 12px off the hole column, then across"""
    if P[0] == Q[0] or P[1] == Q[1]:
        return []
    jx, jy = P[0] + 12, Q[0] + 12
    return [[jx, P[1]], [jx, Q[1]], [jy, Q[1]]]


def route(conn):
    a, b = conn['a'], conn['b']
    P, Q = pixel(a), pixel(b)
    if P is None or Q is None or P == Q:
        return []
    fb, tb = a.get('board', -1), b.get('board', -1)
    if fb == tb:
        return jog(P, Q)
    new_row = {5, 6, 7}
    # 1) player/shared <-> player/shared : one band below board0
    if fb in new_row and tb in new_row:
        y = alloc(BAND_A, min(P[0], Q[0]), max(P[0], Q[0]))
        return [[P[0], y], [Q[0], y]]
    # 2) player/shared <-> board0 (rank DIP bridges)
    if (fb in new_row and tb == 0) or (fb == 0 and tb in new_row):
        y = alloc(BAND_A, min(P[0], Q[0]), max(P[0], Q[0]))
        return [[P[0], y], [Q[0], y]]
    # 3) arbiter result tap (board 4) <-> shared board (7)
    if (fb == 4 and tb in new_row) or (tb == 4 and fb in new_row):
        if fb == 4:
            Pp, Qq = P, Q
        else:
            Pp, Qq = Q, P
        corr = CORR_L if Pp[0] < 900 else CORR_R
        cx = alloc(corr, min(Pp[1], 0), max(Qq[1], 0))
        yTop = alloc(BAND_B, min(Pp[0], cx), max(Pp[0], cx))
        yBot = alloc(BAND_A, min(cx, Qq[0]), max(cx, Qq[0]))
        return [[Pp[0], yTop], [cx, yTop], [cx, yBot], [Qq[0], yBot]]
    # 4) supply tie to board0 rails
    if {fb, tb} & {5, 6, 7} and 0 in (fb, tb):
        if fb in new_row:
            Pp, Qq = P, Q
        else:
            Pp, Qq = Q, P
        if Qq[1] < 300:      # board0 top rail -> go up the corridor
            corr = CORR_L if Pp[0] < 900 else CORR_R
            cx = alloc(corr, min(Pp[1], Qq[1]), max(Pp[1], Qq[1]))
            y = alloc(BAND_A, min(Pp[0], cx), max(Pp[0], cx))
            return [[Pp[0], y], [cx, y], [cx, Qq[1]], [Qq[0], Qq[1]]]
        y = alloc(BAND_A, min(Pp[0], Qq[0]), max(Pp[0], Qq[0]))
        return [[Pp[0], y], [Qq[0], y]]
    # fallback
    y = alloc(BAND_A, min(P[0], Q[0]), max(P[0], Q[0]))
    return [[P[0], y], [Q[0], y]]


for conn in new_conns:
    conn['pivots'] = route(conn)

# --------------------------------------------------------------------------
# assemble output
# --------------------------------------------------------------------------
out = copy.deepcopy(d)
for part in out['parts']:
    if part['id'] in new_pos:
        part['x'], part['y'] = new_pos[part['id']]

# boards
out['boards'] = [b for b in out['boards'] if b['index'] <= 4]
out['boards'] += V3_NEW_BOARDS
out['connections'] = d['connections'][:N_ORIG_CONN] + new_conns
out['name'] = 'Arbiter-9 v3 clean (ranks stored + submission control)'

# notes: board titles + connection-area labels
notes = [n for n in out['notes'] if n['id'] not in
         ('note_9101', 'note_9102', 'note_9103', 'note_9105')]
notes += [
    {"id": "note_9200", "text": "PLAYER A", "x": -1618, "y": 1260, "w": 300, "h": 34,
     "color": "#000000", "fontSize": 18, "fontFamily": "Arial", "bold": True, "italic": False, "underline": False},
    {"id": "note_9201", "text": "PLAYER B", "x": 1882, "y": 1260, "w": 300, "h": 34,
     "color": "#000000", "fontSize": 18, "fontFamily": "Arial", "bold": True, "italic": False, "underline": False},
    {"id": "note_9202", "text": "SHARED CONTROL", "x": 270, "y": 1260, "w": 400, "h": 34,
     "color": "#000000", "fontSize": 18, "fontFamily": "Arial", "bold": True, "italic": False, "underline": False},
    {"id": "note_9203", "text": "PLAYER A edge -> SHARED: A_Done, /Reset, /Game_Over.  A rank bus A3..A0 stays on this board.", "x": -1618, "y": 1720, "w": 1000, "h": 40,
     "color": "#000000", "fontSize": 12, "fontFamily": "Arial", "bold": False, "italic": False, "underline": False},
    {"id": "note_9204", "text": "PLAYER B edge -> SHARED: B_Done, /Reset, /Game_Over.  B rank bus B3..B0 stays on this board.", "x": 1882, "y": 1720, "w": 1000, "h": 40,
     "color": "#000000", "fontSize": 12, "fontFamily": "Arial", "bold": False, "italic": False, "underline": False},
    {"id": "note_9205", "text": "SHARED edge -> PLAYER A/B: Display_Enable, /Reset, /Game_Over.  -> arbiter: A_Win/Tie/B_Win, A_Final/B_Final taps.", "x": 270, "y": 1720, "w": 1400, "h": 40,
     "color": "#000000", "fontSize": 12, "fontFamily": "Arial", "bold": False, "italic": False, "underline": False},
    {"id": "note_9206", "text": "A/B rank DIP switches were MOVED onto the player boards (approved). The original arbiter boards, 9 LEDs and Turn switches are unchanged.",
     "x": -1300, "y": 520, "w": 1400, "h": 60, "color": "#000000", "fontSize": 12, "fontFamily": "Arial", "bold": False, "italic": False, "underline": False},
]
out['notes'] = notes

json.dump(out, open(DST, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print('wrote', DST)
print('parts', len(out['parts']), 'boards', len(out['boards']), 'connections', len(out['connections']), 'notes', len(out['notes']))
