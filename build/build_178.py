"""
build_178.py
Block model for 178 Lafayette Street (Corcoran, 705 sf whitebox) from the NYC Open Data layers in data/ (pulled by build/pull.py).
Same build as west-27th-527/build/build_527.py, re-pointed; stage_sites() + stage_building() draw 178 and its two neighbours; stage_interior() the leased space.
Headless (never his open Blender):  /Applications/Blender.app/Contents/MacOS/Blender --background --python build/build_178.py
Facade + room from the Corcoran flyer (listing/): plan 18-2 x 25-0 retail, bath + stair behind, cellar 13-11 x 41-4; storefront counted off the interior photo (window, door pair, window, two small transoms). Both flyer exteriors are virtually staged.
"""
import bpy, bmesh, json, math, os
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

OUT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if '__file__' in globals() else "/Users/michaelweinfeld/Documents/2026/PJ O'Rourke/Location Research/lafayette-178"
DATA_DIR = os.path.join(OUT_DIR, "data")
SITE_LAT, SITE_LON = 40.7206287, -73.9989430
SITES = {"1004730044": ("SITE_178", "PJ_CREAM"), "1004730045": ("SITE_176", "PJ_REDBRICK"), "1004730043": ("SITE_180", "PJ_TAN")}
FT = 0.3048; H_FALLBACK = 9.0; COLLECTION = "LAF_178"
# dark ground; 178 in its cream brick with a black fascia and cream bulkhead, 176 red brick, 180 tan with a red cast-iron ground floor.
# Accent for the page is the 6-train green (Canal St / Spring St, 230 m). Colours are one line to change.
PALETTE = {"PJ_INK": "2A2724", "PJ_GROUND": "141210", "PJ_ROAD": "1C1A18", "PJ_WALK": "2B2823", "PJ_MEDIAN": "34302A", "PJ_TREE": "4A5A3A",
           "PJ_LABEL": "8A857C", "PJ_GLASS": "0D1714", "PJ_SHOPGLASS": "A9B8B4", "PJ_IRON": "121212", "PJ_CREAM": "D9CBA8", "PJ_REDBRICK": "7E4A3A",
           "PJ_TAN": "B89B72", "PJ_CASTIRON": "8E2F2A", "PJ_FIRE": "7A2A24", "PJ_BULKHEAD": "E6DCC0", "PJ_TRIM": "C9C2B4", "PJ_GREEN": "00933C",
           "PJ_FLOOR": "9A9A96", "PJ_WHITE": "ECEAE4", "PJ_TIN": "E4E2DC", "PJ_TUNNEL": "0A0908", "PJ_ALU": "B8BABD"}
COSL = math.cos(math.radians(SITE_LAT))

def proj(lon, lat): return ((lon - SITE_LON) * 111320.0 * COSL, (lat - SITE_LAT) * 110540.0)
def hex_to_linear(h):
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i+2], 16) / 255.0; out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (out[0], out[1], out[2], 1.0)
def make_materials():
    for name, hexc in PALETTE.items():
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
        b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if b: b.inputs["Base Color"].default_value = hex_to_linear(hexc); b.inputs["Roughness"].default_value = 0.95
        m.diffuse_color = hex_to_linear(hexc)
        if name == "PJ_STEEL" and b:
            b.inputs["Roughness"].default_value = 0.35
            if "Metallic" in b.inputs: b.inputs["Metallic"].default_value = 0.8
        if name == "PJ_SHOPGLASS" and b:                                                      # clear storefront glass
            b.inputs["Alpha"].default_value = 0.10; b.inputs["Roughness"].default_value = 0.04
            for k in ("Specular IOR Level", "Specular"):
                if k in b.inputs: b.inputs[k].default_value = 0.0
            for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND"), ("use_backface_culling", False), ("show_transparent_back", True), ("use_transparency_overlap", True)):
                try: setattr(m, attr, val)
                except Exception: pass
def load(key):
    """data/<key>.json is a list of Socrata rows with the geometry in the_geom (or multipolygon). Return GeoJSON-ish features."""
    rows = json.load(open(os.path.join(DATA_DIR, key + ".json")))
    out = []
    for r in rows:
        g = r.get("the_geom") or r.get("multipolygon") or r.get("geometry")
        if g: out.append({"properties": r, "geometry": g})
    return out
def rings(geom):
    t = geom.get("type"); c = geom.get("coordinates", [])
    if t == "Polygon": return [c[0]] if c else []
    if t == "MultiPolygon": return [p[0] for p in c if p]
    return []
def contours(geom):
    t = geom.get("type"); c = geom.get("coordinates", [])
    src = [c] if t == "Polygon" else (c if t == "MultiPolygon" else [])
    for poly in src:
        out = []
        for ring in poly:
            pts = [proj(a, b) for a, b in ring]; cl = []
            for p in pts:
                if not cl or abs(p[0]-cl[-1][0]) > 1e-7 or abs(p[1]-cl[-1][1]) > 1e-7: cl.append(p)
            if len(cl) > 2 and abs(cl[0][0]-cl[-1][0]) < 1e-7 and abs(cl[0][1]-cl[-1][1]) < 1e-7: cl = cl[:-1]
            if len(cl) >= 3: out.append(cl)
        if out: yield out

def get_collection():
    old = bpy.data.collections.get(COLLECTION)
    if old:
        for o in list(old.objects): bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(old)
    col = bpy.data.collections.new(COLLECTION); bpy.context.scene.collection.children.link(col); return col
def col(): return bpy.data.collections.get(COLLECTION) or get_collection()

