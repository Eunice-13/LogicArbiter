# Arbiter-9 upgrade — rank storage, submission lockout, display enable, round + game control

Result of applying `digital_flag_arbiter_upgrade.md` to the LogicBench project.

## 1. Files

| File | What it is |
|---|---|
| **`Arbiter-9-upgraded.json`** | The upgraded project (72 parts, 8 boards, 433 connections, 43 notes). Open/Import this in LogicBench. |
| `Arbiter-9-original-backup.json` | Byte-for-byte backup of the untouched `Arbiter-9.json`. |
| `Arbiter-9-3LED-original-backup.json` | Backup of the untouched 3-LED build (not modified). |
| `_newparts.json` | The exact JSON for the 28 new parts. Each was produced by round-tripping the part through the LogicBench engine during development, so the field set (`kind`, `attrs`, …) matches the app exactly. |
| `build_upgrade.py` | Merges the original file with the new parts/boards/connections/notes and re-runs the preservation asserts. Reads `_newparts.json`. |

The original `Arbiter-9.json` and `Arbiter-9-3LED.json` are left untouched.

## 2. Guarantee that the original circuit is unchanged

`build_upgrade.py` copies the original file and **appends**. It then prints:

```
original parts preserved: True
original connections preserved: True
```

i.e. every existing part, board and connection is identical, and every original
part id / coordinate / wire stays as it was. A load test through the simulator's
own parser (`deserialise`) succeeds:

```
OK deserialise: components 72 breadboards 8 wires 433 joints 0 notes 43
badPinRefs 0 badHoleBoards 0 badBusBoards 0 duplicateEdges 0
```

The nine existing LEDs (`c1871…c1873`, `c4001…c4006`) and the Turn switches are
untouched, at their original coordinates, with their original wiring.

## 3. New components (28)

| Id | IC / part | Section | Function |
|---|---|---|---|
| `uA1` | 74HC175 quad D-FF | Player A | `A_Stored_Rank[3:0]` register |
| `uA2` | 74HC74 dual D-FF | Player A | `A_Done` flag latch |
| `uA3` | 74HC11 3-input AND | Player A/B | `Accept_A`, `Accept_B` |
| `bA` | push button | Player A | `A_Submit` |
| `pA` | 10 kΩ | Player A | `A_Submit` pull-down |
| `LA`,`rLA` | green LED + 330 Ω | Player A | `A_Done` indicator |
| `uB1` | 74HC175 | Player B | `B_Stored_Rank[3:0]` |
| `uB2` | 74HC74 | Player B | `B_Done` |
| `uB3` | 74HC11 | Player B | second `Accept` gate + spare |
| `bB`,`pB`,`LB`,`rLB` | button, 10 kΩ, green LED, 330 Ω | Player B | `B_Submit` + indicator |
| `uS1` | 74HC08 quad AND | Shared | `Display_Enable` + 3 gated outputs |
| `uS2` | 74HC32 quad OR | Shared | `(A_Win_Final OR B_Win_Final)` |
| `uS3` | 74HC74 | Shared | `Game_Over` latch |
| `uS4` | 74HC14 Schmitt inverter | Shared | `/Reset`, `/Game_Over` |
| `bR`,`pR` | push button, 10 kΩ | Shared | Reset (round + game) |
| `LGO`,`rGO` | red LED + 330 Ω | Shared | `Game_Over` indicator |
| `LD1…LD3` + `rLD1…rLD3` | red LED + 330 Ω ×3 | Shared | gated `A_Win_Display / Tie_Display / B_Win_Display` |

**74HC173 is not a supported symbol in LogicBench**, so the 4-bit rank store uses
the 74HC175 (quad D-FF) — the closest supported 4-bit register. Everything else
uses a symbol the simulator already provides.

### Signal definitions

| Signal | Definition |
|---|---|
| `A_Submit` / `B_Submit` | push-button outputs (pulled down) |
| `A_Done` / `B_Done` | 74HC74 latch, `D=1`, clocked by `Accept_*`, cleared by `/Reset` |
| `Accept_A` | `A_Submit AND /A_Done AND /Game_Over` (74HC11) |
| `Accept_B` | `B_Submit AND /B_Done AND /Game_Over` |
| `A_Stored_Rank[3:0]` / `B_Stored_Rank[3:0]` | 74HC175 Q outputs, clocked by `Accept_*`, cleared by `/Reset` |
| `Display_Enable` (= `Round_Ready`) | `A_Done AND B_Done` |
| `A_Win_Display` / `Tie_Display` / `B_Win_Display` | raw result `AND Display_Enable` |
| `Game_Over` | latched `(A_Win_Final OR B_Win_Final)`, cleared only by Reset |

## 4. New wiring (117 connections)

