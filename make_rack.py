#!/usr/bin/env python3
"""Zero Rax: a stackable mini rack for Pi Zeros and full-size Pis.

Built in the style of Lab Rax: black chamfered frame, lime accent panels,
a hex-mesh front band with raised lettering, big top handles and a swirl
fan grille.

  base          feet, vented top
  tier (x2)     one part, printed twice: the Pi tier (bottom) and the Zero
                tier (top). 4 slots at 57 mm pitch.
  cap           hex front band with "ZERO RAX", handles on top, 92 mm fan
  modules       Zero cassettes (Whisplay / 2.13" e-ink / plain Zero),
                full-size Pi blades (Pi 3B / 4 / 5), blanks

Every part fits a 256 x 256 mm bed. Run:
  pip install manifold3d trimesh numpy networkx lxml matplotlib
  python3 make_rack.py
"""

import math
import os

import numpy as np
import trimesh
from manifold3d import CrossSection, FillRule, JoinType, Manifold, OpType
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

OUT = os.path.dirname(os.path.abspath(__file__))
SEG = 40

# ------------------------------------------------------------------ sizes (mm)
W, D = 244.0, 118.0          # outer width and depth of every layer
WALL = 6.0                   # tier side walls
FLOOR = 3.0
TIER_H = 96.0
BASE_H, FOOT_H = 16.0, 8.0
CAP_H, CAP_WALL = 36.0, 12.0
BEAM = 8.0                   # front beams the modules screw to
PITCH, FACE_W, FACE_T = 57.0, 55.0, 2.5
SLOT_X0 = WALL + 3.0         # left edge of slot 0
SLOTS = 4

M3_PILOT, M3_CLEAR, M3_HEAD = 2.6, 3.4, 6.6
M25_PILOT, M25_CLEAR, M25_HEAD = 2.2, 2.9, 5.0
DOWEL_D, DOWEL_HOLE = 2.9, 3.3

# Pi Zero (65 x 30) with its HAT, mounted upright behind the face
ZERO_L, ZERO_W = 65.0, 30.0
ZERO_HOLES = [(3.5, 3.5), (26.5, 3.5), (3.5, 61.5), (26.5, 61.5)]  # (x across, z up)
HAT_GAP = 11.0               # header gap between the Pi Zero and the HAT

# Full-size Pi (85 x 56): Pi 3B / 4 / 5, standing on a long edge
BIG_L, BIG_W = 85.0, 56.0
BIG_HOLES = [(23.5, 3.5), (81.5, 3.5), (23.5, 52.5), (81.5, 52.5)]  # (from port end, up)
BIG_STANDOFF = 3.0
BIG_Z0 = 9.0                 # board bottom edge above the tier floor bottom
SLED_T = 2.5

FAN = 92.0                   # fan size in the cap
FAN_HOLE_SPACING = 82.5

# dowel sockets and joint-clip screws
DOWEL_Y = (30.0, 88.0)
CLIP_Y = (22.0, 96.0)
CLIP_W, CLIP_H, CLIP_T, CLIP_OFF = 24.0, 32.0, 4.0, 8.0


# ------------------------------------------------------------------ helpers
def poly(points):
    """Polygon from a list of (x, y) points, in either winding order."""
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]))
    return CrossSection([points if area > 0 else points[::-1]])


def rrect(w, h, r):
    r = max(0.01, min(r, w / 2 - 0.01, h / 2 - 0.01))
    return CrossSection.square((w - 2 * r, h - 2 * r)).translate((r, r)).offset(r, circular_segments=SEG)


def box(x, y, z, w, d, h):
    return Manifold.cube((w, d, h)).translate((x, y, z))


def cyl_z(x, y, z, d, h, d2=None):
    return Manifold.cylinder(h, d / 2, (d2 if d2 is not None else d) / 2, SEG).translate((x, y, z))


def cyl_y(x, y, z, d, h, d2=None):
    """Cylinder along +y starting at y."""
    return Manifold.cylinder(h, d / 2, (d2 if d2 is not None else d) / 2, SEG).rotate((-90, 0, 0)).translate((x, y, z))


def cyl_x(x, y, z, d, h, d2=None):
    """Cylinder along +x starting at x."""
    return Manifold.cylinder(h, d / 2, (d2 if d2 is not None else d) / 2, SEG).rotate((0, 90, 0)).translate((x, y, z))


def prism_xz(cs, y0, depth):
    """Extrude a profile drawn in (x, z) along +y."""
    return Manifold.extrude(cs, depth).rotate((90, 0, 0)).translate((0, y0 + depth, 0))


