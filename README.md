# 钢琴谱集

在本目录运行 `python -m http.server 8000 --bind 127.0.0.1`，浏览器打开 http://127.0.0.1:8000 。请通过 HTTP 打开，直接双击 HTML 可能无法读取曲库。

曲库共 51 份曲谱，其中新增 21 份来自 `pianogen3/final` 的配套 MIDI 版本（见下文）。原有《阳光宅男》《IRIS OUT》《枫》《灶门炭治郎之歌》支持播放和 MIDI 跟练。puzi.zip 的 25 份 PDF 加上 add2 的《JANE DOE》，共 26 份导入 PDF，均有音符数据并接入播放、左右手及双手 MIDI 跟练。其中《Call of Silence》和《Young and Beautiful》为对照谱面核对的参考转写；其余 24 份为可试听、试练的识别草稿，下拉框和谱面提示均标注「待校对」。两个《火花》PDF 分别保留，可在曲目下拉框切换。

早先从 puzi.zip 和 add2 导入的 PDF 没有配套的 MIDI / MusicXML，包含扫描图和多种乐谱排版。**全部曲目有数据，不等于所有音符都已准确提取；24 首的逐音校准尚未完成，不能保证正确播放原曲或准确判定跟练。** 扫描识别可能漏音、多音，复调、调号变化、八度线、连线与反复记号仍有待复核。未闭合的小节在草稿试听中按拍号缩放，具体小节列在每首的 `review.json` 中，不能当作已确认时值。

原始 PDF、两倍分辨率 PNG 和元数据保存在 `scores/<曲目 ID>/`，曲库入口为 `songs.json`。`score.json` 中保留压缩包原文件名和 SHA-256，便于溯源。原有四首的音符和谱面数据未改动。

## 重复导入

需要 Python 3.8+ 和 PyMuPDF（`python -m pip install PyMuPDF`）：

```sh
python scripts/import_pdf_scores.py ../puzi.zip
```

导入器专用于这份压缩包，处理 GBK 中文文件名，保留原 PDF，完整转换后更新目录。重复执行不会重复添加曲目；已有曲目如已加入演奏数据，脚本会拒绝覆盖。

## 检查

```sh
node scripts/test_library.cjs
python scripts/test_transcriptions.py
```

需要 Node.js 18+，Python 检查需要 PyMuPDF。检查曲库、全部图片尺寸、PDF 资源、阅谱与播放切换、可播放曲目的模拟 MIDI 跟练，以及新增转写曲目的整曲跟练遍历。转写检查覆盖符头完整性、小节边界、延音线、震音、八度线和手工核对的三连音、还原号。DOM 和音频替身检查不等于浏览器听音或实体 MIDI 设备实测。

## 已转写的两份原谱

| 曲目 | 页数 | 小节 | 音符事件 | 状态 |
|---|---:|---:|---:|---|
| Call of Silence | 2 | 44 | 1185 | 可播放、可跟练；第 9–10 小节按六连音作参考解释 |
| Young and Beautiful | 5 | 112 | 1620 | 可播放、可跟练；默认参考速度 90 BPM |

《Call of Silence》逐小节读谱的起拍与时值保存在 `transcription/call-of-silence/reading.py`，谱面坐标由 PDF 字形辅助定位。三层谱表按谱表位置和 m.d. 标记参考分手；震音缩写展开成实际按键事件。第 9–10 小节每拍六音的数字未印出，当前依据四拍的其他声部解释为六连音，这不是已消除歧义的权威版本。

《Young and Beautiful》对照五页原谱核对了复调错位、三连音、谱表归属与还原号，全部 1620 个原谱符头均保留。没有标数值的速度采用可调整的 90 BPM。两曲的琶音按同时和弦演奏，未定量的渐慢未额外延长。

重新生成（需要 PyMuPDF，Call of Silence 的 MIDI 文件导出还需要 mido）：

