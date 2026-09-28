"""Revised concept B: stackable tiers (front view + side section), mm."""
import textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Polygon, Circle

from sketches import rrect, dim, whisplay_face, eink_face, blank_face, BODY, EDGE, LIME, PCB, CABLE, PLUG

FRAME = "#1d2126"; PORT = "#c9ccd1"; ETH = "#d9b44a"; COOL = "#5a5f66"

W = 196          # outer width (4 slots x 45 + walls)
TIER = 90        # tier height
BASE, CAP = 10, 22
PITCH, X0 = 45, 8

def big_pi_face(ax, x, y, w, h, label, pi5=False):
    rrect(ax, x, y, w, h, BODY, r=2)
    # USB + Ethernet window, ports stacked vertically (board stands on edge)
    wx = x + w / 2 - 10
    rrect(ax, wx, y + 10, 20, 58, "#0e1013", r=2, z=2)
    for k in range(2 if not pi5 else 2):
        ax.add_patch(Rectangle((wx + 3, y + 14 + k * 17), 14, 14, fc=PORT, ec=EDGE, zorder=3))  # USB pairs
    ax.add_patch(Rectangle((wx + 3, y + 49), 14, 16, fc=ETH if not pi5 else ETH, ec=EDGE, zorder=3))  # Ethernet
    ax.text(x + w / 2, y + 4, label, fontsize=6, color=LIME, ha="center", zorder=3)
    ax.add_patch(Circle((x + w / 2, y + h - 6), 1.5, fc="#ff4d4d", ec="none", zorder=3))

fig = plt.figure(figsize=(16, 10), facecolor="white")
fig.suptitle("Concept B, stackable: \"Zero Rax\" tiers (front view and side section; mm)", fontsize=15, weight="bold", y=0.98)

# ---------------- front view
ax = fig.add_axes([0.01, 0.05, 0.5, 0.86]); ax.set_aspect("equal"); ax.axis("off")
y = 0
rrect(ax, 0, y, W, BASE, FRAME, r=2); ax.text(W / 2, y + 3.2, "base with rubber feet", fontsize=6.5, color="#aaa", ha="center")
y += BASE + 1
# Pi tier (bottom, heavier)
rrect(ax, 0, y, W, TIER, FRAME, r=3, lw=1.5)
for i, (lab, pi5) in enumerate([("Pi 3B", False), (None, None), (None, None), (None, None)]):
    fx = X0 + i * PITCH
    if lab:
        big_pi_face(ax, fx, y + 4, PITCH - 4, TIER - 8, "Pi 3B · Homebridge")
    else:
        blank_face(ax, fx, y + 4, PITCH - 4, TIER - 8, "Pi 5 later" if i == 1 else "Future Pi")
ax.text(W + 8, y + TIER / 2, "Pi tier\n4 full-size Pis\n(Pi 3B / 4 / 5)", fontsize=9, va="center")
y += TIER + 1
# Zero tier
rrect(ax, 0, y, W, TIER, FRAME, r=3, lw=1.5)
for i, f in enumerate([whisplay_face, eink_face, blank_face, blank_face]):
    f(ax, X0 + i * PITCH, y + 4, PITCH - 4, TIER - 8)
ax.text(W + 8, y + TIER / 2, "Zero tier\n4 Pi Zeros", fontsize=9, va="center")
y += TIER + 1
# top cap
rrect(ax, 0, y, W, CAP, FRAME, r=3, lw=1.5)
for k in range(12):
    ax.add_patch(Polygon([(12 + k * 14.5 + dx, y + 16 + dy) for dx, dy in ((0, 0), (5, 3), (10, 0), (10, -5), (5, -8), (0, -5))], fc="#0b0c0e", ec="none"))
ax.text(W / 2, y + 3, "ZERO RAX", fontsize=9, color=LIME, weight="bold", ha="center")
for hx in (16, W - 62):
    ax.add_patch(Polygon([(hx, y + CAP), (hx + 14, y + CAP + 18), (hx + 32, y + CAP + 18), (hx + 46, y + CAP)], fc=BODY, ec=EDGE))
top = y + CAP + 18
dim(ax, 0, -8, W, -8, f"{W}")
dim(ax, -12, 0, -12, top, "")
ax.text(-16, top / 2, f"≈{top:.0f}", fontsize=7, color="#666", ha="right", va="center")
ax.annotate("add more tiers any time:\nthey stack on pins and\nbolt together", (W, BASE + TIER), (W + 8, BASE + TIER - 30),
            fontsize=8, color="#555", arrowprops=dict(arrowstyle="->", color="#999"))