def prism_yz(cs, x0, width):
    """Extrude a profile drawn in (y, z) along +x."""
    return Manifold.extrude(cs, width).rotate((90, 0, 0)).rotate((0, 0, 90)).translate((x0, 0, 0))


def countersunk_y(x, z, y_front, depth, clear, head):
    """Countersunk hole drilled from the front face (y = y_front) toward +y."""
    return cyl_y(x, y_front - 0.01, z, head, (head - clear) / 2 + 0.01, clear) + cyl_y(x, y_front, z, clear, depth)


def text_cs(s, size, bold=True):
    tp = TextPath((0, 0), s, size=size, prop=FontProperties(family="DejaVu Sans", weight="bold" if bold else "normal"))
    polys = [p.tolist() for p in tp.to_polygons() if len(p) > 2]
    cs = CrossSection(polys, FillRule.EvenOdd)
    (x0, y0), (x1, y1) = cs.bounds()[:2], cs.bounds()[2:]
    return cs.translate((-(x0 + x1) / 2, -(y0 + y1) / 2))


def hexagon(cx, cy, r, rot=0.0):
    return poly([(cx + r * math.cos(math.radians(a + rot)), cy + r * math.sin(math.radians(a + rot)))
                          for a in range(0, 360, 60)])


def hex_window(w, h, point):
    """Elongated hexagon, pointed along w (self-supporting when printed pointing up)."""
    return poly([(0, h / 2), (point, 0), (w - point, 0), (w, h / 2), (w - point, h), (point, h)])


def chamfered_plate(w, h, t, chamfer, r=2.0):
    """Plate in the x-z plane, front face at y = 0, back at y = t, front edges chamfered."""
    back = Manifold.extrude(rrect(w, h, r), t - chamfer).translate((0, 0, chamfer))
    front = Manifold.extrude(rrect(w - 2 * chamfer, h - 2 * chamfer, max(r - chamfer, 0.3)).translate((chamfer, chamfer)), chamfer + 0.01)
    plate = Manifold.batch_hull([back, front])
    # built with thickness along z: turn so thickness runs along +y and the front is at y = 0
    return plate.rotate((-90, 0, 0)).translate((0, 0, h)).mirror((0, 0, 1)).translate((0, 0, h))


def slot_x(i):
    return SLOT_X0 + i * PITCH


# ------------------------------------------------------------------ tier
def side_window():
    return hex_window(84.0, 66.0, 16.0)     # in (y, z)


def tier():
    t = box(0, 0, 0, W, D, FLOOR)
    t += box(0, 0, 0, WALL, D, TIER_H) + box(W - WALL, 0, 0, WALL, D, TIER_H)
    t += box(WALL, 0, 0, W - 2 * WALL, BEAM, BEAM)                    # front bottom beam
    t += box(WALL, 0, TIER_H - BEAM, W - 2 * WALL, BEAM, BEAM)        # front top beam
    t += box(WALL, D - 5, 0, W - 2 * WALL, 5, 6)                      # rear floor lip

    # chamfer the four outer vertical corners
    c = 4.0
    for x, y in ((0, 0), (W, 0), (0, D), (W, D)):
        tri = poly([(x, y), (x + (c if x == 0 else -c), y), (x, y + (c if y == 0 else -c))])
        t -= Manifold.extrude(tri, TIER_H + 2).translate((0, 0, -1))

    # side windows with a lime insert pocket on the inside
    win = side_window().translate((17.0, 15.0))
    pocket = win.offset(3.0, JoinType.Miter)
    for x_out, x_in in ((0, WALL - 2.0), (W - WALL, 0)):
        t -= prism_yz(win, x_out - 1 if x_out == 0 else x_out - 1, WALL + 2)
        if x_out == 0:
            t -= prism_yz(pocket, WALL - 2.0, 2.01)
        else:
            t -= prism_yz(pocket, W - WALL - 0.01, 2.01)

    # floor: grooves for blade sleds, vent slots between them
    for i in range(SLOTS):
        gx = slot_x(i)
        t -= box(gx - 0.25, BEAM, FLOOR - 1.7, SLED_T + 0.5, D - BEAM - 3, 2.2)
        for k in range(6):
            vx = gx + 9 + k * 7.0
            t -= box(vx, 16, -1, 3.0, D - 32, FLOOR + 2)

    # screw pilots in the front beams, one top and one bottom per slot
    for i in range(SLOTS):
        cx = slot_x(i) + FACE_W / 2
        for z in (BEAM / 2, TIER_H - BEAM / 2):
            t -= cyl_y(cx, -0.01, z, M3_PILOT, BEAM - 1)

    # dowel sockets top and bottom, clip screw pilots on the outside of the walls
    for xw in (WALL / 2, W - WALL / 2):
        for y in DOWEL_Y:
            t -= cyl_z(xw, y, -0.01, DOWEL_HOLE, 5)
            t -= cyl_z(xw, y, TIER_H - 5, DOWEL_HOLE, 5.01)
    for y in CLIP_Y:
        for z in (CLIP_OFF, TIER_H - CLIP_OFF):
            t -= cyl_x(-0.01, y, z, M3_PILOT, WALL - 1)
            t -= cyl_x(W - WALL + 1, y, z, M3_PILOT, WALL)
    return t


