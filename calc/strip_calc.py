"""1 m strip board variants: per-board current, power cells, outputs per driver. Output: calc/strip_calc.md"""
import math
I_LED=0.060; ABL=0.25; ETA=0.92; V5=5.1; V12=12.0
SEG=4; SEG_L=250.0            # 4 identical 250 mm segments (JLC PCBA max 470x500 mm; bare 2-layer max 1020x600 mm)
I_CELL=10.0                   # A per power cell (TPS56C215 12 A rated, 80 % derating); eFuse 5 A @12 V per cell
o=['| Connectors / 1 m | Pitch | Segments × conn. | px / strand | px / board | I5V ABL 25 % / board | I5V / segment | Power cells / segment | I12V / segment | I / strand (ABL) | Data buffers / seg | Clock buffers / seg | Clock groups / seg | Strand connector |',
   '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
for N in (124,64,48,32):
    n=N//SEG; px=N; I_b=N*N*I_LED*ABL; I_s=I_b/SEG; cells=math.ceil(I_s/I_CELL)
    i12=I_s*V5/V12/ETA; ist=px*I_LED*ABL
    conn='JST XH B4B-XH-A, 2 staggered rows (16.1 mm per row)' if 1000/N<12.5 else 'JST XH B4B-XH-A, 1 row'
    o.append(f'| **{N}** | {1000/N:.2f} mm | {SEG} × {n} | {px} | {N*N:,} | {I_b:.0f} A | {I_s:.1f} A | {cells} | {i12:.1f} A | {ist:.2f} A | {math.ceil(n/8)} | {math.ceil(n/8)} | {math.ceil(n/16)} | {conn} |')
open(__file__.replace('.py','.md'),'w').write('\n'.join(o)+'\n'); print('\n'.join(o))
