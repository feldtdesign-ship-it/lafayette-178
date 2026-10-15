"""
fitout_178.py — PJ's shop inside the 178 Lafayette white box (build/lafayette_178.blend, made by build_178.py).
Headless:  /Applications/Blender.app/Contents/MacOS/Blender --background --python build/fitout_178.py
Opens the block file, appends the ready-made assets from mott-167/build/mott_167.blend (21 colourway tees on hangers with his art,
the Galaga cabinet, the Gumbit statue = SuitGuy_Complete), builds the fixtures, adds the hero cameras (all 24 mm), saves the file.
Frame: everything is parented to the B178_IN root (south front corner of 178): x = feet north along the glass, y = feet into the room, z = feet up.
Room: x 1.0 .. 19.17 (18'-2"), y 0 .. 25 (the retail), glass at y = 0, door x 7.35 .. 12.85, ceiling 10.5 ft.
"""
import bpy, bmesh, math, os, glob
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
BLEND = os.path.join(HERE, "lafayette_178.blend")
MOTT = os.path.join(os.path.dirname(OUT), "mott-167", "build", "mott_167.blend")
AVEA = os.path.join(os.path.dirname(OUT), "avea-115-interior")
ART_DIR = os.path.join(AVEA, "artwork"); VINYL_WHITE = os.path.join(AVEA, "vinyl_pj_sig_white.png")
FT = 0.3048
X0, X1, ROOM_D, CEIL = 1.0, 19.17, 25.0, 10.5
WIN_S = (1.2, 7.17); DOOR = (7.17, 13.87); WIN_N = (13.87, 18.97)
COLOURWAYS = [('cream', '#F2DFC0'), ('navy', '#304766'), ('lilac', '#EDD0EF'), ('moss', '#4C605E'), ('peach', '#FEA580'), ('black', '#151515'), ('white', '#F4F2EC')]
TEE_PITCH = 0.35; TEE_HOOK_ABOVE_ORIGIN = 0.022      # feet between hangers; metres from the asset origin up to the hook (measured at Avenue A)
FRAME_W, FRAME_H, FRAME_D, LIP = 16/12, 20/12, 0.07, 0.07; PRINT_W, PRINT_H = 11/12, 14/12
# north wall unit: uprights at these y (feet), planks + a hanging rail in every bay
UPRIGHTS = (3.0, 7.0, 11.0, 15.0, 19.0, 23.0); PLANK_Z = (6.4, 8.0); RAIL_Z = 5.0; RAIL_OFF = 1.1; PLANK_D = 1.0; PIPE_R = 0.07
BAY_COLOURS = ('cream', 'navy', 'lilac', 'moss', 'peach')
STATUE_H = 4.0; STATUE_AT = (16.4, 2.3); PEDESTAL = (2.0, 2.0, 3.0)      # pedestal to sill height (3.3 ft) so the figure fills the window 3-7 ft

def srgb(h, a=1.0):
    h = h.lstrip('#'); r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b), a)
def principled(m): return next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
def mat_flat(name, hexc, rough=0.7, metal=0.0):
    m = bpy.data.materials.get(name)
    if not m: m = bpy.data.materials.new(name); m.use_nodes = True
    p = principled(m); p.inputs['Base Color'].default_value = srgb(hexc); p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    m.diffuse_color = srgb(hexc); return m
def image_mat(name, path, emit=0.0, alpha=False):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); p = nt.nodes.new('ShaderNodeBsdfPrincipled'); tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path, check_existing=True); nt.links.new(tex.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.8
    if alpha:
        nt.links.new(tex.outputs['Alpha'], p.inputs['Alpha'])
        for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND"), ("use_backface_culling", False)):
            try: setattr(m, attr, val)
            except Exception: pass
    if emit: nt.links.new(tex.outputs['Color'], p.inputs['Emission Color']); p.inputs['Emission Strength'].default_value = emit
    nt.links.new(p.outputs[0], out.inputs[0]); return m, tex.image

def root(): return bpy.data.objects["B178_IN"]
def coll(name):
    c = bpy.data.collections.get(name)
    if not c: c = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c)
    return c
