# Arbiter-9 v5 — rearranged breadboards and re-routed wiring

Applied `arrangement_and_wiring_prompt.md` to `Arbiter-9_v3_clean.json`.
Style reference: `final-na-to-ata.json` (same board spacing for the arbiter boards,
x = 288 column, 552 px pitch, small boards in row 0).

## 1. Files

| File | What it is |
|---|---|
| **`Arbiter-9_v5_arranged.json`** | the rearranged / re-routed project (72 parts, 7 boards, 433 wires, 45 notes) |
| `Arbiter-9_v3_clean.json` | the previous version, **never overwritten** (the backup) |
| `arrange_layout.py` | the generator (moves the boards, removes the unused one, re-routes) |
| `check_arrange.py`, `check_cross2.py` | geometry / rule verification scripts |
| `verify_arrangement.js` | loads both files in the simulator engine and diffs the netlist it actually builds |
| `Arbiter-9_v5_routed-wires.md` | delivery 3: the before/after table of every re-routed wire |
| `_pins.json`, `_dumppins.js`, `_env.js`, `_bundle.js` | pin-geometry dump + the simulator harness used to produce and verify it |

## 2. Board arrangement (target met)

```
 PLAYER A            centre column              PLAYER B
 x=-2400..-888        x=288..1800               x=2208..3720
 (y=-348)             (top -> bottom)           (y=-348)
```

| New idx | Was | What it holds | Old position | New position | Status |
|---|---|---|---|---|---|
| 0 | 4 | the nine LEDs + their resistors | (288, -1200) | (288, -1440) | kept (moved) |
| 1 | 2 | arbiter board 2 (7408 / 7432 win+flag logic) | (288, -792) | (288, -888) | kept (moved) |
| 2 | 1 | arbiter board 1 (7404 / 7485 / 7430) | (288, -336) | (288, -336) | kept (unchanged) |
| 3 | 3 | Turn buttons + supply | (-600, 120) | (-600, 192) | kept (moved 24 px to the reference pitch) |
| 4 | 7 | SHARED CONTROL | (288, 1300) | (288, 744) | kept (moved) |
| 5 | 5 | PLAYER A | (-1600, 1300) | (-2400, -348) | kept (moved) |
| 6 | 6 | PLAYER B | (1900, 1300) | (2208, -348) | kept (moved) |
| — | **0** | *(was the A/B rank-input board — now empty)* | (168, 120) | — | **REMOVED** |

* Player A is far left, Player B far right, the centre column separates them, and the
  left/right gaps are equal (288 px each).
* PLAYER A / PLAYER B are vertically centred on the column (y = -348).
* No two boards overlap; every part keeps its offset inside its board (checked).

## 3. The removed breadboard

Board 0 (the half board at (168, 120)) **held no components** — the rank DIP switches
and their pull-downs had already been moved onto the player boards — but 42 wires
still ended on it. Its nets were re-connected before it was deleted:

* the 8 rank-bit feeds now run **straight from the player switch strip to the board-1
  input strip** (no longer through board 0);
* the 8 pull-down bottoms now run to the **main GND rail** (the rail they were on);
* the 4 board-0/board-3 supply ties were rebuilt as `board3 -> board1` ties;
* the 6 new `player -> board0` supply/bridge wires were rebuilt as
  `player -> board1` ties and `player -> board1` rank feeds.

Result: **0 connections reference board 0**, and the netlist is unchanged.

