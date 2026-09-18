'use strict';
const $=id=>document.getElementById(id);
const NS='http://www.w3.org/2000/svg';
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
const names=['C','C♯','D','D♯','E','F','F♯','G','G♯','A','A♯','B'];
const noteName=n=>names[n%12]+(Math.floor(n/12)-1);
const timeString=s=>Math.floor(s/60)+':'+String(Math.floor(s%60)).padStart(2,'0');
let score,starting=false,playing=false,beat=0,tempo=140,anchorBeat=0,anchorTime=0,ctx,master,limiter,piano;
let queueIndex=0,timer=null,soundEvents=[],voices=new Set(),lastSystem=-1,lastActive='',scrubbing=false,wasPlaying=false;
let lastFingers="",fingerMap=new Map();const fingerBadges=new Map();
const keys=new Map(),pageEls=[],overlays=[],pointers=[],noteLayers=[];
let songs=[],songBase='',loadGeneration=0,startGeneration=0;
const playable=()=>!!score&&score.mode!=='view';
const pageSize=p=>score.pageSizes?.[p]||{width:score.width,height:score.height};
let practiceMode='play',practiceRunning=false,practiceSteps=[],practiceIndex=0;
const practiceHits=new Set(),heldInputs=new Map();
const practicing=()=>practiceMode!=='play';
const running=()=>playing||practiceRunning;
function buildPractice(){
  practiceSteps=[];
  if(!playable()||!practicing())return;
  const attacks=score.events.filter(e=>e.hand===practiceMode&&e.tieFrom==null).sort((a,b)=>a.beat-b.beat);
  for(const e of attacks){let step=practiceSteps.at(-1);if(!step||Math.abs(step.beat-e.beat)>1e-5){step={beat:e.beat,events:[],notes:[]};practiceSteps.push(step);}step.events.push(e);if(!step.notes.includes(e.midi))step.notes.push(e.midi);}
  practiceSteps.forEach(s=>s.notes.sort((a,b)=>a-b));
}
function locatePractice(){
  practiceHits.clear();practiceIndex=practiceSteps.findIndex(s=>s.beat>=beat-1e-5);
  if(practiceIndex<0)practiceIndex=practiceSteps.length;
  beat=practiceSteps[practiceIndex]?.beat??score.totalBeats;lastActive='';
}
function renderFingers(active){
  const signature=String($('showFingers').checked)+':'+active.map(e=>e.id).join(',');
  if(signature===lastFingers)return;lastFingers=signature;
  for(const badge of fingerBadges.values()){badge.hidden=true;badge.textContent='';}
  $('fingerAdvice').hidden=!$('showFingers').checked;
  if(!$('showFingers').checked)return;
  const text=[],warnings=new Set();
  for(const hand of ['R','L']){
    const es=active.filter(e=>e.hand===hand),items=[];
    for(const e of es){const advice=fingerMap.get(e.id);if(!advice)continue;
      if(advice.warning)warnings.add(advice.warning);
      items.push(noteName(e.midi)+'：'+(advice.finger?advice.finger+' 指':'待调整'));
      const badge=fingerBadges.get(e.midi);if(advice.finger&&badge){badge.hidden=false;badge.textContent+=(badge.textContent?' / ':'')+(hand==='R'?'右':'左')+advice.finger;}
    }
    if(items.length)text.push((hand==='R'?'右手 ':'左手 ')+[...new Set(items)].join(' · '));
  }
  $('fingerAdvice').textContent=(text.join(' ｜ ')||'选择练习模式或播放，查看当前音的建议指法。')+(warnings.size?' '+[...warnings].join(' '):'');
}
$('showFingers').addEventListener('change',()=>render());
function renderPractice(){
  $('practicePanel').hidden=!practicing();document.querySelector('.app').classList.toggle('practicing',practicing());
  for(const k of keys.values())k.classList.remove('expected','matched');
  if(!practicing()||!playable())return;
  const step=practiceSteps[practiceIndex];
  $('practiceCount').textContent=step?`${practiceIndex+1} / ${practiceSteps.length} 组`:`${practiceSteps.length} / ${practiceSteps.length} 组`;
  if(!step){$('practicePrompt').textContent='本曲练习完成，点击开始可重新练习。';return;}
  const missing=step.notes.filter(n=>!practiceHits.has(n));
  $('practicePrompt').textContent=(practiceRunning?'等待'+(practiceMode==='L'?'左手':'右手')+'：':'点击「开始练习」：')+missing.map(noteName).join(' · ');
  for(const n of step.notes)keys.get(n)?.classList.add(practiceHits.has(n)?'matched':'expected');
}
function practicePress(n){
  if(!practiceRunning||!playable())return;
  const step=practiceSteps[practiceIndex];if(!step)return;
  if(!step.notes.includes(n)){
    const key=keys.get(n);key?.classList.add('wrong');setTimeout(()=>key?.classList.remove('wrong'),220);
    $('practicePrompt').textContent=`${noteName(n)} 不在当前提示中，请按：`+step.notes.filter(v=>!practiceHits.has(v)).map(noteName).join(' · ');return;
  }
  practiceHits.add(n);
  if(step.notes.every(v=>practiceHits.has(v))){
    practiceIndex++;practiceHits.clear();beat=practiceSteps[practiceIndex]?.beat??score.totalBeats;lastActive='';lastSystem=-1;
    if(practiceIndex===practiceSteps.length)practiceRunning=false;
    updateTransport();render();if(practiceRunning)followPosition();
  }else renderPractice();
}
const inputVoices=new Map(),inputTokens=new Map(),midiPedals=new Set(),pedalVoices=new Map();
function inputDown(n,source,velocity=1){
  if(!playable()||n<21||n>108||heldInputs.has(source))return;
  heldInputs.set(source,n);const key=keys.get(n);key?.classList.add('manual');
  const generation=loadGeneration,mode=practiceMode,token={};inputTokens.set(source,token);practicePress(n);
  audioReady().then(()=>{if(generation===loadGeneration&&mode===practiceMode&&heldInputs.has(source)&&inputTokens.get(source)===token)inputVoices.set(source,pianoTone(n,ctx.currentTime,Infinity,mode==='L'?'L':'R',velocity));}).catch(e=>showError(e.message));
}
function inputUp(source){
  const n=heldInputs.get(source),voice=inputVoices.get(source),channel=source.slice(0,source.lastIndexOf(':'));heldInputs.delete(source);inputTokens.delete(source);inputVoices.delete(source);
  if(voice){if(source.startsWith('midi:')&&midiPedals.has(channel)){if(!pedalVoices.has(channel))pedalVoices.set(channel,new Set());pedalVoices.get(channel).add(voice);}else voice.release();}
  if(![...heldInputs.values()].includes(n))keys.get(n)?.classList.remove('manual');
}
function clearInputs(){for(const source of [...heldInputs.keys()])inputUp(source);}
function changePracticeMode(mode){
  pause();clearInputs();practiceMode=mode;buildPractice();if(practicing()&&playable())locatePractice();
  $('tempo').disabled=practicing()||!playable();lastActive='';updateTransport();render();renderPractice();if(playable())followPosition();
}
$('practiceMode').addEventListener('change',e=>changePracticeMode(e.target.value));
const keyboardMap={KeyA:0,KeyW:1,KeyS:2,KeyE:3,KeyD:4,KeyF:5,KeyT:6,KeyG:7,KeyY:8,KeyH:9,KeyU:10,KeyJ:11,KeyK:12};
window.addEventListener('keydown',e=>{
  if(!practicing()||!playable()||e.ctrlKey||e.altKey||e.metaKey||e.isComposing||/INPUT|TEXTAREA|SELECT/.test(e.target.tagName)||e.target.isContentEditable)return;
  if(e.code==='KeyZ'||e.code==='KeyX'){e.preventDefault();if(!e.repeat)$('inputOctave').value=clamp(Number($('inputOctave').value)+(e.code==='KeyX'?1:-1),0,7);return;}
  if(keyboardMap[e.code]!=null){e.preventDefault();if(!e.repeat)inputDown((Number($('inputOctave').value)+1)*12+keyboardMap[e.code],'computer:'+e.code);}
});
window.addEventListener('keyup',e=>inputUp('computer:'+e.code));
window.addEventListener('pointerup',e=>inputUp('pointer:'+e.pointerId));
window.addEventListener('pointercancel',e=>inputUp('pointer:'+e.pointerId));
let midiAccess=null;const midiInputs=new Map();
function midiMessage(id,event){
  const [status,n,velocity]=event.data,type=status&240,channel=`midi:${id}:${status&15}`,source=channel+':'+n;
  if(type===144&&velocity>0)inputDown(n,source,.2+velocity/127);
  else if(type===128||(type===144&&velocity===0))inputUp(source);
  else if(type===176&&n===64){if(velocity>=64)midiPedals.add(channel);else{midiPedals.delete(channel);for(const voice of pedalVoices.get(channel)||[])voice.release();pedalVoices.delete(channel);}}
}
function refreshMidi(){
  for(const [id,input] of midiInputs)if(!midiAccess.inputs.has(id)||input.state==='disconnected'){
    input.onmidimessage=null;midiInputs.delete(id);for(const channel of [...midiPedals])if(channel.startsWith('midi:'+id+':')){midiPedals.delete(channel);for(const voice of pedalVoices.get(channel)||[])voice.release();pedalVoices.delete(channel);}
    for(const source of [...heldInputs.keys()])if(source.startsWith('midi:'+id+':'))inputUp(source);
  }
  for(const input of midiAccess.inputs.values())if(input.state!=='disconnected'){input.onmidimessage=e=>midiMessage(input.id,e);midiInputs.set(input.id,input);}
  $('midiStatus').textContent=midiInputs.size?'已连接：'+[...midiInputs.values()].map(i=>i.name||'MIDI 键盘').join('、'):'未检测到键盘，请连接后重试';
}
$('connectMidi').onclick=async()=>{
  if(!navigator.requestMIDIAccess){$('midiStatus').textContent='此浏览器不支持 MIDI，请用 Chrome / Edge，或点击屏幕琴键。';return;}
  $('connectMidi').disabled=true;
  try{await audioReady();midiAccess=await navigator.requestMIDIAccess({sysex:false});midiAccess.onstatechange=refreshMidi;refreshMidi();}
  catch(e){$('midiStatus').textContent='未能连接 MIDI，请检查浏览器授权和设备；仍可使用屏幕琴键。';}
  finally{$('connectMidi').disabled=false;}
};

