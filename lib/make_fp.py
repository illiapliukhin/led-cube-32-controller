"""Custom footprints drawn from manufacturer land patterns (see docs/FOOTPRINTS.md)."""
import os
D=os.path.join(os.path.dirname(os.path.abspath(__file__)),'cube.pretty')
def pad(n,x,y,w,h,shape='roundrect'):
    return f'  (pad "{n}" smd {shape} (at {x:.4f} {y:.4f}) (size {w:.4f} {h:.4f}) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2))\n'
def fp(name,descr,pads,body,crt,model=None,extra=''):
    bw,bh=body; cw,ch=crt
    s=f'(footprint "{name}" (version 20240108) (generator "cube_make_fp") (layer "F.Cu")\n  (descr "{descr}")\n  (attr smd)\n'
    s+=f'  (property "Reference" "REF**" (at 0 {-ch/2-0.8:.2f} 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))\n'
    s+=f'  (property "Value" "{name}" (at 0 {ch/2+0.8:.2f} 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))\n'
    s+=f'  (fp_rect (start {-bw/2:.3f} {-bh/2:.3f}) (end {bw/2:.3f} {bh/2:.3f}) (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))\n'
    s+=f'  (fp_rect (start {-cw/2:.3f} {-ch/2:.3f}) (end {cw/2:.3f} {ch/2:.3f}) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))\n'
    s+=extra+''.join(pads)
    if model: s+=f'  (model "{model}" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))\n'
    s+=')\n'; open(os.path.join(D,name+'.kicad_mod'),'w').write(s)
# TI RPW0010A (TPS25947), land pattern example 4225183/A, top view, KiCad y down
P=[]
for n,y in ((1,-0.7),(2,-0.225),(3,0.225),(4,0.7)):
    h=0.3 if n in (1,4) else 0.25
    P.append(pad(n,-0.9,y,0.6,h))
for n,y in ((10,-0.7),(9,-0.225),(8,0.225),(7,0.7)):
    h=0.3 if n in (7,10) else 0.25
    P.append(pad(n,0.9,y,0.6,h))
# L-legs of corner pads (same pad number => same net)
for n,x,y0,y1 in ((1,-0.725,-1.2,-0.7),(10,0.725,-1.2,-0.7),(4,-0.725,0.7,1.2),(7,0.725,0.7,1.2)):
    P.append(pad(n,x,(y0+y1)/2,0.25,abs(y1-y0)))
P.append(pad(5,-0.25,0.1,0.3,2.2)); P.append(pad(6,0.25,0.1,0.3,2.2))
silk='  (fp_line (start -1.1 -1.35) (end -0.6 -1.35) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))\n  (fp_circle (center -1.35 -1.0) (end -1.25 -1.0) (stroke (width 0.12) (type solid)) (fill solid) (layer "F.SilkS"))\n'
fp('TI_RPW0010A_VQFN-HR-10_2x2mm_P0.45mm','TI RPW0010A VQFN-HR 2x2 mm (TPS25947), land pattern per TI 4225183/A',P,(2.0,2.0),(2.9,2.9),'${KICAD10_3DMODEL_DIR}/Package_DFN_QFN.3dshapes/Texas_RPU0010A_VQFN-HR-10_2x2mm_P0.5mm.step',silk)
# YJYCOIN YSPI1365: F=14.5 total, G=5.0 pad height, H=6.5 gap -> pad 4.0 x 5.0 at +-5.25
fp('L_YJYCOIN_YSPI1365','YJYCOIN YSPI1365 13.8x12.6 mm molded inductor, land per datasheet (F14.5 G5.0 H6.5)',
   [pad(1,-5.25,0,4.0,5.0),pad(2,5.25,0,4.0,5.0)],(13.8,12.6),(15.0,13.2),'${KICAD10_3DMODEL_DIR}/Inductor_SMD.3dshapes/L_TaiTech_TMPC1265_13.5x12.5mm.step')
# Cjiang FXL0630: a=3.7 gap, b=8.4 total, c=3.5 pad height -> pad 2.35 x 3.5 at +-3.025
fp('L_Cjiang_FXL0630','Cjiang FXL0630 7.0x6.6 mm molded inductor, land per datasheet (a3.7 b8.4 c3.5)',
   [pad(1,-3.025,0,2.35,3.5),pad(2,3.025,0,2.35,3.5)],(7.0,6.6),(9.0,7.2),'${KICAD10_3DMODEL_DIR}/Inductor_SMD.3dshapes/L_Bourns_SRP7028A_7.3x6.6mm.step')
print('ok')
