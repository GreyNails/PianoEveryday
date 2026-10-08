"""Render symbol templates from fonts embedded in the user's source PDFs."""
import io,json,fitz,numpy as np,cv2
from pathlib import Path
from fontTools.ttLib import TTFont,newTable
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
ROOT=Path(__file__).resolve().parent.parent
CACHE=ROOT/'transcription'/'symbol-templates'
SYMBOLS='\ue050\ue062\ue260\ue261\ue262\ue4e3\ue4e4\ue4e5\ue4e6\ue4e7'

def templates():
    path=CACHE/'index.json'
    if not path.exists():
        CACHE.mkdir(exist_ok=True);index=[]
        for sid in ('hua-hai','secret-base'):
            src=fitz.open(ROOT/'scores'/sid/'original.pdf')
            f=next(f for f in src[0].get_fonts() if f[3]=='Leland')
            font=TTFont(io.BytesIO(src.extract_font(f[0])[3]));order=font.getGlyphOrder()
            cmap={c[0]:order[c[1]] for p in src for tr in p.get_texttrace() if tr['font']=='Leland' for c in tr['chars'] if c[1]<len(order)}
            font['cmap']=newTable('cmap');font['cmap'].tableVersion=0;t=CmapSubtable.newSubtable(4);t.platformID=3;t.platEncID=1;t.language=0;t.cmap=cmap;font['cmap'].tables=[t]
            buffer=io.BytesIO();font.save(buffer)
            for symbol in SYMBOLS:
                if ord(symbol) not in cmap:continue
                doc=fitz.open();page=doc.new_page(width=120,height=160);page.insert_font(fontname='music',fontbuffer=buffer.getvalue());page.insert_text((40,90),symbol,fontname='music',fontsize=40)
                pm=page.get_pixmap(matrix=fitz.Matrix(2,2),colorspace=fitz.csGRAY);ink=(np.frombuffer(pm.samples,np.uint8).reshape(pm.height,pm.width)<180).astype(np.uint8)
                yy,xx=np.where(ink);x0=max(0,int(xx.min())-2);y0=max(0,int(yy.min())-2);x1=int(xx.max())+3;y1=int(yy.max())+3
                name=sid+'-'+str(ord(symbol))+'.png';cv2.imwrite(str(CACHE/name),ink[y0:y1,x0:x1]*255)
                index.append(dict(symbol=symbol,file=name,gap=20,ox=80-x0,oy=180-y0))
        path.write_text(json.dumps(index,ensure_ascii=False))
    return [(item,cv2.imread(str(CACHE/item['file']),cv2.IMREAD_GRAYSCALE)/255.) for item in json.loads(path.read_text())]