def extrude_ring(bm, xy, z0, z1):
    cl = []
    for p in xy:
        if not cl or abs(p[0]-cl[-1][0]) > 1e-6 or abs(p[1]-cl[-1][1]) > 1e-6: cl.append(p)
    if len(cl) > 2 and abs(cl[0][0]-cl[-1][0]) < 1e-6 and abs(cl[0][1]-cl[-1][1]) < 1e-6: cl = cl[:-1]
    if len(cl) < 3: return False
    vs = [bm.verts.new((p[0], p[1], z0)) for p in cl]
    try: face = bm.faces.new(vs)
    except ValueError: return False
    res = bmesh.ops.extrude_face_region(bm, geom=[face])
    bmesh.ops.translate(bm, vec=(0, 0, z1 - z0), verts=[v for v in res["geom"] if isinstance(v, bmesh.types.BMVert)])
    return True
def mesh_from_bm(bm, name, mat):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); col().objects.link(ob); ob.data.materials.append(bpy.data.materials[mat]); return ob

def stage_massing():
    make_materials(); get_collection(); feats = load("footprints")
    bases = [float(f["properties"].get("ground_elevation") or 0) for f in feats if f["properties"].get("base_bbl") in SITES]
    base = sum(bases) / len(bases) if bases else 0.0
    bm = bmesh.new(); n = 0; guessed = 0
    for f in feats:
        p = f["properties"]
        if p.get("base_bbl") in SITES: continue                      # the three fronts are built by stage_sites()
        try: h_ft = float(p.get("height_roof") or 0)
        except ValueError: h_ft = 0.0
        h = h_ft * FT
        if h <= 0: h = H_FALLBACK; guessed += 1
        ge = (float(p.get("ground_elevation") or base) - base) * FT
        for ring in rings(f["geometry"]):
            if extrude_ring(bm, [proj(a, b) for a, b in ring], ge, ge + h): n += 1
    mesh_from_bm(bm, "SOHO_MASSING", "PJ_INK")
    return "massing: {} solids, {} without height".format(n, guessed)

def build_flat(key, name, z, mat):
    feats = load(key); verts, faces = [], []
    for f in feats:
        for cont in contours(f["geometry"]):
            vecs = [[Vector((x, y, 0.0)) for (x, y) in ring] for ring in cont]; flat = [v for ring in vecs for v in ring]; b = len(verts)
            try: idx = tessellate_polygon(vecs)
            except Exception: continue
            verts.extend([(v.x, v.y, z) for v in flat]); faces.extend([(b+t[0], b+t[1], b+t[2]) for t in idx])
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    ob = bpy.data.objects.new(name, me); col().objects.link(ob); ob.data.materials.append(bpy.data.materials[mat])
    return "{}: {} tris".format(name, len(faces))
def stage_flat():
    return "; ".join([build_flat("roadbed", "ROADBED", 0.02, "PJ_ROAD"), build_flat("sidewalk", "SIDEWALK", 0.14, "PJ_WALK"), build_flat("median", "MEDIAN", 0.18, "PJ_MEDIAN")])

def at_fraction(pts, frac):
    segs = [math.dist(pts[i], pts[i+1]) for i in range(len(pts)-1)]; total = sum(segs); want = total * frac; run = 0.0
    for i, s in enumerate(segs):
        if run + s >= want:
            t = (want - run) / s if s else 0.0; a, b = pts[i], pts[i+1]
            return ((a[0] + (b[0]-a[0])*t, a[1] + (b[1]-a[1])*t), math.atan2(b[1]-a[1], b[0]-a[0]))
        run += s
    return pts[-1], math.atan2(pts[-1][1]-pts[0][1], pts[-1][0]-pts[0][0])
def stage_labels(size=12.0, min_gap=34.0):
    feats = load("centerline"); longest = {}
    for f in feats:
        n = (f["properties"].get("stname_label") or "").strip()
        if not n: continue
        g = f["geometry"]; parts = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
        for line in parts:
            pts = [proj(a, b) for a, b in line]; L = sum(math.dist(pts[i], pts[i+1]) for i in range(len(pts)-1))
            if n not in longest or L > longest[n][0]: longest[n] = (L, pts)
    placed = []
    for name, (L, pts) in sorted(longest.items(), key=lambda kv: -kv[1][0]):
        if L < 40: continue
        spot = None
        for frac in (0.5, 0.3, 0.7, 0.18, 0.82):
            p, ang = at_fraction(pts, frac)
            if all(math.dist(p, q) > min_gap for q in placed): spot = (p, ang); break
        if spot is None: spot = at_fraction(pts, 0.5)
        p, ang = spot
        if ang > math.pi/2: ang -= math.pi
        if ang < -math.pi/2: ang += math.pi
        cu = bpy.data.curves.new("ST_" + name, type='FONT'); cu.body = name; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.size = size; cu.extrude = 0.04; cu.space_character = 1.15
        ob = bpy.data.objects.new("ST_" + name, cu); col().objects.link(ob); ob.location = (p[0], p[1], 0.6); ob.rotation_euler = (0, 0, ang); ob.data.materials.append(bpy.data.materials["PJ_LABEL"]); placed.append(p)
    return "labels: {}".format(len(placed))

