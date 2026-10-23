import json, copy, math, sys

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


def pin_ep(part, pin):
    return {"type": "pin", "partId": part, "pin": pin}


def hole_ep(h):
    return {"type": "hole", "board": h["board"], "col": h["col"], "row": h["row"]}


def bus_ep(board, bus, col):
    return {"type": "bus", "board": board, "bus": bus, "col": col}


def epkey(ep):
    return json.dumps(ep, sort_keys=True)


def net_color(pins):
    parts = {(p["part"], p["pin"]) for p in pins}
    pids = {p["part"] for p in pins}
    # Turn and turn indicators.
    if pids & {"c4201", "c4202", "c4105", "c4106"}:
        return YELLOW
    # Flag indicators.
    if pids & {"c4101", "c4102"}:
        return GREEN
    # Final / battle / general LED wiring.
    if pids & {"c1871", "c1872", "c1873", "c4001", "c4002", "c4003", "c4004",
               "c4005", "c4006", "c3001", "c3002", "c3003", "c4103", "c4104"}:
        return ORANGE

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
    return GRAY


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def mst_edges(groups, start_idx=0):
    """Prim MST over group representatives; returns index pairs."""
    n = len(groups)
    if n < 2:
        return []
    in_tree = {start_idx}
    out = []
    while len(in_tree) < n:
        best = None
        for i in sorted(in_tree):
            for j in range(n):
                if j in in_tree:
                    continue
                d = manhattan(groups[i]["coord"], groups[j]["coord"])
                if best is None or d < best[0]:
                    best = (d, i, j)
        d, i, j = best
        out.append((i, j))
        in_tree.add(j)
    return out


def build(layout_path, pinmap_path, nets_path, out_path, nine):
    d = json.load(open(layout_path, encoding="utf-8"))
    pinmap = json.load(open(pinmap_path, encoding="utf-8"))["pins"]
    nets = json.load(open(nets_path, encoding="utf-8"))

    parts = {p["id"]: p for p in d["parts"]}
    wires = []
    seen = set()

    def add(a, b, color):
        if epkey(a) == epkey(b):
            return
        key = tuple(sorted([epkey(a), epkey(b)]))
        if key in seen:
            return
        seen.add(key)
        wires.append({"a": a, "b": b, "color": color, "locked": False, "pivots": []})

    def endpoint_for(pin):
        h = pinmap.get(pin["part"] + ":" + pin["pin"])
        if h:
            return hole_ep(h), (h["x"], h["y"]), (h["board"], h["col"], 0 if h["row"] <= 4 else 1)
        return pin_ep(pin["part"], pin["pin"]), (pin["x"], pin["y"]), ("pin", pin["part"], pin["pin"])

    def offboard_bus_col(pin):
        # Only the eight 10k pull-down lower legs are deliberately off-board.
        if pin["part"] in {"c4", "c5", "c6", "c7", "c8", "c9", "c10", "c11"} and pin["pin"] == "B":
            return 0, int(round((pin["x"] - 168) / 24))
        raise RuntimeError(f"unmapped non-power pin {pin['part']}:{pin['pin']}")

    for net in nets:
        pins = [p for p in net["pins"] if p["part"] in parts]
        if len(pins) < 2:
            continue
        is_gnd = any(p["part"] == "c2132" and p["pin"] == "-" for p in pins)
        is_vcc = any(p["part"] == "c2132" and p["pin"] == "+" for p in pins)

        if is_gnd or is_vcc:
            color = BLACK if is_gnd else RED
            bus = "BN" if is_gnd else "TP"
            for p in pins:
                if p["part"] == "c2132":
                    continue
                h = pinmap.get(p["part"] + ":" + p["pin"])
                if h:
                    board, col = h["board"], h["col"]
                    add(hole_ep(h), bus_ep(board, bus, col), color)
                else:
                    board, col = offboard_bus_col(p)
                    add(pin_ep(p["part"], p["pin"]), bus_ep(board, bus, col), color)
            continue

        # Signal net: collapse pins already joined by a breadboard column half.
        groups = {}
        order = []
        for p in pins:
            ep, coord, nk = endpoint_for(p)
            if nk not in groups:
                groups[nk] = {"endpoint": ep, "coord": coord, "pins": [], "driver": False}
                order.append(nk)
            g = groups[nk]
            g["pins"].append(p)
            if p["type"] in ("OUTPUT", "WEAK"):
                g["driver"] = True
        glist = [groups[k] for k in order]
        if len(glist) < 2:
            continue
        start = next((i for i, g in enumerate(glist) if g["driver"]), 0)
        color = net_color(pins)
        for i, j in mst_edges(glist, start):
            add(glist[i]["endpoint"], glist[j]["endpoint"], color)

    # Tie the breadboard rails together.  These are the same rail links used by
    # the working base, plus board 4 (output strip) and board 3 (turn controls).
    ties = [
        # VCC: top/bottom positive rails of boards 1 and 2, plus board 0.
        (bus_ep(1, "BP", 62), bus_ep(1, "TP", 62), RED),
        (bus_ep(1, "TP", 61), bus_ep(2, "BP", 61), RED),
        (bus_ep(2, "BP", 62), bus_ep(2, "TP", 62), RED),
        (bus_ep(0, "TP", 29), bus_ep(1, "BP", 60), RED),
        # Board 3 carries the regulated supply; tie its positive rails into the
        # main VCC rail.  The battery pins are wired explicitly below.
        (bus_ep(3, "BP", 1), bus_ep(3, "TP", 1), RED),
        (bus_ep(3, "TP", 29), bus_ep(0, "TP", 0), RED),
        # GND: negative rails of all five boards.
        (bus_ep(2, "TN", 62), bus_ep(2, "BN", 62), BLACK),
        (bus_ep(2, "BN", 61), bus_ep(1, "TN", 61), BLACK),
        (bus_ep(1, "TN", 62), bus_ep(1, "BN", 62), BLACK),
        (bus_ep(0, "BN", 29), bus_ep(1, "BN", 60), BLACK),
        (bus_ep(3, "BN", 29), bus_ep(0, "BN", 0), BLACK),
        (bus_ep(4, "BN", 62), bus_ep(2, "TN", 62), BLACK),
    ]
    for a, b, c in ties:
        add(a, b, c)

    # Explicit regulated-supply leads.  The battery sits on board 3's lower
    # rails, so these are short vertical leads rather than a long harness.
    add(pin_ep("c2132", "+"), bus_ep(3, "BP", 1), RED)
    add(pin_ep("c2132", "-"), bus_ep(3, "BN", 1), BLACK)

    d["connections"] = wires
    d["joints"] = []
    d["name"] = "Arbiter-9 (9 LEDs, breadboard)" if nine else "Arbiter-9 (3 LEDs, breadboard)"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    print(out_path, len(d["parts"]), "parts", len(d["connections"]), "connections", len(d["boards"]), "boards")


if __name__ == "__main__":
    base = r"C:\Users\eunic\AppData\Local\Temp\opencode\pwt"
    build("layout9.json", base + r"\pinmap9.json", base + r"\nets7.json",
          "Arbiter-9.json", True)
    build("layout3.json", base + r"\pinmap3.json", base + r"\nets7-3led.json",
          "Arbiter-9-3LED.json", False)
