// Headless DOM/audio contract test. This is not a browser or listening test.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const root=path.resolve(__dirname,'../dist');
class Element{
 constructor(tag='div'){this.tag=tag;this.children=[];this.style={};this.dataset={};this.listeners={};this.value='';this.hidden=false;this.scrollTop=0;this.scrollLeft=0;this.scrollWidth=3000;this.checked=true;this.complete=true;this.textContent='';this.classList={add(){},remove(){},toggle(){},contains(){return false}};}
 append(...a){this.children.push(...a)} replaceChildren(...a){this.children=a} setAttribute(k,v){this[k]=v} addEventListener(k,v){this.listeners[k]=v} querySelector(t){return this.children.find(c=>c.tag===t)||new Element(t)} getBoundingClientRect(){return {top:0,left:0,right:600,bottom:900,width:600,height:900}} scrollTo(x){Object.assign(this,{scrollTop:x.top||0,scrollLeft:x.left||0})} setPointerCapture(){}
}
let nodes=new Map();const get=id=>{if(!nodes.has(id))nodes.set(id,new Element());return nodes.get(id)};get('volume').value=65;
const param=()=>({value:0,setValueAtTime(){},linearRampToValueAtTime(){},exponentialRampToValueAtTime(){},cancelScheduledValues(){},setTargetAtTime(){}});
let starts=0,stops=0;
class AudioContext{
 constructor(){this.currentTime=0;this.sampleRate=44100;this.destination={}}
 createBuffer(c,n){return {getChannelData:()=>new Float32Array(n)}}createConvolver(){return {connect(){},disconnect(){}}}createBiquadFilter(){return {frequency:param(),Q:param(),connect(){},disconnect(){}}}decodeAudioData(){return Promise.resolve({duration:16})}createBufferSource(){return {playbackRate:param(),connect(){},disconnect(){},start(){starts++},stop(){stops++}}}resume(){return Promise.resolve()}createGain(){return {gain:param(),connect(){},disconnect(){}}}createStereoPanner(){return {pan:param(),connect(){},disconnect(){}}}createDynamicsCompressor(){return {threshold:param(),knee:param(),ratio:param(),connect(){}}}createPeriodicWave(){return {}}createOscillator(){return {frequency:param(),detune:param(),connect(){},setPeriodicWave(){},start(){starts++},stop(){stops++}}}
}
const handlers={};const sandbox={console,navigator:{},document:{getElementById:get,querySelector:get,createElement:t=>new Element(t),createElementNS:(_,t)=>new Element(t)},window:{AudioContext,addEventListener(name,fn){(handlers[name]??=[]).push(fn)}},location:{hash:''},history:{replaceState(){}},AbortController,clearTimeout,fetch:async u=>({ok:true,arrayBuffer:async()=>new ArrayBuffer(10),json:async()=>JSON.parse(fs.readFileSync(path.join(root,u),'utf8'))}),setInterval:()=>1,clearInterval(){},setTimeout,requestAnimationFrame(){}};
vm.createContext(sandbox);vm.runInContext(fs.readFileSync(path.join(root,'piano-audio.js'),'utf8'),sandbox);vm.runInContext(fs.readFileSync(path.join(root,'fingering.js'),'utf8'),sandbox);vm.runInContext(fs.readFileSync(path.join(root,'app.js'),'utf8'),sandbox);
(async()=>{await new Promise(r=>setImmediate(r));
 for(const id of ['sunshine','iris-out','feng','tanjiro','sunshine']){
  await vm.runInContext(`loadSong('${id}')`,sandbox);
  assert(vm.runInContext('playable()',sandbox));assert(!get('play').disabled);assert(vm.runInContext('keys.size>40',sandbox));
  assert.equal(get('pageNav').children.length,vm.runInContext('score.pages',sandbox));
  vm.runInContext('for(let b=0;b<=score.totalBeats;b+=.31){if(Math.abs(secondsBeat(beatSeconds(b))-b)>1e-7)throw Error("clock inverse");}',sandbox);
  await vm.runInContext('start()',sandbox);assert(vm.runInContext('playing',sandbox));
  vm.runInContext('ctx.currentTime+=.7;render();pause()',sandbox);assert(!vm.runInContext('playing',sandbox));assert(vm.runInContext('voices.size===0',sandbox));
  vm.runInContext('seek(score.totalBeats*.54);render()',sandbox);await vm.runInContext('start()',sandbox);
  vm.runInContext('ctx.currentTime+=.2;schedule();pause();seek(score.totalBeats);render()',sandbox);
  assert.equal(get('status').textContent,'播放结束');
  console.log(id,'load, clock, play, pause, seek, keys OK');
 }
 assert(starts>0&&stops>=starts);
 await vm.runInContext("Promise.all([loadSong('feng'),loadSong('iris-out')])",sandbox);assert.equal(get('songTitle').textContent,'IRIS OUT');
 for(const id of ['sunshine','iris-out','feng','tanjiro']){
  await vm.runInContext(`loadSong('${id}')`,sandbox);
  for(const hand of ['L','R']){
   vm.runInContext(`changePracticeMode('${hand}');seek(0)`,sandbox);await vm.runInContext('start()',sandbox);
   assert(vm.runInContext('practiceRunning&&!playing',sandbox));
   const b=vm.runInContext('beat',sandbox);vm.runInContext('ctx.currentTime+=100;render()',sandbox);assert.equal(vm.runInContext('beat',sandbox),b);
   vm.runInContext('practicePress(practiceSteps[practiceIndex].notes.includes(21)?22:21)',sandbox);assert.equal(vm.runInContext('practiceIndex',sandbox),0);
   vm.runInContext('practiceSteps[practiceIndex].notes.slice().forEach(practicePress)',sandbox);assert.equal(vm.runInContext('practiceIndex',sandbox),1);
   vm.runInContext('pause();practicePress(practiceSteps[practiceIndex].notes[0])',sandbox);assert.equal(vm.runInContext('practiceIndex',sandbox),1);
   vm.runInContext('seek(score.totalBeats*.5)',sandbox);assert(vm.runInContext('beat===practiceSteps[practiceIndex].beat',sandbox));
   vm.runInContext('seek(practiceSteps.at(-1).beat)',sandbox);await vm.runInContext('start()',sandbox);
   vm.runInContext('practiceSteps.at(-1).notes.slice().forEach(practicePress)',sandbox);assert(vm.runInContext('!practiceRunning&&beat===score.totalBeats',sandbox));
   assert(vm.runInContext('practiceSteps.every(s=>s.events.every(e=>e.hand===practiceMode&&e.tieFrom==null))',sandbox));
  }
  console.log(id,'both hand practice, wrong note, pause, seek, end OK');
 }
 // Repeated pitches need fresh note-on; chord clicks accumulate, ties omitted.
 vm.runInContext(`pause();practiceMode='R';score={...score,totalBeats:4,events:[
 {id:0,midi:60,beat:0,duration:1,hand:'R'}, {id:1,midi:64,beat:0,duration:1,hand:'R'},
 {id:2,midi:60,beat:1,duration:1,hand:'R'}, {id:3,midi:60,beat:2,duration:1,hand:'R',tieFrom:2},
 {id:4,midi:65,beat:3,duration:1,hand:'L'}]};buildPractice();beat=0;locatePractice();practiceRunning=true;`,sandbox);
 assert.equal(vm.runInContext('practiceSteps.length',sandbox),2);
 // Render requires physical score coordinates: keep matching logic but stub rendering.
 vm.runInContext('render=()=>{};followPosition=()=>{};renderPractice=()=>{}',sandbox);
 vm.runInContext("inputDown(60,'computer:KeyA');inputDown(64,'computer:KeyD')",sandbox);assert.equal(vm.runInContext('practiceIndex',sandbox),1);
 vm.runInContext("inputDown(60,'computer:KeyA')",sandbox);assert.equal(vm.runInContext('practiceIndex',sandbox),1);
 vm.runInContext("inputUp('computer:KeyA');inputDown(60,'computer:KeyA')",sandbox);assert(vm.runInContext('!practiceRunning&&practiceIndex===2',sandbox));
 vm.runInContext("clearInputs();practiceIndex=0;practiceRunning=true;practiceHits.clear();midiMessage('test',{data:[144,60,90]});midiMessage('test',{data:[144,60,0]})",sandbox);assert.equal(vm.runInContext('heldInputs.size',sandbox),0);
 await get('connectMidi').onclick();assert(get('midiStatus').textContent.includes('不支持 MIDI'));
 console.log('all tests passed',starts,'sample voice starts');
})().catch(e=>{console.error(e);process.exitCode=1});
