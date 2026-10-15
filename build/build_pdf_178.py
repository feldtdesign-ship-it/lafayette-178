"""
build_pdf_178.py — the marketing PDF: PJ O'Rourke II at 178 Lafayette. Letter portrait, six pages, in the spirit of the Corcoran flyer.
Run: python3 build/build_pdf_178.py            -> pdf/178_lafayette.html + PJ_ORourke_II_178_Lafayette.pdf (in the folder root)
Images: pdf/img/<shot>.jpg. By default they are copied from listing/plates/ (the Cycles plates). Drop Michael's Gemini visualizations
into pdf/img/ with the same names and rerun; the layout never changes. No money anywhere in this file, on purpose.
Printing goes through pj-tee-tech-pack/tools/print_pdf.mjs (Chrome over DevTools; Chrome's own --print-to-pdf hangs on this Mac).
"""
import os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE); PJ = os.path.dirname(os.path.dirname(OUT))
PDF_DIR = os.path.join(OUT, "pdf"); IMG = os.path.join(PDF_DIR, "img"); os.makedirs(IMG, exist_ok=True)
PLATES = os.path.join(OUT, "listing", "plates")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PRINT = os.path.join(PJ, "pj-tee-tech-pack", "tools", "print_pdf.mjs")
SIG = os.path.join(PJ, "Signature", "PJ_Signature_ink_transparent.png")
ART = os.path.join(PJ, "Location Research", "avea-115-interior", "artwork")
TEE_ART = os.path.join(PJ, "Location Research", "mott-167", "listing", "tee_art")
SHOTS = ["CAM_178_front", "CAM_178_hero_window", "CAM_178_in_long", "CAM_178_in_gallery", "CAM_178_in_shelves", "CAM_178_in_to_street", "CAM_178_sidewalk"]

def stage_images():
    for s in SHOTS:
        dst = os.path.join(IMG, s + ".jpg"); src = os.path.join(PLATES, s + ".jpg")
        if os.path.exists(src) and (not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst)): shutil.copy(src, dst)   # a newer plate replaces its copy; a Gemini image dropped in later stays
    if os.path.exists(SIG): shutil.copy(SIG, os.path.join(IMG, "sig.png"))
    for i in range(1, 8):
        p = os.path.join(ART, "art_%02d.jpg" % i)
        if os.path.exists(p): shutil.copy(p, os.path.join(IMG, "art_%02d.jpg" % i))
    for cw in ("cream", "navy", "lilac", "moss", "peach"):
        p = os.path.join(TEE_ART, "tee_%s_01.png" % cw)
        if os.path.exists(p): shutil.copy(p, os.path.join(IMG, "tee_%s.png" % cw))
    plan = os.path.join(OUT, "frames", "CAM_178_in_plan.jpg")
    if os.path.exists(plan): shutil.copy(plan, os.path.join(IMG, "plan.jpg"))

