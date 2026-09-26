# -*- coding: utf-8 -*-
"""Map scene asset ids -> local files in the user's asset pack.

Two halves, joined here:
  scene_assets.tsv  - produced by the Luau snippet in scene_dump.lua, run in Studio
  pack ids          - parsed from filenames in TRG Sounds & Images pack

No network, no credentials. The upload step (blocked on user auth) consumes this.
"""
import os
import re
import sys
import collections

PACK = r"D:\rblxTRGproject\TRG Sounds & Images pack"
SCENE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scene_assets.tsv")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "asset_map.tsv")

ID_RE = re.compile(r"_(\d+)\.\w+$")
IMG = {".png", ".jpg", ".jpeg", ".bmp", ".tga"}
SND = {".ogg", ".mp3", ".wav", ".flac"}


def pack_index():
    """id -> (relpath, ext). Filenames embed the original asset id last."""
    found, noid = {}, []
    for dirpath, _dirs, files in os.walk(PACK):
        for f in files:
            m = ID_RE.search(f)
            rel = os.path.relpath(os.path.join(dirpath, f), PACK)
            if not m:
                noid.append(rel)
                continue
            aid = m.group(1)
            if aid in found:
                found[aid] = found[aid] + "|" + rel
            else:
                found[aid] = rel
    return found, noid


def main():
    found, noid = pack_index()
    exts = collections.Counter(os.path.splitext(v.split("|")[0])[1].lower()
                               for v in found.values())
    print("PACK: %d distinct ids, %d files with no id in name"
          % (len(found), len(noid)))
    print("      by ext: " + "  ".join("%s=%d" % kv for kv in exts.most_common()))
    print("      img=%d snd=%d other=%d"
          % (sum(n for e, n in exts.items() if e in IMG),
             sum(n for e, n in exts.items() if e in SND),
             sum(n for e, n in exts.items() if e not in IMG and e not in SND)))
    if noid:
        print("      no-id files:", noid[:12])

    if not os.path.exists(SCENE):
        print("\nscene_assets.tsv not present -- run scene_dump.lua in Studio,"
              " paste its output into that file, then re-run.")
        return 1

    rows, hit, miss = [], 0, 0
    for line in open(SCENE, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        kind, aid, n = line.split("\t")
        local = found.get(aid)
        if local:
            hit += 1
        else:
            miss += 1
        rows.append((int(n), kind, aid, local or ""))

    rows.sort(key=lambda r: (-r[0], r[2]))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("# count\tkind\tscene_asset_id\tlocal_file\n")
        for n, kind, aid, local in rows:
            fh.write("%d\t%s\t%s\t%s\n" % (n, kind, aid, local))

    print("\nSCENE: %d distinct ids | local copy %d | no local copy %d"
          % (len(rows), hit, miss))
    print("wrote %s\n" % OUT)
    print("-- repointable, texture/visual family, by scene usage --")
    for n, kind, aid, local in rows:
        if local and kind != "SND":
            print("  %5d  %-11s %-16s %s" % (n, kind, aid, local))
    return 0


if __name__ == "__main__":
    sys.exit(main())
