"""Readings of the supplied Musicnotes edition's later notation."""
import copy

def apply(pages):
    rows=[(p,s,m) for p in pages for s in p['systems'] for m in s['measures']]
    assert len(rows)==107
    for p in pages:p['reviewedOctavesComplete']=True
    corrections=[]
    for n in [53,94]:rows[n-1][2]['reviewedMeter']=4
    rows[53][2]['reviewedMeter']=3
    rows[55][2]['reviewedTempo']=60
    # Short 8va/8vb indications without a dashed continuation affect one
    # chord only. Long lines cover the explicitly indicated bar range.
    for n in list(range(44,52))+[52,53,58,59,60,63,68,72,77,89,90,93]:
        p,s,m=rows[n-1];staff=s['staves'][0 if n<61 else 1]['index']
        gs=[g for g in m['groups'] if g['staff']==staff and g['notes']]
        xs=sorted(set(round(g['x'],1) for g in gs))
        if 44<=n<=51:a=xs[2]-2;b=xs[2]+8
        elif n==58:a=xs[-1]-2;b=m['right']
        elif n in (63,68,72,77,89,90):a=m['left'];b=xs[0]+8
        else:a=m['left'];b=m['right']
        p.setdefault('reviewedOctaves',[]).append((staff,a,b,12 if n<61 else -12))
    p,s,m=rows[80];r,l=[st['index'] for st in s['staves']]
    for selector,onsets in [
        (lambda g:g['staff']==r and g['notes'] and g['direction']=='up',[0,1,2]),
        (lambda g:g['staff']==r and g['notes'] and g['direction']=='down',[b+t for b in range(3) for t in [.25,.5,.75]]),
        (lambda g:g['staff']==r and not g['notes'],[0,1,2]),
        (lambda g:g['staff']==l,[i/2 for i in range(6)]),
    ]:
        gs=sorted(filter(selector,m['groups']),key=lambda g:g['x']);assert len(gs)==len(onsets)
        for g,b in zip(gs,onsets):g['reviewedBeat']=b
    corrections.append(dict(measure=81,reason='四分音符旋律、右手十六分伴奏和左手八分和弦独立对齐。'))
    # The last variation starts at beat one after the opening silent beat.
    p,s,m=rows[103];r,l=[st['index'] for st in s['staves']]
    rr=sorted([g for g in m['groups'] if g['staff']==r],key=lambda g:g['x'])
    assert len(rr)==10
    for g,b in zip(rr,[0]+[1+i/4 for i in range(8)]+[3]):g['reviewedBeat']=b
    rr[0]['duration']=1
    for g in m['groups']:
        if g['staff']!=l:continue
        x=g['x'];g['reviewedBeat']=0 if x<350 else 1 if x<400 else 2 if x<480 else 3 if x<520 else 3.5
    corrections.append(dict(measure=104,reason='按独立声部核对尾段起拍；开头留一拍，十六分音符乐句占第 2–3 拍。'))
    # Measured three-stroke tremolos alternate the two printed pitch sets.
    # Before expanding, establish every other voice's literal timing.
    from compile_library_drafts import timing
    for number in range(102,108):
        p,s,m=rows[number-1];gs=m['groups'];r,l=[st['index'] for st in s['staves']]
        if number!=107:
            timing(gs,4,s['staves'][0]['step']*2)
            for g in gs:g.setdefault('reviewedBeat',g['localBeat'])
        else:
            beats=[0,0,0,0,1,1,2,2,2,3,3]
            assert len(gs)==len(beats)
            for g,b in zip(gs,beats):g['reviewedBeat']=b
            gs[8]['duration']=2;gs[8]['symbol']='\ue4e4'
        pairs=[]
        if number<=106:
            left=sorted([g for g in gs if g['staff']==l and g['notes'] and g['duration']==2],key=lambda g:g['x'])
            assert len(left)==2;pairs.append((left,1,2))
            if number>=105:
                right=sorted([g for g in gs if g['staff']==r and g['notes'] and g['duration']==2],key=lambda g:g['x'])
                assert len(right)==2;pairs.append((right,1,2))
        else:pairs=[([gs[0],gs[4]],0,2),([gs[6],gs[9]],2,2),([gs[3],gs[5]],0,2),([gs[7],gs[10]],2,2)]
        for pair,start,length in pairs:
            for g in pair:gs.remove(g)
            for i in range(round(length*8)):
                g=copy.deepcopy(pair[i%2]);g.update(reviewedBeat=start+i/8,duration=.125,sourceRepeat='printed-measured-tremolo')
                gs.append(g)
        corrections.append(dict(measure=number,reason='原谱三道斜杠的两音／和弦震音展开为三十二分音符，独立声部与休止保留。'))
    return corrections
