# 178 Lafayette Street · PJ O'Rourke II

A micro site and a marketing PDF for PJ O'Rourke II's store at 178 Lafayette Street, SoHo: a 705 square foot storefront between Grand and Broome, with the shop drawn inside it.

Live page: https://feldtdesign-ship-it.github.io/lafayette-178/

## Build

All Blender work runs headless (Blender 5.0):

1. `build/build_178.py` — the block from NYC Open Data (`data/`), the three Lafayette fronts, and the white box → `build/lafayette_178.blend`
2. `build/fitout_178.py` — the shop: print wall, pipe-and-plank shelving, tables, the Gumbit figure, Galaga
3. `build/render_178.py` — Cycles plates
4. `build/export_glb_178.py` → `assets/lafayette_178.glb`
5. `python3 build/make_template_178.py && python3 build/build_page_178.py` → `index.html`, then `build/make_card.sh` → `og.jpg`
6. `python3 build/build_pdf_178.py` → `PJ_ORourke_II_178_Lafayette.pdf`

Model data: NYC building footprints, planimetric roadbed and sidewalk, street centerlines, street tree census. The store is drawn from the broker's plan and interior photograph.

© PJ O'Rourke II. All rights reserved.
