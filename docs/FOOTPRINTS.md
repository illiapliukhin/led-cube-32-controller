# Footprint and 3D-model verification
**Кратко (RU):** собственные футпринты нарисованы по даташитам; стандартные модели KiCad скачиваются `tools/fetch3d.sh`; где модели нет — ближайший корпус (таблица).

| Footprint (lib cube) | Datasheet | Land pattern | 3D model |
|---|---|---|---|
| TI_RPW0010A_VQFN-HR-10_2x2mm_P0.45mm (TPS25947) | TI 4225183/A | side pads 0.6×0.25/0.3 @ x ±0.9, corner L-legs, pins 5/6 bars 0.3×2.2 | Texas_DSQ0010A WSON-10 2×2 (body approximation) |
| L_YJYCOIN_YSPI1365 | YJYCOIN YSPI1365 | pads 4.0×5.0 @ ±5.25 (F 14.5, G 5.0, H 6.5); stock TaiTech footprint did NOT match | L_Changjiang_FXL1365 (same 13.5×12.5 body) |
| L_Cjiang_FXL0630 | Changjiang FXL0630 | pads 2.35×3.5 @ ±3.025 (a 3.7, b 8.4, c 3.5); stock SRP7028A did NOT match | L_Changjiang_FXL0630 (exact) |

Stock footprints without an upstream model use a substitute body of the same outline:
TS-1187A switch → CK KMR2, HRO TYPE-C-31-M-12 → GCT USB4105, Fuse 1812 → L_1812_4532Metric, TI RNN0018A → TI RGE0024C body.
Models live in `$KICAD10_3DMODEL_DIR` (default /workspace/kicad3d). They are not committed; `tools/fab.sh` fetches them.
