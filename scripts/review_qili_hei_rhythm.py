"""Local readings of the supplied Qi Li Xiang and Black Sweater PDFs.

Tuplet numbers, independent stems, cross-staff heads and ottava brackets are
read separately from rhythmic closure. Unmarked rubato is not inferred.
"""

def apply(sid,pages):
    if sid not in ('qi-li-xiang','hei-se-mao-yi'):return []
    rows=[(p,s,m) for p in pages for s in p['systems'] for m in s['measures']]
    notes=[]
    def voices(number):
        p,s,m=rows[number-1];r,l=[st['index'] for st in s['staves']]
        def select(st,pred=lambda g:True):return sorted([g for g in m['groups'] if g['staff']==st and pred(g)],key=lambda g:g['x'])
        def seq(gs,ds=None,start=0):
            ds=ds if ds is not None else [g['duration'] for g in gs]
            assert len(gs)==len(ds),(sid,number,len(gs),len(ds))
            for g,d in zip(gs,ds):g.update(reviewedBeat=start,duration=d);start+=d
            return start
        return p,s,m,r,l,select,seq
    def octave(p,st,a,b,shift):p.setdefault('reviewedOctaves',[]).append((st,a,b,shift))
    if sid=='qi-li-xiang':
        for n in (4,27,41,42,43,44,48,56,72,80):
            p,s,m,r,l,sel,seq=voices(n)
            if n==4:
                seq(sel(r),[.5]+[.25]*7+[.5]+[.25]*5);seq(sel(l))
            elif n==27:
                seq(sel(r,lambda g:g['direction']=='down'),[.5,.5,1])
                rr=sel(r,lambda g:g['direction']=='up');seq(rr,[1.5]+[.5]*5)
                # Bass upper eighths and the lower quarter share stems/columns.
                seq(sel(l,lambda g:g['direction']=='up'),[.5]*4)
                seq(sel(l,lambda g:g['direction']!='up'),[1,.25,.25,.5,.25,.25,.5,.5],.5)
            elif n in (41,42,43):
                seq(sel(r));seq(sel(l))
                octave(p,r,m['left'],m['right'],12)
            elif n==44:
                seq(sel(r,lambda g:g['direction']=='up'),[.5]*8)
                seq(sel(r,lambda g:g['direction']=='down'),[.5]*2,3)
                seq(sel(l));octave(p,r,m['left'],m['right'],12)
            elif n==48:
                # Second upper-staff triplet dips close to the bass staff.
                wrong=sel(l,lambda g:399<g['x']<401)
                assert len(wrong)==2
                g=min(wrong,key=lambda g:g['y']);g['staff']=r
                for h in g['notes']:h['pitchStaff']=r
                seq(sel(r,lambda g:g['direction']=='down'),[1/3]*6)
                seq(sel(r,lambda g:g['direction']!='down'),[.5]*7+[.25]*2)
                low=sel(l,lambda g:g['direction']=='down')
                seq(low,[2/3,1/3]+[1/3]*3+[.25]*4)
                seq(sel(l,lambda g:g['direction']!='down'),[.5,.5,.5],2)
                # The second upper bass eighth starts at beat 3, not 2.5.
                vv=sel(l,lambda g:g['direction']!='down')
                vv[1]['reviewedBeat']=3;vv[2]['reviewedBeat']=3.5
            elif n==56:
                rr=sel(r);seq(rr[:2],[1,1])
                rr[1]['reviewedBeat']=0
                seq(rr[2:5],[.5,.5,1],1)
                seq(rr[5:],[1/14]*14,3)
                octave(p,r,439.48,499.018,12)  # Original dashed bracket: 454.48–498.02.
                seq(sel(l),[.5,.25,.25,.25,.5,.25,.25,.25,.25,.125,.125,.5,.25,.25])
            elif n==72:
                seq(sel(r,lambda g:g['direction']=='down'),[.5]*4)
                rr=sel(r,lambda g:g['direction']=='up');seq(rr,[.5,.5,.5,.5,.25,.25])
                seq(rr[1:],[.5,.5,.5,.25,.25],2)
                seq(sel(l))
            elif n==80:
                rr=sel(r);seq(rr[:2],[.5,.5]);rr[1]['reviewedBeat']=0
                for g in rr[2:6]:g['reviewedBeat']=.5 if g['x']<340 else 1
                seq(rr[6:],[1/9]*18,2)
                ll=sel(l);seq(ll[:6]);seq(ll[6:],[.5,.375,.125,.5,.5],2)
                ll[8]['grace']=True
            assert all('reviewedBeat' in g for g in m['groups']),(sid,n)
            assert max(g['reviewedBeat']+g['duration'] for g in m['groups'])<=4+1e-7,(sid,n)
            notes.append(dict(measure=n,reason='独立声部按谱对齐；48 跨谱表三连音；56 两组七连音；80 两组九连音。'))
        p,s,m=rows[85];octave(p,s['staves'][1]['index'],m['left'],m['right'],-12)
    else:
        # The metronome change is engraved before the 2/4 section.
        rows[4][2]['reviewedTempo']=62
        for n in (3,4,13,28,33,34,41,42,43,78,86,90,91,92,97,116,117,118,119,120):
            p,s,m,r,l,sel,seq=voices(n)
            if n==3:
                seq(sel(r),[.75,.25,.5,.5,.25,.25,.5]);seq(sel(l))
            elif n==4:
                seq(sel(r),[.25,2],.75)
                seq(sel(l,lambda g:g['direction']=='up'),[.25]*3)
                seq(sel(l,lambda g:g['direction']=='down'),[3])
            elif n==43:
                seq(sel(r),[.5,.5,.5,.25,.25]);seq(sel(l))
            elif n==78:
                seq(sel(r),[.25]+[1/12]*9+[1/12]*6+[1/12]*3+[.25])
                seq(sel(l));octave(p,r,119.64,193.65,12)  # 8va starts mid-run, ends after the first note of beat 2 (compare head centers, not glyph origins).
            elif n==86:
                seq(sel(r),[.5]*4);seq(sel(l))
            elif n==97:
                # Upper chord's long stem crosses the bass; preserve its pitch
                # in the written bass clef, with the two bass notes independent.
                wrong=sel(l,lambda g:g['direction']=='up');assert len(wrong)==1
                g=wrong[0];g['staff']=r
                for h in g['notes']:h['pitchStaff']=l
                seq(sel(r),[.5,.5,.5,.25,.25]);seq(sel(l))
            elif n==120:
                seq(sel(r));seq(sel(l),[2])
            else:
                seq(sel(r));seq(sel(l))
            length=3 if n<=4 else 2
            assert all('reviewedBeat' in g for g in m['groups']),(sid,n)
            assert max(g['reviewedBeat']+g['duration'] for g in m['groups'])<=length+1e-7,(sid,n)
            notes.append(dict(measure=n,reason='按原谱重排独立声部，保留休止、切分、三连音与跨谱表和弦。'))
        for number in (55,119,120):
            p,s,m=rows[number-1];r=s['staves'][0]['index']
            a=m['left']
            if number==55:a=min(n['ox'] for g in m['groups'] if g['staff']==r and not g['grace'] for n in g['notes'])-.01
            octave(p,r,a,m['right'],12)
    return notes
