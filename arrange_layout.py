"""Rearrange the breadboards and re-route the wires (reference style).

Arbiter-9_v3_clean.json  ->  Arbiter-9_v5_arranged.json

  PLAYER A (far left) | centre column (9-LED / arbiter2 / arbiter1 / turn+supply / SHARED) | PLAYER B (far right)

* board positions follow the reference file final-na-to-ata.json for boards 1/2/3/4.
* the empty small breadboard (index 0) is removed; the nets its wires carried are
  re-connected on the boards that really use them.
* a wire whose two ends are on the SAME board simply moves with that board;
  only wires between different boards are re-routed.
* the netlist is preserved exactly.
"""
import copy
import json
import collections

SRC = 'Arbiter-9_v3_clean.json'
DST = 'Arbiter-9_v5_arranged.json'
N_ORIG = 307

OFF = {0: 72, 1: 96, 2: 120, 3: 144, 4: 168, 5: 216, 6: 240, 7: 264, 8: 288, 9: 312}
RAIL_OFF = {'TP': 0, 'TN': 24, 'BP': 360, 'BN': 384}

C_VCC, C_GND = '#e53e3e', '#1a1a1a'
C_RANK_A, C_RANK_B = '#3182ce', '#805ad5'
C_CTRL, C_STATUS, C_GAMEOVER, C_DISPLAY, C_TEAL = '#d69e2e', '#38a169', '#dd6b20', '#ed8936', '#319795'

d = json.load(open(SRC, encoding='utf-8'))
pins = json.load(open('_pins.json', encoding='utf-8'))

# reference positions (final-na-to-ata.json) for 1/2/3/4, new ones for the rest
NEW_POS = {1: (288, -336), 2: (288, -888), 3: (-600, 192), 4: (288, -1440),
           5: (-2400, -348), 6: (2208, -348), 7: (288, 744)}
OLD = {b['index']: (b['x'], b['y']) for b in d['boards']}
DELTA = {b: (NEW_POS[b][0] - OLD[b][0], NEW_POS[b][1] - OLD[b][1]) for b in NEW_POS}
print('board deltas:', DELTA)

boards = {}
for b in d['boards']:
    if b['index'] == 0:
        continue
    nb = dict(b)
    nb['x'], nb['y'] = NEW_POS[b['index']]
    nb['locked'] = False
    boards[b['index']] = nb


def comp_board(cid):
    hits = collections.Counter()
    for label in pins[cid]['pins']:
        x, y = pins[cid]['pins'][label]
        for b in d['boards']:
            if (int(round(x)) - b['x']) % 24 == 0 and 0 <= (int(round(x)) - b['x']) // 24 <= b['cols']:
                c = (int(round(x)) - b['x']) // 24
                for r, off in OFF.items():
                    if b['y'] + off == int(round(y)):
                        hits[b['index']] += 1
    return hits.most_common(1)[0][0] if hits else None


part_board = {p['id']: comp_board(p['id']) for p in d['parts']}
# the supply sits on the Turn+supply breadboard even though its legs are off the
# grid, so it must move with board 3
part_board['c2132'] = 3
newpart = {}
for p in d['parts']:
    b = part_board[p['id']]
    if b in DELTA:
        newpart[p['id']] = (p['x'] + DELTA[b][0], p['y'] + DELTA[b][1])


def coord(b, col, row):
    return (boards[b]['x'] + 24 * col, boards[b]['y'] + OFF[row])


def locate(x, y):
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


def strip_of(x, y):
    h = locate(x, y)
    return None if not h else (h[0], h[1], 0 if h[2] <= 4 else 1)


def pin_xy(cid, label):
    x, y = pins[cid]['pins'][label]
    if cid in newpart:
        return (int(round(x + newpart[cid][0] - pins[cid]['x'])),
                int(round(y + newpart[cid][1] - pins[cid]['y'])))
    return (int(round(x)), int(round(y)))


pin_holes = set()
for cid in pins:
    for label in pins[cid]['pins']:
        h = locate(*pin_xy(cid, label))
        if h:
            pin_holes.add(h)

# ---- split by board membership -------------------------------------------
same_board, cross_board = [], []
for i, c in enumerate(d['connections']):
    bs = set()
    for e in (c['a'], c['b']):
        if e['type'] == 'hole':
            bs.add(e['board'])
        elif e['type'] == 'bus':
            bs.add(e['board'])
        elif e['type'] == 'pin':
            bs.add(part_board[e['partId']])
    if 0 in bs:
        continue
    if len(bs) == 1 and i < N_ORIG:
        same_board.append(c)          # moves rigidly with its board
    else:
        cross_board.append(c)         # re-routed

