"""Read a KiCad schematic netlist (kicad-cli export, kicadsexpr) -> comps, pin->net."""
import re,subprocess
KC='/workspace/.kicad10/AppDir/bin/kicad-cli'
def _blocks(text,key):
    out=[];i=0
    while True:
        i=text.find('('+key+' ',i)
        if i<0: return out
        d=0;j=i
        while True:
            c=text[j]
            if c=='(': d+=1
            elif c==')':
                d-=1
                if d==0: break
            j+=1
        out.append(text[i:j+1]); i=j+1
def read(sch,tmp='/tmp/_nl.net'):
    subprocess.run([KC,'sch','export','netlist','--format','kicadsexpr','-o',tmp,sch],check=True,capture_output=True)
    t=re.sub(r'\s+',' ',open(tmp).read()).replace('( ','(')
    comps={}
    for c in _blocks(t[t.find('(components'):t.find('(libparts')],'comp'):
        g=lambda k:(re.search(r'\(%s "([^"]*)"'%k,c) or [None,''])[1]
        f={m.group(1):m.group(2) for m in re.finditer(r'\(field \(name "([^"]+)"\) "([^"]*)"\)',c)}
        comps[g('ref')]=dict(value=g('value'),footprint=g('footprint'),ts=g('tstamps'),fields=f)
    pin2net={}
    for n in _blocks(t[t.find('(nets'):],'net'):
        name=re.search(r'\(name "([^"]*)"',n).group(1)
        for nd in re.finditer(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"',n): pin2net[(nd.group(1),nd.group(2))]=name
    return comps,pin2net
