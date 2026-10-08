"""PDF glyph geometry helper used alongside direct visual transcription.

Keep geometric extraction, rhythmic reconstruction and reviewed corrections
separate. Debug JSON retains every detected symbol and rhythm decision.
"""
import argparse, collections, json, math
from pathlib import Path
import fitz

ROOT=Path(__file__).resolve().parent.parent
SPECS={
 'feng':dict(title='枫',credit='Oskar Roman Jezior 编配',bpm=72,key=0),
 'iris-out':dict(title='IRIS OUT',credit='Animenz 编配',bpm=135,key=5),
 'tanjiro':dict(title='灶门炭治郎之歌',credit='Animenz 编配',bpm=76,key=-1),
}
NOTE={'œ':1,'˙':2,'w':4,'\ue0a4':1,'\ue0a3':2,'\ue0a2':4}
REST={'∑':4,'®':.125,'‰':.5,'≈':.25,'Œ':1,'Ó':2,'\ue4e6':.5,'\ue4e7':.25,'\ue4e5':1,'\ue4e3':4,'\ue4e4':2,'\ue4f5':.5}
CLEF={'&':'G','?':'F','\ue050':'G','\ue062':'F'}
ACC={'N':0,'#':1,'n':0,'b':-1,'‹':2,'\ue262':1,'\ue261':0,'\ue260':-1,'\ue263':2,'\ue264':-2}
FLAGS={'j':1,'J':1,'r':2,'R':2,'\ue240':1,'\ue241':1,'\ue242':2,'\ue243':2}
ALOISEN={'\uf074':'\ue0a4','\uf07c':'\ue0a3','\uf022':'\ue260',
 '\uf080':'\ue050','\uf081':'\ue062','\uf0c7':'\ue1e7',
 '\uf065':'\ue4e7','\uf049':'\ue240','\uf059':'\ue241',
 '\uf04a':'\ue242','\uf05a':'\ue243','\uf036':'\ue086','\uf038':'\ue088'}

def rounded(v):return round(float(v),4)
def cluster(values,tol=.6):
    groups=[]
    for v in sorted(values):
        if groups and v-groups[-1][-1]<tol:groups[-1].append(v)
        else:groups.append([v])
    return [sum(g)/len(g) for g in groups]

