#!/bin/bash
# fab outputs + 3D renders for one board: tools/fab.sh path/to/board.kicad_pcb
set -e; R=$(readlink -f "$(dirname "$0")/.."); PCB=$(readlink -f "$1"); D=$(dirname "$PCB"); N=$(basename "$PCB" .kicad_pcb)
KC="/workspace/.kicad10/AppDir/AppRun kicad-cli"; export KICAD10_3DMODEL_DIR=${KICAD10_3DMODEL_DIR:-/workspace/kicad3d}
"$R/tools/fetch3d.sh" >/dev/null 2>&1 || true
"$R/kpy.sh" -c "import pcbnew,sys;b=pcbnew.LoadBoard(sys.argv[1]);pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.Save(sys.argv[1])" "$PCB"   # lesson: refill before plot
F=$D/fab; rm -rf "$F"; mkdir -p "$F" "$D/renders"
$KC pcb export gerbers --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts -o "$F/" "$PCB" >/dev/null
$KC pcb export drill --format excellon --excellon-separate-th -o "$F/" "$PCB" >/dev/null
$KC pcb export pos --format csv --units mm --exclude-dnp -o "$F/$N-pos.csv" "$PCB" >/dev/null
"$R/kpy.sh" "$R/tools/bom.py" "$PCB" "$F/$N-BOM.csv"
(cd "$F" && python3 -c "import zipfile,glob,sys;z=zipfile.ZipFile(sys.argv[1],'w',zipfile.ZIP_DEFLATED);[z.write(f) for f in sorted(glob.glob('*.g*')+glob.glob('*.drl'))]" "${N}_gerbers.zip")
for s in top bottom; do $KC pcb render --side $s --quality high -w 2400 -h 1400 -o "$D/renders/${N}_$s.png" "$PCB" >/dev/null; done
$KC pcb render --rotate '-45,0,30' --quality high -w 2400 -h 1400 -o "$D/renders/${N}_iso.png" "$PCB" >/dev/null
echo "fab ok: $F"
