115. A RAKED PLANE HAS NO SINGLE HEIGHT, SO COMPARING WORLDLY MINIMA ACROSS ONE MEASURES THE
     RAKE AND NOT THE GAP.

    WHAT HAPPENED. The acceptance test for the new Main register compared the axis-aligned bounding
    box minimum Y of a lever's base plate against the bounding box minimum Y of the register's own
    RegPlate, and refused a good build: "lever base plates clear the register plate by at least
    -0.2489 studs". Both parts are tilted 20 degrees and both minima sit at their own front edge -
    a lever base plate is 1.55 deep, the register 14.80 - so the two corners are at different x, and
    on a rake different x means different height. The number was reporting the register's rise across
    the desk, not the distance between two surfaces.

    THE FIX. Compare along the register's normal at a matched point: project each base's bottom-face
    centre onto the plane through P with normal REG_ROT.UpVector. That reports +0.0100 studs, which is
    the number the build was designed to produce.

    THE GENERAL LESSON. Any comparison on a sloped or rotated surface has to be made in that
    surface's own frame or along its normal. A world-axis quantity taken on a tilted assembly is a
    mixture of the assembly's shape and its tilt, and the mixture is what produced a confident wrong
    answer here. Note that the bad number was also SELF-CONSISTENT - all three levers reported
    exactly -0.2489 - so it looked like a measurement rather than the artefact it was.

116. A CYLINDER'S UpVector IS NOT ITS AXIS.

    WHAT HAPPENED. Immediately after the double-rake fix, the two button collars measured 70.00
    degrees off vertical while everything else in the same assembly measured 20.00, and that read as
    a fresh defect. It is not one. Those parts are Cylinders laid flat on the panel, so their own
    rotation already puts UpVector horizontal - 90 degrees - before the rake, and the rake carries
    it to 70. The disc's AXIS is XVector, and that measures 0.020 degrees off the register normal,
    which is correct.

    WHY IT IS THE SAME SPECIES AS DECISIONS 113. There, a rotation-matrix component that was
    identically zero in every pose reported nothing while looking like a finding. Here, the property
    that was read is not the property that carries the meaning. Both are a wrong choice of component,
    and both produce a number that is real, reproducible, and about something other than the question.

    HOW TO AVOID IT. For a Part, decide which of RightVector / UpVector / XVector is the axis for
    that Shape. UpVector is the axis only for an unrotated part. For a Cylinder the circular faces
    are on X, so XVector is the axis and UpVector is a radial direction.

117. WELDING A PARENT FRAME INTO A CHILD TRANSFORM APPLIES IT TWICE.

    WHAT HAPPENED. The register controls were mounted with `P * REG_ROT * (A^-1 * pose)`, where
    P already carried the rake - it was built as `L * CFrame.Angles(0, 0, -RAKE) * CFrame.new(0, d, 0)`.
    The net rotation is therefore REG_ROT squared: 20 degrees in, 40 degrees out, on every part of
    every control. The tell was a round number exactly double the intended one, appearing everywhere
    while the register itself - the reference - measured correct.

    WHY NOTHING ELSE CAUGHT IT. The build compiled, installed, matched its height baseline against an
    independent previous generation, and resolved all seven dot paths. A screenshot of a raked desk
    with controls leaning at 40 degrees instead of 20 looks like a raked desk with controls on it -
    the eye has no absolute reference for twenty degrees. Only the measurement had one.

    HOW TO AVOID IT. When composing a transform, write down what each factor contributes before
    writing the code. A frame that already carries an orientation must not be multiplied by that
    orientation again. The correct form here was simply `P * (A^-1 * pose)`, with P taken on the
    register's own top surface so no separate offset arithmetic was needed either.

    THE GENERAL LESSON. A defect whose only symptom is a magnitude the eye cannot judge needs a
    measurement to find it - and the measurement must be of the magnitude itself, not of something
    correlated with it. This is DECISIONS 113 and 116 seen from the third side: 113 read a component
    with no variance, 116 read the wrong component, and here the component was right and the
    composition was wrong.

