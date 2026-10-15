"""
render_178.py — Cycles hero plates from build/lafayette_178.blend (block by build_178.py, shop by fitout_178.py).
Headless, so the ~60 s MCP limit does not apply:  /Applications/Blender.app/Contents/MacOS/Blender --background --python build/render_178.py [camera ...]
Plates go to listing/plates/<camera>.jpg. These are the clean geometry plates for Gemini img2img (Vault D1): the words carry the materials.
Exteriors get a real sky (Nishita) and a late-morning sun square on the ESE front; interiors keep the shop's own lights plus daylight through the glass.
"""
import bpy, math, os, sys
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
BLEND = os.path.join(HERE, "lafayette_178.blend"); PLATES = os.path.join(OUT, "listing", "plates"); os.makedirs(PLATES, exist_ok=True)
SHOTS = {   # camera: (interior?, width, height, samples)
    "CAM_178_front":        (False, 1800, 1200, 160),
    "CAM_178_sidewalk":     (False, 1800, 1200, 160),
    "CAM_178_hero_window":  (False, 1800, 1200, 200),
    "CAM_178_in_long":      (True, 1800, 1200, 200),
    "CAM_178_in_gallery":   (True, 1800, 1200, 200),
    "CAM_178_in_shelves":   (True, 1800, 1200, 200),
    "CAM_178_in_to_street": (True, 1800, 1200, 200),
}
def cycles():
    sc = bpy.context.scene
    try: sc.render.engine = 'CYCLES'
    except TypeError as e: print("engine", e)
    prefs = bpy.context.preferences.addons.get('cycles')
    if prefs:
        cp = prefs.preferences
        for dt in ('METAL', 'CUDA', 'OPTIX', 'NONE'):
            try: cp.compute_device_type = dt; break
            except TypeError: continue
        try:
            cp.get_devices()
            for d in cp.devices: d.use = True
        except Exception as e: print("devices", e)
    sc.cycles.device = 'GPU'; sc.cycles.use_denoising = True; sc.cycles.max_bounces = 8; sc.cycles.transparent_max_bounces = 12
    sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 94
    vs = sc.view_settings
    for vt in ('AgX', 'Filmic', 'Standard'):
        try: vs.view_transform = vt; break
        except TypeError: continue
def world(sky):
    sc = bpy.context.scene; w = sc.world; nt = w.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground'); nt.links.new(bg.outputs[0], out.inputs[0])
    if sky:
        tex = nt.nodes.new('ShaderNodeTexSky')
        try: tex.sky_type = 'NISHITA'; tex.sun_elevation = math.radians(42); tex.sun_rotation = math.radians(180 - 125); tex.sun_intensity = 0.6; tex.altitude = 10
        except Exception as e: print("sky", e)
        nt.links.new(tex.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 0.9
    else:
        bg.inputs[0].default_value = (0.62, 0.66, 0.72, 1); bg.inputs[1].default_value = 1.6
def set_sun(interior):
    sun = bpy.data.objects.get("SUN")
    if not sun: return
    sun.data.energy = 3.0 if not interior else 2.2; sun.data.angle = math.radians(1.2)
def glass_for_cycles():
    for name in ("PJ_SHOPGLASS",):
        m = bpy.data.materials.get(name)
        if not m: continue
        b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if b:
            b.inputs["Alpha"].default_value = 0.08; b.inputs["Roughness"].default_value = 0.02; b.inputs["Transmission Weight"].default_value = 0.0 if "Transmission Weight" not in b.inputs else 0.0
            for k in ("Specular IOR Level",):
                if k in b.inputs: b.inputs[k].default_value = 0.3
def interior_view(on):
    for n in ("SITE_178", "SITE_176", "SITE_180"):
        o = bpy.data.objects.get(n)
        if o: o.hide_render = on
def render(cam):
    interior, w, h, samples = SHOTS[cam]; sc = bpy.context.scene
    sc.camera = bpy.data.objects[cam]; sc.render.resolution_x = w; sc.render.resolution_y = h; sc.cycles.samples = samples
    world(sky=True); set_sun(interior); interior_view(interior)
    sc.view_settings.exposure = 0.0 if interior else -0.3
    sc.render.filepath = os.path.join(PLATES, cam + ".jpg"); bpy.ops.render.render(write_still=True); return "plate " + cam
if bpy.app.background:
    bpy.ops.wm.open_mainfile(filepath=BLEND); cycles(); glass_for_cycles()
    cams = [a for a in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else list(SHOTS)
    for c in cams:
        try: print(render(c), flush=True)
        except Exception as e: print("render failed", c, e, flush=True)
    print("PLATES DONE", flush=True)
