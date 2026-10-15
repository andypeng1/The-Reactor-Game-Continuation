"""append_lf.py SRC DST -- append SRC to DST, forcing LF line endings.

The repo pins `* text=auto eol=lf` (.gitattributes) and the Write tool emits
CRLF on this machine, so appending a written file directly leaves mixed
endings: a phantom "M" whose diff is empty.  Normalising here is the fix.
"""
import sys

src, dst = sys.argv[1], sys.argv[2]
data = open(src, "rb").read().replace(b"\r\n", b"\n")
with open(dst, "ab") as handle:
    handle.write(data)
print("%s + %d bytes" % (dst, len(data)))
