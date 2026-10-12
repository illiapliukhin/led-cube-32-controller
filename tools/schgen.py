"""Minimal KiCad schematic generator: box symbols + net labels at every pin end (flat sheet).
comps: list of dict(ref,value,footprint,fields{},pins[(num,name,net or None)])"""
import uuid, math
G=2.54
def U(): return str(uuid.uuid4())
def esc(s): return s.replace('"','\\"')
def fmt(v): return ('%.4f'%v).rstrip('0').rstrip('.')
def symdef(name,pins):
    n=len(pins); left=pins[:math.ceil(n/2)]; right=pins[math.ceil(n/2):]
    h=max(len(left),len(right))*G; w=G*8
    o=[f'(symbol "cube:{name}" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)',
       f'(property "Reference" "U" (at 0 {fmt(h/2+G)} 0) (effects (font (size 1.27 1.27))))',
       f'(property "Value" "{name}" (at 0 {fmt(-h/2-G*1.5)} 0) (effects (font (size 1.27 1.27))))',
       '(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
       '(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
       f'(symbol "{name}_0_1" (rectangle (start {fmt(-w/2)} {fmt(h/2)}) (end {fmt(w/2)} {fmt(-h/2-G/2)}) (stroke (width 0.254) (type default)) (fill (type background))))',
       f'(symbol "{name}_1_1"']
    ends=[]
    for i,(num,pn,_) in enumerate(left):
        y=h/2-G*(i+0.5); y=round(y/1.27)*1.27; x=-w/2-G*2
        o.append(f'(pin passive line (at {fmt(x)} {fmt(y)} 0) (length {fmt(G*2)}) (name "{esc(pn)}" (effects (font (size 1.0 1.0)))) (number "{num}" (effects (font (size 1.0 1.0)))))'); ends.append((num,x,y,'L'))
    for i,(num,pn,_) in enumerate(right):
        y=h/2-G*(i+0.5); y=round(y/1.27)*1.27; x=w/2+G*2
        o.append(f'(pin passive line (at {fmt(x)} {fmt(y)} 180) (length {fmt(G*2)}) (name "{esc(pn)}" (effects (font (size 1.0 1.0)))) (number "{num}" (effects (font (size 1.0 1.0)))))'); ends.append((num,x,y,'R'))
    o.append('))'); return '\n'.join(o),ends,w,h
