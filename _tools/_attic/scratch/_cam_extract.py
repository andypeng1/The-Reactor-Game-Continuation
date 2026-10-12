import json, sys, glob, os
path = sys.argv[1]
seen = []
with open(path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line: continue
        try: obj = json.loads(line)
        except Exception: continue
        msg = obj.get('message') or {}
        content = msg.get('content')
        if not isinstance(content, list): continue
        for c in content:
            if not isinstance(c, dict): continue
            if c.get('type') != 'tool_use': continue
            name = c.get('name','')
            if 'screen_capture' not in name and 'capture_screenshot' not in name: continue
            inp = c.get('input') or {}
            seen.append((obj.get('timestamp',''), name.split('__')[-1],
                         inp.get('capture_id'),
                         inp.get('camera_position'), inp.get('look_at_position')))
for ts, name, cid, cam, look in seen:
    print(f"{ts} {name} id={cid} cam={cam} look={look}")
print(f"--- {len(seen)} capture calls ---")
