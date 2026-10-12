# LED Cube 32×32×32 Controller — Architecture Study (Phase 1)

## Кратко (RU)
**Вердикт: PASS WITH RISKS (архитектура, без схемы/разводки).**
- Куб 32×32×32 = 32 768 одноцветных LED, шаг 31,25 мм, ~1 м³. **Слои = общий анод (32 слоя), вертикальные колонны = катоды (1024 колонны).** Развёртка **1/32** по слоям.
- Драйверы колонн: **64× MBI5153 (16 кан., встроенные SRAM + S-PWM, 1:32 scan)** вместо MBI5124 из v15. С MBI5124 МК должен был бы сам делать BCM: 252 Мбит/с — нереально для одного ESP32-S3. С MBI5153 МК передаёт только кадр: 31,5 Мбит/с (16 бит, 60 fps).
- **Модульность:** 16 плиток-оснований 250×250 мм (4×4), на каждой 4× MBI5153 = 64 колонны; провода колонн впаиваются прямо в металлизированные отверстия плитки → **никаких кабелей на 1024 канала**. Плитки соединяются с контроллером короткими IDC-шлейфами 2×8.
- Контроллер (одна плата на краю куба): **ESP32-S3** (Wi-Fi, SD, анимации) + **RP2040** (PIO: 16 параллельных линий данных, GCLK, синхронизация слоёв) + 32 P-MOSFET **AOD4185** (40 В/40 А) для слоёв (ток слоя 10,24 А пик).
- Ток 10 мА пик, средний 0,31 мА на LED; обновление ~1,5 кГц (GCLK 25 МГц), 16-бит градации (S-PWM).
- Питание: 5 В, **Mean Well LRS-100-5 (18 А)**; LED всё-включено 51 Вт. Вариант 15 мА → LRS-150F-5.
- LED: **5 мм матовые (diffused) белые/одноцветные**, провод каркаса **0,8 мм лужёная медь** (~2,2 км, ~10 кг), ~67 600 паек → нужны кондукторы (jig).
- **Масштабирование** (48/64 LED в колонне, 48³, 64³): колонна делится на зоны по ≤32 LED, каждая зона со своими драйверами → скважность не хуже 1/32, яркость постоянна; растут только число плиток, ток БП и полоса данных. См. §9.
- Ориентировочная стоимость: электроника ≈ $300–350, LED+провод ≈ $600–900, рама ≈ $150–300 → **итого ≈ $1 100–1 500**.

---

## 1. Goal & constraints
| Item | Value |
|---|---|
| Voxels | 32×32×32 = 32 768, single colour |
| Size | ~1 m³, pitch 1000/32 = 31.25 mm |
| Controller | ONE main board (may contain several MCUs) + passive-ish modular driver tiles |
| Refresh | ≥ 960 Hz flicker-free (camera-safe preferred) |
| Hardware | real, orderable parts (LCSC/JLC first) |
| Baseline | v15 mono board (ESP32-S3, MBI5124, 74HC154 + AO3403, 1/32, 960 Hz) — copied to `hardware/v15_baseline/` |

## 2. Assumptions
| # | Assumption | Status |
|---|---|---|
| A1 | LED Vf ≈ 3.0–3.2 V @10 mA (white) ; Cj ≈ 30 pF | typical, verify on chosen LED |
| A2 | MBI5153 13-bit mode: 513 GCLK per scan line, GCLK ≤ 25–33 MHz | **verify against datasheet** before schematic |
| A3 | ICND2153 is drop-in second source (same SSOP-24 pinout) | pinout matches per datasheet; protocol near-identical — verify |
| A4 | 5 mm diffused LED ~1–3 cd @20 mA; 0.31 mA avg readable indoors at 1–3 m | to be tested with 1 column sample |
| A5 | Max cube current = all LEDs of 1 layer on (only one layer active at a time) | true by construction |

