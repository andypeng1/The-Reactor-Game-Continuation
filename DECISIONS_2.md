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

## 426. 挡住点击的是 LayerCollector，不是那个按钮（Phase 106）

**Why:** 在 `Workspace.Consoles.ThermalConsole.CFLever1.ClickPart` 上做四格梯子，每一格
都在**开火那一刻**验过 `mouse.Target == ClickPart`：不出手 → `MouseClick=0`；
`UnlockUI.Visible=false` → **仍然 0**；再 `+MouseGui.Enabled=false` → 0；
再 `+ScreenGui.Enabled=false` → **1**。而 `PlayerGui:GetGuiObjectsAtPosition(575, 299)` 在那一像素上
**只有一个** Active/可点件：`ScreenGui.UnlockUI`（`1151.2 × 714.4` @ `0, −58`，全屏）。
两个读法都还活着（游戏把自己的锁写回 `true`，或 `Visible` 不是引擎命中测试用的那个属性），
但**能用的操作只有一个**：把 `LayerCollector.Enabled` 置 `false`。
**此前「把 `UnlockUI` 藏起来就能点」是错的** —— 它从来没有单独成立过。

**How to apply:** 要往世界里点之前，**逐个关掉 `PlayerGui` 下的 `LayerCollector`**
（`ScreenGui` / `MouseGui` 都要），用完同一步恢复；不要只藏某一个按钮的 `Visible`。
判据用服务端复制出来的值（见 427），不要用本地信号。

## 427. 本地数到的 `MouseClick` 可能是 0，而服务端已经动手了（Phase 106）

**Why:** 落在 `MainReactorConsole.StartUpBigLever.StartClickPart` 上、**真的落地**的那一次
（`Stats` 变了两个值：`BreachValCore false->true`、`HDEF.IntegrityVal 12->20`）报的是
`MouseClick=0`；另一次报 `MouseClick=1` 的反而一个值都没动（那次在 `MonitorBoot` 之前按，
被游戏自己挡了）。**两个方向都不一致。** 客户端 `MouseClick` 不是判据。

**How to apply:** 点一下之后读**服务端的复制态**（这里是 `Workspace.Stats` 的 32 个 `ValueBase`）
并做前后差。本地信号只能在**它响了**的时候当正证据；**它不响时什么也证明不了**。

## 428. 被截断的枚举，不能拿来支撑一个否定（Phase 106）

**Why:** 同一轮犯了两次。`GetGuiObjectsAtPosition` 的 33 件里「只有一个 Active」是从
**打印了 12 of 26** 的那一段读出来的；Thermal 监视器 **117** 条非空 `TextLabel` 只看前 **45** 条，
就写下「没有温度读数标签」。**两次都不是数据不支持，是打印先截断了。**
同族 §0.20（数出来多少个，先问数的是谁）。

**How to apply:** 任何「**没有 X**」的结论，先确认枚举**跑完了**：要么去掉上限，要么把上限
写进那句结论（「前 45 条里没有」）。截断是**我看不见的**，它不会报错。

## 429. HDEF 发电机开着就会过热，而冷却不是杠杆（Phase 106，操作员两次更正）

**Why:** 我把开机链第六步（`Consoles.HDEFGenerator.PowerLever`）开着就不再管它，
`HDEF.IntegrityVal` 一路 `12 → 20 → 66 → 88 → 99` 单调爬（**这一段是我量的**）。
操作员两句话，第二句把第一句给的那个解法也否掉了：
「HDEF Generator爆炸了（其实是过热，开时间太长就会这样）」→
**「HDEF Generator过热是必然的，冷却没办法减缓」**。

**我把第一句读成了「缺冷却」，于是写下「先开 C-Pumps 再开 HDEF」—— 那条处方作废。**
能用的规则只剩一句：**别让那台发电机一直开着**；C-Pumps 不是它的解药。
（原版这一族系统本来就没做完 —— Phase 74 量到那段手册自己盖着 `{wip system}` 的章。）
**没定的是**「把电源杆关掉之后 `IntegrityVal` 会不会回落」：那是可以量的，还没量。

## 430. 「反应堆开着」有两个判据，而它们不一致（Phase 106）

**Why:** 同一时刻：`Stats.GameActive=true`、`Core.OutputVal=144` GW、`TemperatureVal=9420 F`；
而配额监视器 `PreStartupFrame` 仍写着 `PENDING REACTOR ACTIVATION`、`Stats.GameStart=false`，
Log 监视器顶栏是 `CORE COLLAPSE DETECTED - PLEASE WAIT WHILE THE REACTOR COMPLETES ITS
AUTOMATED SHUTDOWN INSTRUCTIONS. ANY INTERRUPTIONS …`。**机械读数说在跑，状态机说没有。**
而且 T / P / 输出 **20 秒逐位不动**、只有辐射在爬（676→715）—— 那是停机积分器，不是活堆芯。

**How to apply:** 报「开着」的时候**两半都报**（机械读数 + 游戏自己的状态字符串），不要挑一个
当结论。注意那句 `CORE COLLAPSE DETECTED` 在我按**任何东西之前**就挂在顶栏上了。

## 431. 只在一张隐藏页上读到的读数，不是读数（Phase 107）

**Why:** `ThermalControlRoomMonitor` 的六条 `StatusLabel`（都在 `FanFrame` 里）在一次 16 秒观测里
从 `ON ON ON ON ON ON` 翻成 `OFF ×6`，我据此写下「六台风扇自己关了」；而**同刻**
`Stats.Fans.Fan1..6` **全是 `true`**。原因：`FanFrame` 整页 `shown=false`（被别的页盖着）。
同一轮里 `MainMonitorFrame.ReadingsFrame` 的 `TempLabel` / `PressureLabel` / `FluctuationLabel`
也全是 `shown=false`，而它们的值**一直在动**（`3731->1065`、`582->-238`）。
**隐藏页的文本由游戏照常更新** —— 所以「页被盖住」与「值在动」同时成立，
**两者都不告诉你这一页在不在屏上**。

**How to apply:** 读监视器上的任何东西之前先算**有效可见性**：
自己的 `Visible`（`LayerCollector` 用 `Enabled`）**乘上每一层祖先**的同一个属性，
再叠一层 `TextTransparency < 0.95`。`first(ui, 'Name')` 这种「文档序第一个同名件」的读法
**必须废掉** —— 它跨页取件，取到哪一页是布局的巧合。同族 §0.2（读实例状态）。

## 432. 按名字的递归查找，会把一条路径读成「不存在」（Phase 107）

**Why:** `Stats:FindFirstChild('Core.TemperatureVal', true)` 问的是**名字等于
`"Core.TemperatureVal"`** 的子件，而 `Core` 是文件夹、`TemperatureVal` 是它的孩子 ——
于是 32 个值**全部**读成 `?`，而 `Stats` 好好的（`n=32`，键全在）。
**上一轮同一次探测**用的是 `d:GetFullName():gsub('^Workspace%.Stats%.','')`，读到全部 32 个。
**同一个对象、两个读法，一个好、一个「全空」。**

**How to apply:** 带点的路径**不能**喂给 `FindFirstChild` / `WaitForChild` —— 要么逐段走，
要么拿 `GetFullName()` 当键。**「全空」先怀疑读法**（§0.20：数出来多少个，先问数的是谁）。

## 433. `plr:PlayerGui` —— 一个属性被当方法调（Phase 107）

**Why:** 整段脚本以 `attempt to call a nil value` 中止，改掉一个字符（`:` -> `.`）就好。
**这一族错误是好的**：它**响**（运行时错误），不像 431 / 432 那样安静地给出一个错答案 ——
**安静的那个才要防。**

**How to apply:** 属性用点、方法用冒号。运行时错误值得庆祝。

## 434. 温度有两个读数，一个在掉、一个钉死（Phase 107）—— 这是 `温度监听那个变量好像有点问题` 的第一份数据

**Why:** 同一时刻 `Stats.Core.TemperatureVal = 9420`（~60 次采样**逐位不变**）、
`Core.PressureVal = 7320`（同），而监视器**被盖住的那一页**上
`TempLabel 3731 -> 1065 F`、`PressureLabel 582 -> -238 PSI` 在动。
**两者不是同一个量**（9420 vs 1065）。**机制没定** —— 我列得出两种读法
（停机积分器的残留值 / 一张不随状态切换的旧页），**都不能排除**。
把更简单那个解释否掉的是：`Core.RadiationVal` 在 `785 -> 460` 动过 ——
所以**不是「`Stats` 整个不写了」**。

**How to apply:** 报温度一律**点名是哪一个字段**（`Stats.Core.TemperatureVal`，还是监视器
`MainMonitorFrame.ReadingsFrame.TempLabel`）。**要定机制，必须在温度真的在动的那一段里同时抓两个读数**，
而那时监视器必须停在**读数页**上（本轮它停在 `ShutdownFrame`）。

## 435. 一次 `changed=0` 的按压，不是闸门的证据（Phase 107）

**Why:** 同一套机架、同一个 `ClickPart`、同一个方向与距离（`1,0,0@4.5`，
`mouse.Target == part` 在开火那一刻验过）：一次回 `changed=0`，**下一次把拉杆拨动了**
（`LeverUnion 108.8817 -> 110.4322`，t≈0.2–0.4 s）。**两次输入逐字节相同，结果不同** ——
所以单次 `changed=0` 分不开「游戏挡掉」与「这一下没按到」；**第一次为什么没按到，没定。**

**How to apply:** 要下「这一步按不动」这种否定，**同一条件重复几次**，
并且**先把枚举展开**（Phase 106 那个 `MonitorBoot` 的否定能站住，是因为它对着 1000 键的
GUI 指纹**零变化**）。同族 **427**（本地 `MouseClick` 不是判据）、**428**（截断的枚举支撑不了否定）。

## 436. 反应堆点着之后失速了，而那条指令早就在我手上（Phase 107）

**Why:** 报告屏逐行是 `FAILED QUOTA PENALTY -$200000`、**`STALLOUT PREVENTION -$60000`**、
`CBL DAMAGE -$40000`、`TOTAL -$263000`；告警板上 `STALLOUT POSSIBILITY` 是**全板唯一的蓝**
（`0.00,0.67,1.00`）。算术用操作员自己的模型：`floor(9420/50) - 70*6 = -232 PSI/tick`，
对 `StallPressure ≈ 2200`。**六个风扇全开、温度 9420 时压力站不住。**
操作员原话 `快，先关一点风扇，不然会失速` **在失速之前就说过** —— 我没在它发生前动手。

**How to apply:** 开机链走完之后，**第一件事是看压力斜率**，不是继续走别的装置：
`floor(T/50) - 70*fans` 为负就**先关风扇**。**失速是低压故障**，风扇是 **−60 PSI/tick**，
所以**关风扇是抬压**。这条现在有代价：一个班次（`-$263000`）。

## 437. 班次结算屏只有操作员能按（Phase 107）—— 而它现在开着

**Why:** 报告屏开着（`A.E.R.N - SHIFT [1] REPORT`，`TOTAL -$263000`），全屏唯一可点件是
`PostShiftButton`（`HoldButton` 也在）。按它 = 确认结算 + 进 `Shift [2]`，
而那是**操作员的钱与进度**。§3.11.9 的规矩没变，**这一轮我没按**。
我观测的二十秒里 `ResetShift` 恒 `true`、`NextShift` 恒 `false`，**没有任何自发的重置**；
**能不能绕开那个按钮我不知道，也没试。**

**How to apply:** 报告屏只读。要开始下一班**得他按**，或者他明确授权我按（`QUESTIONS.md` **D7**）。
不要为了「让进度往前走」去按它 —— 进度不是我的。


## 438. 按下去的那个点来自**引擎**，不来自算术（Phase 108）

**Why:** `d1..d4` 把点击点**算**出来（`AbsolutePosition + AbsoluteSize/2`，GUI 空间）再交给
`VirtualInputManager`，而 VIM 吃**屏幕空间**，两者差 `GetGuiInset().Y = 58` px。
于是**每一次合成按压都落在目标上方 58 px，而症状是零** —— 事件返回、点击落别处，
和「按了没反应」逐字节同形（§0.18 最纯的那张脸）。Phase 106/107 那条**真的点亮了反应堆**的
配方根本没做这个算术：**移动 → 问 `UIS:GetMouseLocation()` → 按它报的那个点**。

**How to apply:** 合成输入一律「**先动、再问引擎、再按引擎报的点**」；**永远不要**把
GUI 矩形的中心算出来当屏幕坐标用。这条已收成原语 `clickScreen()`，且是驱动器里**唯一**
按像素的地方（构建器断言调用点）。任何「按下去没反应」先怀疑**你按的是你的答案，不是引擎的答案**。

## 439. 一个只在有活时才抬的下限，不是下限（Phase 108）

**Why:** 执行器读自己那份 `trg_drive_state.txt` 会**滞后** —— 文件里是 `203`，
同一次 pass 里 `loadSeq()` 却回了 `0`。`runCmds` 因此看到 `last = 0`，**从头重放了整份命令文件**，
穿过那条本该结束会话的 `stop`，走进结束会话的那一按。把下限也放进内存（`M._seq`）**还不够**：
早先的写法只在**有活要跑**的那一 pass 抬它，于是「已经全部做完」的那一 pass 把下限留成空的 ——
**而那一刻，挡在一次滞后读和文件开头之间的，正是那次滞后读本身。**

**How to apply:** 排序下限要活在**最快的、不会滞后的**存储里（内存），而且**每一 pass 都抬**
（`if maxSeq > (M._seq or 0) then M._seq = maxSeq end`），**不只在有活的那一 pass**。
「有活才写」写下的不是下限。任何「我做过了」的标记，先问：**它是在哪一条路径上被写的，
那条路径失败时它还会不会在。**

## 440. 驱动器的整文件闸：5.1 解析 + 0 反斜杠 + 0 CR —— 并且说清证的是哪一件（Phase 108）

**Why:** 驱动器的那些 harness **每段只编译一个 region**，命令循环、抗挂机、普查那几段**没人看** ——
一个语法错会由**原版游戏里的执行器**发现，而不是在这里。录制器和监视器早有整文件闸，驱动器一直没有。

**How to apply:** `run_tests.sh` 里加一道整文件闸：`loadfile` 过一遍（**Lua 5.1**）、
数一遍反斜杠（**必须是 0**，§0.10：编辑层会解码一次转义）、数一遍 CR（**仓库钉 LF**）。
**在输出里写清它是 5.1 解析不是 Luau 编译** —— 两者**证的不是一件事**
（同 378：「结构性证据不是数值证据」）。

## 441. 文件头上的 tag 必须等于 `M.TAG`（Phase 108）

**Why:** `TRG_original_drive.luau` 自己的头写着 `(tag d5)`、版本块写着 `==== d7`、
而 `M.TAG = 'd9'` —— **三个标签互相不一致**，一件事三张脸。这正是 commit `f65c21f` 修过的那一类
（HOWTO 的 13.9 头写着 `d5` 而身份表写着 `d6`），也是 Phase 102 那条
「两个 build 都不改 TAG = 没有 tag」的同族。

**How to apply:** 文件的**自述身份**（头 tag、版本块、`M.TAG`）必须**同时**改，
或者干脆只留一个权威（`M.TAG`）+ 一句「当前身份看 HOWTO §13.9.1」。
**散文说的谎和代码说的谎一样贵。**


## 442. 这台 Studio 的 `EditableMesh` 是**按 id 间接**的旧一套 —— 而它**探不到的名字会硬报错**（Phase 109）

**Why:** `EditableMesh` 在这里是个 **datatype**（`typeof(em) == "Object"`），**不是 Instance**，
所以「成员不存在」不是回 `nil`，是**抛错** —— 想用 `if em.SetVertexColor then` 这种写法探它，
探的本身就是一次错误。于是每一个名字都得先用 `pcall` 试，并且**把报错原文打出来**，
因为报错说的是**实参形状**不是「没有这个函数」：
`SetColor(vertexId, Color3)` → `Unexpected EditableMesh id type. Expected Color id, received Vertex id`；
`SetFaceColors(f, c1, c2, c3)` → `EditableMesh function: expects 2 arguments`；
`SetFaceColors(f, {Color3, ...})` → `Invalid id`。
**三条报错里没有一条说「你这个 API 是间接的」** —— 它们是**同一句实话的三种译法**（§0.13 的报错不指向事实那一族）。

**How to apply:** 这一套的正确形状是 **面记颜色 id、颜色 id 再映 `Color3`**：
`SetFaceColors(faceId, {colorId, colorId, colorId})`（**表**）配 `SetColor(colorId, Color3)`。
**先量工具再写调用**；探一个未知 datatype 的成员，先用 `pcall` 拿到**报错字符串**，
不要指望 `nil` 检查（§0.18：错的量法不报错 —— 这里反过来，**错的存在性检查会报错**）。

## 443. 颜色 id **算不出来，只能当场收** —— 它是按顶点共享的（Phase 109）

**Why:** 颜色 id 在**第一次用到时**按面的顺序分配，而且是**按顶点**共享的：
`f1=(a,b,c)` 拿到 889/890/891，`f2=(b,d,c)` 拿到 890/892/891 —— 同一个 `b` 还是 890。
所以**没有**任何事后反推的办法：`GetFaceColors` 只在你**刚建完那个面**时告诉你想知道的东西，
攒着以后再问，拿到的是你这次新建面的新 id。构建时数出的 `colourConflicts = 0` 正是这个假设**被证实**的那一下 ——
若颜色是按面存的，这里会立刻变成一万多，而**画面照样是对的**（每面一个顶点色，肉眼分不出）。

**How to apply:** 建面的那个函数里**顺手**收 `GetFaceColors(faceId)`，维护 `vertexId -> colorId`；
**并**在构建末尾把它变成一条**会红的**计数（`conflicts`），别让「假设成立」只活在我的脑子里（§0.13）。

## 444. 两个上限是**量出来**的，而且绑定的是三角形那一条（Phase 109）

**Why:** 顶点 **60000**、三角形 **20000**，两条都是探针撞出来的（`Vertex count above limit` /
`Triangle count above limit`），不是文档给的。而**先撞到的是三角形那条**：
`172 × 176` 那版拓扑顶点才 30k、面 60k，是**面**先越界。所以「留余量」要按**面**留，
按顶点脑子里算一遍会得出「还很宽」这种**错的宽裕感**。

**How to apply:** 用之前先跑一次探针把上限变成数字；`build()` 的开头用**具名常量**
（`CAP_VERTICES` / `CAP_TRIANGLES`）把它挡住，越界时抛的是**我自己的话 + 我自己的两个数**，
而不是引擎那句**没有数字的** `Triangle count above limit`。交付的拓扑留 848 面余量（19152/20000）。

## 445. 「它真的在动」的唯一证据是一对**受控对照**（Phase 109）

**Why:** 单独两张截图**什么都不证明** —— 相机可能动了、部件可能挪了、时间当然在走。
我先犯过一次：某一对里有一张**是操作员自己挪了镜头**后拍的，画面完全不同，
我一开始差点把它读成「透镜变了」。**变量没有钉住的时候，两张不同的图就是两张不同的图。**

**How to apply:** 要证「渲染跟着顶点走」，就造一对**只有时钟变**的：`camPos` 同、`partPos` 同、
同一个部件、**同一个模块实例**（用一个持久的 holder `require` 它，命中模块缓存，
于是 `state` 是同一份而不是重建的一份），只改 `clock`。然后**用工具比**（`compare_images`），
不要用眼睛下结论。**并且提前写下否证**：如果两张逐字节相同，那是「渲染不跟顶点」，不是「动得小」。

## 446. 一个采样到**黑色**顶点的检查，什么都证明不了（Phase 109）

**Why:** 第一版的 `verify` 拿第 1 环的颜色去比 —— 那是**阴影正中心**，
`vertexColour` 在那里本来就把亮度压到近 0，而我的比对函数在那里也返回近 0。
**两边同时为黑，于是断言恒真**（§0.13：不会失败的检查不是检查）。它是**绿色的**，
而且绿得很有说服力，因为它旁边那几条断言确实在干活。

**How to apply:** 采样点要**沿着一个会变的量展开**（这里取 1, 6, 11, … 环，横跨阴影、爱因斯坦环、
外缘三区），并**报出最亮的那一个采样值**（`brightestSample 2.148`）——
**一个恒为黑的量，是「这条检查没在测东西」的唯一信号**。另外把 1/255 那个数**写进文档**：
`worstColourDelta 0.0029` 是 mesh 的 8 位量化，不是缺陷，免得下次有人把它当 bug 追。

## 447. Edit ≠ Play 在几何交付上的形状：**一个 `Script` + 一块静帧，字节同一**（Phase 109）

**Why:** Edit 模式里建出来的 `MeshPart` 是**静帧** —— 它漂亮、可读、可截图，但**不会动**。
会动的那一版必须是 Play 里跑起来的脚本，而 **Play 里改 `Source` 不落盘、Edit 里改也不动运行时副本**（§0.4）。
所以「交付」不是那一块 `MeshPart`，是**那两个东西加同一份字节**。

**How to apply:** 交付一个 `Script`（`ServerScriptService.GravityLens`，Play 时 `build()` +
`Heartbeat:Connect(M.step)`）**加上**一块由**同一份源码**在 Edit 模式建出来的 `MeshPart`；
两边都按**长度 + 校验和**核到同一份 18961 字节。**并且明写在文档里：静帧是给人看的，
动的那一半只有源码保证** —— 一个只验了静帧的交付，是一张**照片**，不是效果。


## 448. `-I` 会把**用户级 site-packages** 从 `sys.path` 里拿掉 —— 于是「没装」和「探条把它藏了」长得一样（Phase 109）

**Why:** 我为引力透镜写 `_tools/ppm_to_png.py`（纯 stdlib 的 PNG 编码器），写的**理由是错的**：
我在 docstring 里写下「这台机器上没有 Pillow，说它有那条 memory 是错的」。
实测 `python -I -c "import PIL"` -> `ModuleNotFoundError`，而 `python -c "import PIL"` -> **`PIL 12.3.0`**。
落点是 **用户级** site-packages（`C:\Users\andypeng1NB\AppData\Roaming\Python\Python314\site-packages\PIL`）。
本仓库的每一条 Python 命令都带 `-I`（隔离：忽略 `PYTHONPATH`、不加载 user site），
理由是防**被别人种下的 `import json`**；而 **`-I` 恰恰就是那个把用户 site 从 `sys.path` 摘掉的开关**。
所以「我没装这个包」和「我用了藏它的那个开关」在终端上**逐字节同形** —— **§0.2 的又一页**：
**探条只探它探的那件事**。（`-E` 单独用没事；`-s` 单独就能复现。`numpy 2.5.3` 在同一个目录，同样会被藏。）

**How to apply:** 判「某包有没有」**一律用两个解释器各问一次**：
`python -c "import X; print(X.__file__)"`（默认）**和** `python -I -c ...`（本仓库的常规）。
两者不一致 ⇒ 包在，是**标志**藏了它，不是包不在。**报「没有 X」之前必须先说出你用哪个标志探的。**
反面也成立：既然写成了零依赖，就**别改回去** —— 零依赖的脚本在两种标志下都对，
而「因为以为没有 Pillow 才写成零依赖」这个理由**不能留着不修**（散文的谎和代码的谎一样贵，同 441）。

## 449. `Content.fromObject(editableMesh)` **是进程局部的** —— 它不跨网络，另一端拿到的是**单位立方体**（Phase 110）

同一个实例、同一句 `AssetService:CreateEditableMeshAsync(part.MeshContent)`：
建它的那个进程回 `9728` 顶点 / `(-46 -46 -11) .. (46 46 -0.7)`，
另一个进程回 **`1536` 顶点 / `(0,0,0) .. (1,1,1)`** —— 一个**单位立方体**。

这就是操作员那句「进测试之后透镜变成一个小方块」的**全部原因**：
`MeshContent.SourceType = Object` 的网格**活在创建它的那个进程的内存里**，
服务端建、客户端画 —— **画不出来**。棋盘格占位是渲染器对「内容不可解析」的说法。

**规矩：** 用 `EditableMesh` 做的东西必须**在画它的那个进程里建**。
「把网格发过去」这条路不存在 —— 要共享形状，共享的是**参数和公式**，不是网格。

## 450. 进程局部的资产在另一端的表现是「一个像样的错东西」，不是「一个错误」（Phase 110）

两条同族，都是**没有报错**的：

- `AssetService:CreateEditableMesh()` 在给不了它的进程里**返回 `nil`**（不抛错）。所以
  `pcall` 回 `ok = true, em = nil`，而 `if not ok` 那句一切正常 —— 崩在**下一个消费者**身上。
- `CreateEditableMeshAsync(content)` 拿不到内容时**也返回一个网格**（那个单位立方体），
  **不是失败**。所以「读回来有 1536 个顶点」和「读回来就是那个网格」在类型上同形。

**规矩：** 凡「读回来对不对」的检查，先问**它是不是那个 fallback**。
判据是**形状**不是**存在**：0 顶点 = 空；**1536 顶点、跨 1.0** = 替代品。
`pcall` 只挡抛错，挡不住「成功返回了一个错东西」。

## 451. 「每帧改写多少顶点」**不是一个已经成立的机制** —— 它是我的外推，而不成立的那一半今天没复现（Phase 110）

我一度看到客户端自建的透镜变棋盘格，于是给出一个**很合理**的解释：30 Hz 全量重写 9728 个顶点，
客户端丢弃网格。**今天它没有复现。** stride 1（每拍全量）与 stride 4 各自跑满约 4 分钟、
约 6600 拍，都是**完整的透镜**，`CreateEditableMesh()` 预算恒 `ok`、往返恒 `loadable 9728`。

所以那一次的棋盘格**至今没有解释**（诚实的说法就是这一句）。分片仍然留在交付里
（`CFG.SLICE_STRIDE = 4`：每拍 ≤ 2432 次写入、整张盘 0.13 s 刷新一遍），
但文档里必须写成**保险**，不能写成**已证的必需** —— 见 297（算过的和量过的在盘上同形）。

## 452. `execute_luau` 跑的不是游戏那个 VM —— 交付路径必须**自己跑过自己**（Phase 110）

我这一轮前半段的每一条「Play 客户端」读数都是在**插件 VM** 里取的，
而**真正要交付的东西是 `StarterPlayerScripts` 里的一个 `LocalScript`**：
**它从来没在我的探针里跑过。** 我拿插件 VM 的结果去替它回答，替了三轮。

**做法（§0.17 的同一条）：** 要在**游戏的 VM** 里问问题，就在
`Players.LocalPlayer.PlayerScripts` 下放一个临时 `LocalScript` 让它**自己**测，
把结论写进 workspace 上一个 `StringValue`（`workspace.LensReport`），插件 VM 再读**那个值**。
**这与 §0.2 同源**：`require`/模块状态在命令栏里是空的；**这一轮又多一条 —— 被测者本身不在那个 VM 里。**

## 453. `cam.CFrame * CFrame.new(0, 0, -d)` 不是「相机前方 d stud」（Phase 110）

相机 look 向下约 15 度时，`-260` 把部件放到**离地 67 stud 的地下**，
而 `WorldToViewportPoint` 照样回 **`onScreen = true`**（它在视锥里，只是在基板下面）。
我照着三张这样的读数摆了一排测试盘，截图里一片空白，我先去怀疑渲染。

**规矩：** 要摆「看得见的东西」，用相机的**水平**方向（`Vector3.new(look.X, 0, look.Z).Unit`）
加一个**指定高度**，别用相机自己的 -Z。**投影在屏 ≠ 看得见** ——
遮挡不在 `WorldToViewportPoint` 的回答范围里。

## 454. **尺子换一次，同一个节拍就从 92.25 变成 90.000** —— `nfft` 是尺子的一部分，不是格式细节（Phase 111）

仓库里存着的那份 `asstes/music/ReactorStartup.report.txt` 说 **92.25 bpm strength 0.700**。
我按它去 remix，自己量出来却是 **90.000**。查下去：那份报告是 `--nfft 8192` / hop 2048 出的
（`stft 4097 bins x 5679 frames (21.5 fps, 5.4 Hz/bin)`），而 `analyze.main` 的默认、
也是 `remix.py` 用的是 `n=2048` / hop 512（**fps 86.13**）。

**在细尺子上，90.00 的梳状得分 326.174，92.25 是 13.441**（24 倍），
峰很尖（±0.05 bpm 的肩 109 / 89）。所以 **90.000 是对的，存的 92.25 被取代**。

规矩：**一份存的测量报告带着它的尺子** —— 报告里那句 `stft … bins x … frames (… fps)`
不是元数据，是**答案的一部分**。要用它的数，先看它用的是哪把尺子；
**两个不同的 `nfft` 给出的「同一个量」不是同一个量**。（§0.18 的同族：错的量法不报错。）
那条 92.25 没有被抹掉 —— 它连着理由一起被取代了，因为「为什么两份报告不一样」是下一次会再问的问题。

## 455. 四个**单调**的「相位候选」是**斜率**，不是正拍 —— 换梳状才看得见（Phase 111）

要定「四拍里哪一拍是正拍」，我先用**拍上的平均包络**打分，四个候选给出
**59.3554 / 59.5056 / 59.6567 / 59.8085** —— 单调、跨度 **0.77%**。单调是**信号**：
把相位整体挪一拍，就是把一拍从前沿挤出去，而这段录音的能量**一路涨到 140 s 的高潮**，
于是「分数」量的是**包络的斜率**。**分母里坐着被测对象**（§0.21）。

改成**梳状**：`mean(拍上) − mean(交错的拍间)`。两个集合**在整个时长上交错铺满**，
每个候选看到同样的跨度，斜率抵消。这才把判据变成真的判据。

**并且加一个零假设**：24 个相位里最差的 `on/off` 比是 **1.016**，最好的 1.831 —— 判据得站在噪声上面。
最终余量只有 **+1.01 dB**（阈值 1.0 dB），所以这条**擦线过**，写进没验的那一半。

## 456. remix 进 `.gitignore` 的理由是**它引用的那段录音**，不是「文件大」（Phase 111）

`asstes/music/ReactorStartup_Remix.*` 是**采样那份母带**做出来的 —— 它引用的就是那段录音本身，
所以它**不能比它的源更自由地发布**。这和仓库里已有一条（`ReactorStartup.mp3` 本身）是**同一条理由**，
只是多推了一层派生。`.report.txt` 一起忽略：它描述同一段音频，数字足以重建混音。

**工具（`_tools/music/remix.py`）进仓库** —— 编配表、参数、检查器都是原创的，
和被采样的录音无关。**派生出来的数字搬进 `PROGRESS.md` Phase 111**，
因为报告本身不进仓库了（同 Phase 93 对 `ReactorShift` 的做法：**生成给人用的媒体进仓库**，
但那条规矩的前提是**它不含别人的录音**，这里前提不成立）。

**操作员知情**：选项文本就写了「它含别人的录音，公开出去是版权上的事，你自己定」，他选了这条路。
**我的那一半**是把它挡在公开仓库外面 —— 这一half是能自己判断、不需要问的。

## 457. 角色是**量出来的**，不是按位置摊的：最密的段落同时是最安静的（Phase 111）

给 remix 分「intro / main / build / climax」时，**按时间位置摊**会犯两个错，因为这段录音的形状是反的：

- **50–57 小节 dense 0.394–0.564，是它最密的地方，同时电平 34–38 dB，是它最安静的地方。**
  按位置摊 = 把**最忙的鼓组**（应该的 build）压在**最安静的音乐**上。
- **最后 88 s 电平 45–47.6 dB，是它最响的地方。** 按位置摊 = 给最响的尾巴上一个高通。
  实测尾巴比中位电平高 **+5.8 dB** → **拒绝**做一个 88 s outro，尾部走 main 的处理。

判据因此是**两个 z 分数**（电平 + 密度）一起看，不是时间。
**位置是「这段音乐在第几分钟」，角色是「这段音乐在干什么」—— 它们在这首曲子上是反的。**

## 458. 一个 **p90** 只有在**按角色分开**之后才说得通（Phase 111）

脚鼓对齐到最近的原曲低频起始：整体 **中位 26 ms**（半拍是 333 ms，很好），
但 **p90 = 4575 ms**（很差）。一个数说不出话的时候，**先问它在谁身上平均**：

    main    中位    23 ms   p90    733 ms   (n=169)
    build   中位  7455 ms   p90  11455 ms   (n=16)
    climax  中位  2069 ms   p90   4510 ms   (n=32)

`build` 与 `climax` 这两段**本来就没有强的低频起始可以落** —— 一个 p90 是**两个集合的混合**，
不是「脚鼓对不齐」。**分组汇总会把错的东西压得很合理**（§0.18 第二条）：看整体会去修一个不存在的缺陷，
按角色分开才知道要修的不是对齐，是**要不要在这两段落 kick**。

## 459. 标题里那个 **[WIP]** 是一句关于音频的**可检验**的话 —— 量一下，它是真的（Phase 111）

操作员给出了那份录音的**来源**：
`[WIP] (Piano) Portal 2 OST - Reconstructing More Science - Aperture Science Psychoacoustic Laboratories`。
「WIP」不是只影响文档措辞的元数据 —— 它是**关于这段音频会怎么结束**的断言，而那个尾巴我一直在猜。

量下来：音乐**跑到 t−1.6 s 还满着**（RMS 0.264），**~0.5 s 内掉进数字静音**，
**最后约 1.1 s 逐位为 0**。所以它是**「停了，后面接静音」**，不是作曲上的 outro，
也不是剁在半个音上的截断 —— **与 [WIP] 对得上**。

