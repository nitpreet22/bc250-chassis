# BC-250 cluster fit report

Document: `bc250_cluster.FCStd` - 102 checked objects

## Clashes (3)

| Object A | Object B | Overlap (mm^3) | Note |
|---|---|---|---|
| Node1_Components | Node1_NexGen_AM4_GenericBottom | 19.8 | Investigated: bracket is aligned to the 4 cooler holes (95.7 mm square) within 0.1 mm. Its flat underside sits on 0.4 mm SMD passives and one corner overlaps a 3.5 mm part next to the (-28.7, -37.2) hole by ~1.8 mm. Likely a board-model inaccuracy; check at test-fit. |
| Node2_Components | Node2_NexGen_AM4_GenericBottom | 19.8 | Investigated: bracket is aligned to the 4 cooler holes (95.7 mm square) within 0.1 mm. Its flat underside sits on 0.4 mm SMD passives and one corner overlaps a 3.5 mm part next to the (-28.7, -37.2) hole by ~1.8 mm. Likely a board-model inaccuracy; check at test-fit. |
| Node3_Components | Node3_NexGen_AM4_GenericBottom | 19.8 | Investigated: bracket is aligned to the 4 cooler holes (95.7 mm square) within 0.1 mm. Its flat underside sits on 0.4 mm SMD passives and one corner overlaps a 3.5 mm part next to the (-28.7, -37.2) hole by ~1.8 mm. Likely a board-model inaccuracy; check at test-fit. |

Not checked: overlaps between a board's own PCB / components / connectors (they come from the downloaded STEP, e.g. pins modelled inside the PCB).

## Clearances (minimum distance)

| Between | And | mm |
|---|---|---|
| Node1_TeucerPump | FrontFrame_Window | 16.5 |
| Node1_MemoryHeatsink_CutCentre | ColumnDivider_1 | 15.5 |
| Node2_TeucerPump | ColumnDivider_1 | 15.5 |
| Node3_MemoryHeatsink_CutCentre | BackFrame_Window | 16.5 |
| Node1_Radiator | FrontFrame_UprightL | 2.5 |
| Node3_MemoryHeatsink_CutCentre | BackFrame_UprightR | 3.8 |
| Node1_KO_PowerPlugs | SideWall_L_CableSlots | 12.3 |
| Node1_IntakeFan_ArcticP12 | Node1_PCB | 7.5 |
| Node1_MemoryBlower | Node1_MemoryHeatsink_CutCentre | 3.2 |
| Node1_USB25GDongle | Node1_Tube_2 | 5.5 |
| Node1_RadiatorFan_Teucer | TopGrille | 2.0 |
| PSU_MSI_A1000PL | PSUBox_RearWall_FanGrille | 3.0 |
| PSU_MSI_A1000PL | PSUBox_FrontWall_ChannelOpening | 0.5 |
| PWMFanHub_1 | PSUBox_Lid | 14.0 |

## Size per assembly (bounding box, mm)

| Assembly | Width X | Depth Y | Height Z | X range | Z range |
|---|---|---|---|---|---|
| Rack_Frames_Reused | 200.0 | 383.0 | 502.4 | -100.0 .. 100.0 | 0.0 .. 502.4 |
| Printed_Case | 206.0 | 383.0 | 499.4 | -103.0 .. 103.0 | -30.0 .. 469.4 |
| Node | 172.8 | 366.0 | 441.9 | -89.0 .. 83.8 | 22.5 .. 464.4 |
| Cable_Channel | 45.5 | 347.0 | 126.0 | -148.5 .. -103.0 | 27.0 .. 153.0 |
| PSU_Box | 228.0 | 95.5 | 223.0 | -123.0 .. 105.0 | -30.0 .. 193.0 |
| Network | 26.0 | 126.0 | 209.0 | 103.5 .. 129.5 | 150.0 .. 359.0 |

## Tube centre-line lengths

| Tube | mm |
|---|---|
| Node1_Tube_1 | 209 |
| Node1_Tube_2 | 239 |
| Node2_Tube_1 | 209 |
| Node2_Tube_2 | 239 |
| Node3_Tube_1 | 209 |
| Node3_Tube_2 | 239 |

## Overall envelope including external parts

X -148.5 .. 129.5 (278.0 wide), Y 0.0 .. 479.5 (479.5 deep), Z -30.0 .. 502.4 (532.5 tall)
