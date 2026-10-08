"""Attack columns read on 1050px previews of the supplied scanned scores.

Numbers are x / sixteenth-note tick within the printed 4/4 bar. These readings
align attacks, not pitches. Durations and missing heads remain candidates.
No timing is inferred from a recording, and no whole-bar time stretching is
used in the covered passages. Rests retain their own source columns.
"""
# All columns needed by either staff, including silent onsets.
QING = {
13:'224/0 262/2 309/4 329/5 356/6 397/8 434/10 460/11 480/12 517/14 541/15',
14:'577/0 616/2 641/3 668/4 706/6 738/8 764/9 789/10 814/11 832/12 873/14',
15:'225/0 263/2 287/3 309/4 337/6 362/7 397/8 433/10 459/11 480/12 496/13 518/14 541/15',
16:'575/0 621/2 656/3 656/4 681/5 711/7 711/6 738/8 779/10 824/12 856/14 878/15',
17:'223/0 264/2 281/3 301/4 320/5 339/6 363/7 396/8 417/9 438/10 460/11 480/12 500/13 521/14 541/15',
18:'577/0 598/1 621/2 640/3 662/4 681/5 701/6 725/7 754/8 779/9 805/10 827/11 850/12 871/13 879/14 901/15',
19:'224/0 245/1 267/2 287/3 310/4 331/5 350/6 374/7 397/8 417/9 438/10 460/11 480/12 500/13 521/14 541/15',
20:'577/0 623/2 655/3 663/4 706/6 741/8 781/10 801/11 819/12 842/13 867/14 890/15',
21:'225/0 264/2 287/3 311/4 330/5 350/6 355/6 398/8 439/10 460/11 484/12 502/13 521/14',
22:'578/0 620/2 663/4 704/6 727/7 748/8 770/9 792/10 813/11 835/12 876/14 898/15',
23:'224/0 261/2 285/3 308/4 327/5 350/6 395/8 430/10 455/11 482/12 500/13 521/14',
24:'580/0 625/2 674/4 719/6 763/8 810/10 854/12',
25:'223/0 266/2 289/3 309/4 352/6 393/8 433/10 465/12 506/14',
26:'558/0 600/2 626/3 651/4 690/6 716/7 737/8 759/9 779/10 805/11 828/12 872/14',
27:'224/0 266/2 290/3 309/4 330/5 350/6 395/8 437/10 457/11 481/12 500/13 523/14',
28:'578/0 618/2 639/3 662/4 700/6 728/8 756/10 781/11 806/12 826/13 852/14',
29:'235/0 269/2 290/3 309/4 330/5 356/6 393/8 429/10 450/11 474/12 494/13 520/14',
30:'566/0 604/2 624/3 650/4 674/5 691/6 718/7 741/8 786/10 807/11 829/12 849/13 872/14',
31:'222/0 249/2 266/3 281/4 304/6 332/8 358/10 377/11 395/12 411/13 429/14',
32:'465/0 489/2 502/3 518/4 534/5 549/6 569/8 600/10 628/12 648/14',
33:'683/0 713/2 730/3 749/4 779/6 797/8 823/10 840/11 860/12 887/14',
34:'222/0 264/2 293/3 319/4 350/6 378/7 403/8 428/9 457/10 464/11 488/12 511/13 528/14',
35:'576/0 621/2 662/4 685/5 705/6 737/7 756/8 801/10 824/11 850/12 873/13 892/14',
36:'224/0 266/2 287/3 310/4 353/6 389/8 412/10 459/11 482/12 522/14',
37:'581/0 610/2 654/4 676/5 701/6 737/8 779/10 807/11 831/12 851/13 873/14',
38:'224/0 267/2 286/3 310/4 331/5 355/6 401/8 439/10 460/11 483/12 505/13 533/14',
39:'578/0 618/2 641/3 663/4 701/6 738/8 779/10 813/11 831/12 852/13 873/14',
40:'224/0 266/2 284/3 302/4 335/6 374/8 407/10 433/11 453/12 489/14',
41:'537/0 574/2 602/3 626/4 667/6 692/7 717/8 744/9 767/10 796/11 820/12 845/13 871/14',
42:'224/0 267/2 293/3 326/4 362/6 386/7 414/8 439/9 462/10 497/11 523/12 552/13 576/14',
43:'626/0 662/2 683/3 698/4 730/6 766/8 784/9 813/10 835/12 852/13 879/14',
44:'229/0 265/2 289/3 313/4 351/6 389/8 426/10 466/12 498/15',
45:'534/0 554/1 577/2 599/3 622/4 644/5 677/6 701/7 725/8 744/9 765/10 787/11 812/12 832/13 861/14 884/15',
46:'225/0 271/1 314/2 356/3 401/4 444/5 485/6 527/7 569/8 613/9 654/10 696/11 740/12 783/13 823/14 867/15',
47:'222/0 246/1 271/2 293/3 320/4 343/5 368/6 394/7 419/8 445/9 467/10 492/11 517/12 540/13 563/14 586/15',
48:'627/0 671/2 677/3 704/4 747/6 767/8 795/10 840/12 856/13 876/14 896/15',
49:'220/0 258/2 283/3 303/4 340/6 377/8 398/9 419/10 460/12 481/13 501/14',
50:'554/0 598/2 622/3 646/4 684/6 706/7 726/8 751/9 773/10 796/11 824/12 851/14 875/15',
51:'221/0 263/2 286/3 304/4 324/5 348/6 390/8 432/10 449/11 479/12 496/13 524/14',
52:'559/0 603/2 646/4 690/6 735/8 778/10 823/12 868/14',
53:'221/0 264/2 288/3 307/4 348/6 394/8 434/10 454/11 478/12 516/14',
54:'568/0 607/2 641/3 656/4 693/6 725/7 745/8 768/9 798/10 837/12 877/14',
55:'222/0 264/2 287/3 307/4 329/5 353/6 385/8 428/10 449/11 478/12 495/13 517/14',
56:'570/0 609/2 640/3 655/4 698/6 730/8 751/10 777/11 819/12 844/13 873/14',
57:'237/0 270/2 294/3 314/4 336/5 361/6 399/8 437/10 457/11 478/12 499/13 523/14',
58:'568/0 607/2 627/3 650/4 674/5 699/6 726/7 749/8 790/10 813/11 830/12 853/13 876/14',
59:'230/0 269/2 288/3 310/4 349/6 383/8 402/9 442/11 444/10 479/12 499/13 523/14',
60:'573/0 614/2 640/3 651/4 675/5 704/6 727/7 752/8 791/10 832/12 871/14',
61:'227/0 267/2 287/3 310/4 350/6 394/8 438/10 457/11 477/12 510/14',
62:'564/0 607/2 639/3 653/4 690/6 729/8 751/9 792/10 820/11 829/12 853/13 877/14',
63:'229/0 271/2 286/3 312/4 335/5 356/6 395/8 437/10 458/11 481/12 499/13 523/14',
64:'573/0 613/2 639/3 655/4 694/6 732/8 753/10 782/11 807/12 831/13 862/14',
65:'236/0 271/2 294/3 314/4 336/5 358/6 399/8 438/10 458/11 480/12 501/13 523/14',
66:'567/0 606/2 624/3 650/4 674/5 702/6 728/7 750/8 790/10 812/11 831/12 851/13 877/14',
67:'229/0 269/2 286/3 309/4 350/6 386/8 405/9 435/10 466/12 502/14',
68:'553/0 597/2 622/3 645/4 690/6 715/7 740/8 778/10 821/12 885/15',
69:'222/0 253/2 276/3 298/4 324/6 347/7 370/8 391/9 412/10 434/11 458/12 475/13 497/14 519/15',
70:'553/0 585/2 609/3 631/4 662/6 685/7 711/8 734/9 755/10 778/11 802/12 825/13 847/14 871/15 893/15.5',
71:'230/0 267/2 286/3 310/4 351/6 371/7 389/8 418/9 439/10 461/11 484/12 506/13 523/14 548/15',
72:'580/0 614/2 637/3 657/4 699/6 719/7 737/8 759/9 781/10 802/11 822/12 845/13 869/14 891/15',
73:'227/0 257/2 279/3 294/4 312/5 331/6 356/7 378/8 397/9 417/10 438/11 461/12 480/13 497/14 518/15',
74:'552/0 575/2 595/3 618/4 644/5 666/6 690/7 717/8 742/9 766/10 790/11 812/12 834/13 855/14 884/15',
75:'230/0 268/2 294/3 317/4 355/6 379/7 397/8 420/9 441/10 462/11 486/12 510/13 530/14',
76:'579/0 609/2 624/3 642/4 676/6 699/8 729/10 750/11 767/12 788/13 806/14',
}

