import json
import math
import copy

SRC9 = "Arbiter-7.json"
NETS9 = r"C:\Users\eunic\AppData\Local\Temp\opencode\pwt\nets7.json"
SRC3 = "Arbiter-7-3LED.json"
NETS3 = r"C:\Users\eunic\AppData\Local\Temp\opencode\pwt\nets7-3led.json"

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

LABELS = {
    "c2": "A INPUTS",
    "c3": "B INPUTS",
    "c4201": "TURN A",
    "c4202": "TURN B",
    "c56": "NOT A",
    "c57": "NOT B",
    "c118": "7485 COMPARE",
    "c351": "SPY A",
    "c352": "SPY B",
    "c501": "FLAG A",
    "c502": "FLAG B",
    "c1205": "COMPARE",
    "c445": "INVERT",
    "c1206": "WIN OR",
    "c1319": "FINALS / TIE",
    "c2132": "5V SUPPLY",
    "c1871": "A_Win",
    "c1872": "Tie",
    "c1873": "B_Win",
    "c4001": "Flag_A",
    "c4002": "Flag_B",
    "c4003": "A_Win_Final",
    "c4004": "B_Win_Final",
    "c4005": "Turn_A",
    "c4006": "Turn_B",
}

# Functional schematic layout.  All components are off-board.
POS_COMMON = {
    # Inputs and pull-downs.
    "c2": (0, -700),
    "c3": (0, -450),
    "c4": (-8, -580),
    "c5": (16, -580),
    "c6": (40, -580),
    "c7": (64, -580),
    "c9": (-8, -330),
    "c10": (16, -330),
    "c11": (40, -330),
    "c8": (64, -330),
    "c4201": (0, 0),
    "c4202": (0, 200),
    "c4301": (-8, 80),
    "c4302": (-8, 280),
    # Inverters and magnitude comparator.
    "c56": (500, -700),
    "c57": (500, -450),
    "c118": (800, -575),
    # Logic panel.
    "c351": (1200, -700),
    "c352": (1500, -700),
    "c501": (1200, -450),
    "c502": (1500, -450),
    "c1205": (1200, -200),
    "c445": (1500, -200),
    "c1206": (1200, 50),
    "c1319": (1500, 50),
    # Supply.
    "c2132": (900, 500),
}

POS_9 = {
    # Output grid: battle / flags / finals / turn.
    "c1871": (2000, -700),
    "c4001": (2250, -700),
    "c4003": (2500, -700),
    "c1872": (2000, -450),
    "c4002": (2250, -450),
    "c4004": (2500, -450),
    "c1873": (2000, -200),
    "c4005": (2250, -200),
    "c4006": (2500, -200),
    "c3001": (2002, -820),
    "c4101": (2252, -820),
    "c4103": (2502, -820),
    "c3002": (2002, -570),
    "c4102": (2252, -570),
    "c4104": (2502, -570),
    "c3003": (2002, -320),
    "c4105": (2252, -320),
    "c4106": (2502, -320),
}

POS_3 = {
    "c1871": (2000, -700),
    "c1872": (2000, -450),
    "c1873": (2000, -200),
    "c3001": (2002, -820),
    "c3002": (2002, -570),
    "c3003": (2002, -320),
}


def pin_endpoint(part, pin):
    return {"type": "pin", "partId": part, "pin": pin}


def wire(a, b, color):
    return {"a": pin_endpoint(*a), "b": pin_endpoint(*b), "color": color, "locked": False, "pivots": []}


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def nearest_chain(items, start, coord):
    """Nearest-neighbour path over items, beginning at start."""
    remaining = [p for p in items if (p["part"], p["pin"]) != (start["part"], start["pin"])]
    chain = []
    current = start
    while remaining:
        nxt = min(remaining, key=lambda p: dist(coord(current), coord(p)))
        chain.append((current, nxt))
        remaining.remove(nxt)
        current = nxt
    return chain


