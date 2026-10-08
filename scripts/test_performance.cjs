'use strict';
const assert=require('assert'),fs=require('fs'),path=require('path');
const Performance=require('../performance.js'),SamplePiano=require('../piano-audio.js');
const make=(id,midi,beat,duration,hand='R',extra={})=>({id,midi,beat,duration,soundDuration:duration,hand,measure:0,...extra});
const score={measures:[{start:0,duration:4}],events:[make(0,72,0,1),make(1,64,0,1),make(2,48,0,1,'L'),make(3,72,0,2,'L'),make(4,72,1,.5),make(5,74,1.5,.5),make(6,76,3,1)]};
const original=JSON.stringify(score),plan=Performance.build(score);
assert.equal(plan.duplicates,1);assert.equal(plan.events.filter(e=>e.beat===0&&e.midi===72).length,1);
assert.equal(plan.events.find(e=>e.id===0).pedalDuration,1,'A repeated key ends the previous excitation');
assert(plan.events.find(e=>e.id===0).velocity>plan.events.find(e=>e.id===1).velocity,'Inner chord tones must not cover the top melody');
assert.equal(plan.events.find(e=>e.id===4).legatoSeconds,.025);
assert.equal(plan.events.find(e=>e.id===5).legatoSeconds,0,'Do not fill a written rest');
assert.equal(JSON.stringify(score),original,'Performance shaping must not change the practice score');
assert(Performance.build(score,'written').events.every(e=>e.velocity===1));
assert.equal(Performance.build({events:[make(0,60,0,1,'R',{tieFrom:8})]}).events.length,0);
const marked={events:[make(0,60,0,1,'R',{velocity:.4}),make(1,64,2,1,'R',{velocity:1.1})]};
const explicit=Performance.build(marked).events;assert(explicit[1].velocity>2*explicit[0].velocity,'Keep explicit dynamics');
const leftSolo=Performance.build({events:[make(0,60,0,1,'L')]}).events[0];assert(leftSolo.velocity>=.85,'Do not blanket-soften a left-hand solo');
function param(){return {value:0,log:[],setValueAtTime(v,t){this.log.push(['set',v,t]);},linearRampToValueAtTime(v,t){this.log.push(['linear',v,t]);},exponentialRampToValueAtTime(v,t){this.log.push(['exp',v,t]);},cancelScheduledValues(t){this.log.push(['cancel',t]);},cancelAndHoldAtTime(t){this.log.push(['hold',t]);}};}
function node(){return {connect(){},disconnect(){}};}
class Context{
  constructor(){this.currentTime=0;this.sampleRate=100;this.sources=[];this.gains=[];}
  createGain(){const n={...node(),gain:param()};this.gains.push(n);return n;}
  createConvolver(){return node();}
  createBuffer(channels,length){const data=Array.from({length:channels},()=>new Float32Array(length));return {getChannelData:i=>data[i]};}
  createBiquadFilter(){return {...node(),frequency:param(),Q:param()};}
  createStereoPanner(){return {...node(),pan:param()};}
  createBufferSource(){const n={...node(),playbackRate:param(),starts:[],stops:[],start(...args){this.starts.push(args);},stop(t){this.stops.push(t);}};this.sources.push(n);return n;}
}
const ctx=new Context(),piano=new SamplePiano(ctx,node());piano.buffers.set(60,{duration:20});
const first=piano.play(60,0,.5,'R',1),g=ctx.gains.at(-1).gain;
ctx.currentTime=.6;const value=first.levelAt(.6);assert(value>0&&value<.54);
piano.play(60,.6,1,'R',1);
const sets=g.log.filter(c=>c[0]==='set');assert(Math.abs(sets.at(-1)[1]-value)<1e-9,'Re-damping must hold the decaying envelope, not jump to attack level');
assert(ctx.sources[0].stops.at(-1)<.7,'Repeated notes do not leave the old sustained voice ringing');
ctx.currentTime=1;
piano.play(72,1,2,'R',.7,{offset:1.25});assert.equal(ctx.sources.at(-1).starts[0][1],2.5,'Seek offsets must account for sample pitch rate');
const count=piano.voices.size;assert.equal(piano.play(72,1,1,'R',1,{offset:20}),null);assert.equal(piano.voices.size,count,'An exhausted sample is not re-attacked');
piano.silence();assert.equal(piano.voices.size,0);
const ctx2=new Context(),p2=new SamplePiano(ctx2,node());p2.buffers.set(60,{duration:20});
p2.play(60,1,1,'L',.7);const left=ctx2.gains.at(-1).gain.log.find(c=>c[0]==='linear')[1];
p2.play(60,1,1,'R',.7);const right=ctx2.gains.at(-1).gain.log.find(c=>c[0]==='linear')[1];assert.equal(left,right,'Live input velocity must not depend on assigned hand');
for(const holdSupported of [true,false]){
  const c=new Context(),p=new SamplePiano(c,node());p.buffers.set(60,{duration:20});
  const v=p.play(60,0,.5),gain=c.gains.at(-1).gain;
  if(!holdSupported)delete gain.cancelAndHoldAtTime;
  const expected=v.levelAt(.55);
  v.damp(.65,.028);c.currentTime=.55;v.stop();
  assert(Math.abs(gain.log.filter(e=>e[0]==='set').at(-1)[1]-expected)<1e-9,'Pausing before a scheduled repeat must retain the earlier decay curve');
}
// Imported MIDI expression is already performed; keep written practice beats.
const midiScore={performanceSource:'midi',events:[
  make(0,72,0,1,'R',{playBeat:.023,velocity:91/127,pedalDuration:1.5}),
  make(1,48,0,1,'L',{playBeat:.01,velocity:64/127}),
  make(2,74,1,.5,'R',{playBeat:1.023,velocity:83/127})]};
const midiPlan=Performance.build(midiScore);
assert.deepEqual(midiPlan.events.map(e=>e.beat),[.01,.023,1.023]);
for(const e of midiPlan.events){assert.equal(e.velocity,midiScore.events[e.id].velocity);assert.equal(e.legatoSeconds,0);}
assert.equal(midiScore.events[0].beat,0);assert.equal(midiPlan.events.find(e=>e.id===0).pedalDuration,1.5);
// Inspect every real score, not only synthetic examples.
const root=path.resolve(__dirname,'..'),songs=JSON.parse(fs.readFileSync(path.join(root,'songs.json')));let dedup=0;
for(const song of songs){
  const data=JSON.parse(fs.readFileSync(path.join(root,song.url)));const before=JSON.stringify(data),p=Performance.build(data);dedup+=p.duplicates;
  assert.equal(JSON.stringify(data),before,song.id+' score was mutated');
  const seen=new Set();
  for(const e of p.events){
    const key=Math.round(e.beat*100000)+':'+e.midi;assert(!seen.has(key));seen.add(key);
    assert(Number.isFinite(e.pedalDuration)&&e.pedalDuration>0,song.id+' invalid release');
    assert(Number.isFinite(e.velocity)&&e.velocity>=0&&e.velocity<=1.25);
    if(e.nextAttackBeat!=null)assert(e.beat+e.pedalDuration<=e.nextAttackBeat+1e-5);
  }
}
console.log(`PASS: score-preserving voicing, rests/ties, repeated keys, sample offsets, continuous envelopes and ${songs.length}-score playback plans (${dedup} duplicate attacks removed).`);
