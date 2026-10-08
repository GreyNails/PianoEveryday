"""Explicit notehead readings missed by the raster detector.

Pitch positions are staff half-space steps above the bottom line. These are
annotations on the supplied PDF, not inferred harmony or generated bass.
"""
from review_scan_structure import apply as layout
import copy

def apply(sid,pages):
    if sid!='wo-ji-de':return
    # bar: hand, preview x, diatonic positions, head kind, duration.
    specs={
      17:[('R',745,[11],'hollow',2)],
      24:[('R',184,[0],'whole',4)],
      32:[('R',184,[5],'whole',4)],
      52:[('R',184,[9,2],'whole',4)],
      56:[('R',627,[7,0],'whole',4)],
      76:[('R',659,[7,0],'whole',4)],
      84:[('R',541,[14,7],'whole',4)],
      88:[('R',693,[7,2],'whole',4),('L',693,[0,-7],'whole',4)],
    }
    # Find the raw system through a layout copy, retaining raw evidence order.
    reviewed=copy.deepcopy(pages);layout(sid,reviewed);number=0
    for p in reviewed:
      for si,s in enumerate(p['systems']):
       for m in s['measures']:
        number+=1
        for hand,x,steps,kind,duration in specs.get(number,[]):
            st=s['staves'][0 if hand=='R' else 1];x=x*p['width']/1050
            raw=pages[p['page']]['systems'][si]
            target=next((v for v in raw['measures'] if v['left']<x<v['right']),None)
            assert target is not None,(number,x)
            notes=[]
            for degree in steps:
                y=round(st['bottom']-degree*st['step'],3)
                n=dict(x=round(x,3),ox=x-st['step']*1.2,y=y,w=st['step']*2.4,c='\ue0a2' if kind=='whole' else '\ue0a3',kind=kind,staff=st['index'],grace=False,manualHeadReading=True)
                notes.append(n)
                pages[p['page']].setdefault('manualNoteheadReadings',[]).append(dict(measure=number,hand=hand,x=n['x'],y=y,staffStep=degree,kind=kind))
            target['groups'].append(dict(staff=st['index'],stem=None,x=x,y=notes[0]['y'],notes=notes,kind='note',duration=duration,direction='none',grace=False,beamIds=[],manualHeadReading=True))
