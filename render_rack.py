"""Render the assembled Zero Rax (front view and 3/4 view) to rack_preview.png."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from manifold3d import JoinType

import make_rack as mr

BLACK, LIME, PCB, SCREEN, EINK = (0.06, 0.065, 0.075), (0.62, 0.82, 0.05), (0.15, 0.45, 0.25), (0.2, 0.45, 0.8), (0.9, 0.9, 0.86)


def assembly(explode=0.0):
    parts = []
    z = 0.0
    parts.append((mr.base(), BLACK)); z = mr.FOOT_H + mr.BASE_H + explode
    for tier_i, modules in enumerate([
        [("blade", "PI 3B"), ("blank",), ("blank",), ("blank",)],
        [("cassette", "HOMEBRIDGE"), ("cassette", "RAGNAR"), ("blank",), ("blank",)],
    ]):
        parts.append((mr.tier().translate((0, 0, z)), BLACK))
        for x_side in (mr.WALL - 1.9, mr.W - mr.WALL + 0.1):
            ins = mr.prism_yz(mr.side_window().offset(2.8, JoinType.Miter).translate((17, 15)), x_side, 1.8)
            parts.append((ins.translate((0, 0, z)), LIME))
        for i, mod in enumerate(modules):
            x = mr.slot_x(i)
            if mod[0] == "blade":
                m = mr.blade(mod[1])
                board = mr.box(mr.SLED_T + mr.BIG_STANDOFF, mr.FACE_T + 3, mr.BIG_Z0, 1.4, mr.BIG_L, mr.BIG_W)
                parts.append((board.translate((x, -mr.FACE_T - explode * 0.6, z)), PCB))
            elif mod[0] == "cassette":
                m = mr.cassette(mod[1])
                bx, bz = mr.zero_board_origin()
                screen = SCREEN if mod[1] == "HOMEBRIDGE" else EINK
                parts.append((mr.box(bx + 1, mr.FACE_T - 1.5, bz + 6, mr.ZERO_W - 2, 1.6, 40).translate((x, -mr.FACE_T - explode * 0.6, z)), screen))
                parts.append((mr.box(bx, mr.FACE_T + 0.1, bz, mr.ZERO_W, 14, mr.ZERO_L).translate((x, -mr.FACE_T - explode * 0.6, z)), PCB))
            else:
                m = mr.blank()
            parts.append((m.translate((x, -mr.FACE_T - explode * 0.6, z)), BLACK))
        # joint clips
        for xc in (-mr.CLIP_T, mr.W):
            for y in mr.CLIP_Y:
                c = mr.clip().rotate((0, -90, 0)) if xc < 0 else mr.clip().rotate((0, 90, 0))
                bb = c.bounding_box()
                c = c.translate((xc - bb[0], y - mr.CLIP_W / 2 - bb[1], z - mr.CLIP_H / 2 - bb[2]))
                parts.append((c, BLACK))
        z += mr.TIER_H + explode
    parts.append((mr.cap().translate((0, 0, z)), BLACK))
    parts.append((mr.cap_panel().translate((mr.PANEL_X0, mr.PANEL_Y0, z + mr.CAP_H - mr.PANEL_T + explode * 0.5)), LIME))
    hy = mr.D / 2 - 52
    parts.append((mr.handle().translate((0, hy, z + mr.CAP_H + explode * 0.8)), BLACK))
    parts.append((mr.handle().rotate((0, 0, 180)).translate((mr.W, hy + 104, z + mr.CAP_H + explode * 0.8)), BLACK))
    return parts


def draw(ax, parts, elev, azim, light=(0.35, -0.8, 0.5)):
    light = np.array(light) / np.linalg.norm(light)
    lo, hi = np.full(3, 1e9), np.full(3, -1e9)
    for m, col in parts:
        mesh = mr.to_mesh(m)
        tris = mesh.vertices[mesh.faces]
        lum = np.clip(mesh.face_normals @ light, 0, 1) * 0.65 + 0.3
        ax.add_collection3d(Poly3DCollection(tris, facecolors=[tuple(c * l for c in col) for l in lum], edgecolors="none"))
        lo, hi = np.minimum(lo, mesh.bounds[0]), np.maximum(hi, mesh.bounds[1])
    c, s = (lo + hi) / 2, (hi - lo).max() / 2
    ax.set_xlim(c[0] - s, c[0] + s); ax.set_ylim(c[1] - s, c[1] + s); ax.set_zlim(c[2] - s, c[2] + s)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev, azim); ax.set_axis_off()
    try:
        ax.set_proj_type("ortho")
    except Exception:
        pass


if __name__ == "__main__":
    fig = plt.figure(figsize=(16, 8.5), facecolor="white")
    a1 = fig.add_subplot(1, 2, 1, projection="3d"); draw(a1, assembly(), 12, -62); a1.set_title("Zero Rax, assembled", fontsize=13)
    a2 = fig.add_subplot(1, 2, 2, projection="3d"); draw(a2, assembly(explode=40), 18, -118); a2.set_title("exploded, from the back left", fontsize=13)
    plt.tight_layout(); plt.savefig("rack_preview.png", dpi=85)
    print("ok")
