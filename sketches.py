"""Concept sketches for a modular Pi Zero rack (front and top views, mm)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Polygon, Circle

BODY = "#2b2f36"; EDGE = "#15181c"; LIME = "#c8e04a"; SCREEN = "#3a78c9"; EINK = "#e9e7df"
PCB = "#2f8f4e"; BLANK = "#3a3f47"; CABLE = "#1f5fd6"; DIM = "#666"; PLUG = "#111"

def rrect(ax, x, y, w, h, fc, ec=EDGE, r=2, lw=1.2, z=1, **kw):
    ax.add_patch(FancyBboxPatch((x + r, y + r), w - 2 * r, h - 2 * r, boxstyle=f"round,pad={r}",
                                fc=fc, ec=ec, lw=lw, zorder=z, **kw))

def dim(ax, x0, y0, x1, y1, text, off=-5, fs=7):
    ax.annotate("", (x0, y0), (x1, y1), arrowprops=dict(arrowstyle="<->", color=DIM, lw=0.8))
    ax.text((x0 + x1) / 2 + (4 if x0 == x1 else 0), (y0 + y1) / 2 + (0 if x0 == x1 else off), text,
            fontsize=fs, color=DIM, ha="left" if x0 == x1 else "center", va="center")

def whisplay_face(ax, x, y, w, h):
    rrect(ax, x, y, w, h, BODY, r=2)
    rrect(ax, x + w / 2 - 14, y + h - 44, 28, 33, SCREEN, ec="#0d2a4d", r=3, z=2)  # 1.69" LCD
    ax.add_patch(Circle((x + w / 2, y + h - 6), 1.6, fc="#4cff6a", ec="none", zorder=3))  # LED window
    ax.add_patch(Circle((x + w / 2, y + 14), 3.2, fc="#666", ec=EDGE, zorder=3))  # button
    ax.text(x + w / 2, y + 4, "Homebridge", fontsize=5.5, color=LIME, ha="center", zorder=3)

def eink_face(ax, x, y, w, h):
    rrect(ax, x, y, w, h, BODY, r=2)
    rrect(ax, x + w / 2 - 14, y + h / 2 - 25, 28, 50, EINK, ec="#777", r=1, z=2)  # 2.13" e-paper, portrait
    ax.text(x + w / 2, y + h / 2, "RAGNAR", fontsize=5, rotation=90, ha="center", va="center", color="#222", zorder=3)
    ax.text(x + w / 2, y + 4, "Ragnar", fontsize=5.5, color=LIME, ha="center", zorder=3)

def blank_face(ax, x, y, w, h, label="Future Pi"):
    rrect(ax, x, y, w, h, BLANK, r=2)
    for i in range(5):
        ax.add_patch(Rectangle((x + w / 2 - 8, y + h / 2 - 16 + i * 7), 16, 2.2, fc="#22262b", ec="none", zorder=2))
    ax.text(x + w / 2, y + h - 12, label, fontsize=7, color=LIME, rotation=90, ha="center", va="top", zorder=3)

def rack_ears(ax, x, y, w, h, holes=True):
    rrect(ax, x, y, w, h, "#1d2126", r=3, lw=1.5, z=0)
    if holes:
        for hx in (x + 7, x + w - 7):
            for k in range(int(h // 15.875)):
                ax.add_patch(Circle((hx, y + 8 + k * 15.875), 2.2, fc="#9aa0a6", ec=EDGE, zorder=1))

def main():
    fig = plt.figure(figsize=(17, 12.5), facecolor="white")
    fig.suptitle("Pi Zero rack: three concepts (front view above, top view below; mm)", fontsize=15, weight="bold", y=0.985)

    # ---------------------------------------------------------------- A: 10" rack panel, vertical blades
    ax = fig.add_axes([0.02, 0.43, 0.46, 0.5]); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("A. 10\" rack panel, 2U with 5 vertical blades\n(fits a Lab Rax / 10\" rack)", fontsize=11, loc="left")
    W, H = 254, 88.9
    rack_ears(ax, 0, 0, W, H)
    x0, pitch, bw = 20, 43, 40
    faces = [whisplay_face, eink_face, blank_face, blank_face, blank_face]
    for i, f in enumerate(faces):
        f(ax, x0 + i * pitch, 3, bw, H - 6)
    dim(ax, 0, -6, W, -6, "254 (10\" rack width)")
    dim(ax, W + 6, 0, W + 6, H, "2U = 88.9")
    dim(ax, x0, H + 5, x0 + pitch, H + 5, "43 pitch", off=4)
    ax.set_xlim(-10, W + 40); ax.set_ylim(-60, H + 15)
    # top view
    ty = -55
    ax.add_patch(Rectangle((0, ty), W, 4, fc="#1d2126", ec=EDGE))
    for i in range(5):
        bx = x0 + i * pitch
        ax.add_patch(Rectangle((bx, ty + 4), bw, 3, fc=BODY, ec=EDGE))  # face plate
        if i < 2:
            ax.add_patch(Rectangle((bx + 5, ty + 12), 30, 1.6, fc=PCB, ec=EDGE))  # Pi board
            ax.add_patch(Rectangle((bx + 5, ty + 7), 30, 5, fc="#555", ec=EDGE))   # HAT stack
            ax.add_patch(Rectangle((bx + 35, ty + 11), 6, 5, fc=PLUG, ec=EDGE))    # 90-degree plug
            ax.plot([bx + 41, bx + 41, bx + 38], [ty + 13.5, ty + 30, ty + 42], color=CABLE, lw=2)
    ax.text(W / 2, ty - 5, "top view: 90° micro-USB plugs turn backward in the gap beside each Pi", fontsize=7, ha="center", color=DIM)

    # ---------------------------------------------------------------- B: standalone desktop mini rack
    ax = fig.add_axes([0.52, 0.43, 0.46, 0.5]); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("B. Standalone desktop \"Zero Rax\", 4 slide-in cassettes\n(Lab Rax look: handles, hex top vent)", fontsize=11, loc="left")
    FW, FH = 196, 104
    rrect(ax, 0, 0, FW, FH, "#1d2126", r=4, lw=1.5, z=0)
    ax.add_patch(Polygon([(18, FH), (38, FH + 16), (58, FH + 16), (62, FH)], fc=BODY, ec=EDGE))           # handle
    ax.add_patch(Polygon([(FW - 18, FH), (FW - 38, FH + 16), (FW - 58, FH + 16), (FW - 62, FH)], fc=BODY, ec=EDGE))
    for k in range(12):  # hex vent strip
        ax.add_patch(Polygon([(12 + k * 14.5 + dx, FH - 10 + dy) for dx, dy in ((0, 0), (5, 3), (10, 0), (10, -5), (5, -8), (0, -5))], fc="#111", ec="none"))
    ax.text(FW / 2, FH - 22, "ZERO RAX", fontsize=9, color=LIME, weight="bold", ha="center")
    x0, pitch, cw = 10, 45, 41
    for i, f in enumerate([whisplay_face, eink_face, blank_face, blank_face]):
        f(ax, x0 + i * pitch, 6, cw, FH - 34)
    for sx in (4, FW - 7):
        for k in range(4):
            ax.add_patch(Circle((sx + 1.5, 12 + k * 20), 1.8, fc="#9aa0a6", ec=EDGE))
    dim(ax, 0, -6, FW, -6, "≈196")
    dim(ax, FW + 6, 0, FW + 6, FH, "≈104 (+16 handles)")
    ax.set_xlim(-10, FW + 60); ax.set_ylim(-60, FH + 25)
    ty = -55
    ax.add_patch(Rectangle((0, ty), FW, 38, fc="none", ec=EDGE, lw=1.2))
    for i in range(4):
        bx = x0 + i * pitch
        ax.add_patch(Rectangle((bx, ty + 35), cw, 3, fc=BODY, ec=EDGE))
        ax.add_patch(Rectangle((bx + 2, ty + 2), 3, 33, fc="#444", ec=EDGE))  # cassette spine / rail
        if i < 2:
            ax.add_patch(Rectangle((bx + 6, ty + 28), 30, 1.6, fc=PCB, ec=EDGE))
            ax.add_patch(Rectangle((bx + 36, ty + 24), 7, 5, fc=PLUG, ec=EDGE))
            ax.plot([bx + 40, bx + 43, bx + 43], [ty + 24, ty + 14, ty - 2], color=CABLE, lw=2)
    ax.text(FW / 2, ty - 5, "top view: cassettes slide in on rails; cables exit through the open back", fontsize=7, ha="center", color=DIM)

    # ---------------------------------------------------------------- C: stackable cubes
    ax = fig.add_axes([0.02, 0.02, 0.46, 0.38]); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("C. Snap-together pods: one pod per Pi, dovetails on the sides\n(add pods as you add Pis; end caps + blank pods)", fontsize=11, loc="left")
    pw, ph = 48, 92
    xs = [0, pw + 1, 2 * (pw + 1), 3 * (pw + 1)]
    for x, f in zip(xs, [whisplay_face, eink_face, blank_face, None]):
        rrect(ax, x, 0, pw, ph, "#1d2126", r=4, lw=1.5, z=0)
        if f:
            f(ax, x + 4, 4, pw - 8, ph - 8)
        else:
            ax.text(x + pw / 2, ph / 2, "+ add\npod", ha="center", va="center", fontsize=9, color="#999")
            ax.patches[-1].set_linestyle("--")
        for k in range(3):  # dovetail marks
            ax.add_patch(Polygon([(x + pw - 1, 16 + k * 28), (x + pw + 2, 13 + k * 28), (x + pw + 2, 23 + k * 28), (x + pw - 1, 20 + k * 28)], fc=LIME, ec="none"))
    dim(ax, 0, -6, pw, -6, "48 per pod")
    dim(ax, 4 * (pw + 1) + 5, 0, 4 * (pw + 1) + 5, ph, "92")
    ax.set_xlim(-10, 4 * (pw + 1) + 40); ax.set_ylim(-20, ph + 10)

    # ---------------------------------------------------------------- notes
    ax = fig.add_axes([0.52, 0.01, 0.47, 0.40]); ax.axis("off")
    notes = [
        ("A. 10\" rack panel", "Screws into any 10\" rack. 5 slots at 43 mm, each a face plate with the Pi screwed to its back. "
         "Needs 90° micro-USB cables. Best if you'll own or build a 10\" rack; the panel alone is 254 mm wide, "
         "too big for most print beds, so it prints as 2–3 pieces."),
        ("B. Standalone \"Zero Rax\"", "A small self-contained Lab Rax look-alike: frame, handles, hex vent, 4 cassettes that slide in "
         "on rails and lock with one screw. Cables leave out the open back, so straight or 90° plugs both work. "
         "Frame prints in 3 parts; cassettes and blanks print flat. Easy to make a 6-slot version."),
        ("C. Snap-together pods", "One enclosed pod per Pi, joined with printed dovetails. Grows one Pi at a time, "
         "each pod is a small print, and a pod can be pulled out on its own. Less rack-like; cables come out each pod's side or back."),
        ("Common to all", "Pi mounted upright, screen showing through a window sized for the Whisplay (1.69\") or the 2.13\" e-ink; "
         "the button and LED stay reachable. Swappable face plates: Whisplay, 2.13\" e-ink, plain Pi, blank. "
         "Labels on each plate, like the photo. Vents behind every slot."),
    ]
    y = 0.97
    for head, body in notes:
        ax.text(0, y, head, fontsize=10.5, weight="bold", va="top"); y -= 0.062
        import textwrap
        for line in textwrap.wrap(body, 100):
            ax.text(0, y, line, fontsize=8.8, va="top"); y -= 0.05
        y -= 0.025
    fig.savefig("concepts.png", dpi=110)
    print("ok")


if __name__ == "__main__":
    main()
