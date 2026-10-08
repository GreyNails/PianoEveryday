"""Compile a direct visual reading, retaining original PDF coordinates.

The written noteheads are collected by read_call_geometry.py. Onsets and
durations are explicitly entered in transcription/call-of-silence/reading.py.
This is not a general PDF-to-MIDI recognizer.
"""
import collections
import argparse
from fractions import Fraction
import importlib.util
import json
from pathlib import Path

import fitz
import mido

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / 'transcription/call-of-silence'
spec = importlib.util.spec_from_file_location('reading', WORK / 'reading.py')
reading = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reading)


def number(value):
    return float(Fraction(value.replace(':', '/')))


def compile_score():
    geometry = json.loads((WORK / 'geometry.json').read_text())
    original = json.loads((ROOT / 'scores/call-of-silence/score.json').read_text())
    systems, measures, events = [], [], []
    by_system = {}
    for m in geometry:
        num = m['number']
        key = (m['page'], m['system'])
        if key not in by_system:
            by_system[key] = len(systems)
            systems.append(dict(index=len(systems), page=m['page'], top=max(0,m['top']-30),
                                bottom=m['bottom']+32, start=(num-1)*4, measures=[]))
        si = by_system[key]
        sy = systems[si]
        om = dict(index=len(measures), displayNumber=num, system=si, page=m['page'],
                  left=m['left'], right=m['right'], start=(num-1)*4, duration=4, groups=[])
        measures.append(om)
        sy['measures'].append(om['index'])
        sy['end'] = num*4
        anchors = collections.defaultdict(list)

        def emit(staff, group_index, beat, durations, tremolo=False):
            group = m['staves'][staff]['groups'][group_index]
            assert beat >= 0
            if len(durations) == 1:
                durations = durations * len(group['notes'])
            assert len(durations) == len(group['notes']), (num,staff,group_index)
            hand = 'R' if staff == 0 else 'L'
            # Explicit m.d. instructions on the middle staff.
            if len(m['staves']) == 3 and staff == 1:
                right = {2:[0],3:[0],4:[0],5:[0],6:[0],7:[0,1,5,6],8:[4,5],10:[0,1],11:list(range(7))}
                if group_index in right.get(num,[]):
                    hand = 'R'
            shift = 0
            if staff == 0 and (num in (6,7,8,44) or num == 5 and group_index >= 4
                              or num == 21 and group_index == 3 or num == 37 and group_index in (1,2,3)):
                shift = 12
            og = dict(x=group['x']+2.5,beat=om['start']+beat,duration=max(durations),hand=hand,notes=[])
            unique = {}
            for n,duration in zip(group['notes'],durations):
                assert 0 < duration and beat+duration <= 4+1e-7,(num,staff,group_index,beat,duration)
                midi = n['midi']+shift
                assert 21<=midi<=108,(num,midi)
                k = (midi,round(n['y'],3))
                if k in unique:
                    unique[k]['duration'] = max(unique[k]['duration'],duration)
                    continue
                event = dict(id=len(events),midi=midi,beat=om['start']+beat,duration=duration,
                             hand=hand,x=n['x']+2.5,y=n['y'],page=m['page'],system=si,
                             measure=om['index'],staff=staff,sourceGroup=group_index,
                             velocity=.38 if tremolo and num<=8 else .7)
                events.append(event)
                unique[k]=event
                og['notes'].append(event['id'])
            om['groups'].append(og)
            if not tremolo:
                anchors[round(og['beat'],8)].append(og['x'])

        for staff,st in enumerate(m['staves']):
            timing = reading.TIMING[num][staff]
            if staff == 0 and num in reading.TREMOLOS:
                for a,b,start,length,step in reading.TREMOLOS[num]:
                    for i in range(round(length/step)):
                        emit(staff,a if i%2==0 else b,start+i*step,[step],True)
                continue
            if timing is None:
                # Measures 9–10: six sixteenths per beat, inferred from the
                # independent four-beat middle/bass voices (number omitted).
                if num in (9,10):
                    count = 18 if num==9 else 12
                    for i in range(count):
                        emit(staff,i,(1 if num==9 else 0)+i/6,[1/6])
                    if num==10:emit(staff,12,2,[1])
                else:
                    assert len(st['groups']) == 16,(num,staff,len(st['groups']))
                    for i,g in enumerate(st['groups']):
                        duration = 1 if (num,i) in [(19,12),(20,0),(25,2)] else .5 if (num,i)==(20,10) else .25
                        emit(staff,i,i/4,[duration])
                continue
            tokens=timing.split()
            assert len(tokens)==len(st['groups']),(num,staff,len(tokens),len(st['groups']))
            for i,token in enumerate(tokens):
                beat,durations=token.split('/')
                emit(staff,i,number(beat),[number(v) for v in durations.split(',')])
        # A tremolo's two printed heads denote the whole span, not successive
        # x positions for every repeated attack. Use other voices for the cursor.
        clean=[]
        for beat,xs in sorted(anchors.items()):
            x=min(xs)
            if not clean or x>clean[-1][1]+.2:
                clean.append([beat,x])
        if not clean or clean[0][0]>om['start']:
            clean.insert(0,[om['start'],om['left']+3])
        clean.append([om['start']+4,om['right']-2])
        om['anchors']=clean

    # Only same-pitch, contiguous notes supported by a printed curve may tie.
    # Use the filled curve once; Sibelius also emits a duplicate stroke path.
    at_time=collections.defaultdict(list)
    for e in events:at_time[round(e['beat'],6)].append(e)
    doc=fitz.open(ROOT / 'scores/call-of-silence/original.pdf')
    for pi,page in enumerate(doc):
        for d in page.get_drawings():
            curves=[item for item in d['items'] if item[0]=='c']
            if d['type']!='fs' or not curves or d['rect'].height>12:
                continue
            a,b=curves[0][1],curves[0][-1]
            x0,x1=sorted([a.x,b.x]);y0=a.y;y1=b.y
            candidates=[]
            for e in events:
                if e['page']!=pi or e.get('tieTo') is not None or not -3<x0-e['x']<8 or abs(y0-e['y'])>6:
                    continue
                for f in at_time[round(e['beat']+e['duration'],6)]:
                    if f['midi']!=e['midi'] or f['hand']!=e['hand'] or f.get('tieFrom') is not None:
                        continue
                    same=f['system']==e['system'] and -3<f['x']-x1<8 and abs(y1-f['y'])<6
                    cross=f['system']==e['system']+1 and x1>page.rect.width-55
                    if same or cross:
                        candidates.append((abs(x0-e['x'])+abs(y0-e['y'])+(abs(x1-f['x']) if same else 12),e,f))
            if candidates:
                _,e,f=min(candidates,key=lambda item:item[0]);e['tieTo']=f['id'];f['tieFrom']=e['id']
    # The upper F#2 tie in bar 33 is almost flat and was checked visually.
    e=next(e for e in events if e['measure']==32 and e['staff']==1 and e['sourceGroup']==0 and e['midi']==42)
    f=next(e for e in events if e['measure']==32 and e['staff']==1 and e['sourceGroup']==1 and e['midi']==42)
    assert e['beat']+e['duration']==f['beat']
    e['tieTo']=f['id'];f['tieFrom']=e['id']
    for e in events:
        if e.get('tieFrom') is not None:continue
        last=e;seen=set()
        while last.get('tieTo') is not None:
            assert last['id'] not in seen;seen.add(last['id']);last=events[last['tieTo']]
        e['soundDuration']=last['beat']+last['duration']-e['beat']
    data=dict(original,mode='play',bpm=60,keyLabel='A 大调 / F♯ 小调',meterLabel='4/4',totalBeats=176,
              systems=systems,measures=measures,events=events,
              transcriptionStatus='manual-reference',
              performanceNote='人工对照原谱转写的参考演奏版。第 9–10 小节上方音型按六连音处理（原谱未标数字）；震音已展开。琶音按同时和弦播放，未定量的渐慢未额外延长。左右手按谱表及 m.d. 标记给出参考分配。')
    data.pop('status',None)
    (WORK/'performance-draft.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    mid=mido.MidiFile(ticks_per_beat=960)
    for hand,channel in [('R',0),('L',1)]:
        track=mido.MidiTrack();mid.tracks.append(track)
        track.append(mido.MetaMessage('track_name',name=hand))
        track.append(mido.MetaMessage('set_tempo',tempo=1000000))
        scheduled=[]
        for e in events:
            if e['hand']!=hand or not e.get('soundDuration'):continue
            scheduled.append((round(e['beat']*960),1,mido.Message('note_on',channel=channel,note=e['midi'],velocity=round(90*e['velocity']))))
            scheduled.append((round((e['beat']+e['soundDuration'])*960),0,mido.Message('note_off',channel=channel,note=e['midi'],velocity=0)))
        clock=0
        for tick,_,message in sorted(scheduled,key=lambda row:row[:2]):
            track.append(message.copy(time=tick-clock));clock=tick
    mid.save(WORK/'performance-draft.mid')
    report=dict(measures=len(measures),pages=len(doc),events=len(events),attacks=sum('soundDuration' in e for e in events),
                ties=[dict(fromMeasure=e['measure']+1,toMeasure=events[e['tieTo']]['measure']+1,midi=e['midi'],beat=e['beat']) for e in events if 'tieTo' in e],
                sourceAmbiguities=reading.UNRESOLVED)
    (WORK/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='ties'},ensure_ascii=False))
    print('Printed ties:',len(report['ties']))
    return data


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install',action='store_true',help='Install the compiled reference reading in the local player.')
    args=parser.parse_args()
    data=compile_score()
    if args.install:
        target=ROOT/'scores/call-of-silence'
        (target/'score.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
        (target/'performance.mid').write_bytes((WORK/'performance-draft.mid').read_bytes())
        catalog=json.loads((ROOT/'songs.json').read_text())
        entry=next(s for s in catalog if s['id']=='call-of-silence')
        entry['playable']=True
        entry['transcriptionStatus']='manual-reference'
        (ROOT/'songs.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
        print('Installed Call of Silence reference transcription.')
