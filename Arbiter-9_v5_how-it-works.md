# Arbiter-9 v5 — how it works

Companion to `Arbiter-9_v5_arranged.json` (72 parts, 7 boards, 433 wires, 45 notes).
Open it at <https://www.logicbench.online/simulator-app> with *Open/Import*.

---

## 1. What the project is

Two layers on one canvas:

1. **The arbiter (original logic, unchanged)** — reads a 4-bit piece code from each
   side, compares the ranks, applies the special rules, and drives the round / flag /
   final result signals.
2. **The control layer (added)** — stores each player's submitted rank, locks out
   double submissions, hides the result until both players have submitted, and latches
   the game-over state until an explicit reset.

The arbiter's wires are all still there; the control layer was added **around** it, and
every new wire taps an existing signal through a free hole of the same 5-hole strip
rather than cutting or moving anything original.

---

## 2. Board arrangement

```
 PLAYER A           centre column (top → bottom)            PLAYER B
 x -2400 … -888     x 288 … 1800                            x 2208 … 3720
 y -348 … 36        ├ board 0  y -1440   nine-LED display    y -348 … 36
                    ├ board 1  y  -888   win / flag / final
                    ├ board 2  y  -336   compare / spy / inverters
                    ├ board 3  y   192   Turn switches + 5 V supply
                    └ board 4  y   744   SHARED CONTROL
```

| Board | Contents |
|---|---|
| **0** nine-LED display | `c1871` A_Win, `c1872` Tie, `c1873` B_Win, `c4001` Flag_A, `c4002` Flag_B, `c4003` A_Win_Final, `c4004` B_Win_Final, `c4005` Turn_A, `c4006` Turn_B + their 330 Ω resistors |
| **1** win logic | `c501` `c502` `c1205` 74HC08, `c1206` 74HC32, `c1319` 74HC08 |
| **2** compare logic | `c118` 74HC85, `c351` `c352` 74HC30, `c56` `c57` `c445` 74HC04 |
| **3** Turn + supply | `c4201` Turn_A, `c4202` Turn_B, `c4301` `c4302` pull-downs, `c2132` regulated 5 V supply |
| **4** shared control | `uS1` 74HC08, `uS2` 74HC32, `uS3` 74HC74, `uS4` 74HC14, `bR` reset button + `pR`, display LEDs `LD1..LD3`, game-over LED `LGO` + resistors |
| **5** PLAYER A | `c2` A rank DIP + pull-downs `c4..c7`, `bA` submit + `pA`, `uA1` 74HC175, `uA2` 74HC74, `uA3` 74HC11, `LA` A_Done LED + `rLA` |
| **6** PLAYER B | `c3` B rank DIP + pull-downs `c8..c11`, `bB` submit + `pB`, `uB1` 74HC175, `uB2` 74HC74, `uB3` 74HC11, `LB` B_Done LED + `rLB` |

Left/right gaps are equal (288 px). PLAYER A and PLAYER B are vertically centred on the
column and never touch each other; the only connections between them run through the
shared board (plus +5 V and GND).

---

## 3. How the arbiter decides a round (original rules)

The 4-bit code is `b3 b2 b1 b0` (b3 = MSB):

| code | piece | code | piece |
|---|---|---|---|
| 0000 | **Flag** | 1000 | Colonel |
| 0001 | **Private** | 1001 | Brigadier General |
| 0010 | Sergeant | 1010 | Major General |
| 0011 | 2nd Lieutenant | 1011 | Lieutenant General |
| 0100 | 1st Lieutenant | 1100 | 4-Star General |
| 0101 | Captain | 1101 | 5-Star General |
| 0110 | Major | 1110 | **Spy** |
| 0111 | Lieutenant Colonel | 1111 | unused |

Rank order: `Flag < Private < Sergeant < 2LT < 1LT < CPT < MAJ < LTC < COL < Brig <
MajGen < LtGen < 4-Star < 5-Star < Spy`, with two exceptions:

* **Private beats Spy** (the only piece that can).
* **Flag loses to every non-Flag piece**; Flag vs Flag is decided by the Turn switches
  (`c4201`/`c4202`), not by rank.