# Wo Ji De: the bass figures supply exact eighth-note columns. Exceptions
# below are read from the printed bass rhythm, including its rests.
WO_BASS = {n:[i/2 for i in range(8)] for n in range(13,85)}
for n in [13,25,29,33,37]:WO_BASS[n]=[0,1,2,3]
for n in [14,26,30,34,38]:WO_BASS[n]=[0,1,2,3,3.5]
for n in [18,22,42,43,46,47,51,55,66,67,71]:WO_BASS[n]=[0,.5,1,1.5,2,2.5,3,3.5,3.75]
for n in [19,23]:WO_BASS[n]=[0,.5,1,1.5,2,2.5,3]
WO_BASS[20]=[0,1,1.5,2,2.5,3,3.5]
WO_BASS[27]=[0,.5,1,1.5,2,3,3.5]
for n in [57,58,61,62]:WO_BASS[n]=[0,.5,1,1.25,1.5,1.75,2,2.5,3,3.25,3.5,3.75]
WO_BASS[59]=[0,.5,1,1.25,1.5,1.75,2,2.5,3,3.5,3.75]
WO_BASS[60]=[0,1,1.5,2,2.5,3,3.5]
WO_BASS[63]=[0,.5,1,1.5,1.75,2,2.5,3,3.5,3.75]
for n in [73,75,77,79,81,83]:WO_BASS[n]=[0,.5,.75,1,1.5,2,2.5,2.75,3,3.5]
for n in [74,78,82]:WO_BASS[n]=[0,.5,.75,1,1.5,2,2.5,2.75,3,3.5,3.75]
WO_BASS[84]=[0,.5,.75,1,1.5,2,2.5,3,3.5]