def wipe(prefixes):
    for o in [o for o in bpy.data.objects if o.name.startswith(prefixes)]: bpy.data.objects.remove(o, do_unlink=True)
def mesh_obj(name, bm, mat, c, parent=True):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); c.objects.link(o); o.data.materials.append(mat)
    if parent: o.parent = root()
    return o
def box(name, x0, x1, y0, y1, z0, z1, mat, c, parent=True):
    """feet, in the room frame"""
    bm = bmesh.new(); x0, x1, y0, y1, z0, z1 = [v * FT for v in (x0, x1, y0, y1, z0, z1)]
    vs = [bm.verts.new(p) for p in ((x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1))]
    for f in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)): bm.faces.new([vs[i] for i in f])
    return mesh_obj(name, bm, mat, c, parent)
def pipe(name, p0, p1, mat, c, r=PIPE_R):
    bm = bmesh.new(); a = Vector(p0) * FT; b = Vector(p1) * FT; d = b - a
    bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=r * FT, radius2=r * FT, depth=d.length)
    bmesh.ops.transform(bm, matrix=d.to_track_quat('Z', 'Y').to_matrix().to_4x4(), verts=bm.verts); bmesh.ops.translate(bm, vec=(a + b) / 2, verts=bm.verts)
    return mesh_obj(name, bm, mat, c)
def quad(name, pts, uvs, mat, c, parent=None):
    bm = bmesh.new(); v = [bm.verts.new((x * FT, y * FT, z * FT)) for x, y, z in pts]; f = bm.faces.new(v); uv = bm.loops.layers.uv.new()
    for loop, t in zip(f.loops, uvs): loop[uv].uv = t
    o = mesh_obj(name, bm, mat, c)
    if parent: o.parent = parent
    return o

# ---------- assets ----------
ASSET_COLLS = ['Coin-op Arcade Game Cabinet Galaga'] + ['ASSET_tee_%s_%s' % (cw, a) for cw, _ in COLOURWAYS for a in ('01', '02', '03')]
def append_assets():
    need = [n for n in ASSET_COLLS if not bpy.data.collections.get(n)]
    if need or not bpy.data.objects.get('SuitGuy_Complete'):
        with bpy.data.libraries.load(MOTT, link=False) as (src, dst):
            dst.collections = [n for n in need if n in src.collections]
            dst.objects = ['SuitGuy_Complete'] if ('SuitGuy_Complete' in src.objects and not bpy.data.objects.get('SuitGuy_Complete')) else []
    got = 0
    for n in ASSET_COLLS:
        c = bpy.data.collections.get(n)
        if not c: continue
        if c.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(c)
        lc = bpy.context.view_layer.layer_collection.children.get(c.name)
        if lc: lc.exclude = True
        got += 1
    return "assets: %d collections, statue %s" % (got, bool(bpy.data.objects.get('SuitGuy_Complete')))

