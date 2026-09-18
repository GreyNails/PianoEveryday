"""Source-specific corrections checked against the supplied page engravings.

Numbers refer to engraved physical measures, not performance occurrences.
No bar is stretched/normalised to hide a rhythm discrepancy.
"""
def apply_geometry_corrections(sid,page,system,m):
    gs=m['groups'];num=m['number']
    if sid=='tanjiro':
        if num==30:
            for g in gs:
                if 450<g['x']<453:g['x']=446.6 # displaced second in upper LH chord
        if num in (103,104):
            for g in gs:
                if g['direction']=='none':g['x']=min(h['x'] for h in gs)
        if num==45:
            for g in gs:
                if g['staff']%2==0 and g['direction']=='up':g['staff']+=1
        if num==87:
            # The inner eighth voice and the seven-note 32nd run start together.
            for g in gs:
                if 150<g['x']<152 and g['staff']%2==0:g['runStart']=True
    m['groups']=sorted(gs,key=lambda g:g['x'])

def sequence(groups,start=0):
    t=start
    for g in sorted(groups,key=lambda g:g['x']):g['localBeat']=t;t+=g['duration']
    return t

def apply_timing_corrections(sid,page,system,m):
    gs=m['groups'];num=m['number']
    if sid=='feng' and num==56:
        run=[g for g in gs if g['grace'] and g['staff']%2==0 and g['x']>410]
        assert len(run)==18
        for i,g in enumerate(run):g.update(grace=False,duration=1/36,localBeat=3.5+i/36,tuplet=9)
    if sid=='feng' and num==73:
        for g in gs:
            if g.get('symbol')=='\ue4e3':g['localBeat']=0
    if sid=='feng' and num in (51,52):
        # Independent dotted rhythm against the three 16ths in an eighth.
        # They have distinct x columns; their grids must not advance each other.
        for staff in (0,1):
            sub=[g for g in gs if g['staff']%2==staff and not g['grace']]
            if staff==1:sequence(sub)
            else:
                for direction in ('up','down'):
                    lane=[g for g in sub if g['direction']==direction or (g['kind']=='rest' and direction=='up')]
                    sequence(lane)
    if sid=='tanjiro' and num==45:
        rh=[g for g in gs if g['staff']%2==0 and not g['grace']]
        # Two 16th rests, each followed by fourteen 32nds.
        notes=[g for g in rh if g['notes']]
        assert len(notes)==29 # second group contains fifteen 32nds
        for i,g in enumerate(notes):g['localBeat']=(.25+i*.125) if i<14 else (2.125+(i-14)*.125)
        for g in gs:
            if g['staff']%2==1:
                if g['direction']=='down':g['localBeat']=[0,1,2,3][[h for h in gs if h['staff']%2==1 and h['direction']=='down'].index(g)]
                else:g['localBeat']=0 if g['x']<400 else 2
    if sid=='tanjiro' and num==78:
        rh=[g for g in gs if g['staff']%2==0 and not g['grace']]
        for g in rh:
            if g.get('tuplet')==9:g['duration']=.75/9
        sequence([g for g in rh if not (g['direction']=='up' and g['duration']==2)])
        for g in rh:
            if g['direction']=='up' and g['duration']==2:g['localBeat']=0
        sequence([g for g in gs if g['staff']%2==1 and not g['grace']])
    if sid=='tanjiro' and num in (80,81,82,83):
        rh=[g for g in gs if g['staff']%2==0 and not g['grace']]
        for g in rh:
            if g.get('tuplet') in (7,8):g['duration']=.75/g['tuplet']
        assert abs(sequence(rh)-4)<1e-6,(num,'RH sum',sequence(rh))
        lh=[g for g in gs if g['staff']%2==1 and not g['grace']]
        sequence([g for g in lh if g['direction']=='down'])
        sequence([g for g in lh if g['direction']!='down'])
    if sid=='tanjiro' and num==87:
        sequence([g for g in gs if g['staff']%2==1 and not g['grace']])
        run=[g for g in gs if g['staff']%2==0 and g['x']>155 and g['notes']]
        for i,g in enumerate(run):g['localBeat']=3.125+i*.125
        for g in gs:
            if g['staff']%2==0 and g.get('symbol')=='‰':g['localBeat']=3.5
        # Quarter rest in the upper voice is printed at beat three; the inner
        # eighth holds independently while the small run begins after a 32nd rest.
    if sid=='tanjiro' and num==103:
        for g in gs:
            if g['staff']%2==0 or g['direction']=='none':g['localBeat']=0
            elif g['x']<400:g['localBeat']=0
            elif g['x']<420:g['localBeat']=1
            elif g['x']<445:g['localBeat']=2
            else:g['localBeat']=3
    m['rawDuration']=max((g.get('localBeat',0)+g['duration'] for g in gs if not g['grace']),default=0)
