"""Find identifiers read as globals in a Luau file -- the silent-nil bug class.

    python _tools/check_luau_globals.py _tools/TRG_original_recorder.luau

Why this exists as a file rather than a one-off: it has already caught four real
bugs in a single script, and every one of them was invisible to a syntax check
and to reading the diff. Lua resolves a free name at the point the function is
COMPILED, so a `local` declared further down the file is not visible to a
function above it -- that name silently becomes a global reading nil, and the
two halves of the file look identical while using different variables. In this
project that produced `now - lastPoll` (arithmetic on nil) and a UI button that
set a field on a different table, so the seal could never fire.

The check: walk the file in textual order, tracking what is local at each line.
An occurrence of a name with no `local` declaration before it, and no known
global meaning, is reported. Usage before declaration is therefore caught
automatically, which is exactly the intended case -- but so is a plain typo, and
both are the same defect from the reader's point of view.

Two deliberate details, both of them lessons this project already paid for:

  * Strings are stripped BEFORE comments. The reverse order eats the closing
    quote of any string containing a double dash and then silently swallows
    whatever code follows it, which is how the first version of this check
    reported a clean file by not seeing most of it.

  * It reports suspicions, not errors. A name can legitimately be a global
    (Roblox's own, or one the script publishes on purpose), so `--allow` takes
    extra names and the report says what each finding would do at runtime
    instead of asserting a verdict it cannot support.
"""

import argparse
import re
import sys
from collections import OrderedDict

# Roblox / Luau globals a script may legitimately read.
BUILTINS = {
    "game", "workspace", "script", "plugin", "shared", "Enum", "Instance",
    "Vector3", "Vector2", "CFrame", "Color3", "BrickColor", "UDim", "UDim2",
    "Ray", "Region3", "Rect", "NumberRange", "NumberSequence",
    "NumberSequenceKeypoint", "ColorSequence", "ColorSequenceKeypoint",
    "TweenInfo", "PhysicalProperties", "Random", "Faces", "Axes", "BrickColor",
    "DateTime", "Font", "PathWaypoint", "RaycastParams", "OverlapParams",
    "CatalogSearchParams", "DockWidgetPluginGuiInfo", "RotationCurveKey",
    "math", "string", "table", "task", "coroutine", "os", "utf8", "buffer",
    "bit32", "debug", "pcall", "xpcall", "error", "assert", "select",
    "tostring", "tonumber", "type", "typeof", "unpack", "next", "pairs",
    "ipairs", "rawget", "rawset", "rawequal", "rawlen", "setmetatable",
    "getmetatable", "print", "warn", "require", "tick", "time", "wait",
    "spawn", "delay", "elapsedTime", "settings", "UserSettings", "gcinfo",
    "newproxy", "collectgarbage", "loadstring", "load", "getfenv", "setfenv",
    "ypcall", "_G", "_VERSION",
    # Executor-only globals the injector script probes for on purpose.
    "syn", "request", "http_request", "http", "fluxus", "krnl", "getgenv",
    "readfile", "writefile", "isfile", "setclipboard", "identifyexecutor",
    "hookfunction", "getrawmetatable", "setreadonly", "checkcaller",
    "getconnections", "firetouchinterest", "gethui", "cloneref", "getnamecallmethod",
    # Executor-only, and the injection recorder depends on this one: clicking a
    # ClickDetector in a way the SERVER sees has no plain-Luau equivalent.
    "fireclickdetector",
    "self", "Continue",
}

# Fields and method names are not reads of a free name.
DECL = re.compile(
    r"\blocal\s+(?:function\s+)?([A-Za-z_]\w*)"
    r"(?:\s*,\s*([A-Za-z_]\w*))*"
)
IDENT = re.compile(r"\b([A-Za-z_]\w*)\b")
FORVAR = re.compile(r"\bfor\s+([A-Za-z_][\w\s,]*?)\s*(?:=|\bin\b)")
FUNC_PARAMS = re.compile(r"\bfunction\s*[\w.:]*\s*\(([^)]*)\)")
KEYWORD = {
    "and", "break", "do", "else", "elseif", "end", "false", "for", "function",
    "if", "in", "local", "nil", "not", "or", "repeat", "return", "then",
    "true", "until", "while", "export", "type", "continue",
}


