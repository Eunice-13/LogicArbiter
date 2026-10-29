"""Build Arbiter-9-upgraded.json.

The original project (Arbiter-9.json) is copied through unchanged -- every
existing part, board and connection is carried over byte-for-byte.  A new
rank-storage / submission-control section is appended on three extra
breadboards (Player A, Player B, shared control) and wired by explicit
connections.  Parts JSON is produced by gen_parts.js (round-tripped through
the simulator engine so the field set matches the app exactly).
"""
import json

SRC = 'Arbiter-9.json'
DST = 'Arbiter-9-upgraded.json'

BLUE = '#3182ce'
PURPLE = '#805ad5'
GREEN = '#38a169'
ORANGE = '#ed8936'
AMBER = '#dd6b20'
TEAL = '#319795'
YELLOW = '#d69e2e'
RED = '#e53e3e'
BLACK = '#1a1a1a'

orig = json.load(open(SRC, encoding='utf-8'))
new_parts = json.load(open('_newparts.json', encoding='utf-8'))


def P(part, pin):
    return {"type": "pin", "partId": part, "pin": pin}


def H(board, col, row):
    return {"type": "hole", "board": board, "col": col, "row": row}


def B(board, bus, col):
    return {"type": "bus", "board": board, "bus": bus, "col": col}


new_boards = [
    {"index": 5, "cols": 63, "x": -1200, "y": 600, "locked": False, "angle": 0, "sizeKey": "full", "rails": True},
    {"index": 6, "cols": 63, "x": 400, "y": 600, "locked": False, "angle": 0, "sizeKey": "full", "rails": True},
    {"index": 7, "cols": 63, "x": 400, "y": 1300, "locked": False, "angle": 0, "sizeKey": "full", "rails": True},
]

nets = []


def net(color, *eps):
    nets.append((color, list(eps)))


# ---------------- Player A breadboard (board 5) ----------------
net(BLUE, P("bA", "OUT"), P("pA", "A"), P("uA3", "1"))                  # A_Submit
net(BLACK, P("pA", "B"), B(5, "BN", 1))                                 # A_Submit pull-down
net(GREEN, P("uA2", "6"), P("uA3", "2"))                                # /A_Done
net(GREEN, P("uA3", "12"), P("uA1", "9"), P("uA2", "3"))                # Accept_A -> CLK_A
net(BLUE, H(1, 1, 5), P("uA1", "4"))                                    # A3
net(BLUE, H(1, 4, 4), P("uA1", "5"))                                    # A2
net(BLUE, H(1, 2, 4), P("uA1", "12"))                                   # A1
net(BLUE, H(1, 3, 5), P("uA1", "13"))                                   # A0
net(GREEN, P("uA2", "5"), P("uS1", "1"), P("rLA", "A"))                 # A_Done
net(GREEN, P("rLA", "B"), P("LA", "anode"))
net(BLACK, P("LA", "cathode"), B(5, "BN", 1))

# ---------------- Player B breadboard (board 6) ----------------
net(PURPLE, P("bB", "OUT"), P("pB", "A"), P("uB3", "3"))                # B_Submit
net(BLACK, P("pB", "B"), B(6, "BN", 1))
net(GREEN, P("uB2", "6"), P("uB3", "4"))                                # /B_Done
net(GREEN, P("uB3", "6"), P("uB1", "9"), P("uB2", "3"))                 # Accept_B -> CLK_B
net(PURPLE, H(1, 12, 5), P("uB1", "4"))                                 # B3
net(PURPLE, H(1, 15, 4), P("uB1", "5"))                                 # B2
net(PURPLE, H(1, 13, 4), P("uB1", "12"))                                # B1
net(PURPLE, H(1, 14, 5), P("uB1", "13"))                                # B0
net(GREEN, P("uB2", "5"), P("uS1", "2"), P("rLB", "A"))                 # B_Done
net(GREEN, P("rLB", "B"), P("LB", "anode"))
net(BLACK, P("LB", "cathode"), B(6, "BN", 1))

