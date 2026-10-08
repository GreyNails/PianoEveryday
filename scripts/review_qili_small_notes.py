"""Small printed heads can be metered inner voices, not grace notes.

Readings use PDF-point stem columns. Keep ornaments, cue-size voices and
measured tuplets distinct; do not delete small heads or change other songs.
"""

def apply(pages,timing):
    rows=[(p,s,m) for p in pages for s in p['systems'] for m in s['measures']]
    # This low pickup below bar 30 was attached to the next system's treble.
    _,_,wrong=rows[32];p,sy,target=rows[29]
    moved=[g for g in wrong['groups'] if g['staff']%2==0 and g['grace'] and g['x']>550]
    assert len(moved)==1
    g=moved[0];wrong['groups'].remove(g);g['staff']=sy['staves'][1]['index']
    for n in g['notes']:n['pitchStaff']=g['staff']
    target['groups'].append(g)
    # Whole right-hand voice readings in bars with independent small heads.
    # (column, beat, duration), including rests when another voice is sounding.
    maps={}
    def add(number,xs,bs,ds):
        xs=list(map(float,xs.split()))
        if isinstance(ds,(int,float)):ds=[ds]*len(xs)
        assert len(xs)==len(bs)==len(ds)
        maps[number]=list(zip(xs,bs,ds))
    for number,xs in [(9,'417.3 417.4 447.4 447.5 467.9 478.1 490.2 490.3 520.2 520.2 546.9'),
                      (13,'87.1 87.3 115.6 115.8 135.1 144.8 156.9 157.0 185.4 185.4 204.9')]:
        # The doubled rest column has different lengths in the two voices.
        add(number,xs,[0,0,1,1,1.5,1.75,2,2,3,3,3.75 if number==9 else 3.5],
            [1,1,1,.5,.25,.25,1,1,1,.75 if number==9 else .5,.25 if number==9 else .5])
    add(10,'87.3 87.5 104.6 126.0 126.1 147.6 158.1 158.3 172.1 172.2 183.0 210.9 210.9 228.2',
        [0,0,.5,1,1,1.5,1.75,1.75,2,2,2.25,3,3,3.5], [1,.5,.5,.75,.5,.25,.25,.25,1,.25,.75,.5,1,.5])
    add(32,'243.5 245.7 259.1 281.5 283.6 304.1 326.4 328.6 342.0 364.5 380.0 391.2',
        [0,0,.5,1,1,1.5,2,2,2.5,3,3.5,3.75],[1,.5,.5,1,.5,.5,1,.5,.5,.5,.25,.25])
    for number,xs in [(33,'421.5 421.6 452.7 468.5 488.0 503.6 523.2 542.7'),
                      (37,'87.1 87.3 120.3 138.8 157.2 172.0 190.4 208.8'),
                      (53,'229.6 229.7 266.8 287.6 308.2 324.8 345.4 366.1')]:
        add(number,xs,[0,0,1,1.5,2,2.5,3,3.5],[1,1.5,1,.5,.5,.5,.5,.5])
    add(39,'432.5 432.6 446.4 463.7 480.9 498.5 512.3 530.0 552.4',
        [0,0,.5,1,1.5,2,2.5,3,3.75],[.5]*7+[.75,.25])
    for number,xs in [(49,'87.1 87.3 101.2 119.5 137.6 155.4 169.5 187.1 205.0'),
                      (51,'412.0 414.2 428.0 447.7 467.6 487.3 503.1 522.8 542.6')]:
        add(number,xs,[0,0,.5,1,1.5,2,2.5,3,3.5],[.5,1.5,.5,1,.5,.5,.5,.5,.5])
    for number,xs in [(65,'87.1 89.3 106.5 106.6 134.8 134.8 163.1 163.3 191.5 199.3 214.8 243.1 250.9 271.4'),
                      (67,'87.3 89.5 110.9 111.0 134.6 134.6 164.1 164.3 193.8 201.6 217.5 247.0 254.8 276.6')]:
        add(number,xs,[0,0,.5,.5,1,1,1.5,1.5,2,2.25,2.5,3,3.25,3.5],.5)
    add(69,'87.3 89.5 110.6 139.6 168.7 195.4 215.3 244.2 273.2',[0,0,.5,1,1.5,2,2.5,3,3.5],.5)
    add(70,'313.8 349.5 385.3 421.0 440.4 459.6 459.8 512.9 539.7',
        [0,.5,1,1.5,1.75,2,2,3,3.5],[.5,.5,.5,.25,.25,1,1.5,.5,.5])
    add(73,'421.1 423.3 438.3 453.8 469.2 469.4 488.7 504.1 523.5 542.8',
        [0,0,.5,1,1.5,1.5,2,2.5,3,3.5],.5)
    add(75,'318.7 342.2 359.5 376.7 393.9 411.1 428.5 450.0 473.7 497.4 531.9',
        [0,.5,.75,1,1.25,1.5,1.75,2,2.5,3,3.5],[.5]+[.25]*6+[.5]*4)
    add(77,'257.7 259.8 274.9 285.6 301.3 324.0 334.9 351.9 368.9',[0,0,.5,1,1.5,2,2.5,3,3.5],.5)
    add(78,'399.6 417.1 441.8 463.0 473.9 487.9 498.8 515.0 515.2 524.0 524.2 541.4 541.5',
        [0,.5,1,1.5,1.75,2,2.25,2.75,2.75,3,3,3.5,3.5],
        [.5,.5,.5,.25,.25,.25,.5,.25,.25,.5,.5,.5,.5])
    reports=[]
    for number,(p,sy,m) in enumerate(rows,1):
        gs=m['groups']
        if not any(n['grace'] for g in gs for n in g['notes']):continue
        already_reviewed=all('reviewedBeat' in g for g in gs)
        _,closed=timing(gs,4,sy['staves'][0]['step']*2)
        assert closed,('Baseline must close before small-head correction',number)
        for g in gs:g['reviewedBeat']=g['localBeat'];g['duration']=g['playDuration']
        if number in maps:
            rr=sorted([g for g in gs if g['staff']%2==0],key=lambda g:g['x'])
            readings=maps[number]
            assert len(rr)==len(readings),(number,len(rr),len(readings))
            for g,(x,b,d) in zip(rr,readings):
                assert abs(g['x']-x)<.12,(number,g['x'],x)
                g.update(reviewedBeat=b,duration=d)
        for g in gs:
            if g['staff']%2==0 and number not in (5,81):
                g['grace']=False
            for n in g['notes']:
                if not n['grace']:continue
                role='ornament' if g['grace'] or number in (56,80) else 'accompaniment'
                n.update(reviewedVelocity=.58,reviewedVoiceRole=role,smallNotehead=True)
        # Three printed 32nds are successive attacks, not one simultaneous chord.
        if number in (5,81):
            ornaments=sorted([g for g in gs if g['staff']%2==0 and g['grace']],key=lambda g:g['x'])
            assert len(ornaments)==3
            for i,g in enumerate(ornaments):g.update(reviewedBeat=3.625+i/8,duration=.125)
        # Retain sequential pitches in bass pickup pairs (previously coalesced).
        if number in (47,65,77):
            ending=4 if number!=77 else 2
            ornaments=sorted([g for g in gs if g['staff']%2==1 and g['grace'] and abs(g['reviewedBeat']+g['duration']-ending)<1e-6],key=lambda g:g['x'])
            assert len(ornaments)==2,(number,len(ornaments))
            for i,g in enumerate(ornaments):g.update(reviewedBeat=ending-.25+i/8,duration=.125)
        if not already_reviewed:m['sourcePulseAligned']=True
        reports.append(dict(measure=number,reason='小符头区分计拍内声部、连音与装饰音；内声部恢复谱面时值，装饰音组依次起音，小音符使用较轻的参考力度。'))
    return reports


