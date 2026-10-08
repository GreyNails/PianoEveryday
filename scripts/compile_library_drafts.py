"""Compile source-derived, explicitly unreviewed note data for all PDF scores.

These are audition/practice drafts, not verified editions. Non-closing rhythms
are recorded in review.json; their original readings are never overwritten.
The two manually reviewed transcriptions are not touched.
"""
import argparse,collections,copy,hashlib,json,math
from pathlib import Path
import fitz,mido
from read_vector_geometry import CLEF,ACC,NOTE
from reviewed_library_corrections import apply as apply_reviewed_corrections
from review_opening_passages import apply as apply_opening_readings
ROOT=Path(__file__).resolve().parent.parent
# Opening keys and printed tempos read from each first music page. A numeric
# default is used when only a verbal tempo is printed; the UI permits changes.
SPECS={
 'jane-doe':(2,201,4.5),
 'sparkle-animenz':(5,126,4),'sparkle-alternate':(5,126,4),
 'qing-tian':(1,80,4),'a-thousand-years':(-2,90,3),'city-of-stars':(-1,100,4),
 'flower-dance':(4,75,4),'kataware-doki':(0,65,4),'secret-base':(-5,120,4),
 'wake-me-up-when-september-ends':(1,100,4),'wo-ji-de':(4,70,4),
 'yi-lu-xiang-bei':(-1,75,4),'qi-li-xiang':(-3,71,4),
 'silksong-clockwork-dancers':(-3,100,4),'your-name-date':(0,60,4),
 'an-jing':(-2,70,4),'uchiage-hanabi':(6,70,4),'ge-qian':(-1,60,4),
 'interstellar':(0,80,3),'hua-hai':(3,70,4),'pu-gong-ying-de-yue-ding':(0,70,4),
 'jue-bie-shu':(-1,104,4),'zhe-shi-jie-na-me-duo-ren':(4,70,4),'hei-se-mao-yi':(0,50,3),
}
STEPS=[0,2,4,5,7,9,11]

def timing(groups,length,gap):
    """Align engraved voices; retain a review issue when they do not close."""
    if groups and all('reviewedBeat' in g for g in groups):
        end=max(g['reviewedBeat']+g['duration'] for g in groups)
        assert end<=length+1e-6,('Reviewed rhythm exceeds meter',end,length)
        for g in groups:g['localBeat']=g['reviewedBeat'];g['playDuration']=g['duration']
        return length,True  # Explicit onsets may end with a written rest.
    def attempt(tol,displaced):
        cols=[];out={};active=[];clock=0
        for i,g in sorted(enumerate(groups),key=lambda a:a[1]['x']):
            if g['grace'] or g.get('symbol') in ('\ue4e3','∑'):continue
            shift=cols and abs(g['x']-cols[-1]['x'])<displaced and any(g['staff']==groups[j]['staff'] and {g['direction'],groups[j]['direction']}=={'up','down'} for j in cols[-1]['ids'])
            if cols and (abs(g['x']-cols[-1]['x'])<tol or shift or len(cols)==1 and abs(g['x']-cols[-1]['x'])<gap*1.9):cols[-1]['ids'].append(i)
            else:cols.append(dict(x=g['x'],ids=[i]))
        for col in cols:
            for i in col['ids']:out[i]=clock;active.append(clock+groups[i]['duration'])
            clock=min(a for a in active if a>clock+1e-6);active=[a for a in active if a>clock+1e-6]
        end=max([out[i]+groups[i]['duration'] for i in out],default=length)
        return out,end
    best=None
    for tol,disp in ((gap*.44,gap*1.6),(gap*.3,gap*1.6),(gap*.56,gap*1.9),(gap*.2,gap*1.1),(gap*.7,gap*1.9)):
        times,end=attempt(tol,disp)
        if best is None or abs(end-length)<abs(best[1]-length):best=(times,end)
        if abs(end-length)<1e-5:break
    times,raw=best;closed=abs(raw-length)<1e-5
    # Audition fallback is disclosed, not promoted to a reviewed rhythm. Scale
    # the observed sequence to the meter without generating any extra pitches.
    factor=1 if closed or raw<=0 else length/raw
    for i,g in enumerate(groups):
        if g.get('symbol') in ('\ue4e3','∑'):g['localBeat']=0;g['playDuration']=length
        elif g['grace']:
            following=[(j,h) for j,h in enumerate(groups) if j in times and h['staff']==g['staff'] and h['x']>g['x']]
            nxt=min(following,key=lambda a:a[1]['x']) if following else None
            g['localBeat']=max(0,(times[nxt[0]]*factor if nxt else length)-.1);g['playDuration']=.1
        else:
            g['localBeat']=times.get(i,0)*factor
            g['playDuration']=max(.01,min(g['duration']*factor,length-g['localBeat']))
    return raw,closed

