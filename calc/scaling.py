#!/usr/bin/env python3
"""Scalability: cube X*Y*Z, Z = LEDs per column (layers). MBI5153 max 1:32 scan,
so Z>32 is split into G=ceil(Z/32) electrically separate column segments (zones),
each with own driver set (top zone fed from a top tile ceiling, or mid-cut). Ipk 10 mA."""
import math
I=0.010; GCLK=25e6; out=[]
hdr=f"{'cube':>10} {'LEDs':>7} {'scan':>5} {'zones':>5} {'ch':>5} {'drv':>4} {'tiles':>5} {'avg mA':>6} {'refresh Hz':>10} {'PSU A':>6} {'Mbit/s@16b60fps':>15} {'lanes':>5}"
out.append(hdr)
for X,Y,Z in [(32,32,32),(32,32,48),(32,32,64),(48,48,48),(64,64,64),(32,32,16)]:
    G=math.ceil(Z/32); scan=math.ceil(Z/G); ch=X*Y*G; drv=ch//16
    tiles=drv//4; avg=I/scan*1e3; ref=GCLK/(513*scan); A=X*Y*G*I+2
    bw=X*Y*Z*16*60/1e6; lanes=tiles
    out.append(f"{X}x{Y}x{Z:>3} {X*Y*Z:>7} 1/{scan:<3} {G:>5} {ch:>5} {drv:>4} {tiles:>5} {avg:>6.3f} {ref:>10.0f} {A:>6.1f} {bw:>15.1f} {lanes:>5}")
out.append("\nNotes: duty never worse than 1/32 because zones scan in parallel -> brightness constant;")
out.append("PSU current grows with X*Y*zones; bandwidth per lane stays ~2 Mbit/s; one RP2040 PIO SM drives 16-30 lanes (2x RP2040 for 64^3).")
out.append("Column wire: 64 LEDs x 31 mm = 2 m, R(0.8mm)=69 mOhm, 10 mA -> 0.7 mV drop: irrelevant. Limits are mechanical (buckling/sag) and layer current (X*Y*10 mA: 64x64 -> 41 A per layer FET -> split layer into 4 quadrants, 4 FETs).")
print('\n'.join(out)); open('calc/scaling_results.txt','w').write('\n'.join(out)+'\n')
