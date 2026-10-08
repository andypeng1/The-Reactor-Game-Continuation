75. THE CLICK PLATE ON EVERY LEVER WAS BURIED, SO NO MOUSE COULD EVER REACH IT.
    Found while verifying Phase 22 - a defect the refactor exposed rather than caused. A
    ClickDetector fires only for its own parent or a descendant of that parent. The Mk2 rebuild
    wraps each lever's `ClickPart` in a `Collar` and a `Grip`, and on a lever that plate is 1.1 by
    0.2 by 1.4 studs sitting underneath both - so the mouse ray stops on the decorative ring and
    the detector never sees a click at all.

    MEASURED, NOT ASSUMED. A 26-direction scan around a lever returned `Collar` at 30 degrees
    elevation, `LeverUnion` at 55 and `Grip` at 80, and never the plate. Across the bench the plate
    was mouse-reachable for 68 of 73 controls before the fix and 70 of 73 after.
    `ControlTrigger.detectorHost` now parents the detector to the nearest ancestor model that owns
    exactly this one click plate - for a lever the lever's own model, for a button the button. The
    walk stops at the first ancestor owning more than one plate, and that is what stops a
    27-control console panel collapsing into a single giant hitbox. 25 detectors moved: every
    lever, plus `OverloadButton`, `PressureButton`, `MASS1Systems`, `AtmosphereVentButton`,
    `PEAVentilation`, `PressurizerVent`, `MonitorBootButton` and `EmergencyControl`. Both `ECC`
    receptacles moved as well, once `ClickHitBox` was added to the recognised plate names.

    A PROBE THAT LIES, AND HOW IT WAS CAUGHT. The first version of the scan reported parts as
    blocked when the ray ORIGIN was itself inside geometry, which it was for most origins. The scan
    now requires each origin to be free space - `GetPartBoundsInRadius(pos, 0.6)` returning nothing
    solid - before its rays are counted. Without that step the result was a false negative dressed
    up as a finding, which is the more dangerous of the two failure modes.

    THE THREE PARTS DELIBERATELY LEFT OPEN. `PowerCell1.Cell`, `PowerCell2.NeonPart` and
    `PowerCell3.Cell` in the HDEF cabinet are still unreachable. Measured from 50 verified-free
    origins at 6, 9 and 12 studs, exactly 0 rays reach them - against 26 for the control lever that
    proves the method works. They are genuinely enclosed by the rebuilt cabinet, so relocating
    their detectors needs a decision about what the operator is meant to click: the cell behind its
    glass, or the bay lip in front of it. That is a gameplay question, and CLAUDE section 1.4 says
    gameplay is not mine to change. They stay as they are, recorded, and fully drivable from the
    command bar.

76. TWO TOOLING TRAPS WORTH KNOWING BEFORE THE NEXT PHASE.
    THE EDIT LAYER DECODES LUA ESCAPES. Text written through the Studio edit tools arrives
    transformed: a two-character escape sequence for a newline inside a short Lua string becomes a
    real line break, and an escaped double quote becomes a real quote. Both turn valid Lua into a
    syntax error, and the error points at the string rather than at the tool that wrote it.
    `ControlTrigger` is therefore written with zero backslash characters on purpose - newlines come
    from `string.char(10)` held in a local, and any string needing an embedded double quote uses
    single-quoted Lua syntax instead. This is a convention, not a workaround to be tidied away
    later: the file is immune to the editing path because of it.

    THE OFFICIAL MOUSE TOOL'S Y COORDINATE IS NOT VIEWPORT SPACE. At a 1020 by 550 viewport,
    requesting y=275 and reading back `UserInputService:GetMouseLocation()` gives (510, 333) - a
    +58 pixel offset, with x unaffected. Requesting y=217 read back exactly 275.0, which is what
    confirmed it. This is why the first two physical clicks appeared to land on empty space, and
    the compensating offset is what made the click that finally hit. A second, smaller trap in the
    same tool: `instance_path` accepts GuiObjects only, so for a `Part` the pixels have to be
    computed with `Camera:WorldToViewportPoint`.

77. THE FOUR DOCS ARE NOT BYTE-MIRRORS, AND THREE OF THE FOUR DIVERGENCES ARE BY DESIGN.
    KEPT FOR THE LESSON - SUPERSEDED BY DECISIONS 82. Every divergence listed below has since been
    removed, and the terminator case was not in fact permanent. Read this entry for why the defects
    survived, not for the state of the mirror.

    CLAUDE section 0.0 presents each disk file as a mirror of the same-named ModuleScript. Measured
    with a 31-multiplier rolling hash over 256, 1024 and 4096 byte blocks, three of the four pairs
    had real content differences. None of them was visible to a byte count:

        DECISIONS  the disk held the literal long-bracket terminator inside one paragraph. The
                   module may not contain that sequence, so it read "the closing bracket pair"
                   instead. This entry called the divergence mandatory and permanent. It is not:
                   entry 82 changed the DISK to the module's wording, and the pair now matches.
        README     two blank lines in different places, one on each side. Both blank, so both
                   weigh nothing, and the totals agreed anyway.
        PROGRESS   the same shape: a blank line before "### 20c. The monitor bank (done)" on one
                   side and before "### 20d" on the other.
        CLAUDE     the disk is longer by section 0.0, which exists only on disk and says so. This
                   one IS by design, and entry 82 confirms it is the only divergence left.

    THE LESSON, WHICH STILL HOLDS. A length-based parity check is not a parity check. Two files can
    differ in the middle and still agree on every count a quick glance would use, and the
    divergences above survived exactly that glance. Hash the CONTENT, do not count bytes - and do
    not whitelist an exception you have not at least tried to remove.

78. THE THREE CBL LASERS WERE REFINISHED, NOT REBUILT, AND THEIR RADII CAME FROM A RAYCAST.
    NIGHT_LOG priority 3 asked for `Workspace.ReactorCBLs.Reactor_Laser_Mk3_1/2/3` to be rebuilt.
    They were measured first, and the measurement changed the job. Each machine is 2,763 BaseParts
    carrying 210 MeshParts, 100 UnionOperations, 485 Wedges and 251 live Texture/Decal children,
    with 2,607 of the parts solid hull already textured. A primitive rebuild deletes all of that
    and puts boxes in its place, and CLAUDE section 1.4 forbids removing a feature when no
    replacement exists - there is no procedural substitute for an authored mesh. The defect was
    chromatic, not structural: measured against `ServerStorage.GameCoreBaseline.ReactorCBLs_original`,
    each machine had 103 distinct colours and every one was a grey, led by 99,98,100 on 816 parts,
    with no emissive accent anywhere. So `GameCore.Rebuild.LaserKit` recolours and adds, and
    renames, deletes and moves nothing. Part count went 2,763 to 2,869 per machine, exactly +106.

    THE MUZZLE WAS SETTLED BY MEASUREMENT, BECAUSE THE AXIS IS AMBIGUOUS. In a near-symmetric tube
    the frame derived from `Laser.LaserPart` gives an axis but not a direction, and choosing wrong
    puts the aperture on the breech. The authored names resolve it: `FiringEffectPart` sits at
    +7.40, the 48 `CautionTape` hazard plates span +4.46 to +5.96, a ring of MeshParts sits at one
    station +5.22, and the hull pieces stop dead at +5.86. Hazard tape and firing effect at the
    same end means the muzzle is +X, with the Wedges running back to -52.6 on the other side.

    THREE DRAFTS OF THE RADIUS, EACH WRONG IN A DIFFERENT WAY - and the third is the interesting
    one. Draft one bucketed part CENTRES, so every on-axis disc measured radius 0.00 while the hull
    sat at 5 to 7. Draft two measured each part's true extent over all eight corners of its oriented
    box, which fixed that - but a bare percentile is still the wrong question, because the machine
    carries a cage of twelve Struts at radius 9.58 and a stack of thin discs at 9.9, so a maximum
    produced a 20-stud washer while a 60th percentile produced a ring buried inside the shell. Draft
    three added an angular filter to pick the local surface, on the reasoning that a perpendicular
    inlay line needs the hull directly under it - and that failed too, because at most stations no
    part centre lies within 26 degrees of +Y at all. The plating is not centred on the cardinals.
    `SurfaceScanner` now casts a ray inward from outside the machine at the precise station and
    angle, which answers the only question that matters. It reads 8.08 at the breech, 5.86 at the
    seam and 4.78 at the muzzle, uniform to within 0.02 all the way round, and it proved the
    analytic build had been sizing the breech two studs too small.

    THE LESSON GENERALISES PAST THIS MACHINE. A statistic over a part list answers "how big is this
    assembly", which is not the question a surface-mounted detail is asking. The ray is the only
    instrument here that measures the surface rather than the population of parts behind it.

    TWO DEFECTS THAT ONLY PHOTOGRAPHS COULD FIND. The breech cap is two `Meshes/ThinCircle2` discs
    14.3 studs across - the widest flat surface on the machine - and the first zone table painted
    that end with the brightest tone, so it caught the most light and read as a pale mass against
    the dark hall. The rear cap is now the darkest zone, which also gives the brass `BreechRing` at
    -52.5 a dark field to read as a bright rim against. And the pale lump on the emitter head was
    `SlightlyBetterSpinnyThing/Effects`: solid opaque CorrodedMetal unions authored at (188,187,190)
    inside a folder literally named Effects, which the skip list had been protecting as though it
    were a particle rig. Material is what protects the FX layer, not the folder name - every real
    emitter and glow in there is Neon, Glass or transparent, and the material filter already
    excluded all of them.

    IDEMPOTENCE WAS BROKEN BY A GUARD, AND ONLY A SECOND RUN COULD FIND IT. `Recolour` skips parts
    below luminance 0.25 so it cannot lighten the three SmoothPlastic pieces authored at pure
    black. But `steelDark` tones to luminance 0.185, so a second run treated its own output as
    deliberately black and skipped it, and the count fell from 2,358 to 2,266 with nothing visibly
    changing. The threshold is 0.10 now - above those black pieces and below the darkest palette
    tone. Verified by running the whole pass twice against the bench clone: 2,411 recoloured on both
    runs, byte-identical colours, 106 accents both times, descendants steady at 4,102.

    THE BENCH CLONE LIED ABOUT ITS NEIGHBOURS, TWICE. Two rounds of "the breech is still pale" went
    into chasing a cylinder that turned out to be surrounding facility geometry. The clone sits
    inside the live reactor hall, and one of the cameras had been placed inside the laser's own
    length span, so the pale mass at the edge of frame was never the machine. Reading the part
    colours back is what settled it: the cap measured (40,41,45) and (46,47,51), correctly dark,
    while the picture still looked wrong. The picture was right, about a different object.

79. THE TempLabel SECOND WRITER WAS PowerSystem, AND IT WAS A FRAME-RATE LEAK.
    CLAUDE section 3.2 recorded that the main monitor's TempLabel changed at irregular
    sub-second intervals (0.40 0.72 0.38 0.30 0.80 0.40 0.70 0.10) while FluctuationLabel
    held a steady 1.10 seconds, and asked who else was writing it. Ruled out first: a
    second TempLabel under MainControlRoomMonitor, of which there is exactly one, at
    MainMonitorFrame.ReadingsFrame.TempLabel, and the monitor's own writer in
    MonitorService.UpdateMain. Reproduced with a sampler on both labels together in a live
    server: once every ~1.1 seconds the display takes a large step (6477 to 6318 to 6186 -
    the once-per-second core update), and between those steps it counts down by exactly
    1 F about three times a second. Three changes per second at 1 F each is what a slow
    continuous ramp looks like through %.0f.

    THE WRITER WAS PowerSystem.Update: r.Temperature -= r.PowerOutput *
    cfg.ExtractionHeatLoss * dt. With ExtractionHeatLoss 0.02 and PowerOutput 141 at
    ignition, that is 2.8 F per second, delivered as 0.28 F per frame - one display step
    every 3.5 ticks, or 0.35s. That matches the measurement to the digit. Every other
    writer of Temperature is discrete: ReactorState's once-per-second block, the E-VENT
    click, and the METU dump. Only this one ran per frame.

    IT WAS ALSO A SINGLE-WRITER VIOLATION. DECISIONS 7 says ReactorState alone changes
    Temperature, and that CoolantSystem only owns the heat removal ReactorState reads.
    PowerSystem was doing to Temperature exactly what CoolantSystem is forbidden to do.

    THE FIX MOVES THE WRITE, NOT THE NUMBER. PowerSystem now publishes
    r.ExtractionHeatRate = r.PowerOutput * cfg.ExtractionHeatLoss in F per second, and
    ReactorState subtracts (r.ExtractionHeatRate or 0) * step inside its own
    once-per-second block, next to the passive loss. The rate is unchanged, the
    coefficient is unchanged, and the per-second total is unchanged - the only difference
    is the instant it lands on, which is the point. A GameState field rather than a
    GetExtractionHeat() call because PowerSystem already requires ReactorState, so a
    matching call would be a require cycle; CoolantSystem can expose a function precisely
    because it does not.

    VERIFIED IN A FRESH PLAY SESSION, because Edit-mode execute_luau gets a fresh module
    instance and cannot see a running simulation at all (CLAUDE 0.2, 0.3). TempLabel gaps
    are now 1.10 1.11 1.10 1.10 1.09 1.09 - the model's own cadence - and the temperature
    label and the fluctuation label now move together on the same step, which they never
    did before. Cooling magnitude is preserved: the mean step was -129 F over seven steps
    before and -134 F after, the difference being the 2.8 F of extraction now folded in
    rather than applied between steps. GameCoreSelfTest finalStatus PASS, resetOk true,
    devices 15, bridgeResolved 18; GameCoreControlTest pass 13 fail 0.

    A SIDE EFFECT WORTH KEEPING: TempFluctuation now measures the complete per-second
    change. It used to exclude the extraction drain, so it understated every reading by
    about 3 F in the cooling direction. That is a correctness improvement to a readout,
    not a change to the mechanic.

    NOTE ON METHOD. The traceback route failed - a GetPropertyChangedSignal handler on
    Text runs deferred and debug.traceback returns no frames - so the writer was
    identified by matching the measured cadence against the coefficient in the source
    instead. 0.28 F per frame predicts 0.35s between display steps, and the sampler
    measured 0.30 and 0.40 alternating. A prediction that lands on the measurement is
    worth more than a stack trace here, and it also answers the next reader's why.

80. THE SEVEN MONITORS RE-EXAMINED UNDER THE NEW GRADE  (PROGRESS Phase 25)

    CLAUDE 3.1 carried one open item out of Phase 20: every monitor was rebuilt before
    the Phase 21c grade landed, so not one of them had been looked at under it. Settling
    it needed two things, and only the second one is about appearance.

    INSTANCE STATE ALONE SETTLES NOTHING ABOUT APPEARANCE, and it is worth being clear
    about that rather than treating the check as done. What it does settle is that every
    Lighting value matches the DECISIONS 66 table to the digit, and that all seven
    screens are Neon 17,17,17 with SurfaceGui.LightInfluence 0.00 - the documented
    contract for a screen backing, and precisely the field a rebuild drops.

    THE QUESTION THE CAPTURES HAD TO ANSWER was whether a monitor that reads well is
    reading well, or is merely blown out. DECISIONS 58 and 59 recorded that under
    EnvironmentSpecularScale 0.8 every Metal part rendered white whatever its albedo, so
    the two cases are identical in a capture and no number in a property panel separates
    them. The way out is to delete the variable rather than measure it: set both trim
    members - the Metal band and the Plastic beads - to ONE albedo, 75,75,76, and
    capture. The band came back dark grey with the ceiling light panels in the same frame
    at pure white. Under the old grade the band would have gone with them. The specular
    fix is confirmed on the real parts, not only on the property value.

    A FALSE ALARM WORTH RECORDING, because it cost time twice. In the ordinary captures
    the light outer border is the authored Plastic bead at 186,186,188, and it sits
    0.135 studs IN FRONT of the Metal band at 75,75,76. Two different members at two
    different depths, which is the design intent, and which a screenshot alone will
    always make look like a mismatch.

    THE NEON SCREEN BACKING STAYS, and not because the workaround is still required - it
    is not, a dark panel would now stay dark. It stays because a flat, self-lit,
    shadow-free surface is the correct look for a screen, because each screen's four
    SurfaceLights are built on that part, and because it is a binding-critical host that
    no possible gain justifies touching. Here the workaround and the right answer happen
    to coincide; the reason it is kept is the second one, so that the next reader does
    not conclude the workaround is load-bearing.

    All seven nameplates carry the authored SMER - ... house style. Left as authored.

81. THE MAIN MONITOR DIAGRAM IS DRIVEN AS A PURE OBSERVER  (PROGRESS Phase 26)

    CoreDiagramFrame and ReactorDiagramFrame were the last static panel on the main
    monitor. Both intensity graphs shipped Visible=false AND with a zero-height box
    parked one full frame-height down and about two frame-widths right, so the art was
    authored unused rather than switched off. GraphDetailThingy, the Script inside
    CoreDiagramFrame, is a three-line UniversalSynSaveInstance comment stub with no
    logic: the original animation is not recoverable from the place.

    WHERE THE FEATURE LIVES. Inside MonitorService, NOT registered as a system. A 26th
    system would change the documented count, add a row to the SystemManager priority
    table and put pressure on GameCoreSelfTest - all real costs, paid for a display
    feature that owns no state. Everything it needs is already in GameState.

    IT WRITES NOTHING. It reads GameState and GameState alone - the rule DECISIONS 54
    and 60 set for the log and the forecast. Simulation output is bit-identical with or
    without this file, which is the only behaviour a cosmetic addition may have under
    DECISIONS 7.

    THE BAR IS WIDTH, NOT A FILL TEXTURE. The graph images are re-anchored to (0,0,0,0)
    and sized frac,0,1,0. Three reasons: the authored texture could not be inspected at
    all (the Open Cloud key is not set on this machine, so nothing about that asset is
    known), a width reads correctly whatever the image turns out to be, and at frac 0 the
    panel is exactly the static art being replaced, so a dead reactor looks like the old
    monitor rather than like an empty one.

    A BUG OF MY OWN, recorded because the class of mistake is easy to repeat. The first
    version set Visible and Size and NOT Position, so both bars were laid out a full
    frame-height below the panel and two frame-widths to its right: invisible, and
    invisible in a way that is indistinguishable from the feature never running. A
    control node authored off-screen has to be re-anchored explicitly; giving it a size
    means nothing on its own.

    VERIFYING IT TOOK TWO PASSES, and the failed one is the instructive one. Four
    synthetic calls with four different inputs came back byte-identical. That is not a
    bug in the code under test - it is CLAUDE 0.2. An execute_luau require returns a
    fresh empty module whose cache is nil, so UpdateDiagram early-returns and the values
    read back are the live game's own, not the ones just injected. Calling
    MonitorService.Initialize() on that fresh instance first populates the cache and the
    branches become reachable. Byte-identical output from differing input is the
    signature to watch for.

    The branches were then exercised directly. Live first: a real Play session's own
    Update produced colours that exist only in the new code, confirming the path runs
    against real data. Then, forced: stress 100 shows the three warning triangles at pure
    red; an Equinox event turns the graphs, the beams, the core, the labels and the
    warning purple (190,80,255) together, which is the one diagram colour the Wiki names;
    offline hides the core image and the energy bar and darkens every beam.

    After the Edit-mode probes both GraphImageLabels were returned to the authored parked
    state - Visible false, Position 1.900 and 1.817 by 1.000, Size 2.000 by 0 - and read
    back to confirm it, so the saved place keeps the static art it shipped with.

82. THE FOUR DOCS ARE BYTE-MIRRORS NOW, AND EVERY EARLIER PARITY CHECK PASSED WITHOUT THEM BEING ONE.

    Supersedes the "permanent" reading in entry 77 and the "All four now reconcile" claim in entry
    71. Measured with a 31-multiplier rolling hash over the whole body, three pairs are identical to
    their modules and the fourth differs only by its disk-only section:

        README    disk 32502   = module body 32502    identical
        PROGRESS  disk 93583   = module body 93583    identical
        DECISIONS disk 124214  = module body 124214   identical
        CLAUDE    disk 46719   = module body 45393 + the 1326 bytes of disk-only section 0.0

    Those numbers are a snapshot and go stale the moment any doc is edited - which is the lesson of
    both entries above, not a footnote to it. Re-derive them; do not quote them. Two facts are
    durable:

        1. The wrapper is EXACTLY 17 bytes, not "about 18": 11 for the return statement, 4 for the
           closing bracket pair, 2 newlines. Module Source length minus 17 is the body.
        2. Compare bodies by HASH. Not by byte count and not by line count. Every real divergence
           found here was invisible to a byte count, because each one MOVED bytes rather than
           adding or removing them.

    WHAT WAS ACTUALLY WRONG. Five edits in a 1670-line document:

        lines 1180-1183   the disk carried the literal long-bracket terminator inside a paragraph
                          about the wrapper. The module may not contain that sequence, so it read
                          "the closing bracket pair" instead. 20 bytes, one side only.
        lines 1192-1194   the module carried a later wording - "table" for "TABLE", "carrying" for
                          "that carry", "the method ... the right one" for "the check ... the right
                          method" - that was never mirrored out to the disk. 9 bytes.
        lines 1197-1198   the same edit re-wrapped a long line and the disk kept the old wrap.
                          Byte-neutral, which is why nothing noticed it.
        line 1275         the module held a REAL NEWLINE inside a quoted Luau pattern where the
                          newline escape was intended, splitting one source line into two.
        line 1280         the same, inside a gsub that strips newlines.

    THE TERMINATOR CONFLICT IS NOT MANDATORY, AND ENTRY 77 WAS WRONG TO CALL IT PERMANENT. The
    argument there - the disk may hold the sequence, the module may not, so the two can never match
    - is true of the module and says nothing about the disk. Paraphrasing the DISK to match the
    module removes the divergence instead of whitelisting it forever, costs the document nothing in
    meaning, and buys an exact mirror. Entry 77 whitelisted instead, and the whitelist is what let
    the other four differences hide behind it.

    THE ESCAPE TRAP HAD ALREADY BITTEN THIS DOCUMENT, TWICE, IN ENTRY 71'S OWN RECIPE. CLAUDE
    section 0.10 records that the Studio edit layer decodes Lua escapes on the way in, so a newline
    escape written inside a quoted example lands as a real newline in the source. It had happened at
    lines 1275 and 1280, and comparing the two files could not find it, because the disk had been
    written as raw bytes by Python and was CORRECT - the module was the broken copy. The repair must
    be pattern-free: the literal being replaced contains bracket and parenthesis characters, so a
    pattern replace raises "invalid pattern capture". Build both sides of the substitution out of
    string.char and splice by byte offset. And when the replacement text is itself a code sample
    containing an escape, name the escape in prose rather than re-quoting it, or the repair
    reintroduces the defect it just fixed.

    WHAT WAS NOT WRONG. No content was missing on either side, no section was out of order, and the
    Chinese character counts agreed throughout. Every difference this pass started from was either
    one of the five above, or a blank line whose twin sat somewhere else in the same file.

83. THE AMBIENT LAYER WAS NEVER MISSING, AND TWO OF ITS EMITTERS COULD NEVER DRAW.

    CLAUDE 2.10 says the built-in effects "only fire when an event triggers" and that what the place
    needs is a baseline ambient layer. Half of that is right and half of it is wrong, and the wrong
    half had been steering work toward building something that already exists. Measured across the
    whole of Workspace:

        emitters Enabled AND Rate > 0        278
        emitters disabled                  1,368

    So the always-on layer is already there. By container:

        Geometry 93   Facility 56   Mainframe 38   MovingParts 21   CullFolder 20
        GravitationShafts 18   CoolantReserviors 10   GravatronUnit 10   METU 7
        CRC1/2/3 and MedicalDispenser 1 each, QuantumMainframe 1

    The 20 in CullFolder sit in the cull folder and are cosmetic-only, which leaves 258 live ambient
    emitters in the rendered scene. The dominant always-on family is Smoke, 105 of them - that is
    the steam and haze the TODO was asking for. An earlier pass in this same session guessed the
    family was Aura at 60 and wrote that down before checking; Aura is in fact 20 on and 40 off, and
    the guess is corrected here rather than left standing.

    CORE IS WHERE 2.10 IS RIGHT, PRECISELY. Workspace.Core measures on=0 and off=97. Every emitter
    in the core is gated behind an event. The claim is a correct statement about the core and an
    incorrect statement about the place, and those two readings had been treated as one.

    WHAT THE LAYER DEPENDS ON. Of the 278 always-on emitters, 277 take their sprite from a custom
    asset id, one uses a stock rbxasset path, and none is blank. The appearance of the whole ambient
    layer is therefore hostage to those uploads. An asset the experience cannot load is not an error
    anyone sees; it is a particle that emits nothing.

    TWO OF THEM WERE DEAD ON ARRIVAL, AND NOT BECAUSE OF PERMISSIONS. A pure string audit of every
    ParticleEmitter and Decal Texture, every Sound SoundId and every MeshPart MeshId - no asset API
    involved, so nothing to throttle - gives:

        canonical rbxassetid://<digits>                      28,893
        legacy http://www.roblox.com/asset/?id=<digits>         365
        stock rbxasset://                                         2
        blank                                                     7
        malformed                                                 2   <- and both were live

    Both malformed values were the same string on two ParticleEmitters, both Enabled at Rate 5:

        6422188442'

    A bare id, no rbxassetid prefix and a stray apostrophe on the end. Neither form resolves, so
    those two emitters have drawn nothing for the life of the file. They are always-on and
    permanently invisible - the worst pair of properties, because nothing looks broken. Normalised
    to rbxassetid://6422188442 and re-audited; the malformed count is now zero.

    WHY A STRING AUDIT AND NOT AN ASSET PROBE. AssetService:CreateEditableImageAsync was tried first
    as an authorization oracle, on the theory that it must fetch the image and would therefore fail
    on an unauthorized one. The same code run twice gave contradictory answers: the first run
    reported 11 of 12 textures loading, the second reported all 13 failing with "no permission to
    load asset". That is throttling, not data. It is recorded here instead of resolved because
    either number would have been believed if only one run had happened, and the second number -
    277 unauthorized textures - would have been a false alarm large enough to reshape the schedule.
    A shape check on the string needs no network and cannot be throttled, and it found a real defect
    that the API probe could not have described even when it worked.

    THE LOG'S PERMISSION ERRORS ARE AUDIO. Six "The experience does not have access permission to
    use asset id N" lines in one output sample name ids 18927295136, 13331862090, 14650238979,
    16226739864, 91563796959335 and 18897887641. Every one of them resolves to a Sound.SoundId in
    Workspace: BreachExplosion, Modified_Energy_Sound, FacilityUpgrade, SynthesiserRefine,
    MalfunctionSound, WindAmbience, VentSound. None is a texture, a mesh or a decal. The whole
    permission-error class is audio, which is why the local sound pack the user pointed at is the
    right remedy for it, and why the visual layer needs no upload to be repaired.

84. THE MATERIAL PASS SKIPPED A THIRD OF ITS OWN TARGETS, AND NOTHING COULD HAVE REPORTED IT.

    WHAT WAS WRONG. The pass that applied the three AI materials filtered on

        if d.Material == Enum.Material.Metal then

    That is a filter on the material NAME, and it has a blind spot the pass itself created: a
    part ALREADY authored as DiamondPlate or CorrodedMetal never entered the branch at all. It
    was neither converted nor tagged, and because the pass counted only what it touched, its
    summary line - steel 49,758 / wall 44,456 / floor 5,906 - described its own successes and
    said nothing at all about what it walked past.

    THE NUMBERS. Measured 2026-09-22 across every top-level container except GameCoreTests and
    _MCPVisualTracking:

        Metal          48,546 tagged    305 untagged
        DiamondPlate    5,907 tagged  3,194 untagged
        CorrodedMetal  44,456 tagged      0 untagged

    CorrodedMetal is clean for a reason worth recording: the HEAVY containers were explicitly SET
    to CorrodedMetal plus ReactorWallPlate rather than matched, so that family never depended on
    the filter. DiamondPlate had no such path, which is exactly why it is the one that broke -
    35 per cent of every DiamondPlate surface in the place rendered as stock diamond plate sitting
    directly beside 65 per cent carrying the custom floor texture. Same material name, two
    appearances, and no error anywhere, because both are perfectly valid materials.

    THE FIX. Tagged 3,545 parts: DiamondPlate to FacilityFloorPlate, Metal to FacilitySteelPanel.
    The assignment maps on Material and only assigns a variant whose BaseMaterial matches, so it
    can never silently rewrite the Material itself as a side effect. Result: tagged 3,545, failed
    0, untagged remaining 0. Totals are now Metal 48,983 / DiamondPlate 9,103 / CorrodedMetal
    46,951, all tagged.

    Those are not the old totals and should not be reconciled against them. The place has changed
    since the first pass - console rebuild, monitor rebuild, laser rebuild, LED bars - so CLAUDE
    2.8's table was a point-in-time snapshot being read as an invariant. It now says so.

    THREE EMPTY VARIANTS, DELIBERATELY LEFT ALONE. MaterialService holds MaterialVariant and
    MaterialVariant1 (both base Plastic) and CoolantRepeatingTexture (base Concrete). All three
    have NO Texture child and ZERO part references. The first two are shaped exactly like the
    empty output generate_material is documented to produce (CLAUDE 5.3), so they are probably
    debris from that step. They are not deleted: a variant nothing references is visually inert,
    so removing it buys nothing a player can see while stepping outside the appearance-property
    envelope this project stays inside. Recorded instead, so a later sweep does not read them as
    intent.

    SECONDARY CORRECTION. Workspace holds 941 ClickDetector instances, not the 1,023 that CLAUDE
    2.9 and 6 record; both are corrected. And the four containers the night log named as the
    facility shell are not the whole shell: MonitorsFacility, RoomLights, Alarms and Lights are
    ClickDetector-free as claimed, but Facility carries 16, MovingParts 30 and Geometry 1, so
    shell work is not uniformly binding-free.
85. THE CONTROL-ROOM SHELL NEEDED A CORRECTION, NOT A REBUILD, AND THE AUDIT IS WHAT SAID SO.

    THE PLAN THAT DID NOT SURVIVE MEASUREMENT. The shell was assumed to be a bare box waiting for
    geometry, so the kit was written to lay a 182-part panel-and-rib field on all four walls and
    to add a perimeter ceiling bulkhead and a cove. Its own clash audit returned HARD=0 and
    SOFT=713. HARD=0 confirmed the rib-depth reasoning - 182 planned specs, zero clashes with any
    of the 561 light parts - but the 713 soft hits were the point, because they forced a
    structural dump of the walls, and the walls turned out to be fully dressed already.

      Wall (east)   Union 40.1 x 21.25 x 0.75 base plane, 10 vertical panels 0.125 thick, and
                    4 full-height ribs 1.5 x 21.25 x 0.75
      Wall (south)  lower panel field 7.95 x 9.95 x 0.1 and 7.75 x 9.75 x 1 (y 277.6..287.6),
                    upper panel 21.9 x 10.55 x 0.75 (y 287.6..298.1), slats 0.2 x 13.25 x 0.75
      Wall (north)  mirror of south
      FrontWall     no solid plane at all - a duct chase, 26.5 x 4 x 10 beams crossing from the
                    west wall to x = 108.3, fifteen studs inside the room

    The field would have laid a second panel layer over hand-authored work on all four walls, and
    two of its specs would have buried a security camera TextPart at (141.80, 295.85, -0.71).
    The plan was dropped in full: no panels, no ribs, no bulkhead, no cove, no accent line.
    Nothing in the kit builds anything.

    THE DEFECT THAT WAS ACTUALLY THERE. The room already runs a coherent tonal ladder. Across the
    shell's 1,379 parts the ceiling band (y_top above 296) reads 100 x 702 / 75 x 295 / 60 x 84 /
    50 x 23, and 16 wall parts already sat at 100. Two things fell outside that ladder:

      1. The ceiling slab (Geometry.Unions.Union, 55.58 x 1.00 x 74.03 at y 298.61) wore
         DiamondPlate plus FacilityFloorPlate at 160,160,160 - the same material AND the same
         variant the control-room floor wears. A floor texture on a ceiling. Sixteen wall parts
         wore it too.
      2. The walls were 160,160,160 and thirteen FrontWall parts were 205,205,205. RebuildKit's
         desk palette is hull 108 / post 86 / dark 75 / darker 60 and the deck runs 68..83, so
         every wall was brighter than the brightest large desk surface. The furniture read as
         dark shapes on a bright wall - ART_DIRECTION 2.1's red line, expressed tonally.

    Same class as DECISIONS 84: a legal material, in the wrong place, producing no error.

    THE NEAR MISS, WHICH IS WHY THIS ENTRY EXISTS. The first version of the rule was a blanket
    luminance threshold. The dry run showed it would have recoloured 25 of the room's own light
    plates - RebuildKit's light (163,162,165) Plastic, which the palette comment says MUST stay
    Plastic or it blows out to flat white - plus two amber signal lights at (226,155,64). Those
    are fittings, not surfaces. Greying them would have deleted the room's lighting in order to
    fix its walls. The gate was moved from the tone to the material variant: a part wearing
    FacilitySteelPanel or FacilityFloorPlate is structure, a part wearing no variant is a fitting
    and is left alone, and the luminance test then only chooses which outliers inside that
    structural set get pulled back.

    RESULT. recoloured 80, resteeled 25, failed 0, skipped 1,291 of 1,379. Verified from live
    instances: zero structural parts above luminance 120, zero FacilityFloorPlate left anywhere
    on the shell, all 27 fittings preserved, and 88 origin records - exactly 80 + 25 - 17 overlap.
    The shell now reads 100 x 813 / 75 x 301 / 60 x 87, so its brightest large surface is 100,
    below the desk hull at 108.

    APPEARANCE PROPERTIES ONLY - Color, Material, MaterialVariant. No part created, renamed,
    moved or destroyed, and CullFolder.ControlRoom holds zero ClickDetectors, so nothing in
    CLAUDE 6's binding table was reachable. Originals are recorded per part in a ShellKitOrigin
    attribute before the first write, so RestoreBase() is exact.

86. THE REACTOR CHAMBER'S WALLS ARE NOT A DEFECT, AND A TONE-DISTANCE TEST COULD NOT HAVE SAID SO.

    WHAT WAS SUSPECTED. ART_DIRECTION 3.6 records the research direction for the chamber - a
    near-black box lit by emissive accents - so a bright wall family reads as the thing standing
    between the room and its own art direction. The candidate was 230 wall parts at 200,205 (the
    census splits them Metal/FacilitySteelPanel 136 and CorrodedMetal/ReactorWallPlate 94), the
    largest bright family anywhere in the facility at 378,704 studs of face area, and 71 per cent
    of every large surface in the chamber. The chamber's own wall-panel family - same material,
    same variant, same role - sat at 96..127. Same material and same variant two octaves apart is
    exactly the DECISIONS 84/85 signature, so this looked like that defect again.

    WHAT KILLED IT. The full tone histogram of the wall subtrees - every non-Neon part, not just
    the large ones - as 16-wide luminance buckets:

        0-15 46 | 16-31 120 | 32-47 407 | 48-63 231 | 64-79 264 | 80-95 290 | 96-111 313
        112-127 523 | 128-143 234 | 160-175 234 | 192-207 1040 | 208-223 108 | 224-239 40
        240-255 229      (total 4,079)

    A continuous ladder across the whole range with its mode at 192-207, and 229 parts above the
    suspected family. The suspected tone IS the room's dominant tone. Nothing here is an outlier.

    WHY THE WRONG READING LOOKED SOLID. The first histogram was restricted to large faces, face
    >= 300 studs. Large-face statistics are not the room's tone, and inside the chamber the two
    diverge completely: 980 of the 1,138 non-Neon parts in the 190-223 band ARE the walls, so
    filtering to large faces keeps the walls and discards the ladder they live in. THE MEASUREMENT
    APERTURE DECIDED THE FINDING. That is the same failure as round 5's already-existing 278
    emitters and round 7's already-dressed shell: the todo list assumes the place is under-built,
    and the place is over-authored.

    THREE INDEPENDENT CONFIRMATIONS. (1) The band above 223 is 269 parts totalling 2,044 studs of
    face area - 0.5 per cent of the wall family - and ZERO of them reach face 300. Small bright
    fittings, not blown slabs. (2) The 267 FacilityFloorPlate and 12 bright Concrete parts inside
    the wall subtrees are all VERTICAL strips at thin 0.1-0.2, i.e. decorative detail segments,
    not floor material laid on a wall. (3) Mainframe's own 2,405-part family above 223 is 1,421
    Line plus 776 TextPart plus white fan parts, 7,719 studs of face in total: labels, line work,
    and a white fan.

    THE INSTRUMENT WAS WRONG, NOT JUST THE THRESHOLD. A second test was run facility-wide: per
    container, flag every large-surface family more than 64 luminance from that container's own
    large-surface mode. It flagged five containers, and CullFolder's 55 "detached" surfaces are
    simply ReactorChamber's walls against ControlRoom's corrected shell, because one container
    holds two rooms. A tone-distance rule cannot separate an authored interior from a mistake.
    Round 7 shipped that instrument once already, as a blanket luminance threshold that would have
    greyed 25 light plates and 2 amber signal lights.

    THE INSTRUMENT THAT WORKS is material-role mismatch, which is what actually found round 7's
    ceiling. Re-run facility-wide - a horizontal slab (thin axis Y) wearing FacilityFloorPlate in
    the top quarter of its container - it finds no recurrence. Its largest hit is 1,921 studs in
    QuantumMainframe, a container only 72 studs tall where an upper horizontal surface is a deck,
    against the 4,114-stud ceiling slab it was built to catch. It also has a structural limit worth
    recording: it compares against the CONTAINER's vertical span, so for a container holding two
    rooms the "top quarter" is not a ceiling at all.

    DECISION: NO SCENE WRITE, AND NO KIT. Nothing in the chamber's walls is wrong. A ChamberKit was
    considered the way ShellKit was written and then deliberately NOT written, because a kit whose
    own scan reports "nothing to fix" is a liability - it invites a later round to run it anyway
    and act on a report that was already refuted. The measurement queries are kept on disk in
    _tools/shell_audit.lua so the audit is repeatable rather than remembered.

    STANDING CONCLUSION for CLAUDE 3.1's shell item: the facility shell is not under-built and is
    not mis-toned. What remains there is decoration and hero assets, not correction.

87. THE HDEF POWER LEVER'S ANIMATION HAD BEEN DEAD SINCE BIND TIME - A COLLISION BETWEEN TWO CONTROLS THAT RESOLVE TO THE SAME LEVER.

    WHAT BROKE. ConsoleBinder defines two controls on HDEFGenerator: PowerLever.ClickPart with
    action hdef_lever, and EmergencyControl with action hdef_emergency. HDEFGenerator owns exactly
    ONE LeverUnion, and it is PowerLever's. ControlVisuals.findLeverParts climbs Model ancestors
    from the click part and returns on the FIRST ancestor owning a LeverUnion, so BOTH controls
    resolve to that same lever. Bind order in the def table is PowerLever, then EmergencyControl,
    then the three PowerCells, and Bind overwrote the lever entry unconditionally - so the action
    ended up as hdef_emergency.

    WHY THAT IS FATAL AND NOT MERELY WRONG. detent() is the only place that decides which actions
    can move a lever, and it has no hdef_emergency branch. detent returns nil, applyLever returns
    early, and the handle never moves again. The control still FIRES: the bus reports the action
    engaged, BackupPowerSystem.LeverPulled flips, the lamp changes colour. Nothing in the log and
    nothing on any monitor says the animation is gone - the lever is simply frozen at whatever
    angle it was last rendered at.

    CONFIRMED LIVE BEFORE THE FIX. Invoke on HDEF Power Lever reported the action engaged while the
    LeverUnion's CFrame was byte-identical afterwards, and the diagnostics list showed
    action=hdef_emergency detent=-1 with no hdef_lever entry anywhere in it.

    THE ACTUAL HIJACKER IS NOT THE POWER CELLS. hdef_cell is not in STATES, so Bind skips its lever
    branch entirely and the three power cells never touch the lever. The collision is PowerLever
    against EmergencyControl alone. That matters: the obvious suspect - three controls crowded onto
    one generator - is not the one, and a fix aimed at it would have missed.

    THE FIX ASKS detent() RATHER THAN KEEPING A SECOND LIST. Bind now installs an incoming action
    only if the lever holds no action yet, or the incoming action has a detent branch, or the held
    one does not:

        local incomingDrives = action and detent(action, 0, 0) ~= nil
        local heldAction = levers[moving].action
        local heldDrives = heldAction and detent(heldAction, 0, 0) ~= nil
        if action and (not heldAction or incomingDrives or not heldDrives) then ... end

    A detented action can therefore never be displaced by a non-detented one, while last-bind-wins
    survives among detented actions - which is what PW1..PW5, coolant on/off/level and
    startup/shutdown rely on. Asking detent() instead of enumerating the actions a second time
    means the guard and the renderer cannot drift apart.

    WHY A GENERAL GUARD AND NOT A SPECIAL CASE FOR HDEF. Every lever reachable by more than one
    action was enumerated. There are five. Four are legitimate and every one of their actions is
    detented: coolant_pump_on / coolant_pump_off / coolant_pump_level on the three CoolantControl
    levers, and startup / shutdown on StartUpBigLever, both of which read r.Online. Exactly one is
    pathological, and the test had already flagged it. So the guard is general in form and touches
    exactly one lever in fact.

    MEASURED AFTER. The diagnostics list carries 18 levers and the HDEF entry now reads
    action=hdef_lever detent=2 states=2, with no hdef_emergency anywhere in it. The test row for
    HDEF power lever reports moved=true with a CFrame delta of 0.169 studs in X.

88. THE CONTROL TEST'S UNCOVERED SET WAS MIS-COUNTED, AND THE PROBE ITSELF MANUFACTURED A FALSE FAIL AND A SPURIOUS PASS.

    THE CATEGORY ERROR IN CLAUDE 3.3. That item listed four things as uncovered CONTROLS -
    coolant_recalibrate, QPU replacement, Gateway, GravLift - as if they were one family.
    ConsoleBinder's def table contains no QPU, Gateway or GravLift entry at all. Those are
    standalone FacilitySystem modules, not actions on the control bus, so a console-control test is
    the wrong instrument for them and always was. The genuinely uncovered CONTROLS numbered twelve:
    coolant_recalibrate, startup, shutdown, monitor_boot, pressurizer_vent, pea_vent,
    gravatron_charge, gravatron_overload, hdef_lever, hdef_emergency, hdef_cell, metu_ecc.

    WHY THEY WERE UNCOVERED. The existing test only knew how to assert on the SCENE - does the pivot
    move, does the lamp change colour. Most of those twelve are visually stateless: pressing them
    changes a number and nothing physical. Covering them required a second phase asserting on
    GameState and on the owning system instead of on the scene, a capability this file did not have.

    THE PROBE MANUFACTURED TWO FAILURES. The first re-run reported pass:28 fail:2, and BOTH failures
    were the test's fault, not the scene's. Some rows need a precondition (startup refuses while the
    reactor is already online), so a row declares an Arm step. Arm writes GameState - but the lever
    is a RENDER of GameState and only moves when ControlVisuals.Update runs. The loop sampled the
    pivot immediately after Arm and before any re-render, so it read the PREVIOUS state's angle.
    When the armed state happened to match the stale render, a lever that really does swing on the
    click was reported as did-not-move. Fixed by re-rendering after Arm:

        if t.Arm then t.Arm(); ControlVisuals.Update(); task.wait(0.35) end

    AND ONE SPURIOUS PASS. Worse than the false failures: the Reactor shutdown row passed for the
    wrong reason. It passed only because the Reactor startup row before it had already left the
    scene in the armed pose, so the stale read happened to be correct. A probe that can pass by
    accident is not a probe.

    THE FLUCTUATION COUNT FELL FROM 60/60 TO 5/5, AND THAT IS CORRECT. The recorded 60/60 measured
    the double-writer bug fixed in DECISIONS 79 - PowerSystem wrote r.Temperature every frame, so
    all 60 iterations produced a real delta. Temperature now settles once per second, so 60
    iterations at dt = 1/10 can produce about five real updates. The loop was left untouched on
    purpose: it is measuring the 1 Hz cadence, and 5/5 is what the cadence actually is.

    MEASURED AFTER. pass:30 fail:0, finalStatus PASS, visuals 18 levers / 41 lamps, fluctuation
    checks 5 signMatches 5, and a 12-row stateTests table all PASS.

89. THE DOC MIRROR DRIFTED A SECOND TIME, AND THIS TIME THE CAUSE IS NAMED.

    THE MEASUREMENT. Six thousand nine hundred and forty-nine bytes separated the CLAUDE
    ModuleScript from its disk mirror. Measured, not estimated: call A took the source from 49378
    to 49448 (+70), calls B and C from 49448 to 54734 (+5286), one more insert from 54734 to
    56327 (+1593). Total +6949, and 56310 - 49361 = 6949 exactly. After the last insert the body
    hashed to 559f6b8e, byte-identical to the disk.

    THE CAUSE, AND IT IS NOT A MYSTERY. The drifting content is precisely what rounds 5 through 8
    wrote into the disk .md - the 2.8 material-table warning block, the 2.9 ClickDetector row, the
    2.10 ambient rewrite, three 3.1 items, the 3.4 screenshot item, two rows in 6. Round 9's own
    edits WERE in the module. So those four rounds wrote the disk and not the ModuleScript: CLAUDE
    0.0 asks for a two-way write and they did half of it. This is a process failure with a name,
    not a sync mystery.

    DECISIONS 82 ALREADY PREDICTED THIS. That entry recorded that the four docs are byte-mirrors
    now and that every earlier parity check had passed WITHOUT them being one - the checks compared
    disk to disk and could never have caught a module that had stopped being written. This
    recurrence is the consequence of exactly that blind spot, so it confirms 82 rather than
    contradicting it.

    HOW IT WAS LOCALIZED: CUMULATIVE PREFIX HASHES, A DIFF THAT MOVES NO TEXT. Reading 6949 bytes
    of prose to find a difference is both expensive and unreliable - this drift is grammatical and
    correct, only stale, so nothing looks wrong while reading it. Instead the rolling hash was
    taken over the PREFIX before each heading, on both sides, and compared. Nine anchors from the
    1 heading through 3.1 matched; everything from 3.2 onward differed. That confined 100 percent
    of the drift to one section. The same trick one level down, over the item lines inside 3.1,
    put the first divergence between the monitor-screen item and the shell item. A 1828-byte window
    dump of the disk then showed it by eye: an entire COMPLETED item, the control-room shell entry,
    that the plan for 3.1 had never accounted for - it recognized the remaining shell item and not
    the finished one directly above it. The block measured exactly 1593 bytes, which is the whole
    remaining shortfall. Total moved: about a kilobyte of hex digits, and not one byte of prose.

    THE READING RULE FOR PREFIX HASHES. A match at anchor k means everything BEFORE k is identical,
    so the section that differs is the one immediately PRECEDING the first mismatch - not the one
    the mismatch is printed on. I nearly read that backwards, which would have sent me into 3.2.

    THE FIVE-EDITS-APPLIED ANOMALY IS CLOSED. Call A sent four edits and the tool reported five.
    The final body hash now equals the disk, and a spurious fifth edit would necessarily have
    changed the text. Byte equality is the strongest available form of that conclusion, so the
    discrepancy was in the count report and never in the state. It is recorded here because an
    unexplained count is a real observation, and only its resolution is allowed to be reassuring.

    WHAT WOULD HAVE PREVENTED IT. A round's closing check must compare the MODULE's hash against
    the disk's, which requires reading the module. Re-hashing the disk against its own recorded
    value cannot detect a module that was never written - and that is the check that was run in
    between. Writing the disk .md without writing the ModuleScript in the same step is the failure
    mode, and it is invisible from the disk side by construction.

90. REPLICATEDSTORAGE DOES NOT RENDER, BUT IT DOES REPLICATE.

    THE MOVE. ReplicatedStorage.CulledParts - 38869 BaseParts in five room folders - was reparented
    to ServerStorage on 2026-09-22. ReplicatedStorage went from 38875 BaseParts to 6. ServerStorage
    went from 11754 to 50623. Workspace stayed at exactly 129980. That last number being unchanged
    is the proof that nothing in the world moved, and it is the measurement to quote, not the
    promise that nothing moved.

    WHY IT COSTS NOTHING VISUALLY. ReplicatedStorage is not Workspace, so parts parented there are
    never rendered and never simulated. They were already invisible. What they were NOT was free:
    every part in ReplicatedStorage replicates to every client on join and stays resident in that
    client memory for the whole session. 38869 instances of pure payload were being shipped to each
    player in order never to be looked at. ServerStorage does not replicate, so that number is now
    zero.

    WHAT THE STORE ACTUALLY IS. It is the original game room-streaming cache. Workspace.CullFolder
    holds the loaded rooms, ReplicatedStorage.CulledParts holds the unloaded ones, and the original
    CullController swapped them on every room change. The reader is dead twice over: it is a
    recovered decompiled LocalScript parked in ServerStorage, which is where scripts go to never
    run, and GameState has no room or sector concept at all - Facility is only AreasOnline, Doors,
    EmergencyMode, Lighting, Power. The remake never implemented streaming, so the world is frozen
    at whatever the last save captured: ControlRoom and ReactorChamber loaded, five rooms parked.

    THE COST OF THAT FREEZE, STATED PLAINLY. Workspace.Facility.Rooms contains MainHallwaySegment,
    HallwayRoomConnector, HMGatewayRoom, RMGatewayRoom, RLGatewayRoom, GravGate and
    ToolStorageFacility - corridors, connectors and doorways, 6637 parts - and not one of the five
    sector rooms themselves. HMSector, RMSector, LowerRMSector, ReactorLounge and Gravatron exist
    only in this store. The hallways are built and the rooms they lead to are not in the world. The
    move did not cause that, because those rooms were already unrendered; it only makes the state
    legible.

    REVERSIBILITY. A StringValue named ORIGIN was placed inside the store recording what it is,
    where it came from and how to undo it. Every park in this round carries one.

91. SERVERSTORAGE SCRIPTS NEVER RUN, SO THEIR REFERENCES ARE DEAD REFERENCES.

    THE HOLE IN THE INSTRUMENT. The reference count treated every LuaSourceContainer that named a
    container as a reader, including the ones that cannot execute. ServerStorage is not a place
    where scripts run: a Script, LocalScript or ModuleScript parented there is inert. CullController
    and MovementController live in ServerStorage.RecoveredHiddenScripts and they are the only
    non-document readers of CullFolder and of MovingParts. Counted naively that is two references.
    Counted correctly it is zero, and MovingParts - 13094 parts, 1807 textures, 842 unions - has no
    live driver at all.

    THE FILTER, NOW EXPLICIT. Live means: a LuaSourceContainer that is not a descendant of
    ServerStorage, not one of the four document modules or the Wiki dump, not a Rebuild kit (those
    are design-time tools driven by hand from the command bar), and not a GameCoreTests script
    (disabled except during a run). Anything else is a reference only in the archaeological sense.

    This reclassified the largest containers in the place, and it is why the audit had to be redone
    twice inside one round. Both times the first version was the one that looked finished.

92. A NAME-BASED REFERENCE TEST IS UNRELIABLE FOR SHORT OR COMMON NAMES.

    THE FALSE POSITIVE. The same instrument said Workspace.Core had 41 live readers. All 41 were the
    Animate script, which is a passenger inside the character rigs and happens to contain the
    substring Core in unrelated text. Tools, Stats, Sounds, MES and Camera are equally unsafe tokens.
    CullFolder, MovingParts, ReactorCBLs, ChamberWalls, GravitationShafts, Geometry and
    MainframeToolStorageCull are distinctive enough to trust.

    THE RULE. A substring search can prove a container is not being found by name only when the token
    is distinctive. For short tokens it proves nothing in either direction, and the number it prints
    still looks like evidence. This is the same failure as every other instrument defect in this
    project: the output was well-formed and the conclusion drawn from it was wrong.

    THE COMPLEMENT, WHICH IS THE REAL LIMIT. Even a distinctive token only catches readers that name
    the container literally. A system that reaches it by iterating Workspace children, or by
    CollectionService tag, or by a path assembled from Config, is invisible to this test. CBLSystem
    is the worked example: it has no code that finds the lasers at all - its only mention of Laser is
    the comment on line 1 - because it is a pure simulation that heats the core from Config numbers
    and never touches the models. ReactorCBLs is 8609 parts of scenery with no driver, and that was
    only established by reading the system, not by counting references to it.

93. THE UNANCHORED PARTS WERE NEVER THE PROBLEM - RETRACTION.

    WHAT I SAID. In the first performance pass I told the user that the 7504 unanchored parts were
    the bigger lever, larger than moving containers, and recommended investigating them first. The
    user took that recommendation.

    WHAT THE MEASUREMENT SAID. Physics cost is carried by assemblies, not by parts, and the test that
    matters is whether a part root is anchored, which is what part:GetRootPart().Anchored reports.
    Of the 7504 parts with Anchored false, 3961 are welded into assemblies whose root IS anchored and
    therefore cost nothing. Of the 3543 that survive, 3165 do not collide. The whole set collapses to
    134 distinct assemblies, of which MovingParts accounts for 44 assemblies, 2309 parts and 8
    colliding. A hypothesis that predicted a large win predicted 134 objects.

    WHY IT IS WRITTEN DOWN. The recommendation was mine and it was acted on, so the retraction has to
    be at least as loud as the claim was. The instrument error is the ordinary one for this project -
    counting the wrong noun - and the fix is the same as always: name the noun the engine charges
    for. The engine charges for simulated assemblies, for rendered surfaces, for replicated
    instances and for light sources. It does not charge for the Anchored flag.

94. THE LOOSE MK3_3 LASER WAS REBUILD RESIDUE.

    THE FINDING. Workspace had a top-level Model named Reactor_Laser_Mk3_3, 2869 BaseParts, while
    Workspace.ReactorCBLs contained a Model of the same name and the same 98.0 by 36.7 by 36.7 size.
    Identical size, different place: 110.079 studs apart. The reactor chamber occupies
    (-115.4, 0.8, -105.1) to (95.6, 505.9, 103.8). Mk3_1, Mk3_2 and the in-folder Mk3_3 all sit
    inside it. The loose copy occupies (-0.8, 302.2, 124.8) to (39.7, 318.8, 192.1) - past the
    chamber wall in z, above it in y, outside it.

    WHY IT IS RESIDUE AND NOT A FOURTH LASER. It carries no ClickDetector, no attribute and no tag,
    and no live script names ReactorCBLs at all. It sits beside the two other survivors of the same
    kind: Workspace.Rebuild.Models.LaserBench, which holds a laser-sized reference copy, and
    Workspace.ControlRoomMk2, which holds 89 parts of console-build deck. All three are staging
    left in the world by rebuilds that finished.

    THE ACTION. It was parked into ServerStorage.Reactor_Laser_Mk3_3_StrayCopy with an ORIGIN marker,
    not deleted. The abort guard in front of the move refuses to touch it if it turns out to carry a
    ClickDetector, an attribute or a tag - and it ran, and passed, before anything moved. Workspace
    went from 129980 to 127111 BaseParts and the three real lasers are intact at 2869, 2871 and 2869.

    ControlRoomMk2, Rebuild.Models.LaserBench and ServerStorage.GameCoreBaseline were NOT touched.
    Those are on the do-not-delete list and residue status does not override it.

95. THE DISK MIRROR HAS A RULE, AND IT EATS PUNCTUATION SILENTLY.

    THE RULE, MEASURED RATHER THAN ASSUMED. The disk file is the module content with the
    single leading newline dropped, plus one trailing newline only if it does not already
    end with one. Checked against all four documents: PROGRESS and DECISIONS content begins
    and ends with a newline, so those two disk files are exactly content[2..]; CLAUDE begins
    with '#' and ends without a newline, so its disk file is content plus one newline. The
    older note in this project said "content plus a newline" for all four. That agreed with
    CLAUDE by luck and was wrong for the other three.

    THE TWO BYTES THAT WERE LOST, AND WHY ONLY A HASH COULD SEE THEM. Appending a section
    with the Studio edit tool re-anchors on the last line of the previous section. In both
    PROGRESS and DECISIONS that anchor dropped the full stop that ended the preceding
    sentence: the module said "no scene write" and "by construction" while the disk still
    said "no scene write." and "by construction.". One byte apart, same length, same look.
    The disk-versus-disk check could not see it because the expected value had itself been
    recorded from the disk -- DECISIONS 89's failure mode arriving by another road.

    WHAT THE CHECK HAS TO BE. The ModuleScript reports the value the disk file is required
    to equal, the hash and the length of content[2..], so the acceptance test compares
    module to disk instead of disk to disk. Length alone is not a check: both broken files
    were exactly the right length.

    THE HALF-BYTE TRANSCRIPTION. The Phase-33 delta leaves the module as 64-byte hex
    chunks. One chunk was typed back reading "simulated" where the module, at the time,
    said "simulate" -- my own typo, silently corrected by hand while copying. A per-chunk
    hash list from the module localised it in one pass, and the chunk was then recovered
    without a second transfer by trying every single-byte deletion and substitution and
    keeping the one that reproduced the hash. Exactly one did. Per-chunk hashes earn their
    cost on any transfer longer than a few hundred bytes.

    ONE MORE PROBE ARTEFACT, FOR THE RECORD. Lua's string.find with a plain pattern returns
    the offset of the newline, not of the character after it, so pairing it against a
    Python find that returns the position of that character produced a table of headings
    that all agreed with each other and were all one byte out. Read bytes with string.byte
    at an explicit index; never infer them from a window offset.

96. THE DOC MIRROR RULE, GENERALISED -- AND TWO ORPHAN PERIODS.

    WHAT THE RULE ACTUALLY IS. Take the ModuleScript Source, take the string body between
    the long-string brackets, strip the newlines at both ends and put exactly one back. That
    is the disk file, byte for byte, for all four documents: CLAUDE 59431/0bc66b87,
    PROGRESS 107208/624c01e9, DECISIONS 166120/44336faf, README 33262/796f17d2.

    WHY THE OLD STATEMENTS WERE WRONG. Every earlier version of the rule was fitted to the
    disk it had been checked against, so it agreed with itself and was wrong at the edges:
    one dropped the leading "#" of CLAUDE, another stripped a real sentence period. The
    check that settled it did not assert a rule and then verify it -- it tried every head
    crop 0..6 against every tail crop 0..6 and reported which crop reproduced the disk hash.
    A rule derived from the artefact is worth more than one confirmed against it.

    THE TWO ORPHAN PERIODS. PROGRESS and DECISIONS each ended with a line containing nothing
    but a period. No disk file had it. It is a scar from the eaten-period repair recorded in
    95 -- the lost period came back on its own line instead of at the end of its sentence.
    Both removed from the modules; both disks were already correct and were not touched. A
    lone period renders as its own paragraph, so it was plain to any reader and invisible to
    every check that compared prose rather than bytes.

    THE ONE PLACE THE DISK IS NOT A MIRROR. CLAUDE.md is longer than its module's 59431
    bytes, because section 0.0 exists only on disk -- the section that says so itself.
    Dropping that whole block, heading to heading, reproduces 0bc66b87 exactly, and no other
    doc has a disk-only section. The excess is deliberately not written down here: section
    0.0 is editable on disk, so a figure frozen into this entry starts rotting the next time
    somebody improves it. The check finds the block by its headings and asserts its length,
    which catches a silent edit either way -- the assertion is the point, not the number.

97. A RAY CANNOT SEE A PART WITH CanQuery FALSE, SO AN OCCLUSION CHECK RUN AGAINST THE
    SHIPPED FLAGS IS A TAUTOLOGY.
    The first proof that CoreAssembly sits inside the world's free shell compared ray
    distances before and after the build and found them identical on all 512 rays. Every
    one of those rays was blind to the assembly by construction: the new parts ship with
    CanQuery=false, and a raycast cannot land on a part that has opted out, at any
    distance. The comparison could not have produced any other answer, which means it
    produced no evidence at all. The repair is not a better argument but a better
    instrument: CoreKit.Probe() flips CanQuery on for the duration of the scan, restores
    it afterwards, and reads the restore count back out of the instances so that a leak
    reports as a number. With the flag off the scan sees nothing; with it on, 204 of 512
    rays land on the assembly. Both numbers are now on the record.

98. BOUNDING-BOX INSTRUMENTS ANSWER BOX QUESTIONS.
    Three times in this phase a box was used to ask about geometry that is not a box.
    GetPartsInPart returned 166 overlaps, among them a hollow chamber wall 81.7 x 116.4 x
    137.4 whose box passes 6.61 studs from the core centre while its actual surfaces stay
    far outside. A hollow shell is the worst case for a box test and it is also the shape
    every wall in this facility has. A bounding-box distance cannot distinguish a hoop from
    a disc: it reported 0.00 studs for a frame whose interior is empty and 7.83 for a
    cylinder whose box corners are the only thing near. The reach of 18.08 that fell out of
    it was a corner, a point at which no part exists. That metric was removed rather than
    explained away. What replaced it reports counts, and the farthest part CENTRE from the
    core centre, which is a quantity a reader can check against the render.

99. THE CORE'S LIGHT: SWITCH ON THE ONE THAT IS ALREADY THERE, AT A LOWER BRIGHTNESS.
    CORE carries an authored PointLight -- brightness 30, range 60, colour (0,150,255),
    shadows on -- and it ships disabled, with no script in the place referencing it. Adding
    a second light would have created a second owner of the chamber's exposure; enabling
    the authored one keeps the single-writer habit and stays one line to undo. Brightness
    is set to 8 rather than the authored 30, because 30 with shadows on and a 60-stud range
    is a blinding pool rather than a glow. The authored value is written to an attribute
    before being overwritten, so the off path restores instead of guessing. Same-step
    consequence worth recording: a core that now emits light could have changed the control
    room, which DECISIONS 52 forbids. It does not. The nearest control-room part is 101.0
    studs away, the monitors 103.6, the consoles 113.5, against a 60-stud range. Measured
    after the fact rather than assumed before it.

100. CAGE PHASE IS A VIEWING-POSITION DECISION, NOT A COUNT DECISION.
    The first cage had six meridians at phase 0 and photographed as a single vertical bar
    plus a circle. The cause was not too few ribs. A rib at 0 or 180 degrees lies in the
    plane that contains the eye and the core and collapses to a line; one at 90 or 270
    collapses into the silhouette. Two ribs in six were therefore invisible as ribs, and
    they were invisible from the only seat in the game that looks at this object along that
    axis. Offsetting the phase by half a gap fixed it with no additional geometry. The count
    went to eight for density, but the phase is what fixed it.

101. AN EDIT THAT ANCHORS ON A SUBSTRING CAN LAND IN THE WRONG BLOCK.
     The core-glow section was inserted by matching `return CoreKit`, which occurs first inside
     `return CoreKit.Verify()` at Build()'s tail, so the section - function definitions included
     - went inside Build()'s body and was gone by the time anything could call it. Two habits
     come out of this. First, anchor on a string that is unique by construction, or assert
     uniqueness before writing. Second, after inserting code, MEASURE THE BLOCK DEPTH instead of
     reading the result: the text looks correct either way, because it parses, the names are
     present, and only the nesting is wrong. The checker that finally worked strips string
     literals BEFORE comments. Stripping comments first ate the closing quote of a line whose
     own text contained `--`, and produced a confident, wrong reading that Build never closed -
     a wrong instrument is worse than none, and it sent the whole diagnosis sideways once.

102. A pcall AROUND A NAME THAT MAY NOT EXIST CONVERTS A WIRING FAULT INTO SILENCE.
     `pcall(CoreKit.Glow, state)` failed quietly every tick for a whole session. Nothing else
     broke, so there was no symptom - only an absence, which is the hardest kind of fault to
     notice. A pcall exists for a callee that can throw; it is not a licence to call something
     that may not be there at all. Check the name, warn once if it is missing, and keep the
     pcall for the throw. In general: an error path that cannot be distinguished from success
     is not error handling.

103. A PURE OBSERVER MUST NOT NUDGE WHAT IT OBSERVES BY ONE STEP.
     RGB -> HSV -> RGB is not the identity at 8-bit precision; the round trip lands about 1/255
     away, measurably on 26,78,122 -> 25,78,122 and 28,92,114 -> 27,92,114. That would be
     invisible on a colour the reactor is about to shift anyway, and it is not invisible as a
     standing state: states 0 and 1 are the normal band, where severity is 0, so the core would
     have sat permanently one step off its designed colour in the ordinary case, for nothing.
     hsvShift now returns its input untouched when the shift is zero. The guard costs one
     comparison; its absence costs a designed colour that is never quite the colour designed.

     Corollary, met on the way there: a guard edited while Play is running is not in the running
     session (CLAUDE 0.3, 0.4). The drift survived the fix and looked like a failure of the fix;
     a fresh start cleared it, with edit mode byte-exact the whole time. When a change does not
     seem to take, ask whether the session loaded it before concluding that it does not work.

104. A TITLE BAR SPANS THE FRAME, NOT THE TEXT.

    THE MEASUREMENT. TitleText on all seven monitors has AutomaticSize, so its box is the width of
    its own string. Padding a bar around that box therefore produced a near-full bar on the four
    380px screens and a stub 30 percent wide on Main, Power and Thermal at 1045 to 1220px. One rule,
    two different-looking headers - and the divergence was visible in two screenshots taken minutes
    apart rather than reasoned about. The first draft also inherited the title's AnchorPoint, which
    is wrong for the same reason: a centred title would centre a full-width bar on itself and push
    half of it off the screen. A bar's width comes from the frame it heads; only its height comes
    from the text it sits behind.

    WHAT MADE THIS CHEAP TO GET WRONG. The bar is ZIndex 0, behind everything, so a wrong bar can
    hide content but can never obscure it. That is worth remembering for any future overlay in that
    strip: the layering already forbids the failure that matters, which leaves only aesthetics to
    argue about.

105. AN INVISIBLE FRAME IS NOT A HIDDEN FEATURE.

    WHAT WAS TRUE. AlertsControlRoomMonitor shipped with MainMonitorFrame.Visible false. No script
    in the place sets it true. MonitorService drives all 27 AlertFrame lamps every tick, and it
    resolves them through that same frame, so every one of those writes landed in an invisible
    subtree. The monitor rendered as a black slab, and it had done so for as long as the frame has
    been authored that way.

    WHY IT SURVIVED A REBUILD AND TWO COLOUR PASSES. The shell rebuild worked on the bezel and the
    case, where the frame's visibility does not matter. The colour passes work on content. Neither
    asked whether the content's parent was switched on, because a black screen and a dark screen
    look alike until they are compared side by side - which is precisely what the new green title
    bar made possible.

    THE PRECEDENT IS IN THE CODEBASE. MonitorService already flips the identical authored false on
    the Forecast panel and calls it a straight bug in a comment. Treating the Alerts frame
    differently would have meant two rules for one defect class.

    THE GENERAL LESSON. When a defect class has already been named in a comment, the cheapest way
    to find the rest of the class is to search for the AUTHORED STATE rather than the symptom.
    Scanning Visible across every monitor's frames took one query and found this; reading
    MonitorService looking for bugs would not have, because the service is doing exactly what it
    should.

106. A SCREENSHOT IS A HYPOTHESIS. A HISTOGRAM IS A MEASUREMENT.

    WHAT HAPPENED. Looking at a three-quarter screenshot of ORIG_MainReactorConsole I said the
    original desk was warm brass-bodied against Mk2's cool grey, and started designing around
    that. The next query counted instead of reading: 53 parts at rgb(125,124,126) Metal, 16 at
    rgb(125,125,125), 16 at rgb(105,105,105), 34 light rgb(163,162,165), 16 cyan rgb(128,187,219),
    18 unlit rgb(17,17,17), 16 dark rgb(75,75,76). Grey, with cyan accents. There is no brass body.
    What read as warmth was a brass band and two amber readouts.

    WHY THE EYE LOST. The screenshot was a distance view in a bright room. A brass band running the
    full 15 studs of the front, plus saturated amber displays, is a small fraction of the surface
    area and a large fraction of the saturated colour. Colour impression integrates saturation,
    not area - which is exactly why a part count or an area histogram disagrees with it, and
    exactly why the histogram is the one to trust once the claim is going to drive an edit.

    THE GENERAL LESSON. One query either confirms a visual impression or kills it, and it costs
    less than the edit it replaces. Two separate theories died this way in a single session. Both
    would have produced a full rebuild of six desks pointed the wrong way, and the second would
    have looked plausible the whole way through: a desk painted the wrong colour still parses,
    still binds, still runs, and still lights up.

107. AREA SHARE IS THE TONE THE EYE READS. PART COUNT IS NOT.

    WHAT HAPPENED. The first pass at "why do these two desks look different" compared part counts
    and colour histograms by part. Both misled. ORIG_MainReactorConsole has 496 parts against
    Mk2's 220, which reads as a large density gap - but a large share of the original's parts are
    0.19-stud chips. Weighting each part by its surface area moved the figures by ten points in
    both directions and made the real defect obvious: Mk2 spent 15.7 percent of its area on pure
    black against the original's 1.5, and 10.8 percent on rgb(75,75,76) against 1.2, while the
    original spent 10.2 percent on a light rgb(163,162,165) that Mk2 used almost nowhere. Four
    palette keys were pointed at the wrong surfaces; two more had drifted from the values their
    own comments recorded.

    WHERE AREA SHARE IS WRONG, WHICH MATTERS JUST AS MUCH. It counts faces that cannot be seen.
    Two seam strips 0.09 studs thick and 4.04 x 14.90 across contributed 247 square studs of
    "black" while their large faces sit flush against the brass band on both sides. That inflated
    one figure by more than ten points and would have sent the fix straight at a seam the original
    also has. A metric that cannot see occlusion always over-reports thin strips.

    THE PRECEDENT IS IN THE CODEBASE. DECISIONS 42 settled the same class of question for
    geometry: measure the bounding box, not the pivot, because a pivot is an authoring choice and
    the bounding box is a property of the geometry. Same rule here. Part count is the pivot - a
    choice about how finely the builder subdivides - and area share is the bounding box.

    THE GENERAL LESSON. Use area share to find WHICH tone is misallocated, then check the winning
    candidates against geometry before writing. Both failure modes happened in the same pass: a
    blind spot for hidden faces, and a false density signal from chip counts.

108. A FRAME IS NOT A REBUILD. SECTION 1.4 IS WHY.

    WHAT HAPPENED. The CBL lasers were asked for a second rebuild pass. They had already had one -
    LaserKit repainted them and added ring collars, seam rings, cyan inlays, status lamps and a
    muzzle glow ring. What LaserKit could not fix is the SHAPE: the machines are long round barrels
    carrying round ring collars, beside control-room desks that are now rectangular, bevelled and
    brass-banded. Recolouring a barrel keeps it a barrel.

    WHY THE OBVIOUS ANSWER WAS WRONG. A new hull is a DELETE plus a build, and each laser is about
    2,655 authored opaque hull parts - 210 MeshParts, 100 UnionOperations, 485 Wedges and 251 live
    Texture/Decal children. There is no procedural replacement for an authored mesh, so a new hull
    would have to cover the old one. A plain box in front of a detailed machine is a worse
    silhouette, not a better one: the operator would get a second style to look at, not a resolved
    one. And section 1.4 rule 2 forbids deleting a feature without a replacement.

    WHAT WAS DONE INSTEAD. LaserFrame is ADDITIVE - 125 new parts per laser in a folder named
    Mk2Frame, and nothing else. The barrel is still visible through the bays; the rectangular read
    comes from the ribs, rails and ducting built around it. No part was renamed, deleted or moved,
    no ClickDetector was created, and no name in section 6 was touched. The whole pass reverts with
    one folder deletion per laser.

    THE GENERAL LESSON. When a style mismatch is asked to be fixed and the thing is authored and
    expensive, the frame around it is often the honest answer. Additive decoration changes what the
    eye reads without touching the surface the gameplay is bound to. It also fails cheaply.

109. SAMPLING A RING AT ITS OWN CENTRES PROVES NOTHING.

    WHAT HAPPENED. The laser ribs are octagonal: eight plates per station, each centred on a
    multiple of 45 degrees, each spanning about 22.9 degrees either side of its centre. The first
    version measured the hull with an 8-point sweep - exactly the eight angles the plate CENTRES
    sit on - and placed every plate from that. Rib 7 came out at radius 9.78. A 16-point sweep put
    it at 10.52. The vent bulge that would have clipped the plate sits at a 22.5-degree offset,
    precisely between the old samples.

    WHY THE FIRST SWEEP LOOKED RIGHT. It sampled the angles the plates are named after, which is
    the intuitive choice and the least demanding one: the hull's widest point can sit halfway
    between two samples and neither one sees it. The angles that matter are the plate EDGES and the
    midpoints between, not the centres.

    THE PRECEDENT IS IN THE SAME FILE. LaserKit's own ringRadius already swept 16 for this reason.
    The new code was written next to a correct implementation of the same measurement and used half
    its resolution.

    THE GENERAL LESSON. When a measurement decides geometry, the sample count has to follow the
    GEOMETRY's angular extent, not the label's. A sweep at the feature centres measures the least
    constrained case and reports a number that is too small. If the feature spans a sector, sample
    its edges and the sector's middle too.

110. A HALF-BUILT FOLDER IS WORSE THAN NO FOLDER.

    WHAT HAPPENED. The first frame build threw partway through - a helper function had been dropped
    in an edit, and the throw landed on part 88 of the first laser. Because the folder was parented
    to the machine from the start, Mk3_1 was left with 88 orphan parts and Mk3_2 and Mk3_3 were
    never touched. The result was visually a complete machine with a partial frame bolted to it,
    which reads as a design, not as a failure.

    WHY THE THROW ESCAPED. BuildAll looped over the three roots and called Build directly, so one
    machine's exception aborted the loop for all three. A defect on laser 1 became a
    non-execution on lasers 2 and 3.

    WHAT WAS CHANGED, IN TWO PLACES, BECAUSE THERE WERE TWO DEFECTS. The folder is now built
    UNPARENTED and assigned to the machine only after the last part is created, so a mid-build
    throw leaves the machine exactly as it was. And BuildAll now wraps each per-machine Build in
    pcall, so one failure is reported and the other two still build. The atomicity fix is the more
    important one: it makes the failure mode visible instead of half-applied.

    THE GENERAL LESSON. For a multi-part decoration pass, parent last. An unparented folder is
    invisible and garbage-collected; a half-built one is a wrong world.

111. pcall RETURNS EVERY RETURN VALUE, SO TWO LOCALS SILENTLY DROP THE THIRD.

    WHAT HAPPENED. `local ok, msg = pcall(Build, root)` was expected to capture the build report in
    `msg`. It captured `true`, because pcall returns `(ok, f's first value, f's second value, ...)`
    - Build returns `(ok, msg)`, so the third slot held the report and the second held a redundant
    true. The report was dropped and every run looked like it had returned no message.

    WHY IT IS EASY TO MISS. The pattern reads correctly: `ok, msg = pcall(...)` is what almost
    every example shows. It is only wrong when the callee itself returns a status first, which is
    exactly what a report-returning function does.

    THE GENERAL LESSON. Match the destructuring to the callee's actual return list, not to the
    shape of pcall. If the callee returns `(ok, msg)`, the call site needs three locals. Related:
    pcall is for callees that THROW - not a licence to call something that may be nil. A nil callee
    raises "attempt to call a nil value", which pcall will happily swallow into an indistinguishable
    `ok = false`.

112. IN ROBLOX, _G IS NOT THE FUNCTION ENVIRONMENT.

    WHAT HAPPENED. To reload an edited module in the command bar without restarting Play, the source
    was compiled with loadstring and its environment set to a stub holding `script`. The stub's
    __index pointed at _G, and the load failed at the first `require`: `attempt to call a nil
    value`. `require` is not in _G.

    WHY. _G is a shared TABLE that scripts may write to. The function environment is a separate
    thing, and it is the environment - not _G - that carries `require`, `game`, `workspace`,
    `Instance`, `Enum` and the rest. Reading _G in the command bar shows almost nothing, which is
    why it looks empty rather than wrong.

    THE FIX. Fall back to the environment itself:
    `setmetatable(stub, { __index = getfenv() })`.

    THE GENERAL LESSON. When stubbing an environment, the fallback is the environment, not _G. And
    the failure is informative if read literally: the missing name was `require`, which is a
    builtin, which means the fallback was never reaching builtins at all.

113. A COMPONENT THAT IS IDENTICALLY ZERO IN EVERY POSE CANNOT DISTINGUISH ANY TWO OF THEM.

    WHAT HAPPENED. Lever state was read by sampling one rotation-matrix component. That component
    is exactly 0.0000 in every pose these levers take, so all four levers measured identical in
    every state - including states that were provably different - and the diff then reported all
    four as CHANGED, which is the opposite of what the data said. The component that carries the
    lever swing is r12.

    WHY THE PHASE-38 VERSION OF THE SAME MISTAKE WAS WORSE. It had already happened once before on
    this project as a bogus all-CHANGED diff. The second time it cost about an hour and produced no
    information at all, because the measured quantity had no variance to measure.

    HOW TO AVOID IT. Before trusting a diff, confirm the sampled quantity VARIES across the states
    being compared. A quick check is to read the value in two states known to differ; if it is equal
    there, the metric is blind and any conclusion drawn from it is noise. GetComponents returns 12
    values - 1-3 position, then nine rotation entries - and printing all twelve costs nothing
    compared to a wrong conclusion.

    THE GENERAL LESSON. A metric with zero variance across the compared states does not report
    "no change", it reports nothing. Treat an all-identical result as a broken instrument before
    treating it as a finding.

114. RS REPLICATES TO EVERY CLIENT. SS DOES NOT. THAT IS THE ONLY DIFFERENCE THAT MATTERS.

    WHAT HAPPENED. The instruction was to move the original facility content out of the world so a
    consistent rebuild could replace it, and the question was where to put it. ReplicatedStorage and
    ServerStorage both look like "away", and only one of them is.

    WHY THEY ARE NOT INTERCHANGEABLE. RS is replicated to every client: content parked there still
    costs every player the replication and the memory, it simply does not render or simulate. SS is
    server-only. So RS is a place to put something you want on the client without showing it, and SS
    is the only place that actually unloads.

    TWO CONSEQUENCES ALREADY RECORDED, STILL BINDING. Scripts inside SS never run, so when counting
    live references to a container, SS must be excluded or dead references get counted as live
    (DECISIONS 91). And RS parts do not render, so RS to SS is a free move visually, while moving
    anything out of Workspace changes the world and must be asked about first.

    THE GENERAL LESSON. "Parked" is not one state. Decide whether the goal is "hidden from the
    player" or "not paid for by the client", because only SS achieves the second.

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

    CORRECTED IN PHASE 42 - see DECISIONS 124. The lamp does not say it. No part is bound to
    coolant_recalibrate: the station's three LEDs are claimed by coolant_pump_on first, because
    ConsoleBinder binds the ON button before the BigLever and Bind only upgrades a lamp whose action
    is falsy. So this branch has never run. Worse, the press left those three LEDs on the activation
    flash colour permanently, because applyLamp was both the flash's only clearer and an early return
    on a nil state. The DECISION above still stands - a momentary action is displayed by a lamp and
    never by a lever position - it simply had no part to display it. Both halves are fixed and
    verified in Phase 42.

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

124. A TEST OF THE PREDICATE IS NOT A TEST OF THE WIRING.

    WHAT HAPPENED. Phase 40 added a lampState branch so that coolant_recalibrate - a momentary action
    with a real 30-second cooldown and no lever position - would be shown by the lamp instead of the
    lever, and recorded that the lamp now says "spent while cooling, ready after". DECISIONS 121 is
    that record. Measured against the running place, no part is bound to coolant_recalibrate at all.
    The branch never executes.

    WHY. Three parts decide it, and each is individually reasonable.

      * ConsoleBinder line 45 binds CoolantControl<i>.OnButton.ClickPart with action coolant_pump_on.
        The BigLever, bound at line 51 with coolant_recalibrate, comes second.
      * ControlVisuals.findLampParts walks up from a click part to the nearest Model holding a lamp,
        and OnButton's own ClickPart is not named for one - it is "ClickPart", not "NeonPart". Both
        binds therefore resolve to the SAME three parts: CoolantControl<i>.Light1/2/3.NeonPart.
      * Bind upgrades an existing lamp entry only when its action is falsy - the condition reads
        "elseif action and not entry.action". By the time the BigLever binds, the LEDs already carry
        coolant_pump_on, which is truthy, so the upgrade is skipped and coolant_recalibrate ends up
        attached to nothing.

    lampState has no branch for coolant_pump_on either, so it returns nil for these parts - and that
    is where a second, worse defect was hiding. ControlVisuals.Pulse writes PULSE_COLOR
    unconditionally on every press and sets a 0.6-second timer. applyLamp was both the timer's only
    clearer AND an early return on a nil state. So the flash was cleared, no steady state was written,
    and the part simply kept the flash colour - permanently. Measured: after one press
    CoolantControl1 and CoolantControl2 read (90,255,120) indefinitely, while the untouched
    CoolantControl3 still read its authored (235,235,235). Any press on any unmanaged control in the
    place did this.

    THE FIX, AND WHY IT IS THIS ONE. applyLamp now falls back to entry.base instead of returning, and
    writes only when the colour actually changes. entry.base is captured at Bind, so it is the
    authored colour - the correct resting state for a lamp whose action has no branch, and a strictly
    better default than "leave whatever was there", which is exactly how the flash colour became
    permanent. The per-tick guard is not an optimisation: this loop visits every lamp every frame, and
    an unconditional assignment would mark the property dirty sixty times a second for a colour that
    is not moving.

    WHAT WAS DELIBERATELY NOT CHANGED. The binding precedence. Which control should own the three
    station LEDs is a design question - RebuildKit describes them as the pump LEVEL indicator,
    coolant_pump_level has no branch either, and the original leaves OnButton and OffButton with no
    lamp of their own - and answering it by reordering two binds would be guessing with the test
    scene. DECISIONS 121's design decision (a momentary action is displayed by a lamp, never by a
    lever position) still stands. What it did not have was any part to display it.

    VERIFIED IN THE FALSIFIABLE FORM. A Heartbeat sampler recording every colour change of
    CoolantControl1.Light1.NeonPart through one real simulated click:

        0.02 s  (235,235,235)    5.57 s  (90,255,120)    6.28 s  (235,235,235)

    The third reading is the test, and it did not exist before the fix. Managed lamps were read in the
    same run and are unchanged: StartUpBigLever (22,22,22), E_VENTLever1 (240,240,240),
    E_VENTLever2 (22,22,22), E_VENTLever3 (240,240,240), MonitorBootButton (240,240,240).

    THE GENERAL LESSON. DECISIONS 118 is good practice and is not the problem: it tested the shipped
    text rather than a retyped copy, which is exactly right. The problem is that the claim being made
    was about WIRING - "the lamp says it" - while the test was of a PREDICATE. Extracting and running
    the function proves the function is correct; it cannot prove the function is reached. The tell is
    the one DECISIONS 120 gives: ask what would have to be true for the claim to fail, and if the test
    could pass while the claim is false, it is not a test of the claim. Here it passed and the claim
    was false. Phase 42 records the sibling case - "the client cannot reach the console" - which
    failed the same way for the same reason: an inference written down as a measurement.

125. A MATERIAL SKIN UNDER AUTHORED ARTWORK CANNOT BE SWAPPED FREELY - AN OVERLAY COMPOSITES WITH ITS BASE.

    WHAT HAPPENED. PaletteKit's first rules retired the rust skin on every structural part,
    including the ones carrying content, on a claim written into the module header: "a Decal is
    unaffected by the material underneath it". A same-camera capture of the coolant deck showed the
    opposite. CoolantReserviors.C1.Union, a 178 by 1 by 80 plate carrying a Texture, went from dark
    olive under CorrodedMetal to bright yellow under Metal.

    WHY THE CLAIM WAS FALSE. A Decal and a Texture are not the same object with different settings. A
    Texture tiles across a face with transparency, so it composites WITH the base material and the
    skin shows through the gaps; a Decal covers more of the face. "Covers more" is not "cannot
    show", and nothing had been measured that says a Decal is immune. The reason the claim survived
    review is that it was plausible and it was written down - and a plausible claim in a header
    comment reads exactly like a measured one.

    THE DETECTION WAS THE RENDER, NOT THE SCAN. Scan() reported the touched content set as a count,
    and a count of 5,218 against 96,483 structural parts reads as a detail. It took a matched-camera
    capture of the applied result to make the defect obvious. A dry run can confirm that a rule
    fires; it cannot tell you whether firing was right.

    THE FIX IS A CONSTRAINT, NOT A PATCH. Both Decal and Texture now block Rule 1 as well as Rule 2,
    so a part carrying authored artwork is left exactly as it was found. The cost is bounded and
    known: 1,555 parts, 1.0% of the facility, traded against repainting art that PaletteKit cannot
    regenerate. See DECISIONS 126.

126. AN EXEMPTION MUST USE THE SAME PREDICATE AS THE RULE IT EXEMPTS.

    WHAT HAPPENED. Restoring the content parts touched before the exemption existed needed a
    selector. A child-count census predicted 1,307 of them - 858 carrying a Texture plus 449 carrying
    a Decal. RestoreFaced() actually restored 1,555. The 248-part difference is not drift: the census
    counted CHILDREN, while the rule's isContent() also matches by NAME, and 248 structural parts are
    named TextPart or Line without carrying a face of their own.

    WHY THIS IS THE POINT AND NOT A CURIOSITY. The census looked like a measurement of the right set
    but was taken with a different test than the one that mattered. RestoreFaced selects with
    isContent() - the same function decide() calls - so the two cannot disagree about which parts are
    content. Had the restore used the census instead, 248 parts would have kept a skin the rule had
    already been corrected to leave alone, and the inconsistency would have been invisible: both
    numbers are internally consistent, and only their difference is evidence.

    THE GENERAL FORM. When a rule gains an exemption, the exemption is part of the rule.
    Re-deriving it elsewhere guarantees two definitions of "content" that will diverge at the next
    edit.

127. A READ BY PATH IS NOT A READ BY IDENTITY.

    WHAT HAPPENED. Verifying the PaletteKit run, a probe of CoolantReserviors.C1.Union reported
    DiamondPlate/FacilityFloorPlate with no children - the opposite of the plate that had just been
    diagnosed as Metal/FacilitySteelPanel carrying a Texture. Nothing had gone wrong with the write.
    C1 has more than one child named Union, and FindFirstChild returns the first match. The child
    count was what gave it away.

    WHY THIS IS A SEPARATE ENTRY FROM 119. 119 is about DELETING by index and says identity must be
    used instead. This is the same failure on a READ, where it is more dangerous rather than less: a
    delete by the wrong identity destroys something and is usually noticed, while a read by the wrong
    identity returns a confident, well-formed answer about a different object and is believed. The
    probe here produced a contradiction that looked like a bug in the code under test.

    THE RULE. When a result is surprising, suspect the selector before the subject. Get the instance
    from a query that returns the real set, and confirm identity against a property the diagnosis
    itself recorded - here the size and the child list, not the name.

128. A NAME SEARCH DOES NOT MEASURE WHETHER SOMETHING IS DRIVEN.

    WHAT HAPPENED. The operator proposed MedicalDispenser as the parking pilot because its reference
    graph came to a single grep hit. That was checked two further ways before anything moved: the
    hit is a ROOT_MAP table entry and no code reads the entry it produces, and the unit's only
    trigger host has zero matches in any script.

    WHY THE FIRST HIT WAS NOT ENOUGH. A grep tells you where a NAME is written. It cannot tell you
    that the thing those names name is ever dereferenced, called or driven, and an entry added to a
    table is only a name written down. The pilot was safe because of the second and third
    measurements, not the first.

    THE INSTRUMENT HAS LIMITS AND THEY WERE STATED. Zero matches for TriggerPart proves nobody binds
    by that name. It does not prove nothing binds by CLASS or by REGION, so the search for a driver
    was widened to every Touched:Connect in the project - one exists, on a single named box. A
    conclusion is only as strong as the search that produced it, and the honest form of the claim is
    that no driver was found by name or by class, not that there is no driver.

129. THE ARCHIVE LEDGER IS COPIED FROM THE SHIPPED ENTRIES, NOT INVENTED.

    WHAT HAPPENED. Parking MedicalDispenser needed the provenance attributes, and the project
    already had them on ORIG_MainReactorConsole and on the legacy Workspace.Rebuild.Models.AB_REF.
    They were read first and then reproduced: GameCoreParkedName, GameCoreParkedFrom,
    GameCoreParkedPivot (a real CFrame) and GameCoreArchivedFrom.

    WHY READING FIRST MATTERED. GameCoreArchivedFrom names the BAY, not the source. Both shipped
    examples agree - ParkedFrom is Workspace.Consoles.MainReactorConsole while ArchivedFrom is
    Workspace.Rebuild.Originals. A self-consistent guess the other way round would have written the
    source path into both fields: every attribute present, every type correct, and one of them
    carrying no information at all. Nothing would have failed, because nothing reads these fields
    automatically.

    THE GENERAL FORM. A provenance record is a format, and a format described only in prose is
    guessable. Where an example exists, the example is the specification.

130. A BOOT-TIME WARNING CAN BE THE CORRECT SIGNAL RATHER THAN NOISE TO BE SILENCED.

    WHAT HAPPENED. Parking a unit that FacilityBridge maps makes it warn once per boot: missing
    workspace model. The obvious tidying is a fallback that resolves the name out of the archive,
    so the warning disappears.

    WHY THAT WOULD BE WORSE. Not every mapped unit is inert. For the ones whose descendants the
    bridge actually drives, CacheLights and CacheAlarmSounds walk RoomLights, Lights and Alarms and
    assign Light.Enabled or call Sound:Play. A ServerStorage fallback would hand back instances that
    accept those writes and do nothing, so the bridge would report success while the facility
    stayed dark and silent - the failure CLAUDE 0.13 describes, where the error path and the success
    path have the same shape.

    WHAT THE WARNING ACTUALLY IS. It is emitted exactly while a parked unit has no Mk2 at its old
    path, and it stops by itself when the Mk2 is installed under the original's own name. It is a
    per-unit statement of what the parking pass still owes, which is the pairing the operator asked
    for. The self-test's bridgeResolved count says the same thing numerically: 18 entries, 17
    resolved, one unit waiting.

131. A CLIENT-SIDE WRITER OF A SERVER-OWNED PROPERTY WINS FOR AS LONG AS IT AGREES, SO ITS DISAGREEMENT READS AS A UNITS BUG RATHER THAN A SECOND WRITER.

    WHAT HAPPENED. StarterPlayer.StarterPlayerScripts.VisualFeedback, a 148-line LocalScript with
    Disabled = false, wrote LeverUnion.CFrame and NeonPart.Color on every Heartbeat. It was a second
    writer of the exact parts ReactorBackend.VisualFeedback owns, and it won, because a client-side
    write is not overwritten until the server next changes that property.

    WHY IT READ AS A UNIT ERROR. The two sides disagreed by |delta| = 50.000 exactly, along the
    union's own LookVector. Fifty is Config.Visual.LeverArcDegrees being spent as a stud distance -
    the variable in that script even carried the comment "repurposed as travel distance in studs".
    Six fan levers stood 50 studs off their consoles, and the C-Pump 3 lever sat pinned at its
    authored CFrame on the client while the server held it 0.8 studs out, so a lever that had just
    been clicked appeared not to move at all. A wrong-unit conversion in a second writer is worth
    looking for whenever two observers disagree by a round number that appears in the config.

    WHY A DISABLE AND NOT A DELETE. Disabled = true was written in Edit mode, because a change made
    during a playtest is discarded when that playtest stops. A header records the supersession, so
    the file stays as the record of the client-side approach. Nothing is lost by turning it off: the
    server module covers every lever and lamp this one touched and several it did not, and a server
    CFrame write reaches a client when the part streams in, so StreamingEnabled is not a reason to
    keep a client copy.

    HOW THE SINGLE WRITER IS ESTABLISHED. By measurement, not assertion: a scan of all 126 scripts
    finds exactly two that mention LeverUnion - the disabled LocalScript and
    ReactorBackend.VisualFeedback - and three that mention NeonPart, those two plus
    ServerStorage.Data.DataCollection, which sits in ServerStorage and therefore never runs.

132. A THROW DISTANCE IS A PROPERTY OF THE RIG FAMILY, AND THE TEMPLATE LIBRARY IS THE AUTHORITY FOR THE FAMILIES WITH NO PER-LEVEL TARGET.

    WHAT HAPPENED. THROW_TRAVEL = 1.6 was applied to all 23 console levers, and the motion was
    CFrame.Angles about a marker rather than a slide. Both came from MovingParts.DecayFields: the
    eleven LeverModel rigs there carry 0.500 studs plus 60 degrees, and every one of them is an
    AirlockConsole or GatewayConsole door bar. Not one is a console lever.

    THE AUTHORITY. ReplicatedStorage.Levers is the builder's own template library, four families
    parked at the world origin, 733 descendants: 2Level, 3Level, 5Level, SmallLever. It is the only
    source that says anything about the four controls whose consoles carry no per-level target at
    all. Measured: SmallLever.Up union x 88.225 against SmallLever.Down union x 88.925, so the throw
    is 0.700. Twelve live levers wear that rig - six CFLever, three E_VENTLever, ShuttersLever and
    the two MASS PowerLevers - and all were being thrown 1.600, which is 2.29x the authored distance.

    THE ARGUMENT THAT NEEDS NO SEMANTIC. For the CFLever rigs the old code drew the union at
    U0 + 1.600 LV. That rig's authored stops are U0 - 0.658 LV and U0 + 0.042 LV. 1.600 is not
    between them, so a running fan was drawn at a pose the art does not contain. The same reading
    retires the apparent fans-against-shutters contradiction - both authored on Down with opposite
    engine levels - without inventing a semantic for either.

    THE SIGN RULE. ClickPart is fixed and only the union slides, so moving the union by delta moves
    d = (ClickPart.Position - union.Position) . LookVector by minus delta. The throw from the stop a
    rig sits on to the other stop is d minus that other stop's own offset: +0.700 for a rig authored
    on Up, -0.700 for one authored on Down. Five of the twelve are authored on Up and seven on Down,
    and that is not derivable from the engine's levels. Reading each rig's own d lands a rig parked
    off its stop exactly on both - the CFLevers read -0.408, which is 0.042 short of Down, so they
    finish on the Up stop rather than 0.042 past it.

133. A PROBE THAT SHARES AN INITIALIZATION STEP WITH THE SYSTEM IT MEASURES MUST PERFORM THAT STEP ITSELF, AND A FAILURE UNIFORM ACROSS EVERY CASE BELONGS TO THE INSTRUMENT.

    WHAT HAPPENED. Thirteen lamps and the master start-up lever had been carried as unproven since
    they were wired. The probe was a Server Script, and Server Scripts start in an undefined order:
    it lost a race with Runtime, ran VisualFeedback.Refresh against a module whose levers and lamps
    tables were still empty, and so measured a module that touched nothing. Every poseLever and
    lightLamp returns early when its key is absent, so the probe read each part's authored colour,
    constant across every case - which is exactly what a broken lamp looks like. Every start-up
    comparison read delta 0.0000 for the same reason, and five of them counted as passes because
    nothing had moved while the sixth, starting != cold, counted as a failure.

    THE CASE THAT PASSES IS THE TELL, NOT THE CASE THAT FAILS. Only seven of the thirty-eight cases
    passed, and the two colour cases that passed are what named the fault rather than hiding it:
    "atmo while running" and "cbl1 nominal" both read Nominal, because
    MainReactorConsole.AtmosphereVentButton.NeonPart and CBL1-3Systems.PressureButton.NeonPart are
    authored (137,255,147) and Config.Visual.Nominal was measured off them. A lamp cannot read a
    palette entry by accident unless nothing painted it.

    WHAT WAS PROVEN. shutterLamp closed to Amber, open to Off. muteLamp off to Off, on to Fault.
    atmoLamp cold to Off, running to Nominal, inside its own cooldown back to Off. vent1-3Lamp
    unused to Off, spent to Fault. cbl1-3Lamp Off while inactive, Nominal, Yellow at PW5, Purple on
    stress, Blue below stall pressure, Fault, and all four precedence pairs, each beating the branch
    it must. gravSwitchLamp Idle to Off, Charging and Armed both to Ready. gravArmedLamp Charging to
    Off, Armed to Yellow only. samLamp1-2 Off, then Nominal on both lamps together. The lever moves
    1.686 studs, exactly TRAVEL.start, in the three started phases, and reads delta 0.0000 against
    Cold in the other four, with Running and Stopping deliberately the same pose as Starting.

134. A ROUTINE THAT MEASURES FROM LIVE STATE IS NOT IDEMPOTENT UNLESS IT IS WRITTEN TO BE.

    WHAT HAPPENED. The probe's own Initialize call and Runtime's produced two capture lines in one
    playtest and they disagreed: the first read fan1-6 at -0.658, the second at +0.700. Only the
    first is a measurement. smallThrow reads a SmallLever's sign from the union's current position -
    level 1 is whichever stop the rig is found on - and Runtime's own first Refresh had already
    driven the six fans to their far stop, because the engine boots with the fans running. The
    second capture therefore measured the rig standing on its other stop and inverted the travel of
    every fan for the rest of the session. The lever still moves on a click, it moves the wrong way
    and lands on a pose the art does not contain, and nothing in the console reports it.

    WHAT IT RETIRED. The flapping signs in a boot log had been attributed to the place having
    displaced levers. It had not: an Edit-mode measurement of all twelve SmallLever rigs found 0 of
    12 off their home stops, every rig reading exactly the d the module's own note records - vent1-3
    at 0.2502 against 0.250, mass1-2 at 0.2482 against 0.248, shutters at -0.4501 against -0.450,
    fan1-6 at -0.4078 and -0.4094 against -0.408.

    THE FIX. Initialize no longer empties levers and lamps: a key whose part is still parented keeps
    its first capture, and only a key whose part has gone is re-resolved, so a repeat call is a no-op
    for poses and is safe to call from more than one place. Verified by re-running: the two throws
    lines are byte-identical, and the captures read 54 and 54 where they read 54 and 52.

    THE COUNTER THAT MOVED ON ITS OWN. The SAM lamps are captured by walking the keyboard rather than
    by resolving a path, and their captured increment sat inside the branch that added them, so a
    repeat call counted two fewer than the first. A counter an operator watches for loss must be
    comparable between calls to the same function, and an increment inside a conditional is not.

135. A DERIVED FLAG CAN BE THE RIGHT JUDGEMENT FOR THE OPERATOR AND STILL BE THE WRONG TRIGGER FOR AN EVENT, BECAUSE AN EVENT NEEDS TO KNOW WHICH CYCLE IT IS IN.

    WHAT HAPPENED. `q.up` is `q.clock > 0`, and `q.clock` walks a 12-hour dial that puts 12:00 PM at
    0 - so the flag is false for exactly one minute out of 1440 and true for the rest. As the
    operator's own rule (`B1`: the clock past 12:00PM means the core is up) that is exactly right,
    and it is right for the reason that matters: on a cold start the dial begins at noon, so "not at
    zero" and "has been running" are the same statement. `announceClock` then used the same flag as
    the TRIGGER for "the shift has started", and a trigger has a requirement a judgement does not:
    it must know which pass around the dial it is on. On a run injected with the core already up the
    dial must travel a full circle before it reads past noon again, and the crossing is then a WRAP.
    The recorder announced both, 60 s apart, in the middle of a shift, on 2026-09-26.

    WHY IT IS NOT A ONE-LINE BUG. The false line is indistinguishable from the true one, because it
    is the true one: the same reading, the same transition, the same arithmetic. Nothing in the
    reading itself separates a shift start from a dial wrap - only the state at injection does, and
    that state was available and unused. So the fix is not to sharpen the flag (no reformulation of
    `mins > 0` can order a 12-hour dial, which the code's own comment already says) but to record
    what the first read was and let the event consult it. `clockStartedUp` is that one bit, and the
    fix is inert unless the injection happened with the core up.

    AND THE READING IS NOT THROWN AWAY WITH THE CLAIM. The wrap message carries the raw
    `q.timeText`, and `readQuota` still writes `q.clock` / `q.up` unchanged, so the moment stays in
    the file and can be re-read. Refusing to interpret a reading is not the same act as discarding
    it, and a fix that dropped it would have satisfied every assertion about what is NOT said.

    HOW IT IS HELD. `_tools/build_clock_test.py` drives the shipped `announceClock` against a mock
    clock in both directions - K1 for the mid-shift inject, K2 for the cold opening that must still
    announce - and `_tools/selftest_clock_test.py` breaks each property in turn to prove the harness
    can go red on the assertion that guards it. K4 pins that the moment stays locatable, so the
    cheap over-repair is caught too.

136. WHEN ONE VERDICT COVERS SEVERAL CAUSES, THE SENTENCE THAT REPORTS IT MUST FOLLOW THE CAUSE AND NOT THE VERDICT.

    WHAT HAPPENED. The driver ends a run on the first of four signals: `v.shutdown` (the operator's
    own press, `B3`), then `s.GameActive=false`, `s.MainframeMeltdown=true`, `s.GameFail=true`. All
    four set the same verdict, `user-shut`, and the verdict is correct for all four - it answers
    "who pressed", and "not the driver" is the honest answer to a meltdown. But the SENTENCE that
    reported it hard-coded the primary cause for every branch:
    `the operator shut it down: s.MainframeMeltdown=true`. The line contradicted its own `said`
    field, in the one place the seal is recorded, on a file that contains no shutdown-lever click at
    all.

    WHY THE VERDICT WAS STILL LEFT ALONE. The tempting repair is to split the verdict - a
    `machine-shut` beside `user-shut` - and it is the wrong one. The verdict is a receipt field, a
    HOWTO table row and the subject of four `selftest_driver_test` mutation proofs, and every one of
    those consumers means "who pressed", not "what ended it". Splitting it to make one sentence read
    better would move all of them to say the same thing less precisely. The narrower fix is correct:
    the `said` field already carries the cause, so the sentence only had to stop overriding it. Only
    `v.shutdown` says "the operator"; the three fallbacks say "the shift ended".

    THE GENERAL SHAPE. A fallback path that inherits the primary's wording misattributes the cause,
    and it does so silently because the verdict, the state, the timing and the exit code are all
    right. This is the same failure as `CLAUDE` 0.13's in another costume: two paths that differ in
    what they SAY, with nothing downstream able to tell them apart. The tell here was a sentence
    that disagreed with a field printed twelve characters later on the same line.

137. A DERIVED VALUE MUST SHIP ALONGSIDE ITS INPUT, BECAUSE RE-DERIVING IT LATER IS THE ONLY WAY THIS CLASS OF DEFECT IS EVER FOUND.

    WHAT HAPPENED. The wrap in entry 135 was diagnosed, not guessed. It was found because the
    recorder writes `q.timeText` (the underived string), `q.clock` (the number it parsed to) and
    `q.up` (the conclusion) every time the label changes, and the raw string showed 11:59 AM to
    12:00 PM to 12:01 PM as one continuous march with no reset - which is what rules out a real
    shift boundary and leaves only the wrap. Had the file carried the boolean alone, the same
    evidence would have been unavailable and the two readings indistinguishable, on a run that
    cannot be repeated without the operator's machine.

    WHY THIS IS WORTH WRITING DOWN AS A DECISION RATHER THAN A TASTE. The rule was already stated,
    and it had already named this exact failure - the HOWTO lists "or it wraps at some point" among
    the reasons to keep the underived strings. The design therefore predicted the bug and shipped
    the evidence for it in the same breath, many runs before anyone looked. The lesson is not "raw
    data is nice"; it is that the cost of the third column is a few bytes per change and the cost of
    its absence is an unrepeatable run that cannot be re-read. The same reasoning is why `flow` is
    `sawDown` and why the receipt keeps `kinds` counts beside the events.

138. A MONITOR LABEL IS NOT THE STATE, AND IT GOES BLIND EXACTLY WHEN THE STATE IS MOST INTERESTING.

    WHAT HAPPENED. Phase 48 read `m.temp` and announced that the operator had injected
    mid-shift. The operator said they had injected first and started the core afterwards. The file
    is on their side: `B 1 t=1.34` carries `s.Core.TemperatureVal=0 s.Core.OutputVal=0
    s.Core.RadiationVal=0` with every fan, every coolant pump and every CBL off, and
    `EVT2072-2079 CLICK StartUpLever` -- eight clicks at t=2..13 s -- is the power-on. What made the
    wrong reading look right is one line: `EVT1139 TEXT x.temp ERR F`. The monitors had not been
    booted, so the label being read was printing `ERR F` for the first 99 seconds.

    WHY THIS IS WORTH WRITING DOWN AS A DECISION RATHER THAN A SCRUPLE. The wrong source was the
    only CONTINUOUS one. `m.temp` runs t=98.8 to t=868.9, the whole shift; `s.Core.TemperatureVal`
    covers the cold start and then freezes at 9420 at t=97.90. A reader who wants a temperature
    curve reaches for the series that spans the run, and that series begins exactly where the part
    that was asked about ends. Neither source is wrong; each is blank over the half the other one
    covers, and picking either alone yields a confident answer about the wrong half. The failure
    mode is not carelessness, it is that continuity reads as authority.

    HOW TO APPLY. Before reading a series as a state, ask whether it is a LABEL -- something a
    screen prints, which can print `ERR`, which can lag a tick, and which can be blank because
    nobody turned the screen on. `s.Core.*` is the state; `m.*` is a screen. And when two sources
    overlap, prefer the one that spans the run -- but check first whether a third series already
    spans it. Here one did. `t.ReadingsFrame.TempLabel` runs t=88.53 to t=865.09, 416 samples, and
    compares EQUAL to `m.temp` on every overlapping poll; 394 + 22 = 416, and the 22 are exactly the
    polls where `s.Core.TemperatureVal` still had a value. The numbers never needed splicing -- they
    were one reading recorded twice, through two paths that start at different times.
    (This paragraph replaced a wrong one, 2026-09-27: it spliced `s.Core` 9420 at t=97.90 to
    `m.temp` 9330 at t=98.77 and called it "90 F over 0.87 s = 103 F/s, the same speed the stat had
    been climbing at". That compares a FALL against a RISE, and 9420 is a terminal value -- the
    series never appears again after t=97.90 -- not a waypoint. See PROGRESS 49.4b.)

139. `m.fluct` IS THE TEMPERATURE STEP, AND THAT REWRITES WHAT "STABILITY" MEANS.

    WHAT HAPPENED. 391 of the 393 rows where `m.temp` moved satisfy
    `temp(next) - temp(this) == m.fluct`, exactly; the other two are a read-order artefact (a row
    carrying one tick s temperature and the next tick s fluct). So `temp(t+1) = temp(t) +
    m.fluct(t)`. `m.fluct` is not a second reading sitting beside the temperature. It is the
    per-tick increment, and `m.temp` is its running sum.

    WHY THIS IS WORTH WRITING DOWN. It changes the shape of the model, and it is not a detail that
    can be recovered from the field name. `temp` is an accumulator: there is nothing to fit on it
    and no time constant to read off it. The quantity with a law behind it is `fluct`. It also
    explains the calibration console -- NET STABILITY is showing the derivative directly, which is
    why the operator can be asked to judge a stability reading at all.

    A SECOND CONSEQUENCE, filed here because it is the same measurement. The tick is real: gaps
    between `m.temp` changes are median 1.79 s, mode 2.0 s, p10 1.51 / p90 2.04 at a ~3.3 Hz poll,
    and `m.temp`, `m.press` and `m.fluct` move on the same row and never separately. One physics
    step writes all three. So a derivative taken per poll is fitting the repaint schedule: the
    first attempt at this fit returned R2=0.084 with physically backwards signs for exactly that
    reason, and the same data asked per tick returns R2=0.33 with every sign right. When a series
    moves in quantised bursts, the burst is the sample.

140. AN OPERATOR'S INPUTS ARE A RESPONSE, NOT AN EXPERIMENT.

    WHAT HAPPENED. Fitting the per-tick temperature step on the controls gives, per tick:
    `sum(cblPct)` +5.05 +- 0.42, `coolSum` -58.2 +- 9.7, `fanCount` -32.8 +- 9.4, R2 0.33. The
    one term that is not a control -- the current temperature -- comes back at -0.0068 +- 0.0044,
    indistinguishable from zero across a 6600..14000 F band. But the same fit also puts a POSITIVE
    coefficient on `coolSum*T`, i.e. coolant losing its bite as the core heats up. That is
    backwards, and it is not a small correction.

    WHY. Every control was moved in response to the temperature it is being regressed against. The
    operator turned coolant on because the core was hot, so high coolant coincides with high
    temperature by construction and the interaction term absorbs the coincidence. Twenty-eight
    degrees per second appears in both directions across stretches whose controls differ by one
    fan, because what is being fitted is a person's policy, not the machine's response.

    HOW TO APPLY. Split "can a model be read off this file" into two questions with different
    answers. GAINS: order of magnitude only, and only inside the band that was actually flown --
    `sum(cblPct)` reaches 300 during the cold start where the fit predicts +1104 F/tick and the
    file shows +180, a factor of six, because the CBL s effect saturates above ~75%. STRUCTURE:
    recoverable outright, and the load-bearing results here are structural -- that the temperature
    does not feed back on its own rate. And the honest test is the one that does not pool: inside a
    single control setting the mix cannot confound anything. `(cbl 75, cool 2, fan 4)` spans
    9069..13716 F with a slope of +0.3 F per 1000 F and correlation +0.01: flat, no restoring
    force, over 4600 F. `(75, 1, 3)` over a similar span gives -40.4 with correlation -0.52, i.e.
    tau ~ 45 s. Both are in the file, both are real, and they disagree, so tau is not determinable
    from this run -- and the correct response to that is to say so, not to fit harder.

141. A CONSTANT THE OPERATOR HANDS YOU IS A HYPOTHESIS, AND CHECKING IT IS THE CHEAPEST THING IN THE FILE.

    WHAT HAPPENED. The operator volunteered `一个风扇每tick降低60PSI`. The file was already open,
    so it was checked rather than filed. Twelve fan toggles across the run, twelve correct
    directions, median |delta| = 58 PSI/tick; and one stretch where the operator toggled fan 1 and
    2 four times with cblPct and coolSum held still, in which the pressure slope snapped between
    +58 and -2 -- a difference of exactly 60. The number is right.

    WHY THIS IS WORTH A DECISION AND NOT A THANK-YOU. A number from the operator arrives with more
    authority than a number from a fit and less evidence: it is one person's memory of a system
    they have been running, and it is exactly the kind of figure that ends up in a Config table
    and is never questioned again. It is also nearly free to test, because the operator has
    already spent the run doing A/B tests on the machine -- every control they touched twice is a
    step response they did not know they were performing. Checking cost one query. Believing it
    unchecked would have cost a wrong constant sitting in the remake under a comment saying it was
    measured.

    THE CHECK FOUND THE LIMIT AS WELL AS THE VALUE, which is the part a bare confirmation would
    have missed. The linearity holds to three fans. fan 3->4 toggles give -47 to -62, but the
    fan-4 window at t=310..356 is not a steady slope at all -- it walks -30, -26, -24, ..., -14,
    converging toward zero, i.e. it is a transient that happens to be labelled with the right fan
    count. So above three fans the file neither confirms nor denies saturation, and that is what
    gets written down. A number accepted on authority would have been recorded as linear
    everywhere.

    HOW TO APPLY. Check it before filing it, and report the limit alongside the value. And take
    the units seriously: the operator said "per tick", the file's pressure changes land 1.79 s
    apart and its temperature changes land 1.79 s apart, so the tick in their sentence and the
    tick in the data are the same ~1.8 s. That agreement was not derivable from the file alone --
    the file can only measure its own cadence -- and it means every gain in F/tick or PSI/tick is
    already in the unit they will think in. The same check also says what NOT to generalise: the
    coolant pumps' pressure deltas across five toggles are +0, +11, +4, -102 and -4, so the tidy
    -60 belongs to the fans and does not transfer.

142. A PUBLIC REPO IS A DIFFERENT ARTIFACT FROM A WORKING FOLDER, AND WHAT IT LEAVES OUT IS THE DECISION.

    WHAT HAPPENED. The working folder had never been a git repo. Turning it into one and pushing it
    to a public GitHub repo needed a judgement per top-level entry rather than a single `git add
    -A`, because the folder held 6527 MB whose only sensible destination was 9.04 MB of it.

    WHY NOT JUST ADD EVERYTHING. Three of the four exclusions are not about size at all, which is
    the part a size threshold would have got wrong. 5986 MB of whisper model cache is merely
    wasteful -- rebuildable, and no repo wants it. But 426 MB of unpacked game assets and 104 MB of
    third-party YouTube guides are *within* GitHub's limits and were excluded because they are
    someone else's work, and a rule of "ignore files over N MB" would have published them. The
    fourth, the machine-local vision and permission caches, is excluded because it is state that
    would only ever conflict.

    AND ONE THING THAT WOULD HAVE BEEN LOST SILENTLY. `core.autocrlf` was true, which rewrites
    every .md on checkout. In most repos that is cosmetic. Here the documentation is the artifact
    -- DECISIONS 96 is a bug that turned on two files of equal byte length and different content,
    and the whole doc-verification apparatus of that era was built to notice exactly that class of
    drift. A VCS quietly re-encoding every document would have defeated it at the storage layer
    while every check stayed green. So line endings are pinned in .gitattributes and the repo's
    autocrlf is off, rather than trusting a global Windows default that was set for someone else's
    C# project.

    HOW TO APPLY. Sort every candidate by "is this ours to publish", then "can it be rebuilt", then
    by hard limits -- in that order, because the size filter runs last and only catches the
    cheapest mistakes. Write the reason into .gitignore itself rather than into a commit message:
    the commit message scrolls away, and the ignore file is the one place a future reader looks
    when they wonder why something is missing. And when the artifact is bytes you are on record
    about, pin the encoding instead of inheriting a global default.

    THE PART THAT IS NOT MINE TO DECIDE. Three files under Data/ are verbatim copies of the
    original game's ModuleScript source, and they are now public. That is a legal exposure rather
    than a technical one, so it is recorded as a question for the operator (QUESTIONS P5) rather
    than settled here.

143. WHEN ONE HOST OF A SERVICE IS BLOCKED, THE OTHER DOOR IS OPEN -- AND THE PROOF OF IDENTITY IS THE HASH, NOT THE TRANSFER.

    WHAT HAPPENED. The Phase 51 documentation commit could not be pushed. Five `git push` attempts
    failed, the last three stably at `Failed to connect to github.com port 443 after 21080 ms`. But
    `api.github.com` answered the same minute in 0.43 s. GitHub serves git transport and its REST API
    from different hostnames, and on this machine only one of them is reachable.

    WHY THAT IS NOT A WORKAROUND. Reaching the same content by a different door is a transport
    substitution, not a change to what got published. What makes it safe is that git's tree sha is a
    hash of the entries and their blob shas, so the server computes a value that must equal the local
    `HEAD^{tree}` if and only if the content is byte-identical. The script asserts that equality
    *before* it moves the ref, then reads the tree back and compares all 176 blobs against
    `git ls-tree -r HEAD`. The transfer is not the evidence; the hash is.

    THE PART TO REMEMBER. The resulting commit is NOT the local commit's sha. The author identity is
    replaced with the authenticated user's and a trailing newline is dropped -- and there is some
    header in GitHub's object that a reconstruction does not reproduce: same tree, same parent, same
    author, same timestamp, and the hand-built object still hashes to something else. So local and
    remote now hold content-identical commits with different hashes, and the next push will be
    refused as non-fast-forward. Write that down where it is created, with its one-line fix, rather
    than letting the next person meet it as an unexplained rejection. Content-identical is not the
    same claim as sha-identical, and only the second makes a push a no-op.

    HOW TO APPLY. When a service has separate hosts for its API and its data plane, measure them
    separately before concluding the service is down. Then, if you have to go in by the other door,
    pick an identity check the receiving side computes itself -- a content hash, not a byte count and
    not an echo of what you sent -- and fail before mutating anything if it does not match.

    AND A SMALLER TRAP THAT LOOKED LIKE A FLAKE. The first push succeeded and the second died with
    `UnicodeDecodeError: 'gbk' codec can't decode byte 0x88`. Nothing about the network had changed.
    The local console codec is GBK, `subprocess.run(..., text=True)` uses it, and the first commit's
    message happened to be pure ASCII while the second's contained an em-dash. Read subprocess output
    as bytes and decode with the encoding the *sender* used, not the one the console prefers -- an
    intermittently-working text pipeline is usually an encoding that is right for the first sample.


144. AN UNATTRIBUTED CHANGE MEANS "NOT THIS CLIENT" -- AND THAT IS ONLY EVIDENCE IF THE HOOK IS PROVABLY ALIVE.

    WHAT HAPPENED. The operator asked whether the full start-up sequence had been recorded. The
    states are all there: the capture opens on a fully cold plant (`s.Core.TemperatureVal=0`, every
    fan, every pump and every CBL off, `s.GameActive=false`) and closes on the seal. The operator s
    own clicks are there by name too -- twenty between t=1.95 and t=13.39, ending with
    `EVT2072-2079 CLICK StartUpLever` eight times and followed by `EVT2081 SUBSPACE REACTOR START-UP
    SEQUENCE INITIATED` and `PowerLabel 524 GW -> 3.001 TW`, so the panels confirm they were real
    presses and not an artefact of attaching the recorder. Then, for seventy-seven seconds, the
    plant is configured -- three coolant pumps onto level 1, six fans on, three CBLs onto level 4
    and back to level 2 -- and NOT ONE click is recorded.

    WHY THE ABSENCE IS STILL READABLE. Taken alone, "no click" proves nothing: the client may have
    been out of activation range, or the control may never have been hooked. What makes it readable
    here is a positive control inside the same file -- later, the same three control families DO
    produce clicks (Coolant3-OFF at t=124.30, Fan4/5/6 at t=107-132, CBL*-PW* at t=113-120), and the
    PROMPT count for the whole run is zero, so the presses did not arrive by ProximityPrompt either.
    With the hook demonstrably alive, the earlier silence is evidence. And the SHAPE agrees: the
    three coolant pumps change in the same poll, the three CBLs change in the same poll, and the six
    fans come on in numeric order at 0.30-0.60 s intervals. Hands do not do that; a script does. So
    the machine configured the plant and the operator threw the lever -- which is also why the core
    sits at exactly 0 F for the first 88 s of a 98 s start-up.

    THE PART TO REMEMBER. `UNATTR` is a claim about the observing client, not about the world. It
    becomes a claim about the world only when you can point at the same instrument working elsewhere
    in the same recording. A hook that is checked once, at attach, carries no such guarantee -- its
    value is entirely borrowed from the clicks that did arrive, so the clicks that did arrive are
    part of the evidence, not just the result.

    HOW TO APPLY. Before reading an absence as evidence, look for a positive control in the same
    file: the same family, the same instrument, a different time. And when the shape of the changes
    is available -- lockstep, even spacing, ordinal order -- read it; shape distinguishes a script
    from a hand more cheaply than any instrumentation does.


145. A CONTROL THAT MOVES THE WORLD IS NOT A NEW MECHANIC -- BUT ONLY IF THE WORLD ALREADY HAS BOTH AUTHORED POSITIONS.

    WHAT HAPPENED. The operator asked for the complete start-up flow in this project, naming the room
    lights and monitor power specifically. The engine already owned the whole chain, gated and costed:
    `monitor_power` (which also clears `booted`), `shutters`, `lights`, `mute`, `boot` (refused unless
    monitors are powered and shutters open), `start` (refused unless the boot has finished). All six
    controls were already in `workspace.Consoles` under labels ControlBinder matches verbatim. What
    was missing was that nothing happened to the ROOM: MonitorBootButton, MonitorPowerButton and
    RoomLightButton carry no NeonPart of their own (measured, recorded at the foot of
    VisualFeedback.Refresh), and no script anywhere in the DataModel had ever named `RoomLights`,
    `MonitorUI` or `PowerNeon`. The world half was authored as art and left unwired.

    THE PART TO REMEMBER. The justification for writing world state is not "the user asked for it" and
    not "it looks better" -- it is that the place itself already contains the other position.
    ControlRoomLights is the one cell of Workspace.RoomLights authored dark (20 NeonParts at
    (17,17,17) Transparency 0.50, all 8 SurfaceLights off) while every sibling cell -- SynthRoomLight,
    CRC1-3Lights -- is authored lit at (248,248,248) Transparency 0.25. The two pairs are the same
    fixture in its two authored positions, so writing one from the other is restoring the art rather
    than inventing it. The distinction decides what may be written: Brightness, Range and Face are NOT
    written, because each cell has its own (0.25/32 for ControlRoomLights, 0.25/30 for SynthRoomLight)
    and overwriting them WOULD be inventing light. Reading both positions off the world is what makes
    the write admissible under the standing constraint never to change existing gameplay mechanics --
    no gate, cost or timing in Engine is touched to make this happen.

    HOW TO APPLY. Before adding state to the world, find both authored positions in the place and
    write only the fields where the two positions actually differ. If a field varies for reasons of
    per-cell design rather than on/off, it is not yours to write.

146. AN EMITTER IS FIXTURE DESIGN, NOT LIGHTING STATE -- AND NAME IS THE WRONG WAY TO TELL THEM APART.

    WHAT HAPPENED. The first capture swept up every part in the light cell with Material Neon and
    called them lamps. That collection included eight parts at Transparency 1.00 -- invisible
    housings, each carrying the SurfaceLight that does the actual lighting -- and the first
    applyLights then wrote the off-state transparency 0.50 onto them, which does not dim an emitter,
    it makes it visible. They were only caught because the on-state matrix was read back row by row
    and showed `transp=0.50` where the emitter bodies were meant to be untouched. The fix splits the
    collection STRUCTURALLY -- `FindFirstChildWhichIsA('SurfaceLight')` means emitter, and emitters
    are checked but never written -- rather than by name, which would have been a list of eight names
    that the next art pass invalidates silently.

    THE PART TO REMEMBER. All 64 emitter bodies across the place's light cells sit at exactly 1.000,
    in colours as arbitrary as (255,255,0). That uniformity is the tell: an emitter's own appearance
    is what the fixture is MADE of, not what state it is in. The lamps are allowed to move and the
    emitters are not, and the reason is the same one as 145 -- one of the two has an authored second
    position and the other does not.

    HOW TO APPLY. Classify by structure -- what the part contains, what it is attached to -- whenever
    a property can plausibly be shared by two roles. A name list is a claim about the art that the art
    never agreed to. And read the matrix back: a write that produces a plausible-looking value is
    exactly the kind that goes unnoticed.

147. SET THE FLAG ON BOTH BRANCHES, OR ONE ENGINE STATE LEAVES TWO DIFFERENT WORLDS.

    WHAT HAPPENED. Monitor faces were originally set only inside the powered branch; the unpowered
    branch left Visible exactly as it found it. Entering the place to verify, five monitors were
    holding an idle face and three were holding BootFrame, on monitors the art otherwise builds
    identically. The world was carrying history rather than state: "unpowered" showed whatever the
    last powered phase had happened to put there. Writing both branches -- powered shows its phase's
    face, unpowered hides every owned face -- turns two reachable worlds per engine state into one. A
    twelve-state matrix comparing `Running->unpowered` against `Failed->unpowered` now reads
    DETERMINISTIC: true.

    THE PART TO REMEMBER. A branch that does nothing is a branch that preserves whatever was there,
    which is a dependency on history nobody declared. The single-writer rule is about who MAY write;
    this is the companion rule about who MUST. A writer that owns a value has to assign it on every
    path, not only on the interesting one.

    HOW TO APPLY. For any owned property, ask what the "off" path writes. If the answer is "nothing",
    the value is co-owned by the last thing that touched it. Test it by driving two different states
    into the same branch and comparing the results.

148. A CACHED `require` HANDS BACK A TABLE THAT IS MISSING KEYS -- AND THE CRASH LANDS IN THE CONSUMER.

    WHAT HAPPENED. RoomShell aborted at line 126 with `attempt to perform arithmetic (sub) on number
    and nil`, reading `config.Shell.EmitterTransparency`. The same module's `Shell` table, required in
    the same plugin VM, had exactly three keys -- MonitorPowerOff, RoomLightOff, RoomLightOn -- and the
    diagnostic printed `items(#)=3` while `#config.Source` was 8975 and byte-identical to disk. The
    plugin VM was serving a compiled `Config` from before the fourth key existed. The important detail
    is not that the cache was stale. It is that the failure surfaced in the MODULE THAT READS THE
    TABLE, three files away from the stale one, so the error named the wrong suspect. The remedy was
    to Clone() the Config and RoomShell ModuleScripts into a temporary Folder in ServerStorage and
    require the clones -- a new instance is a new cache entry, so the bytecode recompiles -- then
    Destroy() the folder. Result: `fresh require -> EmitterTransparency=1 ; captured lamps=20
    emitters=8 monitors=7`.

    THE PART TO REMEMBER. This generalises CLAUDE.md 0.3, which says the require cache does not
    invalidate. The sharper form is that a stale require does not throw where it is stale: it returns
    a structurally valid table with keys missing, and every consumer downstream reads nil. So "the
    source is correct, therefore the running code is correct" is unsound in the plugin VM, and a
    byte-identical `cmp` against disk is not evidence that what is loaded came from those bytes.

    HOW TO APPLY. When a value reads nil that the source obviously defines, suspect the cache before
    editing anything. Check with a clone-and-require rather than by reading Source -- reading Source
    shows you the bytes, not the bytecode. And read the error's file location as "where the nil was
    consumed", not "where it was produced".

149. `workspace.Camera` IS A DOT LOOKUP, AND THIS PLACE HAS TWO MODELS NAMED `Camera`.

    WHAT HAPPENED. `rblx_screen_capture` failed with `CameraType is not a valid member of Model
    "Workspace.Camera"` -- because `workspace.Camera` had resolved to an art Model at
    (310.4,136.7,8.5), not to the Camera instance. Renaming that one did not fix it: a SECOND Model of
    the same name at (310.4,136.7,-9.8) took over the lookup, so `workspace.Camera` was still a Model
    even though the first had been renamed. Both had to be renamed before `workspace.Camera.CameraType`
    read back Enum.CameraType.Fixed. Both names were restored afterwards (126 scripts searched, one
    comment hit, nothing bound to either).

    THE PART TO REMEMBER. `workspace.Camera` is not a service getter; it is a find-by-name, and art
    can shadow it. And a fix that appears not to work may simply have uncovered the next instance of
    the same cause -- "I renamed it and nothing changed" is not evidence that renaming was the wrong
    fix, it is evidence there is more than one.

    HOW TO APPLY. Enumerate children and count before asserting that a name-based lookup resolves the
    way you expect. And note that this route is abandoned, not pending: neither capture tool honours a
    camera passed to it -- two different cameras produced BYTE-IDENTICAL images, meaning the tool
    drives the camera itself -- and `capture_device_matrix` fails with `device simulator get failed on
    edit: ... missing argument #1`. There is currently no working way to photograph this place, so no
    claim in this phase rests on an image.

150. WHEN A VERIFICATION ROUTE IS CLOSED, SAY WHICH HALF WAS VERIFIED.

    WHAT HAPPENED. The world side was verified hard: room lamps, emitters, monitor neons and faces
    all read back off real instance properties, twelve hand-driven states each matched their intended
    face, the cold state matched the art, and all seven modules compared byte-identical to disk
    (`cmp` IDENTICAL; md5 `Config 7548d2ef…`, `RoomShell a9c4e7ab…`, both sides). What could NOT be
    verified is the thing the operator actually named -- what happens when the game really runs. On
    this machine `solo_playtest` reports `isRunning: true`, but the plugin registers no server or
    client peer: `get_connected_instances` returns only `edit`, `eval_server_runtime` and
    `execute_luau target='server'` both answer `No "server" peer answered`, and the playtest's own
    prints are unreadable (`get_playtest_output` returns asset-permission errors; `get_output_log`
    returns the EDIT log, timestamps included). Both screenshot routes are closed as recorded in 149.

    THE PART TO REMEMBER. "Verified" is not a property of a phase, it is a property of a claim.
    Reporting a phase as verified when the runtime half was only read off source is the specific
    failure the standing constraint about not pretending to be finished is aimed at, and it is easy
    to commit by accident here, because the instance-state evidence is genuinely strong. Strong
    adjacent evidence does not transfer.

    HOW TO APPLY. Split the report: what was read off the world, what was read off source, and what
    was never observed at all. Write the third list down even when it is embarrassing, and do not
    close the gap by reasoning about it. This is also why RoomShell publishes its four flags through
    StateBridge -- so the next attempt has an instance-state trail to read, instead of needing the log
    that is not available.

151. THE BRIDGE CREATES NODES EXACTLY ONCE, AND SAYS SO.

    WHAT HAPPENED. StateBridge was written as a compatibility adapter: it publishes into nodes the
    place already has and never creates anything. The four start-up flags -- Lights, MonitorPower,
    ShuttersOpen, Booted -- had no node under Workspace.Stats to publish into, so a single `ensure()`
    helper was added that creates the BoolValue if it is absent, and only then. The alternative was to
    leave the chain with no instance-visible trace, which would have made the whole feature readable
    only through module state -- the exact thing CLAUDE.md 0.2 forbids reading.

    THE PART TO REMEMBER. This is a deliberate exception and the module header says so, because an
    adapter that silently creates whatever it is asked to write stops being an adapter: a typo in a
    node name becomes a new node instead of a missing-node report, and the failure mode inverts from
    loud to silent.

    HOW TO APPLY. When an adapter must create, keep it one narrow named helper with the reason in the
    comment, so the exception is greppable and the rule it breaks stays legible.

152. A LINE YOU CANNOT UN-WRITE MUST NEVER BE WRITTEN -- SUPPRESSION IS A HOLD, NOT AN ERASURE.
    The room watcher has to separate operator events from ambient motion in a place that has both, and
    the first design tried to do it after the fact: write every line immediately, and when a key had
    moved often enough to prove it was decoration, tombstone its history and report how many lines
    were erased.

    MEASURED, AND IT DOES NOT WORK. The sink APPENDS, so by the time the ninth move tripped the rule,
    moves one through eight were already flushed. Two files carry the proof, and they are consecutive
    runs of the SAME design: Data/roomwatch_run4/changes.log (8,857,672 bytes, 18,365 lines) contains
    the three tombstones it wrote in place of the history --
    "...CONTINUOUS, moved on each of the last 9 scans -- its first 8 line(s) erased, suppressed until
    it is quiet for 5"; Data/roomwatch_run5/suppressed.txt then tallies "# 1942 key(s) suppressed as
    ambient" over rows reading "[144 change(s) by t=12.0s, 8 line(s) erased]" while run5's own
    changes.log was 7,624,702 bytes and 15,733 lines -- the erasure was real in memory and invisible
    on disk. A design that can only work if the file system cooperates is not a design; the append was
    not a limitation to route around, it was the specification.

    CITATION CORRECTED 2026-09-27. This entry used to read "run 4's suppressed.txt honestly reported
    1,891 keys at '8 line(s) erased' while changes.log was still 7,557,244 bytes and 15,527 lines",
    and three things were wrong with that sentence. run4 has NO suppressed.txt at all -- that file
    first exists in run5, so the sentence named a file that does not exist. The byte and line counts
    match no file on disk (run5 is the nearest at 7,624,702 / 15,733; run4 is 8,857,672 / 18,365).
    And 1,891 belongs to a DIFFERENT and LATER design -- it is Data/roomwatch_run11/suppressed.txt's
    "# 1891 key(s) judged ambient: moved more than 8 times without going quiet for 5 scans", i.e. the
    hold design this entry argues FOR, quoted as evidence for the erasure design it argues AGAINST.
    The argument was right and its evidence was assembled from three runs while reading as one. Serves
    as the reminder that a number in a decision is a citation: check it resolves to a file.

    REPLACED BY A HOLD. Every key keeps a ring of its recent lines un-written, capped at NoisyAfter.
    A key that fills the ring is ambient: the ring is dropped and the key is named in suppressed.txt.
    A key that instead goes quiet for QuietScans is an event: the ring is written out in order. Nothing
    is ever un-written, so nothing has to be recovered, and the failure mode of the whole mechanism --
    dropping an event -- is bounded by ring size and disclosed by file rather than by absence.

    HOW TO APPLY. When a sink is append-only, erase-after-the-fact is not a slower version of correct,
    it is a different program that reports success while doing nothing. Withhold first.

153. AGE IS NOT EVIDENCE THAT A SPINNER IS NOT A CLOCK -- THE RING FILLING IS.
    The first hold design promoted a key to "an event" a fixed number of scans (12) after its first
    move if it had not overflowed the ring by then. That reads as the conservative choice and is the
    opposite: it certifies a key before the key has had a chance to say what it is.

    MEASURED. Run 6 ran the fixed clock: 90 seconds produced 1,045 lines, led by two ChamberFan keys at
    47 and 46 lines each, whose first move was followed by a 32-second gap. They were judged events
    during the gap and then logged every move for the rest of the run. Removing the clock and letting
    only ring overflow decide -- with release on five quiet scans as the other half -- gave 232 lines
    over a comparable window, with 1,943 keys named in suppressed.txt.

    The two halves are not symmetric and that is why both exist. Overflow is proof of decoration and
    can be acted on at once. Going quiet is proof of an EVENT and only exists afterwards, which is why
    it is measured from the last move rather than from the key's age.

    HOW TO APPLY. When classifying a stream you cannot rewind, prefer the test that only fires on
    positive evidence over the one that fires on the absence of it -- a timeout is a guess about what
    has not happened yet.

154. A DIAGNOSTIC THAT DIES FROM ITS OWN BUG IS WORSE THAN NO DIAGNOSTIC -- SO IT WATCHES ITSELF.
    The watcher's scan loop lives in a spawned thread, so nothing awaits it and nothing catches it. When
    an arithmetic-on-nil in releaseQuiet killed the loop on the first tick of run 7, the only symptom
    from outside was that two files had been written and a third never was -- indistinguishable from a
    watcher that is running correctly and finding nothing. That is the same shape as the defect
    recorded in CLAUDE.md 0.16 (the runtime half was unreadable, so "not verified" and "not working"
    looked alike), except here the missing evidence was the instrument's own output.

    WHAT CHANGED. scan() is wrapped in pcall; a failure writes error.txt to the same sink as every other
    artifact, warns once, and sets a `fatal` field that Status() reports. The run is then readable from
    disk, which is the one channel that survives the session.

    HOW TO APPLY. Any long-lived diagnostic process should be required to say why it stopped. Silence
    from a monitoring tool must never be the same bytes as health.

155. THE SHUTTER TRAVEL WAS NEVER MISSING -- THE SEARCH WAS POINTED THE WRONG WAY.
    Phase 52 recorded that the control room shutter travel "cannot be measured" and declined to invent
    it. Both halves of that conclusion were wrong. The thing that retracts is not the Glass, it is the
    shutter Model; and the travel is not inside the glass's own frame, it is INTO THE WALL BESIDE IT.

    The operator gave the number -- descend 10.58 -- and the world confirms it independently: all three
    shutters sit closed at Y ~ 282.199 and open at Y ~ 271.619, a difference of exactly -10.5800. It is
    not a round number precisely because it is not a guess; 10.58 puts the top of the 10.650-tall Glass
    flush with the sill at 276.7.

    The subtraction is a world Vector3 and not `CFrame * CFrame.new(0,-travel,0)`, because the middle
    shutter's Frame is rotated 90 degrees about Y and there is no reason to depend on its local Y
    happening to coincide with the world's.

    HOW TO APPLY. "Cannot be measured" is a claim about the search that was run, not about the world.
    Say which search was run and what it covered, so the next reader can tell an absent value from an
    absent idea.

156. SEVEN IDENTICAL DUMPS ARE NOT SEVEN PIECES OF EVIDENCE.
    Phase 53's watcher writes a per-run instance dump, Data/roomwatch*/inventory.txt, 5,278,228 bytes.
    All seven runs produced a BYTE-IDENTICAL copy -- the same md5, the same length -- because it is a
    snapshot of a world nobody edited between runs. Committing all seven would have added 37 MB of one
    file to a repository that Phase 51 had just shrunk from 6527 MB to 9.04 MB.

    The dump is ignored; the derived answer is not. rooms.txt (5.7 KB) carries the coverage numbers
    the dump exists to support, and it is tracked -- and it too came out byte-identical between run 6
    and run 8, which is an independent check that the coverage does not drift run to run. The dump can
    be regenerated by running the watcher again; the fact that the seven copies agreed is recorded
    here, so the agreement survives even though the redundant bytes do not.

    The files stayed on disk. Ignored is not deleted.

    HOW TO APPLY. Before tracking N copies of an artifact, hash them. If they agree, track one -- or
    none, and track the derivation instead. Redundancy is not volume of evidence; it is the same
    evidence repeated, and it costs the same to carry.

157. A HOOK SEES TRANSITIONS, NOT STATES -- SO A WATCHER THAT ONLY HOOKS IS BLIND AT t=0.
    The audio half of the room watcher subscribes to Sound.Played / Stopped / Ended, because a
    0.73-second clip starts and finishes inside one 1-second poll and polling structurally cannot
    see it. That reasoning is right, and it buys a second blind spot in the same move: a signal fires
    on a CHANGE, so a sound that is already playing when the hook attaches can never produce a
    Played event. It is not a rare edge -- it was the whole ambient floor of the place.

    MEASURED. Data/roomwatch_run11/audio.txt (the first audio run) held one line, a STOPPED, and no
    PLAYED at all, for a sound that
    by the property watch (Data/roomwatch_run11/changes.log t=23.93 "...FanSFX.Playing | true | false") had been audible
    from before the watcher finished attaching. Two candidate explanations, and one sample could not
    separate them: (a) the hook cannot see the state it attached into, or (b) Pitch=0.00 meant the
    sound never really started. So the probe played a sound that was stopped, had a SoundId and
    Pitch=1.00, and let the engine rule: PLAYED at t=6.08, ENDED at t=6.81. ENDED minus PLAYED is
    0.73 s, the clip's own length. (a) confirmed, (b) refuted. 280 Sounds under the 43 roots, of
    which 23 were Playing before anything attached.

    THE FIX IS THE SECOND PATH, NOT A BETTER HOOK. attachAudio reads Playing once at attach time and
    emits its own ALREADY-PLAYING event, and reads the asset id and SoundGroup off the instance
    rather than off a Played event that does not exist. Two mechanisms covering one subject is the
    point: the hook gets short clips the poll cannot see, the poll gets state the hook cannot see,
    and each one's absence is evidence about the other.

    AND THE FIX EXPOSED A THIRD BUG IN MY OWN TALLY, which is the sharper lesson. The tally printed
    one row per sound and filtered rows on "plays + stops + ends > 0". The ALREADY-PLAYING path adds
    none of those three, so all 23 pre-existing sounds printed no row, the "[ALREADY PLAYING AT t=0]"
    marker was unreachable code, the header read "1 of them have been audible" against 24 audible
    sounds, and the roll-up said "plays by bus: Interactables=1" while EnvironmentSounds hummed.
    A filter written for one kind of row was silently excluding the other kind -- and the failure
    looked like a quiet room rather than like a bug.

    HOW TO APPLY. When one subject is observed two ways, count each observation with the test that
    matches how it was made, and never let one kind of record be filtered out by a predicate written
    for the other. Ask of every counter: what does zero mean here, and can the thing it counts
    arrive by a path that skips the increment? Also: a summary that rolls up by "plays" cannot
    summarise a stream that includes things that never played.

158. A CITATION IN A DECISION IS AN ADDRESS -- IF IT DOES NOT RESOLVE, THE ARGUMENT IS UNSUPPORTED
     EVEN WHEN THE CONCLUSION IS RIGHT.
    Entry 152 argued against erase-after-the-fact and cited "run 4's suppressed.txt honestly reported
    1,891 keys at '8 line(s) erased' while changes.log was still 7,557,244 bytes and 15,527 lines."
    Three separate things were wrong with one sentence. Data/roomwatch_run4/ has NO suppressed.txt --
    that file first exists in run 5, so the address pointed at nothing. No file on disk has those byte
    and line counts (run5's changes.log is 7,624,702 / 15,733; run4's is 8,857,672 / 18,365). And
    1,891 is Data/roomwatch_run11/suppressed.txt's count for the HOLD design -- the design 152 argues FOR -- quoted as evidence
    for the erasure design it argues against.

    The conclusion survived because it was re-derived from the files while correcting this: run4's
    changes.log really does contain the tombstones it wrote in place of history ("...CONTINUOUS,
    moved on each of the last 9 scans -- its first 8 line(s) erased..."), and run5's suppressed.txt
    really does tally "# 1942 key(s) suppressed as ambient" over rows reading "[144 change(s) by
    t=12.0s, 8 line(s) erased]" while its own changes.log was 7,624,702 bytes. The erasure was real
    in memory and invisible on disk. Right answer, fabricated citation -- and it read as one coherent
    measurement because three runs' numbers sitting in one sentence look like one run's numbers.

    HOW TO APPLY. Numbers in a decision are addresses: resolve them. Where a claim carries counts or
    quotes, name the file they came from, and when a run is renumbered or a directory is archived,
    re-resolve the citations that named it. A wrong citation is worse than a missing one, because it
    certifies the argument and cannot be noticed by reading the argument. Since 2026-09-27 the
    convention is mechanical and checkable: "run N" means Data/roomwatch_runN, and the archive
    directories carry exactly those names, so a grep for the number decides it.

159. AN UNREACHABLE RULE READS EXACTLY LIKE A WORKING ONE -- SO CHECK OWNERSHIP, NOT PLACEMENT.
    Watching the mixer's seven SoundGroups required a propsFor branch for SoundGroup, and while
    adding it I also added one for SoundEffect. That second branch could never run: SoundEffect is
    matched by an earlier elseif in the same chain, and Lua stops at the first match. The dead rule
    was indistinguishable from a live one by reading it -- right class, right property, a comment
    explaining why Enabled matters. Nothing about it looked wrong. The only reliable test is
    structural and does not need a run: in a chain of elseifs, a class tested twice means the second
    test is dead, and a grep for the class name answers that in one line.

    WHY IT MATTERS MORE HERE THAN ORDINARY DEAD CODE. This file's whole contract is "what is watched
    is what the report says is watched". A dead branch in propsFor is a silent hole in a coverage
    claim, i.e. the exact failure the entry above is about, and it would have been invisible in
    exactly the same way: no error, no gap in the output, just a class that reads as covered.

    THE SAME LESSON ARRIVED TWICE IN ONE ROUND, from the other direction. buildAudioIndex assigned
    report.byGroup['Audio'], and coverageReport printed groups by iterating the GROUPS list -- which
    holds ControlRoom and Chamber only. So 77 newly registered instances were counted in the header
    total and detailed nowhere, and the run read as "77 more than last time, unexplained". A tally
    that is written but never read is the same defect as a branch that is read but never reached:
    the writer and the reader each look right on their own.

    HOW TO APPLY. When you add a case to a dispatch chain, grep for the class or key first -- if it
    is already claimed, the new arm is dead. When you add a bucket to a report, check who iterates
    the container it lives in. Both are one-line checks and neither can be done by reading the code
    you just wrote, because the code you just wrote is the thing that looks fine.

160. WHEN YOU HAVE NEVER SEEN THE TREE, THE CENSUS HAS TO COME FIRST -- AND IT HAS TO SAY WHY
     IT CHOSE WHAT IT CHOSE.
    The room watcher for our own place takes five hardcoded roots, and that was right there: we
    have looked at every part of that tree, so the paths are measurements. The watcher for the
    ORIGINAL game cannot do that. Nobody here has seen its tree, and a hardcoded root list would
    turn a guess into an assumption whose failure is silent -- a root that does not exist produces
    zero lines, and "nothing happened" and "the path is misspelled" are the same output. That is
    the shape of every failure this project has already paid for.

    SO THE ROOT IS CHOSEN AT RUNTIME, AND THE CHOICE IS PART OF THE OUTPUT. The watcher walks the
    candidate roots, enumerates them, takes them SMALLEST-FIRST until the instance budget runs out,
    and writes rooms.txt listing which roots it took, which it skipped, the reason for each skip
    ("over PerRootBudget (30000)"), and a one-level drill into every skipped root. Smallest-first
    is deliberate: a 40,000-instance container would otherwise swallow the whole budget and the
    interesting small rooms would never be watched. The reason string is not decoration -- without
    it, a skipped root and a nonexistent root are indistinguishable in the artifact, which is the
    same defect one level up from the one this entry is about.

    VERIFIED IN THE HARNESS, NOT IN THE GAME. The fixture contains a 40,000-part Facility, and the
    suite asserts both that the smaller roots were taken and that the giant is absent from the watch
    -- so the budget rule is shown to be doing something, not just present. What is NOT verified is
    whether 80,000 is the right number for the original, or whether the roots it picks up are the
    control room and the chamber. The first thing to read after a run is rooms.txt, because it will
    say so out loud instead of handing back a quiet, empty file.

    HOW TO APPLY. When you are pointed at something you have never enumerated, spend the first pass
    discovering the shape and writing down the rule you used to choose -- do not encode your guess
    as a constant. And make the skip reason a string in the artifact: a filter that omits something
    without recording that it omitted it is indistinguishable from a filter that found nothing.

161. A WRITE-ONLY VARIABLE IS AN UNFALSIFIABLE CLAIM ABOUT THE OUTPUT.
    This is DECISIONS 159 in the opposite direction. That entry was about a rule that could never be
    REACHED; this one is about state that is written and never READ -- and it is worse, because a
    dead branch at least has a reader that cannot get to it.

    MEASURED. `judged` was declared at line 286, cleared at 723, assigned at 1181 and 1253, and read
    nowhere in the file. Meanwhile suppressed.txt's own header said: "A key that IS in changes.log
    was judged the other way: it went quiet long enough for its held lines to be written out, so
    logging it is not a guess." The document described a judgement that nothing computed. Both the
    sentence and the variable read perfectly well on their own.

    WHAT MADE IT VISIBLE WAS MUTATION TESTING, AND ONLY THAT. Deleting the entire quiet-release rule
    -- the thing that decides which keys are "judged discrete" -- changed NO artifact on disk except
    wall-clock stamps. Every one of the 43 checks stayed green, because every one of them asked
    "is this line in changes.log" and the answer was still yes: Watch.Report() calls drainHeld()
    every 30 scans and flushes ANY ring still held, so a missing release only makes a line arrive
    later, never absent. A stored value with no reader cannot be tested, and the claim it was
    standing in for was therefore untestable too.

    THE FIX WAS TO MAKE THE CLAIM REAL, NOT TO DELETE IT. judgedCount() now counts the keys released
    on quiet AND not also ambient -- the `not ambient` half matters, because an ambient spinner that
    pauses is still ambient and counting it would report "logged" about keys the reader cannot find
    in changes.log. The number is printed in suppressed.txt, the sentence next to it is now true,
    and the release rule finally has an observable.

    HOW TO APPLY. For every variable, ask who reads it. A value that is only ever written is not
    bookkeeping, it is a comment in the shape of code -- and if a document nearby refers to it, you
    have two independent-looking things that are both wrong in the same direction. Mutation testing
    is what finds this class: a mutation that changes nothing is not a wasted mutation, it is a
    measurement of how much of the program is load-bearing.

162. AN ASSERTION THAT HAS NEVER FAILED IS NOT EVIDENCE -- AND THE HALF THAT MATTERS IS THE ONE
     THAT MUST STAY GREEN.
    watch_harness.luau went 43/43 the first time it was ever executed. That result is worth exactly
    nothing on its own: every check in it could have been `check('x', true)` and the output would
    have been identical. So selftest_watch.py breaks the shipped watcher thirteen ways and requires
    the matching check to be the one that turns red.

    TWO RULES MAKE IT WORTH RUNNING. First, every mutation names a check that must STAY green as
    well as one that must go red -- without that, a mutation which simply destroys the watcher
    satisfies "the target check went red" while proving nothing about whether the check measures
    the right thing. Second, every mutation's anchor string must occur EXACTLY ONCE in the source,
    and a non-unique anchor is reported as a failure of the TEST rather than skipped. That rule is
    not hygiene: an anchor that matched twice once wrote an entire function into the wrong block and
    the module stopped exporting it, with no symptom until a pcall failed silently every tick.

    IT ALSO CAUGHT TWO THINGS I DID NOT PLAN FOR. M1 (the quiet release never fires) was initially
    NOT DETECTED -- and that finding, followed up, produced the entry above. And the ordered-release
    mutation had no absolute invariant to assert against: "changes.log is non-decreasing in t=" is
    NOT a property the watcher guarantees, since a line released at tick 31 can carry a tick as old
    as 26 while a report drain at tick 30 has already written a stamp of 30. Asserting that anyway
    would have been a check that is right about the fixture and wrong about the program. It is
    asserted DIFFERENTIALLY instead -- the mutant's changes.log must differ from the baseline's once
    wall-clock stamps are stripped -- which is always true when the sort is doing something and
    never an invented invariant.

    HOW TO APPLY. A test suite whose every run has been green is a hypothesis, not a result. Before
    trusting it, break the subject on purpose, one property at a time, and check that the right
    assertion is the one that objects -- and that the others stay quiet. When no honest invariant
    exists for a property, compare against a baseline instead of writing down something that is
    merely true here.

163. A FLAG PARSED CORRECTLY AND TESTED AGAIN ELSEWHERE IS A FLAG THAT SILENTLY DOES NOTHING.
    The harness sets DUMP = true when it sees --dump, and then, at the point of writing files, asks
    `arg[1] == '--dump'` a second time. With a path argument -- `lua watch_harness.luau <mutant>
    --dump` -- arg[1] is the path, so the second test is false and the dump writes nothing. No
    error, no warning: an empty directory.

    WHAT MADE IT DANGEROUS IS WHAT IT LOOKED LIKE. An empty output directory reads as "this mutant
    produces no output", not as "the flag was ignored". It was found only because I wanted to diff a
    mutant's artifacts against the baseline and the diff reported every single file as different --
    which was the tool being right, since one side did not exist.

    The fix is to test the parsed state (DUMP) and nowhere else, and to let the output directory be
    named with --out=DIR so two runs can be compared without moving directories around.

    HOW TO APPLY. Parse each option once, into a variable, and never re-derive it from the raw
    argument list at the point of use -- the second derivation has a different notion of what the
    arguments are, and it fails silently in exactly the cases where it is hardest to notice. And
    when a tool produces "nothing", check whether it produced nothing or was never asked.

164. TWO SCRIPTS, ONE SESSION, ONE SPENT ATTEMPT -- A SHARED HOTKEY IS NOT A SHARED
     CONVENIENCE.
    The watcher shipped binding RightShift to "write every file out now". TRG_original_
    recorder.luau binds RightShift to SEAL -- it ends that recording and stops the collector.
    Both scripts are meant to run side by side, injected into the same session, on an attempt
    the operator has said can be made only ONCE. So the key an operator would press meaning
    "flush the watcher" was the key that discards the recording, and the cost of the mistake
    is the whole run.

    NOTHING COULD HAVE CAUGHT THIS BUT READING BOTH FILES. The watcher's own suite cannot see
    it: the key does nothing until a human presses it, and what it does then happens in the
    OTHER script. The recorder's suite cannot see it either -- from inside that file, RightShift
    is doing exactly what it was written to do. Every test on both sides is green in this
    configuration. It is invisible at exactly the seam where two independently-correct programs
    meet, which is the class of defect that no amount of testing one program can reach.

    THE FIX IS THAT THE WATCHER MOVES, AND THE ASYMMETRY IS THE RULE. Its key is a convenience
    -- press it if you want the files sooner than the next summary tick. The recorder's key is a
    commitment -- press it and the attempt is over. When two functions want the same scarce
    resource, the one whose claim is weaker yields, and that is a property of what each key
    MEANS, not of which was written first.

    A CHECK NOW GUARDS IT, and it is deliberately unusual: it reads the watcher's SOURCE and
    fails if the string KeyCode.RightShift appears anywhere in it. That is not testing behaviour,
    and it is the right instrument anyway -- the property is "this file does not claim this key",
    which is a property of the text. A behavioural test would have to press a key and then go
    look in a different program for the damage.

    HOW TO APPLY. Before running two scripts against the same live session, compare their global
    hotkeys, their global variables and their output paths -- the three places side-by-side
    programs silently collide. When they do collide, decide which side yields by asking which
    one's action is recoverable, and make that side move. And when a collision is found, leave a
    check behind that would catch it returning: a comment explaining it is not a guard.

165. HARMLESS IS NOT A REASON TO KEEP SOMETHING -- HAVING A READER IS.
    The room watcher built in Phase 53 was reviewed on one axis: does it hurt? On that axis it
    scored well. It writes nothing into the world (no assignment to any watched instance anywhere
    in the file), it touches no gameplay, and its cost was MEASURED rather than guessed -- about
    750 ms to build the index once per server start, 19 to 112 ms per one-second scan, a few POSTs
    per second to a sink that is usually not running, and 1,521 signal connections that cost
    nothing until a sound actually plays. Even the sink being down was tested: the loop kept
    ticking and the backlog went out in one go when the sink came back.

    THE REVIEW NEVER ASKED WHO READS IT. The question put to the operator was keep / delete /
    keep-but-off, and all three options take the monitor's usefulness for granted -- they argue
    only about what it costs to have it. The correction that opened Phase 54 changed the fact
    underneath: the monitoring was always meant for the ORIGINAL game, and this place is not the
    original game. Under that fact the AIRemake copy has no reader at all, so every number above,
    however small, buys nothing. It was deleted, and the one-line reason was the whole argument:
    what we are collecting lives in the other game.

    DELETING IT REQUIRED PROVING TWO THINGS, AND BOTH WERE CHEAP.
    First, that the copy on disk really is the copy that was deleted. Byte length is not identity
    -- this project has already been bitten by two files of equal length and different content --
    so the check was character by character, and it was run INSIDE Studio: the disk file was pulled
    back through HTTP into the same VM as the instance and compared against Source directly. Both
    came back identical (68907 and 462 characters). Comparing a hash computed outside the game
    against a hash computed outside the game would have been a tautology of the kind this project
    has a standing rule against.
    Second, that nothing binds the name. A grep over every script in the DataModel had to return
    only the file's own self-references, and it did. Note how close this is to the RS/SS rule: an
    unreferenced thing and a thing whose only reference sits in a script that never runs are
    indistinguishable if you do not ask where the reference lives.

    THE COST IS WRITTEN DOWN AS TWO SEPARATE LISTS, because "it is gone" is not one fact. Lost: the
    default-on capture in this place, and with it the ability to read what a running session did
    there. Kept: both files in _tools with their install notes, the seven artifact runs, and every
    number Phase 53 recorded. The replacement is the files themselves, which is what makes this a
    move rather than a removal.

    HOW TO APPLY. Establish that something has a reader BEFORE measuring what it costs -- a cost
    measured against the wrong axis is precision without a purpose, and it will read as diligence.
    When you remove something from the live place, make it reversible first: prove the disk copy is
    identical character by character from inside the same VM, and prove nothing binds the name.
    Then say plainly which half was lost and which half was kept, because a deletion reported as a
    single fact hides exactly the part someone will come looking for.

166. ASK THE ENGINE WHICH PROPERTY IT ANSWERS -- DO NOT DERIVE IT FROM THE CLASS NAME.
    The player-GUI reader has to record, for every object on the player's screen, whether that
    object is showing. There are two properties that mean "showing" and which one applies depends
    on the class: a ScreenGui answers Enabled, a Frame answers Visible. The obvious implementation
    is a class test -- IsA('LayerCollector') and Enabled or Visible -- and it was measured in
    Studio before it was written, where the measurement said something the class test cannot use:
    NOTHING ANSWERS BOTH, AND ASKING THE WRONG ONE IS AN ERROR, NOT A NIL.

        LayerCollector (ScreenGui, SurfaceGui, BillboardGui, GuiMain)  Visible -> error,  Enabled -> reads
        GuiObject (Frame, TextLabel, TextButton, TextBox, ImageLabel,
                   ViewportFrame, CanvasGroup, ScrollingFrame)        Visible -> reads,  Enabled -> error

    An error is the whole argument. A wrong guess that produced nil would cost one missing field in
    one record. This one propagates: readGui raises, pollOnce raises, and the sample is not taken --
    so the price of a wrong guess is not a bad reading, it is THE ENTIRE RUN, silently, in a script
    that gets one shot. The class test is also correct-today-and-wrong-tomorrow: it encodes the
    current class list in a form that fails silently the moment a class is added, which is the
    failure shape this project already has a rule against.

    So flagReaderFor probes instead: pcall each property once per object AT REBUILD TIME (not per
    poll), keep the one that answers, and count -- not guess -- anything that answers neither. The
    probe costs one pcall per new object; the poll that follows reads one property per record.

    HOW TO APPLY. When the engine has two properties for one concept, the question "which class
    takes which" is an empirical question and it is cheap to ask. Ask it, and write the answer down
    with the class list you measured, because the day it changes you want a failing probe and not a
    plausible-looking line of data. Being wrong about a property that returns nil costs a value;
    being wrong about a property that raises costs everything after it in the same function.

167. A COST MEASURED ON A MOCK IS A COST OF THE MOCK. COUNT THE PROBE INSTEAD.
    The claim the GUI reader rests on is that it is cheap: one property read per record per poll, and
    a rebuild only when the tree actually changed. The tempting way to test that is to time it. Timing
    it would have measured the mock: the harness runs under stubbed instances with no engine behind
    them, so the number returned would be a property of the stub, and it would have looked like
    evidence.

    So the mock counts instead. FLAG_READS is incremented inside the metatable arms for Visible and
    Enabled -- the only two places a flag can be read from -- and the suite asserts the count:
    one poll reads EXACTLY one flag per record, and a rebuild pays between one and two probes per
    object. That is a statement about the shipped design, which is what was actually in question,
    and it cannot drift when the mock gets faster.

    HOW TO APPLY. Before timing anything, ask what the stopwatch is attached to. If the thing being
    timed is a stub, a substitute, or a different machine, the measurement answers a question nobody
    asked. Prefer counting the operation you claim to bound: a counter is exact, it survives being
    ported, and it fails when the design changes rather than when the host does.

168. ONE FACT, ONE WRITER -- SO THE GUI TEXT IS NOT READ HERE.
    The feature asked for was "collect the player's GUI data", and the player's GUI is mostly text.
    The recorder already has a machine for reading text: the readout walk, with its whitespace
    normalisation, its per-instance and per-key guards, its chatter detection, and its NOISY and
    ANIM verdicts. The new reader could have read the labels itself -- three lines -- and the file
    would then contain two independent opinions about the same string, maintained by two pieces of
    code, which is the exact shape of the double-write bug this project has ruled against before.

    So the split is by namespace and it is deliberate: g.<key> holds an object's own flag and is
    written only by the GUI reader; t.<key> and x.<key> hold a label's text and are written only by
    the existing readout walk. The GUI reader's whole contribution to the text is to hand the labels
    it found to the walk that already knows how to read them, and to record the ones it could not
    take. Both halves were already tested separately, which is the payoff: the GUI suite tests flags
    and membership, the readout suite tests text, and neither one has to be re-derived.

    HOW TO APPLY. When a new subsystem needs a kind of value an existing subsystem already owns, give
    it a namespace and route the value through the owner. A second reader of the same field is not
    redundancy -- it is a second author, and the two will disagree eventually in a way that looks
    like a discovery about the game.

169. A HOTSPOT RANKING BUILT ON ANOTHER PLACE'S PART COUNTS IS PRECISION WITHOUT A PURPOSE.
    Asked why the recorder was slow, this file produced a ranked list of the expensive walks and put
    the lamp matrix first: roughly 1,000 NeonParts, ~8 allocations each, four times a second. Every
    arithmetic step in that sentence was right. The 1,000 was wrong -- it is the count in the OTHER
    place, the AIRemake rebuild, and the recorder does not run there.

    The recorder's own output had the answer the whole time. It reports z.parts = 28 and z.systems =
    20 for the lamp matrix and STATADD = 38 for the stats board, so both walks are negligible. What
    is actually large is READOUTS found = 1115 -- about 1,115 labels walked per poll, roughly 4,600
    reads and pattern matches a second -- and that is where the remaining cost is.

    The error was not in the estimate, it was in the SOURCE OF THE ESTIMATE. A count taken from the
    wrong place is not approximately right, it is a different number with the same units, and it is
    more dangerous than no estimate at all because it reads as diligence.

    HOW TO APPLY. An estimate about a specific running system must quote a number that system
    reported, or a number measured from it -- never a number carried over from its analogue. This
    place and the original game have the same architecture and different contents, and every cost
    question is a question about contents. When the artefact itself publishes the counts, read the
    file before ranking anything.

170. A TEST-REPORT PARSER THAT READS ONE STREAM CANNOT TELL "RED" FROM "NEVER RAN".
    The GUI mutation suite ran all ten mutations and reported, for every single one, that the mutant
    "did not build -- the harness did not load". There was nothing wrong with any of the ten. The
    harness writes its report to stderr and exits 1 when it goes red, and prints to stdout only when
    it goes green, so a failing run leaves stdout empty -- and the parser read stdout. Every mutant
    that was detected correctly was reported as a broken test.

    What makes it worth writing down is which error it imitates: "did not run at all" is the one
    failure that looks like a problem with the test rather than a problem with the subject, so the
    natural response is to go and fix the harness -- which was already correct. The fix is one line,
    parse both streams, and the guard is that the no-output-at-all branch has to say so in its own
    words rather than returning an empty result that reads as success.

    HOW TO APPLY. Any tool whose output is read by another tool must be read from every stream it can
    use, and the empty case must be distinguishable from the negative case. This is the same rule as
    the scripts that write their own death to a file: "quiet" and "dead" must not be the same
    reading, and that applies to the harness reading the subject as much as to the subject reading
    itself.

171. A PIN IS A CLAIM ABOUT THE RUN, AND A NAME MAY ONLY BE PINNED ON EVIDENCE THAT IT EXISTS.
    The watcher chose roots by discovery -- census Workspace, take the smallest first until the
    budget runs out -- and `Pinned = {}` meant the whole run was a gamble on which roots the budget
    would reach. That gamble is real and not hypothetical: TotalBudget is 80,000 against a Workspace
    of roughly 92,000 instances, so the budget is going to run out somewhere, and whether it runs out
    before or after any particular root is not something a one-shot injection should leave to luck.

    The operator closed that hole himself by naming the path -- `game.Workspace.Alarms` -- and that
    provenance is the entire reason the name is allowed in the list. Pinning is a claim that a name
    exists; a name that does not exist has no effect at all, and no effect is exactly what success
    looks like from the outside. A pin invented from a plausible guess would therefore be a silent
    falsehood of the same species as the anchor that matched twice and the module that stopped
    exporting a function: everything reads fine, and the one thing that is missing leaves no symptom.

    What makes the pin honest is that it does not shortcut anything. The census still enumerates every
    direct child, tree.txt still lists all of them, and rooms.txt prints the pinned names on their own
    line, so the exemption is stated in the artefact rather than implied by it. The cost is one
    2,334-instance root out of an 80,000 allowance.

    HOW TO APPLY. Pin by name only names that someone who has read the target has stated, and make the
    product say on its face which names were pinned -- an exemption that is not printed is
    indistinguishable from a bug. When a branch has never executed because its input was always empty,
    treat first execution as untested code and cover it before the one run that matters, not after.

172. A PRODUCT THAT WRITES ITS OWN OUTPUT PATH MAKES A MISPLACED SINK A LIE, NOT A NUISANCE.
    Both injected scripts print the command that starts their receiver in their header comments, and
    that command names D:/rblxTRGproject/Data. The receiver that was actually running had been started
    with a different --dir, so the previous run landed outside Data entirely -- a single file sitting
    in a verify directory, in a place the artefact's own documentation says it will not be. Nothing
    broke. No reader failed. The file was found, byte-identical, and moved.

    It is worth writing down because of how quietly it would have gone wrong later: the sink root is
    not a wire protocol, so no code depends on it, which is precisely why a mismatch produces no error
    at any point. The only thing that would ever have noticed is a person looking for a file in the
    directory the documentation promised -- and the documentation was the thing that was wrong.

    HOW TO APPLY. When a program documents the path its output will appear at, that path is part of the
    contract and a receiver pointed elsewhere makes the documentation false rather than merely
    inconvenient. Before repointing one, measure that nothing reads the old location -- prose mentions
    in a log are not dependencies, and the check is cheap. Compare the moved artefact by hash, not by
    size, for the reason in 96.

173. A RECORDING WINDOW GATES THE TIMELINE, NOT THE WATCH.

    WHAT HAPPENED. The operator bounded the recording: it starts when he presses the start-up lever
    and ends when the shift dial reads 12:00. The obvious reading -- "start looking at the lever" --
    is the wrong one, and the difference decides whether a run with no press can be told apart from a
    watcher that was never injected at all. The scan, the property watch, the counters, the ambient
    judgement and the audio hooks all keep running while the window is shut. What is withheld is the
    two TIMELINE files: changes.log and audio.txt. summary.txt, inventory.txt, audio_tally.txt,
    health.txt and window.txt are NOT gated, and that is what makes the distinction readable -- the
    state files answer "was anything watched at all" independently of whether anything was recorded.

    WHY THE BASELINE IS WORTH THE SCANS IT COSTS. A watcher that only started looking at the lever
    would have no baseline, so its first post-lever line would describe a move away from a value it
    had never read -- a diff with a hole where the "before" should be. The withheld lines are also
    counted rather than silently dropped, so "nothing happened before the lever" and "a lot happened
    and was withheld" are two different files rather than the same blank one.

    HOW TO APPLY. When a window is specified as "record from X to Y", decide explicitly which
    artifacts it gates, and leave the state/diagnostic artifacts ungated on purpose. A gate applied to
    everything turns "the event never occurred" into the same reading as "the observer was absent".

174. PRE-WINDOW EVIDENCE WEARS TWO HATS, AND A COUNT THAT DENIES THE FILE BENEATH IT IS WORSE THAN NO
     COUNT.

    WHAT HAPPENED. Opening the window has to count the lines the rule withheld and then drop them.
    The first version counted `#logLines` and cleared it. The harness then read a product that
    contradicted itself: an OPEN marker stamped t=3 announcing "0 line(s) before this were withheld"
    sitting directly above t=1 and t=2 lines that had leaked past it. The arithmetic was not merely
    short -- it denied the evidence in the same file.

    WHY. A key that is still MOVING when the lever goes down keeps its lines in a hold ring, not in
    logLines; the quiet release writes them out several scans later, i.e. after the window opened. So
    the pre-window evidence lives in two places and the count covered one of them. Counting and
    dropping are also two separate acts, and the suite can now see either one fail alone: one mutation
    removes the count, another counts but does not drop.

    HOW TO APPLY. When you withhold evidence, enumerate every buffer it can be sitting in, not just
    the one the writer touches first -- and make the count and the drop independently testable. If a
    summary number can disagree with the artifact printed underneath it, a reader has no way to know
    which of the two to believe.

175. A STRING PROBE CANNOT SEE A LEAK THAT THE STAMP CAN.

    WHAT HAPPENED. The check for "the withheld lines did not reach the timeline" searched
    changes.log for `QUICK BOOT UP INITIALIZED`. It failed on a CORRECT file, because that same
    string is the `from` value of a legitimate post-window line
    (`TitleText.Text | QUICK BOOT UP INITIALIZED | REACTOR ONLINE`), and it also missed the real
    leak -- the leaking lines were not that string at all. One probe, wrong in both directions,
    which is the worst possible outcome for a check: a false alarm on the good case teaches you to
    ignore it, and then it cannot protect the bad one.

    WHY THE STAMP IS THE RIGHT INSTRUMENT. The property the window actually guarantees is causal, not
    lexical: after the open, no recorded line is stamped before the OPEN marker. A value string may
    legitimately appear on both sides of the boundary -- as a `from` and as a `to` -- so no string can
    express the rule. A timestamp can, because it is the file's own statement of when each line
    happened.

    HOW TO APPLY. When a boundary is under test, assert the ordering invariant the boundary creates
    rather than searching for text you associate with the wrong side of it. Choose the field that
    cannot be quoted: here, the stamp, because the same name/value pair is expected on both sides.

176. TWO IDENTICAL CODE PATHS NEED TWO WITNESSES.

    WHAT HAPPENED. One mutation in the watcher's suite came back NOT DETECTED: dropping the sort from
    the held-line release. The fixture had been extended with two interleaved rings specifically to
    make a sort observable, and the differential still said the artifact was unchanged. The reason was
    not the fixture. There are TWO `table.sort` calls with byte-identical bodies -- releaseQuiet's
    `batch` and drainHeld's `pending` -- and the mutation anchored on the release one while the
    fixture only fed the drain one, because lines still in a ring when the run ends are written by
    drainHeld at Report time.

    WHY THE FIRST WITNESS ALSO FAILED, ONE LEVEL DOWN. A release batch only forms when two keys share
    a release SCAN, and the test is the strict `tick - last > QuietScans`. Two rings whose last moves
    were one scan apart released one scan apart -- two batches of one key each, each already in order.
    The product showed it plainly (`100, 102, 101, 103`: grouped by key), which is what a sort that
    never saw both keys looks like. Equal last ticks is what merges them.

    HOW TO APPLY. When a mutation comes back undetected, first ask whether the mutation and the
    witness are about the same code path -- a duplicated body is a place where the answer can be no.
    Then check that the witness satisfies the exact predicate the code uses, including its
    strictness. A sort needs one drain with two interleaved keys, and "interleaved" is a claim about
    the values, not about the intent.

177. A BACKSTOP GATED ON AN EDGE KEEPS COUNTING THROUGH A RECOVERY.

    WHAT HAPPENED. The down backstop ("the core read as stopped for 40 polls with no end signal")
    was gated on `sawDown`, which is an EDGE: it stays set from the DOWN until something explicitly
    clears it. So the counter kept counting while the core recovered, and fired on a core that was
    demonstrably running. The operator's run is the measurement -- DOWN at t=549.73, back above the
    line at t=567.57, sealed 0.33 s after the recorder had itself emitted the UP, for "having been
    down 40 polls".

    WHY IT IS WORSE THAN A WRONG NUMBER. It stole the ending from the settle path, so the receipt
    named the backstop instead of the relight. A wrong CAUSE is worse than no cause: the receipt is
    the one line a reader trusts when they are not going to re-derive the run, and it is now wrong in
    a way that looks like a measurement.

    HOW TO APPLY. A counter that represents "this is still true" must be gated on a LEVEL test of the
    thing itself, not on an edge that records that it once became true -- and it must reset on the same
    expression the rest of the code uses to decide the thing is over. Watch the reset's shape too:
    "clear, then fall through to the increment" leaves the counter at 1 on a run-state poll, which is
    an off-by-one in every later dwell.

178. "TRIPPED DOWN" IS A CLAIM ABOUT A CORE THAT WAS UP.

    WHAT HAPPENED. The cold-trip arm seals a run whose temperature sits under `LowTripF = 2000` F for
    eight polls. A NEW SHIFT OPENS WITH THE CORE COLD -- the operator said so (A1) -- and a cold core
    is below that line by definition, so a level test seals a file two seconds after inject with
    nothing recorded in it. The `everRan` gate (the temperature has been at or above
    `CoreThresholds[1]` at least once) now stands above every arm that can only be true of a core that
    has run.

    WHY THE HOT ARM DOES NOT NEED IT, AND WHAT IT NEEDS INSTEAD. A core that never ran cannot read
    39000 F, so `everRan` distinguishes nothing at the hot end; there the dwell is what keeps the arm
    honest -- one bad readout is not a verdict. And the hot arm reads the TEMPERATURE, not
    `s.MainframeMeltdown`: that flag is the machine room's meltdown and says nothing about the core
    (D9, measured when it went true at t=719.86 while the monitor read about 13000 F).

    HOW TO APPLY. Before adding a threshold rule to a script that may be injected before the thing it
    watches has started, ask whether the condition is true of a plant that has not started yet -- if
    it is, the rule needs a history gate, not a lower threshold. Keep the history gate below only the
    arms it can help; applying it to an arm that is already impossible on a cold plant is noise that
    hides which line is doing the work.

179. A RECOVERY IS NOT A SHUTDOWN, AND A BOUNDARY WITH TWO ENDINGS WILL ALWAYS MISREAD THE THIRD.

    WHAT HAPPENED. The flow boundary that decides what a run's flow WAS had exactly two outcomes: the
    core goes down (DOWN), and the core comes back WITH SOMETHING LIT SINCE THE DOWN (UP, then settle,
    then seal). The operator's stall-and-rescue was neither -- the core dipped below the line and came
    back with nothing lit in between -- so it fell into the UP path and a shift that never shut down
    was recorded as a shutdown and a restart. His complaint was that the file said those words about
    what was a stall.

    WHY SILENCE WOULD HAVE BEEN THE WRONG FIX. The third state is now named and emitted as RECOVER,
    which clears `sawDown`, emits no UP and does not arm the settle countdown. It is emitted rather
    than swallowed because the earlier failure was not the wrong state -- it was the file SAYING the
    wrong thing, and a boundary that goes quiet when it changes its mind leaves the reader holding the
    last thing it said. The reset also means a second dip needs its own debounce; a recovery does not
    pre-charge the next DOWN.

    HOW TO APPLY. When a state machine has an outcome for "worse" and an outcome for "better because
    something happened", check whether "better because nothing happened" exists -- recoveries are
    usually the unmodelled one, and they are exactly what an operator reports as "I got it back".
    Emit the transition rather than filtering it, and name it in the vocabulary the operator used.

180. A FILE REMOVED FROM THE NEXT COMMIT IS STILL PUBLISHED, SO "WITHDRAW" IS NOT ONE OF THE OPTIONS.

    WHAT HAPPENED. Three verbatim copies of the original game's own ModuleScripts (TRGWeb,
    DataCollection, Summary01) live in Data/ and went out with the Phase 51 push to a public MIT
    repository. The operator was asked whether to withdraw them and delegated the call back. Reading
    the two options carefully changed the question: `git rm` removes them from the NEXT commit, while
    the commit that is already pushed keeps them, and rewriting that history costs more risk than the
    exposure it would undo. So the choice was never "keep or recall" -- it was "keep, or stop
    publishing from here on", which is a much smaller thing than the question implied.

    WHY KEEP. The repository's own README states that the project exists because the original is gone
    and this is its continuation, and the copies are the evidence for that claim. DECISIONS and
    QUESTIONS cite the three files in hundreds of places, so the "about one minute" cost quoted in
    the question was wrong -- one minute covers `git rm`, not the reference sweep. And the operator
    had already published the game's own telemetry file, which is the same judgement made earlier.

    HOW TO APPLY. Before offering "remove it from the repository" as an option, check whether the
    artifact has already been pushed. If it has, say so inside the question -- otherwise the option
    reads as reversible to someone who cannot see the difference, and the answer gets given against a
    false cost. A ledger that records the answer must also record that the history is not recovered,
    or the next reader will believe a withdrawal happened.

181. A DUPLICATED KEY IS A SYMPTOM, SO PROBE IT BEFORE DEDUPLICATING IT.

    WHAT HAPPENED. The recorder's readout index holds 1115 records over 928 keys, so 187 keys carry
    more than one record. The symptom is already visible one layer up: the per-poll animation guard
    trips at 5, and it can only reach 5 because `st.thisPoll` is keyed by record key -- five records
    on one key add five in a single poll. Twelve readouts are then marked dead for the rest of the
    run, and the line left behind blames the game's animation.

    WHY NOT JUST DEDUPLICATE. The two guards in buildReadouts (seenLabel by instance, seen[key] by
    key) READ as airtight, and the file says they are not. Something about the key -- how it is
    built, or which records collide on it -- is not understood yet, and a dedupe applied on top of an
    unknown mechanism repairs the count while erasing the question. The duplicates may also be
    intended, in which case dedupe silently changes a behaviour nobody asked to change.

    HOW TO APPLY. When a count is wrong, ask whether the wrong count is the bug or the evidence of
    one. Prefer the instrument that reports the mechanism over the edit that hides the number --
    especially when the edit is cheap, because cheap edits to unexplained state are how a real
    invariant gets destroyed. The probe must not change collection behaviour, so that the run it
    rides on stays usable whether or not the probe has a conclusion.

182. A CORRECTION IS NOT A FIX FOR THE SYMPTOM IT ARRIVED WITH.

    WHAT HAPPENED. The operator reported a stall that sealed its own recording, and in the same
    message corrected the cold-trip line from 2000 F to 1000 F. The two are unrelated. His capture
    bottoms out at 4316 F -- never within 2300 F of either number -- and the arm that ended that run
    is the 40-poll down backstop, which the receipt names outright. Applying the constant would have
    looked like fixing the report.

    WHY IT MATTERS. A constant moved while a symptom is open reads, afterwards, as an explanation of
    that symptom. The next reader finds a changed number, a closed report and no way to see that the
    backstop was the cause -- and the backstop is the thing that needs attention, because it fires
    when the game has not said anything for 40 polls, which is a different failure from a cold core.

    HOW TO APPLY. When a witness corrects a value in the same breath as reporting a fault, measure
    whether the value could have produced that fault before changing it. If it could not, change the
    value and say so where it lives -- the comment above Config.LowTripF carries the measurement,
    not just the new number. Two changes in one message are two changes; keep them separable in
    the record even when they arrive together.

183. A HARNESS THAT COPIES A NUMBER CANNOT FOLLOW IT; ONLY ONE THAT READS IT CAN.

    WHAT HAPPENED. build_end_test.py carried its own hand-typed copy of the recorder's Config, so
    moving the cold-trip line would have left the dwell test measuring a line the recorder had
    stopped using -- green, and about nothing. The fix extracts the numbers from the shipped
    recorder by text (`__CONFIG__` + extract_config) and derives the fixtures from them, so the
    suite has no opinion of its own to go stale.

    WHY A MUTATION IS NEEDED FOR THIS ONE. Every other mutation in the end suite asserts that
    breaking a guard turns the suite red. This failure is the opposite shape: the guard is fine and
    the TEST is wrong, so it can only be caught by a change that must leave the suite GREEN while
    moving the number it measures. That is what FOLLOW_MUTATIONS is: move LowTripF, require rc=0 AND
    require the new number to appear in the generated states file. Without it, "the suite is
    green" and "the suite is measuring the shipped line" are indistinguishable -- which is how the
    typed copy survived as long as it did.

    HOW TO APPLY. A test may copy a value only if the copy is itself asserted against the source at
    run time. Otherwise read it. And when the property under test is "this test tracks that code",
    the only mutation that can prove it is one that is required to stay green.

184. A STUB THAT ACCEPTS ANYTHING IS NOT A TEST.

    WHAT HAPPENED. The transport probe's first version handed every candidate `(url, body)`.
    syn.request and its siblings take a request TABLE, so on a real executor every working
    transport would have raised and been reported as broken -- the exact inversion of the question
    the probe was injected to answer. The harness stayed green through it, because its stub was
    `function(req) sentB[#sentB + 1] = req.Url ... end` and `('http://...').Url` resolves through
    the string metatable to `string.Url` = nil, so `t[#t + 1] = nil` was a silent no-op that still
    returned `{StatusCode = 200}`.

    WHY IT IS SILENT IN BOTH DIRECTIONS. A permissive stub makes a wrong call look right; the
    string metatable then makes the stub's own bookkeeping disappear rather than error. Two
    independent silences, and the harness read green.

    HOW TO APPLY. A stub standing in for an external API must assert the SHAPE of what it is given,
    not only react to it -- record and check `type(req)`, and assert the fields the real callee
    requires. "It accepted my arguments" is not evidence that the arguments were right. This is
    DECISIONS 183 one layer out: the harness had no opinion about the calling convention, so it
    could not have one that went stale or wrong.

185. THE ABSENCE OF A FILE HAS AS MANY CAUSES AS THERE ARE WAYS TO DIE -- SO BRACKET THE LOAD.

    WHAT HAPPENED. The watcher's first artifact, hello.txt, is posted from inside Watch.Start(),
    which is the file's LAST statement. A whole shift produced no bytes at all, and "never injected",
    "died at load", "died in the census" and "still censusing" are the same reading from the sink:
    an empty directory. The operator can only start the reactor once, so that reading costs a shift
    to re-take.

    WHY THE OBVIOUS FIX IS NOT ENOUGH. Adding a beacon next to hello.txt does not help: both are
    after the load, so they fail together. The beacon's value is entirely its POSITION. It now sits
    before the registration, audio, census and Start code -- everything from line 673 to the end of
    the file -- so the readings separate into: nothing at all (never ran as far as the beacon), only
    the beacon (loaded, died in the module body), both (Start ran, and tree.txt/error.txt split what
    is left).

    HOW TO APPLY. When a reader must distinguish "did not happen" from "died before it could be
    recorded", put the recorder of the event BEFORE the work, not beside the other records of it.
    Then ask what the new artifact cannot see and state that limit in the artifact itself, rather
    than letting the reader assume the bracket is complete.

186. HEALTH BOOKKEEPING BELONGS TO THE CLOCK THAT PRODUCED IT.

    WHAT HAPPENED. The load-time beacon deliberately does not go through post(). post() maintains
    the sink outage counters in run-relative time, and the run's clock does not exist until Start
    re-bases it -- startedAt is 0 until then. A beacon folded into that bookkeeping would measure
    its outage from the wrong origin and write a large negative sink_down_total into the file the
    operator reads hours later to decide what to repair.

    WHY THIS IS NOT FUSSINESS. The beacon exists to make an absence readable. A beacon that corrupts
    the health fields it is supposed to make readable is worse than no beacon, and the failure is
    invisible: the field is present, plausible-looking in shape, and wrong in sign.

    HOW TO APPLY. Before routing a new event through an existing accounting path, check which clock
    that path's units are in and whether the clock exists yet at the new event's time. If it does
    not, send it outside the accounting and say why -- and check that the failure you are bypassing
    is still visible through the next event that does go through it.

187. AN ANIMATION BELONGS TO THE WRITER THAT ALREADY OWNS THE VALUE.

    WHAT HAPPENED. The lever throw moved from an instant CFrame assignment to a TweenService tween.
    Two tempting places to put it already existed in this place: the library the user had just added
    (ReplicatedStorage.Functions.Functions, with TweenModel / MultiTween / TweenModelAroundPivot) and
    a tween relay predating it (ReplicatedStorage.TweeningEvent -> ReplicatedFirst
    .ClientTweenReplicatedFirst, 12 lines). Both route the animation string to the CLIENT.

    WHY BOTH WERE WRONG, ON TWO INDEPENDENT COUNTS. (1) VisualFeedback is the single writer of these
    CFrames -- its own line 4 says so -- so animating them from the client makes two writers of one
    value, and the failure is not cosmetic: this exact arrangement was already retired once, and
    StarterPlayer.StarterPlayerScripts.VisualFeedback carries the recorded symptom in its header
    ("SUPERSEDED 2026-09-26: disabled, not deleted." -- the C-Pump 3 lever sat at its authored CFrame
    on the client while the server held it 1.6 studs along its throw, so a click moved nothing on
    screen; "the client won, because a client write is not overwritten until the server next changes
    that property"). (2) The library does not even work on these rigs: TweenModel errors on all 41
    uniones, none of which has a PrimaryPart; TweenModelAroundPivot always falls through its own warn
    path because PivotOffset is CFrame.new() on all 41, and its offset branch tears the rig apart
    (door<->primary 11.358 -> 5.000 studs); its Part-as-model branch always errors.

    HOW TO APPLY. An animation is a write, so hand it to whatever already owns that value and count
    writers before counting conveniences. A helper library existing is not evidence that it applies
    -- take the census the failure needs (PrimaryPart, PivotOffset) on the actual population, and
    treat "it accepted my arguments" as no evidence at all (183).

188. CANCEL BEFORE CREATE, BECAUSE TWO LIVE TWEENS RACE PER FRAME.

    WHAT HAPPENED. TweenService does not serialize per property. Two tweens alive on one property both
    write it every frame and the winner is decided per frame by ordering, not by which was requested
    last. With a 0.3 s throw behind a 1 Hz signature-gated refresh, a second click or a refresh that
    lands mid-flight produces exactly that state, and the union can come to rest on a detent nobody
    asked for.

    WHY CANCEL AND NOT PAUSE OR IGNORE. Cancel() leaves the part where it is, so the new tween starts
    from the reached pose and the throw continues instead of snapping back to the last completed
    detent. Measured on the real rig: interrupted at 41.8 % of travel, the step across the cancel is
    0.000000 studs, and the union still landed bit-exact on the far stop at t = 13.498 s.

    HOW TO APPLY. Store the live tween on the entry and Cancel() it before creating the next. Then
    verify the seam, not just the endpoints -- "it ended on the right stop" is satisfied by a version
    that visibly jumps.

189. A LEVER'S BASELINE IS THE AUTHORED POSE, SO RE-RESOLVING MUST NOT RE-MEASURE IT.

    WHAT HAPPENED. smallThrow(part) reads the throw's SIGN off the rig's own ClickPart sibling. That
    measurement is only valid while the union is sitting on one of its two stops. A re-Initialize that
    happens mid-throw would re-measure and take an in-between pose as the baseline.

    WHY IT MUST NOT. The sign can invert, and after that every throw on that lever goes the wrong way
    with no symptom at all: a lever that reaches the wrong detent is still a lever that moved, and the
    console still lights. This module is self-healing by design (it re-Initializes when its tables are
    cleared), so a mid-flight re-resolve is a reachable state, not a hypothetical one.

    HOW TO APPLY. When the same instance is resolved again, carry over the old baseline and travel
    instead of re-deriving them. Measured: the offset from the original baseline stayed -0.6578 where
    a re-measure would have read 0.

190. A MISSING CONFIG KEY MUST NOT TAKE THE MECHANISM DOWN, AND MUST SAY SO ONCE.

    WHAT HAPPENED. The throw duration is read from Config.Visual.LeverTweenSeconds. A nil there either
    throws out of TweenInfo.new or, if guarded by an early return, silently stops the levers moving --
    and "the levers stopped" is the feature the user asked for.

    WHY IT IS NOT HYPOTHETICAL. This is DECISIONS 0.15's failure exactly: a stale require in the
    plugin VM handed back a Config table missing a key while the source on disk carried it, and the
    error surfaced in a consumer three modules away. A timing knob is the wrong place for a hard
    dependency.

    HOW TO APPLY. Fall back to the module's own default, and warn ONCE (a per-frame warn is how a real
    message becomes noise). Keep the warning about the knob: say the stops are unaffected, so the
    reader does not go looking for a broke mechanism.

191. A VERIFICATION THAT WRITES THE LIVE WORLD MUST BE ABLE TO PUT IT BACK.

    WHAT HAPPENED. The first behavioural test of the tween called Initialize plus a quiet Refresh on
    the live rig, and only then died -- on task.wait, which the rblx_execute_luau VM cannot yield on.
    Both of those calls are writes: the whole 31-lamp module inventory had been repainted to the quiet
    pose, and the test reported nothing, because the death came after the damage and the error
    mentioned neither.

    WHY IT IS EASY TO MISS. The failure is not the test failing; it is the test succeeding partway.
    Nothing distinguishes "died before writing" from "died after writing" from outside, and the world
    keeps the difference forever.

    HOW TO APPLY. Before a live-world probe, record what the authored value of everything it may
    touch is, and restore to THAT rather than to "unwound" -- then check the restore by reading the
    values back (here: all 21 levers back to their authored CFrame, all 31 lamps matching the
    authored histogram, zero mismatches). Undo is a global stack, so guard it too: re-measure the
    sources it could have touched after each undo (38996 / 10350 -- unchanged) rather than trusting
    Un/Redo's own account of what it did.

192. A VERIFICATION MUST SNAPSHOT THE WHOLE WRITE SET, NOT JUST THE THING IT WATCHES.

    WHAT HAPPENED. Verifying the shutter tween meant calling the shipped RoomShell.Refresh, which
    writes four unrelated families: shutter CFrames, NeonPart colour/transparency, Light.Enabled,
    and monitor ScreenGui.Enabled / Frame.Visible. Watching only the shutters would have been
    enough to prove the tween worked, and would have left two facts unmeasured and the world
    unrestored.

    WHY IT IS EASY TO MISS. The interesting thing is the subject, and the rest of the write is
    "obviously fine". But a controlled experiment needs its control: the first Refresh was sent the
    state the world was ALREADY in, so if anything outside the shutters had moved, the run would
    have been measuring two changes and attributing one of them. It moved nothing -- zero NeonPart
    writes, zero GUI writes -- and that is what makes the three ticks after it a clean measurement
    of the shutters alone.

    HOW TO APPLY. Snapshot by WRITE SET, not by subject: enumerate what the entry point can touch
    and record all of it, including the properties you have no interest in. The same snapshot then
    answers two questions at once -- "did anything else move?" and "can I put it back?" -- and the
    restore check is just the snapshot compared again (here: drift 0).

193. EDIT-MODE HEARTBEAT DELIVERS IN BURSTS, SO PER-TICK DELTAS CANNOT MEASURE SMOOTHNESS.

    WHAT HAPPENED. The first trace of the shutter tween showed 2.707 studs in 11.9 ms, i.e. 227
    studs/s, against a Quad/Out peak of 35.3 studs/s -- 6.4x too fast, and at the worst possible
    place: the first frames, where a jump is exactly what the change existed to remove.

    WHY IT IS EASY TO MISS. Every individual number is plausible. dt is a real clock reading, dy is
    a real position, the tick rate averages 60.5 Hz. What is wrong is the PAIRING. The tween
    advances on the render step while the Heartbeat callback is delivered in bursts, so 111 of 121
    callbacks saw |dy| < 0.005 and the movement piled into the few that did not. Total time and
    total distance stay exactly right while the per-tick picture is pure aliasing.

    HOW TO APPLY. Bin by TIME, not by tick: over 50 ms buckets the worst move was 1.934 studs
    against an analytic 1.763 (and up to 3.53 across a bucket boundary), i.e. inside the honest
    band. Then confirm the macro shape independently -- elapsed time to land (0.583 s of a
    configured 0.6 s) and the fraction of travel at a known wall-clock moment (69.2% at 0.25 s,
    which is Quad/Out at t = 0.267 s). Do not conclude "not smooth" from a per-tick delta, and do
    not conclude "smooth" from a clean landing either. Measure the shape.

194. ASK A GUIOBJECT FOR Visible AND A LAYERCOLLECTOR FOR Enabled. THE WRONG ONE IS AN ERROR.

    WHAT HAPPENED. The snapshot loop did `d.Enabled` on every GuiObject and died on "Enabled is not
    a valid member of Frame Workspace.MonitorsFacility...MainMonitorFrame". It aborted before the
    first write, so nothing was damaged -- this time.

    WHY IT IS EASY TO MISS. Enabled reads like a property every GUI thing has, and ScreenGui -- the
    one instance everybody pictures -- does have it. It lives on LayerCollector, from which
    GuiObject does NOT inherit; the two are siblings under GuiBase2d. Roblox raises rather than
    returning nil, so a defensive `or true` does not save you, and the failure lands wherever the
    loop happened to be standing.

    HOW TO APPLY. Branch on the class instead of guessing one property for all: GuiObject answers
    Visible, LayerCollector answers Enabled, and the two are read and restored separately. This is
    the Phase 55 rule arriving from the other side; the standing form is "walk the tree and ask by
    capability, never by name and never by remembered shape".

195. A HASH THAT CANNOT SEE CONTENT IS NOT A CHECK.

    WHAT HAPPENED. Checking whether a Studio edit had landed byte-for-byte with djb2, the first
    version wrote `s.byte(i)` instead of `s:byte(i)`. In Lua those are the same call: `s.byte(i)`
    is `string.byte(i)`, which hashes the INDEX'S OWN DIGITS and therefore varies with string
    length and with nothing else. It reported MATCH, and the MATCH was meaningless.

    WHY IT IS EASY TO MISS. It fails OPEN. Two unrelated strings of equal length hash equal, so the
    check passes exactly when you want it to, and the only signal is that it never says no. Nothing
    errors, nothing warns, and it is at its most convincing on the comparison you most want to
    succeed.

    HOW TO APPLY. Give every hash function a self-probe on the same call: hash two strings that
    differ only in content and assert they differ (`djb2('abcdef') ~= djb2('abcdeg')` --
    CONTENT-SENSITIVE). Until that probe has run, treat "the check passed" as a claim about the
    check, not about the data. Same family as "never verify disk against disk" (95) and "compare
    hashes, not byte counts" (183): a check that cannot fail is not evidence.

196. src/ IS THE AUTHORITATIVE PREVIOUS VERSION. A ONE-OFF PULL CAN ONLY DISPROVE.

    WHAT HAPPENED. Phase 59 needed the pre-edit Config to prove the new text was the old text plus
    one 512-byte block. The reference used first was _tools/_pull/verify/Config.luau -- 8975 bytes,
    863 short of the live module, because it was pulled on 2026-09-27 and Phase 58 had edited
    Config since. The authoritative reference was src/ReactorBackend/Config.luau:
    `git show HEAD:src/ReactorBackend/Config.luau` measures 9838 / 0x97f981b8, matching the strip
    derivation exactly.

    WHY IT IS EASY TO MISS. A file named Config.luau, in a directory named verify, written when it
    was genuinely current, reads like a baseline. Its staleness is invisible from its contents --
    it is a perfectly well-formed older Config. A pull directory is scratch: it records what the
    live module WAS at one moment, which is not the same thing as what the previous VERSION was.

    HOW TO APPLY. For "what did this look like before I changed it", use the version-controlled
    mirror under src/ or git itself, because both carry the provenance that makes the claim
    checkable. Keep one-off pulls for what they are good at -- disproving, by showing that the live
    bytes differ from a remembered form. Rename stale copies so the staleness is in the FILENAME
    (Config.pre-phase59.luau) and not in somebody's memory.

    NOTE, 2026-09-30: the guard numbers quoted in 191 are the ones true when it was written. Config
    is 10943 since Phase 60 -- read that pair as history, not as a current fingerprint.

197. THE HOOK THAT OPENS THE RECORDING WINDOW MUST NOT WAIT FOR THE CENSUS.
    It did, and the price was the whole power-up. `attachWindow()` sat after `pcall(bootWalk)` in
    `Watch.Start()`, defended by a comment whose stated premise was "the census finishes in
    seconds". The first real run measured that premise false by a factor of five: the census is
    71236 instances / 557548 properties and its first `changes.log` line is stamped **t=47.93s**,
    while the operator throws the lever at **t~20s** -- the recorder brackets `CLICK StartUpLever`
    between `S 40 t=18.11` and `S 67 t=27.03`. The walk to the console the ordering was relying on
    takes fifteen of those seconds, not forty.

    The failure shape is what makes this worth a numbered entry. Nothing was broken: the path
    resolved, the ClickDetector was found, `MouseClick:Connect` returned, and `window.txt` then
    read `lever_hooked=true` **on the same page** as `opened_at=not yet why=(nothing has opened
    it)`. That pair is also exactly what a typo in `LeverPath` produces. A correct hook that is
    28 seconds late and a hook that was never made are one reading, and the operator can spend
    that power-up once -- 「我没办法随便开关机，开机/关机只能一次」.

    The hook is now taken synchronously in `Start()`, before the spawned walk, because it depends
    on nothing the walk produces: `resolvePath` walks down from `workspace` with `FindFirstChild`
    and never consults `ents`, the root selection, or the budgets.

198. A QUEUE CAP APPLIED TO A QUEUE THAT IS NOT BEING DRAINED IS A SILENT DELETION.
    `flush()` posts nothing while `windowState` is 'waiting' -- that is the recording window's
    whole instruction -- but the `MaxQueue` truncation below it runs on every tick regardless. So
    the two mechanisms compose into: while the window is shut, the queue grows and the cap eats
    the front of it. The first real run reported `dropped=794` while its window never opened, and
    those 794 lines are gone. The number is not a rounding error: the run produced 10439 lines in
    46 seconds, **6463 of them in one 10-second bin** around the CBL firing, so a cap of 4000 is
    smaller than a single power-up's peak and every such run loses its beginning.

    Raised to 20000 (~4 MB at the observed 190 bytes per line). The general lesson is the one
    worth keeping: a bound is only a bound if you know which quantity it is expected to be larger
    than, and 4000 was chosen without ever measuring that quantity.

    The two defects in 197 and 198 are coupled in the worst way -- the truncation only bites when
    the window is shut, so it destroys evidence **exactly on the runs whose window failed**. Fixing
    the hook removes the trigger; raising the cap removes the trap underneath it.

199. [RETRACTED -- SEE 201] THE WATCHER'S 12:00 IS MIDNIGHT; THE RECORDER'S BOUNDARY IS NOON.
    THEY ARE DIFFERENT EVENTS.
    The operator settled this the other way on 2026-09-30: 「时钟到达12PM时结束」 makes 12:00 NOON,
    and the watcher now closes on the 1439 -> 0 wrap. 201 states the correction and, more
    usefully, why this entry was convincing while being wrong. Left in place rather than deleted
    because the evidence it cites is correct and it is the reasoning over that evidence that
    failed -- and because a retracted entry that still reads as authoritative is a trap.
    I claimed `EndMins = 720` was wrong -- that the shift hands over at noon, so closing the
    window at midnight ends the recording ten dial minutes into a twelve-hour shift. That was
    wrong, and the evidence I used for it refutes it. `Stats.GameActive` is **false** through the
    whole countdown and goes **true** within two dial minutes of 720 (t=98.47 in
    `original_260926-230049`, t=153.58 in `260927-123212`), then stays true across noon and to the
    end of that run. So midnight is the game's own "the shift has begun" and noon is the handover,
    and the interval the operator asked to record -- 「按下开机拉杆开始记录，游戏时间到12：00结束记录」
    -- is the one that ENDS when `GameActive` goes true. Every observed run was injected at 11:50PM
    (q.clock=710), so the window is ten dial minutes, about two real minutes at the measured 12.3
    real seconds per dial minute.

    What made the wrong reading attractive: `260927-123212` continues to `q.clock=1130` (6:50AM)
    long after 720 with no boundary event, which looks like proof that 720 is not a boundary. It is
    proof that 720 is not a boundary **for the recorder**, which is a different script with a
    different question. One file, two consumers, two boundaries -- and reading the recorder's
    timeline as evidence about the watcher's window is the mistake.

200. A WRONG ORDER CAN BE MODELLED AS A PREDICATE WHEN THE PREDICATE IS EMPTY EXACTLY WHEN THE
     ORDER IS WRONG.
    The mutation for 197 has to restore "the hook is taken after the census" without moving code,
    because the mutation format is one string replace. It is expressed as `if #ents > 0 then
    attachWindow() end`: `ents` is empty until the census registers its first instance, so the
    predicate IS "after the census". The property that makes it a good mutation is that it leaves
    every other scenario green -- the main run's census completes, so the only witness is the
    `--boot` scenario, whose census throws. That is the right witness on the merits and not by
    convenience: a hook that survives a census which never finishes provably did not depend on it.

201. THE WATCHER'S 12:00 IS NOON, NOT MIDNIGHT -- ENTRY 199 IS RETRACTED.
    The operator settled the ambiguity on 2026-09-30 in four words: 「何时结束？：时钟到达12PM时
    结束」. 12PM is noon, so the recording window closes at the 11:59 AM -> 12:00 PM handover,
    which the dial shows as 1439 -> 0 -- and entry 199's `EndMins = 720` (midnight) is wrong.

    What 199 got RIGHT is the evidence, and that is the whole of why it was convincing.
    `s.GameActive` really does go true within two dial minutes of 720 (t=98.47 in
    `original_260926-230049`, t=153.58 in `260927-123212`) and really does stay true across noon
    to the end of that run. The error was in reading that as the window's END. It is the window's
    START: 720 is where the shift BEGINS -- the countdown ending and the core coming up -- and the
    lever the operator opens the window with is thrown at 710, ten dial minutes before it. So the
    window he asked for runs from the lever to the NEXT noon, about 730 dial minutes.

    The shape of the mistake is worth more than the correction. `EndMins` is a name I CHOSE, and
    it silently answered the question for me: a key called `EndMins` holding 720 reads as "the
    minute the window ends", so a measurement showing that 720 is a START arrived already labelled
    as an end. A config name that answers the question you are measuring is not documentation, it
    is a conclusion with no evidence behind it.

    The implementation that replaced it is a FALLING EDGE, not a threshold, and that is forced
    rather than chosen. 12:00PM maps to 0 and the dial counts to 1439 before wrapping, so
    `mins >= 0` is true on every scan of every run; a threshold cannot express the handover at
    all. What is stored is the size of the fall that counts as it (`WrapDropMins = 60`), plus
    `EndPolls = 2` so a single mis-parse cannot spend the one start-up the operator gets. The dial
    is monotonic inside a shift, so the only fall it can produce is the 1439 -> 0 wrap itself; 60
    rather than "the reading is under 5" is what survives a starved poll, since the live dial runs
    at about one dial minute per real second and the watcher's own scan measured 1089 ms -- a
    six-second stall lands the first post-wrap reading at 12:06 PM.

202. THE DRIVER IS DELETED, AND THE REPLACEMENT WAS ALREADY IN THE FILE.
    "不需要什么driver，只需要seal" removes a capability, which is what §1.4 rule 2 is about -- so
    the question is what stands in its place, and the answer was found by reading before cutting:
    the CLICK hook is NOT inside the DRIVER section. It walks every ClickDetector and
    ProximityPrompt in the world (1019 of them) and records each by path. So the operator's own
    presses still reach the file, and they reach it more completely than the driver's did -- the
    driver pressed two switches, the hook records all of them. That read is the reason the
    deletion was safe; it is not a note attached to it.

    What went with the driver rather than being left behind: `ShutdownEndsShift` and `pollDt`.
    Both had exactly one reader and it was inside `driveStep`. A config key with no reader is a
    claim about behaviour that no longer exists, and this project has already paid for leaving one
    in place (§0.13).

    The three driver files are in `_tools/_attic/driver/`, not deleted. The scenarios in them are
    measurements about this game's two switches -- how long the lever takes to arm, what a
    shutdown does to a recording -- and if the driver is ever wanted back, that is the whole of
    what is known. Archiving is not a compromise here: the capability is gone at the operator's
    explicit instruction, and what is kept is knowledge about the game, which was never the thing
    he asked to remove.

    The cost is real and belongs on the record: a shift where nobody presses anything now produces
    a file with no ignition in it. That is acceptable only because the file says so -- the CLICK
    hook records the absence honestly (nothing, rather than a synthesised press), and the core
    gate below means the file has no reactor readings either, so "the operator did not start it"
    is a state the products can be read as, not a suspicion.

203. HOLDING A VALUE AND FILTERING IT PRODUCE THE SAME BYTES UNTIL THEY DON'T.
    The core gate must not write `Stats.Core` before the reactor is on. Two implementations of
    that: hold it (never write it, never touch `last`) and filter it (write it into `last` so the
    change detector knows the value, then decline to emit). They produce byte-identical output --
    until the ignition poll carries a value EQUAL to the pre-boot one, at which point the filter
    sees "no change" and the ignition is never reported at all.

    That is not a corner case here, it is the common one. A cold core's temperature IS 0 and
    `s.Core.PressureVal` sits at its resting value, so the first live sample after the gate opens
    is a small number that can equal the thing being filtered against. The failure is silent,
    plausible, one line long, and indistinguishable from a shift that simply started late.

    So the difference has to be a CHECK, not a comment: G5 feeds the same reading on both sides of
    the gate and requires it to be written, which only the hold implementation does. The general
    rule this is an instance of -- when two implementations differ only on an input you have not
    tried, the test is the input, not the reasoning.

204. AN ANCHOR MUST NOT PIN WHAT THE CODE SAYS, ONLY WHERE IT IS.
    Twice in one harness, and both times the symptom was "red, but not on the check that guards
    the mutation". The gate builder anchored its slice on `local coreLive = false` and asserted
    that exact token, so the mutation "the gate defaults to OPEN" made the BUILDER fail to build
    -- and a builder refusing to build is not the harness catching anything. The mutation was
    being credited to the wrong component, which is worse than not being caught at all: it reads
    as evidence.

    The fix is the same both times: anchor on the declaration (`local coreLive`), not on the
    initial value. The tokens that guard against a short slice exist to prove the SLICE is
    complete, not to pin the recorder's behaviour -- and pinning behaviour inside a test builder
    makes the builder a second copy of the thing under test, which is the failure this project
    keeps re-learning (see the end harness's `LowTripF` FOLLOW case, whose whole point is that a
    typed copy of a number goes stale silently).

    The general form: when a mutation goes red in the wrong place, THE PLACE is the finding. An
    assertion that fails for an unrelated reason cannot be trusted to fail for its own -- and this
    one had been quietly leaving two of the six mutations unevidenced.

205. A HARNESS THAT CANNOT SEE A PROPERTY SHOULD SAY SO, NOT BE QUIET ABOUT IT.
    `selftest_gate_test.py` carries one FOLLOW entry that is not a mutation at all: the gate
    defaulting to OPEN. `reset()` clears the latch at the top of every scenario, so the initial
    value is overwritten before any G-check runs and no check in the file can observe it. The
    first reaction was to delete the mutation as untestable; the better one is to keep it, assert
    that the suite stays GREEN, and assert that the mutant reached the harness (the generated
    states file carries the new declaration).

    Both halves matter. The green assertion is what proves the blindness is the HARNESS's and not
    the runner's failure to apply the edit -- otherwise "it stayed green" is indistinguishable
    from "the mutation never happened", which is the same shape as §0.15's missing-key table and
    §0.17's stubbed `GetAsync`. And writing the blind spot down is how it stays a known one: the
    next person to try this mutation finds the reason instead of a hole, and the thing that
    actually covers it -- the shipped default and the diff -- is named.

    This is the argument the end harness makes about its own FOLLOW class, and the one
    `run_tests.sh` makes about every harness here: a suite that can only go red cannot be told
    apart from one whose checks are all `true`.

206. AN IGNORE PATTERN WRITTEN BY ANALOGY MATCHES NOTHING, SILENTLY.
    `Data/originalwatch*/inventory.txt` was copied from `Data/roomwatch*/inventory.txt` and looks
    correct. It matches nothing: the room watcher's roots sit one level under `Data/`, this one's
    sit under `Data/originalwatch/<run>/`, and a gitignore pattern carries its own number of
    slashes. The consequence is not an error, it is an 11,684,084-byte file in the index and a
    `--stat` line reading 123,423 insertions, with nothing anywhere saying the rule did not fire.

    Two habits fall out. The pattern is `Data/originalwatch*/**/inventory.txt`, and **the rule gets
    verified by `git check-ignore -v <path>`, which echoes WHICH LINE matched** -- that output is
    the difference between "the rule is written" and "the rule applies", and it is a command rather
    than a reading of my own patch. The same distinction as DECISIONS 95 (a hash cannot verify
    itself) and section 0.15 (a stale module hands you a table missing keys): in both cases the
    artifact looks right and the failure is silent.

    Note what this is NOT: the reason for ignoring the file is section 53.8's reason and it has not
    changed -- nothing reads it back, and the derived answers are tracked. What was wrong was only
    whether the rule reached the file. 53.8 also claimed byte-identity across the copies; that leg
    is NOT available here, because there is one original-game run on disk, and the comment says so
    instead of borrowing the argument.

207. A MANIFEST THAT IS NEVER REGENERATED IS A CLAIM ABOUT THE PAST WEARING THE CLOTHES OF AN INDEX.
    `_tools/_attic/MANIFEST.txt` was 84 entries against 105 files. It was honest when it was
    written -- it records what the Phase-47 organisation moved where -- and then it stopped, while
    files kept arriving. The entries it was missing include the three `driver/` files, which is
    precisely the archive that section 1.4 clause 2 ("do not delete a feature without a
    replacement") points a reader at.

    It is now regenerated from the filesystem, sorted, with the date of generation in a three-line
    header. The date is the real change: without it, "is this file current?" has no answer, and a
    reader has to diff it against `find` to find out -- which is how it drifted 21 files without
    anyone noticing. A generated index is only useful if it says when it was generated.

    What did NOT change is that ignored machine state under `_attic/logs/` is excluded. That is the
    same line the file already drew between "a thing the project did" and "a port on this machine".

208. MEASURE THE HUNCH BEFORE ACTING ON IT, EVEN WHEN THE HUNCH IS THE WELL-KNOWN ONE.
    `.gitattributes` pins `* text=auto eol=lf`, so `start_services.bat` checks out with LF endings
    on Windows. That is a textbook batch-file breakage and I was about to add `*.bat eol=crlf`.
    Instead I built two files of the same shape -- a `&&` controlled block, an `if (...)` block, and
    a `goto` with a label -- one CRLF and one LF, and ran both through `cmd /c`.

    Identical output on both, including the `goto`/label case. No exception was added. The
    difference the exception would have made is zero, and it would have been a permanent
    unexplained rule in a file whose other line exists to protect byte-exactness.

    The lesson is not "LF batch files are fine" -- that was measured on ONE machine and ONE shape,
    and the `goto`/label folklore is real elsewhere. The lesson is the order of operations: this
    repo has already paid for a file whose bytes were argued about instead of checked. A hunch that
    is cheap to test gets tested, and a negative result is recorded so the next reader does not
    re-litigate it -- which is the same reason section 0.14 kept its two dead screenshot tools.

209. A NAMESPACE FILTER HIDES A PAGE MOVE, AND A REFRESH MUST NOT LOSE COVERAGE THE OLD ONE HAD.
    Refreshing the wiki snapshot (`reactor.fandom.com`, the calibration source section 7 leans on)
    with the puller's own filter -- `apnamespace=0`, `apfilterredir=nonredirects` -- returned 75
    titles against the 2026-09-18 snapshot's 77. The delta is not decay. Three pages moved, all
    three on 2026-09-22/23, all three confirmed through `list=logevents&letype=move`:

      Power Extraction Assembly (P.E.A) -> Power Extraction Assembly   renamed, 2497 B identical
      Shifts                            -> Category:Shifts             moved,   6126 B identical
      Reactor Components                -> Category:Reactor Components moved,   285 -> 1955 B rewritten

    The two that left namespace 0 are still on the wiki, with their text intact; they are simply no
    longer in the namespace the filter walks. And that is the shape of the trap: a narrow filter is
    not a diff. It answers "75" and you have to already know the number used to be 77 to notice --
    the same silence as DECISIONS 206 (a rule that matches nothing) and section 0.15 (a stale table
    with missing keys). The content did not disappear; the *view* of it did.

    So the snapshot is now ns 0 union 14 -- 104 pages -- and the JSON records what the pull covered
    (`namespaces`, `api`, `pulled`) so that the next reader is not asked to infer the scope from the
    page count. The rule applied is: a refresh may not have LESS coverage than the snapshot it
    replaces. That is why the two Category pages are in even though 27 of the 29 ns14 pages are wiki
    machinery ("Pages with broken file links", "Hatnote templates with errors"). Bounded noise is
    the price; silent loss of the shift-mechanics article is not payable at any price.

    Coverage was checked against the backup, not asserted: every title in the 09-18 snapshot has a
    home in the new one, and exactly two common pages changed text -- the AVB page, where an editor
    deleted the words "poorly written" from "consult this poorly written formula" (no numbers, so
    nothing our calibration rests on moves), and the front page, a cosmetic rewrite that also
    REMOVED the standing notice that most of the wiki is old and outdated. The source did not get
    better because it stopped saying that about itself.

    Two things this entry deliberately does not claim. (1) The artifact cannot be produced by the
    user's `TRGWikiPull.py` as written: that needs `requests`, which is not installed on this
    machine (Python 3.14.7), and it walks ns 0 only. The pull was done through `urllib.request`
    (stdlib, no install, no consent needed for a package). (2) The script was NOT edited to match,
    even though the fix is one line (`apnamespace` -> `"0|14"`), because an edit to a tool that
    cannot then be RUN is an unverified change -- the exact class of thing this log exists to
    refuse. The divergence between artifact and tool is recorded instead, here and in the report,
    and the one-line fix is the user's to take or leave.

210. A TIME-BASED BRANCH INSIDE A WAIT-COUNTED FIXTURE IS A COIN FLIP, AND SHOULD BE TREATED AS A
     BUG IN THE FIXTURE, NOT IN THE SUBJECT.
     `TRG_original_watch.luau` grew three sliced walks, each yielding once the current slice has run
     `MaxBlockMs` of CPU, so a census over ~92k instances cannot freeze the client for its whole
     duration. `watch_harness.luau` drives its mutation timeline by COUNTING `task.wait` calls --
     `STEPS[waits]`, `waits` incremented in the shim -- so every yield the watcher makes is one step
     of a timeline it was never meant to advance. The result was measured, not argued: the same
     UNMODIFIED file reported 73 PASS / 1 FAIL three runs out of four, and 74 PASS / 0 FAIL the
     fourth. The failing check moved with the load on the machine because whether `STEPS[3]` (the
     lever) landed before or after the census depended on how many slices had actually yielded.

     The isolation was three runs, and it is the whole of the evidence: `MaxBlockMs = 100000` (no
     yields) -> 74/0, the shipped `25` -> flaky, `MaxBlockMs = 0` (a yield every 64 instances) ->
     27/47. So the yields were the sole cause, and the fixture was the thing that was wrong.

     Why the fixture and not the watcher: a fixture whose verdict depends on how fast the machine is
     cannot tell a broken watcher from a busy one, and that is the one property a harness sells. The
     watcher's behaviour is CORRECT on a slow machine and on a fast one -- it yields more or less,
     which is what a time budget means. The fixture's assumption ("every `task.wait` is one step of
     the shift") was never true, it had simply never been stressed.

     The fix keys on the one difference that is real rather than incidental: the loop's cadence is
     `task.wait(CONFIG.Interval)` and carries an argument, a slice's yield is `task.wait()` and does
     not. Only the timed wait advances the timeline. Eight consecutive runs then reported 74/0, and
     the harness prints `bare_waits=2`, so the ignored path is provably still being walked -- this is
     "the fixture ignores it", not "it never happens".

211. A TEST THAT A FIX CHANGED NOTHING ELSE MUST BE A MEASUREMENT, NOT AN ARGUMENT.
     Saying "the fixture no longer counts yields" only restores determinism. It does not establish
     the property that actually matters: that a yield budget changes WHEN the watcher works and not
     WHAT it records. That one is cheap to measure and is now measured on every run of
     `run_tests.sh`: run the shipped file, run a copy with `MaxBlockMs` forced to 0 (a yield every
     `SLICE_CHECK` instances, the finest possible slicing), and require the two `changes.log` files
     to be identical line for line once the wall-clock column is stripped. Result on the shipped
     `w61`: 19 lines, identical.

     Three guards are part of the test rather than of the runner, because each of them is a way this
     test could pass while proving nothing. (1) The anchor is asserted UNIQUE before the
     substitution -- `MaxBlockMs` is named in several comments, so a looser pattern could rewrite
     prose and still leave a green run. (2) A baseline log of fewer than five lines fails the test:
     two empty files are trivially identical. (3) The clock column is stripped rather than the
     comparison being loosened -- the two runs are a second apart, and "they differ only by the
     clock" is exactly the claim being made.

     The wall clock is the one column a differential like this cannot avoid, and it is worth saying
     which direction that cuts: the t= field is already run-relative, so the stripping removes the
     ONE field that is a property of when the harness ran and not of what the watcher saw.

212. A DERIVED NUMBER MUST SAY WHAT IT IS DERIVED FROM, AND THE COMMENT THAT SAID OTHERWISE WAS A BUG.
     The health line's `duty` was documented as "the share of the wall clock -- scan plus the frame
     waits inside it, plus the sleep". `scanMs` is `os.clock()`, which is CPU time and does not
     advance while the walk is yielded, so the frame waits are NOT in it and the sentence described
     a quantity nobody was computing. Corrected to say what it measures (the Lua work of the last
     scan against the wall-clock period) and which way the error points (the true period is longer
     than `scan_ms + Interval + sleep_ms` by exactly the frames handed back, so the real share is at
     or BELOW the printed duty).

     The direction matters more than the number. A reader asks "is my machine being eaten?" and the
     safe direction for that question is to overstate, not to understate: printed <= target then
     really <= target, and a run that prints high has earned a second look rather than a verdict.
     The frames handed back are the game's -- that is what handing them back means -- so counting
     them as a cost to the watcher would be counting the cure as the disease.

     This is the same class as the `Interval` comment in the same file, falsified by the same run
     ("the budget below is set to keep a scan near 300 ms" was calibrated on our own place, 30219
     instances, and the original has 71587). Two comments in one file describing numbers that were
     true somewhere else. The remedy is not more careful prose: it is that `w61` PRINTS
     `scan_ms / sleep_ms / duty / yields`, so the next run's own artifacts decide whether the cure
     worked, and no comment has to be trusted for it.

213. THE SEAL BACKSTOP READS THE MONITOR LABEL, AND THE 2026-10-01 RUN IS THE FIRST TIME THAT
     DIFFERENCE COULD BE SEEN. RECORDED, NOT CHANGED -- THE SEAL CRITERIA ARE THE OPERATOR'S.
     `endReason()` takes `local t = last['m.temp']`, so the cold trip, the meltdown arm and the
     40-poll backstop all read the MONITOR's temp label, not `s.Core.TemperatureVal`. That has been
     true since the arms were written; what the 2026-10-01 capture adds is a case where the two
     disagree in a way that decides the run.

     `m.temp` reads 10659 at t=247.14 and 3659 at t=249.07 -- 7000 F in one poll -- and then does not
     change once in the remaining 22 seconds. `s.Core.TemperatureVal` over the same window falls
     monotonically from 10188 to 4911 and crosses the game's own 5600 F running line only at
     S 521 / t=268.51 (5709 the poll before). The seal fires at S 531 / t=271.56 as `core read as
     down for 40 polls with no end signal`. Ten polls separate the core's crossing from the seal;
     the counter that had reached 40 was therefore fed by the monitor label from the poll it froze
     on, not by the core. Stated as a counterfactual, which is the cleanest form of it: had the arm
     read `s.Core`, `downPolls` would have been at 10 at t=271.56 and the run would not have ended
     there. Neither of the operator's two stated criteria (he shut it down / it shut itself down) was
     the trigger -- `GameActive` never went false, and `COREGATE` appears exactly once in the whole
     file, on the way up.

     What is NOT claimed: that the seal was wrong. The core really was cooling and 4911 F is below
     the game's own lowest band, so a seal at that temperature may be correct. What is claimed is
     narrower and checkable from the bytes: the run ended on the monitor's reading, ~19 seconds
     before the core's own reading would have justified the same arm, and the monitor's reading was
     frozen at the time. Whether the backstop should read the core instead is a change to the
     operator's own seal rule, so it is a question (`QUESTIONS.md` P9), not an edit -- and it is
     exactly the shape of thing section 1.4 forbids deciding on his behalf.

     Kept beside the earlier correction in the same file (the `m.temp`-is-not-core-temperature note):
     that one said the monitor is blindest when the core is coldest. This run says the same monitor
     can also FREEZE, and that a rule which counts polls against it inherits the freeze.

214. THE START-UP IS A LIST OF HOLDS, NOT A DURATION AND NOT A TIMELINE. THE SUM IS DERIVED FROM
     THE TABLE RATHER THAN TYPED BESIDE IT.
     The remake's start-up used to be `StartupSeconds=8` and one log line. The original's is a
     16-message chain whose total is not a constant: 91.4 / 112.6 / 114.3 / 151.7 s across the four
     runs that finished it. Replacing 8 with 111 would have swapped a number chosen at the keyboard
     for a number chosen off one run's clock -- the same error, better dressed. So the shipped table
     is HOLDS: seconds from the previous message, not an absolute offset. An absolute-offset table
     would bake one run's head into every later step and would have to be regenerated whenever the
     captures are added to.

     `StartupSeconds` itself was NOT deleted, which is a change from the approved plan. It is now
     computed at the foot of the file by summing the holds, so it can never disagree with the table.
     The plan's argument for deleting it (it has one reader, `Engine:Step`, which the table
     replaces) is still true; what changed is the realisation that leaving a DERIVED value in place
     is strictly safer than leaving a HAND-TYPED one, because the failure mode it removes is two
     sources of truth for one duration. That is the thing the whole phase is about, so deleting the
     field would have been the one place the phase contradicted itself.

     Two estimators were run independently and agree to 0.04 s: the sum of the per-message median
     gaps is 113.4, and the median of the four runs' own end-to-end totals is 113.44. Neither was
     fitted to the other -- the totals were never fed into the medians. Agreement here is evidence
     in a way that a single derivation is not, which is why the script now prints both.

215. THE OLD `StartupSeconds` COMMENT WAS FALSE, AND RE-DERIVING THE CAPTURES IS WHAT FOUND IT.
     RECORDED BECAUSE A COMMENT THAT DESCRIBES A DERIVATION IT DID NOT PERFORM IS THE CLASS OF BUG
     THIS PROJECT KEEPS MEETING.
     The first pass at this table carried the comment "the holds below are the per-gap medians
     across those runs and sum to 96.5". Both halves were wrong. The holds were not the medians --
     24 sat where the median gap is 29.4 and 16.5 where it is 27.2 -- and the true sum is 113.4, not
     96.5. Nobody could have caught this by reading the table, because the table is a plausible
     start-up either way and 96.5 is a plausible sum for it. It surfaced only when
     `_tools/_attic/scratch/startup_chain.py` was extended to compute the medians instead of
     printing per-run chains, i.e. when the claim was made to produce its own number.

     This is DECISIONS 212 arriving again in a different file: there, two comments in the watcher
     described numbers that had been calibrated somewhere else. The remedy is the same and is not
     more careful prose -- the number has to be produced by the same run that prints it. The
     Config comment now names the script and the script now prints the table, so the next person
     can check the claim rather than believe it.

     The general lesson, stated so it can be applied without this phase's context: when a table is
     transcribed by hand from a derivation, the derivation must be re-run before the comment about
     it is written, because a hand-copied table is exactly where a number and its description drift
     apart -- and drift silently, since both halves stay individually self-consistent.

216. THE PANEL WRITES CLONES INTO `LogsFrame`; IT NEVER WRITES THE TEMPLATES.
     `TemplateLogFrame1/2/3` are the original's own saved objects: `Visible=false`, carrying the
     archive's leftover text (`TemplateLogFrame3.TextLabel` reads `E INITIATED`, the truncated tail
     of an earlier session's SEQUENCE INITIATED). Writing into them would have been fewer moving
     parts and would have destroyed the evidence that this chain was ever rendered through these
     three frames -- which is the single most useful thing the place's saved state tells us about
     the panel. So `LogPanel.Refresh` clones the template that matches the event's kind, parents the
     clone to `LogsFrame`, sets `Visible` and `LayoutOrder`, and destroys the previous tick's clones
     first. On exit `LogsFrame` is back to one child (its `UIListLayout`), which is how it was found.

     Two consequences worth having on the record. First, the row colours are a SEVERITY KEY read off
     the templates rather than invented: the three differ only in `TextLabel.TextColor3` --
     0.667,1,1 cyan / 1,0.667,0 orange / 1,0.306,0.306 red -- so the panel's palette is the
     original's, not a choice. Second, `RichText=true` on those labels is what proves the
     `<b>[ALERT]</b>` markup in the captured text is payload rather than a scraping artifact, and is
     why `StartupSteps[i].text` carries the markup verbatim while `kind` is stored separately for
     readers that want to colour or filter without parsing a rich-text string.

217. FOUR ROWS, FROM THE FRAME'S OWN GEOMETRY -- NOT FROM THE FLOOD'S 27.
     `LogsFrame` is 340x365 with a `UIListLayout` of `Padding={0,20}` against 60-pixel templates:
     365/(60+20) = 4.56, so four rows fit and a fifth does not. A separate capture
     (`original_260926-230049`, via `panel_growth.py`) shows the original holding 27 rows at once
     during a duplicate-message flood, which means the original's list is unbounded -- it grows and
     lets the frame clip. That number is real but it is not the answer to "how many should the
     remake show": it is a property of one pathological run, while the geometry is a property of the
     panel. Shipping 27 would have been transcribing an accident.

     What is NOT claimed: that the original scrolls, clips, or retires rows at four. The captures
     cannot say -- see 218 -- and the remake makes no attempt to reproduce the original's overflow
     behaviour, only its visible capacity.

218. ROW ORDER AND INTRA-GROUP ORDER ARE NOT IN THE BYTES, AND ARE NOT PRETENDED TO BE.
     The recorder's `snapshot()` collects every TextLabel under the root, writes `Name=Text` for
     each and then `table.sort()`s the result. A `log.panel` dump is therefore ALPHABETISED: it
     carries which rows are on the glass but not where they sit, and any tool that reads row
     position out of a dump is reading the sort. `_tools/_attic/scratch/panel_dumps.py` exists
     because the opposite was assumed; its header now records that the premise was wrong.

     The same property makes INTRA-GROUP order unobservable in the start-up table. Messages that
     land on the same poll (rows 5/6/7, rows 13/14) appear in the dump in string order, so
     "CALIBRATING before E-VENT" is not measured data. The shipped table's order within such a
     group is arbitrary, and the comment says so. What IS measured is that the group shares a
     timestamp -- and even that is a median: in `260927-111843` the SUBSPACE RIFT line is 9.6 s
     later than the two it is tied with in the other four runs, which the median smooths away.

219. `CONTROL` IS DELIBERATELY OFF THE PANEL. `Engine:Command` logs one `CONTROL` event for every
     accepted command, so the player's own switch throws are in `engine.events` alongside the
     machine's messages. `LogPanel`'s `SHOWN = {ALERT, WARN, ERROR, INFO}` excludes `CONTROL`, so
     the panel shows what the reactor said, not what the operator did. That is a judgement about
     what the panel is FOR, not a claim about the original (which cannot be checked -- see 218).
     The events are not filtered at the source: `engine.events` keeps every kind, and the exclusion
     is one table in the one consumer, so a future reader that wants the audit trail still has it.

220. NO NEW `Stats` FLAG FOR THE START-UP STEP. The four existing flags (`Lights`, `MonitorPower`,
     `ShuttersOpen`, `Booted`) currently have no readers, and adding a fifth unread one would deepen
     the same hole this phase exists to close -- `engine.events` had no reader either. The
     observable surface is the panel's four labels, which are read by the same technique the
     project already requires (read the instance, not the module -- CLAUDE.md 0.2) and have the
     additional virtue of being what the player actually sees. A number nobody reads is not
     instrumentation.

221. THE TWO MESSAGE VARIANTS ARE NOT MODELLED, AND THE REASON IS SECTION 1.4, NOT EFFORT.
     The captures split into two status-message sets (EXCESSIVE ENERGY FLUCTUATION / COMPUTATIONAL
     BENCHMARKS UNSATISFIED / TESSERACT MAINFRAME OVERCLOCK / QPU DEGREDATION on one side,
     ELECTROMAGNETIC ANOMALIES / ANOMALY PROCEDURE OVERRIDEN on the other), plus a
     COMPLETE MAINFRAME CRASH tail in three of the five runs. The branch condition between them was
     never measured. The tail additionally describes permanent loss -- its own text says
     "IN FUTURE ACTIVATIONS" -- which is a gameplay mechanic, and section 1.4's first rule forbids
     changing gameplay mechanics. Both halves of that (unknown condition, forbidden subject) point
     the same way, so the trunk is what ships and the variants are recorded in Config's comment.

     A corollary that is easy to miss: the quorum test that separates the trunk (present in >=4 of
     5 runs) from the variants (<=3) has a visible gap under it -- 4 versus 3, with 35 rows below
     the cut. That gap is what makes the rule checkable rather than a hand-picked end marker.

222. ASSERTION A4 WAS A TAUTOLOGY, AND IT WAS FOUND BY A MUTANT THAT SHOULD HAVE GONE RED AND DID
     NOT. `StartupSeconds` is computed FROM `StartupSteps`, so the original A4 -- "the flip happens
     at or after `StartupSeconds - 0.2`" -- was comparing the table against a value derived from
     that same table. Every hold mutation moved both sides together. With `hold[4] = -24` the chain
     shortened to 48.5 s and A1 through A5 all still passed. This is DECISIONS 95 in a new place:
     the earlier version was a hash computed from disk used to verify disk.

     The fix is A4b and A4c: A4b compares the sum against an independently transcribed literal
     (113.4), and A4c checks it falls inside the envelope the captures actually span (86.3..146.5).
     Neither can move when the table moves. The lesson is narrower than "write better assertions":
     a derived value is not an independent check on its own derivation, and a test suite that passes
     on the wrong table is indistinguishable from one that passes on the right table -- which is
     exactly why the mutant mattered more than the green.

223. SWAPPING TWO INTERIOR HOLDS IS A BLIND SPOT THAT THIS EVIDENCE CANNOT CLOSE. STATED, NOT
     FIXED.
     If two holds are exchanged so the total is unchanged (4/5, for instance), every assertion stays
     green. The cause is structural, not a gap in the test suite: the captures are poll-quantised
     -- the recorder writes only on change, and one quiet stretch in the 2026-10-01 run went 19.3 s
     with no poll at all -- so PER-MESSAGE TIMESTAMPS DO NOT EXIST at the resolution the claim would
     need. There is no evidence to assert against, and manufacturing one (a synthetic timeline
     checked against itself) would be tautology 222 again wearing a different hat.

     The right response is to write it down as a known blind spot rather than to paper over it, the
     same way Phase 62's harness recorded that "the gate defaults open" was structurally invisible.
     A blind spot that is written down is a known limit; the same blind spot left unstated reads as
     coverage.

224. `Engine:Reset` REPLACES THE STATE TABLE ON PURPOSE -- AND CACHING THE OLD ONE FROZE STUDIO.
     `Reset` builds an entirely new `state` table rather than clearing the fields of the current
     one, precisely so that every system fetches the current reference instead of holding a stale
     copy. The verification harness then did the thing the design exists to prevent: it took
     `local S = engine.state` once, called `Reset`, and waited on `S.phase` -- a table that
     `Reset` had already orphaned. The wait never terminated, `Engine:Step` does not yield, and the
     plugin's thread stopped answering every subsequent call including `return 'alive'`. Studio had
     to be restarted. No a-priori reason was violated by the design; the harness cached a reference
     across a documented replacement.

     This is CLAUDE.md 0.2's rule arriving from the other side. That rule says: do not read module
     state, read instance state, because the command bar's `require` hands back a fresh and empty
     module. The failure here is the same root -- state changed containers and the reference was
     not re-fetched -- but it reaches the opposite conclusion about where to look, which is why it
     is recorded separately: "read the instance" is not a rule about instances, it is a rule about
     not trusting a reference across a boundary where it can be replaced.

     Cleanup owed after the restart was `ServerScriptService.ClaudeBench65`, the temporary Folder the
     harness builds to hold cloned `Config`/`Engine` (CLAUDE.md 0.15, the stale-require workaround).
     It turned out not to be owed: the Folder had never been saved, so the restart settled it by
     itself -- a second reminder that a killed Studio discards everything the session did not
     commit. The restart did surface a DIFFERENT leftover that an earlier session HAD saved,
     `ServerScriptService.PanelProbe`, holding clones of `Engine` and `LogPanel`. That one was
     deleted after a character-by-character check (`Engine` 17703/17703 identical, `LogPanel`
     6924/6924 identical) and a whole-DataModel grep confirming no script named it: `Runtime` line
     14 requires `ReactorBackend.LogPanel`, the shipped module. Clones are cheap to rebuild; a
     stale one that nothing names is only a thing to re-explain later.

225. A SENTINEL IS THE ONLY ASSERTION AN INLINED CONSTANT CANNOT PASS.
     Assertion A6 wanted to prove that `Engine:AdvanceStartup` READS `c.Sim.StartupTemperature`
     rather than inlining `9420`. It compared the temperature at the flip against the config value
     and failed by 15.6, because the `Step` that finishes the chain runs one tick of Running physics
     in the same call -- exactly as the code this replaced did. The failure was the assertion's
     fault, but relaxing the tolerance would have made it useless: with a hardcoded 9420 the same
     drift appears, so a read and an inline land in the same place and no tolerance separates them.

     What separates them is a sentinel. Set `Sim.StartupTemperature` to 12345 and the read reports
     12345 while the inline still reports 9420. The mutant run shows the shape plainly: with line 88
     replaced by the literal, the config-comparison assertion (B1) stayed GREEN -- it compares 9420
     against the config's own 9420 -- and only the sentinel assertion (B2) turned red. B1 is a value
     check; B2 is a provenance check, and only provenance distinguishes a read from an inline.
     Assertions that compare a value to its own source are DECISIONS 95's tautology seen from the
     other end, and take the same remedy: bring in something the code under test could not have
     produced itself.

     Two practical consequences. To compare EXACTLY rather than approximately, prove it by calling
     `AdvanceStartup` directly with the cursor parked on the last step and `startupHold` set past
     the remaining holds: it assigns temperature and pressure and returns, so no physics tick
     intervenes and `==` is available. And the whole re-run was written with two harness rules that
     came out of DECISIONS 224 -- EVERY loop carries an iteration bound, and nothing caches
     `state` -- which is what made it safe to run in the same plugin VM that had just been wedged.

226. "AN INDEPENDENT MEASUREMENT" ONLY COUNTS IF IT MEASURES THE SAME OBJECT.
     The user's 180 MB `Data/auxcollection/startup/ScreenChanges.txt` is a real, independent channel:
     1,162,737 per-property GUI writes on the seven `Workspace.Monitors.*` screens of the ORIGINAL,
     captured by something that is not my recorder. It was tempting to read it as corroboration of
     Phase 65's 16-step `StartupSteps` chain. It is not, and it cannot be: that file is a
     FIXED-DESCENDANT-SET watcher, and the log-panel rows are instances `LogPanel` creates at run
     time. A clone that did not exist when the watcher enumerated its set is invisible to it. The
     whole file contains exactly ONE `Text` write under `LogControlRoomMonitor` -- the ErrorFrame
     DescLabel at t=109 -- and zero of the sixteen messages.

     The corroboration it DOES give is real but narrower, and it is worth being precise about which:
     the face sequence (Boot -> PreStartup -> Main -> Error -> Main, 0/14/21/109/154 s) matches
     `RoomShell.faceFor`'s phase branches segment for segment, and `BootFrame` existing on only
     three of the seven matches `if mon.boot then`. So it validates the thing it can see and says
     nothing about the thing it cannot. Reporting the first as if it were the second would be the
     same shape as DECISIONS 91 (counting SS references as live) and DECISIONS 223 (a blind spot
     stated as a result): the instrument's field of view is part of the finding.

227. FILE ORDER IS NOT TIME ORDER, AND A HEADER STATISTIC IS THE EASIEST PLACE TO BE WRONG.
     `aux_screenchanges.py`'s summary line said `first 19:21:59 / last 19:23:49 / span 110`,
     while entries later in its own output carried t=153 and t=154. The writer flushed its tail
     buffer before its middle one: timestamps climb 0..38, jump to 149..158, then resume at 48..110.
     Exactly ONE backward jump, which is what makes it a delivery artifact rather than two sessions.
     Sorted by the `Time:` stamp the real span is 158 s, with silences at 39..47 and 111..148.

     The remedy is structural, not a patch: `aux_narrative.py` sorts before it reports, and the
     header statistics belong to the sorted stream, never to the file. This is the same failure
     family as the byte-count-vs-hash rule in section 0.0 -- a cheap summary statistic that agrees
     with itself and disagrees with the data. Note also where it bites: the number would have been
     WRONG AND PLAUSIBLE. 110 s sits right next to Phase 65's ~113 s, so the mistake would have
     read as a confirmation.

228. "QUICK BOOT UP INITIALIZED" RESOLVES PHASE 65'S BOOT-DURATION CONTRADICTION, AND THE ANSWER
     IS THAT THERE ARE TWO BOOTS.
     Phase 65 recorded a conflict it could not settle: one run was 21.8 s from MONITOR BOOT to an
     accepted lever throw, another was 11 s or less. The aux capture shows both numbers in one
     file. Its opening presentation -- BootFrame 0..13 s, `PreStartupFrame` at 14, `MainMonitorFrame`
     at 21 -- is a 21 s standard boot. Its tail is something else: at 153 s `BootFrame.LogFrame.
     TitleText1` is overwritten with `QUICK BOOT UP INITIALIZED`, the seven ErrorFrames go false,
     and by 154 the MainMonitorFrames are back. That is a 1-2 s recovery pass, and the string itself
     is proof the machine had booted before.

     So the short run was most likely a quick boot, not a faster standard one. Two cautions, both of
     which belong in the record rather than in a footnote. First: this is an explanation, not a
     measurement -- the frame timeline of the 09-26 run was never broken out, so the assignment is
     inference. Second: it does not license changing `Config.Shift.BootSeconds`. What is now measured
     is that the standard boot's PRESENTATION is 14 s of BootFrame plus 7 s of PreStartupFrame; the
     config value is a phase duration the engine drives, and equating the two would be Phase 65's
     own error (a run's wall-clock read as the machine's rule) with the sign flipped.

     CORRECTED 2026-10-01 (Phase 67.1). The operator produced the hook that generated the capture and
     said outright that it is a standard startup, which puts t=0 at the MonitorBootButton click. So
     the quick boot at t=153 is not an alternative to the standard boot -- it happens AFTER one, as
     the recovery pass that follows MAINFRAME CONNECTION LOST at t=109. The conclusion above survives
     (the 09-26 run was still probably a quick boot) but its REASON changes: not "there are two kinds
     of boot", rather "that run probably hit a crash and took the recovery pass". The caution in the
     last paragraph is therefore unchanged and now more pointed -- this is still inference, and the
     09-26 frame timeline still has never been broken out.

229. A USER-SUPPLIED 180 MB DUMP IS NOT A PROJECT ARTIFACT, AND THE REASON TO IGNORE IT IS NOT SIZE.
     `Data/auxcollection/` is data the user handed me to read. It now sits under a `.gitignore`
     rule with the reasoning written next to it, because the obvious reason -- "it is big" -- is the
     weakest true one. The one that decides it is that a single file of 179,788,590 bytes is over
     GitHub's 100 MB hard file limit, so an accidental `git add -A` is not a repository that grows,
     it is a `git push` that fails at the end of a long session with the commit already made. The
     findings are what is worth keeping, and they are reproducible from the three analysers under
     `_tools/_attic/scratch/` plus PROGRESS.md Phase 66; the dump itself is not needed to re-derive
     any of them. Note the asymmetry with the ripped-asset entries already in that file: those are
     ignored for copyright, this one for reproducibility and a hard limit. Same rule, different
     reason, and the reason is what the next person needs.

230. THE PROVENANCE OF A MEASUREMENT IS PART OF THE MEASUREMENT, AND ITS ABSENCE IS NOT NEUTRAL.
     `ScreenChanges.txt` had been read for two phases as a log of the monitor being exercised by
     somebody. Every conclusion drawn from it carried a hidden hedge -- PROGRESS 66.5 wrote "the
     opening before t=0 was not captured", which is not an observation about the machine but an
     inference about the recorder, and a wrong one: t=0 is the MonitorBootButton click. The file did
     not change. What changed is that its producer said what he had done.

     The rule: when a capture arrives with no stated provenance, the unknowns are not "extra
     caution", they are UNKNOWN VALUES, and any claim that depends on them is a guess that will be
     written down as a finding. The cheap fix -- ask, or read the hook that made it -- was available
     the whole time and was not taken for two phases. Note the asymmetry that made the wrong reading
     survive: "the capture starts mid-boot" is consistent with the file, and so is "the capture
     starts at the button". Two explanations fitting one file is exactly the shape of every
     false-negative in CLAUDE.md 0.17, and the tiebreaker is never more analysis of the same bytes.

     Corollary, applied here: the correction is left in place with the old claim struck through
     rather than deleted. The next person needs to know which conclusions were standing on the bad
     inference, and a silently rewritten paragraph hides exactly that.

231. MODEL THE BOOLEANS. DO NOT RECONSTRUCT THE CURVES.
     The boot screen's reveal is 0.3% of the capture; the other 99.7% is Position/Size/Rotation/
     CanvasPosition churn, re-drawn every frame. The temptation is to treat that 99.7% as a richer
     measurement than the 0.3% and rebuild the animations faithfully. It is the opposite: the watcher
     writes a value only when it CHANGED, so the dense properties are sampled at most once a second
     and the sparse ones are exactly reproducible.

     A boolean survives that sampling intact -- a label is up or down, and one sample per second
     captures a reveal that lasts seconds. An eased position does not: a second of a curve sampled
     once is a fact about one instant, not about the path. Rebuilding an ease from those samples
     means inventing the shape between them and then presenting the result as measured, which is a
     worse error than having no animation at all.

     So `BootPanel` drives `Visible` and nothing else. A screen that reveals the right lines at the
     right seconds and does not grow them is a smaller lie than one that eases them along a curve
     nobody measured. The test for which properties fall on which side of the line is not
     "how many samples" but "does sampling lose the thing being claimed".

232. THE BOOT SCREEN NEEDED A WRITER THAT RoomShell IS STRUCTURALLY UNABLE TO BE.
     RoomShell owns which monitor face is showing: it writes `frame.Visible` once per phase change,
     gated on a signature of `lights|monitorPower|booted|phase|shuttersOpen`. The boot screen needs a
     write every second INSIDE one phase, during which that whole signature is constant -- Booting
     for 14 s with nothing else moving. Putting the reveal in RoomShell would mean either widening
     its gate to include something that changes every second (breaking the property that makes it
     cheap) or letting it write unconditionally (breaking the gate's meaning for every other face).

     BootPanel is a second writer that does not collide: RoomShell writes `BootFrame.Visible` and
     BootPanel writes `.Visible` on labels INSIDE that frame. Disjoint properties, so the
     single-writer rule holds -- and the disjointness is the reason the module may exist at all,
     not a happy accident to be verified later. Both modules being signature-gated separately is
     also what keeps the cost at zero on the other 99.99% of ticks: two string compares.

     The initial `Refresh` is called on the command path as well as in the heartbeat, because
     ControlBinder publishes on the same tick the button is clicked. Without it t=0 shows the
     pre-click screen -- caught by the verification rig, which is why t=0 is a row in it.

233. A "CODE OF RECORD WITH GIT BEHIND IT" IS ONLY WORTH WHAT ITS FRESHNESS IS, SO CHECK IT BY HASH.

     PROGRESS 4766-4769 named src/ReactorBackend/ the authority for "what the previous version
     said". By 2026-10-01 that authority was four phases behind the live modules, and the worst
     part was the shape of the staleness: five of ten files were byte-identical and three were
     not, and two did not exist at all. A mirror that is uniformly old announces itself; a mirror
     that is half-refreshed does not, because the file you happen to open may be current.

     So the refresh ran through the Studio -> disk channel (POST each Source to the sink, plus a
     manifest of `<name> <bytes> <crc32>` computed by the same script), the two sides were
     compared by CRC-32, and only then were the bytes copied into src/ -- and then hashed again.
     Two reasons for the double check rather than one: the copy is the step that can silently
     corrupt, and a check that runs before it cannot speak about it.

     Lengths were used to FIND the candidates and never to confirm them, which is the same rule
     CLAUDE.md 0.0 has carried since the mirror era. Equal length is not a match; this round it
     happened to be right five times out of five, and that is exactly why relying on it would
     have been a coincidence rather than a method.

     What this does NOT license: treating the refresh as a licence to stop checking later. The
     mirror has no writer. Every future phase that edits a live module orphans it again, and the
     only thing that will notice is a person deciding to look. The honest long-term fix is a
     writer, and this entry is the record that the first four phases of drift happened with
     nobody looking.

234. A TEST HARNESS THAT IS NOT CONCURRENCY-SAFE FAILS AS A LIE, NOT AS AN ERROR.

     selftest_watch.py reuses one fixed mutant path (_tools/_watch_mutant.luau) and one fixed
     output directory (_tools/_mut_out), and rmtree's that directory at the end. Running the
     suite twice at once therefore makes each run delete the other's evidence, and the result is
     not a crash: it is "NOT DETECTED" on mutants that are known good -- the harness reporting
     that a discipline is not being enforced. One of the two interleaved runs exited 0 while
     printing 17 of 29.

     Two fingerprints make this recognisable rather than mysterious, and both are worth keeping:
     the two runs printed DIFFERENT counts (17 and 25) for one deterministic suite, which no
     honest run can do; and the protection line "shipped file untouched" printed in BOTH, which
     shows the corruption is confined to the verdict and does not touch the artifact under test.
     So the rule is: judge the suite by its "N of M detected" line, not by its exit code, and
     treat two different counts from one file as proof of interference rather than noise.

     This matters more here than in an ordinary repo because these mutation runs are the only
     evidence available before a one-shot, non-repeatable shift in the original game (see the
     comment at the gui-mutations stage of run_tests.sh). A number from a contaminated run is
     not a weaker number; it is a wrong one that looks like a finding.

235. A REFRESH MUST PRESERVE THE FIELDS IT DID NOT WRITE, EVEN WHEN IT CANNOT FIND A READER FOR THEM.

     The TRG wiki snapshot carries seven top-level fields. The user's own TRGWikiPull.py writes
     four of them. It does not write api, namespaces, or pulled -- so a refresh that copies that
     script's output shape drops all three, which is what the first version of _tools/trgwiki_pull.py
     did. The result was 0 differences in every page's content AND in every page's revision
     timestamp, and a file 126 bytes smaller. Nothing in the page data could see it. See PROGRESS
     Phase 69.

     `namespaces: [0, 14]` is the reason this is an entry rather than a footnote. It is the only
     record of WHY the pull walks two namespaces -- the decision that exists because apnamespace=0
     silently drops any article the wiki has moved into Category (DECISIONS 209, measured when
     Shifts became Category:Shifts). Lose the field and the next reader cannot distinguish a
     faithful refresh from an ns0-only one, because an ns0-only file is otherwise perfectly clean.
     The provenance of a decision and the decision itself are equally load-bearing when the failure
     mode is silence.

     The generalisation, which is the twin of the "compare hashes, not lengths" rule in CLAUDE.md
     0.0: do not compare only the fields you believe matter. The check that would have caught this
     was comparing the KEY SETS, not the values -- cheap, and it is the only check that notices a
     field that is present in one file and absent in the other. Both rules fail the same way: the
     thing you did not look at is the thing that changed.

     Ordering matters too, and it is cheap to get right: back up BEFORE the first write, and skip
     the backup when it already exists. A backup step that overwrites on every run hands you
     "after" labelled as "before" on the second run -- which is exactly the run where you would be
     trying to work out what the first one changed.

236. AN OPTIMIZATION OF SOMEONE ELSE'S SCRIPT IS MEASURED AGAINST THEIR SCRIPT, AND THEY GET TO KEEP THEIR SCRIPT.

     The request was "optimize the startup [recorder] I wrote". The thing named by "I wrote" is a real
     file the operator runs (SolaraTab/Test.lua), and it stays theirs: the executor rewrites every file
     in that tab, so editing it in place would be undone and, worse, would make the next diff unattributable.
     The optimization therefore lands as a new repo file (TRG_original_boot.luau) that they fetch and inject.

     This is not a courtesy, it is the only way the claim can be checked. "Optimized" is a comparative with
     no meaning unless the baseline exists, so the baseline was read twice: the source, and its own output
     (1,162,737 lines / 179.8 MB in 158 s). Every change is a row against a measured defect -- the 99.4%
     that was one GlitchFrame's geometry, the appendfile that made two injections into one file, the
     missing DescendantAdded, the absent transport, the 1.14 MB/s with no ceiling. An optimization whose
     targets were chosen from taste would be unarguable and unverifiable at the same time.

     The scope is part of the baseline too. The original resolves its root as
     workspace:FindFirstChild("Monitors"); so does this one, and RootName is pinned to 'Monitors' for that
     reason. An "optimization" that quietly narrowed the view would be a different instrument, not a faster one.

237. THE LINE FORMAT IS FROZEN, AND THAT IS WHY NOTHING NEW IS EVER APPENDED TO A LINE.

     A reader's pattern is ^Time:\[([0-9:]+)\]<-O:\[([^\]]*)\]<-C:\[([^\]]*)\]<-V:\[(.*)\]$ -- anchored at
     both ends, with a greedy (.*) for the value. Ancestors: adding a field to the end of that line is not
     backward compatible, because the greedy group swallows it and no reader ever sees it. The end anchor is
     what tells a reader the line is complete, so the same property that makes the format checkable is the one
     that makes it closed.

     Everything new therefore goes in a new line starting with '#', or in a new file. The header line, the
     beacon fields, the seal reason -- all of it. The alternative, a second format that only the new reader
     knows, is how a capture stops being one artifact.

     Seven archived analysers compile that pattern, and "they all agree" had been asserted from memory. It is
     now a check: verify_boot_capture.py reads the pattern out of the seven source files, requires exactly one
     declaration in each, requires all seven to be byte-identical, requires the anchors, and only then tests
     the capture with it. A copy retyped into the checker would keep passing after a reader changed, which is
     precisely the failure the check exists to catch.

238. A COALESCER'S PRICE IS STATED WHERE THE COALESCER IS, AND THE SEED IS THE WHOLE OF THE CHANGE-AND-REVERT RULE.

     Writing only on a tick, and only when the value differs from the last one written, is what removes 99.4%
     of the noise. It also means a value that changes and reverts inside one tick is never recorded. That is a
     real loss and it is written in the how-to next to the coalescer, not buried in a comment: the operator
     read the old behaviour (event-time writes, 1.16 M lines) and is entitled to know what they are trading.

     The other half of the rule is subtler. Registration seeds lastValue[key] with the current value, so a key
     that has been false since the beginning does not emit a line on the first tick -- the baseline is a
     baseline, not a change. That single line is the entire difference between "a change that came back" and
     "a value that was always there", and it is a payload drop if it is wrong, so it has its own mutation.

239. THE 99.4% IS NEVER PRODUCED, NOT FILTERED AT THE READER, AND ONLY FOR GEOMETRY.

     The dead weight in the operator's capture was Position/Size writes from ...MonitorUI.GlitchEffect.GlitchFrame,
     a decoration. Filtering those lines out afterwards would have kept the cost that mattered: the writes, the
     network, the ceiling, all of it still paid. GeometrySkip = {'.GlitchEffect'} skips the connection, so the
     lines do not exist.

     It is scoped to geometry on purpose. Visible, Image, colours and Text are still watched on those same
     instances, because the boot screen's own reveals are the 0.2% underneath the 99.4% -- and they sit in the
     same file, on the same ClassName, under the same path prefix. That is why the split has to be by property
     within a path and not by class: a rule that dropped the whole subtree would have thrown away the signal
     along with the noise, and the two are not separable any other way.

240. NOTHING ABOUT THE WORLD IS RESOLVED UNTIL THE PRESS -- AND ONE LINE SAYS WHETHER IT WAS THERE.

     The harness first demanded this file die at injection when Workspace.Monitors is absent, and that demand
     was wrong, so the harness changed and not the file. Under StreamingEnabled a root missing at injection is
     usually merely late, so killing the run for it is a false alarm; everything structural is therefore resolved
     at the press. The honest answer to "did I inject too early" is a measurement, not a policy, so the beacon
     carries root_visible_at_inject= -- one boolean, taken at injection, about the only moment that can answer it.

     The press is also where the header goes. Written the other way round, a press on a world with no root left
     a capture file containing nothing but its own header: a run that looks started and a file that looks like
     data, which is the shape of defect this whole project keeps re-learning to reject. arm() now runs first, so
     a failed arm leaves the capture untouched and the death is in meta.txt where a death belongs.

241. A SCENARIO THAT DOES NOT CHANGE THE INPUT IS NOT A SCENARIO, AND A SKIP IS PRINTED, NOT SCORED.

     The nosink scenario was declared and never implemented -- SINK_UP was a local that nothing ever lowered, so
     the "sink refuses" case ran the happy path and its four fallback checks failed against a sink that had been
     quietly working the whole time. Four red lines pointing at the script, all four caused by the test rig. The
     lesson is not "be careful", it is structural: a flag that never changes value is indistinguishable from a
     flag that is honoured, and it reads as coverage.

     Where a check genuinely cannot run in a scenario, the harness prints SKIP and counts it separately from
     PASS. Scoring it as a pass is how "one check did not run" becomes "all checks passed" -- and the number that
     reports that is the one anybody quotes later.

242. THE FORMAT CHECK READS THE PATTERN OUT OF THE READERS, BECAUSE A PARAPHRASE OUTLIVES THE THING IT DESCRIBES.

     Same rule as 237's second half, stated on its own because it generalises. A compatibility promise is worth
     exactly the freshness of whatever it is compared against. A pattern retyped into the verifier is a promise
     to agree with a memory, and it will keep agreeing after the readers have moved on -- green, and measuring
     nothing.

     So the verifier discovers its oracle: it parses the seven reader sources, asserts exactly one pattern
     declaration in each, asserts all seven are byte-identical, asserts the anchors, and only then tests. If a
     reader is rewritten the check goes red instead of quietly testing the old format. This also turned "the
     seven agree" from a recollection into a fact that has to keep being true, which is the cheapest kind of
     insurance available on a claim that had already been made wrongly once in this project.

243. A GUARD IS ONLY AS GOOD AS THE VALUE IT IS ARMED BY, AND AN ASSUMED VALUE ARMS NOTHING.

     The wrap seal was written as "12:00 AM seals, but not while the dial is still on its opening value", and
     the opening value was assumed to BE 12:00 AM -- written down as an assumption in Phase 62 and never
     measured. The first real run reads 11:51 PM at the press, so the very first reading disarmed the guard,
     and midnight -- 89 s later, in the middle of the core's ignition ramp -- sealed the capture. The code did
     exactly what it said; the thing it was protecting against was not in the input any more.

     The rule that survives is the narrower one: the guard has to be armed by the SAME quantity it is meant to
     be excluded by. "Not while the dial is on its opening value" is only meaningful if something has measured
     what the opening value is -- and the honest version of that sentence names the measurement, not the
     assumption. Where a stop rule can be replaced by a record at its own trigger point (see 244), that is
     strictly better than a rule whose correctness rests on a world fact nobody has looked at.

244. MIDNIGHT IS A MARK, NOT AN END -- AND A COMMENT LINE IS THE ONLY FORMAT-SAFE WAY TO SAY SO.

     Removing the wrap seal could have been the whole change. It was not, because the moment itself is data:
     the dial crossing 12:00 AM is the shift's start, and the boot chain's own timestamps should be read
     against it. Losing it would have been the same class of defect as the seal was, from the other side.

     It is written as a '#' comment inside the capture rather than as a new field on a data line, because the
     line format is frozen and appending a field is not backward compatible (237) -- the greedy value group
     swallows it and the end anchor is what tells a reader the line is complete. Comment lines are the one
     thing every archived reader already skips, by construction, so a mark cannot be misread as data by an
     analyser written before it existed. A separate artifact file would also have worked and was rejected:
     the mark belongs where the events around it are, not in a file a reader has to correlate by timestamp.

245. REGISTERING AN INSTANCE IS NOT SEEING IT: SEEDING IS RIGHT FOR A CENSUS AND WRONG FOR A BIRTH.

     Seeding at registration exists to make "changed and changed back inside one tick" cost nothing (236's
     neighbour). For the initial walk that is exactly right: the value at the press is a baseline, and a
     property that never moves should never produce a line. For an instance that comes into existence during
     the run it inverts: the value at birth is not a baseline, it is the first and often the ONLY data the
     instance will ever have -- and the live game writes a cloned log frame's message BEFORE parenting the
     frame, so the message was seeded away. 5156 lines of fades and not one character of the boot's own
     narration is what that costs.

     The fix is the exception stated where the rule is: register() takes `born`, one call site passes it, and
     a born instance's baseline is set to a NUL sentinel -- unrepresentable in any formatted value -- so the
     next tick writes what it holds through the same one-line-per-key path and against the same budget. The
     cost is stated with it: a subtree cloned mid-run now writes its watched values once.

246. A SCENARIO WRITTEN FROM THE IMAGINED INPUT TESTS THE IMAGINED PROGRAM.

     The clock scenario set 12:00 AM once, as the opening value, and then went to noon. The rule it was
     supposed to cover -- seal on the way BACK to midnight -- had no scenario at all, which is why it stayed
     green through a mutation suite and died on the first real run. The scenario is now laid out to the shape
     the artifact actually has: 11:51 PM, 11:59 PM, 12:00 AM, and noon after.

     This is 241 from the other end. That one said a scenario that does not change the input is not a
     scenario; this one says a scenario whose input is a guess tests the guess. The two together are the shape
     of the whole defect: the rig and the program agreed with each other, and neither had been compared with
     the world. Tests earned from measurement can disagree with the program; tests written beside the program
     can only agree with it.

247. A KEY IS A PATH, AND A PATH IS NOT AN OBJECT.

     The boot recorder keys every watched property by `full path | property`, and register() admitted a key
     once: `if keys[key] == nil`. That is correct for a world with a fixed cast of instances and wrong for
     one that clones. The original's log panel does not move a message through three fixed labels -- it
     clones a fresh row per message onto the SAME three names and destroys the row when the fade ends. So
     after the first three messages every later one was skipped whole, and worse, the surviving connection
     still pointed at a row that had already been destroyed: the key was occupied by a dead object, so the
     new instance's writes had nothing watching them at all.

     Two instruments measuring the same face of the same shift are what named it. This file counted 3 log
     messages; r60, running in the same session against the same LogsFrame, counted 35 distinct ones
     including START-UP COMPLETED; the watcher counted the three TextLabels destroyed 47 times (12 + 27 + 8
     distinct instances). 3 is a defect of this measurement, not a property of the panel.

     The fix keeps the key path-shaped and makes the registration re-point it: a born instance on a known
     path disconnects the stale connection, connects the new one, and takes the birth record again.
     `keys[key]` and `writes[key]` deliberately survive -- the write budget is per PATH, because that is
     what suppressed.txt's ledger names. Disconnecting before re-pointing is not tidiness: without it a dead
     connection keeps writing to a path it no longer occupies, and the artifact reports messages the panel
     never showed. A recorder that invents data is worse than one that misses it.

248. THE HARNESS CLONED A NEW PATH, WHICH IS WHY IT STAYED GREEN.

     The birth record shipped in b2 with a test and with a mutation that made it go red. Both used a clone
     onto a NEW path (TemplateLogFrame4). The defect was the second instance on the SAME path -- a shape the
     rig did not contain -- so b2 went to the real game with a full green board. This is 246's twin: 246 was
     a scenario written from a guessed input, this is a scenario written for the convenient shape. A suite
     can only fail in the shapes someone thought of, and the defect lives in the shapes nobody did.

     Two smaller things from the same pass. The signal stub had no Disconnect method, so the shipped file's
     own pcall(conn:Disconnect) -- correct code -- would have failed silently and been reported as a broken
     file: a stub that cannot do what the real object does is a test that lies. And the harness used to
     hard-code `build=b2` in its header assertion, which meant bumping the build failed a correct file; it
     now reads the build string off the shipped source, because a literal in the rig is a second copy of the
     one number that changes every build.

## 249. A SANDBOX REFUSAL IS A PROPERTY OF THE CALLER, NOT OF THE CODE.

Official `rblx_execute_luau` runs inside Studio's own assistant sandbox. `SSS.ReactorBackend`
carries `Capabilities = LoadUnownedAsset (and 3 more)`, and that folder rejects everything the
assistant VM tries to do with it: clone-into-a-temp-Folder fails
(`cannot reparent 'Config' to 'ServerScriptService.__StartupDemo' since '…__StartupDemo' has
additional values for the Capabilities property`), clone-into-`ReactorBackend` fails
(`'…ReactorBackend' has additional values`), and a plain `require` fails
(`cannot require 'Config' since 'Config' has additional values …`). The third-party
`mcp__robloxstudio__execute_luau` VM does all three without complaint.

Three different refusals, two different sentences, and both point at the TARGET
("… has additional values") rather than at the SANDBOX. Nothing distinguishes "this module is
unloadable" from "this CALLER may not load it", and the same shape is already on record for the
HTTP stub (CLAUDE.md §0.17, line 225: `ProtectedString expected, got nil`, an error that points
at an assignment instead of at the network).

**The rule, and the reason it is worth a numbered entry:** when a capability or sandbox error
names a property of an instance you did not set yourself, the caller is the variable — **change
channels before you change code.** This cost three calls to learn. Handing the two channels one
job each also keeps §0.17 honest: the official tool still owns source MOVEMENT (its `GetAsync`
is real where the plugin VM's is a stub), and the plugin VM owns `require` + live driving. A
failure on one is evidence about one, never about the other.

**Corollary for the record:** I never had to touch `ReactorBackend` to find this out, and the
refusal was not a sign that anything was wrong with it.

---

## 250. 「机房容易坏」是规格，不是缺陷 —— 所以查清楚之后**一个字都不改**

你问「为啥机房这么容易坏掉」。答案在**原版自己的世界里**（Digital Reactor Manual 的
MAINFRAME 段，`Workspace.Consoles.ElectricGridConsole.DRMScreen…MainframeFrame…TextLabel`，
我们的 flow 产物逐字抓到了，见 `PROGRESS.md` Phase 74.1）：

> Majority of its computational operations are controlled by **QPUs**, which have a tendency to
> **degrade**, especially in unfavorable environmental conditions or **overclocking** scenarios.

> components of the **mainframe may catch on fire** from reactor operation … Excessive **fires**
> may raise the mainframe temperature and **cause QPUs to degrade at a much faster rate.**

> TLDR: … if theres enough, they can trigger a mainframe meltdown …

**Tesseract 是全设施唯一一台量子机，要同时算 CBL + 控制台 + 传送门 + 医疗机，
本来就长期超频；QPU 降解是它的磨损方式，不是它出了故障。** 6 个 QPU = 6 次配额，
前五次只是监视器蓝屏/软重启，第六次才真的瘫 —— 而且**换 QPU 就能修**。

**为什么这值得一条 decision，而不是一条 progress：** 查到这里有一条**看起来的**下一步 ——
「把 QPU 降解实现进 remake」。**我没做，而且这是刻意的。**

1. **它是玩法机制**，而 `CLAUDE.md` §1.4 第一条是
   「NEVER CHANGE EXISTING GAMEPLAY MECHANICS」。往一个模拟器里**新加**一条周期性资源损耗，
   改变的是这个游戏有多难、玩家要花多少时间在维护上 —— 这不是我可以自己拍板的事。
2. **速率一个数都没量到。** 我量到的是**旗标翻起**（`t=719.86` / `t=868.94`），
   不是「第一个 QPU 在第几秒掉」。把 720 s 当成降解周期，就是把**一趟的运行时长
   当成了机器的规则** —— `PROGRESS.md` Phase 65 里已经为同一类错误写过一次拒绝
   （那时差点把 `StartupSeconds` 从 8 改成 111）。**没量到就不实现**，同 65.6。
3. **remake 里那个位置是空的，但口子已经开好了**：`StateBridge` 第 57 行
   `set(stats,'ActiveQPUs',6)` —— 名字和类型都照原版搭了，值焊死。
   将来要接，缺的只是**写入者**。**不留一个没人读的一半**（同 Phase 65「不加新 `Stats` 值」
   那条理由的反面：这里 `ActiveQPUs` 本来就在，只是恒定）。

**所以：**这条进了 `QUESTIONS.md` 的 **P10**，带三个选项（不做 / 只做监视器蓝屏那一刻 /
整条 QPU 磨损），等你一句话。**在你说之前，remake 保持现状 —— 机房不会坏，因为它根本没装。**

---

## 251. 跨 place 搬建模：**照抄原版的世界坐标**，不做「摆好看」

Rebuild 从 AIRemake 搬腔室时，**不按视觉效果重新定位**，而是把几何**推回原版的绝对世界坐标**。
见 `PROGRESS.md` Phase 75.4。

**为什么这不是一件可以随手定的事：**

1. **坐标系只有一套的时候，误差是零；有两套的时候，误差是「每一件都要重测」。**
   Rebuild 要把整个游戏从零搭起来，后面还有几十件要搬。每一件都由我来「找个好看的位置」，
   件与件之间的相对关系就**没有任何东西在保证** —— 而那种错是**静默**的：每一件单看都对。
2. **同一次搬运里，也不保证每一件都落在同一个偏移上。** 这次就是：
   `ChamberWalls` **早就在原坐标上**（pivot 两边逐位相同），而 `Core` / `PEA` 各偏了
   `(+0.633843, −193.746674, −146.267456)` —— 是**两次**贴进来的。
   如果我假设「墙搬对了所以核心也搬对了」，就会把核心**留在墙外面 194 个 stud**，
   而且**看起来什么都没坏**（三件都在，件数都对，指纹在相对坐标下还全绿）。
3. **共用坐标让验收变成一次比较，而不是一次判断。** 摆正后我比的是包围盒的 6 个数、
   pivot 的 6 位小数 —— 有确定答案，不需要「看着差不多」。

**做法**：算出 `Δ = 目标 − 当前`（这次用两个独立测点互证，都要一致到 6 位），
`Model:PivotTo(pivot + Δ)`，包在 `ChangeHistoryService:TryBeginRecording/FinishRecording` 里
（**让这件事是可撤销的**），然后把包围盒和 pivot 与原版逐位核对。

**代价**：Rebuild 的世界原点因此被原版**绑死**（腔室在 `y −67..495`，而 Rebuild 的 Baseplate
顶面在 `y=0`，底下 67 个 stud 埋在板里）。这是**故意接受的**——地面层怎么处理是另一件事
（Phase 75.5 里没定），但**几何的相对关系不能靠地面层来定义**。

---

## 252. 证明一次搬运：**比指纹，不比件数** —— 而且阈值要**量**，不能拍

**件数是所有检查里最弱的一个。** 「件数相同、件不同」和「件数不同」在屏幕上同形，
但前者会让你在错误的几何上继续工作。跨 place 搬运的验收固定用四把尺子
（`PROGRESS.md` Phase 75.3）：

1. 件数；
2. **逐件指纹**（名称/类别/尺寸/朝向/材质/颜色/透明度/`MeshId`/子件数 → 排序 → 滚动哈希）；
3. **相对位置指纹**（各件减质心 → 排序 → 哈希；平移不变，偏移自动消掉）；
4. **包围盒 min/max + pivot**，与原版**逐位**比对。

**这里踩到的是一个「永远红」式的陷阱的变体：** 我第一版用固定 `0.01` stud 取整，
报出 `PowerExtractionAssembly` 两边不一致 —— 而它其实**是同一份几何**。
Roblox 的部件坐标是 **float32**，同一份东西从 `y≈250` 搬到 `y≈50`，同一个真实坐标的
**表示**就变了最后几位（残差 ≈ 1e-6 stud）。**一个没量过的阈值，会把「表示精度」
报成「搬运失败」。**

**规矩：阈值必须做成阶梯（0.001 → 0.2），找到两边开始一致的那一档。**
一致的那一档告诉你残差有多大；如果**粗到 0.2 还不一致**，那才是真的搬错了。
判据是**「N of M detected」式的形状**，不是「红/绿」—— 同 `PROGRESS.md` Phase 68 那条
（`run_tests.sh` 并发互删产物，报成「NOT DETECTED」，因为**判据本身选错了**）。

**顺带的结论**：`ChamberWalls` / `Core` 能在 `0.001` 上全绿，**不代表它们「搬得更准」**，
只代表它们的坐标本来就落在 float32 能精确表示的格点上。**把「恰好干净」读成「质量更高」，
是这次差点犯的第二个错。**

---

## 253. 量一个旋转过的件，不能用 `Position ± Size/2` —— **尺子错了，照它建出来的东西就错了**

2026-10-03，Rebuild 腔室第二刀。我按 `min = CFrame.Position − Size*0.5` 量了
`PowerExtractionAssembly`，得到顶 `y 286.0`，然后**照着这把尺子**建了 `RebuildColumn_v1`。

**那把尺子是错的。** `Size` 是**局部轴**上的尺寸；`ThermalOutline` 的 `Size` 是
`8.4 × 39.6 × 39.6` 而它**平躺着**（局部 X 竖直），naive 法把局部 Y 当世界 Y，
凭空造出一个 39.6 高的圆柱，把 PEA 的顶从 **270.4** 抬到 **286.0**。
`v1` 因此**高了 16 stud**。

正确做法是逐轴投影：

```lua
local R, U, L = cf.RightVector, cf.UpVector, cf.LookVector
local ex = math.abs(R.X)*s.X + math.abs(U.X)*s.Y + math.abs(L.X)*s.Z
-- ey / ez 同理
```

**三条要坚持的：**

1. **「比较」和「量值」是两回事。** §75.4 那张「逐位相同」的表**作为比较仍然成立**
   —— 同一个错方法量两个 place，两边一起错，差还是 0。搬运本身没问题。
   但表里的**数字不是包围盒**，不能当尺寸用。取舍 252 不受影响。
2. **一个错的量法不会报错，它只会安静地给出一个数。** 它骗了我一整轮 ——
   没有任何症状，直到我拿 OBB 量了同一件东西，两个数差了 15.6。
   这和 §0.13（锚点落进错块）、Phase 68（判据选错）是**同一类**：
   **错的是工具，不是代码**，而工具不会自报家门。
3. **量「实物」优先于量「分组汇总」。** 我直到把 `ThermalOutline` **单独**拿出来
   （一个 `x 1 n= 1` 的行）才看出 `8.4` 是厚度。分组汇总把 1921 件压成 13 行，
   每行看起来都很合理。

## 254. 包围盒对不上时，改到「不能再好」为止，**不要改到「某一面正好」**

`RebuildColumn_v2` 最后停在 `89.8 × 54.1 × 101.4`，原版 `90.9 × 54.0 × 98.1`。

- X 差 −1.2%，Y 差 +0.2%，底/顶 **对上**；
- **Z 差 +3.4%**，而且我**知道**怎么消掉它：舱段上下盖的切向宽度 47 就是 Z 的极值来源。

**但我没消。** 因为顶盖**同时**是 +X 的极值来源：

| 顶盖切向宽 | X 总宽 | Z 总深 | 与目标差的绝对值和 |
|---|---|---|---|
| 47（当前） | 89.8 | 101.4 | **4.6** |
| 43（缩窄） | 87.6 | 99.4 | 4.9 |

**一个能改善某一面的改动，如果让总量更差，那它就不是改善。** 这类取舍在有**多个量纲**
的重建里会一再出现，判据只能是「离目标的总距离」，不能是「我盯着的那一面」。
把它写下来，是为了下一次不要再花一轮去「修好」一个**已经是最优**的数。

**同一轮里另有一条自我约束**：反解三座舱段的 R/T 时得到了一个**自相矛盾**的结果
（用 X 极值反推 R=47.875 会让 Z 变成 52.5，而实测 49.05）。这说明原版那三座舱段
**不是三个全等的径向盒子**，或者分组里混了非径向对称的件。
我**没有继续追这个矛盾**，也没有挑一个能同时满足两式的假 R/T —— 取了折中的
R=44.5 / T=24.5，把矛盾**写进 `PROGRESS.md` 76.3**。
**一个解释不了的残留，要写成「解释不了」，不要用一组凑出来的参数把它盖掉。**

---

## 255. **分组包围盒会把四条分开的东西合成一条不存在的平板** —— 读结构必须先逐件

2026-10-03，量 `ChamberWalls`。我按**名字**把 2267 件汇总成 19 行，其中一行是：

```
MeshPart   x16 n=16   ctr -51.6, 290.5, -0.7   sz 106.4, 8.0, 205.8
```

**看起来就是一块横穿腔室的 106 × 8 × 206 的平板**，我差点照着它建一块平台。

把这 16 件**逐件**打出来才发现：它们的 θ 是 `±86.1 / ±103.1 / ±115.6 / ±124.4 …`，
真正的形状是 **±Z 两侧各一条 θ 跨度 64° 的弧形观察窗带**。
那个 106 × 206 **是把两条弧带各自的包围盒并起来的结果，没有任何一件是这个形状**。

**规矩：汇总只能用来「找」，不能用来「读」。**
先逐件看一遍（哪怕只打名字/θ/尺寸），确认形状之后再汇总出尺寸 ——
反过来做，你会把「包围盒的并集」当成「实物的形状」，
而**这个错误在数据里看不出来**：那一行数字完全正确，错的是我给它配的解释。

**同一天的另一面（同一个坑的反向触发）：** `Union` 那件单独量是
`40.9 × 55.5 × 27.8 @ (77.5, 235.0)`，相对轴心 r ≈ **87.4**。
我第一版按「贴着外墙」放在 r = 104，多探出 10 stud ——
**一个位置读错，整体包围盒立刻从对称变不对称**（x 从 −108..108 变成 −108..118）。
**对称性是这种错误的免费探测器**：腔室是对称的，我的输出不对称，
那就一定是某一处读错了位置，不是「设计如此」。

## 256. 重建 ≠ 复制：mesh 用近似几何代替，**并且说出来**

Rebuild 里建的是**新的一套**，不是把原版搬过来（用户原话「拷贝当尺子，重新建一套」）。
所以原版里那些**独有的 mesh 资产**（`Meshes/Circle`、`Trapezoid (0.5 stud…`、
`Meshes/TrapizoidCube`）**我不去复制它们**，用 `Concrete` 圆柱 / 普通 Box 近似。

**但这件事必须写下来**，因为「看起来对」和「用的是同一批资产」是两回事：

- 尺寸、位置、材质名可以逐位对上，**网格本身对不上**；
- 以后如果有人问「为什么 Rebuild 的窗框比原版圆」，答案在文档里，不在代码里；
- 反过来，如果我不写，下一个人会以为那里**本来就没用 mesh**。

**判断准则：凡是「我用 A 代替了 B」的地方，A 和 B 都要写出来。**
只写 A（我建了什么）会让 B 消失；只写 B（原版是什么）会让人以为没建。

**同一轮的正面例子**：原版顶部倒角是 118 个 `Wedge`，我改用 60 片
**倾斜 132° 的 Box**。同样是代替，同样写进了 `PROGRESS.md` 77.4 第 5 条 ——
理由是**楔形的朝向是个已知会踩的坑**，而倾斜 Box 能一次摆对。
**省掉的坑也要写成取舍，不能只写成「做法」。**


## 257. 「在空白处做」不等于「随便放」—— 先量空地，再摆

这一轮的活是「在空白地方做一个辐射滤芯和擦除器」。**空白是相对的**：这台机器
2048 x 2048 的世界里，设备全挤在 x -69..45 / z -143..30，其余地方**看起来**是空的，
但「空」不等于「能放」。

**做法**：先用 4-stud 栅格 + 逐件 OBB 把「有东西」的格子标出来（§0.18 那把尺子，
这次量的是**空隙**不是尺寸），再在空格里找**四周还有一圈空格**的孤立格 —— 那才是
真·空白。第一次摆位就错了两次：
- 偏西 **3.10**：西墙立柱（x -69.05）在 z 25.4..33.6 有一排，
  而我按「墙在 x -69」的直觉摆，实际立柱面在 -69.05，**差 0.05 就穿模**；
- 偏东 **3.43**：MK1 格栅西面在 x -57.52，我摆的柜子东面到 -60.95，**差 3.43**。

两次都是靠**实测**挪的，不是靠眼睛估。挪完再跑一遍**全 DataModel 逐件 OBB 求交**
（227 件非地形件），hits = 0 才算完。

**判断准则：「空白」是一个需要测量的量，不是一个形容词。**
任何「找个空地放东西」的活，第一步永远是**量**，第二步才是摆；
摆完再量一次**净距**（不只是包围盒不重叠 —— 0.20 的净距和 0.00 的净距在 OBB
求交里都是 0，但前者能开门、后者不能）。

**同一条的反面**：如果我直接 import_build 到 (0,0,0) 的原点，它会**正好落在
MK1 格栅上**（MK1 就在原点附近），而盘上看不出任何问题 —— 直到有人 playtest。

## 258. 5.902 那个换算是量出来的，但它**可能**是导入设置而不是文件的属性

`ChamberGrate` 从 Blender 出去是 `201.79 x 201.79 x 347.00`，Studio 读回来的
MeshPart 是 `1190.965 x 2048 x 1190.966`。三个轴同一个比值：`1190.965/201.79`
= `2048/347.00` = **5.902**。同一比值 = **纯缩放、没换轴**（Blender Z-up 到
Studio Y-up 这一步是对的）。

**顺手撞到一个陷阱**：2048 是 Roblox 的**单件尺寸上限**，而 `347 x 5.902 = 2047.99`
—— **卡在上限上、差 0.01**。如果那层壳再高一点，读回来的就是**被夹过**的数，
而**被夹过的尺寸和一个正常的尺寸长得一模一样**。所以「量回来对得上」在接近上限时，
第一步是排除截断，不是庆祝。

**取舍**：把 `1/5.902` 钉进 `trg.py` 的 `STUDS_PER_UNIT`，导出时折回去
（FBX 用 `global_scale`，glTF 没有这个参数所以临时改 object scale），让产物落地就 1:1。

**代价写清楚**：如果 5.902 其实来自**操作员的导入对话框**而不是文件本身，那么换一次
导入设置它就变了，而**盘上没有任何东西会报错**。所以脚本多打一行
`expected_studio_size` —— 那行**就是这个假设的检验器**：导入后读到的 Size
不等于它，说明 5.902 错了，不是模型错了。**假设必须带一个会红的检查，否则它不是假设、
是信仰。**

## 259. 真曲面比 box 堆**更省** —— 这条否掉了我自己前面的推理

我说过「Blender 强在够得到曲面」并把「只能 primitive」的成本算在**观感**上。
Phase 79 那版我用了 box，**67968 tris**。Phase 80 的 scrubber 用 `revolve`
（整条母线一次车出、无接缝）+ `sweep_arc`（真弯管），**10956 tris**，
而形状复杂得多（筒身 + 蝶形封头 + 中段法兰 + 弯管 + 弧形面板）。

**所以曲面不只是好看 —— 它是更便宜的表示。** 一节 64 边圆柱是 64 个面；同样的
圆柱用 box 堆要几十个 box、几百个面，还带一堆接缝。成本在**面数**上，而且方向和我
以为的**相反**。

**但这条有个前提：得会用。** Phase 79 我够得到 `revolve`，伸手拿了个 cube。

## 260. 一对东西的「像一对」，只能靠**共用同一段构建代码**

LaserPort 的两个端口没有标签、没有配色差、没有名牌。**读的人凭什么知道它们是一对。**
唯一的手段是：底座（板 / 螺栓 / 轮毂 / 两条轭臂 / 枢轴销）由**同一个函数**、用**同一批常量**
建出来，只有头在分岔。所以那些常量不是「美观选择」，它们是**配对关系的载体** ——
`HEAD_R = 0.47 < 轭臂内侧面 0.49` 这种咬合关系一旦被谁单独改掉，
先坏的不是外观，是**「这是同一台机器的两端」这个事实**。

反过来说，**差异必须落在一条轴上、且不能太大**：发射端 5 片齿 + 内凹碟，接收端 3 片齿 +
喇叭口 —— 是形状和数量的差，不是长度的差。**明显更长的那一端会读成失误。**
（我这次两只头 x 都到 2.16 / 1.92，差 0.24，在「看得出来是两种」和「看不出来是两代」
之间 —— **这是估计，不是我验证过的界线**，得等操作员说。）

**顺带，一个更一般的形状**：这一轮的起点其实是坐标轴。墙挂件要**沿墙的法线建**，
而「绕 Z 建好再旋转 mesh」会**静默换掉局部轴朝上的那一根** —— 不报错，只是东西躺着，
而**躺着要等导入之后才看得出来**。加 `axis` 参数不是为了好看，是因为
**在一个错的局部坐标系里建出来的东西，所有数字都对，只有世界不对。**

## 261. 关节不在代码里，在**局部坐标系**里 —— 一个件的原点就是它的转轴

用户要「像摄像头那样动」的激光端口。第一版我把它焊成一个 mesh，于是它**只能朝一个方向** ——
这不是没写旋转代码，是**结构上没有可转的东西**。两条一起才成立：

1. **一个 mesh 是刚体。** Roblox 的 MeshPart 里没有任何一部分能单独转。想把整个头做成一个
   mesh，就等于宣布它永远朝一个方向。
2. **件的原点就是它的转轴。** 所以三个刚体（底座 / 轭 / 头）的**原点必须分别建在
   pan 轴、俯仰销上**，而不是建成「一块几何体 + 一个旋转脚本」。**关节是建进去的，
   不是接上去的。**

**最贵的推论：烘过的原点和完好的原点，从外面长得一模一样。** 三件摆得完全正确、尺寸正确、
`open_edges = 0`、渲染也对 —— 只要导出把变换烘进几何体（原点塌到包围盒中心），
整个东西就**永远动不了，而所有数字仍然漂亮**。所以这种交付物的正确性**不可能从构建脚本里
看出来**，只能在**文件外面**证明（→ 262）。

**随附一条**：上一版那个销**是竖直的**（穿过从上、下夹着头的两条臂），那是 **pan** 关节的
形状，而头焊在轭上 —— 所以那根销什么都没瞄，**tilt 根本不存在**。切块之前得先问
「这个关节连的是哪两件」；只把东西切碎而不动销，会得到「能水平转、永远不能俯仰」，
**看起来改过了，还是只能朝一个方向**。

**再随附一条**：冷却管是硬的，**跨关节装就会撕**。现在每段管整个待在一个刚体内部。

## 262. 交付物的正确性只能在**交付物外面**证明 —— 而且**同一条轴在两套坐标系里要分别命名**

Phase 82 新写了 `_tools/blender/laser_port_check.py`：把导出的 **FBX 重新导入**，逐件读
原点/尺寸/tris，**再摆一遍姿态**读第二遍。它给出的数字是这一轮唯一能作证据的：
三件的原点与设计值**差 0.0000**（导出没烘变换）、尺寸与构建时逐位相同、
tilt 段与 pan 段的旋转**逐元素相等**、两个刚性不变量各自守恒。

**为什么值得单独写一个脚本**：构建循环读了它自己写进去的东西，同义反复；而
**「原点被烘掉」这种缺陷在构建侧完全不可见**（见 261）。

**两段不只是为了清楚，是因为不变量不一样**：俯仰销**会被 pan 带走**，所以在 pan 之后
量「到销的距离」是在对一个已经荡走的销量 —— **会把刚体运动报成断裂**。tilt 的不变量
只能在 pan **之前**量。

**同一条轴，两套坐标系，两个名字**：同一个 tilt，在 Blender 里叫「绕 Y」，导入 Studio 后
叫「绕 local Z」；pan 在 Blender 是「绕 Z」，在 Studio 是「绕 local Y」。脚本里
`Rotation(pan, "Z")` 和打给操作员的「pan 绕 local Y」**差的那一下是映射，不是不一致**。
**说明里不写坐标系，就是在一台对的机器上给一个错的轴。**

**两个自打的尺子错**（同 253/§0.18 一族，都是「错的量法不报错」）：
① FBX 按 `global_scale = 1/5.902` 导出，**文件里存的是 studs/5.902**；拿以 studs 写的
设计值去减以文件单位读回的平移，报了 **5.31 studs 的误差**，而那两个件是**精确的**。
② 保距要量在**垂直于转轴**的平面里（pan → XY，tilt → XZ）；量错平面会报 NOT RIGID。

**变异**：`TILT_PIVOT` 的 z 改 0.90 → **2 failed / exit 1**；tilt 轴从 `"Y"` 改 `"X"` →
**5 failed / exit 1**。第二个还翻出：接收端枪口**正好在过销的 X 轴上**，绕错轴**改不了
任何距离** —— 距离检查抓不到，只有**旋转**检查抓到。**两类检查都要有，不是保险起见。**

## 263. 一个 VM 答应等，**不等于**它会执行你给它的回调

插件 VM 里 `RunService.Heartbeat:Wait()` **会返回**（实测一次 0.0190 s），
而**同一个 VM 里 `Heartbeat:Connect` 注册的回调，3 拍跑了 0 次**，`conn.Connected` 还是 `true`。
两者能同时成立，所以「Wait 回来了」**不能**推出「我的回调跑了」。

**后果：别把每帧的工作藏在连接里面。** 它从唯一能驱动的那个 VM 里是**看不见的**，
而「看不见」与「没写」在盘上长得一模一样 —— §0.17 那条纪律的第三个化身。

**做法**：把连接体提成公开函数（`M.stepBeam(rig)`），**连接里调用的就是它**。
测的是**同一段代码**，不是副本；连接本身缩成一行，可以一眼读完。
这不是为了测试开的口子：**要等下一帧才知道的东西**（这里的落点）本来就应该有一个名字。

## 264. 一个 Part **出生在世界原点** —— 「创建即看得见」的件必须**同帧摆好**

`Instance.new("Part")` 的 CFrame 是单位阵。所以一条 `Size = (120, 0.16, 0.16)` 的光束
在**第一次被摆之前**，是**一根 120 stud 长的 Neon 圆柱横躺在 (0,0,0)** ——
**穿过整张地图的橙色杆子**。它只在「创建」和「第一拍 Heartbeat」之间出现，
**在代码里读起来完全正常**。

这是**提取 263 那个函数时顺手翻出来的**（我本来只想让它可测），不是专门去找的 ——
但它**是玩家能看见的**，所以是 bug 不是瑕疵。修法：`fire()` 里**同帧先摆一次**再进循环。

**同族**：任何「先建、后摆」的东西都这样 —— `Transparency = 1` 的落点标记出生在原点也一样，
只是它不可见所以没人管。**可见的那一个才咬人。**

## 265. 认件要**按形状认，并且要求次优解离得足够远**

导入器可以重排件、重命名件，所以「第几个」「叫什么」都不是稳定的身份。
`bestRow` 给每个候选拟合一个比例 k、取残差最小者，**并且次优解离最优解太近就拒绝**（差值 < 0.02）。
理由与 253/§0.18 同源：**错认一个件不报错，它只是安静地给出一个数** ——
在这里那个数是**转轴**，于是「会动，只是动得不对」。

## 266. 交付成 `Script` 还是 `ModuleScript`，取决于**它要不要自己跑**

ModuleScript **自己不会运行**；`ClickDetector` **只在 Play 模式下存在**。所以
「点一下就动」这件事**只能**由一个 `Script` 完成 —— 交付物是
`Workspace.Scene.LaserPortGimbal`（`Script`，`Enabled = true`）。

但**测试要能 require**。两条路都留着：① 同一个文件写成**双形状**（`script:IsA("Script")`
时自装，否则只导出 API）；② 测试把 **`Script.Source` 读出来**塞进临时 ModuleScript 再 require
（§0.15 的路线用在 Script 上）。**② 才是关键**：它保证被测的是**交付物自己的字节**，
而不是我重打一遍的副本（§0.17「每条通道各管一半」）。

## 267. 交付物是**拓扑**的时候，几何随便挑，**计数必须断言** —— 而"删除两者的顶面和底面"有两解

用户给的是**一个拓扑任务**："18 边接 24 边，用 Bridge Edge Loops 出三角过渡网格"。
半径、高度、倒角都是**自由选择**；**必须精确**的只有：一个闭合流形、18 边环与 24 边环、
中间正好 18 + 24 = 42 个三角形、不扭。
所以构建脚本里**断言**这三个数，再让 `*_check.py` 从**导出后的文件**读回来。
"我建的时候是 42 个"和"文件里是 42 个"是两件事，而它们之间的那段路（导出/导入/焊接）
正是**上一份资产真的坏过**的地方。

**同一句话里的歧义，选"让算子有定义"的那一读。**「删除两者的顶面和底面」可以是
"四个端面全删"或"删相对的那一对"。前者留下**四条**开环，`bridge_loops` **照样会产出**
一个网格（它会两两配对），只是不是要的那个 —— **不报错，安静地给你另一个东西**。
后者正好两条环。所以我选了后者，并在报告里**明说选法**，让他能一行话推翻。

**空隙不是余量，空隙就是桥。** 两条环若共面，桥出来的带子高度为零 → 42 个**退化**三角形：
零面积、看不见，而"42 个面"这个计数**照样成立**。凡是"计数对但内容是空的"地方，
都要另配一条**几何**断言（这里：零面积检查）。

## 268. 要问两个导出器**同一个问题**，先按位置焊接 —— 否则那个可怕的数是**关于问法的**

`.glb` 读回来 `verts=504 open_edges=504 components=128`，看着像导出彻底坏了。
**不是**：glTF **没有地方放多边形**，于是把**每个角**拆成独立顶点（法线在倒角处不同、
UV 在缝上不同）。**按位置焊接之后 126 个顶点** —— 和 FBX **一模一样**。
两个文件描述**同一个实体**，只有一个还把拓扑留在索引里。

**纪律**：跨格式比较前先焊接；报告的"存储形态"和"焊接后形态"**两行都印**，
让读者一眼看到 504 → 126 是**存储差**而不是**几何差**。

**顺带一个我自己的错，属于同一族**：Blender 场景坐标是**文件单位**（= studs/5.902），
我拿它去比**以 stud 写死**的高度 → **每条环都返回 n=0**，读起来像"导出坏了"。
`laser_port_check.py` 里早就有 `u(v) = v/SPU`，我这次没抄 ——
**上一个人踩过的坑不会因为你读过它就消失**（§0.18 同族：错的量法不报错，只安静给你一个数）。

## 269. 一个**会回来的绿**变异是结果，不是失败 —— 以及倒角的角度过滤**依赖带子是对的**

`--twist`（翻转顶部圆柱的绕向）跑出来与正确版本**逐位相同**（126 / 128 / 2.1837，一位不差）。
**负结果，而且有两条独立原因**：`trg.finish` 会 `recalc_face_normals` 抹掉翻转；
`bridge_loops` 按**几何**推对应关系，不按递给它的环序。所以**绕向错误传不到带子上**。
留着的价值：流水线一变，这是最便宜的**重测**方式。
**写下负结果和写下正结果一样重要** —— 否则下一个人会以为那条守卫防着某种真实失败。

**同一个变异还翻出一条真性质**：倒角是 **25° 角度过滤**的。正确的带子只向内倾
`atan(0.30/0.80) = 20.6°` → **被跳过**；**交叉的带子很陡 → 倒角去吃它**，
把每个带子三角形切碎，并把两条环从设计高度上拽下来（verts 126 → 240，`band_faces` 归 0）。
也就是说：**一块错的带子会被倒角藏起来** —— 看起来不像"错了"，像"那一段什么都没有"。
**过滤器写的是"角度"，实际滤的是"形状对不对"**，这是一个隐藏的耦合，不是设计。

## 270. 一条**从没红过**的断言不是检查器，是装饰

`band not twisted`（最小质心半径 > 0.9·min(R)）这条线，前两次变异里都只**顺带**红过
（带子为空 → 半径 −1），**从没被真的扭过的带子逼红过**。
我本来就此收尾 —— 那会留下一条**没演示过**的断言，正是 DECISIONS 205 要避免的东西。

于是造了第三种变异：**手工搭一条对侧相接的带子**（每个顶点接对面那一个），
保持 18 + 24 = 42 个面、保持三角形、保持每条棱被覆盖一次。
结果：**18 绿 2 红，红的只有 twist 那一行** —— 闭合、单壳、两条环的边数与半径、
带子 42 个三角形**全对**，`min centroid radius = 0.5898`（正确 2.1837，门槛 1.8900）。
**这一条线现在有证据了。**

**门槛是推出来的，不是挑的**（`0.9 * min(BASE_R, TOP_R)`），所以设计尺寸改了它自己跟着走 ——
手挑一个常数会在下一次改尺寸时**静默失效**。
**"只有一行红"比"十行全红"更有价值**：十行全红说明变异太粗暴，分不清是哪条断言在起作用。

## 271. 非 Block 的 `Size` 不是一个尺寸 —— §0.18 换的第三张脸

`Shape = Ball` 的直径是 `min(Size)`；`Cylinder` 的直径是另两个分量的 `min`、轴长取剩下的那个。
所以 `Size = (0.5, 46, 35)` 的 Ball 是**一颗 0.5 stud 的弹珠**，46 和 35 是**死数字**，渲染器不看。
「位置 ± Size/2」这条尺子在**旋转过的件**上会错朝向（§0.18），在**非 Block** 上更彻底：
它**读出一个根本不存在的尺寸**。我据此报出「46×35 的玻璃板」，两张截图和三组实例读数
**同时**在否定它，而我先怀疑了模型。

**纪律**：量一件东西之前先看 `Shape`；`Block` 以外一律走形状规则，不走包围盒规则。
**同一族的第三条**（前两条：旋转、分组汇总）——**错的量法不报错，它只安静地给你一个数。**

**附带一条**：`Size` **不随 `Shape` 变**。用户那两块板 `(0.5,46,35)` / `(0.45,41.4,31.5)`
改成 Ball 之后参数原地留着，形状缩成弹珠 —— 那对数字是**改形状的化石**，
从它们能反推出原来的设计。**死参数是线索，不是噪声。**

## 272. `undo` 是一次**盲写**，不能当清理工具

我为了撤销自己刚做的染色实验调了一次 Studio 的 `undo`。结果：**什么都没撤销**，
而 `undo` **不返回它改了哪一条**。它和「读」放在一起会让人误以为安全 —— 它不是读，
它是对**别人状态**的一次写入，且不可观测。若它当真撤销了别的什么，我连发现了都不会知道。

**配套的那条更贵**：我改一件东西之前**没有把原值读全** —— 记了 `Color` 和 `Transparency`，
**没记 `Material`**。于是「还原」里有一项只能是推断（同族 22 件全 `Metal` + 颜色同档 → 按 `Metal` 还原，
并向操作员明说）。**写之前先读全值，读全值比读懂值便宜。**

## 273. 交付物是别人的设计时，**只读不动**

用户说的是「看下」。我做的是：普查 → 读脚本 → 读属性 → 拍照 → 做**一次可逆实验**把
「画面上到底是什么」钉死 → **逐项还原** → 报告里把**推断**和**实测**分开写。
**没有**去改他的材质或形状。理由：`idk` 是他的设计迭代，`Glass` 可能是**故意**选的；
而我刚刚已经因为一次没读全值的写入而要向他交代一件说不准的事。
**「看下」这句话的授权范围就是看。** 改与不改，差一个明确的字。

---

## 274. 「正确衔接」里的**那个数**必须是量出来的，其余都可以是挑的

用户要的是「往外扩展为 24 边形墙壁，**并且要正确衔接**」。这一句里只有「衔接」是不可替换的：
新的 24 边环的 apothem（68.000）、墙高（13.20）、壁厚（4.00）**都是我挑的数**，改一个数就换一种比例；
而**下环的 apothem 63.712 和相位（顶点在 +X）只能来自 720 条射线**，错一点就不是接上了，
是**摆在旁边**。

所以 design 块的第一行就写着「MEASURED IN THE PLACE, not chosen」，并且脚本里有一条
断言用 `1e-3` 的量级再确认「我叫做 18out 的那条环，半径就是 R_OUT18」。
**自由参数和量出来的参数要在代码里长得不一样** —— 否则下一个人调比例时会顺手把它一起调了。

（顺带一条与它配套的：`A24` 一旦调回 63.712 就**不悬挑**，但那也不是「往外扩展」了。
悬挑 3.3 stud 是这句话的直接后果，我选了留着，并且把它写进了 PROGRESS 86.3。）

## 275. 归一化必须**各自除以自己** —— 除以「场景里最大的那个」不是归一化

`apply_chamber_wall_materials.luau` 第一版要判断一个 MeshPart 是不是「底座」，
做法是把两边的尺寸都除以**场景里最宽的那一件**，再比。它**通过了设计尺寸的测试**，
然后在整体 ×1.6943 的那一轮里**全军覆没**：

```
Workspace...ChamberWall24A  219.225 x 2.033 x 219.225   ratios (1.00000, 0.00927)   ← 与设计一模一样
WARN ... ChamberWall24A: UNMATCHED (closest WallBand, score 0.5062) -- left as it is
```

**比例打印得完全正确，而判据是错的** —— 因为分母 `W` 是**场景的**，而 `row.size` 是**设计的**，
两边不是一个尺度。除以场景最宽只在「导入恰好是设计尺寸」时抵消，**也就是在最不需要它的那一轮**。
正确的做法是 `shape(v) = v / max(v.X,v.Y,v.Z)`，**每一件都除以自己**，两边的尺度都消掉。

**教训的形状**：一条只在参数取默认值时才成立的归一化，在默认值上测是测不出来的。
**所以那个 ×1.6943 的测试不是「顺便多测一种」，它是唯一能拿到这条 bug 的测法**
（1.6943 是有来源的数，不是随手挑的倍数：LaserPort 实测 = 10/5.902）。

## 276. 倒角**关掉**，而不是调到看不出来

`trg.finish()` 的倒角按 25° 过滤。这条过渡带倾
`atan((68.000 − 63.712) / (4.20 − 1.20)) = 55°`，**远在门槛之外** ——
倒角会去吃全部 84 个三角形，把它们切碎，并把两条环从设计高度上拽下来
（Phase 84 的 `--cross` 上量到过同一个现象：`verts 126 → 240`，`band_faces` 归 0）。

**DECISIONS 269 已经写明那个「角度」过滤器其实滤的是「形状对不对」** —— 于是这里有一个
诱人的错误做法：把 bevel offset 调小，让损伤看不出来。**不。** 那等于把一件已知会撒谎的
工具调到它的谎话小到不容易读。`bevel=0.0`，理由写在代码里。

## 277. 相位不变性可以说「不需要修正」，但**必须说清是哪个方向的不变**

FBX 导入把 `(bx,by,bz)` 映成 `(−bx, bz, by)`，即 Studio 方位角 `= 180° − b`。
18 边顶点每 20°、24 边每 15°，**两个集合都对 180° 旋转不变**，所以也对这个镜像不变 ——
导入后**不需要转**。这一条省掉了一次「导进去发现对不齐」的往返。

**但它是关于这个设计的结论，不是关于导出器的结论。** 一个偏移 7.5° 的 24 边**不**不变，
那种设计必须在导入后转 7.5°。把它写成「FBX 导入不改变朝向」就会在下一个设计上炸 ——
**不变性要连它的对称群一起写下来**（这里写的就是「顶点集对 180° 旋转不变」）。

## 278. 「症状的成因就是被要求的功能」时，不要修症状

`Workspace.idk` 里那颗白球是 `Material = Glass`。用户说「光照上去会有反射」，
我给的处方是**改成 `Plastic`**（哑光高光少）。他当天就驳回：

> **「不对啊，你改成plastic就没有那种扭曲的效果了啊」**

他说的「扭曲」是 Glass 的**折射**，而**折射和高光出自同一个着色器** ——
那个亮斑不是叠在玻璃上的另一层，**它就是玻璃**。关掉高光就关掉折射，
**我拿他要的功能去换了一个他不喜欢的副作用**，还把它写进了交付文档。

**判据：「这个症状是不是刚好由一个他要的东西产生？」** 是的话，改动方向就不是「削掉它」，
而是「在材质层重做一份只有其中一半的」——这里对应 `MaterialVariant`，
`BaseMaterial = Glass` + 白 `RoughnessMap` 压反射 / 黑 `MetalnessMap` 压镜面，
**但两张图都要上传的 `ContentId`，本机没有凭据**（`ROBLOX_OPEN_CLOUD_API_KEY` 与 creator id 都没设），
所以这条路**当前封死**，不是「没想到」。不装东西的替代只有三条，且各有代价：
`Lighting.EnvironmentSpecularScale` 1 → 0 是**全局**的（会动整个世界的高光）、
`Material = Water` 换的是另一种折射而不是「没有反射」、把 `Glass` 染黑只压亮度不压高光。

**顺带纠正一条我自己写下的观察**：「两个 Glass 件的 `Reflectance` 已经是 0」
意味着**根本没有一个独立的反射层可以关** —— 那句「关掉反射」在实现上是空的。
所以这条取舍里连着两个错：**改错了东西**，并且**改的那个东西不存在**。

**记这一条的理由**：错的处方已经进了 `CLAUDE.md` §8 的 Phase 85 段，而那一份**每轮都进上下文** ——
放在那儿的一句坏建议，比放在 `PROGRESS.md` 里的一句坏建议贵得多。已在原处改成更正 +
指向本节。（同 §0.13 的教训：**散文说的谎和代码说的谎一样贵**。）


---

## 279. 射线打 MeshPart 查的是**碰撞体**，不是渲染网格 —— 而运行时建的 MeshPart 碰撞体**改不了**

`workspace:Raycast` 命中 MeshPart 时给的是**碰撞几何**，不是渲染网格。默认
`CollisionFidelity` 是**凸包**，环面的凸包是**实心圆盘** —— 于是出现了
「同一个网格，24 角那一段读数逐位正确、领圈那一段胖 0.6 stud」。

**这个矛盾本身就是线索**：一个面真、一个面假，物理上不可能同时成立，所以
**错的是尺子**。我没有先怀疑它，是反解出凸包公式之后才对上的
（`64.695 + (h/4.2)*3.892`，y=0.6 -> 65.2508，读数 65.2497）。
**判据**：同一把尺子量同一样东西、两个部位给出不一致 —— **先怀疑尺子，别先怀疑物体**。

**第二条更硬，而且它有对照。** `CollisionFidelity` 在
`MeshContent.SourceType = Object` 的 MeshPart 上**写不进去**：
Default / Hull / PreciseConvexDecomposition / Box 四个值，**四次赋值全部 `pcall` 返回 ok、
四次读回 `Default`**，re-parent 无效。而在邻座 `SourceType = Uri` 的导入件上，
**同一个写立刻生效**（它们本来就已经是 `PreciseConvexDecomposition`）。

**没有邻座那三件，我只能得出两个都错的结论** ——「Studio 写不进去」，或者「我调用写错了」。
**对照才是这条的全部价值。**

**教训**：`pcall` 返回 ok 只说明**没抛错**，不说明**生效**。
凡是「写了之后还要读」的属性，**写完必须读回**；而且**读回的值要和写之前比** ——
「设置成功」和「值就是我想要的」是两句不同的话。

## 280. 拿不到**正确**的碰撞体时，选「没有碰撞」而不是「错的碰撞」

凸包在这里是一块 **137.17 stud 见方的实心圆盘**，跨 y 47.4 -> 60.6，会把反应堆腔室**封死**。
两个选项都是谎：`CanCollide = true` 是一座**看不见的墙**，`false` 是一面**走得过去的墙**。

选了后者。理由：**错的碰撞会改变玩法**（§1.4 第一条明令禁止），
而没有的碰撞只是这面墙少一个功能 —— 它本来就是装饰性的延续。
**两个都是谎的时候，选小的那个，并且把原因写进建它的那段代码里**，不只是写进报告。

**顺带**：`CanQuery` 要一起关。同一个凸包也会被**游戏里任何一条射线**看见 ——
只关 `CanCollide` 是关掉了物理，把它留给了查询。

## 281. 正多边形的 `rmax` 落在**每一个**角上 —— argmax 是噪声，用 argmin

`rmax` 在正多边形的每个角上都取到，所以「谁最大」由**最后一位的 float32 噪声**决定：
同一份几何两次跑，角度给出 `340.00°` 和 `320.00°`。
`argmin` 每个扇区**唯一**，所以相位改成报 `argmin mod (360/n)`，
并且断言它等于 `(360/n)/2`。

**一般化**：报告一个**极值点不唯一**的几何量的位置，报出来的是**存储格式**，不是几何。

## 282. 容差不能比被测量的**存储精度**还小

构建时的自检把 apothem 的容差写成 `1e-6`，于是**必然**红：
`Vector3` 是 float32，在量级 ~64 上的可表示步长已经约 **7.6e-6**。
改成 `1e-3`，**并把原因写进代码**。

**它红的方式很有欺骗性**：报「apothem 不是 A18」，看起来像几何错了，其实是尺子的刻度比材料还细。

## 283. 会**写**世界的探针，必须还原成**它找到的样子**，不是它想要的样子

`cw24_import.luau` 要测「`CollisionFidelity` 在 Uri 件上写不写得进」，所以它得真写一次。
第一版复原时写死成 `Box` —— 那是把一件**没人让我碰的东西**静默改成探针想要的值。

改成先记 `was`、再还原 `was`。**同 §0.13**：这类失败长得**完全像什么都没发生**，
而且它会活到**下一次真机**，那时候没人记得是探针干的。

## 284. **永远不可能通过**的检查是噪音；`#out` 不是检查数

`cw24_verify.luau` 原来有条
`want(holePCD == nil, "precise collision keeps the chamber's opening open")` ——
而那个属性**根本写不进去**，所以它**永远红**。永远红的检查会**训练人忽略红**。
改成写**发现**（属性只读 + 对照证据）**加上交付物必须成立的两条**
（`CanCollide = false` / `CanQuery = false`）—— 检查从此可以真的红。

同一份文件末尾原来写 `say("ALL CHECKS PASS -- %d ok", #out)`：
**`#out` 是日志行数，不是检查数**。加了一个真计数器，现在报 `32 ok, 0 failed`。
**一个把行数当检查数的汇总，会在你删掉一条检查时把数字变大。**

## 285. 不删不是自己的东西：搬走、留档、**搬之前先断言形状**

`Workspace.Wall24` 是用户照 §3.5 手动拖进来的（1.0769 倍、偏 0.873、接不上）。
§0.12 第三条要求动 Workspace 之前先问 —— 问了，他答「搬进 ServerStorage 存档」。
搬成 `ServerStorage.Wall24_import_20261004`，**没删任何东西**。

**搬之前 `cw24_park.luau` 先断言它找到的形状**（是 `Wall24`、非空、目标名不冲突），
**对不上就拒绝动手**。一个「把同名下的东西搬走」的脚本，
总有一天会搬走**错的那件**，而它照样会打印「已搬走」——
**没有断言的可逆操作，只是「慢一点的不可逆」。**

## 286. 外形与碰撞不一致是**可见缺陷**；宁可重做几何，也不加一件看不见的碰撞

那面墙的 `CanCollide=false` 是从「凸包是实心盘、不能进物理」推出来的**保守选择**，
直到量出来：它**是整个邻里唯一不参与物理的一件**（环 19/19、与墙重叠的 60/60 全是实心）。
保守在这里变成了「玩家能穿过去的那道墙」。
三条路摆在用户面前 —— ① 再加一件**隐形**碰撞环、② 保持能穿过、③ **由同一批 Part
同时负责外形与碰撞**；他选了 ③。理由就是选项里那句：**没有「视觉与碰撞不一致」的可能**。
**代价照付**：件数 1 → 66，已验过的几何重做一遍（Phase 87 的几何一个字没改，只是换人承载）。
**没有动玩法机制**（§1.4 第一条）—— 这面墙是 Phase 87 才建的新件，不是既有机制；
被它取代的 MeshPart 也**没删**，进了 `ServerStorage`。

## 287. 正多边形壳 = 每边一个 Box，弦取满 `2a·tan(π/n)`

弦长取**满**时，两个半弦正好够到多边形的**顶点**，相邻面板于是在顶点处**恰好相接**、
在内侧轻微重叠 —— **一圈面板的并集精确等于多边形壳，角也是**。
不需要楔形补角、不会缺角、也不会外凸。
弦取**不满**（环 `18` 自己取的是 `20.705`，真弦是 `22.468`）就会在每个顶点留 V 形缺口，
得靠那块 `UnionOperation` 盖板补上 —— 那是**另一种**做法，不是错的，
但**得知道自己选的是哪一种**。本次选「取满」。
**一般化**：能用精确基元拼出来的形状，别用近似基元再补角 ——
补角件与它补的主体是**两个**东西，后来的编辑迟早只会改其中一个。

## 288. 斜面板的厚度是**垂直厚度**；而且端面倾斜必须让它**不外戳**

带的面板斜 55°，内外两个表面是**两条平行线**：水平隔 4.00 → 垂直隔
`4.00·cos(55.02°) = 2.2930`。按 4.00 写会让带**厚出 74%**。
第二件：盒子的端面**垂直于斜面**，所以上端面从 `(68.000, 4.20)` 往**内上**方走 ——
外缘**恰好止于墙脚**时，端面永远不超过 68，**不会戳穿墙的外表面**。
这一条是**先想清楚再写**的约束，不是事后调出来的数：外缘一旦越过墙脚，
斜带就会在墙面外面露出一圈薄薄的毛边，而量 apothem 的那些检查**一条都不会红**。

## 289. 「盒子拼的多边形壳，角上比理论多边形凸出」——所以手算的台肩量会偏大

接缝处的台肩：手算 **0.434**、实测 **0.3002**。
原因是带的面板宽 17.9047 是按**顶端** apothem 68 取的弦，在底端（apothem 63.712）
按多边形该只有 **16.77** —— 盒子的角在切向上**悬出**那个并不存在的顶点。
**手算拿两个多边形顶点相减，减掉了一个不存在的量。**
同一份手算里的**另一项**（带追上那个角的高度 0.5153 vs 实测 0.520）几乎全对，
因为它算的是**面中心方向**上的交会，那里没有悬出 ——
**同一个几何量，一个方向对、一个方向错。**
**纪律**：手算是用来**定形状**的，不是用来**出交付数字**的。
交付数字一律实测，**两者都写下来**（手算错的那一个也写，就写在实测旁边）。

## 290. 错的问题也会得到一个响亮的数（§0.18 第四张脸）

验证器问「rho 62 的向下射线落在 collar 的顶面上吗」，答 **y 50.2007** ——
一个干净、精确、**完全错误**的期望值（48.6）。collar 的顶面**处处被带盖住**：
带的内表面就**从 collar 的内缘起坡**（两者都在 apothem 59.712），
所以那个面**不存在**于任何一条向下射线的路上。
**处置不是「换个位置再问」，而是把问题改成对的**：断言改成量**带的内表面**，
并把「顶面被盖住」写进日志 —— 下一个人读到的是一条**说明**，而不是一条被删掉的检查。
（§0.18 至此四个面孔：`Position ± Size/2`、分组包围盒、非 `Block` 的 `Shape`、**问错的面**。）

## 291. §0.14「截图给出逐字节相同的画面」今天不成立 —— 记录，不改历史

四张**显式机位**的 `rblx_screen_capture` 给出四张清晰不同、且正确的画面
（整体 / 接缝特写 / 俯视 / 贴脸的接头）。§0.14 那条曾让「靠看图验证」被判死，
现在**至少官方工具这条路是活的**；`CLAUDE.md` §0.14 加一行**带日期**的更正。
**边界要写清**：它证明的是「我能看到渲染结果」，**不等于** Play 模式 / 玩家输入那一半能读
（§0.16 未变）。**能看图之后，§0.18 那类错会更早暴露** —— 那面「46×35 的玻璃板」
就是被两张图否掉的。

## 292. 幂等的操作不该被**一次性**守卫挡住

`park` 守卫原来写「存档名被占 → 拒绝」，于是为了「盘上的文件 = 跑过的文件」而**第二次**建墙时，
被**自己上一次的存档**挡住。改成只有**两者同时成立**才拒：
「世界里还有待存的 mesh」**且**「存档名已被占」—— 那才是真的会丢东西的情形。
**一般化**：守卫要守的是**不可逆的那一步**，不是「这个脚本以前跑过」。
一个挡住合法操作的守卫会被绕过，而**绕过它的那一次没有守卫**。

## 293. 「最外围」是一个**半径**，而这个环有**两个** —— 取大的那个，而且它是可证最小的

用户说的「依据 18 那个 part 的**最外围**来扩」，`最外围` 是我读错过的一个词两次。
第一次（Phase 86/88）我读成**面平面**（apothem 63.7114），于是环的 18 个**角**（64.6951）
从新墙里戳出来，戳出量 0.3002..0.9837 —— **而那一版把这个差写进了设计注释，当成故意的台肩**。

正 n 边形壳的「最外围」**永远是角**：`R = a / cos(π/n)`，比面平面大 `1/cos(π/n)`。
外接 m 边形（inradius `R`）包含它（circumradius `R′`）当且仅当 `R ≥ R′`，
所以 `R = R′` **就是最小可行值**，不是「保险起见取大一点」。
**一般化**：一个几何量如果在你读它的那个词下面有**两个候选**（平面/角、内/外、局部/世界），
先把它拆成**两个名字**再选，别让一个词替你做选择。

## 294. 转**半格**的壳，过掉**所有**半径检查 —— 相位必须锚在**被接的那个东西**上

正 n 边形转 `360/2n` 度之后：apothem、弦长、面积、轮廓半径**全都不变**。
所以「collar 63.7120 对环 63.7114，delta 0.0006」这个**验收数**，
在相位整整差半格的情况下**照样成立**。半径检查对相位是**瞎的**，
唯一看得见的是角度比较。

配套的两条，缺一条这检查就没用：
- **锚在环上，不锚在自己身上。** 拿墙的格去量墙 = 自问自答，转多少度都自洽。
  量的是「**接上了没有**」，所以基准只能是**已经在那儿的那一件**。
- **拟合 apothem 时要按环自己的相位去取面法线。** 一个正 n 边形顶点在
  `phase + 360k/n`，它的**面法线**在 `phase + 180/n + 360k/n`；
  拿顶点方向去投影，量回来的是 **circumradius** —— 一个响亮的、自信的错答案
  （§0.18 同族：错的量法不报错，它只安静地给你一个数）。

## 295. Blender `--background --python` 下，未捕获异常退出码是 **0** —— 崩溃与通过同形

**实测**（2026-10-04，Blender 5.1.2）：

| 脚本结尾 | 退出码 |
|---|---|
| `raise RuntimeError("boom")` | **0** |
| `sys.exit(1)` | 1 |
| `os._exit(1)` | 1 |

于是「检查器崩了」和「检查器全过」在 shell 眼里**逐字节同形** ——
而且**崩溃更可能发生在错误的那一次**（畸形输入正是会让解析器抛异常的那种输入）。
`--no-bridge` 变异就是被这一条吃掉的：未桥接的网格一条带面都没有，
`max(... for f in band)` 抛 `ValueError`，进程 rc=0，**盘上读到的是一片绿**。

修法是一个 `try/except BaseException`（`SystemExit` 原样放行）把逃出来的任何东西
变成 `sys.exit(1)`。**这不是这个资产的细节，是所有 `--background --python` 检查器的通用洞。**

同一天翻出的第二半：变异必须写成 `--python s.py -- --flag`。
写成 `--python s.py --flag` 时 Blender 把 `--flag` 当作**要打开的文件**
（`ERROR Cannot read file "...\--wrong-pair"`），然后**照常跑完、照常导出** ——
于是「四个变异全红」这一整张表都可能是假红（红的理由是别的）。

## 296. 空集合会说**两次**谎：`all([])` 为真，`max(())` 抛

同一段代码里同时中了两条，方向相反：

- `all(len(f) == 3 for f in band)` 在 `band == []` 时是 **`True`** —— 「全是三角形」**真空通过**；
- `max(wrap(f) for f in band)` 在同一个空表上抛 `ValueError` —— 配合 **295** 就是**静默绿**。

一个空的主语既能让断言**无条件成立**，也能让检查**根本不跑**。
所以：**凡是以「缺失的东西」为主语的断言，先 `bool(x)`。**
配合 295 的 try/except，这条是**兜底**而不是唯一防线 —— 两层都要有。

## 297. 「半径 0.8」有两个读法 —— 取外接圆，但把另一个也**打进日志**

正 n 边形的「radius」可以是**外接圆**（到顶点）或**内切圆**（apothem，到面平面），
同一句话两个意思，差 `cos(π/18)` = **1.5%**。取外接圆，理由是**构造性的**：
把顶点放在半径 r 的圆上画环，那个 r 就是外接圆，也是唯一让 18 和 24 两环落在**同一个圆族**上、
从而「同轴」这句话有内容的读法。

但**取一个不等于另一个不存在**：构建日志里并排打印 apothem（0.787846 / 1.189734）。
这不是「多打一行」，是 **Phase 89/§0.18 的正面用法** —— 上一轮的错正是「两个半径里用了错的那个，
而所有检查都在量另一个」（取舍 **293**）。**歧义的读法要写在交付旁边，而不是等被问。**

## 298. 42 是 Euler 逼出来的，所以「6 组 × 7」不是设计选择

环面（annulus，两条边界）的 `χ = (a+b) − (3F+a+b)/2 + F = 0` ⇒ `F = a+b`。
`18 + 24 = 42` 于是**不是**用户挑的，是他那条 `18 × (4/3) = 24` 的**唯一**三角形实现。
**推论（有用）**：任何「6 组各组 7 个」的方案都自动满足 Euler，所以**Euler 不能用来验证他的表**；
能验证的是**那 42 条关系本身**（`--fan` 变异红的正是这一条）。**只能被一个变异逼红的断言，才是那条断言的证据。**

## 299. 按**边数**给面分类，回答的是**文件格式**，不是资产

初版 `len(f) == 3` 认桥接三角形 → GLB 里把 22 + 16 个端面三角形一并数进去，
「42 个桥接三角形」读出 **80**，闭合、材料跟着全红。**同一个文件、同一份源码，两个格式给出两个答案**
—— 这就是「问题问错了」的信号，不是「文件坏了」（与 Phase 84 的
`open_edges=504`／取舍 **265** 同一族）。

**改用 material slot 分类**：它是**两个文件都有的**，而且它**本来就是第 6 条在说的事**。
输出面数改成**三角化后的三角形数** `Σ(len(f)−2)`（两格式都是 80），不再断 `44 == 44`。

## 300. 只与**定义**同义的断言不是断言

分类改成按 slot 之后，「42 个桥接面都是 slot 1」**变成同义反复** —— `br_faces` 就是按那个 slot 定义的。
所以**删掉它**，换成一条**读文件**的：把两个 slot 的 `Base Color`（取不到再退 `diffuse_color`）
读回来，对第 6 条要的蓝和红。理由不是洁癖 —— **Workbench 渲染读的是 `diffuse_color`，
而导出器写的是 Principled 的 `Base Color`，是两个字段**：一张看着全对的图，救不了一个导出成白色的材质
（§0.14b 的反面：这次**图是对的、问题是它没在量那件事**）。
实测两个格式都逐位来回（`0.045/0.130/0.800`、`0.800/0.055/0.045`）。

## 301. 分区不能靠 `round()` 落在边界上：银行家舍入 + 15° 整除 60°

「每组 3 个小角 + 4 个大角」按方位分区，第一版 `int(azim(p) // 60)` 与第二版 `round()` **都错**，
而且**看起来只错一半**（实测：小环 `[3,3,3,3,3,3]` 全对，大环 `[3,4,5,3,5,4]`）。
三条叠在一起：

1. 24 边形的 **15° 间距整除 60°** → 角**正落在分区边界上**；
2. `atan2` 对「标称 60°」的角回 **59.999999** → `//` 把它丢进**下面**一格；
3. Python 的 `round()` 是**银行家舍入**（`round(1.5) == 2`、`round(2.5) == 2`）→ 边界角**忽上忽下**。

**修法：先把方位吸附到环自己的角格**（`round(azim / (360/n)) % n`），**再**除成组号 ——
吸附留 ~10° 余量，浮点是 ~1e-5。**副作用是断言更强**：从「每格有几个」升级成
「第 g 组 = 小环 `3g..3g+2`、大环 `4g..4g+3`，六组逐个比」。
**18 边形那一半会掩盖这个 bug**（20° 间距永远碰不到边界）—— **两个样本都错才算错，一个错是线索。**

## 302. 一个从没被变异逼红过的断言是装饰 —— 把**没有**的那些也写下来

（沿用 **205 / 270** 的纪律。）这一轮的变异给规格四条各配了一个红：

| 规格 | 变异 | 红在哪 |
|---|---|---|
| 3 两个同轴环 | `--radius` / `--zshift` | 18 边形外接半径 / 顶点分落两个平面 |
| 4 端面是 n-gon | `--one-cap` | 盖角数、面积、闭合、Euler、`.blend` 那一面 |
| 5 用户那 42 条 | `--fan` | **42 条关系有面不匹配** |
| 6 蓝端面 + 红桥接 | `--swap-rgb` | **两个 slot 的颜色** |

`--swap-mats` 单独留着并**不是**重复：它换的是**面用哪个 slot**（颜色不变），红的也是另一组断言。
**还**没有自己变异的：包围盒、同轴、24 边形半径、42 个唯一顶点、两个 slot 的存在性 ——
这些是**佐证**而非规格条目，**写下来算已知缺口**，不算覆盖。

## 303. 片子必须是 `t` 的纯函数 —— 拖进度条要是真跳，不是快进（Phase 91）

片头整个就是 `render(t)`：进来只有 t，出去只有样式，**没有状态机、没有累积增量、
没有任何东西记得"上一帧"**。三条直接后果：

1. **拖动进度条 = 真的跳到那一刻**。带状态的写法里，拖到 20 s 却不把前面
   15 s 的动画播一遍，画面对不上；纯函数没有这个问题，它根本不看历史。
2. **循环第二遍和第一遍逐字节相同**。这是可以验的性质，不是一个愿望。
3. **每一行的出场时间都在 `T` 表里读得到**，不需要跟踪代码去反推。

**这和 `GameState` 的"单一真相源"是同一条纪律**：时间只有一个，所有元素都是它的读者，
谁都不许自己攒一份。

**推出来的两个结构决定**：`#stage` 是固定 1920×1080 设计空间、整块等比缩放 ——
于是任何窗口都是同一幅画；`#film` **故意从 `#stage` 里拆出来** ——
CRT 收线只压 `#film`，播放器在外面，否则片尾控制条会被一起压扁。

**将来若要加音效**，必须同样由 t 驱动（`[at, until]` 窗口 + 记住**窗口序号**），
**不许写"我是不是已经放过这个了"** —— 那是一个状态机，会让拖进度条变成随机行为。
（本片**无声**：操作员明确要求不用 `asstes/` 里的音乐。那个空着的 6.13 节就是留给它的接法。）

## 304. 出处分**三**档：V 逐字采集 / G 游戏别处原文 / R 重建 —— 合成两档就是过度声称（Phase 91）

片头 45 行诊断，一开始只想分"来自游戏"和"编的"两档。**不够**：
有一批行（8 行）确实是**游戏自己的字符串**，但来自**另一处采集**，不在开机屏这一屏上。
把它们塞进"来自游戏"这一档，读的人会以为是**同一次**采集里的 —— 那就是过度声称。

于是三档：**V** 逐字恢复自采集、**G** 游戏里别处的原文、**R** 重建（13 行）。
**R 的那些行不删，留着但标出来**（"不混进实测里"）—— 删了片头就没有开机刷屏那种密度，
而标出来之后读的人知道哪几行是新的。同样地，三条规格卡
（`NO CONTROL RODS` / `THREE INDIRECT SYSTEMS` / `ONE SHIFT TO GET IT RIGHT`）
是全片**唯一**一组"不是游戏原文"的文案，单独列一节，不混进上两张表。

**这条的现代版本**：交付物旁边要写清**哪个数字是量出来的、哪个是挑的**（同 274）。
这里量出来的是文字，挑的是节奏。

## 305. 拼写错误是**数据**，不是待修的 bug（Phase 91）

采集里是 `ACCEPETED` / `INFASTRUCTURE` / `MANFUACTURING` / `UNAUTHORIZE` /
`REPROCUSSIONS` / `PRIMAIRY`。**这些不是打错的**，是游戏自己的语气；
逐字恢复的意思就是**连它一起搬**。**改"对"了才是改错了** ——
改完那行就不再是那一行，而后面所有"逐字"的说法都跟着变成假的。

（同族：Phase 90 里"端面留作 n-gon"只在 FBX 问原话成立，glTF 问就变三角。
**格式/载体换了，问同一句话会得到不同答案** —— 所以出处标签要连着载体一起说。）

## 306. 变异只红**一条**才算精确 —— 红五条等于没告诉你违反了哪条性质（Phase 91）

沿用 **298 / 302** 的纪律（从没红过的检查是装饰）。这一轮它的加强版是：
`_tools/intro_mutants.py` 把每个缺陷种回副本，除了"必须红"，
还检查**只有指定那一条变红** —— 8 个变异**每个恰好红一条**，说明断言是**精确**的。
一个变异红五条的话，你得先弄清哪几条是它真的违反的，**覆盖率数字就失去了分辨力**。

**已知边界也写下来**：两个结构缺陷（播放器不能嵌在 `#film` 里、点击必须
`stopPropagation`）**没法用数值微调表达**，只能用文本替身。
另外 `intro_check.js` 里那四条 CSS 事实（水印高度、标记顺序…）是**文本**断言，
在 `(source)` 标签下**不算"渲染过"** —— 与 §0.14b 同一条：图证明"看起来对"，
读数证明"真的是那个值"，两样都要，**谁也不替谁**。

## 307. 一个"读 style"的检查器，**结构上**看不见布局缺陷（Phase 92）

`_tools/intro_check.js` 24 条全绿的同时，片子里**最重要那块面板前 7 秒是空的**。
它断言的每一句话都是真的 —— `node.style.opacity` 确实是 `1`，45 行一行不少 ——
而屏幕上**最多只有 2 行**（能装下 23 行）。根因是 `#diagList` 用了 `bottom:0`：
它 1215px 高、窗口只有 630px，于是块的**顶端落在 −346px**，前 25 行全在面板外面；
而滚动变换 `-max(0, shown*rowH - windowH)` 又在往上推同一块东西 ——
**两个位移相加，而不是抵消**，所以错得越多、越像故意的。

**这是 §0.2 换了第七张脸**：那一课是"读模块状态 ≠ 读实例状态"，
这一课是"**读实例状态 ≠ 读屏幕**"。行是真的亮了，位置是错的。

**结论是加一条通道，不是加一条断言**：桩 DOM 里 `getBoundingClientRect()` 是假的、
没有布局可错，所以这个缺陷**在那一侧永远不可能红**。凡是"位置/尺寸/是否被裁掉"
这一类性质，**只能**由真浏览器持有 —— `_tools/intro_render.js --check`。
两条通道各管一半，谁都不许替对方签字（同 §0.14b：图证明"看起来对"，
读数证明"真的是那个值"）。

## 308. 断言要问**设计真正在说的那一面** —— 我第一版把 27px 判成了缺陷（Phase 92）

L3 第一版量的是"**最新的、已经亮透的那一行**的底边是否贴住面板底边"，于是
t=7.25 红在"偏 27px"。那不是缺陷，**是我的尺子问错了面**（**§0.18 第五张脸**）：
滚动索引用 `floor(clock)` 推，而每行有 0.05 s 淡入，所以"索引进到第 27 行"时
"亮透的"才到第 25 行 —— 差的正好一行。

设计说的是"**最新一行钉在底部**"（游戏用 `CanvasPosition` 钉底）。要量的是
**最后一条已经开始出现的行**（`opacity > 0`，不管多小）的底边。换成这个之后
Δ=0。**同一个几何量在"最新的行"这个词下面有两个候选**（亮透的／出现的），
和 293（`最外围` = 面平面还是角）同族：**一个词如果替你做了选择，
你读到的就不是测量。**

## 309. 浏览器当**尺子**，判定写在 Node 里（Phase 92）

`--check` 让页面把 39 个时刻的原始测量（lit / visible / live / 底边 / 块顶 / 行高）
当 JSON 吐回来，**判定在 `intro_render.js` 的 `judge()` 里**。
两个理由：**① 量了又判的人会悄悄改判据** —— 判据放在另一个文件里，改它要显式去改；
**② 判定要能读** —— 浏览器里那段只负责量，一行一句"什么是正确的"写在 Node 里，
人和下一次会话都读得到。

顺带一条：L3 的"已经滚起来了"这个前提，是**从布局读的**（块顶被推到面板顶之上），
不是拿行数把片子自己的公式再算一遍 —— 后者对**任何**变换都会通过，
因为那是把它的话说回给它自己听。

## 310. 渲染不是录屏 —— 纯函数的钱在这一步兑现（Phase 92）

因为片子是 `render(t)`（**303**），"渲成视频"就是**逐帧 `render(t)` + 截图**：
没有时钟要抢、没有帧会丢、同一条命令跑两遍出同一个文件。实时抓屏只会更差 ——
它采样的恰是片子当初特意不依赖的那个东西（页面自己的 `requestAnimationFrame` 节奏）。

**两个必须做对的地方：**

1. **页面的自动播循环要在它存在之前就被掐掉。** 片尾自启动一行
   `requestAnimationFrame(now=>{play(); tick(now);})`（第 935 行）。用
   `Page.addScriptToEvaluateOnNewDocument` 把 `requestAnimationFrame` 打成空函数，
   **在页面脚本跑之前**注入 —— 否则那个循环会一直在我背后覆写已经驱动的帧。
   **这是 §0.19 的同一条**："在跑但没事发生"和"没写"从外面长得一模一样；
   这里反过来，**两个写入者都在跑**，而盘上的代码读起来完全正常。
2. **视口钉成恰好 1920×1080**（`Emulation.setDeviceMetricsOverride`），
   于是 `fit()` 算出的 scale 恰好是 1、没有黑边要裁。

**播放器是 UI 不是片子**：`#player` / `#bigplay` / `#hint` 渲染前 `display:none`。

## 311. 行高**量出来**，不写两遍（Phase 92）

`27` 原来活在两处：`.drow` 的 CSS `line-height:27px`，和滚动算术里的 `shown*27`。
**改字号那天滚动会静默错位** —— 两边都对，只有相对关系错了，正是 §0.18 那一族。
现在读 `diagNodes[0].offsetHeight`，拿不到布局（桩 DOM）才回落到作者写的数 ——
和同一行里 `$('scroll').clientHeight || 690` 同一个写法。

**并且给它配了一个 FOLLOW 变异**（`diag-rowsize`：`line-height` 27 → 40）：
它**必须保持绿**。如果哪天有人把字面量写回去，这个变异就会开始红 ——
**留绿不是"没测到"，是"这条性质被证明了"**（同 302：把没有的也写下来）。

## 312. 交付的 mp4 进仓库，**通往它的 1051 张 PNG 不进**（Phase 92）

中间的帧是 ~300 MB 的过程产物，`intro_render.js` 跑完自己删；忽略它只是为了
**跑到一半被杀时不留东西在暂存区**（同 `_tools/_harness_out/` 的理由）。

`intro/THE_REACTOR_GAME_intro.mp4`（5.66 MiB）**是交付物，进仓库** ——
和 `asstes/music/ReactorShift.*` 同一条规矩：**生成出来的、要给人用的媒体进仓库，
生成用的中间件不进**。它确实可以从 `intro/index.html` 五分钟重跑出来，
但"可以重跑"和"要给人看"是两件事；操作员要的是那个文件。

**它的身份是量出来的**（`ffprobe`）：1920×1080、H.264 High、yuv420p、30 fps、
**1051 帧写入 = 1051 帧读回**、35.033 s（= 1051/30）、1.35 Mbps、5,932,568 字节。

> **【Phase 94 追记】** 上面这串数是**第一次渲染**的身份，**不改**（当时确实如此，
> 同 Phase 70 那条「同一个路径现在装着 b3」）。Phase 94 修完两处版式缺陷后**重渲**了同一个文件：
> 帧数 / 时长 / 格式**逐项不变**，只体积变了 —— **5,881,392 字节（5.61 MiB）/ 1.34 Mbps**、
> md5 `e59fe798f3a853f98f71f19726ddf25b`、捕获 424.9 s + 编码约 64 s。
> **路径上现在装的是这一份**；`intro/SHOTLIST.md` / `README.md` / `docs/SYSTEMS.md` 写的是当前值。

## 313. 波段功率看不见「一条连续的地板」和「打在拍上的撞击」（Phase 93）

同一个 2–8 kHz 八度带，一条**连续**噪声床和一条**被闸切成 8 分音符**的床，
八度带表给出的数是**同一个数** —— 功率是能量在**频率**上怎么分，
而「下雨」是能量在**时间**上怎么分。所以整条 `TARGET`（八度轮廓、RMS、side/mid、corr）
**全都对**，而操作员听见的是雨。

要抓它必须换一把**时间**上的尺子：**50 ms 帧 RMS 的 median / p90 / spread = p90 − median**。
参考 `6.26 / −28.36 / −22.09`，旧床 `3.03 / −25.75 / −22.71` ——
**地板热 2.6 dB、峰值只热 0.6 dB**，那个**不对称**就是掩蔽本身：spread 从 6.26 塌成 3.03。
把床关掉，texture 与参考**逐位相同**（6.26 vs 6.26）—— 证明**内容早就有对的形状**，
要改的只是「床不要再当一条地板」。取舍 314。

## 314. 均值为 1 的闸只搬**时间**、不动**功率** —— 这就是它能被调的前提（Phase 93）

`air_gate` 逐 8 分音符乘一条衰减包络、**归一化到均值 1**。后果不是好看，是**可调**：
`AIR_PTS/AIR_DB` 是**对着参考的八度轮廓解出来的**，均值为 1 意味着**开闸不改动任何一个带的功率**，
那组解**继续成立** —— 整条深度扫描上最差带只从 **+0.65 走到 +0.66 dB**、s/mid 0.122 → 0.123。
**不然每拧一次深度就得重解一遍轮廓，而那条轮廓是全曲的骨架。**

`DEPTH=0` 精确复现旧的连续床，所以那条扫描是**真 A/B 而不是重写**。

## 315. 均衡环锁死了每条 stem 的**占比** —— 一个 stem 的电平不是它自己的平衡旋钮（Phase 93）

母带里那个 `np.clip(TARGET_DB − prof, −12, +6)` 的环**每轮把八度轮廓压回目标**。
于是：**调一个 stem 的电平，改不了它在一个带里的份额**（环会把它连本带利还回去），
只改它自己的绝对量。`air_amt` 因此**从头到尾不是平衡旋钮** ——
把床降 3 dB，量出来 texture 只从 −28.07 走到 −28.02、s/mid 0.118。

**这条同时解释了另一件事**：`--probe` 里那套宽度预算能一次算对，也是因为环把
「每个元素占多少」和「总轮廓是多少」分成了两件事。

## 316. 母带之后**测不出**某个元素的突出度 —— 突出度正是那个环要抹平的东西（Phase 93）

第一次在**母带之后**量旋律余量：`master(full) − master(rest)`，逐音符临界带相减，
回 **narrow −26.7 dB / wide −272.7 dB**（相减为负、被地板到 1e-30）。

**这不是 bug。** 两个版本被那个环压到**同一条八度轮廓**上 —— 而「旋律有多突出」
**恰恰是那个环要消除的量**。所以：**能测的只有母带之前**，
而母带之前那张表就是感知那一张（环在带内只施加一个增益，带内的比例原样传到输出）。

**不要读成「母带杀了旋律」** —— 母带之后旋律照样在，只是**用这把尺子量不到**。
量不到的地方，尺子坏了和事实坏了长得一模一样。

## 317. 波段 RMS 分散度对「旋律突不突出」是一把**死尺子**（Phase 93）

把旋律推 **+10 dB**，`320–1280 Hz` 的帧 RMS 分散度 **3.79 → 3.79（动了 0.00）**，
+8 dB 和 +14 dB 也一样。原因不是缺陷，是算术：那个带被 kick / bass / arp 占着，
**一个带里 2% 的功率推不动一个百分位数**。

**和那个被自身素材顶死的 click 检查是同一族**（取舍 318）：尺子的**分母**是问题所在。
正确的分母是**此刻**：每个音符一条窗，量 `10log10( 旋律 / 此刻其它一切 )`，
`narrow` = 基频 ±1/6 八度（**载着音高那一条**）、`wide` = 到 4×（谐波）。
出厂版 narrow **−11.8 dB** —— **在自己那条临界带里比伴奏低 11.8 dB，在掩蔽阈之下**，
所以它读成织体不读成曲调；而谐波**持平**（−1.3 dB），给了「好像有个东西」的错觉。

**+6 dB 是挑的判据**（「清楚可闻，不是仅仅存在」），表里的余量才是测量 ——
两者在同一张表里必须长得不一样（同 274）。

## 318. 点击检查的基线必须是**局部**的 —— 全局百分位会被自己的素材顶起来（Phase 93）

旧 click 检查拿**最大步进 ÷ 全局 99.99 百分位步进**。材料平滑时没问题；
空气床变成**闸过的 8 分音符节奏**之后，那些起音**正好落进那 0.01%**，
百分位于是**涨上去迎接那个拼接**，检查**死了**：
**健康文件 1.98、一个 0.9 的拼接 3.23，两个都在旧的 4.0 门槛之下。**

**变异面板抓到的**（`click` 变体）—— 那正是它存在的理由。
改成**局部**：每个候选除以**它自己 ±5 ms 窗里的中位步进**。分离度 **1.6× → 8×**
（健康 15.9 = 一次 kick 的起音；0.9 拼接 129.7），门槛 45.0 落在几何中点。

**教训是尺子的分母必须是「邻居」而不是「全体」** —— 和一个**会随自己的素材长大**的基线，
迟早会把任何一个阈值吞掉。

## 319. 编码器过冲**真实存在**，而且**会随素材变尖而变大** —— 峰值上限是留给过冲的（Phase 93）

母带里的限幅器天花板是 −1.0 dB，但这一版**够不到它**（内存峰值 −2.05 dBFS）。
`peak` 那条检查管的**不是混音**，是**有损编码器的过冲**：mp3 −1.14 / ogg −0.91。

两次实测的迁移：
- 闸把顶层变尖之前 **−2.65 / −2.16** → 之后 **−1.11 / −0.82**（过冲因形变而变大）；
- 旋律抬 21.6 dB 之后 **−1.14 / −0.91**，而**内存峰值几乎没动**（−2.03 → −2.05）——
  响度环钉着 RMS、限幅器接住峰值，**「把某个元素推响」买到的是过冲，不是电平**。

上限 **−0.50 是留给过冲的**，不是围着那个够不到的天花板画的（围着画只是在量更早的一版混音）。
**ogg 只剩 0.41 dB 余量** —— 顶层一改形状就该重读这个数，而不是等它红。

## 320. `--reuse` 会把**旧旋律**原样送出去 —— 缓存里装的是旧代码的产物（Phase 93）

旋律电平住在 `render_stems()` 的核心 stems 里，而 `--reuse` 就是"从缓存装配"。
所以改完 `LEAD_DRY/LEAD_SEND` 之后跑 `--reuse`，会**用新代码把旧旋律原样编码**，
而且**全程无警告** —— §0.15 换了张脸。
**这一轮没用 `--reuse`**，跑的是完整渲染。

反面的对照：`load_stems()` 里 `airC`/`airD` **每次都按当前常量重建**，
所以缓存**钉不住**闸的深度 —— **同一个缓存，一处钉得住、一处钉不住，差别只在有没有人在重建它**。

## 321. 一个「写上去、从没调过」的电平，就是问题本身（Phase 93）

旋律的 0.085 / 0.16 是**写上去的**，不是量出来的：**湿占优 1.88 倍**、在自己那条临界带里
**−11.8 dB**（掩蔽阈之下）、**sparse（只占 22% 的时间）**。
四个数里没有一个是当初决定它时看过的 —— 而操作员**一听就听出来了**。

这条和 §0.18 是同一条，只是尺子换成了耳朵：**错的量法不报错，它只安静地给你一个数**；
**而没量过的旋钮，连错的数都没有。**

补上测量之后，杠杆的位置还和直觉相反：**send 几乎不是杠杆**（×1 → ×5 只换 1 dB，且
5 倍 send **不会**把整首弄湿，s/mid 恒 0.115 —— 这是我的一个**错假设**），
**干湿比才是** —— 顺带把原来湿占优的旋律改成干占优（0.39），这也是咬字要的。

## 322. 一个元素**各自都对**，和**它们之间**对，是两个问题（Phase 94）

用户用眼睛报出来的那个错（片尾 170px 的 `THE REACTOR GAME` 把三条规格和片尾句全盖住），
**两个 harness 当时都是绿的**，而且两边绿的理由不一样：

- **桩 DOM** 结构上就没有布局（307），**没有排版可错**；
- **布局 harness** 量的是 `m.title.w > 200 && m.title.h > 20` ——
  那条 1920×170 的带子**完美通过**。

**这是 §0.2 换了第八张脸。** 第七张是"读实例状态 ≠ 读屏幕"，
这一张是"**每个元素各自都对，而它们互相盖住**"—— 一条**只问单个元素**的断言，
无论多精确，**永远问不到两个元素之间**。"这个块排出来了吗"和"这个块压住了谁"
是**两个**问题，需要**两把**尺子。L5 因此不是 L4 的加强版，是一个新维度：
**同屏两两相交面积**。

## 323. 数**同屏**，不要数**相撞** —— 空集课的第三次（Phase 94）

L5 第一版把"这条断言有没有力"判成 `Σ r.pairs > 0`，而 `pairs` 数的是**相交对** ——
干净片子上恒为 0，于是**断言自己把自己判死**，报出
`NEVER TWO THINGS ON SCREEN AT ONCE -- this test has no force`。

**"没有两个东西撞上"在一张"自始至终只出现过一个东西"的扫描上是免费的。**
所以力必须量**同屏数**（`n >= 2`），不是**相撞数**。这和 §0.6 的空集课、
302 的"把没有的也写下来"是同一条：**报出"干净"之前，先证明场上曾经有过东西。**

## 324. 有效不透明度是**乘**出来的；量字形盒，不量边框盒（Phase 94）

L5 有两处错了会让它变成噪音，都很好犯：

**① 只读元素自己的 `opacity`。** 三张规格卡是**整组**淡入的（父元素 `#specCard`
带 opacity），子元素 `.spec` 自己的 `opacity` 一直是 1 —— 只读它自己，
会把**还没入场的卡当成在场**，然后报一堆假交叠。**有效不透明度 = 自己的 × 每一层祖先的。**

**② 量 `getBoundingClientRect()` 的边框盒。** `#title` 是 `left:0;right:0`，
它的边框盒**就是整个 1920**；直接量会把"横铺满"读成"和所有东西都相交"，
于是它**永远**红、也就**永远**没有信息（和 308 同族：问错了面）。
要用 `document.createRange()` + `selectNodeContents()` 拿**那块字的墨**。

## 325. 「裁掉」有两种：**有记号**的和**没记号**的 —— 而只有后者是缺陷（Phase 94）

顺着"字被挡住"这条线头，摸出第二类：诊断面板里两条开机记录比面板宽，
`#scroll` 一裁就**断在词中间**（最长那条墨到 1671，面板右边缘 1225，**吃掉 446 px**）。
**它落在所有已有检查的缝里**：行在屏上（L1 绿）、光标在窗内（L2 绿）、
最新一行贴底（L3 绿）、`opacity` 是 1 —— **每一句都是真的，而 446px 的字不在那儿。**

关键是把性质说对。**它不是"不许裁"** —— 终端面板在边缘裁掉一条长行是**对的**。
它是"**裁了要有个记号**"。所以 L6 断言的是
`text-overflow === 'ellipsis'`，不是 `ink <= pane`。

**这条区别用一条 FOLLOW 钉住**：`diag-bigger-type`（字号 19 → 21）会**裁得更多**，
**必须保持绿**。它红了，就说明 L6 漏进了"字号多大"这个口味问题里。

## 326. 修一个**缺陷**和换一个**效果**是两件事（Phase 94）

那条 446px 的裁切有三个候选修法，只有一个是"修"：

| 修法 | 后果 |
|---|---|
| `overflow:hidden;text-overflow:ellipsis` | **行高不变**、滚动算式不动、外观只多一个 `…` —— **修了缺陷** |
| `white-space:normal`（换行） | 行高**随时**变高，`shown*rowH` 的滚动算式必须改成逐行累加；`diag-rowsize` 那条 FOLLOW 直接失效 |
| 字号 19 → 13 | 最长那条也塞得下，但面板从"滚动的终端"（23 行）变成"一张静态列表"（35 行装下 45 行里的大半）—— **那是换了个效果，不是修了个缺陷** |

**判据是"交付物还认不认得出来"。** 换行和缩字号都能让检查变绿，
但它们改的是片子的**样子**；`…` 改的是片子的**诚实度**。

## 327. 不采用生成模型：**第一条理由是我听不见**，不是硬件（Phase 95）

用户问「能不能找点 github 上面的做音乐的那种」。开源那边**确实有**（YuE / ACE-Step /
SongGeneration / SongGen / InspireMusic 都在发权重，music21 是乐理库不是生成器），
本机也确实**没有可用 GPU**、**C: 只剩 2.3 GB**。**但决定性的不是这些。**

**决定性的第一条是「我听不见」。** 生成器吐回一个文件，而**没有耳朵的那个是我** ——
循环就变成「渲 6 分钟 → 交给操作员的耳朵 → 他再写一句」。这个代价**不是假设的**：
Phase 93 那两轮，**我全部检查器全绿**，而他连续两次说「很难听清旋律」。
换个工具只会把「我判断不了」这件事从一次变成每一次。

**第二条是规格的形状**：`make_song.TARGET` 里每个数都是对参考曲的**测量**
（八度轮廓、10 s 块的频段占比、p5/p95、side/mid、corr）。**生成器没有那个旋钮** ——
它不给你「把 2–8 kHz 地板压 2.6 dB、别动峰值」这种接口。**能对齐规格的是代码，不是采样。**

**第三条才是硬件。** 顺带纠正一条**我自己曾经相信过的事**：
**「PyTorch 没有 Python 3.14 的轮子」是错的** ——
`pip install --dry-run --no-deps --only-binary=:all: torch` 回 **Would install torch-2.14.1**，
PyPI 上确实有 **cp314 win_amd64**（0.12 GB）。以后不要再拿「没轮子」当理由。

## 328. 一个「余量」必须对着**没有被测对象**的底量（Phase 95）

旧的旋律余量尺子算的是 `mix − lead_isolated`。而新编曲**已经把 lead 混进 `mix` 了** ——
于是减掉的**不是伴奏，是同一段旋律的第二份拷贝**。`assemble()` 对各级电平是**线性**的，
所以正确的底是 `with_lead(stems, 0, 0)`：**它定义上就不含旋律。**

**「余量」这个词本身就替你做了一半的选择**（同 §0.18 第五张脸：一个词如果替你做了选择，
你读到的就不是测量）。`.18` 那个词是「最外围」，这个词是「伴奏」——
**在一个已经含有被测对象的混合里，「其余的一切」不是一个可以减出来的集合。**

## 329. 两个**分别**量的带功率的和 ≠ **和的**带功率（Phase 95）

干声和湿声在**音符自己那条带里是相关的**，所以 `bp(dry) + bp(wet)` 与 `bp(dry+wet)`
在这里差 **约 3 dB**。这不是浮点误差，是**量的东西不一样**。

**规矩：要量一个信号的功率，就把那个信号先加起来再量。**
先把两半各自量完再相加，**只有在两半不相关时**才等于前者 ——
而「两半不相关」正好是**你不知道、也不该假设**的那件事。

## 330. 外推不是测量 —— 它**算过**、给了**表**、还错了 **11.4 dB**（Phase 95）

上一轮我给出的「旋律余量 **+6.9 dB**」是 `dry² · pd` 推出来的。
这一轮对着真正无旋律的底重测，**同一个旧动机、同一个电平**：**−4.5 dB**。

**11.4 dB 的误差，而它当时长得完全可信**：有一条从 1× 到 8× 的扫表、
读数单调、还落在「+6 dB 以上」这一侧。**它是 321（「写上去、从没量过」）的第二次换脸：
这一次它算过、算得很像样、还给了张漂亮的表。**

代价要说清楚：**旋律从头到尾就一直在它自己那条临界带里低于伴奏 3–4.5 dB**，
而上一轮那句「把旋律抬上去」**从来没有清掉它自己的判据**。
**外推的结论必须标成外推**，否则它和测量在盘上逐字同形，只在**下一次被质疑**时分开。

## 331. 电平不能住在缓存里（Phase 95）

原来的 `render_stems` 把 lead **按当时的 `LEAD_DRY` 混进缓存的 `mono/send`**。
改了电平再跑 `--reuse`，**渲染成功、母带成功、检查全绿、回放正常**，
而送出去的是**旧电平** —— §0.15 那一族，**这一张脸特别难认**，因为它什么都不报错。

改法：缓存里存**单位电平**的 `leadD`/`leadS`，电平由 `with_lead()` 在**装配时**施加一次。
收益立刻可见：**扫一遍电平从「六分钟一渲」变成「一个装配点一次」** ——
**这才是「量一个电平」和「猜一个电平」之间那条线。**

两条随附纪律：`with_lead()` **必须幂等**（返回的表里 lead 已清空），否则**每个手工备 stems
的调用方都会静默拿到双倍旋律**；`load_stems()` 对没有 `leadD` 的旧缓存**直接报错说清楚怎么修**,
不让它变成 `assemble` 深处一个看不懂的 `KeyError` —— 更要紧的是**不让它被容忍过去，
产出一首渲染、母带、回放全都完美、就是没有旋律的曲子**。

## 332. 「高潮」在**能测的那一半里**是**余量**和**份**，不是整体响度（Phase 95）

母带把整体响度钉死在 −15.10 dBFS（那正是它该做的），所以**在 RMS 上找高潮永远找不到** ——
`range` p95−p5 这一轮是 **14.51 → 14.31 dB，还窄了 0.2 dB**。

它在两个地方看得见：

- **旋律相对伴奏的余量**：climax 段 **+12.8 dB**（窄带），groove **+6.4**；
  主题 `b`（上行句）**+12.2** 对主题 `a` **+6.1**。
- **它在整块能量里的份**：10 s 块的中频占比 **130-140 s 14% → 140-150 s 55% → 150-160 s 23%**
  （bar 52 = 140.4 s）。**旧曲这一列是平的**（全程 3–21%，没有一块站得出来）。

**但这一条只能走到这里。** 它证明「这一段和别段不一样，而且是旋律站出来的那种不一样」，
**证明不了「这是一段曲子」。** 判据是挑的（+6 dB），**不是测量的**；耳朵是操作员的。

## 333. 一个「发展」是可以在代码里被**否掉**的性质（Phase 95）

「全曲一个旋律在放」这句话，在源码里就是一行：

```lua
if bar % 2 == 0 then  play(bar, MOTIF, ...) end   -- 97 小节，同一个模子
```

**而它旁边所有的数都是绿的** —— 波段功率、RMS、八度轮廓、纹理、side/mid、corr，
**没有一个在问「这段和上一段是不是同一段」。** 这就是「缺一个检查」和「缺一个维度」
的区别：前者补一条断言就行，后者要求**换一个问题**（同 307/321 那条线）。

修法也是结构性的，不是调参：`lead_plan()` 把旋律**当成一张表**返回
（`(bar, beat, note, dur, tag)`），**渲染器和尺子读同一张表** ——
尺子因此不可能量到自己的私有副本。发展本身由三件事构成：
**陈述/应答**（A 的移调）、**上行**（B/B2 顶到 C6）、**反向**（ctr 下行长音）；
外加两段加速过门和一段**刻意不给旋律**的尾段（81–91，29.7 s）。

## 334. 「撤销所有移动」撤的是**改变世界的那一次**，不是「把每一项位移反向」（Phase 96）

用户说的是「撤销所有移动」。**照字面做**（只把**本轮**搬的东西搬回去），世界会**停在坏掉的状态**——
因为坏掉的原因正是那次 park 本身。**要撤的是「让房间变样」的那一次操作。**

而且**复原只能重建，不能 undo**：`ChangeHistoryService` 的 undo 是**盲写**
（Phase 85 已经量过 —— 它**什么都不撤销、也不告诉你改了什么**，取舍 272）。
所以复盘只能靠**测量**：部件总数（**91,905**）、`Workspace.Consoles` 还解析得到、射线。

**规矩：当「撤销」落在一个不可用的 undo 上时，它的正确实现是一次带**不变式**的重建，
而且那个不变式要能独立复算**（数部件、打射线，而不是「看起来回来了」）。

## 335. Roblox 允许**兄弟重名** —— 所以「合并同名的根」既不必要、又不可逆（Phase 96）

Lua 里给 `Parent` 赋值**从不改名**（**只有 Studio 的 UI** 会加后缀）。
这个 place 里因此同时住着 **109 个叫 `Model` 的根**、90 多个裸 `Part`、**45 个空 `Model` 壳**。

**「怕重名，先合并再搬」把一个可逆的搬运变成了一次不可逆的破坏**：合并毁掉的是**分组**，
而分组**没有名字、没有属性、没有绑定** —— 所以事后**没有任何东西**可以拿来复原它（取舍 340）。

**规矩：`Parent` 赋值不需要唯一名；需要唯一名的只有你自己的查找代码。
要搬就整根搬，永远不要为了搬运去改世界的形状。**

## 336. 空掉一个 `Model` 之后，`GetPivot()` 还在（Phase 96）

45 个被合并清空的 `Model` 壳，`GetPivot()` **仍然返回原来的世界坐标**：

```
(244.38,278.24,6.54)   (241.72,289.64,-4.99)  (256.32,278.24,6.54)  (250.35,278.24,6.54)
(193.17,278.23,-49.48) (193.18,278.22,-55.45) (244.38,278.24,-7.87) (260.52,276.95,40.61)
… 44 个落在控制室/走廊 x131..261 y276..305 z-58..55
(-0.29,-965.13,-288.67)   ← 唯一一个 pivot 从来没设过的
```

两件事同时成立：**这是「合并发生过」的证据**（不然这些壳为什么会在那些位置），
**也是唯一还能指出「丢的是哪一份分组」的东西**。

**但它只是点，不是数据。** 见取舍 **340** —— 拿点去分配零件会给你一个**看起来完全合理**的答案。
**别把「还能读出一个坐标」当成「还能恢复」。**

## 337. 从 y=400 往下打的「地板射线」，打到的是**天花板**（Phase 96）

我为了判断「控制室地板在不在」从 y=400 垂直向下打，读数 `hit=12 miss=18`。
**那个数毫无意义** —— 向下打的第一撞是**天花板**。同一批「天花板探针」从 y=288 向下打，
起点在**天花板之上**，于是也全错。

**一条问错面向的射线会给出一个响亮的、错的数**（§0.18 第五张脸）。
正确做法：**房间水平扫**（720 条 × 三层高度，0 漏才算密封），
**地板从地板往上探**（控制台上方 y280.5 起，20/20 命中 y288–298）。

**规矩：射线回答的是「谁先被撞到」，所以「打哪一条」必须由问题决定，不能由方便决定。**

## 338. 合并过的容器可以**按索引**拆回去 —— 但每一条边界要先证明（Phase 96）

拆法是三条护栏，**任何一条不过就整个 `return`（什么都不动）**：

```lua
if total ~= #kids then return end          -- 各块之和必须正好等于孩子数
if got[1] ~= ownParts then return end      -- 孩子的顺序必须还是追加顺序
if #empties < #blocks - 1 then return end  -- 得有足够的同名空壳接住
```

拆完**必须再量一次**：四个分块的包围盒要**真的是四段相邻的几何**
（x163..178 / 178..193 / 193..208 / 208..223 —— 15 stud 一段、首尾相接），
而不是四个各占一角的杂乱集合。

**「护栏过了」只说明算术对，几何对不对要另外量** —— 否则护栏只是一张
「我没做傻事」的自我声明。

## 339. 会话转录里的计数**不是 ground truth**（Phase 96）

我从会话 JSONL 里 grep 出「合并日志行」想反推每个容器原来有几件，得到 `Model(N)`
十几个档位、相加 ≈ **2,694**；而那个容器实际只有 **1,539** 个部件。
`MainHallwaySegment(456)` 出现 **8** 次，而真实合并是 **3** 次。

两条原因：`uniq -c` 把**每条工具结果算两遍**；**诊断那一趟也打过同样的行**
（我为了看清要合并什么，先跑过一遍只打印不动的）。

**转录是「找」的通道，不是「读」的通道** —— 同取舍 **255**（分组包围盒只能用来找、不能用来读）。
**要数一个东西有几件，就问那个东西，别问日志。**

## 340. 拆不回去的时候，正确的产物是**说清楚丢了什么**，不是**给一个像样的猜测**（Phase 96）

`Model[1]`（476 孩子 / 1,539 部件）拆不回去。我手上**有**一个能让它看起来很体面的办法：
按最近邻 pivot 把 476 个孩子分配给 45 个空壳。它会跑通、会给出 45 个大小合理的容器、
**没有任何东西会报错**。

**我不做，因为那是挑的数不是量出来的数**（同取舍 **274**：量出来的数和挑的数要在代码里长得不一样）。
而且这些 pivot 在控制室里**彼此只隔 2–15 stud**，一个道具的零件跨到邻居 pivot 上是**必然**的 ——
所以它不只是「不确定」，它**大概率是错的**，而错误的方式是**又一次不可逆的搬运**。

**规矩：证据不足时，交付物是「哪一格丢了、为什么补不回来、补它需要什么」，
不是一格替代品。**「我做不到」和「我做了个像的」在这件事上不是同一句话。

## 341. 「加个 GUI 库」被改口两次，最后交付的是**一个文件**（Phase 97）

原始要求里有「加 bootstrape 那个 GUI 库」和「搞成模块化，我可以自己添加新的控件」。
我按字面做了：五个模块、控件注册表、规格校验器、一套「拒绝坏规格」的测试。
操作员看了以后说「**停止，别搞这么复杂，就 tkinter 好了**」，整批删掉。

**这不是「少做了一点」，是做错了一个方向。** 他要的是**能看数、能快速切档**，
而「模块化」在他那句话里是**目的**（「我可以自己添加新的控件」），不是**架构要求**；
我把它读成了后者，于是花在框架上的每一行都在**推迟**他要的那件事。

**规矩：一句话里的名词不都是规格。** 如果「A 并且要 B」里的 B 回答的是
「**那我以后能做什么**」，B 往往可以用**文档里两行做法**满足，不必用一层抽象满足。
（同 §0.18 第五张脸一族：一个词替你做了选择，你读到的就不是需求。）

## 342. `ttk::scale` 没有 `-resolution`：**「间隔 1」是 spinbox 提供的**（Phase 97）

用户要「温度滑动间隔1」。我先把 ttk 的 scale 当成了能干这件事的控件，**两个选项都试过**：
**`ttk::scale` 既没有 `-resolution`**（那是**经典 `tk.Scale`** 的选项）**也没有 `-increment`**。
它的步长是**像素级**的。

**答案不在文档里，在 `ttk/scale.tcl` 里**（Tk 9.0.4，逐字读的）：`<Button-1>` → `Press`，
而 `Press` 对 `*track|*trough` 干的是 **`ttk::Repeatedly Increment $w ±1`**，
`<Button-2/3>` → `Jump`（`$w set [$w get $x $y]`，跳到点击处），
`<B1-Motion>` → `Drag`（绝对跟随）。**所以「点一下 trough = ±1」是 Tk 原生给的**，
用户要的那句在 slider 上**本来就成立** —— 只是**不是**靠一个叫「间隔」的选项成立的。

**于是分工是**：slider 负责「快」（像素级、可达任意位置），
**spinbox 负责「准」**（`-increment=1` + `-format="%.0f"`，能把一个精确数字放在里面）。
**给用户的是两个控件，而不是一个假装两样都行的控件。**

## 343. 取整只贴在**显示**上；模型一位不进（Phase 97）

操作员要求「全部取整数」。**取整写在 `shown()` 里，模型保持完整 float** ——
`Pressure` 还是像 `.luau` 那样累加。

理由是**验证能力**，不是风格：把模型也取整，它就会**慢慢漂离原版**，
而那个偏移**恰好在 `.luau` 对照里看不见** —— 两边每一拍都在各自的舍入误差里，
差的正是同一个量。**一个让「和参考实现对照」这个手段失效的改动，
不能因为它只是「显示一下」就顺手做。**

**并且不能用 Python 的 `round()`**：它是**银行家舍入**（`round(1.5)==2`、`round(2.5)==2`），
而这里的数**真的会落在 .5 上**（slope 项 `0.01 × 整数温度`，State 2 每步 `0.0075 × T`）。
落在 .5 的读数用 `round()` 会**隔一拍才变一次**，读起来像「我输的数被吃了」——
**一个舍入规则能以「像是输入丢失」的形式表现出来。**

**唯一不取整的读数是 tick period**：它是**时长**不是读数，
取整之后 `0.25` 会印成 `0`（一个控件报告一个它没有的值，比一个宽的值更糟）。

## 344. `identify` 返回的名字**带主题前缀**（Phase 97）

`ttk` 的 `identify` 答的是 **`Spinbox.uparrow`**、**`Horizontal.Scale.slider`**，
**不是** `uparrow` / `slider`。Tcl 那边是**用 glob 匹配**的（`switch -glob -- *uparrow`），
所以**问裸名字什么都找不到** —— 而「找不到」在我这一侧读起来正好是
「**这个控件没有箭头**」，于是检查会心安理得地跳过。

**这就是 §0.20 那张脸**：问题问错了名字，答案**不是空的，是错的**。
修法是**问同一个 glob**（`.endswith("uparrow")`）—— 检查器和绑定要**用同一把尺子**。
同一个坑一量两次：`thumb local x range: not found` 是同一件事。

## 345. `event_generate` 只落在**有焦点**的 widget 上，而 `ttk::spinbox::Press` 会替你设焦点（Phase 97）

我给主控件写检查时，`event_generate("<Return>")` **通过了** —— 而那次的通过
**不来自我写的任何一行**：`ttk::spinbox::Press` 的第一句就是 `focus $w`，
所以**前面那次箭头点击顺手把焦点给了这个 box**。**一个意外的前置条件**，
没有任何一行代码或注释说过它。

它被抓住的方式值得记：**是截图和读数互相矛盾**（box 显示 `12345`，读数那栏写着 `5600`）。
**读数自己看不出这件事，因为它每一次都自洽。**

**规矩：用 `event_generate` 就必须显式 `focus_force()`，并且把理由写下来** ——
在这里理由是现成的：**人本来就得先点进那个 box 才能打字**。
再加两个变异（`no-return-bind` / `no-focusout-bind`）把两条绑定证明成**承重的**：
一条绑定如果删掉之后没有任何检查变红，它就**不是功能，是装饰**。

## 346. 读一个 `StringVar` **不是**读那件 widget（Phase 97）

我的检查读的是 `con.temp_box.get()` —— **那个变量的值**。
变异 `box-shares-slider-var`（把 spinbox 的 `textvariable` 换成 slider 的 DoubleVar）
**红了，但红在错的那一项上**：`StringVar` 会**留着模型写进去的字符串**，
**即使 widget 已经不再听这个变量**。

**读变量是在给一个已经断线的显示报平安。** 该问的是 **`widget.get()`**。
这是 §0.2 换的又一张脸：**模块状态 vs 实例状态** —— 在那里我读的是 `require` 出来的
空表，在这里我读的是一个**没人显示的字符串**。**两边的错法一样：
读到了「本该是那个值的东西」，而不是「屏幕上那个值」。**

## 347. 注释里的数字会**跟着它旁边的布局陈旧**，而且不会报错（Phase 97）

`gui.py` 里有一句注释：「one pixel of these **~293** is about **137** degrees」。
实测这个 widget 是 **300×26** → `40000/300 = **133.3**`。两个数**当时是对的**：
slider 旁边原来有一个多余的 `temp_value` 标签，拿掉之后 slider 宽了 7 px。

**关键不是「我算错了」，是「这两个数是读数，而它们被写成了常量」。**
一个读数的有效期**绑在它当初被量的那个状态上**，而这里改变状态的
是**同一个函数里的另一行**。**改注释的人不会知道它已经过期，
因为没有东西会因此报错**（§0.18 同族）。

修法：**把算式写出来，把读数标成读数** —— 现在是「40000 over a 300-pixel widget」
＋ 一句「这个宽度是布局给的，不是选的」，并把 **293/137 作为「曾经的读数」留下**。
**按取舍 274 的规矩：量出来的数和挑的数要在代码里长得不一样。**

## 348. 验证不许动操作员的**真实光标**（Phase 97）

我用 `SetCursorPos` + `mouse_event` 点过界面。用户原话：**「你别老动我鼠标」** ——
**那动的是他自己的光标**，而他和我共用这一台机器、这一个桌面。

**替换掉的是工具，不是覆盖度**：

- **驱动** → `event_generate` 送给**同一件 widget**，跑**同一批 Tcl 绑定**，
  窗口可以 `-alpha 0.0` 隐身。坐标是 **widget 局部**的 —— **§0.11 那个 58 px 偏移
  在这条路上不存在，因为全程没有产生过一个屏幕坐标。**
- **截图** → `PrintWindow(..., 2)`：**请窗口自己画自己**，被遮住也能拍，
  **不抬窗、不置顶、不碰光标**。

**两条可以推广的：① 一个会夺走操作员输入设备的验证工具，
即使它测得对，也是不可接受的** —— 他把这一点说得比我意识到得早。
**② 「不动用户的东西」和「测得准」不冲突**：`event_generate` 跑的是**真绑定**，
`PrintWindow` 拿的是**真渲染** —— 少了的两样只有「真指针」和「真焦点」，
而这两样恰是**这次检查的噪声来源**（取舍 345 就死在焦点上）。

## 349. 一句话里**没说**的选择，两个都算出来，把选择留着（Phase 98）

用户原话：「相邻两个数据，如果不一样，就算deltapressure/deltatemperature(也就是fluc),
**只算连续升高处**」。

「连续升高」至少有两个读法：**A** 每一步 delta 为正（孤立的一升也算）、
**B** 只算落在**长度 ≥ 2 的连续上升段**里（单独一升不叫「连续」）。
差得不小：dTemp 上 A = **109 步 / +15053**，B = **83 步 / +14225**。

**我没有挑一个当答案，也没有回头问他 —— 两个都算、都写进产物（两列标志位）。**
理由是他**不喜欢被反复问**（§4.1），而这两个读法**都是他那句话的合法读法**，
所以「问他」和「挑一个」都是把我的判断塞进他的测量里。

**和取舍 293（§0.18 第五张脸）是一枚硬币的两面**：那一轮是**一个词替我做了选择**而我没发现，
于是读到的不是测量；这一轮是**我发现了一个词在做选择**，于是把**两条路都留下**。
**能一次算出两种读法、并且让读的人自己选，就不要在一个歧义上停下两次。**

## 350. 文件自带的那一列**不是**它看起来在量的那个量 —— 判据是**符号相反**（Phase 98）

`logs.csv` 有 `Time,Temp,Pres,Fluc` 四列，而用户自己说「deltatemperature（**也就是 fluc**）」
—— 他把 `Fluc` 当成温度差。**它确实是温度差，在 239 / 278 步上逐位相等。**

**不等的那 39 步不是散的，是一整段**（`16:29:28 .. 16:30:08`），
而这一段**正好就是 `Pres` 冻在 `5007` 不动的那一段**。**两个列的符号是反的**：
`sum(Fluc) = +1113`，`sum(dTemp) = -6735`（同 39 步）——
**一个说升温、一个说降温**，所以那个窗口里它们**不在描述同一个量**。
另一个解释（`Fluc` 是**延迟一步**的 `dTemp`）实测 **0 步**符合，**是死的**。

**两条能带走的**：
1. **「这两列应该相等」是这次唯一便宜的判据**，而它红在一个有边界的位置上
   —— **红在哪儿**比**红了多少**信息量更大：边界吻合到一个物理事实（压力冻结），
   就不是随机噪声，是这个文件在告诉我它有两套来源。
2. **机制我没有定，我就说没定。** 采集换了源？监视器那一段的读数与 tick 脱钩？
   我手里没有能分开这两者的证据，所以**只写事实**（同 274/340：没有 ground truth 就交付
   「丢了什么」，不交付替代品）。

**影响是有界的，而且是量出来的**：那 39 步里**只有 1 步是升**（`16:29:28`，`dTemp=+247` vs
`Fluc=265`），其余 38 步都是降、**用户的规则本来就丢**。所以交付的数字对「用哪一列」不敏感。

## 351. 一个**不可能因输入而红**的断言 —— 试过一次没红，然后想清楚为什么（Phase 98）

我给「逐项差之和 = 首尾之差」这条望远镜不变量配的变异是「**删掉一行**」。**它留着绿。**

**那个绿是对的。** 望远镜在**任何**一串相邻差上都**代数地**成立：它约束的是**走法**
（有没有跳过样本、有没有重算），**不是数据**。对它做输入编辑，等于在测一个恒等式。
换成**隔一个样本配对**，立刻红（`-17054 vs -8854`）。

**规矩**：**一个检查挡不住的东西，要说出来它挡不住什么。**
不然下一个人（包括三个月后的我）会把它当成一张关于数据的网 —— 而它只是一张关于构造的网。
**没红过的断言是装饰**（取舍 306）；而**试过一次没红、然后把「为什么它不该红」写下来**，
比直接换一个能红的断言多留下一样东西：**一个已知的边界**。

## 352. 用户的原始数据不进公开仓库，**派生的答案**进 PROGRESS（Phase 98）

`Data/analyze/` 是他自己的分析工作夹（`logs.csv` 444 行、`idkatall.txt` 四个数、
以及分析写回去的两份 CSV）。**它此前没有被 ignore，而 `git add -A` + `push` 在这里是
永久授权、自动跑的** —— 也就是说**第一个人分析完，这个 push 就会把他的捕获公开出去，
而没有任何人选择过要公开它。**

按仓库里已有的三条先例（`Data/auxcollection/`、两份 watcher 的 `inventory.txt`、
他放进来的参考曲 `ReactorStartup.mp3`）处理：**加进 `.gitignore`，
把理由写在 `.gitignore` 里**，而**派生的答案写进 `PROGRESS.md`** —— 于是
「仓库 + 他手上那个文件」**仍然能复现每一个数**（读取器 `_tools/analyze_fluc_steps.py` 是跟踪的）。

**能带走的**：**自动化的写权限 + 一个没被 ignore 的目录 = 一次没人做过的发布决定。**
该问的问题不是「这份数据重要吗」，是「**谁选的**」。

## 353. 公式里的斜杠是**除号**，不是清单 —— 一个符号替我做完了选择（Phase 98.7）

用户原话：「相邻两个数据，如果不一样，就算**deltapressure/deltatemperature**(也就是fluc)」，
我把它读成**两个量**，交付了 `dTemp` 和 `dPres` **两列**。他更正：

> 你没理解我的意思啊 …… 而有 c_n=a_n-a_(n-1)
> 我要拉表格的内容就是 样板平均查和 **d=(b_n-b_(n-1))/(c_n)**

**斜杠是除号。整份交付只有一列。**

**为什么这个错读活了下来**：他在第二句里**亲自写了 `(b_n-b_(n-1))/(c_n)`**，
而我把那个括号读成了**排版**、把斜杠读成了**顿号/斜杠列表**。
三件事让错的读法**一路都成立**：那个括号里的分子分母**用到的两列他都有**、
「(也就是fluc)」在**错的读法下也讲得通**、以及「只算连续升高处」在**两种读法下都是个合理的过滤**。
**错的解析不会报错，它只会让整份交付往旁边挪一格**（§0.18 那一族的第五张脸，
但这次的词是**一个符号**）。

**能带走的**：**公式里出现的每一个符号都在做一次选择**，而**选择做完了你读到的就不是测量**。
一个 `(/` 加 `)` 组成的式子，第一件该做的事是**问它算出来是不是一个数**，
而不是问它列的是哪几个东西。

**附带的一半**：`c == 0` 的那一步（`16:30:14`）`d` **留空**。
**「除不了」和「除出来是 0」不是同一件事** —— 前者是一次**没有发生的测量**，
后者是一次测到 0。（同一个理由在 98.2 里让第 1 行留 `/nil/`。）

## 354. 「平均」在数据上**至少有三个合法的读法**，而它们符号都不同（Phase 98.7）

用户要的是「**样板平均**查和 d」。我算出三个，**没有挑**：

| 读法 | A（每一步升，n=109） | B（≥2 上升段内，n=83） |
|---|---|---|
| 逐步比值的算术平均 | **−1.0608** | −0.79845 |
| 中位数 | **+0.014981** | +0.063694 |
| 合并比 `ΣdP/Σc` | **−0.063841** | +0.013989 |

**均值 −1.06 与中位数 +0.015 符号相反**，差得也不是一点点（**71 倍**）。

**这不是噪声，是分母**：`d` 的分母**就是被测对象**，而温度会有一动不动近似一动不动的一步。
109 个上升步里 **14 步 `c ≤ 20`**、**31 步 `|d| > 1`**；
极值 `16:32:51  c = +1  dP = −34  →  d = −34` —— **一步的 c 只有 1**。
**均值被这些点整个拽走，中位数不受影响。**

**所以「平均」这个词不能只交付一个数**：交付一个数就是**替读的人选了读法**。
`d_summary.txt` 给**三组 × 三种 + min/max + p10/p90**，并写明**中位/p10/p90 描述典型的一步**。
（同 349：一句话里**没说**的选择，两个都算出来，把选择留着。
区别是 349 歧义在**分组**，这里的歧义在**统计量**。）

## 355. 我写的变异**断言了一个不存在的数** —— 而它红给我看（Phase 98.7）

98.3 量到：`Fluc` 列在 **39** 步上与重算的 `c` 不同。于是 98.7 我给「用 `Fluc` 当分母」
这个变异写下的断言是**「39 步全变」**。跑出来：**1 步**。

**因为它 38 步的 `dP` 是 0。** 那 39 步**整段就在压力冻在 5007 的那一段里**，
而 `0 / x = 0` 对任何分母成立 —— **分母是多少都不重要**。
唯一会动的是 `n = 78`（`16:29:28`，`+238/+247` vs `+238/+265`），
`d` 从 **0.963562753** 变 **0.898113208**，**差 −0.0654495**。

**两条**：
1. **一个变异没红，先查变异自己的断言，别先改被测代码。** 这里错的是**前提**
   （「那 39 步在算 `d`」），不是 `d` 的算法。**和 351 是同一族的反面**：
   351 是**断言太笼统所以永远不会红**，这里是**断言太具体所以红在错的地方**。
2. **改完之后，把「为什么只动一步」单独立成一条判据**（`38 of the 39 have dP == 0`）。
   **错的那一版留给我的东西，不是「改成 1」，是那个 38** ——
   它是理由，写在断言旁边才不会在下一次被重新猜一遍。

## 356. 他替自己做了选择 —— 而那个选择**翻了符号**（Phase 98.8）

98.7 我把「连续升高」的两个读法（A = 每一步升 / B = 落在 ≥2 上升段里）都算了出来、
**故意不选**（取舍 **354**：交付一个数就是替读的人选了读法）。他回了一句
「**只算连续升高处**」，选的是 **B**。

**留着不选是对的**（选择是他的）。**而选完之后的后果我原来没提前说**：

> A 比 B 多的那 **26** 步，`Σc = +828` 而 `ΣdP = −1160` —— **温度上浅、压力上陡**。
> 于是合并比 `ΣdP/Σc` 从 **B 的 +0.013989455** 变成 **A 的 −0.063841095**。

**符号相反。** 也就是说「平均压力每升一度变多少」这个问题的**答案的正负**，
是由「孤立的一升算不算」这一句决定的。逐步比值的均值也动了 33%
（−1.0608425 → −0.79845432，**同号**）。

**能带走的**：把选择留着的时候（349/354），**要把「选哪一个会改变什么」一并留着** ——
不是「A 和 B 差不多」这种安抚，而是**差在哪、差多少、有没有翻号**。
否则「两个都给你」读起来像「随便哪个都行」。

## 357. 一个词指定了**在哪一列上判连续** —— 而我没假设，我量了（Phase 98.8）

「连续升温」的段判据要加在**某一列**的增量上。三个候选都真实存在，
而且**各给一个不同的集合**：

| 段判据加在 | 步数 | 段数 |
|---|---|---|
| `c` = 温度差（重算的，选定） | **83** | 11 |
| `dP` = 压力差 | 81 | 5 |
| `fluc` = 文件自带的第三列 | 98 | 13 |

我锚的是 `c`（温度），理由是这句话说的是**升温**、而 `c` 就是温度那一步的增量。
**但这条理由本身不是测量** —— 测量是**另外两条也跑了**：
正因为三个数不同，`83` 才不只是「某个段判据的输出」。

**和 98.3 是同一族的正面版**：那里文件自带的第三列**在 39 步上不是温度差**（机制未定，取舍 355）；
这里那一列**改变的是答案的规模**（83 → 98）。**同一份文件里三个「温度增量」候选给出三个不同的世界** ——
所以「用哪一列」必须**每一处都点名**，不能靠上下文。


## 358. 一个异常「不复现」，也是一条读数 —— 它把异常的归属从工具挪到了一趟窗口（Phase 98.9）

`logs.csv` 里文件自带的 `Fluc` 列**在 39 步上与重算的 `c` 不一致**（239/278 相符，
取舍 355）。`logs.txt` 里同一个位置（同样四列、同样带标签的行）**52/52 全相符**。

**「那个采集器写的第三列坏了」是一个我差点默认下来的结论**，而它被第二份文件否掉：
偏差**属于那一趟窗口**，不属于写文件的那段代码。
而这两份文件出自**同一个记录器** —— 一份的表现证明不了另一份，各自都得量。

**能带走的**：把「坏」写成**一个实测的偏差窗口**（39 步、边界是 `Pres` 冻在 5007 那一刻），
而不是写成**那个东西坏了**。前者的范围有限、可以被第二趟推翻；后者一旦写下来就到处适用，
而且**无从反驳**。同 §0.22 的「证据不足时交付『丢了什么』，不交付替代品」。

## 359. 检查器看的是一个**命名空间**，而缺陷住在一个**栈帧**里 —— 而交付物是写出来的那个文件（Phase 98.9）

`main()` 里一句 `header, body, fmt = load(src)` 把模块级的 `fmt(v)`（数字格式化函数）
在**那个函数帧里**遮成了字符串。`row_of()` 里的 `fmt(...)` 于是变成 `"csv"(90)`
→ `TypeError: 'str' object is not callable`。分析器**打开 `steps_all.csv`、写了表头、
在第一行上死掉**，留下 **69 字节的空壳**。

**三条都绿着**：

1. 控制台报表**照打** —— 崩在写文件那一段，报表早就打完了；
2. 检查器当时 **46 条全绿** —— 它跑的是 `A.load / A.build_rows / A.runs`，**读的那一半**；
3. 检查器里**本来就有一条** `A.fmt(-0.0) == "0"`，**一直绿**。

**第 3 条是这里唯一值钱的那句。** 模块级单元测试看不见函数内的重绑定：
`A.fmt` 在模块命名空间里**完好无损**，被遮的是 `main()` 的**局部**。
「有断言覆盖 `fmt`」和「`fmt` 没被遮」是**两件事**。

**修法不是再加一条单元测试，是把程序跑起来、读它写出来的东西**：
新增 `writer_claims()`，真的调 `A.main()`（重定向 stdout、驱动 `sys.argv`），
写进临时目录，然后**数行数**（`steps_all` 279/53、`rise_steps` 134/52、`d_summary` 非空、
第 1 行没有 `c` 也没有 `d`）。外加一个**逐字复现**那个 bug 的变异（`A.fmt = "csv"`
→ 断言抛 `TypeError` 且留下 0 行的壳）—— 没有它，这个新块也可能只是装饰。

**没被这条救回来的那次**：`| head` / `| tail` 把 traceback 截掉了，而管道后面的 `rc=$?`
报的是**分页器**的状态。同 §0.6：**崩溃与全过在 shell 眼里同形**，而崩溃更可能发生在错的那一次。

## 360. 分派必须分在一个**能分辨**的事实上（Phase 98.9）

新的 `main()` 用 `if header == A.SOURCE_COLS:` 在两种捕获之间分派。
**恒真**：`.txt` 的列名是**造出来的**，而它和 `.csv` 写在表头里的**正好是同样那四个**
（`Time / Temp / Pres / Fluc`）。于是 CSV 捕获被送进 txt 的断言，
死在它**合法**的那一个 `c == 0` 步上。

**「列名相同」不是「两种文件一样」的证据，是「我选的这个判据没有区分力」的证据**（§0.20 同族：
先问数的是谁）。真正不同的事实是**文件有没有在表头行上花掉一行** ——
那件事 `load()` **本来就已经知道**（它按结构嗅探），只是没往外说。

**修法**：让 `load()` 返回**它自己嗅到的格式**（`(header, body, kind)`、`kind ∈ {"txt","csv"}`），
分派走 `kind`。**判据本身也进了检查**（`dispatch_claims()`）：
两文件的列名**相同** + 格式**不同** + 一条**按构造留绿**的 FOLLOW
（`mut dispatch on header -> 两者同一个分支`）——
把「这个判据没有区分力」从一句注释变成**一条永远绿的断言**。

## 361. 一个守卫**跳过**的时候，和它**通过**的时候长得一模一样（Phase 98.9）

新写的分派守卫是 `if SRC in (LOGS_CSV, LOGS_TXT):` —— `SRC` 是 `sys.argv[1]` 的**原样字符串**，
两个常量是**绝对路径字面量**。于是：

| 调用拼法 | 分派块 | RESULT |
|---|---|---|
| 绝对路径 | 跑 | **55 ok / 0 FAILED** |
| `Data/analyze/logs.csv` | **不跑** | **52 ok / 0 FAILED** |

**两个都 rc = 0、都写 `0 FAILED`。** 少掉的三条**不在 `failed` 里，在 `passed` 里** ——
一个只在总数上少 3 的缺口，缩在 52 行输出后面**没有任何东西会指出来**。
而相对路径不是边缘写法，是**命令行上最常打的那一种**。

**这是同一轮里第三次同病**（98.9.7(a) 的 `header == SOURCE_COLS` 恒真、这里的
`SRC in (…)` 恒假）：**判据没有问过自己「这两种输入我能不能分开」**。
`in` 表达式**长得像断言**，读起来不会让人想到它同时是个分支 —— 而它
**既没有 `else`、也不打印**。「跳过」于是和「通过」**在输出里同形**（§0.6 的族谱）。

**修法**：`same_path()`（`normcase(abspath())` 比较）+ `is_capture()`。修完两种拼法都是 **55 / 47**。
**能带走的**：任何**决定「要不要检查」**的条件，都要保证**它自己那句不许悄悄为假** ——
真值可疑就**报出来**，不要 `if`。**一个把断言关掉的守卫，比没有那条断言更糟**：
没有它你知道自己没有；有关掉它的开关，你以为你有。

## 362. 窄温区里最小二乘给的两个系数**各自都不可信**，可信的是那条线（Phase 98.10）

把 `dP = a + b·T` 拟到一条窄带上（温度跨度 ~4000 F），得到

| 带 | a | b | R² | 模型 g | 模型 s |
|---|---|---|---|---|---|
| I | 118.538（**+7.8%**） | 0.008552（**−14.5%**） | **0.9976** | 110 | 0.01 |
| II | 358.248（+2.3%） | 0.006423（−14.4%） | 0.9984 | 350 | 0.0075 |
| III | 791.458（−1.1%） | 0.005365（+7.3%） | 0.9974 | 800 | 0.005 |

**两个系数各自错 8–15%，而那条线在整段上只差 3–5%** —— 因为因变量被量化到整数
（band I 是一条 **+2 的晶格**），而自变量只跨了它三分之一个带，
a 与 b **强共线** —— 一个向上走多少，另一个就向下走多少，而和变化不到。

**能带走的**：**拿一条窄带拟合出来的斜率和截距去反推游戏常数，会得到两个各自错、合起来对的数**。
反向也不通：跨带合起来拟合，会被**边界跳变**主导 —— 全部 52 步合起来 R² 只有 **0.8560**，
拟出的 b 是 **0.032067**，那是跳变的斜率，不是任何一带的。
**可靠的用法只有一种**：拿公式当假设，然后问它在**整段**上预测得准不准（k），
**不要反过来解它**。同 §0.18：错的量法不报错，它只安静地给你一个 R²=0.9976。

## 363. 一个 tick 周期，两条输入不交集的路线（Phase 98.10）

`logs.txt` 的 tick 周期量了两次，而两次的**输入不交集**：

| 路线 | 输入 | 结果 |
|---|---|---|
| 数步 / 时间 | 91 s ÷ 52 步 | **1.750 s** |
| 数重复行 | 重复率 36/89 = 0.409 → `1/(1−p)` | **1.692 s** |

两条差 **3.3%**，而它们一条用步数、一条用「轮询没看见变化」的比例，
**不共用任何一个数**。第二条的前提（轮询 ≈ 1 Hz 而 tick 慢于它）另有一条独立支持：
**每步的整数 tick 直方图是 51×1 + 1×2** —— 一个也没有落在 2 以上，
说明没有两个 tick 挤进同一个间隔。而且这一致**同时把公式钉在「per tick」上** ——
如果每一行是一秒而不是一 tick，模型的每-tick 值就不可能同时对上步数和重复率。

**能带走的**：**两个用不同输入的估计互相靠住，才叫证据**；同一个输入的两种算法
只是同一个数写两遍（Phase 68 那个 `rc` 就是这个病）。

## 364. 报「平均」之前先问「里面有没有台阶」（Phase 98.11）

全部 52 步的 dT 均值是 **492.3 F/step** —— 而真实结构是 **224.4 / 509.0 / 973.7** 三档台阶。
那个均值**不落在任何一档上**；它是把三段连起来的那条斜线的斜率，
和取舍 **362** 里「合起来拟合的 b 是跳变的斜率，不是任何一带的」是同一件事换了个量。

三段区间**互不重叠**（295 < 444、581 < 910）—— 这恰恰是「均值有意义」的反面：
要一个均值有意义，相邻档的区间得**重叠**。

**能带走的**：报均值之前先做一次**按公式边界的分段检验**。不是在**事后找到**的拐点上分 ——
那样分出来的段，拐点是找出来的，就不能同时拿它当「分段存在」的证据（同取舍 **274**）。
一个 4 倍的台阶上取平均，得到的数**没有对应的物理量**，而它会安静地印在报表上。

## 365. 抖动的**绝对**大小和**相对**大小说的是两件事（Phase 98.11）

带 I / II / III 的 dT 半幅 **±73 / ±68 / ±68**，相对散布 **±33% / ±13% / ±7%**。
同一个抖动，相对那一栏读出「档位越高越稳」，绝对那一栏读出「三档一样吵」。
**只有绝对那一栏对得上「这是一个与速率无关的固定噪声」** ——
相对那一栏是**除出来的**：分母（速率）涨了 4 倍，抖动没涨，商自然就小了。

**能带走的**：一个量在档位之间差几倍时，**先问它的抖动是乘法的还是加法的**。
乘法的看相对，加法的看绝对；**看错那一栏，会读出一个不存在的质量差异**。
同族 §0.21：那里的分母里坐着被测对象，这里的分母（速率）**就是被测的那件事本身**。

## 366. 一个量在两趟里复现，不推出它的**分界**也复现（Phase 98.12）

同一段速率、两次独立运行：三个离散温升电平的**值**重合
（≈199 / 507 / 965 vs ≈224 / 512 / 974，档内 R² ≤ 0.14），
而**换档点**在 T 上差了 **3212 F**（13763 vs 16975）。

四个候选变量里**没有一个在两趟里都对得上**，而且**对得上的那一个在两趟里不是同一个**：
1→2 只有 `P` 对得上，2→3 只有 `T` 对得上。`φ = T + k·P` 也无解（`k > 14.25` 与 `k ≤ 1.43` 取交为空）。

**能带走的**：「这个量有 N 个电平」和「电平在 X 处切换」是**两条独立的结论** ——
前者只要**值**复现，后者要**边界**复现。把前者卖成后者，就是拿一次捕获的分档当机制。
分档切点还必须从**分布的空隙**里读出来；**拿聚类去切，它会把空隙也切出来，
然后告诉你它找到了三档**（同取舍 **274**：量出来的数和挑的数要在代码里长得不一样）。
同族 §0.18 第五张脸：**一个词（这里是「档位」）如果替你做了选择，你读到的就不是测量。**
Phase 98.12 的现场是：**值全对，边界全错** —— 而边界才是机制所在的那一半。

## 367. `sys.path` 上的**同名影子文件**：真错在**目录**，报错在**调用方**（Phase 98.12）

`C:\...\tmp\` 里有一份旧的 `analyze_fluc_steps.py`（13005 B），挡在 `_tools\` 那份（18433 B）前面 ——
因为它所在的目录被 `insert(0, ...)` **后**插。它返回 2 元组，真品返回 3，
于是 `ValueError: not enough values to unpack (expected 3, got 2)` **指着我自己的解包行**。

**判据**：任何 `insert(0, path)` 之后再 import 共享模块，**先 print `A.__file__`**。
这是 §0.15（插件 VM 里的过期字节码）和取舍 **359/360**（同名的 `fmt` 格式串遮住格式化函数）
的第三张脸：**「我从哪儿 import 的」和「我 import 到了什么」是两件事，而它们只在 `__file__` 上分开。**

**顺带**：那个 `import` **本来就没被用过**。没人用的 import 不只是噪音 ——
**它是一个会挑错的钩子**（它挑的错，报在别处）。

## 368. 两条边界落在两个变量上，不是「找不到变量」，是**两个门的指纹**（Phase 98.13）

我 98.12 的结语是「没有一个变量同时解释两条边界 …… 这让『找对了变量、只是阈值没定』
这条退路也关掉了」。**这句话假设了机制里只有一个门。** 去读原版自己的原型
（`Data/TRGWeb.luau:177..203`）：它的温度一路**就是两个门**，一个开在 `core_temp` 上
（`>29500`）、一个开在 `core_pressure` 上（`>13500`）—— 于是「每条边界只有它自己的变量认得」
**不是死路，正是那个形状本身**。`φ = T + k·P` 的「无解」同理：那是**强行要求一个 φ** 的产物。

**能带走的**：一个否定结论要先问**它否定的那个假设是谁写的**。
「没有单一变量能解释」是一个**关于单一性的**陈述，而单一性往往是我的框架带来的、不是数据带来的
（同 §0.18 第五张脸 —— 这次替你做了选择的那个词是「**一个**」）。

**顺带**：这条更正让「边界不复现」整条**解散**。按每条边界自己的变量比，两趟**都复现**，
1→2 的 P 中心只差 **37 PSI**，而且方向由 `T*² = T_0² + 100·r·(P* − P_0)` 独立解释
（快的跑必须到更高的 T 才撞到同一个压力门）。

## 369. `span/span` 不是斜率；一个比值里的分子可能是纯噪声（Phase 98.13）

`dT 跨度 / P 跨度` 在 tier 2 上两趟都读 **0.01116 / 0.01146**，与 TRGWeb 的 `floor(P/100)` 斜率
`0.01000` 几乎一样 —— **看起来像证据，其实不是**。真拟合出的斜率是 **+0.002177 / −0.002617**，
R² ≤ 0.0550：**没有斜坡，符号都不一致**。分母（P 的跨度）是实的，**分子（dT 的跨度）
绝大部分是那条 ±50 的随机散布**，所以这个比值是**噪声除以跨度**：它随跨度变小而变大，
跟斜率无关。

**判据**：两个量相除之前，先问**分子里有没有一个不受被测效应支配的项**。
这是 §0.21（分母里坐着被测对象）的**镜像** —— 那边分母脏、这边分子脏，**同一张脸的两面**。
**斜率只能来自拟合，不能来自 `max − min`。**

## 370. 被降级成"参考"的文件，可能还是一条**活的依赖** —— 降级来源之前先查谁在复制它（Phase 98.14）

用户说「**trgweb只作为参考**」。我按字面接受，把它当成"陈旧的原型"。
结果去读 remake 的引擎：`src/ReactorBackend/Engine.luau:273` 是
`(math.floor(s.temperature/c.Sim.PressureDivisor) - fans*c.Sim.FanPressure)` ——
**TRGWeb 的 `Math.floor(core_temp/50) - fans*70`，连 50 和 70 都是同一对数字**。
`Config.luau:16` 只搬了两个常数（`State1` 6000→5600、`StallPressure` 2250→2200），
**形状一个字没动**，还在上面加了两个补偿台阶（`State2Pressure` / `State3Pressure`）。

**"参考"是**使用者的**意图，不是文件在图里的**位置**。** 把一个来源降级，只改变了**我打算怎么用它**，
不改变**别人有没有在抄它**。要断言"这只是参考"，得先跑一遍引用 —— 我这一轮没跑，是撞上去才发现的。

**能带走的**：给一份文件贴上"仅供参考"之前，先问**谁在复制它**；
一个被改了两个数、留了全部结构的副本，是最难认的一种依赖 —— 它**看起来**已经被处理过了。

## 371. 一个错的形状加一个补偿项，不是半个对，是**更错**（Phase 98.14）

remake 在 TRGWeb 的 `floor(T/50)` 之上加了 `+200`（`T>17500`）与 `+300`（`T>29500`）。
如果把这两个台阶理解成"补上 TRGWeb 缺掉的那一段斜率"，那它应该**缩小**误差。
实测相反：全步中位 `|dP − pred|` **裸 TRGWeb 46.0 / 64.0 → remake 114.0 / 153.0**，
**每个状态都更差**（状态 2 的比值从 1.067 掉到 **0.751**）。

**为什么**：`floor(T/50)` 的斜率（0.02）**本来就覆盖**温度区间，台阶加的是**同一段斜率第二次**。
补一个错的结构，是在错的那条线上再叠一项，**两处错各自可加**。

**判据**：看到"在旧公式上加一个修正项"，先问**修正项补的是旧公式缺的，还是它多出来的**。
缺的能补，多出来的只会翻倍 —— 而**这两种在代码里长得一模一样**（一行 `if`，一个加法）。
**唯一分得开的是把两个版本各自拿去撞数据**（这一轮：46 → 114）。
## 372. 一张对账表也有盲区 —— 缺的那一行，正好制造出「手册只字未提」（Phase 98.15）

`docs/airemake/INGAME_MANUAL.md` 的 "Reconciliation against the skeleton's Config" 有 12 行。
我上一轮据此说过「手册对高压→温度的耦合只字未提」。**是错的。**

手册第 **41** 条（`[TextLabel]`，全文）：

> Hazardous Chamber Radiation and High Chamber Pressure will both decrease the H.D.E.F's integrity,
> however **High Chamber Pressure will also cause an increase in Temp Fluctuation**.

这就是 `Engine.luau:277`（`if s.pressure > c.Sim.HighPressure then s.temperature += floor(P/100)*scale`）。
**机制在最高权威里逐字成立，而那一行不在对账表里** —— 表列了
#84/#86/#18/#42-75/#137-73/#51/#31-140/#87/#44/#17-47/#27-34，**没有 #41**。

所以「手册没说」这句话，读的是**表的覆盖度**，不是**手册的覆盖度**。同 §0.2：
**没找 ≠ 没有。** 一张自己写的对账表，它的空白处长得和「来源本身是空白」一模一样。

**How to apply:** 任何「来源 X 没说 Y」的结论，都要回到 X 的**全文**去查一次关键词，
不能只读自己摘要出来的那张表。表的空行是**我的**省略，不是 X 的沉默。

## 373. 定性句不能给定量机制背书 —— `verified` 是一个被高估的判决（Phase 98.15）

对账表第 #51 行：手册说「in a higher state **the pressure will increase at a greater rate**」
→ `Sim.State2Pressure=200`/`State3Pressure=300`/`State3Heat=700` → **verified in `Engine:226-227`**。

那句话是**定性**的，而 `g[st] + s[st]·T`（110/350/800 + 0.01/0.0075/0.005）**同样满足它** ——
两个模型都让「更高的状态涨得更快」。所以这条 `verified` 只证明**代码里有这个机制**，
**没有**证明**这些数字**是原版的数字。

数字的独立支持仍然是零：手册**不给数**（#31/140 的 outtake fans 也一样不给），
`Config.luau` 的表头自己写着「Where neither has a value, the number is TRGWeb-derived and
carries no independent support」。

**How to apply:** 把「prose ↔ 代码」的对账拆成两问：**机制在不在**（prose 能判）和
**数字对不对**（prose 判不了，要捕获或第二来源）。混在一格里写 `verified`，
会把前者的成立读成后者的成立。

## 374. 不是「谁旧」，是「哪一款」—— 两个游戏、两个压力模型（Phase 98.15）

五条来源各自成体系，而且**内部自洽**：

| 来源 | 压力步 | stall | 状态边界 | 风扇 |
|---|---|---|---|---|
| 原版捕获（placeId 17596243941） | `g+s·T`（4–10× 最优） | ~2200 | 17500 / 29500 | — |
| 社区 wiki | `110/350/800 + 0.01/0.0075/0.005` | **2200** | **5,600** / 17,500 / 29,500 | **60 PSI/vent** |
| `luau-windows/calculation.luau`（操作员） | 同上，逐字 | 2200 | 5600 / 17500 / 29499 | 60 |
| `docs/airemake/INGAME_MANUAL.md`（最高权威） | 只说「higher state → greater rate」 | **~2300** | **17,000** / ~18000 / ~29000 | 不给数 |
| `Data/TRGWeb.luau`（+ remake `Engine.luau`） | `floor(T/50)` +200/+300 | **2250** | 17500 / 29500 | **70** |

**这不是版本差，是设计差。** AIRemake 把原版的压力模型换成了一套「状态 + 每 tick 常量」，
并把它写进了自己的手册；remake 的引擎是照 AIRemake 的手册写的（`Config.luau` 表头写明了
adjudication 顺序）。

**形状上的证据**（Phase 98.15 新量）：捕获里那个高压耦合是**一次性跳变**（第一道门在
≈11,300 处 `+288.8/+287.6`，第二道门在 29500 处 `+457.3/+461.7`，两趟都是一次性的），
而 remake 写成了**每 tick 的斜坡**（`+200*scale`、`floor(P/100)*scale`）——
这就是 state 2/3 残差最大的原因（每 tick 加一次 vs 只加一次）。

**How to apply:** 撞上「两个都自洽的来源」时，先问**它们是不是在描述同一个东西**；
不是的话，问题就不是「哪个数对」，而是「我在做哪一个」—— 那是操作员的决定（§1.4 第一条）。


## 375. 一个「一次性」在压力侧成立，在温度侧不成立 —— 同一句话的两个半边（Phase 98.16）

Phase 98.15 ④ 我写：两道温度效应（`HighPressure` 与 `State3Heat`）在捕获里是**一次性跳变**，
而我们写成了每 tick 的斜坡，于是把 state 2/3 的残差归因给「每 tick vs 一次」。

Phase 98.16 按 `P` 分层重测（§0.21：不分层的话「T 高 ⇒ 压力高、dT 也大」会把结论造出来）：

| 捕获 | state 1，`P>11300` | state 1，`P<=` | state 2 | state 3 |
|---|---|---|---|---|
| live | n=8，中位 **486**（min 444） | n=21，中位 191 | n=23，中位 516 | n=9，中位 **974** |
| arch | n=1，**573** | n=20，中位 224.5 | n=24，中位 510 | n=9，中位 **985** |

**跨过阈值的每一步都是高的，而且不衰减** —— 两趟捕获一致。所以温度侧是**每 tick**，不是一次性。
压力侧那个 `+288.8/+287.6`、`+457.3/+461.7` 确实是**一次性**的（98.15 量对了），
但同一句话搬到温度侧就是错的，而且错得**没有症状**：两处代码读起来一样，值也都对得上量级。

**How to apply:** 「一次性 vs 每 tick」是对**一个具体量**说的，不是一个可以整段挪用的形容词。
搬之前问：**这一条是在哪个数上量出来的？** 换了一个量就要重新量（§0.18 第五张脸的近亲）。

## 376. 在交付值上改对了公式，指标反而变差 —— 错的形状加补偿项 = 两处错各自可加（Phase 98.16）

把 `floor(T/50)` 换成 `g[st]+s[st]·T+d[PEA]−60·fan` 之后：

| ReferenceTick | 新式，中位绝对误差（live / arch） | 旧式，中位绝对误差 |
|---|---|---|
| **1**（原版 tick） | **11.42 / 14.25** | 107.00 / 136.50 |
| **2.5**（交付值） | 279.27 / 292.43 | **231.60 / 238.80** |

在**交付的那个 tick 长度**上，改对的那一版**更差**。原因是量出来的：两个模型都按 `1/2.5`
缩放，都只发出捕获的约 **40%**（tick 探针：T=10101、原版 dP=204，RT=1 给 211.0、RT=2.5 给 84.4）。
旧式那条线本身是**错形状**（`floor(T/50)`，没有状态台阶），但它的误差**在采样的温度区间里
和 0.4 倍速的亏空方向相反**，两者相消。改对形状 = 把补偿项拆掉一半，剩下的亏空就露出来了。

371 说的是「错的形状 + 补偿项 = 两处错各自可加」；这里是同一个东西第二次现身，
而这次**补的是 tick 缩放**，所以它比公式漂亮得多。

**修正它的是 tick，不是公式**（原版 tick 实测 ≈ **1.70 s**，交付 `2.5` ⇒ 班次长约 **1.47 倍**）。
那是**节奏**常量，§1.4 第一条挡着 ⇒ **只报不改**。

**How to apply:** 交付一个「改对了」的东西之前，**在交付的那组常量上跑一遍**。
只在你调过的那个参数上测赢不叫赢 —— 那可能只是把补偿项拆掉了一半。

## 377. 一个斜率的符号可以整个由两行决定（Phase 98.16）

state 1 的最小二乘残差斜率：live **−0.004175**、arch **+0.005755** —— 符号相反，
而两个文件在 state 1 里**都是平的**。逐行列出（新加的 `residual by T prev` 那行）：

- live：`9667:+60 9934:+60`，然后平在 `+7…+17`（另有 `11012:+220` 一个采样伪影）。
- arch：平在 `+11…+17`，除了 `14600:−127 14770:−231`。

**两趟的斜率都是两个离群点的产物，一个在低 T 端、一个在高 T 端**；去掉各自那一对，
两边都是 ≈ **+11** 的平线。所以「两趟给出相反的斜率」不是模型在动，是**杠杆** ——
端点上的两个点拿走了整条线的斜度。

这也解释了 362（不要反解常数）为什么在这里必须遵守：`StateSlope[2]=0.0075` 与实测
（两趟都 **+0.0010**）差约 13%、`[3]=0.005` 差约 7%，但**线误差 ≤24 PSI（≤5%）和 ≤6 PSI（≤0.6%）**
—— 常数错得多，线错得少。

**How to apply:** 报一个拟合斜率之前，**把逐点残差按自变量排一遍**。
一个 `+0.0058` 可以是一条平线加两个端点，而那两个点不是同一个东西（§0.18 第三张脸）。
**两趟独立捕获符号相反**是最便宜的报警器之一。

## 378. 「一线一致性」是结构性证据，不是数值证据（Phase 98.16）

回放里加了一条断言：**每一步**的引擎 ΔP 是否**恰好**等于
`(g[st]+s[st]·Tprev+d[PEA]−60·fans)/ReferenceTick`（容差 1e-6）。结果 **61/61**（live）、
**52/52**（arch）—— 全中。

它**不是**「模型对了」的证据：那条式子是我自己写进去的，全中是**同义反复**。
它证明的是另一件事，而且是真事：**压力路径上没有第二个写入者** ——
连 `Fail` 把所有 CBL 关掉之后那一拍，ΔP 仍然逐位等于这条线。
CBL 不在压力公式里，这条断言把「读代码读出来的」变成了「量出来的」。

**How to apply:** 一条「我的公式 == 我的输出」的断言**只对结构问题有效**
（有没有别的东西在写、缩放有没有被应用两次）。要拿它当数值证据，就必须让它对
**不是自己产生**的数成立 —— 这里做不到，所以把它的**职能写清楚**，
别让它混进「模型更准了」那一段。

## 379. 指标本身的时长盲区 —— 一个合格的公式检查、一个没用的节奏检查（Phase 98.16）

Part B 拿**一次 `eng:Step(1)`** 对**一步捕获**。前者是**一个真实秒**（Runtime 一秒一步），
后者是**一个原版 tick ≈ 1.70 秒**。两个不同长度的步相减，只有时长相等时才成立 ——
而它只在 `ReferenceTick = 1` 时相等，因为那时引擎每步发的正好是一个公式单位，
捕获每步发的也正好是同一个（211.0 vs 204）。

修正（两边都换成每真实秒）：

| `ReferenceTick` | 逐拍 live / arch | 每真实秒 live / arch |
|---|---|---|
| 1 | **11.42 / 14.25** | 209.80 / 216.92 |
| **1.70** | 187.63 / 197.02 | **6.72 / 8.38** |
| 2.5 | 279.27 / 292.43 | 84.79 / 88.18 |

**排名相反。** 逐拍指标奖励的是「引擎的每拍增量 == 公式单位」这件事，而那件事
**和 `ReferenceTick` 该取多少无关** —— 所以它给出的是 `RT=1`，也就是那个让整局快 1.70 倍的值。

**危险**：在 RT=1.70 上逐拍读 187.63，看起来像「公式差三倍」；照着它反解常数就是 371 的陷阱，
而这次陷阱是**指标自己**造的。**一个对被测参数不敏感的指标，不能拿来选那个参数。**

**How to apply:** 报一个误差中位数之前，先问**两边量的是不是一个东西** ——
这里两边都是「一次压力的变化」，但一个是每 1 秒、一个是每 1.70 秒（§0.21 的镜像：
那里的分母里坐着被测对象，这里的分母里坐着被测的那个 tick）。

## 380. 两条不相交的输入落在同一个数上，才算证据（Phase 98.16）

「原版 tick 多长」有两条互不相交的路：

1. **从捕获自己的行距**（Phase 98.10）：91 s ÷ 52 步 = **1.750**；重复行 36/89 → **1.692**。
   用的是**时间戳**，不碰任何物理量。
2. **从压力误差的最小值**（本轮）：`|ΔP_engine − ΔP_capture/t|` 在 `t = 1.70` 最小。
   用的是**压力**，不碰时间戳。

两条路的输入没有交集，落在同一个数上（1.70 落在 1.692..1.750 区间内）。这才是证据（363）。
**任何单独一条都是估计**：第一条只说明采集的节奏，第二条只说明「用哪个 t 让线最贴」——
两条靠住之后，`ReferenceTick = 1.70` 就不再是一个挑的数。

**How to apply:** 一个能同时被「时间」和「物理量」两条路量出来的常量，就**两条都量一遍**。
它们不相交才有信息量；如果第二条其实是「把第一条代进去」（比如拿 1.70 去归一化再比），
那是**同义反复**，不是交叉验证（95 的现代版）。


## 381. 温度这一路没有权威文件可抄，所以它的判据只能是「两份捕获」—— 而它们自己差 33.5 F（Phase 98.17）

压力那一路有一个你点名的权威（`luau-windows/calculation.luau`）。温度**没有** ——
那个文件**只读** `T`（`g[st]+s[st]*T`），从不写 `T`。所以温度的判据只能是**捕获**，
而两份捕获在**基线**上彼此差 **33.5 F**（live 191 vs arch 224.5，同一标称条件）。

交付的 `195 = 3 * CBLHeat(65)` 落在两者**之间**：比 live 高 4，比 arch 低 29.5。

**这不是「含糊」，这是唯一能落的位置。** 两份地面真值自己就不一致时，交付值要么落在中间，
要么就得选边 —— 而选边需要一条**它们之外的**理由，现在没有。
（旁证：arch 的负偏差是**全带一致**的 —— -29.5 / -23 / -32 —— 不是一格的问题，是它的基础热量偏高。）

**How to apply:** 一个量如果有两个真值源而它们不一致，**把不一致本身当成结论的一部分报出去**，
不要拿一个去盖另一个。「落在中间」和「拍脑袋取中」在盘上同形，分开它们的是**那两个数是量出来的**。

## 382. 同一个方法换一条通道，比「两条不相交的路」弱一档 —— 而且要说清是哪一档（Phase 98.17）

Phase 98.10 那对「互不相交」是：**时间戳**（不碰物理量）× **压力误差**（不碰时间戳）——
**输入不相交，方法也不相交**。这才是 380 要的那种证据。

这一轮「时长盲区」在**温度**通道上复现，最小值同样落在 **1.70**（19.41 / 20.59，
交付的 2.5 是 90.24 / 95.64）。**但它是同一个估计量、只换了一条被测量的通道** ——
输入不相交（压力 vs 温度），方法相同。

**它加固了 1.70，但没有把 1.70 变成一条新证据。** 两种说法都能写得很像，
分开它们的是：**问「这个数是怎么进到比较里去的」** —— 如果第二次只是把第一次的量换成另一个物理量、
公式一个字没动，那它是一次**复制**，不是一次**交叉**。

**How to apply:** 报「独立验证」之前，先分开说两件事：**输入**相不相交、**方法**相不相交。
两个都不相交才是 380 那一档；只有一个，就说「加固」不说「独立」。

## 383. 「没有斜坡」是被量出来的，不是被假设的（Phase 98.17）

越压门以上分了**四个压力箱**，横跨 `11300 -> 20000+`。`floor(P/100)` 若还在，
这四个箱子会给出一个**单调 +100 的斜坡**。实测 live **486 / 513.5 / 506 / 537**（跨 51 F，**非单调**）、
arch **548.5 / 506 / 503 / 498**（**下降**）。

**一个平坦的读数只否掉「斜坡」，它自己不会说出为什么是平的** —— 所以这里能说的是
「原版的高压耦合是某个平铺项」，不是「原版的高压耦合长什么样」。
这独立确认了 Phase 98.16 ③ 在压力侧得到的同一条判决。

**How to apply:** 断言「A 不在里面」时，**要有 A 若在里面会给出的形状**，并且量到那个形状没出现。
「我分箱看了一眼，挺平的」不是同一条话 —— 它没说你预期的不平是什么样。

## 384. 出口比交付宽，而机制没定就写没定（Phase 98.17）

捕获每一格 `dT` 的跨度：**六格里五格在 125-147 F**（146/147/125 live，146/137/137 arch）。
交付的 `random(-50, 49)` **最多造 100**，而 n=6..31 的 min/max **只会低估**真实跨度 ——
所以交付的抖动**一定**更窄。

**而且宽度在每个区制里一样** -> 这是**步级抖动**，不是缺一项物理项
（缺物理项会随区制改宽度）。这一条是有区分力的，值得单独写下来。

**机制有两种候选，都符合数据**：原版 random 比 +-50 宽；或捕获的步长本身在抖
（Phase 98.9 / 98.12 都量到过 Temp 与 Pres 写在**不同拍**上的采样伪影）。
**我不挑。** 残差中位 live 33/33/45、arch 46/31/35 对 `+-50/1.70 ~ 29` 的地板；
p90 79-99 对 +-50 只能解释的 ~45 —— **多出来的那 30-50 归因不了。**

**How to apply:** 「宽度在每一格里都一样」比「宽度比预期大」信息量大得多 ——
前者区分「少一项物理」和「多一份噪声」，后者两个都兼容。

## 385. 错的注释不报错，它只安静地教下一个读者一个不存在的模型（Phase 98.17）

我 98.16 在温度块上写了「Every gate below reads the value the step STARTED with」。
**三道门里有一道读的是更新后的压力。** 代码是对的（那道门一直在这么做），
**注释是错的**，而错注释的代价推迟到「有人照着它改代码」的那一刻才收。

改法：把三道的读法**分别写明**，并在 stall 行上面写清它读的是 post-step 压力、以及它为什么被留着
（`P12`）。**改前的 13 检查 / 1 失败与改后的 13 检查 / 1 失败一致，Part B 两张表逐位不变** ——
**改注释不许动一个数**，这是唯一能证明「我只改了注释」的那次测量。

**How to apply:** 注释里凡是出现「**每一道 / 全都 / 一律**」这类全称词，就去把每一个数一遍。
全称句的错法是**漏掉例外**，而漏掉的那个例外通常正是下一轮要踩的。

## 386. 「遗留」和「我造的」在代码里长得一样，只有 diff 分得开（Phase 98.17）

那道 stall/越压的读法不对称**是我自己造的**：`git show 3f1712e` 显示改之前
**两道温度门都读更新后压力**，我只把越压门挪到了入口。

只看当前源码，「一道门和别人不一样」读起来像**历史遗留**（原版可能就这样）；
只有把改动 diff 出来，才知道**它是我这次改动造出来的新不对称**。
两者对操作员的含义完全不同：遗留可以不动，**新造的是我欠一个交代的**。

**How to apply:** 发现自己写的代码有个「怪地方」时，先 `git log -S` / `git show` 定位它是谁引入的，
再决定它是「不动」还是「要交代」。**凭源码猜来源 = 在自家院子里认不出自己的脚印。**
## 387. 规格里的三条，要把「哪条归谁」说在前面（Phase 98.18）

操作员给的是三条规格，但它们落在**三条不同的通道**上：两条是**温度**的耦合（捕获量得到），
一条是**显示**的规则（捕获里没有这一路）。**开门第一句就要把这件事说完** ——
否则「三条里我否掉两条」听起来像「我否掉了他三分之二的规格」，而实际上
被否掉的两条**是同一条通道**上的，剩下那条**根本不是同一个问题**。

**How to apply:** 拿到一串规格时，先按「**裁决它需要哪个通道**」分组，再按组报。
一组一条结论，别把不同通道的条目混在一个「对了 1 条错了 2 条」里数 ——
那个分数是**编出来的**，因为分母上的三条不是同一类东西。

## 388. 一条规则打 0 错，只有在别的规则打非 0 时才是一句证据（Phase 98.18）

`big iff T>=29500`（入口）在两趟上分别错 **0/61** 和 **0/52**。
单看它是**一个从未红过的断言**（取舍 306 那一族），因为「全对」和「这个规则没有区分力」
在输出里长得一样 —— 一个把每一行都判成同一档的规则，在只有一档的数据上也会显得全对。

**它之所以算数，是因为旁边那三条打的是 2/61、4/52、1/61、3/52、1/61、1/52。**
区分力不是被假设的，是被**同一张表上的竞争者**逼出来的。

**How to apply:** 报「全对」的时候，**必须把输掉的那几条一起报**。单独一句
「我的规则 0 错」在两个方向上都是空话：可能是它对，也可能是这个测试问不出差别。

## 389. 括号不相交，比「括号差多少」强得多（Phase 98.18）

第二道门如果是压力门，两趟给出的括号是 live `(24644, 25188]` 与 arch `(23470, 24016]` ——
**不相交**，所以**一个 P 阈值解释不了两趟**。如果是温度门，括号是 `(28987, 29568]` 与
`(29368, 29888]` —— **相交，而且 29500 落在交集里**。

差异的**大小**只说明「哪一个更离谱」；**相交与否**说明「存不存在一个能同时成立的数」。
后者是**结构**，前者是**程度**。一个差 3212 F 的括号如果还相交，它就还活着。

**How to apply:** 拿多个数据集去夹一个阈值时，问的第一件事是**交集空不空**。
空 = 那条假设死了，不用再看数；不空 = 才算到「谁在交集中间」那一步。

## 390. 最锋利的那条证据，是离阈值只差 114 PSI 的那一行（Phase 98.18）

arch 第 47 行：入口 `P=26886`，距离操作员的 27000 只有 **114 PSI**，而它读 **+1019**（全量高档加成）。
按他的规则，这一行该只有 ~493 —— 差 **526 F**，而抖动带是 ±50。
一行上下不靠阈值的错行，可以解释成「阈值其实在 26900」；**这一行不能** ——
它把 27000 这个数按死在了它自己的邻域里。

同时它是**唯一**在「更新后读法」下也被抓住的一行（它的 `Ppost=27854` 越过了 27000，
而 #44/#45/#46 没有）：**最尖的那条证据，在两种读法下都是尖的。**

**How to apply:** 「我的阈值和你的差一点」和「有一行就在你的阈值下面、行为按我的规则走」
是两句完全不同的话。找的不是最大的那行，是**离边界最近的那行**。

## 391. 「显示」和「物理」是两条通道，量不到就说量不到，别把它折进结论（Phase 98.18）

操作员那句「≥12000PSI **显示为黄色**且对温度有一定影响」里**有两个断言**：
显示那条**捕获里没有通道**（没有颜色/材质/贴图任何一路），温度那条有。
而 remake 侧**根本没有压力驱动的颜色** —— 全 DataModel 只有 CBL 灯和 grav-armed 灯是黄的，
`StateBridge` 把压力写成一个纯数字。

能说的只有两句：**温度那道门我量了，12000 被排除；显示那条我量不到，而 remake 里它不存在。**
把后者说成「他没有这个功能」或者「他说错了」都是**越界** —— 缺一个功能不是错一个数。

**How to apply:** 一条规格里如果混着**可观测的和不可观测的**，拆开说，并**明确哪一个没有仪器**。
「量不到」是一条结论，不是一句免责声明。

## 392. 玩家读到的是更新后的数——这一条把 P12 的推荐撤了（Phase 98.18）

`P12` 问的是 stall 门读**步的入口**还是**更新后**的压力，我推荐的是入口（三道门一致）。
这一轮操作员那句「压力小于2200时失速」是一条**新输入**：他是在游戏里**看着表**说的，
而表上显示的是**这一步跑完之后**的压力（`StateBridge.luau:31` 写在 `Engine:Step` 之后）。
所以在「看到 < 2200 就失速」这个观察下，**更新后读法才是自洽的那一条** ——
入口读法会出现「表上 2410 而温度正在往下掉」。

**这不把证据变成「已定」**（他的措辞是关于**现象**的，不是关于**实现**的），
但它足够把「A 推荐」那个标签撤掉：两侧现在各有一条弱证据，而代码停在 B。

**How to apply:** 「操作员说的一句话」也算证据，只要问清**他是从哪个观测点说的**。
表盘上的数、日志里的数、内部变量的数在同一个词（「压力」）下面**是三个东西**（取舍 293 那一族）。

## 393. 门读门槛的两个坐标轴可以同时扫，而扫出来的集合能是不相交的（Phase 98.19）

`P12` 一直是「读入口还是读更新后」的二选一。这趟捕获说明**不该那样问**：
把 θ 和读法**一起**扫，各自给出一个**判对全部 40 步的集合** ——
入口 **(2127, 2251]**、更新后 **(1999, 2127]**。**两个集合不相交，只在 2127 相接。**

于是**交付的 (2200, 更新后) 落在自己那个集合的外面**，TRGWeb 自己的 (2250, 更新后) 一样，
两个各错在同一步。**一个布尔会把这件事故意藏起来**：单问「2200 对不对」，
两边都能答「差不多」；**问集合，不相交就自己跳出来。**

打折的两条也写在同一处：压在一步上（40 步里 39 步两法同判），
且那一列压力前面 5 拍没重画过（机制没定）。
但那个 P 值通过了一条**独立**的测试 —— 它满足 `calculation.luau` 的耗损律到 ≤7 PSI，
而所在平台的残差跨度只有 0.9 / 5.7 PSI。

**How to apply:** 当一个阈值模型有两个自由坐标（这里是「门槛」和「读哪一刻」），
报告**能判对全部数据的取值集合**，不要报告「某个具体组合对不对」。
两个集合的不相交本身就是结果，而这个结果只有集合的写法能表达。

## 394. 一个纯偏移常量，要用「把一组实测分布平移过去」来验，不是比均值（Phase 98.19）

`StallCooling` 交付 750，从来没验过。实测 **≈806**（均值 805.56 / 中位 808.00）。
判据不是两个均值相减 —— 那是同一个数换一种写法。
判据是：**纯偏移保跨度**，所以把降温那 21 步整体抬 806，应当**看起来像**升温那 19 步。
实测升温 `[150..298]`，抬 806 的降温 `[153..306]`（几乎重合），抬 750 的是 `[97..250]`
（低端 97 落在升温从没出现过的地方）。跨度 148 / 153 也支持「纯偏移」。
n≈20、跨度 ~150 ⇒ 两组均值之差的标准误 ≈9–10 F ⇒ 806 vs 750 约 5.5–6σ，不是噪声。

**How to apply:** 一个常量如果是两相之间的**纯偏移**，就把它当成一次分布平移来检验：
平移后的分布要落在被对照的那个分布上。只比均值等于没检验。

## 395. `calculation.luau` 的斜率被钉到 ±2%，而整份文件的残差「跨度」是个没有意义的数（Phase 98.19）

98.15/98.16 走的是**水平**（逐拍 `|dP − pred|` 的中位），这次走**斜率**：
在安静段拟合 `dP = a + b·T`，b 在 0.00892..0.01091（三条拟合），
**calc 的 0.010 每条都在 11% 内，TRGWeb 的 0.020 差 45–55%**。
最尖的一条横跨 4130 F，残差跨度只有 **0.97 PSI**（b=0.010 预言 41.3）⇒ **b = 0.0100 ± ~0.0002**。
这是**第二条输入不相交的路**给同一个模型投票（取舍 380）。

**方法上的一半更重要**：先把整份文件的残差跨度算成一个数，是**没有意义的** ——
它把「段」压成了「一个数」，而信号**只在按步编号看时才在**。
把整份文件当一个数看会给一个**看起来完全合理**的答案（§0.18 同族）。

**两条负结果一起报**：头段斜率 −0.06644 / R² 0.5731、尾段 +0.00020 / R² 0.0050，
两段都**不安静**，不参与这个比较。**没红的断言要写下它为什么不该红。**

**How to apply:** 比模型时先按「安静段」筛，再拟合；把筛掉的那些段的数也打出来，
否则「只报拟合好的那些」和「全都拟合」在纸面上逐字同形。

## 396. 从一个台阶表里读「控制器的量子」之前，先查有没有那种控制器做不出的台阶（Phase 98.19）

残差里 `131.50/2 = 65.75` 与 `196.76/3 = 65.59` **互相吻合到 0.25%**（q ≈ 65.7），
看起来像一个干净的读数（尤其它既不是 60 也不是 70，很「有信息」）。
**但同一个文件里有 542.31 和 441.60 两个台阶，风扇最大 6×70 = 420 也做不出来** ——
所以这份数据里**肯定还有一条连续排气**，那两个比值就是**两条控制叠在同一段上**的产物。
**这条不是数，是测试 ③ 的线索。**

**How to apply:** 量子 ≈ 台阶 / 整数之前，先问「这个文件里有没有我假设的那个控制器
**做不到**的台阶？」有 ⇒ 台阶的来源不止一个，比值读不得（§0.21 同族：分母里坐着被测对象）。

## 397. 「两条独立的路给出同一个数」要先写下每条路到底算了什么（Phase 98.19）

tick 周期这趟是 **1.7750 s**（71 s ÷ 40 步），是第四条时间戳路。
第一版脚本把这个和「重复行计数」并称两条路 —— **那是错的**：预测值与观测值由同一个计数推出来，
它是**恒等式**，不是第二条路。这正好是取舍 380 的反面：
380 说两条路落在同一个数上才算证据，这里要补一句 **—— 称它们为「两条」之前要逐条写出来。**

**How to apply:** 每写下一个「另一条独立的路」，就把它的输入和算式写出来。
两条路用的若是同一个计数、同一个字段，那是一条路说两遍。
## 398. 一个「留字母序前 N 条」的截断不是大小限制，是一次按名字的随机删除 —— 而给它说话的注释是可以单独证伪的（Phase 99）

**Why:** `panelLines` 在监视器亮灯 >12 时只留**字母序前四条**，注释给的理由是
「for a monitor that lists its alarms [the first few are] enough to see which fired」。
**这句话两半都量出来是假的** —— 警报根本不在文本里（见 399），而上限丢掉的正好是payoff。
实测损失：`MainControlRoomMonitor` 81 亮 → 丢 77 条，含
`PressureLabel`/`StressLabel`/`TempLabel`/`PEANameText`；`ThermalControlRoomMonitor`
丢掉 `Title=NET C-PUMP FLOW RATE` 和整条 `PUMP C1..C3` / `CHAMBER FAN 1..6` 名册。
**排序键和重要性之间没有任何关系**：按名字取前几条，丢掉哪些**完全由名字决定**。

**How to apply:** 看到快照截断，**先问排序键是什么** —— 按字母序截断等于按名字删，
而名字和这个快照要回答的问题无关。其次：**一句替一个上限说话的注释本身是一个可测的断言**，
量它，不要去改上限。修法上，去重可以（相同字符串不带额外信息）**但必须保留重数**
（`xN`，因为三条一样的 `StressLabel=0 %` 是三个通道），而且**印刷的计数要留在原来的定义上**
（这里留 `nlit`），否则你会把「去重把读数改了」和「读数本来如此」混在一起。

## 399. 两个对象可以共用一块矩形，于是状态通道躲在一个静态通道后面（Phase 99）

**Why:** `AlertsControlRoomMonitor` 载 39 条 caption，**39 条全部** `Visible=true` /
`TextTransparency=0.00`，警报响不响都一样 —— 它们是永久标签。**状态在每条背后另一块 Frame 上。**
所以一份**只看文本**的快照**看起来**覆盖了警报面板，实际上什么都没覆盖：
它把 39 个永久字符串抄了一遍，而真正在变的那一层不在里面。**几何是这条路唯一的入口**：
按 `(AbsolutePosition, AbsoluteSize)` 取整配对，27 条 caption 配到**唯一**一块板，
剩下 12 条正好是非警报标签，**27 + 12 = 39** 对得上 —— 这个等式是配对方法正确的证据。

**How to apply:** 一块屏幕上「显示了一批状态」的字，**不一定是那批状态本身** ——
问一句「变的是这个标签，还是它背后/旁边的东西」。配对（captions ↔ plates）要按**几何**做，
而且要**带重数**：一块板被两条 caption 共用的，**当歧义丢掉，不要靠运气配上**
（同 Blender 那几轮 `bridge_loops` 的「先断言再动手」）。最后，**把假设写成假设**：
「板亮 = 该警报在响」符合每一条读数，但**没有一块板被看过它转变**，所以交付的注释里
就标着它是假设，并写下一行的测试方法。**不容怀疑的是那条否定**（caption 是死的）。

## 400. 观察窗口短于被观察者自己的周期，就分不出「活着」和「死了」；而一个引用了自己记录格式的表头，会让朴素的计数器永远数到 1（Phase 99）

**Why:** 两条都在同一轮挣到，**都是「错的量法不报错」那一家**（§0.18）。
**① 窗口 vs 周期**：`Heartbeat = 30`、`Flush = 1`。我在 12 秒里读了三次文件、每次都是
31,085 字节，差一点写下「采集器在 61 s 死了」；13:31 那个文件 41,223 字节、**还在长**。
**一个 30 秒周期的写者，在 12 秒的窗口里必然是一条平线** —— 平线是它的正常形状，
不是死亡证据。**② 计数器数到了图例**：`sum(1 for l in lines if ' -> ' in l)` 得 **1**，
而全场唯一的 ` -> ` 在表头行 `# record: [HH:MM:SS] <rel-s> <path> <old> -> <new>` 里 ——
**真记录行 0 条**。一个跑在「表头把这个文件的记录格式原样引用了一遍」的文件上的计数器，
**永远会数到至少 1**（同 359/360：影子在栈帧里，检查在看命名空间）。

**How to apply:** **先知道被观察者的周期，再选窗口** —— 窗口必须**长于**它。
判「这个进程还活着吗」时，一个平坦的读数**在窗口短于周期时什么都不说明**。
写文件扫描器时，**表头和正文要能被分开**（这里表头全部以 `#` 开头，正文行才带 ` -> `），
否则你的计数器会把格式说明当成数据；**一个数出来是 1 的计数，先去看那 1 条长什么样**。


## 401. 驱动器走「命令文件」，不走热键、也不走硬编码序列（Phase 100）

**Why:** 三条路都想过，只有一条留下来了。热键不行 —— `RightAlt` / `RightControl` /
`RightShift` 已经被采集器、监视器和开机采集器占了，**第四个别名会静默撞车**（Phase 54 撞过）。
硬编码序列不行 —— 那是一条**我停不下来的**序列，而且它把「我按了什么」藏在字节码里。
命令文件是**耐久记录**：我在 Windows 这一侧写一行 `3 fire <路径>`，它在 Roblox 那一侧执行，
`trg_drive_log.txt` 记下结果。**「被要求过什么」和「做到了什么」都在盘上。**
而且它**不依赖 worker** —— 此刻 worker 掉了、`execute-script` 被拒，文件系统那条路照样能用。

**How to apply:** 命令格式 `<seq> <verb> <args>`，seq 单调，执行所有 `seq > 上次执行的`，
`trg_drive_state.txt` 存最后那个 seq。**命令文件永不截断** —— 清空之后一条丢掉的命令
就看不见了。要重跑就写一个**更大的 seq**，不要改老的。桩与模块都靠文件收活，
所以「注入一次」= 「通道重建」，不需要任何工具面。

## 402. 先传送、再发火（Phase 100）

**Why:** `fireclickdetector` 只**发信号**，它**不移动角色**。任何距离检查看的仍是角色的
**真实位置**，所以隔着一张地图按下去会被**无声拒绝** —— 没有报错、没有日志、
`MouseClick` 也「发过了」。这和 §0.18 那一族同源：**错的量法不报错，它只安静地给你一个数**，
这里错的按法也一样安静。`doFire` 因此先 `PivotTo` 到该件旁边再发火。

**How to apply:** 距离默认 `DefaultStuds = 4`、抬高 `RiseStuds = 3`，
第三参数可以覆盖。**日志里记的是实际那句发火调用**，不是「我打算用哪句」。

## 403. `fire NOCHANGE` 是真结果，不是失败（Phase 100）

**Why:** 发火之后读 `Workspace.Stats` 前后比一次，变了记 `CHANGED`、没变记 `NOCHANGE`。
`NOCHANGE` 是一条**负测量**：它说「这个信号传过去了，但世界没动」。它和「根本没发出去」
（`ERROR`）是两件事，和「没按」更是两件事 —— 把三者混成一个「失败」，
就等于把三种不同的现场压成一句话（同 §0.12 第 1 条那种压缩）。

**How to apply:** 三个读数是三件事：`CHANGED`（按到了）· `NOCHANGE`（按了、没反应 ——
可能是距离门、可能是这个 CD 本来就不写 Stats、也可能是客户端/服务端那条缝）·
`ERROR`（这句调用本身炸了）。**负测量也算交付**，因为它把「有反应」这一支排除掉了。

## 404. 抗挂机必须记下「这次走的是哪条路」（Phase 101）

**Why:** 抗挂机有两条路：`VirtualUser:CaptureController()` + `ClickButton2()`（真输入），
和一个 `PivotTo` 抬 0.5 stud 的退路。后者**根本不重置那个计时器** —— 它只证明角色还活着。
两条路在代码里只差一个 `return`，跑起来却一条能救命一条救不了，而**踢人是静默的**：
会话消失之后，后面的命令根本没被执行过，盘上没有任何一行会说它没跑。
这和 `fire` 记「实际用哪句」是同一件事：**一个静默的退化和真跑了，事后必须长得不一样。**
写成 `antiidle <哪条路> at rel <秒>`，两条都不可用就写 `antiidle nil` ——
**一个 nil 比一行不写诚实**（不写就等于把「这里没有抗挂机」伪装成「还没到时间」）。

**How to apply:** 任何「主路 + 退路」的写法，日志里都要有那个区分主退路的字段，
而且**退路自己也要能报告自己失败了**（`nil` 是一个值，不是缺席）。
判据放在日志里，不要放在「我写了 `pcall` 所以它一定成」这句话里。

## 405. GUI 按钮是控制面的**客户端那一半**（Phase 101）

**Why:** `ClickDetector.MouseClick` 的处理函数跑在**服务端**，而从客户端 VM 发火
只到得了客户端自己的监听者。所以 `d1` 那六次 `fire NOCHANGE` **在结构上就分不开**
「按到了但那个东西在这个状态下是惰性的」和「根本没按到」—— 传感器没有量到被测对象。
GUI 按钮是反过来的：它的处理函数**一定是客户端 LocalScript**，从这里按下去跑的是真代码，
它发的 remote **真的到服务端**。**这是一个关于 Roblox 的事实，不是关于这台执行器的** ——
普查列了 1019 个 `ClickDetector`，**没有一个是开局面的**，而一张菜单按钮正是
「停着的游戏在等什么」的最可能答案。

**How to apply:** 要判断「游戏是不是停在一个可交互面上」，先找 **`PlayerGui` 里的
`TextButton` / `ImageButton`**，不要一棵一棵去撞 `ClickDetector`。
按下去之后仍然要 `CHANGED` / `NOCHANGE` 两分（取舍 403），
因为「客户端跑了」不等于「服务端认了」。

## 406. `ok and v or 'ERR'` 会把一个**假布尔**渲染成「读不出来」（Phase 101）

**Why:** Lua 的 `and/or` 挑的是**假值**，不是 `nil`。于是 `tostring(ok and v or 'ERR')`
在 `v == false` 时给出 `ERR` —— **每一个「真的是 false」的旗标都读成「这个字段坏了」**。
现场症状不是报错，是**整份 dump 看起来像坏的**：`GameActive=false` 和 `ISEBreach=false`
（正是停机那一刻该有的两个值）全都变成 `ERR`。**读不出来的字段和读到假的字段被压成了同一个字串**，
而它们要做的判断正好相反。修法是按**类型**渲染：只有真的 `pcall` 失败才写 `ERR`。

**How to apply:** 任何 `x and y or z` 的三元写法，先问一句「`y` 可能是 `false` 吗」。
是的话就展开成 `if/else`。同一个坑在 `guiCensus` 里是**预先躲开**的：
`Visible` 是布尔、`false` 在那里是一个**真答案**，所以那一段故意不用 `and/or`
（写成 `visStr = '?'` 再被 `if okv` 覆盖 —— `?` 只留给真的读不到）。

## 407. 桩必须**故意缺**着真环境缺的那一样，退路才算被验过（Phase 101）

**Why:** `d2` 的发火链是三条依次试（`firesignal` → `sig:Fire` → `getconnections`）。
如果桩里塞一个完整的信号桩，第一条就赢，**后两条一次都不会跑到**，
而「三条都会试」这句断言**是在量桩的构造，不是在量世界**（同取舍 351 那族）。
所以桩的 `mksig()` 里 `Fire` **直接抛**
`Fire is not a valid member of RBXScriptSignal` —— 照着真执行器做，于是
`getconnections` 那条**是被走到的**，`press FAIL no route worked` 那个分支**是到得了的**。

**How to apply:** 写桩之前先问「真环境里**缺**什么」，然后**照着缺**。
一个总能让被测代码走第一条分支的桩，验的是第一条分支；
**能被验到的那条退路，才是真的退路。** 反过来，跑完之后要回头数一遍
**哪些分支一次都没到过** —— 这一轮就是这样才发现 `sig:Fire` **一次都没赢过**，
它是一条**永远输的退路**（别的执行器有，所以不是死代码，但日志里别指望看见它）。


## 408. `md5` 证明两份文件一致，说不了**跑的是哪一份**（Phase 102）

**Why:** 交付件的身份一直是用 `md5(repo) == md5(exec)` 核的 —— 那个等式是真的，
但它只对**盘上的字节**说话。这一轮它第一次不够用：`d3` 的字节推进 `workspace\` 之后，
「已经跑起来的那一份」**仍然是 `d2`**（`autoexec` 桩在**注入那一刻**读盘，之后改盘不追）。
于是有两个不同的东西同时叫「驱动器」，而 `md5` **对哪个都没意见**。
能分开它们的只有**运行自己的输出**：`execute-script` 回的 `loaded tag=d3 bytes=30875 running=true`，
和日志里那行 `# d3 start 23:25:18`。
同一件事还有第二张脸：`M.start()` 是**追加**的，所以 `# d1` / `# d2` / `# d3` 三行
**同时住在同一份日志里**，读「第一行」永远读到最老的那一份 —— **文件名说的是这件事，不是这件事的当前值**。

**How to apply:** 一个身份由**两个**独立读数构成：盘上的字节（`md5`），和运行里自报的 TAG。
**只有前者的检查，在「换了盘没换进程」时全绿。** 所以交付一件能被热替换的东西时，
它必须**自己说出自己的版本**（`M.TAG` 出现在每一段输出的开头），
而读取端要读**最新**那一条，不是第一条。

## 409. 换版本之前先停，而且用**文件的 `mtime`** 验它真的停了（Phase 102）

**Why:** 驱动器是一个 `while M.running do` 的轮询循环，两个循环同时读同一个命令文件时，
`seq` 会互相抢、日志交错，而**任一份输出都还是格式正确的**。所以「停」必须**先于**「换」。
但「停」也不能靠回话：`stop requested` 是**请求**，`drive loop exited` 是**日志**，
两者都写在它自己的文件里，而那个文件**在循环没停时也照样被写**。
真正的判据是**另一个文件停止变化**：`trg_drive_loop.txt` 每 poll 重写一次，
所以它的 `mtime` **冻住**才是「循环真的退出来了」—— 短窗口分不出「活着」和「死了」（§13.6 同族）。

**How to apply:** 停止一个自驱进程的顺序是**停 → 看它的心跳文件冻住 → 才动字节 → 再起**。
验「停了」用**心跳的 `mtime`**，不用它说「我停了」——
一句话可以是上一次循环留下的，一个不再变的时间戳不能。

## 410. 两个调用点写同一行，就等于没有调用点（Phase 102）

**Why:** `d2` 的抗挂机有两个触发器（周期计时器 `AntiIdlePeriod`、事件 `Player.Idled`），
**两个都写 `antiidle <路> at rel <秒>`**。于是「这次是谁触发的」在盘上读不出来 ——
和「两个 build 都不改 TAG」是同一个病，只是换了一层。
`d3` 的修法是让日志带上来源：`antiidle <路> via <verb|timer|idled> at rel <秒>`。
它**当场就还了账**：23:27:39 同一刻两行，
`140.8 … via idled`（`d3`）和 `744.7 …`（**还活着的老 `d2` 实例**，没有 `via`），
**除了 `via` 那个词以外逐字节相同** —— 没有它，这两行读起来就是「它同一秒动了两次」。
**顺带**：`loadstring` 热重载在**同一个 VM** 里留下旧模块的 `Connect`，所以「热重载」≠「重注入」；
这条对桩也成立 —— `mksig()` 必须给出**真的 `Connect`**（真 `RBXScriptSignal` 上 `Connect` 存在，
只有 `Fire` 不存在），否则事件那条路**根本注册不上**，「`via idled` 从没出现过」
就分不清「没触发」和「挂不上钩」。

**How to apply:** 一个「多个触发器 → 同一段动作」的地方，动作那一行必须带**来源字段**。
判据是：把任意两行的来源名字盖住，你还能不能说出这次是谁干的。不能，就是缺字段。
以及：用一个能留下旧连接的机制做热重载时，**重载之后先数一遍同刻的输出行数**，
那是在数 hook 的个数，不是在数动作发生了几次。


## 411. 先把「回得来」验掉，再发「停」（Phase 103）

**Why:** 我停了循环，然后才发现我回不去 —— 而「回来」依赖的东西（daemon 的 worker）
**在我停之前就已经死了**。停本身是可逆的**设计**，但不是可逆的**操作**：
一个 `while M.running` 的循环，它读的那份命令文件、它写的那个心跳，
**都要有一个活着的 VM 才有意义**。所以「先停、再换、再起」（取舍 409）这条链的**第一步是正确的**，
**错的顺序是我把「停」放在了「起」的前面却没有先证明「起」在这台机器上还成立**。

**How to apply:** 任何「先关掉再换」的步骤，**先证明开得回来** —— 哪怕只是证明那条路的每一步都还在。
判据是一句话：**这一步失败之后，我能不能只用已经验过的东西回到起点。**
不能，就先别做这一步，或者先把「回到起点」那条路也验一遍。
「我有权限做 X」和「我有能力撤销 X」是两件事。

## 412. `process_window: 0` 是「扫早了」的指纹，而且它没有第二枪（Phase 103）

**Why:** `findMainWindow` 在 76 分钟里只打三行，**两次 new-process 都在进程出生后约 1 秒扫**，
那一刻窗口还不存在，而 **Solara 不重扫**。同一个二进制在同一个晚上，
一次接住（2220，因为扫描时它已经在跑）、两次漏掉（13592 / 15512，因为扫描比窗口早）。
**这里错的不是能力，是顺序** —— 而 `process_window: 0` 这一个数把「扫早了」和「没扫到」
分开了（前者是窗口不存在，后者是进程不存在）。

**How to apply:** 一个只在**某个时刻**找一次的机制，它的失败要说成「**顺序错了**」，
不要说成「**没有 / 坏了**」。恢复方式通常是**把顺序倒过来**
（让被找的东西先存在，再启动找它的东西），而不是去修那个找的动作。
连带：`0` 和「没有这一行」不是同一件事 —— 写日志的时候，**「找了，没找到」要打一个数出来**。

## 413. 同一个失败跑两遍不是两次证据，除非第二遍改掉了那个嫌疑（Phase 103）

**Why:** 我上一轮把「第一个客户端的失败」归因成「**另一个实例还活着**」。
第二次实验时机器上**一个客户端都没有**，失败**逐字相同** —— **否定它的是我自己安排的第二次实验**。
两遍下来，被证掉的是那个嫌疑，留下的才是机制（`gameinfo:` 空 ⇒ 403）。

**How to apply:** 一个假设要写进文档，得先有一个**会把它和别的假设分开**的实验，
而不是一个「再试一次」。同一条命令跑第二遍，只有当你**改掉了那个嫌疑**，第二遍才是证据；
否则两遍只是一个嫌疑说了两次。**失败跑两遍给的是同一个机制，不是同一个嫌疑人。**

## 414. 子串会匹配到它自己的否定（Phase 103）

**Why:** `"unconnected": 1` **含**子串 `connected":1`，而这两个是**相反**的状态。
于是 `grep -q 'connected":1'` 在一个**断开**的客户端上**成功**（已实测 `in` 为 True）。
同族还有一次是**名字不对**（`identify` 回 `Spinbox.uparrow`，问裸名字找不到，取舍 344）——
**那次是名字错了，这次是名字对但被父串罩住**：两种都让「找不到」和「找到了」在输出里同形。

**How to apply:** **不要把 JSON 当文本搜。** 状态字段是一整格的时候，
先把它**切出来**再比（发 `"%d|%s"`、用 `${R%%|*}` 取数、再 `[ "$N" -ge 1 ]`）。
更一般的判据：**你要断言的那个值是另一个值的子串吗** —— 是，就不能用「包含」。

## 415. 一条够重要的相关性，机制没定也要写在交付旁边（Phase 103）

**Why:** 2220 的优雅退场（`23:41:47.799 shutDown`）比我启动第二个客户端晚 **10.0 秒**，
而日志里**没有一句**把因果连起来。**机制没定就写没定** —— 但这条如果不发出去，
下一次我还会在旁边起第二个，而代价是**唯一一条活通道**。

**How to apply:** 区分「**当成结论**」和「**当成操作约束**」。前者要机制，后者只要相关性足够强、
且**代价不对称**（遵守它几乎不花钱，违反它可能毁掉你唯一的东西）。
写的时候把两件事分开写：读数是什么、机制没定。**不要把「没定」当成「不能说」。**

## 416. `AbsolutePosition` 是 GUI 空间，`VirtualInputManager` 是屏幕空间（Phase 104）

**Why:** `GuiObject.AbsolutePosition` 的 y **从顶栏下面量起**；`VirtualInputManager` 的
`SendMouseMoveEvent` / `SendMouseButtonEvent` 和 `UserInputService:GetMouseLocation()`
**把顶栏算在内**。两者差 `GuiService:GetGuiInset().Y`，这台客户端是 **58**。
我自己的交付物 `pressAt` 漏了这个换算，于是 **`d1`..`d4` 的每一次合成按压都落在目标上方 58 px**，
而**症状是零**：`SendMouseMoveEvent` 返回、按钮事件返回、点击落到那个像素上的别的东西上。
`clickPoint()` 也只是**返回两个可信的数**，只是空间错了 —— §0.18 最纯的那张脸。

**How to apply:** 换算是 `ap + inset + as / 2`，而 **inset 要从 `GuiService` 读**，
~~并且**先看 `ScreenGui.IgnoreGuiInset`**：带这个旗的 ScreenGui **本来就在屏幕空间**，
再加 inset 就反着错 58 px；`SurfaceGui` / `BillboardGui` 同理（inset 只对一种情形成立）。~~
**已更正，见 Phase 105 / 取舍 422：`IgnoreGuiInset` 不搬子件的空间** ——
它只搬 ScreenGui 自己那个 rect（与 Roblox 自己的 `MouseGui` 是一对精确镜像，底边同一条、顶边差 58）。
inset 对**每一个** ScreenGui 后代都要加、**不带条件**；那个旗**只进返回的名字**，**不进分支**。
一个 rect 转点的地方**只许有一处**：`as / 2` 全文件恰好一次、调用点恰好两个，写进构建器当不变量。

## 417. 桩缺一个元方法臂，红的是「harness 炸了」不是「检查失败了」（Phase 104）

**Why:** 桩里的 `Vector2` 有 `__add` / `__div` 而没有 `__sub`。SUBTRACT 那个变异让
`ap - inset` 抛 `attempt to perform arithmetic on local 'ap' (a table value)`，
整个 harness **中止**，红的理由是**桩不完整**，和被测的换算毫无关系。
**这比最坏的绿还坏 —— 因为它和一个真的抓到逐字节同形。**

**How to apply:** 桩要覆盖被测表达式**可能出现的每一个算子臂**，而**验法是把每个变异都跑一遍**
（变异会走到你没打算走的那条路）。一条检查红在一个**和它无关**的理由上时，
先问「是检查失败了，还是这个文件**炸了**」—— 后者的输出里没有 `FAIL`，只有 traceback。

## 418. 生成的 harness 必须 `io.write` 它的报告（Phase 104）

**Why:** `lua file.luau` **丢弃顶层 `return`**。一个只 `return report` 的 harness 在**全绿**时
**什么都不打印**，于是一个调用方（自测里那句 `"PASS " in out`）**分不出「全绿」和「从没跑过」**
—— 两者在这条路上**逐字节同形**。

**How to apply:** 报告**打印出来**（`io.write(report .. string.char(10))`），`return` 可以留着
但不能是唯一出口。更一般的判据：**任何「没输出」都可能同时是「通过」和「没执行」**，
所以一个跑起来该说话的东西**在成功时也要说话**。

## 419. 参数的形状错了，报错会指向那个参数（Phase 104）

**Why:** `VirtualInputManager:SendMouseMoveEvent` 第 3 参、`SendMouseButtonEvent` 第 5 参
在这个 build 里是 **`Object` 类型**。我传 `false` 抛 `Unable to cast value to Object`，
而 `game` 和 `nil` **都成功**。**我把这句读成了「这个 VM 是只读的」并写进了结论** ——
报错说的是**参数**，不是 VM 的能力（§0.17 一族：报错指向的地方不是出错的地方）。

**How to apply:** 一个 API 报 `Unable to cast value to Object` 时，**先扫它自己的参数类型**
（换一个合法形状再试：`game` / `nil` / 真容器），**别急着给宿主下结论**。
`pcall` 的失败是**关于那次调用**的，不是关于环境的。

## 420. 合成输入是排队、在脚本返回之后处理的（Phase 104）

**Why:** 同一次 `execute-script` 里 move + click，点的是**上一个**指针位置；
`UIS:GetMouseLocation()` 也**慢一拍**。所以「我把指针移过去了然后点了」在这条通道上
**不成立** —— 两次调用之间必须**真的过一拍**，或者接受「点在上一个位置」。

**How to apply:** 需要「先移后点」时，把移动和点击**拆成两拍**（两次 `execute-script`，
或让它自己等一拍）。同理，读回自己的动作结果之前要留一拍。

## 421. 一条「真的信号 + 视觉上是零」的读数，两半都报（Phase 104）

**Why:** 用零对照钉住了指纹稳定之后，`Union` / `Caution` 那 **0.001 stud** 的位移
是**真信号**（对照不动，它动）—— 但**视觉上是零**。只说「动了」是过度声称，
只说「没动」是漏掉信号。

**How to apply:** 把两个判决**分开写**：仪器上是什么、眼睛上是什么。别让「视觉上是零」
自动降级成「什么都没发生」，也别让「有读数」自动升格成「能看出来」。

## 422. 两个 GUI 空间，而 `IgnoreGuiInset` 不搬空间（Phase 105）

**Why:** `GuiObject.AbsolutePosition` / `AbsoluteSize` 和 `GetGuiObjectsAtPosition` 答的是
**CoreUISafe 空间**（y 从顶栏下沿量起，**可以为负** —— 实测背景开始在 **−58**）；
`VirtualInputManager` 与 `UIS:GetMouseLocation()` 答的是**屏幕空间**。两者差
`GuiService:GetGuiInset().Y`（这台 **58**）。四条互相独立的边（背景起止、按钮起止）**全部**落在
CoreUISafe 上，所以这不是一个点上的巧合。
我先前断言「`IgnoreGuiInset=true` 只改 `ScreenInsets` 而不改子件的空间，所以那个旗在撒谎」
—— **是错的**。它们是一对精确镜像：带旗的 `ScreenGui abs=0,-58 1151x714`、不带旗的 `MouseGui
abs=0,0 1151x656`（**底边同一条 656、顶边差 58**）。旗子搬的是
**ScreenGui 自己那个 rect**，子件的 `AbsolutePosition` **一个空间都不换**。

**How to apply:** 换算是 `ap + inset + as / 2`，**对每一个 ScreenGui 后代都加、不带条件**；
`inset` 从 `GuiService:GetGuiInset()` 读（`TopbarInset` 是个 `Rect`，`.Max.Y` 才是 58，`.X`/`.Y` 抛）。
`IgnoreGuiInset` **只许进返回的名字**（`…/ignoreinset`），**不许进分支** ——
把它写成 `if` 的那一版（`d5`）算出 614，而真值是 673。一个 rect 转点的地方**只许有一处**：
`as / 2` 全文件恰好一次、调用点恰好两个，写进构建器当不变量。

## 423. `GetGuiObjectsAtPosition` 是一把不产生输入的尺子，但它答的是 GUI 空间（Phase 105）

**Why:** 要判「那一下合成按压到底落在哪个像素上」，需要的是一把**不合成任何输入**的尺子 ——
否则量它的那一次本身就会按下去。`PlayerGui:GetGuiObjectsAtPosition(x,y)` 就是它：
**输入为零**、只读一张列表。代价是它答的是 **GUI 空间**（同 422），
所以它**能**回答「这个像素上有什么」，**不能**回答「VIM 该指向哪里」。

**How to apply:** 用它当**旁证**、不当**换算**。它还有一个便宜的第二用途：同一条 x 列在
两个空间里返回的**个数不同**（实测 `n=11` 对 `n=15`），是「两个空间确实不同」的独立征兆。
它**不在官方参考的方法列表里**（`getmetatable(PlayerGui).__index` 是 nil），
所以别指望文档能确认它存在 —— 运行时存在就够了，**但要在源码里写下「这是量出来的」**。

## 424. `NOCHANGE` 分不开「按钮是死的」和「按压根本没落到按钮上」（Phase 105）

**Why:** `d1`..`d4` 的 `press` 把结果分成 `CHANGED` / `NOCHANGE` / `ERROR`，当时看起来够用。
cmd 44 报的是 `NOCHANGE` —— 而真因是**那一下按空了 28.4 px**（同 422，就是少加了那次 inset）。
一个「按到了、按钮没接线」的世界和一个「压根没按到」的世界，**在这一列上逐字节相同**。

**How to apply:** 一个「没反应」的读数**必须**配一把**独立**的尺子来分岔 ——
这里就是 `GetGuiObjectsAtPosition`（423）。日志里**记实际发出的那一句**
（`mouse@476,596`），因为**意图**和**效果**是两件事，而这次分的正是它们。
按下目标之前先算**它到底在哪个像素**，别让「我瞄准了它」自动升级成「我按到了它」。

## 425. 变异测试里「必须留绿」的对照，必须挑变异**动不了**的那个（Phase 105）

**Why:** `selftest_drive_clickpoint.py` 的每个变异都点明一条必须留绿的断言 ——
否则「红了一大片」只证明这个文件**会**失败，不证明某条断言和某个缺陷有关。
`d6` 之后 `C_IGNORE`（`IgnoreGuiInset` 那一例）**和 `C1` 一起红**：因为 inset 现在对每个
ScreenGui 后代都加，去掉 inset 自然把它也带走。**一个会红的对照不是对照。**

**How to apply:** 对照**挑变异结构上碰不到的**输入 —— 这里换成两个 **inset 为零**的案子
（`C_SURF` / `C_NONE`）：丢掉或减掉 inset，它们逐字节不动。改完 **9/9 变异各自红在指定那条上**、
对照全绿。**「对照红了」不是测试坏了，是它不再是掩护** —— 对它要做的动作是**换**，不是删。
