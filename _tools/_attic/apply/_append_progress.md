## Phase 40 - The six desks get raked registers, and the controls were leaning at double  [DONE]

Scope, from the user's instruction: after the CBL lasers' second pass, redo the consoles - including the
coolant calibration - then continue. The Mk2 desks were called ugly, and Main was the flattest of the
six: the other four carry raked control surfaces while Main laid its whole control row on the deck.

WHAT WAS MEASURED BEFORE ANYTHING WAS WRITTEN. ORIG_MainReactorConsole carries 113 parts at exactly
20.00 degrees about Z, and they run the desk's full 15-stud length. That is the original's idiom, and
it is what the eye reads as missing when the six desks are seen together. Deliberately NOT copied: a
full-deck rake. 4.10 studs of deck at 20 degrees rises 1.49 and drives into the instrument face at
Y 3.96, so on this desk the rake is a REGISTER - 1.55 deep, hinged at the deck's front edge, rising
0.56.

WHAT IT BUILDS. Three layers in BuildMainReactorConsole - RegPlate / RegRim / RegWell at +0.11 / +0.21
/ +0.25 over the rake line, the same stack deckModule lays for the other four desks - plus RegSkirt
closing the wedge behind the plate and a two-tone hazard bar along the front rim. The three layers are
INLINED rather than calling deckModule, which builds exactly that stack for the other four: deckModule
is declared further down the same chunk, so a call from here would resolve to nothing at all, and
inlining three parts is cheaper than reordering three shared builders that four other desks depend on.

The controls are then remounted in ONE pass over a table of seven (name, z) pairs, rather than teaching
buildLever / buildBigLever / buildButton / buildKeypad about rakes: those four also serve CBL, Electric,
Thermal and ALT, each at its own register depth, and four rake arguments would be four chances to
arrive at four different answers. The mount is a rigid re-expression - with A the deck point under a
control and P the register point above it, each part's new pose is P * (A^-1 * pose) - so every
assembly lands square on the slope, base flush and handle normal to the register. That is what the
original does with its own controls, its button axes measuring (0.34, 0.94, 0.00).

Tilting the levers is safe, and not by assumption: ControlVisuals captures both the hinge and the rest
pose FROM the part's CFrame at bind time and writes every swing as hinge * Angles(angle) *
inverse(hinge) * base, so a lever whose rest pose is already raked swings in the register's own frame.

THE DEFECT, AND HOW IT WAS FOUND. The first version wrote P * REG_ROT * (A^-1 * pose). P already
carries REG_ROT, so the rake was applied twice. It installed cleanly, passed a height check against an
independent baseline, resolved all seven dot paths, and looked plausible in a screenshot. What caught
it was measuring the angle: RegPlate read 20.00 degrees off vertical and EVERY control read 40.00, with
the buttons' flat-laid collars at 50.00 - which is 90 minus 40. The register was right and the controls
leaned at double. Fixed by dropping the second rotation and taking P on the register's own top surface,
from the plate's own numbers rather than a second copy of the rake arithmetic. Re-measured after:
every control part at 20.00 or 70.00, the 70.00 parts being cylinders whose AXIS measures 0.020 degrees
off the register normal. Recorded as DECISIONS 117.

Also fixed this phase, carried over from the CBL desk: rakeY returns an ABSOLUTE deck height, and the
CBL pressure pad fed it into a +Y translation as a delta, flying the pad 4.20 studs up and putting that
desk 2.03 studs over its riser. Now rakeY(X, frontX) - DECK_TOP.

ACCEPTANCE. MainReactorConsole: height 6.250 against the independent MK2PREV_MainReactorConsole_preBar
baseline, top at 282.833, seven dot paths resolving, no part at the 40.00 or 50.00 signature, and lever
base plates clearing the register's top face by exactly +0.0100 studs - the hundredth that stops a 0.22
base plate and a 0.22 register plate speckling into one another's plane. Two screenshots: the register
reads as a solid riser with the controls standing normal to it, matching the other four desks.

COOLANT CALIBRATION. ConsoleBinder binds coolant_recalibrate to ThermalConsole.CoolantControl<i>.BigLever,
whose LeverUnion sits at 20.00 on the raked register like every other control. It had no lamp state at
all, so applyLamp returned early and the lamp sat on its authored colour forever - a dead prop. It now
follows the atmosphere_vent branch exactly: spent while CoolantSystem's 30-second cooldown runs, ready
after. No STATES entry, deliberately - see DECISIONS 121.

HDEFGenerator was left alone on purpose. It is 4.65 x 7.38 x 1.38 - a cabinet, not a desk - with its own
frame carcass, glazed cell window, three power cells and brass cap band. A raked register is the desk
family's idiom, and bolting one onto a cabinet would be the style mismatch this pass exists to remove.

VERIFICATION, AND ITS LIMIT. The lamp branch was tested by extracting the shipped lampState text out of
the live module and running it against ten cases - 10 passed, 0 failed - including the 30-second
boundary, per-pump isolation, and the existing atmosphere_vent branches as a regression check. See
DECISIONS 118 for why the extracted text and not a retyped copy.

What could NOT be done is the simulated click. Workspace.StreamingEnabled is true and the place has one
SpawnLocation at (233, 402.9, 1370) - about 1400 studs from the control room and 120 studs below it - so
a playtest client has neither the console geometry nor a path to it: the client's Consoles folder held
97 descendants against thousands on the server, and ThermalConsole 42 against 651. A real click test
therefore also needs a spawn near the desks. The click bindings here are verified by dot-path resolution
and by the ClickParts' CanQuery, NOT by a mouse. Recorded so the next session does not read this as a
click-tested phase.

STILL OPEN. ServerStorage.Mk2Pass1 holds two superseded Main builds (PASS2TMP_MainReactorConsole and
PASS2FLAT_MainReactorConsole) and Mk2Stage holds NEW_MainReactorConsole; all three should be cleaned up
BY IDENTITY, never by index - see DECISIONS 119.