def stage_trees():
    rows = [r for r in json.load(open(os.path.join(DATA_DIR, "trees.json"))) if r.get("status") == "Alive"]
    bm = bmesh.new(); n = 0
    for t in rows:
        try: x, y = proj(float(t["longitude"]), float(t["latitude"])); dbh = float(t.get("tree_dbh") or 6)
        except (TypeError, ValueError, KeyError): continue
        r = max(1.4, min(4.2, 1.2 + dbh * 0.12)); h = max(4.0, min(11.0, 3.5 + dbh * 0.35))
        tb = bmesh.new(); bmesh.ops.create_icosphere(tb, subdivisions=1, radius=1.0); bmesh.ops.scale(tb, vec=(r, r, r * 0.8), verts=tb.verts); bmesh.ops.translate(tb, vec=(x, y, h), verts=tb.verts)
        me = bpy.data.meshes.new("t"); tb.to_mesh(me); tb.free(); bm.from_mesh(me); bpy.data.meshes.remove(me); n += 1
    mesh_from_bm(bm, "TREES", "PJ_TREE")
    return "trees: {}".format(n)

def stage_ground():
    bpy.ops.mesh.primitive_plane_add(size=2000, location=(0, 0, -0.3)); g = bpy.context.active_object; g.name = "GROUND"
    for c in g.users_collection: c.objects.unlink(g)

# ---------- the three fronts on Lafayette ----------
# The city outline's 25 ft edge on Lafayette is the building's EAST side; 176 is south of it, 180 north. Local frame per face:
# x = feet along the face from its south corner, d = metres out over the sidewalk (east), z metres up. side = -1 makes +d east.
ROOF_178 = 62.94 * FT; GF = 12.0 * FT; NFL_178 = 6
ROOF_176 = 61.93 * FT; NFL_176 = 5; ROOF_180 = 87.61 * FT; NFL_180 = 7
def _box(bm, x0, x1, y0, y1, z0, z1):
    x0, x1 = min(x0, x1), max(x0, x1); y0, y1 = min(y0, y1), max(y0, y1); z0, z1 = min(z0, z1), max(z0, z1)
    vs = [bm.verts.new(p) for p in ((x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1))]
    for f in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)): bm.faces.new([vs[i] for i in f])
MATS = tuple(PALETTE.keys())
def _front(bbl):
    """(south corner, north corner) in lon/lat of the Lafayette edge of a lot: the two outline points with the largest x+... the east-most edge."""
    for f in load("footprints"):
        if f["properties"].get("base_bbl") != bbl: continue
        ring = rings(f["geometry"])[0]; pts = [(proj(a, b), (a, b)) for a, b in ring]
        best = None
        for i in range(len(pts) - 1):
            (p, pl), (q, ql) = pts[i], pts[i + 1]
            L = math.dist(p, q)
            if L < 6.5: continue
            mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2); score = mid[0] * 0.84 - mid[1] * 0.54     # most ESE edge
            if best is None or score > best[0]: best = (score, pl, ql, p, q)
        _, pl, ql, p, q = best
        return (pl, ql) if p[1] < q[1] else (ql, pl)
    raise RuntimeError("no footprint " + bbl)
def _face(name, a_ll, b_ll, draw, side=-1, prefix="B178_"):
    a = proj(*a_ll); b = proj(*b_ll); ang = math.atan2(b[1]-a[1], b[0]-a[0]); L = math.dist(a, b) / FT
    parts = {}
    def B(mat, x0, x1, d0, d1, z0, z1): _box(parts.setdefault(mat, bmesh.new()), x0 * FT, x1 * FT, side * d0, side * d1, z0, z1)
    cuts = []
    def CUT(x0, x1, d0, d1, z0, z1): cuts.append((x0 * FT, x1 * FT, side * d0, side * d1, z0, z1))
    B.cut = CUT
    draw(B, L)
    root = bpy.data.objects.new(prefix + name, None); col().objects.link(root); root.location = (a[0], a[1], 0.14); root.rotation_euler = (0, 0, ang)
    for mat, bm in parts.items():
        if not bm.faces: bm.free(); continue
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces); me = bpy.data.meshes.new(prefix + name + "_" + mat[3:]); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(prefix + name + "_" + mat[3:], me); col().objects.link(ob); ob.parent = root; ob.data.materials.append(bpy.data.materials[mat])
    for i, c in enumerate(cuts):
        cb = bmesh.new(); _box(cb, *c); me = bpy.data.meshes.new("CUT"); cb.to_mesh(me); cb.free()
        co = bpy.data.objects.new(prefix + "CUT_%s_%d" % (name, i), me); col().objects.link(co); co.parent = root; co.hide_render = True; co.display_type = 'WIRE'
    return root, L
def _win(B, x0, x1, z0, z1, panes=1, d=0.0, glass="PJ_GLASS", frame="PJ_IRON", f=0.25):
    B(glass, x0, x1, d + 0.00, d + 0.04, z0, z1)
    for xx in [x0 + (x1 - x0) * i / panes for i in range(panes + 1)]: B(frame, xx - f / 2, xx + f / 2, d - 0.01, d + 0.07, z0, z1)
    for zz in (z0, z1): B(frame, x0 - f / 2, x1 + f / 2, d - 0.01, d + 0.07, zz - 0.04, zz + 0.04)
def _uppers(B, L, gf, roof, nfl, bays, mat_sill="PJ_TRIM", w=3.4, h=5.2, sill=2.6):
    """Punched windows: `bays` = x centres in feet, on every upper floor; stone sill under each; coping on top."""
    fh = (roof - gf) / (nfl - 1)
    for fl in range(nfl - 1):
        z = gf + fl * fh
        for cx in bays:
            _win(B, cx - w / 2, cx + w / 2, z + sill * FT, z + (sill + h) * FT, panes=2, d=-0.12, glass="PJ_GLASS")
            B(mat_sill, cx - w / 2 - 0.3, cx + w / 2 + 0.3, -0.12, 0.06, z + sill * FT - 0.08, z + sill * FT)
    B(mat_sill, -0.1, L + 0.1, -0.02, 0.10, roof - 0.15, roof + 0.05)
