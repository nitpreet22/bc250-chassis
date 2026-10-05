# Reference models and dimension sources

Downloaded 2026-10-03 from Printables. Files are unmodified. The licences allow
personal use with attribution. None of them allow commercial use, and the NexGen3D
mount allows no derivatives, so redistribute these files (or an `.FCStd` that embeds
them) only on the licence terms.

| File | Printables model | Author | Licence | Used for |
|---|---|---|---|---|
| `BC250_Completeish_V1.step` | [#1828755 ASRock BC250 Complete-ish CAD Model](https://www.printables.com/model/1828755-asrock-bc250-complete-ish-cad-model) | MandicReally | CC BY-NC-SA 4.0 | Board, stock backplate (moved back from its 200 mm exploded offset) and the 3-piece cut stock heatsink. The full uncut heatsink is not used. |
| `board_BC-250_torassk.step` | [#1341336 Accurate 3D model of the AMD BC-250 board](https://www.printables.com/model/1341336-accurate-3d-model-of-the-amd-bc-250-board) | torassk | Printables Standard Digital File License | Cross-check only: PCB 308.0 x 144.3 mm (341.6 mm incl. I/O bracket and end bracket) |
| `nexgen3d_aio_mount/*.3mf` | [#1554003 NexGen3D: AIO Mount for the BC-250](https://www.printables.com/model/1554003-nexgen3d-aio-mount-for-the-bc-250) | NexGen-3D-Printing | CC BY-NC-ND 4.0 | AIO bracket ("AM4 - Generic" top/bottom + back brace) |

Note: NexGen3D lists the Teucer AIO as "fitment being tested". The generic bracket is drilled for
the AM4/AM5 and LGA1700/1851 patterns, and the Teucer booklet lists AM4/AM5 and LGA17xx hardware,
so the patterns should match. Confirm when the cooler arrives.

## Off-the-shelf part dimensions

| Part | Dimensions used (mm) | Source / status |
|---|---|---|
| Tecmojo 9U 10" rack | 280 W x 200 D x 469.45 H frame, 502.45 with handles; 210 clear between uprights | Tecmojo spec drawing (product image `11120502-___2.jpg`) |
| Rack: clear width between side panels | 266 | Confirmed by the owner; puts each window 7 mm in from the frame's outer face |
| Rack: upright cross-section, floor height | 20 x 35, 22 | **Estimate**: the side frames are now the case's front and back - measure |
| MSI PRO A1000PL PCIE5 | 150 x 150 x 86 | [MSI spec page](https://www.msi.com/Power-Supply/PRO-A1000PL-PCIE5/Specification) |
| Teucer AF-120 cold head | 83 x 78.6 x 58 | [AF-120 manual](https://manuals.plus/ae/1005007431587335) |
| Teucer AF-120 radiator | 155 x 120 x 27 | 155 x 120 from the owner; 27 thickness still an **estimate** |
| Teucer AF-120 tubes / sockets | 300 mm tubes; AM4/AM5, LGA2011, LGA17xx, 115x, 1366 | Owner, from the cooler booklet |
| Arctic P12 Silent (ACFAN00130A) | 120 x 120 x 25; 1050 rpm, 24.1 CFM, 0.5 mmH2O, 3-pin | [PCPartPicker / Arctic listing](https://pcpartpicker.com/product/pBbCmG/arctic-p12-silent-241-cfm-120-mm-fan-acfan00130a) |
| Teucer AF-12025 radiator fan | 120 x 120 x 25; 1000-1800 rpm, 78 CFM, 2.06 mmH2O, PWM | [AF-120 manual](https://manuals.plus/ae/1005007431587335) |
| BC-250 thermals | 136 W avg / 223 W peak package (40 CU @ 2 GHz); memory max ~80 °C, no sensor; 220-250 W gaming, >320 W Furmark at the wall | [BC-250 docs: cooling](https://elektricm.github.io/amd-bc250-docs/hardware/cooling/), [overclocking](https://elektricm.github.io/amd-bc250-docs/bios/overclocking/) |
| BB7515 blower | 75 x 75 x 15 | **Estimate** from model number - measure |
| TP-Link TL-SG105-M2 | 209 x 126 x 26 | [TP-Link spec](https://www.tp-link.com/us/business-networking/soho-switch-unmanaged/tl-sg105-m2/) |
| USB 2.5G Ethernet dongle | 62 x 26 x 17 body | **Estimate** - measure |
| 1-to-5 PWM fan hub | 80 x 25 x 12 | **Estimate** - measure |
