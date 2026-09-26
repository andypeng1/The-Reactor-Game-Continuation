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