WO_BASS[83]=[0,.5,.75,1,1.5,2,2.5,3,3.25,3.5,3.75]
# Beam/stem intersections, checked against the page. Values use preview x.
WO_FALSE_BASS={22:[577.5],23:[852.2],42:[870.3],51:[859.8],58:[800.9],62:[800.9],66:[813.8],71:[392.6],74:[586.8],78:[586.8],84:[638.5]}

def sequence(*durations):
    b=0;out={}
    for d in durations:out[b]=d;b+=d
    assert abs(b-4)<1e-6,(durations,b)
    return out

MELODY_A=sequence(.5,.5,.25,.25,.25,.25,.5,.5,.25,.25,.25,.25)
MELODY_B=sequence(.5,.5,.5,.25,.25,.5,.5,.5,.25,.25)
WO_RIGHT={n:dict(MELODY_A) for n in [14,25,26,29,30,33,34,37,38,65,69,70]}
WO_RIGHT[13]=sequence(.5,.25,.25,.25,.25,.25,.25,.5,.5,.25,.25,.25,.25)
for n in [15,67,71]:WO_RIGHT[n]=sequence(.5,.5,.5,.25,.25,.5,.5,.5,.25,.25)
WO_RIGHT[15].pop(1) # Printed eighth rest.
for n in [27,31,35,39,66]:WO_RIGHT[n]=dict(MELODY_B)
for n in [16]:WO_RIGHT[n]={0:2}
for n in [17,21,73,74,77,78]:WO_RIGHT[n]=sequence(*([.5]*8))
for n in [18,22]:WO_RIGHT[n]=sequence(.5,.5,.5,.25,.25,.5,.5,.5,.25,.25)
for n in [19]:WO_RIGHT[n]={0:1.5,1.5:.25,1.75:.25,2:.5,2.5:.5,3:.5,3.5:.5}
WO_RIGHT[23]={0:1.5,1.5:.25,1.75:.25,2:.5,2.5:.25,2.75:.25,3:.5,3.5:.25,3.75:.25}
for n in [20,60]:WO_RIGHT[n]={0:.5,.5:1.5}
for n in [24,52,56,88]:WO_RIGHT[n]={0:4}
for n in [28,36]:WO_RIGHT[n]={0:2,.5:.5,1:.5,1.5:.5,2:.5,2.5:.5,3:.5,3.5:.5}
WO_RIGHT[32]={0:4,.5:.5,1:.5,1.5:.5,2:1,3:.25,3.25:.25,3.5:.25,3.75:.25}
for n in [40,72]:WO_RIGHT[n]={0:1.75,1.75:.25,**{2+i/4:.25 for i in range(8)}}
for n in [41,45,81,85,86]:WO_RIGHT[n]={0:2,2:.5,2.5:.5,3:.5,3.5:.5}
for n in [42,46,82]:WO_RIGHT[n]={0:2,2:.5,2.5:.5,3:.5,3.5:.25,3.75:.25}
for n in [43,47,79,83]:WO_RIGHT[n]=sequence(1.5,.25,.25,.5,.25,.25,.5,.25,.25)
WO_RIGHT[44]=sequence(2,1.5,.5)
for n in [48,49,51,53,57,58,61,62]:WO_RIGHT[n]=sequence(2,2)
WO_RIGHT[50]=sequence(1.5,.25,.25,.5,1,.5)
for n in [54,55]:WO_RIGHT[n]=sequence(1.5,.25,.25,.25,.25,.5,.5,.5)
WO_RIGHT[59]=sequence(1,1,1.5,.5)
WO_RIGHT[63]=sequence(1,.5,.5,1,.5,.25,.25)
WO_RIGHT[64]={0:2,**{2.25+i/4:.25 for i in range(7)}}
WO_RIGHT[68]=sequence(.5,1,.25,.25,.25,.25,.5,.75,.25)
WO_RIGHT[75]=sequence(.25,.75,.75,.25,.5,.25,.25,.5,.25,.25)
for n in [76,80,84]:WO_RIGHT[n]=sequence(*([.5]*8))
WO_RIGHT[87]=sequence(.5,1,.5,.5,.25,.25,.5,.5)


