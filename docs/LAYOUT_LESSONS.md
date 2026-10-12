# v15 lessons → how they are applied (main board v1.1, branch board v1)

| # | v15 lesson | Applied in | How / evidence |
|---|---|---|---|
| 1 | **Arcs only, no sharp 90° bends** | `tools/pcbkit.py: Board.path()` | Every polyline (structured spine and A* routes alike) gets circular fillets at each corner (r 0.6 mm signals, 0.4 mm on B fan-out, auto-reduced on short legs). The board outline has R4 arc corners. |
| 2 | **Zone refill before plotting / DRC** | `tools/fill_drc.py`, `tools/drc.sh`, `tools/repair.py` | `ZONE_FILLER.Fill()` runs and saves before every DRC and before gerber export. The repair pass refills before each iteration. |
| 3 | **0.127 mm minimum clearance in project rules** | `main_v1.kicad_pro`, `main_gen.py` | `min_clearance = 0.127`, netclass clearance 0.15, track ≥ 0.15 (0.2 default), via 0.5/0.3, edge 0.3. Router keep-out = w/2 + 0.15 + 0.02. |
| 4 | **TVS/ESD near connectors** | main: D4 SMBJ15A at J10, U3 USBLC6-2SC6 at USB-C; branch: D30 SMBJ15A at J30, UE0–15 USBLC6-2SC6 at each strand JST | Ports J1–J8 (board-to-board ribbon) have no separate TVS. The LVC245 is 5 V tolerant, the branch side uses AHCT Schmitt inputs, and a 33 Ω series resistor sits on each strand output. *Open item:* add TPD4E05U06 per port if field ESD shows up. |
| 5 | **Decoupling close to pins** | `main_gen.py` power block | Each 74LVC245 has its own 100 nF 0603 placed 5.6 mm from the IC centre on the VCC (pin 20) side. The track runs pin 20 → cap → 3V3 via, with the cap GND via 1 mm from its pad. Buck: C2 100 nF on VIN, 10 µF/50 V, C7 BST. ESP32: C5/C8 near pin 2. |
| 6 | **Thermal reliefs on small passives** | zone settings | GND pours use thermal connection (gap 0.25, spoke 0.35) on all pads. The USB-C GND pads are set to solid to avoid starved thermals. |
| 7 | **Fiducials** | FID1–3 | 3× 1 mm/2 mm-mask global fiducials in non-collinear corners (12,4), (295,14), (295,116). |
| 8 | **Stackup defined** | `ds.SetBoardThickness(1.6)`, fab notes | 2-layer: F.Cu 35 µm / FR-4 1.51 mm / B.Cu 35 µm, HASL/ENIG, green mask. Impedance is not controlled (13 MHz edges; the ribbon dominates). |
| 9 | **Wide power copper, pours, via stitching** | `main_gen.py` | +3V3 distribution lines are 1.2 mm on B.Cu (2 lines, ~0.43 A each). F+B GND pours, plus 446 stitching vias on a 5 mm grid wherever clearance allows. Buffer GND pins and cap GND pads have dedicated vias. |
| 10 | **IPC-2221 current sizing** | see table below | External layer, 1 oz, ΔT = 10 °C: I = 0.048·ΔT^0.44·A^0.725 (A in mil²). |
| 11 | **Fuse per output** | branch: F10–F25 PTC 2 A hold per strand; main: F1 PTC 2 A on input | Per-port output is logic-level only (no power on ribbon), so it needs no fuse. |
| 12 | **Reverse polarity protection** | main: D3 SS34 series; branch: TPS259474L (integrated reverse-polarity block to −15 V) | The diode drop (≈0.45 V at 0.4 A) is fine on the main board. The branch board uses the eFuse's back-to-back FETs, so no diode loss at 3.5 A. |
| 13 | **eFuse** | branch U30 TPS259474LRPWR (C2864845) | R_ILM 750 Ω → 4.46 A limit, UVLO 9.2 V, OVLO 15.8 V, dV/dt 10 nF, ITIMER 10 nF, PG → pull-up. *Footprint `cube:TI_RPW0010A` (0.45 mm pitch) still has to be drawn: this is the only ERC warning.* |

## IPC-2221 sizing (external, 1 oz = 1.38 mil, ΔT 10 °C)
| Net | Width | I_max (calc) | I_design |
|---|---|---|---|
| Bus/port signals | 0.20 mm | 0.75 A | < 20 mA |
| Corner power (VIN, SW, 3V3 feeders) | 0.30 mm | 1.0 A | ≤ 0.6 A (2 parallel 3V3 feeders) |
| +3V3 distribution lines (B.Cu) | 1.20 mm | 2.8 A | 0.43 A each |
| Branch 12 V input (planned pour) | ≥ 2.5 mm | 5.1 A | 3.5 A |
| Branch +5V buck output → strands (planned pour) | ≥ 5 mm / both layers | 9 A per layer | 7.7 A |

## Gates (main board v1.1)
- DRC: **0 errors, 0 unconnected**. Warnings: 199 silk overlap/over-copper (generated reference text, cosmetic), 3 zero-length dangling stubs, 2 co-located EPAD holes (ESP32 footprint).
- ERC (main schematic, generated from the same netlist): 0. Schematic↔PCB parity is **not linked**: the schematic is regenerated from the PCB netlist, so no UUID annotation link exists yet (289 parity items).
- Branch ERC: 0 errors, 1 warning (missing custom eFuse footprint).

## 2026-10-12 additions
* ESD at every connector, including the 8 ribbon ports (6 × TPD4E05U06 per port, bottom side, ≤ 4.5 mm from the header pins).
* The schematic is the source of truth: `tools/sch2pcb.py` links KIIDs and checks value, footprint and net, so the DRC parity gate = 0.
* Zone refill runs before every plot (`tools/fab.sh`). 3D models are fetched before renders.
* Gate status: main_v1 DRC errors 0, unconnected 0, parity 0. strip variants: ERC 0, PCB pending.
