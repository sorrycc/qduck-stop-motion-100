#!/usr/bin/env python3
import json,time
import pipeline as p
seen={};last=-1
while True:
    for plan in p.PLANS:
        case=p.case_dir(plan);sheet=case/"storyboard.png"
        if not (case/"generation.json").exists() or not sheet.exists():continue
        stamp=sheet.stat().st_mtime_ns
        if (case/"audit.json").exists() or seen.get(plan["id"])==stamp:continue
        seen[plan["id"]]=stamp
        try:p.build(plan)
        except Exception as exc:
            p.write_json(case/"qa"/"build-error.json",{"id":plan["id"],"error":str(exc)})
            print(json.dumps({"build_error":plan["id"],"error":str(exc)}),flush=True)
    count=sum((p.case_dir(x)/"audit.json").exists() for x in p.PLANS)
    if count!=last:
        p.collect();last=count
    if count==100:break
    time.sleep(10)