def net_color(pins):
    if any(p["part"] == "c2132" and p["pin"] == "+" for p in pins):
        return RED
    if any(p["part"] == "c2132" and p["pin"] == "-" for p in pins):
        return BLACK

    drivers = [p for p in pins if p["type"] in ("OUTPUT", "WEAK")]
    if drivers:
        p = drivers[0]
        part, pin = p["part"], p["pin"]
        if part in ("c2", "c56"):
            return BLUE
        if part in ("c3", "c57"):
            return PURPLE
        if part == "c118":
            return TEAL
        if part in ("c351", "c352"):
            return AMBER
        if part == "c445":
            return GREEN if pin == "2" else AMBER
        if part in ("c501", "c502"):
            return GREEN
        if part == "c1205":
            if pin in ("3", "6"):
                return TEAL
            if pin == "8":
                return GREEN
            if pin == "11":
                return YELLOW
        if part == "c1206":
            return ORANGE
        if part == "c1319":
            if pin in ("3", "11"):
                return ORANGE
            if pin == "6":
                return YELLOW
            if pin == "8":
                return GREEN
        if part in ("c4201", "c4202"):
            return YELLOW

    if any(
        p["part"].startswith("c187")
        or p["part"].startswith("c400")
        or p["part"] in ("c3001", "c3002", "c3003")
        or p["part"].startswith("c41")
        for p in pins
    ):
        return ORANGE
    return GRAY


def gnd_groups(pins):
    keys = {(p["part"], p["pin"]): p for p in pins}
    groups = []
    input_ids = {"c4", "c5", "c6", "c7", "c8", "c9", "c10", "c11"}
    ic_ids = {"c56", "c57", "c118", "c351", "c352", "c445", "c501", "c502", "c1205", "c1206", "c1319"}
    led_ids = {p for p in keys if p[0].startswith("c187") or p[0].startswith("c400")}
    turn_ids = {"c4301", "c4302"}
    leaves = {}
    for (part, pin), p in keys.items():
        if part in input_ids and pin == "B":
            groups.append(p)
        elif part in ic_ids and pin in ("7", "8") and p["type"] == "GROUND":
            groups.append(p)
        elif (part, pin) in led_ids:
            groups.append(p)
        elif part in turn_ids and pin == "B":
            groups.append(p)
        elif part == "c118" and pin in ("2", "4"):
            leaves[(part, pin)] = ("c118", "8")
        elif part == "c2132" and pin == "-":
            pass
        else:
            raise RuntimeError(f"unassigned GND pin {part}:{pin} ({p['type']})")
    return groups, leaves


def vcc_groups(pins):
    keys = {(p["part"], p["pin"]): p for p in pins}
    groups = []
    leaves = {}
    ic_ids = {"c56", "c57", "c118", "c351", "c352", "c445", "c501", "c502", "c1205", "c1206", "c1319"}
    for (part, pin), p in keys.items():
        if part in ic_ids and pin in ("14", "16") and p["type"] == "POWER":
            groups.append(p)
        elif part == "c118" and pin == "3":
            leaves[(part, pin)] = ("c118", "16")
        elif part == "c2132" and pin == "+":
            pass
        else:
            raise RuntimeError(f"unassigned VCC pin {part}:{pin} ({p['type']})")
    return groups, leaves