def clusters(gs,p,tolerance=6):
    result=[]
    for g in sorted(gs,key=lambda g:g['x']):
        x=g['x']/p['width']*1050
        if result and x-result[-1][0]<tolerance:
            result[-1][1].append(g)
        else:result.append((x,[g]))
    return result


def wo(pages):
    corrections=[];number=0
    for p in pages:
      for s in p['systems']:
       for m in s['measures']:
        number+=1
        if not 13<=number<=88:continue
        r,l=[st['index'] for st in s['staves']]
        gs=m['groups'];excluded=[]
        for g in gs[:]:
            x=g['x']/p['width']*1050
            if g['staff']==l and any(abs(x-v)<2 for v in WO_FALSE_BASS.get(number,[])):
                excluded.extend(g['notes']);gs.remove(g)
        bass=[g for g in gs if g['staff']==l and g['notes'] and (number not in range(57,64) or all(n['kind']=='filled' for n in g['notes']))]
        cols=clusters(bass,p)
        if number<=84:
            beats=WO_BASS[number]
            assert len(cols)==len(beats),(number,len(cols),len(beats))
        else:
            beats=[0,2] if number<=87 else [0]
            assert len(cols)==len(beats),(number,len(cols),len(beats))
        anchors=list(zip([c[0] for c in cols],beats))

        # Use the literal bass-note durations, not a stretched total length.
        for i,((x,gg),b) in enumerate(zip(cols,beats)):
            duration=(beats+[4])[i+1]-b
            if number in (20,27) and b==(0 if number==20 else 2):duration=.5
            for g in gg:g.update(reviewedBeat=b,duration=duration)
        def x_at(b):
            for (x,a),(y,c) in zip(anchors,anchors[1:]):
                if a<=b<=c:return x+(y-x)*(b-a)/(c-a)
            if b<=anchors[0][1]:return anchors[0][0]
            if len(anchors)>1:
                (x,a),(y,c)=anchors[-2:];return y+(y-x)*(b-c)/(c-a)
            return anchors[0][0]+(m['right']/p['width']*1050-anchors[0][0])*b/4
        expected=WO_RIGHT[number]
        for g in gs[:]:
            if not g['notes']:
                # Candidate rest templates often duplicate note stems. Silent
                # spans are specified by the literal voice timelines above.
                gs.remove(g);continue
            if g in bass:continue
            x=g['x']/p['width']*1050
            if g['staff']==l:
                b=min([0,2],key=lambda b:abs(x-x_at(b))) if number!=60 else 0
                g.update(reviewedBeat=b,duration=4 if number==60 else 2)
            else:
                b=min(expected,key=lambda b:abs(x-x_at(b)))
                g.update(reviewedBeat=b,duration=expected[b])
                # Independent written long tones alongside a moving voice.
                if any(n['kind'] in ('hollow','whole') for n in g['notes']):
                    if number in [17,21,73,74,77,78]:g['duration']=2
                    if number in [76,84]:g['duration']=4;g['reviewedBeat']=0
                    if number==80:g['duration']=2;g['reviewedBeat']=0
                    if number in [18,22]:g['duration']=2;g['reviewedBeat']=0
                    if number==19 and g['y']<s['staves'][0]['center']:g['duration']=3;g['reviewedBeat']=0
                    if number==23 and g['y']<s['staves'][0]['center']:g['duration']=3;g['reviewedBeat']=0
                if number in (28,36) and b==2:g['duration']=.5
                g['duration']=min(g['duration'],4-g['reviewedBeat'])
        m['sourcePulseAligned']=True
        corrections.append(dict(measure=number,reason='按原谱左手音型确定拍点，再对齐右手独立声部；音高和漏音仍待复核。',bassOnsets=beats,excludedCandidates=excluded))
    return corrections

