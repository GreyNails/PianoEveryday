"""Checks derived from the printed scores, plus structural integrity checks."""
import hashlib
import json
import math
from pathlib import Path
import unittest

import fitz

ROOT = Path(__file__).resolve().parent.parent


def score(sid):
    return json.loads((ROOT/'scores'/sid/'score.json').read_text())


class TranscriptionTests(unittest.TestCase):
    def test_date_later_polyphony_and_ending(self):
        d=score('your-name-date')
        review=json.loads((ROOT/'scores/your-name-date/review.json').read_text())
        self.assertEqual(review['rhythmIssues'],[])
        self.assertTrue(all(m['rhythmReviewed'] for m in d['measures']))
        def source(n):
            m=next(m for m in d['measures'] if m['sourceMeasure']==n)
            return m,[e for e in d['events'] if e['measure']==m['index']]
        # Held upper C6 is independent of the C5/G5 sixteenth figure.
        m,es=source(24)
        self.assertEqual({(e['midi'],e['duration']) for e in es if e['hand']=='R' and e['beat']==m['start']},{(72,.25),(84,2)})
        m,es=source(33)
        self.assertEqual({e['midi'] for e in es if e['hand']=='L'},{41,50,53})
        self.assertTrue(all(e['duration']==4 for e in es if e['hand']=='L'))
        # The final page has continuous C5-D5-G5 sixteenths, not beam artifacts.
        for n in (54,55,56,57):
            m,es=source(n);r=[e for e in es if e['hand']=='R']
            self.assertEqual([e['midi'] for e in r],[72,74,79]*4)
            self.assertEqual([e['beat']-m['start'] for e in r],[i/4 for i in range(12)])
            self.assertEqual([e['duration'] for e in r],[.25]*12)
        self.assertEqual(source(34)[0]['duration'],1)
        self.assertEqual(source(53)[0]['duration'],1.5)
        m,es=source(58)
        self.assertEqual({e['midi'] for e in es},{79,84,86,91,96,98,103})
        self.assertTrue(all(e['duration']==3 for e in es))
        m,es=source(36)
        self.assertTrue(all('tieFrom' in e for e in es if e['beat']==m['start']))

    def test_silksong_fast_passages_and_source_coverage(self):
        d=score('silksong-clockwork-dancers')
        r=json.loads((ROOT/'scores/silksong-clockwork-dancers/review.json').read_text())
        self.assertEqual(r['rhythmIssues'],[])
        self.assertEqual(len(d['measures']),75)
        self.assertEqual(d['measures'][50]['duration'],2)
        tremolo=[e for e in d['events'] if e.get('sourceRepeat')=='printed-measured-tremolo']
        self.assertEqual(len(tremolo),72)
        for n in (43,44,45):
            m=d['measures'][n]
            rr=[e for e in tremolo if e['measure']==n]
            self.assertEqual(len(rr),24)
            self.assertEqual(sorted({e['beat']-m['start'] for e in rr}),[2.5+i/8 for i in range(12)])
            self.assertTrue(all(e['duration']==.125 and e['hand']=='R' for e in rr))
            ll=[e for e in d['events'] if e['measure']==n and e['hand']=='L' and 2.5-1e-7<=e['beat']-m['start']<3.5-1e-7]
            self.assertEqual(len(ll),6)
            for i,e in enumerate(ll):
                self.assertAlmostEqual(e['beat']-m['start'],2.5+i/6)
                self.assertAlmostEqual(e['duration'],1/6)
        # Interleaved hands enter on alternating sixteenth-note subdivisions.
        m=d['measures'][37]
        for hand,offset in [('R',0),('L',.25)]:
            es=[e for e in d['events'] if e['measure']==37 and e['hand']==hand]
            self.assertEqual(sorted({e['beat']-m['start'] for e in es}),[offset+i/2 for i in range(8)])
        ps=json.loads((ROOT/'transcription/silksong-clockwork-dancers/geometry-raw.json').read_text())
        heads={(p['page'],round(n['x'],3),round(n['y'],3)) for p in ps for sy in p['systems'] for m in sy['measures'] for g in m['groups'] for n in g['notes']}
        events={(e['page'],round(e['x'],3),round(e['y'],3)) for e in d['events']}
        self.assertEqual(events,heads)
        self.assertFalse(d['noteDataComplete'])

    def test_later_playback_source_pulse_and_missing_long_notes(self):
        for sid,count in [('qing-tian',64),('wo-ji-de',76)]:
            d=score(sid)
            self.assertEqual(d['sourcePulseAlignedMeasures'],count)
            self.assertEqual(d['manuallyReadMeasures'],12)
            self.assertFalse(d['noteDataComplete'])
            later=[e for e in d['events'] if e['measure']>=12]
            self.assertTrue(all(abs(e['beat']*8-round(e['beat']*8))<1e-6 for e in later))
            self.assertTrue(all(not m['rhythmReviewed'] for m in d['measures'][12:]))
        sunny=score('qing-tian');m=sunny['measures'][23]
        # The printed D1/D2 octaves used to be discarded as wide ledger strokes.
        for pitch in [26,38]:
            bass=[e for e in sunny['events'] if e['measure']==23 and e['hand']=='L' and e['midi']==pitch]
            self.assertEqual([e['beat']-m['start'] for e in bass],[0,.5,1,1.5,2,2.5,3])
            self.assertEqual([e['duration'] for e in bass],[.5]*6+[1])
        remembered=score('wo-ji-de')
        for bar in [40,41,44,45,48,49,50,52,53,54,56,64,65,68,69,70,72,76,80]:
            m=remembered['measures'][bar-1]
            onsets=sorted({e['beat']-m['start'] for e in remembered['events'] if e['measure']==bar-1 and e['hand']=='L'})
            self.assertEqual(onsets,[i/2 for i in range(8)],bar)
        ending=[e for e in remembered['events'] if e['measure']==87]
        self.assertEqual({e['midi'] for e in ending},{52,64,68,76})
        self.assertTrue(all(e['duration']==4 for e in ending))
        self.assertFalse(any(e['measure']==88 for e in remembered['events']))
        held=[e for e in remembered['events'] if e['measure']==23 and e['hand']=='R']
        self.assertEqual([(e['midi'],e['duration']) for e in held],[(64,4)])

    def test_interstellar_restored_pages_meter_and_tremolo(self):
        d=score('interstellar')
        self.assertEqual(len(d['measures']),107)
        self.assertEqual([len(s['measures']) for s in d['systems'] if s['page']==4],[3,3,3,3,3])
        self.assertEqual([d['measures'][i-1]['duration'] for i in [52,53,54,93,94,107]],[3,4,3,3,4,4])
        self.assertEqual(d['tempoMap'],[{'beat':0,'factor':1},{'beat':166,'factor':2/3}])
        r=json.loads((ROOT/'scores/interstellar/review.json').read_text())
        self.assertEqual(r['rhythmIssues'],[]);self.assertEqual(r['rejectedCandidates'],[])
        self.assertTrue(all(abs(e['beat']*8-round(e['beat']*8))<1e-6 for e in d['events'] if e['measure']>=40))
        tremolo=[e for e in d['events'] if e.get('sourceRepeat')=='printed-measured-tremolo']
        self.assertEqual(len(tremolo),336)
        self.assertEqual({e['measure'] for e in tremolo},set(range(101,107)))
        self.assertTrue(all(e['duration']==.125 for e in tremolo))

    def test_jane_doe_source_coverage_and_compound_meter(self):
        d=score('jane-doe')
        self.assertEqual((d['pages'],len(d['measures']),len(d['events'])),(7,190,2876))
        self.assertEqual(d['bpm'],201)  # Dotted quarter = 134, quarter = 201.
        self.assertTrue(all(m['duration']==4.5 for m in d['measures']))
        self.assertFalse(d['noteDataComplete'])
        with fitz.open(ROOT/'scores/jane-doe/original.pdf') as pdf:
            heads={(pi,round(c['origin'][0],3),round(c['origin'][1],3))
                   for pi,p in enumerate(pdf) for b in p.get_text('rawdict')['blocks']
                   for line in b.get('lines',[]) for span in line['spans']
                   for c in span['chars'] if span['font']=='Chaconne' and c['c'] in ('œ','˙','w')}
        ps=json.loads((ROOT/'transcription/jane-doe/geometry-raw.json').read_text())
        extracted={(p['page'],round(n['ox'],3),round(n['y'],3)) for p in ps for sy in p['systems'] for m in sy['measures'] for g in m['groups'] for n in g['notes']}
        self.assertEqual(extracted,heads);self.assertEqual(len(heads),len(d['events']))
        first=[e for e in d['events'] if e['measure']==0 and e['beat']==0]
        self.assertEqual({e['midi'] for e in first},{69,71,74,78})
        self.assertTrue(all(e['soundDuration']==4.5 for e in first))
        self.assertFalse(any(e['measure']==43 for e in d['events']))  # Printed full-bar silence.
        for page,row,bar,hand,count,dt in [(1,3,1,'L',10,.3),(1,4,0,'L',10,.3),(2,0,3,'L',8,.375),(5,1,2,'R',8,.1875)]:
            sy=[s for s in d['systems'] if s['page']==page][row];mi=sy['measures'][bar]
            notes=[e for e in d['events'] if e['measure']==mi and e['hand']==hand and abs(e['duration']-dt)<1e-7]
            self.assertEqual(len(notes),count)
        sy=[s for s in d['systems'] if s['page']==2][0];mi=sy['measures'][3]
        cross=[e for e in d['events'] if e['measure']==mi and e['hand']=='L' and 2.25<=e['beat']-d['measures'][mi]['start']<3]
        self.assertEqual([e['midi'] for e in cross],[64,66])
        # The outlined 8va starts at the fourth eighth-note position.
        sy=[s for s in d['systems'] if s['page']==6][3];mi=sy['measures'][0]
        r=[e for e in d['events'] if e['measure']==mi and e['hand']=='R']
        at=lambda b:{e['midi'] for e in r if abs(e['beat']-d['measures'][mi]['start']-b)<1e-7}
        self.assertEqual(at(1.5),{86,95})  # Written D5/B5 -> D6/B6.
        self.assertEqual(at(2),{83})  # Written middle-line B4 -> B5.

    def test_dusk_full_reading_and_independent_subdivisions(self):
        d=score('kataware-doki')
        self.assertEqual((len(d['measures']),d['totalBeats'],d['manuallyReadMeasures']),(55,220,55))
        self.assertFalse(d['noteDataComplete'])
        self.assertTrue(all(m['rhythmReviewed'] for m in d['measures']))
        r=[e for e in d['events'] if e['measure']==2 and e['hand']=='R']
        self.assertEqual([e['midi'] for e in r],[79,79,72,84,83,81,79,79,81])
        self.assertEqual([e['duration'] for e in r],[1,.75,.25,.5,.25,.25,.5,.25,.25])
        # Bar 18: the triplet numeral belongs to the upper staff alone.
        for hand,duration,onsets in [('R',1/3,[1,4/3,5/3]),('L',.25,[1,1.25,1.5,1.75])]:
            notes=[e for e in d['events'] if e['measure']==17 and e['hand']==hand and 69<=e['beat']<70]
            self.assertEqual(len(notes),len(onsets))
            for e,b in zip(notes,onsets):
                self.assertAlmostEqual(e['beat']-68,b);self.assertAlmostEqual(e['duration'],duration)
        flat=next(e for e in d['events'] if e['measure']==12 and e['hand']=='L' and e['beat']==49.5)
        self.assertEqual(flat['midi'],58)  # Printed B flat, not B natural.
        held=[e for e in d['events'] if e['measure']==36]
        self.assertEqual(len(held),5)
        self.assertTrue(all('tieFrom' in e for e in held))
        for e in d['events']:
            if 48<=e['measure']<=50 and e['hand']=='R':self.assertEqual(e['octaveShift'],12)
            if e['measure']>=52:self.assertEqual(e['octaveShift'],0)

    def test_corrected_scan_layouts_and_quiet_polyphony(self):
        quiet=score('an-jing')
        self.assertEqual(len(quiet['measures']),99)
        self.assertEqual([m['duration'] for m in quiet['measures'][77:79]],[1,4])
        chord=[e for e in quiet['events'] if e['measure']==11 and e['hand']=='L' and e['beat']==46]
        self.assertEqual({e['midi'] for e in chord},{41,60,58,65})
        self.assertEqual([e['midi'] for e in quiet['events'] if e['measure']==11 and e['hand']=='L' and e['beat']==46.5],[48])
        for sid,count in [('qing-tian',77),('wo-ji-de',89)]:
            d=score(sid)
            self.assertEqual(len(d['measures']),count)
            self.assertEqual(d['measures'][-1]['duration'],4)
            self.assertFalse(any(e['measure']==count-1 for e in d['events']))
        # The hand-verified key cancellation must survive page boundaries.
        from review_scan_structure import apply
        ps=json.loads((ROOT/'transcription/an-jing/geometry-candidates.json').read_text())
        apply('an-jing',ps)
        self.assertEqual(ps[4]['systems'][4]['measures'][3]['reviewedKey'],0)

    def test_date_voltas_ties_meter_and_midi_tempos(self):
        import mido
        d=score('your-name-date')
        self.assertEqual(d['manuallyReadMeasures'],59)
        self.assertEqual(d['sourceMeasureCount'],59)
        # Printed 1st/2nd/3rd endings: 17-18, 17-19, 17-20.
        self.assertEqual([m['sourceMeasure'] for m in d['measures'] if 17<=m['sourceMeasure']<=20],[17,18,17,19,17,20])
        self.assertEqual([m['sourceMeasure'] for m in d['measures'] if 5<=m['sourceMeasure']<=10],[5,6,7,8,5,6,9,10])
        for m in d['measures']:
            src=m['sourceMeasure'];notes=[e for e in d['events'] if e['measure']==m['index']]
            if src==5:
                r=[e for e in notes if e['hand']=='R']
                self.assertEqual([e['midi'] for e in r],[72,79,72,79,72,72,72,79,72,79,72])
                self.assertEqual(r[4]['soundDuration'],1.5);self.assertIn('tieFrom',r[5])
            if src==11:
                left=[e for e in notes if e['hand']=='L']
                self.assertEqual([e['beat']-m['start'] for e in left],[0,.5,1.5,2,2.5,3.5])
                self.assertEqual([e['midi'] for e in left],[55,67,67,55,67,67])
            if src in (13,15):
                first=next(e for e in notes if e['hand']=='R' and e['beat']==m['start'])
                self.assertIn('tieFrom',first)  # Tie survives the volta jump.
            if 17<=src<=23:self.assertEqual(m['duration'],3)
        mid=mido.MidiFile(ROOT/'scores/your-name-date/performance.mid');tick=0;tempos=[]
        for msg in mid.tracks[0]:
            tick+=msg.time
            if msg.type=='set_tempo':tempos.append((tick/mid.ticks_per_beat,round(mido.tempo2bpm(msg.tempo))))
        self.assertEqual(tempos,[(0,60),(33,54),(65,58),(97,63),(124,55)])

    def test_additional_opening_readings(self):
        date=score('your-name-date')
        self.assertEqual(date['measures'][0]['duration'],.5)
        self.assertEqual(date['measures'][1]['start'],.5)
        self.assertEqual([e['midi'] for e in date['events'] if e['measure']==0],[72,74])
        self.assertEqual(date['measures'][0]['displayNumber'],'弱起')
        quiet=score('an-jing')
        self.assertEqual(len([s for s in quiet['systems'] if s['page']==0]),4)
        self.assertEqual(quiet['manuallyReadMeasures'],14)
        self.assertEqual([e['midi'] for e in quiet['events'] if e['measure']==0 and e['hand']=='R'][:5],[62,53,58,63,58])
        tied=[e for e in quiet['events'] if e['measure']==0 and e['beat']==2 and e['hand']=='R']
        self.assertTrue(all('tieFrom' in e for e in tied))
        dusk=score('kataware-doki')
        melody=[e for e in dusk['events'] if e['measure']==0 and e['hand']=='R']
        self.assertEqual([e['midi'] for e in melody],[79,79,79,79,76,74,74,72])
        self.assertEqual([e['duration'] for e in melody],[1,.75,.25,.5,.5,.5,.25,.25])
        sunny=score('qing-tian')
        self.assertTrue(all(e['hand']=='L' for e in sunny['events'] if e['measure']<4))
        self.assertEqual([e['midi'] for e in sunny['events'] if e['measure']==0],[52,55,62,55,48,50,52,62,55])
        self.assertEqual(sunny['manuallyReadMeasures'],12)
        # Printed vocal entrance: D5 D5 G4 G4 A4 B4, above an
        # independent D4 accompaniment; it must not be serialized after it.
        entrance=[e for e in sunny['events'] if e['measure']==8 and e['hand']=='R' and e['midi']>=67]
        self.assertEqual([e['midi'] for e in entrance],[74,74,67,67,69,71])
        self.assertEqual([e['beat']-32 for e in entrance],[.5,1,1.5,2,3,3.5])
        pickup=[e for e in sunny['events'] if e['measure']==7 and e['hand']=='R' and e['duration']<.2]
        self.assertEqual([e['midi'] for e in pickup],[50,55,57])
        self.assertTrue(all(abs(e['duration']-1/6)<1e-8 for e in pickup))
        # Real sixteenth rest on the third beat in bar 5, followed by
        # the syncopated chord. Never stretch earlier notes across this rest.
        self.assertFalse(any(e['beat']==18 and e['hand']=='R' for e in sunny['events']))
        self.assertTrue(any(e['beat']==18.25 and e['hand']=='R' for e in sunny['events']))
        remembered=score('wo-ji-de')
        self.assertEqual([e['midi'] for e in remembered['events'] if e['measure']==0],[52,59,64,59,51,59,64,59])
        self.assertTrue(all(e['writtenClef']=='F' for e in remembered['events'] if e['measure']==8 and e['hand']=='R'))

    def test_uchiage_tremolo_tuplets_and_printed_rest(self):
        data=score('uchiage-hanabi')
        review=json.loads((ROOT/'scores/uchiage-hanabi/review.json').read_text())
        self.assertEqual(review['rhythmIssues'],[])
        self.assertFalse(review['reviewed'])
        tremolo=[e for e in data['events'] if e.get('sourceRepeat')]
        self.assertEqual(len(tremolo),44)
        self.assertTrue(all(e['measure']==23 and e['hand']=='L' for e in tremolo))
        for bar in (79,80,81):
            right=sorted((e for e in data['events'] if e['measure']==bar and e['hand']=='R'),key=lambda e:e['beat'])
            self.assertEqual(len(right),24)
            for i,e in enumerate(right):
                self.assertAlmostEqual(e['beat']-bar*4,i/6)
                self.assertAlmostEqual(e['duration'],1/6)
        last=[e for e in data['events'] if e['measure']==70]
        self.assertAlmostEqual(max(e['beat']+e['duration'] for e in last),282.5)
        self.assertTrue(all(e['beat']>=284 for e in data['events'] if e['measure']==71))

    def test_interstellar_printed_opening_and_independent_voices(self):
        data=score('interstellar')
        self.assertEqual(data['bpm'],90)
        self.assertEqual(data['manuallyReadMeasures'],40)
        for bar in range(4):
            notes=sorted((e for e in data['events'] if e['measure']==bar),key=lambda e:e['beat'])
            self.assertEqual([e['midi'] for e in notes],[64,60]*3)
            self.assertEqual([e['beat']-bar*3 for e in notes],[0,.5,1,1.5,2,2.5])
            self.assertTrue(all(e['duration']==.5 and e['hand']=='R' for e in notes))
        melody=[e for e in data['events'] if e['measure']==4 and e['duration']==3]
        self.assertEqual({(e['midi'],e['hand']) for e in melody},{(69,'R'),(57,'L')})
        for midi in (71,59):
            a=next(e for e in data['events'] if e['measure']==5 and e['midi']==midi)
            b=data['events'][a['tieTo']]
            self.assertEqual(b['measure'],6);self.assertEqual(a['soundDuration'],6)
            self.assertNotIn('soundDuration',b)
        cross=next(e for e in data['events'] if e['measure']==11 and e['beat']==34 and e['hand']=='L' and e['writtenClef']=='G')
        self.assertEqual(cross['midi'],76);self.assertEqual(cross['duration'],2)
        self.assertFalse(data['noteDataComplete'])

    def test_jue_printed_melody_key_tuplet_and_tempos(self):
        import mido
        data=score('jue-bie-shu')
        self.assertEqual(data['manuallyReadMeasures'],25)
        first=[e for e in data['events'] if e['measure']==0 and e['hand']=='R']
        self.assertEqual([e['midi'] for e in first],[74,81,79,81])
        self.assertEqual([e['beat'] for e in first],[0,1,1.5,2])
        self.assertEqual([e['duration'] for e in first],[1,.5,.5,2])
        left=[e for e in data['events'] if e['measure']==0 and e['hand']=='L']
        self.assertEqual({e['midi'] for e in left},{58,65,69})
        self.assertTrue(all(e['duration']==3 for e in left if e['beat']==1))
        tuplet=[e for e in data['events'] if e['measure']==11 and e['hand']=='R']
        self.assertAlmostEqual(tuplet[0]['beat']-44,1/3)
        self.assertTrue(all(e['octaveShift']==12 for e in tuplet))
        mid=mido.MidiFile(ROOT/'scores/jue-bie-shu/performance.mid');tick=0;tempos=[]
        for msg in mid.tracks[0]:
            tick+=msg.time
            if msg.type=='set_tempo':tempos.append((tick/mid.ticks_per_beat,round(mido.tempo2bpm(msg.tempo))))
        self.assertEqual(tempos,[(0,104),(32,132),(100,116),(349,128),(381,104)])
        self.assertFalse(data['noteDataComplete'])

    def test_original_notehead_coverage(self):
        sid='young-and-beautiful'
        with fitz.open(ROOT/'scores'/sid/'original.pdf') as pdf:
            original={(pi,round(c['origin'][0],2),round(c['origin'][1],2))
                      for pi,p in enumerate(pdf) for b in p.get_text('rawdict')['blocks']
                      for line in b.get('lines',[]) for span in line['spans']
                      for c in span['chars'] if span['font']=='MScore' and c['c'] in ('\ue0a2','\ue0a3','\ue0a4')}
        pages=json.loads((ROOT/'transcription'/sid/'geometry.json').read_text())
        extracted=[(p['page'],round(n['ox'],2),round(n['y'],2))
                   for p in pages for sy in p['systems'] for m in sy['measures']
                   for g in m['groups'] for n in g['notes']]
        self.assertEqual(set(extracted),original)
        self.assertEqual(len(extracted),len(score(sid)['events']))

    def test_events_and_ties(self):
        for sid in ['call-of-silence','young-and-beautiful']:
            data=score(sid)
            self.assertEqual(hashlib.sha256((ROOT/'scores'/sid/'original.pdf').read_bytes()).hexdigest(),data['sourceSha256'])
            self.assertEqual({e['page'] for e in data['events']},set(range(data['pages'])))
            self.assertEqual({e['measure'] for e in data['events']},set(range(len(data['measures']))))
            for i,e in enumerate(data['events']):
                self.assertEqual(i,e['id'])
                self.assertTrue(21<=e['midi']<=108)
                self.assertIn(e['hand'],('R','L'))
                self.assertTrue(all(math.isfinite(e[k]) for k in ['beat','duration','x','y']))
                m=data['measures'][e['measure']]
                self.assertGreater(e['duration'],0)
                self.assertGreaterEqual(e['beat'],m['start']-1e-6)
                self.assertLessEqual(e['beat']+e['duration'],m['start']+m['duration']+1e-6)
                if 'tieTo' in e:
                    target=data['events'][e['tieTo']]
                    self.assertEqual(target['tieFrom'],e['id'])
                    self.assertEqual(target['midi'],e['midi'])
                    self.assertEqual(target['hand'],e['hand'])
                    self.assertAlmostEqual(target['beat'],e['beat']+e['duration'])
                if 'tieFrom' in e:
                    self.assertNotIn('soundDuration',e)
                else:
                    self.assertGreaterEqual(e['soundDuration']+1e-6,e['duration'])
            for m in data['measures']:
                for a,b in zip(m['anchors'],m['anchors'][1:]):
                    self.assertLess(a[0],b[0])
                    self.assertLess(a[1],b[1])

    def test_call_tremolo_octave_and_triplet(self):
        data=score('call-of-silence')
        first=[e for e in data['events'] if e['measure']==0 and e['staff']==0]
        self.assertEqual(len(first),32)
        self.assertEqual([e['midi'] for e in first],[80,92]*16)
        self.assertEqual([e['beat'] for e in first],[i/8 for i in range(32)])
        octave=[e for e in data['events'] if e['measure']==5 and e['staff']==0]
        self.assertEqual({e['midi'] for e in octave},{92,104})
        triplet=[e for e in data['events'] if e['measure']==40 and e['staff']==0 and e['sourceGroup'] in [2,3,4]]
        self.assertEqual([e['midi'] for e in triplet],[56,57,59])
        for i,e in enumerate(triplet):
            self.assertAlmostEqual(e['beat']-160,1+i/3)
            self.assertAlmostEqual(e['duration'],1/3)

    def test_young_reading_corrections(self):
        data=score('young-and-beautiful')
        first=[e for e in data['events'] if e['measure']==0 and e['hand']=='R']
        self.assertEqual([e['midi'] for e in first],[73,71,71,76])
        self.assertEqual(first[1]['tieTo'],first[2]['id'])
        natural=[e for e in data['events'] if e['measure']==86 and e['hand']=='L' and e['beat']==344]
        self.assertEqual({e['midi'] for e in natural},{24,36})
        low=[e for e in data['events'] if e['measure']==59 and e['hand']=='L' and e['beat']==239.5]
        self.assertEqual([e['midi'] for e in low],[31])
        triplet=[e for e in data['events'] if e['measure']==103 and e['hand']=='R' and e['beat']>=414]
        self.assertEqual(len(triplet),3)
        for i,e in enumerate(triplet):
            self.assertAlmostEqual(e['beat'],414+i*2/3)
            self.assertAlmostEqual(e['duration'],2/3)
        self.assertEqual({e['midi'] for e in data['events'] if e['measure']==107 and e['hand']=='L'},{62,69})

    def test_yi_lu_small_left_hand_voice(self):
        data=score('yi-lu-xiang-bei')
        self.assertEqual(data['measures'][39]['duration'],6)
        self.assertEqual(data['measures'][40]['duration'],4)
        self.assertEqual(data['totalBeats'],322)
        measure=data['measures'][47]
        cues=[e for e in data['events'] if e['measure']==47 and e['midi'] in (77,79,84)]
        self.assertEqual([e['midi'] for e in cues],[77,79,84])
        self.assertEqual([e['beat']-measure['start'] for e in cues],[1.5,2,2])
        for e in cues:
            self.assertEqual(e['hand'],'L')
            self.assertEqual(e['duration'],.5)
            self.assertFalse(e['grace'])


if __name__=='__main__':
    unittest.main()
