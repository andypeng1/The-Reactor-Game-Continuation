# -*- coding: utf-8 -*-
"""Mirror the Phase-33 CLAUDE ModuleScript edits onto the disk CLAUDE.md.

The new text is NOT retyped. It was read out of the ModuleScript as hex by Lua, emitted in
64-byte chunks with a stated byte count, and is reassembled here. The first attempt used one
continuous hand-copied hex blob and it was wrong -- INS3 came back with an odd digit count.
That is the whole argument for chunked + length-asserted transfer: prose looks fine after a
dropped character, hex does not.

The disk file is the module content with a disk-only section (the 0.0 sync-rules block)
spliced in at byte 327, plus a trailing newline. That is what verify_docs.py models with
raw[:327] + raw[1653:]. So the acceptance test is: strip the disk the same way, drop the
trailing newline, and the result must hash to what the ModuleScript reports.
"""
import io
import sys

P = r"D:\rblxTRGproject\CLAUDE.md"

# ---- pre-edit baseline, from verify_docs.py's EXPECT -------------------------------
BASE_LEN = 56454
BASE_HASH = "1b7ede6e"

# ---- the ModuleScript's own view, read back this round -----------------------------
MODULE_LEN = 59430
MODULE_HASH = "3a2fb0e3"

H1 = "## 1. 项目概述"
H3 = "## 3. 待办事项 / 下一步计划"