**规矩：一个来源标签如果可以被音频验证，就去验它**，别只在文档里抄一遍。
代价是**一次 15 秒的解码**；收益是那个 6 s `fade` 从**默认值**变成**量过之后的选择**。
（同 Phase 111 的其余部分：这条不改变任何音乐决定，只加固「不能发布」那条结论 ——
链条现在是两段：Valve 的曲子 → 某人的钢琴录音 → 这版 remix。）


## 460. 尺子必须**能判自己错** —— 新工具里第一件抓到的东西就是我自己写的长度（Phase 111 追补）

写 `_tools/music/midi_grid.py` 时，报告曲子长度的那一行是
`max(x[0] + x[1] for x in notes)` —— 我想要的显然是「最后一个 **note-off** 的 tick」，
写出来的是**两个绝对 tick 相加**（note-on + note-off）。结果：**90.00 s 的曲子报成 179.50 s**，
正好是个「看着像有 fade 的长曲子」的数。

它没被眼睛抓住，被**同一个工具刚加进去的那条自检**抓住了：**「有没有音符结束在自己那轨的结尾之后」**
（`off > track.length` 在格式正确的文件里不可能）。查下来每条轨都是 **0 个**，
于是 `max(on+off)` 那个 68928 只可能来自**加法本身** —— 一根算术，不是格式。

两条可复用的：
1. **一个看起来像整倍数的时长，先怀疑是量法，不是素材。** 179.5 / 90.0 ≈ 1.99。
   同族：§0.18 那五张脸全是一个模子 —— **错的量法不报错，它只安静地给你一个数**。
2. **解析器要自带一条「在这份文件里不可能」的断言。** running status 读错一个字节**不会抛异常**，
   它会继续产出事件、只是不是这份文件的事件；区分「解析出了点东西」和「解析出了这份文件」
   靠的就是这类不变式。这条自检留在工具里，**没通过就 exit 1**（同 §0.6 那条「崩溃与全过在 shell 眼里同形」）。

## 461. 操作员给的 MIDI **不是**那份录音 —— 而且这个结论要**旋转之后再问**，不是直接问（Phase 111 追补）

操作员 2026-10-11 往 `asstes/music/` 放了一份 `.mid`，**只给了文件名**：
`[WIP] (Piano) Portal 2 OST - Reconstructing More Science - Aperture Science Psychoacoustic Laboratories`。
从名字看它显然就是那份录音的曲子，**而这是本轮唯一需要先验的前提** —— 它决定后面每一件事能不能做。

**量下来是「不是」**：MIDI 是严格七声，**D#、G、A# 在 936 个音里一次不响**；
录音的 chroma **没有空档**，且第二大音级就是 **G（11.04%）**。

**关键在判据怎么下。** 最省事的写法是「MIDI 有没有用满 12 个音级」——
但**移调的改编是常态**，直接问会把合法的移调版本一起毙掉。
正确顺序是**先旋转、再看空档**：最佳旋转（−4 个半音，r +0.680）
**仍然把 D#、F#、B 留在 0**，而录音在这三处有 6.67% / 6.31% / 5.75%。
**一个在最有利的移调下都还缺三个音级的文件，不可能是这份录音** —— 这才是无条件的那句话。
（`r = 0.680` **不是**证据：它是旋转的相关系数，只说明「一堆坏答案里最好的那个有多好」。）
`midi_grid.py --compare` 现在**先旋转再报空档**，就是为了让结论不依赖「最好的坏答案」。

**连带（这条是纪律，不是发现）：** 前提错了就要**停下来说** ——
上一轮我差点把这个 MIDI 当成「那份录音的谱子」接着用；如果真按它去改 remix，
改出来的是**另一首曲子的和声**，而**它听起来会完全正常**。
同族：**「算过的和量过的在盘上逐字同形」**（§0.21 第 3 条）—— 只有被质疑时才分得开。

**这份 MIDI 进 `.gitignore`**（`asstes/music/*.mid`）：一份 MIDI **就是音符本身**，
中间没有录音可以让出处变得可争议 —— 它并不比它会被用来推导的那个来源更适合发布。
它**曾经被一次 `git add -A` 扫进一个公开仓库的提交**（`05c38c2`，只在本地的，已 `--amend` 掉，
新 sha `470e2e3`），**文件保留在盘上**。


## 462. **工作树是 HEAD，不是「你要推的那个提交」** —— 三条提交一起推才暴露出来（Phase 111 追补）

`github.com:443` 又断了，走 `_tools/_attic/scratch/api_push.py`（取舍 51/143 那条退路）。
这次积了**三条**提交，而那个脚本**只会推 HEAD 一条** —— 于是顺手把它改成推**一段范围**
（按**内容**认「服务器已经到哪儿了」，不看本地的 `origin/main`，因为那个 ref
**恰恰在需要这个脚本的时候是过期的**）。

改完立刻翻出一个一直存在的 bug：**它从工作树读字节。**

推 HEAD 的时候这是对的 —— 工作树里就是 HEAD。**推任何别的东西时它是错的**：
工作树里是 **HEAD 的字节**，而树上要的是**那条提交的字节**。实测 `470e2e3` 那 8 个路径里，
**5 个（正好是我刚改过的那 5 份 .md）工作树比提交里大**（`PROGRESS.md` 843728 vs 840798 …），
于是服务器上重建出来的 tree 与本地不等，守卫生效、什么都没提交 ——
而那个报错长得像「blob 重建失败」，其实是一个 **「我看的是哪个版本」** 的错位。

**修法：blob 一律 `git cat-file blob <rev>:<path>`，不从工作树读。**

**顺带补了两条同族：**
- **改名是一条写 + 一条删**。只发新路径，base tree 里的旧 blob 会**留着**，
  重建出来的树**两个都在**，守卫照样不通过（同 §0.22 那条「合并/改名都是不可逆的形状改动」的反面）。
- **删除没有 blob 可读**，`read_bytes()` 会在**推到最后一步**时死掉 —— 改用 `--name-status`，
  删除项发 `sha: null`。

**这一条的普适形态（同 §0.18 一族）：**「我以为我在读 X，其实我在读 Y」是**不会报错的**，
它只在**上下文变了之后**（这里是「从只推 HEAD 变成推一段范围」）才显形。
**一个只在单一用法下测过的工具，等于没测过**（同 §0.6 那条「探条只探它探的那件事」）。


## 463. **打击层不能用 RMS 定级** —— 一个瞬态的「平均值」不是它的响度（Phase 112）

`marks`（三个段落边界上的软冲击）原来是照 sub / pad 的规矩定的：和钢琴总线的 RMS 差 −8 dB。
读出来的**峰值是 1.0261** —— 三个冲击里的一个比**其余整首混音**还响。

**连锁反应比错误本身大**：母带的余量保护看到峰值 1.82（其中一半来自这三个冲击），
于是**把整首降了 6.02 dB**，交付文件测出 −22.01 dB 而目标是 −16.00。

**为什么 RMS 在这里是错的量**：一个瞬态的 RMS 只是它峰值的一小撮。用 RMS 给一个打击定级，
等于用「它平均有多响」去回答「它响的那一下有多响」。持续层（sub / pad）用 RMS 是对的，
因为它们的峰值和均值的距离小。**按信号的性质选尺子，不是按项目里其他层用了什么。**

---

## 464. 响度目标必须是**不动点**，不是**一步**（Phase 112）

母带原来的顺序：合并 → 归一到目标 → 为峰值取余量 → 限幅。
交付测出 **−22.01 dB**，目标 −16.00 —— 差的**正好就是那个余量 0.5007**。

**在峰值保护之前加的那个增益，不是到达文件的增益**，因为保护会拿走一部分。
所以目标不能是「先归一再到别处去」，得是**不动点**：归一 → 限幅 → **测量** → 再来，直到测出来的落位。
现在最多 4 趟、落在 0.25 dB 内停，并且**把限幅器自己削掉多少印出来**
（`limiter peak reduction`）——「花了多少响度」是个数，不是一句话。

**同族**：取舍 **463**（也是「一个数在链子上被另一个环节改掉」），
以及 §0.21（**差值里的分母坐着被测对象**）—— 都是「你以为你设的那个数，不是到达的那个数」。

---

## 465. `0.5 * (L + R) ** 2` 与 `(0.5 * (L + R)) ** 2` 差 √2 —— 而两者都不报错（Phase 112）

修完 464 之后干跑仍然不对，**指纹是第 2 趟 gain 1.0000 却还是量到 −22.01**。
原因是单声道 RMS 写成了 `np.sqrt((0.5 * (L + R) ** 2).mean())` ——
Python 把它读成 `0.5 * ((L+R)**2)`，比真正的单声道 RMS **高 √2**，于是每趟落在目标下 **3.01 dB**，
而打印出来的增益说它到了。

这是 §0.18「**错的量法不报错，它只安静地给你一个数**」的又一例。
可复用的判据是**这个病征的形状**：一个声称到达目标的增益，配一个稳定偏离目标、
**且偏离量是某个常数**（这里是 √2）的读数 —— 那是**算式**错，不是**被控对象**错。
两个错误的表达式**都能跑、都不抛**，所以只能靠「偏离量是不是一个整齐的常数」来分开。

---

## 466. **在混叠上取最大值不是测量** —— 相关峰落在梳齿上时（Phase 112）

onset 走时检验报出 **lag +19 帧（221 ms）**。真相：那份 MIDI **每个音都在十六分格上**
（250 ms = 21.5 帧），所以 flux↔train 的相关是**一把梳子**，齿在 +19 / −24 / +41 / −46 帧，
分数 0.240 / 0.224 / 0.224 / 0.215，而**物理预测的那一处（−2 帧）是 0.215** —— **在噪声里打平**。
第一版在整个 ±20 帧取 argmax，于是报出的是**哪一颗齿碰巧最高**。

**改了搜索窗没有用 —— 得改问法。** 现在窗**只要半格宽**（任何齿都进不来），
并且**用物理去判它**：`|lag − (−n/(2·hop))| ≤ 2.5`。这是一条**可证伪的预言**，
不是「允许有偏差」——真有一个 100 ms 的错，峰会跑到 8.6 帧外。
**并且把齿的分数照印**（0.240）：相关**分不开**零和一个十六分，正是窗口必须窄的理由。
把齿藏起来、只印赢的那个数，就把这条变成了便宜话。

**同族**：取舍 **465**（错的算式照样给数）、§0.20（**分区的边界落在数据上时，两种取整都会错，而且只错一半**）。

---

## 467. **top-4 音级顺序不是音符检验** —— 频带把音区耦合进了权重（Phase 112）

检验「交付音频最强的四个音级 = 源最强的四个」在**录音**上过（r 0.894，top-4 全对），
在这个合成音色上**不过**：音频 `A, B, F#, G#` vs 源 `C#, D, E, F#`。
差点去怀疑渲染 —— 但它**不是**音符错：

**基准把每个音数一遍；测量是 300–3000 Hz 的带通。** 在那个带里，**高音的基频直接露出来**
（B4 = 494 Hz 正在带里），**低音只剩泛音**（D2 = 73 Hz 整根埋在带下面，只能靠它的谐波说话）。
于是**频带把音区耦合进了权重**：音频 **B 10.84% vs 源 4.70%**、**D 8.02% vs 源 16.24%**。
那个顺序是**音色**的事实，不是音符的事实。

**换成旋转检验**：12 个移调里哪个最合？它**有零点差 —— 另外 11 个**，
而且它回答的是真问题（这首有没有被移调）。实测**零旋转 r +0.813 胜出，次好的 +0.508**。
top-4 照印，标 `PRINTED, not checked` 和理由 —— 一个自己知道自己弱在哪里的检查，
比一个悄悄通过的好看的检查有用。

**同族**：§0.21（**一个词如果替你做了选择，你读到的就不是测量** —— 那里的词是「伴奏」，这里是「最强」）。

---

## 468. 用**限幅买来的响度**是唯一还不回去的那种（Phase 112）

目标响度定 **−19.0 dB**，不是 `make_song` / `remix` 用的 −16.0。理由是**量出来的**：
这首的**波峰因数约 21 dB**（钢琴的起音比平均电平高 21 dB），所以够到 −16 得**在每一记起音上削掉 5 dB** ——
会得到一个数达标、听起来被压扁的文件。

三条：① **平台会把安静的文件免费提上来**，所以「不够响」是可逆的、**被压扁是不可逆的**；
② 反向的取舍不存在对称性 —— 没人能「把 5 dB 的限幅还回去」；
③ 所以母带**把限幅器自己削了多少印出来**（`limiter peak reduction`），
让「花了多少响度」是个数而不是一句话。

**这一条不能推广成「一律更安静」** —— 它说的是：**当你只能用不可逆的手段去够一个数时，
先问那个数是不是你真正要的。**

---

## 469. 第三种版权派生：**不是采样那段录音，是把音符弹出来**（Phase 112）

三份东西，派生一层比一层薄：

| 东西 | 和原曲的关系 | 状态 |
|---|---|---|
| `ReactorStartup.mp3` | 别人**作曲**、别人**演奏**的录音 | gitignore |
| `ReactorStartup_Remix.*` | **采样那份母带**做出来的，引用的是录音本身 | gitignore |
| `asstes/music/*.mid` | 一份**音符级转录**：**就是那首曲子的音符**，中间没有录音 | gitignore |
| `ReconstructingMoreScience.*` | **演奏那份转录的音符** —— 复现的是**作曲**本身，不是指向它 | gitignore |

最后一份是**最薄**的一种，也是最像「可以发布」的一种 —— 因为它里面**没有别人的录音**。
但那正是它不能发布的理由：**它复现的就是那首曲子**。
**这个选择是操作员自己做的**（他要的就是这个），而**我的那一半是把它挡在公开仓库外面** ——
仓库是**公开的**（Phase 51）。派生出来的数字写在 Phase 112 里，因为那份 `.report.txt` 不进仓库。

---

---

## 470. 记录器的 `CLICK` 通道挂的就是执行器触发的那**一个**信号 —— 「被点击」不自证服务器接受了（Phase 113）

`window.txt` 写着 `why=the start-up lever was clicked`，`opened_at=105.90`。
**那不是独立证据**：flow 里 11 条 `CLICK` 与我那 11 次合成按压一一对应
（`StartUpLever`×3 / `RoomLight` / `Shutters` / `MonitorPower` / `MonitorBoot`×4 / `Fan1`）。
`lever_hooked=true` 挂的正是 `fireclickdetector` 与 `VirtualInputManager` 都要经过的那个信号。

**一条只活在「自证」里的读数**不会报错 —— 它给出一句**恰好为真**的话（窗口确实在那一刻开了），
而它**证明的是我的探针发出去了**，不是游戏收下了。

**反过来的用法才是它值钱的地方**：**按压计数对不上，就是探针本身坏了**。
这次 11 : 11 对上，于是「探针确实发了 11 发」这件事是**量出来的**，不是假设的。
**要证明服务器收下了，得用 `Workspace.Stats`**（服务端写、客户端复制）——
而它确实动了，一直烧到 9420。

## 471. 判据窗口比被测状态机短时，「没动」不是判决（Phase 113）

每一次按压都套着 `st0 -> fire -> wait(1.4) -> st1`，**每一次都回 `stats=[]`**。
而堆芯起来了、烧到 9420、熔毁了。**转变比那 1.4 秒慢。**

这与 §0.19 同族（`Heartbeat:Wait()` 回来了，推不出 `Connect` 的回调跑了）：
**「当场没动」是「我的窗口里没动」，不是「没发生」。**

**修法不是把窗口加大**（那只是把同一个猜测调大）—— 是**换一把尺子**：
记录器有它自己的**上游**判据（`COREGATE` / `SEAL` / `CLOCK`），
**几秒的一前一后差**永远量不过一个有自己的状态机、自己的时序的系统。
**哪一半验了、哪一半没验，分开写。**

## 472. `MaxActivationDistance = 0` 不拦 `fireclickdetector` —— 62 个里唯一的例外是**启动杆自己**（Phase 113）

`Consoles` 下 62 个 `ClickDetector`：**61 个 `6`，1 个 `0`**，而那一个 `0` 正是
`Consoles.MainReactorConsole.StartUpBigLever.StartClickPart`（110.4, 279.6, -0.7）。
实测那一按 `dist 5.16 of 0`，**堆芯照样起来了**。

官方文档对该属性只有一句：**「用来限制玩家离探测器多远之后就不再可点」** ——
它是**输入管线**上的闸门。`fireclickdetector` 直接触发信号，闸门在它后面，不在它前面。
（同族于 §0.2：探条只探它探的那件事 —— 我一度把「6」当成「这游戏的控制都够得着」的证据。）

## 473. 原版的熔毁是一个**冻结的终局**，而且带一份可以照抄的文案（Phase 113）

`SEAL shift over` 之后，两次间隔 79 秒的读数**逐字节相同** ——
`TemperatureVal 9420 / PressureVal 7320 / RadiationVal 406 / HDEF.IntegrityVal 99 /
OutputVal 144 / BreachVal false / GameActive false`，CBL 全退（`Active=false`、`TempVal 925`）。
监视器留在 `SHUTDOWN PROTOCOL` + `CORE COLLAPSE DETECTED ...` + **`REACTOR ENERGY QUOTA NOT MET`**
（最后这句说明结局不只是热崩溃，**配额也没挣到**）。

**这是复刻那一条失败路径的参照**：它不是一段动画描述，是一个**可以逐项复算的终局状态**
加一份**逐字可以照抄的文案**。**记住它是冻结的** —— 「还在降」和「停住了」在读法上不一样，
而这里两次采样就分开了。

## 474. 一条路径的「变化次数」先问它是不是**被整块重写** —— 打字机与 `NOISY`（Phase 113）

同一份 `TEXT` 通道里，两个**方向相反**的陷阱同时存在：

**① 打字机把 3 条消息写成 100 条事件。** `x.ScreenGui.HintText` 录到 **100 次变化**，
而它只有 **3 条消息** —— 原文是**逐字**打出来的（`The` → `The obj` → `The object` → …），
所以那 100 是**重绘次数**。我一度把「100」读成「100 个目标文本」。

**② `NOISY` 把 8 行写成 8 次变化。** 记录器对**每轮被整表重画**的路径打 `NOISY`
（`… changed 8 times in 8 polls`）：`SettingsFrame.ControlsTab.ControlFrame` 的 6 行按键表、
DRM 手册页、监视器故障页 —— 它们的「8 条事件」是 **8 行 × N 轮**的重画，不是 8 次改动。

**两个陷阱方向相反，错的却是同一个动作：把事件计数当成状态变化计数。**
规矩：**读一条路径的变化之前，先问它是不是被整块重写**（打字机 / 每轮重画 / 滚动列表）。
同族 §0.20（按边数给面分类，回答的是**文件格式**）、§0.21（分母里坐着被测对象）。

**最该记的一层**：记录器**早就替我把这两个标好了** —— `NOISY` 就是它的标记，
`HintText` 那串前缀也在盘上一眼可见。**工具给了信号，是我没先看它。**
「读数错了」和「读数没错但读的不是那件事」在盘上同形，只在**下一次被质疑**时分开。

---

## 475. 「工具能做那件事」≠「那件事在这里能做」—— 80 个工具里没有可用的输入原语（Phase 114）

difz 那台服务器暴露 **80 个工具**，其中名字带 `interact` 的只有一个：
`interact-prompts`，**参数只有 `range`（一个距离半径）**。
它的语义是「在半径内找 `ProximityPrompt` 并触发」——
而**全游戏 `ProximityPrompt` 数量 = 0**（`game:GetDescendants()` 全表扫过）。
于是它在这里**退化成 `fireclickdetector`**，而后者**早已被证否**（只在客户端本地响应，服务端收不到）。

**「工具目录里有一个动作」被读成了「这个动作在这里可行」。** 两句话差着一整次枚举。
判据只有一条：**那个工具的参数里，有没有「对谁」** —— 只有半径、没有目标的工具，
回答的是「附近有没有东西」，不是「把那个东西按下去」。
同族：§0.2（读实例，不读模块）、§0.18（错的量法不报错，它只安静地给你一个数）。

## 476. 一个目录里住着两种生命周期：**每轮重写**的和**只在启动写一次**的（Phase 114）

`Data/originalwatch/261011-084400/` 十三份产物，mtime 恰好分成两组：

| 每轮重写 | 只在 `Start()` 写一次 |
|---|---|
| `summary.txt` `audio_tally.txt` `suppressed.txt` | `alive` `hello` `inventory` `rooms` `tree` **`health`** **`window`** |

我拿 `window.txt` 的 `lever_hooked=false` 和 `health.txt` 的 `clock=(never read)`
当**当前的**故障，而它们是 **08:44 那一次的快照**；`clock=(never read)` **现在可证为假**
（同一个时钟读数我这一轮读了三遍）。

**陈旧读数和活读数在盘上逐字同形** —— 它们不像「文件缺失」那样会喊。
规矩：**报一个读数之前，先看它的 mtime 和它兄弟的 mtime**；
一份产物如果**只有它自己在停在旧时间上**，那不是数据在说事，是**写它的人早就不写了**。
这不能推出「读数是错的」，只能推出「**它不是关于现在的**」。
（同族 §0.18、§0.20：问错了对象，会得到一个响亮的数。）

## 477. 工具集说的「这里」和跑我脚本的「这里」可以**不是同一个 place** —— 两句话各验一遍（Phase 114）

同一次会话里同时成立：

- `execute-script` 里读 `game.PlaceId` = **17596243941**（原版）、`RunService:IsStudio()` = **false**、
  `ServerScriptService:GetChildren()` = **`{}`** —— 脚本在**原版的 Player 客户端**里跑；
- `take-screenshot(workerId=…)` 拍回来的是 **Studio 的窗口**（"The Reactor [Rebuild]"），
  `list-roblox-processes` 把同一个 workerId 映到 Studio pid `11412`、同时报 `player: RobloxPlayerBeta`（pid `7688`）。

**没有任何一条错误提示说这件事。** 两边都「成功」了，只是成功的是两件事。
所以**凡是要靠「我说的是哪个 place」下结论的，都必须在那条通道内部自证**
（读 `PlaceId` / 读标记 / 读一个只在一侧存在的容器），
**不能拿另一条通道的返回当同一件事的证据**。§0.2 说的是「读实例不读模块」，
这一条是它的**跨通道版**：读**同一通道**里的实例。

## 478. 「这是不是一块活的分钟表」要靠一段**可比的斜坡**，单点读数答不了（Phase 114）

监视器上那个 `11:50 PM`：单看它是**一个数**，停着还是活着**它自己不说**。
能把它判成**活的**的是第一轮那条斜坡 —— `11:53 → 11:54 → 11:55 PM …… 12:00 AM`
（`EVT3323/3330/3338` 一路到 `EVT3401` 才 `GameActive=true`）。
**是那条斜坡把「分钟表」这个身份定的性**，有了身份之后，这一轮的 `11:50 PM` 才**敢**读成「停」。
两条随附纪律：
**① 判「停」也要有斜率** —— 32 分钟的**两个端点**是斜率，单张截图不是；
**② 「上一轮它不会自己复位」不能直接搬到这一轮** —— 那是**旧服务器熔毁之后**量的，
这一轮是**新服务器停在休息屏**，状态不同，结论不继承（同 §0.21 第 3 条：外推要当场标成外推）。

## 479. 丢掉一个样本和一整个通道挂掉，在输出文件里**长得一样**（Phase 114）

间隔采样 12 次，**只有 6 次落进文件**，另外 6 次那一格只写着一个 `{`。
原因**定死了，而且很小**：我的提取写的是 `head -1`，而**同一个工具偶尔会把响应漂亮打印**，
漂亮打印的第一行正好是 `{`。把提取改成**先把换行抹掉再找 `{"success"`**，
同一状态、同一工具、下 8 次 **8/8 全中** —— **一次都没丢**。
（不是「隔一次坏一次」：同一秒里连打两次可以两次都成，所以它**不是**一个可预测的节律。）

**所以那个 bug 是提取器的，不是工具的** —— 而这一条的要害**恰恰**在这儿：
我一开始把它当成「工具不稳定」，差点去换通道。

**要害不是那个 bug，是它在文件里长的样子。**
一个错字 `{`、一个 `PARSE_FAIL`、和一拍**真的什么都没发生**，
在一份 TSV 里**都是「这一拍没有数」**。于是
**「12 拍里 6 拍是停的」和「12 拍里 6 拍没采到」读起来一模一样**，
而前者是结论、后者是缺失。

规矩：**采样器必须自己报产率**（采到 / 采丢），并且**丢掉的格子要写一个显眼的符号**
（我这一轮是**自己数行数**才发现少了一半 —— 工具没告诉我）。
同族 §0.17（脚本必须自己报告自己的死因：`task.spawn` 里「在跑但没事发生」和「第一拍就崩了」
外面看一样）、§0.18（错的量法不报错）。
**「采样跑完了」和「采样采到了」是两句话。**

---

## 480. 给一个**不存在的名词**写设定：先量它存不存在；查不成的那一格要**改证据数**，不能装作查过（Phase 115）

**事件：** 用户丢过来一个全称加缩写 ——「Subspace Radiation Suppression Unit - S. R. S. U」，
说「你给他添加点设定」。**这串字母在本项目里从未出现过。**

**第一件事不是写，是量。** 三处查：仓库（0 命中）、Wiki 快照（0 命中）、
原版实例（**没查成** —— `:28429` 拒连，`URLError [WinError 10061]`）。
前两处是同方向的证据。**「我没找到」和「它不存在」不是同一句话**，
但两份独立来源都空，足够支撑「它是新造的」这个判断。

**要害在第三格。** 一次**跑不成**的检查不会留下任何痕迹，而它和一次
「查过了、没有」在笔记里**长得一模一样**（§0.17 / §0.20 / §0.21 全族）。
所以两条：
**① 结论要写明它由几份证据撑着** —— `docs/SRSU.md` 抬头与 `QUESTIONS.md` S1 都写
「两份，不是三份」，并留了「你知道原版里其实有的话说一声」的入口；
**② 没查成的那一格要写得像没查成** —— 带错误码，不带形容词。

**第二件事：把「新的」写在文件里。** 一个名词的出处不写下来，半年后没人分得清它是
**复刻**还是**新造** —— 而这个项目里两者的处理方式完全相反（复刻要逐字对齐原版，
新造只要自洽）。所以 `docs/SRSU.md` 抬头第一段就是出处与那三次扫描的结果。

**第三件事：一份「提案」必须看起来像提案。** 设定写到后面势必要给数值，
而数值一旦和**实测的公式**并排排好，**下一轮的我就会把它当成现成的**去接代码 ——
§0.18 那次错的量法只是**给错一个数**，这次会变成**错的机制**。
所以 §7 整节的标题里就有「**提案，不是实测**」；我选的常数标「选的」，
对齐实测的常数标「对的是实测值」；最后还写了一条硬约束
（**接入也不该让 S.A.M.O.S. 永远可用** —— 那会抹平一条现成的难度线，
而 `SAMRadiationLimit = 600` 正好卡在 State 4 的裸辐射值 `120×5`，那是设计不是疏忽）。

---

## 481. 射线回答的是**它打到的那一件** —— 六条射线读到同一个数，可能是六件东西（Phase 115 附录）

**事件：** 量他新装的一圈 `BottomSuppressionStructure` 时，我从堆芯轴水平打了六条射线
（30/90/…/330°），六条**全在 55.70–55.82** 停住。我当场把它读成
「腔体内壁在 r ≈ 55.76」，并准备写进文档。**它是错的。** 只多打了一条、
把 `GetFullName()` 打出来，才看见那六条各停在**六台不同的
`RadiationScrubberUnitMK2` 的玻璃**上（`Workspace.Folder.WithinCore.…`，高 36.90，
比我要量的那圈还高 2 stud）。**要量的东西一直没被射线碰到。**

**四条：**

**① 射线给的是「第一个挡路的东西」，你要的那个东西得自己认。** 量几何就**先把命中的
实例全名打出来**；只打距离的那一行，和量对了的那一行**在盘上逐字同形**。

**② 六个相同的读数不等于一个物体。** 正因为它们**同族**（六台同型号设备按同一半径排成一圈），
「六条射线一个数」才读起来像「一堵墙」。**同族件是这个错的放大器** ——
换成六面不同的墙，我当场就会看出来。

**③ 一句话里只要有一半是从数里推断的，就要把那半标出来。**「玻璃在 55.76」里，
「55.76」是量的，「玻璃」是量的，**「它是腔体的壁」这一层什么都没有支撑** ——
而错的正是最后一层。写结论时把**能直接量到的名词**放前面，推断的那层另起一句。

**④ 同一个探针里的另一个数也是这么来的：径向范围。** 我拿「包围盒半对角线 ± 半径」
去算某件伸到哪，于是**一根 38.79 长的切向主梁**被算成「伸进 r ≈ 32」。
那是**量法**的产物，不是几何。能站住的只有两句话：**本体在 r = 54.35，屏蔽板在 r ≈ 57**。
（§0.18 家族：错的量法不报错，它只安静地给你一个数 —— 这次一口气给了两个。）

---

## 482. 「带小数点的角度」不是一个数集 —— 314 个是浮点尾巴，5 个是真的角度（Phase 116）

**事件：** 用户让把 place 里所有带小数的角度取整。扫出来 **319 个**。
如果汇报停在那句「319 个都有小数点」，这句话**在盘上、在汇报里都成立** ——
而它把两件事混成了一件：**314 个只差 0.001°**（浮点尾巴，改完肉眼不可见），
**5 个差 0.011°–0.262°**（真实的角度差 —— 最大的一次是 `Workspace.Folder.RoofSupport`
被转了 **0.262°**）。取整这个动作对两者一模一样，**但「我改动了什么」对两者完全不同**。

**三条：**

**① 一个筛选条件回答的是「谁符合」，不是「有多大」。**「有小数」是**二值的**，
而这次真正的量是**差多少度**。分桶之前，314 件和 1 件一样大。

**② 批量改动必须报「最大的一次动到哪一件」。** 用户要的是「取整」，
他没有同意「把 `RoofSupport` 转 0.262°」—— 那件事一共 5 件，**说得出名字**。
（§0.21 第 3 条：外推 / 批量类结论当场标出边界。）

**③ 阈值低于平台自身噪声的检查器，第一次就撒谎。** 我用 `> 1e-6 stud` 判「位置动了」，
于是**空操作写入**（把每个部件写回它自己的 `Orientation`）也报出 2 个「动了」，
最大 **1.907e-06**。**这就是 §0.0 那条「永远红的检查就是噪音」的同一件事**：
判据要比被测平台的固有误差**高一个量级**，否则第一个报出来的永远是噪声。

**连带：** `Orientation` 的语义是绕**自身中心**旋转，`Position` **定义上**不参与 ——
拿位置去验一次角度改动，**量的是别的东西**（同 §0.21：选错了验证面 / 分母，
数照样响亮）。这次能立刻看穿，只是因为多跑了一次对照实验；**没有对照实验的话，
那句「1 个部件移动了」就写进文档了。**

---

## 483. `Orientation` 在 `BasePart` 上是**存的**，在 `Attachment` 上是**算的** —— 同一个请求，一边做得到一边做不到（Phase 116 第二轮）

**事件：** 用户说「继续修复」→ 选了「继续清浮点小数」。角度那一轮很干净
（319 个 → 残留 0），于是我以为**所有** 1e-5 量级的小数都是同一件事：
写个整数值进去，它就整了。**不是。** `Attachment.Orientation` 那半边，
**210 个写进去，重读还剩 126 个是小数**，而且**再跑一次一模一样的判据，落点一模一样**
（126；`Weld`/`Motor6D` 的 `C0`/`C1` 旋转是 33）。

**定点就是证明。** 两次同样的判据落在同一批值上，说明**不是方法脏** ——
是那个数**在那个属性上表示不出来**。

**对照实验（一次就分清了）：** 在 `ServerStorage` 里搭一个临时 `Part` + `Attachment`
（不渲染、不进世界、用完 `Destroy()`），写进同一组角：

| 写进去 | `Part` 读回 | `Attachment` 读回 |
|---|---|---|
| `(17, 23, 41)` | **17.00000000  23.00000000  41.00000000** | 17.0000038  **23.0000019**  41.0000000 |
| `(0, 180, 0)` | 0  180  0 | **-0.0000000  -179.9999847**  0 |
| `(90, -115, 0)` | 精确 | 精确 |
| `(0, -20, 0)` | 精确 | 精确 |

**四条：**

**① 动手之前先问：这个属性是「存的」还是「算的」。** `BasePart.Orientation` 是**存储**
（写进去是那个值，读回来还是）；`Attachment.Orientation` 是它的 `CFrame`
**矩阵的一个分解**（float32），而对称整数角**大多不在可达集合里**。
**「取整」这个动作对存量是幂等的，对视图量不是。**

**② 什么能精确、什么不能，有规律，规律藏在矩阵里。** 90 的倍数两边都精确
（矩阵里的 0 和 ±1 在 float32 里是精确的）；`(17, 23, 41)` 这种就不行，
误差恰好是 **1.5e-5 = 2⁻¹⁶** —— 一个 ULP。**看到误差正好是 2 的整数次幂，
就该怀疑「表示精度」而不是「我的算式」。**

**③ 「清小数」这类活的边界要按属性报，不能按部件报。** 同一个 `ConnectionNode` 里，
`Part` 的位置/尺寸能清到 0 残差，它身上的 `Attachment` 清不到。
按部件汇报会写出「这一台清干净了」这种**整体为真、逐项为假**的句子。

