"""Collect printed Opus note coordinates for the manually read Call of Silence edition.

This only records glyph locations and written pitch candidates.
Rhythms, voices, octave lines and ties are supplied by the separate visual reading.
"""
import fitz,json,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
doc=fitz.open(ROOT/'scores/call-of-silence/original.pdf')
result=[]; number=0
NAMES=['C','D','E','F','G','A','B'];STEPS=[0,2,4,5,7,9,11]
for pi,page in enumerate(doc):
 ds=page.get_drawings();lines=sorted(set(round(d['rect'].y0,3) for d in ds if d['rect'].width>350 and d['rect'].height<.02))
 staves=[dict(top=lines[i],bottom=lines[i+4],step=(lines[i+4]-lines[i])/8) for i in range(0,len(lines),5)]
 chars=[]
 for b in page.get_text('rawdict')['blocks']:
  for l in b.get('lines',[]):
   for s in l['spans']:
    if s['font']=='OpusStd':
     chars.extend(dict(c=c['c'],x=c['origin'][0],y=c['origin'][1],size=s['size']) for c in s['chars'] if c['c']!=' ')
 for c in chars:c['staff']=min(range(len(staves)),key=lambda j:abs((staves[j]['top']+staves[j]['bottom'])/2-c['y']))
 start=0
 for sy,count in enumerate(([3,3,2,2,2] if pi==0 else [2,2,2,2])):
  ss=staves[start:start+count];top=ss[0]['top'];bottom=ss[-1]['bottom']
  bars=sorted(set(round(d['rect'].x0,3) for d in ds if d['rect'].width<.1 and abs(d['rect'].y0-top)<1 and abs(d['rect'].y1-bottom)<1))
  bars=[b for i,b in enumerate(bars) if i==0 or b-bars[i-1]>3]
  for left,right in zip(bars,bars[1:]):
   number+=1;m=dict(number=number,page=pi,system=sy,left=left,right=right,top=top,bottom=bottom,staves=[])
   for j,st in enumerate(ss):
    sc=[c for c in chars if c['staff']==start+j]
    clefs=[c for c in sc if c['c'] in ['&','?']]
    def dia(c):
     cs=[v for v in clefs if v['x']<c['x']]
     clef=max(cs,key=lambda v:v['x'])['c'] if cs else ('?' if j==count-1 else '&')
     return (30 if clef=='&' else 18)+round((st['bottom']-c['y'])/st['step'])
    notes=sorted([c.copy() for c in sc if c['c'] in ['œ','˙','w'] and left<c['x']<right],key=lambda c:(c['x'],c['y']))
    states={}; accs=sorted([c for c in sc if c['c'] in ['#','b','n','N'] and left<c['x']<right],key=lambda c:c['x'])
    firstx=min([n['x'] for n in notes],default=right)
    # Header key signature, three sharps; later accidentals remain local.
    if left==bars[0]:accs=[a for a in accs if not(a['c']=='#' and a['x']<firstx-8)]
    for n in notes:
     for a in accs:
      if not a.get('done') and a['x']<n['x'] and abs(a['y']-n['y'])<1 and n['x']-a['x']<20:
       states[dia(n)]={'#':1,'b':-1,'n':0,'N':0}[a['c']];a['done']=True
     d=dia(n);octave,degree=divmod(d,7);alter=states.get(d,1 if degree in [0,3,4] else 0)
     n.update(midi=12*(octave+1)+STEPS[degree]+alter,pitch=NAMES[degree]+('#' if alter==1 else 'b' if alter==-1 else '')+str(octave))
    groups=[]
    for n in notes:
     if groups and abs(n['x']-groups[-1]['x'])<.6:groups[-1]['notes'].append(n)
     else:groups.append(dict(x=n['x'],notes=[n]))
    m['staves'].append(dict(**st,groups=groups))
   result.append(m)
  start+=count
out=ROOT/'transcription/call-of-silence/geometry.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2))
for m in result:
 print('M',m['number'],'page',m['page']+1,'sys',m['system']+1)
 for i,st in enumerate(m['staves']):
  print(i,' '.join(str(k)+':'+','.join(n['pitch']+n['c'] for n in g['notes']) for k,g in enumerate(st['groups'])))