118. TEST THE SHIPPED TEXT, NOT A RETYPED COPY.

    WHAT HAPPENED. The new coolant lamp branch was verified by pulling the `lampState` function text
    OUT OF THE LIVE MODULESCRIPT SOURCE, wrapping it with stubs for the four names it closes over
    (R, GameState, require, cfg), and running ten cases against it: never recalibrated, 10 seconds
    after, 29.9 seconds after, exactly 30, 31, per-pump isolation, and the three pre-existing
    atmosphere_vent branches as a regression check. 10 passed, 0 failed.

    WHY IT IS WRITTEN DOWN. The version that would have been worthless is the obvious one - retyping
    the predicate into the test harness and asserting that the retyped copy behaves. That copy agrees
    with whatever the author already believed, which is exactly the tautology section 0.0 warns about
    in the mirror rule and DECISIONS 95 records: two sides wrong in the same direction compare equal.
    Extracting the text means the test can disagree with the module, and therefore can mean something.

    HOW TO DO IT. `string.find(src, "local function NAME", 1, true)` to the first newline followed by
    `end` at column zero gives the function body. Prepend the stubs as parameters, append
    `return NAME`, and `loadstring` it. Stub only the names it actually closes over, and stub the
    config it reads with the real values so the boundary cases are the real boundaries.

119. NEVER DESTROY BY INDEX OR BY NAME LOOKUP. DESTROY BY IDENTITY.

    WHAT HAPPENED. Cleaning up duplicated ServerStorage folders, the code collected same-named
    children into a list and destroyed `all[2..n]`. For one folder the list order happened to make
    `all[2]` the stale copy. For the other the order was the same but the reasoning about it was
    inverted, and `all[2]` was the real folder - the one holding all six of the Mk2 desks built in
    the previous phase. They were destroyed.

    WHY IT WAS SURVIVABLE, AND WHAT WAS NOT RISKED. The authoritative originals were intact in
    GameCoreBaseline, an earlier Mk2 generation was preserved in Superseded_Mk2_preLEDBar, and the
    desks are regenerable from the kit - all three of which were checked before deciding anything.
    Studio undo was deliberately NOT used, because it could have reverted the install the user had
    just asked for, turning a recoverable mistake into a worse one.

    THE GENERAL LESSON. `FindFirstChild` by name and position in a children list are both facts about
    the container's history, not about the object you think you are holding. Before destroying
    anything, assert the victim: check an attribute, check asserted content, or capture the handle
    before the operation that may change the list. A cleanup routine that cannot name what it is
    deleting is a gamble, and this one lost. It is also worth noting what the duplicate folders were
    in the first place - the debris of an earlier run that died partway - so the cleanup that was
    meant to tidy a mistake is where the real damage happened.

120. AN INDEPENDENT BASELINE, OR THE CHECK IS A TAUTOLOGY.

    WHAT HAPPENED. The first Main re-install "verified" that the new desk's world box matched the old
    desk's, and that check cannot fail: the build is anchored with `o = oldLo - tmpLo` precisely so
    the new box lands on the old one. The same run then reported a false rejection by comparing the
    replacement against the broken desk it was replacing.

    WHAT ACTUALLY WORKS. Superseded_Mk2_preLEDBar's MK2PREV_* desks - built before this work began and
    not derived from it - are a baseline that can disagree. Comparing the CBL desk's height against
    that baseline is what found it 2.03 studs over its riser, and comparing Main's is what confirms
    6.250.

    THE GENERAL LESSON. A check whose inputs are produced by the thing being checked measures nothing,
    however much arithmetic it contains. Section 0.0 already records this for the documentation
    mirrors and DECISIONS 95 for hashes; it reappeared here in geometry, which is why it is worth a
    number of its own rather than a footnote. The tell is asking "what would have to be true for this
    assertion to fail" - and if the answer is "nothing", it is not a check.

121. A MOMENTARY ACTION HAS NO LEVER POSITION.

    WHAT HAPPENED. `coolant_recalibrate` is bound to a BigLever, but `CoolantSystem.Recalibrate`
    returns `(ok, reason)` - a transient outcome plus a 30-second cooldown. `detent` can only return a
    position from persistent state, and a momentary action has no persistent position, so the lever
    never moved and `STATES` had no entry for it.

    THE CHOICE. Adding one anyway - deriving a position from the cooldown - would park the lever in its
    thrown position for the whole 30 seconds, and a lever resting in its thrown position reads as a
    switch left ON. That is the wrong claim about a cooldown, and it would be a visual that lies in
    order to look busy. So the lever stays still and the LAMP says it instead: spent while cooling,
    ready after, which is word for word the branch `atmosphere_vent` already uses two branches up.

    WHY atmosphere_vent IS THE PRECEDENT AND NOT A COINCIDENCE. It is the same case - a momentary
    action with a real cooldown and no persistent position - and it is a button with a lamp and no
    lever entry in STATES, for the same reason. The existing shape of the code already contained the
    answer to the design question.

    THE GENERAL LESSON. A two-position control may only display a two-position state. Where the state
    is momentary, say it with a lamp. And before inventing a display for something, look for the
    control that already had this problem - the convention is usually already in the file.
