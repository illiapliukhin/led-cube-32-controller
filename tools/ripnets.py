import sys,pcbnew
fn=sys.argv[1]; nets=set(sys.argv[2].split(',')); x1=float(sys.argv[3])
b=pcbnew.LoadBoard(fn); n=0
for t in list(b.GetTracks()):
    if t.GetNetname() in nets and t.GetPosition().x/1e6<x1: b.Remove(t); n+=1
b.Save(fn); print('ripped',n)