def side_insert():
    """Lime panel that presses into the pocket behind each side window."""
    shape = side_window().offset(3.0 - 0.2, JoinType.Miter)
    return Manifold.extrude(shape, 1.8)


# ------------------------------------------------------------------ base
def base():
    b = box(0, 0, 0, W, D, BASE_H)
    b -= box(WALL, WALL, -1, W - 2 * WALL, D - 2 * WALL, BASE_H - 3 + 1)    # hollow underneath
    for x, y in ((0, 0), (W - 34, 0), (0, D - 34), (W - 34, D - 34)):        # solid corners for the feet
        b += box(x, y, 0, 34, 34, BASE_H)
    c = 4.0
    for x, y in ((0, 0), (W, 0), (0, D), (W, D)):
        tri = poly([(x, y), (x + (c if x == 0 else -c), y), (x, y + (c if y == 0 else -c))])
        b -= Manifold.extrude(tri, BASE_H + 2).translate((0, 0, -1))
    for i in range(SLOTS):   # vents in the top plate
        for k in range(6):
            b -= box(slot_x(i) + 9 + k * 7.0, 36, BASE_H - 4, 3.0, D - 72, 5)
    # Lab Rax style feet: short cones with a pocket for a rubber pad
    for x, y in ((19, 19), (W - 19, 19), (19, D - 19), (W - 19, D - 19)):
        b += cyl_z(x, y, -FOOT_H, 22, FOOT_H + 0.01, 26)
        b -= cyl_z(x, y, -FOOT_H - 0.01, 10, 1.5)
    for xw in (WALL / 2, W - WALL / 2):
        for y in DOWEL_Y:
            b -= cyl_z(xw, y, BASE_H - 5, DOWEL_HOLE, 5.01)
    for y in CLIP_Y:
        b -= cyl_x(-0.01, y, BASE_H - CLIP_OFF, M3_PILOT, WALL - 1)
        b -= cyl_x(W - WALL + 1, y, BASE_H - CLIP_OFF, M3_PILOT, WALL)
    return b.translate((0, 0, FOOT_H))


# ------------------------------------------------------------------ cap
PANEL_X0, PANEL_Y0 = CAP_WALL - 3, 6 - 3
PANEL_W, PANEL_D, PANEL_T = W - 2 * CAP_WALL + 6, D - 12 + 6, 3.0
COLS = [(CAP_WALL, 6), (W - CAP_WALL - 14, 6), (CAP_WALL, D - 20), (W - CAP_WALL - 14, D - 20)]


