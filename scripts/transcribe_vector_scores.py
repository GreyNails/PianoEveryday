"""Font-aware vector transcription for the three supplied engraved PDFs.

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
REST={'®':.125,'‰':.5,'≈':.25,'Œ':1,'Ó':2,'\ue4e6':.5,'\ue4e7':.25,'\ue4e5':1,'\ue4e3':4,'\ue4e4':2,'\ue4f5':.5}
CLEF={'&':'G','?':'F','\ue050':'G','\ue062':'F'}
ACC={'N':0,'#':1,'n':0,'b':-1,'‹':2,'\ue262':1,'\ue261':0,'\ue260':-1}
FLAGS={'j':1,'J':1,'r':2,'R':2,'\ue240':1,'\ue241':1,'\ue242':2,'\ue243':2}

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
                music=span['font'] in ('MScore','MScoreText','Chaconne')
                if not music:
                    texts.append(dict(text=''.join(c['c'] for c in span['chars']),font=span['font'],x=span['origin'][0],y=span['origin'][1]))
                for c in span['chars']:
                    if music and c['c']!=' ':
                        chars.append(dict(c=c['c'],ox=c['origin'][0],y=c['origin'][1],w=c['bbox'][2]-c['bbox'][0],size=span['size']))
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
        if d['type'] in ('f','fs') and len(it) in (3,4) and all(t[0]=='l' for t in it) and r.width>3 and 1.5<r.height<30:
            # Require a filled ribbon, not a hairpin or ledger.
            points=[t[1] for t in it]+[it[-1][2]]
            if abs(points[0].x-points[-1].x)>.1 or abs(points[0].y-points[-1].y)>.1:points.append(points[0])
            area=abs(sum(a.x*b.y-b.x*a.y for a,b in zip(points,points[1:])))/2
            if 1.5<area/r.width<3.3:beams.append(dict(id=di,x0=r.x0,x1=r.x1,y0=r.y0,y1=r.y1,points=[[p.x,p.y] for p in points]))
        if any(t[0]=='c' for t in it) and r.width>3 and r.height<25:
            cs=[t for t in it if t[0]=='c']
            if cs:
                a=cs[0][1];b=cs[0][-1]
                # Chaconne may have multiple cubic segments along an arc.
                extrema=[p for t in cs for p in [t[1],t[-1]]]
                left=min(extrema,key=lambda p:p.x);right=max(extrema,key=lambda p:p.x)
                ties.append(dict(x0=left.x,y0=left.y,x1=right.x,y1=right.y,w=r.width,h=r.height))
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
            if len(matched)==2:xs.append(x)
        if sid=='feng':xs=[x for y,a,b in lines if abs(y-top)<.4 for x in (a,b)]
        bars=cluster(xs+[pair[0]['left'],pair[0]['right']],3)
        sy=dict(page=pi,local=si//2,top=max(0,top-26),bottom=min(page.rect.height,bottom+32),staves=pair,measures=[])
        for left,right in zip(bars,bars[1:]):
            gs=[g for g in groups if g['staff'] in (si,si+1) and left+1<g['x']<right-1]
            if not gs:continue
            sy['measures'].append(dict(left=left,right=right,groups=sorted(gs,key=lambda g:g['x'])))
        systems.append(sy)
    return dict(page=pi,width=page.rect.width,height=page.rect.height,chars=chars,texts=texts,systems=systems,tuplets=tuplets,ties=ties,beams=beams)

def reconstruct(sid):
    spec=SPECS[sid];pdf=ROOT/'dist'/'scores'/sid/'original.pdf';doc=fitz.open(pdf)
    pages=[extract_page(p,i,sid) for i,p in enumerate(doc)]
    diagnostics=[];counter=0;time=0
    for page in pages:
        for system in page['systems']:
            for m in system['measures']:
                counter+=1;m['number']=counter
                apply_geometry_corrections(sid,page,system,m)
                # The shortest currently active duration defines the next onset.
                # Inspect every exception before exporting performance events.
                columns=[]
                for g in m['groups']:
                    if g['grace']:continue
                    if g['kind']=='rest' and g.get('symbol')=='\ue4e3' and m['number']==73:continue
                    if sid=='feng' and m['number']==15 and abs(g['x']-436.8)<1:g['x']=427
                    
                    displaced=columns and abs(g['x']-columns[-1]['x'])<(9 if sid=='feng' else 5.4) and any(g['staff']==h['staff'] and {g['direction'],h['direction']}=={'up','down'} for h in columns[-1]['groups'])
                    if columns and (abs(g['x']-columns[-1]['x'])<2.8 or displaced):
                        columns[-1]['groups'].append(g)
                    else:columns.append(dict(x=g['x'],groups=[g]))
                clock=0;active=[]
                for col in columns:
                    for g in col['groups']:g['localBeat']=clock;active.append(clock+g['duration'])
                    col['beat']=clock
                    clock=min(a for a in active if a>clock+1e-6)
                    active=[a for a in active if a>clock+1e-6]
                total=max([g.get('localBeat',0)+g['duration'] for g in m['groups'] if not g['grace']],default=0)
                m['columns']=columns;m['rawDuration']=total
                apply_timing_corrections(sid,page,system,m)
                total=m['rawDuration']
                if abs(total-4)>.001:diagnostics.append(dict(number=counter,page=page['page']+1,system=system['local'],total=total))
    out=ROOT/'transcription'/f'{sid}-extracted.json';out.write_text(json.dumps(pages,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(sid,'measures',counter,'noteheads',sum(len(g['notes']) for p in pages for s in p['systems'] for m in s['measures'] for g in m['groups']),'non4',len(diagnostics))
    print(json.dumps(diagnostics))
    print('tuplets',[(p['page']+1,t['n'],t['matched'],round(t['x'],1),round(t['y'],1)) for p in pages for t in p['tuplets']])

from reviewed_corrections import apply_geometry_corrections, apply_timing_corrections

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('song',choices=list(SPECS)+['all']);a=p.parse_args()
    for sid in SPECS if a.song=='all' else [a.song]:reconstruct(sid)
