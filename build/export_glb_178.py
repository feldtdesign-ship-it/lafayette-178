"""
export_glb_178.py — the web model for the micro site: block, the three fronts, the white box and PJ's fixtures (no tees, no statue: too heavy) → assets/lafayette_178.glb
Headless:  /Applications/Blender.app/Contents/MacOS/Blender --background --python build/export_glb_178.py
Selects by name only among objects that are in the view layer (the earlier in-build export failed on GROUND for that reason).
"""
import bpy, os
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "lafayette_178.blend"))
for n in ("SITE_178", "SITE_176", "SITE_180"):
    o = bpy.data.objects.get(n)
    if o: o.hide_viewport = False; o.hide_render = False
KEEP = ("SOHO_MASSING", "SITE_178", "SITE_176", "SITE_180", "ROADBED", "SIDEWALK", "MEDIAN", "GROUND", "TREES")
PREFIX = ("ST_", "B178_", "B176_", "B180_", "gal_", "unit_", "tbl_", "wrap_", "plinth_", "pedestal_", "fold_")
vl = bpy.context.view_layer
for o in bpy.data.objects:
    try: o.select_set(False)
    except RuntimeError: pass
n = 0
for o in bpy.data.objects:
    if o.type not in ("MESH", "FONT"): continue
    if o.name in KEEP or o.name.startswith(PREFIX):
        if o.name not in vl.objects: continue
        o.hide_set(False); o.select_set(True); n += 1
vl.objects.active = bpy.data.objects["SOHO_MASSING"]
path = os.path.join(OUT, "assets", "lafayette_178.glb"); os.makedirs(os.path.dirname(path), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6, export_apply=True, export_cameras=False, export_lights=False, export_yup=True)
print("exported", n, "objects ->", path, os.path.getsize(path) // 1024, "KB", flush=True)