# Refined from the enlarged crop: the sixteenth notes in the lower staff
# occur between the first four right-hand eighth-note chords.
QING[16]='571/0 606/2 629/3 651/4 673/5 695/6 717/7 739/8 762/9 783/10 805/11 827/12 850/14 879/15'
QING[59]='230/0 269/2 288/3 310/4 349/6 383/8 402/9 444/10 463/11 479/12 499/13 523/14'


def align_columns(actual,expected):
    """Monotone match of detected columns to the read source columns.

    Coordinates in the small inspection preview are approximate. Missing
    heads and spurious symbols must not shift all following rhythmic columns.
    """
    import numpy as np
    n,k=len(actual),len(expected)
    cost=np.full((n+1,k+1),float('inf'));cost[0,0]=0;back={}
    for i in range(n+1):
      for j in range(k+1):
        for a,b,c,op in [(i+1,j,4,'skip-head'),(i,j+1,4,'missing-head'),(i+1,j+1,abs(actual[i]-expected[j][0])/4 if i<n and j<k else 0,'match')]:
            if a>n or b>k:continue
            if cost[i,j]+c<cost[a,b]:cost[a,b]=cost[i,j]+c;back[a,b]=(i,j,op)
    pairs={};i,j=n,k
    while i or j:
        a,b,op=back[i,j]
        if op=='match':pairs[a]=b
        i,j=a,b
    return pairs


def qing(pages):
    out=[];number=0
    for p in pages:
      for s in p['systems']:
       for m in s['measures']:
        number+=1
        if number not in QING:continue
        expected=[(float(z.split('/')[0]),float(z.split('/')[1])/4) for z in QING[number].split()]
        assert all(a[0]<b[0] and a[1]<=b[1] for a,b in zip(expected,expected[1:])),number
        # Whole/half rest template hits here are beam intersections. These
        # source bars have no whole/half rests; the last full-bar rest is 77.
        gs=[g for g in m['groups'] if g['notes'] or g.get('symbol') not in ('\ue4e3','\ue4e4')]
        cols=clusters(gs,p,10);pairs=align_columns([x for x,_ in cols],expected)
        uncertain=[]
        for i,(x,gg) in enumerate(cols):
            j=pairs.get(i)
            if j is None:
                j=min(range(len(expected)),key=lambda j:abs(expected[j][0]-x))
                uncertain.append(dict(x=round(x,2),beat=expected[j][1],kind='unmatched-candidate-column'))
            b=expected[j][1]
            for g in gg:g['reviewedBeat']=b
        for g in gs:
            # A shorter following attack bounds the inferred stem duration;
            # genuine rests and longer held voices are never filled by pedal.
            voice=lambda h:(h['staff'],h['direction'] if h['staff']%2==0 else 'bass')
            after=[h['reviewedBeat'] for h in gs if h['reviewedBeat']>g['reviewedBeat'] and voice(h)==voice(g)]
            end=min(after,default=4)
            g['duration']=min(g['duration'],end-g['reviewedBeat'],4-g['reviewedBeat'])
            if number==24 and g['notes'] and g['staff']==s['staves'][0]['index']:
                # The lower chord voice has six eighths then a quarter; the
                # scanner counted the crossing upper stem as another beam.
                g['duration']=.5 if g['reviewedBeat']<3 else 1
        m['groups']=gs;m['sourcePulseAligned']=True
        out.append(dict(measure=number,reason='原谱拍点标注对齐扫描候选；不再对整小节做非等拍缩放。候选音高、漏音和部分时值仍待逐音复核。',previewWidth=1050,sourceBeatColumns=expected,uncertainCandidates=uncertain))
    return out