# the leased room, from the flyer plan (feet): 18'-2" x 25'-0" retail, then 9 ft of bath + stair, 36 ft of lease depth; cellar below.
WALL_S = 1.0; ROOM_W = 18.17; ROOM_D = 25.0; BACK_D = 9.0; HALL_W = 4.2; CEIL = 10.5; CELLAR_W, CELLAR_D, CELLAR_Z = 13.9, 41.3, -9.0
X0 = WALL_S; X1 = WALL_S + ROOM_W                                # retail runs x = 1.0 .. 19.17 ft from the south party wall
HX0 = X1 + 0.8; HX1 = HX0 + HALL_W                               # apartment hall north of it (the plan's thick strip + the cellar's side strip)
# From the interior photo (the only real one; both flyer exteriors are staged), measured against the 18'-2" wall. Michael 2026-10-15:
# "doors sitting high, windows rather large, no windows on the back wall, really study the real image."
# One continuous black storefront, no piers: from inside (looking east) left = NORTH window ~5.1 ft, door pair ~6.7 ft, right = SOUTH window ~6.0 ft.
# Window glass 3.3 -> 7.3 ft, door head 7.6 ft, push bars at 3.9 ft, 0.6 ft bottom rails. Louvred vents 3.4 x 1.8 ft centred over each window at 8.0-9.8 ft, AC over the door.
WIN_S = (X0 + 0.2, X0 + 6.17); DOOR = (X0 + 6.17, X0 + 12.87); WIN_N = (X0 + 12.87, X0 + 17.97)
GLASS_Z0, GLASS_Z1, DOOR_Z1, VENT_Z0, VENT_Z1 = 3.3 * FT, 7.3 * FT, 7.6 * FT, 8.0 * FT, 9.8 * FT
def _lafayette_178(B, L):
    # storefront: cream bulkhead under the windows, one run of thick black frames, window / door pair / window touching, vents above, black fascia over all of it.
    B.cut(X0, X1, -(ROOM_D + BACK_D + 1.0) * FT, 0.05, 0.0, CEIL * FT)                                    # the room, cut out of the solid, open at the front
    FR = 0.3                                                                                              # frame width, feet (heavy black storefront)
    for w in (WIN_S, WIN_N):
        B("PJ_BULKHEAD", w[0], w[1], -0.02, 0.10, 0.0, GLASS_Z0)                                          # bulkhead under each window only (never across the door)
        _win(B, w[0], w[1], GLASS_Z0, GLASS_Z1, panes=1, d=0.02, glass="PJ_SHOPGLASS", f=FR)              # fixed display window, thick black frame
        B("PJ_BULKHEAD", w[0], w[1], -0.02, 0.10, GLASS_Z1, VENT_Z0)                                      # solid band between window head and the vent
        cx = (w[0] + w[1]) / 2
        _win(B, cx - 1.7, cx + 1.7, VENT_Z0, VENT_Z1, panes=1, d=0.02, glass="PJ_GLASS", f=0.2)          # louvred vent, centred over the window
        for k in range(5): B("PJ_ALU", cx - 1.6, cx + 1.6, 0.02, 0.05, VENT_Z0 + 0.08 + k * 0.1, VENT_Z0 + 0.10 + k * 0.1)   # louvre slats
        B("PJ_BULKHEAD", w[0], cx - 1.7, -0.02, 0.10, VENT_Z0, VENT_Z1); B("PJ_BULKHEAD", cx + 1.7, w[1], -0.02, 0.10, VENT_Z0, VENT_Z1)
    B("PJ_BULKHEAD", X0, WIN_S[0], -0.02, 0.10, 0.0, VENT_Z1); B("PJ_BULKHEAD", WIN_N[1], X1, -0.02, 0.10, 0.0, VENT_Z1)    # end margins
    # door pair: heavy black jambs and head, two leaves of glass with bottom rails and push bars, threshold
    B("PJ_IRON", DOOR[0], DOOR[1], 0.02, 0.09, 0.0, 0.08)
    for xx in (DOOR[0], DOOR[1] - FR): B("PJ_IRON", xx, xx + FR, -0.01, 0.10, 0.0, DOOR_Z1)
    B("PJ_IRON", DOOR[0], DOOR[1], -0.01, 0.10, DOOR_Z1 - 0.08, DOOR_Z1 + 0.05)
    mid = (DOOR[0] + DOOR[1]) / 2
    for a, b in ((DOOR[0] + FR, mid), (mid, DOOR[1] - FR)):
        B("PJ_SHOPGLASS", a + 0.15, b - 0.15, 0.03, 0.06, 0.6 * FT, DOOR_Z1 - 0.1)                       # leaf glass
        B("PJ_IRON", a, a + 0.15, 0.02, 0.08, 0.08, DOOR_Z1 - 0.08); B("PJ_IRON", b - 0.15, b, 0.02, 0.08, 0.08, DOOR_Z1 - 0.08)   # stiles
        B("PJ_IRON", a, b, 0.02, 0.08, 0.08, 0.6 * FT); B("PJ_IRON", a, b, 0.02, 0.08, DOOR_Z1 - 0.18, DOOR_Z1 - 0.08)   # bottom rail, top rail
        B("PJ_IRON", a + 0.6, b - 0.6, 0.09, 0.14, 3.85 * FT, 4.0 * FT)                                   # push bar, outside
        B("PJ_IRON", a + 0.6, b - 0.6, -0.04, 0.01, 3.85 * FT, 4.0 * FT)                                  # push bar, inside
    B("PJ_BULKHEAD", DOOR[0], DOOR[1], -0.02, 0.10, DOOR_Z1 + 0.05, VENT_Z1)                              # solid panel over the door (the AC hangs inside)
    B("PJ_IRON", X0 - 0.5, X1 + 0.5, 0.0, 0.28, VENT_Z1, GF)                                              # black fascia, sign face left blank (flush inside, never through the wall)
    # apartment hall door north of the shop: dark door, transom, a stone step
    B.cut(HX0, HX1, -(ROOM_D + BACK_D + 1.0) * FT, 0.05, 0.0, 9.0 * FT)
    B("PJ_IRON", HX0 + 0.3, HX1 - 0.3, 0.02, 0.08, 0.12, 7.5 * FT); B("PJ_ALU", HX1 - 0.9, HX1 - 0.8, 0.08, 0.13, 0.95, 1.05)
    _win(B, HX0 + 0.3, HX1 - 0.3, 7.6 * FT, 9.0 * FT, panes=1, d=0.02)
    B("PJ_TRIM", HX0, HX1, 0.0, 0.35, 0.0, 0.12); B("PJ_CREAM", HX0 - 0.4, HX1 + 0.4, -0.02, 0.10, 9.0 * FT, GF)
    B("PJ_CREAM", X1, HX0, -0.02, 0.10, 0.0, GF); B("PJ_CREAM", HX1, L, -0.02, 0.10, 0.0, GF); B("PJ_CREAM", 0, X0, -0.02, 0.10, 0.0, GF)
    # uppers: cream brick, three windows a floor, the red fire escape hung on the middle of the front
    bays = (L * 0.2, L * 0.5, L * 0.8)
    _uppers(B, L, GF, ROOF_178, NFL_178, bays)
    fh = (ROOF_178 - GF) / (NFL_178 - 1)
    for fl in range(NFL_178 - 1):
        z = GF + fl * fh + 0.25
        B("PJ_FIRE", L * 0.32, L * 0.68, 0.10, 0.95, z, z + 0.05)                                         # balcony grating
        for dd in (0.92,): B("PJ_FIRE", L * 0.32, L * 0.68, dd, dd + 0.03, z, z + 1.0)                    # front rail
        for xx in (L * 0.32, L * 0.68): B("PJ_FIRE", xx, xx + 0.1, 0.10, 0.95, z, z + 1.0)                 # side rails
        if fl < NFL_178 - 2: B("PJ_FIRE", L * 0.36, L * 0.44, 0.45, 0.60, z + 0.05, z + fh)                 # ladder as a thin slab
