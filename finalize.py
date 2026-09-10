#!/usr/bin/env python3
"""Verify the whole delivered set and create a 100-case overview."""
import hashlib, json, subprocess, time
from html.parser import HTMLParser
from pathlib import Path
import pipeline as p

root=Path(__file__).resolve().parent
expected=[f'{n:03d}' for n in range(1,101)]
assert [x['id'] for x in p.PLANS]==expected
reviews=json.loads((root/'qa/visual-reviews.json').read_text())
audits=[]
for plan in p.PLANS:
    case=p.case_dir(plan)
    assert reviews.get(plan['id'],{}).get('status')=='approved',plan['id']
    assert (case/'generation.json').is_file(),plan['id']
    assert (case/'prompt.txt').read_text().strip()==plan['prompt'].strip()
    audit=p.inspect_case(plan)
    assert audit['sheet_size'][0]==audit['sheet_size'][1]
    assert audit['sheet_size'][0]==6*audit['frame_size'][0]
    assert audit['sheet_size'][1]==6*audit['frame_size'][1]
    p.write_json(case/'audit.json',audit)
    audits.append(audit)
assert len(list((root/'cases').glob('*/storyboard.png')))==100
assert len(list((root/'cases').glob('*/animation.gif')))==100
assert len(list((root/'cases').glob('*/frames/frame_*.png')))==3600
assert len({a['sheet_sha256'] for a in audits})==100
assert len({a['gif_sha256'] for a in audits})==100
summary=p.collect()
assert all(summary[k]==100 for k in ['generated','encoded_verified','visual_approved','complete'])

class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.cards=0
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='article':self.cards+=1
        if tag=='a':self.links.append(attrs['href'])
        if tag=='img':self.links.append(attrs['src'])
page=Links();page.feed((root/'index.html').read_text())
assert page.cards==100
assert all((root/link).is_file() for link in page.links)

command=['magick','montage']
for plan in p.PLANS:
    command+=['-label',plan['id'],str(p.case_dir(plan)/'frames/frame_19.png')]
command+=['-font','Helvetica','-pointsize','17','-fill','#302c25','-background','#f4f1eb','-gravity','center','-tile','10x10','-geometry','209x209+6+6',str(root/'overview-100.jpg')]
subprocess.run(command,check=True)
report={'status':'passed','additional_cases':100,'storyboards':100,'png_frames':3600,'gifs':100,'frames_per_gif':36,'duration_ms_each':3000,'loop':'infinite','unique_storyboard_hashes':100,'unique_gif_hashes':100,'visual_reviews':100,'gallery_cards':page.cards,'local_gallery_links_checked':len(page.links),'sheet_dimensions':sorted({tuple(a['sheet_size']) for a in audits}),'frame_dimensions':sorted({tuple(a['frame_size']) for a in audits}),'gif_total_bytes':sum(a['gif_bytes'] for a in audits),'checked_at':time.strftime('%Y-%m-%dT%H:%M:%S%z')}
p.write_json(root/'qa/final-audit.json',report)
(root/'COMPLETION.md').write_text('# 100 套动画交付\n\n新增 100 套，原版未计入。100 张 6×6 分镜图、3600 张逐帧 PNG、100 个 GIF。每个 GIF 均为 36 帧、3 秒、无限循环。\n\n打开 index.html 浏览、搜索并查看动画；overview-100.jpg 汇总全部编号。每套的 prompt.txt 保存实际生成提示词，audit.json 保存尺寸、时长、哈希和逐帧记录。\n\n每张分镜均逐套检查过动作和角色结构。生成画面保留定格动画的姿态、光线和材质变化；循环首尾并非逐像素一致。\n\n使用内置 image_gen 生成，ImageMagick 拆帧，FFmpeg 编码。原生分镜尺寸和 GIF 尺寸详见 qa/final-audit.json，未进行虚假高分辨率放大。\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
