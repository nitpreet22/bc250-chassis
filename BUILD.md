# Build guide: cooling and case

The build is split in two:
- **Version 1 (now):** stock heatsinks and PLA prints.
- **Version 2 (later):** AIO water cooling and the heatsink cut. It needs ABS/ASA prints.

Nothing is printed until the part it fits has been measured.

## Version 1: stock heatsinks, white PLA, Bambu Lab A1

### Decisions (2026-10-09)

- **Heatsinks stay stock and uncut.** No AIO, no cut heatsink.
- **No core unlock.** The CPU stays at its stock 6 cores (12 threads).
- **The GPU starts capped at 1500 MHz.**
  - This is the cap the BC-250 docs give for sustained full-GPU load on the stock heatsink:
    about 83 °C with two Arctic P12 Max fans.
  - Without the cap they measured 89.6 °C average and 107 °C peak.
  - Our fans are weaker than the P12 Max, so we measure before raising the cap.
- **Cooling:** fans face the heatsink, the community-standard BC-250 arrangement.
  - Per node:
    - a Teucer AF-12025 (strong, PWM) over the lower half of the fins;
    - an Arctic P12 Silent over the upper half;
    - a BB7515 blower on the backplate (memory).
  - A small baffle closes the bottom of the fins, so all the hot air leaves upward through the
    top grille.
  - The 4th Arctic blows fresh air into the cable channel, as before.
  - Fresh air comes in through the floor. Each fan wall draws from the space in front of it,
    which also runs past the backplate of the node in front.
- **PLA heat rule.** PLA Basic softens at about 55-60 °C.
  - No PLA part touches a heatsink or a backplate.
  - Fan walls and baffles stand at least 3 mm off the metal.
  - Boards are held by their metal end brackets and by PCB edges away from the VRMs.
- **Print size.** The A1's bed is 256 × 256 mm, so the large panels print in pieces that join with
  screws and alignment keys.

### Order of work

| Step | What | Printed parts? |
|---|---|---|
| 1 | Put board 3 back together with its stock heatsink and fresh paste. Bench test with a fan. | No |
| 2 | Take the V1 case measurements below | No |
| 3 | I redo the CAD for V1 and produce print-ready, bed-sized PLA parts with fasteners | - |
| 4 | Print, then test-fit one node's column before printing the rest | Yes |
| 5 | Assemble the case, install the nodes, wire the fans and power | Yes |
| 6 | Set the GPU cap, run a sustained load, read temperatures, adjust | No |

### Step 1: reassemble board 3 (stock heatsink)

Board 3 is apart from the V2 pilot. Its heatsink is uncut, so it goes back as it came.

1. **Clean the APU.** Wipe the old compound off the APU die and the heatsink's copper pad with
   isopropyl alcohol and a lint-free cloth until both are shiny. Don't touch the cleaned surfaces.
2. **Leave the other thermal material alone.**
   - VRM putty: it's intact, with the fin imprints, so leave it in place. Don't add more, and
     don't swap in pads of another thickness.
   - Grey putty blocks near the M.2 and power connectors: leave them.
   - Memory pads on the back: leave them.
   - If any piece has torn or moved, press it back where its imprint shows it was.
3. **Paste.** Use the paste that came with the Teucer kit (H).
   - The APU is a bare die, so spread a thin, even layer over the whole die with a card.
   - A pea-sized dot doesn't cover a rectangular die reliably.
4. **Assemble:**
   1. Lay the heatsink fins-down on the bench.
   2. Lower the board onto it, face down, so the posts go through the 4 holes around the APU.
   3. Put the backplate on the back.
   4. Start all 8 screws by hand.
   5. Tighten the 4 spring screws around the APU in an X pattern, two turns at a time, until
      each one stops turning easily (spring fully compressed). Don't force them past that.
   6. Tighten the 4 outer screws until snug.