used_holes = set()
for c in same_board + cross_board:
    for e in (c['a'], c['b']):
        if e['type'] == 'hole':
            used_holes.add((e['board'], e['col'], e['row']))


def free_hole(strip):
    b, c, half = strip
    for r in (range(0, 5) if half == 0 else range(5, 10)):
        h = (b, c, r)
        if h not in pin_holes and h not in used_holes:
            used_holes.add(h)
            return {'type': 'hole', 'board': b, 'col': c, 'row': r}
    raise RuntimeError('no free hole in strip %s' % (strip,))


def col_map(b0col):
    if 1 <= b0col <= 4:
        return (5, b0col + 1)
    if 25 <= b0col <= 28:
        return (6, b0col - 23)
    return None


repl = []


def add(color, a, b):
    repl.append({'a': a, 'b': b, 'color': color, 'locked': False, 'pivots': []})


for c in d['connections'][:N_ORIG]:
    tb = {e['board'] for e in (c['a'], c['b']) if e['type'] in ('hole', 'bus')}
    if 0 not in tb:
        continue
    hb0 = next((e for e in (c['a'], c['b']) if e['type'] == 'hole' and e['board'] == 0), None)
    if hb0 is None:
        continue
    other = c['b'] if hb0 is c['a'] else c['a']
    pb, pc = col_map(hb0['col'])
    if other['type'] == 'hole' and other['board'] == 1:
        add(C_RANK_A if pb == 5 else C_RANK_B, free_hole((pb, pc, 0)),
            free_hole((1, other['col'], 0 if other['row'] <= 4 else 1)))
    elif other['type'] == 'bus':
        # pull-down bottom -> the board's own GND rail (short black stub)
        add(C_GND, free_hole((pb, pc, 1)), {'type': 'bus', 'board': pb, 'bus': 'BN', 'col': pc})

for b in (5, 6, 7):
    # VCC and GND use each board's own rails, so the player/shared boards are now
    # really tied to the supply ground (approved fix)
    add(C_VCC, {'type': 'bus', 'board': b, 'bus': 'TP', 'col': 7},
        {'type': 'bus', 'board': 1, 'bus': 'TP', 'col': 7})
    add(C_GND, {'type': 'bus', 'board': b, 'bus': 'BN', 'col': 7},
        {'type': 'bus', 'board': 1, 'bus': 'BN', 'col': 7})
add(C_VCC, {'type': 'bus', 'board': 3, 'bus': 'TP', 'col': 29},
    {'type': 'bus', 'board': 1, 'bus': 'TP', 'col': 29})
add(C_GND, {'type': 'bus', 'board': 3, 'bus': 'BN', 'col': 29},
    {'type': 'bus', 'board': 1, 'bus': 'BN', 'col': 29})

# ---- orthogonal router with a channel registry ---------------------------
# every horizontal/vertical segment of every wire is registered so a new wire can
# never overlap one; rows that lie inside a breadboard are only usable by wires
# that belong to that board.
SIDE = (5, 6)
CY = {1: -696, 2: -144, 3: 384, 4: -1248, 5: -156, 6: -156, 7: 936}


def bbox(bi):
    b = boards[bi]
    return (b['x'], b['y'], b['x'] + 24 * b['cols'] + 120, b['y'] + 384)


def vclear(x, y1, y2, own):
    """vertical run may only touch its own board"""
    lo, hi = min(y1, y2), max(y1, y2)
    for bi in boards:
        if bi == own:
            continue
        x0, y0, x1, y1b = bbox(bi)
        if x0 <= x <= x1 and not (hi < y0 or lo > y1b):
            return False
    return True


_hr = {}
_vr = {}


def hfree(y, lo, hi):
    lo, hi = min(lo, hi), max(lo, hi)
    return not any(not (hi <= a or b <= lo) for a, b in _hr.get(y, []))


def vfree(x, lo, hi):
    lo, hi = min(lo, hi), max(lo, hi)
    return not any(not (hi <= a or b <= lo) for a, b in _vr.get(x, []))


def reg_h(y, lo, hi):
    _hr.setdefault(y, []).append((min(lo, hi), max(lo, hi)))


def reg_v(x, lo, hi):
    _vr.setdefault(x, []).append((min(lo, hi), max(lo, hi)))


# free canvas rows: no breadboard spans them
FREE_ROWS = [y for y in range(-3600, 3600, 12)
             if not any(b['y'] <= y <= b['y'] + 384 for b in boards.values())]


