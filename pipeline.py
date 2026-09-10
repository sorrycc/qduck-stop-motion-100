#!/usr/bin/env python3
"""Assemble image_gen sheets with ImageMagick/FFmpeg. Pillow is read-only validation."""
import hashlib, html, json, subprocess, sys, time
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parent
PLANS=json.loads((ROOT/"concepts.json").read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write_json(path,value):
    temp=path.with_suffix(path.suffix+".tmp")
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n")
    temp.replace(path)
def case_dir(p): return ROOT/"cases"/(p["id"]+"-"+p["slug"])
def inspect_case(p):
    case=case_dir(p); sheet=case/"storyboard.png"; gif=case/"animation.gif"
    paths=sorted((case/"frames").glob("frame_*.png"))
    assert len(paths)==36, f"{p['id']}: {len(paths)} PNG frames"
    with Image.open(sheet) as im: sw,sh=im.size
    delays=[]; gh=[]
    with Image.open(gif) as im:
        count=im.n_frames; size=im.size; loop=im.info.get("loop")
        for i in range(count):
            im.seek(i);delays.append(im.info.get("duration",0))
            gh.append(hashlib.sha256(im.convert("RGB").tobytes()).hexdigest())
    assert count==36, f"{p['id']}: GIF has {count} frames"
    assert sum(delays)==3000, f"{p['id']}: duration {sum(delays)}"
    assert loop==0, f"{p['id']}: non-infinite loop"
    frames=[]
    for i,path in enumerate(paths):
        with Image.open(path) as im:
            assert im.size==size
            pixel_hash=hashlib.sha256(im.convert("RGB").tobytes()).hexdigest()
        frames.append({"frame":i+1,"file":str(path.relative_to(case)),"duration_ms":delays[i],"sha256":sha(path),"pixel_sha256":pixel_hash})
    unique=len({f["pixel_sha256"] for f in frames})
    assert unique>=18, f"{p['id']}: too few distinct source poses ({unique})"
    return {"id":p["id"],"title":p["title"],"technical_status":"passed","sheet_size":[sw,sh],"grid":[6,6],"frame_size":list(size),"png_frames":36,"unique_png_frames":unique,"gif_frames":count,"unique_gif_frames":len(set(gh)),"gif_duration_ms":sum(delays),"gif_loop":0,"gif_bytes":gif.stat().st_size,"sheet_sha256":sha(sheet),"gif_sha256":sha(gif),"frames":frames,"checked_at":time.strftime("%Y-%m-%dT%H:%M:%S%z")}
def build(p):
    case=case_dir(p); sheet=case/"storyboard.png"
    with Image.open(sheet) as im: w,h=im.size
    assert w==h and w%6==0,f"{p['id']}: non-square or indivisible sheet {w}x{h}"
    tile=w//6
    subprocess.run(["magick",str(sheet),"-crop",f"{tile}x{tile}","+repage","-scene","1",str(case/"frames"/"frame_%02d.png")],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    result=subprocess.run(["ffmpeg","-hide_banner","-loglevel","warning","-y","-framerate","12","-start_number","1","-i",str(case/"frames"/"frame_%02d.png"),"-filter_complex","split[a][b];[a]palettegen=max_colors=256:stats_mode=full[p];[b][p]paletteuse=dither=sierra2_4a","-frames:v","36","-loop","0","-final_delay","8",str(case/"animation.gif")],check=True,capture_output=True,text=True)
    (case/"qa"/"encode.log").write_text(result.stderr)
    audit=inspect_case(p);write_json(case/"audit.json",audit)
    print(json.dumps({"built":p["id"],"title":p["title"],"unique_frames":audit["unique_png_frames"],"duration_ms":audit["gif_duration_ms"]},ensure_ascii=False),flush=True)
def collect():
    reviews_path=ROOT/"qa"/"visual-reviews.json"
    reviews=json.loads(reviews_path.read_text()) if reviews_path.exists() else {}
    entries=[]
    for p in PLANS:
        case=case_dir(p); audit_path=case/"audit.json"
        generated=(case/"generation.json").exists() and (case/"storyboard.png").exists()
        audit=json.loads(audit_path.read_text()) if audit_path.exists() else None
        reviewed=reviews.get(p["id"],{}).get("status")=="approved"
        entries.append({"id":p["id"],"slug":p["slug"],"title":p["title"],"style":p["style"],"generated":generated,"technical_passed":bool(audit),"visual_approved":reviewed,"complete":bool(audit) and reviewed,"folder":str(case.relative_to(ROOT)), "audit":str(audit_path.relative_to(ROOT)) if audit else None})
    summary={"target":100,"generated":sum(e["generated"] for e in entries),"encoded_verified":sum(e["technical_passed"] for e in entries),"visual_approved":sum(e["visual_approved"] for e in entries),"complete":sum(e["complete"] for e in entries),"updated_at":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"entries":entries}
    write_json(ROOT/"manifest.json",summary)
    cards=[]
    for e in entries:
        if not e["technical_passed"]:continue
        folder=e["folder"];caption=html.escape(e["id"]+" · "+e["title"])
        cards.append(f'<article data-search="{html.escape(e["id"]+" "+e["title"]+" "+e["style"])}"><a class="visual" href="{folder}/animation.gif"><img loading="lazy" width="209" height="209" src="{folder}/animation.gif" alt="{caption}"></a><h2>{caption}</h2><p>{html.escape(e["style"])}</p><nav><a href="{folder}/storyboard.png">36 帧大图</a><a href="{folder}/animation.gif">GIF</a><a href="{folder}/prompt.txt">提示词</a></nav></article>')
    page='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>100 段动作与创意</title><style>*{box-sizing:border-box}body{margin:0;background:#f4f1eb;color:#26251e;font:15px system-ui,sans-serif}header{max-width:1240px;margin:50px auto 30px;padding:0 24px}h1{font-size:40px;letter-spacing:-1px;margin-bottom:12px}header p{color:#68645c;line-height:1.7}input{padding:14px 18px;width:100%;max-width:520px;border:1px solid #cbc5b8;border-radius:12px;background:white;font:inherit}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:18px;max-width:1240px;margin:auto;padding:0 24px 64px}article{border-radius:16px;overflow:hidden;background:#fff;box-shadow:0 3px 14px #27210c0a;padding-bottom:18px}.visual{display:flex;align-items:center;justify-content:center;background:#ece9e2;min-height:245px}img{width:209px;height:209px;object-fit:contain}h2{font-size:18px;margin:18px 18px 10px}article p{font-size:12px;color:#756e62;line-height:1.5;margin:0 18px;min-height:54px}nav{display:flex;gap:14px;margin:16px 18px 0}a{color:#776024;text-decoration:none}a:hover{text-decoration:underline}[hidden]{display:none}</style><header><h1>100 段动作与创意</h1><p>同一个黄色表情，100 种视觉风格与动作。每段 36 帧、3 秒、循环播放。<br>以动作表现为主，带一点故事性。点击大图查看完整分镜。</p><input id="search" aria-label="搜索编号、风格或标题" placeholder="搜索编号、风格或标题"></header><main>'+''.join(cards)+'</main><script>const search=document.querySelector("#search");function filter(){const q=search.value.toLowerCase();document.querySelectorAll("article").forEach(a=>a.hidden=!a.dataset.search.toLowerCase().includes(q))}search.addEventListener("input",filter);window.addEventListener("pageshow",filter);filter()</script></html>'
    (ROOT/"index.html").write_text(page)
    print(json.dumps({k:v for k,v in summary.items() if k!="entries"},ensure_ascii=False),flush=True)
    return summary
def main():
    mode=sys.argv[1] if len(sys.argv)>1 else "status"
    if mode in ["build-pending","build-all"]:
        for p in PLANS:
            case=case_dir(p)
            if not (case/"generation.json").exists():continue
            if mode=="build-pending" and (case/"audit.json").exists():continue
            try:build(p)
            except Exception as exc:
                write_json(case/"qa"/"build-error.json",{"id":p["id"],"error":str(exc)})
                print(json.dumps({"build_error":p["id"],"error":str(exc)}),flush=True)
    elif mode=="verify-all":
        for p in PLANS:
            case=case_dir(p)
            if not (case/"audit.json").exists():continue
            audit=inspect_case(p);write_json(case/"audit.json",audit)
        print("Read back every available sheet, PNG and GIF",flush=True)
    collect()
if __name__=="__main__":main()