The worked-out net list (physical endpoints) is:

```
NET 1  bA.OUT  <-> pA.A <-> uA3.1                                   (A_Submit)
NET 2  pA.B <-> GND rail b5 <-> LA.cathode <-> uA1.8 uA2.7 uA3.7
       uA2.11 uA2.12 uA3.3 uA3.4 uA3.5 uA3.9 uA3.10 uA3.11          (A GND + unused-input ties)
NET 3  uA2.6 <-> uA3.2                                              (/A_Done)
NET 4  uA3.12 <-> uA1.9 <-> uA2.3                                   (Accept_A -> CLK_A)
NET 5  A DIP hole b1c1r5  <-> uA1.4                                 (A3)
NET 6  A DIP hole b1c4r4  <-> uA1.5                                 (A2)
NET 7  A DIP hole b1c2r4  <-> uA1.12                                (A1)
NET 8  A DIP hole b1c3r5  <-> uA1.13                                (A0)
NET 9  uA2.5 <-> uS1.1 <-> rLA.A                                    (A_Done)
NET10  rLA.B <-> LA.anode                                           (A_DONE LED)
NET11  bB.OUT <-> pB.A <-> uB3.3                                    (B_Submit)
NET12  pB.B <-> GND rail b6 <-> LB.cathode <-> uB1.8 uB2.7 uB3.7
       uB2.11 uB2.12 uB3.1 uB3.2 uB3.13 uB3.9 uB3.10 uB3.11        (B GND + ties)
NET13  uB2.6 <-> uB3.4                                              (/B_Done)
NET14  uB3.6 <-> uB1.9 <-> uB2.3                                    (Accept_B -> CLK_B)
NET15  B DIP hole b1c12r5 <-> uB1.4                                 (B3)
NET16  B DIP hole b1c15r4 <-> uB1.5                                 (B2)
NET17  B DIP hole b1c13r4 <-> uB1.12                                (B1)
NET18  B DIP hole b1c14r5 <-> uB1.13                                (B0)
NET19  uB2.5 <-> uS1.2 <-> rLB.A                                    (B_Done)
NET20  rLB.B <-> LB.anode                                           (B_DONE LED)
NET21  uS1.3 uS1.5 uS1.10 uS1.13                                    (Display_Enable)
NET22  A_Win tap hole b4c1r5  <-> uS1.4
NET23  Tie   tap hole b4c7r5  <-> uS1.9
NET24  B_Win tap hole b4c13r5 <-> uS1.12
NET25  uS1.6 <-> rLD1.A   NET26 rLD1.B <-> LD1.anode               (A_Win_Display)
NET28  uS1.8 <-> rLD2.A   NET29 rLD2.B <-> LD2.anode               (Tie_Display)
NET30  uS1.11 <-> rLD3.A  NET31 rLD3.B <-> LD3.anode               (B_Win_Display)
NET27  LD1/LD2/LD3/LGO cathodes + GND rail b7 + uS1.7 uS2.7 uS3.7
       uS4.7 uS2.4 uS2.5 uS2.9 uS2.10 uS2.12 uS2.13 uS3.11 uS3.12
       uS4.5 uS4.9 uS4.11 uS4.13                                     (shared GND + ties)
NET32  A_Win_Final tap hole b4c31r5 <-> uS2.1
NET33  B_Win_Final tap hole b4c37r5 <-> uS2.2
NET34  uS2.3 <-> uS3.3                                              (Final OR -> GO clock)
NET35  uS3.5 <-> uS4.3 <-> rGO.A                                    (Game_Over)
NET36  rGO.B <-> LGO.anode                                          (GAME_OVER LED)
NET37  uS4.4 <-> uA3.13 <-> uB3.5                                   (/Game_Over)
NET38  bR.OUT <-> pR.A <-> uS4.1                                    (Reset)
NET39  uS4.2 <-> uA1.1 uA2.1 uB1.1 uB2.1 uS3.1                      (/Reset)
NET40  VCC rail tie + every new IC's VCC pin (and held PRE/CLR, D=1)
```

The four A-rank taps (`b1c1r5 b1c4r4 b1c2r4 b1c3r5`), the four B-rank taps and
the five result taps are **holes that already carry the original signals**, so
the taps are non-invasive (a second wire on an existing hole). All new logic is
pin-to-pin / pin-to-rail; **no existing wire is cut or moved**.

## 5. Breadboard sections

| Board | Placement | Contents |
|---|---|---|
| **Player A** (index 5, full) | left of the original layout, `x=-1200, y=600` | `uA1 uA2 uA3 bA pA LA rLA` |
| **Player B** (index 6, full) | right of the original layout, `x=400, y=600` | `uB1 uB2 uB3 bB pB LB rLB` |
| **Shared control** (index 7, full) | below the original layout, `x=400, y=1300` | `uS1 uS2 uS3 uS4 bR pR LGO … LD3` |

