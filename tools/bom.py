import sys,os,csv,collections,pcbnew
HERE=os.path.dirname(os.path.abspath(__file__))
b=pcbnew.LoadBoard(sys.argv[1])
g=collections.OrderedDict()
for f in sorted(b.GetFootprints(),key=lambda f:f.GetReference()):
    r=f.GetReference()
    if r.startswith(('H','FID')): continue
    k=(f.GetValue(),str(f.GetFPID().GetLibItemName()),f.GetFieldText('LCSC') if f.HasField('LCSC') else '',f.GetFieldText('MPN') if f.HasField('MPN') else '')
    g.setdefault(k,[]).append(r)
with open(sys.argv[2],'w',newline='') as fh:
    w=csv.writer(fh); w.writerow(['Comment','Designator','Footprint','LCSC Part #','MPN','Qty'])
    for (v,fp,l,m),refs in g.items(): w.writerow([v,','.join(refs),fp,l,m,len(refs)])
print(len(g),'lines')
