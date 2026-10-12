# LED Cube Controller — Architecture v2 (RGB, hanging strands)

> **2026-10-12:** the branch board is now a 1 m strip of 4 × 250 mm segments in 4 variants (124/64/48/32 connectors per m). See docs/STRIP_BOARD.md. Main board v1.1 adds TPD4E05U06 ESD on all 8 ribbon ports, schematic→PCB parity 0. Footprints: docs/FOOTPRINTS.md.

## Кратко (RU)
**Вердикт: PASS WITH RISKS (архитектура + схемы; разводка главной платы — см. отчёт DRC в `hardware/main_v1`).**

**Рекомендация:** адресные **тактируемые RGB-пиксели HD108** (16 бит/канал, внутренний ШИМ 27 кГц, SPI до 40 МГц) на **висящих нитях** (pixel string / лента 32 LED/м). Мультиплексирование не нужно → нет мерцания на камеру, нет ghosting, «почти идеальная» картинка.
- **Топология:** 1 главная плата (ESP32-S3) → 8 портов IDC 2×20 → в каждом порту цепочка из 8 **ветвевых плат** (регенерация шины) → каждая ветвевая плата держит **16 нитей**. Итого 1 главная плата = 64 ветви = **1024 нити**.
- **Трюк:** ESP32-S3 LCD_CAM выдаёт 16-битную параллельную шину + общий CLK. HD108 сдвигает данные только по фронтам CLK, поэтому ветвь выбирается **гейтированием CLK** (компаратор адреса 74HC688 + 74AHC1G32 на ветви). Одна DMA-передача = 16 нитей одновременно.
- **1 м³:** 32³ = 32 768 RGB, шаг 31,25 мм, **~96 fps** с одной главной платой, 16 бит цвета, 27 кГц ШИМ. Премиум: 48³ (20,8 мм, 110 592 LED, 3 главные платы, ~65 fps).
- **2 м³:** 64³ = 262 144 RGB, шаг 31,25 мм, 4 главные платы с синхронизацией кадра (SYNC), ~49 fps. 96³/128³ — только как исследовательский вариант (стоимость/мощность/вес).
- **Мощность (32³):** абсолютный максимум белого 1966 А при 5 В (9,8 кВт) — нереально и не нужно. Ограничитель яркости (ABL) 25 % → ≤ 2,46 кВт, типичная сцена 3D-объекта (APL ≈ 15 %) ≈ 1,5 кВт. **Распределение поднято до 12 В** (v1.1): 5× Mean Well LRS-600-12 (50 А) → шина 12 В → на каждой ветви eFuse TPS259474L (защита от переполюсовки, лимит 4,46 А) + синхронный buck TPS56C215 12 В→5 В 12 А (локальная инжекция). Ток по кабелю ветви 3,5 А вместо 7,7 А (в 2,2 раза меньше), падение на 2 м кабеля 1 мм² 0,24 В вместо 0,53 В, и оно не влияет на 5 В пикселей. Каждая нить через PTC 2 А + ESD (USBLC6-2SC6) на разъёме.
- **Стоимость LED (32³):** ≈ $5,9–11,5 тыс. (HD108/SK9822 нити $0,18–0,35/пиксель); электроника ≈ $400–600; БП ≈ $350.
- **Вес (32³):** ≈ 60 кг висящей массы → верхняя рама из профиля 4040, нити с грузиками/нижней сеткой-растяжкой.

