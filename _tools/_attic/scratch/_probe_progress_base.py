# -*- coding: utf-8 -*-
"""Locate the first byte where the disk PROGRESS mirror diverges from the module content.

The end-to-end check failed with EQUAL lengths (107208) and different hashes, so some byte was
substituted. The boundary probe then reported the mismatch already at the base prefix -- over
the OLD 103389 bytes, i.e. before the delta this round appended. That relocates the question:
either the disk mirror had already drifted from the module by an equal-length substitution, or
one of the two hash loops is misaligned.

This compares the module's own prefix hashes (read out of the ModuleScript at 1024-byte steps)
against the same prefixes of the disk-derived content, so the first divergence is a byte range
and not a guess. No file is written.
"""
import io

P = r"D:\rblxTRGproject\PROGRESS.md"
BAK = r"D:\rblxTRGproject\PROGRESS.md.bakphase33"

# Prefix hashes emitted by the ModuleScript itself, at i = 1 + 1024k bytes.
MODULE = """1 0000000a
1025 05a41df0
2049 7dc9cdc3
3073 24236179
4097 5c9e89cc
5121 102d36c0
6145 01e3183f
7169 2358c25d
8193 3ac06206
9217 56cab92c
10241 2c18267c
11265 0fe55810
12289 1703a500
13313 529eb17a
14337 1b25cfdc
15361 7bc6f6b4
16385 3708d130
17409 037193a9
18433 3c84caa9
19457 5036c0e4
20481 3615e503
21505 5a06e531
22529 5cb5827c
23553 2df555f6
24577 189f8352
25601 67bfcd58
26625 205a18cc
27649 48c63258
28673 11ccf7c6
29697 1844b480
30721 4ac8bec0
31745 3f968bb9
32769 2e9a3165
33793 551bcda7
34817 1e03a418
35841 78b5e904
36865 38fa6d26
37889 35d11f3e
38913 3baad368
39937 55839dbc
40961 7ab73740
41985 1a2e94ce
43009 1e13e475
44033 2081105f
45057 34c75a58
46081 78794d76
47105 7bdba1fa
48129 746be72f
49153 2b8abf06
50177 43c311e2
51201 1c1faa91
52225 0bcc50bd
53249 72ff2c62
54273 7ca95d96
55297 4fc489b0
56321 6d11abab
57345 2e71347a
58369 7c544e8f
59393 103bcc29
60417 30e10e41
61441 4f10c177
62465 24c9274f
63489 04ab7df9
64513 7944d1a2
65537 52037a72
66561 17373ec0
67585 39cd21e1
68609 08cd49e7
69633 61caa73e
70657 34292f75
71681 54f9fcd8
72705 3051528d
73729 7ed5f0f4
74753 3ef601c9
75777 0617cfc1
76801 27fea4ea
77825 3be4aa18
78849 102b2f88
79873 55a6c190
80897 4d5ea673
81921 56409f4f
82945 6bf09841
83969 05eb1a30
84993 1a7c2c42
86017 066322f6
87041 26bb144e
88065 51a0d98c
89089 789c38c8
90113 581e3001
91137 7c5d07f2
92161 58ca9337
93185 50dc85ce
94209 4b4b1964
95233 67bfc1bf
96257 327cbd9c
97281 4b12150f
98305 53903c27
99329 3b4db2c1
100353 6dcb73d3
101377 6d65049e
102401 41c8b7b2
103425 1dc077c4
104449 2df4b5fe
105473 0cb726a3
106497 336ea07f"""


def roll(bs):
    h = 0
    for b in bs:
        h = (h * 31 + b) & 0x7FFFFFFF
    return "%08x" % h


pairs = []
for line in MODULE.strip().split("\n"):
    off, h = line.split()
    pairs.append((int(off), h))

new_content = io.open(P, "rb").read()[:-1]        # what the mirror now claims = module content
old_file = io.open(BAK, "rb").read()              # pre-edit disk file

print("disk-derived content: len=%d hash=%s" % (len(new_content), roll(new_content)))
print("old disk file       : len=%d hash=%s   (EXPECT 103390/0a9dcfb9)" % (len(old_file), roll(old_file)))
print()
print(" off     module   | new disk | old disk")
first = None
for off, want in pairs:
    m = roll(new_content[:off])
    o = roll(old_file[:off]) if off <= len(old_file) else "--"
    nm = "OK " if m == want else "BAD"
    om = "OK " if o == want else "BAD"
    if first is None and m != want:
        first = off
    mark = "  <== first divergence" if (first == off and m != want) else ""
    print("%7d  %s %s | %s %s | %s %s%s" % (off, want, nm, m, nm, o, om, mark))

print()
print("first divergence between module and new disk content at offset <= %s" % first)

# Now find the exact byte: bisect within (first - 1024, first].
if first is not None:
    lo = first - 1024
    # No per-byte localisation here on purpose: the module only ever reported hashes at 1024-byte
    # steps, so anything finer would be the disk compared against itself -- a loop that cannot
    # fail. The window is printed for a human to read instead.
    print("disk window  [%d:%d] = %r" % (lo, first, new_content[lo:first][:200]))
    print("old  window  [%d:%d] = %r" % (lo, first, old_file[lo:first][:200]))
    if lo <= len(old_file):
        print("disk vs old differ in window: %s"
              % (new_content[lo:first] != old_file[lo:first]))