**④ 证法要便宜到可以随手做：临时件搭在 `ServerStorage`。** 不渲染、不进世界、
用完 `Destroy()`，**世界上一个字节都没动** —— 于是「A 能、B 不能」是一次**实验**，
不是一次推理。这是 §0.2 的正面形态：**让被测对象在一个你能读回来的地方活一次。**

**连带（同一轮量到的）：** `BasePart.Position` 上**一个可清的尾巴都没有** ——
5,470 个部件里只有 **4 个**坐标是整数，其余是继承来的 0.1–0.5 的小数。
所以「位置取整」**不是清小数，是把整座设施吸到整数网格上**（每个部件最多挪半个 stud，
接缝会被顶开）。**同一个词（「清小数」）在两个属性上指的不是同一件事** ——
先量分布，再决定动不动（§0.21 第五张脸的同族）。

---

**484. 「清不掉」和「本来就整」从计数上看是同一个 0**

第三轮（同一天，用户「再修」）又扫了两个属性类，得到两个都是 **0** 的读数：

- `Model.WorldPivot` 的**旋转**：写 107、回来 **106**（第三遍同样的判据仍是 106 —— 定点）。
- GUI（全 place 的 `GuiObject`）：`UDim2` 的四个数、`AnchorPoint`、`Rotation`、`TextSize`
  —— **每一项都是 0**，而我**一个字节都没改**，它**本来就整**。

**两个 0 在报告里长得一模一样，含义相反**：一个是「我试过、它被平台退回来了」，
另一个是「这里从来没有问题」。**计数只回答「还有几个」，不回答「为什么没有」。**
所以每一轮清点的汇报里，**改过又退回来的**和**没动过就是整的**要**分开列**，
否则下一轮的人会把「本来就整」也当成一个已经打完的仗，或者更糟 ——
把「清不掉」当成「已经清干净了」。

**顺带把 483① 升成通则：** 现在有三个同族的例子了 ——
`Attachment.Orientation`（126）、`Weld`/`Motor6D` 的 `C0`/`C1` 旋转（33）、
`Model.WorldPivot` 的旋转（106）。**它们都是 `CFrame` 矩阵的分解，不是字段。**
能取整的只有 `BasePart.Orientation` / `Size` 这种**存字段**的属性。
判据不是「难不难」，是「**它在 DataModel 里是存的还是算的**」。

---

**485. 射线答的是碰撞体，不是画面 —— CSG 做出来的「环」，射线量出来是实心盘**

**事件：** 12 个 `UnionOperation` 环建完，我用一条横穿盘面的射线验收：
在半径 `rho` 处打一条水平线，期望「rho 落在第 k 圈里就只命中 `Ck`」。读数却是
**每一处都先撞到 `C12`，然后 `C11`、`C10`……** —— 看着就是 12 块实心盘叠在一起。
**我差点据此把这批环判成废品重做。**

**真正的原因：union 的查询几何是它的凸包。** `PartOperation` 的 `CollisionFidelity`
默认落到 `Hull` 那一侧，而**一个环的凸包恰好就是一块实心盘** ——
射线回答的是「碰撞体占不占这里」，我问的是「画面里这里空不空」。**问题问错了面**（§0.18 第四张脸）。

**推翻它的是一张图：** 把 12 个环设成红蓝相间、不透明，从炉膛上方俯拍 ——
**12 圈同心色带，一圈不少，中间是空的。** §0.14b 那句再对一次：
**读数的错是安静的，图的错是响的。**

**同一族里同一天还犯了两次：** ① `Part.Shape = Cylinder` 的**轴在局部 X**，
我却拿 `UpVector` 判「这 12 个环平不平」，于是 12 个环全报「不平」（应该查 `RightVector`）。
② 给 union 上色不生效（见 486），而第一反应同样是去怀疑几何。

**三条纪律：**
**① 量「有没有洞」不许用射线** —— 要么看图，要么先把 `CollisionFidelity` 改成
`PreciseConvexDecomposition`。**默认值也是一次选择，只是没人替你写下来。**
**② 每次量之前先问一句：这个查询答的是哪一层？**（碰撞体 / 渲染体 / 存字段 / 算出来的视图 ——
后者同 483。）
**③ 代价可能是零，读数照样骗人。** 这 12 个环 `CanCollide=false`、`CanQuery=false`，
碰撞体是什么形状**在游戏里毫无影响** —— 但它是**我的尺子**，而且给了一个很确定的数。

**附带：** `UsePartColor` 那件事的干净证法是 `MeshContent`（直接从网格顶点量最小半径，
实心盘会有顶点落在半径 0 附近，环不会）—— **但 `UnionOperation` 没有 `MeshContent`**
（那是 `MeshPart` 的属性），这条路当场断了。**便宜的证法被平台没有的东西挡住时，
换一条更便宜的（截图），不要改道去做更贵的推断。**

---

**486. `UsePartColor = false`：`Color` 写得进去、读得回来、渲染时被无视**

**事件：** 12 个环设成红蓝相间（`Color` 一奇一偶、`Material = Neon`、`Transparency = 0`），
截图**整盘是白的**，一点红蓝都没有。我第一反应是「CSG 那一步是废的」。

**真正的原因：** `PartOperation` 出生时 **`UsePartColor = false`**，此时它用**烘进网格的颜色**
（来自 CSG 的输入件 —— 两个默认灰白的 `Part`），`Color` 属性**照写、照读、不参与渲染**。
设 `UsePartColor = true` 之后，同一张图立刻是 12 圈红蓝。

**这是 §0.2 / §0.15 的同一张脸：写成功 ≠ 生效。**
写下去不报错、读回来是对的、唯一的证人是**画出来的那一张图**。
（§0.2 是「读到的是另一个 VM 的空表」，§0.15 是「读到的是旧版模块」，
这里是「写进了一个没人看的字段」—— 三件事的共同点是**中间那一步不报错**。）

**纪律：给 `PartOperation` / union 上色，第一件事是 `UsePartColor = true`。**
**判断依据同样是「存的还是算的」**（同 483①）：`BasePart.Color` 在普通 `Part` 上是存的，
在 union 上被 `UsePartColor` 这个开关**接管**。

---

**487. 「把一块盘切成 N 个环」这笔账，以及为什么静止透明度存 0.4**

**为什么是 CSG：** Roblox 没有 ring 图元，三条路 ——
**① CSG 减**（`GeometryService:SubtractAsync`，一圈 0.02 秒、12 个件、精确贴合）；
② 一圈一堆小件拼（r=60 的周长 377 stud，1 stud 一段就是 377 件/圈，太碎）；
③ Blender 出网格再导入（**最后一公里走不通**：上传要凭据，§0.6）。
选 ①。

**代价一：边是正多边形。** `Part.Shape = Cylinder` 的截面是 24 边形，
r=60 处的弦高误差 **0.51 stud** —— 最外两圈近距离能看出直线。
大盘那个 `MeshPart` 是光滑的圆。**接受**，因为静止时它半隐（0.4）、
闪白那一下它的身份是「光」不是「边」。

> **【2026-10-11 更正（Phase 118）】上面那句「大盘那个 `MeshPart` 是光滑的圆」是错的。**
> 量下来它有**恰好 18 个角度**（10°、30°…350°，间隔 20°）—— 它本来就是 18 边形。
> 也就是说 24 边的 CSG 环**比大盘本身更圆**，这一段代价我按**相反的方向**估了。
> 附带：`Cylinder` 的截面是不是 24 边形，我当时也是当常量用的（见 492）。

**代价二：圈数就是分辨率，而且写进了名字里。** 12 圈 = 每圈 5 stud，波峰跨 2–3 圈。
几何件的名字是 `C1`..`C12`，脚本里还有 `RING_COUNT = 12` ——
**改圈数 = 重建几何 + 改常量**，不是改一个数。**这是选 12 的价，写在这里免得下次忘。**

**代价三：波跑在服务端。** 与那个特效自己的 `Script` 同级同类型（服务端），
所以核弹那边接一次波就是一行 `rig.Play:Fire()`。代价是 CFrame 变更会复制给所有客户端
—— 这是 Roblox 服务端特效的常态（那台特效自己也用 `Tween` 这么干），
而且加了一条「只在真的动了才写」的护栏：静止的那些帧一个字节都不发。

**静止透明度存 0.4，是个有意的折中：** 编辑模式下脚本不跑，
**盘上存什么就是什么** —— 所以「静止时看起来怎样」只能靠**存**，不能靠脚本。
存 `1`：他打开工程什么都看不见，很可能以为我没做；存 `0.4`：看得见 12 圈同心环。
选 0.4，并且在汇报里写明「不想常显就把 12 个 `C*` 的 `Transparency` 设成 1」。
**「脚本能管的那一半」和「只能存的那一半」要分清楚**（同 484 的精神）。

---

**488. 「写不进去」是**那种件的权限**，不是那张网格的毛病 —— 判据是**新建一个空的同款件**（Phase 118）**

`MeshPart.MeshContent` 赋值回的是
`The current thread cannot write 'MeshContent' (lacking capability NotAccessible)`。
一句话里没有主语，于是只有一个便宜的问法：**这是拒绝这张网格，还是拒绝这一类件？**
判据是 `Instance.new("MeshPart")` —— 一个空件一样拒绝。

**能走的路只有一条：** `AssetService:CreateMeshPartAsync(Content.fromObject(em))`，
而且它返回的件**直接持有那张 `EditableMesh` 本身**：抬一个顶点、再从**件自己的
`MeshContent`** 读回来，读到的是抬高的值。**「我改的那张表」和「件里真的是那张表」
是两个问题**，这里量的是后者 —— 这个判据在 Phase 118 被写成了常驻自检
（PaletteKit 那套「测量留着」的做法同源）。

**489. 上游换人了 ≠ 我该重建 —— 6 次重建把可编辑网格的预算耗到「连自己读回来都是 nil」（Phase 118）**

这个 place 开着 `StreamingEnabled`：`Wave` 在客户端会被**送走再送回来，而且是另一个实例**
（同一段时间服务端三次采样 `GetDebugId()` 完全相同 —— 所以这不是服务端在动它）。
旧版一见 `part.Parent == nil` 就 `sheet = nil; builtSegments = -1`，下一帧重建 1800 个顶点。
那一轮重建了 6 次，然后**连 `CreateEditableMeshAsync` 读回这张网格都返回 `nil`**。

**教训不是「流式会换实例」（§0.2 早写了），是「我的重建条件写在了别人的生命周期上」：**
薄片需要圆盘的只有两样 —— **外形**和**站位** —— 而这两样都在它出生那一刻就拷走了
（`Size = MeshSize`、`CFrame` 每帧跟一次）。**圆盘走了波照跑，圆盘回来了再隐它一次；
只有薄片自己没了才重建**（那意味着整个 rig 被收走）。
修复后的对照读数：`built` 只出现一次，`disc=0`，跑满 120 秒。

**消费方要能区分「等」和「崩」**：`makeSheet` 在没有圆盘可依据时返回 `nil` 并写一行
`live("... no disc to stand in for at this moment")` —— **等待和失败都要有名字**，
否则「安静地不做事」和「一帧就崩」从外面看一模一样（同 §0.17 那条）。

**490. 快照尺寸：`MeshSize` 是**建件那一刻**量下来的，`Size = MeshSize` 才是恒等映射（Phase 118）**

`MeshPart` 渲染时按 `Size / MeshSize` 缩放。而一个**生下来就是平的**网格，
它的 `MeshSize.Y` 快照到引擎的 epsilon **0.001** —— 于是 `Size.Y = 0.25` 就是
**250 倍**的 Y 拉伸，屏幕上是一台**火山**，围着直径 650 stud 的坑口。

两条一起做才算修好：**① 网格生下来就是 0.25 stud 的板**（`±0.125`）；
**② 建完立刻 `Size = MeshSize`**（X 是 118.1769 而不是 120 —— 18 边形的**对边距**
`2·60·cos10°`，这个数就是「它真的是个 18 边形」的第二个证据）。
**「尺寸」这种东西如果是快照，那它就同时是同义词陷阱和单位陷阱**（同 0.18 那一族）。

**491. 一次「读回来说是平的」有两种来源：**竞态**和**真的是平的**（Phase 118）**

同一个 Play 会话里两次读到「平」：
① `ymax=0.12`（正好是 `HALF`，全平）—— 那是**重建后的第一帧**，`install()` 把 `heights`
清成 0，`applyHeight` 要下一帧才写；
② 三连采样 `no mesh` —— `FindFirstChild("WaveSheet")` 落在「旧的已 `Destroy`、
新的刚 `Parent`」之间。

**两种都不是缺陷，而两种都和「真的平了」逐字节同形。** 分开它们的不是读数的形状，
是**采样落在生命周期的哪一格** —— 所以要么读件的**自述**（脚本把 `heights` 印出来，
再把件里读回的最大值并排印出来，见 Phase 118 的 `the part itself holds` 那行），
要么给读数配一个**时间**。**没有时间戳的「平」不能当证据。**

**492. 「本质上就是 18 边形」是**量得到**的用户判断 —— 量到之后还要定「哪一半连续」（Phase 118）**

用户说他画的盘「本质上就是 18 边形」。这是可以量的一件事实：网格在半径 100 处有
**恰好 18 个不同角度**（10°、30°…350°，`360/18`，间隔 20°），件 `Size 120` 缩放 0.6
→ 世界半径 60。**他对了，而 Phase 117 的我写「大盘是光滑的圆」** ——
用户的形状判断在我的读数之外，它不该只被当成一句观感。

**但「18 边形」不能直接翻译成几何**，它同时说了两件事，得分开：**楔面是硬的**（18 个），
**径向的运动是连续的**（不是 18 级台阶）。做法因此是：**每个楔的两个角点各自复制顶点**
（边才硬），每帧只改 `SetPosition` 的 **Y**。
**一句话里往往有「离散的那一半」和「连续的那一半」，先拆开再建东西**（同 0.18 第五张脸：
一个词如果替你做了选择，你读到的就不是测量 —— 这次是它的正面用法）。

---

**493. 「改主意」不等于「删掉上一版」—— 一个属性挂两种运动，顺带：**共享的数值属性**是延迟的陷阱（Phase 118 第二轮）**

用户看完 Phase 118 那张薄片，改要「从中间上下动 ±1，到边缘衰减到不动」——
**这是另一种运动，不是把上一种调一下**（行波：鼓包走到哪抬到哪，处处同高；
呼吸：整张网同步上下，靠半径衰减）。
没有把行波那段代码换掉，而是加了 `Motion`，**`"pulse"` 与 `"wave"` 并存**。
理由不是「保险」，是 §1.4 第 2 条：**没有替代品就不要删** —— 而这里连「替代品」都不算，
是**两种要的东西**。同一族的先例：12 个 CSG 环也留着没删（只是用**另一个**开关停用）。

**共享的数值属性是延迟的陷阱：** `Amplitude` 这个名字**同时**被 12 环那个旧驱动读。
今天无害（它 `Enabled = false`），但**明天谁把环打回来，两个驱动就会抢同一个数**。
开关那件事我在 487 之后已经学乖了（`Enabled` / `WaveEnabled` 分开），
**数值属性还没学乖** —— 写在这里：**下一次给新驱动加参数，先查一遍同名的属性有谁在读**
（`rig:GetAttribute` 的调用点全在这个 rig 的脚本里，查一遍是一分钟的事）。

**494. 「不动」的判据是**两次读数之差为零**，不是「数很小」（Phase 118 第二轮）**

「到边缘衰减到不动」这句话里，**「不动」是一个关于时间的事实**，而一个瞬间的读数
说不出任何关于时间的事 —— `+0.004` 可能是「静止但没归零」，也可能是「正在经过零点」，**长得一样**。
所以量法是**同一个顶点隔一段时间读两次**：

```
A rim y = -0.1250 .. +0.1250   centre top y = +0.831
B rim y = -0.1250 .. +0.1250   centre top y = +0.835     <- 第四位逐位相同
```

**另一半是让「零」真的是零：** 包络用升余弦 `0.5·(1 + cos(π·r/RADIUS))`，
在 `r = RADIUS` 处 `math.cos(math.pi)` 在双精度里**就是 `−1`**，
所以那一圈的高度是**逐位的 0**，不是 `1e-7` 那种「小到看不见」。
区别不在今天好不好看，在**下一次缩放**：薄片半径从 60 改成 600 时，
`1e-7` 变成 `1e-6` 仍然看不见，但**任何一个「大致为零」的写法都是一个还没被决定的数**
（同 0.18 那一族：**错的量法不报错，它只安静地给你一个数**）。
顺带一个**更强的断言**：`h[12]` 在五次采样里**每次都正好是 `h[0]` 的一半** ——
升余弦在半半径处是 0.5，所以这一条同时钉住了**衰减的形状**，不只是「在衰减」。

**495. `Instance:GetAttributes()` 在这个助手的沙箱里**回空表** —— 名字问得出来，枚举问不出来（Phase 119）**

同一个对象，`rig:GetAttribute("Motion")` 回 `"wave"`，而 `#rig:GetAttributes()` 回 **0**、
`rig:GetAttributes()[1]` 回 **nil**（`pcall` 都是 `true`，所以不是抛错，是**空**）。
`typeof` 说它是 `table`。也就是说：**「这个件没有属性」和「这个探条枚举不了属性」长得一样**。

这是 §0.2 那一族的第一百次换脸：**你问的工具永远只回答它被问的那一件事**，
而"没有"和"拿不到"在屏幕上逐字同形。
**规矩**：读属性**按名字读**（`GetAttribute(name)`），别把 `GetAttributes()` 的返回当成"件上有什么"的普查；
要证明某个属性**不存在**，得先证明枚举本身是好用的（拿一个**已知存在**的属性当阳性对照）。

**496. 「只是停用、随时能恢复」是一句**有保质期的断言**（Phase 119）**

上一轮我交付薄片时，把 Phase 117 那 12 个同心环停在盘上、写进文档：「停用不是删除，
把 `Enabled` 打回 `true` 就能回来」（§1.4.2「不能在没有替代品的情况下删功能」的做法）。
**这一轮复查，那 12 个环已经不在 DataModel 里了** —— `Workspace` / `ServerStorage` /
`ReplicatedStorage` 三处搜 `C1`/`C12` **各 0 个**；`ShockRipple` 的兄弟只剩
`Cylinder2` + 18 个 `Neon` + `Ring` + `Script` + `Union`。

**不是这个脚本删的**（`shock_ripple_client.luau` 里没有一处 `Destroy` 打在它们身上），
也不是这一轮删的 —— **是别处、别的时间删的，没有任何信号**。
`Enabled=false` 和 `Rig`（4038 字节的服务端驱动）都还在，所以**盘上的字全都是对的，
只有世界不在了**。

为什么这条值得单列：**「留一个开关」是一个关于未来的承诺，而承诺的对象可能在某天被第三方删掉。**
- 写「只是停用」的时候，**顺带写下怎么验证被留的东西还在**（一句 `GetTagged`/`FindFirstChild`
  的存在性检查就够）—— 否则那句承诺会一直读起来像真的；
- 复查时**先量对象还在不在，再读开关的值**。我这一轮本来只是去改属性，
  顺手量了一下 children —— 如果没量，我会继续在报告里承诺一个已经不存在的能力。

**497. 给行波加衰减：**差**是量出来的，单个数不是（Phase 119）**

用户要在行波上加衰减。做法是给两支共用的包络加一个指数
`envelope(r) = (0.5*(1+cos(pi*r/RADIUS)))^Falloff`，`Falloff = 0` 时是恒等 ——
**所以旧那版「全程满高跑到边上」没有被删掉，它变成了 `Falloff` 的一个取值。**

验收**不能只报衰减版的那三个数**：`max h[12] = 2.49` 既可能是衰减，
也可能只是「鼓包本来就只长到 2.5」—— **一个数不说明任何事**。真正的证据是 A/B，
同一套 `Amplitude / Speed / Period / Width`，**只动 `Falloff`**：

```
Falloff=1   max h[0]=5.00   max h[12]=2.49   max h[24]=0.00
Falloff=0   max h[0]=4.99   max h[12]=5.00   max h[24]=4.98
```

**差（5.00 → 2.49）就是那个乘数**，而且它正好等于「半半径处 = 一半」——
和呼吸那一轮量到的形状是同一条曲线。**改一个数、其余全不动，是把"因果"和"相关"分开的最便宜办法。**

**顺带的第二个读数：行波和呼吸靠「先后」分开，不靠「多高」。** 两者每环的最**高**值可以完全一样
（形状相同），差别在于行波是**中间先到峰、边上后到峰**，呼吸是三环**同时**到峰。
所以量行波要采**时间序列**（这次 22 s / 每 0.5 s），量呼吸只要采**一次形状**。

**498. 同名兄弟：`Instance.new` + `Parent` **不会顶替旧的** —— 我把第三个客户端脚本塞进了第二个（Phase 119）**

注入新版本时我写的是一段"先 `FindFirstChild` 看看旧的有多大，然后建一个新的"。
**`Instance.new("LocalScript")` 从来不会让旧的走开** —— 它只是让 `StarterPlayerScripts`
底下出现**第二个**叫 `ShockRippleClient` 的东西。于是：

```
bytes=25193 ... "replacing old 23177" | now bytes=23177     <- 读回读到的是**旧的那个**
```

哈希是对的、写入是成功的、`WaitForChild` 也"找到了" —— **三个信号全绿，而盘上的呈现是假的**。
这是 §0.22（Roblox 允许兄弟重名）和 §0.14 的正面撞车：**同一个名字在这个引擎里不是一个身份。**

**规矩**：写一个"替换"之前先**枚举同名件并逐个处理**，写完**回头数一遍**
（`found 2 | [1] 23177 | [2] 25193 → left=1 bytes=25193 hash=…`），
别拿 `FindFirstChild` 的返回当"现在盘上是什么" —— 它回的是**任意一个**。

**499. 「同一首曲子」有两个文件，而它们**结构不一样** —— 对齐点必须按**要用的那一份**重测（Phase 120）**

我照着 `ReactorStartup_Remix.mp3` 量出「静音 10.30→16.20、+18.8 dB @ 16.20」，
把整部片子的时间轴（推黑 9.70、点火 16.20）都搭在这套数上。操作员一句
「**音乐选 reactorstartup 不是你做的，是最开始的那个**」把地基掀了 ——
`ReactorStartup.mp3`（原版）**只有开头一处静音**（0.00→2.25 s，之后 263.9 s 不断），
声音回来的那一秒是 **2.30 s（+34.5 dB）**，和 Remix 的 16.20 差了 13.9 秒。

**教训不是「我量错了」，是「我量的对象不是交付的对象」。**
两个文件名只差一个 `_Remix`，时长只差 3 秒（263.9 vs 266.9），**在盘上长得几乎一样**；
但**静音段的位置和长度完全不同**，所以「以它为对齐基准」这件事**整个作废**。
**量一个同步点之前，先确认你量的是要交付的那个文件**（同 §0.2「探条只探它探的那件事」）。
换文件 = **换一把尺子**，不是换个数字。

**顺带的做法**：原版的静音只有 2.25 s，而片子要 6.5 s —— 于是**拼**：
把原版从它自己起声的 2.30 s 截起走 9.7 s，插 6.5 s 真静音，再从原处接回去。
两段首尾相接（`2.30→12.00` 接 `12.00→71.80`），所以**只有一次「没声音→有声音」**，
落在点火帧（成品实测 `SILENCE 9.70..16.20` / `+33.6 dB @ 16.25 s`）。
**〔2026-10-12 补记：后半句那个 `+33.6 dB` 本轮复现不出来，见取舍 507 ——
它留在这里，取代它的是 `silencedetect` 的 9.693→16.201 和跨点火那两个窗。〕**

**500. 每镜各自淡出 = 每切一刀黑一帧；**要重叠的窗口**才是溶（Phase 120）**

透明度写成 `ramp(p, t0, t0+XF) * (1 - ramp(p, t1-XF, t1))`：上一镜在 `[t1-XF, t1]` 淡出、
下一镜在 `[t1, t1+XF]` 淡入。两个窗口**不重叠**（A 恰好归零时 B 才起步），
于是切点那一帧**两镜都是 0** —— 12 个切点各黑一帧、前后各 0.45 s 变暗。
**这看起来像「刻意的黑场剪辑」，其实是把「淡出」写成了「先淡出再淡入」。**

修法：**让两个窗口都跨在切点上**（`[t0-XF, t0+XF]` 和 `[t1-XF, t1+XF]`）。
相邻两镜的 `t1 == t0`，所以两个 ramp **落在同一区间、互为补数**，合成恒等于 1。
**判据是「切点处的和」**：探条 `sum=1.00 | max=0.50`（两镜各半）对，`sum=0` 就是黑了。

**这条是「抽帧抽出来的」，而且差点被抽帧自己骗过去**：我在成品 mp4 上每隔几秒抽一帧做
contact sheet，结果一屏黑 —— 因为我抽的 12 个时刻**恰好每个都落在切点**上
（每镜 4.44 s，我按 3 秒步长抽，正好踩中)。**一个「全部黑」的结果先要问「我抽的是哪几帧」。**
（同 §0.20：问错了问题也会得到一个响亮的答案。）

**501. Windows 不会删掉一个被某进程当作工作目录的目录 —— `rmSync` 会回 EPERM（Phase 120）**

全量渲染死在 `FAIL EPERM, Permission denied: ...\_tools\_frames`。**不是权限坏了**：
那一次的会话 shell 的工作目录**恰好就是 `_tools/_frames`**，而 Windows 拒绝删除
任何进程当前所在的目录。`cd` 回工程根再跑就好了，一个字节的代码都没改，
**但报错说的是 EPERM —— 它指向「权限」，而真因是「谁站在里面」。**
这是 §0.2 那一族的又一换脸：**报错文本命名的是它自己的机制，不是原因。**

**502. 交叉溶解的时候，「覆盖率」是**和**不是最大值 —— 而这只在窗口互为补数时才成立（Phase 121）**

点火级联的五张图各带一条
`ramp(p, t0-IG_XF, t0+IG_XF) * (1 - ramp(p, t1-IG_XF, t1+IG_XF))`。
要判断「级联现在压不压着画面」（用来决定巡礼的说明条露不露），得有一个 0..1 的覆盖率。
**`max()` 是错的**：交叠处两张各 0.5，`max` 读 0.5 —— 每切一刀就有 0.6 秒
「级联只覆盖了一半」，巡礼的说明条会从那半里漏出来。
**「和」才对**，而且对得**有理由**：相邻两张的窗口跨在同一个切点上、互为补数
（取舍 500 那条规则），所以交叠处两边加起来恒等于 1。**「和」是覆盖率，前提是这一段
本身就是一次交叉溶解** —— 换成不重叠的窗口（501 那种），和在切点会掉到 0，
这个式子**当场变成错的**，而它在两种窗口下**长得一模一样**。

**503. 图像可以溶，文字不能溶（Phase 121）**

级联第一版每张图各带一个 `<span>` 说明，跟着图的 opacity 一起淡。**19.45 那一帧
（级联交给巡礼的那一下）实测是两行大字叠在一起**：「CORE IGNITION」和「MONITOR NETWORK」
各 50%。**数字全对** —— 覆盖率读到 0.5、说明条读到 0.5，探条一个字都没抱怨；
**是图先喊的**（§0.14b）。两段半透明的字不是转场，是脏。

两条修法合起来用：
① **全级联共用一个字块**，跟着「哪张图在主导」（`op > ignBest`）**硬切** ——
切点正好落在两张各占 50% 的那一帧：图像在溶、文字在切，读起来就是「换了一镜」。
② **字比图早退 0.15 s**：级联最后一张开始溶（19.15）时字已经走完，
把左下角让给巡礼第一镜的说明条（它从同一刻起从 0 升上来），**两条字永远不同时存在**。

**顺带**：门（`ignCov > 0.5`）和显示（字块自己的不透明度）用两个不同的判据，就会出现
「大字已经没了、角标还在报 MONITOR NETWORK」的一小段 —— 两处**必须用同一个门**。

**504. 一个没有宽度的绝对定位容器，会安静地把文字折行（Phase 121）**

字块从「每张图各一个 span」改成「一个共用的 `#ignCap`」之后，它只写了
`left:110px; bottom:164px` —— 于是**容器是 0×0**。子件是 `left:0` + auto 宽的绝对定位，
可用宽取自容器，于是**每碰到一个词边界就折**：实测 `#ignLab` 的盒子 **287×121**
（60px 的字 →两行），24px 的中文折成 **157 高**。
**它不报错、不消失、字还在**，只是变成了另一种排版 —— 而在一帧 1080p 的画面里，
「另一种排版」看起来像「本来就是这么设计的」。
两道闸：容器给 `right:0`（可用宽 = 1810），子件加 `white-space:nowrap`。
**量法是盒子**：`getBoundingClientRect()` 的**高**就是行数，不是装饰。

**505. 父层有 `transform`，子件的 `z-index` 就出不去（Phase 121）**

同一个字块的第二张脸：它一开始挂在 `#ignite` 里面（想跟着那层一起吃缓推）。
`#ignite` 带 `transform:scale()` → **它自成一个层叠上下文**，
于是 `#ignCap` 的 `z-index` 再大也只在它**内部**排序，整层落在 `#scrim`（z-index 4）底下。
`#scrim` 就是左下角那团雾（存在的理由是「让说明条永远读得出来」），它盖在字上，
把白字压成**灰字** —— 而「灰一点」没有人会报错。
修法是**把字块搬出 `#ignite`**，去做巡礼 `#caps` 的邻居、和它同一个 z-index。
**代价是失去那层的缓推**，而这恰恰是赚的：说明文字本来就不该跟着镜头推，巡礼的说明条也不推。

**506. 「一共多少盏亮着」这个数，藏得住「是哪一组亮着」（Phase 121）**

拍完要把场景还回去。上一轮的记录是「98 盏」，于是我按 98 去关 —— **量回来是 130**。
多出来的 32 盏是 `Workspace.Lights.METULights`。**两个数都"对"**
（98 = 舱内照明那 98，130 = 这个 place 里所有亮着的 `NeonPart`），
错的是**我把上一轮记下的那个数当成了全集**。
证据链三条（都不是「我觉得」）：`Data/originalwatch/*/summary.txt` 里那 32 盏的
`SurfaceLight.Enabled` 记的是 `false [was true]` —— **是那一轮把它们的关掉记下来的，
所以它们的静止状态是开**；repo 里对 `METULights` 的唯一引用是采集器的清单；
分组普查 130 − 98 = 32 恰好是这一组。
于是**按原版的样子**（开）留 32 盏、其余全关，读数 `METULights 32/32 on`、其它组 0。
**没能排除的那一半照实写**：动手之前我没有记过逐组读数，所以「这 32 盏是不是我自己
上一轮留下的」**我证不了** —— 能说的只是「它现在在原版该有的样子上」。
**下次先记逐组读数，再动手**：`uniq -c` 出来的总数**能拿来"找"，不能拿来"读"**（§0.22 第 ⑤ 条同源）。

**507. 复现不了的旧数：取代它，不改写它（Phase 121）**

`docs/PROMO.md` §3 记过一条 `BIGGEST RISE 33.6 dB at t=16.25 s (-55.5 -> -21.9 dB)` ——
「点火那一帧音乐升了 33.6 dB」。2026-10-12 重新验收成品时，我按记忆重建了那个度量
（`astats:reset=1` + `ametadata=print` 抽 50 ms RMS 再找最大跳变），
**同一个脚本对成品和 `_bed.m4a` 给出逐字节相同的输出**，两者都报
`BIGGEST RISE 63.5 dB at t=0.00 s (-111.0 -> -47.5 dB)`。

**两条路都不通**：不能说「33.6 是错的」（它当时可能是另一种量法量出来的，只是**那次的方法
没写下来**），也不能说「现在的 63.5 才对」（**同一个数出现在两个内容不同的文件上 ——
错的是尺子**，§0.20「数出来多少个，先问数的是谁」的同族）。
所以：**新数进文档，旧数留在原地并写明「本轮未复现」** —— 不删、不覆盖、不悄悄换成新数。
**一个量若没有跟它一起记下来的命令，它就不是证据，是回忆。**

顺带把这次的「验收」定成两条**能复现、且互不依赖**的量：`silencedetect` 的
`9.693 → 16.201（6.508 s）`，以及跨点火那一帧两个**互不相交**的窗
（16.05–16.20 = -91.0 dB 对 16.22–16.37 = -19.5 dB）。
第二条的 -91.0 是**底不是值**（静音段是真正的数字零），所以结论只能写成**至少** 71 dB ——
**给下界，不给数**。

**508. 抽帧的图和探条的读数，用的是两个不同的时刻（Phase 121）**

验收点火级联时，我把五帧从成品里 `-ss` 抽出来和探条的读数并排放，
于是读到两处"矛盾"：探条说 `t=16.85` 大字是 **Main Chamber**，而抽出来的
`f16.85.png` 上写的是 **CHAMBER LIGHTING**；`t=17.45` 说 **Chamber Lighting**，
图上写 **CBL ARRAY**。**两处都像 bug，其实两处都不是。**

`-ss 16.85` 取的是**覆盖 16.85 的那一帧**，即帧 `506 = 16.8667`；而 `--eval` 是在
**恰好 `render(16.85)`** 上求值。字块又是在**切点上硬切**的（取舍 503），
所以**差一帧就是差一档**。实测这一对（同一台机器，相隔几秒）：

