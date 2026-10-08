// Local DOM/audio contract checks; no server, browser, or MIDI hardware needed.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'..');
class Element {
  constructor(tag='div') {
    this.tag=tag;this.children=[];this.style={};this.dataset={};this.listeners={};
    this.value='';this.hidden=false;this.checked=true;this.complete=true;
    this.scrollTop=0;this.scrollLeft=0;this.scrollWidth=3000;
    this.classes=new Set();this.classList={add:(...cs)=>cs.forEach(c=>this.classes.add(c)),remove:(...cs)=>cs.forEach(c=>this.classes.delete(c)),contains:c=>this.classes.has(c),toggle:(c,on)=>on?this.classes.add(c):this.classes.delete(c)};
  }
  append(...nodes){this.children.push(...nodes)}
  replaceChildren(...nodes){this.children=nodes}
  setAttribute(k,v){this[k]=v}
  removeAttribute(k){delete this[k]}
  addEventListener(k,v){this.listeners[k]=v}
  querySelector(tag){return this.children.find(c=>c.tag===tag)||new Element(tag)}
  getBoundingClientRect(){return {top:0,left:0,right:600,bottom:900,width:600,height:900}}
  scrollTo(v){Object.assign(this,{scrollTop:v.top||0,scrollLeft:v.left||0})}
}
const nodes=new Map(),get=id=>{if(!nodes.has(id))nodes.set(id,new Element());return nodes.get(id)};
get('volume').value=65;
const param=()=>({value:0,setTargetAtTime(){}});
class AudioContext {
  constructor(){this.currentTime=0;this.destination={}}
  resume(){return Promise.resolve()}
  createGain(){return {gain:param(),connect(){}}}
  createDynamicsCompressor(){return {threshold:param(),knee:param(),ratio:param(),connect(){}}}
}
class SamplePiano {
  constructor(){this.voices=new Set();this.calls=[]}
  ready(){return Promise.resolve()}
  play(...args){this.calls.push(args);const v={release:()=>this.voices.delete(v)};this.voices.add(v);return v}
  silence(){this.voices.clear()}
}
const sandbox={console,navigator:{},SamplePiano,AbortController,document:{getElementById:get,querySelector:get,createElement:t=>new Element(t),createElementNS:(_,t)=>new Element(t)},window:{AudioContext,addEventListener(){}},location:{hash:'',protocol:'http:'},history:{replaceState(){}},fetch:async u=>({ok:true,json:async()=>JSON.parse(fs.readFileSync(path.join(root,u),'utf8'))}),setInterval:()=>1,clearInterval(){},setTimeout,clearTimeout,requestAnimationFrame(){}};
vm.createContext(sandbox);
for(const name of ['fingering.js','performance.js','app.js'])vm.runInContext(fs.readFileSync(path.join(root,name),'utf8'),sandbox);
const run=code=>vm.runInContext(code,sandbox);
(async()=>{
  await new Promise(resolve=>setImmediate(resolve));
  const songs=JSON.parse(fs.readFileSync(path.join(root,'songs.json'),'utf8'));
  assert.equal(songs.length,51);assert.equal(new Set(songs.map(s=>s.id)).size,51);
  const original=songs.filter(s=>s.playable),added=songs.filter(s=>s.collection);
  assert(original.length>=4);assert.equal(added.length,47);assert.equal(added.filter(s=>s.collection==='pianogen3-final').length,21);
  assert.equal(added.filter(s=>s.collection==='puzi').length,25);
  assert(added.some(s=>s.id==='jane-doe'&&s.collection==='add2'));
  await run("changePracticeMode('both');start()");
  assert(run('practiceRunning'));
  for(const song of added){
    await run(`loadSong(${JSON.stringify(song.id)})`);
    const data=JSON.parse(fs.readFileSync(path.join(root,song.url),'utf8'));
    if(!song.playable){
    assert.equal(data.mode,'view');assert.equal(data.events.length,0);
    assert(!run('playable()||playing||practiceRunning'));
    assert(get('play').disabled&&get('practiceMode').disabled&&get('practicePanel').hidden);
    assert(get('.app').classes.has('view-only'));assert(!get('.app').classes.has('practicing'));
    }
    assert.equal(get('pageNav').children.length,data.pages);
    assert.equal(get('scorePages').children.length,data.pages);
    assert.equal(get('originalPdf').href,song.pdf);assert(!get('originalPdf').hidden);
    assert(fs.readFileSync(path.join(root,song.pdf)).subarray(0,5).equals(Buffer.from('%PDF-')));
    for(let p=0;p<data.pages;p++){
      const png=fs.readFileSync(path.join(root,song.base,`page-${p+1}.png`));
      assert(png.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])));
      assert(Math.abs(png.readUInt32BE(16)-data.pageSizes[p].width*2)<2);
      assert(Math.abs(png.readUInt32BE(20)-data.pageSizes[p].height*2)<2);
    }
    get('pageNav').children.at(-1).onclick();
    assert.equal(get('pageNav').children.at(-1)['aria-current'],'page');
    if(!song.playable){await run('start()');assert(!run('playing||practiceRunning'));}
    if(song.id==='interstellar'&&song.playable){
      get('pageNav').children[0].onclick();assert.equal(get('pageNav').children[0]['aria-current'],'page');
      assert(Number.isFinite(run('locationBeat(100,100)')));
    }
    if(song.id==='your-name-date'){
      // Clicking a repeated PDF passage must keep its current occurrence.
      run(`for(const m of score.measures.filter(m=>m.sourceMeasure===5||m.sourceMeasure===11)){
        seek(m.start+.1);
        const sy=score.systems[m.system],size=pageSize(0);
        const selected=locationBeat(m.anchors[0][1]/size.width*600,(sy.top+sy.bottom)/2/size.height*900);
        if(Math.abs(selected-m.start)>1e-6)throw Error('Repeat seek selected another occurrence');
      }`);
    }
    if(song.transcriptionStatus==='unreviewed-draft'){
      assert(!get('scoreNotice').hidden);assert.match(get('scoreNotice').textContent,/未校对/);
      assert(get('songSelect').children.some(o=>o.value===song.id&&o.textContent.includes('识别草稿')));
    }
  }
  for(const song of original){
    await run(`loadSong(${JSON.stringify(song.id)})`);
    assert(run('playable()'));assert(!get('play').disabled);
    assert.equal(get('originalPdf').hidden,!song.pdf);assert(!get('.app').classes.has('view-only'));
    await run("changePracticeMode('play');seek(soundEvents[0].beat);start()");assert(run('playing&&voices.size>0'));
    if(song.id==='young-and-beautiful'){
      const notes=run('JSON.stringify(score.events)');
      run('piano.calls=[];ctx.currentTime=anchorTime+beatSeconds(12)+.01;schedule()');
      assert(run('piano.calls.length<=soundEvents.filter(e=>e.beat<secondsBeat(beatSeconds(currentBeat())+.18)&&anchorTime+beatSeconds(e.beat+e.pedalDuration)-beatSeconds(anchorBeat)+(e.legatoSeconds||0)>ctx.currentTime).length'),'A delayed scheduler must not burst expired notes');
      run('finishPlayback()');assert(run('!playing&&beat===score.totalBeats&&voices.size>0'),'Natural ending must keep the release tail');
      run('pause()');assert(run('voices.size===0'));
      // Seek into an existing long bass note: resume the decayed sample,
      // rather than hammering every held note again at the seek position.
      run('piano.calls=[];seek(2)');await run('start()');
      assert(run('piano.calls.some(c=>c[5].offset>1)'));
      run('pause()');
      assert.equal(run('JSON.stringify(score.events)'),notes);
    }
    run('pause()');assert(run('!playing&&voices.size===0'));
    for(const mode of ['L','R','both']){
      await run(`changePracticeMode('${mode}');seek(0);start()`);
      assert(run('practiceRunning'));assert(!get('practicePanel').hidden);
      run('practiceSteps[0].notes.forEach(n=>{midiMessage("test",{data:[144,n,90]});midiMessage("test",{data:[128,n,0]});})');
      assert.equal(run('practiceIndex'),1);
      run('pause()');
    }
    if(song.transcriptionStatus){
      run('for(let b=0;b<score.totalBeats;b+=.25){seek(b);if(Math.abs(secondsBeat(beatSeconds(b))-b)>1e-6)throw Error("Clock mismatch");}');
      for(const mode of ['L','R','both']){
        await run(`changePracticeMode('${mode}');seek(0);start()`);
        run('while(practiceRunning){const step=practiceSteps[practiceIndex];for(const n of step.notes){midiMessage("whole-song",{data:[144,n,90]});midiMessage("whole-song",{data:[128,n,0]});}}');
        assert(run('beat===score.totalBeats&&practiceIndex===practiceSteps.length'));
        assert(run('heldInputs.size===0'));
      }
    }
  }
  await run("Promise.all([loadSong('flower-dance'),loadSong('feng')])");
  assert.equal(get('songTitle').textContent,'枫');assert(run('playable()'));
  assert(get('error').hidden);
  sandbox.fetch=async()=>({ok:false,status:404});
  await assert.rejects(run("loadJSON('songs.json')"),/HTTP 404/);
  sandbox.fetch=async()=>({ok:true,json:async()=>{throw new SyntaxError('Unexpected token <')}});
  await assert.rejects(run("loadJSON('songs.json')"),/不是有效曲谱数据/);
  sandbox.location.protocol='file:';
  await assert.rejects(run("loadJSON('songs.json')"),/不能直接双击 HTML/);
  sandbox.location.protocol='http:';
  sandbox.setTimeout=fn=>setImmediate(fn);sandbox.clearTimeout=clearImmediate;
  sandbox.fetch=(_,options)=>new Promise((resolve,reject)=>options.signal.addEventListener('abort',()=>reject(Object.assign(new Error('Aborted'),{name:'AbortError'}))));
  await assert.rejects(run("loadJSON('songs.json')"),/超时/);
  const startup=fs.readFileSync(path.join(root,'index.html'),'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
  const handlers={},notice={hidden:true},location={protocol:'http:'};let timeout;
  const context={window:{addEventListener:(name,fn)=>handlers[name]=fn},document:{getElementById:()=>notice,addEventListener:(name,fn)=>handlers[name]=fn},location,setTimeout:fn=>{timeout=fn;return 1},clearTimeout:()=>{timeout=null}};
  vm.runInNewContext(startup,context);
  handlers.error({target:{tagName:'SCRIPT'}});assert.match(notice.textContent,/脚本加载失败/);assert(!notice.hidden);
  location.protocol='file:';handlers.DOMContentLoaded();assert.match(notice.textContent,/直接打开了 HTML/);
  console.log('PASS: missing/invalid JSON, file URLs, request timeout, and independent startup error messages.');
  console.log(`PASS: ${songs.length} entries, all imported pages/PDFs, view/play transitions, playback and simulated MIDI practice for ${original.length} playable songs; complete practice traversal for new transcriptions.`);
})().catch(error=>{console.error(error);process.exitCode=1});
