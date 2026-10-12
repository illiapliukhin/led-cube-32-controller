#!/usr/bin/env python3
"""RGB hanging-strand cube sizing (HD108 clocked 16-bit pixels, clock-gated parallel bus).
Run: python3 calc/rgb_scaling.py"""
BITS_LED=64            # HD108: 16 bit header(3+5x3 gain) + 3x16 bit colour
I_MAX=0.060            # A per LED full white at max gain (5050, 3x20 mA) - datasheet class value
APL=0.15               # realistic average picture level for 3D objects in mostly-dark volume
ABL=0.25               # firmware brightness/power limiter: total current <= 25% of absolute max
LANES=16               # ESP32-S3 LCD_CAM i80 16-bit bus = 16 strands in parallel
PCLK=13.3e6            # conservative bus clock over ribbon + 8-deep regen chain
STRAND_W_G=1.2         # g per LED node incl. its share of 4-core cable (pixel string), +20 g/m cable
COST_LED=(0.18,0.35)   # USD per node, HD108/SK9822 pixel string or 32/m strip (market ranges, see ARCHITECTURE)
out=[]; p=out.append
p(f"{'size':>5} {'N/axis':>6} {'pitch mm':>8} {'LEDs':>9} {'strands':>7} {'branch(16)':>10} {'ports(8br)':>10} {'mainboards':>10} {'fps@1MB':>7} {'fps total':>9} {'Imax A':>8} {'ABL A':>7} {'avg A':>7} {'PSU(LRS-350-5,60A)':>18} {'kg':>5} {'LED cost $':>13}")
for size,N in [(1,32),(1,48),(1,64),(2,64),(2,96),(2,128)]:
    leds=N**3; strands=N*N; br=strands//LANES; ports=-(-br//8)
    clocks_branch=N*BITS_LED+64+N//2+32          # start frame + end frame
    fps_one=PCLK/(clocks_branch*br)               # one main board serving all branches
    # main boards: each main board (one ESP32-S3) handles up to 64 branches (8 ports x 8)
    mb=-(-br//64); fps=PCLK/(clocks_branch*min(br,64))
    imax=leds*I_MAX; iabl=imax*ABL; iavg=imax*APL
    psu=-(-int(iabl)//60)
    kg=(leds*STRAND_W_G+strands*size*20)/1000
    p(f"{size:>4}m {N:>6} {1000*size/N:>8.1f} {leds:>9,} {strands:>7} {br:>10} {ports:>10} {mb:>10} {fps_one:>7.0f} {fps:>9.0f} {imax:>8.0f} {iabl:>7.0f} {iavg:>7.0f} {psu:>18} {kg:>5.0f} {leds*COST_LED[0]:>6.0f}-{leds*COST_LED[1]:<6.0f}")
p("\nNotes:")
p(" fps@1MB = one main board driving everything; fps total = with 1 main board per 64 branches, boards frame-synced (SYNC line).")
p(" Refresh/flicker is NOT tied to fps: HD108 has internal 27 kHz PWM, 16-bit per colour.")
p(" Strand current full white: N*60 mA (32 -> 1.92 A, 64 -> 3.84 A); per strand 4-core 22 AWG ok to 2 A/1 m, 20 AWG for 2 m / 64 LEDs.")
for N,L in [(32,1),(64,2),(128,2)]:
    I=N*I_MAX*ABL; R22=0.0530; R20=0.0333; R18=0.0210  # ohm/m
    p(f"  strand {N} LEDs {L} m @ABL {I:.2f} A: drop (distributed, 2 conductors) 22AWG {I*R22*L:.2f} V, 20AWG {I*R20*L:.2f} V, 18AWG {I*R18*L:.2f} V; inject both ends if >0.3 V")
print('\n'.join(out)); open('calc/rgb_scaling_results.txt','w').write('\n'.join(out)+'\n')
