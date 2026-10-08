"""Regressions for specific read source passages, not global accuracy claims."""
import collections,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def score(sid):return json.loads((ROOT/'scores'/sid/'score.json').read_text())
def bar(s,n,hand):
    start=s['measures'][n-1]['start']
    return [(round(e['beat']-start,7),e) for e in s['events'] if e['measure']==n-1 and e['hand']==hand]

class FourSourcePassages(unittest.TestCase):
    def test_flower_complete_fast_runs_and_written_rest(self):
        s=score('flower-dance')
        for n in [47,48,*range(95,105)]:
            es=bar(s,n,'R');count=24 if n==48 else 32
            self.assertEqual(len(es),count,n)
            self.assertEqual(sorted(b for b,e in es),[i/8 for i in range(count)],n)
            self.assertTrue(all(e['duration']==.125 for _,e in es),n)
        self.assertEqual(len(s['measures']),120)
        self.assertEqual(s['totalBeats'],480)
        self.assertEqual(len([e for e in s['events'] if e.get('sourceEvidence')=='visual-head-reading']),106)
        # 48 ends with a quarter rest; 108 holds a half note then rests.
        self.assertFalse(any(b>=3 for b,_ in bar(s,48,'R')))
        self.assertTrue(all(b==0 and e['duration']==2 for b,e in bar(s,108,'R')))

    def test_flower_printed_tempo_changes(self):
        s=score('flower-dance')
        self.assertEqual(s['bpm'],75)
        self.assertEqual([(t['beat'],round(t['factor']*75)) for t in s['tempoMap']],[(0,75),(352,96),(416,90),(448,71)])

    def test_an_jing_ties_and_one_beat_transition(self):
        s=score('an-jing');m=s['measures'][77]
        self.assertEqual(m['duration'],1);self.assertEqual(s['totalBeats'],393)
        self.assertEqual(bar(s,78,'R'),[])
        self.assertTrue(all(b==0 and e['duration']==1 for b,e in bar(s,78,'L')))
        tied=[e for b,e in bar(s,15,'R') if b==2 and 'tieFrom' in e]
        self.assertTrue(tied)
        for e in tied:self.assertEqual(s['events'][e['tieFrom']]['beat'],s['measures'][14]['start']+1.5)
        self.assertTrue(all(e['duration']==.25 for b,e in bar(s,16,'R') if b==2.75))

    def test_ge_qian_measured_tremolo_and_cue_voice(self):
        s=score('ge-qian');es=[(b,e) for b,e in bar(s,4,'R') if e.get('sourceRepeat')]
        self.assertEqual(sorted(set(b for b,e in es)),[2+i/16 for i in range(24)])
        self.assertTrue(all(e['duration']==1/16 for b,e in es))
        self.assertEqual(s['measures'][48]['duration'],3.25)
        self.assertEqual(s['totalBeats'],239.25)
        for n in (5,25,26,31,32,41,53):self.assertFalse(any(e['grace'] for _,e in bar(s,n,'R')),n)
        small=[e for b,e in bar(s,53,'L') if b<1]
        self.assertTrue(small);self.assertTrue(all(abs(e['duration']-1/6)<1e-7 for e in small))
        self.assertEqual(min(e['midi'] for b,e in bar(s,17,'L') if b==0),22)
        self.assertIn(97,[e['midi'] for b,e in bar(s,49,'R') if b==.1])

    def test_pu_gong_ying_tuplets_and_displaced_chords(self):
        s=score('pu-gong-ying-de-yue-ding')
        rr=bar(s,70,'R');self.assertEqual(sorted(set(b for b,e in rr if b<1)),[0,.2,.4,.6,.8])
        self.assertEqual(sorted(set(b for b,e in bar(s,61,'R') if .5<=b<1)),[round(.5+i/12,7) for i in range(6)])
        for n in (17,25):
            self.assertFalse(any(3<b<3.75 for b,e in bar(s,n,'R')))
            self.assertTrue(all(e['duration']==.75 for b,e in bar(s,n,'R') if b==3))
        # The corrected edition keeps every PDF notehead, including seconds.
        ps=json.loads((ROOT/'transcription/pu-gong-ying-de-yue-ding/geometry-raw.json').read_text())
        heads=collections.Counter((p['page'],round(h['x'],3),round(h['y'],3)) for p in ps for sy in p['systems'] for m in sy['measures'] for g in m['groups'] for h in g['notes'])
        events=collections.Counter((e['page'],round(e['x'],3),round(e['y'],3)) for e in s['events'])
        self.assertEqual(events,heads)

if __name__=='__main__':unittest.main()