CHUNKS = {
    "INS1": (1136, [
        "23232320302e313220e38090e7baa6e5ae9ae380915253202f205353202f2053535320e79a84e7bca9e58699efbc88e794a8e688b7e6988ee7a1aee5ae9ae4b8",
        "8befbc890a0ae794a8e688b7e58e9fe8af9defbc9ae3808ce6b3a8e6848f3a52533d5265706c69636174656453746f72616765efbc8c5353203d205365727665",
        "7253746f72616765efbc8c535353203d20536572766572536372697074536572766963650aefbc88e8bf99e5b0b1e698afe68891e4bbace7baa6e5ae9ae5a5bd",
        "e79a84efbc89e3808de380822a2ae8bf99e698afe7baa6e5ae9aefbc8ce4b88de8a681e5868de78c9ce38081e4b99fe4b88de8a681e6b7b7e794a8e380822a2a",
        "0a0a7c20e7bca9e58699207c20e69c8de58aa1207c20e585b3e994aee680a7e8b4a8207c0a7c2d2d2d7c2d2d2d7c2d2d2d7c0a7c202a2a52532a2a207c206052",
        "65706c69636174656453746f7261676560207c202a2ae5a48de588b6e7bb99e6af8fe4b8aae5aea2e688b7e7abaf2a2aefbc8ce4bd862a2ae4b88de6b8b2e69f",
        "93e38081e4b88de58f82e4b88ee789a9e790862a2a207c0a7c202a2a53532a2a207c206053657276657253746f7261676560207c20e4bb85e69c8de58aa1e7ab",
        "afefbc9b2a2ae9878ce99da2e79a84e8849ae69cace6b0b8e8bf9ce4b88de8bf90e8a18c2a2a207c0a7c202a2a5353532a2a207c206053657276657253637269",
        "70745365727669636560207c20e69c8de58aa1e7abafefbc9b2a2ae8849ae69cace59ca8e8bf99e9878ce8bf90e8a18c2a2a207c0a0a2a2ae4b889e69da1e794",
        "b1e6ada4e68ea8e587bae79a84e7a1ace7bb93e8aeba2a2aefbc88e69cace8bdaee8b8a9e8bf87efbc89efbc9a0a312e20e68a8ae4b89ce8a5bfe5a19ee8bf9b",
        "205253202a2ae79c81e4b88de68e89e5aea2e688b7e7abafe79a84e8b49fe68b852a2a20e28094e2809420e5ae83e785a7e6a0b7e5a48de588b6e8bf87e58ebb",
        "e38082e79c9fe8a681e58db8e8bdbde7bb99e5aea2e688b7e7abafefbc8ce7bb88e782b9e698af202a2a53532a2ae380820a322e20e694bee59ca820535320e9",
        "878ce79a84e8849ae69cace698af2a2ae683b0e680a72a2ae79a84e38082e7bb9fe8aea1e3808ce8b081e5bc95e794a8e4ba86e8bf99e4b8aae5aeb9e599a8e3",
        "808de697b62a2ae5bf85e9a1bbe68e92e999a42053532a2aefbc8c0a202020e590a6e58899e4bc9ae68a8ae6adbbe5bc95e794a8e7ae97e68890e6b4bbe5bc95",
        "e794a8efbc88604445434953494f4e5360203931efbc89e380820a332e20525320e9878ce79a84e983a8e4bbb62a2ae69cace69da5e5b0b1e4b88de6b8b2e69f",
        "932a2aefbc8ce68980e4bba5e3808c525320e28692205353e3808de8bf99e7a78de690ace8bf812a2ae794bbe99da2e99bb6e58f98e58c962a2aefbc8ce58faf",
        "e4bba5e79bb4e68ea5e5819aefbc9b0a202020e8808c20576f726b737061636520e9878ce79a84e983a8e4bbb62a2ae6ada3e59ca8e6b8b2e69f932a2aefbc8c",
        "e690ace8b5b0e5b0b1e694b9e58f98e4b896e7958cefbc8ce5bf85e9a1bbe58588e997aee794a8e688b7e380820a0a0a",
    ]),
    "INS3": (1779, [
        "232320322e313120e697a7e4bbb6e5b081e5ad98efbc88323032362d30392d3232efbc8c5068617365203333efbc890a0ae58e9fe78988e79a84e688bfe997b4",
        "e6b581e5bc8fe58aa0e8bdbde69cbae588b6e5819ce4ba86efbc886043756c6c436f6e74726f6c6c65726020e698afe59b9ee694b6e79a84e58f8de7bc96e8af",
        "91e4bbb6e38081e8babae59ca820535320e9878ce4b88de8b791efbc89efbc8c0a6047616d6553746174656020e4b99f2a2ae4bb8ee69da5e6b2a1e69c89e688",
        "bfe997b42fe68987e58cbae6a682e5bfb52a2aefbc8ce68980e4bba5e4b896e7958ce586bbe59ca8e69c80e5908ee4b880e6aca1e4bf9de5ad98e79a84e78ab6",
        "e68081e38082e68daee6ada4e5b081e5ad98e4ba86e4b8a4e4bbb6efbc9a0a0a7c20e4bb8e207c20e588b0207c20e983a8e4bbb6207c20e680a7e8b4a8207c0a",
        "7c2d2d2d7c2d2d2d7c2d2d2d7c2d2d2d7c0a7c20605265706c69636174656453746f726167652e43756c6c6564506172747360207c206053657276657253746f",
        "726167652e43756c6c6564506172747360207c202a2a33382c3836392a2a207c203520e4b8aae69caae58aa0e8bdbde79a84e68987e58cbae688bfe997b4efbc",
        "9b525320e4b88de6b8b2e69f93e4bd86e4bc9ae5a48de588b6207c0a7c2060576f726b73706163652e52656163746f725f4c617365725f4d6b335f3360207c20",
        "6053657276657253746f726167652e52656163746f725f4c617365725f4d6b335f335f5374726179436f707960207c202a2a322c3836392a2a207c20e9878de5",
        "bbbae6ae8be6b8a3efbc9be59ca8e58f8de5ba94e5a086e888b1e5a496efbc8ce99bb6e782b9e587bbe599a82fe5b19ee680a72fe6a087e7adbe207c0a0ae4b8",
        "a4e4b8aae5afb9e8b1a1e59084e5b8a6e4b880e4b8aa20604f524947494e6020537472696e6756616c756520e8aeb0e5bd95e69da5e58e86e4b88ee8bf98e58e",
        "9fe696b9e6b395e380822a2ae6b2a1e69c89e588a0e999a4e4bbbbe4bd95e4b89ce8a5bfe380822a2a0a0a2a2ae8aea1e695b0e58f98e58c96efbc88e5ae9ee6",
        "b58befbc89efbc9a2a2a2052532033382c38373520e28692202a2a362a2aefbc9b576f726b7370616365203132392c39383020e28692202a2a3132372c313131",
        "2a2aefbc9b53532031312c37353420e28692202a2a35332c3439322a2ae380820ae7acace4b880e6aca1e690ace8bf81202a2a576f726b737061636520e4b880",
        "e4bbb6e6b2a1e58aa82a2aefbc8ce8bf99e5b0b1e698afe3808ce4b896e7958ce6b2a1e8a2abe694b9e58aa8e3808de79a84e8af81e68daee380820a0a2a2ae4",
        "bb8de784b6e5bc80e79d80e38081e99c80e8a681e794a8e688b7e68b8de69dbfe79a842a2aefbc88e58fafe8a781e38081e4bd86e6b2a1e69c89e4bbbbe4bd95",
        "e6b4bbe4bba3e7a081e8afbbe5ae83efbc89efbc9a0a604d6f76696e675061727473602831332c30393429202f206052656163746f7243424c736028382c3630",
        "3929202f206047656f6d657472796028352c36393529202f0a604772617669746174696f6e5368616674736028322c36323129202f20604368616d6265725761",
        "6c6c736028322c32363729e380820ae5ae83e4bbac2a2ae6ada3e59ca8e6b8b2e69f932a2aefbc8ce690ace8b5b0203d20e794bbe99da2e5b091e4b89ce8a5bf",
        "efbc8ce68980e4bba5e4b88de883bde887aae4bd9ce4b8bbe5bca0e380820a0a2a2a6043756c6c466f6c646572602832312c3732372920e4b88de59ca8e8bf99",
        "e5bca0e8a1a8e9878cefbc8ce4b99fe6b0b8e8bf9ce4b88de8a681e58aa0e8bf9be58ebb2a2a20e28094e280940a576f726b737061636520e6a0b9e69cace6b2",
        "a1e69c892060436f6e74726f6c526f6f6d6020e5aeb9e599a8efbc8ce78ea9e5aeb6e68980e59ca8e79a84e688bfe997b4e5b0b1e698af206043756c6c466f6c",
        "6465722e436f6e74726f6c526f6f6d60e380820ae5ae83e99bb6e5bc95e794a8e58faae8afb4e6988ee6b2a1e69c89e8849ae69cac2a2ae782b9e5908d2a2ae5",
        "ae83e380820a0a2a2ae982a3203520e4b8aae68987e58cbae688bfe997b4e78eb0e59ca8e4b88de59ca8e4b896e7958ce9878ce380822a2a2060576f726b7370",
        "6163652e466163696c6974792e526f6f6d736020e8a385e79a84e698afe9809ae5be80e5ae83e4bbace79a840ae8b5b0e5bb8a202f20e8bf9ee68ea5e4bbb620",
        "2f20e997a8e58e85efbc88604d61696e48616c6c7761795365676d656e7460202f206048616c6c776179526f6f6d436f6e6e6563746f7260202f2060484d4761",
        "7465776179526f6f6d6020e280a6efbc89efbc8c0a2a2ae4b88de590abe688bfe997b4e69cace8baab2a2ae38082e8a681e4b88de8a681e681a2e5a48de688bf",
        "e997b4e6b581e5bc8fe58aa0e8bdbde698afe8aebee8aea1e586b3e7ad96efbc8ce4b88de698afe6b885e79086e380820a0a0a",
    ]),
    "R_WSTOTAL": (74, [
        "7c20576f726b737061636520e680bbe983a8e4bbb6207c202a2a3132372c3131312a2aefbc88e5b081e5ad98e5898d203132392c393830efbc8ce8a78120c2a7",
        "322e3131efbc89207c0a",
    ]),
    "R_TOPLEVEL": (42, [
        "7c20e9a1b6e5b182e5aeb9e599a8207c203432efbc88e695b4e79086e5898d2031383238efbc89207c0a",
    ]),
    "R_CLICKDET": (99, [
        "7c20436c69636b4465746563746f7220e5ae9ee4be8b207c202a2a3934312a2aefbc88e697a7e8aeb020312c303233efbc8ce8a78120604445434953494f4e53",
        "60203834efbc9be5ae9ee6b58b20436f6e736f6c657320e58685203639efbc89207c0a",
    ]),
}

