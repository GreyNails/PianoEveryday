"""Source passage regressions for the three reported playback problems."""
import collections
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent.parent

def read(sid):
    return json.loads((ROOT/'scores'/sid/'score.json').read_text())

def passage(d,number,hand):
    m=d['measures'][number-1]
    return m,sorted([e for e in d['events'] if e['measure']==number-1 and e['hand']==hand],key=lambda e:e['beat'])

class ThreeSongRhythm(unittest.TestCase):
    def test_qili_small_heads_are_not_all_grace_notes(self):
        import mido
        d=read('qi-li-xiang')
        self.assertEqual(sum(e.get('noteSize')=='small' for e in d['events']),225)
        m,es=passage(d,9,'R')
        cue=[e for e in es if e.get('noteSize')=='small']
        self.assertEqual(len(cue),3)
        self.assertTrue(all(e['beat']==m['start']+2 and e['duration']==1 and not e['grace'] for e in cue))
        m,es=passage(d,75,'R')
        cue=[e for e in es if e.get('noteSize')=='small']
        self.assertEqual(sorted({e['beat']-m['start'] for e in cue}),[0,.5,.75,1,1.25])
        self.assertTrue(all(not e['grace'] and e['velocity']<.8 for e in cue))
        for number,pitches in [(5,[84,87,84]),(81,[72,75,72])]:
            m,es=passage(d,number,'R');grace=[e for e in es if e['grace']]
            self.assertEqual([e['midi'] for e in grace],pitches)
            self.assert_run(grace,m['start']+3.625,.125,3)
        # An F1 pickup below bar 30 must not become a G7 in bar 33.
        m,es=passage(d,30,'L')
        self.assertTrue(any(e['midi']==29 and e['grace'] and abs(e['beat']-m['start']-3.9)<1e-7 for e in es))
        self.assertFalse(any(e['midi']==103 for e in passage(d,33,'R')[1]))
        m,es=passage(d,69,'R')
        held=[e for e in es if e['beat']==m['start'] and e['midi'] in (75,79,84)]
        self.assertEqual(len(held),3)
        for e in held:
            while 'tieFrom' in e:e=d['events'][e['tieFrom']]
            self.assertAlmostEqual(e['beat']+e['soundDuration'],m['start']+1.5)
        # Export keeps the same lighter attacks as the source event plan.
        mid=mido.MidiFile(ROOT/'scores/qi-li-xiang/performance.mid')
        actual=collections.Counter((msg.note,msg.velocity) for tr in mid.tracks for msg in tr if msg.type=='note_on' and msg.velocity)
        expected=collections.Counter((e['midi'],e.get('midiVelocity',75)) for e in d['events'] if 'tieFrom' not in e)
        self.assertEqual(actual,expected)

    def assert_run(self,events,start,step,count):
        self.assertEqual(len(events),count)
        for i,e in enumerate(events):
            self.assertAlmostEqual(e['beat'],start+i*step)
            self.assertAlmostEqual(e['duration'],step)

    def test_qili_seven_and_nine_note_groups(self):
        d=read('qi-li-xiang')
        for number,offset,step,count in [(56,3,1/14,14),(80,2,1/9,18)]:
            m,es=passage(d,number,'R')
            fast=[e for e in es if e['beat']>=m['start']+offset]
            self.assert_run(fast,m['start']+offset,step,count)
        # The two septuplets join by step when the 8va bracket ends.
        m,es=passage(d,56,'R')
        fast=[e for e in es if e['beat']>=m['start']+3]
        self.assertEqual([e['midi'] for e in fast],[89,87,86,84,82,80,79,77,75,74,72,70,68,67])

    def test_hei_tempo_cross_staff_and_octave_endpoint(self):
        d=read('hei-se-mao-yi')
        self.assertEqual(d['tempoMap'],[{'beat':0,'factor':1},{'beat':12,'factor':62/50}])
        m,es=passage(d,78,'R')
        self.assert_run(es[:-1],m['start']+.25,1/12,18)
        self.assertEqual([e['midi'] for e in es],[76,81,83,88,93,95,100,95,93,88,83,81,76,71,69,64,59,57,52])
        m,es=passage(d,97,'R')
        self.assertEqual({e['midi'] for e in es if e['beat']==m['start']},{53,57,60})
        m,es=passage(d,4,'L')
        self.assertEqual([(e['beat']-m['start'],e['duration']) for e in es if e['midi']==45],[(0,3)])
        m,es=passage(d,120,'R')
        self.assertTrue(all('tieFrom' in e for e in es))

    def test_vector_source_heads_are_preserved(self):
        for sid in ('qi-li-xiang','hei-se-mao-yi'):
            ps=json.loads((ROOT/'transcription'/sid/'geometry-raw.json').read_text())
            raw=collections.Counter((p['page'],round(n['x'],3),round(n['y'],3)) for p in ps for s in p['systems'] for m in s['measures'] for g in m['groups'] for n in g['notes'])
            events=collections.Counter((e['page'],round(e['x'],3),round(e['y'],3)) for e in read(sid)['events'])
            self.assertEqual(raw,events,sid)

    def test_jue_fast_groups_meter_ending_and_written_rest(self):
        d=read('jue-bie-shu')
        self.assertEqual(d['sourcePulseAlignedMeasures'],75)
        self.assertEqual([d['measures'][n-1]['duration'] for n in [53,54,55,56,57]],[4,3,3,3,4])
        self.assertEqual(d['totalBeats'],397)
        m,es=passage(d,47,'R');fast=[e for e in es if e['beat']>=m['start']+2.5]
        self.assert_run(fast[:-1],m['start']+2.5,1/16,16)
        self.assertEqual((fast[-1]['beat']-m['start'],fast[-1]['duration']), (3.5,.25))
        self.assertFalse(any(e['beat']>=m['start']+3.75 for e in es))
        m,es=passage(d,68,'R')
        self.assert_run(es[:4],m['start'],.25,4)
        self.assert_run(es[4:],m['start']+1,1/6,18)
        m,es=passage(d,56,'L')
        fast=[e for e in es if m['start']+.5<=e['beat']<m['start']+1]
        self.assert_run(fast,m['start']+.5,1/12,6)
        self.assertFalse(any(m['start']+1<=e['beat']<m['start']+1.25 for e in es))
        for n,pitches in [(99,{65,67,72,76}),(100,{74})]:
            m,es=passage(d,n,'R')
            self.assertEqual({e['midi'] for e in es},pitches)
            self.assertTrue(all(e['duration']==4 for e in es))
        for sid in ('jue-bie-shu','qi-li-xiang','hei-se-mao-yi'):
            r=json.loads((ROOT/'scores'/sid/'review.json').read_text())
            self.assertEqual(r['rhythmIssues'],[])
            self.assertFalse(read(sid)['noteDataComplete'])

if __name__=='__main__':unittest.main()