## 1. Resolution per size (`calc/size_table.py` → `calc/size_table.md`, v1.1: HD108 + 12 V bus)
**Chosen pixel: HD108** (5050 RGB, 2-wire DATA+CLK, 16 bit per colour + 5-bit current gain per colour, 27 kHz internal PWM, ≤ 40 MHz clock, 5 V).
Why:
- (1) 16-bit colour removes banding in dark gradients, so shaded 3D objects look smooth.
- (2) 27 kHz PWM means no flicker by eye or on camera.
- (3) It is clocked, so a branch is selected by **gating CLK**, and one ESP32-S3 can drive 1024 strands on one 16-bit bus. Single-wire WS281x would need 1024 independent timed outputs.
- (4) It is commercially available with a JST-SM 4-pin plug. Reference price: [superlightingled HD108 60 LED/m, 5 m, $65.98 ≈ $0.22/px](https://www.superlightingled.com/hd108-ic-individually-addressable-led-rgb-full-color-changing-digital-flexible-dc5v-led-strip-lights-p-4522.html) and [144 LED/m 1 m $30.98 ≈ $0.22/px](https://www.superlightingled.com/individually-addressable-dc5v-hd108-pixel-led-rgb-color-changing-led-strip-lights-p-4523.html). A custom 31.25 mm-pitch string is estimated at ≤ $0.35/px (quote pending).

Fallback: HD107S (same protocol, 8-bit). Rejected: WS2812B/WS2815 (8-bit, 0.4–2 kHz PWM, no clock gating).

Assumptions:
- Data: 64 bit/pixel, 16 lanes × 13.3 MHz = 213 Mbit/s per main board.
- Power: 60 mA/pixel full white at 5 V. Typical = APL 15 %, ABL cap 25 %. Supplied by Mean Well LRS-600-12 at 90 % load and 92 % buck efficiency.
- Costs: main board $45, branch board $14, PSU $95.
- Weight = pixels + 4-core 22 AWG strands + top frame.

| Size | LEDs/axis | Pitch | LEDs | Strands (outputs) | Branch boards | Main boards / ribbon ports | Data rate | fps (16-bit) | Power typ (APL 15 %) | ABL 25 % cap | Abs. max | 12 V PSUs (LRS-600-12) | LED cost | Electronics+PSU | Weight |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 m³ | **32** | 31.2 mm | 32,768 | 1,024 | 64 | 1 / 8 | 213 Mbit/s | 101 | 1.5 kW | 2.5 kW | 9.8 kW | 5 | $7.2k–11.5k | $1.4k | 119 kg |
| 1 m³ | **48** | 20.8 mm | 110,592 | 2,304 | 144 | 3 / 24 | 638 Mbit/s | 90 | 5.0 kW | 8.3 kW | 33.2 kW | 17 | $24.3k–38.7k | $3.8k | 261 kg |
| 1 m³ | **64** | 15.6 mm | 262,144 | 4,096 | 256 | 4 / 32 | 851 Mbit/s | 51 | 11.8 kW | 19.7 kW | 78.6 kW | 40 | $57.7k–91.8k | $7.6k | 512 kg |
| 2 m³ | **64** | 31.2 mm | 262,144 | 4,096 | 256 | 4 / 32 | 851 Mbit/s | 51 | 11.8 kW | 19.7 kW | 78.6 kW | 40 | $57.7k–91.8k | $7.6k | 790 kg |
| 2 m³ | **96** | 20.8 mm | 884,736 | 9,216 | 576 | 9 / 72 | 1915 Mbit/s | 34 | 39.8 kW | 66.4 kW | 265.4 kW | 134 | $194.6k–309.7k | $21.2k | 1931 kg |
| 2 m³ | **128** | 15.6 mm | 2,097,152 | 16,384 | 1024 | 16 / 128 | 3405 Mbit/s | 25 | 94.4 kW | 157.3 kW | 629.1 kW | 317 | $461.4k–734.0k | $45.2k | 3938 kg |

**Recommended per size (for convincing real 3D objects):**
- **1 m³ → 32³ (baseline), 48³ (premium).** 32 voxels per axis is enough for recognisable solid objects (a head or a car is about 20–25 voxels), and 16-bit colour gives smooth shading. 48³ noticeably improves the silhouettes, but costs 3.4× the LEDs and power.
- **2 m³ → 64³ at 31 mm pitch.** The viewing distance is larger (3–5 m), so the angular resolution is the same as a 1 m 32³ cube viewed from 1.5–2.5 m. 96³ and up would need megawatt-class-avoidance ABL, a tonne-level structure and $150k+ of LEDs, which is not realistic.
- Inner-voxel visibility (transparency): pixel *strings* (nodes on wires) are better than strips. For strips, use 5–10 mm wide 32 LED/m strips mounted edge-on to the main viewing direction.

## 2. Pixel technology choice
| Option | Colour bits | PWM refresh | Interface | Strand drive | Verdict |
|---|---|---|---|---|---|
| **HD108** | 16 per colour + 5-bit gain/colour | 27 kHz | DATA+CLK, ≤40 MHz | clock-gated parallel bus | **chosen** |
| HD107S / APA102 | 8 + 5-bit global | 20–27 kHz | DATA+CLK, ≤40 MHz | same | fallback (cheaper, 8-bit banding in dark gradients) |
| SK9822 | 8 + 5-bit | 4.7 kHz | DATA+CLK, ~15 MHz | same, lower PCLK | fallback, camera-visible at high shutter |
| WS2812B / SK6812 | 8 | 0.4–1.2 kHz | 800 kbps single wire | needs 1024 independent outputs | rejected (flicker on camera, no clock gating → many MCUs) |
| WS2815 (12 V) | 8 | ~2 kHz | 800 kbps + backup | same | rejected for same reason; nice 12 V wiring though |
| Multiplexed RGB matrix (3×1024 sinks, 1/32) | 13–14 | 1.4 kHz | MBI5153 ×192 | wiring nightmare with hanging RGB | rejected (see v1 doc) |

Market references (prices are indicative, Oct 2026):
- HD108 5050 strip 16-bit/27 kHz, 30–144 LED/m, custom length, JST-SM 4-pin: [Rose Lighting](https://www.rose-lighting.com/products/fastest-16bit-hd108ledstrip/); protocol summary: [ENTTEC HD108](https://www.enttec.com/pixel-protocols/HD108)
- SK9822 strip 30/32/36… LED/m (32/m = exactly 31.25 mm pitch), $4.98–30 per m: [BTF-LIGHTING](https://www.btf-lighting.com/products/1-sk9822-led-pixel-strip-data-and-clock-dc5v)
- 12 mm bullet pixel strings 5 V (custom IC/pitch from factories, MOQ quote): [example](https://www.ledpixellight.com/sale-6564065-bullet-type-12mm-led-pixel-f8-dc05v-rgb-full-color-led-pxiel-string-light.html)
- **Open item:** a factory quote for an "HD108 pixel string, 32 nodes, 31.25 mm pitch, 4-core 22 AWG, XH-4 plug" (1 100 pcs).

## 3. Data path & timing
- Per strand: N × 64 bit + start (64) + end (≥ N/2) ≈ 2 128 clocks for N = 32.
- Bus: ESP32-S3 LCD_CAM i80 16-bit, PCLK 13.3 MHz (conservative: ribbon + 8-deep 74AHCT regen chain; duty-cycle distortion ≤ 8×1.5 ns).
- One frame = 64 branches × 2 128 clocks = 136 k clocks → 10.2 ms → **96 fps**. PSRAM DMA = 2 B × 13.3 MHz = 26.6 MB/s (within S3 octal PSRAM capability). Double frame buffer = 2 × 272 kB.
- Branch select: 6 address lines (static during a branch burst) → 74HC688 vs solder-jumper ID → `CLK OR SEL_N` (74AHC1G32). Unselected branches see CLK stuck high, so they shift nothing.
- Flicker: none (HD108 internal 27 kHz PWM, independent of fps). Colour: 16-bit + 5-bit per-channel current gain → gamma 2.4 without banding.
- Multi-board (2 m³): each main board drives ≤ 64 branches. A shared SYNC line (opto/RS-485 pair on a spare port pin) latches all boards' frame start; content is distributed over Wi-Fi/Ethernet (W5500 option) as voxel slabs.

## 4. Power distribution (32³), v1.1: 12 V bus with local buck per branch
Why 12 V: the HD108 runs at 5 V. Distributing 5 V across 1 m³ means 492 A (ABL) through long cables, and the drop lands on the pixels. A 12 V bus with point-of-load bucks keeps the cables thin and the pixel rail regulated.

| Bus | Total @ABL 25 % | Per branch (64) | Drop, 2 m of 1.0 mm² pair | Comment |
|---|---|---|---|---|
| 5 V direct | 492 A | 7.68 A | 0.53 V (10.6 %!) | v1 plan; drop shows on the pixels |
| **12 V + local buck (chosen)** | 223 A | 3.48 A | 0.24 V (2 %, absorbed by buck) | TPS56C215 (VIN ≤ 17 V) |
| 24 V + local buck | 111 A | 1.74 A | 0.12 V | needs a 36–60 V buck (e.g. LM5145 controller + FETs); kept as option for 2 m³ |

WS2815 (12 V pixels) was rejected. It is single-wire 800 kHz with 8-bit colour and 2 kHz PWM, which breaks the 16-bit, flicker-free, high-fps goal. The 12 V gain is better had from a local buck.

- PSUs: 5× Mean Well **LRS-600-12** (12 V/50 A) for 32³ at ABL. Each PSU feeds ~13 branch boards through a daisy-chained 12 V bus (2× terminal per branch, in/out, 1.5 mm² trunk, 1.0 mm² drops). Main board takes 12 V from the same bus (≤ 0.4 A).
- **Branch board power chain** (schematic `hardware/branch_v1`): J30/J31 12 V → SMBJ15A TVS (C83846) → **TPS259474LRPWR eFuse** (C2864845: reverse-polarity, OV/UV lockout (9.2 V / 15.8 V dividers), current limit R_ILM = 750 Ω → 4.46 A, dV/dt soft-start 10 nF) → **TPS56C215RNNR** (C473372) 12 A sync buck, 800 kHz FCCM (MODE 120k/20k), V_OUT = 0.6·(1+75k/10k) = 5.1 V, L = 1.5 µH/20 A YSPI1365-1R5M (C5158939), 6× 47 µF 1210 out, 4× 10 µF/50 V in → +5V → **per-strand PTC 2 A hold (C20812)** → JST XH-4.
  - Buck sizing: 512 px × 60 mA × ABL 0.25 = 7.7 A (64 % of 12 A). Firmware ABL is the primary limiter; the eFuse is the hard backstop (4.46 A × 12 V ≈ 49 W in).
  - Ripple: ΔI_L = (12−5.1)·5.1/(12·0.8 MHz·1.5 µH) = 2.4 A p-p (31 % of 7.7 A).
- Strand: 32 nodes, 1 m, 4-core 22 AWG. At ABL, 0.48 A → 0.03 V drop. A local full-white burst of 1.92 A is still under the 2 A PTC hold.
- **Main board power** (`hardware/main_v1`): 12 V terminal → PTC 2 A (C20812) → SS34 series reverse-polarity diode (C8678) → SMBJ15A TVS → AP63203WU-7 3.3 V/2 A buck (C780769, 3.8–32 V in). USB-C VBUS joins through an SS34 OR diode, with USBLC6-2SC6 ESD on D+/D−/VBUS. Buck instead of the v1 AMS1117: 24× LVC245 driving ribbons ≈ 0.85 A at 3.3 V, and an LDO from 5 V would burn 2 W.
- Heat: ≤ 2.5 kW (ABL) is spread over 1 m³ of thin strands, so free convection handles it. Per-branch buck loss ≈ 3 W (92 %), spread over a 495 mm strip. PSUs sit in a ventilated rack.

## 5. Boards
**Main board v1.1** (`hardware/main_v1`, 300×130 mm, 2-layer 1.6 mm FR-4, 1 oz; **DRC 0 errors / 0 unconnected, ERC 0**):
- ESP32-S3-WROOM-1-N16R8 (C2913202), USB-C (C165948) + USBLC6-2SC6 ESD, 12 V input chain (see §4), AP63203 buck 3.3 V.
- 24× 74LVC245APW (C6082) line drivers, 3 per port: D0–7, D8–15, CLK+A0–A5. Each has its own 100 nF at the VCC pin.
- 8× IDC 2×20 box headers (C9138). Buffer OE_N is pulled up (outputs Hi-Z at boot).
- **Port pinout (v1.1):** odd 1–31 = D0..D15, 33 = CLK, 35/37/39 = A0–A2, **34/36/38 = A3–A5**, all other pins GND. Branch schematic was updated to match.
- Layout: 23 bus lines run as a B.Cu "spine" (1.0 mm pitch) between the two port rows. Each buffer drops straight to its line with a via, and the outputs fan out to the header in a non-crossing staircase. Every corner is an arc fillet. Details: `docs/LAYOUT_LESSONS.md`.

**Branch board v1** (`hardware/branch_v1`, schematic; proposed 495×30 mm strip lying on the top frame, strands hang at 31.25 mm pitch):
- 3× 74AHCT245 (C173388) regenerate the bus to the OUT port (daisy chain).
- 74HC688 (C88042) address compare against 6 solder-jumper ID bits; 74AHC1G32 (C7470) clock gate.
- 2× 74AHCT245 data drivers + 2× 74AHCT245 clock fan-out, each output through 33 Ω (C23140).
- 16× JST XH 4-pin strand plugs (C144395): +5V, DATA, CLK, GND.
- 12 V in/out terminals, TVS, eFuse, 12 A buck, PTC + ESD per strand (§4).

## 6. Cables & connectors
| Link | Part | Notes |
|---|---|---|
| Main → branch chain | 40-way 1.27 mm flat ribbon, IDC 2×20 sockets | ≤ 1 m per hop, every 2nd conductor GND (except A3–A5 pairs) |
| Strand | 4-core 22 AWG (1 m) / 20 AWG (2 m), JST XH-4 plug at the top | data/clock twisted with GND if custom |
| Power | 12 V trunk 1.5 mm² (16 AWG) daisy-chain, 1.0 mm² (18 AWG) drops; 5 A blade fuse per drop; eFuse on board | 3.5 A per branch at ABL |

## 7. Risks
| Risk | Sev | Mitigation |
|---|---|---|
| HD108 pixel string at exact 31.25 mm pitch not off-the-shelf | H | 32 LED/m strips (BTF/Rose) or factory custom quote; fallback HD107S |
| Bus SI at 13 MHz over 8 ribbon hops | M | 74AHCT regen per hop, 33 Ω series on strand outputs; lower PCLK if needed (fps scales linearly) |
| ESP32-S3 PSRAM DMA bandwidth + CPU frame packing | M | 16×16 bit-transpose in IRAM; option ESP32-P4 / FPGA for 48³+ |
| Power/thermal at 2 m scale | H | ABL mandatory; PSU per zone; content tuned for dark volume |
| Mechanical: 60 kg (1 m) / 480 kg (2 m) hanging mass | H | 4040 frame, ceiling anchors, structural review |
| ID jumpers mis-set (two branches answering) | L | boot-time self-test via LED pattern |

## 8. Next steps
1. Get a factory quote for HD108 strings, and order 2 sample strands + 1 strip.
2. Bring-up with 1 main board + 1 branch board (16 strands, 512 px).
3. Branch board layout (495×30 mm).
4. Firmware: LCD_CAM DMA + bit-transpose + ABL + Wi-Fi voxel stream.
