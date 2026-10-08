"""Source-page pulse readings for An Jing and Flower Dance.

1100px source previews. A run records literal evenly engraved attack columns,
not a stretch of detector durations. Missing/spurious columns remain reported.
Pitch candidates and accompaniment subdivision readings remain a draft.
"""
from review_scan_pulse import clusters,align_columns

FLOWER_BARS=[
 [[551,786,1035],[397,607,823,1035],[299,546,770,1035],[417,700,1035],[608,1035]],
 [[600,1035],[674,1035],[595,1035],[521,755,1035]],
 [[438,775,1035],[418,698,1035],[603,1035],[605,1035]],
 [[571,1035],[516,824,1035],[457,721,1035],[426,693,1035]],
 [[1035],[1035],[595,1035],[720,1035]],
 [[595,1035],[486,694,1035],[605,1035],[585,1035],[605,1035]],
 [[494,1035],[605,1035],[605,1035],[605,1035]],
 [[622,1035],[605,1035],[595,1035],[605,1035]],
 [[585,1035],[608,1035],[548,1035],[591,1035]],
 [[510,777,1035],[456,729,1035],[1035],[1035],[1035]],
 [[1035],[1035],[1035],[1035],[1035]],
 [[1035],[1035],[835,1035],[374,611,792,1035],[393,760,1035]],
 [[460,746,1035],[472,752,1035],[756,1035]],
]

def flower_layout(pages):
    out=[]
    for p,layouts in zip(pages,FLOWER_BARS):
        assert len(p['systems'])==len(layouts),(p['page'],len(p['systems']),len(layouts))
        scale=p['width']/1100;p['reviewedClefs']={};p['reviewedOctaves']=[];p['reviewedOctavesComplete']=True
        for si,(s,ends) in enumerate(zip(p['systems'],layouts)):
            gs=[g for m in s['measures'] for g in m['groups'] if g['x']/scale>(325 if p['page']==0 and si==0 else 180)]
            bounds=[s['staves'][0]['left']]+[v*scale for v in ends]
            s['measures']=[dict(left=a,right=b,groups=[g for g in gs if a<=g['x']<b]) for a,b in zip(bounds,bounds[1:])]
            r,l=[st['index'] for st in s['staves']];p['reviewedClefs'][r]=[(0,'G')];p['reviewedClefs'][l]=[(0,'F')]
            pi=p['page']
            changes={(0,1):[(0,'G'),(372,'F')],(0,0):[(0,'F'),(1012,'G')],(4,1):[(0,'F'),(550,'G'),(1015,'F')],(7,0):[(0,'F'),(325,'G'),(605,'F')],(9,0):[(0,'F'),(490,'G')],(9,1):[(0,'G'),(650,'F'),(913,'G'),(1013,'F')],(10,1):[(0,'F'),(340,'G'),(1015,'F')],(11,4):[(0,'F'),(610,'G'),(748,'F')],(12,0):[(0,'F'),(310,'G'),(440,'F'),(600,'G'),(720,'F'),(806,'G')],(12,1):[(0,'G'),(450,'F')],(12,2):[(0,'F'),(283,'G')]}
            p['reviewedClefs'][l]=[(x*scale,c) for x,c in changes.get((pi,si),[(0,'F')])]
            regions={(0,1):[(180,393)],(3,2):[(180,1035)],(3,3):[(180,1035)],(4,0):[(180,1035)],(4,1):[(180,680)],(5,1):[(180,694)]}
            spans=regions.get((pi,si),[])
            if pi==7:spans=[(635,1035)] if si==0 else [(180,1035)]
            if pi==8 and si==0:spans=[(180,585)]
            if pi==8 and si==3:spans=[(605,1035)]
            if pi in (9,10):spans=[(180,1035)]
            if pi==11 and si<=2:spans=[(180,835 if si==2 else 1035)]
            if pi==12:spans=[(180,752 if si==1 else 1035)]
            p['reviewedOctaves'] += [(r,a*scale,b*scale,12) for a,b in spans]
        out.append(dict(page=p['page']+1,barlines=layouts))
    rows=[m for p in pages for s in p['systems'] for m in s['measures']]
    assert len(rows)==120,len(rows)
    rows[0]['reviewedKey']=5
    for n,bpm in [(89,96),(105,90),(113,71)]:rows[n-1]['reviewedTempo']=bpm
    return [dict(reason='按原谱页码和小节号重建 120 小节，恢复漏行，核对五升号、换谱号、八度线和数字速度。',layouts=out)]

