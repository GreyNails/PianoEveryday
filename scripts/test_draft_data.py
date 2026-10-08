"""Integrity and source-provenance checks, not musical-accuracy certification."""
import collections,hashlib,json,math,unittest
from pathlib import Path
import mido
ROOT=Path(__file__).resolve().parent.parent

class DraftIntegrity(unittest.TestCase):
    def test_all_scores_have_real_source_candidates_and_midi(self):
        catalog=json.loads((ROOT/'songs.json').read_text())
        imported=[e for e in catalog if e.get('collection') in ('puzi','add2')]
        self.assertEqual(len(imported),26)
        self.assertEqual(sum(e['collection']=='puzi' for e in imported),25)
        drafts=[e for e in imported if e.get('transcriptionStatus')=='unreviewed-draft']
        self.assertEqual(len(drafts),24)
        for entry in drafts:
            sid=entry['id']
            with self.subTest(score=sid):
                data=json.loads((ROOT/entry['url']).read_text())
                self.assertTrue(entry['playable']);self.assertEqual(data['mode'],'play')
                self.assertTrue(data['reviewRequired']);self.assertFalse(data['noteDataComplete'])
                self.assertIn('未校对',data['performanceNote'])
                self.assertEqual(data['sourceSha256'],hashlib.sha256((ROOT/entry['pdf']).read_bytes()).hexdigest())
                folder=ROOT/'transcription'/sid;path=folder/'geometry-raw.json'
                if not path.exists():path=folder/'geometry-candidates.json'
                ps=json.loads(path.read_text())
                candidates=collections.Counter((p['page'],round(n['x'],3),round(n['y'],3)) for p in ps for s in p['systems'] for m in s['measures'] for g in m['groups'] for n in g['notes'])
                self.assertEqual(len(ps),data['pages'])
                report=json.loads((ROOT/'scores'/sid/'review.json').read_text());self.assertFalse(report['reviewed'])
                visual={n['id']:n for n in report.get('visualReadings',[])}
                self.assertGreater(len(data['events']),0)
                self.assertEqual(sum(report['pageEventCounts']),len(data['events']))
                for pi,count in enumerate(report['pageEventCounts']):
                    if sid=='interstellar' and pi==0:self.assertEqual(count,0)
                    else:self.assertGreater(count,0,('No notes on a music page',sid,pi+1))
                for i,e in enumerate(data['events']):
                    self.assertEqual(i,e['id']);self.assertTrue(21<=e['midi']<=108);self.assertIn(e['hand'],('L','R'))
                    self.assertTrue(all(math.isfinite(e[k]) for k in ('beat','duration','x','y')))
                    pos=(e['page'],round(e['x'],3),round(e['y'],3))
                    if e.get('sourceEvidence')=='visual-reading':
                        self.assertIn(i,visual,('Missing explicit visual source annotation',e))
                        n=visual[i]
                        self.assertEqual((n['page']-1,n['x'],n['y'],n['midi']),(e['page'],e['x'],e['y'],e['midi']))
                        self.assertIn(e['page']+1,report['reviewedPageNumbers'])
                    elif e.get('sourceRepeat')=='printed-measured-tremolo':
                        self.assertIn(sid,('uchiage-hanabi','interstellar','silksong-clockwork-dancers','ge-qian'))
                        if sid=='uchiage-hanabi':self.assertEqual(e['measure'],23)
                        elif sid=='interstellar':self.assertTrue(101<=e['measure']<=106)
                        elif sid=='ge-qian':self.assertEqual(e['measure'],3)
                        else:self.assertTrue(43<=e['measure']<=45)
                        self.assertGreater(candidates[pos],0,('Tremolo needs a printed notehead',e))
                        self.assertEqual(e['duration'],1/16 if sid=='ge-qian' else .125)
                    else:
                        self.assertGreater(candidates[pos],0,('No printed source candidate',e));candidates[pos]-=1
                    measure=data['measures'][e['measure']]
                    self.assertGreater(e['duration'],0)
                    self.assertGreaterEqual(e['beat']+1e-6,measure['start'])
                    self.assertLessEqual(e['beat']+e['duration'],measure['start']+measure['duration']+1e-6)
                    size=data['pageSizes'][e['page']];self.assertTrue(0<=e['x']<=size['width'] and 0<=e['y']<=size['height'])
                    if 'tieTo' in e:
                        target=data['events'][e['tieTo']];self.assertEqual(target['tieFrom'],i);self.assertEqual(target['midi'],e['midi']);self.assertAlmostEqual(target['beat'],e['beat']+e['duration'])
                    if 'tieFrom' in e:self.assertNotIn('soundDuration',e)
                    else:self.assertGreaterEqual(e['soundDuration']+1e-6,e['duration'])
                for m in data['measures']:
                    for a,b in zip(m['anchors'],m['anchors'][1:]):self.assertLess(a[0],b[0]);self.assertLess(a[1],b[1])
                midi=mido.MidiFile(ROOT/'scores'/sid/'performance.mid')
                ons=collections.Counter(msg.note for tr in midi.tracks for msg in tr if msg.type=='note_on' and msg.velocity)
                attacks=collections.Counter(e['midi'] for e in data['events'] if 'tieFrom' not in e)
                self.assertEqual(ons,attacks)
                self.assertTrue(all(msg.time>=0 for tr in midi.tracks for msg in tr))

if __name__=='__main__':unittest.main()
