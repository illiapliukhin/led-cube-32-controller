#!/bin/bash
# full regeneration: placement + structured routing + A* + schematic link + repair passes + fill + DRC
set -e; cd "$(dirname "$0")"; R=$(readlink -f ../..); PCB=$PWD/branch_v1.kicad_pcb
$R/kpy.sh $PWD/branch_gen.py
$R/kpy.sh $R/tools/sch2pcb.py $PCB $PWD/branch_v1.kicad_sch
$R/kpy.sh $R/tools/repair.py $PCB 0 0 221.5 100 0.2
$R/kpy.sh $R/tools/repair.py $PCB 221.5 0 250 70 0.2 0.15
$R/kpy.sh $R/tools/repair.py $PCB 0 0 250 100 0.2 0.15 --gnd
bash $R/tools/drc.sh $PCB