def run(a,b,n,start=0,step=.25):return [(a+(b-a)*i/(n-1),start+i*step) for i in range(n)]
def literal(xs,beats):
    assert len(xs)==len(beats),(xs,beats)
    return list(zip(xs,beats))
FLOWER={}
for n,a,b,count,step in [(1,334,523,8,.5),(2,569,759,8,.5),(3,805,994,8,.5),(5,415,584,8,.5),(6,625,798,8,.5),(7,843,1007,8,.5),(15,195,584,16,.25),(16,623,1009,16,.25),(18,623,1009,16,.25),(19,195,642,16,.25),(22,614,1009,16,.25),(31,716,1013,16,.25),(32,194,579,16,.25),(34,195,579,16,.25),(35,623,1009,16,.25),(38,194,494,16,.25),(47,194,1008,32,.125),(48,194,906,24,.125),(50,615,1008,24,1/6),(51,194,693,24,1/6),(54,615,1008,24,1/6),(58,194,579,16,.25),(62,195,577,16,.25),(65,513,1001,16,.25),(66,195,579,16,.25),(67,623,1008,16,.25),(69,623,1008,16,.25),(70,195,579,16,.25),(71,623,1008,16,.25),(72,194,577,16,.25),(73,640,1009,16,.25),(74,194,579,16,.25),(75,623,1009,16,.25),(77,615,1009,16,.25),(78,194,579,16,.25),(82,194,579,16,.25),(83,628,1009,16,.25),(86,194,574,16,.25)]:FLOWER[n]=run(a,b,count,step=step)
FLOWER[4]=run(218,337,6,start=.5,step=.5)
for n,xs in [(9,[323,384,406,428,449,504]),(13,[441,526,551,576,602,653]),(25,[767,833,855,878,899,982]),(29,[194,259,282,304,327,374]),(41,[194,274,296,321,348,401]),(45,[447,521,544,566,590,643]),(89,[528,601,626,652,680,738]),(93,[750,827,850,875,899,969])]:FLOWER[n]=literal(xs,[0,1.25,1.5,1.75,2,3])
for n,xs in [(14,[721,752,779,806,837,859,879,906,932,959,985,1006]),(30,[440,466,493,520,546,569,592,616,641,665,687,710])]:
    FLOWER[n]=literal(xs,[0,.5,1,1.5]+[2+i/4 for i in range(8)])