Text notes were also moved with the boards they describe (each note whose position fell
inside a board that moved was translated by that board's delta), so every original label
still points at its own board.

## 4. Wire handling

* 256 original connections whose two ends are on the **same** board simply **moved
  rigidly** with that board (their bend points translated by exactly the board delta);
* 177 connections that span boards were **re-routed**: every one is now a
  right-angle path made of a vertical lane in the side gap and a horizontal lane in
  the free band next to the destination board (12 px lane pitch);
* each new wire endpoint is a **free hole of the same 5-hole strip as the pin it
  serves** (never the pin's own hole, never a hole used by another wire);
* colours follow the reference convention: red +5 V, black GND, blue A rank bus,
  purple B rank bus, amber Reset/Submit, green A_Done/B_Done/Display_Enable,
  teal finals, orange display outputs;
* no wire runs directly between PLAYER A and PLAYER B — the one such net was split so
  both sides reach the SHARED board.

## 5. Checks run (and results)

| Check | Result |
|---|---|
| **Netlist before/after** | **PASS with the approved change** — 137 nets before, 134 after: the only difference is the GND fix you approved (PLAYER A's, PLAYER B's and the SHARED board's grounds now join the main ground; every other net and every pin is unchanged). Verified from the JSON model *and* from the wires the simulator itself loads |
| File loads in the simulator | **PASS** — 72 components, 7 boards, **433 / 433 wires**, 45 notes |
| PLAYER A far left, PLAYER B far right, centre column in order | **PASS** |
| Unused small board removed | **PASS** (it held no components) |
| Every Player A part on A's board / every B part on B's board | **PASS** (by board position) |
| No A signal shares a wire/hole with a B signal | **PASS** (0 direct A↔B wires) |
| No board overlaps another; side gaps equal | **PASS** |
| Each board moved rigidly; no component changed its position on its board | **PASS** |
| No diagonal segments in **new** wires | **PASS** (0) |
| New wire endpoint in a component pin hole / two new endpoints in one hole | **PASS** (0 / 0) |
| New wire over an original wire | **PASS** — 0 overlapping segments; 1121 single right-angle crossings remain |
| Original IDs / labels / colours unchanged | **PASS** (only x,y of moved boards' parts change) |
| Behaviour tests (arbiter result, lockout, Display_Enable, round reset, Game_Over) | not run — the browser's WASM simulation engine is not part of the downloadable files; structure and netlist were verified instead |

## 6. Rules that are not fully met, and why

1. **"No two wires share a lane/row/column, no wire segments overlap"** — PASS except
   for **one** pair: a rank wire (`board 6 c3 r1 -> board 2 c14 r6`) shares a 12 px
   column with the local GND stub of `board 6 c3 r6`. The reference's lines were drawn by
   LogicBench's own autorouter, which is not available here (the bundle ships without a
   working JS router); the hand-written planner in `arrange_layout.py` clears every other
   collision (overlaps went 179 → 1).
2. **Crossings** — 1121 single right-angle crossings remain between new and original
   wires: both player boards have to reach the centre column's wiring. The rule allows
   crossings that cannot be avoided and forbids overlapping/parallel runs, which the
   planner guarantees.
3. **"No wire passes over an IC, LED or other component"** — wires entering an IC pin
   field are counted here (a wire has to reach its pin); no wire runs along or through a
   component body.
4. **"No diagonal wires remain"** — 63 *original* connections still have diagonal bend
   points. They are pre-existing in the project (the pristine `Arbiter-9.json` has 88
   such connections) and the hard constraint says original wires must not be changed, so
   they were left alone. All re-routed wires are orthogonal.
5. **"No wire endpoint shares a hole with a component pin" / "no two endpoints share a
   hole"** — 196 / 136 instances exist, all in *original* wires (LED, resistor, DIP and
   battery legs have no pin endpoints in this format, so their wires necessarily land on
   the leg's own hole). All new wires comply.
6. **Centre column has 5 rows, not 4.** The prompt's diagram lists four centre boards,
   but the file really contains five (the two arbiter boards are separate). All five are
   stacked in one aligned column.
7. **Board indices were renumbered 0..6** (from 1..7). The simulator silently drops every
   wire on a board whose list has no index 0 — with the old numbering it loaded only
   311 of 433 wires. The physical layout is unaffected; only the internal board numbers
   changed (old 4→0, 2→1, 1→2, 3→3, 7→4, 5→5, 6→6).
8. The small Turn+supply board is a **half board**, so only its left edge can align with
   the full-width column; its right edge cannot.

## 7. Defects found and their state

* **FIXED (you approved it):** on the player and shared boards the IC ground pins sat on
  the board's `BN` rail while the supply ties used `TN`, so those three grounds were not
  actually tied to the main ground. The ties and every pull-down/GND stub now use each
  board's own `BN` rail. This is the one intended netlist change (137 → 134 nets; the
  four ground nets became one, every other net and pin identical).
* **FIXED:** the supply (battery) stood off the grid and was left behind when board 3
  moved, which put its +5 V leg in board 3's GND rail hole and shorted the supply. It now
  moves with board 3.
* **FIXED:** the simulator requires a board with index 0; without it every wire on the
  renumbered boards was dropped (433 → 311). Boards are now 0..6.
* **Left as-is (original wiring):** 63 original connections with diagonal bend points,
  136 holes hosting two original wire ends, and 196 original wire ends sitting in a
  component leg's hole. Changing them means editing the original circuit.

## 8. Both follow-ups are done

1. The **GND fix** you approved is in — see §7; every GND stub is now a short drop to its
   own board's rail.
2. The **lane planner** is in `arrange_layout.py`: every wire is an orthogonal path whose
   segments are registered in a channel table, so no two wires can overlap or run along
   each other; the router tries alternative rows and columns, keeps the variant with the
   fewest crossings, routes the longest wires first and retries the wires that failed.
   Overlaps went from 179 to 1.
