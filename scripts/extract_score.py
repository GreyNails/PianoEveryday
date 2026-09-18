import fitz, json, math
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/'source'/'score.pdf'
OUT=ROOT/'dist'
doc=fitz.open(SOURCE)
systems=[]; measures=[]; events=[]; diagnostics=[]; all_ties=[]
for pi,page in enumerate(doc):
    ds=page.get_drawings()
    lines=sorted([(d['rect'].y0+d['rect'].y1)/2 for d in ds if d['rect'].width>450 and d['rect'].height<1])
    staves=[lines[i:i+5] for i in range(0,len(lines),5)]
    assert len(staves)==12,(pi,len(staves))
    heads=[]; dots=[]; rests=[]
    for di,d in enumerate(ds):
        r=d['rect']; kinds=''.join(it[0] for it in d['items'])
        if kinds in ['cccc','cccccccc','ccccccccc'] and 6.5<r.width<9.5 and 5<r.height<5.6:
            heads.append(dict(x=(r.x0+r.x1)/2,y=(r.y0+r.y1)/2,kind=len(d['items']),di=di))
        elif kinds=='cccc' and 1.5<r.width<2.2 and 1.5<r.height<2.2:dots.append(r)
        elif len(d['items'])==10 and 5<r.width<5.5 and 8.5<r.height<9.2:rests.append(dict(x=r.x0+1,y=r.y0+3,kind=0,di=di))
    stems=[d['rect'] for d in ds if .3<d['rect'].width<.7 and 12<d['rect'].height<58]
    flags=[d['rect'] for d in ds if len(d['items']) in (14,15) and 4.8<d['rect'].width<6.1 and 13<d['rect'].height<14.8]
    beams=[d for d in ds if len(d['items'])==4 and all(it[0]=='l' for it in d['items']) and d['rect'].width>5 and 2<d['rect'].height<12]
    ties=[d for d in ds if len(d['items'])==2 and all(it[0]=='c' for it in d['items'])]
    for n in heads+rests:
        x,y=n['x'],n['y']
        candidates=[s for s in stems if min(abs(s.x0-x-3.2),abs(s.x0-x+3.4))<.8 and s.y0-2<y<s.y1+2]
        cy=y
        if candidates:
            s=min(candidates,key=lambda s:abs(s.y0-y)+abs(s.y1-y))
            cy=(s.y0+s.y1)/2
        n['staff']=min(range(len(staves)),key=lambda i:abs(staves[i][2]-cy))
    def beam_at(d,x,y):
        # Intersect the filled beam polygon with the stem's x coordinate.
        yy=[]
        for it in d['items']:
            a,b=it[1:]
            if min(a.x,b.x)-.5<=x<=max(a.x,b.x)+.5 and abs(b.x-a.x)>1:
                yy.append(a.y+(b.y-a.y)*(x-a.x)/(b.x-a.x))
        return len(yy)>=2 and min(yy)-.6<=y<=max(yy)+.6
    for si in range(6):
        treble,bass=staves[2*si:2*si+2]
        top,bottom=treble[0],bass[-1]
        sy=dict(page=pi,top=round(top-15,2),bottom=round(bottom+29,2),start=len(measures)*4,index=len(systems),measures=[])
        systems.append(sy)
        bars=sorted(set(round((d['rect'].x0+d['rect'].x1)/2,2) for d in ds if d['rect'].width<2 and abs(d['rect'].y0-top)<1 and abs(d['rect'].y1-bottom)<1))
        bars=[b for i,b in enumerate(bars) if not i or b-bars[i-1]>4]
        bars=[98]+[b for b in bars if b>98]
        for bi,(left,right) in enumerate(zip(bars,bars[1:])):
            m=dict(index=len(measures),system=sy['index'],page=pi,left=left,right=right,start=len(measures)*4,duration=4,groups=[])
            measures.append(m);sy['measures'].append(m['index'])
            for hand in ['R','L']:
                lo,hi=(top-25,(treble[-1]+bass[0])/2) if hand=='R' else ((treble[-1]+bass[0])/2,bottom+35)
                ns=sorted([dict(n) for n in heads+rests if left<n['x']<right and n['staff']==2*si+(hand=='L')],key=lambda n:n['x'])
                groups=[]
                for n in ns:
                    if groups and abs(groups[-1][0]['x']-n['x'])<1:groups[-1].append(n)
                    else:groups.append([n])
                t=0
                for group in groups:
                    x=group[0]['x']; ys=[n['y'] for n in group]; kind=max(n['kind'] for n in group)
                    duration={0:.5,4:1,8:2,9:4}[kind]
                    candidates=[s for s in stems if min(abs(s.x0-x-3.2),abs(s.x0-x+3.4))<.8 and any(s.y0-2<y<s.y1+2 for y in ys)]
                    if kind==4 and candidates:
                        stem=min(candidates,key=lambda s:min(abs(s.y0-y)+abs(s.y1-y) for y in ys))
                        tip=stem.y0 if abs(stem.y0-sum(ys)/len(ys))>abs(stem.y1-sum(ys)/len(ys)) else stem.y1
                        sx=(stem.x0+stem.x1)/2
                        nb=sum(1 for b in beams if any(beam_at(b,sx,tip+off) for off in [-4,0,4]))
                        flagged=any(abs(f.x0-sx)<1 and (abs(f.y0-tip)<1 or abs(f.y1-tip)<1) for f in flags)
                        if nb or flagged:duration=.5 if nb<2 else .25
                    dotted=any(x+4<d.x0<x+9 and any(abs((d.y0+d.y1)/2-y)<3 for y in ys) for d in dots)
                    if dotted:duration*=1.5
                    g=dict(x=round(x,2),beat=m['start']+t,duration=duration,hand=hand,notes=[])
                    for n in group:
                        if not n['kind']:continue
                        # Diatonic bottom lines: E4 (treble), G2 (bass). Four sharps.
                        staff=treble if hand=='R' else bass
                        diatonic=(4*7+2 if hand=='R' else 2*7+4)+round((staff[-1]-n['y'])/((staff[-1]-staff[0])/8))
                        octave,degree=divmod(diatonic,7)
                        midi=12*(octave+1)+[0,2,4,5,7,9,11][degree]+(1 if degree in [0,1,3,4] else 0)
                        e=dict(midi=midi,beat=g['beat'],duration=duration,hand=hand,x=round(n['x'],2),y=round(n['y'],2),page=pi,system=sy['index'],measure=m['index'],di=n['di'])
                        g['notes'].append(len(events));events.append(e)
                    m['groups'].append(g);t+=duration
                if abs(t-4)>.001:diagnostics.append(dict(measure=m['index']+1,hand=hand,total=t,groups=[(round(g[0]['x'],2),g[0]['kind']) for g in groups]))
        sy['end']=len(measures)*4
    for d in ties:
        curve=d['items'][0]
        a,b=curve[1],curve[-1]
        all_ties.append(dict(page=pi,x0=a.x,y0=a.y,x1=b.x,y1=b.y))
    page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False).save(str(OUT/f'page-{pi+1}.png'))