for n,a,b,last in [(17,194,500,[553,579]),(33,623,932,[982,1009]),(79,623,928,[980,1009]),(81,604,932,[983,1009])]:FLOWER[n]=run(a,b,13)+[(last[0],3.5),(last[1],3.75)]
for n,xs in [(20,[695,721,751,813,842,880,923,961,1001]),(84,[194,220,245,311,340,384,429,470,511])]:FLOWER[n]=literal(xs,[0,.25,.5,1,1.5,2,2.5,3,3.5])
for n,a,b,last in [(21,194,508,[535,560]),(37,590,946,[975,1008]),(85,569,942,[974,1008])]:FLOWER[n]=run(a,b,13)+[(last[0],3.5),(last[1],3.75)]
for n,xs in [(23,[195,220,244,267,288,308,338,361,383,405,429,451,474,495]),(39,[534,558,578,603,623,645,668,691,713,735,758,780,802,824]),(55,[194,219,241,258,279,300,324,344,364,383,404,424,444,464]),(87,[615,641,665,693,716,741,767,791,815,839,864,889,913,940])]:FLOWER[n]=literal(xs,[0,.5,.75,1,1.25,1.5,2,2.25,2.5,2.75,3,3.25,3.5,3.75])
for n,xs in [(24,[540,573,603,637,660,716]),(40,[847,885,919,949,971,1010]),(56,[508,528,563,591,629]),(88,[194,242,281,325,367,438])]:FLOWER[n]=literal(xs,[0,.5,1,1.75,2,3][:len(xs)])
FLOWER[28]=literal([800,857,916,976,1006],[0,1,2,3,3.5])
FLOWER[36]=literal([194,224,253,283,311,342,373,401,429,461,501,533],[0,.25,.5,.75,1,1.25,1.5,1.75,2,2.5,3,3.5])
for n,xs in [(44,[204,228,261,288,324,376]),(92,[480,498,524,551,579,663])]:FLOWER[n]=literal(xs,[0,.5,1,1.5,2,3])
FLOWER[46]=literal([714,747,773,799],[0,.5,1,1.5])+run(826,1015,12,2,1/6)
FLOWER[49]=run(194,492,18,step=1/6)+literal([518,554,578],[3,3.5,3.75])
FLOWER[53]=run(194,492,18,step=1/6)+literal([518,554,578],[3,3.5,3.75])
FLOWER[52]=literal([741,769,815,844,868,894,922,951,977,1007],[0,.5,1,1.5,2,2.25,2.5,2.75,3,3.5])
for n,a,b,last in [(57,712,993,[1017]),(59,623,981,[1014]),(61,603,981,[1008]),(63,623,981,[1008])]:FLOWER[n]=run(a,b,13)+[(last[0],3.25)]
for n,a,b,last in [(60,195,482,[514,552]),(68,194,477,[502,553]),(76,194,476,[513,578]),(80,194,480,[510,563])]:FLOWER[n]=run(a,b,12)+literal(last,[3,3.5])
FLOWER[64]=[(194,0),(274,1)]
FLOWER[94]=literal([205,275,349,414],[0,.5,1,1.5])+run(480,1008,12,2,1/6)
for n in range(95,104):FLOWER[n]=run(194 if n!=97 else 209,1008,32,step=.125)
FLOWER[104]=run(194,811,32,step=.125)
FLOWER[105]=literal([854,913,936,959,983],[0,1.25,1.5,1.75,2])
for n,a,b in [(113,194,422),(114,493,710),(115,780,1001),(116,194,421),(118,780,1001),(119,194,687)]:FLOWER[n]=run(a,b,8,step=.5)
for n,xs in [(117,[490,525,560,595,630,666,717])]:FLOWER[n]=literal(xs,[0,.5,1,1.5,2,2.5,3.5])
FLOWER[120]=[(785,0)]

# Right-hand rhythms read on all six An Jing pages. Values are literal beats,
# including gaps for printed rests. Ambiguous bar 54 is left unreviewed.
AN_R={n:[.5+i*.5 for i in range(7)] for n in list(range(15,100))}
for n in (15,20,46,47,48,50):AN_R[n]=[0,.5,1,1.5,2,3,3.5]
AN_R[20]=[0,.5,1,1.5,2,3.5]
AN_R[16]=[0,.5,1,1.5,2,2.5,2.75]
AN_R[18]=[0,.5,1,1.5,2]
for n in (21,23,49,55,67,79,83,87):AN_R[n]=[i*.5 for i in range(8)]
AN_R[79]=[.5,1,1.5,2,2.5,3,3.5]
AN_R[83]=[.5,1,1.5,2,2.5,3,3.5]
AN_R[87]=[.5,1,1.5,2,2.5,3,3.5]
AN_R[22]=[0,.5,1,1.5,2.5,3.5]
AN_R[24]=[0,1,2,3]
for n in (28,36):AN_R[n]=[0,.5,1,1.5,2,2.5]
AN_R[41]=[0,1.5,2,2.5,3,3.5,3.75]
for n in (42,43):AN_R[n]=[1,1.5,2,2.5,3,3.5,3.75]
AN_R[44]=[1.5,2]
AN_R[51]=[0,.5,1,1.5,3,3.5]
AN_R[52]=[0,.5,1,1.5,2.5,2.75]
AN_R.pop(54)
AN_R[56]=[0,.5,1,1.5,2,3,3.5]
AN_R[57]=[0,.5,1,1.5,2.5,3.5,3.75]
AN_R[58]=[0,.5,1,1.5,3.5]
AN_R[59]=[0,.5,1,1.5,2.5,3,3.5]
AN_R[60]=[0,.5,1,2,2.5,2.75]
AN_R[64]=[0,.5,1,1.5,2.5]
AN_R[72]=[0,.5,1,1.5,2.5]
AN_R[77]=[i/2 for i in range(8)];AN_R[78]=[]
AN_R[82]=[0,.5,1,1.5,2.5,3.5]
AN_R[90]=[0,.5,1,1.5,2,2.5]
AN_R[95]=[0,.5,1,1.5,2,2.5,3,3.5,3.75]
for n in (96,97):AN_R[n]=[0,.5,1,1.5,2,2.5,3,3.5,3.75]
AN_R[98]=[0,.5,1,1.5,2,2.5,3,3.5,3.75]
AN_R[99]=[0]
# Explicit preview positions where the detector misses heads or invents an
# extra column. Regular eight-note accompaniment supplies the other anchors.
AN_X={18:[193,224,258,280,303],22:[196,218,243,265,318,366],29:[816,855,876,898,926,954,980],30:[225,262,286,307,327,348,369],37:[815,855,876,898,926,954,980],40:[625,666,689,710,734,755,776],41:[812,878,901,925,949,973,989],47:[194,246,297,348,417,524,575],50:[462,485,528,556,578,660,693],56:[795,832,868,891,922,964,986],58:[485,515,544,574,707],64:[194,224,248,278,333],77:[430,454,478,502,527,552,579,608],82:[602,624,653,676,726,764],90:[602,624,653,680,706,732],95:[800,820,845,876,901,925,950,974,989],98:[635,660,681,705,731,755,779,805,817],99:[852]}