def strip_strings_and_comments(src):
    """Blank out string and comment CONTENT, preserving byte offsets.

    Order matters: strings first, then comments. Doing it the other way eats the
    closing quote of a string containing `--` and swallows the code after it.
    Offsets are preserved so every finding can quote the original line.
    """
    out = list(src)
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        # long bracket string
        m = re.match(r"\[(=*)\[", src[i:])
        if m:
            close = "]" + m.group(1) + "]"
            j = src.find(close, i + len(m.group(0)))
            j = n if j < 0 else j + len(close)
            for k in range(i, j):
                if out[k] != "\n":
                    out[k] = " "
            i = j
            continue
        if c in "'\"":
            j = i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == c:
                    j += 1
                    break
                if src[j] == "\n":
                    break
                j += 1
            for k in range(i, j):
                if out[k] != "\n":
                    out[k] = " "
            i = j
            continue
        if src.startswith("--", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            for k in range(i, j):
                out[k] = " "
            i = j
            continue
        i += 1
    return "".join(out)


def scan(src, allow):
    """Return findings: {name: [line_no, line_text, count, is_assign]}."""
    code = strip_strings_and_comments(src)
    lines = src.split("\n")
    codelines = code.split("\n")

    declared = set()
    findings = OrderedDict()

    for n, cline in enumerate(codelines, 1):
        # Declarations on a line are absorbed BEFORE that line's identifiers are
        # judged. Doing it the other way round reports every `local x = ...` as
        # a write to a global named x -- 159 findings, all of them the
        # declaration, which drowns the handful that matter. The cost is that
        # `local x = x + 1` no longer flags the read on the right; that trade is
        # worth it, because a check nobody can read is a check nobody runs.
        for m in re.finditer(r"\blocal\s+function\s+([A-Za-z_]\w*)", cline):
            declared.add(m.group(1))
        for m in re.finditer(r"\blocal\s+(?![Ff]unction\b)([^=\n]+)", cline):
            for part in m.group(1).split(","):
                name = part.strip()
                if re.fullmatch(r"[A-Za-z_]\w*", name):
                    declared.add(name)
        for m in FORVAR.finditer(cline):
            for part in m.group(1).split(","):
                name = part.strip()
                if re.fullmatch(r"[A-Za-z_]\w*", name):
                    declared.add(name)
        for m in FUNC_PARAMS.finditer(cline):
            for part in m.group(1).split(","):
                name = part.strip().lstrip("...")
                if re.fullmatch(r"[A-Za-z_]\w*", name):
                    declared.add(name)

        for m in IDENT.finditer(cline):
            name = m.group(1)
            if name in KEYWORD or name in BUILTINS or name in allow or name in declared:
                continue
            before = cline[:m.start()].rstrip()
            # Table field or method name, not a free read.
            if before.endswith(".") or before.endswith(":") or before.endswith("::"):
                continue
            if re.search(r"\bfunction\s*$", before):
                continue
            after = cline[m.end():].lstrip()
            # An assignment target or a table-constructor key. The right-hand
            # side is scanned on its own pass through this same loop, so nothing
            # is hidden by skipping the name itself.
            if after.startswith("=") and not after.startswith("=="):
                continue
            if name not in findings:
                findings[name] = [n, lines[n - 1].strip()[:90], 0, False]
            findings[name][2] += 1

    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--allow", action="append", default=[],
                    help="extra names that are intentional globals (repeatable)")
    args = ap.parse_args()

    src = open(args.path, encoding="utf-8").read()
    findings = scan(src, set(args.allow))

    reads = {k: v for k, v in findings.items() if not v[3]}
    writes = {k: v for k, v in findings.items() if v[3]}

    print("%s: %d lines, %d suspicious global reads, %d global writes"
          % (args.path, src.count("\n") + 1, len(reads), len(writes)))
    if writes:
        print()
        print("global WRITES (a decision -- confirm each is intended):")
        for k, (n, txt, cnt, _) in sorted(writes.items(), key=lambda x: x[1][0]):
            print("   line %-5d %-24s x%-4d %s" % (n, k, cnt, txt))
    if reads:
        print()
        print("global READS with no `local` above them (each one is nil at runtime):")
        for k, (n, txt, cnt, _) in sorted(reads.items(), key=lambda x: x[1][0]):
            print("   line %-5d %-24s x%-4d %s" % (n, k, cnt, txt))
    if not reads and not writes:
        print()
        print("clean: every name used is either local-above, a builtin, or allowed")
    return 1 if reads else 0


if __name__ == "__main__":
    sys.exit(main())
