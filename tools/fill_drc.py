import sys,pcbnew,json,subprocess,collections
fn=sys.argv[1]
b=pcbnew.LoadBoard(fn); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(fn)
print('filled')
