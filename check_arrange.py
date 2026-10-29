"""Verify Arbiter-9_v5_arranged.json."""
import collections
import json

BEFORE = 'Arbiter-9_v3_clean.json'
AFTER = 'Arbiter-9_v5_arranged.json'
BASE = 'Arbiter-9.json'
N_ORIG = 307
OFF = {0: 72, 1: 96, 2: 120, 3: 144, 4: 168, 5: 216, 6: 240, 7: 264, 8: 288, 9: 312}
RAIL = {'TP': 0, 'TN': 24, 'BP': 360, 'BN': 384}
pins = json.load(open('_pins.json', encoding='utf-8'))


def load(p):
    d = json.load(open(p, encoding='utf-8'))
    return d, {b['index']: b for b in d['boards']}, {q['id']: (q['x'], q['y']) for q in d['parts']}


def pin_xy(cid, label, pos):
    x, y = pins[cid]['pins'][label]
    if cid in pos:
        x += pos[cid][0] - pins[cid]['x']
        y += pos[cid][1] - pins[cid]['y']
    return (int(round(x)), int(round(y)))


def hole_of(bd, x, y):
    x, y = int(round(x)), int(round(y))
    for bi, b in bd.items():
        if (x - b['x']) % 24:
            continue
        col = (x - b['x']) // 24
        if not (0 <= col <= b['cols']):
            continue
        for r, off in OFF.items():
            if b['y'] + off == y:
                return (bi, col, r)
    return None