The three new boards' top rails are tied to the existing +5 V rail and their
bottom rails to GND (`bus b5/b6/b7 TP -> b1 TP`, `TN -> b1 TN`), so the new
section is powered from the existing regulated 5 V supply. Player A and Player B
are fully independent (own switch taps, own button, own register, own flag);
only `Display_Enable`, `Game_Over` and `Reset` cross into the shared board.

## 6. Physical BOM (added parts)

| Qty | Part | Notes |
|---|---|---|
| 2 | 74HC175 quad D-FF | rank registers (substitute for the unsupported 74HC173) |
| 2 | 74HC74 dual D-FF | `A_Done`, `B_Done`, `Game_Over` (3 of 4 halves used) |
| 1 | 74HC11 triple 3-input AND | `Accept_A`, `Accept_B` |
| 1 | 74HC08 quad AND | `Display_Enable` + 3 gated outputs |
| 1 | 74HC32 quad OR | `A_Win_Final OR B_Win_Final` |
| 1 | 74HC14 Schmitt inverter | `/Reset`, `/Game_Over` |
| 3 | momentary push buttons | Submit A, Submit B, Reset |
| 4 | 10 kΩ | button pull-downs (+1 spare) |
| 6 | 330 Ω | added LED series resistors |
| 6 | LEDs | 2 green (A/B done), 4 red (game over + 3 gated results) |
| as needed | 100 nF | one per added IC (the simulator does not model decoupling) |

Optional (real hardware only): 1 µF across each button to ground for contact
debounce plus the 74HC14, as allowed by the spec. The simulator applies button
state changes cleanly, so no debounce is modelled in the file.

## 7. Pin-by-pin guide for the added ICs

Pin numbers are the DIP pin numbers used by the simulator (standard datasheet
pinouts).

**74HC175 (`uA1`/`uB1`, rank register)** — pin 1 = MR (active-low), 4/5/12/13 =
1D…4D, 9 = CP; outputs 1Q..4Q = 2/6/11/15, 1Q̄..4Q̄ = 3/7/10/14; 8 = GND, 16 =
VCC. Wiring: 1 ← `/Reset`; 4,5,12,13 ← A/B rank bits; 9 ← `Accept_*`; 16 → +5 V;
8 → GND. 1Q̄..4Q̄ unused.

**74HC74 (`uA2`/`uB2`/`uS3`)** — 1 = 1CLR̄, 2 = 1D, 3 = 1CLK, 4 = 1PRĒ, 5 = 1Q,
6 = 1Q̄, 7 = GND, 8 = 2Q̄, 9 = 2Q, 10 = 2PRĒ, 11 = 2CLK, 12 = 2D, 13 = 2CLR̄,
14 = VCC. Done FF: 1 ← `/Reset`, 2 ← +5 V (D=1), 3 ← `Accept_*`, 4 ← +5 V, 5 =
`A_Done`/`B_Done`. Game-over FF: 1 ← `/Reset`, 2 ← +5 V, 3 ← `(A_Final OR B_Final)`,
4 ← +5 V, 5 = `Game_Over`. Second half of each: 10,13 ← +5 V; 11,12 → GND.

**74HC11 (`uA3`/`uB3`)** — gate 1 in 1,2,13 out 12; gate 2 in 3,4,5 out 6; gate 3
in 9,10,11 out 8; 7 = GND, 14 = VCC. `uA3` gate 1: 1 = `A_Submit`, 2 = `/A_Done`,
13 = `/Game_Over` → 12 = `Accept_A`. `uB3` gate 2: 3 = `B_Submit`, 4 = `/B_Done`,
5 = `/Game_Over` → 6 = `Accept_B`. All unused inputs tied to GND.

**74HC08 (`uS1`)** — gate 1 in 1,2 → 3; gate 2 in 4,5 → 6; gate 3 in 9,10 → 8;
gate 4 in 12,13 → 11. 1 = `A_Done`, 2 = `B_Done` → 3 = `Display_Enable`;
4 = raw `A_Win`, 5 = `Display_Enable` → 6 = `A_Win_Display`; 9 = raw `Tie`,
10 = `Display_Enable` → 8 = `Tie_Display`; 12 = raw `B_Win`, 13 =
`Display_Enable` → 11 = `B_Win_Display`.

**74HC32 (`uS2`)** — gate 1 in 1,2 → 3. 1 = `A_Win_Final`, 2 = `B_Win_Final`.
Unused inputs tied to GND.