ROWS = [
    ("| Workspace 总部件 |", "R_WSTOTAL"),
    ("| 顶层容器 |", "R_TOPLEVEL"),
    ("| ClickDetector 实例 |", "R_CLICKDET"),
]


def roll(bs):
    h = 0
    for b in bs:
        h = (h * 31 + b) & 0x7FFFFFFF
    return "%08x" % h


def grab(name):
    nbytes, chunks = CHUNKS[name]
    hx = "".join(chunks)
    if len(hx) != nbytes * 2:
        raise SystemExit("*** %s: hex is %d chars, expected %d -- ABORT ***"
                         % (name, len(hx), nbytes * 2))
    return bytes.fromhex(hx).decode("utf-8")


INS1 = grab("INS1")

# 2.11 is a "###" heading, level with 2.1 through 2.10. The Lua probe located it with the
# pattern "## 2.11", which also matches -- one byte later -- inside "### 2.11", so find()
# returned the SECOND hash and the grabbed text came back one byte short. That single byte
# was the whole cross-check failure; every other anchor and segment matched byte for byte.
# The probe is fixed at the source too, but the text is prepended here so the transfer that
# was actually measured stays the transfer that is used.
INS3 = "#" + grab("INS3")
ROWTEXT = {k: grab(k) for _, k in ROWS}