# ---------------- Shared: display enable + gated result LEDs (board 7) ----
net(GREEN, P("uS1", "3"), P("uS1", "5"), P("uS1", "10"), P("uS1", "13"))  # Display_Enable
net(ORANGE, H(4, 1, 5), P("uS1", "4"))                                  # A_Win raw tap
net(ORANGE, H(4, 7, 5), P("uS1", "9"))                                  # Tie raw tap
net(ORANGE, H(4, 13, 5), P("uS1", "12"))                                # B_Win raw tap
net(ORANGE, P("uS1", "6"), P("rLD1", "A"))
net(ORANGE, P("rLD1", "B"), P("LD1", "anode"))
net(BLACK, P("LD1", "cathode"), B(7, "BN", 1))
net(ORANGE, P("uS1", "8"), P("rLD2", "A"))
net(ORANGE, P("rLD2", "B"), P("LD2", "anode"))
net(BLACK, P("LD2", "cathode"), B(7, "BN", 1))
net(ORANGE, P("uS1", "11"), P("rLD3", "A"))
net(ORANGE, P("rLD3", "B"), P("LD3", "anode"))
net(BLACK, P("LD3", "cathode"), B(7, "BN", 1))

# ---------------- Shared: game over ----------------
net(TEAL, H(4, 31, 5), P("uS2", "1"))                                   # A_Win_Final tap
net(TEAL, H(4, 37, 5), P("uS2", "2"))                                   # B_Win_Final tap
net(TEAL, P("uS2", "3"), P("uS3", "3"))                                 # (A_Final OR B_Final)
net(AMBER, P("uS3", "5"), P("uS4", "3"), P("rGO", "A"))                 # Game_Over
net(AMBER, P("rGO", "B"), P("LGO", "anode"))
net(BLACK, P("LGO", "cathode"), B(7, "BN", 1))
net(AMBER, P("uS4", "4"), P("uA3", "13"), P("uB3", "5"))                # /Game_Over

# ---------------- Shared: reset ----------------
net(YELLOW, P("bR", "OUT"), P("pR", "A"), P("uS4", "1"))                # Reset
net(BLACK, P("pR", "B"), B(7, "BN", 1))
net(YELLOW, P("uS4", "2"), P("uA1", "1"), P("uA2", "1"),
    P("uB1", "1"), P("uB2", "1"), P("uS3", "1"))                        # /Reset

# ---------------- Power rails and unused-input ties ----------------
net(RED, P("uA1", "16"), P("uA2", "14"), P("uA3", "14"),
    P("uA2", "2"), P("uA2", "4"), P("uA2", "10"), P("uA2", "13"), B(5, "TP", 1))  # A VCC (+ D=1, held PRE/CLR)
net(BLACK, P("uA1", "8"), P("uA2", "7"), P("uA3", "7"),
    P("uA2", "11"), P("uA2", "12"),
    P("uA3", "3"), P("uA3", "4"), P("uA3", "5"),
    P("uA3", "9"), P("uA3", "10"), P("uA3", "11"), B(5, "BN", 1))      # A GND + ties
net(RED, P("uB1", "16"), P("uB2", "14"), P("uB3", "14"),
    P("uB2", "2"), P("uB2", "4"), P("uB2", "10"), P("uB2", "13"), B(6, "TP", 1))  # B VCC
net(BLACK, P("uB1", "8"), P("uB2", "7"), P("uB3", "7"),
    P("uB2", "11"), P("uB2", "12"),
    P("uB3", "1"), P("uB3", "2"), P("uB3", "13"),
    P("uB3", "9"), P("uB3", "10"), P("uB3", "11"), B(6, "BN", 1))      # B GND + ties
net(RED, P("uS1", "14"), P("uS2", "14"), P("uS3", "14"), P("uS4", "14"),
    P("uS3", "2"), P("uS3", "4"), P("uS3", "10"), P("uS3", "13"), B(7, "TP", 1))  # S VCC
net(BLACK, P("uS1", "7"), P("uS2", "7"), P("uS3", "7"), P("uS4", "7"),
    P("uS2", "4"), P("uS2", "5"), P("uS2", "9"), P("uS2", "10"), P("uS2", "12"), P("uS2", "13"),
    P("uS3", "11"), P("uS3", "12"),
    P("uS4", "5"), P("uS4", "9"), P("uS4", "11"), P("uS4", "13"), B(7, "BN", 1))  # S GND + ties

