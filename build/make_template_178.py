"""make_template_178.py: builds build/laf178_template.html from the 527 page (west-27th-527/build/w27_template.html): same scroll-driven model,
with 178 Lafayette's words (laf178_body.html), model, camera path, 6-train green, and NO part two (no traffic numbers: this is a marketing page).
Michael 2026-10-15: "show off the model in the background a bit more, they seem to get a bit hidden" -> lighter scrim, narrower and more
see-through cards, two sections with slim cards, and the camera keeps the building in the open half of the screen."""
import os, re
S = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(S, '..', '..', 'west-27th-527', 'build', 'w27_template.html')).read()
head = src[:src.index('<style>')]; css = src[src.index('<style>'):src.index('</style>') + 8]
js = src[src.index('<script type="importmap">'):]      # the import map and the module script together
mid = src[src.index('</style>') + 8:src.index('<body>') + 6]      # the three.js import map lives between the style block and the body
def sub(s, pairs):
    for a, b in pairs:
        assert a in s, a[:80]; s = s.replace(a, b)
    return s
URL = 'https://feldtdesign-ship-it.github.io/lafayette-178/'
DESC = "PJ O'Rourke II at 178 Lafayette Street: a 705 square foot storefront between Grand and Broome, SoHo, with the shop drawn inside it. Prints on one wall, tees on the other, Gumbit in the window. The building, the space, the store, the work."
head = sub(head, [
 ('<title>Never Opened</title>', "<title>Jewel Box</title>"),
 ('https://feldtdesign-ship-it.github.io/west-27th-527/og.jpg', URL + 'og.jpg'),
 ('https://feldtdesign-ship-it.github.io/west-27th-527/', URL),
 ('527 West 27th Street · Never Opened', "178 Lafayette Street · PJ O'Rourke II"),
])
for k in ('name="description"', 'property="og:description"', 'name="twitter:description"'):
    head = re.sub(r'<meta ' + re.escape(k) + r' content="[^"]*">', f'<meta {k} content="{DESC}">', head)
