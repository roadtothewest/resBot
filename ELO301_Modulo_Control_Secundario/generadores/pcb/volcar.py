"""Vuelca la placa (mm desde el origen): /tmp/geometria.json con T pistas, A arcos, V vías, S serigrafía de componentes y
D designadores, y /tmp/pads.json con los pads."""
import json
from drc_comun import *
r = correr(f"""{VARS}    P, It2 : IDispatch;
    BB : TCoordRect;
    capa, red : String;
{ABRIR}s := '';
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eTrackObject, eArcObject, eViaObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
X := It.FirstPCBObject;
while X <> nil do
begin
    red := ''; if X.Net <> nil then red := X.Net.Name;
    if X.ObjectId = eViaObject then
        s := s + 'V;' + FloatToStr(CoordToMMs(X.x - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(X.y - Board.YOrigin)) + ';' + FloatToStr(CoordToMMs(X.Size)) + ';' + red + #10
    else if (not X.InComponent) and (not X.InPolygon) then
    begin
        BB := X.BoundingRectangle;
        if X.ObjectId = eTrackObject then
            s := s + 'T;' + Layer2String(X.Layer) + ';' + FloatToStr(CoordToMMs(X.x1 - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(X.y1 - Board.YOrigin)) + ';' + FloatToStr(CoordToMMs(X.x2 - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(X.y2 - Board.YOrigin)) + ';' + FloatToStr(CoordToMMs(X.Width)) + ';' + red + #10
        else
            s := s + 'A;' + Layer2String(X.Layer) + ';' + FloatToStr(CoordToMMs(BB.Left - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(BB.Bottom - Board.YOrigin)) + ';' + FloatToStr(CoordToMMs(BB.Right - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(BB.Top - Board.YOrigin)) + ';' + FloatToStr(CoordToMMs(X.LineWidth)) + ';' + red + #10;
    end
    else if X.InComponent and ((X.Layer = eTopOverlay) or (X.Layer = eBottomOverlay)) then
    begin
        BB := X.BoundingRectangle;
        s := s + 'S;' + Layer2String(X.Layer) + ';' + FloatToStr(CoordToMMs(BB.Left - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(BB.Bottom - Board.YOrigin)) + ';' + FloatToStr(CoordToMMs(BB.Right - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(BB.Top - Board.YOrigin)) + #10;
    end;
    X := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eComponentObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
C := It.FirstPCBObject;
while C <> nil do
begin
    BB := C.Name.BoundingRectangle;
    s := s + 'D;' + C.Name.Text + ';' + FloatToStr(CoordToMMs(C.Name.XLocation - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(C.Name.YLocation - Board.YOrigin)) + ';'
         + FloatToStr(CoordToMMs(BB.Left - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(BB.Bottom - Board.YOrigin)) + ';' + FloatToStr(CoordToMMs(BB.Right - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(BB.Top - Board.YOrigin)) + ';' + BoolToStr(C.NameOn) + ';' + Layer2String(C.Name.Layer) + #10;
    C := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
ResultText := s;""")
g = {'T': [], 'A': [], 'V': [], 'S': [], 'D': []}
num = lambda v: float(v.replace(',', '.'))
for l in r.strip().split('\n'):
    c = l.split(';')
    if c[0] == 'V': g['V'].append([num(c[1]), num(c[2]), num(c[3]), c[4]])
    elif c[0] in 'TA': g[c[0]].append([c[1]] + [num(v) for v in c[2:7]] + [c[7]])
    elif c[0] == 'S': g['S'].append([c[1]] + [num(v) for v in c[2:6]])
    elif c[0] == 'D': g['D'].append([c[1]] + [num(v) for v in c[2:8]] + [c[8], c[9]])
json.dump(g, open('/tmp/geometria.json', 'w'))
print({k: len(v) for k, v in g.items()}, 'capas pistas:', sorted({t[0] for t in g['T']}))

# pads de todos los componentes -> /tmp/pads.json
r = correr(f"""{VARS}    ItP, P : IDispatch;
    BB : TCoordRect;
    red : String;
{ABRIR}s := '';
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eComponentObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
C := It.FirstPCBObject;
while C <> nil do
begin
    ItP := C.GroupIterator_Create; ItP.AddFilter_ObjectSet(MkSet(ePadObject));
    P := ItP.FirstPCBObject;
    while P <> nil do
    begin
        red := '';
        if P.Net <> nil then red := P.Net.Name;
        BB := P.BoundingRectangle;
        s := s + C.Name.Text + ';' + P.Name + ';' + red + ';' + Layer2String(P.Layer) + ';' + FloatToStr(CoordToMMs(C.x - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(C.y - Board.YOrigin)) + ';'
             + FloatToStr(CoordToMMs(P.x - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(P.y - Board.YOrigin)) + ';'
             + FloatToStr(CoordToMMs(BB.Left - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(BB.Bottom - Board.YOrigin)) + ';' + FloatToStr(CoordToMMs(BB.Right - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(BB.Top - Board.YOrigin)) + ';' + FloatToStr(CoordToMMs(P.HoleSize)) + #10;
        P := ItP.NextPCBObject;
    end;
    C.GroupIterator_Destroy(ItP);
    C := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
ResultText := s;""")
pads = []
for l in r.strip().split('\n'):
    c = l.split(';')
    f = [num(x) for x in c[4:]]
    pads.append({'des': c[0], 'pad': c[1], 'net': c[2], 'capa': c[3], 'comp': f[0:2], 'centro': f[2:4], 'caja': f[4:8], 'agujero': f[8]})
json.dump(pads, open('/tmp/pads.json', 'w'))
print(len(pads), 'pads')
