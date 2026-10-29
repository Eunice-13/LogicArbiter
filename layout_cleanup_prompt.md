# Task: Clean Up Layout and Wire Routing of the Upgraded Digital Flag Arbiter JSON

Do not change any logic.

## Problem

The upgraded file works logically, but the layout is a mess:

- Long diagonal wires cross the whole canvas, from the top arbiter boards down to the Player A, Player B and shared-control boards.
- The new breadboards are scattered with no clear order.
- Wire endpoints sit in the same hole as a component pin or leg, so it is unclear what is connected to what.
- Wires overlap and bundle together, so individual signals cannot be traced.

## Target

Match the neatness of the earlier "final" version of the project file:

- Every wire has its own designated hole.
- Nothing is tangled.
- Every signal can be traced by eye from start to end.

Use that file as the style reference for spacing, wire colors, routing and labeling.

## Hard Constraints (do not violate)

1. Do not change any logic or any electrical connection. The netlist after cleanup must be identical to the netlist before cleanup. Only positions and wire paths may change.
2. Do not touch the original arbiter boards, the original nine LEDs, the original comparator, gates, resistors, DIP switches or the Turn button. Keep their component IDs, coordinates, labels, colors and wires exactly as they are.
3. Only the NEW components (74HC173 x2, 74HC74, 74HC14, new buttons, new resistors, capacitors, optional indicator LEDs) and the NEW wires may be moved or re-routed.
4. Work from a backup. Save the result as a new file, for example `<name>_v3_clean.json`. Never overwrite the previous file.
5. Use only fields and component types already present in the project's JSON schema.

## Player A / Player B Separation (mandatory, overrides any layout rule that conflicts)

1. Player A and Player B each get their own separate breadboard. Never put both players' switches on the same board.
2. Player A's board holds ONLY Player A's parts:
   - A's 4-bit rank DIP switch
   - Submit A button
   - A's 74HC173 rank register
   - A_Done flip-flop and its debounce parts
   - optional "A submitted" LED and its resistor
3. Player B's board holds ONLY Player B's parts, in the same left-to-right order as A's board:
   - B's 4-bit rank DIP switch
   - Submit B button
   - B's 74HC173 rank register
   - B_Done flip-flop and its debounce parts
   - optional "B submitted" LED and its resistor
4. Nothing from Player A may sit on Player B's board, and nothing from Player B may sit on Player A's board. This includes switches, buttons, wires, resistors and ICs.
5. The only wires between the two player boards are the shared signals that go to the shared control board, such as A_Done, B_Done, Reset and Game_Over. Player A and Player B signals must never share a wire, a hole or a rail, except 5V and GND.
6. Place the A and B boards side by side as mirror images, with the shared control board between them or directly beneath them. This keeps every cable short and straight.
7. The shared control board holds only the shared logic: Display_Enable, Round_Ready/Round_Done, Game_Over latch, Reset logic, and the display gating. The original arbiter boards and the original nine LEDs stay where they are.
8. Label each board clearly: "PLAYER A", "PLAYER B", "SHARED CONTROL".

### Existing Switches

- First check where the original DIP switches and the Turn button are now and which boards they sit on. Do not move original components.
- If the original A and B DIP switches are already on separate boards, keep them there. Build Player A's and Player B's new parts on those same boards, next to the matching switch.
- If both original DIP switches are on the same board, do not move them. Stop and tell me, and propose a layout that separates them. Wait for my approval.
- Do not copy or duplicate the original DIP switches. Reuse the existing ones.

## Layout Rules

1. Arrange the new boards in a clear grid, close to the arbiter section they connect to, following the Player A / Player B Separation rules above.
2. Put the 4-bit rank DIP, Submit button, 74HC173 and A_Done/B_Done flip-flop in the same left-to-right order on both player boards.
3. Place every new IC with its pin 1 notch in the same orientation. Leave at least 2 empty columns between neighboring ICs so wires can reach each pin.
4. Put the 100 nF bypass capacitor right next to each IC's VCC/GND pins.
5. Put optional indicator LEDs and their resistors next to the board that owns them (A submitted on A's board, B submitted on B's board, Game Over on the shared board). They must not use or overlap the original nine LEDs.

## Wiring Rules

1. No wire endpoint may sit in the same hole as a component pin or leg, whether IC, resistor, LED, capacitor, switch or button. If a wire must join a pin's net, land it in a DIFFERENT hole of the same 5-hole strip as that pin.
2. One wire per hole. Two wire endpoints must never share a hole. If a net needs several connections, use different holes along the strip or the power rails.
3. No long diagonal wires. Route with straight horizontal and vertical segments or short wires between adjacent boards. If the format only supports point-to-point wires, keep each wire as short as possible and place the boards so wires do not cross other signals' paths.
4. Group related wires into parallel, evenly spaced lanes (for example the 4-bit rank bus A_Stored_Rank[3:0] runs as four parallel wires that stay in order). The wires must not cross inside a bus.
5. Reduce wire crossings. Where a crossing cannot be avoided, make it a single perpendicular crossing, never an overlap or a run along another wire.
6. Color code wires consistently and keep the colors the same on all three boards:
   - red for +5V
   - black for GND
   - one color for each rank bus
   - one color for control signals (Submit, Clock/Enable, Reset)
   - one color for status signals (A_Done, B_Done, Display_Enable, Game_Over)
7. Use the power rails for VCC and GND on every board. Do not run a power wire across to another board when the local rail can feed it.
8. Every signal that crosses between boards (A_Stored_Rank, B_Stored_Rank, A_Done, B_Done, Display_Enable, Reset, Game_Over) must enter and leave through one tidy connection area on each board, at the board edge nearest the other board.
9. Add a small text label next to each connection area giving the signal name, and a title label on each board (Player A, Player B, Shared Control).

## Process

1. Parse the file and list every new component and every new wire with its endpoints.
2. Record the connection list (netlist) of the whole project before any change.
3. Reposition the new boards and components, then re-route the new wires according to the rules above.
4. Rebuild the netlist and compare it with the original. They must match exactly. Report any difference and fix it before continuing.
5. Run these checks and report the results:
   - No wire endpoint shares a hole with a component pin.
   - No two wire endpoints share a hole.
   - No new wire passes over an original component or an original wire.
   - Original component IDs, coordinates and wires are unchanged (diff against the backup).
   - The JSON is valid and loads in the simulator format.
   - All earlier tests (existing arbiter behavior, submission lockout, Display_Enable, round reset, Game_Over) still pass.
   - Report which board each component is on, and confirm that every Player A part is on A's board and every Player B part is on B's board.
   - Confirm that no wire connects an A-only signal to a B-only signal, other than through the shared control board.
6. Deliver the cleaned JSON, a before/after list of moved components, the check results, and any rule that could not be met because of the format, with the reason.

If any rule can only be met by changing the original circuit or its logic, stop and explain instead of changing it.
