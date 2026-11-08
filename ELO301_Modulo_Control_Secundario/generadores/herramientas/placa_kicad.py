"""Exporta los pads y vías de la placa, importada a KiCad, para lvs_gerber.py. Se corre con el Python de KiCad:

kicad-cli pcb import --format altium -o placa.kicad_pcb altium/ELO301_G1.PcbDoc
flatpak run --command=python3 org.kicad.KiCad placa_kicad.py placa.kicad_pcb pads.json
"""
import json, sys
import pcbnew

b = pcbnew.PCB_IO_MGR.Load(pcbnew.PCB_IO_MGR.KICAD_SEXP, sys.argv[1])
e = b.GetBoardEdgesBoundingBox()
e.Inflate(-25000)  # el borde lo incluye el ancho de línea de Edge.Cuts (0,05 mm)
x0, y1 = e.GetLeft(), e.GetBottom()
mm = lambda v: round(v / 1e6, 5)
pads = []
for f in b.GetFootprints():
    for p in f.Pads():
        c, q = p.ShapePos(p.GetLayerSet().Seq()[0]), p.GetPosition()
        pads.append(dict(ref=f.GetReference(), pin=p.GetNumber(), net=p.GetNetname(), x=mm(c.x - x0), y=mm(y1 - c.y), px=mm(q.x - x0), py=mm(y1 - q.y),
                         th=bool(p.HasHole()), drill=mm(p.GetDrillSizeX()), top=p.IsOnLayer(pcbnew.F_Cu), bot=p.IsOnLayer(pcbnew.B_Cu), sx=mm(p.GetSizeX()), sy=mm(p.GetSizeY())))
vias = [dict(x=mm(t.GetPosition().x - x0), y=mm(y1 - t.GetPosition().y), net=t.GetNetname(), drill=mm(t.GetDrillValue())) for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
json.dump(dict(w=mm(e.GetWidth()), h=mm(e.GetHeight()), pads=pads, vias=vias), open(sys.argv[2], 'w'), indent=0)
print(mm(e.GetWidth()), mm(e.GetHeight()), len(pads), 'pads', len(vias), 'vías')