def _lafayette_176(B, L):
    # Daily Bubble Laundromat: aluminium shopfront, big window + door at the north end, black fascia, red brick above.
    B("PJ_IRON", -0.1, L + 0.1, -0.02, 0.22, 9.3 * FT, GF)
    B("PJ_BULKHEAD", 0, L, -0.02, 0.06, 0.0, 1.2 * FT)
    _win(B, 1.0, L - 6.5, 1.2 * FT, 9.3 * FT, panes=2, d=0.02, glass="PJ_SHOPGLASS", frame="PJ_ALU")
    _win(B, L - 5.5, L - 1.0, 0.12, 9.3 * FT, panes=1, d=0.02, glass="PJ_SHOPGLASS", frame="PJ_ALU")
    B("PJ_REDBRICK", 0, 1.0, -0.02, 0.06, 0.0, GF); B("PJ_REDBRICK", L - 1.0, L, -0.02, 0.06, 0.0, GF); B("PJ_REDBRICK", L - 6.5, L - 5.5, -0.02, 0.06, 0.0, GF)
    _uppers(B, L, GF, ROOF_176, NFL_176, (L * 0.25, L * 0.75), w=3.6)
def _lafayette_180(B, L):
    # the red cast-iron storefront with a stoop: two tall bays and a raised door, tan brick above with three windows a floor.
    B("PJ_CASTIRON", -0.1, L + 0.1, -0.02, 0.18, 0.0, 13.5 * FT)
    _win(B, 1.2, 9.5, 2.0 * FT, 11.5 * FT, panes=2, d=0.02, glass="PJ_GLASS", frame="PJ_CASTIRON")
    _win(B, 15.5, L - 1.2, 2.0 * FT, 11.5 * FT, panes=2, d=0.02, glass="PJ_GLASS", frame="PJ_CASTIRON")
    B("PJ_IRON", 10.7, 14.3, 0.02, 0.08, 2.0 * FT, 10.0 * FT)                                              # door up the stoop
    for k in range(4): B("PJ_TRIM", 10.2, 14.8, 0.18 + k * 0.3, 0.18 + (k + 1) * 0.3 + 0.02, 0.0, (2.0 - k * 0.5) * FT)   # stoop
    _uppers(B, L, 13.5 * FT, ROOF_180, NFL_180, (L * 0.2, L * 0.5, L * 0.8))

def stage_sites():
    """The three lots as their own solids (the massing skips them), each in its facade colour."""
    feats = load("footprints"); base = 0.0
    for f in feats:
        p = f["properties"]
        if p.get("base_bbl") not in SITES: continue
        name, mat = SITES[p["base_bbl"]]; h = float(p.get("height_roof") or 60) * FT
        bm = bmesh.new()
        for ring in rings(f["geometry"]): extrude_ring(bm, [proj(a, b) for a, b in ring], 0.0, h)
        mesh_from_bm(bm, name, mat)
    return "sites: " + ", ".join(v[0] for v in SITES.values())
