# -*- coding: utf-8 -*-
"""One-off: prove verify_docs.py actually goes red. A checker nobody has seen fail is a
checker nobody knows works -- and this one just had its whole comparison rewritten.

Flips one byte deep inside docs/SYSTEMS.md (a satellite, i.e. the new code path), runs the
verifier, restores the file, and runs it again. Both outcomes are asserted.
"""
import io, os, subprocess, sys

D = r"D:\rblxTRGproject"
TARGET = os.path.join(D, "docs", "SYSTEMS.md")


def run():
    p = subprocess.run([sys.executable, os.path.join(D, "_tools", "verify_docs.py")],
                       capture_output=True, cwd=D)
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")


def main():
    good = io.open(TARGET, "rb").read()
    # Deep in section 2, well past the preamble: change one character of prose.
    i = good.find("架构总览".encode("utf-8"))
    assert i > 0, "could not find the anchor text"
    bad = good[:i] + "架構總覽".encode("utf-8") + good[i + len("架构总览".encode("utf-8")):]
    assert len(bad) == len(good), "should be same length -- only the bytes differ"

    rc0, out0 = run()
    io.open(TARGET, "wb").write(bad)
    try:
        rc1, out1 = run()
    finally:
        io.open(TARGET, "wb").write(good)
    rc2, out2 = run()

    def verdict(out):
        """The CLAUDE row, not the notes under it -- and a traceback must not look like one."""
        rows = [l.strip() for l in out.splitlines() if l.startswith("CLAUDE  ")]
        return rows[0] if rows else "<<no CLAUDE row: %s>>" % out.strip().splitlines()[-1]

    print("before  : rc=%d  %s" % (rc0, verdict(out0)))
    print("tampered: rc=%d  %s" % (rc1, verdict(out1)))
    print("restored: rc=%d  %s" % (rc2, verdict(out2)))
    print()
    assert io.open(TARGET, "rb").read() == good, "restore failed"
    ok = rc0 == 0 and rc1 != 0 and rc2 == 0
    print("checker is live" if ok else "*** the checker did not react as expected ***")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
