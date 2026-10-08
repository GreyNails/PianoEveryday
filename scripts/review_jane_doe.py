"""Specific readings of Animenz's supplied JANE DOE PDF, not certification.

Positions use PDF points; retain every source glyph. In this 9/8 engraving,
the quintuplets/quartuplets/eight-note groups each occupy a dotted beat.
"""
def apply(pages):
    reviewed=[]
    def measure(pi,si,mi):return pages[pi]['systems'][si]['measures'][mi]
    def finish(pi,si,mi,reason):
        m=measure(pi,si,mi)
        assert all('reviewedBeat' in g for g in m['groups'])
        assert max(g['reviewedBeat']+g['duration'] for g in m['groups'])<=4.500001
        reviewed.append(dict(page=pi+1,system=si+1,localMeasure=mi+1,reason=reason))
    # Two five-sixteenth runs fill the first two dotted-quarter beats.
    for pi,si,mi in [(1,3,1),(1,4,0)]:
        gs=measure(pi,si,mi)['groups']
        for st in {g['staff'] for g in gs}:
            t=0
            for g in sorted((g for g in gs if g['staff']==st),key=lambda g:g['x']):
                if g.get('tuplet')==5:g['duration']=.3
                g['reviewedBeat']=t;t+=g['duration']
            assert abs(t-4.5)<1e-7
        finish(pi,si,mi,'两组五连音各占附点四分音符（1.5 个四分拍），非普通 5:4。')
    # Quartuplets, including two left-hand notes written on the upper staff.
    gs=measure(2,0,3)['groups'];left=[g for g in gs if g['staff']==1]
    assert len(left)==9
    for i,g in enumerate(left):
        g['reviewedBeat']=i*.375 if i<8 else 3
        if i<8:g['duration']=.375
        if i in (6,7):
            for n in g['notes']:n['pitchStaff']=0
    right=[g for g in gs if g['staff']==0]
    assert len(right)==5
    for g,b in zip(right,[0,1.5,3,3.5,4]):g['reviewedBeat']=b
    finish(2,0,3,'四连音各占 1.5 拍；末两音跨到上谱表，保持左手并按高音谱号取音高。')
    # Four ordinary sixteenths then eight 32nds in one dotted-quarter beat.
    gs=measure(5,1,2)['groups']
    for st in {g['staff'] for g in gs}:
        t=0
        for g in sorted((g for g in gs if g['staff']==st),key=lambda g:g['x']):
            if g.get('tuplet')==8:g['duration']=.1875
            g['reviewedBeat']=t;t+=g['duration']
        assert abs(t-4.5)<1e-7
    finish(5,1,2,'八连音占最后一个附点四分拍，与左手普通八分音符独立对齐。')
    # Displaced heads belong to simultaneous independent voices.
    for pi,si,mi,beats in [
        (1,1,4,[0,0,0,0,1.5,3,3,3,3,4]),
        (5,5,2,[0,0,0,0,.5,1,1.5,1.5,2,2.5,3,3,3,3,3.5,4]),
    ]:
        gs=measure(pi,si,mi)['groups'];assert len(gs)==len(beats)
        for g,b in zip(gs,beats):g['reviewedBeat']=b
        finish(pi,si,mi,'独立长音和横向错开的符头同时起拍，不按印刷横坐标顺次演奏。')
    # Ottava glyph and broken line are drawn as outlines in this PDF.
    pages[6]['reviewedOctaves']=[(6,97,560,12),(8,0,227,12)]
    reviewed.append(dict(page=7,reason='第 4 行首小节第 4 个八分音符起升八度，持续到第 5 行第 2 小节结束。'))
    return reviewed
