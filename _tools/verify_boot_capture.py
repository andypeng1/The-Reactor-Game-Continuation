#!/usr/bin/env python3
"""Authoritative readability check for the boot-screen capture.

TRG_original_boot.luau promises, in its header, that every data line it writes is
byte-compatible with what the seven archived analysers already parse.  The only
honest way to test that promise is with THEIR pattern and not with a re-typed one,
so this script reads the pattern out of the readers' own source at run time and
fails if any of them has stopped containing it.  A paraphrase kept here would go on
passing after the readers changed -- which is exactly the failure this exists to
catch.

It also checks that all seven agree.  "All seven compile the same pattern" was a
claim made from memory once; this turns it into a fact that has to keep being true.

A capture line is acceptable if it is either

    * a comment (starts with '#'), which every reader skips, or
    * a data line that the readers' anchored pattern matches exactly.

Anything else is a broken line: a reader will silently drop it, and the run loses
data with no error anywhere.

Usage:  verify_boot_capture.py CAPTURE [CAPTURE ...]
Exit:   0 clean, 1 unreadable, 2 the readers' pattern could not be established.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.join(HERE, '_attic', 'scratch')

# The seven analysers that were written against the operator's own capture format.
READERS = [
    'aux_bootfaces.py',
    'aux_bootreveal.py',
    'aux_bootsubtree.py',
    'aux_expect.py',
    'aux_narrative.py',
    'aux_screenchanges.py',
    'aux_timeline.py',
]

# One `re.compile(r'...')` on a line that starts the pattern at ^Time: -- the
# pattern text itself contains no single quote, so a plain character class is
# enough and no escaping subtleties are involved.
DECL = re.compile(r"""re\.compile\(r'([^']*)'\)""")


def readers_pattern():
    """Return (pattern_text, [(reader, line_no)]).  Exit 2 on any disagreement."""
    found = []
    for name in READERS:
        path = os.path.join(SCRATCH, name)
        if not os.path.isfile(path):
            print('MISSING reader source: %s' % path)
            sys.exit(2)
        hits = []
        with open(path, 'r', encoding='utf-8', errors='replace') as fh:
            for no, line in enumerate(fh, 1):
                if '^Time:' not in line:
                    continue
                for m in DECL.finditer(line):
                    hits.append((no, m.group(1)))
        if len(hits) != 1:
            print('reader %s declares %d candidate patterns, expected exactly 1'
                  % (name, len(hits)))
            sys.exit(2)
        found.append((name, hits[0][0], hits[0][1]))

    distinct = sorted({p for _, _, p in found})
    if len(distinct) != 1:
        print('the readers no longer agree on one pattern:')
        for text in distinct:
            print('    %s' % text)
            for name, no, pat in found:
                if pat == text:
                    print('        used by %s:%d' % (name, no))
        sys.exit(2)

    pat = distinct[0]
    # Guard against having picked up some other re.compile in those files: the
    # promise is about the ANCHORED form, because a trailing field would still be
    # swallowed by the greedy value group while the end anchor is what tells a
    # reader the line is complete.
    if not pat.startswith('^') or not pat.endswith('$'):
        print('the extracted pattern is not anchored: %r' % pat)
        sys.exit(2)
    return pat, [(n, l) for n, l, _ in found]


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip())
        return 2

    text, provenance = readers_pattern()
    rx = re.compile(text)

    print('pattern read from the readers themselves (%d sources, all identical):'
          % len(provenance))
    for name, no in provenance:
        print('    %s:%d' % (name, no))
    print('    %s' % text)
    print()

    total_data = total_bad = total_other = 0
    bad_files = []
    for path in argv[1:]:
        if not os.path.isfile(path):
            print('%-56s MISSING' % path)
            bad_files.append(path)
            continue
        with open(path, 'rb') as fh:
            raw = fh.read()
        # The readers split on '\n' and anchor at '$', so a CR left on a line makes
        # every line fail.  Report it as the line-ending fault it is instead of
        # counting thousands of broken lines.
        if b'\r\n' in raw:
            print('%-56s CRLF (the readers anchor at $ and would match nothing)'
                  % os.path.basename(path))
            bad_files.append(path)
            continue
        body = raw.decode('utf-8', 'replace')
        lines = body.split('\n')
        # A file that ends with a newline yields one empty final element; it is not
        # a line the writer produced.  An empty line in the middle is a defect.
        if lines and lines[-1] == '':
            lines.pop()
        data = bad = other = 0
        first_bad = None
        for no, line in enumerate(lines, 1):
            if line.startswith('#'):
                continue
            if rx.match(line):
                data += 1
            elif line == '':
                other += 1
                if first_bad is None:
                    first_bad = (no, repr(line))
            else:
                bad += 1
                if first_bad is None:
                    first_bad = (no, repr(line[:120]))
        total_data += data
        total_bad += bad
        total_other += other
        note = ''
        if bad or other:
            note = '   FIRST BAD LINE %d: %s' % first_bad
            bad_files.append(path)
        print('%-56s %7d data, %d broken, %d blank%s'
              % (os.path.basename(path), data, bad, other, note))

    print()
    print('%d data lines, %d broken, %d blank lines across %d files'
          % (total_data, total_bad, total_other, len(argv) - 1))
    if total_data == 0:
        print('NOTHING TO CHECK: no data line was read, so this proves nothing.')
        return 2
    if total_bad or total_other or bad_files:
        print('FAIL: the capture is not readable by the archived readers.')
        return 1
    print('OK: every line is either a comment or a line the readers parse.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