raw = io.open(P, "rb").read()
body = raw[:327] + raw[1653:]
print("baseline: raw=%d stripped=%d hash=%s" % (len(raw), len(body), roll(body)))
if len(body) != BASE_LEN or roll(body) != BASE_HASH:
    print("*** disk is NOT at the pre-edit baseline -- ABORT, file untouched ***")
    sys.exit(1)

for label, txt, head in (("INS1", INS1, "### 0.12 【约定】RS / SS / SSS 的缩写（用户明确定下）"),
                         ("INS3", INS3, "### 2.11 旧件封存（2026-09-22，Phase 33）")):
    first = txt.split("\n")[0]
    print("%s first line %s" % (label, "OK" if first == head else "*** WRONG: %r ***" % first))
    if first != head:
        sys.exit(1)
for k, v in ROWTEXT.items():
    print("%-11s %r" % (k, v[:34]))

text = raw.decode("utf-8")
if text.count(H1) != 1 or text.count(H3) != 1:
    print("*** anchors not unique -- ABORT ***")
    sys.exit(1)
if "### 0.12" in text or "## 2.11" in text:
    print("*** inserts already present -- ABORT (idempotent) ***")
    sys.exit(1)

text = text.replace(H1, INS1 + H1, 1)
text = text.replace(H3, INS3 + H3, 1)

for prefix, key in ROWS:
    if text.count(prefix) != 1:
        print("*** row anchor %r not unique -- ABORT ***" % prefix)
        sys.exit(1)
    i = text.find(prefix)
    a = text.rfind("\n", 0, i) + 1
    b = text.find("\n", i)
    text = text[:a] + ROWTEXT[key].rstrip("\n") + text[b:]

out = text.encode("utf-8")
io.open(P + ".bakphase33", "wb").write(raw)
io.open(P, "wb").write(out)

body2 = out[:327] + out[1653:]
print("disk-only section len %d -> %d (must be unchanged)"
      % (1653 - 327, len(out[327:1653])))
trailing = body2.endswith(b"\n")
content = body2[:-1] if trailing else body2
print("CLAUDE.md %d -> %d (delta %+d)" % (len(raw), len(out), len(out) - len(raw)))
print("derived module content: len=%d hash=%s trailing_newline=%s"
      % (len(content), roll(content), trailing))
print("ModuleScript reports  : len=%d hash=%s" % (MODULE_LEN, MODULE_HASH))
print("CROSS-CHECK " + ("PASS" if (len(content) == MODULE_LEN and roll(content) == MODULE_HASH)
                         else "*** FAIL ***"))