def source_columns(p,m,st,expected):
    gs=[g for g in m['groups'] if g['staff']==st and g['notes']]
    cols=clusters(gs,p,5);actual=[x*1100/1050 for x,_ in cols]
    # The shared matcher is expressed in 1050px units; scaling both inputs
    # keeps its absolute-distance threshold meaningful.
    pairs=align_columns(actual,expected);uncertain=[];matched=[]
    for i,(x,gg) in enumerate(cols):
        j=pairs.get(i)
        if j is None:
            j=min(range(len(expected)),key=lambda j:abs(expected[j][0]-actual[i]))
            uncertain.append(dict(x=round(actual[i],2),beat=expected[j][1],kind='unmatched-candidate-column'))
        elif abs(expected[j][0]-actual[i])>9:
            uncertain.append(dict(x=round(actual[i],2),beat=expected[j][1],kind='wide-column-match'))
        for g in gg:g['reviewedBeat']=expected[j][1]
        matched.append(expected[j][1])
    for j,(x,b) in enumerate(expected):
        if j not in pairs.values():uncertain.append(dict(x=x,beat=b,kind='missing-candidate-column'))
    return gs,uncertain

def apply(sid,pages):
    if sid not in ('an-jing','flower-dance'):return []
    out=flower_layout(pages) if sid=='flower-dance' else []
    rows=[(p,s,m) for p in pages for s in p['systems'] for m in s['measures']]
    for n,(p,s,m) in enumerate(rows,1):
        r,l=[st['index'] for st in s['staves']]
        expected=FLOWER.get(n) if sid=='flower-dance' else None
        if sid=='an-jing' and n in AN_R and AN_R[n]:
            beats=AN_R[n];cols=clusters([g for g in m['groups'] if g['staff']==r and g['notes']],p,5)
            xs=AN_X.get(n)
            if xs is None and len(cols)==len(beats):xs=[x*1100/1050 for x,_ in cols]
            if xs is None:
                # Do not squeeze a missing/extra melody head into a sequence.
                out.append(dict(measure=n,reason='候选旋律列数与原谱不符，保留未校对状态。',unresolvedMelodyColumns=dict(expected=len(beats),detected=len(cols))));continue
            expected=literal(xs,beats)
        if sid=='an-jing' and n==78:
            m['groups']=[g for g in m['groups'] if g['staff']==l and g['notes']]
            for g in m['groups']:g.update(reviewedBeat=0,duration=1)
            m['sourcePulseAligned']=True
            out.append(dict(measure=n,reason='原谱 1/4 过渡小节：右手休止、左手一拍低音。'))
            continue
        if not expected:continue
        rr,uncertain=source_columns(p,m,r,expected)
        length=4
        # Accompaniment attacks use the read melody as a positional reference.
        # This is a candidate alignment, not a duration certification. Every
        # interpolated bass onset remains separately disclosed in the report.
        def at(b):
            for (x,a),(y,c) in zip(expected,expected[1:]):
                if a<=b<=c:return x+(y-x)*(b-a)/(c-a)
            if len(expected)>1:
                (x,a),(y,c)=expected[:2] if b<expected[0][1] else expected[-2:]
                return x+(y-x)*(b-a)/(c-a)
            return expected[0][0]+(m['right']/p['width']*1100-expected[0][0])*b/4
        # Both scores' moving bass figures use binary subdivisions here.
        # Triplet-note columns in Flower 49–54 are provided by the upper part.
        grid=[(at(i/4),i/4) for i in range(16)]
        if sid=='flower-dance' and n in (47,48,*range(95,105)):grid=[(at(i/8),i/8) for i in range(32)]
        left=(FLOWER_L if sid=='flower-dance' else AN_L).get(n)
        ll=[g for g in m['groups'] if g['staff']==l and g['notes']]
        bass_candidates=[]
        if left is not None and not left:ll=[]
        elif left is not None:
            ll,lu=source_columns(p,m,l,[(at(b),b) for b in left])
            uncertain += [dict(hand='L',**v) for v in lu]
            for g in ll:bass_candidates.append(dict(x=round(g['x']/p['width']*1100,2),beat=g['reviewedBeat'],method='read-bass-rhythm-aligned-to-melody-columns'))
        else:
            for g in ll:
                x=g['x']/p['width']*1100;xx,b=min(grid,key=lambda q:abs(q[0]-x));g['reviewedBeat']=b
                bass_candidates.append(dict(x=round(x,2),beat=b,method='interpolated-source-column-needs-review'))
        gs=rr+ll
        for g in gs:
            b=g['reviewedBeat'];st=g['staff']
            following=sorted({h['reviewedBeat'] for h in gs if h['staff']==st and h['reviewedBeat']>b+1e-7})
            end=following[0] if following else length
            if st==r:
                eb=sorted({v for _,v in expected if v>b+1e-7});end=eb[0] if eb else 4
                duration=end-b
                if sid=='flower-dance' and n in (17,18,19,21,22,33,34,35,37,38,*range(49,55),*range(57,87)) and g['direction']=='up':
                    following_voice=[h['reviewedBeat'] for h in rr if h['direction']=='up' and h['reviewedBeat']>b+1e-7]
                    duration=min(following_voice,default=4)-b
                if sid=='flower-dance' and n in (108,120):duration=2
                # Literal rests at the ends of fast runs and melody phrases.
                if sid=='flower-dance' and n==48:duration=min(duration,.125)
                if sid=='flower-dance' and n in (57,59,61,63):duration=min(duration,.25)
                if sid=='flower-dance' and n==64:duration=1
                if sid=='flower-dance' and n==105 and b==2:duration=2
                if sid=='an-jing':
                    if n in (16,52) and b==2.75:duration=.25
                    if n==22:duration=.5
                    if n in (44,64,72,82) and b==2.5:duration=.5
                    if n==44 and b==2:duration=1
                    if n in (48,51,57,58,59) and (b==2 or n==51 and b==1.5 or n==57 and b in (1.5,2.5) or n==58 and b==1.5 or n==59 and b==1.5):duration=.5
                    if n==90 and b==2.5:duration=1
                    if n==99:duration=1
            else:
                duration=left[b] if left is not None else min(g['duration'],end-b)
                if any(h['kind'] in ('whole','hollow') for h in g['notes']):duration=min(4-b,4 if any(h['kind']=='whole' for h in g['notes']) else 2)
            g['duration']=max(1/32,min(duration,4-b));g['grace']=False
        m['groups']=gs;m['sourcePulseAligned']=True
        out.append(dict(measure=n,reason='按原谱旋律拍点重排；伴奏用谱面列位置对齐，伴奏细分、漏音和音高仍待逐音复核。',previewWidth=1100,sourceBeatColumns=expected,uncertainCandidates=uncertain,accompanimentCandidates=bass_candidates))
    return out

