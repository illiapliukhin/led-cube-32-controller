#!/usr/bin/env python3
"""Main board schematic generated from the same netlist as main_gen.py (single source of truth: the PCB generator).
Run: ../../kpy.sh $PWD/main_sch.py  (needs main_v1.kicad_pcb)"""
import sys,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(HERE,'../../tools'))
import pcbnew
from schgen import write
b=pcbnew.LoadBoard(os.path.join(HERE,'main_v1.kicad_pcb'))
import glob
FPL='/workspace/.kicad10/AppDir/share/kicad/footprints/'
IDX={os.path.basename(p)[:-10]:os.path.basename(os.path.dirname(p))[:-7] for p in glob.glob(FPL+'*.pretty/*.kicad_mod')}
C=[]
for f in sorted(b.GetFootprints(),key=lambda f:f.GetReference()):
    ref=f.GetReference()
    if ref.startswith(('H','FID')): continue
    pins={}
    for p in f.Pads():
        n=p.GetNumber()
        if not n or n in pins: continue
        pins[n]=p.GetNetname() or ''
    nm=str(f.GetFPID().GetLibItemName()); fp=IDX.get(nm,'cube')+':'+nm
    fl={k:f.GetFieldText(k) for k in ('LCSC','MPN') if f.HasField(k)} if hasattr(f,'HasField') else {}
    C.append(dict(ref=ref,value=f.GetValue(),footprint=fp,fields=fl,pins=[(n,n,net if net else None) for n,net in sorted(pins.items(),key=lambda t:(len(t[0]),t[0]))]))
n=write(os.path.join(HERE,'main_v1.kicad_sch'),C,'Main board v1.1 - ESP32-S3, 8 ports x 23-bit bus, 12 V in','main_v1')
print('components',n)