# ---------------- Tie the three new boards onto the main 5 V / GND rails ----
for b in (5, 6, 7):
    net(RED, B(b, "TP", 1), B(1, "TP", 60))
    net(BLACK, B(b, "TN", 1), B(1, "TN", 60))

# --------------------------------------------------------------------------
# Emit connections (chain endpoints within each net; skip duplicate pairs).
# --------------------------------------------------------------------------
connections = list(orig['connections'])
seen = set()


def key(ep):
    return json.dumps(ep, sort_keys=True)


for color, eps in nets:
    for a, b in zip(eps, eps[1:]):
        k = tuple(sorted([key(a), key(b)]))
        if k in seen:
            continue
        seen.add(k)
        connections.append({"a": a, "b": b, "color": color, "locked": False, "pivots": []})

# --------------------------------------------------------------------------
# Assemble and write.
# --------------------------------------------------------------------------
out = dict(orig)
out['parts'] = orig['parts'] + new_parts
out['boards'] = orig['boards'] + new_boards
out['connections'] = connections
out['name'] = 'Arbiter-9 UPGRADED (ranks stored + submission control)'

new_notes = [
    {"id": "note_9100", "text": "UPGRADED ARBITER - RANK STORAGE + SUBMISSION CONTROL",
     "x": -1300, "y": 520, "w": 1200, "h": 40, "color": "#000000", "fontSize": 18,
     "fontFamily": "Arial", "bold": True, "italic": False, "underline": False},
    {"id": "note_9101", "text": "PLAYER A BREADBOARD: A DIP rank -> A RANK REG (74HC175) on A_Submit; A DONE FF (74HC74) latches A_Done; Accept_A = A_Submit AND /A_Done AND /Game_Over.",
     "x": -1300, "y": 560, "w": 1000, "h": 80, "color": "#000000", "fontSize": 12,
     "fontFamily": "Arial", "bold": False, "italic": False, "underline": False},
    {"id": "note_9102", "text": "PLAYER B BREADBOARD: same as A, fully independent. Accept_B = B_Submit AND /B_Done AND /Game_Over.",
     "x": 400, "y": 560, "w": 900, "h": 80, "color": "#000000", "fontSize": 12,
     "fontFamily": "Arial", "bold": False, "italic": False, "underline": False},
    {"id": "note_9103", "text": "SHARED CONTROL: Display_Enable = A_Done AND B_Done (= Round_Ready). Gated display LEDs = raw A_Win / Tie / B_Win AND Display_Enable.",
     "x": 400, "y": 1260, "w": 1400, "h": 80, "color": "#000000", "fontSize": 12,
     "fontFamily": "Arial", "bold": False, "italic": False, "underline": False},
    {"id": "note_9104", "text": "GAME_OVER = latched(A_Win_Final OR B_Win_Final), cleared only by the RESET button. While HIGH it blocks both Accept terms. RESET also clears A_Done / B_Done for the next round.",
     "x": 400, "y": 1860, "w": 1400, "h": 80, "color": "#000000", "fontSize": 12,
     "fontFamily": "Arial", "bold": False, "italic": False, "underline": False},
    {"id": "note_9105", "text": "74HC173 is not a supported symbol in LogicBench, so the 4-bit rank store uses 74HC175 (quad D-FF); the 74HC74 / 74HC14 / 74HC08 / 74HC11 / 74HC32 gates are the simulator's existing symbols. Use 74HC parts in the real build.",
     "x": 400, "y": 1940, "w": 1400, "h": 80, "color": "#000000", "fontSize": 12,
     "fontFamily": "Arial", "bold": False, "italic": False, "underline": False},
]
out['notes'] = orig['notes'] + new_notes

with open(DST, 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print('wrote', DST)
print('parts', len(out['parts']), 'boards', len(out['boards']),
      'connections', len(out['connections']), 'notes', len(out['notes']))
print('original parts preserved:', out['parts'][:len(orig['parts'])] == orig['parts'])
print('original connections preserved:',
      out['connections'][:len(orig['connections'])] == orig['connections'])