```
t=16.8333（帧 505） 字块 "Main Chamber"      op=0.5278,0.4722
t=16.8667（帧 506） 字块 "Chamber Lighting"  op=0.4722,0.5278
```

**同一族第三次出现在同一轮**：`f19.15` 那条"淡淡的巡礼说明"也是这么来的 ——
名义 19.15 处 `caps=0`（探条），而那一帧 `19.1667` 是 **0.0278**。

规矩：**两个不同的时刻不能说同一句话。** 图是"这个文件长这样"，读数是"这个函数在那个 t
返回什么" —— **说"图上写着 X"和说"t 处是 X"是两句不同的话**，而它们并排写在表里
长得一模一样（§0.20「数出来多少个，先问数的是谁」的同族：这次问的是**"在哪个时刻"**）。
抽帧之后要报时刻，就报**那一帧自己的时刻**（`i/fps`），不要报请求的那个时刻。

**509. 一个点路径的最后一段是属性，不是子件 —— 一个会话里踩了两次（Phase 122）**

把观察者的路径写回实例时，两次都栽在同一件事上：

- `rotor=nil`：我把 CBL 的 `Effects.SpinnyThingsFront.Moter.HingeConstraint.AngularVelocity`
  当**子件路径**往下走。`AngularVelocity` 是属性，不是子件；而且 `MoterPart` 属于**舱内警报**，
  不属于 CBL（CBL 的三个转子叫 `SpinnyThingsFront/Back/SlightlyBetterSpinnyThing`）。
- `missingPath=428 wrote=0`：更狠的一次 —— 我把**整行**当路径去解析，于是最后一段成了
  `Playing` / `Color` / `AngularVelocity` 这样的**属性名**，而遍历在找名字叫 `Playing` 的孩子。
  它报的是「这一条路径找不到」，**读起来正好像「这个世界里没有这些东西」**。

规矩三条：**① 属性单独取**（`parent = string.match(path, '^(.*)%.[^.]*$')`）；
**② 遍历时每一层的同名兄弟都要展开** —— 观察者的 ` ~(x, y, z)` / ` #n` 是**它自己的寻址**，
去掉会把 48 个同名兄弟塌成一行，于是「写进 48 件」变成「写进 1 件」，而张数**不会报错**；
**③ 这与 §0.17 同族**：报错落在赋值/最终消费者身上，而错的是**地址**。
（写回的值形状也要认：bool / 1 个数 / 3 个 → Color3 或 Vector3 / 5 的倍数 → ColorSequence /
3 的倍数 → NumberSequence / 2 个 → NumberRange。）

**510. 世界的授权基线只能从原版自己的录像里恢复，而且录像与我们的副本会合法地不一样（Phase 122）**

`FacilityCascade.Initialize` 从**世界**读基线（`off` / `lit` / `brightness`），
这是对的（单一真相源，Config 里再写一份就是第二个真相源），代价是
**一次「把世界点亮」的探针会把授权基线点着**：下一次 `Initialize` 把亮着的状态当授权，
整场开机静默失效。`ColdBaseline=true` 救不了（它的 `off` 也读世界）。

出路是 **`old` 就是 t=0**：`changes.log` 每行 `old → new`，所以每个 (路径, 属性)
**最早一次出现**的 `old` 就是它的授权值（`_tools/cold_baseline.py` → `Data/cold_baseline.tsv`，562 行）。

两个必须一起记住的边界：

1. **它是「窗口开始时的值」，不是「宇宙诞生时的值」** —— 如果录像窗口从一个班次中间开始，
   最早的 `old` 是那一刻的值。同一次里 `ControlRoomLowerLights` / `SubLoungeLights` 的
   `Enabled=true` **正是原版的静止状态**，而我们这一份静止是暗的：
   **原版和我们的副本在这里合法地不一致，照抄就是破坏**。判据是**我们自己的 t0 普查**
   （全设施 32 盏亮灯全是 METU 的 ⇒ 其余各组静止时一律灭），所以那几组**只回滚 `Enabled`**。
2. **录像没有行 ≠ 那件东西没有值**。`LightPart.Color` / LoungeLights 从头到尾没有一行，
   它们的授权值只能靠**我们自己的算术**：t0 `48/96` → 点亮 `96/96` ⇒ 恰好 48 件由黑转白
   （亮度只升不降，所以转白的那批就是 t0 全黑的那批）。**同一把算术给出 592 / 32 两个总数，
   与走之前那次独立普查逐项相同** —— 这就是「回来了」，而不是「我觉得回来了」。

**附带（这一轮新量到的）：`rewind` 是精确可逆的。** 克隆走完 step 0..16 再倒回 0，
`non-black 592/742`、`lights on 32`、球 `30,30,30`、`beam transparency 1`、`core 1`、
`PointLight false` —— 逐项回到走之前的读数。**所以「克隆驱一遍」是安全动作**：
它把自己写过的每一条都放回去（这也是三张图拍完世界还干净的凭据）。

**511. `LightPart.Color`：原版从不写，我们写了 —— 留着，可被操作员一句话推翻（Phase 122）**

ClampLights 的 48 件灯 = **39 件 `LightModel.Neon` + 9 件 `LightPart`**（实测，`isLamp` 数出来的）。
原版录像里有 `LightModel.Neon.Color`（`0,0,0` → 亮色），**没有 `LightPart.Color`**
—— 它只写 `LightPart.SurfaceLight.Enabled/Brightness`。我们的 `authoredColour` 优先取
**件自己的 Light 的颜色**，所以这 9 件的 `on` = 白的灯色，ramp 会把它们由黑推到白；
原版让它们一直是黑的。

**留着的理由**：这 9 件的授权色只能由算术得到（48/48，见 510），黑是对的；
但「开机时那 9 块面板该不该跟着亮」**是一个美术判断，不是一个可测的事实** ——
在只有一个缺省规则的 ramp 里，「亮起来」读起来更像开机，而且它只在 ClampLights 这一组出现。
**要推翻它**：给这一组（或按名字给 `LightPart`）一个「只驱动灯、不驱动件色」的名单，
`Config.Cascade` 已经有按名字索引的 `LampColors`，同一个形状加一个 `LightOnly` 即可 ——
改的是 **9 件**的观感，不动任何已验过的时序。

**512. 「同源」不是「同一份」：Studio 里可以**只有**一个模块落后 —— 判据是拉回来逐文件比（Phase 123）**

Phase 122 之后 Studio 侧一直在用的假设是「推过的就是现在的」。真机第一次进 `Running` 就崩在
`Engine:273`（`c.Sim.PressureDivisor` 是 nil，而磁盘的 Config 连这个键都没有 —— 那次压力重写
把 `PressureDivisor` / `HighPressureDivisor` / `State2Pressure` / `State3Pressure`
四个键一起退休了）。把整个 `ReactorBackend` 拉回磁盘 `cmp`：**十个模块里九个逐字节相同，
只有 `Engine` 是 17703 B vs 磁盘 20592 B**。

**所以「我推过」这句话本身不可证伪，而「逐文件比」是可证的。** 三个连带：
① **要拉就拉整个文件夹**，不要只拉你怀疑的那一个 —— 只拉一个的话，「其余的都对」这句话
没有任何证据；这一轮的价值恰恰在于**九个相同**（它把嫌疑锁死在唯一一个不同的文件上）。
② 比的是**哈希**不是字节数（§0.0）：两侧大小不同只是这一次的运气。
③ 崩的位置**不在**出错的模块里（`Engine:273` 是崩点，错的是 Studio 的 `Engine` 与
`Config` 已经不同步）—— 同 §0.15/§0.23 那一族：**报错的位置和出错的位置隔着一个文件**。

**要推翻它**：给出「Studio 侧与磁盘逐文件相同」的一次实际输出（不是「我推过」）。

**513. 自己装的相机保持器会让 `screen_capture` 的显式机位静默失效 —— 拍图前先 Unbind（Phase 123）**

点击装置要求相机被**每帧**钉在一个已知机位上（`BindToRenderStep`，Camera+1），
而 `screen_capture` 是**设一次**相机再截图。两者同时存在时后者永远读不到自己的机位：
工具设完、我的持有器在成帧前写回，**工具报成功、画面是自己的**。
判据是这一族的老面孔：**两个完全不同的请求给出逐字节相同的两张图**
（各 51242 B，md5 `695cf696801842d88ec19177ae00b33f` —— 都是那次被钉住的机位）。
反证也做了：`UnbindFromRenderStep('__probeCamHold')` 之后同一个调用立刻给出**请求的那张**；
再绑回去、请求舱内机位，回来的又是控制台（`Data/startup_shots/10_capture_holder_wins.jpg`）。

**规矩**：**拍图这件事和驱动输入这件事不能同时开** —— 要图先 `UnbindFromRenderStep`
（名字是全局的，从**任何** VM 都能解绑，不必回到注册它的那个脚本里）。这一条与 §0.14
（「两个相机逐字节相同」）同形但**因不同**：那次是工具自己不可信，这次是**我自己的代码**把
它按住了 —— 所以「工具坏了」这个结论在两次之间**不能互推**。

**514. 点击用的像素可以在冷阶段一次全算完：相机是 Scriptable，与停机点无关（Phase 123）**

上一轮把「park 在哪」和「像素是多少」当成一件事（两者的确在同一个机位下一起产生）。
其实分开：**像素只由 `Camera.CFrame.lookAt(eye, aim)` 决定，park 只决定服务端 6 studs 的距离门**
（`Config.Interaction.MaximumDistance`）。所以本轮**在一个 park 上算完四个件的像素**
（两个控制台相距 21.7 studs，正常一次 park 覆盖不了），运行期只按顺序改**属性和机位**、
只在真正要点的那个控制台上 park。四个像素里三个是 (510,239)、一个是 (512,238)
—— **2 px 之隔**，靠「每次点击前重设机位」而不是靠像素本身区分（§0.11 家族）。

**边界**：像素仍然**只在那一个 `lookAt` 下有效**（同一条旧规矩），
所以缓存里必须连 `eye/aim` 一起存；本轮的写法是把机位写进
`workspace.__probe` 上的属性，客户端那个保持器每帧照着它摆 —— 于是「重设机位」= 改 6 个属性。
扫描放在**引擎 `Step` 会早退的相位**（Cold/Ready）里做，同上一轮那条。

**515. 磁盘那一对可以先离线彩排：`luau.exe` + 两个 stub，3 秒换一次真机会话（Phase 123）**

真机一次会话 ≈ 20 分钟（起 Play、park、四次点击、113.4 s 开机链、拆台），
而 `Config` 与 `Engine` **都是纯模块**：它们只用 `Color3.fromRGB` 与 `Vector3.new`，
拼一段 `(function() … end)()` 把两个文件包起来、补两个 stub，就能在
`luau-windows/luau.exe` 里把 260 个 1 s 步跑完（`cold → boot → start → 步 16 → Running`，
t=259 再走到游戏自己的 PEA 过载）。

**它的价值不在快，在于「先证伪」**：这一轮它先跑通，才让后面那次真机崩点**只可能**是
Studio 与磁盘的差异，而不是这一对代码本身 —— **一次会话省下来的是「同一件事试两遍」，
不是「少干一步」**。边界：离线彩排不经过 `Runtime`、不碰实例、不碰 `FacilityCascade`，
**它证明模型能跑，不证明游戏会亮**；两样都要，顺序是先离线后真机。

**516. 结束班次缺的是**传输**，不是屏幕（Phase 124）**

`StarterGui.ScreenGui.EndShiftHandler`（610 行）在这个 place 里**从来没有出现过一次**，
因为它两头都没接上：没有任何东西 fire `ReplicatedStorage.EndShift`，没有任何东西监听
`ReplicatedStorage.MiscEvent`（那才是这块屏幕真正 fire 的 remote），也没有任何东西 fire
`ReplicatedStorage.ResetEvent`。后果是**一个走到 `Report` 或 `Failed` 的班次没有出口**：
`Engine:Command` 过了结尾就以 `'Shift ended'` 拒绝一切，而那条拒绝是**服务端 console 上的
一条 warn**，玩家一个字也看不到。操作员 2026-10-13 报的「突然就是 shift ended 了」量的正是这个。

诊断本身不新鲜（`peaStress` 到 100 → `Engine:Fail('Power extraction assembly overload')` → `Failed`
是按设计），**新鲜的是「之后没有路」**。所以这一轮补的是 `EndShiftBridge`：一个输出适配器
（与 `LogPanel` 同族 —— 不持有状态，只读 `engine.state.phase`），`Publish` 每秒跑、
每个结局**每位玩家**只发一次；屏幕自己的三个词路由到引擎自己的两个命令上，
**每一道门都还是 `Engine` 的**（`next`/`reset` 是它的命令、它的相位检查），
所以客户端只能要求一个引擎**本来就愿意**做的转换。回程 `MiscEvent` 带
`{mode, shift, 'Accepted'|'Refused', err}`，`EndShiftResume` 依此收屏幕、或把屏幕交还给玩家。

钱是 0，而这是一句真话：本 build 没有经济，`p1`（逐条钱的明细）**发空表**而不是填零
—— 屏幕对空表**一行都不加**（`EndShiftHandler` line 505），总额 0 于是落在屏幕**自己写好的**
零总额分支上（line 553：灰字 + ` ... Good Job`）。**屏幕真正缺的是它要报告的那套经济**，
那是设计决定、属于操作员（`QUESTIONS.md`），不属于这里。

**边界**：真机验的是「跨过结尾 + 按住确认 → 重开」这条链（`PROGRESS.md` Phase 124）；
**没有**验的是一次**正常完成配额**的 `Report`（那要先把 512 点能量跑满）。

**517. `Lobby` 是默认路径，所以它不能是死路 —— 把它改写成一个真的转换（Phase 124）**

`EndShiftHandler` 里 `v15` 的默认值是 `'Lobby'`：玩家**按住那个确认按钮**时，
三个按钮一个都没选，屏幕发出去的字符串就是 `Lobby`。原文里这一刻是**传送** ——
一次重生重新克隆 `StarterGui`，一切复位。这个 place **没有传送、也没有大厅**
（全场所没有任何一处 `TeleportService` 调用），也没有经济，所以没有地方可以送。

三条候选：**拒绝**（回一条 console 说「没有出口」，等于把操作员的原始抱怨原样还给他）、
**什么都不做**（同上，而且更安静）、**改写**。选了改写：`Lobby → 'Reset'`、`action = 'reset'`，
并打一条 **print 而不是 warn**（它现在是常规路径，不是故障）。

不改写成「`Lobby` 直传」的理由是**请求词也是回程词**：屏幕的回执处理器按第一个字段把它自己的
`CONTINUE` / `RESTART` 变灰、让按钮停在 `L`（一个 lobby 回执），只有 `Reset` 回执才读 `R`。
把 `Lobby` 原样传下去，屏幕就会显示**一个它没有做过的转换**。

**边界**：这不等于「大厅功能已实现」—— 它等于「这个 build 里**唯一的那个**转换被接到了
默认按钮上」。原文的大厅（下一次班次在那里买）仍然不存在，那是经济的一部分（取舍 516）。

**518. 弱键表会在「键还活着」的时候把它收走（Phase 124）**

`EndShiftBridge` 的去重表一开始是 `setmetatable({}, {__mode='k'})`、以 **Player 实例**为键，
想法是「玩家离开之后自己掉出去」。**量出来不是这样**：2026-10-13 真机上，一个**仍然在
`Players` 里**、Lua 侧没有任何其他引用的 Player，会被一个**纯分配**的循环在**第 8 次
GC**（约 60 s 后）收集出那个表 —— 于是**同一个结局发了两次，正好隔 60 s**，
中间没有任何相位变化：去重**被它自己的键收走了**。

**同一个缺陷在 `ControlBinder.lastUse` 里是另一种症状**：冷却键也没了，于是那道「速率门」
对一个**还在场**的玩家**悄悄不再生效**。

修法：键改成 `player.UserId`，放在**普通表**里。数字收不走；代价是每个点过击的玩家留一个数字，
直到那个结局结束（`Publish` 在离开结局时清表）。

**两条可复用的**：① **弱键表的键能不能活，不由「数据模型还引用着它」决定** —— 那是**另一张**
表里的事，弱表问的是「还有没有**别的**引用」；② **`__mode='k'` 的失效方式是静默的**，
它不报错，它只是**不再去重**（同 §0.19：看不见的东西与没写的东西在盘上同形）。
判据做成了离线的：`_tools/endshift_payload_test.luau` 里玩家表是**真的**（有内容），
因为空玩家表会让**每一条**去重检查空洞地通过。

**519. 能因为别的原因失败的判据，不是干净的实验（Phase 124 —— 本轮最贵的一条）**

`MONITOR BOOT` 的点击**重复失败**，我去找原因，找到的是「角色挡住了射线」：
`workspace:Raycast` 打到 `HumanoidRootPart @ 1.29`，把角色挪开之后**看起来**就好了。
于是我做了对照：角色在 z=2.5 与 z=3.5、同一机位，**两次都失败**；反过来在 `MONITOR POWER`
上做，点击**在角色的挂件 `Circle.015Accessory.Handle` 落在射线上 1.52 studs 时照样成功**。

**真因是 `ShuttersOpen=false`**：`boot` 要求它（`Engine:Command` 的门），
所以那些点击**送达了、被正确地拒绝了** —— 而读数 `Booted=false` 与「点空了」**逐字相同**。

**规矩**：一个判据如果**能因为被测原因之外的原因失败**，它就不是一次实验，是一次巧合。
用实例状态当判据是 §0.2 / §4.4 早就要求的，但**要求还不够** —— 还要问
「**通向这个读数的路径有几条**」。这里通向 `Booted=false` 的有两条（点空了 / 门拒了），
所以 `Booted` 单独**不足以**证明点击送达；真正送达的判据是服务端那条
`[ReactorBackend][Control] <player> -> <LABEL>`（而这一轮控制台不可读，
所以只能**先把门满足、再点**）。

**顺带两个负结果，照实写：**
**① 「角色挡射线」这件事没有结论。** 正实验（同机位、角色两个 z）两次都失败，
反实验（挂件在射线上 1.52 studs）却成功 —— **一次失败的正实验加一次成功的反实验
不构成一条结论**，因为正实验里的失败**已经被门解释了**。
**② 本会话视口是 575.2 × 259.2**（上一会话 1020×550），启动按钮的点击区≈16 px 高，
所以每一次点击都必须**读实例确认**、不能假定。`+58 px` 那条**再次逐位复现**：
`user_mouse_input moveTo(x,y)` → `UIS:GetMouseLocation()` 回 `(x, y+58)`，
`GuiService:GetGuiInset().Y = 58`。**由此得一条省事的推论**：请求
`AbsolutePosition + AbsoluteSize/2`（CoreUISafe 空间的中点）时，那 58 恰好与 inset 抵消，
**所以 GUI 中点的请求坐标就是中点本身**（本轮那一次成功的按住就是这么发的）。

**520. `ok and v or default` 会吞掉 `false`（Phase 124）**

探针写成了 `return ok and v or 'no-visible'`。当 `ok == true` 而 `v == false` 时，
`ok and v` 求值为 `false`，于是 `false or 'no-visible'` 返回 `'no-visible'` ——
**一个正常的 `false` 被报成「读不到」**。我据此怀疑 `EndShiftResume` 的界面复位没生效，
去查 `VitalsFrame`；直接读 `pcall(function() return v.Visible end)` 得到
`ok=true, visible=false`，而 `StarterGui` 侧的**作者值也是 `false`** —— 复位是**对的**。

这不是 Lua 的冷知识，是 §0.18 那一族的第六张脸：**判据报了一个不是原因的原因**。
`and/or` 这个惯用法**只在左侧为真时安全**；一旦值域里有 `false`/`nil`，就必须写 `if`。
同族还有本轮那行 `local a=vg=nil`（我自己的笔误，被解析器当场拒绝 ——
这是**好**的那种失败：它报出来，而不是安静地给一个数）。

**521. Assistant 沙箱里一次 95 s 的阻塞等待会杀掉 Play 桥（Phase 124）**

`task.wait(95)` 在 Assistant 的 `execute_luau` 里直接返回
`Target is closed (HOST_INVOKE_createExecuteLuauBridge_runCodeToRequester, Client)`，
Studio 随即回到 Edit 模式。**规矩：阻塞等待 ≤55 s**，需要更长的等待就切片。

**顺带一个负结果**：这一轮里 `UIS.InputBegan:Connect` 在 Assistant 沙箱里**没有**触发
（`_G.__clickLog` 一直是空的），而**更早的一次会话量到它触发过** —— 所以「沙箱里的连接」
不是一个可靠的仪器，**两次之间不能互推**（同 519 的第二条）。能用的判据仍然是**实例状态**（§0.2）。

**522. 没有对应物的那一行，留黑并报出来（Phase 125）**

写警报格的时候有两个诱惑：把 `ENERGY FLUCTUATION` 指到引擎的 `s.fluctuation` 上，
把 `POWER INTERRUPTION` 指到 `output == 0` 上。**两个都能亮，而且都看起来很对。**
两个都不写。

理由是手册：`ENERGY FLUCTUATION` 那一行讲的是**子空间**那个量（EFE 的幅度），
而 `s.fluctuation` 是**每一步的温度差**，它已经在**下一行** `HIGH TEMP FLUCTUATION`
用掉了。一个数点亮两条不相干的警报，读起来像**两条独立的信息**，实际是**一条**。
`POWER INTERRUPTION` 更直接：这个设施**根本没有建模过供电**，没有可以断的东西。

**规矩**：**「引擎没这件事」和「我暂时没接」在屏幕上长得一模一样**（都是不亮），
所以 Initialize 把这两行 **print 出来** —— print 不是 warn，那不是故障，
但它是**留痕**：缺口在日志里，而不是留给读代码的人自己发现（§0.13 同族）。

**523. 补一件「六台有、一台没有」的东西：这是复原还是发明？（Phase 125）**

`AlertsControlRoomMonitor` 没有 `EFEFrame`，另外六台都有，而手册写着
「all monitors will display a warning」。补，还是不补？

判据不是「我想不想要」，是**三条同时成立**：
**① 它是第六台的逐字节副本** —— 子树连文本（`EFE IMMINENT` /
`BRACE FOR ENERGY FLUCTUATION EVENT`）、颜色（黄 1,1,0）、字号（14）、尺寸都一样，
**只有根件自己的变换**在两族之间不同；
**② 它纯加法** —— 没动任何已有件、没改名、没删任何东西；
**③ 它可逆** —— 删一个 instance 就回到原样。
**缺任何一条，正确动作就是报出来而不是补上**（同 §0.22「证据不足时交付『丢了什么』，
不交付替代品」）。

补的是**全宽那一版**：判据是**被测件自己**的 `MainMonitorFrame` 就是 `{1,0},{1,0}` 锚 0,0。
**用被测件自己的风格选，不用我的偏好选。**
顺带量到 `BootFrame` 只有 **3/7** 台有 —— 所以这个 place 的监视器**本来就不齐**，
「某台缺一件」不是「它被单独做坏了」，这一条也说明补与不补不是「整齐化」的借口：
**只在手册明说七台都该有的那一件上补**。

**524. 代码兑现不了的那个常数，就是错的那一个（Phase 125）**

横幅的生命写成 `Forecast.BannerSeconds = 10.25`（从录像量出来的），
而实现把它兜在 `sequence ~= nil` 上；`sequence` 在 `TimelineOffAt = 14.63` 就没了 ——
判决（5.04）之后它只活 **9.59 s**。**声明的数和兑现的差 0.66 s。**

两个修法只有一个对：**把常数改成 9.59**，是**拿观测去迁就实现**（观测是那 10.25）；
**让实现兑现 10.25** 才对。改法是给横幅**自己的秒表**（`Step` 里 `bannerLeft` 倒计时，
`Refresh` 只 latch 那个慢输入 `equinox`），顺带把两个边都变成**逐帧精确**——
原先它挂在 1 秒闸上，亮的边最迟会晚 1 秒，而它满打满算才 10.25 s。

**同一族要标出来的一条**：钟点映射（`Clock.StartHour=23`、`MinutesPerSecond=1/3`）
**是我定的**。录像只给了判决的**形状**（`HADEN THRESHOLD BREACH ~<钟点>`），没给映射。
所以它住在 Config 里、注释里注明是**我们的**数 —— **外推的结论必须当场标成外推**
（§0.21 第 3 条：算过的和量过的在盘上逐字同形，只在下一次被质疑时分开）。

**525. `receive.py` 的文件名就是 URL 的路径 —— 而上一趟的那份还躺在同一个目录里（Phase 125）**

`PostAsync('http://127.0.0.1:8765/'..child.Name, src)` 落盘的文件**没有 `.luau` 后缀**，
而 `_tools/_pull/round125/` 里还躺着**上一趟**留下的 `ForecastPanel.luau`
（**11609 B**，我改之前的版本）。我读它、对着 Studio 里的 **13605 B** 一比，
差一步就把它写成「推送被截断了」。

真相：**我读的不是我刚写的那一份** —— 两次读数都是真的，
错的是「我读的是哪一趟」。两条可复用的：
**① URL 的路径决定落盘名**，拉取用的后缀要和比对器一致
（`_tools/compare_backend.py` 认 `*.luau`，所以 URL 里必须带后缀）；
**② 一个目录里同时有两趟的东西时，「最新写进去的那个文件」不是「我要的那个文件」** ——
先 `ls` 看**全**，别用通配符只挑一种后缀就下结论（§0.18 同族：错的量法不报错，
它只是安静地给你一个看起来很像样的矛盾）。

**526. 官方 VM 拒绝的不是 `require`，是 `Capabilities`（Phase 125）**

§0.17 记的是「要在活 VM 里 require + 驱动 `ReactorBackend`，走第三方插件 VM」，
依据是官方 VM 里三句报错**都提到 `Capabilities`**。这一轮证明：**那三句报错是关于目标的。**

把同一份源码 `GetAsync` 成**临时 Folder 下的新 `ModuleScript`**（父件**没有**
`Capabilities`），官方 VM 的 `require` **直接成功**：
`require ok; Config.Alerts.Rows=27 Forecast.Step=9`。

于是得到一条**不需要 Play、也不需要第三方 VM** 的路：
**拉源码成临时模块 → require → 驱动 → 读回实例属性 → `Destroy()`**。
（`Instance.new` 的新实例 = 新缓存项 = 重新编译，同 §0.15。）

**边界要划清**：这条路读的是**模块**，不是「跑起来的游戏」。
§0.16 一个字没变 —— 它能替代的是**「只能读源码」**，
不能替代**真机验证**：源码看起来对 ≠ 真机验过。

**527. 他那个 `s` 是 `coreState`，不是 `Sim.State` —— 两个 state 同名不同物（Phase 126）**

操作员 2026-10-13 贴来一条温度式子，其中 `s` 写作「反应堆状态（0, 1, 2, 3）」。
**这个游戏里有两个都叫 "state" 的量**，`Engine.luau` 自己的注释（287-290 行）就写着这件事：

- **`pressureState`**（GUI 的 `Sim.State` 镜像的就是它）：原版那个 if/elseif 链**没有 `else`**，
  所以低于 5600 时**上一档继续有效** —— **latch 住的**；
- **`coreState`**（`Engine.luau:320`）：`T > 29500 and 3 or T > 17500 and 2 or T >= 5600 and 1 or 0`
  —— **温度的纯函数**，而且**有第 0 行**。

**他的表按第二个分组的**，三条独立证据：**① 有第 0 行**（熄火降温），latch 的那个永远到不了 0；
**② 他的 `s` 会降**，latch 的那个在一次崩塌之后**会滞后**；
**③ `baseRate[3] = 1036 ≈ 580 + State3Heat(460)`** —— 引擎在 `>= State3` 时额外加的那 460/拍
正好是 2 档到 3 档的差。

**写错了不会报错，只会安静地错**：把 latch 的那个喂给这张表，后果是
**scram 之后热量还开着**（温度掉到 5600 以下了，而 `Sim.State` 还停在上一档）。
所以模型自己带一个 `core_state(temperature)`，逐阈值实现 `Engine.luau:320`。

**顺带一条同族的**：阈值写成 `> 29500`，**不复用** `STATE_2_MAX`（29499）。
后者是**整数压力**的编码（`29499` 含、`29499.5` 已属 State 3），而温度现在是**浮点** ——
`(29499, 29500]` 这一段两者答案不同。**借来的常数带着借来的定义域**（§0.18 第五张脸）。

**528. `noise(x)` 留在 `× x` 里面，逐字实现；被拒的编辑要放回（Phase 126）**

**① 不替他改式子。** 他的 `noise(x)` 写在**乘法里面**，于是它不是"读数上的一层抖动"，
是**斜率上的一层抖动**：x=100 时 ±80 的摆幅 = **±8000 的散布**，而且**随 x 长大**
（x≈30 时它已盖过 559 那一项）。它写出来是为了「防止画面闪烁」，**照字面它做不到那件事**。
两条路：改了它、或者**照写并当面说清**。选了后者 —— **他的模型是他的**；
替代形状（`T_0 + rate * x + noise(x)`，抖动加在 x **外面**）写在代码注释和 README 里，
**但不替换**（同 §0.21 第 3 条：算过的和量过的在盘上逐字同形，只在下一次被质疑时分开）。

**② 闭式解的读数会跳，而这是模型不是故障。** 他的式子是一条**过 `T_0` 的直线**，不是积分：
行一变，**整条线跟着变**，读数跳 `(新速率 − 旧速率) · x`。1→2 只跳 `21x`（过界处 ≈460），
2→3 跳 `456x`（过界处 ≈**19000**）。在 Desmos 里拖 `s` 就是整条线动，所以这是他的模型。
代价是**跳看起来像 bug** —— 所以 `advance()` 在行变化时**写一行日志**
（`# core row 1 -> 2 at x = 22 s: T = ...`），并且行从**上一拍结束时的温度**读，
和 `Engine.luau` 拿自己的 `before` 判状态项是同一种写法。

**③ "上一个数"和"下一个数"不是同一个数。** 改功率 / 改行 / 切 auto 都会让
**上一步的数字变成一条已经不存在的线**，所以那三处**清空**上一步的读数，**不重算** ——
重算等于往屏幕上放一个**已经记过日志、已经动过压力**的拍。
读数是 `-` 而不是 `0`，因为 `0` 和一个"真的加了 0"的拍在屏幕上**同形**（§0.19 同族）。

**④ 被拒绝的编辑必须放回。** armed 时往温度框里塞一个数：`_set_temperature` 拒绝写入，
但**框里留着那个数**。它只活到下一拍（`advance()` 会盖掉），而**恰恰是"活得很短"才没人会发现**。
一个被忽略的按键是一回事，**一个报告着模型从未用过的温度的框**是另一回事 ——
**拒写要在同一步把显示恢复**，否则"没生效"和"生效了"在屏幕上长得一样。

**529. 模型是 arm 上去的，不是装上去的 —— 一个数不能有两个主人（Phase 126）**

滑杆是这个文件自己的设温度方式，模型是一种算温度的方式。两者**不能同时对同一个数负责**，
所以：

- **默认不 arm**：复选框不勾，下面一行都不跑，窗口行为和以前逐字相同 ——
  **§1.4 第 1 条（不许改现有行为）在桌面工具上也一样管**，而且这是一条**可证伪**的默认
  （检查器第一节量的就是"模型没碰 Temperature"）；
- **armed 时滑杆与数字框 disabled**，模型的写**不经过** `_set_temperature`；
- **`_set_temperature` 是控件侧的唯一闸口**，armed 时它拒绝 —— 这不是冗余：
  `FocusOut` 会在 spinbox **被 disable 掉焦点**时触发，没有这道闸，
  **arm 这个动作本身**就可能把框里那个数立刻写回去。

**530. 检查器读屏幕，不读模型 —— 而它抓出的两个缺陷都只有它能抓（Phase 126）**

`luau-windows/core_model_check.py`：建窗口、`withdraw()`、一拍一拍驱动，
数字**全部从控件上读回来**（`screen()` 走 grid、解析每个 label 的 `textvariable`），
**不读 `Core` 的属性**。读属性的话，"模型里对、屏幕上错"这一类**永远看不见**（§0.2）。

**它抓出两个真缺陷**：

1. **被拒的输入没被放回**（取舍 528 ④）—— 模型属性那一侧**完全正常**，错只存在于屏幕上；
2. **我自己把判据写错了**：解武装那一段断言行按钮回 `normal`，而当时 `auto` 还开着 ——
   行按钮跟着 `auto`、**不跟着 `armed`**。代码是对的，**判据是错的**。
   这正是 §0.26 ①：**能因为被测原因之外的原因失败的判据不是干净的实验**。
   而修法不是把期望值改成 `disabled`（那是**拿观测迁就断言**），而是换成**更有信息量的那条**：
   `auto` 关掉时，行按钮在 **armed 期间**就该是活的 —— 手拨行正是开着模型时会去够的东西。

**锚点不许自证**：检查器里**不重跑 `gui.py` 的算式**（两边一起错也会 PASS，同 §0.0
"绝不能用磁盘算出来的哈希去校验磁盘"），而是把**他贴的那条式子逐字转写**成
`his_temperature()`（他自己的字面量：`[-455.7, 559, 580, 1036]`、三个正弦），
拿它当独立的第二份拼写。**70 项，0 失败，exit=0。**

**顺带一条量法上的**：这一轮的**版面**是靠**请求尺寸**（控件列 363 x 152 px vs 左列下限 400）
加两张截图定的，而**视觉模型读数字不可靠** —— 同一个右列，两次给出互斥的读数。
所以分工照 §0.14b：**图量形状，控件量数字**，两者都不许替对方下结论。


