# 1 m strip board (supersedes the 250×100 mm branch_v1)

**Кратко (RU):** Ветка теперь — тонкая полоса длиной 1 м с разъёмами нитей вдоль неё. Четыре варианта: 124/64/48/32 разъёма на метр
(шаг 8.06/15.6/20.8/31.25 мм), один параметрический генератор (`hardware/strip_v1/strip_sch.py N`). JLCPCB делает голую 2-слойную плату
до 1020×600 мм, но монтаж (PCBA) — только до 470×500 мм, поэтому 1 м = 4 одинаковых сегмента по 250 мм, соединённых коротким
IDC-шлейфом 2×20 (шина пере-буферизуется в каждом сегменте). 12 В подаётся в каждую силовую ячейку отдельно (отвод от магистрали в кабеле).
Схемы всех четырёх вариантов: ERC 0. Трассировка полос — в работе (см. «Status»).

## Fab limits (JLCPCB, checked 2026-10-12)
| Item | Limit | Source |
|---|---|---|
| Bare 2-layer FR-4, 1.0–2.0 mm, 1–2 oz | 1020 × 600 mm (standard 670 × 600) | jlcpcb.com/help/article/pcb-dimensions |
| PCBA single board | Economic 470 × 500 mm, Standard 460 × 500 mm | jlcpcb.com/capabilities/pcb-assembly-capabilities |
| PCBA panel | ≤ 250 × 250 mm recommended | same |
| Note | large aspect ratio → manual audit; ENIG reported rejected on 1000×60 mm, HASL accepted | JLC Q&A #955 |

Decision: a 1 m board can be fabricated bare but **not assembled**, so the strip is **4 × 250 mm identical segments**. 250 mm also fits the
250 mm panel limit, the board stays in Economic PCBA, and one segment design serves every position on the strip. Strand pitch is continuous across
joints (first/last connector at pitch/2 from the segment edge). Segments are joined by a 2×20 IDC jumper (J2 → J1 of the next segment) and screwed
to a common aluminium U-channel. The bus is re-driven by 74AHCT245 in every segment, so four segments add only ~4 × 7 ns of skew.

## Variants (calc/strip_calc.py, HD108 60 mA/px full white, ABL 25 %)
| Connectors / 1 m | Pitch | Segments × conn. | px / strand | px / board | I5V ABL 25 % / board | I5V / segment | Power cells / segment | I12V / segment | I / strand (ABL) | Data buffers / seg | Clock buffers / seg | Clock groups / seg | Strand connector |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **124** | 8.06 mm | 4 × 31 | 124 | 15,376 | 231 A | 57.7 A | 6 | 26.6 A | 1.86 A | 4 | 4 | 2 | JST XH B4B-XH-A, 2 staggered rows (16.1 mm per row) |
| **64** | 15.62 mm | 4 × 16 | 64 | 4,096 | 61 A | 15.4 A | 2 | 7.1 A | 0.96 A | 2 | 2 | 1 | JST XH B4B-XH-A, 1 row |
| **48** | 20.83 mm | 4 × 12 | 48 | 2,304 | 35 A | 8.6 A | 1 | 4.0 A | 0.72 A | 2 | 2 | 1 | JST XH B4B-XH-A, 1 row |
| **32** | 31.25 mm | 4 × 8 | 32 | 1,024 | 15 A | 3.8 A | 1 | 1.8 A | 0.48 A | 1 | 1 | 1 | JST XH B4B-XH-A, 1 row |

* **Power injection:** 12 V is tapped from the trunk in the cable into each **power cell** (2-pin 5.08 mm terminal → SMBJ15A → TPS259474L eFuse
  with R_ILM 680 Ω = 4.9 A, UVLO 9.2 V, OVLO 15.8 V → TPS56C215 5.1 V/≤10 A → 4×47 µF). Each cell feeds its own strand domain `+5V_k`, so cells never run in parallel.
  Cells per segment: 32 → 1, 48 → 1, 64 → 2, 124 → 6 (4 / 4 / 8 / 24 bucks per 1 m board). The 12 V bus never runs along the PCB, so copper is sized
  only for one cell (≤ 4.9 A at 12 V and ≤ 10 A at 5 V over ≤ 60 mm).
* **Outputs per driver:** one 74AHCT245 drives 8 data lines and one drives 8 clocks (2 per 8 strands). Clock gating uses one 74HC688PW + 1G32 per 16-strand group
  (124 variant: 2 groups → 2 board IDs per segment). A 16-bit main-board lane maps to the strand index modulo 16.
* **8.06 mm pitch connector:** JST XH B4B-XH-A (C144395, 3 A, body 9.9 mm) does not fit 8.06 mm in one row, so it is placed in **two staggered rows**
  (16.1 mm pitch per row). JST SH/GH fit one row but are rated ≤ 1 A, and the 124-variant strand draws 1.86 A at ABL 25 % (7.4 A at full white). Rejected.
* **Status:** schematics for all four variants generated, ERC 0. PCB generator, gates and fab outputs for the strips: **not done yet.** branch_v1 is kept as a reference only.
