"""Readings of independent voices, tuplets and tremolo in the supplied PDFs.

Coordinates and group counts deliberately fail if detector evidence changes.
Only the passages enumerated here are rhythm reviewed.
"""
import copy

def apply(sid,pages):
    if sid not in ('ge-qian','pu-gong-ying-de-yue-ding'):return []
    rows=[(p,s,m) for p in pages for s in p['systems'] for m in s['measures']];out=[]
    def setup(n):
        p,s,m=rows[n-1];r,l=[st['index'] for st in s['staves']]
        def sel(st,pred=lambda g:True):return sorted([g for g in m['groups'] if g['staff']==st and pred(g)],key=lambda g:g['x'])
        def seq(gs,ds=None,start=0):
            ds=[g['duration'] for g in gs] if ds is None else ds
            assert len(gs)==len(ds),(sid,n,len(gs),len(ds))
            for g,d in zip(gs,ds):g.update(reviewedBeat=start,duration=d);start+=d
            return start
        def times(gs,bs,ds=None):
            assert len(gs)==len(bs),(sid,n,len(gs),len(bs))
            for i,(g,b) in enumerate(zip(gs,bs)):
                g['reviewedBeat']=b
                if ds is not None:g['duration']=ds[i]
        return p,s,m,r,l,sel,seq,times
    if sid=='pu-gong-ying-de-yue-ding':
      for n in (17,18,25,49,51,53,54,55,56,57,60,61,67,68,69,70,72):
        p,s,m,r,l,sel,seq,times=setup(n)
        if n in (17,25):
            if n==25:
                wrong=sel(l,lambda g:425<g['x']<462 and g['y']<s['staves'][1]['top']-10)
                assert len(wrong)==3,len(wrong)
                for g in wrong:
                    g['staff']=r
                    for h in g['notes']:h['pitchStaff']=r
            rr=sel(r);times(rr,[0,0,.5,1,1,1.5,2,2,2.5,3,3,3.75])
            rr[-3]['duration']=rr[-2]['duration']=.75
            ll=sel(l);times(ll,[0,0,1,2,2,3])
        elif n==18:
            times(sel(r),[0,0,1,2,2,2.5,3,3,3.5]);times(sel(l),[0,0,1,2,2,3])
        elif n==49:
            times(sel(r),[0,0,1,1.5,2,2,2.5,3,3,3.5])
            seq(sel(l),[.5]+[1/6]*6+[.5,.5]+[1/6]*6+[.5])
        elif n==51:
            rr=sel(r);rr[1]['reviewedBeat']=0;seq(rr[:1]+rr[2:],[.5]+[1/6]*9+[.5]*4)
            seq(sel(l),[.5,1/3,1/6,1/6,1/3,1/6,1/3]+[1/6]*6+[.25,.25,.5])
        elif n==53:
            rr=sel(r);rr[0]['reviewedBeat']=0;seq(rr[1:],[.5,1.5]+[.5]*4)
            seq(sel(l),[1/6]*8+[1/3,1/3]+[1/6]*9+[.5])
        elif n==54:
            seq(sel(r,lambda g:g['direction']=='up'),[.5]*8)
            seq(sel(r,lambda g:g['direction']=='down'),[.5]*6+[1])
            ll=sel(l);seq(ll[:13],[1/6]*9+[.5]+[1/6]*3)
            seq(ll[13:],[.125]*3+[1/6]*3+[.5],2.625) # Printed 32nd rest at 2.5.
        elif n==55:
            seq(sel(r));seq(sel(l),[1/6]*3+[.125]*4+[.1]*5+[.125]*4+[.75,.125,.125,1])
        elif n==56:
            rr=sel(r);times(rr,[0,0,1,1.5,1.5,2,2,2.5,2.75,3,3,3+1/3,3+2/3])
            for g in rr:
                if g['notes'] and g['reviewedBeat']>=3:g['duration']=1/3
            seq(sel(l),[1,.25,.75,2/3,1/3]+[1/3]*3)
        elif n==57:
            rr=sel(r);times(rr,[0,0,.5,.625,.75,.875,1,1,1.5,1.5,2,2,3,3,3.5]);rr[2]['duration']=.125
            seq(sel(l))
        elif n==60:
            rr=sel(r);up=sel(r,lambda g:g['direction']=='up');seq(up,[1.5,.5,1])
            other=sel(r,lambda g:g['direction']!='up');seq(other,[1/6]*12+[1/3]*3+[1,1/3,1/3,1/3])
            # Quarter rest and lower triplet attack share beat 3.
            tail=other[-4:];times(tail,[3,3,3+1/3,3+2/3])
            seq(sel(l),[1,.25,.5,.25,.5,.5,.5,.5])
        elif n==61:
            rr=sel(r);times(rr,[0,0]+[.5+i/12 for i in range(6)]+[1,1,1.5,1.5,2,2,2+1/3,2+1/3,2+2/3,2+2/3,3,3,3.5])
            for i in range(2,8):rr[i]['duration']=1/12
            for g in rr:
                if 2<=g['reviewedBeat']<3:g['duration']=1/3
            seq(sel(l),[.75]+[1/12]*3+[1/6]*3+[.5,.5,.25,.25]+[1/3]*3)
        elif n==67:
            seq(sel(r),[1/3]*12);seq(sel(l),[.5,.5,1/3,1/3,1/6,1/6,.5,.5,1])
        elif n==68:
            seq(sel(r),[1/3]*3+[.5,.5]+[1/3]*3+[.5,.5]);seq(sel(l),[1/3]*12)
        elif n==69:
            seq(sel(r),[.5,1/6,1/3,.5,.5,1/3,1/6,1/6,1/3]+[1/3]*3)
            seq(sel(l),[1/3]*9+[.5,.5])
        elif n==70:
            seq(sel(r),[.2]*5+[1/3]*3+[1/6]*12)
            seq(sel(l),[1/3]*3+[.5,1/6,1/3]+[.25,.25,.5,.5,.5])
        elif n==72:
            seq(sel(r),[.25]*4+[.5,.5]+[1/3]*3+[1])
            seq(sel(l),[.25,.25]+[1/6]*3+[1/3]*5+[1/6]*2+[.5,.5])
        assert all('reviewedBeat' in g for g in m['groups']),(sid,n,'missing onset')
        assert max(g['reviewedBeat']+g['duration'] for g in m['groups'])<=4+1e-6,(sid,n,'overflow')
        out.append(dict(measure=n,reason='对照原谱分开持续声部与流动声部，重读三连音、六连音、五连音和休止，修正跨谱表误分配。'))
    else:
      # Leland's ottava labels are glyphs rather than PDF text; the generic
      # textual-label detector misses these explicit printed brackets.
      for number in (25,26):
          p,sy,mm=rows[number-1];p.setdefault('reviewedOctaves',[]).append((sy['staves'][0]['index'],mm['left'],mm['right'],12))
      p,sy,mm=rows[48];p.setdefault('reviewedOctaves',[]).append((sy['staves'][0]['index'],364,mm['right'],12))
      for number in (17,21,42,46,50,54,55,57):
          p,sy,mm=rows[number-1];st=sy['staves'][1]['index'];gg=sorted([g for g in mm['groups'] if g['staff']==st and g['notes']],key=lambda g:g['x']);first=gg[0]
          p.setdefault('reviewedOctaves',[]).append((st,min(h['ox'] for h in first['notes'])-.01,max(h['ox'] for h in first['notes'])+.01,-12))
      p,sy,mm=rows[52];st=sy['staves'][1]['index'];last=max([g for g in mm['groups'] if g['staff']==st and g['notes']],key=lambda g:g['x'])
      p.setdefault('reviewedOctaves',[]).append((st,min(h['ox'] for h in last['notes'])-.01,mm['right'],-12))
      rows[24][2]['reviewedKey']=-4;rows[29][2]['reviewedKey']=-1;rows[48][2].update(reviewedKey=-5,reviewedMeter=3.25);rows[49][2]['reviewedMeter']=4
      for n in (4,5,24,25,26,29,30,31,32,41,49,51,52,53):
        p,s,m,r,l,sel,seq,times=setup(n)
        if n in (5,25,26,29,30,31,32,41,53):
            for g in m['groups']:
                if n!=53 and g['staff']!=r:continue
                if g['grace']:
                    g['grace']=False
                    for h in g['notes']:h['grace']=False;h['smallNotehead']=True;h['reviewedVelocity']=.58;h['reviewedVoiceRole']='inner-voice'
        if n==4:
            rr=sel(r);seq(rr[:3]);rr[-1]['reviewedBeat']=3.5
            # Four tremolo beams: alternate the two printed chords through
            # their shared dotted-quarter span; neither chord adds 1.5 beats.
            m['groups'].remove(rr[3]);m['groups'].remove(rr[4])
            for i in range(24):
                g=copy.deepcopy(rr[3+i%2]);g.update(reviewedBeat=2+i/16,duration=1/16,sourceRepeat='printed-measured-tremolo');m['groups'].append(g)
            seq(sel(l))
        elif n==5:
            seq(sel(r,lambda g:g['direction']=='up'))
            seq(sel(r,lambda g:g['direction']=='down'),[1,1],2);seq(sel(l))
        elif n==24:
            seq(sel(r,lambda g:g['direction']=='up'));seq(sel(r,lambda g:g['direction']!='up'));seq(sel(l))
        elif n in (25,26,29):seq(sel(r));seq(sel(l))
        elif n==30:
            rr=sel(r);held=[g for g in rr if g['direction']=='down' and 149<g['x']<152]
            assert len(held)==1
            held[0].update(reviewedBeat=2.5,duration=1)
            seq([g for g in rr if g not in held]);seq(sel(l)[1:]);sel(l)[0].update(reviewedBeat=0,duration=.08)
        elif n==31:
            times(sel(r),[0,0,.5,.75,1,1.25,1.5,1.75,2,2,2.5,2.75,3,3,3.25,3.75]);seq(sel(l))
        elif n==32:
            times(sel(r),[0,0,1,1.75,2,2,2.5,3,3.5,3.75]);seq(sel(l))
        elif n==41:
            rr=sel(r);times(rr,[0,0,.5,1,1.5,2,2,2.5,3,3.5])
            seq(sel(l),[.75]+[.25]*5+[.5]+[1/12]*15+[.25])
        elif n==49:
            for st in (r,l):
                gg=sel(st)
                for j in range(3):
                    seq(gg[j*4:j*4+3],[1/30]*3,max(0,j-.1))
                    gg[j*4+3].update(reviewedBeat=.1 if j==0 else j,duration=.9 if j==0 else 1)
                rest=[g for g in gg[12:] if not g['notes']]
                for g in rest:g['reviewedBeat']=2 if g['duration']==.5 else 2.5
                seq([g for g in gg[12:] if g['notes']],[1/12]*3,3 if st==r else 2.75)
        elif n==51:
            seq(sel(r,lambda g:g['direction']=='up'));seq(sel(r,lambda g:g['direction']=='down'),[.5,.5,.5,.25,.25,1,.25,.25,.5])
            ll=sel(l);seq(ll[:16],[.5]+[1/12]*15);ll[16].update(reviewedBeat=1.9,duration=.1)
            seq(ll[17:],[.5]+[1/16]*4+[.25,.25,.25,.5],2)
        elif n==52:
            rr=sel(r);times(rr,[0,.5,.75,1,1,1.75,2,2,2.5,2.75,3,3.5])
            ll=sel(l);seq(ll[:6],[.5]+[.1]*5)
            seq(ll[6:11],[1/12]*3+[1/6,.5],1+1/12)
            ll[11].update(reviewedBeat=1.9,duration=.1)
            seq(ll[12:22],[.5]+[1/12]*8+[1/3],2)
            ll[22].update(reviewedBeat=3.625,duration=.375)
        elif n==53:
            up=sel(r,lambda g:g['direction']=='up');seq(up,[1,1,.5,.5,.5,.5])
            seq(sel(r,lambda g:g['direction']!='up'),[1/6]*9+[.25,1/12,1/6,.5]+[.125]*4)
            ll=sel(l);seq(ll[:23],[1/6]*9+[.25,1/12,1/6,.5]+[.1]*5+[.25,.25]+[1/12]*3)
            ll[23].update(reviewedBeat=3.9,duration=.1)
        length=3.25 if n==49 else 4
        assert all('reviewedBeat' in g for g in m['groups']),(sid,n,'missing onset')
        assert max(g['reviewedBeat']+g['duration'] for g in m['groups'])<=length+1e-6,(sid,n,'overflow',max(g['reviewedBeat']+g['duration'] for g in m['groups']))
        out.append(dict(measure=n,reason='按原谱重读独立声部、小符头实际节拍、轮奏与连音；49 小节 13/16，25/30/49 小节转调。'))
    return out
