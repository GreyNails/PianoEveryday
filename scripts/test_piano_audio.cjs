const assert=require('assert'),SamplePiano=require('../dist/piano-audio.js');
function param(){return {value:0,events:[],setValueAtTime(v,t){this.events.push(['set',v,t])},linearRampToValueAtTime(v,t){this.events.push(['linear',v,t])},exponentialRampToValueAtTime(v,t){this.events.push(['exp',v,t])},cancelScheduledValues(t){this.events.push(['cancel',t])}};}
let sources=[],filters=[],impulses=0;
const node=()=>({connect(){},disconnect(){this.disconnected=true}});
const ctx={currentTime:1,sampleRate:22050,createGain(){return {...node(),gain:param()}},createStereoPanner(){return {...node(),pan:param()}},createBuffer(c,n){impulses++;return {getChannelData:()=>new Float32Array(n)}},createConvolver:node,createBiquadFilter(){const f={...node(),frequency:param(),Q:param()};filters.push(f);return f},createBufferSource(){const s={...node(),playbackRate:param(),start(t){this.started=t},stop(t){this.stopped=t}};sources.push(s);return s},decodeAudioData:async()=>({duration:20})};
const p=new SamplePiano(ctx,node());for(let n=21;n<=108;n+=3)p.buffers.set(n,{midi:n});
for(let n=21;n<=108;n++){const v=p.play(n,2,.5);const s=sources.at(-1);assert(Math.abs(s.buffer.midi-n)<=1);assert.equal(s.started,2);assert(s.stopped>2.5);v.stop();}
const soft=p.play(60,1,Infinity,'R',.3),softCutoff=filters.at(-1).frequency.value;
const hard=p.play(60,1,Infinity,'R',1.1);assert(filters.at(-1).frequency.value>softCutoff);assert.equal(sources.at(-1).stopped,undefined);hard.release(1.6);assert(sources.at(-1).stopped>1.6);
const oldRoom=p.room;p.silence();assert.equal(p.voices.size,0);assert(oldRoom.disconnected);assert.equal(impulses,1);p.silence();assert.equal(impulses,1);
console.log('88-key sample mapping, velocity response, held-key release and clearing reverb passed.');
