# BC-250 cluster fit report (Version 1)

Document: `bc250_v1.FCStd` - 78 checked objects

## Clashes (3)

| Object A | Object B | Overlap (mm^3) | Note |
|---|---|---|---|
| Node3_Connectors | Node3_IOBracket_EST | 14.0 | Estimated bracket (not in the STEP): the guessed back strip overlaps the connectors' through-hole pins. Only the shape guess is wrong here; no printed part comes near it. |
| Node1_Connectors | Node1_IOBracket_EST | 14.0 | Estimated bracket (not in the STEP): the guessed back strip overlaps the connectors' through-hole pins. Only the shape guess is wrong here; no printed part comes near it. |
| Node2_Connectors | Node2_IOBracket_EST | 14.0 | Estimated bracket (not in the STEP): the guessed back strip overlaps the connectors' through-hole pins. Only the shape guess is wrong here; no printed part comes near it. |

Not checked: overlaps between a board's own PCB / components / connectors / stock heatsink / backplate (they come from the downloaded STEP, e.g. pins modelled inside the PCB).

## Clearances (minimum distance)

| Between | And | mm |
|---|---|---|
| Node1_StockHeatsink | Col1_FanPlate | 10.2 |
| Node1_StockHeatsink | Col1_Cradle | 7.7 |
| Node1_StockHeatsink | Col1_Crossbar | 33.6 |
| Node1_Backplate | Col1_BlowerHolder | 3.0 |
| Node1_Backplate | Col1_Crossbar | 3.5 |
| Node1_Backplate | Col1_Cradle | 3.0 |
| Node1_Backplate | Col2_Divider | 21.9 |
| Node1_Fan_Lower | Node1_StockHeatsink | 2.0 |
| Node1_IOBracket_EST | Col1_FanPlate | 48.6 |
| Node1_Blower | Node1_Backplate | 4.5 |
| Node1_KO_PowerPlugs | SideWall_L_CableSlots | 13.0 |
| Node1_KO_NetworkAdapter | RoofGrille | 59.4 |
| Node1_Components | Col1_Crossbar | 10.1 |
| Node3_Backplate | BackPlate | 21.8 |

## Size per assembly (bounding box, mm)

| Assembly | Width X | Depth Y | Height Z | X range | Z range |
|---|---|---|---|---|---|
| Rack_Frames_Reused | 200.0 | 421.1 | 502.9 | -100.0 .. 100.0 | 0.0 .. 502.9 |
| Printed_Case | 212.0 | 427.1 | 469.5 | -106.0 .. 106.0 | 0.0 .. 469.5 |
| Node | 165.0 | 310.1 | 368.1 | -87.0 .. 78.0 | 39.0 .. 407.1 |

## Tube centre-line lengths

| Tube | mm |
|---|---|

## Overall envelope including external parts

X -106.0 .. 106.0 (212.0 wide), Y -3.0 .. 424.1 (427.1 deep), Z 0.0 .. 502.9 (502.9 tall)
