"""Corrections established by direct inspection of the supplied score pages.

An entry documents the inspected passage, not certification of the entire work.
Raw detector evidence stays unchanged so each correction can be audited.
"""

def apply(sid,pages):
    from review_scan_structure import apply as scan_structure
    corrections=scan_structure(sid,pages)
    if sid in ('an-jing','flower-dance'):
        from review_four_scan_rhythm import apply as scan_rhythm
        corrections += scan_rhythm(sid,pages)
    if sid in ('qing-tian','wo-ji-de'):
        from review_scan_pulse import apply as pulse
        corrections += pulse(sid,pages)
    if sid=='interstellar' and pages[1].get('beams') is not None:
        from review_interstellar_rhythm import apply as interstellar_rhythm
        return interstellar_rhythm(pages)
    if sid=='jue-bie-shu':
        from review_jue_rhythm import apply as jue_rhythm
        return jue_rhythm(pages)
    if sid in ('ge-qian','pu-gong-ying-de-yue-ding'):
        from review_four_vector_rhythm import apply as four_vector
        return four_vector(sid,pages)
    if sid in ('qi-li-xiang','hei-se-mao-yi'):
        from review_qili_hei_rhythm import apply as song_rhythm
        return song_rhythm(sid,pages)
    if sid=='silksong-clockwork-dancers':
        from review_silksong_rhythm import apply as silksong_rhythm
        return silksong_rhythm(pages)
    if sid=='jane-doe':
        from review_jane_doe import apply as jane_reading
        return jane_reading(pages)
    if sid=='uchiage-hanabi':
        from review_uchiage_rhythm import apply as rhythm_reading
        return rhythm_reading(pages)
    measures=[m for p in pages for s in p['systems'] for m in s['measures']]
    if sid=='yi-lu-xiang-bei':
        groups=measures[47]['groups']
        cues=[g for g in groups if 469<g['x']<494 and g['grace']]
        assert len(cues)==2 and sum(len(g['notes']) for g in cues)==3
        for g in cues:
            g['grace']=False;g['hand']='L'
            for n in g['notes']:n['grace']=False
        corrections.append(dict(page=4,measure=48,reason='l.h. 方括号内缩小印刷的音符是实际左手八分音符声部，不是装饰音。',onsets=[1.5,2],duration=.5,hand='L',pitches=[77,79,84]))
    return corrections
