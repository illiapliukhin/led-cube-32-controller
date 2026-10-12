#!/bin/bash
# Fetch KiCad 3D models used by the boards into $KICAD10_3DMODEL_DIR (default /workspace/kicad3d).
# Parts with no upstream model get the closest upstream body under the referenced name (listed in docs/FOOTPRINTS.md).
D=${KICAD10_3DMODEL_DIR:-/workspace/kicad3d}; U=https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/master
declare -A SUB=(
 [Button_Switch_SMD.3dshapes/SW_Push_1P1T_XKB_TS-1187A.step]=Button_Switch_SMD.3dshapes/SW_Push_1P1T_NO_CK_KMR2.step
 [Connector_USB.3dshapes/USB_C_Receptacle_HRO_TYPE-C-31-M-12.step]=Connector_USB.3dshapes/USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal.step
 [Package_DFN_QFN.3dshapes/Texas_RNN0018A.step]=Package_DFN_QFN.3dshapes/Texas_RGE0024C_VQFN-24-1EP_4x4mm_P0.5mm_EP2.1x2.1mm.step
 [Fuse.3dshapes/Fuse_1812_4532Metric.step]=Inductor_SMD.3dshapes/L_1812_4532Metric.step )
cd "$(dirname "$0")/.."
for p in $(grep -ho '${KICAD10_3DMODEL_DIR}/[^"]*' hardware/main_v1/*.kicad_pcb hardware/branch_v1/*.kicad_pcb lib/cube.pretty/*.kicad_mod | sed 's/.*DIR}\///' | sort -u); do
  [ -s "$D/$p" ] && continue; mkdir -p "$D/$(dirname "$p")"; src=${SUB[$p]:-$p}
  curl -sfL -o "$D/$p" "$U/$src" || { echo "MISSING $p"; rm -f "$D/$p"; }
done