**531. 「我推过」不可证伪，「逐文件比」可证 —— 进 Play 之前先把**整个文件夹**拉回来（Phase 127）**

真机那一趟的**第一个动作**不是点击，是把 `SSS.ReactorBackend` 的**全部**模块 +
两个 `StarterPlayerScripts` 模块推回磁盘逐件比哈希：
**14 same, 0 different, 0 unmatched, 0 absent, exit=0**。

**为什么是「整个文件夹」而不是我怀疑的那几个**：取舍 512 那一轮，「我推过」这句话
在**十个模块九个逐字节相同**的时候仍然放过了一个落后版本的 `Engine` —— 而崩点还不在它身上。
只拉你怀疑的那一个，「其余的都对」这句话**就没有证据**。这条现在是进 Play 的前置。

**532. 「七台屏一起亮」只能在**跑起来的游戏里**验，而判据是**同一个时间戳**（Phase 127）**

Edit 里 require 真模块驱动，能做到的最大值就是「七份引用解析到同一个件」——
那是**接线正确**，不是**同时亮**。真机这趟的采样器**逐台逐属性**比对，
于是「都亮了」这句话被加强成「**七行写在同一拍里**」：七台在 `t=69.824` 一起开、
`t=80.074` 一起关，**间隔 0 ms**，窗口 **10.250 s** 与 `BannerSeconds` 逐位相同
（原版录像那 70 ms 的散布我们这边没有）。

**一个汇总出来的「都亮了」和一个逐件的「同一拍」不是同一个证据** ——
这次连时间戳都是同一个，所以不需要再解释散布从哪来。

**533. 相机**每目标重新瞄准**，把「2 px 的歧义」变成**构造上不存在**（Phase 127）**

取舍 519 里那 2 px 的来路是：相机**瞄准一次**，四个控制散在视口里，于是每个目标
离最近的整数像素各有各的偏差。这一轮改成**每个目标各瞄准一次**，于是每个目标都投影到
视口正中，四个控制解出**同一个**像素 `(287, 71)`。

**歧义不是被压小的，是被消掉的** —— 但也因此这条经验**不能反推**：
「四个控制共用一个像素」只在「每目标重新瞄准」这个前提成立时成立。

**534. 一个永远走不到的分支，是一个安静地死着的配置（Phase 127）**

深扫的判决有两个词（`Breach` / `Anomaly`），而**只有一个能出来**：
`untilEquinox = EquinoxSeconds − state.elapsed`，`elapsed` 在 `Engine.luau:233`
被 `if s.phase ~= 'Running' then return end` 挡着、`startupStep` 又只在 `Starting` 里推进，
而深扫的触发窗整个落在 `Starting` 内 —— 所以 `elapsed ≡ 0`、`untilEquinox ≡ 720 ≤ 900`，
**永远是 breach**。两次独立的量法（Edit 驱动 `~3:15 AM`、真机 `~4:39 AM`）都是 breach。

**这不是缺陷**（`Config` 注释那句「rather than always clearing」说的正是这个选择），
**而是一条之前没写下来的事实**：「两条判决都在」和「只有一条出得来」在盘上长得一样，
而只有后者会在某天有人调 `EquinoxSeconds` 之后**静默地**变成前者。

**535. 音效的窗口可能是**资产**在决定，不是配置在决定（Phase 127）**

`EFEPing.TimeLength = 3.3493 s`，而配置要它响到 `+9.37`（从判决 +5.04 算是 **4.33 s**）。
实测 `Playing` 在 **+8.384** 变 false —— 它不是被代码停的，是**自己响完了**，
差 **0.987 s** 正好等于 `4.333 − 3.3493`。**`PingOffAt` 这个数兑不了现**（同取舍 524 的形状）。

**反方向的有一条，但没有结论**：`Beep` 的 on→off 量到 **0.634 s**，而它的 `TimeLength`
是 **0.321 s**（约两倍）。**量到的窗口比资产长**这件事记下来，**不归因**（§0.21 第 3 条：
外推的结论必须当场标成外推）。

**536. `Visible=true` 不等于**看得见** —— 要一路看祖先（Phase 127）**

报告屏那 17 个统计行的**内层** `StatFrame` 全是 `Visible=true`，里面还写着作者的占位
`1,000,000$ X1`；看着就是「屏幕上明晃晃 17 个假钱」。而它们的容器
`StatContainerTemplate.Visible=false`，**截图里一个数字都没有**。
Phase 124 记的「每一条逐项 `Visible=false`」量的是**容器** —— 两句话一致，不是矛盾。

**差点写成缺陷的正是这一条**：读一个 GuiObject 的可见性，读的是**它自己加上它所有祖先**的合取，
少读一层就会把「作者摆好的样板」当成「玩家看到的东西」。

**537. 同一趟会话里的两个读数，不是同一个时刻的读数（Phase 127）**

我读警报格，读到 `13 excessiveTemperature` 亮、`14 excessPeaStress` 灭、`22 peaMalfunction` 灭
—— 三条放在一张表里看着自相矛盾（13 亮说明温度过了 17000，而 14/22 的门是 75/100）。
真相是**两次读数不在同一拍**：温度先过线，应力后到 100 并触发 `Failed`。
**每一格都按自己的门槛亮着，一个都不错。**

**只有同一拍读出来的数才能互相比较** —— 跨读数下结论之前先问「它们是不是同一时刻的」
（同 274：算过的和量过的在盘上逐字同形，只在被质疑时分开）。

**538. 两张逐字节相同的图，这一次不是工具坏 —— 同形的失败不能互推（Phase 127）**

取舍 513 记过：我自己的相机保持器每帧把 `Camera.CFrame` 写回，于是 `screen_capture`
「成功了」而画面是自己的，两次不同请求给出**逐字节相同**的两张图。
Phase 127 解绑 `__probeCamHold` 之后，**同一个调用立刻给出对的画面**（正面复现）；
随后**又一次**两张请求逐字节相同 —— 而这一次是因为那份 UI **真的停住了**（静止画面本来就只有一张）。

**同一个现象，两次不同的因**。分开它们的不是图，是**动作**：
「解绑之后有没有变化」。两次之间**不能互推**。

**539. 「在下一阶段的第一拍下发」不等于「在上一阶段之内下发」—— 而且它报的是个更好的数（Phase 128）**

`_tools/quota_policy_sim.luau` 把它的「置物块」（关风机、开泵、定 CBL 档）放在**循环的第一拍**，
而循环在 `advance(StartupSeconds + 5)` 之后才开。链长 113.4 s、advance 118 s，
于是**最后四次调用里阶段已经是 `Running`，而三台冷却泵一台都没开**（泵是这个块自己开的）。
实测 `pumpOn=0`：没有冷却时 `heat = 6`，入口温度线跑 `6 × 65 × 0.4 = 156 F/s`，
四秒 **+615 F**；整条轨迹带着这 615 F 进 `Running`，
而 615 F 值 `0.004 × 615 ≈ +2.5 PSI/s`，一班 350 s 就是 **~800 PSI**。
模拟器报 `Pmin 3226..3523`，真机是 **2804**。

**关键不在这个数，在它的形状**：修之前的模拟器**没有报错**，
两次运行**各自都自洽**，而错的那一份**报了一个更好的结果**。
「更好的数」比「更差的数」更难被怀疑 —— 它落在你想要的那一侧。
错的那一侧你会去查，对的那一侧你不会（同 0.18 一族，但这张脸骗的是**我们自己写的工具**）。

**修法是把块挪进链里**，而这不是为了迁就模拟器 ——
**真玩家就是在开机链里扔这几下的**，真机这一趟也是这么做的。
所以正确的写法是「跟被测对象一致」，不是「跟旧输出一致」。

**540. `Engine:Update(dt)` 按**固定的** `Sim.Step` 走 —— 数调用次数不等于数秒（Phase 128）**

```lua
function Engine:Update(dt)
    self.state.accumulator += dt
    while self.state.accumulator >= self.config.Sim.Step and steps < self.config.Sim.MaxCatchupSteps do
        self.state.accumulator -= self.config.Sim.Step
        self:Step(self.config.Sim.Step)      -- 注意传的是 Config.Sim.Step，不是 dt
        steps += 1
    end
end
```

`Step` **永远收到 `Sim.Step`**，`dt` 只决定累加器多久满一次。这里 `Sim.Step = 1`，
所以 `Update(1)` 恰好等于 1 s —— **是巧合，不是规定**。
换成 `Sim.Step = 2.5`（TRGWeb 的 tick），`Update(1)` 要 2.5 次才走一拍，
而 `MaxCatchupSteps` 会在卡顿时**丢掉累加器里的时间**（注释自己写了「keep residual time」，
但上限一到就丢）。**任何「我调了 N 次所以过了 N 秒」的推理，量的都是装置不是世界**（同 539）。

顺带：`quota_policy_sim` 的 `r.seconds = r.tick - BOOT` 里 `r.tick` 是在
`advance(ShutdownSeconds + 2)` **之后**取的，所以它比真正的 `Running` 长 7 s ——
那个数一直是个**复合量**，只是没人问过它由什么组成。

**541. 两个结局在**第一班**逐字相同，是**构造上**相同，不是巧合（Phase 128）**

Phase 124 记过「`Failed` 和 `Quota` 的屏幕看起来一样」，当时只是个观察。
Phase 128 读到了原因，`EndShiftHandler`（在 `StarterGui` 里，不在盘上）第 437 行：

```lua
if p2 == "Quota" then v6 = true end
```

而 `v6` **只有两个读者，两个都以「第三班」为条件**：第 308 行 `if v14 == 3 and v6 then SpecialEnd()`、
第 508 行 `if p4 == 3 and (v6 and k == "RadiationDamage") then task.defer(Diagnostic)`。
第一班 `p4 = 1`，**两个分支都不走**。

所以「一样」不是我运气不好挑了个分辨不出差别的字段，**是 `reason` 在第一班没有消费者**。
这条还**预言了它们在哪分岔**：`Quota` 只在第三班触发 `Diagnostic`（22 行 SOFT TRANSFER 打字机）
和 `SpecialEnd`（`SecretFrame` 那串聊天）。

**一条负面结论只有在找到它的机制之后才算结清** —— 在那之前它和「我没看仔细」同形。
顺带同一个结构：`$0 ... Good Job` 不是「没钱所以显示 0」，
是第 553 行 `if p3 == 0` 那一支**专门**把灰字和 ` ... Good Job` 拼上去的（第 547 行 `p3 < 0` 是红的并 `return`）。

**542. 「没看到那行」只有在证明了「它本来该出现」之后才是读数（Phase 128）**

这一趟 16 行 `[ReactorBackend][Control] … -> <LABEL>`，**0 行 `rejected:`、0 行 `[Gate] refused`**。
后两个「0」**之所以算数**，是因为它们各自的时间窗被前 16 行钉住了：
`[Gate]` 那行和它对应的点击是**同一拍**打印的，而那次点击自己的 `[Control]` 行**活下来了**
（缓冲区 400 行、统计流 ~3 行/s 会挤掉 130 s 之前的东西，
所以「一个同拍的行还在」证明「窗口没过期」）。**同一条点击的送达行在，拒收行不在** —— 这才叫证据。

否则「日志里没有这一行」和「日志把那一节截掉了」是**同一个读数**（同 §0.8 的截断、同 274 一族）。

**543. `phase=Report` 证明的是运输，不是配额（Phase 128）**

`Report` 只说明 `EndShiftBridge.Send` 把事件发出去了。**配额真的到了**要另找证据，
而现成的证据是：`Engine:Command('shutdown')` 在配额不够时**拒绝**
（`'Energy quota not yet met'`），而停机那一下**被接受了**。
**一个被接受的停机 = 一次 `energy >= quota` 的证明**，比读一个自己写进去的字段硬。

`reason = 'Quota'` 本身也是构造出来的（`EndShiftBridge.luau:67`：
`s.phase == 'Failed' and (s.failure or 'Failure') or 'Quota'`），
不需要去读实例 —— 而且**读不到**：payload 是事件参数，`ReplicatedStorage.EndShift` 上**没有** `.Value`。
顺带：日志那行 `end-of-shift report: shift 1 Report -> andypeng1NB` 印的是
`s.shift, s.phase, player.Name`，**中间那个是阶段不是 reason**，别读错（同 §0.24 ① 一族：地址读错）。

**544. 我量的那条射线，不是点击那条射线（Phase 129）**

同一个瞬间（相隔 1 ms）两个互相矛盾的读数：

```
t=98.183 MEASURE ... mouseTarget=ClickPart(Part) in MonitorPowerButton   <- 引擎自己的 Mouse.Target
t=98.184   mouseRay  Handle(MeshPart) d=1.01                            <- 我自己的 Workspace:Raycast
t=98.185   eyeNoChar ClickPart(Part) d=3.52                             <- 排除角色之后
```

**`Workspace:Raycast` 不排除点击者自己的角色；引擎派发点击时用的那条射线排除。**
这两句话就是全部。

容易读错的地方在 `Mouse.TargetFilter`：它读出来是 **`nil`**，而 `nil` 表示
「没有**额外**排除」，**不是**「没有排除角色」—— 引擎对本地角色的内置排除
**不在这个属性里露出来**。Phase 124 正是把这个 `nil` 读成了「没有排除角色」，
于是从「裸 cast 打到角色」推出「角色挡点击」。

**一条只测了工具的结论，会被读成关于世界的结论。** 修法不是更小心地读，
是**换一把尺子**：这一趟并排放了两个读数（引擎的 `mouse.Target` 和我自己的 cast），
矛盾当场就露出来 —— 而两个读数都留着，因为**是谁的那把尺子**这件事本身是结论的一部分。

**545. 「角色挡点击射线」是错的 —— 三臂单变量，`CanQuery` 开着、身体压在射线上 1.01 stud，照样送达（Phase 129）**

`docs/TODO.md` §3.14 ③ 挂了两轮的那条欠账，这一轮做成了干净实验。三臂只动 `CanQuery`：

| arm | `CanQuery` | 身体 | `onSegment` | 送达 |
|---|---|---|---|---|
| off | false | 控制件正中 | 0 | ✅ |
| **on** | **true** | **控制件正中** | **4** | **✅** |
| up | true | 抬高 4 stud | 0 | ✅ |

`on` 是问题，`up` 是对照（「flag 本身做了别的事」）。**两臂同送达 ⟹ 这个 flag 对送达没有影响。**
三臂的 eye 读数**逐位相同**，`off`/`on` 的 root 也逐位相同 —— **装置没动**。
`Stats.MonitorPower` 前后读数（`true` → 点击 → `false`）是第四层、不依赖日志的证据。

**这条同时是 §0.26 ① 的一次正面示范**：Phase 124 那次「正实验失败」之所以不算证据，
是因为它**已经被 `ShuttersOpen` 的门解释了**（那些点击送达了、被正确地拒了，
而 `Booted=false` 与「点空了」逐字相同）。**能因为被测原因之外的原因失败的判据，不是实验** ——
所以当时正确的做法就是记成「没有结论」，而不是记成「挡住了」。

**边界（不许外推）**：这一趟角色**全程静音 + 锚定**（`Transparency=1 / CanCollide=false /
CanTouch=false / Anchored=true`），只动了 `CanQuery`。**「一个正常站着、会动的角色挡不挡」
没有测。**

**546. 「在控制件自己的高度水平通畅」不是「视线通畅」—— 一个词替你把选择做完了（Phase 129）**

Phase 128 的泊车规则是：**在控制件自己的高度水平投一圈，取第一个通畅方向当机位。**
它回答的是**另一个问题**。`COOLING FAN SWITCH 1` 凹在 `ThermalConsole` 面板后面，
**16 个候选方向全部报「通畅」**，而真正要走的「eye → 控制件」那条**下降**的线段
（眼睛在 +0.7）从**每一个候选**都被挡住。

那一版装置会点到一个 `CFLever` 上，然后记下一个**干干净净、彻底错误**的负结果 ——
**没有报错、没有异常读数，只有一个安静的错答案**（§0.18 一族，第五张脸：词是「通畅」）。

**修法**：`findEye` 改成要求**点击真正会走的那条线段**命中控制件（且搜索时排除角色，
所以与 `CanQuery` 无关 —— 三臂因此拿到同一个 eye），并把**这条线段打中了什么**
写成 `eyeHits` 属性。**属性不是控制件的泊车是 VOID 泊车，`Status` 行自己会说出来。**
「泊好了」从此是一个读数，不是一个假设。

**547. `Destroy()` 杀不掉 `task.spawn` 出来的线程（Phase 129）**

往一个**活着的**探针上再注入一份，旧的执行器和旧的日志挂钩**继续跑**。
量到的形态：**同一次报告里出现两组 `t=` 相同的行**（`t=0.011` 出现两次）——
两台执行器在同一个 t0 上各自计数。

`Destroy()` 停的是主线程，`task.spawn` 出来的线程**没有人 await、没有人 catch**，
所以它们照跑。**修法**：每个循环自己检查 `script.Parent == nil`
（这是 `Destroy()` **唯一**会改变的东西），外加渲染步绑定在死的时候自己 `UnbindFromRenderStep`。

同族（§0.19「插件 VM 会答应等，却不跑你给它的回调」的反面）：**「看不见」和「没写」在盘上长得一样**，
而这里是它的另一头 —— **「已经销毁」和「已经停止」也长得一样。**
凡是有东西活在 `Connect`/`task.spawn` 里，**它就需要一个自己的死因**。

**548. 「靠得近」是另一条判据的读数，不是「就是这一件」（Phase 129）**

我写的守卫判据是「鼠标目标离 aim 小于 3 stud」，用来防止**读到过期的指针**。
臂 `off` 那行同时给出了 `mouseAtAim=true` 和 `mouseRay AlarmMuteButton.Part d=2.42` ——
`AlarmMuteButton.Part` 恰好在 aim 的 3 stud 以内，**指针当时明明在隔壁**。
**守卫判据自己给了假阳性，而它守卫的正是「别把过期的读数当读数」。**

判据该按「**是不是那一件**」判（身份），不该按距离（邻近）。
这不是「3 这个数太小」——**换任何阈值都是同一个错**：
问的是邻近，答的是身份，**问题本身选错了**（同 §0.18 第五张脸）。

**549. `UDim2.Offset` 是整数：被截断的 0 和没写过的 0 是同一个数（Phase 130）**

`ReadoutPanel` 第一版把三条储液条写成了**看起来没动过的样子** —— 读数停在作者摆的
`{1, 0}, {0.00999999978, 0}`。查的顺序值一轮：`grep` 排除抢写（没有别的模块碰
`BarFrame`）→ **活写一次 `UDim2.new(1, 0, 0, 0.5)` 当场读回 `{1, 0}, {0, 0}`**
（0.25 / 0.75 同样归零）→ 才定位到 `Offset` 在赋值时被**截断成整数**，
而 `Scale` 是浮点、照收。

**这条坑安静在它的失败形状上**：写进去的 0.5 和被截断的 0.0
**读出来是同一个数**，而「我写了一个 0」看起来和「我根本没写」一模一样。
同族是 §0.18（错的量法不报错），但这一份骗的是**写入侧**：
读数没错、代码没错、**被截断的是我的意图**。

**规矩**：写 `UDim2` 之前先问那一半是 `Scale` 还是 `Offset`；
**小数必须落在 `Scale` 上**，`Offset` 只留给整数（CBL 压力图那种 0..100 的整数档）。

**550. 一个条驱的是哪一半，只能从证据里读，不能从「轴」推（Phase 130）**

第一版的 `BarSpec` 声明的是**轴**（`'Y'` / `'X'`），于是实现只能挑一半猜。
逐字读 `Data/originalwatch/*/changes.log` 之后，三族条**骑的不是同一半**：

| 条 | 录像里的驱动 |
|---|---|
| C1..C3 储液条 | `{1, 0}, {f, 0}` —— **Y.Scale** |
| CBL 压力图 | `{2, 0}, {0, N}` —— **Y.Offset**，整数 0..100 |
| 配额进度条 | `{f, 0}, {1, 0}` —— **X.Scale** |

**修法**：`Component = 'XScale' | 'YScale' | 'YOffset'` 逐条在
`Config.Readouts.Bars` 里声明 —— 配置说的从「哪根轴」变成「**哪一半**」，
因为**被驱动的从来就是一半，不是一根轴**。

**顺带一条不是洁癖的**：`barSize` 把驱动轴的**两半都写**（另一半归 0），
**另一根轴整根保留**。录像里 CBL 图**作者摆的**是 `{2, 0}, {0.75, 0}`（满高），
而**每一个驱动值**都是 `{2, 0}, {0, N}` —— 即 `Y.Scale` 被按回了 0。
**带着一个没人在维护的 `Scale` 会把条按一个没人算过的数缩放。**

**551. 同一块屏幕上可以有两个时钟，而且两个都对（Phase 130）**

`Config.Readouts.Clock`（设施挂钟，正午起 710 分、1 min/s）和
`Config.Forecast.Clock`（深扫的判决轴，23:00 起、1/3 min/s）**并存在同一块配额屏上**，
看起来像重复、像有人抄错了。**两个都是量出来的**：

- 前者：一发 Play 跑 47 s，`3:14 AM → 4:00 AM`，**正好一分钟一秒**；
  五份录像的起步都是 710，速率 0.977~0.990。
- 后者：它在**每一次深扫上结构性地钉住** —— 因为 `time + untilEquinox = EquinoxSeconds`
  是恒等，`720 × 1/3` 分正好给出录像里的 **3:00 AM**。

把后者「统一」成前者的速率会**打断那个标定**（深扫开始时间立刻漂走）。
**修法不是挑一个，是把两个都留着，并在 Config 的注释里写出各自钉的是哪份证据。**
**两个看起来该合并的常数，先问它们各自锚在什么上** —— 锚不同的，合并就是破坏。

**552. 「驱动了但没接」的清单，必须在量到的那一刻写下来（Phase 130）**

`ReadoutPanel` 原来的模块头写着「`CoreDiagramFrame` 只是名字、没有数据可驱动」。
这一轮逐字读录像，**那句话是错的**：`GraphFrame1` 的
**REACTOR ENERGY INTENSITY** 有条、有驱动、录像里三处 `75 / 150 / 250`；
它的三盏 `WarnningImageLabel*.Visible` 也在动。
**一句自信的假话比没有这句更坏** —— 它会让下一个接手的人（或者下一轮的我）
**放心地不动它**。

所以模块头现在分两类写清楚，并且 **`Initialize` 把它们在启动时打印出来**：
**不接**（染色七族、`FanFrame` 的 NET C-PUMP FLOW RATE、`GraphFrame1` 的能量强度条、
`GraphFrame2` 只有 `Visible`）**和「为什么」**（缺的是**谓词**、缺的是**比值**、缺的是**映射**，
不是缺实现）。**清单不打印就等于不存在**（§0.13 同族：锚错了没人报错，
**没写的功能也一个错都不会报**）。

**553. 一个「恰好对得上」的作者字符串不是证据 —— 要走一遍梯子（Phase 130）**

CBL 状态标签第一拍读出来是 `OFFLINE`，和 `Config.Readouts.CblState.Offline` 逐字相同。
**这不能算证明我写进去了** —— 作者本来就可能摆了这个词。

真正的证据是**梯子**：`OFFLINE (t=0) → POWERING (t=72.7) → FIRING (t=85.8) → ACTIVE (t=117.8)`，
因为这四级里**后三个词只有这个模块会发**（原版的 `StateLabel` 写入只出现过
`OFFLINE / POWERING / FIRING`，`ACTIVE` 是**本引擎**的 `Running` 对应的词）。
**走上去才算证明；停在与初始值相同的那个值上，什么都没证明**（同 274/340：
没有 ground truth 的读数 = 挑的数）。

**554. `GetDescendants()[1]` 是「随便一件」，不是「你要的那件」（Phase 130）**

我读 Main 的能量图，用的是 `e:FindFirstChild('BarFrame') or e:GetDescendants()[1]`，
拿回一个 `{1, 0}, {1, 0}` 并一度当成「这条例不驱动」的证据。
**`GetDescendants()[1]` 的排序是遍历序，不是语义序** —— 它给的是一个**合法的实例**，
所以它不抛错、读数看着正常，而它**跟你要问的东西没有关系**。

**结论是从模块里来的，不是从那次读数来的**：`grep` 证明整个 `ReadoutPanel` 只有
**7 条被驱动的条**（3 CBL + 3 储液 + 1 配额），**Main 上一条都没有**。
**退路（fallback）会把「我找不到」伪装成「我找到了一个」** ——
找不到就报找不到（§0.26 ② 的 `and/or` 是同一族：兜底值会吞掉真值）。

**555. 「补充到…里面」= 把修订版并进去，不是并排加一个（Phase 131）**

他贴的标题是「温度计算（**完善**）」，末行「补充到GUI那个计算里面」。`完善` 是"修订"，
所以真正的问题是**换掉旧模型**还是**再添一个模型**。判据是三条**字面证据**（全文
`PROGRESS.md` Phase 131 第二节），最硬的一条：**`passive[0] = -455.7` 逐字等于旧表的
`BASE_RATE[0]`** —— 两份表**同源**，新的是同一批实测数据**按等级分别重拟合**的结果
（旧的是全等级平均的**一个数**）。

**没有加开关。** 同一块面板上两份温度模型 = 两个真相源（§4.3），而且它们会**共用同一批
读数的名字** —— 正是取舍 527「两个 state 同名不同物」那一族。
**可逆性另外记一笔**：旧式子全文在 `DECISIONS_2` 528 / Phase 126 / git 里，一句话能换回来。

**556. `[s+1]` 是 1-based 的下标，不是"阵列多一行"（Phase 131）**

他的 `s ∈ {1,2,3}`、阵列四格、取 `[s+1] ∈ {2,3,4}`。我第一遍读成"下标越界"，
第二遍读成"首项是死的" —— **都不是**：他的列表**从 0 数起**（第 0 格是那个 `0` 和 `-455.7`），
写式子时从 1 报数，于是取 `[s+1]`。
**按他的顺序写成 0-based，下标就等于行号** —— 于是"翻译"这一步**消失了**，
不存在的翻译不会出错。
**看出这一点的记号是 `passive[0]`**：它逐字等于旧表的行 0 —— 一个死格子不会有这个性质。

**557. 拟合表存 (斜率, 截距)，不存算好的数（Phase 131）**

`6.86a + 65.5` 是**一条关于 `a` 的直线**。所以表里存 `ACTIVE = {1: (6.86, 65.5)}`，
而不是 `{1: 408.5}`：后者把 `a = 50` 那个点**焊进表里**，
下一次有人问"level 3 是多少"就得**反解**，而**反解出来的数和拟合出来的数在盘上同形**
（§0.21 第 3 条：算过的和量过的逐字同形，只在被质疑时分开）。
代价是每拍两次乘加 —— 在这块面板上不值得省。

**558. 外推 vs 定义为 0：他的拟合只覆盖 1..5，第 0 档是我们签的字（Phase 131）**

控件有 `off`（`power = 0`），他的 `level` 从 1 起。把 `a = 0` 代进他的线，
行 1 得到 **`+46.3`/拍** —— 一组全灭的激光**照样加热**，因为那是**截距**，不是激光。
两条路：**外推**（把他的线延长到拟合区间之外，得到一个没人量过的数）或
**定义为 0**（"什么都不加"）。选了后者，并把这一格**在外面签字**：
`off` 不在他的拟合里，这是我们定的。
顺带一个自然的连带：`noise` 的振幅乘的是 `level`，所以 0 档连**抖动**也归零 ——
读数**逐字**停住，而检查器量的正是"逐字"（`T' == T`）。

**559. 换模型时要连"它不再需要的量"一起删 —— `T_0` 和 `multiplier()`（Phase 131）**

步进式**没有锚点**：温度由 `Sim` 携带，模型只往上加。于是 `t0`（arm 那一刻的温度）和
`multiplier()`（离 level-2 那个参考点几倍）**同时变成没有读者的量** —— 而两个都还活着：
`T0` 是屏上的一个读数、`multiplier()` 在日志里印成 `(x1 of the level-2 point)`。
**留着它们的坏处不是"浪费"**：一个不再参与计算的量摆在读数旁边，
和模型的项**逐字同形**（§0.27 ① 的同族 —— 那里是"看不见"，这里是"显示着"）。
所以 `t0` 删、`multiplier()` 删、日志改成 `T = ... , t = 0`，
`rearm()` 从"重新锚定"缩成"把噪声的钟归零"（参数 `sim` 留着不读，注释写明为什么留着）。

**560. 真空通过：断言落在"那个量恰好不起作用"的那一行上（Phase 131）**

检查器第一版写"CBL 满功率在屏上"，量到 `-456` 就 PASS 了 —— 因为当时**行 held 在 0**，
而**行 0 的 `active` 是 0**：等级在那个行上**一点影响都没有**
（`baseFluc = 0 · a + 0 + (-455.7)`，`a` 被乘了 0）。
**断言是真的，但它是真的因为 `a` 不在场。**
这和 §0.26 ①「判据能因为别的原因失败时，它就不是实验」是**同一枚硬币的反面**：
那一条说**能因为别的原因失败**的判据不干净，这一条说**能因为别的原因成功**的判据也不干净。
同族还有 §0.20 的"空集合会说两次谎"（`all([])` 为真、`max(())` 抛）。
修法：先把行**按到 3**（`6.8a + 534`，`a` 的系数最大）再量 —— `-456` 变成 `1384`。

**561. 前三拍量不出来的形状，要另找地方量（Phase 131）**

突变测试把 `T + actual + noise(t)` 改成 `T + actual + noise(t) * t`（"抖动又骑回时钟上"，
正是取舍 528 那个形状）。前三拍的断言**全部照样通过** —— `t = 3` 时偏差只有 ±11 度，
落在 300..500 的容差里。专加一条 **`t ≈ 35`** 的读数把它钉住：新写法一拍只走
`base·press` 加上**两个正弦之差**（被 2×振幅封住，level 2 时刚过 100），
旧写法要走 `base·press + noise(t)·t`。
**突变一共点亮 4 条**（含这一条）。§0.6 那条"跑不红的检查是噪音"在这里的具体形态是：
**要挑一个"错的形状在那里已经长大"的时刻去量**，而不是挑一个方便的时刻。

---

**562. 给公开仓库做新交付物，第一件事是量"它从哪来"（Phase 132）**

封面（`cover/`）的每一次取材都只从**已经在版控里的文件**里拿，一个字节都没新拷，
理由不是"省事"而是**曝光面**：`TRG Sounds & Images pack/` 从 Phase 51 起就被
`.gitignore` 排除（原版素材，不是我们能发布的），而**新交付物是最容易把它重新发出去的地方** ——
做一张新图的人脑子里想的是构图，不是 `.gitignore`。
两条具体做法：**① 动手之前先写一张逐文件的出处表**（写不出来的素材就不许用）；
**② 已经在仓库里的文件就引用它、不要再拷一份** —— 第二份拷贝是**第二个可以漂移的真相**。
**什么时候用**：任何"要交付 / 要发布"的新产物，包括下一张图、下一部片子、下一个 README 截图。

**563. 「浏览器量、另一份文件判」对一张**静止的画**同样成立，而且更划算（Phase 132）**

片头那条纪律（309）说的理由是"量了又判的人会悄悄改判据"。静止页面多拿到一条：
判定文件**一行浏览器代码都没有**，于是它是"从一份 JSON 到一个 exit code"的纯函数 ——
**可以在没有浏览器的情况下对着故意改坏的读数跑**。
`cover_judge.js --selftest` 就是这么来的：12 个突变全在**报告层**，每个都必须点亮
它瞄准的那一条（12/12）。同一条纪律还解释了为什么设计空间是**参数**（`--w/--h`）
而不是**第二份渲染器**：两部片子和一张封面对着的是同一台尺子。
**什么时候用**：任何"看得见的东西"，包括 UI 截图、tile 图、文档里的示意图。

**564. 输入的某种属性量不到时，在用它的地方**声明**它，并把量的命令写在旁边（Phase 132）**

"这一层要不要 `invert`"完全由**素材的极性**决定，而极性浏览器量不到
（`file://` 下 canvas 读背景图会被污染）。所以每一层在 HTML 上用 `data-art` 声明
白/黑/渐变，判定文件断言**声明与计算样式一致**的双条件。这条断言**不是"信我"**：
声明旁边写着量出它的那三行命令（`cover_layer_probe.py` 会打那张表）。
**什么时候用**：任何"正确性取决于被测对象之外的某个输入"的场合 ——
把它声明在**用它的那一行**，而不是"大家都知道"。同族：`CLAUDE.md` §0.26① 那条
"能因为别的原因失败的判据不是实验"。

**565. 「看不见」和「没画」是两个失败，需要两个数（Phase 132）**

我第一版写下的结论是"三个装饰层不可见"。像素差把它**拆成两种**：
`#titleBand` / `#hazard` 是 **0 px、最大 Δ0**（喂给 `screen` 的黑素材，
`screen(底,0)=底` —— **层根本不在画上**），而 `#hexes` / `#smMark` 是
**Δ3 / Δ35**（近白素材被 invert 成黑 —— **层在，振幅塌了 1%–14%**）。
两句话的修法不同（一个是补 invert、一个是去掉 invert），**混成一句就两件都没说清**。
**规矩**：凡"看得见/看不见"的判断，都要带一个**振幅**；0 和 1% 不是同一个断言。
同族：§0.18「错的量法不报错」、§0.26②「`ok and v or default` 会吞掉 `false`」、
§0.31「判据真空通过」。

