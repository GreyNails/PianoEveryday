"""Reproduce extraction of all 23 remaining PDFs, preserving review status."""
import argparse,json
import fitz
from read_vector_geometry import extract_page as vector_page
from read_raster_geometry import extract_page as raster_page
from compile_library_drafts import ROOT,SPECS,compile_score
from map_sparkle_edition import map_edition
VECTOR={'sparkle-animenz','sparkle-alternate','a-thousand-years','secret-base','yi-lu-xiang-bei','qi-li-xiang','silksong-clockwork-dancers','uchiage-hanabi','ge-qian','hua-hai','pu-gong-ying-de-yue-ding','hei-se-mao-yi'}

VECTOR.add('jane-doe')
VECTOR.add('interstellar')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--reuse-evidence',action='store_true');ap.add_argument('--install',action='store_true');args=ap.parse_args()
    for sid in SPECS:
        folder=ROOT/'transcription'/sid;folder.mkdir(exist_ok=True)
        path=folder/('geometry-raw.json' if sid in VECTOR else 'geometry-candidates.json')
        if args.reuse_evidence and path.exists():continue
        if sid in ('an-jing','flower-dance'):
            from read_four_geometry import read
            read(sid);continue
        if sid=='jue-bie-shu':
            from read_jue_geometry import read
            read();continue
        if sid=='interstellar':
            from read_interstellar_images import read
            read();continue
        if sid=='sparkle-alternate':map_edition();continue
        pages=[]
        for pi,page in enumerate(fitz.open(ROOT/'scores'/sid/'original.pdf')):
            pages.append(vector_page(page,pi,sid) if sid in VECTOR else raster_page(page,pi,fit_staff_slopes=sid in ('an-jing','flower-dance'),pitch_grid_tolerance=.48 if sid in ('an-jing','flower-dance') else .27))
            print(sid,'page',pi+1,flush=True)
        if sid not in VECTOR:
            from add_scan_head_readings import apply as head_readings
            head_readings(sid,pages)
        path.write_text(json.dumps(pages,ensure_ascii=False))
    # Complete all draft compilation before making the data visible in the UI.
    for sid in SPECS:compile_score(sid,False)
    if args.install:
        for sid in SPECS:
            folder=ROOT/'transcription'/sid;target=ROOT/'scores'/sid
            old=json.loads((target/'score.json').read_text())
            if old.get('transcriptionStatus')=='manual-reference':raise ValueError('Refusing to replace reviewed score '+sid)
            for source,dest in [('performance-draft.json','score.json'),('performance-draft.mid','performance.mid'),('review.json','review.json')]:
                temp=target/(dest+'.tmp');temp.write_bytes((folder/source).read_bytes());temp.replace(target/dest)
        catalog=json.loads((ROOT/'songs.json').read_text())
        for e in catalog:
            if e['id'] in SPECS:e['playable']=True;e['transcriptionStatus']='unreviewed-draft'
        temp=ROOT/'songs.json.tmp';temp.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n');temp.replace(ROOT/'songs.json')
        import update_transcription_status

if __name__=='__main__':main()
