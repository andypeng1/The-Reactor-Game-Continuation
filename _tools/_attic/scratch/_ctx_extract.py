import json, sys
path = sys.argv[1]; a = sys.argv[2]; b = sys.argv[3]
with open(path, 'r', encoding='utf-8') as f:
    for line in f:
        line=line.strip()
        if not line: continue
        try: obj=json.loads(line)
        except Exception: continue
        ts = obj.get('timestamp','')
        if not (a <= ts <= b): continue
        msg = obj.get('message') or {}
        content = msg.get('content')
        role = msg.get('role')
        if isinstance(content, list):
            for c in content:
                if not isinstance(c, dict): continue
                t = c.get('type')
                if t == 'tool_use':
                    print(f"[{ts}] TOOL {c.get('name')}")
                    print(json.dumps(c.get('input'), ensure_ascii=False)[:2200])
                elif t == 'tool_result':
                    cc = c.get('content')
                    s = cc if isinstance(cc,str) else json.dumps(cc, ensure_ascii=False)
                    print(f"[{ts}] RESULT {s[:900]}")
                elif t == 'text':
                    print(f"[{ts}] TEXT {c.get('text','')[:900]}")
        elif isinstance(content, str):
            print(f"[{ts}] {role} {content[:900]}")
