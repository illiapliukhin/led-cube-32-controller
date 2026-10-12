"""repair pass: route DRC-unconnected pairs inside a region with the A* router.
usage: kpy.sh repair.py board.kicad_pcb x0 y0 x1 y1 [w]"""
import sys,os,json,subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from pcbkit import Board, MM
from router import Router
fn=sys.argv[1]; x0,y0,x1,y1=map(float,sys.argv[2:6]); w=float(sys.argv[6]) if len(sys.argv)>6 else 0.3
KC='/workspace/.kicad10/AppDir/bin/kicad-cli'
for it in range(4):
    _b=pcbnew.LoadBoard(fn); pcbnew.ZONE_FILLER(_b).Fill(_b.Zones()); _b.Save(fn); del _b
    subprocess.run([KC,'pcb','drc','--format','json','-o','/tmp/rep.json',fn],capture_output=True)
    d=json.load(open('/tmp/rep.json')); U=d.get('unconnected_items',[])
    print('iter',it,'unconnected',len(U),flush=True)
    if not U: break
    bd=Board(); bd.b=pcbnew.LoadBoard(fn)
    for n in bd.b.GetNetInfo().NetsByName().values() if hasattr(bd.b.GetNetInfo(),'NetsByName') else []: pass
    bd.nets={str(k):v for k,v in bd.b.GetNetInfo().NetsByName().items()}
    rt=Router(bd,x0,y0,x1,y1,step=0.25,w=w,clr=0.15)
    # keep footprint keepout zones blocked
    for f in bd.b.GetFootprints():
        for z in f.Zones():
            bb=z.GetBoundingBox(); rt.block_rect([0,1],bb.GetX()/MM,bb.GetY()/MM,bb.GetRight()/MM,bb.GetBottom()/MM,None)
    rt.load_board(); ok=0
    for v in U:
        a,c=v['items'][0],v['items'][1]
        net=a['description'].split('[')[1].split(']')[0]
        if net=='GND': continue
        pa=(a['pos']['x'],a['pos']['y']); pc=(c['pos']['x'],c['pos']['y'])
        if not all(x0<p[0]<x1 and y0<p[1]<y1 for p in (pa,pc)): continue
        def lays(desc): return [0] if 'F.Cu' in desc and 'B.Cu' not in desc else ([1] if 'B.Cu' in desc and 'F.Cu' not in desc else [0,1])
        src=[(pa[0],pa[1],l) for l in lays(a['description'])]; dst=[(pc[0],pc[1],l) for l in lays(c['description'])]
        if rt.connect(net,src,dst): ok+=1
        else: print(' fail',net,pa,pc)
    bd.b.Save(fn); print(' routed',ok,flush=True)
