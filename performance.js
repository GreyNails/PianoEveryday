'use strict';
// Playback interpretation is separate from written notes and MIDI practice.
// "natural" is a conservative upper-voice balance, not a new transcription.
const PianoPerformance=(()=>{
  const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
  function build(score,mode='natural'){
    const merged=new Map();let duplicates=0;
    for(const writtenEvent of score.events||[]){
      const event=score.performanceSource==='midi'?{...writtenEvent,beat:writtenEvent.playBeat}:writtenEvent;
      if(event.tieFrom!=null||!(event.soundDuration>0))continue;
      const key=Math.round(event.beat*100000)+':'+event.midi;
      const explicitVelocity=Number.isFinite(event.velocity),velocity=explicitVelocity?event.velocity:1;
      const duration=Math.max(event.soundDuration,event.pedalDuration||0);
      if(merged.has(key)){
        const e=merged.get(key);duplicates++;e.sourceIds.push(event.id);
        e.soundDuration=Math.max(e.soundDuration,event.soundDuration);
        e.pedalDuration=Math.max(e.pedalDuration,duration);
        if(explicitVelocity&&!e.explicitVelocity){e.velocity=velocity;e.explicitVelocity=true;}
        else if(explicitVelocity===e.explicitVelocity)e.velocity=Math.max(e.velocity,velocity);
        if(event.hand==='R')e.hand='R';
      }else merged.set(key,{...event,velocity,explicitVelocity,pedalDuration:duration,sourceIds:[event.id],legatoSeconds:0});
    }
    const events=[...merged.values()].sort((a,b)=>a.beat-b.beat||a.midi-b.midi);
    const onsets=[];
    for(const e of events){
      let group=onsets.at(-1);
      if(!group||Math.abs(group.beat-e.beat)>1e-5){group={beat:e.beat,events:[]};onsets.push(group);}
      group.events.push(e);
    }
    let rightActiveUntil=-Infinity;
    for(const group of onsets){
      const right=group.events.filter(e=>e.hand==='R'&&!e.grace),left=group.events.filter(e=>e.hand==='L');
      const highest=Math.max(...right.map(e=>e.midi)),bass=Math.min(...left.map(e=>e.midi));
      if(right.length)rightActiveUntil=Math.max(rightActiveUntil,...right.map(e=>e.beat+e.soundDuration));
      const measure=score.measures?.[group.events[0].measure];
      const local=measure?group.beat-measure.start:0;
      for(const e of group.events){
        if(mode!=='natural'||score.performanceSource==='midi')continue;
        if(!e.explicitVelocity)e.velocity=.85;
        let balance=1;
        // Leave left-hand solos alone. Explicit role metadata takes priority.
        const role=e.voiceRole;
        if(role==='melody')balance=1.03;
        else if(role==='accompaniment')balance=.85;
        else if(e.hand==='R'&&right.length>1)balance=e.midi===highest?1.03:e.midi===highest-12?.91:.81;
        else if(e.hand==='L'&&rightActiveUntil>group.beat+1e-5)balance=e.midi===bass?.94:.85;
        if(e.grace)balance*=.87;
        // Tiny, repeatable metric weighting; no random timing or automatic rubato.
        const pulse=e.grace?1:Math.abs(local)<1e-5?1.015:Math.abs(local-Math.round(local))<1e-5?1:.985;
        e.velocity=clamp(e.velocity*balance*pulse,0,1.25);
      }
    }
    // The same physical string is re-struck, not layered as independent pianos.
    const nextPitch=new Map(),nextHand=new Map();
    for(let i=onsets.length-1;i>=0;i--){
      const group=onsets[i];
      for(const e of group.events){
        const repeat=nextPitch.get(e.midi),next=nextHand.get(e.hand);
        e.nextAttackBeat=repeat?.beat??null;
        e.pedalDuration=Math.max(0,Math.min(e.pedalDuration,repeat?repeat.beat-e.beat:Infinity));
        // A small finger overlap only at an already contiguous melodic join.
        // Never fill a written rest, repeat a tied attack, or sustain staccato.
        const end=e.beat+e.soundDuration;
        if(mode==='natural'&&score.performanceSource!=='midi'&&!e.grace&&!e.articulation&&next&&Math.abs(end-next.beat)<1e-5&&next.events.some(n=>n.hand===e.hand&&n.midi!==e.midi)&&(!repeat||repeat.beat>end+1e-5))e.legatoSeconds=.025;
      }
      for(const e of group.events){nextPitch.set(e.midi,e);nextHand.set(e.hand,group);}
    }
    return {events,duplicates,mode};
  }
  return {build};
})();
if(typeof module!=='undefined')module.exports=PianoPerformance;