function showError(message){$('error').textContent=message;$('error').hidden=false;}
async function audioReady(){
  if(!ctx){
    const Audio=window.AudioContext||window.webkitAudioContext;
    if(!Audio)throw new Error('当前浏览器不支持音频播放，请使用 Chrome、Edge 或 Safari。');
    ctx=new Audio();master=ctx.createGain();master.gain.value=Number($('volume').value)/100*.85;
    limiter=ctx.createDynamicsCompressor();limiter.threshold.value=-9;limiter.knee.value=8;limiter.ratio.value=5;
    master.connect(limiter);limiter.connect(ctx.destination);
    piano=new SamplePiano(ctx,master,message=>{$('toneStatus').textContent=message;});voices=piano.voices;
  }
  await ctx.resume();await piano.ready();
}
function pianoTone(midi,when,duration,hand='R',velocity=1){return piano.play(midi,when,duration,hand,velocity);}
function silence(){if(piano)piano.silence();inputVoices.clear();pedalVoices.clear();midiPedals.clear();}
function beatSeconds(b){
  const map=score?.tempoMap||[{beat:0,factor:1}];let seconds=0;
  for(let i=0;i<map.length;i++){const a=map[i],end=Math.min(b,map[i+1]?.beat??b);if(end>a.beat)seconds+=(end-a.beat)*60/(tempo*a.factor);if(end>=b)break;}return seconds;
}
function secondsBeat(seconds){
  const map=score?.tempoMap||[{beat:0,factor:1}];
  for(let i=0;i<map.length;i++){const a=map[i],end=map[i+1]?.beat??score.totalBeats,span=(end-a.beat)*60/(tempo*a.factor);if(seconds<=span)return a.beat+seconds*tempo*a.factor/60;seconds-=span;}return score.totalBeats;
}
function currentBeat(){return playing?clamp(secondsBeat(beatSeconds(anchorBeat)+ctx.currentTime-anchorTime),anchorBeat,score.totalBeats):beat;}
function schedule(){
  if(!playing)return;
  const b=currentBeat(),end=b+tempo/60*.18;
  while(queueIndex<soundEvents.length&&soundEvents[queueIndex].beat<end){
    const e=soundEvents[queueIndex++];
    if(e.beat+(e.pedalDuration||e.soundDuration)<=anchorBeat)continue;
    const start=Math.max(e.beat,anchorBeat),when=Math.max(ctx.currentTime,anchorTime+beatSeconds(start)-beatSeconds(anchorBeat));
    pianoTone(e.midi,when,beatSeconds(e.beat+(e.pedalDuration||e.soundDuration))-beatSeconds(start),e.hand,e.velocity||1);
  }
}
async function start(){
  if(!playable()||running()||starting)return;
  starting=true;const myStart=++startGeneration;const myLoad=loadGeneration;
  try{await audioReady();$('error').hidden=true;}catch(e){showError(e.message);starting=false;return;}starting=false;if(myStart!==startGeneration||myLoad!==loadGeneration||!playable())return;
  if(practicing()){if(beat>=score.totalBeats)beat=0;locatePractice();practiceRunning=practiceIndex<practiceSteps.length;updateTransport();render();followPosition();return;}
  if(beat>=score.totalBeats-.001)beat=0;
  anchorBeat=beat;anchorTime=ctx.currentTime+.025;playing=true;queueIndex=0;
  while(queueIndex<soundEvents.length&&soundEvents[queueIndex].beat+(soundEvents[queueIndex].pedalDuration||soundEvents[queueIndex].soundDuration)<=beat)queueIndex++;
  // Include sustained notes when resuming in the middle of a tie.
  lastSystem=-1;schedule();timer=setInterval(schedule,25);updateTransport();
}
function pause(){startGeneration++;starting=false;if(playing)beat=currentBeat();playing=false;practiceRunning=false;clearInputs();practiceHits.clear();clearInterval(timer);timer=null;silence();updateTransport();render();}
function toggle(){if(running())pause();else start();}
function seek(value,follow=false){
  if(!playable())return;
  const resume=running();pause();beat=clamp(value,0,score.totalBeats);if(practicing())locatePractice();lastActive='';lastSystem=-1;updateTransport();render();
  if(follow)followPosition(true);if(resume)start();
}
function updateTransport(){
  if(!playable()){$('playIcon').textContent='♪';$('playText').textContent=score?'仅阅谱':'加载琴谱';$('play').setAttribute('aria-pressed','false');$('liveDot').classList.remove('on');$('status').textContent='仅阅谱';return;}
  if(practicing()){
    $('playIcon').textContent=practiceRunning?'Ⅱ':'▶';$('playText').textContent=practiceRunning?'暂停练习':'开始练习';$('play').setAttribute('aria-label',$('playText').textContent);$('play').setAttribute('aria-pressed',String(practiceRunning));$('liveDot').classList.toggle('on',practiceRunning);$('status').textContent=practiceRunning?'等待按键':beat>=score.totalBeats?'练习完成':'练习已暂停';return;
  }
  $('playIcon').textContent=playing?'Ⅱ':'▶';$('playText').textContent=playing?'暂停播放':'开始播放';
  $('play').setAttribute('aria-label',playing?'暂停播放':'开始播放');$('play').setAttribute('aria-pressed',String(playing));
  $('liveDot').classList.toggle('on',playing);$('status').textContent=playing?'正在播放':beat>=score.totalBeats?'播放结束':beat>0?'已暂停':'准备播放';
}
function svgNode(tag,attrs){const n=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);return n;}
function makeScore(){
  $('scorePages').replaceChildren();
  for(let p=0;p<score.pages;p++){
    const el=document.createElement('div');el.className='sheet';el.dataset.page=p;
    const img=document.createElement('img');img.src=`${songBase}page-${p+1}.png`;img.alt=`${score.title}原谱第 ${p+1} 页`;img.width=pageSize(p).width;img.height=pageSize(p).height;img.draggable=false;
    const svg=svgNode('svg',{viewBox:`0 0 ${pageSize(p).width} ${pageSize(p).height}`,'aria-label':`第 ${p+1} 页，点击或拖动以定位播放`});
    const notes=svgNode('g',{}),pointer=svgNode('g',{'aria-hidden':'true'});
    pointer.append(svgNode('rect',{class:'pointer-halo',x:-5,y:0,width:10,height:100}),svgNode('line',{class:'pointer-line',x1:0,x2:0,y1:0,y2:100}),svgNode('path',{d:'M -4 -6 L 4 -6 L 4 -2 L 0 2 L -4 -2 Z',fill:'#327d58'}),svgNode('rect',{class:'playhead-hit',x:-11,y:-10,width:22,height:115,fill:'transparent'}));
    svg.append(notes,pointer);el.append(img,svg);$('scorePages').append(el);pageEls.push(el);overlays.push(svg);pointers.push(pointer);noteLayers.push(notes);
    svg.addEventListener('pointerdown',pointerDown);
    const nav=document.createElement('button');nav.textContent=p+1;nav.setAttribute('aria-label',`跳到第 ${p+1} 页`);nav.onclick=()=>{if(playable())seek(score.systems.find(s=>s.page===p).start,true);else scrollPage(p);};$('pageNav').append(nav);
  }
}
let drag=null;
function locationBeat(clientX,clientY){
  let p=0,best=Infinity;
  pageEls.forEach((el,i)=>{const r=el.getBoundingClientRect(),d=Math.max(r.top-clientY,clientY-r.bottom,0);if(d<best){best=d;p=i;}});
  const r=pageEls[p].getBoundingClientRect(),x=(clientX-r.left)/r.width*pageSize(p).width,y=(clientY-r.top)/r.height*pageSize(p).height;
  const system=score.systems.filter(s=>s.page===p).reduce((a,b)=>Math.abs((a.top+a.bottom)/2-y)<Math.abs((b.top+b.bottom)/2-y)?a:b);
  const ms=system.measures.map(i=>score.measures[i]);const m=ms.find(m=>x<=m.right)||ms[ms.length-1];const anchors=m.anchors;
  if(x<=anchors[0][1])return anchors[0][0];
  for(let i=1;i<anchors.length;i++)if(x<=anchors[i][1]){const a=anchors[i-1],b=anchors[i];return a[0]+clamp((x-a[1])/(b[1]-a[1]),0,1)*(b[0]-a[0]);}
  return Math.min(m.start+m.duration-.001,score.totalBeats);
}
function pointerDown(e){
  if(e.button!==0||!playable())return;
  const direct=e.pointerType==='mouse'||e.target.classList.contains('playhead-hit');
  drag={id:e.pointerId,x:e.clientX,y:e.clientY,direct,resume:running(),el:e.currentTarget,moved:false};
  if(direct){e.preventDefault();e.currentTarget.setPointerCapture(e.pointerId);pause();seek(locationBeat(e.clientX,e.clientY));}
}
window.addEventListener('pointermove',e=>{
  if(!drag||e.pointerId!==drag.id)return;
  if(Math.hypot(e.clientX-drag.x,e.clientY-drag.y)>7)drag.moved=true;
  if(drag.direct){e.preventDefault();seek(locationBeat(e.clientX,e.clientY));}
},{passive:false});
window.addEventListener('pointerup',e=>{
  if(!drag||e.pointerId!==drag.id)return;const d=drag;drag=null;
  if(d.direct){seek(locationBeat(e.clientX,e.clientY));if(d.resume)start();}
  else if(!d.moved)seek(locationBeat(e.clientX,e.clientY));
});
window.addEventListener('pointercancel',()=>{if(drag?.direct&&drag.resume)start();drag=null;});
function makeKeyboard(){
  const min=Math.min(...score.events.map(e=>e.midi)),max=Math.max(...score.events.map(e=>e.midi));
  const low=Math.max(21,Math.floor(min/12)*12),high=Math.min(108,Math.ceil((max+1)/12)*12);
  document.querySelector('.range-label').textContent=noteName(low)+'–'+noteName(high)+' · 中央 C = C4';
  const whites=[];for(let n=low;n<=high;n++)if(!names[n%12].includes('♯'))whites.push(n);
  $('keyboard').style.minWidth=(whites.length*29)+'px';
  let whiteIndex=-1;
  for(let n=low;n<=high;n++){
    const black=names[n%12].includes('♯');if(!black)whiteIndex++;
    const key=document.createElement('button');key.className='key'+(black?' black':'')+(n===60?' middle-c':'');key.dataset.midi=n;
    key.style.left=((black?whiteIndex+.68:whiteIndex)/whites.length*100)+'%';key.style.width=((black?.64:1)/whites.length*100)+'%';
    key.innerHTML=black?`<span>${names[n%12]}</span><span class="octave">${Math.floor(n/12)-1}</span>`:`<span>${noteName(n)}</span>`;
    key.setAttribute('aria-label',noteName(n));key.title=noteName(n)+(n===60?' · 中央 C':'');
    key.addEventListener('pointerdown',e=>{e.preventDefault();key.setPointerCapture(e.pointerId);inputDown(n,'pointer:'+e.pointerId);});
    key.addEventListener('click',e=>{if(e.detail===0){inputDown(n,'accessible:'+n);setTimeout(()=>inputUp('accessible:'+n),180);}});
    const badge=document.createElement('span');badge.className='finger-badge';badge.hidden=true;key.append(badge);fingerBadges.set(n,badge);
    $('keyboard').append(key);keys.set(n,key);
  }
}
function cursorPosition(b){
  const m=(score.measures.find(m=>b>=m.start&&b<m.start+m.duration)||score.measures[score.measures.length-1]),s=score.systems[m.system],a=m.anchors;
  let x=a[0][1];for(let i=1;i<a.length;i++){if(b<=a[i][0]){const f=clamp((b-a[i-1][0])/(a[i][0]-a[i-1][0]),0,1);x=a[i-1][1]+f*(a[i][1]-a[i-1][1]);break;}x=a[i][1];}
  return {m,s,x};
}
function followPosition(force=false){
  if(!playable())return;
  const {s,x}=cursorPosition(currentBeat());if(!force&&!$('follow').checked)return;
  const viewport=$('scoreViewport'),el=pageEls[s.page],r=el.getBoundingClientRect(),vr=viewport.getBoundingClientRect(),scale=r.width/pageSize(s.page).width;
  const top=r.top-vr.top+viewport.scrollTop+s.top*scale;
  viewport.scrollTo({top:Math.max(0,top-28),left:clamp(r.left-vr.left+viewport.scrollLeft+x*scale-vr.width*.45,0,viewport.scrollWidth-vr.width),behavior:'instant'});
}
function render(){
  if(!playable())return;
  const b=currentBeat(),{m,s,x}=cursorPosition(b);
  $('progress').value=b;$('elapsed').textContent=timeString(beatSeconds(b));$('total').textContent=timeString(beatSeconds(score.totalBeats));$('measure').textContent=m.displayNumber||m.index+1;
  if($('beatDots').children.length!==Math.ceil(m.duration)){$('beatDots').replaceChildren(...Array.from({length:Math.ceil(m.duration)},()=>document.createElement('i')));}
  [...$('beatDots').children].forEach((d,i)=>d.classList.toggle('on',i===Math.floor(b-m.start)));
  [...$('pageNav').children].forEach((n,i)=>{n.classList.toggle('active',i===s.page);n.setAttribute('aria-current',i===s.page?'page':'false');});
  pointers.forEach((p,i)=>p.style.display=i===s.page?'':'none');
  const pointer=pointers[s.page],height=s.bottom-s.top;pointer.setAttribute('transform',`translate(${x} ${s.top})`);
  pointer.children[0].setAttribute('height',height);pointer.children[1].setAttribute('y2',height);pointer.children[3].setAttribute('height',height+20);
  // Keep the exact score segment highlighted even during a tied sustain.
  const active=practicing()?(practiceSteps[practiceIndex]?.events||[]):b<score.totalBeats?score.events.filter(e=>e.beat<=b+.00001&&e.beat+e.duration>b+.00001):[];
  const signature=practiceMode+':'+active.map(e=>e.id).join(',');
  if(signature!==lastActive){
    lastActive=signature;for(const k of keys.values())k.classList.remove('active-R','active-L','active-both');noteLayers.forEach(n=>n.replaceChildren());
    const rh=new Set(),lh=new Set();
    for(const e of active){(e.hand==='R'?rh:lh).add(e.midi);const k=keys.get(e.midi);if(k)k.classList.add('active-'+e.hand);noteLayers[e.page].append(svgNode('ellipse',{cx:e.x,cy:e.y,rx:4.4,ry:3.8,class:'active-note '+e.hand}));}
    for(const n of rh)if(lh.has(n))keys.get(n)?.classList.add('active-both');
    $('rightNotes').textContent=[...rh].sort((a,b)=>a-b).map(noteName).join('  ·  ')||'—';$('leftNotes').textContent=[...lh].sort((a,b)=>a-b).map(noteName).join('  ·  ')||'—';
    if(running()&&active.length){const board=$('keyboardScroll'),key=keys.get(active.find(e=>e.hand==='R')?.midi||active[0].midi);if(key){const kr=key.getBoundingClientRect(),br=board.getBoundingClientRect();if(kr.left<br.left+12||kr.right>br.right-12)board.scrollLeft+=kr.left-br.left-br.width*.6;}}
  }
  renderFingers(active);renderPractice();
  if(running()&&s.index!==lastSystem&&!drag){lastSystem=s.index;followPosition();}
}
function tick(){if(playing){render();if(currentBeat()>=score.totalBeats){pause();beat=score.totalBeats;updateTransport();render();}}requestAnimationFrame(tick);}
$('play').onclick=toggle;$('reset').onclick=()=>seek(0,true);
$('tempo').addEventListener('change',()=>{const resume=playing;pause();tempo=clamp(Number($('tempo').value)||140,40,220);$('tempo').value=tempo;render();if(resume)start();});
$('volume').oninput=()=>{if(master)master.gain.setTargetAtTime(Number($('volume').value)/100*.85,ctx.currentTime,.03);};
$('follow').onchange=()=>{if($('follow').checked)followPosition(true);};
$('progress').addEventListener('pointerdown',()=>{if(!score)return;scrubbing=true;wasPlaying=running();pause();});
$('progress').addEventListener('input',e=>{if(score)seek(Number(e.target.value),true);});
function endScrub(){if(scrubbing){scrubbing=false;if(wasPlaying)start();}}
window.addEventListener('pointerup',endScrub);window.addEventListener('pointercancel',endScrub);
window.addEventListener('keydown',e=>{if(!playable()||/INPUT|TEXTAREA|SELECT|BUTTON/.test(e.target.tagName))return;if(e.code==='Space'){e.preventDefault();toggle();}else if(e.code==='ArrowRight'){e.preventDefault();seek(currentBeat()+.5,true);}else if(e.code==='ArrowLeft'){e.preventDefault();seek(currentBeat()-.5,true);}});
window.addEventListener('blur',()=>{clearInputs();if(running())pause();});

