"""Re-extract Jue Bie Shu with visually checked staff and measure boundaries."""
import json
from pathlib import Path
import fitz
from read_raster_geometry import extract_page
ROOT=Path(__file__).resolve().parent.parent

def add_read_heads(pages):
    """Explicit heads visible in the supplied PDF but missed on ledger lines."""
    rows=[(p,s,m) for p in pages for s in p['systems'] for m in s['measures']]
    readings=[(47,'R',920,[18],'filled',1/16),(47,'R',941,[19],'filled',.25),
              (29,'R',260,[8],'hollow',3),
              (50,'L',586,[20],'filled',1/6),
              (58,'L',772,[-1,-3],'filled',.25),(63,'L',229,[7],'filled',.25),(65,'L',708,[6],'filled',.25),
              (87,'R',177,[16],'filled',.25),(87,'R',443,[17],'filled',.25),
              (57,'R',482,[-8],'filled',1/6),(57,'R',559,[-8],'filled',1/6),
              (99,'R',515,[1,2,5,7],'whole',4),
              (99,'L',732,[12],'filled',.25),(99,'L',837,[17],'filled',.25),
              (100,'R',880,[6],'whole',4)]
    for number,hand,x,steps,kind,duration in readings:
        p,sy,m=rows[number-1];st=sy['staves'][hand=='L'];x=x*p['width']/1100
        notes=[]
        for step in steps:
            y=st['bottom']+st.get('slope',0)*x-step*st['step']
            note=dict(x=x,ox=x-st['step'],y=y,w=2*st['step'],c='\ue0a2' if kind=='whole' else '\ue0a4',kind=kind,staff=st['index'],grace=False,manualHeadReading=True)
            notes.append(note)
            p.setdefault('manualNoteheadReadings',[]).append(dict(measure=number,hand=hand,x=x,y=y,staffStep=step,kind=kind))
        m['groups'].append(dict(staff=st['index'],stem=None,x=x,y=notes[0]['y'],notes=notes,kind='note',duration=duration,direction='none',grace=False,beamIds=[],manualHeadReading=True))

def read():
    layout=json.loads((Path(__file__).parent/'jue-scan-layout.json').read_text());out=[]
    with fitz.open(ROOT/'scores/jue-bie-shu/original.pdf') as doc:
        for pi,page in enumerate(doc):
            layout_page=layout[pi]
            p=extract_page(page,pi,[st for s in layout_page['systems'] for st in s['staves']],fit_staff_slopes=pi>0,pitch_grid_tolerance=.48 if pi>0 else .27)
            assert len(p['systems'])==len(layout_page['systems'])
            for sy,source in zip(p['systems'],layout_page['systems']):
                groups=[g for m in sy['measures'] for g in m['groups']]
                bounds=source['bounds']
                sy['measures']=[dict(left=a,right=b,groups=[g for g in groups if a<g['x']<b]) for a,b in zip(bounds,bounds[1:])]
            if pi==0:
                first=p['systems'][0]['measures'];left=first[0]['left'];first.pop(0);first[0]['left']=left
            out.append(p);print('Jue',pi+1,sum(len(g['notes']) for s in p['systems'] for m in s['measures'] for g in m['groups']),flush=True)
    add_read_heads(out)
    (ROOT/'transcription/jue-bie-shu/geometry-candidates.json').write_text(json.dumps(out,ensure_ascii=False)+'\n')

if __name__=='__main__':read()
