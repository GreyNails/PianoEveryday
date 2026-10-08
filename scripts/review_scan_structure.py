"""Source-specific scan layout readings; these do not certify note accuracy.

All numeric horizontal positions use 1280px-wide page previews. The connected
barline detector is restricted to the two engravings whose grand-staff bars
were checked to be continuous. An Jing has disconnected staff barlines.
"""
import cv2
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

DATE_BARS=[
 [[289.1,550.3,728.1,989.3,1154.3],[506.2,846.3,1186.5],[554,925.9,1186.5],[401.4,683,927.5,1184.9],[377.8,579.3,905.5,1184.9]],
 [[409.5,667.9,886.1,981.2,1156.9],[644.3,1186.5],[660.4,1186.5],[488.5,837.7,1186.5],[406.8,745.9,1093,1186.5]],
 [[417,611,920.5,1186.5],[419.1,672.2,966.2,1186.5],[665.8,1186.5],[643.2,1186.5]],
 [[668.5,1186.5],[495.4,852.8,1186.5],[559.9,803.4,1186.5],[439,746.4,1054.3,1184.9]],
]
EXPECTED={
 'qing-tian':[[4,2,2,2,2],[2]*6,[2,2,2,3,2],[2,2,2,2,2,1],[2]*5,[2]*5,[2,2,2,2,3]],
 'wo-ji-de':[[3,3,2,2,2],[2,3,3,3,2],[2]*6,[2,3,3,3,3],[3,2,2,2,2],[2]*5,[2]*5,[3,4]],
}

def connected_bars(sid,p):
    im=cv2.imread(str(ROOT/'scores'/sid/f"page-{p['page']+1}.png"),0)
    ink=cv2.dilate((im<175).astype(np.uint8),np.ones((1,3),np.uint8))
    scale=im.shape[1]/p['width'];out=[]
    for si,sy in enumerate(p['systems']):
        a=round(sy['staves'][0]['top']*scale);b=round(sy['staves'][1]['bottom']*scale)
        columns=np.where(ink[a:b].mean(axis=0)>.88)[0];runs=[]
        for x in columns:
            if runs and x==runs[-1][-1]+1:runs[-1].append(int(x))
            else:runs.append([int(x)])
        ends=[]
        for rr in runs:
            x=float(np.mean(rr))/im.shape[1]*1280
            if x<=sy['staves'][0]['left']/p['width']*1280+10:continue
            if ends and x-ends[-1]<10:ends[-1]=x  # final double bar
            else:ends.append(x)
        assert len(ends)==EXPECTED[sid][p['page']][si],(sid,p['page'],si,ends)
        out.append(ends)
    return out

