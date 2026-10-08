"""Direct visual readings of supplied PDFs; no melody inferred from recordings.

Coordinates below are on the supplied 2x page PNGs. Each tuple is
(onset, duration, x, notehead ys, optional octave shift). Voices are independent.
Only the documented pages are reviewed; later raster candidates stay drafts.
"""
import copy, collections

# (page index, system index on page): bars, each with independent R/L voices.
# Coordinates preserve the written pitch even under 8va/8vb and cross-staff hands.
JUE={
(0,0):[
 {'R':[(0,1,254,[308]),(1,.5,293,[288]),(1.5,.5,319,[293]),(2,2,347,[288])], 'L':[(0,1,254,[457]),(1,3,293,[427,437])]},
 {'R':[(0,.5,438,[254],12),(.5,.5,467,[259],12),(1,.5,496,[274],12),(1.5,.4,527,[288],12),(1.9,.1,547,[288],12),(2,2,567,[293],12)], 'L':[(0,4,438,[402,413,423,408])]},
 {'R':[(0,1,658,[313]),(1,.5,692,[293]),(1.5,.5,713,[298]),(2,2,735,[293])], 'L':[(0,2,658,[433,443,448,453,458]),(2,2,735,[433])]},
 {'R':[(0,.5,795,[269,279]),(.5,1,821,[264,274]),(1.5,.5,858,[259,269]),(2,1,884,[264,274]),(3,1,925,[269,279])], 'L':[(.5,1,821,[403]),(1.5,.5,858,[398])]},
 {'R':[(0,1,992,[313]),(1,.5,1027,[293]),(1.5,.5,1048,[298]),(2,2,1070,[293])], 'L':[(0,2,992,[433,443]),(2,2,1070,[433,443,448,453,463])]},
],
(0,1):[
 {'R':[(i/4,.25,x,[y],12) for i,(x,y) in enumerate(zip([179,199,219,239,259,279,299,319,339,359,379,399,419,439,459,479],[558,533,543,558,568,543,558,568,578,558,568,578,593,568,578,593]))], 'L':[(0,1,179,[666,695]),(1,1,259,[651,676]),(2,1,339,[666,686]),(3,1,419,[695])]},
 {'R':[(0,.875,544,[543,578]),(.875,.125,562,[558]),(1,.5,581,[563]),(1.5,.5,601,[568]),(2,2,624,[563])], 'L':[(0,1,544,[705,730,750]),(1,.5,581,[715]),(1.5,.5,601,[710])]},
 {'R':[(0,.5,689,[529],12),(.5,.5,710,[523],12),(1,1,731,[518],12)], 'L':[(0,.5,689,[705]),(.5,.5,710,[700]),(1,1,731,[695])]},
 {'R':[(0,1,823,[572,592,587]),(1,.5,859,[552]),(1.5,.5,879,[558]),(2,1,899,[552,572]),(3,1,938,[558,568])], 'L':[(0,1,823,[690,725],-12),(1,2,859,[695,705,710,715]),(3,1,938,[695,700])]},
 {'R':[(0,1,999,[552,563]),(1,1,1034,[537,558]),(2,1,1064,[552,568]),(3,1,1095,[558,572])], 'L':[(0,1,999,[695,700]),(1,2,1034,[710]),(3,1,1095,[695,705])], 'ties':[(0,'L',9)]},
],
(0,2):[
 {'R':[(0,.5,193,[838,858,863]),(.5,.5,215,[843]),(1,.5,237,[838]),(1.5,.5,258,[843]),(2,1,280,[838]),(3,1,320,[843])], 'L':[(0,1,193,[1011]),(1,2,237,[986,996]),(3,1,320,[986,1001])]},
 {'R':[(1/3,1/3,393,[809],12),(2/3,1/3,417,[809],12),(1,1/3,442,[843,853],12),(4/3,1/3,467,[819],12),(5/3,1/3,493,[819],12),(2,1/3,522,[843],12),(7/3,2/3,545,[829],12)], 'L':[(0,.5,368,[971,986,996]),(.5,.5,407,[966]),(1,.5,446,[961]),(1.5,.5,485,[986]),(2,.5,524,[981]),(2.5,.5,563,[971])]},
 {'R':[(0,1,655,[863,878]),(1,.5,688,[843]),(1.5,.5,709,[848]),(2,1,731,[843]),(3,1,766,[848])], 'L':[(0,1,655,[981,1016],-12),(1,2,688,[1001,1006,1016]),(3,1,766,[986,996,1001])]},
 {'R':[(0,1,813,[843,853]),(1,1,847,[829]),(2,1,880,[829,863]),(3,1,913,[843])], 'L':[(0,1,813,[986,996,1001]),(1,2,847,[986,1001]),(3,1,913,[986,996])], 'ties':[(0,'L',13)]},
 {'R':[(0,.5,960,[843,863]),(.5,.5,982,[838]),(1,.5,1004,[843]),(1.5,.5,1026,[838]),(2,1,1048,[843,858]),(3,1,1091,[853,863])], 'L':[(0,1,960,[1001,1035],-12),(1,2,1004,[1006,1016]),(3,1,1091,[1006,1016])]},
],
(0,3):[
 {'R':[(0,.5,180,[1141,1171]),(.5,.5,201,[1166]),(1,.5,222,[1171]),(1.5,.5,243,[1166]),(2,1,264,[1171]),(3,1,299,[1166])], 'L':[(0,4,180,[1289])]},
 {'R':[(0,1,354,[1151,1166]),(1,.5,388,[1131,1151]),(1.5,.5,410,[1136]),(2,1,434,[1131]),(3,1,470,[1136])], 'L':[(0,1,354,[1264,1299],-12),(1,1,388,[1279]),(2,1,434,[1269]),(3,.5,470,[1269,1289]),(3.5,.5,494,[1284])]},
 {'R':[(0,1,549,[1131,1151]),(1,1,584,[1116,1131]),(2,.5,619,[1131,1146]),(2.5,.5,639,[1141]),(3,1,660,[1136,1151])], 'L':[(0,1,549,[1279]),(1,1,584,[1274,1279]),(2,1,619,[1284]),(3,1,660,[1289])]},
 {'R':[(0,.5,724,[1131,1156]),(.5,.5,746,[1136]),(1,.5,768,[1131]),(1.5,.5,790,[1136]),(2,1,812,[1131,1151]),(3,1,856,[1136,1146])], 'L':[(0,1,724,[1299]),(1,2,768,[1274,1284]),(3,1,856,[1274,1284])]},
 {'R':[(0,1,918,[1156]),(1,.5,953,[1111,1121]),(1.5,.5,976,[1106,1116]),(2,.5,999,[1101,1111]),(2.5,.5,1022,[1106,1116]),(3,.5,1045,[1111,1121])], 'L':[(0,1,918,[1274,1284]),(1,.5,953,[1284]),(1.5,.5,976,[1279]),(2,.5,999,[1274,1284]),(2.5,.5,1022,[1279]),(3,.5,1045,[1284])], 'ties':[(0,'L',19)]},
],
(0,4):[
 {'R':[(0,1,180,[1425,1440]),(1,.5,212,[1406]),(1.5,.5,233,[1411]),(2,1,255,[1406]),(3,1,297,[1411])], 'L':[(0,1,180,[1535,1570],-12),(1,1,212,[1550,1555,1560]),(2.5,.5,265,[1560]),(3,.5,297,[1555]),(3.5,.5,318,[1550])]},
 {'R':[(0,1,366,[1406,1425]),(1,1,405,[1391]),(2,1,444,[1391]),(3,1,483,[1381,1406])], 'L':[(.5,.5,386,[1540]),(1,.5,405,[1535]),(1.5,.5,424,[1540]),(2,.5,444,[1535]),(2.5,1,463,[1525])]},
 {'R':[(0,.5,566,[1386,1411]),(.5,.5,590,[1381,1406]),(1,.5,614,[1386,1411]),(1.5,.5,637,[1381,1406]),(2,1,662,[1386,1411]),(3,1,708,[1391,1415])], 'L':[(0,.5,566,[1545,1570,1590]),(.5,.5,590,[1525,1540]),(1,.5,614,[1520,1535]),(1.5,.5,637,[1515,1535]),(2,.5,662,[1525,1540]),(2.5,.5,685,[1520,1535,1545]),(3,.5,708,[1525,1540]),(3.5,.5,732,[1525,1540])]},
 {'R':[(0,1,774,[1386]),(2,.5,842,[1391,1406,1411]),(2.5,.5,865,[1386,1401]),(3,.5,888,[1381,1391]),(3.5,.5,914,[1371])], 'L':[(0,.5,774,[1515,1530]),(.5,.5,797,[1505,1520]),(1,.5,820,[1500,1515]),(1.5,.5,842,[1495,1510])]},
 {'R':[(0,3,992,[1366,1386,1391]),(3.5,.5,1066,[1420,1440,1455,1435])], 'L':[(3.5,.5,1066,[1515])], 'bassClef':True},
]}


