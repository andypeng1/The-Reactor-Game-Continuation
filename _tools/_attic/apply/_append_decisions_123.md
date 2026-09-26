123. A MODULESCRIPT Source IS CAPPED AT 200000 BYTES, AND DECISIONS HAS REACHED IT.

    WHAT HAPPENED. Writing the Phase 40 record into the DECISIONS ModuleScript was refused outright:

        Unable to assign property Source. Provided string length (202910) is greater than or equal
        to max length (200000)

    The disk mirror took both appends first -- 190172 -> 200396 for entries 115-121, then -> 202893 for
    entry 122 -- and the module stayed at 190172 with none of it. So for the first time in this
    project the divergence ran the other way: the DISK was ahead and the MODULE was stale.

    WHY THIS IS NOT THE CLAUDE.md PROBLEM AGAIN. The 40.0K limit that forced the CLAUDE split was a
    warning Claude Code prints while assembling context. It is soft, it is about the reader, and the
    document was perfectly representable -- it was merely inconvenient. This is different in kind: a
    hard engine cap on the property itself, enforced at assignment, with no budget to raise. The
    document cannot be made to fit. It has to be split, and only a split will do.

    THE FIX, AND WHY THE PREVIOUS SPLIT'S SHAPE APPLIES UNCHANGED. Part 1 keeps the name every existing
    reference already points at -- `GameCore.DECISIONS` -- so PROGRESS, CLAUDE and the section 0.0
    table do not all have to be rewritten. Part 2 is `GameCore.DECISIONS_2`. The boundary is an ENTRY
    NUMBER, not a byte offset, so it is a fact about the document rather than about its current
    rendering, and the verifier asserts that part 1 stops exactly where part 2 starts instead of
    trusting the cut. The disk mirror is `DECISIONS.md` + `DECISIONS_2.md`; these are not `docs/`
    satellites and carry no disk-only preamble, so unlike the CLAUDE parts each disk file is its
    module's image byte for byte.

    THE PART THAT MATTERS FOR SECTION 0.0. The rule says the game-side modules are authoritative and
    the disk is the mirror, and that a conflict means the user should be told. Here the modules could
    not hold the truth at all. The content was correct on the disk and UNREPRESENTABLE in the module,
    so the split had to be built FROM the disk file -- the one time in this project the mirror is the
    only copy. Section 0.0's direction is a default, not an invariant, and the honest move when it
    breaks is to say so in the record rather than to quietly reverse it.

    THE GENERAL LESSON. A document whose only consumer is a human is still bounded by the property
    that carries it, and the bound is discovered at the moment of writing, which is the worst moment
    to discover it. The tell to watch for is a document that is still growing and has no reason to
    stop: DECISIONS gained 12717 bytes in this phase alone, and at that rate any single-script
    ceiling is a scheduled failure rather than a risk.
