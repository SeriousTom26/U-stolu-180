"""Draw 180 original, offline SVG meal illustrations: no licenses, external URLs or API."""
import json, random, math, hashlib, html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LIB=json.loads((ROOT/'recipes/library.json').read_text(encoding='utf-8'))['recipes']
OUT=ROOT/'assets/img';OUT.mkdir(parents=True,exist_ok=True)

def shape_circle(x,y,r,fill,stroke='#00000010',opacity=1):return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="2" opacity="{opacity}"/>'
def ellipse(x,y,rx,ry,fill,rot=0,opacity=1):return f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{fill}" transform="rotate({rot:.0f} {x:.1f} {y:.1f})" opacity="{opacity}"/>'
def rect(x,y,w,h,fill,rx=10,rot=0):return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" transform="rotate({rot:.0f} {x+w/2:.1f} {y+h/2:.1f})"/>'

def draw(r):
 seed=int(hashlib.sha256(r['id'].encode()).hexdigest()[:12],16); rng=random.Random(seed)
 names={x['name'] for x in r['ingredients']}
 accent='#e2a655'
 if 'dýně Hokkaido' in names:accent='#ed9438'
 elif 'červená řepa' in names:accent='#a94d68'
 elif 'cuketa' in names:accent='#92a763'
 elif 'brokolice' in names:accent='#5d8b54'
 elif 'borůvky' in names:accent='#444a8c'
 elif 'meruňky' in names:accent='#f4ab5e'
 elif 'mrkev' in names:accent='#ef9750'
 elif 'brambory' in names:accent='#d8a95a'
 elif 'batáty' in names:accent='#e28c42'
 elif 'mozzarella' in names:accent='#e3d1a4'
 method=r['method']
 colors=['#e8b86d','#e4a04b','#d79c5e','#e8c184','#d79b60']
 out=[]
 bg=['#f1e8db','#e6ebe3','#ebdfd0','#e6e9ea','#f2e6de'][seed%5]
 out.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 600" width="960" height="600"><defs><radialGradient id="base"><stop offset="0" stop-color="#fffdf9"/><stop offset=".8" stop-color="#f6f3eb"/><stop offset="1" stop-color="#dbd8ce"/></radialGradient><radialGradient id="food"><stop offset="0" stop-color="{accent}"/><stop offset="1" stop-color="#c58a58"/></radialGradient><filter id="blur"><feGaussianBlur stdDeviation="12"/></filter><filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".03" numOctaves="2" seed="{seed%20}"/></filter><clipPath id="plateClip"><ellipse cx="485" cy="315" rx="335" ry="225"/></clipPath></defs>')
 out.append(f'<rect width="960" height="600" fill="{bg}"/>')
 out.append('<rect x="-100" y="95" width="1160" height="380" fill="#fff" opacity=".12" transform="rotate(-8 480 280)"/>')
 for i in range(12):
  x,y=rng.randint(0,960),rng.randint(0,600)
  out.append(ellipse(x,y,rng.randint(90,240),rng.randint(20,90),'#ffffff',rng.randint(-30,30),.05))
 out.append(ellipse(500,350,350,232,'#3f352b',-4,.18))
 out.append(ellipse(486,320,337,229,'#e5e0d8'))
 out.append(ellipse(485,312,326,217,'url(#base)'))
 out.append(ellipse(487,314,298,190,'#f7f4ed'))
 out.append('<g clip-path="url(#plateClip)">')
 if method in ['pancake','waffle','fritter','polenta','bake','muffin']:
  if method=='muffin':
   for j,(x,y) in enumerate([(355,235),(518,230),(410,360),(590,370)]):
    out.append(ellipse(x,y+28,72,50,'#b27b4b',-8))
    out.append(ellipse(x,y,72,51,colors[j%5],rng.randint(-10,10)))
    out.append(ellipse(x-10,y-8,55,35,'#f5d6a6',-8,.8))
  elif method=='waffle':
   for j,(x,y,angle) in enumerate([(385,270,-18),(570,345,18)]):
    out.append(rect(x-112,y-80,218,155,colors[j],24,angle))
    for gx in range(3):
     for gy in range(3):
      out.append(rect(x-82+gx*57,y-57+gy*42,42,27,'#bd833d',9,angle))
  elif method=='bake':
   for j,(x,y) in enumerate([(325,250),(520,230),(390,400),(585,382)]):
    out.append(rect(x-60,y-40,130,95,colors[j],14,rng.randint(-25,25)))
    out.append(rect(x-48,y-30,105,67,'#f5d8b1',15,rng.randint(-12,12)))
  else:
   for j in range(6):
    a=j*math.tau/6+rng.random()*.3
    x=485+185*math.cos(a); y=320+115*math.sin(a)
    fill=colors[j%5] if method!='polenta' else '#edd091'
    out.append(ellipse(x,y+8,79,50,'#7f5e3e',rng.randint(-25,25),.25))
    out.append(ellipse(x,y,81,51,fill,rng.randint(-25,25)))
    out.append(ellipse(x-9,y-9,54,28,'#f5d9a1',rng.randint(-25,25),.66))
 elif method=='soup':
  out.append(ellipse(482,320,255,164,'#dbd4c9'))
  out.append(ellipse(485,314,240,155,'#f4ead5'))
  out.append(ellipse(485,315,226,144,accent))
  out.append('<path d="M330 310c80-80 150 90 247-2 33-26 67-28 91-5" fill="none" stroke="#fff7d2" stroke-width="22" opacity=".63" stroke-linecap="round"/>')
  out.append('<path d="M365 340c105 52 155-80 235-15" fill="none" stroke="#fff9dc" stroke-width="13" opacity=".6" stroke-linecap="round"/>')
 elif method in ['rice','risotto','salad','veg']:
  out.append(ellipse(487,320,249,153,'#d8d0bc'))
  out.append(ellipse(487,310,241,148,'#f6ecd1'))
  for k in range(180):
   x=rng.uniform(270,706);y=rng.uniform(205,429)
   if ((x-487)/235)**2+((y-310)/142)**2>1: continue
   c= rng.choice(['#f2ebce','#e8e1c8','#fff8e9','#f9f0d6']) if method!='salad' else rng.choice(['#a2b87c','#7d9c63','#d7cc8b','#e4d7a2'])
   out.append(ellipse(x,y,rng.uniform(5,10),rng.uniform(2,4),c,rng.randint(-90,90)))
 elif method in ['pasta','noodles','gnocchi','balls']:
  if method in ['pasta','noodles']:
   for k in range(38):
    x=rng.uniform(275,680);y=rng.uniform(190,425)
    out.append(f'<path d="M {x:.1f} {y:.1f} q {rng.randint(-40,30)} -25 {rng.randint(30,70)} 14 t {rng.randint(-40,50)} {rng.randint(-12,35)}" stroke="{rng.choice(["#eecf8b","#f0d89f","#d5b477"])}" stroke-width="{rng.randint(10,16)}" fill="none" stroke-linecap="round"/>')
  else:
   for k in range(26):
    x=rng.uniform(280,690);y=rng.uniform(200,415)
    out.append(ellipse(x,y,rng.randint(17,32),rng.randint(11,24),rng.choice(['#ecd59d','#e6c584','#f1daa5']),rng.randint(-30,30)))
 elif method=='wrap':
  for k,(x,y,angle) in enumerate([(342,260,-30),(490,340,17)]):
   out.append(rect(x-98,y-38,260,96,'#c18751',42,angle))
   out.append(rect(x-96,y-43,260,92,'#eac98f',42,angle))
   for z in range(6):
    out.append(ellipse(x+rng.randint(-55,130),y+rng.randint(-15,30),rng.randint(9,20),rng.randint(6,12),'#8da95f',angle))
 elif method=='omelet':
  out.append(ellipse(486,314,240,145,'#b0773e'))
  out.append(ellipse(484,305,230,136,'#f0c568'))
  out.append(ellipse(463,293,175,98,'#f9d98b',-10,.55))
 elif method=='meat':
  out.append(ellipse(450,320,177,95,'#6a442f',-18))
  out.append(ellipse(448,308,176,92,'#c58859',-18))
  for k in range(25):
   x=rng.uniform(325,550); y=rng.uniform(240,360)
   out.append(ellipse(x,y,rng.randint(5,17),rng.randint(3,9),'#8e5737',rng.randint(-20,20),.6))
 elif method=='tray' or method=='potato':
  for k in range(28):
   x=rng.uniform(280,690);y=rng.uniform(210,420)
   out.append(rect(x-20,y-14,rng.randint(32,58),rng.randint(27,49),rng.choice(['#d29a62','#f0bc7d','#e9a95b','#e0c28b',accent]),9,rng.randint(-40,40)))
 else:
  for k in range(30):
   x=rng.uniform(280,690);y=rng.uniform(215,417)
   out.append(ellipse(x,y,24,15,accent,rng.randint(-20,20)))
 # Garnishes: distinguish by ingredients
 if 'borůvky' in names:
  for k in range(19):
   x=rng.uniform(310,655);y=rng.uniform(220,405)
   out.append(shape_circle(x,y,rng.randint(7,15),rng.choice(['#373f79','#47568f','#5d61a2'])))
 elif 'meruňky' in names or 'broskev' in names:
  for k in range(12):
   x=rng.uniform(320,660);y=rng.uniform(210,410)
   out.append(ellipse(x,y,rng.randint(13,23),rng.randint(9,17),'#f1a653',rng.randint(-35,35)))
 elif 'červená řepa' in names:
  for k in range(16):
   x=rng.uniform(320,655);y=rng.uniform(225,400)
   out.append(ellipse(x,y,rng.randint(15,26),rng.randint(10,18),'#9c476c',rng.randint(-40,40)))
 elif 'brokolice' in names:
  for k in range(17):
   x=rng.uniform(310,655);y=rng.uniform(225,390)
   out.append(shape_circle(x,y,rng.randint(10,22),'#568450'))
 elif 'cuketa' in names:
  for k in range(16):
   x=rng.uniform(315,660);y=rng.uniform(225,405)
   out.append(ellipse(x,y,rng.randint(16,27),rng.randint(9,16),'#89a366',rng.randint(-40,40)))
 elif 'mrkev' in names or 'dýně Hokkaido' in names:
  for k in range(19):
   x=rng.uniform(318,659);y=rng.uniform(230,400)
   out.append(ellipse(x,y,rng.randint(11,23),rng.randint(7,15),'#e89a44',rng.randint(-45,45)))
 # cheese light cream garnishes
 if any(n in names for n in ['tvaroh','ricotta','cottage','mozzarella','čerstvý kozí sýr','žervé']):
  for k in range(9):
   x=rng.uniform(335,645);y=rng.uniform(225,397)
   out.append(ellipse(x,y,rng.randint(11,24),rng.randint(8,16),'#fff7e6',rng.randint(-35,35),.95))
 # micro greens
 for k in range(25):
  x=rng.uniform(310,660);y=rng.uniform(227,393)
  out.append(ellipse(x,y,rng.randint(3,8),rng.randint(2,5),rng.choice(['#5c8457','#739862','#426d49']),rng.randint(-90,90),.85))
 out.append('</g>')
 out.append('<g opacity=".62"><text x="895" y="562" text-anchor="end" font-family="system-ui,Arial" font-size="17" font-weight="600" fill="#53626b">ILUSTRACE</text></g></svg>')
 (OUT/f'{r["id"]}.svg').write_text(''.join(out),encoding='utf-8')

for r in LIB:draw(r)
print(f'Generated {len(LIB)} local unique SVG illustrations')
