"""Export the assembled rack (and an exploded version) as coloured GLB files for rendering."""
import sys
import trimesh
from trimesh.visual.material import PBRMaterial
from trimesh.visual import TextureVisuals

import make_rack as mr
from render_rack import assembly


def export(parts, path):
    scene = trimesh.Scene()
    for k, (m, col) in enumerate(parts):
        mesh = mr.to_mesh(m)
        mesh.visual = TextureVisuals(material=PBRMaterial(baseColorFactor=[*col, 1.0], roughnessFactor=0.8, metallicFactor=0.0))
        scene.add_geometry(mesh, node_name=f"p{k}")
    scene.export(path)


if __name__ == "__main__":
    out = sys.argv[1]
    export(assembly(), f"{out}/rack.glb")
    export(assembly(explode=45), f"{out}/rack_exploded.glb")
    print("ok")