Outputs: `A_Win`, `Tie`, `B_Win` for the round, plus `Flag_A`/`Flag_B` and the final
signals `A_Win_Final = A_Win AND Flag_B`, `B_Win_Final = B_Win AND Flag_A`.

---

## 4. How the control layer works

### 4.1 Signals

| Signal | Where it is made | Meaning |
|---|---|---|
| `A_Submit` / `B_Submit` | `bA` / `bB` (10 kΩ pull-down) | "I have chosen my piece" |
| `A_Done` / `B_Done` | `uA2` / `uB2` (74HC74, D = +5 V, clocked once) | the submission is locked in |
| `Accept_A` | `uA3` (74HC11) | `A_Submit AND NOT A_Done AND NOT Game_Over` |
| `Accept_B` | `uB3` (74HC11) | `B_Submit AND NOT B_Done AND NOT Game_Over` |
| `A_Stored_Rank[3:0]` | `uA1` (74HC175) | the captured piece code |
| `Display_Enable` = `Round_Ready` | `uS1` gate 1 | `A_Done AND B_Done` |
| `A_WIN_DISPLAY`, `TIE_DISPLAY`, `B_WIN_DISPLAY` | `uS1` gates 2-4 | raw result `AND Display_Enable` |
| `Game_Over` | `uS3` (74HC74) | latched `A_Win_Final OR B_Win_Final` |
| `/Reset`, `/Game_Over` | `uS4` (74HC14) | inverted reset and game-over, clearing signals |

`Accept_A` is the **only** clock that reaches `uA1` and `uA2`. Because it contains
`NOT A_Done`, a second press cannot clock the register again: that is the lockout.

### 4.2 The round sequence

1. Player A sets the piece with the **A INPUTS** DIP switch (`c2`) and presses
   **A SUBMIT** (`bA`).
2. `Accept_A` rises → `uA1` captures the four bits → `uA2` sets `A_Done`.
   `LA` lights ("A has submitted"). Pressing submit again changes nothing.
3. Player B does the same with `c3` and `bB`; `LB` lights.
4. `Display_Enable` goes HIGH, so `uS1` passes the arbiter's raw result to
   `LD1` (A_WIN_DISPLAY), `LD2` (TIE_DISPLAY), `LD3` (B_WIN_DISPLAY).
   Until both players have submitted those three LEDs are dark.
5. If the round is a flag capture (`A_Win_Final` or `B_Win_Final`), `uS2` ORs them and
   `uS3` latches `Game_Over`; `LGO` lights and `/Game_Over` blocks both `Accept`
   terms, so no further submissions are taken.
6. A deliberate press of **ROUND/GAME RESET** (`bR`) pulls `/Reset` LOW, which clears
   `A_Done`, `B_Done`, both rank registers and `Game_Over` → the next round starts.
   Note that the reset only *holds* the game-over latch clear: if the switches are still
   showing a flag capture, the latch re-arms the moment the button is released, so
   change a piece code first when you want to play on.

---

## 5. Pin-by-pin guide for the added ICs

All pin numbers are DIP pin numbers (what the simulator uses).

**74HC175 — `uA1` / `uB1` (rank register)**
1 = MR (active low) ← `/Reset`; 9 = CP ← `Accept_A` / `Accept_B`; 16 → +5 V, 8 → GND.
The four D inputs take the DIP-switch bits: 1D (pin 4) ← S1, 2D (pin 5) ← S4,
3D (pin 12) ← S3, 4D (pin 13) ← S2, so the captured code lands on 1Q…4Q =
pins 2, 6, 11, 15. **Those four Q outputs are currently unwired** (see §8).

**74HC74 — `uA2` / `uB2` (submission) and `uS3` (game over)**
1 = 1CLR̄ ← `/Reset`; 2 = 1D ← +5 V; 3 = 1CLK ← `Accept_*` (or the final-OR gate);
4 = 1PRĒ ← +5 V; 5 = 1Q = the flag; 14 → +5 V, 7 → GND. The second half is tied off:
10, 13 ← +5 V; 11, 12 → GND.