def segs_of(pts):
    return [(a, b) for a, b in zip(pts, pts[1:]) if a and b]


def cross_count(segs, others):
    n = 0
    for (x1, y1), (x2, y2) in segs:
        for (x3, y3), (x4, y4) in others:
            if x1 == x2 and x3 == x4:
                if x1 == x3 and not (max(y1, y2) < min(y3, y4) or max(y3, y4) < min(y1, y2)):
                    n += 1
            elif y1 == y2 and y3 == y4:
                if y1 == y3 and not (max(x1, x2) < min(x3, x4) or max(x3, x4) < min(x1, x2)):
                    n += 1
            elif x1 == x2:
                if min(x3, x4) <= x1 <= max(x3, x4) and min(y1, y2) <= y3 <= max(y1, y2):
                    n += 1
            elif y1 == y2:
                if min(y3, y4) <= y1 <= max(y3, y4) and min(x1, x2) <= x3 <= max(x1, x2):
                    n += 1
    return n


ORIG_SEGS = []      # kept (unmoved) wiring, for crossing avoidance


def pixel(e):
    if e['type'] == 'hole':
        return coord(e['board'], e['col'], e['row'])
    if e['type'] == 'bus':
        b = boards[e['board']]
        return (b['x'] + 24 * e['col'], b['y'] + RAIL_OFF[e['bus']])
    if e['type'] == 'pin':
        return pin_xy(e['partId'], e['pin'])
    return None


for c in same_board:
    pts = [pixel(c['a'])] + [tuple(p) for p in (c.get('pivots') or [])] + [pixel(c['b'])]
    if all(pts):
        for s in segs_of(pts):
            ORIG_SEGS.append(s)


OFFSETS = (0, 12, -12, 24, -24, 36, -36, 48, -48, 60, -60, 72, -72)
NEW_SEGS = []


def route(conn):
    a, b = conn['a'], conn['b']
    P, Q = pixel(a), pixel(b)
    if P is None or Q is None or P == Q:
        return []
    fb, tb = a.get('board', -1), b.get('board', -1)
    if fb == -1:
        fb = part_board[a['partId']]
    if tb == -1:
        tb = part_board[b['partId']]
    same = fb == tb
    if same:
        ys = [boards[fb]['y'] + 12 + 12 * k for k in range(29)]
        own = fb
    else:
        ys = list(FREE_ROWS)
        own = fb
    ys.sort(key=lambda y: abs(y - (P[1] + Q[1]) / 2))
    # a straight run is always preferable when it is free
    if P[0] == Q[0] and vfree(P[0], P[1], Q[1]):
        reg_v(P[0], P[1], Q[1])
        NEW_SEGS.append((P, Q))
        return []
    if P[1] == Q[1] and hfree(P[1], P[0], Q[0]):
        reg_h(P[1], P[0], Q[0])
        NEW_SEGS.append((P, Q))
        return []
    best = None
    tried = 0
    for y in ys[:300]:
        for dxp in OFFSETS:
            xP = P[0] + dxp
            if not vclear(xP, P[1], y, own):
                continue
            if not vfree(xP, P[1], y):
                continue
            for dxq in OFFSETS:
                xQ = Q[0] + dxq
                if xQ == xP:
                    continue
                if not vclear(xQ, Q[1], y, tb):
                    continue
                if not vfree(xQ, Q[1], y):
                    continue
                if not hfree(y, xP, xQ):
                    continue
                if xP != P[0] and not hfree(P[1], P[0], xP):
                    continue
                if xQ != Q[0] and not hfree(Q[1], Q[0], xQ):
                    continue
                pts = [[xP, P[1]], [xP, y], [xQ, y], [xQ, Q[1]]]
                segs = segs_of([P] + [tuple(p) for p in pts] + [Q])
                tried += 1
                score = cross_count(segs, ORIG_SEGS) + 2 * cross_count(segs, NEW_SEGS)
                if best is None or score < best[0]:
                    best = (score, pts, segs)
                break
            if best is not None and tried >= 60:
                break
        if best is not None and tried >= 60:
            break
    if best is None:
        return None
    pts = best[1]
    for (x1, y1), (x2, y2) in best[2]:
        NEW_SEGS.append(((x1, y1), (x2, y2)))
        if y1 == y2:
            reg_h(y1, x1, x2)
        elif x1 == x2:
            reg_v(x1, y1, y2)
    return pts


