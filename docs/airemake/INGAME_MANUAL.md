# The live place's own operations manual (extracted verbatim)

> **What this is.** `Workspace.Consoles` ships a documentation screen on every console
> (`*.DRMScreen.SurfaceGui.*`). It is an in-game operator's manual written by the game's
> own authors. Under this project's standing adjudication order —
>
> ```text
> live place  >  video (1 over 2)  >  TRGWeb
> ```
>
> — **this file outranks both videos and TRGWeb**, because it is the place speaking about
> itself. It is the highest-authority source found so far.
>
> **Provenance.** Extracted 2026-09-26 from place `83752844701736` ("The Reactor : AIRemake")
> via `rblx_execute_luau(datamodel_type="Server")`, walking
> `workspace.Consoles:GetDescendants()` for `TextLabel`/`TextButton`/`TextBox` whose
> `GetFullName()` contains `Screen` or `Frame` and whose tag-stripped text exceeds 25
> characters. The query deduplicated by stripped text and sorted the result
> **alphabetically by text**, so the numbering below is a stable identifier for quoting,
> **not** reading order and **not** console grouping. 151 unique strings.
>
> **Fidelity.** Strings are reproduced byte-for-byte as the game holds them, including the
> game's own spelling errors ("primairily", "degredation", "excersie", "resecure",
> "recallibrations", "achives", "H.O.E.F" where the meter is H.D.E.F). **Do not correct
> them.** They are matching keys: any future OCR of a video frame is compared against these
> exact bytes, and a silently "fixed" typo becomes a string that no longer matches its own
> source. HTML tags (`<b>`, `<br>`) were stripped by the extractor; an escaped `\"` is shown
> as a real quote.

---

## The 151 strings