**566. 别让素材的**名字**替它说话（Phase 132）**

ART_DIRECTION §3.3 说的是「黄黑警示框」，而原版那张素材叫
`perfectwarningstripesflip` —— 名字里每个词都在说"警示条纹"，**而它里面没有黄**：
量出来不透明像素逐字 rgb(0,0,0)。我第一版拿它做底边警示带，于是"黄黑"这两个字里
有一半是我编的。改成用调色板里的 Amber 自己排斜纹（每一条颜色都在 `Config.Visual` 里）。
这是 §0.18 第五张脸的又一次：**一个词如果替你做了选择，你读到的就不是测量**
（那一次词是"最外围"、另一次是"伴奏"，这一次是文件名）。
同族还有 §0.0 那条「比哈希、不比字节数」—— 名字和长度都会替你做选择。

**567. 交付物的成品帧要能从它自己的源重新渲出来 —— 判据是像素，不是逐字节相同（Phase 132）**

`cover/index.html` 的注释一直写着"调一百遍和调一遍结果相同"，这一轮把它变成**读数**：
同一份源连渲两次，md5 逐字节相同（`08430ec6…`）。一份**渲不回来**的交付物
是一份**没人能复核**的交付物 —— 而复核的唯一入口就是"从源重放一遍，看是不是同一张"。
**什么时候用**：所有落盘的产物（PNG / mp4 / 导出的 FBX 都算）。

> **同日更正（在这一条还没 `commit` 的时候量到的）。** 上面那个「逐字节相同」是**两次的巧合**。
> 真实分布是**连渲 5 次 = 3 次 `fa7d04cf…`（922894 B）+ 2 次 `08430ec6…`（922895 B）**，
> 两个形态**只差 1 个像素、1 个灰阶**：(790,583) 的 G 通道 `(22,31,34)` vs `(22,32,34)` ——
> 六边裁切边那一列（`hex.right = 789.41` 上取整）的抗锯齿。
> 所以这条的**陈述要改**：要**「逐像素相同」**（`DELTA=2` 门槛下 0 px），
> **不要「逐字节相同」**。一个会**随机变红**的复核判据比没有判据更坏 ——
> 它把「今天运气不好」报成「这版不合规」。错法的形状跟 §0.31 那条真空通过是同一族的两面：
> **判据的松紧要选在「被测对象真的会变」的那一层上。** 量法与全文：`PROGRESS.md` Phase 132
> 「页面自己的注释写着…」那条、`docs/COVER.md` §4/§6。

**568. 换掉画面里的一块之后，同一条跑道要整条重跑 —— 而且要先问它会不会变成真空通过（Phase 133）**

操作员一句「不用实拍图片」，六边里那张实拍换成了 `intro/assets/sm-core.png`。
三件事跟着它走：**① 选谁** —— 从"已经在版控里的、不是照片的"那几个里挑，且挑**量得清**的那个
（`sm-core.png` 的墨**铺满自己的方框**，于是 `contain` 之后**外圈直径 = 盒子边长**，
那个 39.4 px 的余量是个**算得出来的数**，不是美术挑的）；**② 原来那个元素不许删** ——
它是唯一被 `clip-path` 裁的元素，删了 **A6/A7 就真空通过**，所以改名留盒、换内容（取舍 560/561 那一族）；
**③ 新元素要问"它怎么坏"** —— `#coreMark` **不被裁**，坏起来就是"一条线穿出另一条线"，
而画上看着还挺像故意的 → 新增 **A10**。
**什么时候用**：任何"把画面里的主体换掉"的改动。**换掉内容不是换掉结构，但结构断言会跟着内容一起变空。**

**569. 截断的规则名会把两条不同的规则合成同一个字符串（Phase 133）**

`--selftest` 打红规则的名字用的是 `r.label.slice(0, 2)` —— 于是 **A10 被印成 `[A1]`**。
当时唯一在动的就是新加的 A10，而输出说"红了 A1"，**读起来像"新规则没生效、反而点亮了旧的"**；
真相是标签被截断，**判据一直是对的**（红的就是 A10），坏的只有"它叫什么"。
**规矩**：id 按**分隔符**切（`label.split(' ')[0]`），不按**长度**切 ——
长度切法在 `A9 → A10` 这一步**恰好**开始骗人（一位数变两位数），而前九条规则一次都没露馅。
同族：§0.0「比哈希、不比字节数」—— **名字和长度都会替你做选择**（取舍 566 的另一张脸）。

**570. 一对 precision/recall 不是读数，扫描才是；而且要先量"画在哪一个通道"（Phase 133）**

新图层要回答"那 163512 个像素**是不是这张素材**"（平铺一个白方块也能让逐层比像素全绿）。
第一版比对器把素材 `convert("L")` —— **而它是 LA、每个像素的 RGB 都是白的**，
转 L 得到一张**纯白方块**，"墨"变成整个盒子（precision 1.0000 / recall 0.27）。
**那个数不是错的，它是另一个问题的答案**："这张 PNG 的亮度通道长什么样" ≠ "它画了什么"。
**先量"画在哪一个通道"，再写比对器。**
第二版量对了，但**它的输出不该是一对数**：厂标的墨（1% 分位 **95**）和盒子里那两条 HUD 读数
（接近白 **237**）**在亮度上重叠**，于是没有哪一刀是干净的（"分母里坐着不是被测对象的东西"，
`CLAUDE.md` **§0.21** 那一族）。给出整张**扫描表**之后能站住的只剩两句：**整份墨都在画上**
（t≤60 时 44663 个墨像素亮了 44661 个）、**变暗的是外圈不是缺了一块**（r 0.9–1.0 那档 80.7%，
是 `#hexTint` 压暗 —— 又是取舍 **565** 那条"两个失败要两个数"）。
Phase 132 记下的那一对（0.9972 / 0.7371）**参数没记、这一轮复现不出来**，已作废。
**规矩**：读数**对参数敏感**时，参数要么**声明的**，要么读数**不该是一个数**。
同族：取舍 274/340（没有 ground truth 的拆分 = 挑的数，不是量出来的数）。

**571. 砍掉一个元素，跟着退场的是"断言它的那条规则"；而留下来的要一条一条重问（Phase 134）**

操作员「要素太多了，不需要这么复杂」→ 封面从十余样砍到四样。于是有几条规则**不是被改坏，而是宾语被删了**：
**A8**（"读数条每一格的值都在自己那格里" —— 四格读数条没了）、
**A9 里"黑、白两种极性都要在场"那句自检**（页面上仅有的两处黑素材 —— 标题斜纹带、底边警示带 —— 没了，
`black` 那一半没有对象）、以及逐层比像素里那五层被砍掉的。
**两条路都是错的**：留着 → **恒红**（"这一页没有黑素材"是这一页的**常态**，§0.13：永远红的检查就是噪音）；
删掉不问 → 悄悄少一条。第三条路是**回头逐条问：它的宾语还在不在，还在的话它还量得动吗。**
量下来的答案是三种：一条**要加重**（A1，取舍 572）、一条**一个字不用改**（A3 的"最近的一对不到 40 px"——
四样东西的版面上最近的一对是页脚两行，14.00 px，仍然真的近）、一条**对象没了只剩一半**（A9 保住
`white ⟺ 不许 invert`、`gradient ⟺ 不许 invert`，外加"至少有一层声明了真的素材极性"，
两句都还亮得起来 —— 突变里各有一条打它）。
**什么时候用**：任何"删东西"的改动。**规则不会因为宾语被删而变空 —— 它会变安静。**

**572. 计数是代理量：页面变空时，"非真空"那条要**按名字点**，不是把数字改小（Phase 134）**

A1 原来写 `m.text.length >= 12 && m.cells.length === 4`。四样东西的版面上这个门槛**永远不成立**，
于是只有两条路：把数字改小（`>= 4`），或者换一种说法。**换成按名字点**：
`title` / `badge` / `footL` / `footR` 四个名字分别在场，外加六边宽 > 100 px、厂标 > 100 px。
判据是那条老问题 —— **要让它红，得先有什么在场**（§0.31 ①）：`>= 4` 这句话在
"**标题被清空、四块空盒子还在**"的页面上**照样绿**，而"标题在不在"正是这一页唯一还值得守的东西。
代理量总在样本变少时先失效：**计数回答的是"有几块"，不是"是不是那几块"。**
（突变里两条专打它：标题清空、徽章清空。）

**573. 一个偏低但"解释得通"的读数，先问"谁压在上面"，再问"它自己变暗了"（Phase 134）**

`cover_mark_check.py` 在 Phase 133 量到厂标最外那一档只有 **80.7%**，当时的解释是
"`#hexTint` 把四周压暗" —— **一个说得通的机制，于是它被写进文档、当成了结论**（取舍 570 引用过它）。
Phase 134 把压在盒子里的东西砍掉之后，**同一台仪器、同一个阈值，这一档读到 99.7%**。
**但"砍掉的那两样就是原因"也不对** —— 拆开量之后（6×6 暗墨占据格 + 回头读 Phase 133 的 CSS）：

| 读数 | Phase 133 | Phase 134 |
|---|---|---|
| 盒子里墨的亮度 p1 / 中位 | **95 / 189** | **142 / 217** |
| 最外一档（r 0.9–1.0）亮着的比例 | **80.7%** | **99.7%** |
| 墨的集合 | 44663 px | 44663 px（**逐集合不变** —— 盒子、`contain`、素材都没动） |

暗墨**不是绕一圈**：它落在**下缘一条带**（盒内 y 350..420、x 70..350）、
上缘一条轻的（y 0..70、x 70..350），而圆环 **3 点 / 9 点方向是干净的**。
下缘那条带正是居中的那行 `CHAMBER ATMOSPHERE > SEALED`；而 Phase 133 的 CSS 里
**`.hud` / `.hudv` 各自都带黑色 `text-shadow`**（8 px / 10 px），
`#hexTint` 自己还带一条 **180° 的 `linear-gradient`（顶 42% 黑 → 中透明 → 底 55% 黑）**，
`#coreMark` 的 opacity 当时是 **.88**（现在 .92）。**三样都在往同一个方向推，
而三样各占多少这一轮没有拆开量。**
所以正确的记录是两句：**① "四周压暗"这个解释的形状是错的** —— 四周是干净的，暗分在上下两条带；
**② 谁贡献了多少没量**（同 §0.21 第 3 条：算过的和量过的在盘上逐字同形）。
**规矩**：读数偏低而你已经有一个**说得通**的解释时，先问"是不是**别人的东西正压在上面**"——
"被别人遮挡"和"自己变暗"在盘上长得一样，而**遮挡会随别人的东西一起消失**。
同族：取舍 565（"看不见"和"没画"是两个失败要两个数）、`CLAUDE.md` §0.21（分母里坐着被测对象）。

**574. 一个「按键按下去多少」要从**不连续**上读，不能读"按前、按后那两个采样"（Phase 135）**

出厂日志里 6 次 AVB 点击，我第一版仪器用最自然的那种写法读落差：
"按下那一刻之前最后一个采样"减"之后第一个采样"。**6 次里 3 次读出 `drop 0`。**
那三行在表里长这样：`4238 -> 4238   drop 0   drop-3300 -3300` ——
**读起来就是"这个按钮什么都没做"**，而它是错的。

原因是**记录器的采样比游戏拍密**：同一个拍会连着回好几条逐字相同的采样，
而**按键的秒数与某一拍相同**时，"按前"和"按后"取到的是**同一条记录**。
于是那三个 0 是**关于记录器采样率的读数，穿上了关于按钮的外衣**（§0.18 一族：
错的量法不报错，它只安静地给你一个数）。

**按键是一个事件，不是一段时间。** 事件落在**它自己那两条采样之间**，
而那两条**未必**是"时间上离它最近的那一对" —— 它落在**哪一对采样之间**，
取决于它和记录器时钟的相位。所以正确的读法是**找不连续**：
在按键 ±6 秒里找**那一个大的单拍阶跃**（压力自己的移动是几十 PSI，按钮是 3300），
把找到的那两个采样**连时间一起**打出来，让读的人能自己看间隔有多长。

**这一条的一般形状**：凡是**"某个时刻发生的事"**，而你的采样走在**另一个时钟**上，
就不要用"离它最近的那两个采样"去量它 —— 要么找不连续，要么把**相位**也打出来。
**"读数看着像个结论"和"这个读数问的是那件事"是两句话。**

**575. 一个同时容纳两个候选值的区间，一个都没选（Phase 135）**

这台控制台的失速速率有两个候选：操作员量原始游戏得的 **586**，
和我们这份 remake 的 `Config.Sim.StallCooling = 750`。
我去出厂日志里找仲裁，量到 6 次普通掉压的谷底是 **−538 .. −801**。
差一点就写下"日志支持他、不支持我们的 Config" —— **那句话是错的**：
`|750|` 也落在 `[538, 801]` 里，**这个区间两个都装得下，所以它谁都没选。**

这正是 §0.21（分母里坐着被测对象）的同一族，只是这次坐在里面的是**判据的分辨率**：
**一个区间只有在两个候选分处两侧时才是证据。** 区间画在那里、两个候选都在里面，
它是一句**真话**，但它**不是一次选择** —— 而"我们量了日志"和"日志替我们做了决定"
在文档上看起来一模一样。

最后用 586 的理由不是测量，是**出处**：这台控制台从头到尾是**原始游戏**的模型，
所以取原始游戏那个数；750 是我们自己那份游戏与它的**差**，写在注释里而不是被抹掉。
**规矩**：写下"这个读数支持 X"之前，先问一句 —— **它反对 Y 吗？**
答不上来，那它不是一次选择，只是又一次陈述。

**576. 不属于这一类的样本混进判据，只会把判据放宽 —— 而放宽的判据看起来更安全（Phase 135）**

同一台仪器还有两个把数据"弄宽"的错，都是**默默地让结论更保险**：

1. **谷底区间被 t=0 污染。** 开局那几条 `GameActive=false`、压力 0 的样本自己带着
   `fluctuation 0`，混进来把区间从 `−801..−538` 拉成 `−801..0`。
   一个宽了三倍的区间**照样能申明"586 在里面"**，而且**更容易**在里面。
2. **结尾的塌陷被并进失速。** 日志最后一段（19:22:13..19:22:18）压力**一路往下**
   （2056→1332）、温度也一路往下（6288→2318）—— 那是反应堆在**走向失败**，
   不是一次掉压回弹。并进去之后区间变成 `−538 .. −1246`。

两条都是**"多收进来一个样本"**，而多收样本的方向**永远让断言更容易通过**。
所以纪律是：**先问"这一类是谁"，再问"这些样本凭什么算在里面"。**
这里的答案是**从数上读出来的** —— 失速是"压力掉到地板以下、然后**回得来**"，
所以第 7 段（压力跨过整段还在往下）是**另一个 regime**，被单独念出来；
而"最后一段特殊"这种规则**不是**判据（§0.31 ①：要让它红，得先有什么在场）。
同族：§0.20 的"空集合说两次谎"（`all([])` 为真）、取舍 **572**（计数是代理量）。

**577. 一条规格落进模型，先问它**盖过**谁（Phase 135）**

操作员那两行 `pres <= 2200 → fluc = -586` **不是一个新项，是一条覆盖**：
它盖过行（core state 的温度档）、盖过 CBL 档位、盖过压力乘数 —— 但**不盖过噪声**。
四件事里有三件要有一条明确的次序，而**次序不写在规格里**
（"失速的时候读数是 −586 还是 −586 加抖动"那句话他没有说）。

判断的依据是他**上一次**对噪声的位置改过（2026-10-14 把 `noise` 从**斜率**挪到**读数**上），
而噪声的振幅自己乘 level —— 于是**三台全灭时噪声自己归零**，
"一台失速、三台全暗的反应堆**每拍正好掉 586**"就成了一个检查器**能抓住他的数**。
**规格里没写的次序，要用"哪一条能变成可验的读数"来选，不是用"哪一条看起来更整齐"。**

落到代码上是**一个函数、一个拼法**：`step_terms()` 同时被 `Core.step`（真的加）和面板的
"这一拍会加 X/拍"预告调用。**两处拼法会让承诺和行为漂开，而漂开是无声的** ——
这正是 §0.31 ① 那件事。而失速落在哪个压力上**不需要判断**：
`press_multiplier` 在 ≤11500 上一律回 1.0，失速只在 ≤2200 上开，
所以每个失速拍上 `baseFluc` 与 `actualFluc` **逐字相等** —— 一个**能被红掉的断言**，
而不是一句"反正乘数是 1，无所谓"。

**578. 「突变让它红了」「突变让它红在**对的那条**上」「检查器自己崩了」是三个读数（Phase 135）**

第一版突变器跑出 **2 条存活**，两个都不是"洞里没牙"，而是**两个不同的形状**：

1. **崩掉算成了没红。** 把失速地板从 2200 挪到 2500 的那条突变，检查器**抛了
   `KeyError: 'stallout pres <= 2200'`** —— 因为那条检查**按整行渲染出来的字**去找读数，
   而标签里嵌着 `AVB_STALLOUT_PSI`。**崩溃和"红了"在失败计数上长得一样**（§0.6 一族：
   一个未捕获的异常可以让 rc 还是 0）。改法：按**前缀**找（并断言前缀唯一），
   找不到就抛一句人话。
2. **红了，但红的不是它该红的那条。** 另一条用的是"失败名单里有这个名字"，
   而检查的名字带着前缀（`"...and the pressure is floored at 0"`），
   **精确相等**匹配不到，于是**一条真的红了的检查被记成存活**。
   改法：子串匹配。

所以这台仪器报**三个**数而不是一个：**崩掉 / 红了但红错了 / 真的红在对的那条上**。
第一类必须当成**失败**处理（一个自己崩了的检查器和一台永远红的检查器等价 ——
§0.13 那句"永远红的检查就是噪音"），第三类才是牙。
顺带：所有锚点**在写任何东西之前**先断言 `count == 1`（§0.13），
基线**必须先绿**（不然每条突变都会因为同一个理由"红"，整趟是噪音）。

**579. 同一个时长在两台钟上有两个数 —— 落进模型之前先问**这个模型用的是哪台钟**（Phase 135）**

wiki 给的 AVB 冷却是 **"about 25-26 seconds, or around 15 reactor ticks"**。
我一读之下把它当成**两个候选**：25-26 秒一个、15 拍一个，于是去问
"哪一个才是对的"。**这两个数从一开始就不是两件事** ——
25.5 / 15 ≈ **1.7 秒/堆芯拍**，一句话自己就把两台钟的汇率写出来了。
真正的问题是**第三个**：**这台控制台用的是哪台钟？**

- 这台控制台的钟是**操作员自己那份 `calculation.luau`**（末尾 `task.wait(1)`），
  所以它的"秒"是 1 秒一拍；
- 但模型里**其他每一个"每拍的数"都是原始游戏的每拍值** —— `FAN_DRAG = 60.0`
  逐字就是 wiki 的 **"60 PSI of pressure per core tick"**。
- 于是冷却走**同一个币种：15 拍**。我们那份 remake 的 `Config.Vent.Cooldown = 26`
  是同一个 ~26 秒在**它自己那台钟**（`Sim.Step = 1`，1 秒一步）上的说法。
  **两台钟，不是两套数** —— 这一条我一开始写成了"分歧"，还准备把它当问题抛给操作员。

日志能给的佐证是**下界**而不是答案：六次按键的间隔 **26 / 58 / 27 / 26 / 36 秒**，
最小 26 s ⇒ 冷却**至少** 26 秒（**间隔不是冷却** —— 人可能按晚了，
所以最小间隔是下界，不是测量值）。

**两条纪律**：**①** 一个时长落进模型之前，先问**这个模型用的是哪台钟**
（这里是"本模型的每拍 = 原始游戏的每拍，而本模型的秒 ≠ 原始游戏的秒"）；
**②**「本项目一直这么换算」是一句**关于历史的陈述**，不是一次测量 ——
我上一版就是拿它当理由写下去的（§0.21：一个词/一句惯例替你做完了选择，
你读到的就不是测量）。

**580. 源里是**状态相关**的常数，落成固定值之后要记下"这是哪个状态的读数"（Phase 135）**

同一条 wiki 的另一句：**"Based on the [[Core States|State]], the button will take
longer to refresh after use, but will always reduce roughly the same amount of PSI"** ——
**冷却在原版里是状态相关的**，而 wiki **一个每状态的值都没给**。
所以这里的固定 15 拍不是一个"原版的数"，而是一个**状态相关数的状态 1 读数**。

写下来的理由与 §0.27 / §0.30 同族：**一个静默的简化**和**一次准确的复刻**
在盘上长得一模一样，只有在**下一次被质疑**时才分开。所以它进
`gui.py` 的注释（标成 KNOWN SIMPLIFICATION）、进 `docs/SYSTEMS.md` §2.27 的边界表，
并且进 `QUESTIONS.md` —— 不是抹平，也不是自己编一组每状态的值。
顺带一条**边界**：wiki 那半句只说"**更长**"，**没有说单调、也没有说长多少**，
所以连"状态高 = 更久"这个方向都是从"take longer after use 随状态变化"里**读出来的**，
不是它写着的。

**581. 把一段规格放进模型之前，先问它**覆盖**了哪几样 —— 冷却那次问出三个选择（Phase 136）**

操作员「冷却控制呢？三个冷却泵分别控制」。三台泵、每台 0..3 档、
**每档去掉 120 度** —— 常数在动手之前就钉住了（出处见 582）。
**真正要定的是它落在算式里的哪一处**，而这是一个**看起来像抄写、其实是三个决定**的位置：

**(a) 它自己的加项，还是喂进他拟合那条线里的"若干个 CBL 档的负 `a`"？**
选前者，因为后者会**恰好在该起作用的时候把泵静音掉**：他这条线被"off 是咱们自己的规则"
（CBL 为 0 什么都不加）把着门，而**激光黑着不是泵停转的理由**。
**否证就在出厂日志里**：**84 条**记录是 `CBL sum 0` 而泵在 1/2/3 档 ——
原版自己跑过这个情形，而且它是对的。
**"关掉激光就把泵一起关掉"这句话，是被读数打掉的，不是我推掉的。**

**(b) `pMultiplier` 里面还是外面？** 外面：三个来源（`TRGWeb` / 出厂日志 / 我们那份
`Config.Sim.PumpCooling`）**没有一个**给冷却挂压力因子，乘上去就是**发明一个没人给过的数**。

**(c) 失速压不压过它？** 压。他的 `fluc = -586` 说的是**一个塌了的堆芯**，
它定速率，不管行、档、压力、**现在也不管泵**。**另一条理由更硬**：这保住了检查器
**已有的**不变量 —— "失速 + 全黑的堆芯以**恰好 586** 下落" —— 否则它会悄悄变成
"586 加一个泵项"，而那是**一条已经在守的断言被顺手改掉**，不是新增了一条。

**这一条与 577 是同一个动作的第二次**（那一次是失速两行覆盖掉了"off 什么都不加"）。
**共同形状**：一段规格落进一个已经有规则的地方时，它的**位置**不是它自己的属性
——位置是**那个地方**的属性，而既有的规则会**接受**它。
所以问题不是"这段规格说什么"，而是"**它插进来之后，哪几条既有的规则对它生效了，
而那几条里有没有哪一条是我没打算让它管的**"。
§0.31 ① 那条"能因为别的原因**成功**的判据也不是判据"是**判定侧**的同族；
这一条在**建模侧**：**一个静默的位置选择和一次准确的复刻，在盘上是同一个样子。**

**582. 一条恒等式被**三个拼法**同时满足时，它还没有指出是哪一个（Phase 136）**

冷却那个 120 有三条腿，最强的一条是**读出来的**：出厂日志 `Data/DataCollection.Log`
每拍都记着原版**自己**算的 `predictions.predDT`，而

```
predDT * 5  ==  65*sum(cbl.level) - 120*sum(coolant.levels)
```

**在全部 477 条上误差恰好 0.0**（`_tools/coolant_from_log.py` 印出来，rc=0）。
比另外两条腿（`Data/TRGWeb.luau:178` 的原型、我们那份 `Config.Sim.PumpCooling`）强的地方
是：**65 和 120 这两个数是从一台跑着的游戏里读出来的，不是从源文件里抄的**。

**但仪器把"近似拼法"也一起打出来**，这是这一条真正要说的事：

```
   also satisfied by:
     sum(cbl.level where active)   477 / 477
     coolant.sumLevel              477 / 477
   and REJECTED by:
     sum(cbl.power), which is not the level   0 / 477
```

**`level`、`level where active`、`coolant.sumLevel` 三者在合同里是同一个数**
（这份日志分辨不出来 —— 它在每一个都定义的地方都一致）。所以这条恒等式
**钉住了两个常数，但钉不住这三个字段中用了哪一个**。
而 `cbl.power` 是**另一个量穿着相似的名字**（level 0 读 10、level 4 读 100，
`level` 是索引），**0/477 被否** —— 它被否，恰恰是另外三个值得读的原因。

**两条规矩**：**① 仪器打出它**否掉**的那个拼法** —— 一条恒等式旁边没有反例，
你就不道它是"认出了那个式子"还是"认得足够松"；
**② 被三个拼法满足的恒等式，把**它们都写下来**，不要挑一个读起来最像的写进注释**
——"我选了 `level`"和"这份日志说 `level`"是两句不同的话，而盘上它们长得一样。

（与 **574** 同族：那次是六次按键里有三次因为采样而读成 `drop 0`，
这次是三个字段因为定义重叠而读成同一个数 —— 两次都是**读数本身不含它假装含的那条信息**。）

**583. 读数的**地址**里嵌着被测的那个数时，一条突变会**崩在取数上**（Phase 136）**

本轮给冷却写的六条突变里，有一条是**"常数变成记住的数"**（`COOLANT_PER_LEVEL = 120.0`
→ `100.0`）。它**没有把任何一条检查弄红** —— 它把**检查器搞崩了**：

```
KeyError: 'cooling  -120 x K'
```

因为面板上那个读数的**键**是 `"cooling  -%g x K" % COOLANT_PER_LEVEL` 拼出来的，
**被测的数就坐在地址里面**。于是常数一动，**地址先变了**，
检查器在**取数**那一步就死了，根本走不到那条断言。
**崩掉、红错了、红在对的那条 —— 三个结果里最坏的是第一个**，因为它看起来像"发现了问题"。

这与 Phase 135 那条 `stallout pres <= 2200` 是**同一个陷阱**
（当时是把门限写进了检查的名字里，突变一改门限，检查就找不到了）。
修法也一样：**按前缀取数**（`readout(values, "cooling")`），
**值可以进检查的正文，不能进检查的地址。**

**同一天踩到的姊妹坑**（同属"错的尺子"）：三条新检查一开始因为
`691.0 vs 691.0244…`、`-120.024…`、`-586.024…` 这样的亚单位残差而红，
**错在检查器自己** —— 拿**屏上（已被 `shown()` 取整）**的读数去比**未取整的浮点**。
**不是模型错了，是比错了层**（＝ §0.21 的浅版：不是减错了东西，是拿错了一层的数当锚点），
改成比 `gui.shown(<算出来的值>)` 之后全绿。这是 **§0.31 ②** 同一个形状的第二次 ——
那一次是拿原始浮点比屏上取整的值（`got 4821.0, wanted 4821.324069333027`）。

**584. 一条修正要问的第三个问题：它**覆盖**什么（Phase 137）**

Phase 131 把"规格怎么写进代码"拆成过两个问句（§0.31：**要让它红，得先有什么在场？**；
**同一个量有两层数时，锚点必须和读数在同一层**）。这一轮的操作员贴来一条
以 **`Correction:`** 开头的规格 —— 它**不是新功能，是改读法** —— 于是有了第三个问句：

> **这条修正覆盖旧规格里的哪几条？而它有没有**追认**哪一条本来就有的数？**

**必须逐条问，因为一条修正不会只做加法。** 这次三处改法**形态各不相同**：

| 改法 | 这一轮的实例 | 怎么认出来的 |
|---|---|---|
| 换**单位** | `a`：三台的和 → 平均；冷却：和 → 平均 | 他给了字面 `((c1+c2+c3)/3)*25`、`((p1+p2+p3)/3)*120` |
| 换**分支的优先级** | 失速：`fluc = -586`（**速率**）→ `dT = {P<=2200: -586, …}`（**整条**） | 他把 −586 写进了 `dT` 的花括号里，而旧版写的是 `fluc` |

**第二行是最容易漏的**：两句话读起来都是"失速时用 −586"，
而**前者的噪声还骑着**、后者**整条被替换**。
**它只在激光亮着时看得出来**（`noise` 按 `a_avg/25` 缩放，全暗时振幅就是 0），
所以那条**老的**失速检查（激光全暗）**在构造上量不出这个差**
—— 这正是 §0.31 ① 的反面用法：**判据要能红，得先有什么在场，而"在场"这件事要专门造**。

**反过来的那一半也有收获：修正会追认你本来就对的地方。** 这次它第一次写出行 0 的门限
（`T < 5600: 0`），而 `5600` 早就在文件里（`STATE_MIN` = `Config.Sim.State1` =
`Engine.luau:320`）—— **行为一个字没变**，但那条断言从此可以**拿它跟 `STATE_MIN` 比**，
而不是在检查器里再写一遍常数。**"两种拼法给出同一个数"是一个读数、不是巧合**，
所以它值得被写成一条断言，而不是被写成一句注释。

**这一轮的量出来的账**（全部在 `PROGRESS.md` Phase 137）：
三台满档的冷却从 1080 → **360**、`a` 从 375 → **125**；
占比几乎没动（41.2% → **39.8%**，行 2 38.2%、行 3 26.0%），
**但绝对量是三分之一** —— `120` 那个常数一个字没改，**改的是它乘的东西**。

**顺带一条被这一改消解的旧账**：`a = 375` 那条外推（`QUESTIONS.md` R9 ②）。
拟合跨 `a = 25..125`，改之前三台满档是区间的 3 倍；
平均之后三台满档**恰好是 125** —— 不是封了顶，是**够不到外面**。

---

**585. 同一个算式写两遍**不必逐位相同** —— 而原因可以不在模型里（Phase 137）**

第二份拼写（按操作员的**字面**写、不回头调 `gui.py`）一直是"两份必须一致"。
这一轮量到一个**不一致**，而它**不是模型分歧**：

```
gui.noise(1.0, 75.0)   ->  54.665213986169604
his_noise(1.0, 75.0)   ->  54.665213986169597
gap                       7.10543e-15
```

三个分量**逐位相同**（`equal components? True`），**和不同** ——
**CPython 3.12+ 让 `sum()` 成了补偿和（Neumaier）**：它落在比 `a + b + c` 更接近真值的位置。
`gui.noise` 写的是 `sum(amplitude * level * sin(...))`，而他的字面是 `t1 + t2 + t3`。

**做法（三样缺一不可）**：

1. **给它一个具名的容差**，而不是把红的那条删掉：
   `check_close(name, got, want, 1e-12)` 只在这**一处**用；
2. **把量到的差打在同一行**（`within 1e-12 (gap 7.10543e-15)`）——
   下一个人不用重算就知道它有多小；
3. **在别处继续要求逐位相同** —— 一个到处用的容差会把真错一起放过去。

**判据是"容差比这条检查要抓的最小东西小几个数量级"**：这里换两个振幅 = **2.4 度**，
差 = `7.1e-15`，**差十二个数量级**。答不上来这个比，容差就只是"把红的调绿"。

**边界**：这条**只覆盖浮点求和**这一族。同一个会话里另外两处（`a_avg` 的两份拼写、
四条行线的表）**都是逐位相同**的 —— 所以"两份拼写一致"这条规矩**没有被放松**，
只是知道了它**可以有例外，而且例外的理由要写出来**。

---

**586. 落在错槽里的突变是空操作：`HOLE` 也可能意思是"**突变**没牙"（Phase 137）**

突变器（§5.40、取舍 578）的 `HOLE` 有两个意思，这一轮撞上了第二个。
想要的是"让失速那一拍被暗激光清零"，写成了：

```python
- return STALL_FLUC, amp, STALL_FLUC,           0.0, True, 0.0
+ return (STALL_FLUC if power > 0.0 else 0.0), amp, STALL_FLUC, 0.0, True, 0.0
```

条件写进了 **`base` 槽**，而检查读的是 **`actual` 槽** —— **`actualFluc` 仍是 −586**，
突变**什么都没改到**，于是 0 红，被报成 `HOLE`。**读起来像"检查没牙"**。

**两种洞的修法方向相反**：检查没牙 → **加断言**；突变没牙 → **改突变**。
所以写突变时要问和写断言时同一个问题（§0.31 ①）：
**"这个突变想让哪一条红？它真的改到那条路上去了吗？"**
一条元组返回里 `base` / `amp` / `actual` **三个槽长得一模一样**，
错一槽的突变**能通过语法、能通过跑、还能报出一个漂亮的三数**。

**这一轮的读数**：23 条突变 / 0 条存活或红错 —— 而这条**先被写错过一次**，
是"跑起来才发现"的（0 红那条就是这个）。**元组槽位是新的 `§0.13`**：
锚点唯一还不够，**槽位也要唯一地认出来**。

---

**587. 算术三元组的均值**就是**它的中间项 —— 用对称的算例写不出"不是任何一台"（Phase 137）**

操作员给的算例是 `c = 5/3/1`，均值 **75** —— 而**第二台就是 75**。
于是这样一条断言：

