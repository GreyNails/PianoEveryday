"""Import paired final PDFs/MIDI; MIDI is authoritative for played notes.

The engraved score's linked PDF supplies exact PDF coordinates and written
practice beats. Performance attacks, releases, dynamics, tempo and CC64 come
from the supplied MIDI without quantization. Re-running is idempotent.
"""
import argparse,bisect,collections,hashlib,importlib.util,json,os,re,shutil,subprocess
from pathlib import Path
import fitz,mido
ROOT=Path(__file__).resolve().parent.parent
DEFAULT=ROOT.parent.parent/'pianogen3/final'
IDS={'Enchanted':'enchanted','MerryChristmasMrLawrence':'merry-christmas-mr-lawrence','Photogpraph':'photograph','TheFateofOphelia':'the-fate-of-ophelia','alltoowell':'all-too-well','badhabits':'bad-habits','cardigan':'cardigan','exile':'exile','eyesclosed':'eyes-closed','hesapirate1':'hes-a-pirate','janejoe':'jane-doe','lookwhatyoumakemedo':'look-what-you-made-me-do','lovestory':'love-story','perfect2':'perfect','sapphire':'sapphire','shivers':'shivers','speaknow':'speak-now','the1':'the-1','vivalavida2':'viva-la-vida','willow':'willow','烟花易冷':'yan-hua-yi-leng'}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,data):Path(p).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
def midi_read(path):
    mid=mido.MidiFile(path);notes=[];tempos={0:500000};pedals=collections.defaultdict(list);controls=[]
    for ti,track in enumerate(mid.tracks):
        active=collections.defaultdict(collections.deque);tick=0
        hand='L' if 'left' in track.name.lower() else 'R' if 'right' in track.name.lower() else None
        for msg in track:
            tick+=msg.time;b=tick/mid.ticks_per_beat
            if msg.type=='set_tempo':tempos[tick]=msg.tempo
            if msg.type=='control_change':
                controls.append(dict(tick=tick,channel=msg.channel,control=msg.control,value=msg.value))
                if msg.control==64:pedals[msg.channel].append((b,msg.value>=64))
            if msg.type=='note_on' and msg.velocity:
                assert hand is not None,('Missing hand assignment',track.name)
                active[msg.channel,msg.note].append(dict(midi=msg.note,playBeat=b,midiVelocity=msg.velocity,velocity=msg.velocity/127,hand=hand,channel=msg.channel,sourceTrack=ti,sourceOnTick=tick))
            elif msg.type=='note_off' or msg.type=='note_on' and msg.velocity==0:
                assert active[msg.channel,msg.note],('Unpaired note-off',path,ti,tick,msg.note)
                e=active[msg.channel,msg.note].popleft();e.update(soundDuration=b-e['playBeat'],sourceOffTick=tick)
                assert e['soundDuration']>0;notes.append(e)
        assert not any(active.values()),('Unreleased MIDI notes',path)
    for channel,changes in pedals.items():changes.sort()
    for e in notes:
        end=e['sourceOffTick']/mid.ticks_per_beat;changes=pedals[e['channel']]
        i=bisect.bisect_right([x[0] for x in changes],end)-1
        if i>=0 and changes[i][1]:
            release=next((b for b,on in changes[i+1:] if not on),end)
            e['pedalDuration']=max(e['soundDuration'],release-e['playBeat'])
    base=tempos[0];tempo=[dict(beat=t/mid.ticks_per_beat,factor=base/v,microsecondsPerBeat=v) for t,v in sorted(tempos.items())]
    return notes,tempo,60_000_000/base,mid.ticks_per_beat,controls