5. **Bench test, never without airflow.** The stock heatsink is passive.
   - Lay a Teucer fan on the fins, blowing down, and power it from the board's fan header or a
     hub.
   - Boot, then check `sensors` for the GPU edge and `Tctl` temperatures at idle. Node 3 read
     54.6 °C `Tctl` at idle before.
   - Once the node is on the network, I'll set the 1500 MHz cap and run a 10-minute load.

### Step 2: measurements for the V1 case

Enter the readings on the **BC-250 Measurement Sheet**
(https://claude.ai/artifact/FGaDxPEHDyKGMmBPLqynri). It has a dimensioned drawing for each
group and saves every reading so Claude can read it back. It covers more than the summary below:
82 readings, IDs B, S, K, C, R, F, P, X and the Version 2 M/RAD series.

| # | Measure | Why |
|---|---|---|
| V1 | Board slab with the stock heatsink fitted: fin tips to the backplate's outside face, including screw heads | Column depth and fan-wall position |
| V2 | Heatsink length and width, and the distance from each heatsink end to the PCB end (I/O end and far end) | Where the two fans and the baffle sit |
| V3 | I/O bracket and far-end bracket: outline, hole positions and diameters. Photo with the caliper. | How each board is held |
| V4 | Rack side-frame upright cross-section, window inset from the outer face, frame height, existing holes and handle holes | How the printed walls attach |
| V5 | BB7515 blower: outline, outlet size and position, mounting holes | Blower bracket |
| V6 | How many fan headers each board has, and their type (3- or 4-pin) | Fan wiring |
| V7 | PWM hub and USB 2.5 GbE adapter: body sizes | Mounts |

### Case structure: slide-in rails (decided 2026-10-16)

Design review: https://claude.ai/artifact/1nEufsxaiA2zksetCsb2rq. The case is built to forgive print
and assembly errors instead of needing every hole to line up.

- **Plates slide in.** Fan plates, dividers and the back plate drop down channels (rib pairs) on the
  side walls' inside faces and stand on a stop at the bottom. Channel 3.8 mm for a 3 mm plate; plate
  ends 1 mm short of each wall. The walls can be 1 mm too close or 2 mm too far apart.
- **Lids hold them down.** Each cold box's lid sits over the tops of its fan plate and divider; the
  roof does the same for the back plate.
- **Only tie parts screw to the walls**, through slots: lids and roof tiles (±1.5 mm up and down),
  cradles and crossbars (±1.5 mm front to back). 26 wall screws in all, down from 74.
- **2 mm fan gap**, set with the printed shim: hold it between fan and fins while you tighten a
  board's cradle and crossbar, then pull it out.
- **Nuts press into hex pockets** on the lids, roof tiles and splice bars and stay there. The cradles
  and crossbars already printed keep their slot nuts; tape holds those during assembly.
- **Crossbar hold-down:** the new crossbars have a lip over each PCB corner, so a tipped case can't
  lift a board. Unscrew the crossbar to lift a board out. The crossbars already printed work, without
  the lip.
- **Side walls in six pieces each:** three strips split at the dividers' rails (screwed front to back
  through the rail stop and a post above the lid, M3 × 10), each in a lower and an upper piece
  (joined by splice bars on the inside of each cold box and the rear plenum, M3 × 8).

Print files (`cad/print/case_parts.py` regenerates them all from `cad/v1_model.py`):

| File in `cad/print/stl/` | Qty | Notes |
|---|---|---|
| `rail_test.stl` | 1 | **Print first** (about 30 min): rail section, plate offcut, press-in nut block, gap shim |
| `case/wall_R_strip{1,2,3}_{lower,upper}.stl` | 1 each | inside face up |
| `case/wall_L_strip{1,2,3}_{lower,upper}.stl` | 1 each | inside face up |
| `case/fanplate_lower.stl`, `case/fanplate_upper.stl` | 3 each | upper bed also has the two joining strips |
| `case/divider_lower.stl`, `case/divider_upper.stl` | 2 each | |
| `case/backplate_lower.stl`, `case/backplate_upper.stl` | 1 each | |
| `case/roof_front.stl`, `case/roof_back.stl` | 1 each | upside down |
| `case/small_parts.stl` | 1 | 3 lids, 8 splice bars, 2 gap shims |
| `case/crossbars_holddown.stl` | 1 | optional: crossbars with the hold-down lip |