# register the wires that stay put first, so the router keeps clear of them
for c in same_board:
    pts = [pixel(c['a'])] + [tuple(p) for p in (c.get('pivots') or [])] + [pixel(c['b'])]
    for (x1, y1), (x2, y2) in segs_of(pts):
        if y1 == y2:
            reg_h(y1, x1, x2)
        elif x1 == x2:
            reg_v(x1, y1, y2)

work = cross_board + repl
# route the longest wires first: they claim the cleanest lanes, the short ones
# then fit around them


def wire_len(c):
    P, Q = pixel(c['a']), pixel(c['b'])
    if not P or not Q:
        return 0
    return abs(P[0] - Q[0]) + abs(P[1] - Q[1])


for conn in sorted(work, key=wire_len, reverse=True):
    conn['pivots'] = route(conn)

# wires the first pass could not place get a second attempt, now that every other
# wire is fixed; anything still unplaced falls back to a straight run
for conn in [c for c in work if c['pivots'] is None]:
    pts = route(conn)
    if pts is None:
        P, Q = pixel(conn['a']), pixel(conn['b'])
        for (x1, y1), (x2, y2) in segs_of([P, Q]):
            NEW_SEGS.append(((x1, y1), (x2, y2)))
            if y1 == y2:
                reg_h(y1, x1, x2)
            elif x1 == x2:
                reg_v(x1, y1, y2)
        pts = []
    conn['pivots'] = pts

# a same-board wire just moves with its board: translate its bend points
for c in same_board:
    if c.get('pivots'):
        bs = None
        for e in (c['a'], c['b']):
            if e['type'] == 'hole':
                bs = e['board']
            elif e['type'] == 'pin':
                bs = part_board[e['partId']]
        dx, dy = DELTA.get(bs, (0, 0))
        c['pivots'] = [[p[0] + dx, p[1] + dy] for p in c['pivots']]

# no wire may go straight from PLAYER A to PLAYER B: split through the shared board
par = {}


def finds(x):
    par.setdefault(x, x)
    while par[x] != x:
        par[x] = par[par[x]]
        x = par[x]
    return x


def unions(a, b):
    ra, rb = finds(a), finds(b)
    if ra != rb:
        par[ra] = rb


def nd(e):
    if e['type'] == 'pin':
        return ('P', e['partId'], e['pin'])
    if e['type'] == 'hole':
        return ('S', e['board'], e['col'], 0 if e['row'] <= 4 else 1)
    if e['type'] == 'bus':
        return ('R', e['board'], e['bus'])
    return ('?',)


for c in d['connections']:
    unions(nd(c['a']), nd(c['b']))
for cid in pins:
    for label in pins[cid]['pins']:
        s = strip_of(*pin_xy(cid, label))
        if s:
            unions(('P', cid, label), ('S',) + s)

for c in list(work):
    bs = set()
    for e in (c['a'], c['b']):
        bs.add(e.get('board') if e['type'] in ('hole', 'bus') else part_board[e['partId']])
    if bs == {5, 6}:
        work.remove(c)
        target = None
        for col in range(64):
            for half in (0, 1):
                for r in (range(0, 5) if half == 0 else range(5, 10)):
                    if finds(('S', 7, col, half)) == finds(nd(c['a'])) and (7, col, r) not in pin_holes:
                        target = (7, col, half)
                        break
                if target:
                    break
            if target:
                break
        if target:
            for e in (c['a'], c['b']):
                cc = {'a': free_hole(target), 'b': e, 'color': c['color'], 'locked': False, 'pivots': []}
                pts = route(cc)
                cc['pivots'] = pts if pts is not None else []
                work.append(cc)

out = copy.deepcopy(d)
for p in out['parts']:
    if p['id'] in newpart:
        p['x'], p['y'] = newpart[p['id']]
# renumber the boards to a contiguous 0..6 run (the simulator requires index 0),
# in physical order: centre column top->bottom, then PLAYER A, then PLAYER B
ORDER = [4, 2, 1, 3, 7, 5, 6]
remap = {old: new for new, old in enumerate(ORDER)}
out['boards'] = [dict(boards[old], index=remap[old]) for old in ORDER]


def remap_board(e):
    e = dict(e)
    if e['type'] in ('hole', 'bus'):
        e['board'] = remap[e['board']]
    return e


out['connections'] = [{'a': remap_board(c['a']), 'b': remap_board(c['b']),
                       'color': c['color'], 'locked': False,
                       'pivots': c.get('pivots', [])}
                      for c in same_board + work]