def cap():
    c = box(0, 0, 0, W, D, CAP_H)
    c -= box(CAP_WALL, 6, -1, W - 2 * CAP_WALL, D - 12, CAP_H + 2)          # hollow
    c -= box(PANEL_X0, PANEL_Y0, CAP_H - PANEL_T, PANEL_W, PANEL_D, PANEL_T + 1)  # panel rabbet
    for x, y in COLS:                                                       # corner columns for the panel screws
        col = box(x, y, 0, 14, 14, CAP_H - PANEL_T)
        c += col - cyl_z(x + 7, y + 7, CAP_H - PANEL_T - 10, M3_PILOT, 10.01)
    ch = 4.0
    for x, y in ((0, 0), (W, 0), (0, D), (W, D)):
        tri = poly([(x, y), (x + (ch if x == 0 else -ch), y), (x, y + (ch if y == 0 else -ch))])
        c -= Manifold.extrude(tri, CAP_H + 2).translate((0, 0, -1))
    # 45-degree chamfer along the top front edge, like the Lab Rax front beam
    c -= prism_yz(poly([(-1, CAP_H + 1), (-1, CAP_H - 7), (7, CAP_H + 1)]), -1, W + 2)

    # hex-mesh band on the front, with a solid plaque for the name
    name = text_cs("ZERO RAX", 15)
    nb = name.bounds()
    pw = nb[2] - nb[0] + 12
    plaque = rrect(pw, 23, 3).translate((W / 2 - pw / 2, 5.5))
    hexes = []
    r, dx, dz = 4.2, 8.6, 7.45
    row = 0
    z = 6.5
    while z <= CAP_H - 8:
        x = 18.0 + (dx / 2 if row % 2 else 0)
        while x <= W - 18:
            hexes.append(hexagon(x, z, r, 30))
            x += dx
        z += dz
        row += 1
    mesh = CrossSection.batch_boolean(hexes, OpType.Add) - plaque.offset(1.5, JoinType.Round)
    c -= prism_xz(mesh, -1, 8)
    label = Manifold.extrude(name, 1.4)                          # raised letters on the plaque
    label = label.rotate((90, 0, 0)).translate((W / 2, 0, 17))
    c += label
    # handle screw pilots in the side walls, dowel sockets and clip pilots below
    for x in (CAP_WALL / 2 - 1.5, W - CAP_WALL / 2 + 1.5):
        for y in (D / 2 - 42.0, D / 2 + 42.0):
            c -= cyl_z(x, y, CAP_H - 10, M3_PILOT, 10.01)
    for xw in (WALL / 2, W - WALL / 2):
        for y in DOWEL_Y:
            c -= cyl_z(xw, y, -0.01, DOWEL_HOLE, 5)
    for y in CLIP_Y:
        c -= cyl_x(-0.01, y, CLIP_OFF, M3_PILOT, 8)
        c -= cyl_x(W - 8 + 0.01, y, CLIP_OFF, M3_PILOT, 8)
    return c


def swirl_grille(d_open, arms=9):
    """Lab Rax style swirl: curved spokes between a hub and the rim."""
    r_out, r_hub = d_open / 2, 9.0
    opening = CrossSection.circle(r_out, 96)
    solid = [CrossSection.circle(r_hub, 48)]
    for a in range(arms):
        pts_l, pts_r = [], []
        steps = 24
        for s in range(steps + 1):
            rr = r_hub - 1 + (r_out - r_hub + 2) * s / steps
            ang = math.radians(a * 360 / arms) + 1.1 * (rr - r_hub) / (r_out - r_hub)
            w = 1.3
            nx, ny = -math.sin(ang), math.cos(ang)
            px, py = rr * math.cos(ang), rr * math.sin(ang)
            pts_l.append((px + nx * w, py + ny * w))
            pts_r.append((px - nx * w, py - ny * w))
        solid.append(poly(pts_l + pts_r[::-1]))
    return opening - CrossSection.batch_boolean(solid, OpType.Add)


