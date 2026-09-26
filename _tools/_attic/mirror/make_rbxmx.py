#!/usr/bin/env python3
"""Build a one-instance .rbxmx from a source file on disk.

Why this exists: getting a module's text into Studio through a tool call means
handing the bytes to the model and back, which is the one way a file can arrive
one character different from the file it was written from. Studio also
escape-decodes text on the way in (CLAUDE.md 0.10), so a source containing a
backslash can arrive as a different, broken program. Writing the instance as XML
and importing the file keeps the two copies identical by construction.

The source goes in as CDATA, which is byte-preserving for anything that does not
contain the literal `]]>`; that is asserted rather than assumed.

    python _tools/make_rbxmx.py <ClassName> <Name> <src> <out.rbxmx>
"""
import sys

ROOT = 'D:/rblxTRGproject'

HEADER = (
    '<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
    'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">\n'
)


def build(roblox_class, name, source):
    if ']]>' in source:
        raise SystemExit('source contains ]]> and cannot go in a CDATA section')
    if '<' in name or '&' in name:
        raise SystemExit('name needs escaping: %r' % name)
    return (
        HEADER
        + '\t<Item class="%s" referent="RBX0">\n' % roblox_class
        + '\t\t<Properties>\n'
        + '\t\t\t<string name="Name">%s</string>\n' % name
        + '\t\t\t<ProtectedString name="Source"><![CDATA[%s]]></ProtectedString>\n' % source
        + '\t\t</Properties>\n'
        + '\t</Item>\n'
        + '</roblox>\n'
    )


def main():
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    roblox_class, name, src_path, out_path = sys.argv[1:5]
    # Raw bytes, not text mode: this machine's console codec is GBK and reading
    # with the default encoding both mangles and raises on non-ASCII.
    with open(src_path, 'rb') as handle:
        raw = handle.read()
    source = raw.decode('utf-8')
    xml = build(roblox_class, name, source)
    with open(out_path, 'wb') as handle:
        handle.write(xml.encode('utf-8'))
    print('wrote %s: %s %r, %d source bytes'
          % (out_path, roblox_class, name, len(raw)))


if __name__ == '__main__':
    main()
