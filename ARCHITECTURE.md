# LED Cube Controller — Architecture v2 (RGB, hanging strands)

## Кратко (RU)
**Вердикт: PASS WITH RISKS (архитектура + схемы; разводка главной платы — см. отчёт DRC в `hardware/main_v1`).**

**Рекомендация:** адресные **тактируемые RGB-пиксели HD108** (16 бит/канал, внутренний ШИМ 27 кГц, SPI до 40 МГц) на **висящих нитях** (pixel string / лента 32 LED/м). Мультиплексирование не нужно → нет мерцания на камеру, нет ghosting, «почти идеальная» картинка.
- **Топология:** 1 главная плата (ESP32-S3) → 8 портов IDC 2×20 → в каждом порту цепочка из 8 **ветвевых плат** (регенерация шины) → каждая ветвевая плата держит **16 нитей**. Итого 1 главная плата = 64 ветви = **1024 нити**.
- **Трюк:** ESP32-S3 LCD_CAM выдаёт 16-битную параллельную шину + общий CLK. HD108 сдвигает данные только по фронтам CLK, поэтому ветвь выбирается **гейтированием CLK** (компаратор адреса 74HC688 + 74AHC1G32 на ветви). Одна DMA-передача = 16 нитей одновременно.
- **1 м³:** 32³ = 32 768 RGB, шаг 31,25 мм, **~96 fps** с одной главной платой, 16 бит цвета, 27 кГц ШИМ. Премиум: 48³ (20,8 мм, 110 592 LED, 3 главные платы, ~65 fps).
- **2 м³:** 64³ = 262 144 RGB, шаг 31,25 мм, 4 главные платы с синхронизацией кадра (SYNC), ~49 fps. 96³/128³ — только как исследовательский вариант (стоимость/мощность/вес).
- **Мощность (32³):** абсолютный максимум белого 1966 А при 5 В (9,8 кВт) — нереально и не нужно. Ограничитель яркости (ABL) 25 % → ≤ 492 А, типичная сцена 3D-объекта (APL ≈ 15 %) ≈ 295 А / 1,5 кВт. Питание: **9× Mean Well LRS-350-5 (60 А)**, по 1 БП на ~7 ветвей, инжекция на каждой ветви (2 клеммы), нити 4-жильные 22 AWG (1 м) / 20 AWG (2 м).
- **Стоимость LED (32³):** ≈ $5,9–11,5 тыс. (HD108/SK9822 нити $0,18–0,35/пиксель); электроника ≈ $400–600; БП ≈ $350.
- **Вес (32³):** ≈ 60 кг висящей массы → верхняя рама из профиля 4040, нити с грузиками/нижней сеткой-растяжкой.

## 1. Resolution / size options (`calc/rgb_scaling.py` → `calc/rgb_scaling_results.txt`)
| Size | N/axis | Pitch | LEDs | Strands | Branch boards (16 str) | Main boards | fps (16-bit) | I max (A) | I ABL 25% | I avg (APL 15%) | LRS-350-5 | Mass kg | LED cost $ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 m | **32** | 31.2 mm | 32 768 | 1 024 | 64 | **1** | 96 | 1 966 | 492 | 295 | 9 | 60 | 5.9k–11.5k |
| 1 m | 48 | 20.8 mm | 110 592 | 2 304 | 144 | 3 | 65 | 6 636 | 1 659 | 995 | 28 | 179 | 20k–39k |
| 1 m | 64 | 15.6 mm | 262 144 | 4 096 | 256 | 4 | 49 | 15 729 | 3 932 | 2 359 | 66 | 396 | 47k–92k |
| 2 m | **64** | 31.2 mm | 262 144 | 4 096 | 256 | 4 | 49 | 15 729 | 3 932 | 2 359 | 66 | 478 | 47k–92k |
| 2 m | 96 | 20.8 mm | 884 736 | 9 216 | 576 | 9 | 33 | 53 084 | 13 271 | 7 963 | 222 | 1 430 | 159k–310k |
| 2 m | 128 | 15.6 mm | 2.1 M | 16 384 | 1 024 | 16 | 25 | 125 829 | 31 457 | 18 874 | 525 | 3 172 | 377k–734k |

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

## 4. Power distribution (32³)
- Firmware ABL: total current ≤ 25 % of max = 492 A (2.46 kW). Typical 3D-object scenes (APL 10–15 %) draw 200–300 A.
- 9× LRS-350-5 (60 A each, ~$35): each PSU feeds 7–8 branch boards via 2× 14 AWG pairs. Each branch board takes ≤ 7.7 A at ABL on 2 terminal blocks. The main board is powered separately (5 V/2 A plus USB).
- Strand: 32 nodes, 1 m, 4-core 22 AWG. At ABL, 0.48 A → 0.03 V drop. Full white without ABL would be 1.92 A → 0.10 V.
- Protection: one 10 A blade fuse per branch-board feed; 60 A per PSU output bus; PSU OVP built in.
- Heat: ≤ 2.5 kW (ABL) spread over 1 m³ of thin strands, which free air convection handles. PSUs go in a separate ventilated rack.

## 5. Boards
**Main board v1** (`hardware/main_v1`, 300×130 mm, 2-layer):
- ESP32-S3-WROOM-1-N16R8 (C2913202), USB-C (C165948) for programming, AMS1117-3.3 (C6186), SS34 OR-ing (C8678), 5 V terminal (C8465).
- 24× 74LVC245APW (C6082) line drivers, 3 per port: D0–7, D8–15, CLK+A0–A5.
- 8× IDC 2×20 box headers (C9138), with buffer OE gated by firmware (OE_N pulled up).
- Port pinout: odd 1–31 = D0..D15, 33 = CLK, 35/37/39 = A0–A2, 4/8/12 = A3–A5, all other pins GND.

**Branch board v1** (`hardware/branch_v1`, schematic; proposed 495×30 mm strip lying on the top frame, strands hang at 31.25 mm pitch):
- 3× 74AHCT245 (C173388) regenerate the bus to the OUT port (daisy chain).
- 74HC688 (C88042) address compare against 6 solder-jumper ID bits; 74AHC1G32 (C7470) clock gate.
- 2× 74AHCT245 data drivers + 2× 74AHCT245 clock fan-out, each output through 33 Ω (C23140).
- 16× JST XH 4-pin strand plugs (C144395): +5V, DATA, CLK, GND.
- 2× injection terminals, plus bulk and decoupling caps.

## 6. Cables & connectors
| Link | Part | Notes |
|---|---|---|
| Main → branch chain | 40-way 1.27 mm flat ribbon, IDC 2×20 sockets | ≤ 1 m per hop, every 2nd conductor GND (except A3–A5 pairs) |
| Strand | 4-core 22 AWG (1 m) / 20 AWG (2 m), JST XH-4 plug at the top | data/clock twisted with GND if custom |
| Power | 14 AWG pairs PSU → branch, 10 A fuse | |

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