# Engraving columns confirmed again using a notehead overlay on the PDF.
for key,barno,oldxs,newxs in [
    ((0,3),4,[953,976,999,1022,1045],[953,981,1009,1037,1065]),
    ((0,4),0,[180,212,233,255,297,265,318],[193,222,243,265,307,286,328]),
    ((0,4),2,[566,590,614,637,662,685,708,732],[566,593,620,647,673,694,715,737]),
    ((0,4),3,[842,865,888,914],[850,878,905,932]),
]:
    mapping=dict(zip(oldxs,newxs));bar=JUE[key][barno]
    for hand in ('R','L'):
        bar[hand]=[(b,d,mapping.get(x,x),ys,*extra) for b,d,x,ys,*extra in bar[hand]]

# Interstellar's first forty measures: independent held melody, ostinato,
# left-hand bass and the explicitly marked l.h. notes on the upper staff.
def interstellar():
    result={}
    for page in [1,2]:
        for row in range(5):result[page,row]=[]
    # Manually read six engraving columns per measure on each supplied page.
    xs1=[
      [[244,278,313,347,381,415],[466,500,534,568,602,636],[687,721,755,789,824,858],[909,943,977,1011,1045,1079]],
      [[163,200,238,276,314,351],[406,444,482,520,558,596],[649,687,725,763,801,839],[892,929,966,1003,1040,1077]],
      [[163,200,238,276,314,351],[406,444,482,520,558,596],[649,687,725,763,801,839],[892,929,966,1003,1040,1077]],
      [[163,200,238,276,314,351],[406,444,482,520,558,596],[649,687,725,763,801,839],[892,929,966,1003,1040,1077]],
      [[163,200,238,276,314,351],[406,444,482,520,558,596],[649,687,725,763,801,839],[892,929,966,1003,1040,1077]],
    ]
    # y positions on each row: ostinato E/C, upper-staff melody, lower bass.
    rows1=[(351,359),(557,565),(785,793),(1013,1021),(1243,1251)]
    melody1={5:[(0,3,545)],6:[(0,3,541)],7:[(0,3,541)],8:[(0,1,545),(1,1,541),(2,1,537)],9:[(0,1,769),(1,1,773),(2,1,769)],10:[(0,3,765)],11:[(0,3,769)],12:[(0,1,773)],13:[(0,1,1001)],14:[(0,1,997)],15:[(0,1,997)],16:[(0,1,993)],17:[(0,1,1223)],18:[(0,1,1219)],19:[(0,1,1219),(1,1,1215),(2,1,1227)],20:[(0,1,1231)]}
    bass1={5:[(0,3,[628])],6:[(0,3,[624])],7:[(0,3,[624])],8:[(0,1,[657]),(1,1,[653]),(2,1,[649])],9:[(0,1,[874]),(1,1,[878]),(2,1,[874])],10:[(0,3,[870])],11:[(0,3,[874])],12:[(0,2,[849,886]),(2,1,[915])],13:[(0,2,[1080,1117]),(2,1,[1146])],14:[(0,2,[1076,1113]),(2,1,[1142])],15:[(0,2,[1076,1113]),(2,1,[1142])],16:[(0,2,[1072,1109]),(2,1,[1138])],17:[(0,2,[1301,1338]),(2,1,[1367])],18:[(0,2,[1305,1342]),(2,1,[1371])],19:[(0,2,[1305,1342]),(2,1,[1371])],20:[(0,2,[1318,1346]),(2,1,[1375])]}
    for number in range(1,21):
        row,j=divmod(number-1,4);xs=xs1[row][j];high,low=rows1[row]
        # D replaces C in the paired pattern where engraved.
        if number in (6,7,11,14,15,18,19):low-=4
        bar={'R':[(i/2,.5,x,[high if i%2==0 else low]) for i,x in enumerate(xs)],'L':[]}
        bar['R'] += [(b,d,xs[round(b*2)],[y]) for b,d,y in melody1.get(number,[])]
        bar['L'] += [(b,d,xs[round(b*2)],ys) for b,d,ys in bass1.get(number,[])]
        if number>=12 and number!=19:
            bar['cross']=[(1,2,xs[2],[757 if row==2 else 985 if row==3 else 1215])]
        if number==20:bar['R'].append((0,.5,xs[0],[1264]))
        if number==7:bar['ties']=[(0,'R',6),(0,'L',6)]
        result[1,row].append(bar)
    xs2=[[[163,201,240,278,316,354],[405,443,482,520,558,596],[649,687,725,763,801,839],[892,929,966,1003,1040,1077]]]*5
    # Each subsequent system starts at its printed row. The bass part moves
    # the ostinato to the lower staff in bar 36.
    bases=[(165,173,152,136,247,276,305),(459,467,438,430,547,575,604),(767,775,754,737,840,877,906),(1061,1069,1041,1033,1127,1164,1193),(None,None,None,1330,None,None,None)]
    for number in range(21,41):
        row,j=divmod(number-21,4);xs=xs2[row][j];e,c,mel,held,upper,lower,deep=bases[row]
        bar={'R':[],'L':[]}
        if number<=35:
            low=c-4 if number in (22,23,26,27,30,31,34,35) else c
            skip=number in (28,30,32,34)
            bar['R']=[(i/2,.5,x,[e if i%2==0 else low]) for i,x in enumerate(xs) if not(skip and i==0)]
            yy={21:152,22:148,23:148,24:144,25:438,26:435,27:435,28:431,29:754,30:750,31:750,32:746,33:1041,34:1037,35:1037}[number]
            ys=[yy]
            if number in (22,24):ys.append(177)
            if number in (26,27):ys.append(443)
            if number==26:ys.append(463)
            if number==28:ys.extend([418,447])
            if number==30:ys.extend([721,742])
            if number==32:ys.extend([717,737])
            if number==34:ys.extend([1008,1016,1033])
            bar['R'].append((0,1,xs[0],ys))
            if number in (27,35):
                bar['R'] += [(1,1,xs[2],[held]),(2,1,xs[4],[443 if number==27 else 1045])]
            else:bar['cross']=[(1,2,xs[2],[held])]
            bys={21:[247,276],22:[243,272],23:[243,272],24:[239,268],25:[547,575],26:[551,579],27:[551,579],28:[547,567,583],29:[840,861,877],30:[836,857,873],31:[836,857,873],32:[832,853,869],33:[1127,1148,1164],34:[1131,1152,1168],35:[1131,1152,1168]}[number]
            dy={21:305,22:301,23:301,24:297,25:604,26:608,27:608,28:612,29:906,30:902,31:902,32:898,33:1193,34:1197,35:1197}[number]
            bar['L']=[(0,2,xs[0],bys),(2,1,xs[4],[dy])]
        else:
            # Melody upper octave at beat one; measured bass eighth notes.
            if number==36:
                bar['R']=[(0,1,xs[0],[1021,1033,1041,1049]),(1,2,xs[2],[1004,1033])]
                bnotes=[[1119,1135],[1127],[1119,1135],[1127,1143],[1119,1135],[1127,1143]];bass=[1143];dy=[1172,1201]
            else:
                top={37:[1317,1329,1337,1345],38:[1313,1329,1341],39:[1313,1329,1341],40:[1309,1329,1337]}[number]
                bar['R']=[(0,1,xs[0],top),(1,2,xs[2],[1297,1326])]
                # Correct upper held note is E6 / E5 (octave), y1297/1326.
                bnotes=[[1414,1430],[1422],[1414,1430],[1422,1438],[1414,1430],[1422,1438]] if number==37 else [[1414,1426],[1418],[1414,1426],[1418,1434],[1414,1426],[1418,1434]] if number in (38,39) else [[1414,1422],[1422],[1414,1422],[1422],[1414,1422],[1422]]
                bass=[1438] if number==37 else [1434] if number in (38,39) else [1430]
                dy=[1467,1496] if number==37 else [1463,1492] if number in (38,39) else [1459,1488]
            bar['L']=[(i/2,.5,x,ys) for i,(x,ys) in enumerate(zip(xs,bnotes))]+[(0,2,xs[0],bass),(2,1,xs[4],dy)]
        result[2,row].append(bar)
    return result

