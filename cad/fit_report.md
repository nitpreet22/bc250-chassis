# BC-250 cluster fit report

Document: `bc250_cluster.FCStd` - 74 checked objects

## Clashes (3)

| Object A | Object B | Overlap (mm^3) | Note |
|---|---|---|---|
| Node1_Left_Components | Node1_Left_NexGen_AM4_GenericBottom | 19.8 | Investigated: bracket is aligned to the 4 cooler holes (95.7 mm square) within 0.1 mm. Its flat underside sits on 0.4 mm SMD passives and one corner overlaps a 3.5 mm part next to the (-28.7, -37.2) hole by ~1.8 mm. Likely a board-model inaccuracy; check at test-fit. |
| Node3_Right_Components | Node3_Right_NexGen_AM4_GenericBottom | 19.8 | Investigated: bracket is aligned to the 4 cooler holes (95.7 mm square) within 0.1 mm. Its flat underside sits on 0.4 mm SMD passives and one corner overlaps a 3.5 mm part next to the (-28.7, -37.2) hole by ~1.8 mm. Likely a board-model inaccuracy; check at test-fit. |
| Node2_Middle_Components | Node2_Middle_NexGen_AM4_GenericBottom | 19.8 | Investigated: bracket is aligned to the 4 cooler holes (95.7 mm square) within 0.1 mm. Its flat underside sits on 0.4 mm SMD passives and one corner overlaps a 3.5 mm part next to the (-28.7, -37.2) hole by ~1.8 mm. Likely a board-model inaccuracy; check at test-fit. |

Not checked: overlaps between a board's own PCB / components / connectors (they come from the downloaded STEP, e.g. pins modelled inside the PCB).

## Clearances (minimum distance)

| Between | And | mm |
|---|---|---|
| Node1_Left_TeucerPump | SidePanel_L | 4.0 |
| Node3_Right_TeucerPump | SidePanel_R | 4.0 |
| Node1_Left_NexGen_BackBrace | Node2_Middle_NexGen_BackBrace | 21.0 |
| Node2_Middle_TeucerPump | Node3_Right_NexGen_BackBrace | 18.0 |
| Node2_Middle_USB25GDongle | TopPanel | 16.8 |
| Node1_Left_PCB | CardShelf_Printed | 0.5 |
| CardShelf_Printed | PSU_MSI_A1000PL | 0.5 |
| Node2_Middle_KO_PowerPlugs | Upright_FrontL | 79.0 |
| Node3_Right_KO_PowerPlugs | Upright_FrontR | 24.0 |
| Tube_Node1_Left_1 | Upright_RearL | 2.0 |
| Tube_Node3_Right_2 | Upright_RearR | 2.0 |

## Parts outside the rack frame (280 x 200 x 469.45)

| Object | Sticks out by (mm) |
|---|---|
| KO_PSU_ACCord | rear 15.0 |
| FrontFanPanel_Printed | front 3.0 |
| Switch_TL_SG105_M2 | above 28.0 |
| RadiatorPlate_Bottom_Printed | rear 4.5 |
| Radiator_Bottom | rear 33.0 |
| Fan_ArcticP12_BottomExhaust | rear 58.5 |
| RadiatorPlate_Middle_Printed | rear 4.5 |
| Radiator_Middle | rear 33.0 |
| Fan_ArcticP12_MiddleExhaust | rear 58.5 |
| RadiatorPlate_Top_Printed | rear 4.5 |
| Radiator_Top | rear 33.0 |
| Fan_ArcticP12_TopExhaust | rear 58.5 |
| RadiatorPorts_Node1_Left | rear 6.0 |
| RadiatorPorts_Node2_Middle | rear 6.0 |
| RadiatorPorts_Node3_Right | rear 6.0 |

## Tube centre-line lengths

| Tube | mm |
|---|---|
| Tube_Node1_Left_1 | 228 |
| Tube_Node1_Left_2 | 242 |
| Tube_Node2_Middle_1 | 128 |
| Tube_Node2_Middle_2 | 142 |
| Tube_Node3_Right_1 | 155 |
| Tube_Node3_Right_2 | 141 |

## Overall envelope including external parts

X -140.0 .. 140.0 (280.0 wide), Y -3.0 .. 258.5 (261.5 deep), Z 0.0 .. 502.4 (502.4 tall)