# ---------- the fit-out ----------
def gallery_wall():
    """his prints on the south wall: seven 16 x 20 black frames in a row, hung at eye height, facing into the room (+x)"""
    wipe(('gal_',)); c = coll('Shop_Art'); black = mat_flat('frame_black', '#111111', 0.5); matb = mat_flat('mat_board', '#e6e1d3', 1.0)
    files = sorted(glob.glob(os.path.join(ART_DIR, 'art_*.jpg')))[:7]; n = len(files); ys = [3.8 + i * 3.0 for i in range(n)]; zc = 5.3; x = X0
    for i, (f, yc) in enumerate(zip(files, ys)):
        w, h = FRAME_W, FRAME_H
        box('gal_fr_t%d' % i, x, x + FRAME_D, yc - w/2, yc + w/2, zc + h/2 - LIP, zc + h/2, black, c); box('gal_fr_b%d' % i, x, x + FRAME_D, yc - w/2, yc + w/2, zc - h/2, zc - h/2 + LIP, black, c)
        box('gal_fr_l%d' % i, x, x + FRAME_D, yc - w/2, yc - w/2 + LIP, zc - h/2, zc + h/2, black, c); box('gal_fr_r%d' % i, x, x + FRAME_D, yc + w/2 - LIP, yc + w/2, zc - h/2, zc + h/2, black, c)
        box('gal_mat%d' % i, x, x + FRAME_D - 0.02, yc - w/2 + LIP, yc + w/2 - LIP, zc - h/2 + LIP, zc + h/2 - LIP, matb, c)
        m, _ = image_mat('print_%d' % i, f); px = x + FRAME_D - 0.012
        quad('gal_print%d' % i, [(px, yc - PRINT_W/2, zc - PRINT_H/2), (px, yc + PRINT_W/2, zc - PRINT_H/2), (px, yc + PRINT_W/2, zc + PRINT_H/2), (px, yc - PRINT_W/2, zc + PRINT_H/2)], ((0, 0), (1, 0), (1, 1), (0, 1)), m, c)
    # a bench under the middle of the row and a low rail of tees is too much for 18 ft: one low plinth with folded stacks instead
    return "%d prints on the south wall" % n
def shelving():
    """pipe-and-plank unit on the north wall: black pipe uprights, two oak planks a bay, a hanging rail in every bay"""
    wipe(('unit_',)); c = coll('Shop_Fixtures'); pipe_m = mat_flat('pipe_black', '#1a1a1a', 0.45, 0.6); oak = mat_flat('plank_oak', '#9a7549', 0.7); x = X1
    for y in UPRIGHTS:
        pipe('unit_up_%.0f' % y, (x - 0.08, y, 0.0), (x - 0.08, y, CEIL - 0.8), pipe_m, c)
        pipe('unit_arm_%.0f' % y, (x - 0.08, y, RAIL_Z), (x - RAIL_OFF, y, RAIL_Z), pipe_m, c)
        for z in PLANK_Z: pipe('unit_brk_%.0f_%.0f' % (y, z * 10), (x - 0.08, y, z - 0.25), (x - PLANK_D, y, z - 0.25), pipe_m, c)
    for a, b in zip(UPRIGHTS, UPRIGHTS[1:]):
        for z in PLANK_Z: box('unit_plank_%.0f_%.0f' % (a, z * 10), x - PLANK_D, x - 0.02, a - 0.3, b + 0.3, z - 0.12, z, oak, c)
        pipe('unit_rail_%.0f' % a, (x - RAIL_OFF, a, RAIL_Z), (x - RAIL_OFF, b, RAIL_Z), pipe_m, c, r=0.045)
    return "unit: %d uprights, %d bays" % (len(UPRIGHTS), len(UPRIGHTS) - 1)
def tees_on_rails():
    wipe(('tee_inst',)); c = coll('Shop_Racks'); n = 0; z = RAIL_Z + 0.045 - TEE_HOOK_ABOVE_ORIGIN / FT
    for k, (a, b) in enumerate(zip(UPRIGHTS, UPRIGHTS[1:])):
        cw = BAY_COLOURS[k % len(BAY_COLOURS)]; y = a + 0.5; i = 0
        while y < b - 0.45:
            ac = bpy.data.collections.get('ASSET_tee_%s_%s' % (cw, ('01', '02', '03')[i % 3]))
            if not ac: return 'tee assets missing'
            e = bpy.data.objects.new('tee_inst_%03d' % n, None); e.instance_type = 'COLLECTION'; e.instance_collection = ac; e.empty_display_size = 0.1
            e.location = ((X1 - RAIL_OFF) * FT, y * FT, z * FT); e.rotation_euler = (0, 0, math.radians(90)); c.objects.link(e); e.parent = root(); n += 1; i += 1; y += TEE_PITCH
    return "%d tees on the rails" % n
