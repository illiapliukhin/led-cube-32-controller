#!/bin/bash
# usage: drc.sh board.kicad_pcb  -> prints summary
P=$(readlink -f $1); D=$(dirname $P)
/workspace/.kicad10/AppDir/tools_fill(){ :; }
/workspace/led-cube-32-controller/kpy.sh /workspace/led-cube-32-controller/tools/fill_drc.py $P >/dev/null 2>&1
/workspace/.kicad10/AppDir/bin/kicad-cli pcb drc --format json --severity-all --schematic-parity -o $D/drc.json $P >/dev/null 2>&1 || /workspace/.kicad10/AppDir/bin/kicad-cli pcb drc --format json --severity-all -o $D/drc.json $P >/dev/null 2>&1
python3 - $D/drc.json <<'PY'
import json,sys,collections
d=json.load(open(sys.argv[1]))
c=collections.Counter((v['severity'],v['type']) for v in d['violations'])
print('violations',sum(c.values()),dict(c)); print('unconnected',len(d.get('unconnected_items',[])))
print('parity',len(d.get('schematic_parity',[])))
PY
