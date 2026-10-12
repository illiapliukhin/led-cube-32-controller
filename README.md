# led-cube-32-controller
Controller system for 1–2 m³ RGB LED cubes built from hanging clocked-pixel strands (HD108, 16-bit, 27 kHz PWM).
- `ARCHITECTURE.md`: v2 architecture (RU summary + EN), with sizing for 32³…128³
- `calc/`: calculation scripts (`rgb_scaling.py`, plus v1 mono calcs)
- `hardware/main_v1`: main board (ESP32-S3 + 8 ports): schematic, PCB, fab
- `hardware/branch_v1`: branch board (16 strands): schematic
- `hardware/archive`: abandoned v1 mono tile (WIP, not DRC clean); `hardware/v15_baseline`: original mono board
- `docs/ARCHITECTURE_v1_mono.md`: phase-1 mono study (superseded)
