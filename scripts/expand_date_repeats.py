"""Date's printed repeat/volta traversal, shared by playback and MIDI practice.

The physical measure index includes the initial pickup. Keep source indices
and occurrence numbers so every performed event remains traceable to the PDF.
"""
import copy
from collections import defaultdict, Counter

def apply(sid,data,report):
    if sid!='your-name-date':return data,report
    old=copy.deepcopy(data)
    assert len(old['measures'])==59
    order=(list(range(5))*2+[5,6,7,8,5,6,9,10]+
           [11,12,13,14,11,12,15,16]+
           [17,18,17,19,17,20,21,22,23]+list(range(24,59)))
    events=[];measures=[];systems=[];tempo=[];time=0;occ=Counter()
    bymeasure=defaultdict(list)
    for e in old['events']:bymeasure[e['measure']].append(e)
    original_ids=[];maps=[];annotations=[]
    visuals={v['id']:v for v in report['visualReadings']}
    for source in order:
        om=old['measures'][source];occ[source]+=1;mi=len(measures)
        delta=time-om['start']
        if not systems or systems[-1]['sourceSystem']!=om['system'] or source!=order[mi-1]+1:
            sy=copy.deepcopy(old['systems'][om['system']])
            sy.update(index=len(systems),sourceSystem=om['system'],start=time,measures=[])
            systems.append(sy)
        sy=systems[-1];sy['measures'].append(mi)
        m=copy.deepcopy(om)
        m.update(index=mi,start=time,system=sy['index'],sourceMeasure=source,repeatOccurrence=occ[source])
        m['anchors']=[[b+delta,x] for b,x in m['anchors']]
        idmap={}
        for oe in bymeasure[source]:
            e=copy.deepcopy(oe);idmap[oe['id']]=len(events);original_ids.append(oe['id'])
            e.update(id=len(events),measure=mi,system=sy['index'],beat=oe['beat']+delta,sourceMeasure=source,repeatOccurrence=occ[source])
            for k in ('tieFrom','tieTo'):e.pop(k,None)
            e['soundDuration']=e['duration'];events.append(e)
            if oe['id'] in visuals:
                a=copy.deepcopy(visuals[oe['id']]);a.update(id=e['id'],measure=mi+1,sourceMeasure=source,repeatOccurrence=occ[source]);annotations.append(a)
        maps.append(idmap)
        for g in m['groups']:g['beat']+=delta;g['notes']=[idmap[i] for i in g['notes']]
        measures.append(m)
        active=next(t['factor'] for t in reversed(old['tempoMap']) if t['beat']<=om['start'])
        changes=[dict(beat=time,factor=active)]+[dict(beat=t['beat']+delta,factor=t['factor']) for t in old['tempoMap'] if om['start']<t['beat']<om['start']+om['duration']]
        for change in changes:
            if not tempo or tempo[-1]['factor']!=change['factor']:tempo.append(change)
        time+=m['duration'];sy['end']=time
    # Reconnect ties within each occurrence. A tie at the end of a common
    # repeated bar also continues into the matching pitch in the second volta.
    for e,oid in zip(events,original_ids):
        oe=old['events'][oid]
        if 'tieTo' not in oe:continue
        ot=old['events'][oe['tieTo']];mi=e['measure'];target=None
        if ot['measure']==oe['measure']:target=events[maps[mi][ot['id']]]
        elif mi+1<len(measures):
            target=next((events[i] for i in maps[mi+1].values() if events[i]['hand']==e['hand'] and events[i]['midi']==e['midi'] and abs(events[i]['beat']-e['beat']-e['duration'])<1e-7),None)
        if target:
            e['tieTo']=target['id'];target['tieFrom']=e['id'];target.pop('soundDuration',None)
    for e in events:
        if 'tieFrom' in e:continue
        last=e
        while 'tieTo' in last:last=events[last['tieTo']]
        e['soundDuration']=last['beat']+last['duration']-e['beat']
    data.update(events=events,measures=measures,systems=systems,tempoMap=tempo,totalBeats=time,
                sourceMeasureCount=len(old['measures']),performanceOrder=order)
    data['performanceNote']+=' 已展开原谱反复及第 1、2、3 结尾；琶音暂按同时和弦播放，rubato 与 rit. 未量化。'
    issues=report['rhythmIssues']
    report.update(eventCount=len(events),measureCount=len(measures),sourceMeasureCount=len(old['measures']),
                  performanceOrder=order,visualReadings=annotations,
                  pageEventCounts=[sum(e['page']==p for e in events) for p in range(data['pages'])],
                  rhythmIssues=[{**i,'measure':mi+1,'sourceMeasure':source} for mi,source in enumerate(order) for i in issues if i['measure']==source+1])
    return data,report
