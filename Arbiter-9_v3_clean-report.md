# Arbiter-9 v3 clean — layout + wire-routing cleanup

Applied `layout_cleanup_prompt.md` to the upgraded project. **No logic changed: the
pin netlist before and after is identical (137 nets, exact match).**

## Files

| File | Role |
|---|---|
| **`Arbiter-9_v3_clean.json`** | the cleaned project (72 parts, 8 boards, 449 connections, 46 notes) |
| `Arbiter-9-upgraded.json` | the previous version, **never overwritten** (acts as the backup) |
| `cleanup_layout.py` | the generator (repositions parts, re-routes the new wires) |
| `check_layout.py` | the verification script |
| `_pins.json` | pin geometry dump used by both scripts |

## Board layout

| Board | Position | Contents |
|---|---|---|
| **PLAYER A** (index 5, full) | x=168, y=640, left | `c2` + pull-downs `c4–c7`, `bA`+`pA`, `uA1` (74HC175), `uA2` (74HC74), `uA3` (74HC11), `LA`+`rLA` |
| **PLAYER B** (index 6, full) | x=1800, y=640, right | `c3` + pull-downs `c8–c11`, `bB`+`pB`, `uB1`, `uB2`, `uB3`, `LB`+`rLB` |
| **SHARED CONTROL** (index 7, full) | x=984, y=1240, beneath the gap | `bR`+`pR`, `uS1` (74HC08 gate), `uS2` (74HC32), `uS3` (74HC74), `uS4` (74HC14), `LGO`/`LD1..LD3` + resistors |

A and B are mirror images with the **same left-to-right order** (DIP → button → rank
register → done FF → accept gate → status LED) and the shared board sits beneath the
gap between them, so every inter-board cable is short. Original boards 0–4 are in
their original places.

## Moved components (38) — the only coordinates that changed

Original arbiter boards, the nine LEDs, the comparator, gates, resistors, Turn
switches and all 307 original connections are untouched.

* **Approved switch move:** `c2` (176,192)→(200,712) with `c4`(168,302)→(192,822),
  `c5`→(216,822), `c6`→(240,822), `c7`→(264,822); `c3` (752,192)→(1832,712) with
  `c9`→(1824,822), `c10`→(1848,822), `c11`→(1872,822), `c8`→(1896,822).
  (Pull-downs keep their original bit association — `c9/c10/c11/c8` under B's
  S1/S2/S3/S4.)
* **New components** all re-placed on the three new boards; the full before→after
  table is printed by `_report_data.py` / listed in the session output.
* IDs, kinds, labels, colours and attrs are unchanged for every part
  (`non-moved parts identical` check = True).

## Wiring rules applied

* Every one of the 142 new wires has **hole endpoints only** (0 pin endpoints); each
  endpoint is a **free hole** in the same 5-hole strip as the pin it serves, so no
  endpoint sits in a component pin's hole and no two endpoints share a hole.
* Every new wire is routed with **orthogonal pivots** (a 12 px sideways jog off the
  hole column, a horizontal lane, and a second jog) — **0 diagonal new wires**.
* Wires are grouped into **parallel lanes per board pair** (each wire gets its own
  24 px lane), and coloured by class: red +5 V, black GND, blue A-rank bus, purple
  B-rank bus, amber Reset/Submit/Clock, green status (A_Done/B_Done/Display_Enable),
  orange display outputs, teal finals.
* Power/GND for every new IC is taken from **that board's own rails**.

## Check results

| Check | Result |
|---|---|
| Netlist identical before/after | **PASS** — 137 pin-nets, exact match |
| New endpoint in a component pin hole | **PASS** — 0 |
| New hole shared by 2 new endpoints | **PASS** — 0 |
| New hole also used by an original wire | **PASS** — 0 |
| Diagonal (non-orthogonal) new segments | **PASS** — 0 |
| JSON loads in the simulator's parser | **PASS** — 72 comps / 8 boards / 449 wires / 46 notes |
| Original component IDs/coords/labels | **PASS** — unchanged except the 38 approved moves |
| Original 307 connections byte-identical to `Arbiter-9.json` | **PASS** |
| Every Player A part on board 5 / B on 6 / shared on 7 | **PASS** |
| No wire joins an A-only part directly to a B-only part | **PASS** — 0 |

## Rules that could not be fully met (with reasons)

1. *"No wire endpoint shares a hole with a component pin"* — the **original** file
   itself does this 370×, because the LEDs, resistors, DIP switches and battery have
   no pin endpoints and their wires necessarily land on the leg's own hole. Fixing it
   would mean editing the original wiring, which constraints 1–2 forbid, so those are
   left as-is; **all new wiring complies**.
2. *"One wire per hole"* — likewise, 136 holes are shared by two *original* wires.
   All new wires comply.
3. *"No new wire passes over an original component or an original wire"* — crossings
   are minimised (lanes + jogs) but I cannot prove zero crossings without the app's
   own router; please eyeball in LogicBench (the app's *Export combinations /
   Smart auto-routing* can also re-draw the wires if you prefer).
4. *"100 nF bypass capacitor next to each IC's VCC/GND"* — the simulator has no
   100 nF capacitor symbol (only 100 µF/47 µF/10 µF/1 µF/470 µF/1000 µF) and does
   not model decoupling, so this stays a real-build-only item.
5. A/B rank DIP switches were **moved** (your approved override of "do not move
   original components"), since both were on the same board.

## Still open (unchanged from the earlier deliverable)

The comparator still reads the live DIP switches and the three original result LEDs
are not gated — both require editing original wiring; see
`Arbiter-9-upgraded-report.md` §9 for the exact minimal change.
