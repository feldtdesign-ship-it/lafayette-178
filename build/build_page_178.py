"""build_page_178.py — turns data/ into index.html from build/laf178_template.html. No traffic numbers on this page (marketing, not a dossier).
Run: python3 build/make_template_178.py && python3 build/build_page_178.py   (then build/make_card.sh for og.jpg)"""
import json, os, datetime, re, math, subprocess
S = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(S); D = os.path.join(R, 'data')
LAT, LON = 40.7206287, -73.9989430
TODAY = datetime.date(2026, 10, 15)
nbldg = len(json.load(open(os.path.join(D, 'footprints.json'))))
ntrees = sum(1 for x in json.load(open(os.path.join(D, 'trees.json'))) if x.get('status') == 'Alive')
points = json.load(open(os.path.join(D, 'model_points.json')))
# the door the page flies to: the middle of the door pair, 10 ft north of the south front corner, in glTF space (x east, z south); N = out over Lafayette
_cos = math.cos(math.radians(LAT)); _p = lambda lo, la: ((lo - LON) * 111320 * _cos, (la - LAT) * 110540)
best = None
for f in json.load(open(os.path.join(D, 'footprints.json'))):
    if f.get('base_bbl') != '1004730044': continue
    ring = f['the_geom']['coordinates'][0][0] if f['the_geom']['type'] == 'MultiPolygon' else f['the_geom']['coordinates'][0]
    pts = [_p(a, b) for a, b in ring]
    for i in range(len(pts) - 1):
        p, q = pts[i], pts[i + 1]; L = math.dist(p, q)
        if L < 6.5: continue
        mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2); score = mid[0] * 0.84 - mid[1] * 0.54
        if best is None or score > best[0]: best = (score, p, q)
_, p, q = best
a, b = (p, q) if p[1] < q[1] else (q, p)                       # a = south corner, b = north corner
ex = ((b[0] - a[0]) / math.dist(a, b), (b[1] - a[1]) / math.dist(a, b)); out = (ex[1], -ex[0])   # outward = east side of the front
door = (a[0] + ex[0] * 10.02 * 0.3048, a[1] + ex[1] * 10.02 * 0.3048)
points['door'] = [round(door[0], 1), 0, round(-door[1], 1)]
points['facing'] = [round(out[0], 3), round(-out[1], 3)]       # glTF z = -world y
# web copies of the check frames for the poster fallback
os.makedirs(os.path.join(R, 'frames'), exist_ok=True)
for n in ('map_axon', 'map_plan', 'CAM_178_front'):
    src = os.path.join(R, 'frames', n + '.jpg'); dst = os.path.join(R, 'frames', n + '_web.jpg')
    if os.path.exists(src) and not os.path.exists(dst): subprocess.run(['sips', '-Z', '1600', '-s', 'format', 'jpeg', '-s', 'formatOptions', '82', src, '--out', dst], capture_output=True)
subs = {'__POINTS__': json.dumps(points), '__DARKMAX__': '0', '__TODAY__': f"{TODAY.day} {TODAY:%B %Y}", '__NBLDG__': f"{nbldg:,}", '__NTREES__': f"{ntrees:,}"}
out_html = open(os.path.join(S, 'laf178_template.html')).read()
for k, v in subs.items(): out_html = out_html.replace(k, v)
left = sorted(set(re.findall(r'__[A-Z0-9]+__', out_html)))
open(os.path.join(R, 'index.html'), 'w').write(out_html)
print('points', points); print(f"built index.html {len(out_html) // 1024} KB · unfilled {left}")