## 3. Multiplex scheme (calculated, `calc/cube_calc.py` → `calc/results.txt`)
| Scheme | Channels | 16-ch drivers | Duty | Avg/LED @10 mA pk | Peak scan current | Verdict |
|---|---|---|---|---|---|---|
| **1/32 per layer** | 1024 | 64 | 3.1 % | 0.31 mA | 10.2 A | **chosen** |
| 1/16 (2 layer groups) | 2048 | 128 | 6.25 % | 0.63 mA | 20.5 A | 2× brightness, 2× drivers & current, double tile wiring — fallback if A4 fails |
| 1/8 | 4096 | 256 | 12.5 % | 1.25 mA | 41 A | too many channels/cables |
| 1/32 @15 mA | 1024 | 64 | 3.1 % | 0.47 mA | 15.4 A | cheap brightness knob (Rext change + bigger PSU) — **recommended reserve** |

Brightness knob order: (1) raise Ipk to 15–20 mA (MBI5153 needs VDD = 5 V for >10 mA), (2) higher-efficiency LED, (3) only then 1/16.

## 4. Driver chip selection
| Chip | Feature | Scan | LCSC | Price (100+) | Verdict |
|---|---|---|---|---|---|
| MBI5124 (v15) | plain shift-reg CC sink, no PWM | MCU BCM | yes | ~$0.35 | MCU would need 252 Mbit/s → **rejected** |
| **MBI5153GP-A** | 16 ch, SRAM, S-PWM 16-bit, pre-charge anti-ghost, 1:32 | 1–32 | [C183654](https://www.lcsc.com/product-detail/LED-Drivers_MBI5153GP_C183654.html) ~1–2 k stock, marked *discontinued* | $0.24–0.36 | **chosen; buy 80 now** |
| ICND2153AP (Chipone) | same class, 16 KB SRAM, 3840 Hz, 0.5–25 mA, SSOP-24 | 1–32 | [JLC C6288664](https://jlcpcb.com/partdetail/ChiponeTech-ICND2153AP/C6288664) (stock 0 now) | ~$0.03–0.05 | second source / footprint compatible |
| MBI5253 | 1:32 S-PWM, newer | 1–32 | JLC ~$0.37 | | alternative |
| TLC5955 (TI) | 48 ch, 16-bit PWM, no scan SRAM | static | Digikey ~$3 | | static-drive only, expensive → rejected |

## 5. Physical partition: central vs distributed
| Option | Cables | Problems | Verdict |
|---|---|---|---|
| One central board with all 1024 channels | 1024 wires × ~1–1.5 m → 64 IDC ribbons | huge harness, crosstalk/ghosting, capacitance, assembly hell | rejected |
| **Central controller + 16 base tiles (drivers under columns)** | 16 data ribbons + 32 anode feeds | tiles 250×250 mm 2-layer; columns soldered direct | **chosen** |
| Driver boards on each layer edge (anode-side columns horizontal) | 32 boards, 32 ribbons up to 1 m | layer boards in view, more boards | alternative |

Tile (×16): 250×250 mm FR-4 2-layer 1.6 mm, 8×8 grid of plated holes Ø1.0 mm at 31.25 mm, 4× MBI5153 (2 lanes daisy-chained or 1 lane of 4 chips), Rext, 74AHCT245 input buffer, 2×8 IDC IN + OUT (pass-through GCLK/LE/power-sense), local 5 V 100 µF + 0.1 µF per chip. Tile ground = column current return → 2× M3 lug to ground bus bar.

Ghosting/parasitics: column node = 32 LEDs × 30 pF ≈ 1 nF → handled by MBI5153 pre-charge; layer node = 1024 × 30 pF ≈ 31 nF → 47 Ω active pull-down/ blanking ≥ 2 µs per line (τ = 1.4 µs). EMI: 10 A layer edges at 49 kHz line rate → gate resistor for ~0.5–1 µs slew, layer feed + ground return routed as pair along the same cube edge, twisted-pair (GND-signal) ribbon for 25 MHz-class GCLK, series 33 Ω source termination; ribbon ≤ 0.5 m.

## 6. MCUs & bandwidth
- Frame data: 32768 × 16 bit × 60 fps = **31.5 Mbit/s**; split in 16 lanes (one per tile) = **2 Mbit/s per lane** — trivial.
- **ESP32-S3-WROOM-1-N16R8**: content, Wi-Fi/BLE, SD/PSRAM frame buffer (64 kB/frame). Sends frames to RP2040 by QSPI/SPI 40 MHz.
- **RP2040** (LCSC C2040, ~$0.7): PIO SM0 — 16-bit parallel OUT (16 SIN lanes) + shared DCLK/LE; SM1 — continuous GCLK 25 MHz; SM2 — counts 513 GCLK and steps layer address (74HC154 ×2 → 32 gate drivers). Deterministic timing is the reason for RP2040; ESP32-S3-only (LCD_CAM i80 16-bit + LEDC + PCNT) is possible alternative, risk: row sync jitter.
- Alt: iCE40UP5K / Gowin GW1N FPGA — overkill, toolchain cost; keep as option for 64³.

## 7. Power, voltage drop, thermal (`calc/results.txt`)
- Layer peak current 1024 × 10 mA = **10.24 A**; LED all-on 51 W; logic ~9 W → **PSU 5 V ≥ 15 A: Mean Well LRS-100-5 (18 A)**; 15 mA option → LRS-150F-5 (30 A). Main fuse 20 A blade (ATO) + polyfuse per tile 1 A (tile logic only).
- Budget: Vf 3.1 + driver knee 0.5 + FET 0.10 (AOD4185 ~10 mΩ) + feed 0.14 (1.5 mm², 1.2 m, 2 feed points) + mesh 0.15 = 4.0 V → rail 4.5–5 V. Use LRS trim to **4.6 V** to cut driver dissipation (≈10 W total, 160 mW/chip — fine for SSOP-24).
- Layer FET: 32× **AOD4185** (P-ch, -40 V, -40 A, DPAK); gate driven by 74HC154 → NPN/ small N-FET level shifter to 5 V (v15 AO3403 3.3 V gate drive is inadequate at 10 A). Dissipation 10.24² × 0.012 Ω × 1/32 ≈ 40 mW avg each.
- Column wire 0.8 mm, 1.05 m: 36 mΩ → 0.36 mV @10 mA (irrelevant). Layer row wire carries ≤0.32 A → 5.5 mV.

## 8. Cables, connectors, LEDs, mechanics
| Link | Choice | Notes |
|---|---|---|
| Controller→tile data | 2×8 IDC 2.54 mm ribbon, box header (e.g. LCSC C3405-class 2x8 box header), alternating GND | 16 cables ≤0.5 m |
| Layer anode feeds | **Molex Micro-Fit 3.0 2×8 (43025-1600 housing / 43045-1600 header)**, 2 pins per layer, 18 AWG, 4 connectors | ≤5 A/pin at 18 AWG per pin pair OK for 10.24 A peak (31 mA-avg duty) |
| PSU→controller | Micro-Fit 2×2 or screw terminal 2×(2×1.5 mm²) | 20 A fuse |
| Tile ground return | 2.5 mm² bus to PSU − | |
| LED | 5 mm diffused white (or colour), wide angle, bulk ~$0.01–0.02 | 1 m viewing: SMD-on-wire (NCD0603W1 v15) rejected — 65k fragile joints, too small, no self-structure |
| Structure wire | 0.8 mm tinned Cu (columns straightened by stretching 1–2 %) | ~2.2 km, ~10 kg |

Mechanics: aluminium 2040 frame 1.1 m cube; columns **hang** from top comb or stand on base tiles with bottom alignment; recommended: base tiles carry columns, top acrylic/carbon comb holds column tops in tension (springs) → straightness. Each layer built flat on a jig (32 rows × 32 LEDs, anode legs to row wire), then threaded onto columns. Mass: LEDs 8 kg + wire 10 kg ≈ 18–20 kg.

## 9. Scalability (`calc/scaling.py` → `calc/scaling_results.txt`)
MBI5153 scans max 1:32, so a column taller than 32 LEDs is split into **zones** (electrically cut column segments), each zone with its own driver tile set (upper zone: tile ceiling on top or mid-height tiles). Zones scan in parallel → duty stays ≥ 1/32.

| Cube | LEDs | Scan | Zones | Channels | Drivers | Tiles | Avg mA | Refresh | PSU A | Mbit/s (16b, 60fps) |
|---|---|---|---|---|---|---|---|---|---|---|
| 32×32×32 | 32 768 | 1/32 | 1 | 1024 | 64 | 16 | 0.31 | 1523 | 12 | 31 |
| 32×32×48 | 49 152 | 1/24 | 2 | 2048 | 128 | 32 | 0.42 | 2031 | 23 | 47 |
| 32×32×64 | 65 536 | 1/32 | 2 | 2048 | 128 | 32 | 0.31 | 1523 | 23 | 63 |
| 48³ | 110 592 | 1/24 | 2 | 4608 | 288 | 72 | 0.42 | 2031 | 48 | 106 |
| 64³ | 262 144 | 1/32 | 2 | 8192 | 512 | 128 | 0.31 | 1523 | 84 | 252 |

Alternative without zones: 1/64 scan (not supported by MBI5153; needs MBI5124 + FPGA BCM) → half brightness — rejected.
Limits: per-layer current X·Y·10 mA (64×64 → 41 A → split each layer into 4 quadrant FETs); PSU (64³ → 2× LRS-350-5 parallel zones); data: 128 lanes → 2–4 RP2040 or one FPGA; mechanics: 2 m columns need intermediate combs. **Modular rule:** tile = 64 columns × 32 LEDs, ID by DIP/address, controller lanes = tile count, so the same tile PCB scales from 16³ to 64³.

## 10. BOM estimate (32³, qty 1 cube)
| Item | Qty | Unit | Total |
|---|---|---|---|
| MBI5153 (+spares) | 80 | $0.35 | $28 |
| Tile PCB 250×250 2L + assembly | 16 | ~$10 | $160 |
| Controller PCB + ESP32-S3 + RP2040 + 32 FETs | 1 | ~$60 | $60 |
| PSU LRS-100-5 | 1 | $20 | $20 |
| Cables/connectors (IDC, Micro-Fit, wire) | – | – | $50 |
| LEDs 5 mm (+5 %) | 34 500 | $0.015 | $520 |
| 0.8 mm tinned Cu | 2.3 km | – | $200–350 |
| Frame 2040 + combs | – | – | $150–300 |
| **Total** | | | **≈ $1 200–1 500** |

## 11. Risk register
| Risk | Sev | Lik | Mitigation |
|---|---|---|---|
| MBI5153 discontinued / low stock | H | M | buy 80 now; ICND2153 footprint-compatible second source |
| 0.31 mA avg too dim | M | M | build 1 test column; 15–20 mA Rext option; 1/16 fallback |
| MBI5153 protocol (GCLK/LE command timing) complexity | M | M | RP2040 PIO prototype on v15-sized test tile first |
| 67 k solder joints, assembly time 300–500 h | H | H | jigs, layer-at-a-time testing with tile tester |
| Layer 10 A switching EMI / ringing on 1 m feeds | M | M | slew control, paired returns, scope check |
| Column straightness / sag | M | M | tensioned columns, combs |

## 12. Open decisions
1. LED colour & exact part (test 3 samples for brightness at 0.3–0.5 mA avg).
2. Ipk 10 vs 15 mA (PSU LRS-100 vs LRS-150F).
3. RP2040 co-processor vs ESP32-S3-only firmware.
4. Columns standing on base vs hanging from top tiles.
5. Final cube height (32 vs 48/64 → 1 or 2 zones).

## 13. Next phase
Phase 2: schematics — (a) tile board (4× MBI5153, buffers, IDC in/out), (b) controller (ESP32-S3 + RP2040 + 32 layer FET drivers, power entry); then tile layout (250×250, 2-layer, smooth arc bends), plus a 1-tile + 1-column test rig before mass ordering.
