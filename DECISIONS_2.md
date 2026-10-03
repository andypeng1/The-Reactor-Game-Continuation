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
