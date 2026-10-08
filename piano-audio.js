'use strict';
class SamplePiano {
  constructor(ctx,output,onStatus=()=>{}){
    this.ctx=ctx;this.output=output;this.status=onStatus;this.buffers=new Map();this.voices=new Set();this.loading=null;
    this.dry=ctx.createGain();this.dry.gain.value=.88;this.dry.connect(output);
    this.wet=ctx.createGain();this.wet.gain.value=.13;this.wet.connect(output);this.makeRoom();
  }
  makeRoom(){
    const ctx=this.ctx;let ir=this.impulse;
    if(!ir){ir=ctx.createBuffer(2,Math.floor(ctx.sampleRate*1.35),ctx.sampleRate);let seed=4137;
    for(let c=0;c<2;c++){const data=ir.getChannelData(c);for(let i=0;i<data.length;i++){seed=(seed*1664525+1013904223)>>>0;const t=i/ctx.sampleRate;data[i]=(seed/4294967296*2-1)*Math.exp(-t*5.5)*.12*Math.min(1,t/.03);}for(const [t,a] of [[.019,.12],[.037,.08],[.061,.045]])data[Math.floor((t+c*.0017)*ctx.sampleRate)]+=a;}
    this.impulse=ir;}
    this.room=ctx.createConvolver();this.room.buffer=ir;this.room.connect(this.wet);
  }
  async ready(){
    if(this.buffers.size===30)return;
    if(this.loading)return this.loading;
    this.loading=(async()=>{
      const manifest=await this.fetch('audio/piano/manifest.json').then(r=>r.json());let next=0;
      const worker=async()=>{while(next<manifest.length){const s=manifest[next++];if(!this.buffers.has(s.midi)){const bytes=await this.fetch('audio/piano/'+s.file).then(r=>r.arrayBuffer());const buffer=await this.ctx.decodeAudioData(bytes);this.buffers.set(s.midi,buffer);}this.status(`正在加载钢琴音色 ${this.buffers.size}/${manifest.length}`);}};
      await Promise.all(Array.from({length:5},worker));this.status('真实钢琴采样 · 已就绪');
    })().catch(e=>{this.status('钢琴音色加载失败，请点击播放重试');throw new Error('钢琴音色未加载完成，请检查网络后重试。');}).finally(()=>{this.loading=null;});
    return this.loading;
  }
  async fetch(url){const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),20000);try{const r=await fetch(url,{signal:controller.signal});if(!r.ok)throw Error('Sample unavailable');return r;}finally{clearTimeout(timer);}}
  play(midi,when,duration,hand='R',velocity=1,options={}){
    const ctx=this.ctx;
    if(!this.buffers.size)throw Error('Piano samples not ready');
    if(!(velocity>0))return null;
    const root=[...this.buffers.keys()].reduce((a,b)=>Math.abs(a-midi)<=Math.abs(b-midi)?a:b);
    const buffer=this.buffers.get(root),rate=2**((midi-root)/12);
    const offset=Math.max(0,options.offset||0)*rate;
    if(offset>=buffer.duration)return null;
    when=Math.max(ctx.currentTime,when);
    // Repeated keys damp the previous excitation with a short crossfade.
    for(const old of this.voices)if(old.midi===midi&&old.when<when-1e-5)old.damp(when,.028);
    if(this.voices.size>=128){
      const victim=[...this.voices].sort((a,b)=>a.levelAt(ctx.currentTime)-b.levelAt(ctx.currentTime)||a.when-b.when)[0];
      victim.stop();
    }
    const source=ctx.createBufferSource(),filter=ctx.createBiquadFilter(),gain=ctx.createGain(),pan=ctx.createStereoPanner();
    source.buffer=buffer;source.playbackRate.value=rate;
    // Hand balance belongs to the playback interpretation, not to live MIDI
    // input: pressing the same physical key should retain its input velocity.
    const v=Math.min(1.25,velocity),level=.54*v**1.45;
    filter.type='lowpass';filter.frequency.value=Math.min(18000,2000+12500*Math.min(1,v)**1.5);filter.Q.value=.45;
    pan.pan.value=Math.max(-.24,Math.min(.24,(midi-64)/160));
    source.connect(filter);filter.connect(gain);gain.connect(pan);pan.connect(this.dry);pan.connect(this.room);
    gain.gain.setValueAtTime(0,when);gain.gain.linearRampToValueAtTime(level,when+.003);
    let ended=false,releaseEnd=Infinity;
    const fades=[];
    const floor=.00001;
    const levelAt=t=>{
      if(t<when)return 0;
      if(t<when+.003)return level*(t-when)/.003;
      const segment=fades.findLast(s=>s.at<=t);
      if(!segment)return level;
      if(t>=segment.end)return floor;
      return segment.level*(floor/segment.level)**((t-segment.at)/(segment.end-segment.at));
    };
    const fade=(at,tail)=>{
      if(ended)return;
      at=Math.max(ctx.currentTime,at,when+.004);
      if(at+tail>=releaseEnd)return;
      const value=Math.max(floor,levelAt(at));
      // Hold the existing envelope rather than jumping back to attack level.
      if(typeof gain.gain.cancelAndHoldAtTime==='function')gain.gain.cancelAndHoldAtTime(at);
      else{
        gain.gain.cancelScheduledValues(at);
        if(fades.some(s=>s.at<at))gain.gain.exponentialRampToValueAtTime(value,at);
      }
      gain.gain.setValueAtTime(value,at);gain.gain.exponentialRampToValueAtTime(floor,at+tail);
      // Keep earlier decay segments: a pause can precede a repeat that was
      // already scheduled ahead, and must hold the level at the pause time.
      while(fades.length&&fades.at(-1).at>=at)fades.pop();
      releaseEnd=at+tail;fades.push({at,end:releaseEnd,level:value});source.stop(releaseEnd+.015);
    };
    const cleanup=()=>{if(ended)return;ended=true;this.voices.delete(voice);source.disconnect();filter.disconnect();gain.disconnect();pan.disconnect();};
    const voice={midi,when,levelAt,damp:fade,
      release:(at=ctx.currentTime)=>fade(at,Math.max(.13,Math.min(.38,.37-(midi-21)*.0026))),
      stop:()=>{
        if(ended)return;
        this.voices.delete(voice);
        if(ctx.currentTime<when){source.stop(ctx.currentTime);cleanup();return;}
        fade(ctx.currentTime,.012);
      }
    };
    source.onended=cleanup;this.hasSound=true;this.voices.add(voice);source.start(when,offset);
    if(Number.isFinite(duration))voice.release(when+Math.max(.008,duration));
    return voice;
  }
  silence(){if(!this.hasSound)return;this.hasSound=false;for(const voice of [...this.voices])voice.stop();
    // Disconnect the old convolution tail so pausing and changing songs is silent.
    this.room.disconnect();this.makeRoom();
  }
}
if(typeof module!=='undefined')module.exports=SamplePiano;