```text
  1 [TextLabel] (Shift 3) CBL Integrity loss will occcur from frequent reactor activations, and as such this will cause numerous hull breaches to slowly form on the affected CBL, as well as slightly alter the color of the beam.
  2 [TextLabel] (Shift 3) During extensive and repeated operation of the reactor, gravitation wakes can appear and overtime become very disorienting or even deadly. If this happens, the gravatron is able to be overloaded , but do note that it was not originally designed for this and will suffer damage.
  3 [TextLabel] (Shift 3) Gravatron overloads can be sucessfully accomplished by pulling the Output lever into the Overcharge position, and pressing the grav overload button. Refer to [GRAVATRON] panel for more information.
  4 [TextLabel] A 'Gravquake' will cause a large portion of the installation to experience microgravity. Additionally, the gravatron will suffer damage , though the exact cause is unknown outside of an energy spike in gravitation conduits.
  5 [TextLabel] A 'Thunderquake' causes a disruptive electrical spike akin to an EMP that will temporarily disable control room functionality among several other subsystems. The electrical shortages caused by this will damage the facility mainframe.
  6 [TextLabel] A Molecular Weaver or Repair Gun Tool is used to quickly repair minor to moderate damage by mending surrounding materials together while maintaining its overall structual integrity.
  7 [TextLabel] A Radiation breach is a sign of low H.D.E.F Integrity. You will be fined accordingly for any damage caused by radiation, as well as accompanying medical expenses. Activating the H.D.E.F E-Power supply should help resolve a radiation breach.
  8 [Text] AUTOMATED M. A. S. S. CONTROL
  9 [TextLabel] Activating the E-Power Supply will allow the field to regain integrity , but do note that during reactor operation, it has a tendency to overheat , necessitating it be shut off after a certain amount of time.
 10 [TextLabel] Additionally, components of the mainframe may catch on fire from reactor operation. It's advised that when operators are preparing to replace a QPU, they equip a fire extinguisher. Excessive fires may raise the mainframe temperature and cause QPUs to degrade at a much faster rate.
 11 [TextLabel] Additionally, the C-Pumps have been observed degrading twice as fast as their usual rate, which at times ruptures or completely destroys the reactor's coolant network.
 12 [TextLabel] All upgrades displayed on the reactor operations board have descriptions for what they do, as well as potential side-effects, so further explanation is unecessary. Do note that if your funding is in the negative, you will not be able to purchase any upgrades.
 13 [TextLabel] Allowing the hull breaches to remain for a prolonged period of time will compromise the affected CBL's reaction sequence, and cause it to gain a substantial increase in pressure until repaired or an overload occurs.
 14 [TextLabel] As reactor operations personnel, you are required to Achieve the target energy quota, and sucessfully shut down the reactor each shift. You will be nickel and dimed for any company property damaged or destroyed in any way. Remaining funds can be used to invest in equipment to make your job easier.
 15 [TextLabel] Atmosphere Ventilation is a less critical but still vital component of the reactor chamber. These are the vents that line the chamber walls, and are responsible for intaking a large amount of pressure in order to keep the reactor stable.
 16 [TextLabel] CBL Malfunction signals at a major problem with a CBL. During reactor operation, as CBL's are integral to maintaining the core , they should be active at all times. This warning will go off while a CBL is currently disabled , or if the reactor pressure is too low.
 17 [TextLabel] CBL Overload = Red CBL Integrity Loss (Shift 3) = Purple CBL Reaction Loss (low chamber pressure) = Blue High CBL Output = Yellow
 18 [TextLabel] CBL's are dependant on a sufficient enough Chamber Pressure in order to function properly. If the Chamber pressure falls below ~ 2300PSI , then all CBL's maximum output will be lowered significantly (Reaction Loss) , and will cause the core's temperature to rapidly drop.
 19 [TextLabel] CBL's that overload during integrity loss will remain indefinitely offline until more extensive repairs can be made.
 20 [TextLabel] CONTROL ROOM SHUTTERS > [ALT REACTOR CONSOLE]
 21 [TextLabel] Control Room Functions are primairily to fufill start-up prerequisites , or for your personal comfort. Generally this part of the console can be completely ignored once eveything is set up.
 22 [TextLabel] Coolant Pumps or C-Pumps degrade at a constant rate due to the corrosive nature of ISE, and this is made worse based on the pump level. It's recommended you observe the reservior level and reactor chamber Coolant Pipes to guage how close it is to failing.
 23 [TextLabel] Different types of damage will require different repair times, however operators should fire for at least 4 seconds. Overloaded damage may require a longer repair time.
 24 [TextLabel] Do not underestimate the reactor in this state. It can and will destabilize if you are not careful!
 25 [TextLabel] Due to the extreme instability of the core, operators are required to activate an E-VENT, especially as coolant systems have a tendency of failing at this point.
 26 [TextLabel] Due to the volatility of this core, equipment generally degrades extremely fast in comparison to traditional reactor systems. P.E.A Stress, Chamber Pressure, Radiation, and CBLs are all influenced by the core's temperature with a higher temperature causing more disasterous consequences.
 27 [TextLabel] During an EFE , the core will begin to produce twice as much energy as it normally would, and have minimal temperature fluctuation. Additionally, an EFE will typically create a cross-dimensional anomaly. The anomalies classified thusfar are known as 'Thunderquakes' , and 'Gravquakes' .
 28 [TextLabel] E-VENTS or Emergency Ventilations are the large duct-like holes that surround the core. These are responsible for rapidly cooling down the core by ~ 7000F via a more pure and concentrated variant of Isotope E.
 29 [TextLabel] EFEs or Excessive Energy Fluctuation Events are events which occur when a subspace energy fluctuation exceeds the Haden Threshold . When an EFE is about to occur, all monitors will display a warning.
 30 [TextLabel] Each CBL has their own respective diagnostics displayed in a simplified format, with the most notable being Stress & Pressure.
 31 [TextLabel] Enabling outtake fans can help decrease the amount of pressure gained , or help level it off. Remember to disable outtake fans periodically when in State 1 to avoid stallout . Also remember to re-enable them in greater states as to avoid a high pressure warning.
 32 [TextLabel] Energy Fluctuation (Excessive Energy Fluctuation Event or EFE) will usually occur at specific times that are predicted via the Subpace Forecast Monitor. More details are provided in the Core panel.
 33 [TextLabel] Energy Fluctuation Events [EFEs] or Excessive Energy Fluctuation [EEF] occur within a specific time period that is predicted via the Subspace Forecast monitor. Both EFEs and Equinox Events are displayed as a yellow bar, however equinox occurs last.
 34 [TextLabel] Equinox is similar to an EFE, but far worse in magnitude, and indefinite in length. Their disruptive effects tend to cause massive damage to installation infastructure and should subsequently be avoided at all costs.
 35 [TextLabel] Excessive damage may result in the Gravatron completely shutting down and disabling certain grav-shafts, requiring they be temporarily powered with GCCs (Gravitation Containment Cells).
 36 [TextLabel] Excessive P.E.A Stress is triggered when the P.E.A Stress exceeds 75%. Lowering the extraction rate , the core temperature , or increasing the coolant level can help reduce stress.
 37 [TextLabel] Excessive Temperature is a relatively passive alert that signals advanced degredation.
 38 [TextLabel] Excersie caution, and remain vigilant of the reactor. Do not take any unnecessary risk!
 39 [TextLabel] Fire extinguishers operate similarly to Repair Guns with the added benefit of not blowing up in your face. Aim directly at the source of the fire for a few seconds to extinguish it properly.
 40 [TextLabel] FLIP MASTER SWITCH TO START-UP POSITION
 41 [TextLabel] Hazardous Chamber Radiation and High Chamber Pressure will both decrease the H.D.E.F's integrity , however High Chamber Pressure will also cause an increase in Temp Fluctuation.
 42 [TextLabel] High CBL Power will cause the CBL pressure & subsequently the stress to rise dramatically, and High CBL Stress is a sign that a pressure purge is needed to avoid imminent overload.
 43 [TextLabel] High Energy Output refers to the core outputting energy in excess of 400 GW/H. When this occurs, the P.E.A will begin to experience an increase in stress , and is a general sign that equipment will experience advanced degredation.
 44 [TextLabel] High Temp Fluctuation will typically typically occurs above 400F Temp Fluctuation. It is generally advised that the temp fluctuation remains low so as to prevent rapid deterioration.
 45 [TextLabel] Hold the beam for around 4 seconds or longer depending on the damage. Be aware of overloading. Accessable via Maintenance Station or Synthesiser Unit.
 46 [TextLabel] If CBL's are unreliable in this state, focus on increasing pressure.
 47 [TextLabel] Integrity loss will be displayed in purple for the affected CBL, and will require operators to venture inside of the reactor chamber via M.E.S, and repair the hull breaches within a timely manner.
 48 [TextLabel] It is equipped with a B-Grade Molecular Weaver attachment which acts as a compromise between A-Grade and C-Grade Repair Guns while having substantially more range .
 49 [TextLabel] It is powered by two ECC 's (Electron Containment Cell), which are to be replaced once a cell has been expended after firing. ECC's can be replaced by going to the ECC Module in the midsection of the METU , and inserting a cell into the appropriate receptacle.
 50 [TextLabel] It will occur if the Subspace Core has been active for roughly 12 hours [minutes] , and will not revert back to its normal state until it has collapsed / shutdown.
 51 [TextLabel] Its higher energy output has greater consequences however, as equipment will begin to experience advanced degredation. The H.D.E.F will begin to deteriorate due to excessive radiation, the pressure will increase at a greater rate, and the P.E.A will also gain stress faster.
 52 [TextLabel] Large stockpiles of QPUs tend to be counterintuitive, so operators may have to use a Synthesiser Unit in order to sucessfully replace dying QPUs. Be weary that the mainframe is always kept at extremely low temperatures, and as such haste is of the essence. {wip system}
 53 [TextLabel] Majority of its computational operations are controlled by QPUs , which have a tendency to degrade , especially in unfavorable environmental conditions or overclocking scenarios.
 54 [TextLabel] MONITOR BOOT > [MAIN REACTOR CONSOLE]
 55 [TextLabel] MONITOR POWER > [ALT REACTOR CONSOLE]
 56 [TextLabel] NOTICE: ACTIVATE THE HDEF GENERATOR TO PREVENT POTENTIAL CONTROL ROOM RADIATION BREACH DURING START-UP. BE ADVISED THAT DURING REACTOR OPERATION, THE HDEF GENERATOR CAN OVERHEAT. PERIODICALLY SHUT IT OFF TO PREVENT OVERLOAD.
 57 [TextLabel] Note: Avoid letting the H.D.E.F Integrity reach below 30%, the P.E.A stress reach 100%, and a high temperature fluctuation. [P.E.A = Power Extraction Assembly | H.D.E.F = High Density Electron Field or Electron Field | Temp Flux = Temperature Fluctuation]
 58 [TextLabel] Operators are required to replace the affected QPU as soon as possible , otherwise machines across the facility will begin to shut off in order to conserve resources.
 59 [TextLabel] Operators inside of the reactor chamber should avoid maneuvering too far from the core , as it's nullifying gravitational effect has a relatively short range , and exiting this range could cause you to fall and face a lethal injury, even with a Maintenance Exosuit.
 60 [TextLabel] Overview - In order to assist you with either maintaining degrading equipment, or allow for improved mobility, you're authorized to use several different pieces of equipment which can be acessed via the Maintenace Facilities or Synthesiser Units.
 61 [TextLabel] Overview - R&D projects created in the Icarus Installation, or other SM Installations are generally refered to as Facility Prototypes. Some of these project developed are able to relieve stress on Reactor Operators.
 62 [TextLabel] Overview - The Alt Reactor Console is for managing auxillary functions to the reactor such as the M.A.S.S Rails , as well as some control room functions.
 63 [TextLabel] Overview - The CBL Console or Power Console is where all 3 of the CBLs can be managed , and also a major player in managing the core's temperature.
 64 [TextLabel] Overview - The Electric Grid Console is primarily used to manage the P.E.A , and subsequently the quota, however it also controls the Gravatron unit present in Heavy Maintenance.
 65 [TextLabel] Overview - The Gravatron is a large centrifugal machine that provides power to Grav-Shafts, Grav-Gates, Synthesiser Units, and more via Gravitation Conduits. It's secondary function is to eliminate any gravitation wakes that may appear during reactor operation.
 66 [TextLabel] Overview - The High Density Electron Field, H.D.E.F, or H-DEF, is responsible for shielding the control froom from hazardous radiation, energy, or even projectiles.
 67 [TextLabel] Overview - The Main Console contains important functions such as emergency systems like the E-Vents and Atmosphere Ventilation , as well as start-up Prerequisites like the Monitor Boot and Master Switch.
 68 [TextLabel] Overview - The METU or Mass Electron Transmission Unit is a large structure that sits directly above the subspace core, and is responsible for protecting the facility against a full meltdown.
 69 [TextLabel] Overview - The Thermal Console is where core temperature and chamber pressure is primarily managed.
 70 [TextLabel] Overview - The 'Tesseract' Quantum Mainframe is the world's most powerful Quantum Supercomputer, responsible for maintaining extremely complex machinery such as the: CBLs, Reactor Console Command Interface, Gateway Transporters, Medical Dispensers, and more.
 71 [TextLabel] P.E.A Malfunction means that the Power Extraction Assembly is currently offline, typically from excessive stress. It will automatically shut itself off to prevent an explosion, and will take a while to reboot.
 72 [TextLabel] Power Levels 2-5 will cause the CBL's pressure to rise , and once eventually high enough, the CBL stress. The magnitude of pressure gain increases with each subsequent power level.
 73 [TextLabel] Power level 1 or minimum causes a negligible change in internal pressure unless the reactor chamber's pressure reaches an extreme threshold.
 74 [TextLabel] Pressure control systems will become inoperable, CBLs will gain pressure much faster, the Coolant will experience much faster degredation, with the potential of rupturing completely, and many more unforseen consequences.
 75 [TextLabel] Pressure purges should be enacted frequently when necessary, as excessive CBL Pressure can lead to excessive CBL Stress, which can eventually cause a CBL to Overload , which will be fined accordingly.
 76 [TextLabel] Pump Malfunction & Low Coolant Reservior is a sign that the C-Pumps are offline and in need of repairs. Operators are required to go into Reactor Coolant Maintenance and fix the issue.
 77 [TextLabel] QPUs, ECCs, and GCCs are all tools that are inserted into their respective components in order to repair or supply them. More detailed descriptions are available via the Synthesiser Units.
 78 [TextLabel] Refer to the [LASER CONS] Panel for more information regarding CBL Statuses, and how to handle them.
 79 [TextLabel] Remember to keep the H.D.E.F. E-Generator (behind you) active during the start-up sequence. The large burst in energy during ignition typically degrades the field to the point of causing radiation damage.
 80 [TextLabel] Should gravitation wakes from as a result of frequent reactor operation, Operators are recommended to initiate an overload procedure.
 81 [TextLabel] Should the pumps fail, you are required to go in the heavy maintenance sub-sector, and make the appropriate repairs / recallibrations.
 82 [TextLabel] Shut down the reactor as soon as possible if an Equinox State is achieved.
 83 [TextLabel] State 0 or the formation state typically occurs when the core is forming or the reactor temperature is low . In this state, the core is very prone to preemtive collapse, and as such the temperature should be raised immediately.
 84 [TextLabel] State 1 is where normal operations take place. It is the most suitable for making repairs throughout the facility before attempting to advance the quota more quickly. The reactor can only shut down provided the temperature is less than 17000F , which is in the margins of this state.
 85 [TextLabel] State 2 occurs when the reactor has achieves high temperature level in excess of roughly 18000F. If operators wish to achieve the quota quickly, or need to achieve high energy quotas, transitioning into this state may be very suitable.
 86 [TextLabel] State 3 occurs when the reactor temperature is in excess of roughly 29000F. As this state exceeds current operational capabilities, not much is known due to the damage it causes.
 87 [TextLabel] Stallout Possibility will occur if the core temperature is below ~ 6000F , and Core Destabilization will occur if either an EFE or Equinox State is currently active.
 88 [TextLabel] Stress can be gained by: high extraction rate, low coolant power level, or high temperatures. Enabling and boosting the coolant, or lowering the temperature / extraction rate can help reduce stress.
 89 [TextLabel] Sucessful overloads can be accomplished by lowering the Grav Output lever to the Overcharge position, and correctly time when to press the Grav Overload button. When the button flashes yellow rapidly , that is when the overcharge is ready to be fired.
 90 [TextLabel] Sucessfully completed shifts will reward you with greater access to the facility and potential for monetary benefits, however if the debt ceiling is reached, disciplinary action will occur. Good luck! The future of industry starts with you!
 91 [TextLabel] The "Core" of the reactor to put it simply is a wormhole or gateway into Subspace from which energy can be extracted via the P.E.A. It is perhaps the greatest discovery Synthesis Manufacturing and by extension mankind as ever made, and is why it is one of our most top priorties.
 92 [TextLabel] The appropriate C-Pump will be displayed in red for repairs, however coolant sensory equipment has a tendency to be unreliable during reactor opration.
 93 [TextLabel] The Equinox State or Equinox Event is a massive spike in normal energy fluctuations that causes a disruptive effect to electronic equipment, as well as destabilization within the core.
 94 [TextLabel] The Extraction Rate lever controls what percentage of energy is extracted from the Net Output from the core. The total amount of energy extracted can be observed via the Quota Monitoring Screen.
 95 [TextLabel] The Maintenance Exosuit MKII or M.E.S is a heavy duty multi-purpose suit used to operate in high stress environments for maximum efficiency and safety.
 96 [TextLabel] The M.A.S.S Rails are a massively upscaled variant of the scrubbers found in deionization chambers which help protect vital machinery and personnel from chamber emissions.
 97 [TextLabel] The METU or Mass Electron Transmission Unit is a large structure that sits directly above the subspace core, and is responsible for protecting the facility against a full meltdown.
 98 [TextLabel] The MkII subvariant that reactor operations personnel will use is designed to withstand high temperatures, extreme radiological environments, and toxic atmospheres , making it suitable for repairs inside the chamber during reactor operation.
 99 [TextLabel] The suit also makes use of an ionic thruster system which PTMs derrive from, making fuel consumption negligible. Unlike PTMs however, this will not dampen high falls.
100 [TextLabel] There are two large emitters beside the control room, as well as an emergency generator behind this console that maintain the field's integrity.
101 [TextLabel] These alerts provides priority information about the reactor, and are often the alerts that you should be looking out for the most.
102 [TextLabel] These Alerts provide general information about both the core and the control room, and should divert your attention but not be the biggest priority. The most notable alert would be Radiation Breach.
103 [TextLabel] These alerts signal if vital components of the reactor are offline, damaged, or even destroyed . It will also signal special core circumstances such as stallout.
104 [TextLabel] These are the alerts that are by the top and are generally unimportant, with the most notable being Chamber Radiation & Reactor Activation warnings.
105 [TextLabel] These are to be activated in tandem with the H.D.E.F to help prevent or eliminate a radiation breach. Note that the M.A.S.S Rails will interfere with the core's energy output , and lower the amount of net Energy that can be extracted, though this can be mitgated with a lower M.A.S.S Power Level.
106 [TextLabel] This can also be used as another extreme method of cooling the core, however this requires a high degree of precision, especially in higher states, and is very frowned upon by maintenance teams.
107 [TextLabel] This is byfar the most mysterious phenomena of the subspace core, however further research has been suspended due to the unacceptable amount of damage it causes to company infastructure.
108 [TextLabel] This monitor displays information about future Subspace Energy Fluctuations that may occur. The most notable fluctuations are known as EFEs , or Equinox.
109 [TextLabel] This monitor displays information regarding alerts and notable information about the reactor. Most of these alerts are self-explanatory, however more details are provided in the Alerts panel.
110 [TextLabel] This monitor displays information regarding logs about both the facility and the reactor. Should something happen that you are uncertain about that you wish to know quickly, looking at the system logs typically helps.
111 [TextLabel] This monitor is responsible for displaying all vital information about both the subspace core and some of the major components of the reactor chamber. [CBL's, Coolant, P.E.A, H.D.E.F, Pressure, Radiation, Temperature]
112 [TextLabel] This monitor is responsible for displaying all vital information about the 3 CBL's. [Combustion Lasers]
113 [TextLabel] This monitor is responsible for displaying all vital information about both the coolant and chamber fan statuses. [C-PUMP, OUTTAKE FAN]
114 [TextLabel] This monitor is responsible for displaying quota information. 9AM Marks the time which overtime fees will start to be incurred, and 12PM marks the beginning of the Equinox Event. Filling the quota bar will allow the reactor to be shutdown normally if it's in State 1 or below.
115 [TextLabel] This monitor is responsible for displaying quota information. 9AM Marks the time which overtime fees will start to be incurred, and 12PM marks the beginning of the Equinox Event. Filling the quota bar will allow the reactor to be shutdown normally if it's in State 1 or below.
116 [TextLabel] To repair damage, operators will have to aim and fire the beam directly at the target, and hold for a certain amount of time before stopping.
117 [TextLabel] To replace a QPU , operators will first have to disconnect any remaining connections it has to the mainframe. This can be done by disabling any red indicators on a QPU receptacle. Once the old QPU is extracted , a new one can be inserted , and integration will happen automatically.
118 [TextLabel] Unresponsive CBLs in this state is indicative of insufficent pressure , and may result in stallout.
119 [TextLabel] Using both the E-Power Supply as well as the M.A.S.S Rails can help resecure the control room from a radiation breach quickly.
120 [TextLabel] Vacate all personnel from the chamber immediately during reactor activation, there are numerous mechanical hazards, as well as the extremely lethal burst of energy during the ignition or even subspace generator activation phases.
121 [TextLabel] When a coolant pump's net stability value is low, it will appear be leaking within the chamber, and when its almost fully depleted, its reservior value will appear to decrease.
122 [TextLabel] When a QPU fails completely, it will cause connected systems to reconnect and adjust their operations to the remaining QPUs which often results in devices enacting a soft-reboot protocol or in the case of the control room monitors, experience a blue visual distortion.
123 [TextLabel] When operating the reactor, you must be vigilant of both the core's temperature, the health of the reactor's major components, the time it takes to achive the quota, and especially your own health in order to succeed at this job.
124 [TextLabel] When the core is in an Equinox State, pressure systems have been noted to be ineffective due to an as of yet unkown phenomena that affects several systems and components in the installation.
125 [TextLabel] When the reactor is in a higher energy state than normal, it will typically produce an excessive amount of radiation, which will begin to overwhelm the traditional emitters for the H.D.E.F Shield, resulting in Integrity loss.
126 [TextLabel] While overcharges normally damage the gravatron , unsuccessful overloads will result in substantially more damage , however this can be repaired with a repair gun.
127 [TextLabel] While the core will produce the most energy in this state, do not hesistate to use an E-VENT to prevent a possible meltdown.
128 [TextLabel] While the nature of EFEs and their exact cause remains a mystery, you should refer to the [CORE] panel to learn more about their consequences.
129 [TextLabel] While the extinguisher is well equipped to prevent blazes within the reactor, you are required to fire for at least 4 seconds. Overloaded damage may require a longer repair time.
130 [TextLabel] Your exceptional qualifications and work performances has brought you to this job as an S0 Reactor Operator , and as such you have been granted access to some of the best equipment in the world (courtesy of Synthesis Manufacturing) in order to fulfill your new duties.
131 [TLDRLabel] Set the Grav Output lever to overcharge, and press the Grav Overload button when it *FLASHES* yellow *RAPIDLY*. If missfired, damage will occur to the gravatron which can cause it to shutdown completely if not repaired.
132 [TLDRLabel] TLDR: If all QPUs degrade fully, the gateway transporters will remain offline until one is replaced. Be aware of mainframe fires, as if theres enough, they can trigger a mainframe meltdown which will cause QPUs to degrade faster.
133 [TLDRLabel] TLDR: Prototypes are used to make reactor operations easier, though they can only be purchased with any *AVAILABLE* funds. It is in your best interest to not use destructive tactics during reactor operation.
134 [TLDRLabel] TLDR: The gravatron is used to supply power to the grav-shafts, and its auxillary function is to eliminate gravitational anomalies.
135 [TLDRLabel] TLDR: The H.D.E.F Shields the control room from radiation damage, however it's integrity will degrade at a constant rate with excessive radiation or pressure. Enabling the E-Power supply will increase the integrity, however it overheats during reactor operation.
136 [TLDRLabel] TLDR: The METU protects the facility from a full meltdown, however an ECC is expended each time it does so. If both ECC's are depleted, then billions of dollars in damage will occur. ECCs can be replaced by going into the reactor chamber.
137 [TLDRLabel] TLDR: This console controls CBLs which increases the reactor's temperature. CBLs require fequent pressure purges to avoid overload. CBLs will not gain pressure in power level 1.
138 [TLDRLabel] TLDR: This console controls E-Vents and atmosphere ventilation, as well as major start-up pre-requisites.
139 [TLDRLabel] TLDR: This console controls certain start-up prerequisites as well as the M.A.S.S Rails. M.A.S.S Rails act as radiation scrubbers which can help protect the control room from radiation damage, however it will reduce the amount of power that can be extracted.
140 [TLDRLabel] TLDR: This console controls outtake fans and C-Pumps which help reduce the core's pressure and temperature. Higher coolant levels will cause them to degrade faster, necessitating more repairs.
141 [TLDRLabel] TLDR: This console controls the P.E.A & Gravatron (Shift 3 component).
142 [TLDRLabel] TLDR: This console is for managing the reactor's core, atmosphere and ventilation.
143 [State3Label] STATE 3 [OPERATIONAL LIMIT]
144 [EFELabel] EXCESSIVE ENERGY FLUCTUATION [EFE]
145 [SubTitleText] CB LASER CONSOLE OPERATIONS
146 [SubTitleText] ELECTRIC GRID CONSOLE OPERATIONS
147 [SubTitleText] GRAVATRON OPERATIONS [SHIFT 3+]
148 [SubTitleText] HIGH DENSITY ELECTRON FIELD
149 [SubTitleText] MASS ELECTRON TRANSMISSION UNIT
150 [SubTitleText] QUANTUM MAINFRAME OPERATIONS [SHIFT 2+]
151 [SubTitleText] THERMAL CONSOLE OPERATIONS
```