CSS = """
@page { size: 8.5in 11in; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #fff; color: #111; font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.page { width: 8.5in; height: 11in; position: relative; overflow: hidden; page-break-after: always; padding: 0.55in 0.6in 0.5in; }
.page:last-child { page-break-after: auto; }
.k { font-size: 9.5px; letter-spacing: 0.22em; text-transform: uppercase; color: #555; }
h1 { font-size: 46px; line-height: 0.98; letter-spacing: -0.02em; margin: 0; font-weight: 800; }
h2 { font-size: 30px; line-height: 1.02; letter-spacing: -0.015em; margin: 0 0 10px; font-weight: 800; }
h3 { font-size: 13px; margin: 0 0 4px; font-weight: 700; letter-spacing: 0.01em; }
p { font-size: 11.5px; line-height: 1.5; margin: 0 0 9px; }
.lead { font-size: 14.5px; line-height: 1.45; }
.pink { color: #E8559C; } .bg-pink { background: #E8559C; } .yellow { background: #F5DE4A; }
.hero { width: 100%; object-fit: cover; display: block; border-radius: 2px; }
.band { position: absolute; left: 0; right: 0; bottom: 0; height: 0.32in; background: repeating-linear-gradient(90deg, #F5DE4A 0 0.16in, #fff 0.16in 0.24in); }
.band:after { content: ""; position: absolute; inset: 0; background: radial-gradient(circle, #F5DE4A 0.055in, transparent 0.06in) 0 0 / 0.16in 0.16in; }
.foot { position: absolute; left: 0.6in; right: 0.6in; bottom: 0.45in; display: flex; justify-content: space-between; align-items: flex-end; font-size: 9px; letter-spacing: 0.12em; text-transform: uppercase; color: #777; }
.foot img { height: 0.42in; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 0.22in; }
.grid3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.16in; }
.spec { border-top: 2px solid #111; }
.spec div { display: flex; justify-content: space-between; gap: 12px; padding: 6px 0; border-bottom: 1px solid #ddd; font-size: 11px; }
.spec div b { font-weight: 700; } .spec div span:last-child { text-align: right; color: #333; }
.cap { font-size: 9px; color: #666; margin-top: 4px; letter-spacing: 0.04em; }
.big { font-size: 64px; font-weight: 800; letter-spacing: -0.03em; line-height: 1; }
.strip { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; }
.strip img { width: 100%; aspect-ratio: 11/14; object-fit: cover; border: 1px solid #111; }
.tees { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; }
.tee { aspect-ratio: 1; display: flex; align-items: center; justify-content: center; border-radius: 3px; }
.tee img { width: 70%; }
.num { font-size: 34px; font-weight: 800; letter-spacing: -0.02em; line-height: 1; }
ul { margin: 0 0 8px 0; padding-left: 14px; font-size: 11.5px; line-height: 1.5; } li { margin-bottom: 3px; }
.rule { height: 2px; background: #111; margin: 10px 0 12px; }
"""

def page(inner, n):
    return f'<section class="page">{inner}<div class="foot"><span>PJ O\'Rourke II &nbsp;·&nbsp; 178 Lafayette Street, SoHo</span><img src="img/sig.png"><span>{n}</span></div></section>'