def folded_stacks():
    """folded shirts on the planks and the tables, one colourway per stack"""
    wipe(('fold_',)); c = coll('Shop_Stock'); mats = [mat_flat('cw_' + nm, hx, 0.95) for nm, hx in COLOURWAYS]; n = 0; q = 0
    runs = [(X1 - PLANK_D + 0.1, X1 - 0.1, z, a + 0.4, b - 0.4) for a, b in zip(UPRIGHTS, UPRIGHTS[1:]) for z in PLANK_Z]
    for xa, xb, zs, ya, yb in ((7.4, 12.6, 2.6, 8.2, 13.4), (7.4, 12.6, 2.6, 16.2, 19.3), (1.6, 6.8, 3.0, 1.2, 4.9)):   # tables + the south window plinth: a grid of shirt-sized piles
        x = xa + 0.2
        while x + 1.1 <= xb - 0.1: runs.append((x, x + 1.1, zs, ya, yb)); x += 1.45
    for xa, xb, zs, ya, yb in runs:
        y = ya + 0.55; k = 0
        while y < yb - 0.5:
            q += 1
            if q % 5 != 4:
                m = mats[q % len(mats)]; cnt = 4 + q % 3; xs = xa + 0.1 + (k % 2) * 0.0
                for t in range(cnt): box('fold_%d_%d' % (q, t), xs, xb - 0.1, y - 0.5, y + 0.5, zs + t * 0.085, zs + (t + 1) * 0.085 - 0.012, m, c); n += 1
            y += 1.35; k += 1
    return "%d folded shirts" % n
def tables():
    wipe(('tbl_', 'plinth_', 'wrap_')); c = coll('Shop_Fixtures'); blk = mat_flat('plinth_black', '#0e0e0e', 0.6); oak = mat_flat('plank_oak', '#9a7549', 0.7)
    for i, (ya, yb) in enumerate(((8.0, 13.6), (16.0, 19.5))):
        box('tbl_top_%d' % i, 7.2, 12.8, ya, yb, 2.45, 2.6, oak, c)
        for x, y in ((7.5, ya + 0.3), (12.5, ya + 0.3), (7.5, yb - 0.3), (12.5, yb - 0.3)): pipe('tbl_leg_%d_%.0f_%.0f' % (i, x, y), (x, y, 0.0), (x, y, 2.45), mat_flat('pipe_black', '#1a1a1a', 0.45, 0.6), c)
    box('plinth_south_window', 1.5, 6.9, 1.0, 5.2, 0.0, 3.0, blk, c)                                       # to sill height so the display shows in the window                                       # low display plinth in the south window
    box('wrap_body', 14.3, 18.9, 20.6, 22.8, 0.0, 3.1, blk, c); box('wrap_top', 14.1, 19.1, 20.4, 23.0, 3.1, 3.25, oak, c)   # cash wrap by the back door
    return "two tables, window plinth, cash wrap"