def _apply_cuts(site_name, prefix):
    bpy.context.view_layer.update(); site = bpy.data.objects.get(site_name)
    for co in [o for o in bpy.data.objects if o.name.startswith(prefix + "CUT_")]:
        m = site.modifiers.new("cut", 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.object = co
        try: m.solver = 'EXACT'
        except Exception: pass
        with bpy.context.temp_override(object=site, active_object=site): bpy.ops.object.modifier_apply(modifier=m.name)
        bpy.data.objects.remove(co, do_unlink=True)
def stage_building():
    for o in [o for o in bpy.data.objects if o.name.startswith("B178_") or o.name.startswith("B176_") or o.name.startswith("B180_")]: bpy.data.objects.remove(o, do_unlink=True)
    r178, L = _face("LAFAYETTE", *_front("1004730044"), _lafayette_178)
    _face("LAFAYETTE", *_front("1004730045"), _lafayette_176, prefix="B176_")
    _face("LAFAYETTE", *_front("1004730043"), _lafayette_180, prefix="B180_")
    _apply_cuts("SITE_178", "B178_")
    return "building: 178 front {:.1f} ft, retail {:.1f}-{:.1f} ft from the south wall, hall {:.1f}-{:.1f} ft".format(L, X0, X1, HX0, HX1)

# ---------- the leased space (white box): retail room, back section with bath + stair, cellar ----------
T = 0.4
def _interior(B, L):
    ft = lambda v: v * FT                                   # d and z are metres; the plan is in feet
    dr = -ft(ROOM_D); db = -ft(ROOM_D + BACK_D); dl = db - ft(1.0)
    # floor, ceiling (pressed tin), walls
    B("PJ_FLOOR", X0, X1, db, 0.02, 0.02, 0.06)                                                  # retail + back floor, grey tile
    B("PJ_TIN", X0, X1, db, 0.0, ft(CEIL), ft(CEIL) + 0.3)                                        # tin ceiling
    B("PJ_WHITE", X0 - T, X0, db - T, 0.0, 0.0, ft(CEIL) + 0.3)                                  # south wall
    B("PJ_WHITE", X1, X1 + T, db - T, 0.0, 0.0, ft(CEIL) + 0.3)                                  # north wall (hall beyond)
    B("PJ_WHITE", X0 - T, X1 + T, db - T, db, 0.0, ft(CEIL) + 0.3)                               # back wall of the lease
    # dividing wall between retail and the back: solid, with one door left of centre (the plan); no windows (Michael)
    bd = (X0 + 7.6, X0 + 10.7)
    B("PJ_WHITE", X0, bd[0], dr - T, dr, 0.0, ft(CEIL)); B("PJ_WHITE", bd[1], X1, dr - T, dr, 0.0, ft(CEIL)); B("PJ_WHITE", bd[0], bd[1], dr - T, dr, ft(7.2), ft(CEIL))
    # cove moulding at the top of the three long walls
    for (xa, xb, ya, yb) in ((X0, X0 + 0.25, dr, 0.0), (X1 - 0.25, X1, dr, 0.0), (X0, X1, dr, dr + 0.08)): B("PJ_WHITE", xa, xb, ya, yb, ft(CEIL) - 0.12, ft(CEIL))
    # bath (back-left) and the stair down (back-right)
    B("PJ_WHITE", X0 + 5.2, X0 + 5.2 + T, db, dr - T, 0.0, ft(CEIL)); B("PJ_WHITE", X0, X0 + 5.6, db + ft(4.4), db + ft(4.4) + T, 0.0, ft(CEIL))
    B("PJ_IRON", X0 + 5.2 + 0.02, X0 + 5.2 + T - 0.02, db + ft(1.0), db + ft(3.6), 0.0, ft(7.0))   # bath door
    B("PJ_IRON", X1 - 3.6, X1 - 0.3, db + ft(0.6), db + ft(5.8), -0.05, -0.02)                    # stair opening (dark)
    B("PJ_TRIM", X1 - 3.6, X1 - 3.5, db + ft(0.6), db + ft(5.8), 0.0, ft(3.0))                     # rail
    # cellar: a plain void under the room
    B("PJ_FLOOR", X0 + 1.5, X0 + 1.5 + CELLAR_W, -ft(CELLAR_D) - ft(2.0), -ft(2.0), ft(CELLAR_Z) - 0.1, ft(CELLAR_Z))
    B.cut(X0 + 1.5, X0 + 1.5 + CELLAR_W, -ft(CELLAR_D) - ft(2.0), -ft(2.0), ft(CELLAR_Z), -0.4)
    # ten surface lights in two rows of five (the photo) as small discs; the AC over the door
    for i in range(5):
        for xx in (X0 + 4.5, X1 - 4.5): B("PJ_WHITE", xx - 0.2, xx + 0.2, -ft(2.5 + i * 5.0) - 0.06, -ft(2.5 + i * 5.0) + 0.06, ft(CEIL) - 0.12, ft(CEIL))   # bare bulb fixtures on the tin
    B("PJ_WHITE", (DOOR[0] + DOOR[1]) / 2 - 1.4, (DOOR[0] + DOOR[1]) / 2 + 1.4, -0.30, -0.05, ft(8.3), ft(9.4))                 # the split AC over the door
    # apartment hall: floor + walls, open to the back
    B("PJ_FLOOR", HX0, HX1, db, 0.02, 0.02, 0.06); B("PJ_WHITE", HX0, HX1, db, 0.0, ft(9.0), ft(9.0) + 0.3)
    B("PJ_WHITE", HX0 - T, HX0, db, 0.0, 0.0, ft(9.0) + 0.3); B("PJ_WHITE", HX1, HX1 + T, db, 0.0, 0.0, ft(9.0) + 0.3)
def stage_interior():
    for o in [o for o in bpy.data.objects if o.name.startswith("B178_IN_")]: bpy.data.objects.remove(o, do_unlink=True)
    _face("IN", *_front("1004730044"), _interior)
    _apply_cuts("SITE_178", "B178_CUT_IN")
    # lights for the inside plates: the ten cans as point lights
    root = bpy.data.objects["B178_IN"]
    for i in range(5):
        for j, xx in enumerate((X0 + 4.5, X1 - 4.5)):
            ld = bpy.data.lights.new("B178_IN_CAN", 'POINT'); ld.energy = 140; ld.shadow_soft_size = 0.25
            lo = bpy.data.objects.new("B178_IN_CAN_%d%d" % (i, j), ld); col().objects.link(lo); lo.parent = root
            lo.location = (xx * FT, (2.5 + i * 5.0) * FT, CEIL * FT - 0.15)
    return "interior: retail {:.1f} x {:.1f} ft, ceiling {:.1f} ft, back {:.0f} ft, cellar {:.1f} x {:.1f} ft".format(ROOM_W, ROOM_D, CEIL, BACK_D, CELLAR_W, CELLAR_D)
def interior_view(on, ceiling=True):
    """Hide the floors above the shop so the inside cameras see in: the site solid above the ceiling and the neighbours' uppers."""
    for n in ("SITE_178", "SITE_176", "SITE_180") + (() if ceiling else ("B178_IN_TIN",)):
        o = bpy.data.objects.get(n)
        if o: o.hide_render = on; o.hide_viewport = on
    c = bpy.data.objects.get("B178_IN_TIN")
    if c and ceiling: c.hide_render = False; c.hide_viewport = False

def _w(x_ft, d_m, z_m):
    """world point in the 178 front frame: x feet north from the south corner, d metres east of the face, z up"""
    a_ll, b_ll = _front("1004730044"); a = Vector(proj(*a_ll)); b = Vector(proj(*b_ll)); ex = (b - a).normalized(); ey = Vector((-ex.y, ex.x))
    p = a + ex * (x_ft * FT) + ey * (-d_m); return (p.x, p.y, z_m)
def cam(name, loc, target, lens=24, ortho=None):
    c = bpy.data.objects.get(name)
    if not c:
        c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); bpy.context.scene.collection.objects.link(c)
    c.location = loc; c.data.lens = lens; c.data.clip_end = 3000
    if ortho: c.data.type = 'ORTHO'; c.data.ortho_scale = ortho
    c.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return c
