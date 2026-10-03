"""Export reviewed vector notes, ties, pedal and expressive tempo to the player."""
import json,math,collections
from pathlib import Path
import fitz
from transcribe_vector_scores import SPECS,CLEF,ACC
ROOT=Path(__file__).resolve().parent.parent
STEPS=[0,2,4,5,7,9,11]

def export(sid):
    ps=json.loads((ROOT/'transcription'/f'{sid}-extracted.json').read_text());spec=SPECS[sid]
    systems=[];measures=[];events=[];ottavas=[];pedals=[];time=0
    doc=fitz.open(ROOT/'dist'/'scores'/sid/'original.pdf')
    for page in ps:
        pi=page['page'];staves=[st for s in page['systems'] for st in s['staves']]
        for path in doc[pi].get_drawings():
            r=path['rect'];dash=path['dashes'] or ''
            if ('2.125 2.125' in dash or '10.000007 5.' in dash) and r.width>10 and r.height<1:
                st=min(staves,key=lambda s:abs(s['top']-r.y0))
                ottavas.append(dict(page=pi,staff=st['index'],x0=r.x0-(12 if sid=='tanjiro' else 12),x1=r.x1+1,shift=12))
        clefs={st['index']:sorted([c for c in page['chars'] if c['c'] in CLEF and c['staff']==st['index']],key=lambda c:c['ox']) for st in staves}
        def clef_at(st,x):
            cs=[c for c in clefs[st] if c['ox']<x]
            return CLEF[cs[-1]['c']] if cs else ('G' if st%2==0 else 'F')
        def dia(st,x,y):
            clef=clef_at(st,x);s=staves[st]
            return (30 if clef=='G' else 18)+round((s['bottom']-y)/s['step'])
        for sy in page['systems']:
            os=dict(index=len(systems),page=pi,top=sy['top'],bottom=sy['bottom'],start=time,measures=[])
            systems.append(os)
            for m in sy['measures']:
                num=m['number'];length=6 if sid=='feng' and num==4 else 2 if sid=='tanjiro' and num in (34,35,41,68) else 4
                assert abs(m['rawDuration']-length)<1e-5,(sid,num,m['rawDuration'],length)
                om=dict(index=len(measures),displayNumber=num-(1 if sid=='tanjiro' and num>=35 else 0),system=os['index'],page=pi,left=m['left'],right=m['right'],start=time,duration=length,groups=[])
                measures.append(om);os['measures'].append(om['index'])
                key=-4 if sid=='feng' and num>=49 else spec['key']
                keymap={d:(1 if key>0 else -1) for d in ([3,0,4,1,5,2,6] if key>0 else [6,2,5,1,4,0,3])[:abs(key)]}
                gs=m['groups'];states={};changes=[]
                # Associate an explicit accidental with the closest following
                # note on the same pitch line. A system's key block is excluded.
                for c in page['chars']:
                    if c['c'] not in ACC or c['staff'] not in [s['index'] for s in sy['staves']]:continue
                    if not m['left']<c['ox']<m['right']:continue
                    st=c['staff'];first=min([g['x'] for g in gs if g['staff']==st and g['notes']],default=m['right'])
                    if m==sy['measures'][0] and c['ox']<first-9:
                        before=[a for a in page['chars'] if a['c'] in ACC and a['staff']==st and m['left']<a['ox']<first-9]
                        if len(before)>=abs(key) and key and c['ox']<=sorted(before,key=lambda a:a['ox'])[abs(key)-1]['ox']+.1:continue
                    candidates=[(abs(n['y']-c['y'])*8+n['ox']-c['ox'],g,n) for g in gs if g['staff']==st for n in g['notes'] if 0<n['ox']-c['ox']<28 and abs(n['y']-c['y'])<1.2]
                    if candidates:
                        _,g,n=min(candidates,key=lambda v:v[0]);changes.append((g['x']-.01,st,dia(st,n['ox'],n['y']),ACC[c['c']]))
                ci=0;changes.sort()
                # Grace groups have their own short performance time, before
                # the next principal onset, retaining their printed coordinates.
                for g in gs:
                    if g['grace']:
                        targets=[h for h in gs if not h['grace'] and h['x']>g['x'] and h['staff']==g['staff']]
                        target=min(targets,key=lambda h:h['x']) if targets else None
                        g['localBeat']=max(0,(target['localBeat'] if target else length)-.12)
                        g['duration']=.12
                for g in sorted(gs,key=lambda a:a['x']):
                    st=g['staff']
                    while ci<len(changes) and changes[ci][0]<=g['x']:
                        _,ast,d,a=changes[ci];states[ast,d]=a;ci+=1
                    og=dict(x=g['x'],beat=time+g.get('localBeat',0),duration=g['duration'],hand='R' if st%2==0 else 'L',notes=[])
                    for n in g['notes']:
                        d=dia(st,n['ox'],n['y']);octave,degree=divmod(d,7);alter=states.get((st,d),keymap.get(degree,0))
                        shift=sum(o['shift'] for o in ottavas if o['page']==pi and o['staff']==st and o['x0']<=n['ox']<=o['x1'])
                        midi=12*(octave+1)+STEPS[degree]+alter+shift
                        e=dict(id=len(events),midi=midi,beat=og['beat'],duration=og['duration'],hand=og['hand'],x=n['x'],y=n['y'],page=pi,system=os['index'],measure=om['index'],diatonic=d,staff=st,grace=g['grace'])
                        assert 21<=midi<=108,(sid,num,midi,n)
                        events.append(e);og['notes'].append(e['id'])
                    om['groups'].append(og)
                bybeat=collections.defaultdict(list)
                for g in om['groups']:
                    if g['notes'] and not all(events[i]['grace'] for i in g['notes']):bybeat[round(g['beat'],8)].append(g['x'])
                anchors=[[b,min(xs)] for b,xs in sorted(bybeat.items())]
                # In polyphonic passages use the leftmost simultaneous anchor;
                # omit backward x movements while preserving exact event times.
                clean=[]
                for a in anchors:
                    if not clean or a[1]>clean[-1][1]+.2:clean.append(a)
                if not clean or clean[0][0]>time:clean.insert(0,[time,m['left']+2])
                clean.append([time+length,m['right']-2]);om['anchors']=clean
                time+=length
            os['end']=time
    # Ties: only adjacent time points of the same written pitch can connect.
    bytime=collections.defaultdict(list)
    for e in events:bytime[round(e['beat'],5)].append(e)
    for p in ps:
        for arc in p['ties']:
            cand=[]
            for a in events:
                if a['page']!=p['page'] or a.get('tieTo') is not None:continue
                if not -2<arc['x0']-a['x']<8 or abs(arc['y0']-a['y'])>5:continue
                for b in bytime.get(round(a['beat']+a['duration'],5),[]):
                    if b['diatonic']!=a['diatonic'] or b['hand']!=a['hand'] or b.get('tieFrom') is not None:continue
                    same=b['system']==a['system'] and -2<b['x']-arc['x1']<8 and abs(arc['y1']-b['y'])<5
                    cross=b['system']==a['system']+1 and arc['x1']>p['width']-45
                    if same or cross:cand.append((abs(arc['x0']-a['x'])+abs(arc['y0']-a['y'])+abs(arc['y1']-b['y']) if same else 10,a,b))
            if cand:
                _,a,b=min(cand,key=lambda t:t[0]);a['tieTo']=b['id'];b['tieFrom']=a['id'];b['midi']=a['midi']
    for e in events:
        if 'tieFrom' not in e:
            end=e['beat']+e['duration'];cur=e;seen=set()
            while 'tieTo' in cur:
                assert cur['id'] not in seen;seen.add(cur['id']);cur=events[cur['tieTo']];end=cur['beat']+cur['duration']
            e['soundDuration']=end-e['beat']
    def location_time(pi,x,y):
        sy=min([s for s in systems if s['page']==pi],key=lambda s:abs((s['top']+s['bottom'])/2-y))
        es=[e for e in events if e['system']==sy['index']]
        return min(es,key=lambda e:abs(e['x']-x))['beat']
    for p in ps:
        for c in p['chars']:
            if c['c'] in ('°','*'):pedals.append(dict(beat=location_time(p['page'],c['ox'],c['y']-15),down=c['c']=='°'))
    pedals.sort(key=lambda p:p['beat']);ranges=[];start=None
    for p in pedals:
        if p['down']:
            if start is not None:ranges.append([start,p['beat']])
            start=p['beat']
        elif start is not None:ranges.append([start,p['beat']]);start=None
    if start is not None:ranges.append([start,time])
    for e in events:
        if 'soundDuration' in e:
            end=e['beat']+e['soundDuration']
            for a,b in ranges:
                if a<=end<b:end=b
            e['pedalDuration']=end-e['beat']
    dynamics=[]
    for p in ps:
        for c in p['chars']:
            if c['c'] in {'p','P','F','f','ƒ','π','ß','Í'}:
                dynamics.append((location_time(p['page'],c['ox'],c['y']),{'π':.48,'p':.62,'P':.76,'F':.90,'f':1.05,'ƒ':1.18,'ß':1.2,'Í':.65}[c['c']]))
    dynamics.sort()
    for e in events:
        e['velocity']=next((v for b,v in reversed(dynamics) if b<=e['beat']),.85)
    tempoMap=[dict(beat=0,factor=1)]
    if sid=='tanjiro':
        # Relative expressive marks have no exact metronome values in the PDF.
        # These restrained practice defaults are documented as interpretations.
        for n,f in [(95,.97),(96,.90),(97,.82),(98,.84),(102,.78),(103,.72),(104,.62)]:
            tempoMap.append(dict(beat=measures[n-1]['start'],factor=f))
    data=dict(title=spec['title'],credit=spec['credit'],bpm=spec['bpm'],mode='play',pages=len(ps),pageSizes=[dict(width=p['width'],height=p['height']) for p in ps],totalBeats=time,systems=systems,measures=measures,events=events,keyLabel={'feng':'C 大调 → A♭ 大调','iris-out':'B 大调','tanjiro':'F 大调'}[sid],meterLabel='4/4 · 6/4' if sid=='feng' else '4/4 · 2/4' if sid=='tanjiro' else '4/4',pedals=ranges,tempoMap=tempoMap,performanceNote=('原谱未标速度，默认 72 BPM，可自行调整。' if sid=='feng' else '末段渐慢采用参考速度，可调整 BPM。' if sid=='tanjiro' else ''))
    (ROOT/'dist'/'scores'/sid/'score.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
    print(sid,len(measures),len(events),time,'ties',sum('tieTo'in e for e in events),'range',min(e['midi'] for e in events),max(e['midi'] for e in events),'pedals',ranges)
for sid in SPECS:export(sid)