> Two entries are near-duplicates of each other — #114 and #115 are the same sentence on
> two different screens, and #68 and #97 both open "The METU or Mass Electron Transmission
> Unit is a large structure...". They are kept as separate rows because they are separate
> labels in the place; the deduplicator only removes byte-identical text.

---

## Reconciliation against the skeleton's `Config`

Read 2026-09-26 from `ServerScriptService.ReactorBackend.Config` (named `ReferenceContent` at the time of the reading) via
`rblx_execute_luau(datamodel_type="Server")`. **Nothing below has been changed yet** —
this is a diff, and every row marked *conflict* or *unmodeled* is a decision for the user,
not a silent edit. Per `CLAUDE.md` §1.4.1, mechanics are not changed unilaterally.

### Corroborated — manual prose and an authored constant agree

| # | Manual says | `Config` | Verdict |
|---|---|---|---|
| 84 | "shut down provided the temperature is less than **17000F**" | `Shift.ShutdownLimit = 17000` | **exact** |
| 28 | E-VENTs "rapidly cooling down the core by **~7000F**" | `Vent.EmergencyDrop = 7000` | **exact** |
| 50 | "[Equinox] will occur if the Subspace Core has been active for roughly **12 hours [minutes]**" | `Events.EquinoxSeconds = 720` (= 12 min) | **exact** |
| 86 | "State 3 occurs when the reactor temperature is in excess of roughly **29000F**" | `Sim.State3 = 29500` | agree (prose rounds down) |
| 85 | "State 2 ... in excess of roughly **18000F**" | `Sim.State2 = 17500` | agree (prose rounds up) |
| 18 | "Chamber pressure falls below **~2300PSI**" → Reaction Loss | `Sim.StallPressure = 2200` | agree (prose rounds up) |
| 36 | "P.E.A Stress exceeds **75%**" | `Device.CBLStressThreshold = 75` | value agrees; **name** says CBL |
| 42/75 | CBL pressure → stress → overload, purge to relieve | `Device.CBLPressurePerLevel=0.6`, `CBLStressGain=0.4`, `CBLPurgeStressRelief=25`, `CBLPurgeCooldown=4` | chain matches |
| 137/73 | "CBLs will **not** gain pressure in power level 1" | `Device.CBLPressurePerLevel = 0.6` | **verified** in `Engine:215-217` |
| 18 | low pressure → CBLs clamp down, "core's temperature to rapidly drop" | `Sim.StallPressure = 2200` + `Sim.StallCooling = 750` | **verified** in `Engine:215, 228` |
| 51 | in a higher state "the pressure will increase at a greater rate" | `Sim.State2Pressure = 200`, `Sim.State3Pressure = 300`, `Sim.State3Heat = 700` | **verified** in `Engine:226-227` |
| 56/9/135 | HDEF "can **OVERHEAT**. **PERIODICALLY SHUT IT OFF** to prevent overload" | `HDEFHeatGain=1`, `HDEFHeatLoss=2`, `HDEFMaxIntegrity=12`, `HDEFDecay=0.025`, `HDEFRecovery=0.2` | **heat gain while on / loss while off reproduces the manual's stated duty cycle** |
| 105/139/96 | M.A.S.S Rails scrub radiation but "lower the amount of net Energy that can be extracted ... mitigated with a lower M.A.S.S Power Level" | `MASSReductionPerLevel=0.2`, `MASSOutputCostPerLevel=0.025` | matches |
| 22/140 | C-Pumps "degrade at a constant rate ... made worse based on the pump level" | `Device.PumpWearPerLevel = 0.06` | matches |
| 31/140 | outtake fans "decrease the amount of pressure gained ... disable periodically **when in State 1 to avoid stallout**" | `Sim.FanPressure = 70` × `Sim.StallPressure` | the stall coupling is real and is modeled |
| 89/131 | grav overload — "slim time window", button "flashes yellow rapidly" | `Grav.WindowSeconds = 1.5` | timing matches; **colour does not** (see below) |