# Additional literal source columns; these include the silence around long
# chords, dotted rhythms and the two very short pickup notes before triplets.
FLOWER[8]=[(224,0)];FLOWER[12]=[(194,0)]
for n,xs in [(10,[566,599,631,666,688,741]),(26,[194,239,266,297,322,376]),(42,[480,509,538,575,607,659]),(90,[800,841,876,915,944,994])]:FLOWER[n]=literal(xs,[0,.75,1,1.75,2,3])
FLOWER[11]=literal([795,850,903,925,946,962,980,1008],[0,1,2,2.5,2+2/3,2+5/6,3,3.5])
for n,xs in [(27,[457,509,575,595,613,638,658,678,697,743]),(43,[740,791,849,872,894,925,942,960,980,1008]),(91,[194,239,281,296,313,343,362,382,404,431])]:FLOWER[n]=literal(xs,[0,1,2,2+1/16,2+1/8,2.5,2+2/3,2+5/6,3,3.5])
FLOWER[106]=literal([201,230,252,275,299,327,352],[0,.75,1,1.75,2,2.75,3])
FLOWER[107]=literal([399,428,450,472,494,518,531,543,560,584],[0,.75,1,1.75,2,2.5,2+2/3,2+5/6,3,3.5])
FLOWER[108]=[(635,0)]
FLOWER[109]=literal([815,877,896,918,944,984],[0,1.25,1.5,1.75,2,3])
FLOWER[110]=literal([194,233,261,277,299,350],[0,.75,1,1.75,2,3])
FLOWER[111]=run(412,744,16)
FLOWER[112]=literal([781,804,826,847,867,890,919,944,971,997],[0,.25,.5,.75,1,1.5,2,2.5,3,3.5])
AN_X.update({23:[407,435,459,483,508,533,556,579],26:[216,234,255,280,304,329,354],49:[194,217,247,279,317,358,394,430],55:[548,571,596,621,657,694,717,738],57:[194,224,268,298,371,418,432],62:[651,682,706,732,755,777,802],67:[194,224,282,317,345,385,416,435],70:[237,266,293,321,350,365,394],71:[477,507,533,559,587,629,665],79:[818,862,887,911,938,962,987],81:[432,458,484,510,535,560,578],83:[816,841,867,889,913,938,960],85:[428,455,479,509,537,564,595],86:[626,674,701,727,751,774,797],87:[850,874,897,921,943,967,991],88:[219,244,270,294,320,344,367],93:[426,456,485,521,549,576,607]})

