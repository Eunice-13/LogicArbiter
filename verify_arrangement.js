// Final verification: load both files in the simulator engine and compare the
// pin netlist built from the wires the engine actually loads.
const fs = require('fs');
const sb = require('./_env.js')();

const OFF = { 0: 72, 1: 96, 2: 120, 3: 144, 4: 168, 5: 216, 6: 240, 7: 264, 8: 288, 9: 312 };
const RAILOFF = { TP: 0, TN: 24, BP: 360, BN: 384 };

function netlist(file) {
  const raw = JSON.parse(fs.readFileSync(file, 'utf8'));
  const c = sb.deserialise(JSON.stringify(raw)).circuit;
  const bd = {}; for (const b of raw.boards) bd[b.index] = b;
  const par = {};
  const find = (x) => { par[x] = par[x] === undefined ? x : par[x]; while (par[x] !== x) { par[x] = par[par[x]]; x = par[x]; } return x; };
  const uni = (a, b) => { const ra = find(a), rb = find(b); if (ra !== rb) par[ra] = rb; };
  const coordNode = (x, y) => {
    x = Math.round(x); y = Math.round(y);
    for (const bi of Object.keys(bd)) {
      const b = bd[bi];
      if ((x - b.x) % 24) continue;
      const col = (x - b.x) / 24;
      if (!(col >= 0 && col <= b.cols)) continue;
      for (const rr of Object.keys(OFF)) if (b.y + OFF[rr] === y) return 'S' + bi + ',' + col + ',' + (rr <= 4 ? 0 : 1);
      for (const k of Object.keys(RAILOFF)) if (b.y + RAILOFF[k] === y) return 'R' + bi + ':' + k;
    }
    return 'X' + x + ',' + y;
  };
  for (const comp of c.components) for (const p of comp.pins) uni('P' + comp.id + ':' + p.label, coordNode(p.x, p.y));
  for (const w of c.wires) {
    const a = w.startPin, b = w.endPin;
    const na = a.constructor.name === 'Pin' ? 'P' + a.owner.id + ':' + a.label : coordNode(a.x, a.y);
    const nb = b.constructor.name === 'Pin' ? 'P' + b.owner.id + ':' + b.label : coordNode(b.x, b.y);
    uni(na, nb);
  }
  const g = {};
  for (const comp of c.components) for (const p of comp.pins) {
    const r = find('P' + comp.id + ':' + p.label);
    (g[r] = g[r] || []).push(comp.id + ':' + p.label);
  }
  return { nets: Object.values(g).map(a => a.sort().join(' ')).sort(), wires: c.wires.length, comps: c.components.length, boards: c.breadboards.length };
}

const a = netlist(process.argv[2] || 'Arbiter-9_v3_clean.json');
const b = netlist(process.argv[3] || 'Arbiter-9_v5_arranged.json');
console.log('before:', a.comps, 'components,', a.boards, 'boards,', a.wires, 'wires,', a.nets.length, 'nets');
console.log('after :', b.comps, 'components,', b.boards, 'boards,', b.wires, 'wires,', b.nets.length, 'nets');
const key = (a) => a.join(' ');
const onlyInA = a.nets.filter(x => !b.nets.includes(x));
const onlyInB = b.nets.filter(x => !a.nets.includes(x));
console.log('nets only before:', onlyInA.length, '| only after:', onlyInB.length,
  '| approved GND merge (4 into 1):', onlyInA.length === 4 && onlyInB.length === 1);
const shorted = (n) => n.some(x => x.includes('c2132:+') && x.includes('c2132:-'));
console.log('+5V shorted to GND:', shorted(a.nets), '/', shorted(b.nets));