def written_notes(data):
    notes=[];u=data.get('ticksPerQuarter',4)
    for hand,voices in zip('RL',data['staves']):
        for voice in voices:
            tick=0;active={}
            for mi,segments in enumerate(data['voiceMeasures'][voice]):
                for seg in segments:
                    for pitch in seg['pitches']:
                        if pitch in seg['tied']:
                            assert pitch in active,(voice,mi,pitch)
                            active[pitch]['notationEnd']=(tick+seg['ticks'])/u
                        else:
                            e=dict(midi=pitch,beat=tick/u,q=tick,voice=voice,hand=hand,measure=mi,notationEnd=(tick+seg['ticks'])/u)
                            notes.append(e);active[pitch]=e
                    tick+=seg['ticks']
    return notes

def pdf_layout(work,source,record,name,engine,pdf):
    """Re-engrave with source links using the identical PDF backend/layout.

    SVG backend font metrics differ from PDF, so its coordinates cannot be
    superimposed on these supplied PDFs. Source links identify each notehead.
    """
    cache=work/'note-anchors.json'
    if cache.exists():
        payload=json.loads(cache.read_text())
        if payload.get('method')=='pdf-source-links-v2' and payload['pdfSha256']==sha(pdf) and payload['sourceSha256']==record['source_sha256']:return payload
    spec=importlib.util.spec_from_file_location('final_layout_engine',engine/'scripts/layout_final_scores.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    ly=mod.make_ly(dict(source,_animation_tags=True),name,record['staff_size'],record['landscape'],record['paper_size']).replace('\\pointAndClickOff','\\pointAndClickOn')
    reuse=(work/'linked.ly').exists() and (work/'linked.ly').read_text()==ly and (work/'linked.pdf').exists()
    (work/'linked.ly').write_text(ly)
    lily=engine/'tools/lilypond-local/root';env=dict(os.environ)
    env.update(LD_LIBRARY_PATH=str(lily/'usr/lib/x86_64-linux-gnu/lilypond/2.20.0/guile'),LILYPOND_DATADIR=str(lily/'usr/share/lilypond/2.20.0'),GUILE_LOAD_PATH=str(lily/'usr/share/lilypond/2.20.0/guile/1.8'))
    if not reuse:
        with (work/'engraving.log').open('w') as log:
            subprocess.run([str(lily/'usr/bin/lilypond.real'),'-o',str(work/'linked'),str(work/'linked.ly')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    pattern=re.compile(r'\\once \\override NoteHead.output-attributes = #\x27\(\(class .*?data-q . "(\d+)"\).*?data-pitches . "([\d,]+)"\).*?data-voice . "([^"]+)"\)\)\s+(<[^>]+>|[a-g][^\s]*)')
    tokens={}
    for line_no,line in enumerate(ly.splitlines(),1):
        tokens[line_no]=[(m.start(4),m.end(4),int(m[1]),list(map(int,m[2].split(','))),m[3]) for m in pattern.finditer(line)]
    doc=fitz.open(pdf);linked=fitz.open(work/'linked.pdf');assert len(doc)==len(linked),(name,'page count')
    anchors=[];systems=[];bars=[];bar_length=4*float(__import__('fractions').Fraction(source.get('meter','4/4')));u=source.get('ticksPerQuarter',4)
    def lines_of(page):
        out=[]
        for drawing in page.get_drawings():
            for item in drawing['items']:
                if item[0]=='l':out.append((item[1]*page.rotation_matrix,item[2]*page.rotation_matrix))
                elif item[0]=='re':
                    r=item[1]*page.rotation_matrix
                    if r.width<4:out.append((fitz.Point((r.x0+r.x1)/2,r.y0),fitz.Point((r.x0+r.x1)/2,r.y1)))
        return out
    for pi,page in enumerate(doc):
        annotated=linked[pi];annotated.set_rotation(page.rotation)
        annotated=linked.reload_page(annotated)  # Refresh cached link rectangles after rotating landscape PDFs.
        original_lines=lines_of(page);new_lines=lines_of(annotated)
        staff=lambda lines:sorted({round(a.y,2) for a,b in lines if abs(a.y-b.y)<.05 and abs(a.x-b.x)>200})
        ys=staff(original_lines);newys=staff(new_lines)
        assert len(ys)==len(newys) and max(abs(a-b) for a,b in zip(ys,newys))<.02,(name,pi,'PDF geometry changed')
        assert len(ys)%10==0
        grouped=collections.defaultdict(dict);group_pitches={}
        for link in annotated.get_links():
            uri=link.get('uri','')
            if not uri.startswith('textedit:'):continue
            line,col,_=map(int,uri.rsplit(':',3)[1:])
            token=next((t for t in tokens.get(line,[]) if t[0]<=col<t[1]),None)
            if token is None:continue
            _,_,q,pitches,voice=token
            r=link['from']
            if not (3<r.height<6 and 4<r.width<10):continue  # Exclude ties, rests, stems and accidentals.
            # MuPDF link rectangles already use rotated page coordinates.
            grouped[q,voice][tuple(round(v,3) for v in r)]=((r.x0+r.x1)/2,(r.y0+r.y1)/2)
            group_pitches[q,voice]=pitches
        for (q,voice),positions in grouped.items():
            heads=list(positions.values());pitches=sorted(group_pitches[q,voice])
            assert len(heads)==len(pitches),(name,q,voice,len(heads),pitches)
            for (x,y),pitch in zip(sorted(heads,key=lambda t:-t[1]),pitches):anchors.append(dict(q=q,voice=voice,midi=pitch,x=x,y=y,page=pi,system=int(q/u/bar_length)//4))
        for row in range(len(ys)//10):
            si=len(systems);st=ys[row*10:row*10+10];heads=[a for a in anchors if a['system']==si]
            assert heads and all(h['page']==pi for h in heads),(name,si,'page mapping')
            xs=sorted({round(a.x,2) for a,b in original_lines if abs(a.x-b.x)<.05 and abs(min(a.y,b.y)-st[0])<.6 and abs(max(a.y,b.y)-st[4])<.6})
            merged=[]
            for x in xs:
                if not merged or x-merged[-1]>4:merged.append(x)
            count=min(4,len(source['measures'])-si*4)
            assert len(merged)==count,(name,pi,row,'barlines',merged,count)
            left=min(min(a.x,b.x) for a,b in original_lines if abs(a.y-st[0])<.05 and abs(a.y-b.y)<.05 and abs(a.x-b.x)>200)
            bounds=[left]+merged
            systems.append(dict(index=si,page=pi,start=si*4*bar_length,end=min((si+1)*4,len(source['measures']))*bar_length,left=left,right=bounds[-1],top=min(st[0],min(h['y'] for h in heads))-12,bottom=max(st[-1],max(h['y'] for h in heads))+12,staves=[dict(top=st[0],bottom=st[4]),dict(top=st[5],bottom=st[9])]))
            for k,(a,b) in enumerate(zip(bounds,bounds[1:])):bars.append(dict(index=len(bars),displayNumber=len(bars)+1,system=si,page=pi,start=(si*4+k)*bar_length,duration=bar_length,left=a,right=b))
    assert len(bars)==len(source['measures'])
    payload=dict(method='pdf-source-links-v2',pdfSha256=sha(pdf),sourceSha256=record['source_sha256'],pageSizes=[dict(width=p.rect.width,height=p.rect.height) for p in doc],anchors=anchors,systems=systems,measures=bars)
    write(cache,payload);return payload

def compile_song(folder,stage,work,engine):
    name=folder.name;sid='final-'+IDS[name];work.mkdir(parents=True,exist_ok=True)
    record=json.loads((folder/'检查记录/四小节排版检查.json').read_text());pdf=folder/(name+'.pdf');mid=folder/(name+'.mid')
    assert sha(pdf)==record['pdf_sha256'];source_path=Path(record['source']);assert sha(source_path)==record['source_sha256']
    source=json.loads(source_path.read_text());write(work/'notation-source.json',source)
    layout=pdf_layout(work,source,record,name,engine,pdf)
    notes,tempo,bpm,tpb,controllers=midi_read(mid);written=written_notes(source)
    actual_by=collections.defaultdict(list);written_by=collections.defaultdict(list)
    for e in notes:actual_by[e['hand'],e['midi']].append(e)
    for e in written:written_by[e['hand'],e['midi']].append(e)
    assert {k:len(v) for k,v in actual_by.items()}=={k:len(v) for k,v in written_by.items()},(name,'MIDI and score note counts differ')
    anchors={(a['q'],a['voice'],a['midi']):a for a in layout['anchors']};staff_for={v:h for h,vs in zip('RL',source['staves']) for v in vs};max_delta=0
    for key,items in actual_by.items():
        for e,w in zip(sorted(items,key=lambda e:e['playBeat']),sorted(written_by[key],key=lambda e:e['beat'])):
            max_delta=max(max_delta,abs(e['playBeat']-w['beat']));assert abs(e['playBeat']-w['beat'])<.3,(name,e,w)
            a=anchors.get((w['q'],w['voice'],w['midi']))
            if a is None:a=next((a for a in layout['anchors'] if a['q']==w['q'] and a['midi']==w['midi'] and staff_for[a['voice']]==w['hand']),None)
            assert a is not None,(name,'No engraved notehead',w)
            m=layout['measures'][w['measure']]
            e.update(beat=w['beat'],notationDuration=w['notationEnd']-w['beat'],duration=min(w['notationEnd'],m['start']+m['duration'])-w['beat'],measure=w['measure'],system=m['system'],page=m['page'],x=a['x'],y=a['y'],voiceRole=w['voice'],sourceEvidence='paired-midi-and-engraving',grace=False)
    notes.sort(key=lambda e:(e['beat'],e['hand'],e['midi'],e['playBeat']))
    for i,e in enumerate(notes):e['id']=i
    measures=layout['measures'];systems=layout['systems']
    for m in measures:
        cols=collections.defaultdict(list)
        for a in layout['anchors']:
            beat=a['q']/source.get('ticksPerQuarter',4)
            if m['start']<=beat<m['start']+m['duration']:cols[beat].append(a['x'])
        out=[]
        for b,xs in sorted(cols.items()):
            x=min(xs)
            if not out or x>out[-1][1]+.1:out.append([b,x])
        if not out or out[0][0]>m['start']:out.insert(0,[m['start'],m['left']+1])
        out.append([m['start']+m['duration'],max(out[-1][1]+.1,m['right']-1)]);m['anchors']=out
        groups=collections.defaultdict(list)
        for e in notes:
            if e['measure']==m['index']:groups[e['beat'],e['hand']].append(e)
        m['groups']=[dict(beat=b,hand=h,x=min(e['x'] for e in es),duration=max(e['duration'] for e in es),notes=[e['id'] for e in es]) for (b,h),es in sorted(groups.items())]
    total=measures[-1]['start']+measures[-1]['duration']
    performance_end=max(e['playBeat']+max(e['soundDuration'],e.get('pedalDuration',0)) for e in notes)
    notation_total=total;total=max(total,performance_end)  # Preserve the supplied MIDI's final release/pedal tail.
    # The layout source is used only for the already established title map.
    spec=importlib.util.spec_from_file_location('final_titles',engine/'scripts/layout_final_scores.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    title='JANE DOE' if name=='janejoe' else mod.TITLES[name]
    target=stage/sid;target.mkdir();shutil.copy2(pdf,target/'original.pdf');shutil.copy2(mid,target/'performance.mid');shutil.copy2(folder/(name+'.musicxml'),target/'original.musicxml')
    with fitz.open(pdf) as doc:
        for pi,p in enumerate(doc):p.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False).save(target/f'page-{pi+1}.png')
    data=dict(title=title+' · MIDI 版',credit='pianogen3 · final',mode='play',pages=len(layout['pageSizes']),pageSizes=layout['pageSizes'],bpm=bpm,tempoMap=tempo,totalBeats=total,notationTotalBeats=notation_total,keyLabel=source.get('key',''),meterLabel=source.get('meter','4/4'),systems=systems,measures=measures,events=notes,performanceSource='midi',transcriptionStatus='midi-imported',noteDataComplete=True,sourceFilename=pdf.name,sourceSha256=sha(pdf),sourceMidiSha256=sha(mid),sourceMusicXmlSha256=sha(folder/(name+'.musicxml')),performanceNote='随谱 MIDI 版：保留原始演奏速度、力度与踏板；按谱面节拍分组跟练。',reviewUrl='review.json')
    report=dict(id=sid,status='midi-imported',method='original-midi-performance + linked-source-engraving',eventCount=len(notes),measureCount=len(measures),sourceDirectory=str(folder),sourceSha256=sha(pdf),sourceMidiSha256=sha(mid),sourceScoreSha256=sha(source_path),midiTicksPerBeat=tpb,midiControllers=controllers,tempoChanges=len(tempo),maximumPerformanceOffsetBeats=max_delta,notationTotalBeats=notation_total,performanceEndBeat=performance_end,allMidiNotesMapped=True,rhythmIssues=[],limitations=['本次核对导入数据与所提供 MIDI/谱面的对应关系，未重新验证原始扒谱与原曲的一致性。'])
    write(target/'score.json',data);write(target/'review.json',report)
    return dict(id=sid,title=data['title'],credit=data['credit'],url=f'scores/{sid}/score.json',base=f'scores/{sid}/',pdf=f'scores/{sid}/original.pdf',midi=f'scores/{sid}/performance.mid',musicxml=f'scores/{sid}/original.musicxml',playable=True,collection='pianogen3-final',transcriptionStatus='midi-imported'),report

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('source',type=Path,nargs='?',default=DEFAULT);ap.add_argument('--only',nargs='*');ap.add_argument('--install',action='store_true');args=ap.parse_args()
    folders=sorted(d for d in args.source.iterdir() if d.is_dir() and (d/(d.name+'.mid')).is_file())
    assert set(d.name for d in folders)==set(IDS),'Collection changed: inspect new names before importing'
    catalog=json.loads((ROOT/'songs.json').read_text());reports=[];entries=[]
    # Persistent staging allows inspection and resuming a failed batch. The
    # catalogue changes only after every selected song has completed.
    stage=ROOT/'transcription/pianogen3-final/staged';stage.mkdir(parents=True,exist_ok=True)
    for folder in folders:
        if args.only and folder.name not in args.only:continue
        sid='final-'+IDS[folder.name];work=ROOT/'transcription'/sid
        dest=stage/sid
        if dest.exists():shutil.rmtree(dest)
        entry,report=compile_song(folder,stage,work,args.source.parent);entries.append(entry);reports.append(report)
        print(entry['id'],report['eventCount'],'MIDI notes',report['measureCount'],'bars',flush=True)
    if args.install:
        for entry in entries:
            existing=next((e for e in catalog if e['id']==entry['id']),None)
            assert existing is None or existing.get('collection')=='pianogen3-final','Refusing to replace an unrelated score'
        for entry in entries:
            dest=ROOT/'scores'/entry['id'];dest.mkdir(exist_ok=True)
            for f in (stage/entry['id']).iterdir():shutil.copy2(f,dest/f.name)
        ids={e['id'] for e in entries};catalog=[e for e in catalog if e['id'] not in ids]+entries
        write(ROOT/'songs.json.tmp',catalog);(ROOT/'songs.json.tmp').replace(ROOT/'songs.json')
    write(ROOT/'transcription/pianogen3-final/import-report.json',dict(source=str(args.source),count=len(reports),noteCount=sum(r['eventCount'] for r in reports),installed=args.install,scores=reports))

if __name__=='__main__':main()
