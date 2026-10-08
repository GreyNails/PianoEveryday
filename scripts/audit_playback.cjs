'use strict';
const fs=require('fs'),path=require('path'),Performance=require('../performance.js');
const root=path.resolve(__dirname,'..'),catalog=JSON.parse(fs.readFileSync(path.join(root,'songs.json')));
const report={scope:'Playback data and source-derived timing audit; not a claim of listening or full score review.',changes:['Merge simultaneous unison attacks without changing score/practice events.','Optional upper-voice balance with explicit source dynamics preserved.','Same-pitch re-strikes damp the old excitation; written rests stay rests.','Natural ending keeps sample release and room decay.','Late/seek scheduling resumes sample phase rather than bursting missed attacks.'],scores:[]};
for(const entry of catalog){
 const s=JSON.parse(fs.readFileSync(path.join(root,entry.url))),p=Performance.build(s);
 const reviewPath=path.join(root,'scores',entry.id,'review.json'),review=fs.existsSync(reviewPath)?JSON.parse(fs.readFileSync(reviewPath)):{};
 const attacks=s.events.filter(e=>e.tieFrom==null&&e.soundDuration>0);
 report.scores.push({id:entry.id,title:entry.title,status:entry.transcriptionStatus||'existing',writtenAttacks:attacks.length,playbackAttacks:p.events.length,duplicateAttacksMerged:p.duplicates,sourceVelocityLevels:new Set(attacks.map(e=>e.velocity??1)).size,naturalVelocityLevels:new Set(p.events.map(e=>Math.round(e.velocity*10000))).size,contiguousJoins:p.events.filter(e=>e.legatoSeconds>0).length,unresolvedRhythmMeasures:(review.rhythmIssues||[]).map(e=>({page:e.page,measure:e.measure,readBeats:e.readBeats,meterBeats:e.meterBeats})),sourcePulseAlignedMeasures:review.sourcePulseAlignedMeasures||0,onsetAlignmentCandidatesToReview:(review.onsetAlignmentUncertainties||[]).length,hasPedalExtensions:attacks.some(e=>(e.pedalDuration||0)>e.soundDuration)});
}
report.duplicateAttacksMerged=report.scores.reduce((n,s)=>n+s.duplicateAttacksMerged,0);
report.unresolvedRhythmMeasures=report.scores.reduce((n,s)=>n+s.unresolvedRhythmMeasures.length,0);
report.onsetAlignmentCandidatesToReview=report.scores.reduce((n,s)=>n+s.onsetAlignmentCandidatesToReview,0);
fs.writeFileSync(path.join(root,'transcription/playback-audit.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({songs:report.scores.length,duplicateAttacksMerged:report.duplicateAttacksMerged,unresolvedRhythmMeasures:report.unresolvedRhythmMeasures,onsetAlignmentCandidatesToReview:report.onsetAlignmentCandidatesToReview}));
