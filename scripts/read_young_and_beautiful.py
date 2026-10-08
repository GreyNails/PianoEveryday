"""Rebuild visually reviewed Young and Beautiful glyph/rhythm evidence.

Source-specific layout checks accompany review of all five PDF pages.
"""
import fitz,sys,json
from pathlib import Path
root=Path(__file__).resolve().parent.parent
from read_vector_geometry import extract_page
ps=[extract_page(p,i,'young-and-beautiful') for i,p in enumerate(fitz.open(root/'scores/young-and-beautiful/original.pdf'))]
# Visually checked ledger-note ownership in the final two systems.
all_measures=[m for p in ps for sy in p['systems'] for m in sy['measures']]
# The last low G1 in bar 60 belongs to LH, not the next system's RH.
m63=all_measures[62]
low=[g for g in m63['groups'] if g['notes'] and g['y']<530]
assert len(low)==1
for g in low:
 m63['groups'].remove(g);g['staff']=7
 for n in g['notes']:n['staff']=7
 all_measures[59]['groups'].append(g)
all_measures[59]['groups'].sort(key=lambda g:g['x'])
m108=all_measures[107]
misplaced=[g for g in m108['groups'] if g['notes'] and g['y']>630]
assert len(misplaced)==1
for g in misplaced:
 m108['groups'].remove(g);g['staff']=10
 for n in g['notes']:n['staff']=10
 all_measures[111]['groups'].append(g)
for g in m108['groups']:
 if 575<g['y']<585:
  g['staff']=9
  for n in g['notes']:n['staff']=9
all_measures[111]['groups'].sort(key=lambda g:g['x'])
# The low C1 natural in bar 87 is below the staff midpoint boundary.
for c in ps[3]['chars']:
 if c['c']=='\ue261' and 315<c['ox']<325 and 650<c['y']<662:c['staff']=9
num=0;bad=[]
for p in ps:
 for s in p['systems']:
  for m in s['measures']:
   num+=1;m['number']=num
   columns=[]
   for g in m['groups']:
    if g['grace']:continue
    displaced=columns and abs(g['x']-columns[-1]['x'])<9.5 and any(g['staff']==h['staff'] and {g['direction'],h['direction']}=={'up','down'} for h in columns[-1]['groups'])
    if columns and (abs(g['x']-columns[-1]['x'])<2.8 or displaced or (len(columns)==1 and abs(g['x']-columns[-1]['x'])<10)):columns[-1]['groups'].append(g)
    else:columns.append(dict(x=g['x'],groups=[g]))
   clock=0;active=[]
   for col in columns:
    for g in col['groups']:g['localBeat']=clock;active.append(clock+g['duration'])
    col['beat']=clock;clock=min(a for a in active if a>clock+1e-6);active=[a for a in active if a>clock+1e-6]
   total=max([g.get('localBeat',0)+g['duration'] for g in m['groups'] if not g['grace']],default=0)
   if num==104:
    # Bracketed quarter-note triplets in RH; half + quarter triplet in LH.
    for g in m['groups']:
     if g['x']>510:
      if g['staff']%2==0:
       g['localBeat']=2+(0 if g['x']<523 else 1 if g['x']<540 else 2)*2/3
       g['duration']=2/3
      elif g['duration']==2:g['localBeat']=2;g['duration']=4/3
      else:g['localBeat']=10/3;g['duration']=2/3
    total=max(g['localBeat']+g['duration'] for g in m['groups'])
   m['rawDuration']=total;m['columns']=columns
   if abs(total-4)>.001:bad.append((num,total,p['page']+1,s['local']+1))
print(num,'measures',len(bad),'non4',bad)
for p in ps:
 for s in p['systems']:
  for m in s['measures']:
   if m['number'] in [x[0] for x in bad]:print(m['number'],[(round(c['x'],1),c['beat'],[(g['staff']%2,g['kind'],g['direction'],g['duration'],[n['c'] for n in g['notes']]) for g in c['groups']]) for c in m['columns']])
(root/'transcription/young-and-beautiful').mkdir(exist_ok=True)
assert not bad,bad
(root/'transcription/young-and-beautiful/geometry.json').write_text(json.dumps(ps,ensure_ascii=False))