def statue():
    """the Gumbit statue (SuitGuy_Complete, appended from the Mott file with its Decimate) in the north window on a black pedestal, facing the street"""
    wipe(('pedestal_',)); o = bpy.data.objects.get('SuitGuy_Complete')
    if not o: return 'statue missing'
    c = coll('Shop_Fitout')
    for cc in list(o.users_collection): cc.objects.unlink(o)
    c.objects.link(o); o.parent = root(); o.matrix_parent_inverse.identity()
    if not o.modifiers.get('thin_for_shop'): d = o.modifiers.new('thin_for_shop', 'DECIMATE'); d.ratio = 0.2
    o.scale = (1, 1, 1); o.rotation_euler = (0, 0, 0)
    zs = [v[2] for v in o.bound_box]; xs = [v[0] for v in o.bound_box]; ys = [v[1] for v in o.bound_box]; h0 = max(zs) - min(zs)
    s = STATUE_H * FT / h0; o.scale = (s, s, s); o.rotation_euler = (0, 0, 0)                         # yaw 0 = facing the street, as at Mott (same y-is-depth frame)
    pw, pd, ph = PEDESTAL; cx, cy = STATUE_AT; top = 0.035 + ph
    o.location = (cx * FT - s * (min(xs) + max(xs)) / 2, cy * FT - s * (min(ys) + max(ys)) / 2, top * FT - s * min(zs))
    box('pedestal_statue', cx - pw/2, cx + pw/2, cy - pd/2, cy + pd/2, 0.035, top, mat_flat('plinth_black', '#0e0e0e', 0.6), c)
    return "statue %.0f ft on a %.1f ft pedestal in the north window" % (STATUE_H, ph)
