import sys

BS = chr(92)
CRLF = chr(13) + chr(10)

for name in sys.argv[1:]:
    raw = open(name, 'rb').read()
    non_ascii = sum(1 for x in raw if x > 127)
    print('%s bytes=%d backslash=%d crlf=%d nonascii=%d'
          % (name, len(raw), raw.count(BS.encode()), raw.count(CRLF.encode()), non_ascii))
