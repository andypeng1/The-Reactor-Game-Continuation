"""Refresh the TRG wiki snapshot (reactor.fandom.com) -- stdlib only.

Why this exists next to the user's own D:/RobloxAssetsDownloader/TRGWikiPull.py
rather than replacing it: that one imports `requests`, which is not installed for
/c/Python314/python, and its walk is `apnamespace=0` alone, which is NOT "all pages".
On 2026-09-22/23 the wiki moved article text into the Category namespace
(`Shifts` -> `Category:Shifts`, byte-identical; `Reactor Components` rewritten), so a
faithful ns0-only refresh goes 77 -> 75 and drops the shift-mechanics article with no
error at all.  The user's copy is theirs and stays untouched; this one pulls
ns 0 UNION ns 14, uses urllib.request, and DIFFS the result against the file it is
about to overwrite so a silently-dropped article is a loud line, not a mystery.

Every printed line is ASCII on purpose: the console codec here is GBK and one stray
bullet kills the run (memory: windows-console-codec).  Titles go through ascii_safe().
"""

import argparse
import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://reactor.fandom.com/api.php"
UA = "TRGWikiScraper/1.0 (snapshot refresh; python-urllib)"
NAMESPACES = [0, 14]  # article + Category -- see the module docstring
BATCH_SIZE = 50
REQUEST_DELAY = 0.4


def ascii_safe(text):
    """Never let a title reach a GBK console unescaped."""
    return str(text).encode("ascii", "backslashreplace").decode("ascii")


def api_get(params):
    query = dict(params)
    query["format"] = "json"
    query["formatversion"] = "2"
    url = API + "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == 2:
                raise
            print("  retry %d after %s" % (attempt + 1, type(exc).__name__), flush=True)
            time.sleep(2.0)
    if "error" in data:
        raise RuntimeError("API error: %s" % data["error"])
    return data


def fetch_titles(namespace):
    """allpages walk for one namespace, following the continue token."""
    titles = []
    params = {
        "action": "query",
        "list": "allpages",
        "apnamespace": namespace,
        "aplimit": "max",
        "apfilterredir": "nonredirects",
    }
    while True:
        data = api_get(params)
        for page in data.get("query", {}).get("allpages", []):
            titles.append(page["title"])
        cont = data.get("continue")
        if not cont:
            break
        params.update(cont)
    return titles


def fetch_contents(titles):
    """Batch the wikitext.  Same response shape the user's script produced, so the
    JSON stays drop-in compatible with anything already reading it."""
    results = {}
    total = len(titles)
    for start in range(0, total, BATCH_SIZE):
        batch = titles[start:start + BATCH_SIZE]
        params = {
            "action": "query",
            "titles": "|".join(batch),
            "prop": "revisions",
            "rvprop": "content|timestamp",
            "rvslots": "main",
        }
        try:
            data = api_get(params)
        except Exception as exc:  # noqa: BLE001 - a dropped batch must be loud, not fatal
            print("  BATCH FAILED at %d: %s" % (start, ascii_safe(exc)), flush=True)
            continue
        for page in data.get("query", {}).get("pages", []):
            title = page.get("title", "")
            if "missing" in page:
                continue
            revisions = page.get("revisions", [])
            if not revisions:
                results[title] = {"content": None, "timestamp": None}
                continue
            rev = revisions[0]
            results[title] = {
                "content": rev.get("slots", {}).get("main", {}).get("content", ""),
                "timestamp": rev.get("timestamp", ""),
            }
        print("  %d / %d" % (min(start + BATCH_SIZE, total), total), flush=True)
        time.sleep(REQUEST_DELAY)
    return results


def load_previous(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh).get("pages", {})
    except Exception as exc:  # noqa: BLE001 - a corrupt old file must not stop the pull
        print("previous file unreadable (%s); skipping the diff" % ascii_safe(exc))
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="D:/RobloxAssetsDownloader/TRGWiki.json")
    ap.add_argument("--backup-suffix", default=time.strftime("%y%m%d"))
    ap.add_argument("--no-write", action="store_true", help="dry run: pull and diff only")
    args = ap.parse_args()

    before = load_previous(args.out)
    print("previous snapshot: %d pages" % len(before))

    titles = []
    per_ns = {}
    for ns in NAMESPACES:
        got = fetch_titles(ns)
        per_ns[ns] = len(got)
        titles.extend(got)
        print("ns %d: %d titles" % (ns, len(got)))
    # Overlapping titles across namespaces are impossible, but a duplicate would waste a
    # slot in a batch and make the count lie, so de-duplicate while keeping order.
    titles = list(dict.fromkeys(titles))
    print("union: %d titles" % len(titles))

    pages = fetch_contents(titles)
    print("fetched content for %d pages" % len(pages))

    added = sorted(set(pages) - set(before))
    removed = sorted(set(before) - set(pages))
    print("added: %d" % len(added))
    for title in added:
        print("  + " + ascii_safe(title))
    print("removed: %d" % len(removed))
    for title in removed:
        print("  - " + ascii_safe(title))

    if args.no_write:
        print("--no-write: nothing saved")
        return 0

    if os.path.exists(args.out) and before:
        backup = "%s.%s.bak" % (args.out, args.backup_suffix)
        if not os.path.exists(backup):
            shutil.copy2(args.out, backup)
            print("backed up -> %s" % ascii_safe(backup))
        else:
            print("backup already exists, left alone -> %s" % ascii_safe(backup))

    output = {
        "wiki": "The Reactor Game Wiki",
        "source": "https://reactor.fandom.com/wiki/The_Reactor_Game_Wiki",
        # api / namespaces / pulled are NOT written by the user's TRGWikiPull.py, but
        # the 2026-09-30 snapshot carried them, so something upstream expects them and
        # this refresh must not be the step that drops them (CLAUDE.md 1.4 #2). The
        # namespaces field is the only record of the ns 0 UNION ns 14 decision -- i.e.
        # of the trap described in the module docstring -- so losing it would make the
        # next reader unable to tell a faithful pull from an ns0-only one.
        "api": API,
        "namespaces": list(NAMESPACES),
        "pulled": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_pages": len(pages),
        "pages": pages,
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(output, fh, ensure_ascii=False, indent=2)
    print("wrote %s (%d pages)" % (ascii_safe(args.out), len(pages)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
