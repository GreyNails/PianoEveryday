"""Local, inspectable notehead detection for scanned PDF pages.

Produces visual evidence and candidates, never a claim of reviewed transcription.
All positions are PDF points. No generated melody or audio-to-score substitution.
"""
import cv2, fitz, numpy as np, json, argparse
from pathlib import Path
from music_symbol_templates import templates
ROOT=Path(__file__).resolve().parent.parent

def runs(values):
    groups=[]
    for v in values:
        if groups and v<=groups[-1][-1]+1:groups[-1].append(int(v))
        else:groups.append([int(v)])
    return groups

def extract_page(page,pi,staves_override=None,fit_staff_slopes=False,pitch_grid_tolerance=.27):
    scale=1800/page.rect.width
    pm=page.get_pixmap(matrix=fitz.Matrix(scale,scale),colorspace=fitz.csGRAY)
    gray=np.frombuffer(pm.samples,np.uint8).reshape(pm.height,pm.width)
    ink=(gray<190).astype(np.uint8)
    hor=cv2.morphologyEx(ink,cv2.MORPH_OPEN,np.ones((1,max(50,int(pm.width*.04))),np.uint8))
    row=hor.sum(axis=1);ys=[float(np.average(g,weights=row[g])) for g in runs(np.where(row>pm.width*.20)[0])]
    # Compare complete five-line candidates before accepting any of them.
    # A beam followed by four staff lines must lose to the five actual lines.
    # A high global threshold alone loses faint staves on scanned page 6.
    proposals=[]
    for yi,y in enumerate(ys):
        for last in ys[yi+4:yi+10]:
            gap=(last-y)/4
            if not 7<gap<32:continue
            seq=[min(ys,key=lambda v:abs(v-y-gap*j)) for j in range(5)]
            if any(abs(v-y-gap*j)>max(1.5,gap*.18) for j,v in enumerate(seq)):continue
            strengths=[row[max(0,round(v)-1):round(v)+2].max() for v in seq]
            proposals.append((min(strengths)+sum(strengths)*.1,seq,gap))
    accepted_staves=[];used=set()
    for strength,seq,gap in sorted(proposals,key=lambda v:-v[0]):
        if any(v in used for v in seq):continue
        if any(not(seq[-1]<old[0] or seq[0]>old[-1]) for old,_ in accepted_staves):continue
        accepted_staves.append((seq,gap));used.update(seq)
    staves=[]
    for seq,gap in sorted(accepted_staves,key=lambda v:v[0][0]):
        support=np.where(np.maximum.reduce([hor[max(0,round(v)-2):round(v)+3].max(axis=0) for v in seq])>0)[0]
        if not len(support):continue
        staves.append(dict(index=len(staves),top=seq[0]/scale,bottom=seq[-1]/scale,center=seq[2]/scale,step=gap/scale/2,left=float(support.min())/scale,right=float(support.max())/scale))
    if staves_override is not None:
        import copy
        staves=copy.deepcopy(staves_override)
    if not staves:return dict(page=pi,width=page.rect.width,height=page.rect.height,systems=[],chars=[],texts=[],ties=[],tuplets=[],issues=['No five-line staff detected (possibly a cover page).'])
    if fit_staff_slopes:
        # Slight scan skew moves ledger notes off a constant-y pitch grid.
        # Fit all five ink lines together, rejecting beam/head outliers.
        for st in staves:
            sg=st['step']*2*scale;design=[];observed=[]
            for x in range(round(st['left']*scale)+50,round(st['right']*scale)-40,50):
                for k in range(5):
                    center=(st['top']+st['step']*2*k)*scale
                    a=round(center-sg*.48);b=round(center+sg*.48)+1
                    strength=hor[a:b,x:x+40].mean(axis=1)
                    if strength.max()<.5:continue
                    design.append([1,(x+20)/scale,(k-4)*2]);observed.append((a+np.argmax(strength))/scale)
            X=np.array(design);y=np.array(observed)
            assert len(y)>20,('Insufficient staff-line evidence',pi,st['index'])
            co=np.linalg.lstsq(X,y,rcond=None)[0]
            for _ in range(3):
                keep=np.abs(X@co-y)<sg/scale*.15
                co=np.linalg.lstsq(X[keep],y[keep],rcond=None)[0]
            bottom,slope,step=map(float,co)
            st.update(bottom=bottom,top=bottom-8*step,center=bottom-4*step,step=step,slope=slope)
    gaps=[s['step']*2*scale for s in staves];gap=float(np.median(gaps))
    # Repair the body of a note crossed by a staff line, preserving holes.
    # The horizontal morphology also finds long beams. Erasing every result
    # used to erase those beams before counting flags. Remove staff lines only.
    staff_mask=np.zeros_like(hor)
    for st in staves:
        for y in np.linspace(st['top']*scale,st['bottom']*scale,5):
            a=max(0,round(y)-2);b=min(pm.height,round(y)+3)
            if st.get('slope'):
                xx=np.arange(pm.width);yy=np.round(y+st['slope']*xx).astype(int)
                for offset in range(-2,3):
                    rr=np.clip(yy+offset,0,pm.height-1);staff_mask[rr,xx]=hor[rr,xx]
            else:staff_mask[a:b]=hor[a:b]
    clean=ink.copy();clean[staff_mask>0]=0
    for g in runs(np.where(staff_mask.sum(axis=1)>pm.width*.20)[0]):
        a,b=max(0,g[0]-1),min(pm.height-1,g[-1]+1)
        preserve=ink[a]&ink[b]
        clean[g[0]:g[-1]+1]|=preserve
    candidates=[]
    symbols=[]
    # Small rectangular rest templates must not match a long intact beam.
    symbol_clean=ink.copy();symbol_clean[hor>0]=0
    for g in runs(np.where(hor.sum(axis=1)>pm.width*.20)[0]):
        a,b=max(0,g[0]-1),min(pm.height-1,g[-1]+1)
        symbol_clean[g[0]:g[-1]+1]|=ink[a]&ink[b]
    for meta,template in templates():
        factor=gap/meta['gap'];tw=max(3,round(template.shape[1]*factor));th=max(3,round(template.shape[0]*factor))
        template=cv2.resize(template.astype(np.float32),(tw,th))
        result=cv2.matchTemplate(symbol_clean.astype(np.float32),template,cv2.TM_CCOEFF_NORMED)
        maxima=cv2.dilate(result,np.ones((max(3,int(gap)),max(3,int(gap*.5))),np.uint8))
        yy,xx=np.where((result==maxima)&(result>.69))
        for a,b in zip(yy,xx):
            x=b+meta['ox']*factor;y=a+meta['oy']*factor
            st=min(staves,key=lambda s:abs((s['center']+s.get('slope',0)*x/scale)*scale-y))
            if not st['left']*scale+gap*.4<x<st['right']*scale or abs(y-st['center']*scale)>gap*6:continue
            symbols.append(dict(c=meta['symbol'],ox=x/scale,y=y/scale,w=tw/scale,staff=st['index'],confidence=float(result[a,b])))
    chars=[]
    for c in sorted(symbols,key=lambda c:-c['confidence']):
        if any(c['c']==a['c'] and abs(c['ox']-a['ox'])<gap/scale*.6 and abs(c['y']-a['y'])<gap/scale*.6 for a in chars):continue
        chars.append(c)
    # Dense chords have no white border between adjacent heads. Use the black
    # interior as additional evidence without requiring that white border.
    kh=max(3,round(gap*.45));kw=max(5,round(gap*.85))
    kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(kw,kh))
    core=cv2.erode(clean,kernel)
    count,labels,stats,centroids=cv2.connectedComponentsWithStats(core)
    for label in range(1,count):
        xx,yy,ww,hh,area=stats[label]
        x,y=centroids[label];st=min(staves,key=lambda s:abs((s['center']+s.get('slope',0)*x/scale)*scale-y))
        ledger=y<st['top']*scale-gap*.6 or y>st['bottom']*scale+gap*.6
        # Ledger strokes join the filled head and enlarge its eroded core.
        # The former one-space width cutoff deleted complete bass octaves.
        if ww>gap*(1.5 if ledger else 1) or hh>gap*(1.5 if ledger else 1.1):continue
        if x<st['left']*scale+gap*2.2 or x>st['right']*scale-gap*.3 or abs(y-st['center']*scale)>gap*7:continue
        candidates.append(dict(x=x/scale,y=y/scale,kind='filled',confidence=.78,staff=st['index']))
    # Multiple notehead sizes accommodate scanned and slightly reduced cues.
    for kind in ('filled','hollow'):
        for fac in (.9,1,1.1):
            h=max(7,int(round(gap*1.22*fac)));w=max(11,int(round(gap*1.72*fac)))
            templ=np.zeros((h,w),np.uint8)
            cv2.ellipse(templ,(w//2,h//2),(max(2,int(gap*.66*fac)),max(2,int(gap*.38*fac))),-20,0,360,1,-1)
            if kind=='hollow':cv2.ellipse(templ,(w//2,h//2),(max(2,int(gap*.43*fac)),max(1,int(gap*.17*fac))),-20,0,360,0,-1)
            result=cv2.matchTemplate(clean.astype(np.float32),templ.astype(np.float32),cv2.TM_CCOEFF_NORMED)
            maxima=cv2.dilate(result,np.ones((max(3,int(gap*.55)),max(3,int(gap*.8))),np.uint8))
            yy,xx=np.where((result==maxima)&(result>(.66 if kind=='filled' else .60)))
            for a,b in zip(yy,xx):
                x,y=b+w/2,a+h/2
                st=min(staves,key=lambda s:abs((s['center']+s.get('slope',0)*x/scale)*scale-y))
                if x<st['left']*scale+gap*2.2 or x>st['right']*scale-gap*.3 or abs(y-st['center']*scale)>gap*7:continue
                candidates.append(dict(x=x/scale,y=y/scale,kind=kind,confidence=float(result[a,b]),staff=st['index']))
    notes=[]
    for n in sorted(candidates,key=lambda n:-n['confidence']):
        if any(abs(n['x']-m['x'])<gap/scale*.65 and abs(n['y']-m['y'])<gap/scale*.37 for m in notes):continue
        notes.append(n)
    # Stem evidence rejects round letters, dynamics and dots. Whole notes are
    # retained only when a hollow notehead also lies on the half-space grid.
    vertical=cv2.morphologyEx(ink,cv2.MORPH_OPEN,np.ones((max(8,int(gap*2.3)),1),np.uint8))
    accepted=[]
    # Augmentation dots are isolated compact ink components to the right of
    # a head. Without them dotted eighth/quarter bass figures acquire holes.
    cc,_,boxes,centers=cv2.connectedComponentsWithStats(ink)
    dots=[centers[i] for i in range(1,cc) if gap*.10<=boxes[i,2]<=gap*.48 and gap*.10<=boxes[i,3]<=gap*.48 and gap*gap*.018<=boxes[i,4]<=gap*gap*.20 and .45<=boxes[i,2]/boxes[i,3]<=2.1]
    for n in notes:
        x,y=n['x']*scale,n['y']*scale;st=staves[n['staff']];stgap=st['step']*2*scale
        grid=abs(((st['bottom']+st.get('slope',0)*x/scale)*scale-y)/(stgap/2)-round(((st['bottom']+st.get('slope',0)*x/scale)*scale-y)/(stgap/2)))
        if grid>pitch_grid_tolerance:continue
        possible=[]
        for side in (-1,1):
            sx=int(round(x+side*stgap*.58));a=max(0,sx-2);b=min(pm.width,sx+3);yy=int(round(y))
            region=vertical[max(0,yy-int(stgap*4)):min(pm.height,yy+int(stgap*4)),a:b]
            if region.size and region.sum()>stgap*2:possible.append((region.sum(),side,sx))
        if not possible:
            if n['kind']!='hollow' or n['confidence']<.69:continue
            n.update(duration=4,direction='none',stem=None)
        else:
            _,side,sx=max(possible);direction='up' if side==1 else 'down';yy=int(round(y))
            # Ledger-line arpeggios can have stems over five spaces long.
            # Cutting that stem window before its beam turns eighths into
            # quarters and makes the compiler compress a whole bar unevenly.
            stem_window=int(stgap*12)
            col=vertical[max(0,yy-stem_window):min(pm.height,yy+stem_window),max(0,sx-2):sx+3].max(axis=1)
            base=max(0,yy-stem_window);parts=runs(np.where(col>0)[0]);parts=[g for g in parts if base+g[0]<=y+stgap*.7 and base+g[-1]>=y-stgap*.7]
            if not parts:continue
            part=max(parts,key=len);tip=base+(part[0] if direction=='up' else part[-1])
            # Count beam stripes just inside the stem, at its far endpoint.
            bx=int(sx+(1 if direction=='up' else -1)*stgap*.8)
            a=max(0,int(min(tip,tip+(stgap*1.6 if direction=='up' else -stgap*1.6))));b=min(pm.height,int(max(tip,tip+(stgap*1.6 if direction=='up' else -stgap*1.6)))+1)
            levels=0
            # Staff lines are not beams; inspect both sides for the last note
            # of a beamed group as well as the first note.
            for bx in (int(sx+stgap*.8),int(sx-stgap*.8)):
                band=clean[a:b,max(0,bx-1):min(pm.width,bx+2)]
                count=len([g for g in runs(np.where(band.mean(axis=1)>.65)[0]) if len(g)>stgap*.12]) if band.size else 0
                levels=max(levels,count)
            duration=2 if n['kind']=='hollow' else 2**(-min(levels,3))
            n.update(duration=duration,direction=direction,stem=round(sx/scale,1),tip=tip/scale)
        if any(stgap*.7<dx-x<stgap*1.9 and abs(dy-y)<stgap*.60 for dx,dy in dots):
            n['duration']*=1.5;n['dotted']=True
        n['x']=round(n['x'],3);n['y']=round(n['y'],3);accepted.append(n)
    systems=[]
    for i in range(0,len(staves)-1,2):
        pair=staves[i:i+2];top=pair[0]['top'];bottom=pair[1]['bottom']
        # A barline must cross all five lines of at least one staff, and must
        # not simply be a note stem. Empty measures remain in the evidence.
        bar_candidates=[]
        wide_ink=cv2.dilate(ink,np.ones((1,3),np.uint8))
        for st in pair:
            a=int(round(st['top']*scale));b=int(round(st['bottom']*scale));cols=wide_ink[a:b+1].mean(axis=0)
            for rr in runs(np.where(cols>.87)[0]):
                x=float(np.mean(rr))/scale
                if st['left']-1<=x<=st['right']+1:bar_candidates.append((x,st['index']))
        barxs=[]
        for x,st in bar_candidates:
            # Shared x on both staves is required: a single staff's note stem
            # is not enough evidence for a barline in a scanned score.
            if not any(other!=st and abs(x-xx)<gap/scale*.35 for xx,other in bar_candidates):continue
            if x<pair[0]['left']+gap/scale*5:continue
            first_note=min((n['x'] for n in accepted if n['staff'] in (i,i+1)),default=pair[0]['right'])
            if x<first_note-gap/scale:continue
            xx=int(round(x*scale));a=max(0,xx-1);b=min(pm.width,xx+2)
            # Some printed editions intentionally leave the inter-staff gap
            # empty even at barlines. Shared staff endpoints are the evidence.
            extensions=[]
            for staff in pair:
                t=int(round(staff['top']*scale));bt=int(round(staff['bottom']*scale))
                above=ink[max(0,t-int(gap*.7)):max(0,t-2),a:b]
                below=ink[min(pm.height,bt+3):min(pm.height,bt+int(gap*.7)),a:b]
                outside=above if staff['index']==i else below
                extensions.append(float(outside.mean()) if outside.size else 0)
            if max(extensions)>.55:continue
            barxs.append(x)
        xs=[]
        for x in sorted(barxs+[pair[0]['left'],pair[0]['right']]):
            if not xs or x-xs[-1]>gap/scale*.6:xs.append(x)
        groups=[]
        for n in sorted(accepted,key=lambda n:n['x']):
            if n['staff'] not in (i,i+1):continue
            g=next((g for g in groups if n['stem'] is not None and g['stem']==n['stem'] and g['staff']==n['staff']),None)
            if g is None:g=dict(staff=n['staff'],stem=n['stem'],x=n['x'],y=n['y'],notes=[],kind='note',duration=n['duration'],direction=n['direction'],grace=False,beamIds=[]);groups.append(g)
            g['notes'].append(dict(n,ox=n['x']-staves[n['staff']]['step']*1.2,w=staves[n['staff']]['step']*2.4,c='\ue0a4' if n['kind']=='filled' else '\ue0a3',grace=False))
        for c in chars:
            if c['staff'] not in (i,i+1) or c['c'] not in ('\ue4e3','\ue4e4','\ue4e5','\ue4e6','\ue4e7'):continue
            if any(abs(n['x']-c['ox'])<gap/scale and abs(n['y']-c['y'])<gap/scale for n in accepted):continue
            duration={'\ue4e3':4,'\ue4e4':2,'\ue4e5':1,'\ue4e6':.5,'\ue4e7':.25}[c['c']]
            groups.append(dict(staff=c['staff'],stem=None,x=c['ox'],y=c['y'],notes=[],kind='rest',symbol=c['c'],duration=duration,direction='none',grace=False,beamIds=[]))
        measures=[]
        for a,b in zip(xs,xs[1:]):
            gs=[g for g in groups if a<g['x']<b]
            if b-a>gap/scale*2:measures.append(dict(left=a,right=b,groups=gs))
        systems.append(dict(page=pi,local=i//2,top=max(0,top-25),bottom=min(page.rect.height,bottom+30),staves=pair,measures=measures))
    return dict(page=pi,width=page.rect.width,height=page.rect.height,systems=systems,chars=chars,texts=[],ties=[],tuplets=[],issues=['Raster note candidates: clefs, accidentals, rests, ties and rhythm require visual review.'],detector='local-notehead-candidates-v6-staff-beams-dots-ledgers')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('ids',nargs='+');args=ap.parse_args()
    for sid in args.ids:
        out=ROOT/'transcription'/sid;out.mkdir(exist_ok=True)
        pages=[]
        for i,p in enumerate(fitz.open(ROOT/'scores'/sid/'original.pdf')):
            pg=extract_page(p,i);pages.append(pg);print(sid,i+1,sum(len(g['notes']) for s in pg['systems'] for m in s['measures'] for g in m['groups']),flush=True)
        from add_scan_head_readings import apply as head_readings
        head_readings(sid,pages)
        (out/'geometry-candidates.json').write_text(json.dumps(pages,ensure_ascii=False))