# 6-train green back as the accent (Canal St / Spring St on the 6)
css = css.replace('--f:#C56BD3;--six:#B933AD;', '--f:#2DBE6C;--six:#00933C;')
# the model shows more: a lighter scrim, narrower and more see-through cards, a slim card variant
css = sub(css, [
 ('#scrim{position:fixed;inset:0;z-index:1;pointer-events:none;background:linear-gradient(90deg,rgba(20,18,16,.94) 0%,rgba(20,18,16,.72) 34%,rgba(20,18,16,.08) 60%,rgba(20,18,16,0) 100%);transition:background .5s}',
  '#scrim{position:fixed;inset:0;z-index:1;pointer-events:none;background:linear-gradient(90deg,rgba(20,18,16,.70) 0%,rgba(20,18,16,.38) 26%,rgba(20,18,16,0) 48%,rgba(20,18,16,0) 100%);transition:background .5s}'),
 ('#scrim.flip{background:linear-gradient(270deg,rgba(20,18,16,.94) 0%,rgba(20,18,16,.72) 34%,rgba(20,18,16,.08) 60%,rgba(20,18,16,0) 100%)}',
  '#scrim.flip{background:linear-gradient(270deg,rgba(20,18,16,.70) 0%,rgba(20,18,16,.38) 26%,rgba(20,18,16,0) 48%,rgba(20,18,16,0) 100%)}'),
 ('.wrap{width:min(580px,86vw)}', '.wrap{width:min(500px,84vw)}'),
 ('.card{background:rgba(30,27,24,.88);backdrop-filter:blur(6px);border-top:3px solid var(--f);padding:26px 28px}',
  '.card{background:rgba(30,27,24,.66);backdrop-filter:blur(5px);border-top:3px solid var(--f);padding:24px 26px}\n.card.slim{background:rgba(30,27,24,.5);backdrop-filter:blur(3px)}\n.card.slim p{font-size:15.5px}\n.strip{display:grid;grid-template-columns:repeat(7,1fr);gap:5px;margin-top:14px}.strip img{width:100%;aspect-ratio:11/14;object-fit:cover;border:1px solid var(--ink)}'),
])
js = sub(js, [
 ("const MODEL='assets/west_27th_527.glb';", "const MODEL='assets/lafayette_178.glb';"),
 ("const P=__POINTS__; const DOOR=P.door, N=P.facing;   // N = the way the glass faces, out over 27th Street (glTF x east, z south)",
  "const P=__POINTS__; const DOOR=P.door, N=P.facing;   // N = the way the storefront faces, out over Lafayette (glTF x east, z south)"),
 ("BOW=G('hudson_yards_7'), SPR=G('st23_ce'), GRD=G('highline_28'); const MID=[(BOW[0]+SPR[0]+GRD[0])/3,0,(BOW[2]+SPR[2]+GRD[2])/3];",
  "BOW=G('canal_6'), SPR=G('spring_6'), GRD=G('canal_rw'); const MID=[(BOW[0]+SPR[0]+GRD[0])/3,0,(BOW[2]+SPR[2]+GRD[2])/3];"),
 ("if(n.startsWith('CHELSEA_MASSING'))", "if(n.startsWith('SOHO_MASSING'))"),
])
# camera path: seven sections, the building kept in the open half (o slides the picture clear of the card). Sideways S = along the front.
a = js.index('const WP=['); b = js.index('];', a) + 2
js = js[:a] + """const S=[-N[1],0,N[0]];   // along the street, glTF
const WP=[
 {p:[330,470,330],t:[0,8,0],s:250,o:0},                                                                   // s0 wide, the blocks
 {p:[DOOR[0]+N[0]*60-S[0]*30,70,DOOR[2]+N[1]*60-S[2]*30],t:[DOOR[0],9,DOOR[2]],s:26,o:-.40},              // s1 the building, from over Lafayette (card right, picture left)
 {p:[DOOR[0]+N[0]*20+S[0]*6,7,DOOR[2]+N[1]*20+S[2]*6],t:[DOOR[0],2.8,DOOR[2]],s:11,o:.44},                // s2 the space, from the roadway, square on the glass (card left, picture right)
 {p:[DOOR[0]+N[0]*18+S[0]*12,5,DOOR[2]+N[1]*18+S[2]*12],t:[DOOR[0]-N[0]*3+S[0]*2,1.8,DOOR[2]-N[1]*3+S[2]*2],s:7,o:-.42}, // s3 the store, through the north window (the statue) from the roadway
 {p:[DOOR[0]+N[0]*18-S[0]*12,5,DOOR[2]+N[1]*18-S[2]*12],t:[DOOR[0]-N[0]*4-S[0]*3,1.8,DOOR[2]-N[1]*4-S[2]*3],s:7,o:.44},   // s4 the work, through the south window (the print wall) from the roadway
 {p:[DOOR[0]+N[0]*90+S[0]*60,120,DOOR[2]+N[1]*90+S[2]*60],t:[DOOR[0]-N[0]*10,12,DOOR[2]-N[1]*10],s:60,o:-.40}, // s5 the business, the block from the Grand St corner
 {p:[MID[0]+140,560,MID[2]+140],t:[MID[0]*0.5,0,MID[2]*0.5],s:300,o:0},                                   // s6 why here, from above with the stations
 {p:[420,560,420],t:[0,8,0],s:320,o:0}];                                                                  // out
""" + js[b:]
# materials: 178 cream with the storefront lit green, 176 red brick, 180 tan, the white box white, the fixtures in their colours
mat_a = js.index("   else if(n.startsWith('SITE_527')"); mat_b = js.index("   else if(n.startsWith('TREES'))")
js = js[:mat_a] + """   else if(n.startsWith('SITE_178')||n.startsWith('B178_LAFAYETTE_CREAM')||n.startsWith('B178_LAFAYETTE_BULKHEAD')){o.castShadow=true;if(m){m.color=new THREE.Color(0xD9CBA8);m.emissive=new THREE.Color(0xD9CBA8);m.emissiveIntensity=.32;}}
   else if(n.startsWith('SITE_176')||n.startsWith('B176_LAFAYETTE_REDBRICK')){o.castShadow=true;if(m){m.color=new THREE.Color(0x7E4A3A);m.emissive=new THREE.Color(0x7E4A3A);m.emissiveIntensity=.22;}}
   else if(n.startsWith('SITE_180')||n.startsWith('B180_LAFAYETTE_TAN')){o.castShadow=true;if(m){m.color=new THREE.Color(0xB89B72);m.emissive=new THREE.Color(0xB89B72);m.emissiveIntensity=.26;}}
   else if(n.startsWith('B180_LAFAYETTE_CASTIRON')){if(m){m.color=new THREE.Color(0x8E2F2A);m.emissive=new THREE.Color(0x8E2F2A);m.emissiveIntensity=.3;}}
   else if(n.startsWith('B178_LAFAYETTE_FIRE')){if(m){m.color=new THREE.Color(0x7A2A24);m.emissive=new THREE.Color(0x7A2A24);m.emissiveIntensity=.3;}}
   else if(n.includes('_SHOPGLASS')){if(m){m.color=new THREE.Color(0x2DBE6C);m.emissive=new THREE.Color(0x2DBE6C);m.emissiveIntensity=.55;m.transparent=true;m.opacity=.28;m.depthWrite=false;}}
   else if(n.startsWith('B178_IN_WHITE')||n.startsWith('B178_IN_TIN')){o.receiveShadow=true;if(m){m.color=new THREE.Color(0xECEAE4);m.emissive=new THREE.Color(0xECEAE4);m.emissiveIntensity=.45;}}
   else if(n.startsWith('B178_IN_FLOOR')){o.receiveShadow=true;if(m){m.color=new THREE.Color(0x9A9A96);m.emissive=new THREE.Color(0x9A9A96);m.emissiveIntensity=.3;}}
   else if(n.startsWith('B178_IN_')){if(m){m.color=new THREE.Color(0x3A3C40);m.emissive=new THREE.Color(0x3A3C40);m.emissiveIntensity=.2;}}
   else if(n.startsWith('UNIT_PLANK')||n.startsWith('TBL_TOP')||n.startsWith('WRAP_TOP')){if(m){m.color=new THREE.Color(0x9A7549);m.emissive=new THREE.Color(0x9A7549);m.emissiveIntensity=.35;}}
   else if(n.startsWith('UNIT_')||n.startsWith('TBL_LEG')||n.startsWith('GAL_FR')){if(m){m.color=new THREE.Color(0x1A1A1A);}}
   else if(n.startsWith('GAL_MAT')){if(m){m.color=new THREE.Color(0xE6E1D3);m.emissive=new THREE.Color(0xE6E1D3);m.emissiveIntensity=.5;}}
   else if(n.startsWith('GAL_PRINT')){if(m){m.emissive=new THREE.Color(0xFFFFFF);m.emissiveIntensity=.35;m.emissiveMap=m.map||null;}}
   else if(n.startsWith('PLINTH_')||n.startsWith('PEDESTAL_')||n.startsWith('WRAP_BODY')){if(m){m.color=new THREE.Color(0x0E0E0E);}}
   else if(n.startsWith('FOLD_')){if(m){m.emissive=m.color.clone();m.emissiveIntensity=.45;}}
   else if(n.startsWith('B178_')||n.startsWith('B176_')||n.startsWith('B180_')){if(m){m.color=new THREE.Color(0x121212);m.transparent=false;m.opacity=1;}}
""" + js[mat_b:]
# no part two: the numbers block is an empty div after the footer, so the scrim/mast only fade at the very end
js = js.replace("cam.top=state.s; cam.bottom=-state.s;", "cam.top=state.s; cam.bottom=-state.s; cam.near=state.s<20?0.5:-3000;")   # close shots: clip behind the camera
js = js.replace("scrim.className=(n===4||n===5)?'top':(s.querySelector('.wrap.right')?'flip':'');", "scrim.className=(n===6)?'top':(s.querySelector('.wrap.right')?'flip':'');")
body = open(os.path.join(S, 'laf178_body.html')).read()
open(os.path.join(S, 'laf178_template.html'), 'w').write(head + css + mid + '\n' + body + js)
print('template written', len(head + css + body + js) // 1024, 'KB')