def finish(data,report):
    # Three small inner pitches in bar 69 are tied across the first 1.5 beats.
    # Some overlapping tie curves were not paired by the geometry matcher.
    start=data['measures'][68]['start'];es=data['events']
    for a_beat,b_beat in [(0,.5),(.5,1)]:
        aa=[e for e in es if e['hand']=='R' and abs(e['beat']-start-a_beat)<1e-7]
        bb=[e for e in es if e['hand']=='R' and abs(e['beat']-start-b_beat)<1e-7]
        for b in bb:
            a=next((e for e in aa if e['midi']==b['midi']),None)
            if a is None:continue
            assert a.get('tieTo',b['id'])==b['id'] and b.get('tieFrom',a['id'])==a['id']
            a['tieTo']=b['id'];b['tieFrom']=a['id'];b.pop('soundDuration',None)
    for e in es:
        if 'tieFrom' in e:continue
        tail=e;seen=set()
        while 'tieTo' in tail:
            assert tail['id'] not in seen;seen.add(tail['id']);tail=es[tail['tieTo']]
        e['soundDuration']=tail['beat']+tail['duration']-e['beat']
    small=[e for e in es if e.get('noteSize')=='small']
    report['smallNoteReview']=dict(sourceHeads=len(small),meteredHeads=sum(not e['grace'] for e in small),ornamentHeads=sum(e['grace'] for e in small),referenceVelocity=.58,
        correctedStaffAssignment=dict(sourceMeasure=30,previousMeasure=33,previousMidi=103,midi=29),
        limitation='力度是较轻的参考演奏值；全曲未完成实际听音复核。')
    data['performanceNote']='已修正小符头误作装饰音：计拍内声部恢复原谱拍点和时值，连续装饰音依次起音，小音符使用较轻参考力度；修复一处低音误入高音谱表，保留七连音与九连音。全曲音高、漏音与实际听感仍未校对完成。'
    report['limitations'] += ['225 个小符头分别记录为计拍声部或装饰音；较轻力度是参考演奏解释，不是原谱给出的 MIDI 数值。']
