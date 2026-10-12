#!/usr/bin/env python3
"""Main board schematic generated from the same netlist as main_gen.py (single source of truth: the PCB generator).
BOOTSTRAP ONLY. The committed main_v1.kicad_sch is the source of truth; build.sh links the PCB to it with
tools/sch2pcb.py and aborts on any value/footprint/net mismatch. Re-run this only after an intentional
netlist change in main_gen.py:  ../../kpy.sh $PWD/main_sch.py --bootstrap"""
import sys,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(HERE,'../../tools'))
import pcbnew
if '--bootstrap' not in sys.argv: sys.exit('refusing: schematic is the source of truth (use --bootstrap)')
from schgen import write
b=pcbnew.LoadBoard(os.path.join(HERE,'main_v1.kicad_pcb'))
import glob
FPL='/workspace/.kicad10/AppDir/share/kicad/footprints/'
IDX={os.path.basename(p)[:-10]:os.path.basename(os.path.dirname(p))[:-7] for p in glob.glob(FPL+'*.pretty/*.kicad_mod')}
C=[]
for f in sorted(b.GetFootprints(),key=lambda f:f.GetReference()):
    ref=f.GetReference()
    if f.IsBoardOnly(): continue
    pins={}
    for p in f.Pads():
        n=p.GetNumber()
        if not n or n in pins: continue
        pins[n]=p.GetNetname() or ''
    fp=str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName())
    fl={k:f.GetFieldText(k) for k in ('LCSC','MPN') if f.HasField(k)} if hasattr(f,'HasField') else {}
    C.append(dict(ref=ref,value=f.GetValue(),footprint=fp,fields=fl,pins=[(n,n,net if net else None) for n,net in sorted(pins.items(),key=lambda t:(len(t[0]),t[0]))]))
n=write(os.path.join(HERE,'main_v1.kicad_sch'),C,'Main board v1.1 - ESP32-S3, 8 ports x 23-bit bus, 12 V in','main_v1')
ft=os.path.join(HERE,'fp-lib-table'); t=open(ft).read().rstrip().rstrip(')')
for l in ('Fiducial','MountingHole'):
    if '"%s"'%l not in t: t+=' (lib (name "%s")(type "KiCad")(uri "${KICAD10_FOOTPRINT_DIR}/%s.pretty")(options "")(descr ""))\n'%(l,l)
open(ft,'w').write(t+')\n')
print('components',n)
