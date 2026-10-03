# Reference models and dimension sources

Downloaded 2026-10-03 from Printables. Files are unmodified. The licences allow
personal use with attribution. None of them allow commercial use, and the NexGen3D
mount allows no derivatives, so redistribute these files (or an `.FCStd` that embeds
them) only on the licence terms.

| File | Printables model | Author | Licence | Used for |
|---|---|---|---|---|
| `BC250_Completeish_V1.step` | [#1828755 ASRock BC250 Complete-ish CAD Model](https://www.printables.com/model/1828755-asrock-bc250-complete-ish-cad-model) | MandicReally | CC BY-NC-SA 4.0 | Board geometry in the assembly (stock heatsink + backplate excluded) |
| `board_BC-250_torassk.step` | [#1341336 Accurate 3D model of the AMD BC-250 board](https://www.printables.com/model/1341336-accurate-3d-model-of-the-amd-bc-250-board) | torassk | Printables Standard Digital File License | Cross-check only: PCB 308.0 x 144.3 mm (341.6 mm incl. I/O bracket and end bracket) |
| `nexgen3d_aio_mount/*.3mf` | [#1554003 NexGen3D: AIO Mount for the BC-250](https://www.printables.com/model/1554003-nexgen3d-aio-mount-for-the-bc-250) | NexGen-3D-Printing | CC BY-NC-ND 4.0 | AIO bracket ("AM4 - Generic" top/bottom + back brace) |

Note: NexGen3D lists the Teucer AIO as "fitment being tested". The generic AM4 bracket
is the closest published match, but it is not confirmed for the Teucer AF-120.

## Off-the-shelf part dimensions

| Part | Dimensions used (mm) | Source / status |
|---|---|---|
| Tecmojo 9U 10" rack | 280 W x 200 D x 469.45 H frame, 502.45 with handles; 210 clear between uprights | Tecmojo spec drawing (product image `11120502-___2.jpg`) |
| Rack: clear width between side panels | 266 | **Estimate** (side panels mount outside the 35 mm uprights) - measure |
| Rack: upright depth, floor height | 20, 22 | **Estimate** - measure |
| MSI PRO A1000PL PCIE5 | 150 x 150 x 86 | [MSI spec page](https://www.msi.com/Power-Supply/PRO-A1000PL-PCIE5/Specification) |
| Teucer AF-120 cold head | 83 x 78.6 x 58 | [AF-120 manual](https://manuals.plus/ae/1005007431587335) |
| Teucer AF-120 radiator | 155 x 120 x 27 | **Estimate** (not published; AF-S360 is 395 x 120 x 27) - measure |
| Arctic P12 Silent (ACFAN00130A) | 120 x 120 x 25 | Arctic P12 standard frame |
| BB7515 blower | 75 x 75 x 15 | **Estimate** from model number - measure |
| TP-Link TL-SG105-M2 | 209 x 126 x 26 | [TP-Link spec](https://www.tp-link.com/us/business-networking/soho-switch-unmanaged/tl-sg105-m2/) |
| USB 2.5G Ethernet dongle | 62 x 26 x 17 body | **Estimate** - measure |
| 1-to-5 PWM fan hub | 80 x 25 x 12 | **Estimate** - measure |