# Literal accompaniment durations. None means a printed rest. This table is
# intentionally separate from detected stem lengths and from melody timing.
def line(*ds):
    b=0;out={}
    for d in ds:
        if d>0:out[b]=d
        b+=abs(d)
    assert b<=4.00001,(ds,b)
    return out
FLOWER_L={}
for n in (1,2,3):FLOWER_L[n]=line(.5,.5,.5,.5,1,1)
for n in (4,7,11,16,19,32,51,64,80,100,104,113,114,115):FLOWER_L[n]=line(*([.5]*8))
FLOWER_L[4]=line(*([.5]*8));FLOWER_L[5]=line(.5,.5,.5,.5,1,1)
FLOWER_L[6]=line(.5,.5,.5,.5,1,1)
FLOWER_L[8]={};FLOWER_L[9]=line(-.5,1.5,.5,.5,.5,-.5)
for n in (10,26,29,41,42,44,45,109,112):FLOWER_L[n]=line(.5,.5,1,.5,.5,1)
for n in (12,64):FLOWER_L[n]=line(.5,.5,.5,.5,.5,.5,1)
for n in (13,15,25,31):FLOWER_L[n]=line(.5,.5,1,.5,.5,1)
for n in (14,30):FLOWER_L[n]=line(.5,.5,1,.5,.5,1)
for n in (17,18,21,22,33,34,37,38,49,50,53,54,65,67,69,71,73,75,77,79,81,82,85,86):
    FLOWER_L[n]=line(.5,.25,.25,.25,.25,-.5,.5,.25,.25,.25,.25,-.5)