```python
check("...nor any one bank", console.core.power in (125.0, 75.0, 25.0), False)
```

**在构造上永远绿**：`a_avg = 75` 与"读了第二台"**逐字相同**。
它挡得住"读第一台""读第三台"，**挡不住"读第二台"——而第二台恰好是最像的那个错**
（一个大数、一个中数、一个小数，中位数读起来最"合理"）。

**修法：用非对称的三元组**（`125 / 50 / 0` → `a_avg = 58.33…`，**不是任何一台的值**），
那一节整段换成 125/50/0 驱动的，`...nor any one bank` 才第一次有牙。

**这是 §0.31 ① 的又一族**：让判据永远绿的**不是空集**（§0.20 那一次），
**是算例的对称性**。同族的还有 §0.20 ② 的"分格边界落在数据上" ——
**选的样例自己把差别抹平了，而断言读起来句句在理。**
**可复用的问句：这个算例，能让"两个候选答案"给出不同的数吗？**

---

**588. 断言的位置是它**意义**的一部分：`Console.reset()` 是**开始一次运行**，不是**复位面板**（Phase 137）**

新加了两条"控件默认值"断言：

```python
check("the pumps start dark, like the game's", [var.get() for var in console.pump_vars], [0, 0, 0])
```

它们**坐在新加的算例那一节后面**，而那一节把泵拨到了 `2/2/2` —— 于是两条都红了。
**红的原因不是控制台改了**：`Console.reset()` 调 `sim.reset()` + `core.rearm()`、
并把 `pea_var` / `fan_var` / `temp_var` / `temp_box` / `period_var` 重新读一遍，
**它不碰 `cbl_vars` 和 `pump_vars`** —— 那条路是给"开始一次运行"用的，不是"把面板复位"。

**同一条断言，写在文件开头是"控件的默认值是对的"，写在后面就变成"上一节把控件弄坏了"。**
它红的时候，那句"控制台改了"**是错的** —— 而**盘上两条红一模一样**。
**修法**：这一类的断言**移到开头**（控件还没被碰过的那一刻），
并在后面需要干净状态的地方**显式置零**；源码里留一行字说明
**`reset()` 不还原控件位置**，免得下一个人再去踩。

**这也是一条关于**名字**的规矩**：`reset()` 这个名字读起来像"全复位"，
而它复位的只是**一次运行**。**一个名字如果替你做了选择，你读到的就不是实现**（§0.18 第五张脸）。

---

**589. 撤回只够到它**说**的那几行 —— 形状相同不是同一件事（Phase 138）**

操作员 2026-10-16 的 `Correction:` 里改了**两处**，而这两处是**同一个形状的操作**：
「把那个和除以 3」。下一句他只写「**冷却别用平均，重写写一下**」——
**一句话、没有数、没有点名行号**。于是"这句话够到哪几行"**不能从形状推**。

结果是**一个留、一个撤**，而理由**不对称**：

| 上一轮的两处 | 这一轮 | 为什么 |
|---|---|---|
| `a_avg = ((c1+c2+c3)/3)*25` | 留着 | 那条拟合只在 `a = 25..125` 上做过（**一个激光的份**），三个激光求和会跑到拟合外面三倍远 |
| `coolant_avg = (p1+p2+p3)/3` | **撤回** | 泵的 `120` 是**从一台跑着的原版里量的**，**量的就是这个形式**；没有拟合带要守 |

所以这一轮问的不是"它加了什么"，而是**"它够到哪几行"** —— 而答案只能来自**读那句话**，
不能来自**看那两处的形状**。**两处形状逐字相同，命运相反，这不是不一致，这是两条不同的约束。**

**再往前一步**：这是 §0.33（一条修正问的是第三个问题 —— 它**覆盖**了什么、
**追认**了什么）的**同族但不同面** —— 一条修正问的是"补上什么"，
一次**撤回**问的是"它够到哪几行"。**规格走过第二遍时，第二个问题才是那个会被踩的。**
**把理由写进常数块里**：下一轮再有人问"为什么这两处不一致"，那一块要能回答。

---

**590. 被撤回的读数会在**算例**里留下尾数 —— 那是**收据**，不删；而收据写成 `print`（Phase 138）**

他的算例后三项（`coolant_effect` 240 / `dT` 375.465… / `T'` 12375）是**平均值**算出来的。
这句话收回了那个读数，于是**这三项全是旧读数的数**。

**三条都留在检查器里，但留法不同**：

- 屏上是 **720** 的那条（求和）是**断言**；
- 屏上是 **−105**、**11895** 的也是断言；
- "**他的 240 正是 720 的三分之一**"这半句是**打出来的**（`print`），**不是断言**。

**为什么**："`720 / 3 == 240`"这种话**写不出一条能失败的形式** ——
它**永远不会红**，而**一条永远不会红的检查就是噪音**（§0.31 ①：要让它红，
得先有什么在场？答不上来就是噪音）。

**为什么不删**：那三个数是**收据** —— 证明"我们确实按那句话办过"，
不是记错了、也不是抄串了行。**同 §0.14 / §0.29**：错的尺子留下了它量过的结论，
**原文不改、加更正标记**。删掉它们，下一个读这份文件的人看到的是一条**从来没有过争议**的算例，
而它其实被改过一次 —— **这个差别只在"下一次被质疑"时才分开**（§0.21 第 3 条）。

**于是这一轮他的算例不能被当成"整条复现"**：它的一半属于一个已经不成立的读数。
**"复现了他的算例"这句话现在的正确形状是**："**前五项**逐字复现，
后两项属于**另一个**读数（那个读数被这句话收回了）"。

---

**591. 单位还住在**三个给操作员看的字符串**里，而没有一条检查看着它们 —— 那是**故意的**（Phase 138）**

跟着模型动的是三处**字**：泵那个 `LabelFrame` 的标题、读数行的标签、`on_coolant` 打进日志那行。
**一条检查都读不到它们**，而且**读不到是故意的** ——

取那个读数是**按前缀**取的（`readout(values, "cooling")`），因为**标签里嵌着被测的常数 `120`**：
常数一动，**取数那一步先崩**（`KeyError`），而不是那条断言红。
**崩掉 / 红错了 / 红在对的那条，三个结果里最坏的是第一个**，因为它看起来像发现了问题
（§0.31 ④：值可以进检查的**正文**，不能进检查的**地址**）。

**代价是明确的**：**"标题说平均、算式在求和"在盘上没有任何东西会红。**
这是 §0.31 ④ 的**另一面** —— 那一条说地址里不能放值，这一条说**代价在哪**：
按前缀取数**买到了常数可动**，**卖掉了标签与算式的一致性**。
**防线只有一条：改完 grep 一遍**（`grep -rn "mean level\|mean(p1\|coolant_avg"`）。
这一趟的结果剩下的是**文档里对历史的引用** —— 那是**有意**留着的（取舍 590）。

**可复用的问句**：一个单位/一个约定，除了算式里，**还住在哪些字符串里**？
那些字符串**有没有东西看着**？如果没有，**这一轮打算靠什么发现它写错了**？

---

**592. 一条走过两次的规格，**两个读数都要有牙**（Phase 138）**

突变器的规矩是"每条突变必须能红掉**它点名的那条**检查"（Phase 136 取舍 578）。
规格走了两轮，错的读法就有**两个**：**最早那个**（求和）+ **中间那个**（平均）。

上一轮那条突变的形状是"**把平均改回求和**"，名字叫
`the pump average goes back to being the sum`。这一轮**把求和恢复了**，
于是同一条突变**必须改名并换向**：

```python
("the pump sum is divided by three again, as one reading of the spec had it",
 "        return sum(self.pumps) * COOLANT_PER_LEVEL",
 "        return (sum(self.pumps) / float(COOLANT_PUMPS)) * COOLANT_PER_LEVEL", ...)
```

**只钉"回到最早那个"，就钉不住"回到中间那个"** —— 而中间那个**正是这一轮被点名的那个**。
两个锚点**落在同一行上**是有意的：那条线上只有一个单位，两个突变就是它的两个错读法。

**顺带一条"理由蒸发、规矩留下"的**：`a dark laser bank does not silence the pumps`
那条检查两边都做**屏上取整**，注释原来写的理由是"平均会在数里放一个除法"——
**求和之后那个理由没有了**（泵的读数又都是整数）。**规矩留着**，理由换成
"**一条只在看得见需要时才遵守的规矩，早就被忘过一次**"。

**这一条值得单独记**：注释里的**理由**和注释本身一样会过期，而**过期不会报错** ——
它会**安静地指向一个不存在的危险**，让下一个人以为这条规矩可以撤。
**规格回头改一次，所有"因为……所以……"的注释都要重新问一遍**（同 §0.32 那族：
**核对的宾语被删，它不会变空，它会变安静**）。

---

**593. 泵这一侧的分歧**回到零**，剩下的全在热那一侧 —— R11 的 B 退休、C 还挂着（Phase 138）**

Phase 136 的 R11 是"泵的 `120` 量出来了，但你的热线比原版陡 2.6 倍，所以 `120` 相对更弱"。
Phase 137 把平均值一上，那条按字面放大成三分之一。**现在它回到零**：
常数对、单位对，**三处来源全都对得上**（原版原型 `TRGWeb.luau:178`、
我们那份 `Config.Sim.PumpCooling`、**出厂日志 477/477 最大误差恰好 0 的恒等式**）。

**剩下的是同一个硬币的另一面**，而且它**不会消失**：

| 行（三台满档 = `a_avg` 125） | 三台满档激光的热 | 满泵 1080 占比 | 原版自己的同一条 |
|---|---|---|---|
| 行 1 | **903.8** | **119.5%**（**泵赢**） | 1080 对 975 → **110.8%**（泵赢） |
| 行 2 | **942** | **114.6%**（**泵赢**） | 同上 |
| 行 3 | **1384** | **78.0%**（**热赢**） | ——（`+534` 这一项根本不吃 `a`） |

三个热值都是**检查器自己用他的字面量算出来打印的**。于是
**"原版九档泵（1080）压得过它自己的最大激光热（975）"这条性质，这台控制台现在也有了** ——
**同一个数压过同一量级的热**。

**R11 的 B 选项因此退休**：它要恢复的正是这个比值，而**收回平均直接给了**它 ——
**没有做任何折算。**（B 是把泵折算到热线上去，`120 × 2.638 ≈ 317/档`。
**一个"为了对齐而折算常数"的选项，在原始读数被恢复之后就没有宾语了**。）
**C 选项**（回头查热线本身是不是偏大）**照旧挂着**；**A 现在既是选项也是事实**。

**边界**：1080 与原版**同一个数、同一个单位**，但"原版满泵压过满激光"这件事
**我们没在自己那台 remake 上量过** —— 量的是**出厂日志里那条恒等式**和**这台控制台的算术**。
**R11 不算"解决"**，它是**一半结清、一半留着**（§0.28 那条：
**一条负面结论要找到机制才算结清**）。

**594. 冷却那一行在一天里被拨了**四次** —— 一条被拨过 N 次的规格，防线是它自己记着历史（Phase 139）**

Phase 136 求和（这台控制台自己对三处来源的读法，**没有他一个字**）→
Phase 137 `Correction:` 改成平均 → Phase 138「冷却别用平均」收回平均 →
Phase 139「算了冷却计算还是平均吧」又改回平均。**中间两次是他说的，头和尾不是。**

`CLAUDE.md` §0.34 那条在 Phase 138 是"被走过**两遍**时要问**它够到哪几行**"，
这一轮的答案**第四遍还是那一行**：
激光那个平均是我拟合时定的（他的带只在 `a = 25..125` 上做过，**平均有它自己的理由**），
失速那条分支是他的字面，**两次都没动**。所以真正要守的东西换了 ——
**不是"够到哪几行"（答案已经稳定），是"这条行带不带得动它自己的历史"。**

理由：**三处来源的算术全部写的是求和**（原版原型 `Data/TRGWeb.luau:178`、
我们那份 `Config.Sim.PumpCooling = 120`、出厂日志那条 477/477 最大误差 0.0 的恒等式），
**而这一行是唯一不听它们的那一行**，它已经被拨过去拨回来过。
`gui.py` 那段注释因此带着**全部四个阶段**（哪天、谁说的、哪一版），不只是"现在是什么"。
§0.34 第 4 条（理由会蒸发、规矩要留）在这一轮**第二次**生效：
一条会被反复拨动的常数，唯一能防"下次谁把它拨回去"的东西是**它自己记着的清单**。

**595. 三个字符串的翻回方向和模型相反 —— 而两边**一条检查都没有**（Phase 139）**

Phase 138 把三处给操作员看的字从"mean"改成"total"（`LabelFrame` 标题 / 读数行标签 /
`on_coolant` 的日志行），这一轮**改回"mean"**。这三处**没有一条检查读得到，而且读不到是故意的**：
检查器取那个读数是**按前缀**取的（`readout(values, "cooling")`），因为标签里嵌着被测的常数 ——
**常数一动，取数那一步先崩，而不是那条检查红**（取舍 583）。
所以"标题说平均、算式在求和"这句话**在盘上不会红**。
**取舍 591 说那条防线是"改完 grep"；这一轮它就是被 grep 抓着的** ——
方向相反、机制一样：**规格一天翻两次，单位就会在字符串里落后两次。**

**596. 同长度、同一秒的改动会让 `.pyc` 复用 —— 于是突变**根本没跑**，而它报出来是 `HOLE`（Phase 139）**

突变器报过一次**间歇性** HOLE：一次 `the stall is not remembered for the readout`，
再跑一次红错**换成另一条**。**两个读数互相矛盾 ⇒ 先怀疑仪器，不怀疑被测对象**（§0.27 ② 同族）。

机制**量出来**的：CPython 拿（源文件 mtime **按整秒**，源文件字节数）校验 `.pyc`；
这个突变器里**大多数突变的字节数与它替换掉的文本完全相同**
（`-586.0`→`-750.0`、`2200.0`→`2500.0`），而检查器跑一趟约 **0.85 s** ——
**在上一版同一秒里写下的等长突变，两个校验量都相同**，Python 于是**重用了上一趟的字节码**。
复现：改掉 `STALL_FLUC`、**立刻** import，读回来的是**上一版的值**。

**这条比它自己是坏消息更坏，因为它谎报的方向**：它不报"工具坏了"，
它报"**这些检查没有牙**" —— 一个让人去**改检查**的结论，而去改检查等于
**给一个不存在的缺陷打补丁**（同 §0.15：错的是地址，报错落在消费者）。
**修法两半**：检查器用 **`-B`** 跑（请求），**并把请求读回来**（`_stray_cache()` 是读数）——
§0.2 的老话：请求不是读数。两个守卫都做了反向试验（去掉 `-B` → baseline 报出
`['gui.cpython-314.pyc']`；连守卫也去掉 → 23 条全部 `CRASH`）。
**顺带查库**：`selftest_boot.py` 的突变循环走 Lua（不 import Python 模块），
`check_fluc_steps.py` 的 `mkdtemp` 只放输出 —— **只有这一处要修，也只有这一处有。**

**597. 一个"没跑到"的突变必须和"没有牙"的突变**长得不一样**（Phase 139）**

取舍 586 说 `HOLE` 有两个意思（检查没牙 / 突变没牙）**而两种洞的修法方向相反**。
这一轮多出**第三个意思**：**突变没跑**（字节码陈旧、锚点没落、进程崩了）。
三者在旧输出里**逐字同形**（都是 `HOLE`），所以每一条突变现在除了"去红的检查名对不对"，
还要断言**它自己的新文本确实在检查器编译的那个文件里**，并且**没有字节码缓存挡在前面**。
**这条可以外推的形态**："报告一次失败之前，先证明**失败者真的在场**" ——
§0.31 ① 问的是"要让它红得先有什么在场"，这一条问的是"**它真的来过吗**"。

**598. Studio 那 12 个字是**读实例**验的；而"三块不动的牌子"是一条**判断**，不是读数（Phase 139）**

`BottomPipes` **Folder** 里 12 块 TextLabel 全部写入并**读回 `Text`**（`12 / 0 / 12`）——
**不是看截图**：牌子上的字长什么样（字号、换行、贴图方向）**没看过**。
**边界分开写**：哪一半验了、哪一半没验。
而 `Workspace.Model.BottomPipe` 那两块 `FUEL TRANSPORTATION` 和那块已经改好的独立 Part，
**不在他点名的文件夹里**，所以没动 —— **那是我对"文件夹"这个词的读法，不是一次测量**
（同 §0.18 第五张脸）。**读法要写出来，好让他一句话推翻。**
顺带：扫全场景的探针按 `FUEL/TRANSPORT/ROUT` 三个子串扫出 **17** 块，**3 块是假的**
（命中 `SUB-ROUT-INE`）—— **子串探针回答的是探针**。

**599. R11 从"另一半也结清"回到"两个选项"：把泵折算成 317/档那个选项**复活**（Phase 139）**

取舍 593 说"泵这一侧的分歧回到零、B 退休"，理由是**收回平均**直接给了
"满泵压过满激光"那个比值。**平均再一上，那个比值又没有了**（360 对 903.8/942/1384 =
39.8% / 38.2% / 26.0%，原版自己的同一条是 110.8%）。
于是 B（`120 × 2.638 ≈ 317/档`）**从"退休"回到"挂着"**，**没有做任何折算**。

**这一条真正的形状**：**一个"因为宾语消失而退休"的选项，宾语回来它就回来** ——
退休**不是**删除（§0.32 那族：删东西时判据怎么办）。
**而且分母里坐着两个不同的原因，要分开数**：
泵在这台控制台上便宜，一半是**他的热线每 a 单位陡 2.638 倍**（他的，不是这轮的），
一半是**这个除以 3**（这轮的）。**只有第二个是这台控制台自己做的。**

**600. 一个被**重述**过的模型就是一个**可以分叉**的模型 —— 压力那四行（Phase 140）**

操作员这一份规格里**重述了压力递推**（`fan_pressure_drop = fans*60`、`p_base`、
`p_temp_mult`、`dP = p_base + T*p_temp_mult - fan_pressure_drop`），
而这四行**就是这台控制台从第一版就在跑的那一行去掉 PEA 项**。
**"两处都在"不是判据** —— 判据是 `core_model_check.py` **拿他那三个字面量**
（`110/350/800`、`0.01/0.0075/0.005`、`60`）**驱动三个状态**，两份拼法互相比较。
**PEA 的去留**：他那一行里没有，而 PEA 在这台仿真和原版里都是真的；
`PEA_GAIN[1] = 0`，所以**他的式子正好是 PEA = 1 档的情形**，保留，并进 `QUESTIONS.md` **R13**。
出处注释补在 `FAN_DRAG` 上面 —— 一份重述**写下来**，是为了让下一次重述有机会被发现。

**601. 他的 `s` 在两块里**两个基**，而 `passive[s+1]` 是**第三种**下标约定（Phase 140）**

- 热那一块：`s = {T < 5600: 0, …}` —— **0 基的行**，有第 0 行；
- 压力那一块：`p_base = {s == 1: 110, …}` —— **没有 0**，只能是 latch 住的 `Sim.State`（1..3）。

**不是猜的**：110/350/800 就是 `STATE_GAIN`（`calculation.luau` 那一行 + 我们 `Config`，
**两个独立来源**）。判据驱动了能把两者分开的那一拍：`T = 12000` 时**行是 1**，
压力表给 **500**，而**行自己的拼法是 −130** —— **两份读法在同一拍上分开**。
`passive[s+1]` 的 `+1` 是因为**他的列表是 1 基**（Lua），
**定案的是他自己那句注释**「状态 1 = −400，状态 2 = −422」：
按 0 基读列表则状态 1 会是 −422，与他矛盾。
**一个表达式里三层下标约定，靠一句注释和两个独立来源的键定下来**（§0.18 第五张脸）。

**602. `passive` **移出**「关就是零」那道门：全黑的控制台从此**会降温**（Phase 140）**

这是整轮最大的一处行为变化。旧模型的 `actual = 0.0 if power <= 0.0 else base * amp`，
而 `base` 就是 `slope*a + intercept + PASSIVE[row]` —— **整行的贡献都在门后**，
所以**全黑时恰好原地不动**。新形状把 `a_avg <= 0: 0` 那道门**收进 `pure_cbl` 里面**
（他的规格自己这么写），`passive` 落在门外：**行 1 每拍 −400，昨天是 0**。
**代价写明**：出厂日志对这一项只能给**负结果** —— `CBL sum 0` 且泵全关的 39 条
`GameActive` 全是 false，加上第五节那 84 条也是 false，**这份录像里没有一台活着的、
四个控制全关的堆芯**（`_tools/passive_from_log.py`）。所以**这 4 个数按他的字面实现，
日志既不证实也不否证**（负结果不是空结果）。

**603. 热从**每行一条直线**收成**一条曲线** in `a` —— 行从热里退出去，只留一个常数（Phase 140）**

`active[row] = (slope, intercept)`（四行，`{1:(6.86,65.5), 2:(7.24,37.0), 3:(6.8,534.0)}`）
换成 `pure_cbl(a) = {a<=0: 0, 0.0516a² + 1.1a + 426}`。
**行从"改斜率也改截距"变成"只改从里面减掉多少"**，所以
"哪个行热"这件事**换了一种说法**：行 3 的热比最高不是因为它的热最大，
而是因为**它的 `passive` 最小（−22）**。
**四条退役的线留在注释里、不在 diff 里**（§0.34 ④：撤掉一个读数要留牙），
突变器里有一条把它们放回去。

**604. `p_mult` 只乘一项：一个档**乘几项**是位置问题，不是强度问题（Phase 140）**

旧形状里那个档乘的是**整个 `base`**（passive 也在里面），所以加倍的档把降温也加了倍；
他那一行自己的注是「**只乘主动加热**」。这一轮之后这个档**只乘 `pure_cbl`**。
**同一个常数、同一个分支，位置一挪就是另一条规则** —— 与 Phase 136 的三条放置决策同族
（取舍 581），但那一次问的是"这个新项进不进乘法"，这一次问的是
"**已经在里的那一项该不该被这把伞罩着**"。

**605. **写在散文里的数**：84 是量的，79/5 是写的 —— 而它自己复制了三份（Phase 140）**

冷却那一侧的证否句是"出厂日志有 **84 条** `CBL sum 0` 而泵在转"。
**84 是量的，围着它的拆分不是**：第一版更正写「79 是开机前、5 是崩塌后」，
而那 84 条**能试的判据全试过（泵档 / tempF / fluctuation / cbl.sumLevel / active），
只出一种拆分：62 / 22**。两个数**加起来正好 84、正好落在那句话里**，
而且已经**抄进三处**（`gui.py` 注释、`_tools/coolant_from_log.py` 注释、`README.md`），
每一处都带着"这是量出来的"的语气。
**三处按同一规矩处理：原文保留 + 当日更正 + 写明哪一半是量的**。
可复用的形态：**一句"实测"里如果有两个数，要问它们各自来自哪一次读数** ——
**一个数被量过，不代表它旁边那个也被量过**（§0.18 一族，但骗的是**写**的那一半）。

**606. 「尺寸不能变」的判据是**出厂文件的包围盒**，不是构建过程的读数（Phase 141）**

操作员那条硬约束只有四个字，而它最容易被满足成一句空话 ——
"我按原来的尺寸建了"在构建侧**永远成立**（每个件的位置、尺寸读出来都对），
因为错的可以是**轴**：第一版把刀片的长边（2.85）立了起来，整件高了 **2.37 studs**，
而构建侧每一个数都对，错的只是"哪根轴是厚度"。
**判据放在重新导入的 GLB 与 FBX 上**（三个轴、三个最小值、对原始文件的包围盒），
于是它当场红了两次（轴一次、各向异性的 FBX 一次）。
**"不能变"要能说出来变没变，就必须有一个不来自构建过程的读数** ——
这一条与 §0.26 ① 同族：**能因为别的原因通过的判据，不是判据**。

**607. 同一句「乘 1/5.902」，在树的根上和在叶子上不是同一件事（Phase 141）**

逐件乘 1/5.902 导出的 FBX 出来是 **7.83 × 7.23 × 0.34**，三个轴的比例**互不相同**。
原因是这批件**挂在 `Model` EMPTY 下面**：`scale` 与 `location` 各乘一次，
而父节点也被乘了一次 —— 于是每个件被缩放的次数和比例都不一样。
`trg.py` 里那些件挂在**场景根**上，同样的写法在那里是对的，**所以代码是照抄的、
而照抄的代码换了树就换了行为**。
出路是把整件事交给导出器自己的 `global_scale`（它按层级整体缩放），**一个变换都不碰**。
可复用的问句：**这个动作作用在哪一层？** —— 与 §0.22 ⑤「根与叶子」是同一个形状，
但那一条讲的是**搬运**，这一条讲的是**缩放**，而两者都只在一个层级上有意义。

**608. glTF 导入器把 mesh 在节点之间**共用**，而 FBX 导出器**静默丢材质**（Phase 141）**

同一个源 mesh 出现在多个节点上时，导入器让它们**共用一份 datablock**，
而那些节点的材质槽不同。FBX 导出器报九条
`Cannot register a valid material index for 'Material_2' from 'Part.002' mesh, 'Part.005' object`，
**照常导出、rc=0**。`make_single_user(obdata=True, material=True)` 之后警告全消。
**警告和坏了在盘上不同形** —— 所以两个格式都重新导入、逐件把材质名读回来，
而不是"警告没了 = 对了"。这也顺带解释了为什么清空 `Neon` 的材质会同时改到 `Neon.001`：
**我写的是一份共享的 datablock，读起来像在写一个物体。**

**609. `--background` 下相对输出路径不按 cwd 解析，按**盘根**解析 —— 而 `wrote` 会照报（Phase 141）**