def netlist(path):
    d, bd, pos = load(path)
    par = {}

    def f(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    def u(a, b):
        ra, rb = f(a), f(b)
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

    for cid in pins:
        for label in pins[cid]['pins']:
            h = hole_of(bd, *pin_xy(cid, label, pos))
            if h:
                u(('P', cid, label), ('S', h[0], h[1], 0 if h[2] <= 4 else 1))
    for c in d['connections']:
        u(nd(c['a']), nd(c['b']))
    g = collections.defaultdict(list)
    for cid in pins:
        for label in pins[cid]['pins']:
            g[f(('P', cid, label))].append(cid + ':' + label)
    return sorted(' '.join(sorted(v)) for v in g.values())


nA, nB = netlist(BEFORE), netlist(AFTER)
print('NETLIST: %d -> %d nets; only the approved GND merge differs:' % (len(nA), len(nB)),
      len(set(nA) - set(nB)) == 4 and len(set(nB) - set(nA)) == 1)
if nA != nB:
    for x in list(set(nA) - set(nB))[:4]:
        print('  only-before:', x)
    for x in list(set(nB) - set(nA))[:4]:
        print('  only-after :', x)

d, bd, pos = load(AFTER)
print('boards:', [(b, bd[b]['x'], bd[b]['y']) for b in sorted(bd)])
print('board count:', len(bd), '| old unused board (168,120) gone:',
      not any((b['x'], b['y']) == (168, 120) for b in bd.values()))
bb = {b: (bd[b]['x'], bd[b]['y'], bd[b]['x'] + bd[b]['cols'] * 24 + 120, bd[b]['y'] + 384) for b in bd}
ov = []
for i in sorted(bb):
    for j in sorted(bb):
        if i < j and bb[i][0] < bb[j][2] and bb[j][0] < bb[i][2] and bb[i][1] < bb[j][3] and bb[j][1] < bb[i][3]:
            ov.append((i, j, bb[i], bb[j]))
print('overlapping boards:', ov)

# every part on its expected board, rigid offset preserved
db, _, base_pos = load('Arbiter-9_v3_clean.json')
bbase = {b['index']: b for b in db['boards']}


def board_of(bd, pos, cid):
    """board index, matched by the board's position (indices were renumbered)"""
    hits = collections.Counter()
    for label in pins[cid]['pins']:
        h = hole_of(bd, *pin_xy(cid, label, pos))
        if h:
            bb = bd[h[0]]
            hits[(bb['x'], bb['y'])] += 1
    return hits.most_common(1)[0][0] if hits else None


bad = []
bbase_pos = {b['index']: (b['x'], b['y']) for b in db['boards']}
for p in d['parts']:
    b = board_of(bd, pos, p['id'])
    b0 = board_of(bbase, {q['id']: (q['x'], q['y']) for q in db['parts']}, p['id'])
    if b is None or b0 is None:
        bad.append((p['id'], b0, b))
        continue
    # same board?  compare the board each part sits on, by position
    if b != b0:
        bad.append((p['id'], b0, b))
print('parts that changed board:', bad)
ok_rigid = True
ob_all = {q['id']: (q['x'], q['y']) for q in db['parts']}
for cid in pins:
    b0 = board_of(bbase, ob_all, cid)
    b = board_of(bd, pos, cid)
    if b is None or b0 is None:
        continue
    bx, by = b0
    before_off = (round(ob_all[cid][0] - bx, 3), round(ob_all[cid][1] - by, 3))
    after_off = (round(pos[cid][0] - b[0], 3), round(pos[cid][1] - b[1], 3))
    if before_off != after_off:
        ok_rigid = False
        print('  not rigid:', cid, before_off, after_off)
print('every part keeps its offset inside its board:', ok_rigid)

# geometry of connections
pin_hole = set()
for cid in pins:
    for label in pins[cid]['pins']:
        h = hole_of(bd, *pin_xy(cid, label, pos))
        if h:
            pin_hole.add(h)


def px(e):
    if e['type'] == 'hole':
        return (bd[e['board']]['x'] + 24 * e['col'], bd[e['board']]['y'] + OFF[e['row']])
    if e['type'] == 'bus':
        b = bd[e['board']]
        return (b['x'] + 24 * e['col'], b['y'] + RAIL[e['bus']])
    if e['type'] == 'pin':
        return pin_xy(e['partId'], e['pin'], pos)
    return None


diag = 0
for c in d['connections']:
    pts = [px(c['a'])] + [tuple(q) for q in c.get('pivots', [])] + [px(c['b'])]
    for a, b in zip(pts, pts[1:]):
        if a and b and a[0] != b[0] and a[1] != b[1]:
            diag += 1
print('diagonal segments in the file:', diag)

use = collections.Counter()
for c in d['connections']:
    for e in (c['a'], c['b']):
        if e['type'] == 'hole':
            use[(e['board'], e['col'], e['row'])] += 1
pin_hits = [k for k in use if k in pin_hole]
print('holes used by a wire AND holding a pin:', len(pin_hits))
print('holes used by more than one wire endpoint:', sum(1 for v in use.values() if v > 1))
print('connections referencing board 0:', sum(1 for c in d['connections']
      for e in (c['a'], c['b']) if e.get('board') == 0))

# no direct PLAYER A <-> PLAYER B wire
def bof(e):
    if e['type'] in ('hole', 'bus'):
        return e['board']
    return board_of(bd, pos, e['partId'])


ab = [c for c in d['connections'] if {bof(c['a']), bof(c['b'])} == {5, 6}]
print('wire directly joining PLAYER A and PLAYER B:', len(ab))

# base file untouched?
base, _, basepos = load(BASE)
orig_ok = True
for p in d['parts']:
    if not p['id'].startswith('c'):
        continue
    q = next((x for x in base['parts'] if x['id'] == p['id']), None)
    if q is None:
        orig_ok = False
        print('  missing original part', p['id'])
        continue
    for k, v in q.items():
        if k in ('x', 'y'):
            continue
        if p.get(k) != v:
            orig_ok = False
            print('  changed field', p['id'], k, v, '->', p.get(k))
print('original part ids/labels/attrs unchanged:', orig_ok)
orig_conn = [c for c in base['connections']]
kept_identical = 0
for c in d['connections'][:]:
    pass
print('connection count: base', len(base['connections']), 'after', len(d['connections']))
