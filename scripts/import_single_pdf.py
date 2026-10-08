"""Add one local PDF to the library; preserve existing performance data."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile

import fitz
from import_pdf_scores import ROOT, STATUS, write_json


def import_pdf(source, sid, title, credit='', collection='add2', root=ROOT):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',sid):
        raise ValueError('Invalid score ID')
    source=Path(source);pdf=source.read_bytes();digest=hashlib.sha256(pdf).hexdigest()
    catalog=json.loads((root/'songs.json').read_text())
    target=root/'scores'/sid
    existing=next((e for e in catalog if e['id']==sid),None)
    if existing:
        data=json.loads((root/existing['url']).read_text())
        if data.get('sourceSha256')!=digest or hashlib.sha256((root/existing['pdf']).read_bytes()).hexdigest()!=digest:
            raise ValueError('Score ID already belongs to a different PDF')
        if not all((target/f'page-{i+1}.png').exists() for i in range(data['pages'])):
            raise ValueError('Existing score has missing images; repair before importing')
        print(f"保留 {existing['title']}：{data['pages']} 页，已有音符数据不覆盖。")
        return
    if target.exists():raise ValueError(f'Unregistered score directory exists: {target}')
    with tempfile.TemporaryDirectory(prefix='.pdf-import-',dir=root) as tmp:
        stage=Path(tmp);dest=stage/sid;dest.mkdir();sizes=[]
        (dest/'original.pdf').write_bytes(pdf)
        with fitz.open(stream=pdf,filetype='pdf') as document:
            if document.needs_pass or not document.page_count:raise ValueError('Unreadable PDF')
            for i,page in enumerate(document):
                sizes.append(dict(width=page.rect.width,height=page.rect.height))
                page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False).save(dest/f'page-{i+1}.png')
        write_json(dest/'score.json',dict(title=title,credit=credit,mode='view',status=STATUS,
                   pages=len(sizes),pageSizes=sizes,totalBeats=0,systems=[],measures=[],events=[],
                   sourceFilename=source.name,sourceSha256=digest))
        base=f'scores/{sid}/'
        catalog.append(dict(id=sid,title=title,credit=credit,url=base+'score.json',base=base,
                            playable=False,pdf=base+'original.pdf',collection=collection))
        write_json(stage/'songs.json',catalog)
        shutil.move(str(dest),target)
        (stage/'songs.json').replace(root/'songs.json')
    print(f'新增 {title}：{len(sizes)} 页，曲库共 {len(catalog)} 首。')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source',type=Path);ap.add_argument('--id',required=True)
    ap.add_argument('--title',required=True);ap.add_argument('--credit',default='')
    ap.add_argument('--collection',default='add2');args=ap.parse_args()
    import_pdf(args.source,args.id,args.title,args.credit,args.collection)