`preview_gltf.py` 用相对路径渲三张图，三行都打印 `wrote <相对路径>`，**一张都没落在给的目录里**：
它们被写到 `C:\_tools\_attic\scratch\renders_em\`（目录是 Blender 自己建的），
而 `os.getcwd()` 全程报 `D:\rblxTRGproject`。
（补充读数：**只给文件名**时它反而**抛** `RuntimeError: … cannot save: 'C:\rel_after_save.png'` ——
所以同一个错有两张脸，**带目录的静默、不带目录的响**。）
修法只在**决定字节去哪**的那一处做 `os.path.abspath`，两条路都做。
这一条与 §0.26 ① 同族但方向相反：那一条说「**它通过了，但不是因为被测的东西在场**」，
这一条说「**它成功了，但不是因为你给的路对**」——
**"成功"这个词在被测的是一句承诺（我写这里了）时，什么也没证明。**


**610. 一个**已知常数**，只在交付的那一句话里没被用上，它就等于不存在（Phase 141）**

`10 / STUDS_PER_UNIT = 1.6943` —— **glTF 那条路进 Studio 会放大 1.6943 倍**，
这是 Phase 83 亲手量的，`docs/TODO.md` §3.5 那两条写的是
「**必须导 FBX**：glTF 那条路进 Studio 是 1.6943 倍（10 / 5.902）」，
`PROGRESS` / `DECISIONS_2` / `README` 里一共引用了**十几处**，
连 `PHASES.md` 里都有两遍。
而这一轮我写交付说明时，仍然写成「`.glb` 1:1，拖进 Studio 直接等于原尺寸」——
**因为 Blender 里它是 1:1**，那句话在 Blender 的坐标系里为真。
**操作员的约束恰恰是 Studio 里的尺寸。** 于是那条**唯一会毁掉交付的东西**，
在仓库里写了十几遍、在交付物的那一句里一次都没出现。

形态与 §0.36 同族（骗的是**写**的那一半），但比它更窄：
§0.36 是**两个数里混进一个没量过的**，这一条是**一个量过的数在旁边那句里没被用上**。
判据也很难自己红 —— 检查跑的是**文件对文件**（GLB 对 GLB、FBX 对 FBX），
**两条路都过**，因为它们量的都是 Blender 单位。
**可复用的问句：这句话里的单位，是被测的那个坐标系里的单位吗？**
（同 §0.18 第五张脸：一个词如果替你做了选择，你读到的就不是测量 ——
这里那个词是「1:1」。）



**611. 一个「两边应当相同」的对照，最值得报的不是「相同」，是**它们差多少、差在什么单位上**（Phase 142）**

`gui.py` 的压力递推是 `calculation.py` 的手抄件，两万拍逐拍对照的结果是：
**两边确实不一样** —— 差 `5.82077e-11`，而那是读数 `396031` 的**一个 ulp**。
原因不是模型分歧，是 `sum()`（CPython 3.12+ 的补偿和）与 `a+b+c+d` 的裸链（取舍 585 同族）。
所以「一致」这个词在这里有两种写法：**逐位相同**（做不到，也不该要求）
和**差在可解释的最小单位上**（做到了，并且量出来了）。

做法上有三条，都是为了让"容差"不变成橡皮图章：
**① 容差要有推导**（每拍固定次数的舍入，随拍数与读数大小增长，不是拍一个 1e-9）；
**② 每次运行都打印量到的差**，包括为 0 的那些运行 ——「额度没用上」是读数，"通过了"不是；
**③ 同时报 ulp 数**：`5.8e-11` 单独没有意义（大读数下的一个 ulp 和小读数下的一万个 ulp 同形），
`1 ulp` 才有。**同族于 §0.21**：一个数只有配上它的单位/分母才是测量。

**612. 对照之前先断言「在场」：没有一拍走到的表项，是这条检查**没测**的那个常数**（Phase 142）

两边的三张表各有 3 / 3 / 4 个键，风扇有 7 档 —— 但**随机游走不保证走遍**。
于是 `(State, fan, PEA)` 做成 **3 × 7 × 4 = 84 的全交叉**，先断言 84 个组合都真的用过，
再说"两万拍一致"。这是 §0.31 ① 的直接应用：**要让它红，得先有什么在场**；
而"那个键没被走到"和"那个键两边相同"在输出里**逐字同形**（都只会缺席，不会报错）。
同族的反向检查也写了：温度真的跨了三段、Pressure 真的积累了 1e5 以上 ——
否则一个悄悄跑空的 sweep 会以全绿收场。

**613. 对照器看不见「两边一起错」—— 所以结构性那几条要一份**第三拼写**（Phase 142）

parity check 能抓住**分歧**，抓不住**共同的缺陷**。于是状态机的四条
（`5600` 属于 1、`17500` 属于 2、`29499` 属于 2 而 `29499.0001` 属于 3、
**冷读数不复位锁存状态**）在对照器里是**第三遍转写** `stated_state()`，
**不回头调任何一个 driver** —— 与 `core_model_check.py` 那条老规矩同源
（那份文件头写的也是"不 re-run gui.py 的算术去和它自己比"）。
**一个对照器能证明的，永远只是"两个拼法在这个输入上没有分开"。**

**614. 突变的对面是**空突变**：它必须仍然绿，否则量的是模块不是模型（Phase 142）

六个突变（三个表项、`FAN_DRAG`、`STATE_2_MAX`、参考侧的表项）都被抓到，
并报出**第一次红在第几拍**。第七条是空突变：把 `gui.BANDS` 换成一份等价副本 ——
`tick` 根本不读它，所以**必须仍然绿**。
这是 §0.33 ②「两种 HOLE、修法方向相反」的第三条腿：
"改到的那条路"既要用**红**证明它被量到（正突变），也要用**绿**证明它不被误量（空突变）。
只有红的那一半，一个"什么都红"的仪器也能通过。

**615. 存档里的那段文案，不一定是玩家看到的那段（Phase 143，2026-10-18）**

`changes.log` 每行是 `路径 | 旧 | 新`。这一轮发现原版会**在运行时把作者存下的文案改写一遍**：

- `ErrorFrame.Frame.DescLabel.Text`：`FATAL SYSTEM ERROR` → `MAINFRAME CONNECTION LOST`（4 台）
- `ErrorFrame.Frame.InfoLabel.Text`：`…CHIEF INSTALLATION TECHNICIAN PERSONNEL. [ABSOLUTE SERVICE DENIAL - 02]`
  → `…SYSTEMS MAINTENANCE PERSONNEL. [ABSOLUTE SERVICE DENIAL - 03]`（3 台）
- `Thermal…MalfunctionFrame` 两行 + 两条 `TextColor3`：`SYSTEM ERROR` / `CANNOT IDENTIFY ROOT CAUSE`（红）
  → `PLEASE WAIT` / `AUTO RECALIBRATION IN PROGRESS`（琥珀 `1,0.698039,0.180392`）

我当场回 Studio 读回来，**逐字是"旧"那一列**。所以"place 里存着什么"和"屏幕上写着什么"
是**两个读数**，而它们在这里不相等。

**两条推论，第二条更容易踩：**
1. 要引用"玩家看到的字"，引的是日志行**右边那一半** —— 存档里那份是**兜底值**。
2. **`Visible=false` 的 frame 照样会被写。** 属性变化不看可见性，所以
   "这块从没亮过"**推不出**"这块的文案没被改过"。这一轮那两块浮层全程 `Visible=false`，
   而它们的 `Text` 在开机后被改写了两处。

**它在五份录像里的两份出现，两次都在点火窗口内**（判据两侧都取世界里的那一件 —
点火 = `Core.CORE.Transparency 1→0`，改写 = `ControlRoomMonitor…ErrorFrame…` 的行）：
`261001` 点火 `129.98` / 改写首行 `129.98`（同刻，**63 行，持续 10.7 s**）；
`261011-074207` 点火 `2288.86` / 改写首行 `2290.82`（**+1.96 s，14 行，持续 0.44 s**）。
而**另两次点火没有它**（`260930` `92.50`、`261002` `97.72`，控制室 `ErrorFrame` 各 0 行）。
所以「每局都这样」和「只发生过一次」**两句话都不成立**：**触发条件未知，方向固定**。

**这一条我写错过两遍，两次都是同一个方向：先认了一个数，再给它配一个解释。**
第一遍写"只有一份录像有"——把 `MonitorsFacility.*` 那 **74** 行当成全部，
漏了 `261011-074207` 里控制室那七台自己的 **14** 行（该文件 `ErrorFrame` 共 88 行）。
第二遍把 `2290.92`（同秒里的**第二行改写**）当成了点火时刻，于是读成"改写早 0.10 s"，
而世界里的核心在 `2288.86` 就已经亮了；同族的 `98.19` 也不是点火，是**主屏
`ReactorDiagramFrame.Core`** 亮的时刻（世界里的核心在 `97.72`）—— **两个不同的 Core**。
这就是 §621 那条的两次现身：**一个为 0 的数先问它在数什么；
一个为"只有一处"或"两件事相差 0.1 秒"的结论，也先问它数的是什么**（取舍 621）。

**616. 一个 TODO 条目可以**关于一个不存在的世界**（Phase 143）

`docs/TODO.md` §3.5 挂着一条「`LaserPort` / `TransitionPillar` / `RadiationScrubberUnit`
要按设计重量一遍尺寸」。这一轮去量，三件**一件都不在** DataModel 里（24 万后代按名字找、
外加按 Phase 83 记下来的轴线周围 12 studs 找位置）。
**所以它不是"还没做"，是没有可做的对象。** 一条挂了很久的欠账，可能从头到尾**没有一个宾语**。

**连带的那个数字更值得记**：`find("Pillar")` 命中 **120**，`find("TransitionPillar")` 命中 **0**。
只看前一个，"这东西在场"就是一个**看起来有证据**的结论 —— 而那 120 个是
`BasePillar / PillarThing / RadPillar / PillarVents / PillarNeon`，**场景装饰**。
**子串搜索返回的是一个数，不是一次识别。**

**617. 空的量不是过，是不适用（Phase 143）**

上一条那个 0，**不能**读成"三件设备的尺寸是对的"。它读成的是：这个量在这份 place 里
**没有被定义**。§0.31 ③ 说的是"值可以进检查的正文，不能进检查的地址"；
这一条是它的兄弟：**主语不在场时，断言既不为真也不为假。**
要写的是「这轮只读了当前这一个 DataModel」这个**边界**，不是一个绿勾。

**618. 「同拍同刻」证明的是**显示**的规则，不是**原因**（Phase 143）

泵图标变红 ⟺ Thermal 的 `MalfunctionFrame` 亮，**4/4 逐拍同刻**
（`239.29/239.29`、`247.15/247.15`、`394.79/394.79`、`422.60/422.60`）。
这条是硬的，可以照着实现一个**显示**层。而**什么让它变红**仍然是未知的 ——
五份录像里没有记到能反推出输入的量。
**把这两句话分开写**：一句是量到的，一句是没有的。合在一起写（"横幅表示泵故障"）
读起来像后者也被证过，而它没有。

**619. 把永久故障接到瞬时横幅上，得到的是**另一件东西**（Phase 143）

录像里那三台泵**同时变红、8 s / 28 s 后同时回白**。本引擎的泵故障是
`integrity == 0` 的**永久**失败（`Engine.luau:258` 之后 `enabled=false`，只有 `repair_pump` 能回来）。
拿 `integrity <= 25` 去驱动那块浮层，画面上会是一块**永不熄灭**的横幅。
**"接上了"和"复刻了"不是同一件事** —— 前者的判据是"有东西动了"，后者的判据是
"在同一个输入下，它和原版一起动、一起停"（§0.26 ① 的正向版本）。
要接，先得把瞬时跳闸做出来；而那是改玩法，§1.4 第 1 条禁止。

**620. 构造上不可达的分支，写它就是写常数（Phase 143）**

`ShutdownFrame.ShutdownText` 有两个作者写好的值：`ENERGY QUOTA MET`（绿）和
`REACTOR ENERGY QUOTA NOT MET`（红）。录像里原版两个都用过。
而在本引擎里，`Engine.luau:143` 的 `shutdown` 动作**自己就以 `energy >= quota` 为前提** ——
所以走到 `Stopping`/`Report` 时配额**必然已达成**，第二个值是**构造上不可达**的。

写一条"按 quota 选文案"的代码，语法、类型、运行全对，**永远只走真分支**。
这是 §0.31 ① 的镜像：那一条问"要让它红得先有什么在场"，
这一条问"**要让它走另一个分支，得先有什么存在**"—— 答不上来，那个分支就是装饰。

**621. 数不存在的文件，结果也是 0（Phase 143）**

我写了一个逐份录像统计的小循环，`261011-084400` 那一行报出 `0 monitor events / 0 ErrorFrame`——
而那个目录里**根本没有 `changes.log`**（它是 `inventory.txt` / `summary.txt` 那种捕获）。
**"这份录像没有这类事件"和"这份录像不存在"在计数输出里逐字同形。**
修法是把行数本身也印出来，或者先断言文件在。
同族 §0.20（按边数给面分类，回答的是文件格式）：**一个为 0 的数，先问它在数什么。**

**622. 同一块浮层可以有两个不相干的触发，而"它从没亮过"是一个**路径层级**的错误（Phase 143）

`ErrorFrame` 这一轮被读了三次，前两次都读成"从来没亮过"，第三次才对：

1. 第一次数的是 `MonitorsFacility.*` 那一族，得出"只有一份录像有这些行"；
2. 第二次数对了文件，却在**同一秒里读第二行改写**当成了点火时刻，得出"改写早 0.10 s"；
3. 第三次逐层数 `Visible`，才看见 **`261001` 点火同刻 29 块屏一起亮、10.70 s 后一起灭**。

**第三次才对的原因已经查出来了，而且它不是"看漏"：那条清单被 `head -30` 截断了。**
`docs/SNIPPETS.md` §5.47 ② 那条 recipe 是
`… | sort | uniq -c | sort -rn | head -30`，而 `ErrorFrame.Visible` 在七份屏上各一行、
`false→true` 与 `true→false` 分成两条，**每条计数 7** —— 按计数排序落在第 30 名以外。
**清单里没有它，不是因为它不在，是因为清单只有 30 行。**
（同族 §621：一个为 0 的数先问它在数什么；这里更坏一层：**数是对的，显示被截断了**，
而"截断的清单"和"完整的清单"在屏幕上逐字同形。`head`/`tail`/`--top` 这类参数
应当**和它截掉了多少一起打印**，或者干脆别截。）

**更要紧的是第四层**：这块浮层在**两族屏上各有一个触发**，而且形态完全相反 ——

| 屏 | 何时亮 | 亮多久 | 形态 |
|---|---|---|---|
| 控制室 7 块 | 点火同刻（`261001` `129.98`）| **10.70 s** | 七块**同步**、一次 |
| 设施 22 块（`261001`）| 同上 | 10.70 s | 同步 |
| 设施 10 块（`261011-074207`）| `2201.98`（点火前 87 s）| **107.9–112.0 s** | **逐块**崩溃-修复 |

同一块浮层、同一句文案，**一个是"全场一起闪一下"，一个是"这块屏自己坏了再修好"**。
把前者的触发条件写进复刻，会在错误的时间点亮 22 块屏；
把后者写进去，会得到一块亮 110 秒的假故障。**共用美术 ≠ 共用触发。**
（复刻侧结论不变：**不接** —— 控制室那七块五局只亮一局，触发条件仍然未知。）

**623. 同一件仪器服务的第二张图，用参数指过去，不复制一份（Phase 144）

`cover_layers.sh` / `cover_mark_check.py` 里各有四个数（页面、尺寸、成品路径；盒子原点与边长）
是**封面这一张图**的坐标。16:9 那一页需要同一个问题（"这层装饰到底改了像素吗"、
"厂标是不是这张素材"），于是有两条路：复制成 `page_layers.sh` / `page_mark_check.py`，
或者让那四个数可覆盖。

**选后者，理由是这两台仪器的价值恰好在于"文档引用的那个命令"和"实际跑的那个命令"是同一句话。**
复制之后它们会慢慢分开 —— 探头判据、阈值、报错文本各改一处，然后某一天文档引用的是 A、
运行用的是 B，而两边在盘上长得一模一样（§0.35 的同族：**"它跑过了"与"它跑的是它"**）。
默认值一律是封面那一套，所以旧命令一个字都不用改；改完当场重跑了封面：
**逐字节相同**（`5bd615a7…` / 496559 B），四层计数 188752/542/147910/663604 一个没变。

**版面判据反而没有共用，那是另一回事**：`cover_judge.js` 的规则是照着"方画面里六边被
上面一道框、下面一串字夹住"写的；16:9 里六边是被**右边那一列字**夹住的。
把 A5 改个名字搬过去，会得到一条**看起来一样、量的不是另一件事**的规则（§0.18 第五张脸）。
所以 `page_judge.js` 是新的一份，规则号 W0..W10 —— 但**同一句断言在两份里逐字相同**
（W1 按名字点四样、W3 要近失、W6/W7 两个六边形同形、W8 极性、W9 厂标在六边内）。
共用的是**问句**，不是实现。

**624. 16:9 不是把方图居中 —— 而"两行标题"是排版决定，不是测量结论（Phase 144）

1920×1080 里居中塞一个 1080 方图，左右各 420 px 黑边；在 Roblox 的缩略图/横幅里，
那不是"留白"，那是**一张没做完的图**。所以这一页是**重排**：六边左置（中心 x=640）、
字右置（左沿 1030）、页脚压底，四样东西一样没多、一样没少。

**标题必须分行，而这是一个选择。** 右边那一列只有 864 px；一行 `THE REACTOR GAME` 在这台
机器上（`Arial Narrow` 不在，落到 `Impact` 一族）116 px 量到 **1088 px**，装不下；
缩到 92 px 装得下，但 1/5 缩略图上只剩一行细字。两行 116 px 每行都撑满 —— 代价是**锁印和
1:1 封面不同形**。这一条**没有被测量支持**，它是排版决定，写下来是为了让下一个人知道
"两行"不是从某个数推出来的（与 Phase 133 那句"厂标比实拍更合适没有测量支持"同族）。

**判据跟着换了一个量**：不量字号，量**行距**（`titleLines[1].top - titleLines[0].top`
= 110.19 px）。理由是缩略图上读者拿到的就是这个数（1/5 → 22.04 px），而 CSS 的 116 px
既不等于墨高、也不等于行距 —— 量字号等于量一个读者从来拿不到的量。

**625. 两块字"相撞"要看它量的是哪一层盒子；而同一个行盒子会被量两次（Phase 144）

两行标题把 `glyphBox()` 的一个老前提打穿了：

**① 字体框 ≠ 墨迹。** 徽章的 Range 盒子是 **392..414**，标题第一行的 Range 盒子是
**429..560**，两者差 **15 px** —— 而真正的墨迹：徽章那条琥珀边框的最低一像素在 **420**、
标题最高一个白像素在 **452**，中间隔着 **32 px 的空气**（拿成品 PNG 逐像素量的）。
所以"相撞"这条规则按**字体框**写、参数按**真实版面**定：字体框只差 15 px 时规则是**有牙的**
（再往下挪 15 px 就真的撞了），而画上仍然宽松。**反过来把阈值放宽到"看起来还有 30 px"
会让这条规则对真正的碰撞失灵。**

**② `getClientRects()` 把每一行返回两遍。** Range 跨了 `<span>` 和它的父元素，
于是同一行盒子出现两次（`[429..560]` 各一份）。不去重的话"最窄的一行"会被同一行投两次票，
读数看起来完全正常 —— 同 §0.20 ②：**数出来的数先问数的是谁**。去重按几何
（四个坐标拼成键），不按顺序。

**顺带记一条不是缺陷的**：`line-height: .95` 让**行盒子互相重叠**（第一行 429..560、
第二行 539..670）。这不是错 —— 重叠的是字体框，不是墨。任何"两行不许重叠"的断言
在这里恒红，而它红的原因跟版面无关。

**626. 同一条缺陷写两个读数时，每条读数各要一个单独的突变（Phase 144）

W2 说"每一块字都在框内"，W4 说"标题的**每一行**都在右框内"。第一次写突变时，
我只把 `text.title.right` 推出框外 —— 结果只有 W2 红，**W4 一个字都没动**，
因为 W4 读的是 `titleLines`。那条突变于是证明了 W2 的牙，**没有证明 W4 的牙**。

修法是把突变拆成两条：一条动整个文字块（打 W2），一条**只动 `titleLines[0].right`**
（打 W4）。这与 §592 那条"一条走过两次的规格，两个读数都要有牙"同形 ——
在这里，**同一条缺陷有两个读数**（块 / 行），所以也要两条突变。
`--selftest` 现在报 **17/17**，其中两条各红两条规则，其余各自红一条。

**627. 一个截图 API 返回 1，不代表它画了任何东西 —— 而守卫要量"它该画的那一块"（Phase 145）

`PrintWindow(PW_RENDERFULLCONTENT)` 对 Tk 的 toplevel **返回 1，位图里客户区是平的**。
不是 API 坏了，是 **Tk 不处理 `WM_PRINT`** —— 直接发 `WM_PRINT`（两组 flag 都试）同样
返回 1、位图一个像素没动。所以"返回成功"与"没画"在旧输出里**逐字同形**。

同时，旧守卫数的是**整帧**的颜色数：**标题栏自己就是 710 色、亮度 0..255**。
"这里有一个窗口"被当成了"控制台在这上面"。**修法两半**：
守卫改读**裁掉标题栏的客户区**；再按 6 条横带各数一次，任何一带 **<8 色**就红。

可复用的一句话：**当一个 API 的返回值是"我照办了"，而你要的证据是"东西画出来了"，
判据必须落在那个东西本来该出现的矩形里**（§0.31 的"在场"问句换了个位置）。

**628. 两个坐标系差一个屏幕缩放时，唯一的线索是"同一个控件给出两个数"（Phase 145）

进程是 **DPI-unaware** 的：Tk/`GetWindowRect` 报**虚拟化**坐标，`ImageGrab` 读**物理像素**。
表现不是报错，而是**数值列整个不在画上**（窗口物理宽 1305，只抓了 1044）。
抓住它的是一个**已知控件的 x**：Tk 说 **501**，图上是 **623**，比值 **1.25** ——
而屏幕 `GetSystemMetrics` 报 1728×1152、物理 2160×1440，同一个 1.25。

修法：**任何 HWND 出现之前** `SetProcessDpiAwareness(2)`（退路 `SetProcessDPIAware`），
并把**实际拿到的级别打印出来**，因为"我设了"和"它生效了"是两件事（§0.3/§0.15 同族）。
**这条也解释了为什么"某一块没画"这种结论必须先量一个已知位置**：
版面是对的，错的是**取像素的那把尺子**（§0.18 第 5 张脸：尺子替你选了坐标系）。

**629. Tk 在桌面外也会抢焦点；而"没出现在屏幕上"不等于"没打扰他"（Phase 145）

窗口映射在 `+20000+20000`，Tk **照样带激活** —— 截图前读 `GetForegroundWindow()`，
前台已经是控制台自己。于是旧的"窗口从不闪到他屏幕上"是**真的**，
**而他的键盘焦点已经被拿走过一次**。

现在的顺序：**建窗口之前**记前台 HWND → 拍完销毁 → `SetForegroundWindow` 还回去 →
**读回来**验证（并把失败写进 rc）。**"我没有打扰他"是一个读数，不是一个形容词**
（同 §0.31：要让它红，得先有什么在场 —— 这里的"在场"是那个旧 HWND）。

**630. 网页上那个框的长宽比不是素材的规格；而"卡片上还是灰占位符"可能是 `Pending`（Phase 146）

Roblox 的 Game details 页：图标格 **247×216（1.14）**、宣传图格 **451×225（2.0044）** ——
而官方规格是 **16:9**，并且上传后**按 16:9 拉伸**（不是居中裁切）。**两个数都对，
因为它们量的不是一件事**（§0.18 第 5 张脸：这一次替你选的是"框"）。
验的顺序：先排除**截图本身**被非均匀拉伸（两支铅笔按钮 **22×22，比例 1.0**），
再看卡片（右卡 525×263 = **1.996**）⇒ 2:1 是**网页版位**。
**"按框做素材"会把 16:9 的图做成 2:1**，而它传上去仍会被拉回 16:9 —— 错的不是尺寸，是那个框的语义。

第二条：`thumbnails.roblox.com/v1/places/gameicons` 在上传后先回 **`state:"Pending"`**、
随后 `Completed`。所以**页面上那一刻的灰菱形读不出"没传上"**。判据是 `state` **加**
把图下载下来**比像素**（线上 512 与我们封面缩到 512 平均差 **1.07/255**；
另一份 place 同法是 **33.28**）—— **"像不像"要一个对照数**，否则两个数在眼里都是"差不多"。
负面同理要两样一起说：**没有自定义缩略图** = 「multiget 只回 **1** 条」
**且**「那条是占位符」（364 色 / 亮度 **26..56**）。单看"有几条"不够。

**631. 水密性问的是**奇偶**，不是「每条边正好用两次」（Phase 147）

CBL Mk4 的重新导入检查器第一版把「边没用满 2 次」算作洞，Body 报 **48 个洞**。
实测那 48 条**全在 x = 23.36**（设计 `X_SHROUD1`），每条被用 **4** 次 —— 整流罩车削的
`cap_top` 与孔径喇叭车削的 `cap_bottom` 是**两片 48 边形盖**，同一站点、同一半径、面对面、
法线相反、在内部、看不见。**闭合曲面每条边被用偶数次**；「多出来的一次」不是洞。
判据改成奇偶，`>2` 单独报成 `doubled` 当诊断（Body 现在读 `welded open=0 doubled=48`）。
**改的是问题，不是容差** —— `TOL` 一个字节没动。同族：§0.18（错的量法不报错）、
§0.31（判据能因为别的原因红/绿）。

**632. 跨格式只比「局部尺寸 + 三角数」会放过平移；世界盒是免费的第二个数（Phase 147）

`fbx vs glb` 那一行的目的是抓「两个导出器交付了不是一个东西」。`split` 突变只让 FBX 里的
Prongs 多平移 0.5 设计 stud —— 局部 `Size` 不变、三角数不变，**三个检查点全绿**。
把每件的**世界包围盒**也存进同一行之后，它红在 `box 0.5000 studs`。
一个未被平移的件，世界盒仍然值得带着：它是操作员在 Studio 里摆位所依赖的那两个数。
（这一条也是 §0.31 ① 的反面：**判据能因为别的原因通过**。）

**633. 突变体要从交付的 `.blend` 出发，而且要有一个先绿的控制组（Phase 147）

`mk4_mutate.py` 打开交付的 `.blend`、注入一个缺陷、走**同一套导出器**重导 ——
于是红的那一行不可能被归咎于「测试造了个怪文件」。`none` 突变不注入任何东西，
必须复现 **86 / 0**；控制组一红，下面每一条突变都失去意义。
七条突变各自红在不同的判据上（节点集合 / 装配盒 / 材质集合 / 三角数 / 两种水密 / 世界盒），
**每一族断言都至少见过自己失败一次**（§0.35：报告失败之前，先证明失败者真的在场）。

**634. 材质匹配按**绝对尺寸**，不拟合比例 —— 拟合会把区分两行的那个差消掉（Phase 147）

第一版 `bestRow` 拟合一个自由的整体比例 k，于是 **Core/Cyan（42.81）与 Core/White（41.28）
分不开**：精确尺寸下得分 **0.0000 vs 0.0171**，余量 0.02，判 AMBIGUOUS（13 行里 3 行没涂上）。
原因不是余量太小，是**这两行几乎只差大小，而拟合 k 恰好把大小归一掉了**（§0.18 同族）。
k 强制为 1 后同一对差 **0.043**。导入比例本来就不是未知量（操作员填 5.902），
所以「尺寸对不上」应当报**导错了**，并把**隐含比例**写进那一行 —— `.glb` 那条 1.6943 倍的错路
于是会自己报出自己的比例，而不是安静地涂错颜色。k 仍然算，但只当诊断（`ScaleWarn`）。

**635. `.glb` 逐字节稳定，`.fbx` 不稳定 —— 交付物只能按几何验（Phase 147）

同一次构建重复跑：`.glb` 的 md5 每次都是 `e1980dcedff7cb43a2f442e8797d1d62`；
`.fbx` 913180 字节里**每次有 339 个字节不同**，落在稀疏的 4 字节字段上（创建时间 / UID）。
所以 **FBX 没有可比的字节**：交付证明只能是「重新导入 + 量盒子/三角数/原点」，
不是哈希。反过来说，`.glb` 的哈希是可用的 —— 但**两个格式的命运不同，不许互相外推**
（§0.14 同族：两次之间不能互推）。

**636. `bevel(material=-1)` 是材质槽 0，不是「沿用原面」；而重复的旋转体端点会长出零面积面（Phase 147）

(a) `bmesh.ops.bevel` 新生成的面全落到材质槽 0（Hull），于是 Mk4 的枪口整件变成壳色，
而**三角数、尺寸、包围盒、水密性全对**。修法是把倒角面按邻近原面的材质重新归属；
防线是 `CONTROL_MATERIALS`：关掉 bevel 再跑一遍，逐材质面数必须一致（78 ok / 0 failed）。
(b) `trg.revolve` 的轮廓首尾同点，环带生成了 **8468 个零面积三角形** ——
不改包围盒、不影响渲染、不报错，但在 Studio 里是脏几何。修法在 `revolve` 里去重端点。
两条都是**构建侧完全看不见、出厂文件里才存在**的缺陷（§0.37 ④ 同族）。

**637. 检查器读的那份构建日志，必须和交付的字节出自同一趟（Phase 147）

材质尺寸表在日志里，而日志会被重跑覆盖。第一版 `check_mk4_mat_table.py` 读到的是一份
**22:18 的旧日志**（交付文件是 22:44）：`tris_total=69980`、Body 25304 tris、Prongs 上还挂着
Hull 材质 —— 三个数都不对，而它们**看起来完全合理**。所以检查器现在把「日志比交付 `.fbx` 旧」
当成一条**会红的检查**（`build log is from the delivered run`），
失败时直接说「重跑构建并捕获日志」。**表和它描述的那份字节必须是同一趟产物**（§0.37 ④）。

**638. 预览图是判断，不是读数；但没有它，判断就没有输入（Phase 147）

四张预览（hero / side / muzzle / rear）是这个资产唯一「像不像一件事」的证据；
所有数字（尺寸、三角、材质盒、水密）加起来都不能回答「帅不帅」。
`hero` 实看一眼：开窗里能看到螺旋管、爪兜住发亮的孔径、尾闩的三只电容鼓在轮廓里 ——
三处设计改动**都在画上**。**"看一下"和"量一下"两样都要**（§0.14b）：图证明看起来对，
读数证明真的是那个值。

**639. 同一页上的两套数：判据是「哪一套能复现它自己的算例」，不是「哪一套更像权重」（Phase 148）

wiki 的温度页一边写系数 `0.756 / 0.522 / 0.196`（和 **1.474**），一边在散文里写
`51.3 / 35.4 / 13.3`（和 **1.0**）。**"权重通常和为一"是一条很强的先验**，
所以最容易写的错误版本就是拿百分比当系数。分开的不是先验，是**它自己的算例**：
百分比在 (100,25,25) 上给 63.475 → 约 304 F/s，而同一页写的是 ~580。
**一个文档自相矛盾时，能把它自己的例子算对的那一套是正文，另一套是描述。**

**640. 两个例子才能分开两个候选；单看一个，错的读法会因为别的原因通过（Phase 148）

平均与加权在 (100,25,25) 上差 **360.66 度**，但在 (25,25,100) 上只差约 10 度 ——
**平均几乎复现第二个例子**。所以「我核对了 wiki 的例子」这句话，
如果只核对了第二个，它和"没核对"在盘上是同一件事（CLAUDE.md 0.31 ① 的反面：
**能因为别的原因成功的判据，也不是实验**）。判据写成**一对数**、
并且把"平均分不开这一对"和"平均落在第二个例子旁边"各写成一条断言。

**641. 越过拟合带的部分带着、不夹紧 —— 夹紧是造一个源里没有的数（Phase 148）

加权之后 `a_eff` 的天花板是 **184.25**（三台全 PW5），而操作员那条拟合只在
25..125 上做过。夹到 125 会让"三台满档"和"两台半满"给出同一个热 ——
一个 wiki 里不存在的等式。**带着它、并在文档和问号里标明这是外推**（0.21 第 3 条）：
读数单调、方向对，但它的数值是式子给的，不是量到的。
这一条把 R9 ② 在低端关掉的**同一类**问题在高端重新打开了，写进 `QUESTIONS.md`。

**642. 突变器抓到了检查器自己的一条真空断言（Phase 148）

`check("one press takes the wiki's ~7000", dropped, gui.E_VENT_DROP)` ——
**拿结果去比产生它的那个常数**。把常数改成 6500，`dropped` 跟着变成 6500，这条**仍然绿**；
真正红的是旁边那条温度断言（20000 → 13500 ≠ 13000）。
这是 0.31 ① 在**我们自己的检查器**里的形态：**让这条红，需要什么在场？**
答案原来是"什么都不需要"。改成字面 `7000.0` 之后突变器才把它点亮。
**值得记的不是这一条，是抓到它的方式**：没有突变器，282 项全绿会一直看起来很好。

**643. 熔毁写成锁存，不写成第四行 —— 因为 `core_state()` 的返回域是别人的索引（Phase 148）

wiki 说 39,000 以上「温度不再重要」。把它写成 `core_state` 的第 4 档会让
`PASSIVE_ROW` 和压力表**同时越界** —— 两个消费者把那个返回值当 0..3 索引。
所以是 `Core.melted` 这个独立的旗子：跨越那一拍照常报告温度（最后一个诚实的读数），
之后 `step()` 返回 `None`。而 `CORE_MELTDOWN_AT = 39000 < TEMP_MAX = 40000`
是构造上的选择：**停住模型的是墙，不是滑块** —— 上一轮"温度会跑过滑块顶"那条断言
因此改写成"是哪一堵墙停住的"，比原来更强（它还断言面板显示 `4 MELTDOWN`）。

**644. E-Vent 与 AVB 是两台设备：「不碰压力」和「没降是 0、用过了是 `None`」都是判据（Phase 148）

AVB 降**压力**、靠失速间接降温；E-Vent 直接降**温度**、一声不响（wiki 没有任何一页说它动压力）。
把两者当成"两种排气"是这一轮最容易犯的错，所以检查器断言 `Pressure` 前后**逐位相同**。
第二条：同一个开关第二次按返回 **`None`**，不是 **0** ——
0 是一个合法的"这次没降"（3000 度时钳位之后仍可能接近 0），
用 0 表示"用过了"会把这个设备的两件事压成一个数（同 0.26 ②：`and/or` 吞掉 `false` 的家族）。


**645. 图标不是封面的缩小版：三样东西，而且「体现 Continuation」要落成两条能红的判据（Phase 149）

操作员的三个约束（1:1 / 别太复杂 / 要体现 Continuation）落成三个决定：**主体换成这个项目
自己的记号**（不闭合的六边 + 缺口里的箭头 + 芯）、**封面的徽章与页脚不搬过来**（四样 → 三样）、
以及**把「体现」写成 C7/C8**。C7 量缺口（占半径 12%..55%）、箭尖到笔画起点的距离（≥8 且 < 缺口）、
箭尖是否在那条边线上；C8 量箭头方向与圈的行进方向的点积（=1）。
**这两个失败在 64 px 上都还像一个好好的图标** —— 闭合的六边只是"一个六边"，
翻转的箭头只是"一个箭头"。判据不替代审美判断，但它把"图在说什么"从眼里挪到了读数上。

**646. 「Continuation」的最小图形写法：缺口必须被量成**没被箭头填掉**（Phase 149）

第一版只量了 `gap`（笔画两端 A 到 B 的距离）。但箭头可以**长到把缺口填满**，那时 `gap`
一点不动，画上却是一个闭合的圈。所以读数改成 **tip-to-start**：箭尖到笔画起点的距离，
并要求它 **< gap**（头在缺口里）且 **≥ 8**（头没有把圈接上）。
**同一个几何量有两个候选读数时，选那个会因缺陷而改变的量**
（§0.31 ① 的反面：一个量如果**不因被测的缺陷而改变**，它就不是那个缺陷的判据）。

**647. 512 是判定过的那一帧的确定性函数，不是第二个没被判过的渲染（Phase 149）

Roblox 图标吃 512，母版是 1024。交付的 512 是母版的 LANCZOS 降采样 ——
**判据跑在 1024 上，降采样是确定性变换，所以 512 继承那 12 条绿**。
原生 512 渲染字更锐（`mean |diff|` 1.40/255，3.1% 的像素差 > 8，都在字的边缘），
但**它没有过判据**；把它当交付物就等于把"看过"当"量过"。
**换过 `--w/--h` 的渲染，报告里每一个坐标都是另一个空间的**（C0 就是为这个写的）。

**648. 字体栈解析到哪一个字是一个读数；「X 不在」这种解释也要量（Phase 149，更正 Phase 144）

同一串字在六个候选家族里各量一次宽度：没装的家族会和 fallback 给出**同一个数**。
这一页 `var(--cond)` = **982.38**，逐位等于 `"Arial Narrow"` 的 982.38 ⇒ 它在，且就是这一页的大字。
回看 Phase 144：116 px 的同一行今天在 Arial Narrow 上是 **1088.7**，而那天量到 **1088.55**
—— **读数对，解释错**（"Arial Narrow 不在、落到 Impact"）。四个候选里最窄的 Impact 也要 976 > 864，
所以两行那个决定不受影响。**"缺失"是一个可以被量到的断言**（§0.6「探条只探它探的那件事」同族）。

**649. 没有素材的页面必须说"没有素材"，不能打一张别的画的表（Phase 149）

`cover_layer_probe.py` 的极性表原来硬编码封面那两张素材，于是拿它跑一个纯 SVG 的页面时，
它会**打印两张不在这张画上的素材的极性**。这不是空集合说两次谎（§0.20），
是**一张关于另一张画的表**。`ASSETS=""` 现在打印「这一页没有位图素材，没有可量的」。
默认值不变，所以旧命令仍然指同一件事。**仪器的宾语换了，读数也必须跟着换。**

**650. 判据的"非真空"要按名字点这一页真有的东西；规则退休要写理由（Phase 149）

C1 点了两行字（`CONTINUATION` / `THE REACTOR GAME`）和三个部件（圈 / 箭头 / 芯），
因为图标比封面空三倍，"没有东西相撞"在空页面上**更**容易白给（Phase 134 的 A1 同款）。
C10 里那条「至少要有一层声明真的素材极性」**跟着它的宾语退场**（这一页没有位图素材），
留下「声明与 filter 一致 + 至少有一层且都开着」。**一条规则的对象没了，它不会变空，它会变安静**
（取舍 572）。

**651. 同一份源、两个机器状态 → 两个各自稳定的渲染；跨状态复核只比像素（Phase 149）

这条是 **567 的加严版**，也是它在那之后被真正撞上的第一次。

| | 文件 | 批内 | 说明 |
|---|---|---|---|
| 00:24–00:26 | 535110 B / `2a3a83db…` | 2/2 相同 | 同一份 `cover/continuation.html`（mtime 00:24:37，之后没动过） |
| 00:29 以后 | 606769 B / `a0baba54…` | 9/9 相同 | 同一个命令、同一排 pin 住的 flag |

**跨状态差**：mean **0.705/255**、max **57**、**2191 个像素 Δ>8**（0.21%，Δ>16 是 658）；
同一对图缩到 64 px：mean 0.268、max **3**、**0 个像素 Δ>8**。

**机制没定，所以写没定**（同 §0.23 ③）：**强制软件**（`--disable-gpu`）和
**强制 GPU**（`--enable-gpu-rasterization --ignore-gpu-blocklist --use-angle=d3d11`）
**都给现在这一版** —— 旧那一版要不到。能说的是它的形状：差异铺在渐变与
`drop-shadow` 那些**大面积低振幅**的地方，加上字形/描边的抗锯齿边缘（max 57 落在小字的一个边上），
也就是**渲染管线那一侧**，不是几何（C6 的 0.004 px 两次都成立；判据读的是 DOM）。

三条规矩：
1. **"逐字节相同"只在一次机器状态内是真话。** `intro_render.js` 那句
   "two runs on THIS machine identical" 要读成"same machine state"；跨状态用 md5 认**这一次
   落盘的文件**，用**像素**认**这张画**。
2. **像素复核要有量级**，不能只说"看起来一样"：这次给的是 `mean 0.705/255, max 57, 0.21% > Δ8`，
   以及 64 px 上 `max 3 / 0 像素 > Δ8`。**没有量级的"差不多"就是没量**（Phase 132 的 1 像素同族，
   但**这一次不是 1 个像素就能打发的** —— 把 567 那句"DELTA=2 门槛下 0 px"直接搬过来会是错的）。
3. **别用"再渲一次比对"当 CI。** 一个会随机变红的复核判据比没有更坏（567 原话）。

取舍 567 / 全文 `PROGRESS.md` Phase 149「三、仪器」，配方 `docs/SNIPPETS.md` 5.52。