for n in (18,34,50,71,82):FLOWER_L[n]=line(.5,.5,.25,.25,-.5,.5,.25,.25,.25,.25,-.5)
for n in (21,37,85):FLOWER_L[n]=line(.5,.5,.25,.25,-.5,.5,.25,.25,.5,-.5)
for n in (22,38,86):FLOWER_L[n]=line(.5,.25,.25,.25,.25,-.5,.5,.25,.25,.25,.25,-.5)
for n in (19,35,83):FLOWER_L[n]=line(.5,.25,.25,.25,.25,.5,.5,.25,.25,.25,.25,.5)
for n in (20,36,52,84):FLOWER_L[n]=line(.5,.25,.25,.5,.5,.5,.5,1)
for n in (23,39,55,87):FLOWER_L[n]=line(.5,.25,.25,.25,.25,.5,.5,.5,.5,.5)
for n in (24,40,56,88):FLOWER_L[n]=line(.5,.5,.5,.5,.5,.5,1)
FLOWER_L[27]=line(.5,.5,.5,.5,.5,.5,.25,.25,-.5)
FLOWER_L[28]=line(.5,.5,.5,.5,.5,.5,.5,.5)
FLOWER_L[43]=line(.5,.5,.5,.5,.5,.25,.25,.5,-.5)
FLOWER_L[46]=line(.75,.25,.5,.5,.75,.25,.5,-.5)
for n in (47,95,103):FLOWER_L[n]=line(.75,.25,.5,-.5,.75,.25,.5,-.5)
FLOWER_L[48]=line(1.5,.25,.25,.5,.5,.25,.25,.5)
for n in (57,59,61,63):FLOWER_L[n]=line(1,1,1,1)
FLOWER_L[58]=line(1,.5,.5,2);FLOWER_L[60]=line(4);FLOWER_L[62]=line(1,.75,.25,2)
FLOWER_L[66]=line(1,.5,.5,.5,.5,1)
for n in (70,74,78):FLOWER_L[n]=line(1,.25,.25,.25,.25,.25,.25,.25,.25,-.5,.25,.25)
FLOWER_L[72]=line(.5,.5,.5,.5,.5,.5,.5,.5)
FLOWER_L[89]=line(2,2);FLOWER_L[90]=line(2,2)
FLOWER_L[91]=line(.5,.5,.5,.5,.5,.5,.5,.5)
FLOWER_L[92]=line(.5,.5,.5,.5,.5,.5,.5,.5)
FLOWER_L[93]=line(.75,.25,.5,-.5,.75,.25,.5,.5)
FLOWER_L[94]=line(.5,.5,.5,.5,.75,.25,.5,-.5)
FLOWER_L[96]=line(2,-2)
FLOWER_L[97]=line(1,-.25,.25,.25,.25,1,1)
FLOWER_L[98]=line(.75,.25,.75,.25,.75,.25,.75,.25)
FLOWER_L[99]=line(1,1,.75,.25,.5,.5)
FLOWER_L[101]=FLOWER_L[102]=FLOWER_L[106]=FLOWER_L[107]=line(2,2)
FLOWER_L[105]=line(2,2)
FLOWER_L[108]=line(.5,.5,.5,.5,1,1)
FLOWER_L[110]=line(.5,1.5,.5,1,.5)
FLOWER_L[111]=line(.5,.5,1,.5,.5,1)
FLOWER_L[116]=line(-.5,.5,.5,.5,.5,.5,1)
FLOWER_L[117]=line(.5,.5,.5,.5,1,1)
FLOWER_L[118]=line(.5,.5,.5,.5,2)
FLOWER_L[119]=line(.5,.5,.5,.5,.5,.5,1)
FLOWER_L[120]={}
AN_L={n:line(*([.5]*8)) for n in list(range(15,40))+[61,62,63,80,81,87,88,89,90,91,92]}
AN_L[40]=line(.5,.5,.5,.5,1,-1)
for n in (41,42,43):AN_L[n]=line(.5,.5,1,-2)
AN_L[44]=line(.5,.5,1,1,-1)
for n in (45,49):AN_L[n]=line(.5,.5,*([.25]*8),-.25,.25,.5)
AN_L[46]=line(.5,.25,.25,-.25,.25,.5,.25,.25,-.25,.25,.25,.25,.5)
AN_L[47]=line(.5,.25,.25,.25,.25,-.25,.25,*([.25]*6),.5)
AN_L[48]=line(.25,.25,.25,.25,-.25,.25,.5,.5,.5,.5,.5)
AN_L[51]=line(.5,.25,.25,.25,.75,.25,.25,.25,.25,.25,.25,.5)
AN_L[52]=line(.5,.5,.5,.25,.25,-.5,.5,.5,.5)
AN_L[53]=line(.5,.25,.25,.25,.25,.25,.25,.5,.25,.25,1)
AN_L[60]=line(*([.5]*8))
AN_L[64]=line(.5,.5,.5,.5,.5,.5,.5,.25,.25)
AN_L[65]=line(.5,.25,.25,.5,.5,.5,.5,.5,.5)
AN_L[69]=line(.5,.5,.5,.5,.125,.375,.125,.375,.25,.25,.25,.25)
AN_L[70]=line(.5,.5,.5,.5,.375,.125,.5,1)
AN_L[73]=line(.5,.5,.5,.5,.5,.5,.5,.25,.25)
AN_L[76]=line(.5,.5,.5,.5,1,1)
AN_L[77]=line(1,-1,-2)
AN_L[79]=line(-.5,-.25,.25,-1,1,-.5,.5)
AN_L[82]=line(2,.5,.5,.5,.5)
AN_L[83]=line(1,-1,-1,1)
AN_L[94]=line(.5,.5,.5,.5,-2)
AN_L[95]=line(1,-1,-2)
AN_L[96]=line(1,-1,-1,.5,-.5)
AN_L[97]=line(1,-.5,.5,-2)
AN_L[98]=line(1,-1,-2);AN_L[99]=line(1,-1,-2)
FLOWER[98]=literal([194,220,245,269,294,319,358,383,409,435,459,486,511,536,562,587,613,638,663,689,714,739,765,791,814,841,866,891,914,939,965,990],[i/8 for i in range(32)])