def html():
    p1 = f'''
<div class="k">A proposal for the storefront at</div>
<h1 style="margin-top:6px">178 Lafayette<br>Street</h1>
<p class="lead" style="margin-top:12px;max-width:5.4in">PJ O'Rourke II, the New York artist who started selling his prints off a hand-built cart on subway platforms, puts his flagship in a 705 square foot jewel box in the heart of SoHo and Nolita.</p>
<img class="hero" src="img/CAM_178_hero_window.jpg" style="height:5.7in;margin-top:12px">
<div class="cap">The window on Lafayette Street. Visualization from the measured model of the space.</div>
<div class="grid3" style="margin-top:14px">
  <div><div class="num">705</div><div class="k" style="margin-top:4px">square feet, plus cellar</div></div>
  <div><div class="num">18'-2"</div><div class="k" style="margin-top:4px">of glass on Lafayette</div></div>
  <div><div class="num">6</div><div class="k" style="margin-top:4px">train, four minutes away</div></div>
</div>'''
    p2 = f'''
<div class="k">The space</div>
<h2>A white box with a black steel face</h2>
<div class="grid2">
  <div>
    <p>One clean room, 18 feet 2 inches wide and 25 feet deep, under a white pressed-tin ceiling with ten bare bulbs in two rows. Pale grey tile underfoot, white plaster walls, a split system over the door. Behind it, a bath and the stair down to a dedicated 13 by 41 foot cellar for stock.</p>
    <p>The storefront is one run of heavy black steel: a display window, a pair of glass doors, a second display window, with louvred vents above and a plain black fascia ready for one name. Ownership delivers white box with HVAC.</p>
    <div class="spec" style="margin-top:10px">
      <div><b>Ground floor</b><span>705 rentable sq ft</span></div>
      <div><b>Sales room</b><span>18'-2" x 25'-0"</span></div>
      <div><b>Cellar</b><span>13'-11" x 41'-4", dedicated</span></div>
      <div><b>Frontage</b><span>Two display windows and a centre door pair</span></div>
      <div><b>Ceiling</b><span>Pressed tin, about 10'-6"</span></div>
      <div><b>Delivery</b><span>White box, HVAC in place</span></div>
      <div><b>Back of house</b><span>Bath and stair to cellar</span></div>
      <div><b>Block</b><span>Lafayette between Grand and Broome</span></div>
    </div>
  </div>
  <div>
    <img class="hero" src="img/CAM_178_in_to_street.jpg" style="height:2.55in">
    <div class="cap">Looking to the street from the back of the room.</div>
    <img class="hero" src="img/plan.jpg" style="height:2.55in;margin-top:12px;object-fit:cover">
    <div class="cap">Plan of the fitted-out room, from the model.</div>
  </div>
</div>
<div class="rule"></div>
<div class="grid3">
  <div><h3>SoHo meets Nolita</h3><p>Lafayette is the seam between the cast-iron district and the little streets east of it. Foot traffic comes both ways: the SoHo shopper walking east, the Nolita local walking west.</p></div>
  <div><h3>On the 6</h3><p>Spring Street and Canal Street on the 6 are each a four-minute walk. Canal Street's N, Q, R, W, J and Z are five. Prince Street's R and W are seven.</p></div>
  <div><h3>A landmarked front</h3><p>The building is a 1906 walk-up inside the SoHo-Cast Iron Historic District Extension. The red fire escape and cream brick above the shop are the backdrop.</p></div>
</div>'''
    p3 = f'''
<div class="k">The store</div>
<h2>Prints on one wall, tees on the other, the figure in the window</h2>
<img class="hero" src="img/CAM_178_in_long.jpg" style="height:4.3in">
<div class="cap">Straight down the room from the door.</div>
<div class="grid2" style="margin-top:14px">
  <div>
    <h3>The gallery wall</h3>
    <p>The south wall is hung with PJ's prints in one level row of black frames: the line drawings of New York characters that started the whole thing on the subway platforms.</p>
    <h3>The shelving wall</h3>
    <p>The north wall is matte black pipe and white oak plank, planks of folded tees above and a rail of hangers below, one colourway to a bay: cream, navy, lilac, moss, peach.</p>
  </div>
  <div>
    <h3>The floor</h3>
    <p>Two white oak tables carry the folded stock and the current drop. A black counter sits by the back door. A Galaga cabinet stands in the back corner, because every PJ store has one.</p>
    <h3>The window</h3>
    <p>Gumbit, the bubblegum-pink suit-and-tie character, stands four feet tall on a black plinth in the north window, lit from above, facing Lafayette Street. The south window carries the signature in white and the newest work.</p>
  </div>
</div>'''
    p4 = f'''
<div class="grid2">
  <div><img class="hero" src="img/CAM_178_in_gallery.jpg" style="height:3.3in"><div class="cap">The print wall.</div></div>
  <div><img class="hero" src="img/CAM_178_in_shelves.jpg" style="height:3.3in"><div class="cap">The shelving wall and the window.</div></div>
</div>
<div class="k" style="margin-top:18px">The work</div>
<h2>Drawn by hand, printed in New York</h2>
<div class="strip">{''.join('<img src="img/art_%02d.jpg">' % i for i in range(1, 8))}</div>
<div class="cap">Seven of the prints that hang on the gallery wall.</div>
<div class="tees" style="margin-top:14px">
  <div class="tee" style="background:#F2DFC0"><img src="img/tee_cream.png"></div>
  <div class="tee" style="background:#304766"><img src="img/tee_navy.png"></div>
  <div class="tee" style="background:#EDD0EF"><img src="img/tee_lilac.png"></div>
  <div class="tee" style="background:#4C605E"><img src="img/tee_moss.png"></div>
  <div class="tee" style="background:#FEA580"><img src="img/tee_peach.png"></div>
</div>
<div class="cap">The five colourways of the heavyweight garment-dyed tee, 100% USA cotton, screen printed with the line work.</div>
<p style="margin-top:12px">Graphic tees, crop tees, hoodies and bombers, art prints in two sizes, and the Gumbit figure as a small collectible edition. Kids sizes already in the line. Everything carries the signature.</p>'''
    p5 = f'''
<div class="k">The business</div>
<h2>Fourteen years of selling directly to New York</h2>
<div class="grid2">
  <div>
    <p class="lead">On September 26, 2012, PJ O'Rourke II wheeled a hand-built art cart onto an MTA subway platform and started selling his prints to whoever walked past. No connections, no capital, no permission.</p>
    <p>Born in Tulsa, he dropped out of college, landed on a friend's couch in Astoria with one month to figure it out, and built the cart from a single Home Depot trip, metal clips and chicken wire. The subway became his first gallery: raw, public and unforgiving. For eight years he sold directly to the public underground, refining the voice and building a following the hardest way possible.</p>
    <p>In 2014 the pop-ups started in DUMBO, and the prints became apparel on a used heat press. In 2019 he opened his first storefront in the East Village, at 11th Street and First Avenue. The shop, the online store and the Instagram have run ever since.</p>
  </div>
  <div>
    <div class="num">85,800</div><div class="k" style="margin:4px 0 14px">followers on Instagram, @pjorourkeii</div>
    <div class="num">2012</div><div class="k" style="margin:4px 0 14px">first sale, on a subway platform</div>
    <div class="num">2019</div><div class="k" style="margin:4px 0 14px">first storefront, East Village</div>
    <div class="rule"></div>
    <h3>What the brand is</h3>
    <ul>
      <li>New York lore, drawn by hand: the characters, the walk-ups, the hydrants, the platform edge.</li>
      <li>The platform-edge capsule, built on the yellow tactile strip every New Yorker knows underfoot.</li>
      <li>Gumbit, the character, going from the drawings to a figure.</li>
      <li>Pop-ups, drops and a store that people come to on purpose.</li>
    </ul>
  </div>
</div>
<img class="hero" src="img/CAM_178_front.jpg" style="height:3.0in;margin-top:10px">
<div class="cap">178 Lafayette Street from across the road.</div>'''
    p6 = f'''
<div class="k">Why 178 Lafayette</div>
<h2>Small, bright, and on the right street</h2>
<div class="grid2">
  <div>
    <p>A 700 square foot flagship on a corridor that people already walk is the format PJ has proved for a decade: tight, curated, built for content and conversation, with the stock downstairs and the window doing the work.</p>
    <p>The room needs almost nothing done to it. The tin ceiling, the tile and the white walls stay. The fit-out is freestanding: pipe-and-plank shelving, oak tables, frames on the wall. In and trading fast, out cleanly.</p>
    <p>The window is the sign. A four-foot pink figure facing Lafayette Street, lit at night, with the signature in white on the glass beside it.</p>
  </div>
  <div>
    <img class="hero" src="img/CAM_178_sidewalk.jpg" style="height:3.1in">
    <div class="cap">Along the sidewalk, from the north.</div>
  </div>
</div>
<div class="rule"></div>
<div class="grid3">
  <div><h3>Hours</h3><p>Seven days. Late on Thursday, Friday and Saturday, when Lafayette is busiest.</p></div>
  <div><h3>Events</h3><p>Print releases, tee drops, artist nights. The room clears to a gallery in an hour.</p></div>
  <div><h3>Online</h3><p>pjorourkeii.com and @pjorourkeii carry the store to the rest of the city and beyond.</p></div>
</div>
<div style="position:absolute;left:0.6in;right:0.6in;bottom:1.1in">
  <div class="k">Contact</div>
  <p class="lead" style="margin-top:4px"><b>PJ O'Rourke II</b> &nbsp; pjorourkeii.com &nbsp; @pjorourkeii</p>
</div>'''
    body = "".join(page(p, i + 1) for i, p in enumerate((p1, p2, p3, p4, p5, p6)))
    return f'<!doctype html><html><head><meta charset="utf-8"><title>PJ O\'Rourke II at 178 Lafayette</title><style>{CSS}</style></head><body>{body}</body></html>'

if __name__ == "__main__":
    stage_images()
    src = os.path.join(PDF_DIR, "178_lafayette.html"); open(src, "w").write(html()); print("wrote", src)
    out = os.path.join(OUT, "PJ_ORourke_II_178_Lafayette.pdf")
    if "--html" in sys.argv: sys.exit(0)
    r = subprocess.run(["node", PRINT, CHROME, src, out], capture_output=True, text=True, timeout=360)
    print(r.stdout[-400:], r.stderr[-400:]); print("pdf", out, os.path.exists(out) and os.path.getsize(out) // 1024, "KB")