def extract_page(page,pi,sid):
    ds=page.get_drawings();chars=[];texts=[]
    for b in page.get_text('rawdict')['blocks']:
        for l in b.get('lines',[]):
            for span in l['spans']:
                music=span['font'] in ('MScore','MScoreText','Chaconne','Leland','FinaleMaestro','Pavane','FEF75F697B8','AloisenNew')
                if not music:
                    texts.append(dict(text=''.join(c['c'] for c in span['chars']),font=span['font'],x=span['origin'][0],y=span['origin'][1]))
                for c in span['chars']:
                    if music and c['c']!=' ':
                        symbol=ALOISEN.get(c['c'],c['c']) if span['font']=='AloisenNew' else c['c']
                        chars.append(dict(c=symbol,ox=c['origin'][0],y=c['origin'][1],w=c['bbox'][2]-c['bbox'][0],size=span['size']))
    unique={}
    for c in chars:unique[(c['c'],round(c['ox'],2),round(c['y'],2))]=c
    chars=list(unique.values())
    # MuseScore draws the five staff segments per measure in one path;
    # Chaconne draws a full-width path per line.
    lines=[]
    for d in ds:
        r=d['rect']
        if len(d['items'])==5 and all(i[0]=='l' and abs(i[1].y-i[2].y)<.01 and abs(i[1].x-i[2].x)>50 for i in d['items']):
            lines.extend((i[1].y,min(i[1].x,i[2].x),max(i[1].x,i[2].x)) for i in d['items'])
        elif r.width>350 and r.height<.8 and len(d['items'])<=4:
            lines.append(((r.y0+r.y1)/2,r.x0,r.x1))
        elif sid not in ('feng','young-and-beautiful'):
            for item in d['items']:
                if item[0]=='l' and abs(item[1].y-item[2].y)<.02 and abs(item[1].x-item[2].x)>45:
                    lines.append((item[1].y,min(item[1].x,item[2].x),max(item[1].x,item[2].x)))
    ys=cluster([a[0] for a in lines],.3)
    if sid not in ('feng','young-and-beautiful'):
        # Staff segments share the same x endpoints on all five lines. This
        # excludes hairpins, beams and ottava lines even at a staff-line y.
        bybounds=collections.defaultdict(list)
        for y,a,b in lines:bybounds[round(a,1),round(b,1)].append(y)
        valid=[]
        for (a,b),vv in bybounds.items():
            vv=cluster(vv,.3);used=set()
            for y in vv:
                if y in used:continue
                for y1 in vv:
                    gap=y1-y
                    if not 2.5<gap<8:continue
                    seq=[min(vv,key=lambda v:abs(v-y-gap*j)) for j in range(5)]
                    if any(abs(v-y-gap*j)>(.3 if sid=='interstellar' else .15) or v in used for j,v in enumerate(seq)):continue
                    valid.extend((v,a,b) for v in seq);used.update(seq);break
        lines=valid
        ys=cluster([a[0] for a in lines],.3)
    assert len(ys)%5==0,(sid,pi,'staff lines',len(ys))
    staves=[]
    for i in range(0,len(ys),5):
        y=ys[i:i+5];lineparts=[a for a in lines if abs(a[0]-y[0])<.4]
        staves.append(dict(index=len(staves),top=y[0],bottom=y[-1],center=y[2],step=(y[-1]-y[0])/8,left=min(a[1] for a in lineparts),right=max(a[2] for a in lineparts)))
    assert len(staves)%2==0
    stems=[];beams=[];ties=[]
    for di,d in enumerate(ds):
        r=d['rect'];it=d['items']
        if len(it)==1 and it[0][0]=='re':
            rr=it[0][1]; pts=[rr.tl,rr.tr,rr.br,rr.bl,rr.tl];it=[('l',a,b) for a,b in zip(pts,pts[1:])]
        if r.width<.85 and 5<r.height<100 and all(t[0]=='l' for t in it):
            stems.append(dict(id=di,x=(r.x0+r.x1)/2,y0=r.y0,y1=r.y1))
        min_beam=1.1 if sid=='interstellar' else 1.5
        if d['type'] in ('f','fs') and len(it) in (3,4) and all(t[0]=='l' for t in it) and r.width>3 and min_beam<r.height<30:
            # Require a filled ribbon, not a hairpin or ledger.
            points=[t[1] for t in it]+[it[-1][2]]
            if abs(points[0].x-points[-1].x)>.1 or abs(points[0].y-points[-1].y)>.1:points.append(points[0])
            area=abs(sum(a.x*b.y-b.x*a.y for a,b in zip(points,points[1:])))/2
            if min_beam<area/r.width<3.3:beams.append(dict(id=di,x0=r.x0,x1=r.x1,y0=r.y0,y1=r.y1,points=[[p.x,p.y] for p in points]))
        if any(t[0]=='c' for t in it) and r.width>3 and r.height<25:
            cs=[t for t in it if t[0]=='c']
            if cs:
                a=cs[0][1];b=cs[0][-1]
                # Chaconne may have multiple cubic segments along an arc.
                extrema=[p for t in cs for p in [t[1],t[-1]]]
                left=min(extrema,key=lambda p:p.x);right=max(extrema,key=lambda p:p.x)
                ties.append(dict(x0=left.x,y0=left.y,x1=right.x,y1=right.y,w=r.width,h=r.height))
    if sid=='a-thousand-years':
        # This exporter paints a beam as fifteen parallel stroked lines.
        stripes=collections.defaultdict(list)
        for di,d in enumerate(ds):
            if len(d['items'])!=1 or d['items'][0][0]!='l':continue
            _,a,b=d['items'][0]
            if a.x>b.x:a,b=b,a
            if b.x-a.x<3 or abs(b.y-a.y)>25:continue
            stripes[round(a.x,1),round(b.x,1),round(b.y-a.y,1)].append((a.y,b.y,di))
        for (x0,x1,slope),ss in stripes.items():
            chunks=[]
            for item in sorted(ss):
                if chunks and item[0]-chunks[-1][-1][0]<.25:chunks[-1].append(item)
                else:chunks.append([item])
            for chunk in chunks:
                if len(chunk)<6 or chunk[-1][0]-chunk[0][0]<.7:continue
                a,b=chunk[0],chunk[-1];points=[[x0,a[0]],[x1,a[1]],[x1,b[1]],[x0,b[0]],[x0,a[0]]]
                beams.append(dict(id=a[2],x0=x0,x1=x1,y0=min(a[0],a[1]),y1=max(b[0],b[1]),points=points))
    normalw=collections.Counter(round(c['w'],2) for c in chars if c['c'] in NOTE and NOTE[c['c']]==1).most_common(1)[0][0]
    notes=[]
    for c in chars:
        if c['c'] not in NOTE:continue
        n=dict(c);n['duration']=NOTE[c['c']];n['kind']='note';n['x']=c['ox']+c['w']/2;n['grace']=c['w']<normalw*.85
        possible=[]
        for stem in stems:
            x=stem['x'];y0,y1=stem['y0'],stem['y1']
            dx=min(abs(x-c['ox']-.25),abs(x-(c['ox']+c['w']-.4)))
            if dx<.9 and y0-1.7<c['y']<y1+1.7:
                possible.append((dx+min(abs(c['y']-y0),abs(c['y']-y1))*.015,stem))
        if possible and n['duration']<4:
            _,stem=min(possible,key=lambda a:a[0]);n['stem']=stem['id'];n['stemX']=stem['x'];n['stem0']=stem['y0'];n['stem1']=stem['y1']
            center=(stem['y0']+stem['y1'])/2
        else:n['stem']=None;center=c['y']
        n['staff']=min(range(len(staves)),key=lambda i:abs(staves[i]['center']-center))
        notes.append(n)
    groups=[]
    for n in notes:
        # Stem is the durable chord identity, including displaced seconds.
        key=(n['staff'],n['stem']) if n['stem'] is not None else (n['staff'],'whole',round(n['ox'],1))
        g=next((g for g in groups if g['key']==key),None)
        if g is None:g=dict(key=key,staff=n['staff'],notes=[],kind='note');groups.append(g)
        g['notes'].append(n)
    def ribbon_y(beam,x):
        yy=[]
        for a,b in zip(beam['points'],beam['points'][1:]):
            if min(a[0],b[0])-.7<=x<=max(a[0],b[0])+.7 and abs(a[0]-b[0])>1:
                yy.append(a[1]+(b[1]-a[1])*(x-a[0])/(b[0]-a[0]))
        return (min(yy)+max(yy))/2 if len(yy)>=2 else None
    dots=[c for c in chars if c['c'] in ('˜','\ue1e7')]
    for g in groups:
        ns=g['notes'];n=ns[0];g['duration']=max(a['duration'] for a in ns);g['grace']=all(a['grace'] for a in ns)
        y=sum(a['y'] for a in ns)/len(ns);g['y']=y;g['beamIds']=[]
        if n['stem'] is not None:
            up=n['stemX']-sorted(a['ox'] for a in ns)[len(ns)//2]>normalw/2;tip=n['stem0'] if up else n['stem1'];sx=n['stemX']
            g.update(direction='up' if up else 'down',tip=tip,stem=n['stem'],x=sx-(normalw-.4) if up else sx-.25)
            matching=[]
            for beam in beams:
                by=ribbon_y(beam,sx)
                if by is not None and abs(by-tip)<12 and (by>=tip-2 if up else by<=tip+2):matching.append((abs(by-tip),beam))
            matching.sort(key=lambda t:t[0]);matching=[b for dist,b in matching if dist<=10.5]
            g['beamIds']=[b['id'] for b in matching]
            flags=[c for c in chars if c['c'] in FLAGS and abs(c['ox']-sx)<1 and abs(c['y']-tip)<22]
            level=max(len(matching),max([FLAGS[c['c']] for c in flags],default=0))
            if g['duration']==1 and level:g['duration']=2**(-level)
        else:g.update(direction='none',stem=None,x=n['ox']+(n['w']-normalw)/2)
        dotted=any(0<c['ox']-max(a['ox']+a['w'] for a in ns)<6 and min(abs(c['y']-a['y']) for a in ns)<staves[g['staff']]['step']*1.2 for c in dots)
        if dotted:g['duration']*=1.5
        g['dotted']=dotted
        for n in ns:n['duration']=g['duration']
    for c in chars:
        if c['c'] in REST:
            st=min(range(len(staves)),key=lambda i:abs(staves[i]['center']-c['y']))
            dotted=any(0<d['ox']-c['ox']-c['w']<6 and abs(d['y']-c['y'])<6 for d in dots)
            groups.append(dict(key=('rest',c['ox'],c['y']),staff=st,x=c['ox'],y=c['y'],notes=[],kind='rest',symbol=c['c'],duration=REST[c['c']]*(1.5 if dotted else 1),grace=False,direction='none',beamIds=[]))
    # Symbols assigned to their staff for clefs, keys and accidentals.
    for c in chars:c['staff']=min(range(len(staves)),key=lambda i:abs(staves[i]['center']-c['y']))
    # Identify printed tuplet ratios from italic digits near a beam group.
    tuplets=[]
    for t in texts:
        if t['text'].isdigit() and ('Ita' in t['font']) and 2<int(t['text'])<=16:
            n=int(t['text']);tx=t['x']+2.5;ty=t['y']
            candidate=[]
            for b in beams:
                if b['x0']-3<tx<b['x1']+3:
                    members=[g for g in groups if b['id'] in g['beamIds'] and not g['grace']]
                    if 2<=len(members)<=16:
                        cy=(b['y0']+b['y1'])/2
                        candidate.append((abs(cy-ty)+abs(len(members)-n)*4,b,members))
            if candidate:
                _,b,members=min(candidate,key=lambda c:c[0]);factor=2**int(math.log2(n))/n
                if abs((b['y0']+b['y1'])/2-ty)<25 and len(members)==n:
                    for g in members:g['duration']*=factor;g['tuplet']=n
                    tuplets.append(dict(**t,n=n,matched=len(members),beam=b['id']))
                    continue
            tuplets.append(dict(**t,n=n,matched=0))
    # Staff lines, shared barlines, and groups inside each measure.
    systems=[]
    for si in range(0,len(staves),2):
        pair=staves[si:si+2];top,bottom=pair[0]['top'],pair[1]['bottom']
        bar_candidates=[]
        for d in ds:
            r=d['rect']
            if r.width<2 and r.height>pair[0]['bottom']-top-1:
                matched={i for i,s in enumerate(pair) if abs(r.y0-s['top'])<1 and abs(r.y1-s['bottom'])<1}
                if abs(r.y0-top)<1 and abs(r.y1-bottom)<1:matched={0,1}
                if matched:bar_candidates.append(((r.x0+r.x1)/2,matched))
        xs=[]
        for x in cluster([x for x,_ in bar_candidates],2):
            matched=set().union(*(matched for bx,matched in bar_candidates if abs(bx-x)<2))
            occupied=any(n.get('stemX') is not None and abs(n['stemX']-x)<1 for g in groups if g['staff'] in (si,si+1) for n in g['notes'])
            if len(matched)==2 or (sid not in ('feng','young-and-beautiful') and matched and not occupied):xs.append(x)
        if sid in ('feng','young-and-beautiful'):
            xs=[x for y,a,b in lines if abs(y-top)<.4 for x in (a,b)]
        elif any(c['c']=='\ue0a4' for c in chars):
            xs.extend(x for y,a,b in lines if any(abs(y-st['top'])<.4 for st in pair) for x in (a,b))
        bars=cluster(xs+[pair[0]['left'],pair[0]['right']],3)
        sy=dict(page=pi,local=si//2,top=max(0,top-26),bottom=min(page.rect.height,bottom+32),staves=pair,measures=[])
        for left,right in zip(bars,bars[1:]):
            gs=[g for g in groups if g['staff'] in (si,si+1) and left+1<g['x']<right-1]
            if not gs:continue
            sy['measures'].append(dict(left=left,right=right,groups=sorted(gs,key=lambda g:g['x'])))
        systems.append(sy)
    return dict(page=pi,width=page.rect.width,height=page.rect.height,chars=chars,texts=texts,systems=systems,tuplets=tuplets,ties=ties,beams=beams)
