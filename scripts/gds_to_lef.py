# Generate a Tiny Tapeout LEF from a signed-off GDS using pin labels.
# klayout -b -r gds_to_lef.py -rd gds=... -rd lef=... -rd macro=...
import pya

SIGNAL_INPUTS = {"clk", "ena", "rst_n"}
for i in range(8):
    SIGNAL_INPUTS.add(f"ui_in[{i}]")
    SIGNAL_INPUTS.add(f"uio_in[{i}]")
SIGNAL_OUTPUTS = set()
for i in range(8):
    SIGNAL_OUTPUTS.add(f"uio_oe[{i}]")
    SIGNAL_OUTPUTS.add(f"uio_out[{i}]")
    SIGNAL_OUTPUTS.add(f"uo_out[{i}]")

layout = pya.Layout()
layout.read(gds)
top = layout.top_cell()
dbu = layout.dbu
bbox = top.bbox()
width = bbox.right * dbu
height = bbox.top * dbu

labels = {}
for li in layout.layer_indexes():
    info = layout.get_info(li)
    if info.layer != 71:
        continue
    for shape in top.shapes(li).each():
        if not shape.is_text():
            continue
        t = shape.text
        labels.setdefault(t.string, []).append((t.x * dbu, t.y * dbu))

missing = []
for name in ["VPWR", "VGND", "clk", "ena", "rst_n"]:
    if name not in labels:
        missing.append(name)
for bus in ("ui_in", "uio_in", "uio_oe", "uio_out", "uo_out"):
    for i in range(8):
        pin = f"{bus}[{i}]"
        if pin not in labels:
            missing.append(pin)
if missing:
    raise ValueError(f"{macro} missing GDS pin labels: {missing}")


def pin_block(name, direction, use, ports):
    lines = [
        f"  PIN {name}",
        f"    DIRECTION {direction} ;",
        f"    USE {use} ;",
    ]
    for layer, x1, y1, x2, y2 in ports:
        lines += [
            "    PORT",
            f"      LAYER {layer} ;",
            f"        RECT {x1:.3f} {y1:.3f} {x2:.3f} {y2:.3f} ;",
            "    END",
        ]
    lines.append(f"  END {name}")
    return "\n".join(lines)


pg_y1 = 2.480
pg_y2 = height - 2.480
half_w = 0.800

lines = [
    "VERSION 5.7 ;",
    "  NOWIREEXTENSIONATPIN ON ;",
    '  DIVIDERCHAR "/" ;',
    '  BUSBITCHARS "[]" ;',
    f"MACRO {macro}",
    "  CLASS BLOCK ;",
    f"  FOREIGN {macro} ;",
    "  ORIGIN 0.000 0.000 ;",
    f"  SIZE {width:.3f} BY {height:.3f} ;",
]

for pg_name, use in (("VGND", "GROUND"), ("VPWR", "POWER")):
    ports = []
    for x, _y in sorted(labels[pg_name]):
        ports.append(("met4", x - half_w, pg_y1, x + half_w, pg_y2))
    lines.append(pin_block(pg_name, "INOUT", use, ports))

signal_order = (
    ["clk", "ena", "rst_n"]
    + [f"ui_in[{i}]" for i in range(8)]
    + [f"uio_in[{i}]" for i in range(8)]
    + [f"uio_oe[{i}]" for i in range(8)]
    + [f"uio_out[{i}]" for i in range(8)]
    + [f"uo_out[{i}]" for i in range(8)]
)
for name in signal_order:
    x, y = labels[name][0]
    direction = "INPUT" if name in SIGNAL_INPUTS else "OUTPUT"
    lines.append(
        pin_block(name, direction, "SIGNAL", [("met4", x - 0.150, y - 0.500, x + 0.150, y + 0.500)])
    )

# Keep the top pin row and PDN straps exposed; obstruct the rest.
lines += [
    "  OBS",
    "      LAYER li1 ;",
    f"        RECT 2.760 2.635 {width - 2.760:.3f} {height - 2.635:.3f} ;",
    "      LAYER met1 ;",
    f"        RECT 2.760 1.740 {width - 2.460:.3f} {height - 0.720:.3f} ;",
    "      LAYER met2 ;",
    f"        RECT 4.240 1.710 {width - 3.780:.3f} {height - 0.690:.3f} ;",
    "      LAYER met3 ;",
    f"        RECT 5.125 2.555 {width - 4.665:.3f} {height - 0.855:.3f} ;",
    "      LAYER met4 ;",
    f"        RECT 5.000 2.480 {width - 5.000:.3f} {height - 1.400:.3f} ;",
    "  END",
    f"END {macro}",
    "END LIBRARY",
    "",
]

open(lef, "w").write("\n".join(lines))
print(f"Wrote {lef} SIZE {width:.3f} x {height:.3f}")