```sh
python scripts/read_call_geometry.py
python scripts/compile_call_of_silence.py --install
python scripts/read_young_and_beautiful.py
python scripts/export_vector_reading.py --install
```

`transcription/` 保留坐标、手工时值、编译中间数据和校对记录。`--install` 将参考转写写入本地曲库；没有该参数时仅生成中间文件。24 首草稿的每个事件对应一个 PDF 字形或图像符头候选，保存谱面坐标与来源；没有用其他 MIDI 曲目替代原谱。检测候选本身可能误判，完整性与准确性仍需逐谱校准。

## 全曲库识别草稿

```sh
# Python 环境需要 PyMuPDF、numpy、opencv-python、fonttools、mido。
python scripts/extract_library_drafts.py --install
# 已有识别坐标时，仅重新编译和接入曲库：
python scripts/extract_library_drafts.py --reuse-evidence --install
python scripts/test_draft_data.py
python scripts/update_transcription_status.py
```

12 份矢量谱从 PDF 字形、符干、符杠和小节线取得候选；11 份扫描或轮廓谱使用本地图像检测，符号模板来自这些 PDF 自身嵌入的字体。两个 Sparkle 版本的全部符头逐一比较后，按缩放坐标映射，保留各自原谱。

每首草稿保存 `score.json`、`performance.mid` 和 `review.json`；`transcription/<id>/` 另保存原始识别证据。识别数据不会覆盖两份已对照谱面核对的参考转写。`transcription/status.json` 将「已有数据」与「完成校对」分别统计，`complete` 仍为 `false`。

检查只证明文件可读取、事件对应检测候选、坐标与时间合法、MIDI 导出一致、模拟跟练流程可完成；**不证明音符无误或无遗漏**。`interstellar` 第一页是封面，保留为可浏览的无音符页面。

《一路向北》第 48 小节的 l.h. 缩小音符已直接对照谱面修正为左手实际声部，保留 1.5、2 拍起音及八分音符时值；第 40 小节的 6/4 与第 41 小节恢复 4/4 已检查。该曲全部 80 个小节现已通过时长闭合检查，仍保留草稿标记，闭合检查不等于逐音准确性认证。

## 演奏表现与播放修复

播放控制中可切换「自然 · 旋律优先」和「谱面力度」。自然模式采用保守的高声部配平：减轻和弦内声部及伴奏，未提供力度的曲目采用较柔和的默认触键；已有力度变化保留。该设置是一种参考演奏处理，左手旋律或复杂复调可切换为谱面力度对比。没有加入随机抢拍或统一渐慢，也没有根据不可靠的草稿自动补全踏板。

两种模式均合并同拍同音的重复发声，并在同音重新击键时淡出旧声音。连续乐句仅在原有音符首尾相接时加入最多 25 毫秒的衔接，不填补休止。曲终保留自然释放和房间余音；主动暂停、换曲或重新播放仍可停止声音。中途定位和调度延迟从采样的相应衰减位置恢复，避免重敲已经持续的音或集中补播过期音。