linked=set();unmatched=[]
for tie in all_ties:
    candidates=[]
    for i,a in enumerate(events):
        if a['page']!=tie['page'] or not -.8<tie['x0']-a['x']<5.5 or abs(tie['y0']-a['y'])>4.8:continue
        for j,b in enumerate(events):
            if b['midi']!=a['midi'] or b['hand']!=a['hand'] or abs(b['beat']-a['beat']-a['duration'])>.01:continue
            same=b['system']==a['system'] and -.8<b['x']-tie['x1']<5.5 and abs(tie['y1']-b['y'])<4.8
            cross=b['system']==a['system']+1 and tie['x1']>550
            if same or cross:candidates.append((abs(tie['y0']-a['y'])+abs(tie['x0']-a['x']),i,j))
    if candidates:
        _,i,j=min(candidates);events[i]['tieTo']=j;events[j]['tieFrom']=i;linked.add((i,j))
    else:unmatched.append(tie)
print('tie links',len(linked),'unmatched arcs',len(unmatched))
Path('/tmp/unmatched-ties.json').write_text(json.dumps(unmatched,indent=2))
for i,e in enumerate(events):
    e['id']=i
    e.pop('di')
    if 'tieFrom' not in e:
        end=e['beat']+e['duration'];cur=e
        while 'tieTo' in cur:
            cur=events[cur['tieTo']];end=cur['beat']+cur['duration']
        e['soundDuration']=end-e['beat']
for m in measures:
    bybeat={}
    for g in m['groups']:
        if g['notes']:bybeat.setdefault(g['beat'],[]).append(g['x'])
    m['anchors']=[[b,round(sum(xs)/len(xs),2)] for b,xs in sorted(bybeat.items())]+[[m['start']+4,m['right']-2]]
data=dict(title='阳光宅男',credit='陈哲 ChenZhe 编配',keyLabel='E 大调',meterLabel='4/4',mode='play',bpm=140,totalBeats=len(measures)*4,pages=5,width=doc[0].rect.width,height=doc[0].rect.height,systems=systems,measures=measures,events=events)
(OUT/'score.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
Path('/tmp/score-diagnostics.json').write_text(json.dumps(diagnostics,indent=2))
print('measures',len(measures),'notes',len(events),'incorrect duration sums',len(diagnostics))
print(json.dumps(diagnostics,indent=2))
