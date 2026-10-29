# Task: Rearrange the Breadboards and Re-route the Wires (Neat, Untangled, Player A Left, Player B Right)

Change only the position of whole breadboards, remove the one unused breadboard, and re-route the wires of the NEW parts. Do not change any logic or any electrical connection.

## Problem

- The breadboards are scattered with no clear order, and Player A and Player B cannot be told apart.
- Long straight diagonal wires cross the whole canvas, and many wires are stacked in one line or one bundle, so I cannot tell which wire goes where.
- Wire endpoints sit in the same hole as a component pin or leg, so it is unclear what is connected to what.

## Target

Match the neatness of the earlier "final" version of the project (the reference circuit): every wire has its own designated hole, nothing is tangled, and every signal can be traced by eye from start to end. Use that file as the style reference for spacing, wire colors, routing and labeling.

## Target arrangement

```
 PLAYER A          4 BOARDS LINED UP VERTICALLY          PLAYER B
┌─────────┐       ┌───────────────────────────┐         ┌─────────┐
│         │       │ 1. Top board (9 LEDs)     │         │         │
│         │       ├───────────────────────────┤         │         │
│         │  ───► │ 2. Second arbiter board   │ ◄───    │         │
│ PLAYER  │       ├───────────────────────────┤         │ PLAYER  │
│    A    │  ───► │ 3. Small input board      │ ◄───    │    B    │
│         │       │    (Turn buttons, supply) │         │         │
│         │       ├───────────────────────────┤         │         │
│         │  ───► │ 4. SHARED CONTROL         │ ◄───    │         │
└─────────┘       └───────────────────────────┘         └─────────┘
```

1. **Player A board on the far left, Player B board on the far right.** They are mirror images: same size, same top edge, same left-to-right order of parts. Each player board is vertically centered against the center column, so the wires to both sides are about the same length.
2. **Four boards sit in one tidy column between them**, stacked top to bottom: the top board with the nine LEDs, the second arbiter board, the small input board that holds the Turn buttons and the power supply, and the Shared Control board. Align their left and right edges so the column is straight. Identify each board by its contents and position in the current file, not by its name.
3. **Player A and Player B are never next to each other.** The center column always separates them.
4. Leave an even, generous gap on each side of the center column. This is where the wire lanes run. A's wires leave from A's right edge into the left gap. B's wires leave from B's left edge into the right gap.
5. Keep the same gap size on the left and on the right, so the layout looks balanced.

## Player A and Player B must stay separate

- Player A's board holds only A's rank DIP switch, Submit A, A's 74HC173, A_Done flip-flop, debounce parts and the optional "A submitted" LED.
- Player B's board holds only the matching B parts, in the same left-to-right order as A's board.
- Nothing from one player sits on the other player's board. This includes switches, buttons, wires, resistors and ICs.
- A and B signals never share a wire, hole or rail, except +5V and GND. The only connections between the two sides go through the shared control board.
- The shared control board holds only the shared logic: Display_Enable, Round_Ready / Round_Done, Game_Over latch, Reset logic and display gating.
- Reuse the original DIP switches and the Turn button where they are. Do not copy or duplicate them. If both original DIP switches are on the same board, stop and ask me before moving anything.
- Label the boards "PLAYER A", "PLAYER B" and "SHARED CONTROL".

## Remove the unused breadboard

The small breadboard in the middle of the two small boards (the second small board, which sits right of the small input board) looks unused. Verify it, then remove it:

1. List every component and every wire endpoint that sits on that board.
2. **If it holds no components,** remove it.
3. **If wires still end on it,** do not just delete it, because that would break nets. Check which nets those wires carry and connect their other ends directly to the same nets on the board that really uses them. The netlist must stay identical after the removal. Remove the old wires only after the replacement connections exist.
4. **If it still holds any original component** (for example a DIP switch or resistors), do not delete the board and do not move that part by yourself. Tell me what the part is and propose where it should go, then wait for my approval.
5. Do not remove any other board unless it also ends up with no components and no wire endpoints. Report each board you remove and why.
6. Report the final list of boards: the two player boards and the four center boards.

## How to move things (this overrides the earlier "do not move" rule, but only in this way)

1. Move each breadboard as one rigid piece together with everything on it. Every component keeps the same position, orientation and ID relative to its board.
2. Do not move any component from one board to another, and do not change any pin or hole assignment, unless I approve it.
3. Do not change any component ID, label, color or property of the original parts.
4. Wire endpoints that sit on a moved board move with that board. Wires between boards are re-routed afterward (see the wiring rules).
5. Only the NEW components (74HC173 x2, 74HC74, 74HC14, new buttons, new resistors, capacitors, optional indicator LEDs) and the NEW wires may be repositioned or re-routed individually. Original boards, ICs, LEDs, resistors, DIP switches, the Turn button and original wires keep their positions relative to their boards.

