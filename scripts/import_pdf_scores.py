"""Import the supplied PDF collection without inventing performance events.

Requires PyMuPDF. Filenames in puzi.zip use legacy GBK encoding.
Run from any directory: python scripts/import_pdf_scores.py ../puzi.zip
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

import fitz

ROOT = Path(__file__).resolve().parent.parent
COLLECTION = "puzi"
STATUS = "已收录完整原谱，可翻页阅读或打开原 PDF。此版本尚未完成音符与节拍校对，暂不支持自动播放和 MIDI 跟练。"
# Titles distinguish editions; credits are only taken from supplied filenames.
SCORES = [
    ("194 Sparkle 你的名字 火花 A叔 原版.pdf", "sparkle-animenz", "Sparkle / 火花（A叔原版）", "A叔版"),
    ("1_晴天.pdf", "qing-tian", "晴天", ""),
    ("A Thousand Years-Oskar Roman Je.pdf", "a-thousand-years", "A Thousand Years", "Oskar Roman Jezior 版"),
    ("City of stars.pdf", "city-of-stars", "City of Stars", ""),
    ("Flower dance   罗曼耶卓版.pdf", "flower-dance", "Flower Dance", "罗曼耶卓版"),
    ("O叔版~《黄昏之时》你的名字_1053835.pdf", "kataware-doki", "黄昏之时", "O叔版 · 你的名字"),
    ("Secret Base 未闻花名ed （扒谱：bilibili白卉Studio）.pdf", "secret-base", "Secret Base / 未闻花名", "扒谱：bilibili 白卉Studio"),
    ("call_of_silence(oskar.ver) - 完整乐谱.pdf", "call-of-silence", "Call of Silence", "Oskar 版"),
    ("young_and_beautiful.pdf", "young-and-beautiful", "Young and Beautiful", ""),
    ("《Wake Me Up When September Ends》 罗曼耶卓.pdf", "wake-me-up-when-september-ends", "Wake Me Up When September Ends", "罗曼耶卓版"),
    ("《我记得》赵雷，O叔优化版_五线谱_pop_1062603(1).pdf", "wo-ji-de", "我记得", "赵雷 · O叔优化版"),
    ("一路向北-罗曼耶卓.pdf", "yi-lu-xiang-bei", "一路向北", "罗曼耶卓版"),
    ("七里香-罗曼耶卓（大音符排版）.pdf", "qi-li-xiang", "七里香", "罗曼耶卓版 · 大音符排版"),
    ("丝之歌_机枢舞者.pdf", "silksong-clockwork-dancers", "丝之歌 · 机枢舞者", ""),
    ("你的名字《约会》-罗曼耶卓.pdf", "your-name-date", "约会", "罗曼耶卓版 · 你的名字"),
    ("安静  o叔版.pdf", "an-jing", "安静", "O叔版"),
    ("打上花火_fireworks.pdf", "uchiage-hanabi", "打上花火", ""),
    ("搁浅-罗曼耶卓.pdf", "ge-qian", "搁浅", "罗曼耶卓版"),
    ("星际穿越Interstellar (First Step - No Time for Caution) - A Minor - MN0192914.pdf", "interstellar", "星际穿越 / Interstellar", "First Step – No Time for Caution · A Minor"),
    ("火花.pdf", "sparkle-alternate", "火花（另一 PDF 版本）", ""),
    ("花海.pdf", "hua-hai", "花海", ""),
    ("蒲公英的约定.pdf", "pu-gong-ying-de-yue-ding", "蒲公英的约定", ""),
    ("诀别书o叔(1).pdf", "jue-bie-shu", "诀别书", "O叔版"),
    ("这世界那么多人O叔.pdf", "zhe-shi-jie-na-me-duo-ren", "这世界那么多人", "O叔版"),
    ("黑色毛衣.pdf", "hei-se-mao-yi", "黑色毛衣", ""),
]


def archive_name(info):
    return info.filename if info.flag_bits & 0x800 else info.filename.encode("cp437").decode("gbk")


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def import_scores(archive, root=ROOT):
    catalog_path = root / "songs.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    existing = {entry["id"]: entry for entry in catalog}
    added = []
    with zipfile.ZipFile(archive) as source:
        members = {archive_name(info): info for info in source.infolist() if not info.is_dir()}
        if set(members) != {item[0] for item in SCORES}:
            raise ValueError("压缩包内容与 puzi 曲谱清单不符，未导入。")
        # Render everything before changing the published catalog. Never extract
        # archive paths directly or overwrite another collection's score data.
        with tempfile.TemporaryDirectory(prefix=".pdf-import-", dir=root) as staging:
            stage = Path(staging)
            for filename, sid, title, credit in SCORES:
                target = root / "scores" / sid
                old = existing.get(sid)
                if old and old.get("collection") != COLLECTION:
                    raise ValueError(f"曲目 ID 已被使用：{sid}")
                if target.exists() and not old:
                    raise ValueError(f"未登记的曲谱目录已存在：{target}")
                pdf = source.read(members[filename])
                digest = hashlib.sha256(pdf).hexdigest()
                if old:
                    data = json.loads((target / "score.json").read_text(encoding="utf-8"))
                    if data.get("mode") != "view":
                        raise ValueError(f"{sid} 已有演奏数据，禁止覆盖。")
                    if data.get("sourceSha256") != digest or hashlib.sha256((target / "original.pdf").read_bytes()).hexdigest() != digest:
                        raise ValueError(f"{sid} 源文件发生变化，请先核对。")
                    if all((target / f"page-{n+1}.png").is_file() for n in range(data["pages"])):
                        print(f"保留 {title}：{data['pages']} 页", flush=True)
                        continue
                dest = stage / sid
                dest.mkdir()
                (dest / "original.pdf").write_bytes(pdf)
                sizes = []
                with fitz.open(stream=pdf, filetype="pdf") as document:
                    if document.needs_pass or not document.page_count:
                        raise ValueError(f"无法读取 PDF：{filename}")
                    for number, page in enumerate(document, 1):
                        sizes.append(dict(width=page.rect.width, height=page.rect.height))
                        page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).save(dest / f"page-{number}.png")
                data = dict(title=title, credit=credit, mode="view", status=STATUS,
                            pages=len(sizes), pageSizes=sizes, totalBeats=0,
                            systems=[], measures=[], events=[],
                            sourceFilename=filename, sourceSha256=digest)
                write_json(dest / "score.json", data)
                base = f"scores/{sid}/"
                entry = dict(id=sid, title=title, credit=credit, url=base + "score.json",
                             base=base, playable=False, pdf=base + "original.pdf", collection=COLLECTION)
                if not old:
                    added.append(entry)
                print(f"导入 {title}：{len(sizes)} 页", flush=True)
            for dest in stage.iterdir():
                target = root / "scores" / dest.name
                shutil.copytree(dest, target, dirs_exist_ok=True)
            write_json(stage / "songs.json", catalog + added)
            (stage / "songs.json").replace(catalog_path)
    print(f"曲库共 {len(catalog) + len(added)} 首，本次新增 {len(added)} 首。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", nargs="?", type=Path, default=ROOT.parent / "puzi.zip")
    args = parser.parse_args()
    import_scores(args.archive)
