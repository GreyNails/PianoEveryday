"""Exact import invariants: MIDI fidelity, practice grouping and PDF anchors."""
import collections,hashlib,json,unittest
from pathlib import Path
import mido
from import_midi_collection import midi_read,IDS
ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT.parent.parent/'pianogen3/final'

class MidiCollection(unittest.TestCase):
    def test_every_final_score_is_available_with_original_midi(self):
        catalog=json.loads((ROOT/'songs.json').read_text());entries=[e for e in catalog if e.get('collection')=='pianogen3-final']
        self.assertEqual({e['id'] for e in entries},{'final-'+s for s in IDS.values()})
        self.assertEqual(len(catalog),51)
        for entry in entries:
            with self.subTest(score=entry['id']):
                folder=ROOT/entry['base'];s=json.loads((folder/'score.json').read_text());r=json.loads((folder/'review.json').read_text())
                name=next(k for k,v in IDS.items() if entry['id']=='final-'+v);original=SOURCE/name/(name+'.mid')
                self.assertEqual((folder/'performance.mid').read_bytes(),original.read_bytes())
                self.assertEqual(hashlib.sha256((folder/'original.pdf').read_bytes()).hexdigest(),s['sourceSha256'])
                self.assertEqual(s['performanceSource'],'midi');self.assertEqual(s['mode'],'play')
                notes,tempo,bpm,tpb,controls=midi_read(original)
                sig=lambda e:(e['hand'],e['midi'],e['sourceTrack'],e['sourceOnTick'],e['sourceOffTick'],e['midiVelocity'])
                self.assertEqual(collections.Counter(map(sig,s['events'])),collections.Counter(map(sig,notes)))
                by={sig(e):e for e in notes}
                for i,e in enumerate(s['events']):
                    self.assertEqual(e['id'],i);raw=by[sig(e)]
                    for k in ('playBeat','soundDuration','velocity'):self.assertEqual(e[k],raw[k])
                    self.assertEqual(e.get('pedalDuration'),raw.get('pedalDuration'))
                    m=s['measures'][e['measure']];system=s['systems'][e['system']];size=s['pageSizes'][e['page']]
                    self.assertEqual(e['page'],m['page']);self.assertEqual(m['system'],e['system'])
                    self.assertGreaterEqual(e['beat'],m['start']);self.assertLess(e['beat'],m['start']+m['duration'])
                    self.assertTrue(0<=e['x']<=size['width'] and 0<=e['y']<=size['height'])
                    self.assertTrue(m['left']<=e['x']<=m['right'],(e,m))
                    self.assertTrue(system['top']<=e['y']<=system['bottom'])
                self.assertEqual(s['tempoMap'],tempo);self.assertEqual(s['bpm'],bpm)
                self.assertEqual(r['midiControllers'],controls);self.assertTrue(r['allMidiNotesMapped'])
                for m in s['measures']:
                    self.assertGreaterEqual(len(m['anchors']),2)
                    self.assertEqual(m['anchors'][0][0],m['start'])
                    self.assertEqual(m['anchors'][-1][0],m['start']+m['duration'])
                    for a,b in zip(m['anchors'],m['anchors'][1:]):self.assertTrue(a[0]<b[0] and a[1]<b[1])
                self.assertTrue(all((folder/f'page-{pi+1}.png').exists() for pi in range(s['pages'])))

    def test_humanized_chords_remain_single_practice_groups(self):
        s=json.loads((ROOT/'scores/final-enchanted/score.json').read_text())
        chords=collections.defaultdict(list)
        for e in s['events']:chords[e['beat']].append(e)
        varied=[es for es in chords.values() if len({e['playBeat'] for e in es})>1]
        self.assertGreater(len(varied),10)
        self.assertTrue(all(len({e['beat'] for e in es})==1 for es in varied))

if __name__=='__main__':unittest.main()
