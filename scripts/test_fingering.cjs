const assert=require('assert'),F=require('../dist/fingering.js'),fs=require('fs'),path=require('path');
function notes(ns,hand='R',chord=false){return ns.map((midi,id)=>({id,midi,hand,beat:chord?0:id,duration:1,soundDuration:1}));}
for(const hand of ['R','L']){
 for(const ns of [[60,64,67],[60,72],[61,65,68]]){
  const events=notes(ns,hand,true),m=F.recommend(events,hand),f=events.map(e=>m.get(e.id).finger);
  assert(f.every(v=>v>=1&&v<=5));assert.equal(new Set(f).size,ns.length);assert(f.every((v,i)=>!i||(hand==='R'?v>f[i-1]:v<f[i-1])));
 }
 const scale=notes([60,62,64,65,67,69,71,72],hand),m=F.recommend(scale,hand);assert.equal(m.size,scale.length);
 const wide=notes([48,72],hand,true);assert([...F.recommend(wide,hand).values()].every(a=>!a.finger&&a.warning));
 const tied=[{id:0,midi:60,beat:0,duration:1,soundDuration:2,hand},{id:1,midi:60,beat:1,duration:1,hand,tieFrom:0}];const t=F.recommend(tied,hand);assert.equal(t.get(0).finger,t.get(1).finger);
}
for(const song of JSON.parse(fs.readFileSync(path.join(__dirname,'../dist/songs.json')))){
 const s=JSON.parse(fs.readFileSync(path.join(__dirname,'../dist',song.url)));
 for(const hand of ['R','L']){const m=F.recommend(s.events,hand);assert.equal(m.size,s.events.filter(e=>e.hand===hand).length);assert([...m.values()].every(v=>v.finger==null||v.finger>=1&&v.finger<=5));}
}
console.log('Finger range, hand direction, chord uniqueness, wide-chord fallback, ties and four-score coverage passed.');
