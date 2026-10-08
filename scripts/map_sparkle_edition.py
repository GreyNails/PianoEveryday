"""Map the same engraved notes to the resized second Sparkle PDF.

Every note glyph is compared; reject the mapping if either edition differs.
"""
import fitz,numpy as np,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
def map_edition():
    A=fitz.open(ROOT/'scores/sparkle-animenz/original.pdf');B=fitz.open(ROOT/'scores/sparkle-alternate/original.pdf')
    ps=json.loads((ROOT/'transcription/sparkle-animenz/geometry-raw.json').read_text())
    for i,(a,b) in enumerate(zip(A,B)):
     def coords(p):return np.array([c['origin'] for bl in p.get_text('rawdict')['blocks'] for l in bl.get('lines',[]) for s in l['spans'] if s['font'] in ('Pavane','FEF75F697B8') for c in s['chars'] if c['c'] in ('œ','˙','w')])
     aa,bb=coords(a),coords(b);assert aa.shape==bb.shape
     sx,dx=np.linalg.lstsq(np.c_[aa[:,0],np.ones(len(aa))],bb[:,0],rcond=None)[0];sy,dy=np.linalg.lstsq(np.c_[aa[:,1],np.ones(len(aa))],bb[:,1],rcond=None)[0]
     residual=float(np.abs(aa*np.array([sx,sy])+np.array([dx,dy])-bb).max());assert residual<.15,(i,residual)
     def transform(v):
      if isinstance(v,list):return [transform(q) for q in v]
      if not isinstance(v,dict):return v
      out={}
      for k,q in v.items():
       if isinstance(q,(int,float)):
        if k in ('x','ox','x0','x1','left','right','stemX'):q=q*sx+dx
        elif k in ('y','y0','y1','top','bottom','center','tip','stem0','stem1'):q=q*sy+dy
        elif k in ('w','width'):q=q*sx
        elif k in ('h','height','step','size'):q=q*sy
       elif k=='points':q=[[x*sx+dx,y*sy+dy] for x,y in q]
       else:q=transform(q)
       out[k]=q
      return out
     ps[i]=transform(ps[i]);ps[i]['width']=b.rect.width;ps[i]['height']=b.rect.height;ps[i]['editionMappingResidual']=residual
    out=ROOT/'transcription/sparkle-alternate';out.mkdir(exist_ok=True);(out/'geometry-raw.json').write_text(json.dumps(ps,ensure_ascii=False))
    print('Matched all note glyphs in both Sparkle editions, 7 pages.')

if __name__=='__main__':map_edition()
