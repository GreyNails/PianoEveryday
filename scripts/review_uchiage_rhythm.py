"""Rhythm readings from supplied Uchiage Hanabi PDF pages 1,2,3,4,7.

The 71st bar's 1.5-beat final rest is printed and intentionally retained.
"""
import copy

def apply(pages):
    ms=[m for p in pages for s in p['systems'] for m in s['measures']]
    def setbeats(number,beats):
        gs=ms[number-1]['groups'];assert len(gs)==len(beats),(number,len(gs),len(beats))
        for g,b in zip(gs,beats):g['reviewedBeat']=b
    twin=[0,0,0,0,.5,.5,1,1,1.5,1.5,2,2,2.5,2.5,2.5,3,3,3.5,3.5]
    setbeats(6,twin);setbeats(34,twin)
    setbeats(8,[0,0,.5,1,1.5,2,2,2.5,2.5,3,3,3.5,3.5])
    # An exceptionally low bass note belongs to bar 24, not the next system's
    # upper staff in bar 26. Keep the original PDF glyph and accidental.
    wrong=ms[25]['groups'].pop(15)
    assert abs(wrong['x']-489.3)<.5 and abs(wrong['y']-489.6)<.5
    wrong['staff']=5
    for n in wrong['notes']:n['staff']=5
    for c in pages[1]['chars']:
        if 479<c['ox']<491 and 486<c['y']<494:c['staff']=5
    gs=ms[23]['groups'];timing={1:0,5:2,6:2,7:2,8:2.125,9:2.125,10:2.25,11:2.25,12:2.375,13:2.375,14:2.5,15:3,16:3,18:3.5,19:3.75}
    out=[]
    for i,b in timing.items():g=copy.deepcopy(gs[i]);g['reviewedBeat']=b;out.append(g)
    # Measured two-note tremolos: alternating thirty-seconds, not two long
    # sequential notes. Reuse the same printed heads with explicit provenance.
    for pair,start,length in [((gs[0],gs[3]),0,2),((gs[2],gs[4]),0,2),((wrong,gs[17]),2.5,1.5)]:
        for i in range(round(length*8)):
            g=copy.deepcopy(pair[i%2]);g['duration']=.125;g['reviewedBeat']=start+i/8;g['sourceRepeat']='printed-measured-tremolo';out.append(g)
    ms[23]['groups']=out
    setbeats(26,[0,0,0,.5,1,1,1.25,1.5,1.75,2,2,2,2.5,2.5,2.5,3,3,3,3.25,3.25,3.5,3.75])
    setbeats(45,[0,0,0,.75,1,1,1,1.5,2,2,2,2.75,3,3,3.25,3.25,3.5])
    for g in ms[45]['groups']:g['reviewedBeat']=round((g['x']-315.3)/15.69)/4
    # The displaced second of the final beamed eighth is not a quarter note.
    ms[45]['groups'][31].update(reviewedBeat=3.5,duration=.5)
    setbeats(51,[0,0,0,0,.5,1,1,1,1.5,1.5,2,2,2,2,2.5,2.5,2.5,3,3,3,3.5,3.5])
    # Printed six-note groups may carry a 6 on each staff. Apply the ratio once.
    for number in [80,81,82,83]:
        gs=ms[number-1]['groups'];upper=min(g['staff'] for g in gs)
        for staff in [upper,upper+1]:
            voice=sorted((g for g in gs if g['staff']==staff),key=lambda g:g['x'])
            if number==80 or number==81 and staff==upper or number==82 and staff==upper:
                assert len(voice)==24;ds=[1/6]*24
            elif number==81:
                assert len(voice)==22;ds=[1/6]*21+[.5]
            elif number==82:
                assert len(voice)==18;ds=[1/6]*9+[.5]+[.25]*8
            elif staff==upper:
                assert len(voice)==19;ds=[1/6]*15+[.5,.5,.25,.25]
            else:
                assert len(voice)==12;ds=[.25]*8+[.5,.25,.25,1]
            t=0
            for g,d in zip(voice,ds):g['duration']=d;g['reviewedBeat']=t;t+=d
            assert abs(t-4)<1e-6,(number,staff,t)
    return [dict(measures=[6,8,24,26,34,45,46,51,80,81,82,83],reason='直接看谱校正独立声部、震音、六连音及错分谱表；不按整小节缩放。第71小节末尾的1.5拍休止为原谱记号，保留。')]