def write(path,comps,title,project):
    root=U(); defs={}; body=[]
    netcount={}
    for c in comps:
        for _,_,n in c['pins']:
            if n: netcount[n]=netcount.get(n,0)+1
    cols=6; x0,y0=30.48,30.48; colw=76.2; rowy=[y0]*cols
    placed=[]
    for idx,c in enumerate(comps):
        key=c['value'].replace(' ','_')+'_'+str(len(c['pins']))+'_'+c.get('symkey','')
        # unique symbol per pin naming
        sig=key+'_'+str(abs(hash(tuple((p[0],p[1]) for p in c['pins'])))%100000)
        if sig not in defs: defs[sig]=symdef(sig,c['pins'])
        _,ends,w,h=defs[sig]
        col=min(range(cols),key=lambda k:rowy[k]); X=x0+col*colw; Y=rowy[col]+h/2+G*2
        X=round(X/G)*G; Y=round(Y/G)*G
        rowy[col]=Y+h/2+G*5
        f=c.get('fields',{})
        props=[f'(property "Reference" "{c["ref"]}" (at {fmt(X)} {fmt(Y-h/2-G)} 0) (effects (font (size 1.27 1.27))))',
               f'(property "Value" "{esc(c["value"])}" (at {fmt(X)} {fmt(Y+h/2+G*1.5)} 0) (effects (font (size 1.27 1.27))))',
               f'(property "Footprint" "{esc(c["footprint"])}" (at {fmt(X)} {fmt(Y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))',
               f'(property "Datasheet" "" (at {fmt(X)} {fmt(Y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))']
        for k,v in f.items(): props.append(f'(property "{k}" "{esc(v)}" (at {fmt(X)} {fmt(Y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
        pinl=' '.join(f'(pin "{p[0]}" (uuid {U()}))' for p in c['pins'])
        body.append(f'(symbol (lib_id "cube:{sig}") (at {fmt(X)} {fmt(Y)} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid {U()}) {" ".join(props)} {pinl} (instances (project "{project}" (path "/{root}" (reference "{c["ref"]}") (unit 1)))))')
        pmap={p[0]:p for p in c['pins']}
        for num,ex,ey,side in ends:
            ax=X+ex; ay=Y-ey; net=pmap[num][2]
            if not net or netcount.get(net,0)<2:
                body.append(f'(no_connect (at {fmt(ax)} {fmt(ay)}) (uuid {U()}))')
            else:
                ang=180 if side=='L' else 0; just='right' if side=='L' else 'left'
                body.append(f'(label "{esc(net)}" (at {fmt(ax)} {fmt(ay)} {ang}) (effects (font (size 1.0 1.0)) (justify {just} bottom)) (uuid {U()}))')
    paper='A0'
    s=[f'(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0") (uuid {root}) (paper "{paper}")',
       f'(title_block (title "{esc(title)}") (company "led-cube-32-controller"))','(lib_symbols']+[d[0] for d in defs.values()]+[')']+body+['(sheet_instances (path "/" (page "1")))',')']
    open(path,'w').write('\n'.join(s))
    import os,re
    d=os.path.dirname(path)
    lib=['(kicad_symbol_lib (version 20241209) (generator "schgen")']+[x[0].replace('(symbol "cube:','(symbol "',1) for x in defs.values()]+[')']
    open(os.path.join(d,'cube.kicad_sym'),'w').write('\n'.join(lib))
    open(os.path.join(d,'sym-lib-table'),'w').write('(sym_lib_table (version 7)\n (lib (name "cube")(type "KiCad")(uri "${KIPRJMOD}/cube.kicad_sym")(options "")(descr ""))\n)\n')
    libs=sorted({c['footprint'].split(':')[0] for c in comps})
    ent=[]
    for l in libs:
        uri='${KIPRJMOD}/../../lib/cube.pretty' if l=='cube' else '${KICAD10_FOOTPRINT_DIR}/%s.pretty'%l
        ent.append(' (lib (name "%s")(type "KiCad")(uri "%s")(options "")(descr ""))'%(l,uri))
    open(os.path.join(d,'fp-lib-table'),'w').write('(fp_lib_table (version 7)\n'+'\n'.join(ent)+'\n)\n')
    return len(comps)
def from_board(board):
    import pcbnew
    comps=[]
    for f in board.GetFootprints():
        pins={}
        for p in f.Pads():
            num=p.GetNumber()
            if not num: continue
            pins.setdefault(num,p.GetNetname() or None)
        if not pins: continue
        fields={}
        for k in ('LCSC','MPN','Alt'):
            try:
                if f.HasField(k): fields[k]=f.GetFieldText(k)
            except Exception: pass
        comps.append(dict(ref=f.GetReference(),value=f.GetValue(),footprint=str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName()),fields=fields,
                          pins=[(n,(PINNAMES.get(f.GetValue(),{}).get(n) or n),net) for n,net in sorted(pins.items(),key=lambda kv:(len(kv[0]),kv[0]))]))
    return comps
PINNAMES={
 '74LVC245APW':{'1':'DIR','10':'GND','19':'~OE','20':'VCC',**{str(2+i):'A%d'%(i+1) for i in range(8)},**{str(18-i):'B%d'%(i+1) for i in range(8)}},
 '74AHCT245PW':{'1':'DIR','10':'GND','19':'~OE','20':'VCC',**{str(2+i):'A%d'%(i+1) for i in range(8)},**{str(18-i):'B%d'%(i+1) for i in range(8)}},
 'AMS1117-3.3':{'1':'GND','2':'VOUT','3':'VIN'},
}