def galaga():
    wipe(('galaga_inst',)); ac = bpy.data.collections.get('Coin-op Arcade Game Cabinet Galaga')
    if not ac: return 'galaga missing'
    pts = [o.matrix_world @ Vector(b) for o in ac.all_objects if o.type == 'MESH' for b in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    ac.instance_offset = ((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z); depth = max(hi.x - lo.x, hi.y - lo.y) / FT
    e = bpy.data.objects.new('galaga_inst', None); e.instance_type = 'COLLECTION'; e.instance_collection = ac; e.empty_display_size = 0.2
    coll('Shop_Fitout').objects.link(e); e.parent = root(); e.location = ((X0 + 2.4) * FT, (ROOM_D - 2.4) * FT, 0); e.rotation_euler = (0, 0, math.radians(45))   # kitty-corner across the back-south corner, facing the door (Michael)
    return "galaga kitty-corner in the back-south corner, %.1f ft deep" % depth
def window_vinyl():
    """PJ's signature in white on the south window, reading right from the street"""
    wipe(('vinyl_',)); m, img = image_mat('vinyl_white', VINYL_WHITE, emit=0.6, alpha=True); c = coll('Shop_Fitout')
    cx = (WIN_S[0] + WIN_S[1]) / 2; w = 4.0; h = w * img.size[1] / img.size[0]; z = 5.6; y = 0.12
    quad('vinyl_south', [(cx + w/2, y, z - h/2), (cx - w/2, y, z - h/2), (cx - w/2, y, z + h/2), (cx + w/2, y, z + h/2)], ((0, 0), (1, 0), (1, 1), (0, 1)), m, c)
    return "vinyl %.1f ft wide on the south window" % w
def window_lights():
    """two track spots on the statue and two on the south window display, plus the cans brightened for Cycles"""
    wipe(('wspot_',)); c = coll('Shop_Fitout')
    for i, (x, y, tx, ty, tz) in enumerate(((WIN_N[0] + 1.0, 2.8, STATUE_AT[0], STATUE_AT[1], 5.0), (WIN_N[1] - 1.0, 2.8, STATUE_AT[0], STATUE_AT[1], 5.0), (WIN_S[0] + 1.0, 2.8, 4.2, 3.0, 3.2), (WIN_S[1] - 1.0, 2.8, 4.2, 3.0, 3.2))):
        ld = bpy.data.lights.new('wspot', 'SPOT'); ld.energy = 60; ld.spot_size = math.radians(40); ld.shadow_soft_size = 0.08
        lo = bpy.data.objects.new('wspot_%d' % i, ld); c.objects.link(lo); lo.parent = root(); lo.location = (x * FT, y * FT, (CEIL - 0.3) * FT)
        lo.rotation_euler = (Vector((tx, ty, tz)) * FT - Vector(lo.location)).to_track_quat('-Z', 'Y').to_euler()
    for o in bpy.data.objects:
        if o.name.startswith('B178_IN_CAN_'): o.data.energy = 120
    return "4 window spots"

def fitout():
    return [append_assets(), gallery_wall(), shelving(), tees_on_rails(), folded_stacks(), tables(), statue(), galaga(), window_vinyl(), window_lights()]

# ---------- cameras (24 mm) ----------
def _w(x_ft, y_ft, z_m):
    return root().matrix_world @ Vector((x_ft * FT, y_ft * FT, z_m))
def cam(name, loc, target, lens=24):
    c = bpy.data.objects.get(name)
    if not c: c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); bpy.context.scene.collection.objects.link(c)
    c.location = loc; c.data.lens = lens; c.data.clip_end = 3000; c.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return c
def cameras():
    mid = (DOOR[0] + DOOR[1]) / 2
    cam("CAM_178_in_long", _w(mid, 1.3, 1.55), _w(mid, ROOM_D, 1.35))                                  # just inside the door, straight down the room
    cam("CAM_178_in_gallery", _w(X1 - 1.0, 6.0, 1.6), _w(X0 + 2.0, 18.0, 1.4))                          # from the north wall, past the statue, across to the print wall
    cam("CAM_178_in_shelves", _w(X0 + 1.2, 19.5, 1.6), _w(X1, 4.0, 1.5))                                # from beside the Galaga to the shelves and the glass
    cam("CAM_178_in_to_street", _w(X0 + 2.2, 19.0, 1.6), _w(X1 - 3.0, 0.3, 1.5))                       # from beside the Galaga, to the glass
    cam("CAM_178_in_to_back", _w(X1 - 2.0, 1.0, 1.6), _w(X0 + 4.0, ROOM_D, 1.3))
    cam("CAM_178_hero_window", _w(X1 + 1.5, -13.0, 1.45), _w(STATUE_AT[0], STATUE_AT[1], 1.55))   # nearly square to the north window so the figure is not parallaxed behind the pier           # sidewalk, three-quarter onto the statue window
    cam("CAM_178_hero_front", _w(mid - 0.5, -50.0, 1.65), _w(mid - 0.5, 0.0, 3.4))                       # across Lafayette, square on (50 ft back)
    return "cameras: in_long, in_gallery, in_shelves, in_to_street, in_to_back, hero_window, hero_front"

def interior_view(on):
    for n in ("SITE_178", "SITE_176", "SITE_180"):
        o = bpy.data.objects.get(n)
        if o: o.hide_render = on; o.hide_viewport = on
def render(cam_name, filename, engine='BLENDER_EEVEE', samples=64, w=1800, h=1200):
    sc = bpy.context.scene; sc.camera = bpy.data.objects[cam_name]
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    for eng in ((engine, 'BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE') if engine.startswith('BLENDER') else (engine,)):
        if eng in engines:
            try: sc.render.engine = eng; break
            except TypeError: continue
    if sc.render.engine == 'CYCLES': sc.cycles.samples = samples; sc.cycles.use_denoising = True
    sc.render.resolution_x = w; sc.render.resolution_y = h; sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92
    sc.view_settings.exposure = 0.0 if cam_name.startswith("CAM_178_in") else 0.7
    sc.render.filepath = os.path.join(OUT, "frames", filename); bpy.ops.render.render(write_still=True); return "rendered " + filename

if bpy.app.background:
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    for line in fitout(): print(line, flush=True)
    print(cameras(), flush=True)
    bpy.ops.wm.save_mainfile(); print("saved", bpy.data.filepath, flush=True)
    interior_view(True)
    for c in ("CAM_178_in_long", "CAM_178_in_gallery", "CAM_178_in_shelves"):
        try: print(render(c, c + ".jpg"), flush=True)
        except Exception as e: print("render failed", c, e, flush=True)
    interior_view(False)
    try: print(render("CAM_178_hero_window", "CAM_178_hero_window.jpg"), flush=True)
    except Exception as e: print("render failed hero_window", e, flush=True)
    print("FITOUT DONE", flush=True)
