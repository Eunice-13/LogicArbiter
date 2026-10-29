"""Final verification of Arbiter-9_v3_clean.json against the cleanup rules."""
import json
import collections


OFF = {0: 72, 1: 96, 2: 120, 3: 144, 4: 168, 5: 216, 6: 240, 7: 264, 8: 288, 9: 312}


def _netlist(path):
    pins = json.load(open('_pins.json', encoding='utf-8'))
    d = json.load(open(path, encoding='utf-8'))
    bs = {b['index']: b for b in d['boards']}
    ps = {p['id']: (p['x'], p['y']) for p in d['parts']}
    par = {}

    def f(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    def v(a, b):
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

    for pid, p in pins.items():
        for label in p['pins']:
            x, y = p['pins'][label]
            if pid in ps:
                x += ps[pid][0] - p['x']
                y += ps[pid][1] - p['y']
            h = None
            for bi, b in bs.items():
                if (int(round(x)) - b['x']) % 24 == 0 and 0 <= (int(round(x)) - b['x']) // 24 <= b['cols']:
                    c = (int(round(x)) - b['x']) // 24
                    for r, off in OFF.items():
                        if b['y'] + off == int(round(y)):
                            h = (bi, c, 0 if r <= 4 else 1)
            if h:
                v(('P', pid, label), ('S',) + h)
    for c in d['connections']:
        v(nd(c['a']), nd(c['b']))
    g = collections.defaultdict(list)
    for pid, p in pins.items():
        for label in p['pins']:
            g[f(('P', pid, label))].append(pid + ':' + label)
    return sorted(' '.join(sorted(v)) for v in g.values())


nA, nB = _netlist('Arbiter-9-upgraded.json'), _netlist('Arbiter-9_v3_clean.json')
print('NETLIST identical before/after:', nA == nB, '(nets:', len(nA), '/', len(nB), ')')
if nA != nB:
    for x in list(set(nA) - set(nB))[:4]:
        print('   only-before:', x)
    for x in list(set(nB) - set(nA))[:4]:
        print('   only-after :', x)

BEFORE = 'Arbiter-9-upgraded.json'
CLEAN = 'Arbiter-9_v3_clean.json'
ORIG = 'Arbiter-9.json'
N_ORIG = 307

OFF = {0: 72, 1: 96, 2: 120, 3: 144, 4: 168, 5: 216, 6: 240, 7: 264, 8: 288, 9: 312}
pins = json.load(open('_pins.json', encoding='utf-8'))
clean = json.load(open(CLEAN, encoding='utf-8'))
before = json.load(open(BEFORE, encoding='utf-8'))
orig = json.load(open(ORIG, encoding='utf-8'))
boards = {b['index']: b for b in clean['boards']}
pos = {p['id']: (p['x'], p['y']) for p in clean['parts']}


def pin_coord(cid, label):
    x, y = pins[cid]['pins'][label]
    ox, oy = pins[cid]['x'], pins[cid]['y']
    nx, ny = pos[cid]
    return (int(round(x + nx - ox)), int(round(y + ny - oy)))


def hole_of(x, y):
    hit = None
    for bi, b in boards.items():
        if (x - b['x']) % 24:
            continue
        col = (x - b['x']) // 24
        if not (0 <= col <= b['cols']):
            continue
        for r, off in OFF.items():
            if b['y'] + off == y:
                hit = (bi, col, r)
    return hit


pin_hole = {}
for cid, p in pins.items():
    for label in p['pins']:
        h = hole_of(*pin_coord(cid, label))
        if h:
            pin_hole.setdefault(h, []).append(cid + ':' + label)
print('pins seated in a hole:', sum(len(v) for v in pin_hole.values()))

# rule 1 : no wire endpoint in a component pin's hole
# rule 2 : no two wire endpoints share a hole
# rule 3 : every wire is horizontal/vertical
use = collections.Counter()
rule1_new, rule2_new = [], []
for i, c in enumerate(clean['connections']):
    tag = 'ORIG' if i < N_ORIG else 'NEW'
    for e in (c['a'], c['b']):
        if e['type'] == 'hole':
            key = (e['board'], e['col'], e['row'])
            use[key] += 1
            if tag == 'NEW' and key in pin_hole:
                rule1_new.append((i, key, pin_hole[key]))

new_holes = collections.Counter()
for c in clean['connections'][N_ORIG:]:
    for e in (c['a'], c['b']):
        if e['type'] == 'hole':
            new_holes[(e['board'], e['col'], e['row'])] += 1
dup_new = [k for k, v in new_holes.items() if v > 1]
orig_holes = set()
for c in clean['connections'][:N_ORIG]:
    for e in (c['a'], c['b']):
        if e['type'] == 'hole':
            orig_holes.add((e['board'], e['col'], e['row']))
shared_with_orig = [k for k in new_holes if k in orig_holes]

diag = 0
for c in clean['connections']:
    pts = []
    for e in (c['a'], c['b']):
        if e['type'] == 'hole':
            b = boards[e['board']]
            pts.append((b['x'] + 24 * e['col'], b['y'] + OFF[e['row']]))
        else:
            pts.append(None)
    path = [pts[0]] + [tuple(p) for p in c.get('pivots', [])] + [pts[1]]
    if any(p is None for p in path):
        continue
    for a, b in zip(path, path[1:]):
        if a[0] != b[0] and a[1] != b[1]:
            diag += 1

print('NEW endpoints in a component pin hole :', len(rule1_new))
print('NEW holes used by >1 NEW endpoint     :', len(dup_new))
print('NEW holes also used by an ORIG wire   :', len(shared_with_orig))
print('non-orthogonal (diagonal) segments    :', diag)
print('ORIG endpoints in a pin hole (pre-existing, untouched):',
      sum(1 for i, c in enumerate(clean['connections'][:N_ORIG])
          for e in (c['a'], c['b'])
          if e['type'] == 'hole' and (e['board'], e['col'], e['row']) in pin_hole))

# board membership
def board_of(cid):
    locs = set()
    for label in pins[cid]['pins']:
        h = hole_of(*pin_coord(cid, label))
        if h:
            locs.add(h[0])
    return locs

groups = {
    'PLAYER A (5)': ['c2', 'c4', 'c5', 'c6', 'c7', 'bA', 'pA', 'uA1', 'uA2', 'uA3', 'LA', 'rLA'],
    'PLAYER B (6)': ['c3', 'c8', 'c9', 'c10', 'c11', 'bB', 'pB', 'uB1', 'uB2', 'uB3', 'LB', 'rLB'],
    'SHARED (7)': ['bR', 'pR', 'uS1', 'uS2', 'uS3', 'uS4', 'LGO', 'rGO', 'LD1', 'rLD1', 'LD2', 'rLD2', 'LD3', 'rLD3'],
}
for g, ids in groups.items():
    ok = all(board_of(i) == {int(g.split('(')[1][0])} for i in ids)
    print(g, 'all parts on that board:', ok)
    for i in ids:
        b = board_of(i)
        if b != {int(g.split('(')[1][0])}:
            print('   wrong board:', i, b)

# A-only / B-only signals never share a wire except via the shared board
a_sigs = {'uA1', 'uA2', 'uA3', 'bA', 'pA', 'LA', 'rLA'}
b_sigs = {'uB1', 'uB2', 'uB3', 'bB', 'pB', 'LB', 'rLB'}
bad = []
for c in clean['connections'][N_ORIG:]:
    ids = [e['partId'] for e in (c['a'], c['b']) if e['type'] == 'pin']
    if any(i in a_sigs for i in ids) and any(i in b_sigs for i in ids):
        bad.append(c)
print('wires joining an A-only part directly to a B-only part:', len(bad))

print('moved parts:', sum(1 for p in clean['parts']
                         if (p['x'], p['y']) != (next(q for q in before['parts'] if q['id'] == p['id'])['x'],
                                                 next(q for q in before['parts'] if q['id'] == p['id'])['y'])))
print('original 307 connections byte-identical to Arbiter-9.json:',
      clean['connections'][:N_ORIG] == orig['connections'])
print('non-moved parts identical (incl. labels/attrs):',
      all({k: v for k, v in p.items() if k not in ('x', 'y')} ==
          {k: v for k, v in next(q for q in before['parts'] if q['id'] == p['id']).items() if k not in ('x', 'y')}
          for p in clean['parts']))
