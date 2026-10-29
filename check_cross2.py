"""Crossing / overlap / component checks for Arbiter-9_v5_arranged.json."""
import json
import collections

OFF = {0: 72, 1: 96, 2: 120, 3: 144, 4: 168, 5: 216, 6: 240, 7: 264, 8: 288, 9: 312}
RAIL = {'TP': 0, 'TN': 24, 'BP': 360, 'BN': 384}
pins = json.load(open('_pins.json', encoding='utf-8'))
aft = json.load(open('Arbiter-9_v5_arranged.json', encoding='utf-8'))
bd = {b['index']: b for b in aft['boards']}
pos = {p['id']: (p['x'], p['y']) for p in aft['parts']}
N_ORIG = 307


def px(e):
    if e['type'] == 'hole':
        return (bd[e['board']]['x'] + 24 * e['col'], bd[e['board']]['y'] + OFF[e['row']])
    if e['type'] == 'bus':
        b = bd[e['board']]
        return (b['x'] + 24 * e['col'], b['y'] + RAIL[e['bus']])
    if e['type'] == 'pin':
        x, y = pins[e['partId']]['pins'][e['pin']]
        return (x + pos[e['partId']][0] - pins[e['partId']]['x'], y + pos[e['partId']][1] - pins[e['partId']]['y'])
    return None


def segs(c):
    pts = [px(c['a'])] + [tuple(q) for q in c.get('pivots', [])] + [px(c['b'])]
    return [(a, b) for a, b in zip(pts, pts[1:]) if a and b]


orig_segs = []
for c in aft['connections'][:N_ORIG]:
    orig_segs += segs(c)
new_segs = []
for c in aft['connections'][N_ORIG:]:
    new_segs += segs(c)


def bbox(s):
    (x1, y1), (x2, y2) = s
    return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))


def inter(s1, s2):
    b1, b2 = bbox(s1), bbox(s2)
    if b1[2] < b2[0] or b2[2] < b1[0] or b1[3] < b2[1] or b2[3] < b1[1]:
        return False
    (x1, y1), (x2, y2) = s1
    (x3, y3), (x4, y4) = s2
    if x1 == x2 and x3 == x4:
        return x1 == x3
    if y1 == y2 and y3 == y4:
        return y1 == y3
    return True


cross = sum(1 for s in new_segs for t in orig_segs if inter(s, t))
print('new-vs-original wire crossings:', cross)


def overlap(s1, s2):
    (x1, y1), (x2, y2) = s1
    (x3, y3), (x4, y4) = s2
    if x1 == x2 == x3 == x4:
        return min(max(y1, y2), max(y3, y4)) - max(min(y1, y2), min(y3, y4)) > 0
    if y1 == y2 == y3 == y4:
        return min(max(x1, x2), max(x3, x4)) - max(min(x1, x2), min(x3, x4)) > 0
    return False


ov = sum(1 for i in range(len(new_segs)) for j in range(i + 1, len(new_segs))
         if overlap(new_segs[i], new_segs[j]))
print('new-vs-new collinear overlaps:', ov)
ov2 = sum(1 for s in new_segs for t in orig_segs if overlap(s, t))
print('new-vs-original collinear overlaps:', ov2)

bodies = []
for cid in pins:
    pts = [px({'type': 'pin', 'partId': cid, 'pin': l}) for l in pins[cid]['pins']]
    pts = [q for q in pts if q]
    if pts:
        x0, x1 = min(a for a, _ in pts), max(a for a, _ in pts)
        y0, y1 = min(b for _, b in pts), max(b for _, b in pts)
        if x1 - x0 > 24 or y1 - y0 > 24:      # ignore degenerate rows of DIP pins
            bodies.append((cid, x0, y0, x1, y1))
hits = collections.Counter()
for c in aft['connections'][N_ORIG:]:
    for s in segs(c):
        (sx1, sy1), (sx2, sy2) = s
        for cid, x0, y0, x1, y1 in bodies:
            if sx1 == sx2 and x0 < sx1 < x1 and not (max(sy1, sy2) < y0 or min(sy1, sy2) > y1):
                hits[cid] += 1
            if sy1 == sy2 and y0 < sy1 < y1 and not (max(sx1, sx2) < x0 or min(sx1, sx2) > x1):
                hits[cid] += 1
print('new segments passing through a component body:', dict(hits))