### Conflicts and gaps — recorded, not acted on

| # | Issue | Detail |
|---|---|---|
| 87 | **Stallout *possibility* is an alert the skeleton does not have** | Investigated, and **not** the bug it first looked like. `Engine:243` is `elseif s.temperature<c.Sim.StallTemperature then self:Fail('Reactor stallout')` — `StallTemperature = 2000` is a **hard failure floor**, in the same branch as meltdown. The manual's wording is the tell: "**Stallout Possibility** will occur if the core temperature is below ~6000F", and #103 lists it as something the alert panel "will also signal". So ~6000F is a **warning threshold** and 2000 is a **failure threshold** — different quantities, and 2000 is **not contradicted** by 6000. What is genuinely missing is the warning layer: the skeleton jumps from "fine" to `Fail` with nothing in between. Related: #83 says state 0 (below `State1 = 5600`) is "very prone to preemtive collapse, and as such the temperature should be raised immediately" — the manual wants an operator-facing caution band across roughly 5600–6000F that we do not emit. |
| 44 | **Temp fluctuation scale** | Manual: "High Temp Fluctuation ... above **400F**". `Config`: `Sim.NoiseMin = -50`, `Sim.NoiseMax = 49`. Different scale — likely a unit/definition difference, not a wrong number. |
| 43 | **High-output threshold** | Manual: "High Energy Output ... in excess of **400 GW/H**". No `Config` constant; only `OutputDivisors` / `QuotaDivisor = 60`. **Unmodeled.** |
| 17/47 | **The CBL five-colour status code** | Manual defines it exactly: Overload **Red**, Integrity Loss **Purple**, Reaction Loss (low pressure) **Blue**, High Output **Yellow**. `Visual` has only `Off` / `Ready` / `Pulse` / `Fault`. **Four of the five have no home**, which is the missing semantics behind the unwired `CBL[1-3]Systems.PressureButton.NeonPart` family. |
| 89/131 | **Grav-ready flash colour** | Manual: **yellow**, rapid. `Visual.Pulse = (0.353, 1.0, 0.471)` = green. `Pulse` is shared by all lamps, so this is a palette gap, not a bug. |
| 92 | **Coolant sensor unreliability is documented** | "coolant sensory equipment has a tendency to be unreliable during reactor opration". This is the Wiki claim, now confirmed from the highest-authority source. **The skeleton models no sensor noise.** `Device.SAM*` may be the calibration model, but the manual never says "SAM". |
| 27/34 | **EFE ≠ Equinox** | Manual: EFE = "twice as much energy ... minimal temperature fluctuation"; Equinox = "far worse in magnitude, and indefinite". `Config` models only `Events.EquinoxMultiplier = 3` / `EquinoxWearMultiplier = 2` / `EquinoxSeconds = 720`. **No ×2 EFE path.** |
| 145/147/150 | **Shift gating** | Manual titles panels `[SHIFT 2+]` and `[SHIFT 3+]` and prefixes rules "(Shift 3)". Video 2 shows "Note: Shift 3 is temporarily disabled for instability". `Config` has `Shift.Quotas` but no shift-gating model. |
| 143 | **State 3 as the danger band** | The label is `STATE 3 [OPERATIONAL LIMIT]` and 86 says little is known past it; 127 says "use an E-VENT to prevent a possible meltdown". The manual gives **no meltdown number**. So the four-way meltdown disagreement (39000 / 39000 / 39000 / 35000) is **not settled by this source** — but the manual's framing (state 3 *is* the operational limit) points at 29500–39000 as the danger band rather than at any single figure. `Sim.MeltdownTemperature = 39000` stays as authored, still flagged. |
| — | **Uncorroborated constants** | `Sim.State1 = 5600` (manual gives no number for the state 0→1 edge, only "low"), and the whole startup transient (`Shift.StartupSeconds=8`, `BootSeconds=3`, `ShutdownSeconds=5`, `Sim.StartupTemperature=9420`, `StartupPressure=5000`, `Sim.ReferenceTick=2.5`, `Sim.Step=1`), plus `Device.SAMRadiationLimit=600` / `SAMTargetLow=7000` / `SAMTargetHigh=14000`. Nothing contradicts them; nothing confirms them. |

