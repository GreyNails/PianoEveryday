"""Report extraction availability separately from musical review completion."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
catalog=json.loads((ROOT/'songs.json').read_text());rows=[]
for entry in catalog:
    if not entry.get('collection'):continue
    data=json.loads((ROOT/entry['url']).read_text());status=data.get('transcriptionStatus','pending')
    rows.append(dict(id=entry['id'],title=entry['title'],pages=data['pages'],status=status,events=len(data['events']),playable=bool(entry['playable']),sourceSha256=data['sourceSha256'],manuallyReadMeasures=data.get('manuallyReadMeasures',0),sourcePulseAlignedMeasures=data.get('sourcePulseAlignedMeasures',0),sourceMeasureCount=data.get('sourceMeasureCount',len(data['measures'])),performanceMeasureCount=len(data['measures']),rhythmReviewedMeasures=[m['displayNumber'] for m in data['measures'] if m.get('rhythmReviewed')]))
reviewed=[r for r in rows if r['status']=='manual-reference'];drafts=[r for r in rows if r['status']=='unreviewed-draft'];pending=[r for r in rows if not r['events']];midi_imports=[r for r in rows if r['status']=='midi-imported']
report=dict(request=f'全部 {len(rows)} 份导入 PDF 提取音符，支持自动播放及 MIDI 跟练',complete=not drafts and not pending,extractionAvailable=len(rows)-len(pending),scoresWithoutNoteData=len(pending),transcribed=len(reviewed),midiImported=len(midi_imports),unreviewedDrafts=len(drafts),pending=len(drafts)+len(pending),transcribedPages=sum(r['pages'] for r in reviewed),pendingPages=sum(r['pages'] for r in drafts+pending),totalNoteEvents=sum(r['events'] for r in rows),verification=f'数据与模拟跟练检查不等于准确性校对。{len(drafts)} 首识别草稿未完成逐音核对；不能保证所有音符和节奏正确。未实测实体 MIDI 或浏览器听音。',scores=rows)
(ROOT/'transcription/status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print({k:v for k,v in report.items() if k!='scores'})