function scrollPage(page){
  const viewport=$('scoreViewport'),r=pageEls[page].getBoundingClientRect(),vr=viewport.getBoundingClientRect();
  viewport.scrollTo({top:viewport.scrollTop+r.top-vr.top-12,left:0,behavior:'instant'});markPage(page);
}
function markPage(page){[...$('pageNav').children].forEach((n,i)=>{n.classList.toggle('active',i===page);n.setAttribute('aria-current',i===page?'page':'false');});}
$('scoreViewport').addEventListener('scroll',()=>{if(!score||playable())return;const y=$('scoreViewport').getBoundingClientRect().top+40;let best=0;pageEls.forEach((el,i)=>{if(el.getBoundingClientRect().top<=y)best=i;});markPage(best);},{passive:true});
async function loadSong(id){
  const entry=songs.find(s=>s.id===id);if(!entry)return;
  const generation=++loadGeneration;pause();drag=null;scrubbing=false;wasPlaying=false;score=null;practiceSteps=[];practiceIndex=0;renderPractice();beat=0;lastActive='';lastSystem=-1;soundEvents=[];
  pageEls.length=0;overlays.length=0;pointers.length=0;noteLayers.length=0;keys.clear();fingerBadges.clear();fingerMap.clear();lastFingers="";$('fingerAdvice').textContent='';
  $('pageNav').replaceChildren();$('keyboard').replaceChildren();$('scorePages').textContent='正在加载琴谱…';
  $('scoreNotice').hidden=true;$('error').hidden=true;
  for(const id of ['play','reset','tempo','volume','follow','progress','practiceMode'])$(id).disabled=true;
  $('playText').textContent='加载琴谱';$('progress').value=0;$('elapsed').textContent='0:00';$('total').textContent='—';
  try{
    const response=await fetch(entry.url);if(!response.ok)throw new Error('琴谱加载失败，请重新选择曲目重试。');
    const data=await response.json();if(generation!==loadGeneration)return;
    score=data;songBase=entry.base;tempo=score.bpm||140;document.querySelector('.app').classList.toggle('view-only',!playable());
    $('songTitle').textContent=score.title;$('credit').textContent=score.credit||'';document.title=score.title+' · 钢琴谱集';
    $('keyLabel').textContent=score.keyLabel||'';$('meterLabel').textContent=score.meterLabel||'';$('measureTotal').textContent=score.pages+' 页';
    makeScore();$('scoreViewport').scrollTo({top:0,left:0});markPage(0);
    if(playable()){
      $('tempo').value=tempo;$('measureCount').textContent=' / '+(score.measures.at(-1).displayNumber||score.measures.length)+' 小节';
      if(score.performanceNote){$('scoreNotice').textContent=score.performanceNote;$('scoreNotice').hidden=false;}
      fingerMap=new Map([...Fingering.recommend(score.events,'R'),...Fingering.recommend(score.events,'L')]);
      soundEvents=score.events.filter(e=>e.soundDuration).sort((a,b)=>a.beat-b.beat);makeKeyboard();
      for(const id of ['play','reset','tempo','volume','follow','progress','practiceMode'])$(id).disabled=false;
      buildPractice();if(practicing())locatePractice();$('tempo').disabled=practicing();
      $('progress').max=score.totalBeats;updateTransport();render();
      const first=pageEls[0].querySelector('img');const follow=()=>{if(generation===loadGeneration)followPosition(true);};
      first.addEventListener('load',follow,{once:true});if(first.complete)follow();
    }else{
      $('tempo').value=score.bpm||'';$('measure').textContent='—';$('measureCount').textContent=' / '+score.pages+' 页';$('beatDots').replaceChildren();
      $('scoreNotice').textContent=score.status;$('scoreNotice').hidden=false;updateTransport();
    }
    history.replaceState(null,'','#'+entry.id);
  }catch(e){if(generation!==loadGeneration)return;score=null;$('scorePages').textContent='加载失败，可重新选择曲目重试。';showError(e.message);}
}
$('songSelect').addEventListener('change',e=>loadSong(e.target.value));
fetch('songs.json').then(r=>{if(!r.ok)throw new Error('曲谱目录加载失败，请刷新。');return r.json();}).then(catalog=>{
  songs=catalog;$('songSelect').replaceChildren();
  for(const song of songs){const o=document.createElement('option');o.value=song.id;o.textContent=song.title+(song.playable?' · 可播放':' · 仅阅谱');$('songSelect').append(o);}
  const selected=songs.find(s=>s.id===location.hash.slice(1))?.id||songs[0].id;$('songSelect').value=selected;loadSong(selected);requestAnimationFrame(tick);
}).catch(e=>showError(e.message));