def finish(sid,data,report):
    ties=[]
    if sid=='an-jing':
        for n in (15,16,18,20,21,23,28,36,41,42,43,46,47,48,50,90,95,96,97):ties.append((n,1.5,n,2,'R'))
        ties += [(49,3.5,50,0,'R')]
    else:
        ties=[(6,1.5,6,2,'L'),(117,1.5,117,2,'L')]
    annotations=[]
    for ma,ba,mb,bb,hand in ties:
        ta=data['measures'][ma-1]['start']+ba;tb=data['measures'][mb-1]['start']+bb
        aa=[e for e in data['events'] if e['hand']==hand and abs(e['beat']-ta)<1e-6]
        bs=[e for e in data['events'] if e['hand']==hand and abs(e['beat']-tb)<1e-6]
        for b in bs:
            if 'tieFrom' in b:continue
            aa2=[a for a in aa if a['midi']==b['midi'] and 'tieTo' not in a]
            if not aa2:continue
            a=aa2[0];a['duration']=tb-ta;a['tieTo']=b['id'];b['tieFrom']=a['id'];b.pop('soundDuration',None)
            annotations.append(dict(fromId=a['id'],toId=b['id'],measure=ma,targetMeasure=mb,midi=a['midi']))
    for e in data['events']:
        if 'tieFrom' in e:continue
        tail=e;seen=set()
        while 'tieTo' in tail:
            assert tail['id'] not in seen;seen.add(tail['id']);tail=data['events'][tail['tieTo']]
        e['soundDuration']=tail['beat']+tail['duration']-e['beat']
    count=sum(bool(m.get('sourcePulseAligned')) for m in data['measures'])
    data['sourcePulseAlignedMeasures']=report['sourcePulseAlignedMeasures']=count
    report['sourceTieReadings']=annotations
    report['onsetAlignmentUncertainties']=[dict(measure=c['measure'],**u) for c in report['visuallyCheckedCorrections'] for u in c.get('uncertainCandidates',[])]
    report['accompanimentOnsetCandidates']=[dict(measure=c['measure'],**u) for c in report['visuallyCheckedCorrections'] for u in c.get('accompanimentCandidates',[])]
    report['method']='source-melody-pulse-reading + accompaniment-rhythm-candidates + raster-noteheads'
    report['limitations']=['旋律按原谱拍点对齐；伴奏按已读音型或谱面位置对齐，仍有未匹配列和漏音。','扫描音高、局部升降号、独立持续声部与伴奏细分尚未逐音校对；节拍闭合不等于整谱正确。','未完成实际听音及实体 MIDI 键盘验证。']
    data['performanceNote']=f'已对照原谱重排 {count} 小节旋律拍点和部分伴奏节奏，恢复部分连线；'+('重建 120 小节和漏行、补回快速音群漏检符头。' if sid=='flower-dance' else '保留前 14 小节逐音读谱，恢复 1/4 过渡小节。')+'仍有扫描漏音、未匹配列、音高及伴奏细分未校对，不能视为完整校对版。'
    data['meterLabel']='4/4 · 第 78 小节 1/4' if sid=='an-jing' else '4/4 · 120 小节'
    if sid=='flower-dance':data['keyLabel']='五升号 · 局部音高仍待复核'