def build(src, nets_path, nine):
    d = json.load(open(src, encoding="utf-8"))
    d = copy.deepcopy(d)
    nets = json.load(open(nets_path, encoding="utf-8"))
    parts = {p["id"]: p for p in d["parts"]}

    # Pin offsets from the current layout.
    offsets = {}
    for net in nets:
        for p in net["pins"]:
            comp = parts[p["part"]]
            offsets[(p["part"], p["pin"])] = (p["x"] - comp["x"], p["y"] - comp["y"])

    positions = dict(POS_COMMON)
    positions.update(POS_9 if nine else POS_3)
    for pid, comp in parts.items():
        if pid in positions:
            comp["x"], comp["y"] = positions[pid]
        if pid in LABELS:
            comp["label"] = LABELS[pid]

    def coord(p):
        comp = parts[p["part"]]
        ox, oy = offsets[(p["part"], p["pin"])]
        return (comp["x"] + ox, comp["y"] + oy)

    wires = []
    seen = set()

    def add(a, b, color):
        if a == b:
            return
        key = tuple(sorted([a, b]))
        if key in seen:
            return
        seen.add(key)
        wires.append(wire(a, b, color))

    for net in nets:
        pins = [p for p in net["pins"] if p["part"] in parts]
        if len(pins) < 2:
            continue
        color = net_color(pins)
        is_gnd = any(p["part"] == "c2132" and p["pin"] == "-" for p in pins)
        is_vcc = any(p["part"] == "c2132" and p["pin"] == "+" for p in pins)

        if is_gnd or is_vcc:
            root = ("c2132", "-") if is_gnd else ("c2132", "+")
            root_pin = next(p for p in pins if (p["part"], p["pin"]) == root)
            groups, leaves = gnd_groups(pins) if is_gnd else vcc_groups(pins)
            for group in groups:
                start = min(group, key=lambda p: dist(coord(p), coord(root_pin)))
                for a, b in nearest_chain(group, start, coord):
                    add((a["part"], a["pin"]), (b["part"], b["pin"]), color)
                add((start["part"], start["pin"]), root, color)
            for leaf, target in leaves.items():
                add(leaf, target, color)
            continue

        drivers = [p for p in pins if p["type"] in ("OUTPUT", "WEAK")]
        if drivers:
            # Star from the driver to every load.  This keeps signal flow obvious.
            src_pin = drivers[0]
            for p in pins:
                if p is src_pin:
                    continue
                add((src_pin["part"], src_pin["pin"]), (p["part"], p["pin"]), color)
        else:
            # Passive network: shortest nearest-neighbour chain.
            start = pins[0]
            for a, b in nearest_chain(pins, start, coord):
                add((a["part"], a["pin"]), (b["part"], b["pin"]), color)

    # Remove boards and all hole/bus endpoints.
    d["boards"] = []
    d["joints"] = []
    d["connections"] = wires
    d["name"] = "Arbiter-8 (9 LEDs, all off-board)" if nine else "Arbiter-8 (3 LEDs, all off-board)"

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

    notes = [
        note("note_8000", "GAME OF THE GENERALS — BATTLE ARBITER", 0, -1000, 1500, 18, True),
        note(
            "note_8001",
            "ENCODING: Flag=0000, Private=0001, Sergeant=0010, 2LT=0011, 1LT=0100, "
            "CPT=0101, MAJ=0110, LTC=0111, COL=1000, Brig=1001, MajGen=1010, "
            "LtGen=1011, 4-Star=1100, 5-Star=1101, Spy=1110. 1111 is unused.",
            0, -960, 1500, 12,
        ),
        note(
            "note_8002",
            "TURN: set exactly one of Turn_A / Turn_B HIGH only when both pieces are Flags. "
            "The attacker wins Flag-vs-Flag; both LOW is undefined/no-winner.",
            0, -920, 1500, 12,
        ),
        note(
            "note_8003",
            "LOGIC: A_WIN=(A>B)*NOT(Pvt_B*Spy_A)+(Pvt_A*Spy_B)+FlagVsFlag*Turn_A; "
            "B_WIN=(A<B)*NOT(Pvt_A*Spy_B)+(Pvt_B*Spy_A)+FlagVsFlag*Turn_B; "
            "TIE=EQ*NOT FlagVsFlag*NOT(Pvt_A*Spy_B)*NOT(Pvt_B*Spy_A).",
            0, -880, 1600, 12,
        ),
        note(
            "note_8004",
            "A/B INPUTS: 10k pull-downs.  LEDs: 330R series resistors.",
            0, -250, 500, 12,
        ),
        note(
            "note_8005",
            "POWER: regulated 5V only. 74HC logic must stay below 5.5V; "
            "all IC VCC/GND pins are wired.",
            0, 600, 700, 12,
        ),
    ]
    if nine:
        notes.append(
            note(
                "note_8006",
                "OUTPUTS: battle + flags (left two columns), finals + turn (right column).",
                2000, -900, 700, 12,
            )
        )
    else:
        notes.append(
            note(
                "note_8006",
                "3-LED DISPLAY: A_WIN / TIE / B_WIN. FLAG_A, FLAG_B, A_WIN_FINAL and "
                "B_WIN_FINAL are computed internally.",
                2000, -900, 700, 12,
            )
        )
    d["notes"] = notes
    d["textLabels"] = []
    return d


def validate(d, path):
    ids = [p["id"] for p in d["parts"]]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate part ids")
    parts = {p["id"]: p for p in d["parts"]}
    for c in d["connections"]:
        for e in (c["a"], c["b"]):
            if e.get("type") != "pin":
                raise RuntimeError(f"non-pin endpoint: {e}")
            if e["partId"] not in parts:
                raise RuntimeError(f"unknown part: {e}")
    # Check every used pin appears in at most one wire per net?  Not needed.
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    print(f"{path}: {len(d['parts'])} parts, {len(d['connections'])} connections, {len(d['notes'])} notes, {len(d['boards'])} boards")


if __name__ == "__main__":
    validate(build(SRC9, NETS9, True), "Arbiter-8.json")
    validate(build(SRC3, NETS3, False), "Arbiter-8-3LED.json")
