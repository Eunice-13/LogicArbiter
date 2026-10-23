import copy
import json

BASE = "Arbiter-6.json"

# Logic ICs that are moved off-board and fully point-to-point wired.
LOGIC_ICS = ["c351", "c352", "c445", "c501", "c502", "c1205", "c1206", "c1319"]

# Compact logic panel, arranged by signal flow:
#   row 1: Spy detectors
#   row 2: Flag detectors
#   row 3: comparator branches + inverters
#   row 4: win OR + finals/TIE
POS = {
    "c351": (2050, -100),
    "c352": (2350, -100),
    "c501": (2050, -350),
    "c502": (2350, -350),
    "c1205": (2050, -600),
    "c445": (2350, -600),
    "c1206": (2050, -850),
    "c1319": (2350, -850),
}

# Snake order for a short local VCC/GND distribution chain.
POWER_ORDER = ["c351", "c352", "c502", "c501", "c1205", "c445", "c1319", "c1206"]

LABELS = {
    "c351": "SPY A",
    "c352": "SPY B",
    "c501": "FLAG A",
    "c502": "FLAG B",
    "c1205": "COMPARE",
    "c445": "INVERT",
    "c1206": "WIN OR",
    "c1319": "FINALS / TIE",
    "c118": "7485 COMPARE",
    "c56": "NOT A",
    "c57": "NOT B",
}

# Restrained schematic palette.
RED = "#e53e3e"
BLACK = "#1a1a1a"
BLUE = "#3182ce"
PURPLE = "#805ad5"
TEAL = "#319795"
AMBER = "#dd6b20"
GREEN = "#38a169"
YELLOW = "#d69e2e"
ORANGE = "#ed8936"
GRAY = "#718096"
MUTED = "#4a5568"

# Output panel positions.
ORIG_LED_POS = {
    "c1871": (2750, -100),   # A_Win
    "c1872": (2750, -360),   # Tie
    "c1873": (2750, -620),   # B_Win
}
ORIG_RES_POS = {
    "c3001": (2776, 80),
    "c3002": (2776, -180),
    "c3003": (2776, -440),
}

NEW_LEDS = [
    ("c4001", "Flag_A", "red", "c4101", "c501", "8", 2750, -880),
    ("c4002", "Flag_B", "red", "c4102", "c502", "8", 2750, -1140),
    ("c4003", "A_Win_Final", "green", "c4103", "c1319", "11", 2950, -100),
    ("c4004", "B_Win_Final", "green", "c4104", "c1319", "3", 2950, -360),
    ("c4005", "Turn_A", "yellow", "c4105", "c4201", "S1", 2950, -620),
    ("c4006", "Turn_B", "yellow", "c4106", "c4202", "S1", 2950, -880),
]


def pin(part, name):
    return {"type": "pin", "partId": part, "pin": name}


def bus(board, name, col):
    return {"type": "bus", "board": board, "bus": name, "col": col}


def wire(a, b, color=GRAY):
    return {"a": a, "b": b, "color": color, "locked": False, "pivots": []}


def is_pin(endpoint, part, name=None):
    return (
        endpoint.get("type") == "pin"
        and endpoint.get("partId") == part
        and (name is None or endpoint.get("pin") == name)
    )


def endpoint_pin(e):
    return (e.get("partId"), e.get("pin"))


