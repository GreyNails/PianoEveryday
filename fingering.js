'use strict';
// Heuristic reference fingerings, not editorial fingerings from the PDF.
// A bounded sequence search balances hand movement, black-key thumbs,
// thumb crossings and fingers occupied by sustained notes.
const Fingering=(()=>{
  const black=n=>[1,3,6,8,10].includes(n%12);
  const reach=[0,0,2,4,5.5,7.5];
  function choices(count,hand){
    const out=[];
    function walk(a,next){if(a.length===count){out.push(hand==='R'?a:a.map(f=>6-f));return;}for(let f=next;f<=5;f++)walk([...a,f],f+1);}
    walk([],1);return out;
  }
  function recommend(events,hand){
    const steps=[];
    for(const e of events.filter(e=>e.hand===hand&&e.tieFrom==null).sort((a,b)=>a.beat-b.beat)){
      let s=steps.at(-1);if(!s||Math.abs(s.beat-e.beat)>1e-5){s={beat:e.beat,events:[],notes:[]};steps.push(s);}
      s.events.push(e);if(!s.notes.includes(e.midi))s.notes.push(e.midi);
    }
    let beam=[{cost:0,held:[],pose:null,last:null,node:null}];
    const sign=hand==='R'?1:-1;
    for(const step of steps){
      step.notes.sort((a,b)=>a-b);
      const ns=step.notes,wide=ns.length>5||ns.at(-1)-ns[0]>12;
      let next=[];
      for(const state of beam){
        const held=state.held.filter(h=>h.end>step.beat+1e-5);
        for(const fs of wide?[]:choices(ns.length,hand)){
          if(ns.some((n,i)=>held.some(h=>(h.n!==n&&h.f===fs[i])||(h.n===n&&h.f!==fs[i]))))continue;
          // An interval involving a held finger must remain plausible as well.
          const all=[...held.filter(h=>!ns.includes(h.n)),...ns.map((n,i)=>({n,f:fs[i]}))];
          if(all.length>5||Math.max(...all.map(h=>h.n))-Math.min(...all.map(h=>h.n))>12)continue;
          let local=0;
          const poses=all.map(h=>h.n-sign*reach[h.f]);
          const pose=poses.reduce((a,b)=>a+b,0)/poses.length;
          local+=poses.reduce((sum,p)=>sum+(p-pose)**2,0)*.15;
          for(let i=0;i<ns.length;i++)local+=black(ns[i])?(fs[i]===1?1.6:fs[i]===5?.35:0):0;
          if(state.pose!=null)local+=Math.abs(pose-state.pose)*.24;
          if(state.last&&ns.length===1&&state.last.ns.length===1){
            const delta=(ns[0]-state.last.ns[0])*sign,fd=fs[0]-state.last.fs[0];
            if(delta===0&&fd!==0)local+=1.2;
            if(delta!==0&&fd===0)local+=Math.abs(delta)<5?2.2:.6;
            if(delta*fd<0){
              const cross=delta>0?fs[0]===1&&[2,3,4].includes(state.last.fs[0]):state.last.fs[0]===1&&[2,3,4].includes(fs[0]);
              local+=cross?1.0:5;
            }
          }
          const occupied=ns.map((n,i)=>({n,f:fs[i],end:Math.max(...step.events.filter(e=>e.midi===n).map(e=>e.beat+(e.soundDuration||e.duration)))}));
          next.push({cost:state.cost+local,pose,last:{ns,fs},held:[...held.filter(h=>!ns.includes(h.n)),...occupied],node:{prev:state.node,step,fs,warning:''}});
        }
      }
      if(!next.length){
        const best=beam.reduce((a,b)=>a.cost<b.cost?a:b);
        // Do not invent a playable five-finger solution for large/held chords.
        next=[{cost:best.cost,pose:null,last:null,held:[],node:{prev:best.node,step,fs:[],warning:wide?'跨度较大或超过五音，请按手型拆分或调整分手。':'持续声部占用手指，请结合延音调整指法。'}}];
      }
      next.sort((a,b)=>a.cost-b.cost);beam=next.slice(0,20);
    }
    const result=new Map();let node=beam[0].node;
    while(node){node.step.events.forEach(e=>result.set(e.id,{finger:node.fs[node.step.notes.indexOf(e.midi)]||null,warning:node.warning}));node=node.prev;}
    // Tied continuations inherit the original finger without another attack.
    for(const e of events.filter(e=>e.hand===hand))if(e.tieFrom!=null){let p=e,seen=new Set();while(p.tieFrom!=null&&!seen.has(p.id)){seen.add(p.id);p=events.find(a=>a.id===p.tieFrom)||{id:-1};}result.set(e.id,result.get(p.id)||{finger:null,warning:'延音指法请按实际手型调整。'});}
    return result;
  }
  return {recommend};
})();
if(typeof module!=='undefined')module.exports=Fingering;