ax.set_xlim(-40, W + 75); ax.set_ylim(-25, top + 10)

# ---------------- side section of the Pi tier and Zero tier
ax = fig.add_axes([0.53, 0.47, 0.45, 0.44]); ax.set_aspect("equal"); ax.axis("off")
ax.set_title("side section (front on the left)", fontsize=10, loc="left")
D = 115
# Pi tier section
rrect(ax, 0, 0, D, TIER, "none", ec=EDGE, r=3, lw=1.5)
ax.add_patch(Rectangle((0, 4), 3, TIER - 8, fc=BODY, ec=EDGE))  # face plate
ax.add_patch(Rectangle((5, 12), 85, 56, fc=PCB, ec=EDGE, alpha=0.85))  # Pi 3B, standing on its long edge
ax.text(47, 40, "Pi 3B / Pi 5\n85 × 56 board\nstanding on edge", fontsize=7.5, ha="center", va="center", color="white")
for px in (15, 37, 58):  # power / HDMI on the top long edge
    ax.add_patch(Rectangle((px, 68), 8, 4, fc=PLUG, ec=EDGE))
ax.plot([19, 19, 30, 108, 118], [72, 80, 84, 84, 84], color=CABLE, lw=2)
ax.text(62, 78, "power / HDMI cables run back over the board", fontsize=7, color=CABLE, ha="center")
ax.add_patch(Rectangle((0, 12), 3, 56, fc="#0e1013", ec=EDGE))
ax.text(-3, 40, "USB +\nEthernet", fontsize=7, ha="right", va="center")
ax.text(D - 2, 6, "open back", fontsize=7, ha="right", color="#666")
dim(ax, 0, -6, D, -6, f"depth ≈{D}")
# Zero tier section above
zy = TIER + 8
rrect(ax, 0, zy, D, TIER, "none", ec=EDGE, r=3, lw=1.5)
ax.add_patch(Rectangle((0, zy + 4), 3, TIER - 8, fc=BODY, ec=EDGE))
ax.add_patch(Rectangle((3, zy + 10), 20, 65, fc="#555", ec=EDGE))  # HAT + Pi stack seen from the side
ax.add_patch(Rectangle((23, zy + 10), 1.6, 65, fc=PCB, ec=EDGE))
ax.add_patch(Rectangle((24.6, zy + 40), 6, 8, fc=PLUG, ec=EDGE))
ax.plot([30.6, 60, 118], [zy + 44, zy + 44, zy + 44], color=CABLE, lw=2)
ax.text(70, zy + 50, "micro-USB cables out the back", fontsize=7, color=CABLE, ha="center")
ax.text(12, zy + 42, "Pi Zero\n+ HAT", fontsize=6.5, rotation=90, ha="center", va="center", color="white")
ax.text(75, zy + 22, "spare depth: room for a\nUSB power hub later", fontsize=7, ha="center", color="#666")
ax.set_xlim(-30, D + 10); ax.set_ylim(-15, zy + TIER + 5)

# ---------------- notes
ax = fig.add_axes([0.53, 0.02, 0.45, 0.42]); ax.axis("off")
notes = [
    ("Tiers", "Every tier is 196 × 115 × 90 mm, one print each on the P2S with no supports (printed standing on its "
     "open back). Tiers line up on pins and bolt together with 4 × M3 screws. Base and top cap are separate prints."),
    ("Zero tier", "4 slide-in cassettes at 45 mm pitch. Face plates: Whisplay (1.69\" window, button, LED), 2.13\" e-ink "
     "(Ragnar), plain, blank. Each Pi screws to its cassette; one screw holds each cassette in the frame."),
    ("Pi tier", "4 blades at 45 mm pitch, the full-size Pi standing on edge with USB and Ethernet at the front, like the "
     "blades in your photo. Fits Pi 3B, 4 or 5; enough gap for a Pi 5's active cooler. Power and HDMI plug into the "
     "top edge; the cables run back over the board and out the open back."),
    ("Cooling and power", "Hex vents in the top cap and slotted floors in each tier let air rise through the stack. "
     "Option later: a 40 mm fan mount on the back of the Pi tier."),
]
yy = 0.98
for head, body in notes:
    ax.text(0, yy, head, fontsize=10.5, weight="bold", va="top"); yy -= 0.065
    for line in textwrap.wrap(body, 92):
        ax.text(0, yy, line, fontsize=8.8, va="top"); yy -= 0.054
    yy -= 0.025
fig.savefig("concept_b_stack.png", dpi=110)
print("ok")