def wire_color(a, b):
    """Color by the driver/source of the net, not by destination."""
    eps = (a, b)

    # Power rails and local power chains.
    if any(e.get("partId") == "c2132" and e.get("pin") == "+" for e in eps):
        return RED
    if any(e.get("partId") == "c2132" and e.get("pin") == "-" for e in eps):
        return BLACK
    if any(e.get("partId") == "c56" and e.get("pin") == "14" for e in eps):
        return RED
    if any(e.get("partId") == "c56" and e.get("pin") == "7" for e in eps):
        return BLACK
    if any(e.get("partId") in LOGIC_ICS and e.get("pin") == "14" for e in eps):
        return RED
    if any(e.get("partId") in LOGIC_ICS and e.get("pin") == "7" for e in eps):
        return BLACK

    # LED ground chain and pull-down returns.
    if any(e.get("pin") == "cathode" for e in eps):
        return BLACK
    if any(e.get("partId") in ("c4301", "c4302") and e.get("pin") == "B" for e in eps):
        return BLACK

    for e in eps:
        p, pin_name = endpoint_pin(e)
        if p == "c2":
            return BLUE
        if p == "c3":
            return PURPLE
        if p == "c56":
            return BLUE
        if p == "c57":
            return PURPLE
        if p in ("c4201", "c4202"):
            return YELLOW
        if p == "c118":
            return TEAL
        if p in ("c351", "c352"):
            return AMBER
        if p == "c445":
            return GREEN if pin_name == "2" else AMBER
        if p in ("c501", "c502"):
            if pin_name in ("3", "6", "8", "11"):
                return GREEN
        if p == "c1205":
            if pin_name in ("3", "6"):
                return TEAL
            if pin_name == "8":
                return GREEN
            if pin_name == "11":
                return YELLOW
        if p == "c1206":
            return ORANGE
        if p == "c1319":
            if pin_name in ("3", "11"):
                return ORANGE
            if pin_name == "6":
                return YELLOW
            if pin_name == "8":
                return GREEN

    return GRAY


def remove_all_pin_connections(conns, part):
    before = len(conns)
    conns[:] = [
        c
        for c in conns
        if not (is_pin(c["a"], part) or is_pin(c["b"], part))
    ]
    return before - len(conns)


def remove_pin_connections(conns, part, name):
    before = len(conns)
    conns[:] = [
        c
        for c in conns
        if not (is_pin(c["a"], part, name) or is_pin(c["b"], part, name))
    ]
    removed = before - len(conns)
    if removed != 1:
        raise RuntimeError(f"expected 1 connection for {part}:{name}, removed {removed}")
    return removed


def add_parts(d, parts):
    existing = {p["id"] for p in d["parts"]}
    for p in parts:
        if p["id"] in existing:
            raise RuntimeError(f"duplicate part id {p['id']}")
        d["parts"].append(p)


def led(pid, x, y, label, color):
    colors = {
        "red": (220, 50, 50),
        "green": (50, 220, 50),
        "yellow": (220, 200, 50),
    }
    cr, cg, cb = colors[color]
    return {
        "id": pid,
        "kind": "LED_RED",
        "x": x,
        "y": y,
        "label": label,
        "locked": False,
        "attrs": {"angle": 0, "cr": cr, "cg": cg, "cb": cb, "colorName": color},
    }


def resistor(pid, x, y, ohms, angle=90):
    return {
        "id": pid,
        "kind": "Resistor_220",
        "x": x,
        "y": y,
        "label": "",
        "locked": False,
        "attrs": {"angle": angle, "resistance": str(ohms), "isCustom": True},
    }


def dip(pid, x, y, label):
    return {
        "id": pid,
        "kind": "DIPSwitch",
        "x": x,
        "y": y,
        "label": label.replace("_", " ").upper(),
        "locked": False,
        "attrs": {
            "angle": 0,
            "states": [False],
            "bits": 1,
            "switchNames": [label],
            "dipDesignToggle": False,
        },
    }


def note(nid, text, x, y, w=760, size=14, bold=False):
    return {
        "id": nid,
        "text": text,
        "x": x,
        "y": y,
        "w": w,
        "h": 40,
        "color": "#000000",
        "fontSize": size,
        "fontFamily": "Arial",
        "bold": bold,
        "italic": False,
        "underline": False,
    }