**74HC11 — `uA3`, `uB3` (accept gates)**
Gate 1: in 1, 2, 13 → out 12. `uA3`: 1 = `A_Submit`, 2 = `/A_Done`, 13 = `/Game_Over`.
Gate 2: in 3, 4, 5 → out 6. `uB3`: 3 = `B_Submit`, 4 = `/B_Done`, 5 = `/Game_Over`.
14 → +5 V, 7 → GND. All unused inputs are tied to GND.

**74HC08 — `uS1` (display gate)**
Gate 1: 1 = `A_Done`, 2 = `B_Done` → 3 = `Display_Enable`.
Gate 2: 4 = raw `A_Win`, 5 = `Display_Enable` → 6 = `A_WIN_DISPLAY`.
Gate 3: 9 = raw `Tie`, 10 = `Display_Enable` → 8 = `TIE_DISPLAY`.
Gate 4: 12 = raw `B_Win`, 13 = `Display_Enable` → 11 = `B_WIN_DISPLAY`.

**74HC32 — `uS2` (final OR)**
Gate 1: 1 = `A_Win_Final`, 2 = `B_Win_Final` → 3 = final-OR into `uS3` pin 3.

**74HC14 — `uS4` (inverters)**
1 = `Reset` → 2 = `/Reset`; 3 = `Game_Over` → 4 = `/Game_Over`. Unused inputs to GND.

**Indicators** — each LED sits in series with a 330 Ω resistor between its driver
signal and GND: `LA`→`A_Done`, `LB`→`B_Done`, `LGO`→`Game_Over`, `LD1..LD3`→the three
gated display outputs.

---

## 6. Wiring conventions used everywhere

* **5-hole strips.** A wire never lands in a hole that holds a component leg; it lands in
  a *different* hole of the same strip, and no two wire ends share a hole.
* **Right angles only.** Every wire is a series of horizontal and vertical pieces; there
  are no diagonal segments in any re-routed wire.
* **Channel registry.** `arrange_layout.py` allocates each horizontal lane and vertical
  column through a registry, so no two new wires overlap or run along each other.
* **Colours.** red `+5 V`, black `GND`, blue A rank bus, purple B rank bus, amber
  Reset/Submit, green `A_Done`/`B_Done`/`Display_Enable`, teal finals, orange display
  outputs.
* **Lanes run in the gaps:** the free space left/right of the centre column carries the
  vertical runs, the free bands between the stacked boards carry the horizontal runs.

---

## 7. Operating it in the simulator

1. Open/Import `Arbiter-9_v5_arranged.json`, then *Fit to view*.
2. Leave the two Turn switches (`c4201`, `c4202`) OFF for a normal round; for Flag vs
   Flag set exactly one ON.
3. Set A's piece on `c2`, press **A SUBMIT**; set B's piece on `c3`, press **B SUBMIT**.
4. Read `LD1/LD2/LD3` — they only light once both `LA` and `LB` are lit.
5. If `LGO` lights, the game is over: press **ROUND/GAME RESET** to begin again.

---

## 8. Invariants kept (and the one thing to know)

* The netlist is what the previous file had, **except** that the player and shared
  boards' grounds now really join the main ground (137 → 134 nets; four ground nets
  became one, the only intended change).
* Original parts, IDs, labels, colours and the nine original LEDs are untouched; the
  original 307 connections all still exist except the ones that ran through the empty
  board that was removed — those nets were re-connected on the boards that use them.
* **Known limitation — the stored rank does not drive the arbiter yet.** The
  comparator is still fed by the **live DIP switches** (that is the original wiring),
  and the register outputs (pins 2, 6, 11, 15) are not connected to anything. The
  registers do capture and lock the submitted code — changing the switches after
  submitting does not change `A_Stored_Rank`/`B_Stored_Rank` — but the displayed result
  follows the switches. To make the arbiter use the stored code, re-point the seven
  existing wires that feed the comparator at the register outputs, as described in
  `Arbiter-9-upgraded-report.md` §9.
