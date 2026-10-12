#!/bin/bash
# full regeneration: structured routing + corner A* + repair passes + fill + DRC
set -e; cd "$(dirname "$0")"; R=$(readlink -f ../..); PCB=$PWD/main_v1.kicad_pcb
$R/kpy.sh $PWD/main_gen.py
$R/kpy.sh $R/tools/repair.py $PCB 0 0 54 130 0.3
$R/kpy.sh $R/tools/ripnets.py $PCB USB_DN,USB_DP,VBUS,CC2,CC1 54
$R/kpy.sh $R/tools/repair.py $PCB 0 0 54 130 0.2
bash $R/tools/drc.sh $PCB