def write_midi(data,path):
    mid=mido.MidiFile(ticks_per_beat=960);track=mido.MidiTrack();mid.tracks.append(track)
    seq=[]
    for change in data.get('tempoMap',[{'beat':0,'factor':1}]):
        seq.append((round(change['beat']*960),-1,mido.MetaMessage('set_tempo',tempo=mido.bpm2tempo(data['bpm']*change['factor']),time=0)))
    for e in data['events']:
        if 'tieFrom' in e:continue
        channel=0 if e['hand']=='R' else 1
        seq.append((round(e['beat']*960),1,mido.Message('note_on',note=e['midi'],velocity=e.get('midiVelocity',75),channel=channel)))
        seq.append((round((e['beat']+e['soundDuration'])*960),0,mido.Message('note_off',note=e['midi'],velocity=0,channel=channel)))
    last=0
    for tick,_,msg in sorted(seq,key=lambda q:(q[0],q[1])):msg.time=tick-last;track.append(msg);last=tick
    mid.save(path)

def compile_score(sid,install=False):
    folder=ROOT/'transcription'/sid;vector=folder/'geometry-raw.json';raster=not vector.exists()
    evidence=folder/('geometry-candidates.json' if raster else 'geometry-raw.json')
    ps=json.loads(evidence.read_text());key,bpm,meter=SPECS[sid]
    corrections=apply_reviewed_corrections(sid,ps)
    if sid=='qi-li-xiang':
        from review_qili_small_notes import apply as small_note_readings
        corrections+=small_note_readings(ps,timing)
    source=json.loads((ROOT/'scores'/sid/'score.json').read_text())
    if source.get('transcriptionStatus')=='manual-reference':raise ValueError('Refusing to overwrite reviewed transcription '+sid)
    pdf=ROOT/'scores'/sid/'original.pdf';assert hashlib.sha256(pdf.read_bytes()).hexdigest()==source['sourceSha256']
    systems=[];measures=[];events=[];issues=[];time=0;doc=fitz.open(pdf);page_counts=[];dropped=[]
    for p in ps:
        pi=p['page'];before=len(events);staves={st['index']:st for sy in p['systems'] for st in sy['staves']}
        clefs={st:sorted([c for c in p['chars'] if c['c'] in CLEF and c['staff']==st],key=lambda c:c['ox']) for st in staves}
        def dia(st,x,y):
            cs=[c for c in clefs[st] if c['ox']<x]
            clef=CLEF[cs[-1]['c']] if cs else ('G' if st%2==0 else 'F')
            if st in p.get('reviewedClefs',{}):
                clef=next(c for a,c in reversed(p['reviewedClefs'][st]) if a<=x)
            return (30 if clef=='G' else 18)+round((staves[st]['bottom']+staves[st].get('slope',0)*x-y)/staves[st]['step'])
        octaves=list(p.get('reviewedOctaves',[]))
        if not raster and not p.get('reviewedOctavesComplete'):
            for d in doc[pi].get_drawings():
                r=d['rect']
                if d.get('dashes') not in ('','[] 0',None) and r.width>12 and r.height<1:
                    st=min(staves,key=lambda s:abs(staves[s]['top']-r.y0))
                    labels=[t for t in p['texts'] if t['text'].strip() in ('8','8va','8vb','15','15ma') and abs(t['y']-r.y0)<18 and abs(t['x']-r.x0)<30]
                    if labels:
                        label=min(labels,key=lambda t:abs(t['x']-r.x0));shift=24 if '15' in label['text'] else 12
                        if r.y0>staves[st]['bottom']:shift=-shift
                        octaves.append((st,r.x0-15,r.x1+1,shift))
        for sy in p['systems']:
            os=dict(index=len(systems),page=pi,top=sy['top'],bottom=sy['bottom'],start=time,measures=[]);systems.append(os)
            for mi,m in enumerate(sy['measures']):
                gs=copy.deepcopy(m['groups']);number=len(measures)+1;length=2 if sid=='hei-se-mao-yi' and number>4 else meter
                # Meter figures in SMuFL are stacked at the same x. Changes at
                # a bar's far right apply to the following measure.
                digits=[c for c in p['chars'] if '\ue080'<=c['c']<='\ue089' and c['staff']==sy['staves'][0]['index'] and m['left']<c['ox']<m['right']]
                first=min([g['x'] for g in gs],default=m['right'])
                for a in digits:
                    for b in digits:
                        if abs(a['ox']-b['ox'])<1 and a['y']<b['y'] and a['ox']<first:
                            den=ord(b['c'])-0xe080;num=ord(a['c'])-0xe080
                            if den in (2,4,8,16) and 0<num<10:meter=num*4/den;length=meter
                if 'reviewedMeter' in m:meter=length=m['reviewedMeter']
                if 'reviewedKey' in m:key=m['reviewedKey']
                gap=sy['staves'][0]['step']*2
                if sid.startswith('sparkle'):
                    # Repeated triplet figures: after the first printed 3s the
                    # identical beaming omits the numbers (simile notation).
                    seen=set()
                    for g in gs:
                        if g.get('tuplet') or not g['beamIds'] or g.get('duration')!=.5:continue
                        primary=g['beamIds'][0]
                        members=[h for h in gs if primary in h['beamIds'] and not h['grace']]
                        if len(members)==3 and all(h['duration']==.5 for h in members) and primary not in seen:
                            for h in members:h['duration']=1/3;h['tuplet']=3
                            seen.add(primary)
                raw,closed=timing(gs,length,gap)
                if not closed:issues.append(dict(page=pi+1,measure=number,kind='rhythm-not-closed',readBeats=round(raw,6),meterBeats=length,preview='scaled-to-meter',reviewed=False))
                om=dict(index=len(measures),displayNumber=number,system=os['index'],page=pi,left=m['left'],right=m['right'],start=time,duration=length,groups=[],rhythmReviewed=False)
                om['rhythmReviewed']=bool(gs) and all('reviewedBeat' in g for g in gs) and not m.get('sourcePulseAligned')
                if m.get('sourcePulseAligned'):om['sourcePulseAligned']=True
                if 'reviewedTempo' in m:om['bpm']=m['reviewedTempo']
                measures.append(om);os['measures'].append(om['index'])
                keymap={d:(1 if key>0 else -1) for d in ([3,0,4,1,5,2,6] if key>0 else [6,2,5,1,4,0,3])[:abs(key)]};states={};changes=[]
                for c in p['chars']:
                    if p.get('ignoreCandidateAccidentals'):continue
                    if c['c'] not in ACC or c['staff'] not in [st['index'] for st in sy['staves']] or not m['left']<c['ox']<m['right']:continue
                    st=c['staff'];firstnote=min([n['ox'] for g in gs if g['staff']==st for n in g['notes']],default=m['right'])
                    # Exclude the opening key block; explicit note accidentals
                    # are close to the following head at the same pitch line.
                    if mi==0 and c['ox']<firstnote-gap*1.8:continue
                    matches=[(abs(n['y']-c['y'])*8+n['ox']-c['ox'],g,n) for g in gs if g['staff']==st for n in g['notes'] if 0<n['ox']-c['ox']<gap*5 and abs(n['y']-c['y'])<gap*.28]
                    if matches:
                        _,g,n=min(matches,key=lambda v:v[0]);changes.append((g['x']-.01,st,dia(st,n['ox'],n['y']),ACC[c['c']]))
                changes.sort();ci=0
                for g in sorted(gs,key=lambda a:a['x']):
                    while ci<len(changes) and changes[ci][0]<=g['x']:
                        _,st,d,a=changes[ci];states[st,d]=a;ci+=1
                    st=g['staff'];og=dict(x=g['x'],beat=time+g['localBeat'],duration=g['playDuration'],hand=g.get('hand','R' if st%2==0 else 'L'),notes=[])
                    for n in g['notes']:
                        pitch_staff=n.get('pitchStaff',st)
                        diatonic=dia(pitch_staff,n['ox'],n['y']);octave,degree=divmod(diatonic,7);alter=states.get((pitch_staff,diatonic),keymap.get(degree,0));shift=sum(v for staff,a,b,v in octaves if staff==pitch_staff and a<=n['ox']<=b)
                        midi=12*(octave+1)+STEPS[degree]+alter+shift
                        if not 21<=midi<=108:
                            dropped.append(dict(page=pi+1,x=n['x'],y=n['y'],midi=midi,reason='outside-piano-range-review-staff-or-clef'));continue
                        e=dict(id=len(events),midi=midi,beat=og['beat'],duration=og['duration'],soundDuration=og['duration'],hand=og['hand'],x=n['x'],y=n['y'],page=pi,system=os['index'],measure=om['index'],diatonic=diatonic,staff=st,grace=g['grace'],velocity=.8)
                        if raster:e['recognitionConfidence']=n.get('confidence',0)
                        if n.get('manualHeadReading'):e['sourceEvidence']='visual-head-reading'
                        if n.get('smallNotehead'):
                            e.update(noteSize='small',velocity=n['reviewedVelocity'],voiceRole=n['reviewedVoiceRole'],midiVelocity=round(75*n['reviewedVelocity']/.8))
                        if g.get('sourceRepeat'):e['sourceRepeat']=g['sourceRepeat']
                        events.append(e);og['notes'].append(e['id'])
                    om['groups'].append(og)
                bybeat=collections.defaultdict(list)
                for g in om['groups']:
                    if g['notes']:bybeat[round(g['beat'],8)].append(g['x'])
                anchors=[]
                for beat,xs in sorted(bybeat.items()):
                    x=min(xs)
                    if not anchors or x>anchors[-1][1]+.2:anchors.append([beat,x])
                if not anchors or anchors[0][0]>time+1e-7:anchors.insert(0,[time,m['left']+1])
                anchors.append([time+length,max(anchors[-1][1]+.01,m['right']-1)])
                om['anchors']=anchors;time+=length
            os['end']=time
        page_counts.append(len(events)-before)
    # Geometric tie arcs only: same written pitch at adjacent temporal points.
    bytime=collections.defaultdict(list)
    for e in events:bytime[round(e['beat'],5)].append(e)
    for p in ps:
        page_events=[e for e in events if e['page']==p['page']]
        for arc in p['ties']:
            candidates=[]
            for a in page_events:
                if 'tieTo' in a or not -2<arc['x0']-a['x']<8 or abs(arc['y0']-a['y'])>6.5:continue
                for b in bytime.get(round(a['beat']+a['duration'],5),[]):
                    if b['hand']!=a['hand'] or b['diatonic']!=a['diatonic'] or 'tieFrom' in b:continue
                    same=b['system']==a['system'] and -2<b['x']-arc['x1']<8 and abs(arc['y1']-b['y'])<6.5
                    cross=b['system']==a['system']+1 and arc['x1']>p['width']-45
                    if same or cross:candidates.append((abs(arc['x0']-a['x'])+abs(arc['y0']-a['y']),a,b))
            if candidates:
                _,a,b=min(candidates,key=lambda t:t[0]);a['tieTo']=b['id'];b['tieFrom']=a['id'];b['midi']=a['midi'];b.pop('soundDuration',None)
    for e in events:
        if 'tieFrom' in e:continue
        current=e;seen=set();end=e['beat']+e['duration']
        while 'tieTo' in current:
            assert current['id'] not in seen;seen.add(current['id']);current=events[current['tieTo']];end=current['beat']+current['duration']
        e['soundDuration']=end-e['beat']
    assert events and measures and time>0,sid
    report=dict(id=sid,status='unreviewed-draft',reviewed=False,sourceSha256=source['sourceSha256'],method='raster-symbol-candidates' if raster else 'pdf-glyph-geometry',pages=len(ps),pageEventCounts=page_counts,eventCount=len(events),measureCount=len(measures),rhythmIssues=issues,rejectedCandidates=dropped,limitations=['尚未逐音、逐小节人工校准。','扫描识别可能漏音、多音；变调、八度线、连线、复调和重复段待复核。','未闭合小节仅为试听按拍号缩放；不是已确认时值。' if issues else '小节时长闭合不代表所有音高、时值和分手均正确。','反复记号未展开，按谱面顺序试听。'])
    report['candidateCount']=sum(len(g['notes']) for p in ps for s in p['systems'] for m in s['measures'] for g in m['groups'])
    report['visuallyCheckedCorrections']=corrections
    report['manualNoteheadReadings']=[dict(page=p['page']+1,**v) for p in ps for v in p.get('manualNoteheadReadings',[])]
    report['sourceGlyphCount']=None if raster else sum(c['c'] in NOTE for p in ps for c in p['chars'])
    data={**source,'mode':'play','bpm':bpm,'systems':systems,'measures':measures,'events':events,'totalBeats':time,'tempoMap':[dict(beat=0,factor=1)],'transcriptionStatus':'unreviewed-draft','reviewRequired':True,'noteDataComplete':False,'keyLabel':'识别草稿 · 待校对','meterLabel':'6/8' if sid=='a-thousand-years' else '3/4 → 2/4' if sid=='hei-se-mao-yi' else '拍号待复核','performanceNote':'未校对的识别草稿：可试听、试练，但可能漏音、错音或节奏错误，不能用于判断演奏是否正确。反复段未展开；'+(f'{len(issues)} 个小节的识别时值未闭合，试听暂按拍号缩放。' if issues else '时值闭合检查通过，仍需对照原谱逐音校准。'),'reviewUrl':'review.json'}
    data.pop('status',None)
    data['tempoMap']=[dict(beat=0,factor=1)]+[dict(beat=m['start'],factor=m['bpm']/bpm) for m in measures if 'bpm' in m and m['start']>0]
    if sid=='silksong-clockwork-dancers':
        data['keyLabel']='变调已核对 · 音符草稿'
        data['meterLabel']='4/4 · 第 51 小节为两拍短小节'
        data['performanceNote']='已按原谱修正第 37–66 小节的独立声部、交替击键、连音和震音，修正变调及重降号。文字速度与末段渐慢采用参考演奏值，可调节速度。全曲实际听感和全部音符尚未校对。'
        report['limitations']=['第 37–66 小节节奏已对照原谱修正，包含震音展开、三连音及跨谱表分手。','文字速度及渐慢为参考演奏解释；全曲音高及实际听感尚未完成独立复核。']
    if sid=='uchiage-hanabi':
        data['performanceNote']='部分节奏校对：已按原谱修正第 6、8、24、26、34、45、46、51、80–83 小节的声部对齐、震音及六连音。第 71 小节末尾原谱写有 1.5 拍休止，保留。全曲音高与其余节奏尚未校对，仍为识别草稿。'
    if sid=='jane-doe':
        data['keyLabel']='2 个升号 · 待逐音复核'
        data['meterLabel']='9/8 · 附点四分音符 = 134'
        data['performanceNote']='全谱音符字形已提取，未校对全部音高、分手与实际听感。已核对 9/8 拍、复合拍连音、整小节休止、部分独立声部与末页八度线；当前按固定参考速度试听，自由速度、渐慢与踏板尚未量化。'
        report['limitations']=['全部音符字形已提取，不等于音高、节奏与分手全部准确。','局部复合拍连音、休止、跨谱表和八度线已按谱修正；其余仍待逐音复核。','自由速度、渐慢与踏板尚未量化；尚未进行实际听音和实体 MIDI 验证。']
    data,report=apply_opening_readings(sid,data,report,ps)
    if sid in ('qing-tian','wo-ji-de'):
        from review_scan_pulse import performance_reading
        performance_reading(sid,data,report)
    if sid in ('an-jing','flower-dance'):
        from review_four_scan_rhythm import finish as finish_four_scan
        finish_four_scan(sid,data,report)
    if sid in ('ge-qian','pu-gong-ying-de-yue-ding'):
        data['performanceNote']='部分节奏校对：按原谱修正独立声部、连音与休止，取消异常小节缩放；'+('恢复小符头计拍、震音、转调和 13/16 小节。' if sid=='ge-qian' else '修正三连音、六连音、五连音及跨谱表音符。')+'全曲音高、装饰与实际听感仍未校对完成。'
        if sid=='ge-qian':data['meterLabel']='4/4 · 第 49 小节 13/16'
    if sid=='jue-bie-shu':
        from review_jue_rhythm import performance_reading
        performance_reading(data,report)
    if sid in ('qi-li-xiang','hei-se-mao-yi'):
        data['performanceNote']='部分节奏校对：'+('修正七连音、九连音、独立声部、跨谱表和八度线。' if sid=='qi-li-xiang' else '修正三连音、独立声部、跨谱表与八度线；第 5 小节起恢复原谱 62 BPM。')+'全曲音高、漏音及实际听感仍未校对完成。'
        report['limitations']=['已对照原谱修正局部连音、独立声部、跨谱表及八度线，保留全部提取的音符字形。','全曲逐音准确性及实际听感未校对完成，未实测实体 MIDI。']
    if sid=='qi-li-xiang':
        from review_qili_small_notes import finish
        finish(data,report)
    from expand_date_repeats import apply as apply_repeats
    data,report=apply_repeats(sid,data,report)
    (folder/'performance-draft.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n');(folder/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');write_midi(data,folder/'performance-draft.mid')
    if install:
        target=ROOT/'scores'/sid
        (target/'score.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n');(target/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');write_midi(data,target/'performance.mid')
    print(sid,len(data['events']),'events',len(data['measures']),'bars',len(report['rhythmIssues']),'rhythm issues','page counts',report['pageEventCounts'],flush=True)
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--install',action='store_true');ap.add_argument('ids',nargs='*');args=ap.parse_args();reports=[]
    for sid in args.ids or SPECS:reports.append(compile_score(sid,args.install))
    if args.install:
        catalog=json.loads((ROOT/'songs.json').read_text())
        for e in catalog:
            if e['id'] in [r['id'] for r in reports]:e['playable']=True;e['transcriptionStatus']='unreviewed-draft'
        (ROOT/'songs.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