def apply(sid,data,report,evidence):
    from review_more_openings import readings
    config=readings(sid)
    if sid=='jue-bie-shu':config=dict(specs=JUE,key=-1,bpm=104,meter=4,leftClef='G',label='1 个降号',tempos=[(32,132),(100,116)])
    elif sid=='interstellar':config=dict(specs=interstellar(),key=0,bpm=90,meter=3,leftClef='F',label='无升降号')
    if config is None:return data,report
    specs=config['specs'];key=config['key']
    keymap={d:(1 if key>0 else -1) for d in ([3,0,4,1,5,2,6] if key>0 else [6,2,5,1,4,0,3])[:abs(key)]}
    pages={p for p,_ in specs};old=copy.deepcopy(data);events=[];measures=[];systems=[];time=0;oldids={};oldmeasures={};pending_ties=[];annotations=[]
    for sy in old['systems']:
        page=sy['page'];local=sum(s['page']==page for s in systems)
        ns={**sy,'index':len(systems),'start':time,'measures':[]};systems.append(ns)
        source_system=evidence[page]['systems'][local]
        if (page,local) in specs:
            bars=specs[page,local];bounds=[source_system['staves'][0]['left']]+[m['right'] for m in source_system['measures']]
            bounds=config.get('bounds',{}).get((page,local),bounds)
            unit=data['pageSizes'][page]['width']/config['width'] if 'width' in config else .5
            if (page,local) in config.get('previewBounds',{}):bounds=[x*unit for x in config['previewBounds'][page,local]]
            # The initial clef/time-signature block is not an extra measure.
            if len(bounds)==len(bars)+2:bounds.pop(1)
            assert len(bounds)==len(bars)+1,(sid,page,local,bounds)
            for j,bar in enumerate(bars):
                mi=len(measures);m=dict(index=mi,displayNumber=mi+1,page=page,system=ns['index'],left=bounds[j],right=bounds[j+1],start=time,duration=bar.get('length',config['meter']),groups=[],rhythmReviewed=True)
                if 'bpm' in bar:m['bpm']=bar['bpm']
                measures.append(m);ns['measures'].append(mi)
                for role in ('R','L','cross'):
                    for item in bar.get(role,[]):
                        onset,duration,x,ys,*octave=item
                        extra=octave[0] if octave and isinstance(octave[0],dict) else {}
                        shift=extra.get('shift',0) if extra else octave[0] if octave else 0
                        staff_local=0 if role in ('R','cross') else 1;st=source_system['staves'][staff_local]
                        clef=bar.get('rightClef','G') if staff_local==0 else bar.get('leftClef','F' if bar.get('bassClef') else config.get('leftClef','F'))
                        clef=extra.get('clef',clef)
                        g=dict(x=x*unit,beat=time+onset,duration=duration,hand='L' if role=='cross' else role,notes=[])
                        for y in ys:
                            dia=(30 if clef=='G' else 18)+round((st['bottom']-y*unit)/st['step']);oct,degree=divmod(dia,7)
                            midi=(oct+1)*12+[0,2,4,5,7,9,11][degree]+keymap.get(degree,0)+shift
                            midi+=extra.get('alter',0)
                            assert 21<=midi<=108,(mi+1,item,midi)
                            # Keep the observed coordinate, not an invented glyph.
                            velocity=.84 if role=='cross' else .80 if role=='R' else .64
                            voice='melody' if role in ('R','cross') else 'accompaniment'
                            if sid=='interstellar' and role=='R':
                                voice='melody' if duration>=1 else 'accompaniment';velocity=.84 if voice=='melody' else .56
                            e=dict(id=len(events),midi=midi,beat=g['beat'],duration=duration,soundDuration=duration,hand=g['hand'],x=x*unit,y=y*unit,page=page,system=ns['index'],measure=mi,diatonic=dia,staff=st['index'],grace=duration==.1,velocity=velocity,voiceRole=voice,sourceEvidence='visual-reading',writtenClef=clef,octaveShift=shift)
                            events.append(e);g['notes'].append(e['id'])
                            annotations.append(dict(id=e['id'],page=page+1,measure=mi+1,x=e['x'],y=e['y'],midi=midi,beat=onset,duration=duration,clef=clef,octaveShift=shift))
                        m['groups'].append(g)
                for onset,hand,from_bar in bar.get('ties',[]):pending_ties.append((mi,onset,hand,from_bar-1))
                for hand,source_onset,target_onset in bar.get('localTies',[]):
                    pending_ties.append((mi,target_onset,hand,mi))
                time+=m['duration']
        else:
            for oldmi in sy['measures']:
                om=old['measures'][oldmi];delta=time-om['start'];mi=len(measures);oldmeasures[oldmi]=mi
                m=copy.deepcopy(om);m.update(index=mi,displayNumber=mi+1,start=time,system=ns['index']);measures.append(m);ns['measures'].append(mi)
                for e0 in (e for e in old['events'] if e['measure']==oldmi):
                    e=copy.deepcopy(e0);e.update(id=len(events),measure=mi,system=ns['index'],beat=e0['beat']+delta);oldids[e0['id']]=e['id'];events.append(e)
                for g in m['groups']:g['beat']+=delta;g['notes']=[oldids[i] for i in g['notes']]
                time+=m['duration']
        ns['end']=time
    for e in events:
        if e.get('sourceEvidence')=='visual-reading':continue
        for k in ('tieTo','tieFrom'):
            if k in e:e[k]=oldids[e[k]]
    for mi,onset,hand,from_bar in pending_ties:
        for b in [e for e in events if e['measure']==mi and abs(e['beat']-measures[mi]['start']-onset)<1e-6 and e['hand']==hand]:
            prev=[e for e in events if e['measure']==from_bar and e['hand']==hand and e['midi']==b['midi'] and abs(e['beat']+e['duration']-b['beat'])<1e-6]
            if prev:
                a=prev[-1];a['tieTo']=b['id'];b['tieFrom']=a['id'];b.pop('soundDuration',None)
    for e in events:
        if 'tieFrom' in e:continue
        last=e
        while 'tieTo' in last:last=events[last['tieTo']]
        e['soundDuration']=last['beat']+last['duration']-e['beat']
    if sid=='jue-bie-shu':
        # Pedal brackets are explicitly engraved across these bar groups.
        for first,last in [(1,2),(3,4),(5,6),(7,8),(9,10),(11,12),(13,14),(15,16),(17,18),(19,20),(21,22),(23,25)]:
            end=measures[last-1]['start']+measures[last-1]['duration']
            for e in events:
                if first-1<=e['measure']<last and 'tieFrom' not in e:e['pedalDuration']=max(e['soundDuration'],end-e['beat'])
    for m in measures:
        bybeat=collections.defaultdict(list)
        for g in m['groups']:
            if g['notes']:bybeat[round(g['beat'],8)].append(g['x'])
        anchors=[]
        for beat,xs in sorted(bybeat.items()):
            x=min(xs)
            if not anchors or x>anchors[-1][1]+.2:anchors.append([beat,x])
        if not anchors or anchors[0][0]>m['start']+1e-7:anchors.insert(0,[m['start'],m['left']+1])
        anchors.append([m['start']+m['duration'],max(anchors[-1][1]+.01,m['right']-1)])
        m['anchors']=anchors
    data.update(events=events,measures=measures,systems=systems,totalBeats=time)
    data['bpm']=config['bpm']
    data['tempoMap']=[dict(beat=0,factor=1)]
    data['tempoMap'] += [dict(beat=b,factor=t/data['bpm']) for b,t in config.get('tempos',[])]
    data['tempoMap'] += [dict(beat=m['start'],factor=m['bpm']/data['bpm']) for m in measures if 'bpm' in m]
    data['tempoMap']=sorted({t['beat']:t for t in data['tempoMap']}.values(),key=lambda t:t['beat'])
    count=sum(len(bars) for bars in specs.values())
    data['manuallyReadMeasures']=count
    if sid=='your-name-date':
        for m in measures:
            i=m['index']
            m['displayNumber']='弱起' if i in (0,34,53) else i-(i>34)-(i>53)
    data['keyLabel']=config['label']+' · 开头已按谱修正'
    data['meterLabel']=f"开头 {config['meter']}/4 · 后段待复核"
    passage=f'弱起及第 1–{count-1} 小节' if sid=='your-name-date' else f'第 1–{count} 小节'
    data['performanceNote']=f'部分校对：{passage}已直接按原 PDF 重写音高、节奏与声部；后续仍是未校对的识别草稿，存在漏音和节奏错误。尚未与视频逐段听音核验。'
    full_reading=len(specs)==len(systems)
    if full_reading:
        data['keyLabel']=config['label']+' · 全谱重写待复核'
        data['meterLabel']='4/4 · 3/4 · 12/16（含弱起）' if sid=='your-name-date' else f"{config['meter']}/4"
        data['performanceNote']=f'全谱读谱草稿：全部 {count} 小节已按原 PDF 重写，包含换谱号、八度记号、连音及休止。仍未校对实际听感，不能视为无误转写；未标时值的琶音暂按同时和弦播放。'
    report['method']='visual-reading-of-opening-pages + remaining-raster-candidates'
    report['manuallyReadMeasures']=count;report['visualReadings']=annotations
    report['reviewedPageNumbers']=[p+1 for p in sorted(pages)]
    report['reviewedSystems']=[dict(page=p+1,system=s+1) for p,s in specs]
    report['rhythmIssues']=[{**i,'measure':oldmeasures[i['measure']-1]+1} for i in report['rhythmIssues'] if i['measure']-1 in oldmeasures]
    report['pageEventCounts']=[sum(e['page']==p for e in events) for p in range(data['pages'])]
    report.update(eventCount=len(events),measureCount=len(measures))
    if sid in ('jue-bie-shu','interstellar'):report['referenceVideos']=[dict(url='https://www.bilibili.com/video/'+('BV1T1421Z7TK/' if sid=='jue-bie-shu' else 'BV1mf4y1i7H9/'),access='Search metadata only; video fetch returned HTTP 412. Not listened to.')]
    report['limitations'].insert(0,f'仅{passage}做过直接看谱重写；其后未完成校对。')
    if full_reading:
        report['method']='full-score-visual-reading'
        report['limitations']=['全部谱面已重新读谱记录，未完成独立听音复核，仍可能存在转写错误。','未标时值的琶音暂按同时和弦播放；不额外推断自由速度与踏板。']
        report['allMeasuresVisuallyRead']=True
    if sid=='interstellar':
        report['method']='visual-opening-reading + embedded-image-glyphs-and-vector-engraving'
        report['limitations']=['前 40 小节直接看谱重写，后段改用嵌入音符图像及矢量谱线提取；未完成独立听音复核。','按原谱恢复 107 小节、变拍、Grave 速度与尾段震音；强弱、自由延长和踏板尚未量化。']
        data['meterLabel']='3/4 · 第 53、94 小节起有变拍'
        data['performanceNote']='前 40 小节按谱重写；后段已改用 PDF 原始音符图像与矢量小节线提取，恢复 107 小节、变拍、Grave 速度及尾段震音。全曲实际听感尚未校对，强弱、自由延长及踏板仍待复核。'
    return data,report