### What this buys

The four-way **state 3 = 29500 vs 39000** dispute was the single largest unresolved
constant in the project, and it is now settled the right way round: the live place's own
manual says **~29000**, and the authored `Sim.State3 = 29500` already agrees. The earlier
"39000 from three sources" reading was an artefact of treating `CORE_STATE_THRESHOLDS`'s
**last array element as the 2→3 edge**, when in a four-entry table it is the 3→4 edge.
No code change is needed.

`hdef.fault` also stops being a guess: the manual names its cause (overheat/overload),
which is stronger than the intra-file inference the HDEF lamp fix was built on. The
*split* — `enabled` gates whether a lamp is lit, `fault` only colours an already-lit lamp —
remains a chosen convention, but its trigger is now documented.

## Not done yet

- The 151 strings are grouped in neither console nor reading order. A grouped re-extract
  (walking each `DRMScreen` frame in order) is possible in one query if the structure is
  ever needed.
- No `Config` value has been changed on the strength of this document.

### `Engine` line references used above

Read 2026-09-26 from `ServerScriptService.ReactorBackend.Engine.Source` (258 lines; the folder was named `ReferenceContent` at the time of the reading),
`datamodel_type="Server"`. Quoted verbatim, whitespace-trimmed:

```text
215| local level=s.pressure<c.Sim.StallPressure and 1 or device.level
217| device.pressure=math.clamp(device.pressure+(level-1)*c.Device.CBLPressurePerLevel*dt,0,100)
226| if s.temperature>c.Sim.State2 then s.pressure+=c.Sim.State2Pressure*scale end
227| if s.temperature>c.Sim.State3 then s.temperature+=c.Sim.State3Heat*scale; s.pressure+=c.Sim.State3Pressure*scale end
228| if s.pressure<c.Sim.StallPressure then s.temperature-=c.Sim.StallCooling*scale end
232| s.coreState=s.temperature>c.Sim.State3 and 3 or (s.temperature>c.Sim.State2 and 2 or (s.temperature>=c.Sim.State1 and 1 or 0))
242| if s.temperature>=c.Sim.MeltdownTemperature then self:Fail('Reactor meltdown')
243| elseif s.temperature<c.Sim.StallTemperature then self:Fail('Reactor stallout')
```

Line 232 is the whole state model: the boundaries are **`State1`=5600 / `State2`=17500 /
`State3`=29500**, so state 3 begins at 29500 — agreeing with the manual's "~29000F" and
**not** with 39000. Line 242/243 show the only two thermal failure paths, and that both
are hard `Fail`s with no intervening warning band.