def stage_cameras():
    sc = bpy.context.scene
    if not bpy.data.objects.get("SUN"):
        bpy.ops.object.light_add(type='SUN', location=(0, 0, 300)); s = bpy.context.active_object; s.name = "SUN"; s.data.energy = 3.0
        az, el = math.radians(125), math.radians(40)                 # the front faces ESE: mid-morning sun on it
        toward = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el))); s.rotation_euler = (-toward).to_track_quat('-Z', 'Y').to_euler()
    w = sc.world or bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    bg = next((n for n in w.node_tree.nodes if n.type == "BACKGROUND"), None)
    if bg: bg.inputs[0].default_value = (0.08, 0.075, 0.07, 1); bg.inputs[1].default_value = 1.0
    for name, loc, rot, ortho in (("CAM_PLAN", (0, 0, 600), (0, 0, math.radians(29)), 560), ("CAM_WIDE", (0, 0, 600), (0, 0, math.radians(29)), 900)):
        c = bpy.data.objects.get(name)
        if not c:
            cd = bpy.data.cameras.new(name); c = bpy.data.objects.new(name, cd); sc.collection.objects.link(c)
        c.location = loc; c.rotation_euler = rot; c.data.type = 'ORTHO'; c.data.ortho_scale = ortho; c.data.clip_end = 2000
    axon = bpy.data.objects.get("CAM_AXON")
    if not axon:
        cd = bpy.data.cameras.new("CAM_AXON"); axon = bpy.data.objects.new("CAM_AXON", cd); sc.collection.objects.link(axon)
    axon.location = (-260, -420, 420); axon.rotation_euler = (math.radians(50), 0, math.radians(-29)); axon.data.type = 'ORTHO'; axon.data.ortho_scale = 700; axon.data.clip_end = 3000
    mid = (X0 + X1) / 2
    cam("CAM_178_front", _w(mid, 15.5, 1.65), _w(mid, 0.0, 3.4))                              # across Lafayette, square on the shop
    cam("CAM_178_sidewalk", _w(X1 + 14.0, 3.2, 1.6), _w(X0 + 6.0, 0.0, 2.4))                     # on the sidewalk, from the 180 side, looking along the glass
    cam("CAM_178_down_block", _w(-60.0, 9.0, 1.65), _w(mid, 0.5, 6.0))                          # up the block from the Grand St end
    cam("CAM_178_axon_close", _w(mid + 40.0, 70.0, 55.0), _w(mid, -10.0, 8.0), lens=35)
    cam("CAM_178_in_to_street", _w(X0 + 3.0, -(ROOM_D - 1.5) * FT, 1.6), _w(X1 - 3.0, 0.3, 1.5))       # from the back-left corner, to the glass
    cam("CAM_178_in_to_back", _w(X1 - 2.0, -1.0 * FT, 1.6), _w(X0 + 4.0, -ROOM_D * FT, 1.3))           # just inside the north window, to the back wall
    cam("CAM_178_in_long", _w(mid, 0.6, 1.55), _w(mid, -ROOM_D * FT, 1.4))                            # in the doorway, straight down the room
    cam("CAM_178_in_plan", _w(mid, -(ROOM_D + BACK_D) * FT / 2, 40.0), _w(mid, -(ROOM_D + BACK_D) * FT / 2, 0.0), ortho=16.0)
    a_ll, b_ll = _front("1004730044"); a = proj(*a_ll); b = proj(*b_ll)
    bpy.data.objects["CAM_178_in_plan"].rotation_euler[2] = math.atan2(b[1] - a[1], b[0] - a[0])
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'):
        if eng in engines:
            try: sc.render.engine = eng; break
            except TypeError: continue
    sc.render.resolution_x = 1800; sc.render.resolution_y = 1200; sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 90
    vs = sc.view_settings; looks = [i.identifier for i in type(vs).bl_rna.properties['view_transform'].enum_items]
    for vt in ('AgX', 'Filmic', 'Standard'):
        if vt in looks:
            try: vs.view_transform = vt; break
            except TypeError: continue
    return "cameras: plan, wide, axon, front, sidewalk, down_block, axon_close, in_to_street, in_to_back, in_long, in_plan; engine " + sc.render.engine