def build(with_9_leds):
    d = json.load(open(BASE, encoding="utf-8"))
    d = copy.deepcopy(d)
    d["name"] = "Arbiter-7 (9 LEDs)" if with_9_leds else "Arbiter-7 (3 LEDs)"
    conns = d["connections"]

    # Local breadboard jumpers recede into a neutral harness; power and
    # pin-level signal wires keep their functional colors.
    for c in conns:
        if c["a"].get("type") != "pin" and c["b"].get("type") != "pin":
            if c.get("color") not in (RED, BLACK):
                c["color"] = MUTED

    # ---------------------------------------------------------------
    # Move logic off-board, in a compact signal-flow panel.
    # ---------------------------------------------------------------
    for part in LOGIC_ICS:
        removed = remove_all_pin_connections(conns, part)
        if removed == 0:
            raise RuntimeError(f"no connections removed for {part}")
        comp = next(p for p in d["parts"] if p["id"] == part)
        comp["x"], comp["y"] = POS[part]
        if part in LABELS:
            comp["label"] = LABELS[part]

    for part, label in LABELS.items():
        if part not in LOGIC_ICS:
            comp = next((p for p in d["parts"] if p["id"] == part), None)
            if comp is not None:
                comp["label"] = label

    # ---------------------------------------------------------------
    # Move the original three LEDs/resistors into the output panel.
    # ---------------------------------------------------------------
    for part, (x, y) in {**ORIG_LED_POS, **ORIG_RES_POS}.items():
        comp = next((p for p in d["parts"] if p["id"] == part), None)
        if comp is not None:
            comp["x"], comp["y"] = x, y
    for pid, label in (("c1871", "A_Win"), ("c1872", "Tie"), ("c1873", "B_Win")):
        comp = next((p for p in d["parts"] if p["id"] == pid), None)
        if comp is not None:
            comp["label"] = label

    # The original LED cathodes go to a local ground chain, not long TN wires.
    for pid in ("c1871", "c1872", "c1873"):
        remove_pin_connections(conns, pid, "cathode")

    # The three original series resistors are reconnected to the new outputs.
    for part in ("c3001", "c3002", "c3003"):
        remove_pin_connections(conns, part, "A")

    # ---------------------------------------------------------------
    # Point-to-point logic.
    # ---------------------------------------------------------------
    W = []

    def add(a, b):
        W.append(wire(a, b, wire_color(a, b)))

    # Local VCC/GND chain through the logic panel, then one link to c56.
    for i in range(len(POWER_ORDER) - 1):
        add(pin(POWER_ORDER[i], "14"), pin(POWER_ORDER[i + 1], "14"))
        add(pin(POWER_ORDER[i], "7"), pin(POWER_ORDER[i + 1], "7"))
    add(pin(POWER_ORDER[-1], "14"), pin("c56", "14"))
    add(pin(POWER_ORDER[-1], "7"), pin("c56", "7"))

    # --- c351: NOT(Pvt_A * Spy_B), Spy=1110 -------------------------
    add(pin("c351", "1"), pin("c56", "2"))    # NOT A3
    add(pin("c351", "2"), pin("c56", "4"))    # NOT A2
    add(pin("c351", "3"), pin("c56", "12"))   # NOT A1
    add(pin("c351", "4"), pin("c2", "S4"))    # A0
    add(pin("c351", "5"), pin("c3", "S1"))    # B3
    add(pin("c351", "6"), pin("c3", "S2"))    # B2
    add(pin("c351", "11"), pin("c57", "10"))  # NOT B0
    add(pin("c351", "12"), pin("c3", "S3"))   # B1
    add(pin("c351", "8"), pin("c445", "13"))  # -> inverter
    add(pin("c351", "8"), pin("c1205", "5"))  # -> A_WIN branch
    add(pin("c351", "8"), pin("c501", "13"))  # -> TIE chain

    # --- c352: NOT(Pvt_B * Spy_A), Spy=1110 -------------------------
    add(pin("c352", "1"), pin("c57", "2"))    # NOT B3
    add(pin("c352", "2"), pin("c57", "4"))    # NOT B2
    add(pin("c352", "3"), pin("c57", "12"))   # NOT B1
    add(pin("c352", "4"), pin("c3", "S4"))    # B0
    add(pin("c352", "5"), pin("c2", "S1"))    # A3
    add(pin("c352", "6"), pin("c2", "S2"))    # A2
    add(pin("c352", "11"), pin("c56", "10"))  # NOT A0
    add(pin("c352", "12"), pin("c2", "S3"))   # A1
    add(pin("c352", "8"), pin("c445", "11"))  # -> inverter
    add(pin("c352", "8"), pin("c1205", "2"))  # -> B_WIN branch
    add(pin("c352", "8"), pin("c502", "13"))  # -> TIE chain

    # --- c445: inverters -------------------------------------------
    add(pin("c445", "12"), pin("c1206", "2"))  # PvtKillsSpy_A
    add(pin("c445", "10"), pin("c1206", "5"))  # PvtKillsSpy_B
    add(pin("c445", "1"), pin("c1205", "8"))   # FvF input
    add(pin("c445", "2"), pin("c1319", "10"))  # NOT FvF -> TIE1

    # --- c501: Flag_A detector + TIE2 ------------------------------
    add(pin("c501", "1"), pin("c56", "2"))     # NOT A3
    add(pin("c501", "2"), pin("c56", "4"))     # NOT A2
    add(pin("c501", "4"), pin("c56", "12"))    # NOT A1
    add(pin("c501", "5"), pin("c56", "10"))    # NOT A0
    add(pin("c501", "3"), pin("c501", "10"))   # gate1 out -> gate3 in
    add(pin("c501", "6"), pin("c501", "9"))    # gate2 out -> gate3 in
    add(pin("c501", "8"), pin("c1205", "9"))   # Flag_A -> FvF
    add(pin("c501", "8"), pin("c1319", "2"))   # Flag_A -> B_Final
    add(pin("c501", "12"), pin("c1319", "8"))  # TIE1 -> TIE2
    add(pin("c501", "13"), pin("c351", "8"))   # PvtSpyA_n -> TIE2
    add(pin("c501", "11"), pin("c502", "12"))  # TIE2 -> TIE3

    # --- c502: Flag_B detector + TIE -------------------------------
    add(pin("c502", "1"), pin("c57", "2"))     # NOT B3
    add(pin("c502", "2"), pin("c57", "4"))     # NOT B2
    add(pin("c502", "4"), pin("c57", "12"))    # NOT B1
    add(pin("c502", "5"), pin("c57", "10"))    # NOT B0
    add(pin("c502", "3"), pin("c502", "10"))   # gate1 out -> gate3 in
    add(pin("c502", "6"), pin("c502", "9"))    # gate2 out -> gate3 in
    add(pin("c502", "8"), pin("c1205", "10"))  # Flag_B -> FvF
    add(pin("c502", "8"), pin("c1319", "12"))  # Flag_B -> A_Final
    add(pin("c502", "12"), pin("c501", "11"))  # TIE2 -> TIE3
    add(pin("c502", "13"), pin("c352", "8"))   # PvtSpyB_n -> TIE3
    add(pin("c502", "11"), pin("c3002", "A"))  # TIE LED

    # --- c1205: comparator branches + Flag-vs-Flag -----------------
    add(pin("c1205", "1"), pin("c118", "5"))    # A > B
    add(pin("c1205", "2"), pin("c352", "8"))    # PvtSpyB_n
    add(pin("c1205", "4"), pin("c118", "7"))    # A < B
    add(pin("c1205", "5"), pin("c351", "8"))    # PvtSpyA_n
    add(pin("c1205", "3"), pin("c1206", "1"))   # A_GT branch
    add(pin("c1205", "6"), pin("c1206", "4"))   # A_LT branch
    add(pin("c1205", "9"), pin("c501", "8"))    # Flag_A
    add(pin("c1205", "10"), pin("c502", "8"))   # Flag_B
    add(pin("c1205", "8"), pin("c1205", "12"))  # FvF -> FvF*Turn_A
    add(pin("c1205", "13"), pin("c4201", "S1")) # Turn_A
    add(pin("c1205", "8"), pin("c1319", "4"))   # FvF -> FvF*Turn_B
    add(pin("c1205", "8"), pin("c445", "1"))    # FvF -> inverter
    add(pin("c1205", "11"), pin("c1206", "10")) # FvF*Turn_A -> A_WIN

    # --- c1206: A_WIN / B_WIN --------------------------------------
    add(pin("c1206", "3"), pin("c1206", "9"))   # old A_WIN -> new A_WIN OR
    add(pin("c1206", "6"), pin("c1206", "12"))  # old B_WIN -> new B_WIN OR
    add(pin("c1206", "8"), pin("c3001", "A"))   # A_WIN LED
    add(pin("c1206", "8"), pin("c1319", "13"))  # new A_WIN -> A_Final
    add(pin("c1206", "11"), pin("c3003", "A"))  # B_WIN LED
    add(pin("c1206", "11"), pin("c1319", "1"))  # new B_WIN -> B_Final

    # --- c1319: finals + TIE1 --------------------------------------
    add(pin("c1319", "1"), pin("c1206", "11"))  # new B_WIN
    add(pin("c1319", "2"), pin("c501", "8"))    # Flag_A
    add(pin("c1319", "4"), pin("c1205", "8"))   # FvF
    add(pin("c1319", "5"), pin("c4202", "S1"))  # Turn_B
    add(pin("c1319", "6"), pin("c1206", "13"))  # FvF*Turn_B -> B_WIN
    add(pin("c1319", "9"), pin("c118", "6"))    # EQ
    add(pin("c1319", "10"), pin("c445", "2"))   # NOT FvF
    add(pin("c1319", "8"), pin("c501", "12"))   # TIE1 -> TIE2
    add(pin("c1319", "12"), pin("c502", "8"))   # Flag_B
    add(pin("c1319", "13"), pin("c1206", "8"))  # new A_WIN

    conns.extend(W)

    # ---------------------------------------------------------------
    # Turn inputs: compact control block between logic and outputs.
    # ---------------------------------------------------------------
    add_parts(
        d,
        [
            dip("c4201", 2600, -1000, "Turn_A"),
            dip("c4202", 2600, -1150, "Turn_B"),
            resistor("c4301", 2600, -1080, 10000),
            resistor("c4302", 2600, -1230, 10000),
        ],
    )
    conns.extend(
        [
            wire(pin("c4201", "S1"), pin("c4301", "A"), YELLOW),
            wire(pin("c4301", "B"), pin("c1319", "7"), BLACK),
            wire(pin("c4202", "S1"), pin("c4302", "A"), YELLOW),
            wire(pin("c4302", "B"), pin("c1319", "7"), BLACK),
        ]
    )

    # ---------------------------------------------------------------
    # Optional six extra LEDs, in a tidy output panel.
    # ---------------------------------------------------------------
    if with_9_leds:
        add_parts(
            d,
            [
                led(pid, x, y, label, color)
                for pid, label, color, _r, _src, _sp, x, y in NEW_LEDS
            ],
        )
        add_parts(
            d,
            [
                resistor(rid, x + 26, y + 180, 330)
                for _pid, _label, _color, rid, _src, _sp, x, y in NEW_LEDS
            ],
        )
        for pid, label, color, rid, src, sp, x, y in NEW_LEDS:
            conns.extend(
                [
                    wire(pin(src, sp), pin(rid, "A"), wire_color(pin(src, sp), pin(rid, "A"))),
                    wire(pin(rid, "B"), pin(pid, "anode"), ORANGE),
                ]
            )

    # ---------------------------------------------------------------
    # Local LED ground chain (one ground link back to the logic panel).
    # ---------------------------------------------------------------
    if with_9_leds:
        left_chain = ["c1871", "c1872", "c1873", "c4001", "c4002"]
        right_chain = ["c4003", "c4004", "c4005", "c4006"]
        for chain in (left_chain, right_chain):
            for a, b in zip(chain, chain[1:]):
                conns.append(wire(pin(a, "cathode"), pin(b, "cathode"), BLACK))
        conns.append(wire(pin("c4006", "cathode"), pin("c4001", "cathode"), BLACK))
        conns.append(wire(pin("c4002", "cathode"), pin("c1319", "7"), BLACK))
    else:
        for a, b in zip(["c1871", "c1872", "c1873"], ["c1872", "c1873"]):
            conns.append(wire(pin(a, "cathode"), pin(b, "cathode"), BLACK))
        conns.append(wire(pin("c1873", "cathode"), pin("c1319", "7"), BLACK))

    # ---------------------------------------------------------------
    # Notes: compact legend, no stale labels from the old layout.
    # ---------------------------------------------------------------
    d["notes"] = [n for n in d["notes"] if n["id"] in ("note_1940", "note_3005")]
    d["notes"].extend(
        [
            note(
                "note_4000",
                "GAME OF THE GENERALS — BATTLE ARBITER",
                200, -1055, 1500, 18, True,
            ),
            note(
                "note_4001",
                "ENCODING: Flag=0000, Private=0001, Sergeant=0010, 2LT=0011, 1LT=0100, "
                "CPT=0101, MAJ=0110, LTC=0111, COL=1000, Brig=1001, MajGen=1010, "
                "LtGen=1011, 4-Star=1100, 5-Star=1101, Spy=1110. 1111 is unused.",
                200, -1010, 1500, 12,
            ),
            note(
                "note_4002",
                "TURN: set exactly one of Turn_A / Turn_B HIGH only when both pieces are Flags. "
                "The attacker wins Flag-vs-Flag; both LOW is undefined/no-winner.",
                200, -965, 1500, 12,
            ),
            note(
                "note_4003",
                "LOGIC: A_WIN=(A>B)*NOT(Pvt_B*Spy_A)+(Pvt_A*Spy_B)+FlagVsFlag*Turn_A; "
                "B_WIN=(A<B)*NOT(Pvt_A*Spy_B)+(Pvt_B*Spy_A)+FlagVsFlag*Turn_B; "
                "TIE=EQ*NOT FlagVsFlag*NOT(Pvt_A*Spy_B)*NOT(Pvt_B*Spy_A).",
                200, -920, 1600, 12,
            ),
        ]
    )
    if with_9_leds:
        d["notes"].append(
            note(
                "note_4004",
                "OUTPUTS: battle + flags (left column), finals + turn (right column). "
                "Each LED has a 330R series resistor; cathodes share a local ground.",
                2700, -1190, 620, 12,
            )
        )
    else:
        d["notes"].append(
            note(
                "note_4004",
                "3-LED DISPLAY: A_WIN / TIE / B_WIN. FLAG_A, FLAG_B, A_WIN_FINAL and "
                "B_WIN_FINAL are computed internally.",
                2700, -760, 620, 12,
            )
        )
    for n in d["notes"]:
        if n["id"] == "note_3005":
            n["text"] = (
                "POWER: regulated 5V only. 74HC logic must stay below 5.5V; "
                "all IC VCC/GND pins are wired."
            )

    # Drop duplicate point-to-point wires (same two endpoints).
    def endpoint_key(e):
        if e.get("type") == "pin":
            return ("pin", e.get("partId"), e.get("pin"))
        if e.get("type") == "bus":
            return ("bus", e.get("board"), e.get("bus"), e.get("col"))
        return ("other", json.dumps(e, sort_keys=True))

    seen = set()
    deduped = []
    for c in d["connections"]:
        k = tuple(sorted([endpoint_key(c["a"]), endpoint_key(c["b"])]))
        if k in seen:
            continue
        seen.add(k)
        deduped.append(c)
    d["connections"] = deduped

    return d


def validate(d, path):
    ids = [p["id"] for p in d["parts"]]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate part ids")
    parts = {p["id"]: p for p in d["parts"]}
    for c in d["connections"]:
        for e in (c["a"], c["b"]):
            if e.get("type") == "pin" and e.get("partId") not in parts:
                raise RuntimeError(f"unknown part in connection: {e}")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    print(
        f"{path}: {len(d['parts'])} parts, {len(d['connections'])} connections, "
        f"{len(d['notes'])} notes"
    )


if __name__ == "__main__":
    validate(build(True), "Arbiter-7.json")
    validate(build(False), "Arbiter-7-3LED.json")