def apply(sid,pages):
    if sid not in ('your-name-date','wo-ji-de','an-jing','qing-tian'):return []
    removed=[];layouts=[]
    # Every page was inspected: the symbols before these x positions are
    # clefs / key or time signatures, not sounded heads. Grace notes to the
    # right of the limits are retained.
    limits={'wo-ji-de':205,'an-jing':215,'qing-tian':253,'your-name-date':146}
    an_bars={(1,2):[440,686,920,1159],(1,3):[435,671,897,1159],(1,4):[456,700,928,1159],(2,0):[435,671,897,1159],(4,2):[489,800,1159],(4,4):[476,736,821,1161]}
    for p in pages:
        pi=p['page'];u=p['width']/1280
        if sid in EXPECTED:assert len(p['systems'])==len(EXPECTED[sid][pi]),('Missing staff system',sid,pi+1,len(p['systems']))
        detected=connected_bars(sid,p) if sid in EXPECTED else None
        for si,sy in enumerate(p['systems']):
            groups=[g for m in sy['measures'] for g in m['groups']]
            kept=[]
            for g in groups:
                reason=None
                if g['x']<limits[sid]*u:reason='clef-key-time-signature-area'
                # In these bass-clef melody passages the printed lowest note
                # is D-sharp 3. Lower candidates are beam/stem intersections,
                # not heads; this exclusion does not apply to other passages.
                bass_verse=sid=='wo-ji-de' and (pi==1 and (si==0 or si==1 and g['x']<820*u or si==4 and g['x']>633*u) or pi==2 or pi==3 and (si==0 or si==1 and g['x']<320*u))
                if bass_verse and g['staff']==sy['staves'][0]['index']:
                    st=sy['staves'][0]
                    valid=[]
                    for n in g['notes']:
                        if n['y']>st['bottom']-3.5*st['step']:
                            removed.append(dict(page=pi+1,x=n['x'],y=n['y'],reason='beam-below-printed-bass-clef-melody'))
                        else:valid.append(n)
                    if g['notes'] and not valid:continue
                    g['notes']=valid
                if reason:
                    removed.extend(dict(page=pi+1,x=n['x'],y=n['y'],reason=reason) for n in g['notes']);continue
                kept.append(g)
            ends=detected[si] if detected else DATE_BARS[pi][si] if sid=='your-name-date' else an_bars.get((pi,si))
            if ends is None:
                ends=[m['right']/u for m in sy['measures']]
                # The introductory time-signature block is not a bar.
                if sid=='an-jing' and ends[0]<225:ends.pop(0)
            bounds=[sy['staves'][0]['left']]+[x*u for x in ends]
            ms=[dict(left=a,right=b,groups=[]) for a,b in zip(bounds,bounds[1:])]
            for g in kept:
                mi=next((i for i,m in enumerate(ms) if g['x']<m['right']),len(ms)-1)
                ms[mi]['groups'].append(g)
            layouts.append(dict(page=pi+1,system=si+1,measures=len(ms),barlines=ends))
            sy['measures']=ms
    if sid=='an-jing':
        pages[4]['systems'][4]['measures'][2]['reviewedMeter']=1
        pages[4]['systems'][4]['measures'][3].update(reviewedMeter=4,reviewedKey=0)
    if sid=='your-name-date':
        pages[0]['systems'][0]['measures'][0]['reviewedMeter']=.5
        pages[0]['systems'][0]['measures'][1]['reviewedMeter']=4
        pages[0]['systems'][4]['measures'][2].update(reviewedMeter=3,reviewedTempo=63)
        pages[1]['systems'][1]['measures'][0].update(reviewedMeter=4,reviewedTempo=55)
        pages[1]['systems'][4]['measures'][3]['reviewedMeter']=1
        pages[2]['systems'][0]['measures'][0]['reviewedMeter']=4
        pages[3]['systems'][2]['measures'][1]['reviewedMeter']=1.5
        pages[3]['systems'][2]['measures'][2]['reviewedMeter']=3
    for p in pages:
        pi=p['page'];u=p['width']/1280;p['reviewedClefs']={};p['reviewedOctaves']=[]
        for si,sy in enumerate(p['systems']):
            r,l=[st['index'] for st in sy['staves']]
            rc=[(0,'G')];lc=[(0,'F')]
            if sid=='wo-ji-de':
                if pi==0 and si>=3 or pi==1 and si==0 or pi==2 or pi==3 and si==0:rc=[(0,'F')]
                if pi==1 and si==1:rc=[(0,'F'),(823*u,'G')]
                if pi==1 and si==4:rc=[(0,'G'),(550*u,'F')]
                if pi==3 and si==1:rc=[(0,'F'),(320*u,'G')]
                if pi==4 and si>=2 or pi==5 and si==0 or pi==7 and si==1:lc=[(0,'G')]
                if pi==7 and si==0:lc=[(0,'F'),(940*u,'G')]
                regions={(3,4):[(210,1035)],(4,0):[(210,864),(1142,1280)],(4,1):[(210,343),(653,775)],(4,2):[(210,977)],(4,3):[(210,1017)],(4,4):[(210,978)],(5,0):[(210,1177)]}
                p['reviewedOctaves'] += [(r,a*u,b*u,12) for a,b in regions.get((pi,si),[])]
            if sid=='your-name-date':
                v=p['width']/1191
                if pi==0 and si==0:lc=[(0,'G')]
                if pi==3 and si==1:lc=[(0,'F'),(780*v,'G')]
                if pi==3 and si>=2:lc=[(0,'G')]
                for page,row,staff,a,b,shift in [(0,3,l,0,1191,12),(0,4,l,0,496,12),(1,1,l,478,562,12),(3,3,r,991,1191,24)]:
                    if (pi,si)==(page,row):p['reviewedOctaves'].append((staff,a*v,b*v,shift))
            p['reviewedClefs'][r]=rc;p['reviewedClefs'][l]=lc
        if sid in ('wo-ji-de','your-name-date'):
            # These supplied editions contain no local chromatic accidentals.
            # The template detector was finding naturals/sharps in stems and
            # text. Keep the verified key (four sharps / C major) throughout.
            p['ignoreCandidateAccidentals']=True
    if sid in ('qing-tian','wo-ji-de'):
        # Last printed bar is a whole-measure rest on both staves.
        pages[-1]['systems'][-1]['measures'][-1]['groups']=[]
    return [dict(reason='按原谱重建小节边界，排除谱号调号和符杠误识别；核对换谱号及八度线。后续音符节奏仍需逐音校对。',layouts=layouts,excludedCandidates=removed,notation=[dict(page=p['page']+1,clefs=p['reviewedClefs'],octaves=p['reviewedOctaves']) for p in pages])]
