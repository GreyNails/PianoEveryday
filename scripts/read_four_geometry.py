"""Reproducible scan extraction and directly read missing Flower Dance heads."""
import copy,json
from pathlib import Path
import fitz
from read_raster_geometry import extract_page
from review_four_scan_rhythm import flower_layout,FLOWER
from review_scan_pulse import clusters,align_columns
ROOT=Path(__file__).resolve().parent.parent

def add_flower_heads(pages):
    reviewed=copy.deepcopy(pages);flower_layout(reviewed)
    rows=[(p,si,s,m) for p in reviewed for si,s in enumerate(p['systems']) for m in s['measures']]
    down=[13,12,9,6,6,5,2,-1];up=list(reversed(down))
    patterns={n:(down+up)*2 for n in (47,96,97,98,99)}
    patterns[48]=down+up+down;patterns[100]=down+up+up+down
    for n in (102,103):patterns[n]=(up+down)*2
    for number,steps in patterns.items():
        p,si,s,m=rows[number-1];st=s['staves'][0];expected=FLOWER[number]
        cols=clusters([g for g in m['groups'] if g['staff']==st['index'] and g['notes']],p,5)
        pairs=align_columns([x*1100/1050 for x,_ in cols],expected)
        for j,((px,b),step) in enumerate(zip(expected,steps)):
            if j in pairs.values():continue
            x=px*p['width']/1100;y=st['bottom']+st.get('slope',0)*x-step*st['step']
            note=dict(x=x,ox=x-st['step'],y=y,w=2*st['step'],c='\ue0a4',kind='filled',staff=st['index'],grace=False,manualHeadReading=True)
            raw=pages[p['page']]['systems'][si];target=next((v for v in raw['measures'] if v['left']<=x<v['right']),None)
            assert target is not None,(number,px)
            target['groups'].append(dict(staff=st['index'],stem=None,x=x,y=y,notes=[note],kind='note',duration=.125,direction='down',grace=False,beamIds=[],manualHeadReading=True))
            pages[p['page']].setdefault('manualNoteheadReadings',[]).append(dict(measure=number,hand='R',x=x,y=y,staffStep=step,kind='filled',beat=b,reason='逐组对照原谱三道符杠音阶，补回漏检三十二分音符。'))

def read(sid):
    assert sid in ('an-jing','flower-dance')
    ps=[]
    with fitz.open(ROOT/'scores'/sid/'original.pdf') as doc:
        for i,p in enumerate(doc):
            ps.append(extract_page(p,i,fit_staff_slopes=True,pitch_grid_tolerance=.48));print(sid,i+1,flush=True)
    if sid=='flower-dance':add_flower_heads(ps)
    (ROOT/'transcription'/sid/'geometry-candidates.json').write_text(json.dumps(ps,ensure_ascii=False)+'\n')