def cap_panel():
    p = Manifold.extrude(rrect(PANEL_W - 0.4, PANEL_D - 0.4, 2), PANEL_T).translate((0.2, 0.2, 0))
    cx, cy = W / 2 - PANEL_X0, D / 2 - PANEL_Y0
    p -= Manifold.extrude(swirl_grille(FAN - 6), PANEL_T + 2).translate((cx, cy, -1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            p -= cyl_z(cx + sx * FAN_HOLE_SPACING / 2, cy + sy * FAN_HOLE_SPACING / 2, -1, 4.3, PANEL_T + 2)
    for x, y in COLS:
        hx, hy = x + 7 - PANEL_X0, y + 7 - PANEL_Y0
        p -= cyl_z(hx, hy, -1, M3_CLEAR, PANEL_T + 2)
        p -= cyl_z(hx, hy, PANEL_T - 1.6, M3_CLEAR, 1.61, M3_HEAD)
    return p


def handle():
    """Lab Rax style handle, runs front to back along a cap side wall."""
    L, H, T = 104.0, 40.0, CAP_WALL
    outer = poly([(0, 0), (L, 0), (L, 8), (L - 18, H), (18, H), (0, 8)])
    inner = poly([(20, -1), (L - 20, -1), (L - 20, 6), (L - 32, H - 12), (32, H - 12), (20, 6)])
    h = prism_yz(outer - inner, 0, T)
    for y in (L / 2 - 42.0, L / 2 + 42.0):   # 84 mm between the screws
        h -= cyl_z(T / 2 - 1.5, y, -1, M3_CLEAR, 12)
        h -= cyl_z(T / 2 - 1.5, y, 5, M3_HEAD, H)
    return h


# ------------------------------------------------------------------ modules
def face_base(label, label_x=None, label_size=6.0):
    """Common face plate: 55 x 96, countersunk screws top and bottom, label text."""
    f = chamfered_plate(FACE_W, TIER_H - 1.0, FACE_T, 0.8).translate((0, 0, 0.5))
    for z in (BEAM / 2, TIER_H - BEAM / 2):
        f -= countersunk_y(FACE_W / 2, z, 0, FACE_T + 1, M3_CLEAR, M3_HEAD)
    if label:
        txt = Manifold.extrude(text_cs(label, label_size), 0.8).rotate((0, 0, 90))
        txt = txt.rotate((90, 0, 0)).translate((label_x if label_x is not None else FACE_W / 2, 0, TIER_H / 2))
        f += txt
    return f


def zero_board_origin():
    """Bottom-left corner of the Pi Zero HAT on the face (x across, z up)."""
    return FACE_W / 2 - ZERO_W / 2, TIER_H / 2 - ZERO_L / 2


def cassette(label):
    """Zero cassette. The HAT's face (screen) sits against the back of the plate
    behind a board-sized window; four M2.5 screws go in from the front, through
    the HAT, an 11 mm spacer and the Pi Zero, into nuts at the back."""
    bx, bz = zero_board_origin()
    f = face_base(label, label_x=bx / 2 + 0.3, label_size=6.0)
    win = rrect(ZERO_W + 1.2, ZERO_L + 1.2, 3).translate((bx - 0.6, bz - 0.6))
    pads = []
    for hx, hz in ZERO_HOLES:
        x, z = bx + hx, bz + hz
        cx = bx - 0.6 if hx < ZERO_W / 2 else bx + ZERO_W + 0.6
        cz = bz - 0.6 if hz < ZERO_L / 2 else bz + ZERO_L + 0.6
        pads.append(CrossSection.circle(2.9, SEG).translate((x, z)))
        pads.append(CrossSection.square((abs(x - cx), abs(z - cz))).translate((min(x, cx), min(z, cz))))
    win = win - CrossSection.batch_boolean(pads, OpType.Add)
    f -= prism_xz(win, -1, FACE_T + 2)
    for hx, hz in ZERO_HOLES:
        f -= countersunk_y(bx + hx, bz + hz, 0, FACE_T + 1, M25_CLEAR, M25_HEAD)
    return f


def blade(label):
    """Full-size Pi blade: face with a USB/Ethernet window, and a sled the Pi
    screws onto, standing on its long edge with the ports facing front."""
    f = face_base(label, label_x=40.0, label_size=7.5)
    port_x0 = SLED_T + BIG_STANDOFF - 1.0
    f -= prism_xz(rrect(21.0, BIG_W + 2, 2).translate((port_x0, BIG_Z0 - 1)), -1, FACE_T + 2)
    sled_len = 100.0
    sled = poly([(BEAM, 1.5), (sled_len, 1.5), (sled_len, 70), (0, 70), (0, BEAM + 0.5), (BEAM, BEAM + 0.5)])
    f += prism_yz(sled, 0, SLED_T).translate((0, FACE_T - 0.01, 0))
    board_front = FACE_T + 3.0
    for hy, hz in BIG_HOLES:
        y, z = board_front + hy, BIG_Z0 + hz
        f += cyl_x(SLED_T - 0.01, y, z, 6.0, BIG_STANDOFF + 0.01)
        f -= cyl_x(-0.01, y, z, M25_PILOT, SLED_T + BIG_STANDOFF + 0.1)
    return f


def blank(label="FUTURE PI"):
    f = face_base(label, label_x=FACE_W / 2, label_size=7.0)
    for k in range(4):
        for side in (-1, 1):
            x = FACE_W / 2 + side * 16 - 2
            f -= box(x, -1, 20 + k * 16, 4, FACE_T + 2, 10)
    return f


def dowel():
    return cyl_z(0, 0, 0, DOWEL_D, 9.5)


def clip():
    """Joint clip: bridges two stacked layers on the outside of the side walls."""
    body = Manifold.batch_hull([
        box(0, 0, 0, CLIP_W, CLIP_H, CLIP_T - 1),
        box(1, 1, 0, CLIP_W - 2, CLIP_H - 2, CLIP_T),
    ])
    for z in (CLIP_H / 2 - CLIP_OFF, CLIP_H / 2 + CLIP_OFF):
        body -= cyl_z(CLIP_W / 2, z, -1, M3_CLEAR, CLIP_T + 2)
        body -= cyl_z(CLIP_W / 2, z, CLIP_T - (M3_HEAD - M3_CLEAR) / 2, M3_CLEAR, (M3_HEAD - M3_CLEAR) / 2 + 0.01, M3_HEAD)
    return body


def zero_spacer():
    return cyl_z(0, 0, 0, 5.0, HAT_GAP) - cyl_z(0, 0, -1, M25_CLEAR, HAT_GAP + 2)


# ------------------------------------------------------------------ output
def to_mesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts), process=True)


