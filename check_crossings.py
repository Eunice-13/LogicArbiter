"""Check whether any NEW wire crosses an original wire or an original component body."""
import json

OFF = {0: 72, 1: 96, 2: 120, 3: 144, 4: 168, 5: 216, 6: 240, 7: 264, 8: 288, 9: 312}
RAIL = {'TP': 0, 'TN': 24, 'BP': 360, 'BN': 384}
clean = json.load(open('Arbiter-9_v3_clean.json', encoding='utf-8'))
pins = json.load(open('_pins.json', encoding='utf-8'))
boards = {b['index']: b for b in clean['boards']}
pos = {p['id']: (p['x'], p['y']) for p in clean['parts']}
N = 307


def ep_xy(e):
    if e['type'] == 'hole':
        b = boards[e['board']]
        return (b['x'] + 24 * e['col'], b['y'] + OFF[e['row']])
    if e['type'] == 'bus':
        b = boards[e['board']]
        return (b['x'] + 24 * e['col'], b['y'] + RAIL[e['bus']])
    if e['type'] == 'pin':
        x, y = pins[e['partId']]['pins'][e['pin']]
        ox, oy = pins[e['partId']]['x'], pins[e['partId']]['y']
        nx, ny = pos[e['partId']]
        return (x + nx - ox, y + ny - oy)
    return None


def segments(conn):
    pts = [ep_xy(conn['a'])] + [tuple(p) for p in conn.get('pivots', [])] + [ep_xy(conn['b'])]
    return [(a, b) for a, b in zip(pts, pts[1:]) if a and b]


def horiz_or_vert(s):
    (x1, y1), (x2, y2) = s
    return x1 == x2 or y1 == y2


def seg_bbox(s):
    (x1, y1), (x2, y2) = s
    return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))


def intersect(s1, s2):
    (x1, y1), (x2, y2) = s1
    (x3, y3), (x4, y4) = s2
    b1, b2 = seg_bbox(s1), seg_bbox(s2)
    if b1[2] < b2[0] or b2[2] < b1[0] or b1[3] < b2[1] or b2[3] < b1[1]:
        return False
    if x1 == x2 and x3 == x4:
        return x1 == x3 and not (b1[3] < b2[1] or b2[3] < b1[1])
    if y1 == y2 and y3 == y4:
        return y1 == y3 and not (b1[2] < b2[0] or b2[2] < b1[0])
    return True   # one horizontal, one vertical, bboxes overlap -> crossing


orig_segs = []
for c in clean['connections'][:N]:
    orig_segs += segments(c)
new_segs = []
for c in clean['connections'][N:]:
    new_segs += segments(c)

cross = 0
for s in new_segs:
    for t in orig_segs:
        if intersect(s, t):
            cross += 1
print('new segments:', len(new_segs), 'original segments:', len(orig_segs))
print('new-segment / original-segment intersections:', cross)
print('new segments that are diagonal:', sum(1 for s in new_segs if not horiz_or_vert(s)))

# original component bodies (bounding box of their pins), search only near the new boards
orig_ids = [p['id'] for p in clean['parts'] if p['id'][0] == 'c']
bodies = []
for cid in orig_ids:
    xs = [ep_xy({'type': 'pin', 'partId': cid, 'pin': l}) for l in pins[cid]['pins']]
    xs = [p for p in xs if p]
    if not xs:
        continue
    bodies.append((cid, min(p[0] for p in xs), min(p[1] for p in xs),
                   max(p[0] for p in xs), max(p[1] for p in xs)))

hits = 0
for s in new_segs:
    (sx1, sy1), (sx2, sy2) = s
    for cid, x0, y0, x1, y1 in bodies:
        if sx1 == sx2:
            if x0 < sx1 < x1 and not (max(sy1, sy2) < y0 or min(sy1, sy2) > y1):
                hits += 1
        elif sy1 == sy2:
            if y0 < sy1 < y1 and not (max(sx1, sx2) < x0 or min(sx1, sx2) > x1):
                hits += 1
print('new segments passing through an original component body:', hits)