这些处理只改变试听用的演奏事件，不改动原谱音高、起拍、延音线和 MIDI 跟练判定。`performance.js` 可独立测试；音频包络取消后保持原值的处理参考 [Web Audio 参数自动化说明](https://developer.mozilla.org/en-US/docs/Web/API/AudioParam/cancelAndHoldAtTime)。

```sh
node scripts/test_performance.cjs
node scripts/test_library.cjs
node scripts/audit_playback.cjs
```

`transcription/playback-audit.json` 记录全曲库的重复发声、力度层次和未解决的节奏小节。此前 30 首可合并 215 个同拍同音的重复发声，草稿仍有 557 个演奏小节的时值识别未闭合，另有 104 个扫描拍点候选待复核。播放润色不能修正这些节奏、潜在错音或漏音。检查包括模拟音频调度及模拟 MIDI，尚未在浏览器或实体设备中完成试听验证。

## 2026-10-06 对照原谱的局部修复

用户反馈多首曲目无法辨认后，确认问题来自错音、漏谱表、调号、声部起拍和连音识别，单靠力度及音色调整不能解决。以下是实际重写或检查的范围，**不是整首校对完成**：

| 曲目 | 本次直接读谱范围 | 修复内容 |
|---|---|---|
| 诀别书 | 第 1–25 小节，PDF 第 1 页 | 调号、八度线、主旋律与伴奏、连音、速度变化、原谱踏板段落；去除伪小节 |
| 星际穿越 | 第 1–40 小节逐音重写；后段重新提取及节奏复查 | 读取 PDF 内嵌音符图像与矢量谱线，恢复完整 107 小节；修复变拍、Grave 速度、细符杠和尾段震音 |
| 安静 | 第 1–14 小节逐音重写；全谱结构复查 | 第 12 小节左手独立声部同时起音；重建 99 小节，第 78 小节为 1/4，第 79 小节取消调号并恢复 4/4 |
| 约会 | 全部 4 页、59 个源谱片段重新读谱；待独立听音复核 | 修正独立声部、休止、延音、漏检长和弦、八度线、换谱号与 12/16 尾声；反复展开为 70 个演奏片段，取消后段整小节时值缩放 |
| 丝之歌 | 第 37–66 小节节奏复查，全谱调号复查 | 校准交替击键、三连音、三十二分音符；展开第 44–46 小节的测定震音，恢复重降号及第 51 小节两拍短小节 |
| 黄昏之时 | 全部 3 页、55 小节读谱重写，仍待独立听音复核 | 修正第 3 小节多音及错误时值、区分第 18 小节上声部三连音与下声部普通十六分音符，恢复跨小节延音、换谱号、八度记号和结尾 |
| 晴天 | 第 1–12 小节逐音重写；第 13–76 小节拍点对齐 | 修复符杠误作谱线、低音加线符头漏检及附点；恢复低音八度，取消后段逐小节非等拍缩放；第 77 小节保留休止 |
| 我记得 | 第 1–12 小节逐音重写；第 13–88 小节拍点及独立声部对齐 | 修复长符干的符杠识别，按左手原谱音型对齐右手；补回漏掉的全音符长和弦，修复部分延音线，保留第 89 小节休止 |
| 打上花火 | 第 6、8、24、26、34、45、46、51、80–83 小节的节奏 | 独立声部对齐、低音错分谱表、展开震音、六连音时值；保留第 71 小节末尾原谱的 1.5 拍休止 |

手工读谱数据保存在 `scripts/review_opening_passages.py`、`scripts/review_more_openings.py` 和 `scripts/review_uchiage_rhythm.py`，每个重写音符保存原谱坐标；震音展开事件另标记其重复使用的原谱符头。重新编译会保留这些修正。扫描谱检测同时修正了谱线间距拟合和符杠计数，但后续页面的候选仍可能错误，尚未逐音校对。前端提示、每首 `review.json` 和总体 `transcription/status.json` 保留未完成状态。

《黄昏之时》的全谱记录在 `scripts/read_kataware_complete.py`，《约会》的扩展读谱在 `scripts/read_date_opening.py` 和 `scripts/read_date_complete.py`，反复顺序在 `scripts/expand_date_repeats.py`。反复事件保留 `sourceMeasure` 和 `repeatOccurrence`，谱面点击优先定位当前反复轮次。《约会》原谱 59 个片段（包含弱起）展开为 70 个演奏片段；`manuallyReadMeasures` 统计不重复的源谱片段。`scripts/review_scan_structure.py` 保存另外四曲的小节边界、谱号、八度线和伪音符排除记录，《约会》第 2–4 页的候选已用修正后的检测器重新提取，最终音符以逐小节读谱记录为准。

本次复查证实此前已标注“部分校对”的段落仍有错误，因此读谱完成和独立复核分开记录。《黄昏之时》时值检查全部闭合，但仍保留草稿状态。《安静》等尚未完成读谱重写的草稿仍有自动缩放时值；未标时值的琶音暂按同时和弦处理，未定量的自由速度与渐慢尚未处理。数据检查、源谱乐句回归检查和模拟 MIDI 跟练通过，不代表已完成浏览器听音或实体键盘验证。

查到与原谱编配者相符的 Bilibili 参考页面：[Oskar《诀别书》](https://www.bilibili.com/video/BV1T1421Z7TK/) 和 [Oskar《星际穿越》](https://www.bilibili.com/video/BV1mf4y1i7H9/)。视频请求返回 HTTP 412，未取得可播放音视频；本次音符修正依据用户提供的 PDF，不能视为已与视频听音对齐。

```sh
python scripts/compile_library_drafts.py --install jue-bie-shu interstellar an-jing your-name-date kataware-doki qing-tian wo-ji-de uchiage-hanabi
python scripts/test_transcriptions.py
python scripts/test_draft_data.py
python scripts/update_transcription_status.py
node scripts/audit_playback.cjs
```

## 补充曲谱 JANE DOE

已收录用户提供的 7 页《JANE DOE》（米津玄师、宇多田光原曲，Animenz 编配，《电锯人 蕾塞篇》片尾曲），位于 `scores/jane-doe/`，保留原 PDF、逐页图片和源文件 SHA-256。曲库标记来源为 `add2`，原压缩包的 25 首保持独立。

从 Chaconne 字形提取全部 2,876 个音符事件，共 190 小节，接入自动播放与左右手／双手 MIDI 跟练，另生成 `performance.mid`。原谱为 9/8，附点四分音符 = 134；播放器以四分音符为内部拍单位，因此参考速度为 201。已修正两处五连音、一处四连音与跨谱表音高、一处八连音、两处独立声部错位、整小节休止及末页八度线。全部小节时长闭合，仍保留未校对草稿标记：字形覆盖与时值闭合不保证逐音、分手或演奏表现完全准确，渐慢、自由速度与踏板尚未量化，未完成实际听音核验。

单份 PDF 导入器可重复使用，相同源文件不会覆盖已有音符数据：

```sh
python scripts/import_single_pdf.py '/path/to/score.pdf' --id score-id --title '曲名' --credit '编配信息'
```

该命令负责 PDF、图片与曲库登记；音符提取需按对应 PDF 格式单独处理。《JANE DOE》的几何证据位于 `transcription/jane-doe/geometry-raw.json`，局部读谱修正在 `scripts/review_jane_doe.py`，可用 `python scripts/compile_library_drafts.py --install jane-doe` 重新生成音符和 MIDI。

## 后段断续修复（2026-10-06）

《晴天》《我记得》《星际穿越》原先分别有 60、74、49 个后段小节因识别时值不闭合而被按整小节缩放。新数据不再对这三首后段做这种缩放；播放和 MIDI 跟练使用同一套拍点。`transcription/rhythm-repair-report.json` 保存修复前后的指标，`review_scan_pulse.py` 保存两份扫描谱的源谱拍点与左手音型，`read_interstellar_images.py` 保存嵌入式音符图像的读取方法。

《晴天》的谱线检测现在比较完整五条谱线，避免将长符杠纳入谱表，也避免高阈值漏掉较浅的谱表；加线符头允许更宽的连通区域，恢复此前丢失的低音八度。《我记得》的漏检空心／全音符在 `add_scan_head_readings.py` 中逐个记录位置。《星际穿越》恢复第 5 页被漏掉的一行、变拍，以及第 102–107 小节的尾段震音，合计 107 小节、2,885 个事件。

拍点对齐仍不代表逐音校对完成：《晴天》还有 31 个未匹配候选列，扫描音高、部分时值和漏音仍需复核。未做实际听音或实体 MIDI 测试；自动检查覆盖谱面来源、音符时间范围、MIDI 导出、音频调度模拟及整曲模拟跟练。


## 《约会》《丝之歌》后段节奏修复（2026-10-06）

《约会》后段原有 30 个演奏小节依靠整小节缩放闭合，现按独立声部重新记录起拍、时值和休止；补回空心符头及尾声长和弦，剔除横梁误检音符，保留延音线、低音谱号转高音谱号和末和弦 15ma。全部 59 个源谱片段直接读谱，反复后为 70 个演奏片段、1,086 个事件，时值未闭合数为零；原谱琶音仍按同时和弦，自由渐慢未额外量化。

《丝之歌》第 37–66 小节重排左右手、独立声部及连音。第 44–46 小节右手三道斜杠的两音组震音，分别展开为 12 次交替起音（每次 1/8 个四分拍，即三十二分音符），左手保留两个三连音组及末尾四个三十二分音符；补齐这部分原先缺少的 60 个事件。第 55 小节的三连音与快速音群单独核对，原谱重降号现在参与音高计算。全曲 75 小节、1,546 个事件，原有 10 个未闭合小节清零。没有节拍器数字的文字速度使用参考值：100 → 144 → 176 → 66 BPM，末段按 rit. 逐步至 46；这些速度是演奏解释，可在前端调整，不是原谱给出的数值。

修正在 `scripts/read_date_complete.py` 和 `scripts/review_silksong_rhythm.py`。`score.json`、`performance.mid`、跟练音符及校对报告已同步更新。回归检查覆盖震音起音间隔、三连音、交替分手、尾声连续十六分音符、长音与延音线、源谱符头覆盖，以及整曲模拟 MIDI 跟练；未完成实际听音和实体 MIDI 验证，两首保留草稿状态。

```sh
python scripts/compile_library_drafts.py --install your-name-date silksong-clockwork-dancers
```

## 《诀别书》《七里香》《黑色毛衣》节奏修复（2026-10-06）

《诀别书》第 26–100 小节改用原谱拍点与连音分组，取消原有 67 个小节的整体时值缩放。扫描谱按谱线斜率定位，修正第 52、67 小节左手谱表错位与截断；补回部分加线音符及结尾全音符。恢复第 54–56 小节的 3/4、第 89 小节的 128 BPM、第 97 小节的 104 BPM，以及已确认的部分踏板、延音和八度线。全曲现为 100 小节、397 个四分拍、2,622 个事件；前 25 小节仍是逐音读谱，后 75 小节是拍点校准，不能混同为全谱逐音校对。

《七里香》修正独立声部与跨谱表分手，第 56 小节末两组七连音按每音 1/14 拍排列，第 80 小节末两组九连音按每音 1/9 拍排列；修正相关八度线。保留全部 2,889 个源谱符头事件，原有 7 个时值未闭合小节清零。

《黑色毛衣》恢复第 5 小节起的原谱 62 BPM，修正第 4 小节长低音与跨手短音并行、第 78 小节快速三连音与八度线终点、第 97 小节跨谱表和弦以及尾声长和弦。保留全部 1,864 个源谱符头事件，原有 14 个时值未闭合小节清零。

修正数据位于 `scripts/review_jue_rhythm.py`、`scripts/review_qili_hei_rhythm.py`，扫描布局和漏检符头位于 `scripts/jue-scan-layout.json`、`scripts/read_jue_geometry.py`。原始候选不被节奏校准覆盖，排除的未匹配候选也保存在报告中。《诀别书》仍有 66 个未匹配候选列及 7 个缺少已匹配符头的谱面列待复核；时值闭合并不保证无漏音或错音。自由渐慢、全曲演奏表现及实际听音未完成，三曲均保留草稿状态。

`score.json` 与 `performance.mid` 已同步更新，播放和 MIDI 跟练共用修正后的拍点。22 项 Python 回归检查通过，涵盖连音时值、原谱休止、八度线终点、数字速度、变拍、结尾长音和矢量符头覆盖；另有音频调度与整曲模拟 MIDI 检查，不代表实体设备或浏览器实际听音验证。

```sh
python scripts/compile_library_drafts.py --install jue-bie-shu qi-li-xiang hei-se-mao-yi
python -m unittest discover -s scripts -p 'test_*.py'
```

## 《七里香》小符头跟进修正（2026-10-06）

原检测器把所有较小符头都标记为装饰音，导致第 9、32、49、65、69、75、77 等小节的计拍内声部被压缩到 0.1 拍，连续和弦甚至挤到同一拍点。现按原谱区分小符头的独立声部、七／九连音和实际装饰音；225 个小符头全部保留，其中 139 个按谱面计拍、86 个保留装饰音标记。小符头与普通符头共用符干的和弦也逐音保留大小及力度信息。

第 5、81 小节末三个小三十二分音符依次在 3.625、3.75、3.875 拍起音；第 47、65、77 小节的低音双音装饰也恢复顺序。第 69 小节补齐内声部延音线。另将错误归入第 33 小节右手的 MIDI 103 高音，改回第 30 小节末、原坐标处的 MIDI 29 低音，并恢复与下一小节的延音。

小音符采用 0.58 的参考力度（普通提取音符为 0.8），导出 MIDI 对应力度 54（普通为 75），实际力度属于演奏解释。源谱音符总数仍为 2,889，未删去小符头。`scripts/review_qili_small_notes.py` 保存修正，重新编译不会丢失。23 项 Python 检查及音频调度、整曲模拟跟练检查通过；尚未实际听音或实测实体键盘，保留草稿状态。

## 《搁浅》《安静》《Flower Dance》《蒲公英的约定》断奏跟进（2026-10-07）

《搁浅》按原谱重排 14 个重点小节的独立声部与小符头计拍。第 4 小节两和弦之间的四道震音符杠展开为 24 次交替起音，共用原来的附点四分音符时段；第 53 小节缩小印刷的六连音恢复实际节拍及较轻力度。恢复第 25、30、49 小节转调、相关高低八度标记，以及第 49 小节的 13/16 拍。全曲 60 小节、239.25 拍、1,969 个事件。

《蒲公英的约定》修正 17 个重点小节的三连音、六连音、五连音、独立长音与休止；第 17、25 小节相邻符头组成的同拍和弦不再被拆成错开的起音，第 25 小节误分到左手的右手音符归回原声部。保留全部 2,393 个源谱符头。

《安静》保留前 14 小节逐音读谱，后续 84 小节对齐原谱旋律拍点、部分伴奏音型和连线；第 78 小节保持一拍过渡。扫描重提取后为 2,052 个事件。《Flower Dance》重建 120 小节及漏检谱表，恢复五升号、换谱号、八度线和原谱数字速度 75 → 96 → 90 → 71；重点快速段落逐组补回 106 个三十二分音符符头，第 47、95–104 小节右手均恢复 32 次等距起音，第 48 小节为 24 次起音后保留一拍休止。现有 2,319 个事件。

四首旧版时值未闭合小节分别为 8、76、113、17，本轮输出均不再因这些检测结果缩放小节。但扫描谱对齐并非完整逐音校对：《安静》仍有 226 条匹配不确定记录，《Flower Dance》仍有 735 条，包含缺少候选、额外候选及偏离参考列的位置；另有未完整读定的伴奏细分。原谱扫描音高、局部升降号和独立持续声部仍可能错误，保留草稿标签，不应把时值闭合当作识谱准确率。

修正可由 `scripts/review_four_vector_rhythm.py`、`scripts/review_four_scan_rhythm.py`、`scripts/read_four_geometry.py` 重现。`score.json`、`performance.mid` 和校对报告同步更新，自动播放和 MIDI 跟练共用拍点。28 项 Python 检查覆盖三十二分音符缺口、原谱休止、连线、一拍过渡、13/16 拍、震音与连音、八度及源谱符头覆盖；音频调度与全曲模拟 MIDI 跟练检查通过。未完成实际听音及实体键盘验证。

```sh
python scripts/compile_library_drafts.py --install ge-qian an-jing flower-dance pu-gong-ying-de-yue-ding
python -m unittest discover -s scripts -p 'test_*.py'
```

## 配套 MIDI 曲库（2026-10-08）

已加入 `/storage/homes/hongzj/dell/pianogen3/final` 中全部 21 首当前成品，每首保留原 PDF、MIDI、MusicXML 和逐页图片，曲目名称带「MIDI 版」。包含 Enchanted、Merry Christmas Mr. Lawrence、Photograph、The Fate of Ophelia、All Too Well、Bad Habits、Cardigan、Exile、Eyes Closed、He's a Pirate、JANE DOE、Look What You Made Me Do、Love Story、Perfect、Sapphire、Shivers、Speak Now、The 1、Viva La Vida、Willow、烟花易冷。历史 PDF 备份和动画导出不是额外曲目。原有 30 首保留，两个 JANE DOE 版本可分别选择。

音高、起音、松键、力度、变速与 CC64 延音直接来自配套 MIDI，左右手来自 MIDI 轨道。播放使用 `playBeat`，跟练按谱面 `beat` 合并同时和弦，保留 MIDI 的细微错落而不将和弦拆成多个练习步骤。两个演奏模式均保留这些 MIDI 的已有力度与起音，不再叠加自然模式的声部配平或额外连奏。钢琴采样音色和房间效果仍由播放器提供。

谱面坐标由相同源数据与 LilyPond PDF 后端的音符链接取得，并检查页数、谱表几何与原 PDF 一致。全部 MIDI 起音逐个对应谱面音符；延音线的后续符头不重新发声。曲终保留 MIDI 的实际释放时长。导入核验以所提供的文件为依据，没有重新验证原始扒谱与原曲的一致性。

```sh
# 需要 Python、PyMuPDF、mido，以及同级 pianogen3 的源数据、排版脚本和本地 LilyPond。
python scripts/import_midi_collection.py --install
python scripts/test_midi_collection.py
node scripts/test_performance.cjs
node scripts/test_library.cjs
```

导入器先完整生成再更新曲库，可重复运行，不重复添加。`scores/final-*/review.json` 保存来源哈希、MIDI 控制器和逐曲配对结果；`transcription/pianogen3-final/import-report.json` 保存汇总。`transcription/final-*/` 保留制谱数据及坐标提取记录。检查覆盖原 MIDI 音符、速度与力度的一致性、谱面坐标、小节边界和模拟跟练；不等同于实体 MIDI 键盘实测。

本次 30 项 Python 回归检查、51 首播放计划与整曲模拟 MIDI 跟练检查通过，原有 30 首 `score.json` 的 SHA-256 未改变。竖版与横版首页已叠加符头坐标抽查。浏览器启动受当前环境限制，未完成浏览器实际听音或实体键盘测试；结果见 `transcription/pianogen3-final/verification.json`。

## GitHub Pages 发布

目标仓库为 `GreyNails/PianoEveryday`，发布分支为 `gh-pages`，站点入口是根目录 `index.html`。这是静态应用，音源及 51 首曲谱均在仓库中，线上运行不依赖本地 Python、识谱脚本或源曲谱目录。页面使用相对资源路径，支持 `/PianoEveryday/` 子路径。

在仓库 **Settings → Pages** 中，选择 **Deploy from a branch → gh-pages → /(root)**。`.nojekyll` 已包含在发布目录。完成 GitHub 身份验证后，在本目录运行：

```sh
git push origin gh-pages
```

Pages 构建成功后的预期地址为 `https://greynails.github.io/PianoEveryday/`。该地址并不代表本次上传已成功；应在 GitHub Actions / Pages 中确认最新提交的部署状态，并访问网站核对曲库为 51 首。发布方式见 [GitHub 官方说明](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)。

当前应用尚无用户账号系统。GitHub 推送身份验证与网站用户登录是两件独立的事；此发布配置不会提供邮箱登录链接，也不会保护静态曲谱文件。

