"""Read Musicnotes' embedded bitmap glyphs and vector engraving geometry.

The score is not a flattened scan: its noteheads have exact PDF placements.
The glyph table was visually checked against rendered embedded images.
"""
import hashlib,json
from pathlib import Path
import fitz
from read_vector_geometry import extract_page
ROOT=Path(__file__).resolve().parent.parent
GLYPHS={g['hash']:g for g in json.loads((Path(__file__).parent/'interstellar-image-glyphs.json').read_text())}

class GlyphPage:
    def __init__(self,page):self.page=page;self.rect=page.rect
    def get_drawings(self):return self.page.get_drawings()
    def get_text(self,kind):
        raw=self.page.get_text('rawdict');blocks=[b for b in raw['blocks'] if b['type']==0]
        for b in raw['blocks']:
            if b['type']!=1:continue
            g=GLYPHS.get(hashlib.md5(b['image']).hexdigest())
            if not g or not g['symbol']:continue
            a,c,d,e,x,y=b['transform'];l,t,r,bt=g['inkBox'];w,h=b['width'],b['height']
            points=[(a*u/w+d*v/h+x,c*u/w+e*v/h+y) for u,v in [(l,t),(r,t),(l,bt),(r,bt)]]
            box=[min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]
            origin=(box[0],(box[1]+box[3])/2)
            char=dict(c=g['symbol'],origin=origin,bbox=box)
            blocks.append(dict(type=0,lines=[dict(spans=[dict(font='MScore',size=20,origin=origin,chars=[char])])]))
        return dict(blocks=blocks)

def read():
    out=[]
    with fitz.open(ROOT/'scores/interstellar/original.pdf') as doc:
        for i,p in enumerate(doc):
            if i==0:
                out.append(dict(page=0,width=p.rect.width,height=p.rect.height,systems=[],chars=[],texts=[],ties=[],tuplets=[]));continue
            data=extract_page(GlyphPage(p),i,'interstellar')
            # Reduced heads are independent written voices, not grace notes.
            for s in data['systems']:
                for m in s['measures']:
                    for g in m['groups']:
                        g['grace']=False
                        for n in g['notes']:n['grace']=False
            out.append(data)
            print(i+1,[len(s['measures']) for s in data['systems']],flush=True)
    path=ROOT/'transcription/interstellar/geometry-raw.json'
    path.write_text(json.dumps(out,ensure_ascii=False)+'\n')

if __name__=='__main__':read()
