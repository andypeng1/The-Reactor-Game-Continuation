122. APPENDING TO A MODULE BODY MUST NORMALISE THE NEWLINES IT REPLACES, NOT ASSUME THEM.

    WHAT HAPPENED. The Phase 40 block went into the PROGRESS ModuleScript as
    `sub(src, 1, term - 1) .. NL .. NL .. block .. NL`, and the module's reconstructed disk image
    came out at 140882 bytes against the disk file's 140880. Two bytes, identical block, both ends
    matching.

    WHAT IT WAS NOT. The block itself. The block file hashed to 6208 bytes / 70680929, and the block
    as transmitted into Studio hashed to 6208 / 70680929 as well, with first and last fragments equal
    character for character. That exonerated the text and left the surrounding body as the only
    remaining suspect -- which is the useful half of the diagnosis, and it only worked because the
    block was hashed on BOTH sides rather than eyeballed.

    WHAT IT WAS. The body already ended with a blank line in front of its long-bracket terminator.
    The mirror rule strips
    leading and trailing newlines before hashing, so those newlines are not part of the image and
    nothing in the comparison can see them -- but they are still in the source, and the two hardcoded
    separators landed AFTER them. The disk side, rstripping the file before appending a blank line and
    the block, put two newlines between the old text and the block. The module side, keeping whatever
    the body already ended with and then adding two more, put four. One extra byte per trailing
    newline the author happened to leave before the terminator, and there were two.

    THE FIX. Normalise the boundary being edited instead of trusting the shape of the text that was
    found: strip trailing newlines from everything before the terminator, then append exactly
    NL .. NL .. block .. NL. That reproduces the disk exactly whatever the body's tail looked like.

    THE GENERAL LESSON. Section 0.0 strips newlines from both ends so that the two sides can be
    compared at all -- and that same stripping makes the ends the one place where a divergence is
    INVISIBLE to the check while still changing the bytes and the hash. The blind spot and the rule
    that creates it are the same rule. Whenever a norm is applied before comparing, the normalisation
    has to be applied again at the point of writing, not assumed to already hold. This is DECISIONS 120
    in a smaller key: the check could not fail here, so it did not, and the number that caught it was
    the length being compared alongside the hash.
