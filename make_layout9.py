import json, copy

BASE = "Arbiter-7.json"
BASE3 = "Arbiter-7-3LED.json"

POS = {
    # Inputs and 10k pull-downs.  The switches are moved up one half-board;
    # each pull-down sits directly below its switch column, straddling the
    # centre channel.  Its top leg is on the switch node (same column/top half)
    # and its bottom leg goes to the BN rail, so the whole resistor is on-board.
    "c2": (176, 192), "c3": (752, 192),
    "c4": (168, 302), "c5": (192, 302), "c6": (216, 302), "c7": (240, 302),
    "c9": (744, 302), "c10": (768, 302), "c11": (792, 302), "c8": (816, 302),
    # Logic on boards 1 and 2.
    "c56": (302, -168), "c57": (566, -168), "c118": (902, -168),
    "c351": (1166, -168), "c352": (1382, -168), "c445": (1598, -168),
    "c501": (302, -624), "c502": (518, -624), "c1205": (806, -624),
    "c1206": (998, -624), "c1319": (1190, -624),
    # Turn controls on board 3.
    "c4201": (-568, 240), "c4202": (-448, 240),
    "c4301": (-576, 302), "c4302": (-456, 302),
    # Supply (decorative regulated 5 V source).
    "c2132": (-593, 576),
}

# Output strip on board 4.  LED anodes are at y=-984 (row 5).  The 330R
# resistors are horizontal in the same row, immediately left of each LED:
# their left leg is the logic signal and their right leg feeds the LED anode.
# This keeps both resistor legs in holes and avoids a vertical signal wire
# passing through the resistor body (the old straddle layout).
LED_IDS = ["c1871", "c1872", "c1873", "c4001", "c4002", "c4003", "c4004", "c4005", "c4006"]
RES_IDS = ["c3001", "c3002", "c3003", "c4101", "c4102", "c4103", "c4104", "c4105", "c4106"]
for k, pid in enumerate(LED_IDS):
    POS[pid] = (358.344827586207 + 144 * k, -1091.5862068965517)
for k, pid in enumerate(RES_IDS):
    POS[pid] = (312 + 144 * k, -994)

LABELS = {
    "c2": "A INPUTS", "c3": "B INPUTS",
    "c4201": "TURN A", "c4202": "TURN B",
    "c56": "74HC04 A", "c57": "74HC04 B", "c118": "74HC85",
    "c351": "74HC30 A", "c352": "74HC30 B", "c501": "74HC08 A", "c502": "74HC08 B",
    "c1205": "74HC08 C", "c445": "74HC04 INV", "c1206": "74HC32", "c1319": "74HC08 D",
    "c2132": "5V SUPPLY",
    "c1871": "A_Win", "c1872": "Tie", "c1873": "B_Win",
    "c4001": "Flag_A", "c4002": "Flag_B", "c4003": "A_Win_Final",
    "c4004": "B_Win_Final", "c4005": "Turn_A", "c4006": "Turn_B",
}

BOARD4 = {"index": 4, "cols": 63, "x": 288, "y": -1200, "locked": False,
          "angle": 0, "sizeKey": "full", "rails": True}


def note(nid, text, x, y, w=900, size=12, bold=False, h=40):
    return {"id": nid, "text": text, "x": x, "y": y, "w": w, "h": h,
            "color": "#000000", "fontSize": size, "fontFamily": "Arial",
            "bold": bold, "italic": False, "underline": False}


def build(src, nine, out):
    d = json.load(open(src, encoding="utf-8"))
    d = copy.deepcopy(d)
    for p in d["parts"]:
        if p["id"] in POS:
            p["x"], p["y"] = POS[p["id"]]
        if p["id"] in RES_IDS:
            p["attrs"]["angle"] = 0
        if p["id"] in LABELS:
            p["label"] = LABELS[p["id"]]
    boards = copy.deepcopy(d["boards"])
    if not any(b.get("index") == 4 for b in boards):
        boards.append(copy.deepcopy(BOARD4))
    d["boards"] = boards
    d["connections"] = []
    d["joints"] = []
    d["name"] = "Arbiter-9 (9 LEDs, breadboard)" if nine else "Arbiter-9 (3 LEDs, breadboard)"
    notes = [
        note("note_9000", "GAME OF THE GENERALS - BATTLE ARBITER", -700, -1160, 950, 18, True),
        note("note_9001",
             "ENCODING: Flag=0000, Private=0001, Sergeant=0010, 2LT=0011, 1LT=0100, CPT=0101, "
             "MAJ=0110, LTC=0111, COL=1000, Brig=1001, MajGen=1010, LtGen=1011, 4-Star=1100, "
             "5-Star=1101, Spy=1110. 1111 is unused.",
             -700, -1120, 950, 12, False, 80),
        note("note_9002",
             "TURN: set exactly one of Turn_A / Turn_B HIGH only when both pieces are Flags. "
             "The attacker wins Flag-vs-Flag; both LOW is undefined/no-winner.",
             -700, -1040, 950, 12, False, 60),
        note("note_9003",
             "LOGIC: A_WIN=(A>B)*NOT(Pvt_B*Spy_A)+(Pvt_A*Spy_B)+FlagVsFlag*Turn_A; "
             "B_WIN=(A<B)*NOT(Pvt_A*Spy_B)+(Pvt_B*Spy_A)+FlagVsFlag*Turn_B; "
             "TIE=EQ*NOT FlagVsFlag*NOT(Pvt_A*Spy_B)*NOT(Pvt_B*Spy_A).",
             -700, -960, 950, 12, False, 80),
        note("note_9004",
             "INPUTS: 10k pull-downs. OUTPUT LEDs: 330R series resistors. "
             "POWER: regulated 5V; 74HC logic below 5.5V.",
             -700, 650, 700, 12, False, 60),
        note("note_9006",
             "REAL BUILD: 74HC-series logic at regulated 5.0 V (absolute max 5.5 V). "
             "Wire each DIP-switch common to +5 V; every signal has its own 10k pull-down. "
             "330R in series with every LED (~9 mA). Fit 100nF from +5 V to GND at each IC. "
             "Tie every unused 74HC input to GND or +5 V; never leave it floating. "
             "The app's 7408/7432/7404/7485/7430 symbols represent "
             "74HC08/74HC32/74HC04/74HC85/74HC30 packages.",
             -700, 700, 950, 11, False, 120),
        note("note_9007",
             "WIRING: every component leg is in a breadboard hole. Routed wires avoid "
             "component pins and bodies; crossings pass over empty holes only. Keep the "
             "+5 V and GND rails continuous across boards.",
             -700, 840, 950, 11, False, 60),
    ]
    if nine:
        notes.append(note("note_9005",
             "9-LED OUTPUT STRIP: A_Win / Tie / B_Win / Flag_A / Flag_B / A_Final / B_Final / Turn_A / Turn_B.",
             300, -1270, 1100, 12, False, 40))
    else:
        notes.append(note("note_9005",
             "3-LED DISPLAY: A_Win / Tie / B_Win. Flag and final results are computed internally.",
             300, -1270, 1100, 12, False, 40))
    d["notes"] = notes
    d["textLabels"] = []
    with open(out, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    print(out, len(d["parts"]), "parts", len(d["boards"]), "boards")


build(BASE, True, "layout9.json")
build(BASE3, False, "layout3.json")