def apply(sid,pages):
    if sid=='wo-ji-de':return wo(pages)
    if sid=='qing-tian':return qing(pages)
    return []


def performance_reading(sid,data,report):
    # (source bar, source beat, destination bar, destination beat), counted
    # from one. Only the matching printed pitches are tied, never all notes.
    ties=[]
    if sid=='wo-ji-de':
        ties += [(a,b,a+1,0) for a,b in [(15,3.75),(17,3.5),(19,3),(21,3.5),(23,3.75),(41,3.5),(43,3.75),(45,3.5),(47,3.75),(59,3.5),(67,3.75),(73,3.5),(75,3.75),(77,3.5),(79,3.75),(81,3.5),(83,3.75)]]
        for n in [43,47,79,83]:ties += [(n,0,n,1.5),(n,2.75,n,3)]
        for n in [54,55]:ties.append((n,2.5,n,3))
        ties += [(63,2,63,3),(68,2.5,68,3),(75,.25,75,1),(75,2.75,75,3),(87,2.75,87,3)]
    else:
        ties += [(a,b,a+1,0) for a,b in [(16,3.75),(19,3.75),(21,3.5),(23,3.5),(44,3.75),(45,3.75),(46,3.75),(47,3.75),(51,3.5),(68,3.75),(71,3.75),(74,3.75)]]
        ties += [(n,1.5,n,2) for n in [28,30,36,38,56,58,64,66]]
        ties += [(18,1.75,18,2)]
    annotations=[]
    for ma,ba,mb,bb in ties:
        a_time=data['measures'][ma-1]['start']+ba;b_time=data['measures'][mb-1]['start']+bb
        aa=[e for e in data['events'] if e['hand']=='R' and abs(e['beat']-a_time)<1e-7]
        bs=[e for e in data['events'] if e['hand']=='R' and abs(e['beat']-b_time)<1e-7]
        for b in bs:
            if 'tieFrom' in b:continue
            candidates=[a for a in aa if a['midi']==b['midi'] and 'tieTo' not in a]
            if not candidates:continue
            a=candidates[0];a['duration']=b_time-a_time;a['tieTo']=b['id'];b['tieFrom']=a['id'];b.pop('soundDuration',None)
            annotations.append(dict(fromId=a['id'],toId=b['id'],sourceMeasure=ma,targetMeasure=mb,midi=a['midi']))
    for e in data['events']:
        if 'tieFrom' in e:continue
        tail=e;seen=set()
        while 'tieTo' in tail:
            assert tail['id'] not in seen;seen.add(tail['id']);tail=data['events'][tail['tieTo']]
        e['soundDuration']=tail['beat']+tail['duration']-e['beat']
    count=sum(bool(m.get('sourcePulseAligned')) for m in data['measures'])
    data['sourcePulseAlignedMeasures']=count
    data['meterLabel']='4/4 · 后段拍点已对齐'
    data['performanceNote']=f'前 12 小节按原谱重写；后段 {count} 小节已按谱面拍点对齐，修复符杠与谱线误识别，不再逐小节强行压缩速度。仍是未校对完整音高、漏音和实际听感的草稿；部分候选时值仍待复核。'
    report['sourcePulseAlignedMeasures']=count
    report['onsetAlignmentUncertainties']=[dict(measure=c['measure'],**v) for c in report['visuallyCheckedCorrections'] for v in c.get('uncertainCandidates',[])]
    report['sourceTieReadings']=annotations
    report['method']='visual-opening-reading + raster-candidates-with-source-pulse-alignment'
    report['limitations']=['前 12 小节直接读谱；后段按原谱拍点对齐，消除非等拍的小节缩放。','扫描音高、漏音及部分音符时值仍待逐音复核；拍点对齐不代表整谱准确。','尚未完成实际听音或实体 MIDI 键盘验证。']