Assembly order:

1. Join each side wall's six pieces on the bench (splice bars, then the front-to-back seam screws).
2. Bolt both walls to the front and back rack frames: an open-topped box.
3. Screw in the cradles. Stand each board in its cradle and fit its crossbar loosely.
4. Drop each column's divider halves and fan plate halves (fans, clips, joining strips and blower
   holder already fitted) down their rails.
5. Shim the fan gap, slide the board against the shim, tighten cradle and crossbar, remove the shim.
6. Lids (2 screws each), back plate halves, roof tiles (8 screws). Window panels any time after.

To change a fan or board later: roof tile and that column's lid off, then lift the part out.

### Side windows (decided 2026-10-15)

Each column has a window opening over its hot zone, closed by a clear **printed PCTG** panel
screwed to the outside of the wall. The opening is split by the solid band at the wall seam; one
panel covers both parts. The panels carry no load, so they can go on any time. Until then, tape
card over the openings so hot air can't leak out sideways and back into the intakes.

| Panel | Qty | Size (mm) | File |
|---|---|---|---|
| Right wall | 3 | 83.7 × 233 × 2 | `cad/print/stl/window_panel_right.stl` |
| Left wall (shorter: solid wall round the power-cable slots) | 3 | 83.7 × 158 × 2 | `cad/print/stl/window_panel_left.stl` |

- **Filament:** clear PCTG, about 260 g for all six; one 1 kg spool. Bambu Studio profile
  "Generic PCTG @BBL A1".
- **Clarity:** dry the filament, 100 % infill in one direction, slow outer walls. The face against
  the plate copies the plate: the textured PEI gives a frosted pattern, a smooth plate a glossy face.
  Printed PCTG is translucent, not glass-clear.
- **Test first:** print one right panel and screw it on before the other five. The 4 mm holes
  allow ±0.5 mm; PCTG's shrink hasn't been measured, so the export uses the PLA Matte figure.
- **Screws:** M3 × 8 from the outside into nuts pressed into the pockets on the wall's inside face.
- **The view:** the boards stand across the case, so a side window shows each board edge-on: fans,
  fins, PCB edge and blower. The board faces show only through the front and back frames.

## Version 2 (later): AIO water cooling and the heatsink cut

This needs ABS, ASA, PC or PET-CF for the AIO mount. The work below is paused, not cancelled.
The pilot measurements from board 3 are kept for when it resumes.

**V2 order:**
1. Cut the pilot heatsink.
2. Design and print the Teucer mount, then test-fit it.
3. Fit the AIO on the pilot, check for leaks, and bench-test it.
4. Repeat on boards 2 and 3.
5. Rework the case columns for the radiators.

### How the stock heatsink is built (from MandicReally's model)

- One fin stack sits on **three separate base plates**:
  - a rear VRM base at the I/O end;
  - the large centre base over the APU;
  - a front VRM base at the far end.
- Between the bases, the fins are bare underneath. The heatpipes stay inside the centre section,
  so cutting through the two bare-fin gaps cuts only fins.
- **Eight screws hold it on, all from the backplate side:**
  - 4 spring screws around the APU go through the backplate's large holes into 4 threaded posts
    on the centre base. These posts sit on a 95.7 × 95.7 mm square centred on the APU.
  - 4 plain screws go through the backplate's outer standoffs into the two VRM bases, 2 each.

**After the cut:**
- Each VRM piece keeps its own 2 screws and goes back where it was.
- The centre piece flips over onto the back of the board, fins outward. Its 4 posts still line up
  with the 4 APU holes, because the square is centred on the APU.
- Its base then sits on the outside of the stock backplate, over the GDDR6.
- The AIO mount on the front screws into those posts, so the centre piece also serves as the
  **AIO's back brace**.