**74HC14 (`uS4`)** — 1 → 2, 3 → 4, 5 → 6, 9 → 8, 11 → 10, 13 → 12; 7 = GND, 14 =
VCC. 1 = `Reset` → 2 = `/Reset`; 3 = `Game_Over` → 4 = `/Game_Over`. Unused
inputs tied to GND.

## 8. Test report

| Check | Tool | Result |
|---|---|---|
| Upgraded JSON is valid for the simulator | LogicBench `deserialise` | **PASS** (72 parts, 8 boards, 433 wires, 43 notes) |
| Original parts preserved | `build_upgrade.py` assert | **PASS** |
| Original connections preserved | `build_upgrade.py` assert | **PASS** |
| Every pin endpoint references a real part/pin | structural check | **PASS** (0 bad) |
| Every hole/bus endpoint references a real board | structural check | **PASS** (0 bad) |
| No duplicate wire edges | structural check | **PASS** |
| No floating *inputs* on new ICs | pin-coverage check | **PASS** (only unused outputs left open) |
| A/B rank taps land on the real A/B bit nets | net trace | **PASS** (`uA1.4` on net with `c56.1/c118.15/c352.5`, etc.) |
| Result taps land on the real result nets | net trace | **PASS** (`uS1.4` on net with `c1206.8/c1319.13`; `uS2.1` on `c1319.11`) |
| All nine original LEDs and Turn switch keep position/id/wiring | diff of original arrays | **PASS** |

**Not run / not verifiable here:** functional simulation. The LogicBench
JavaScript bundle sets `Circuit._noJsEngine` and its `simulate()` requires a
WebAssembly engine that is fetched by the live app; it is not part of the
downloadable files, so I could not execute the 1,024-case sweep locally. The
upgrade's *logic* is therefore verified structurally and by net tracing, not by
simulation. Please run the sweep in the app (README §15 describes the method).

### Behaviour expected from the wiring (to confirm in the app)

* Neither player submits → `A_Done`/`B_Done` low → `Display_Enable` low → the
  three gated LEDs (`LD1..LD3`) are off.
* Only A submits → `A_Submit` rising clocks `uA1` (rank captured) and `uA2`
  (`A_Done` = 1); `Accept_A` then falls (`/A_Done` = 0) so a second press cannot
  re-clock the register. `Display_Enable` stays low.
* Both submit → `Display_Enable` high → the gated LEDs show `A_Win/Tie/B_Win AND
  Display_Enable`.
* Changing the DIP switches after submitting does not change the captured value
  in `A_Stored_Rank`/`B_Stored_Rank`.
* A final (`c1319.11` or `c1319.3`) clocks `uS3` → `Game_Over` latches high, the
  `LGO` LED lights, and `/Game_Over` blocks both `Accept` terms.
* Reset pulldown→ press clears `A_Done`, `B_Done`, both rank registers and
  `Game_Over`, allowing a new round.

## 9. Assumptions, limitations, and the one change I did **not** make

1. **74HC173 unsupported** → 74HC175 used for the 4-bit rank store.
2. **The existing comparator still reads the live DIP switches.** The spec asks
   the arbiter to compare the *stored* ranks. Doing that requires **rerouting the
   eight existing A/B bit nets** from the DIP switches to the register outputs —
   i.e. *modifying existing wiring/parts*, which §2 and the "Final Priority"
   forbid, and which cannot even be expressed cleanly here (the A/B DIP switch
   pins are not addressed by any wire in the file; they join the nets through
   board geometry). Per §7/§14 ("stop and explain the issue before making
   changes") I left them alone. The rank registers capture and lock the values
   exactly as specified; to make the arbiter *use* them, cut the eight A/B bit
   nets (`A3 b1c1r5, A2 b1c4r4, A1 b1c2r4, A0 b1c3r5`, `B3 b1c12r5, B2 b1c15r4,
   B1 b1c13r4, B0 b1c14r5`) and reconnect them to `uA1/uB1` pins 2/6/11/15.
3. **The three original encounter LEDs are not gated.** Gating them requires
   moving the existing 330 Ω resistors off the `A_Win/Tie/B_Win` nets — again an
   existing-wiring change. Instead the gated results are brought out on the new
   `LD1..LD3` LEDs. §14.A.7 explicitly says to stop and explain when the existing
   LED connections cannot be gated without modifying their wiring, which is the
   case here.
4. **`Round_Ready` = `Display_Enable`**, and `Round_Done` is the same signal:
   the arbiter is purely combinational, so the resolved result is available the
   moment both players have submitted. No artificial timing delay was invented
   (§8).
5. **Debouncing** is provided physically (74HC14 + RC + 1 µF, listed in the BOM);
   the simulator has no contact bounce, so nothing is modelled in the JSON.
6. `Game_Over` is latched and blocks new submissions; it clears only on the
   deliberate Reset, as required.