def on_bed(m):
    bb = m.bounding_box()
    return m.translate((-bb[0], -bb[1], -bb[2]))


def print_pose(name, m):
    """Rotate each part into its print orientation (no supports needed)."""
    if name == "tier":
        return m.rotate((90, 0, 0))                # front face down
    if name == "base":
        return m.mirror((0, 0, 1))                 # top plate down, feet up
    if name in ("cassette_homebridge", "cassette_ragnar", "blank_future_pi"):
        return m.rotate((-90, 0, 0))               # back down, front (and text) up
    if name.startswith("blade"):
        return m.rotate((0, -90, 0))               # sled side down
    if name == "handle":
        return m.rotate((0, 90, 0))
    return m


PARTS = {
    # name: (builder, count, colour)
    "tier": (tier, 2, "black"),
    "base": (base, 1, "black"),
    "cap": (cap, 1, "black"),
    "handle": (handle, 2, "black"),
    "clip": (clip, 12, "black"),
    "dowel": (dowel, 12, "black"),
    "cassette_homebridge": (lambda: cassette("HOMEBRIDGE"), 1, "black"),
    "cassette_ragnar": (lambda: cassette("RAGNAR"), 1, "black"),
    "blade_pi3b": (lambda: blade("PI 3B"), 1, "black"),
    "blade_pi5": (lambda: blade("PI 5"), 0, "black"),
    "blank_future_pi": (blank, 5, "black"),
    "zero_spacer": (zero_spacer, 8, "black"),
    "cap_panel": (cap_panel, 1, "lime"),
    "side_insert": (side_insert, 4, "lime"),
}


def pack(items, bed=250.0, gap=6.0):
    """Shelf-pack (name, mesh) items onto as few beds as possible."""
    plates, x, y, row_h, cur = [], 0.0, 0.0, 0.0, []
    for name, mesh in sorted(items, key=lambda it: -it[1].extents[1]):
        w, d = mesh.extents[0], mesh.extents[1]
        if x + w > bed:
            x, y, row_h = 0.0, y + row_h + gap, 0.0
        if y + d > bed:
            plates.append(cur)
            cur, x, y, row_h = [], 0.0, 0.0, 0.0
        cur.append((name, mesh, x, y))
        x += w + gap
        row_h = max(row_h, d)
    if cur:
        plates.append(cur)
    return plates


def build():
    os.makedirs(os.path.join(OUT, "stl"), exist_ok=True)
    meshes = {}
    for name, (fn, count, colour) in PARTS.items():
        part = on_bed(print_pose(name, fn()))
        mesh = to_mesh(part)
        assert part.status().name == "NoError" and mesh.is_watertight, (name, part.status())
        mesh.export(os.path.join(OUT, "stl", f"{name}.stl"))
        meshes[name] = mesh
        e = mesh.extents
        print(f"{name:22s} x{count:<3d} {colour:6s} {e[0]:6.1f} x {e[1]:6.1f} x {e[2]:6.1f} mm")
    # 3MF plates, grouped by colour, every part at its print orientation
    for colour in ("black", "lime"):
        items = []
        for name, (_, count, c) in PARTS.items():
            if c == colour:
                items += [(name, meshes[name])] * count
        for n, plate in enumerate(pack(items), 1):
            scene = trimesh.Scene()
            for k, (name, mesh, x, y) in enumerate(plate):
                m = mesh.copy()
                m.apply_translation((x + 3, y + 3, 0))
                scene.add_geometry(m, node_name=f"{name}_{k}", geom_name=f"{name}_{k}")
            path = os.path.join(OUT, f"zero_rax_{colour}_plate{n}.3mf")
            scene.export(path)
            print(f"{os.path.basename(path)}: " + ", ".join(sorted({name for name, *_ in plate})))
    return meshes


if __name__ == "__main__":
    build()