**AIO bracket status.** The NexGen V1 "AM4 - Generic" bracket used in the CAD model is obsolete:
its author replaced it with V2 (Printables #1782473). V2 is made for the Thermalright Aqua Elite.
It clamps with a printed plate on the back of the board, exactly where the centre piece goes.
So the plan is a **Teucer-specific mount that anchors into the centre piece's posts**, designed from
the measurements below.

### Step 1: cut the stock heatsink (pilot board)

#### Tools

- Phillips screwdriver and digital calipers.
- **Hacksaw with a 32 TPI blade.** A bandsaw with a metal blade is better if you have one.
- Vice or two clamps, plus two straight scrap boards.
- Masking tape, fine marker, small square or straight edge.
- Flat file, old toothbrush, compressed air, isopropyl alcohol (90 %+), lint-free cloth.
- Safety glasses and gloves. The cut fins are sharp.
- Labelled zip bags, one per board, for the screws.

#### A. Take the heatsink off

Work unplugged, on a non-static surface.

1. Photograph the board front and back.
2. Turn it over. Loosen the **4 spring screws around the APU** in an X pattern, two turns at a time,
   until they are free. Then remove the **4 outer screws**. Bag them.
3. Lift the heatsink straight up. If the paste or putty holds it, twist gently. Never pry against
   the board.
4. Lift off the backplate. **Photograph what is between it and the 8 GDDR6 chips:**
   - pads, or no pads;
   - whether the plastic insulator sheet has windows over the chips, or covers them.
5. **Before cleaning anything**, measure the thickness of the pads:
   - under the two VRM bases;
   - on the memory.

   The VRM pieces must go back on pads of the same thickness. A thicker pad holds the heatsink
   off its parts.

#### B. Measure before cutting

Turn the heatsink fins-down and photograph its underside with a ruler in the shot.

| # | Measure | Model value (photo-aligned, not exact) |
|---|---|---|
| H1 | Length of the centre base plate, along the fins | ~116 mm |
| H2 | Bare-fin gap between the centre base and the I/O-end VRM base | ~31 mm |
| H3 | Bare-fin gap between the centre base and the far-end VRM base | ~39 mm |
| H4 | Does any heatpipe cross either gap? | No |
| H5 | APU post thread: diameter, pitch and length of one of the 4 spring screws. Is the post hole open at both ends? | Probably M3 |
| H6 | Post profile, measured from the base: each step's diameter and height | ~5.9 mm dia × 2 mm, then ~4.25 mm dia × 2.8 mm (4.8 mm total) |
| H7 | Overall fin-stack width and height | ~119.5 × ~24 mm |

**Stop and send me the numbers if:**
- a heatpipe crosses a gap;
- the posts aren't threaded.

H1 to H3 only confirm the model. The cut is set from the real plate edge, so a difference there
doesn't block cutting.

#### C. Mark and cut

1. **Cut line:** across the fins, in each bare-fin gap, **2 mm out from the edge of the centre base**.
   - Keep the centre base whole.
   - Saw on the VRM side of the line, so the blade's width comes off the VRM pieces.
   - All the leftover fin length stays on the VRM pieces. If the AIO mount needs more room later,
     they can be trimmed, but metal can't be added back.
2. Wrap masking tape tightly around the fin stack over each cut zone. It stops the fins
   fluttering. Draw the line all the way round with the square.
3. Clamp the heatsink between the two boards, with their edges right beside the line, so the
   fins are held.
4. **Cut with light, full-length strokes and let the blade do the work.** Turn the part to keep
   the cut square on all sides. Repeat for the second line.
5. Peel off the tape. File the cut faces with strokes going away from the fins. Straighten any
   bent fins with a thin flat blade.
6. **Clean.**
   - Blow out the chips, then scrub in warm soapy water and rinse.
   - Wipe with isopropyl alcohol and dry completely.
   - Cut and clean in a different room from the boards. Aluminium swarf on a board can short it.

#### D. Dry test-fit (no paste, no power)

1. **Front:** put both VRM pieces back on their pads. Do them up finger-tight with their own outer
   screws through the backplate.
2. **Back:** hold the centre piece fins-out on the backplate, posts in the 4 large holes.
3. Measure and photograph:

| # | Measure |
|---|---|
| F1 | Gap between the two VRM pieces, at board level and at fin-top level |
| F2 | Height of the VRM fin tops above the PCB |
| F3 | Does the centre piece sit flat on the backplate, or does a post or the shoulder touch the board? |
| F4 | Distance from the post tip to the PCB's front surface, looking through an APU hole from the front |

If F1 to F4 look right, cut boards 2 and 3 the same way. The pilot board stays apart until its
AIO mount is printed. Boards 2 and 3 keep running until you cut them.

### Pilot results so far (board 3, 2026-10-09)

**From the photos:**

| Item | Result |
|---|---|
| Centre base plate | 117.9 mm along the fins × 119.5 mm across. The model says 115.7 × 120.1; the cut is set from the real edge, so the difference doesn't matter. |
| Posts | 102.5 mm outer-to-outer along one side, so about 96 mm centre-to-centre. This matches the board's 95.7 mm hole square. Stepped, threaded. |
| Heatsink height | 28 mm |
| Fin direction | **Along the board length**, confirmed from the top and underside photos. The cut goes across every fin. |
| VRM contact | Putty residue is on the fin bottoms in both bare-fin gaps, so the VRMs touch the fins there directly. Cutting at the centre plate's edge keeps that whole contact zone on the VRM pieces. |
| VRM piece mounting | After the cut, each piece is held only by its 2 screws at the far end. In test-fit D, check it doesn't rock on its putty. |
| Memory | Pads on all 8 GDDR6 chips. The backplate is aluminium with pads on its inside face. |
| Spring screw | Head 6.9 mm. 7.0 mm is read as the overall length (to confirm). |
| APU-to-VRM clearance | 31.6 mm on the I/O side and 35.4 mm on the power side, read as the APU package edge to the nearest capacitor row (to confirm). |
| Backplate | 1.5 mm, read as its thickness (to confirm). |

**Teucer AF-120 kit:**
- **Pump brackets:**
  - B: two cranked bars with slotted ends, for Intel LGA1700/115x/1366.
  - C: AMD AM4/AM5 brackets.
- **A:** a plastic Intel backplate with yellow sliding nuts.
- **E:** 4 knurled thumbscrews.
- **F:** 5 bracket screws.
- **The Intel backplate can't reach the board's holes.** Its sliders top out around 80 mm (LGA1366), and the board's holes are 95.7 mm apart.

**Mount options, decided by M1 below:**
- (a) The B bars' slots reach the 95.7 mm square. Then long M3 screws with springs go through the slots and the board into the centre piece's posts, and **no printed part is needed**.
- (b) They don't reach. Then a printed adapter frame bolts into the posts and carries inserts at the bars' slot positions.

### Measurements still needed for printed parts

#### Batch 1: the AIO mount (the first print)

| # | Measure |
|---|---|
| M1 | **Screw both B bars onto the pump.** Measure the slot-centre range (min to max) along each bar and between the two bars. Photograph it with the caliper. Do the same with the C brackets. |
| M2 | Distance from the cold-plate face to the underside of the bars. Cold-plate size. |
| M3 | One E thumbscrew: overall length, thread length, thread diameter. Does it have a spring or shoulder? |
| M4 | Post thread: does an M3 screw go into a post? Post outer diameter and height. |
| M5 | After cutting: the backplate's hole diameter at the 4 spring screws. Does the centre piece sit flat on the backplate with its posts through those holes? |
| M6 | Printer model and the filaments you have. The mount must not be PLA or PETG: ABS, ASA, PC or PET-CF. |

#### Batch 2: the radiator (V1 already covers the case)

| # | Measure |
|---|---|
| C3 | Radiator: thickness (assumed 27 mm), length including end tanks, fan-screw hole spacing, port positions |
