"""Clockwork Dancers: literal PDF voices, tuplets and measured tremolos.

The three-stroke two-note tremolos in 44–46 each occupy 1.5 quarter beats.
Tempo numbers are reference interpretations of the printed Italian words;
this edition supplies no metronome numbers.
"""
import copy


def apply(pages):
    rows=[(p,s,m) for p in pages for s in p['systems'] for m in s['measures']]
    assert len(rows)==75
    notes=[]
    for n,key in {1:-3,28:2,29:-2,30:2,31:-2,32:-3,37:-3,56:-5,61:0,64:-3,67:-2}.items():
        rows[n-1][2]['reviewedKey']=key
    for n,bpm in {1:100,20:144,37:176,67:66,72:62,73:58,74:52,75:46}.items():
        rows[n-1][2]['reviewedTempo']=bpm
    rows[50][2]['reviewedMeter']=2;rows[51][2]['reviewedMeter']=4
    for number in range(37,67):
        p,s,m=rows[number-1];r,l=[st['index'] for st in s['staves']];gs=m['groups']
        if number==38:
            wrong=[g for g in gs if g['staff']==l and g['y']<s['staves'][0]['bottom']+15]
            assert len(wrong)==1
            wrong[0]['staff']=r
            for n in wrong[0]['notes']:n['pitchStaff']=r
        def select(staff,pred=lambda g:True):return sorted([g for g in gs if g['staff']==staff and pred(g)],key=lambda g:g['x'])
        def seq(selected,durations,start=0):
            assert len(selected)==len(durations),(number,len(selected),len(durations))
            t=start
            for g,d in zip(selected,durations):g.update(reviewedBeat=t,duration=d);t+=d
            return t
        if number in (37,38,39):
            rr=select(r);ll=select(l,lambda g:g['duration']!=4)
            assert len(rr)==8 and len(ll)==(7 if number==37 else 8)
            for i,g in enumerate(rr):g.update(reviewedBeat=i/2,duration=.5 if number==37 and i==0 else .25)
            for i,g in enumerate(ll):g.update(reviewedBeat=(.75 if number==37 else .25)+i/2,duration=.25)
            for g in select(l,lambda g:g['duration']==4):g['reviewedBeat']=0
        elif number==40:
            seq(select(r),[.25]*14+[.5]);seq(select(l),[1,1,1,.5,.5])
        elif number in (41,42,43):
            # These are normal-size, independently stemmed sixteenth notes,
            # not grace notes. The upper eighth rests belong to that voice.
            first=min(g['x'] for g in gs)
            spacing=14.8 if number==41 else 15.0
            for g in gs:
                b=round((g['x']-first)/spacing)/4
                if number==43 and g['x']>510:b=3 if g['x']<525 else 3.5
                g['reviewedBeat']=b
        elif number in (44,45,46):
            rr=select(r);ll=select(l)
            pair=rr[-2:];assert [g['duration'] for g in pair]==[1.5,1.5]
            seq(rr[:-2],[.5,1,.5,.5] if number==44 else [.5]*5)
            # Printed triplet brackets in 44–45, repeated figure in 46.
            # Two triplet groups + four 32nds occupy the final 1.5 beats.
            left_ds=([1,1,.5] if number==44 else [.5]*5)+[1/6]*6+[.125]*4
            assert abs(seq(ll,left_ds)-4)<1e-7
            for g in pair:gs.remove(g)
            for i in range(12):
                g=copy.deepcopy(pair[i%2]);g.update(reviewedBeat=2.5+i/8,duration=.125,sourceRepeat='printed-measured-tremolo')
                gs.append(g)
        elif number in (47,48,49,50,51,52,53,54,56,57,58,59,65,66):
            # Independent monophonic hands (chords count as one onset).
            for st in [r,l]:
                vv=select(st);ds=[g['duration'] for g in vv]
                seq(vv,ds)
        elif number==55:
            seq(select(r),[2,.5]+[1/6]*3+[.125]*8)
            seq(select(l),[.25]*8+[1,.5,.5])
        elif number in (60,62):
            seq(select(r,lambda g:g['direction']=='up'),[1]*4)
            seq(select(r,lambda g:g['direction']=='down'),[.25]*16)
            seq(select(l),[1]+[.5]*6)
        elif number in (61,63):
            seq(select(r,lambda g:g['direction']=='up'),[1]*3)
            rr=select(r,lambda g:g['direction']=='down')
            assert len(rr)==5
            for g,b,d in zip(rr,[.25,.5,.75,3,3.5],[.25]*3+[.5]*2):g.update(reviewedBeat=b,duration=d)
            ll=select(l);assert len(ll)==14
            ll[0].update(reviewedBeat=0,duration=1)
            ll[1].update(reviewedBeat=1,duration=1)
            seq(ll[2:],[.25]*12,start=1)
        elif number==64:
            seq(select(r),[.25]*16);seq(select(l),[1]*4)
        assert all('reviewedBeat' in g for g in gs),number
        length=2 if number==51 else 4
        assert max(g['reviewedBeat']+g['duration'] for g in gs)<=length+1e-6,number
        notes.append(dict(measure=number,reason='按原谱独立声部对齐；44–46 展开三道斜杠震音并校准连音；51 保留原谱两拍短小节；55 校准三连音。'))
    notes.append(dict(reason='按原谱记录变调和重降号；文字速度采用可调整参考值，末段按 rit. 做参考渐慢。',referenceTempos={1:100,20:144,37:176,67:66,72:62,73:58,74:52,75:46}))
    return notes
