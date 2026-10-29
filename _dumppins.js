const fs = require('fs');
const sb = require('./_env.js')();
const file = process.argv[2] || 'Arbiter-9_v3_clean.json';
const raw = JSON.parse(fs.readFileSync(file, 'utf8'));
const c = sb.deserialise(JSON.stringify(raw)).circuit;
const out = {};
for (const comp of c.components) {
  out[comp.id] = { kind: comp.constructor.name, x: comp.x, y: comp.y, pins: {} };
  for (const p of comp.pins) out[comp.id].pins[p.label] = [p.x, p.y];
}
fs.writeFileSync('_pins.json', JSON.stringify(out, null, 1));
console.log('dumped', Object.keys(out).length, 'components from', file);
// sanity
const c2 = raw.parts.find(p => p.id === 'c2');
console.log('c2 in json at', c2.x, c2.y, '| engine pins S1', out['c2'].pins['S1']);