out['name'] = 'Arbiter-9 v5 arranged (PLAYER A left, PLAYER B right, centre column)'
out['notes'] = [n for n in d['notes'] if n['id'] not in
                ('note_9200', 'note_9201', 'note_9202', 'note_9203', 'note_9204', 'note_9205', 'note_9206')]
out['notes'] += [
    {"id": "note_9300", "text": "PLAYER A", "x": -2418, "y": -460, "w": 300, "h": 34,
     "color": "#000000", "fontSize": 18, "fontFamily": "Arial", "bold": True, "italic": False, "underline": False},
    {"id": "note_9301", "text": "PLAYER B", "x": 2190, "y": -460, "w": 300, "h": 34,
     "color": "#000000", "fontSize": 18, "fontFamily": "Arial", "bold": True, "italic": False, "underline": False},
    {"id": "note_9302", "text": "SHARED CONTROL", "x": 270, "y": 690, "w": 400, "h": 34,
     "color": "#000000", "fontSize": 18, "fontFamily": "Arial", "bold": True, "italic": False, "underline": False},
    {"id": "note_9303", "text": "CENTRE COLUMN (top to bottom): 9-LED board, arbiter board 2, arbiter board 1, Turn+supply board, SHARED CONTROL.",
     "x": -620, "y": -1560, "w": 1400, "h": 40, "color": "#000000", "fontSize": 12,
     "fontFamily": "Arial", "bold": False, "italic": False, "underline": False},
    {"id": "note_9304", "text": "The empty small input breadboard was removed; its nets now run straight from the player rank switches to the arbiter and from the pull-downs to the local GND rail.",
     "x": -620, "y": -1600, "w": 1700, "h": 40, "color": "#000000", "fontSize": 12,
     "fontFamily": "Arial", "bold": False, "italic": False, "underline": False},
    {"id": "note_9305", "text": "PLAYER A edge -> centre: A rank bits, A_Done, /Reset, /Game_Over   |   PLAYER B edge -> centre: B rank bits, B_Done, /Reset, /Game_Over",
     "x": -2418, "y": 60, "w": 1700, "h": 40, "color": "#000000", "fontSize": 12,
     "fontFamily": "Arial", "bold": False, "italic": False, "underline": False},
]

# keep every original note with its board: translate the notes that describe a board
# which moved
for n in out['notes']:
    for bi, (dx, dy) in DELTA.items():
        b = next(x for x in d['boards'] if x['index'] == bi)
        x0, y0 = b['x'], b['y']
        x1, y1 = b['x'] + 24 * b['cols'] + 120, b['y'] + 384
        if x0 <= n['x'] <= x1 and y0 <= n['y'] <= y1:
            n['x'] += dx
            n['y'] += dy
            break

# before/after list of the wires that were re-routed
lines = ['# Re-routed wires (Arbiter-9_v5_arranged.json)', '',
         'Wires whose two ends are on the same board were moved rigidly with that board',
         '(their bend points were translated by the board delta). Everything listed below',
         'was re-routed: the endpoints are unchanged, only the bend points and the hole',
         'each end lands in are new.', '']


def fmt(e):
    if e['type'] == 'hole':
        return 'hole b%s c%s r%s' % (e['board'], e['col'], e['row'])
    if e['type'] == 'bus':
        return 'rail b%s %s c%s' % (e['board'], e['bus'], e['col'])
    return 'pin %s.%s' % (e['partId'], e['pin'])


n_rigid = 0
for c in same_board:
    if not c.get('pivots'):
        continue
    src = None
    for e in (c['a'], c['b']):
        if e['type'] == 'hole':
            src = e['board']
        elif e['type'] == 'pin':
            src = part_board[e['partId']]
    if DELTA.get(src, (0, 0)) != (0, 0):
        n_rigid += 1
lines += ['**%d of the %d same-board wires had bend points and were translated by their board\'s delta**'
          % (n_rigid, len(same_board)),
          '(the rest are straight segments that need no change).', '',
          '**%d wires re-routed:**' % len(work), '',
          '| # | from | to | new bend points |', '|---|---|---|---|']
for i, c in enumerate(work):
    lines.append('| %d | %s | %s | %s |' % (
        i + 1, fmt(c['a']), fmt(c['b']),
        ', '.join('(%g, %g)' % (p[0], p[1]) for p in c.get('pivots', [])) or 'straight'))
open('Arbiter-9_v5_routed-wires.md', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('wrote Arbiter-9_v5_routed-wires.md')
json.dump(out, open(DST, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print('wrote', DST)
print('boards', len(out['boards']), 'parts', len(out['parts']),
      'connections', len(out['connections']), '| same-board', len(same_board), 're-routed', len(work))
