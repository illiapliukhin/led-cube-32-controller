"""Schematic -> PCB link (schematic is the source of truth).
Exports the netlist from <board>.kicad_sch with kicad-cli, then for every footprint:
  * sets the symbol link (KIID path, sheet name/file),
  * checks value + footprint lib id against the schematic (abort on mismatch),
  * checks every pad's net against the schematic net (abort on mismatch) and adopts schematic net names.
usage: kpy.sh sch2pcb.py board.kicad_pcb board.kicad_sch"""
import sys,re,subprocess,collections,pcbnew,os
pcbf,schf=sys.argv[1],sys.argv[2]
KC='/workspace/.kicad10/AppDir/bin/kicad-cli'
subprocess.run([KC,'sch','export','netlist','--format','kicadsexpr','-o','/tmp/s2p.net',schf],check=True,capture_output=True)
t=re.sub(r'\s+',' ',open('/tmp/s2p.net').read()).replace('( ','(')
def blocks(text,key):
    out=[];i=0
    while True:
        i=text.find('('+key+' ',i)
        if i<0: return out
        d=0;j=i
        while True:
            if text[j]=='(': d+=1
            elif text[j]==')':
                d-=1
                if d==0: break
            j+=1
        out.append(text[i:j+1]); i=j+1
comps={}
for c in blocks(t[t.find('(components'):t.find('(libparts')] ,'comp'):
    ref=re.search(r'\(ref "([^"]+)"',c).group(1); val=re.search(r'\(value "([^"]*)"',c).group(1)
    fp=re.search(r'\(footprint "([^"]*)"',c).group(1); ts=re.search(r'\(tstamps "([^"]+)"',c).group(1)
    comps[ref]=(val,fp,ts)
pin2net={}
for n in blocks(t[t.find('(nets'):],'net'):
    name=re.search(r'\(name "([^"]*)"',n).group(1)
    for nd in re.finditer(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"',n): pin2net[(nd.group(1),nd.group(2))]=name
b=pcbnew.LoadBoard(pcbf); err=[]; ren={}
for f in b.GetFootprints():
    r=f.GetReference()
    if f.IsBoardOnly(): continue
    if r not in comps: err.append('no symbol for '+r); continue
    val,fp,ts=comps[r]
    if val!=f.GetValue(): err.append(f'{r} value {f.GetValue()} != {val}')
    lid=str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName())
    if fp!=lid: err.append(f'{r} footprint {lid} != {fp}')
    f.SetPath(pcbnew.KIID_PATH('/'+ts)); f.SetSheetname('/'); f.SetSheetfile(os.path.basename(schf))
    for p in f.Pads():
        if not p.GetNumber(): continue
        k=(r,p.GetNumber()); pn=p.GetNetname(); sn=pin2net.get(k,'')
        if not pn and not sn: continue
        if not sn or sn.startswith('unconnected-'):
            if pn: err.append(f'{r}.{p.GetNumber()} PCB net {pn} but unconnected in schematic')
            elif sn:
                n=b.FindNet(sn)
                if not n: n=pcbnew.NETINFO_ITEM(b,sn); b.Add(n)
                p.SetNet(n)
            continue
        if pn in ren and ren[pn]!=sn: err.append(f'{r}.{p.GetNumber()} net {pn}->{sn} conflicts {ren[pn]}')
        ren.setdefault(pn,sn)
missing=set(comps)-{f.GetReference() for f in b.GetFootprints()}
err+= ['footprint missing for '+m for m in sorted(missing)]
if err:
    print('MISMATCH',len(err)); print('\n'.join(err[:40])); sys.exit(1)
ni=b.GetNetInfo()
for old,new in ren.items():
    if old!=new:
        n=b.FindNet(old); n.SetNetname(new)
b.Save(pcbf); print('linked',len(comps),'symbols; nets renamed',sum(1 for o,n in ren.items() if o!=n))