## Wiring style (match the reference circuit)

1. **Wires are spread out, not bundled.** Each signal has its own path, and no two wires run along the same line.
2. **Right-angle bends only.** Every wire is made of short straight horizontal and vertical pieces with elbows. There are no diagonal wires.
3. **Each signal has its own lane.** Vertical wires drop beside each IC, one column per signal. Horizontal wires run in the open space between boards, one row per signal. Lanes are evenly spaced and parallel, so each wire can be followed by eye.
4. **Wires are color coded.** Different signal groups have different colors (orange, green, purple, blue, teal, yellow, red for +5V, black for GND). Use the same colors for the same kind of signal on every board. Neighboring lanes should not share a color when it can be avoided.
5. **GND and +5V are short.** GND is a short black stub straight to the nearest rail. +5V is a short red stub straight to the nearest rail. Use the local rails on every board. Power wires never run across the canvas.
6. **Every wire has its own hole.** No wire sits in the same hole as an IC pin, resistor leg, LED leg, capacitor leg, switch or button. A wire that joins a pin's net lands in a different hole of the same 5-hole strip. No two wire endpoints share a hole.
7. **Buses stay in order.** Wires in the same bus (for example the 4-bit rank buses A_Stored_Rank[3:0] and B_Stored_Rank[3:0]) run side by side as parallel lanes in the same order, with no crossings inside the bus. Each wire in the bus still gets its own row, so the four wires are visibly separate.
8. **Few crossings.** If two wires must cross, cross them once at a right angle. Never let them overlap or run along each other.
9. **Tidy connection areas.** Signals that cross between boards (A_Stored_Rank, B_Stored_Rank, A_Done, B_Done, Display_Enable, Reset, Game_Over) leave and arrive at one tidy connection area on the board edge that faces the other board. Add a small text label for each signal.
10. **IC placement.** New ICs share the same pin 1 orientation. Leave at least 2 empty columns between neighboring ICs so wires can reach each pin. Put each 100 nF bypass capacitor right next to its IC's VCC/GND pins. Put optional indicator LEDs and their resistors on the board that owns them. They must not use or overlap the original nine LEDs.

## Routing method

For every new wire:

1. Start from a free hole in the same strip as the source pin (never the pin's own hole).
2. Move straight vertically out of the IC area to a free row in the gap between boards.
3. Run horizontally along that row in its own lane.
4. Move straight vertically to the column of the destination, and end in a free hole in the same strip as the destination pin.
5. Give each wire its own row in the gap and its own column beside the ICs. Do not reuse a lane for a second wire.
6. Do not run any new wire over an original IC, an original LED or an original wire.

If the file format has no bend points, use short helper wires through in-between holes (or the file's own routing points, if it has any) to make the same elbow-shaped paths. Do not use long diagonal wires.

## Hard constraints

1. The netlist after the rearrangement and re-routing must be identical to the netlist before it. Only positions and wire paths may change.
2. Do not alter any original logic, Boolean equation, rank-comparison rule or Flag-capture rule.
3. Work from a backup and save as a new file (for example `<name>_v5_arranged.json`). Never overwrite the previous file.
4. Use only fields and component types that already exist in the project's JSON schema.
5. If any rule can only be met by changing the original circuit or its logic, stop and explain instead of changing it.

## Process

1. Parse the file. List every board, every component and every wire with its endpoints.
2. Record the full netlist before any change.
3. Move the boards into the target arrangement and remove the unused board.
4. Re-route the wires with the routing method above.
5. Rebuild the netlist and compare it with the original. They must match exactly. Fix any difference before continuing.
6. Run the checks below and report the results.

## Checks to run and report

- Netlist before and after are identical.
- Player A is on the far left, Player B is on the far right, and the four center boards are in the order given.
- The unused small board is removed, or the reason it was kept is reported.
- Every Player A part is on A's board and every Player B part is on B's board. No A and B signal shares a wire or hole.
- No board overlaps another board, and the gaps are even.
- Each board moved as one rigid piece, and no component changed its position relative to its board.
- No diagonal wires remain.
- No two wires share a lane, row or column, and no wire segments overlap.
- No wire endpoint shares a hole with a component pin, and no two endpoints share a hole.
- No wire passes over an IC, LED or other component.
- Original component IDs, labels, colors and wires are unchanged (diff against the backup).
- The JSON is valid and loads in the simulator.
- All earlier behavior tests still pass (existing arbiter results, submission lockout, Display_Enable, round reset, Game_Over).

## Deliverables

1. The rearranged and re-routed JSON file.
2. A table of every board: old position, new position, and whether it was kept or removed.
3. A before/after list of re-routed wires.
4. The check results.
5. A list of any rule that could not be met because of the file format, and any original part that needs my approval before it can be moved.