def street_look(on):
    sc = bpy.context.scene; w = sc.world; bg = next((n for n in w.node_tree.nodes if n.type == "BACKGROUND"), None)
    if bg: bg.inputs[0].default_value = (0.55, 0.56, 0.58, 1) if on else (0.08, 0.075, 0.07, 1); bg.inputs[1].default_value = 2.6 if on else 1.0
    sc.view_settings.exposure = 0.7 if on else 0.0
    sun = bpy.data.objects.get("SUN")
    if sun: sun.data.energy = 4.5 if on else 3.0
def render(cam_name, filename):
    sc = bpy.context.scene; sc.camera = bpy.data.objects[cam_name]; os.makedirs(os.path.join(OUT_DIR, "frames"), exist_ok=True)
    street_look(cam_name.startswith("CAM_178_"))
    sc.render.filepath = os.path.join(OUT_DIR, "frames", filename)
    bpy.ops.render.render(write_still=True); return "rendered " + sc.render.filepath
def export_glb(filename="lafayette_178.glb"):
    for o in bpy.data.objects: o.select_set(False)
    names = ["SOHO_MASSING", "SITE_178", "SITE_176", "SITE_180", "ROADBED", "SIDEWALK", "MEDIAN", "GROUND", "TREES"] + [o.name for o in bpy.data.objects if o.name.startswith("ST_") or (o.name[:5] in ("B178_", "B176_", "B180_") and o.type == "MESH")]
    for n in names:
        o = bpy.data.objects.get(n)
        if o: o.select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["SOHO_MASSING"]
    path = os.path.join(OUT_DIR, "assets", filename); os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6, export_apply=True, export_cameras=False, export_lights=False, export_yup=True)
    return "exported {} {:.0f} KB".format(path, os.path.getsize(path) / 1024)
def site_center():
    ob = bpy.data.objects.get("SITE_178")
    if not ob or not ob.data.vertices: return None
    xs = [v.co.x for v in ob.data.vertices]; ys = [v.co.y for v in ob.data.vertices]
    return [round(sum(xs)/len(xs), 1), 0, round(-sum(ys)/len(ys), 1)]

if __name__ == "__main__" or bpy.app.background:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for fn in (stage_massing, stage_flat, stage_labels, stage_trees, stage_ground, stage_sites, stage_building, stage_interior, stage_cameras):
        print(fn(), flush=True)
    pts = {"site": site_center(), "canal_6": [round(v, 1) for v in proj(-73.999928, 40.718591)], "spring_6": [round(v, 1) for v in proj(-73.997141, 40.722301)],
           "canal_rw": [round(v, 1) for v in proj(-74.001012, 40.719196)], "prince_rw": [round(v, 1) for v in proj(-73.997702, 40.724329)]}
    json.dump(pts, open(os.path.join(OUT_DIR, "data", "model_points.json"), "w")); print("points", pts, flush=True)
    for c, fn in (("CAM_PLAN", "map_plan.jpg"), ("CAM_AXON", "map_axon.jpg"), ("CAM_178_front", "CAM_178_front.jpg"), ("CAM_178_sidewalk", "CAM_178_sidewalk.jpg"), ("CAM_178_down_block", "CAM_178_down_block.jpg"), ("CAM_178_axon_close", "CAM_178_axon_close.jpg")):
        try: print(render(c, fn), flush=True)
        except Exception as e: print("render failed", c, e, flush=True)
    interior_view(True)
    for c, fn in (("CAM_178_in_to_street", "CAM_178_in_to_street.jpg"), ("CAM_178_in_to_back", "CAM_178_in_to_back.jpg"), ("CAM_178_in_long", "CAM_178_in_long.jpg")):
        try: print(render(c, fn), flush=True)
        except Exception as e: print("render failed", c, e, flush=True)
    interior_view(True, ceiling=False)
    try: print(render("CAM_178_in_plan", "CAM_178_in_plan.jpg"), flush=True)
    except Exception as e: print("render failed plan", e, flush=True)
    interior_view(False)
    try: print(export_glb(), flush=True)
    except Exception as e: print("export failed", e, flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, "build", "lafayette_178.blend"))
    print("BUILD DONE", flush=True)
