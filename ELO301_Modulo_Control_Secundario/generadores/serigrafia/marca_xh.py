"""Marca de pin 1 de la huella «B5B-XH-A - JST» (J3–J6) a más de 0,2 mm del borde.

J3–J6 están en el borde superior y la «L» de pin 1 (convertida de KiCad, 0,29 mm por fuera de la esquina de la
carcasa) quedaba a 0,16 mm del borde. Se baja 0,29 mm, hasta la línea superior de la carcasa: el tramo vertical
termina ahí y el horizontal queda de 0,29 mm, como prolongación de esa línea. Se hace igual en ELO301_G1.PcbLib y en
la placa, y después DRC y guardado. Solo actúa si la marca sigue 0,29 mm por encima de la carcasa (se puede volver a
correr). Uso (con Altium abierto en la VM): python3 marca_xh.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'pcb'))
from drc_comun import correr, resumen, hora_pcb, L, ABRIR, RESUMEN, GUARDAR

HUELLA, BAJA = 'B5B-XH-A - JST', 0.29


def marcas(g, nombre):
    """Agrega a Lista los tramos de más arriba del grupo g (la marca), si siguen BAJA mm sobre la línea de la carcasa."""
    alto = "if P.Y1 > P.Y2 then t := P.Y1 else t := P.Y2;"
    return f"""Todas := TInterfaceList.Create; ymax := -2147483647; y2 := -2147483647;
GI := {g}.GroupIterator_Create; GI.AddFilter_ObjectSet(MkSet(eTrackObject)); GI.AddFilter_LayerSet(MkSet(eTopOverlay));
P := GI.FirstPCBObject;
while P <> nil do begin Todas.Add(P); P := GI.NextPCBObject; end;
{g}.GroupIterator_Destroy(GI);
for i := 0 to Todas.Count - 1 do begin P := Todas.Items[i]; {alto} if t > ymax then ymax := t; end;
for i := 0 to Todas.Count - 1 do begin P := Todas.Items[i]; {alto} if (t < ymax) and (t > y2) then y2 := t; end;
if Abs(ymax - y2 - MMsToCoord({BAJA})) < MMsToCoord(0.005) then begin
  for i := 0 to Todas.Count - 1 do begin P := Todas.Items[i]; {alto} if t = ymax then Lista.Add(P); end;
  s := s + {nombre} + ' marca bajada; ';
end else s := s + {nombre} + ' sin cambio; ';
"""


if __name__ == '__main__':
    r = correr(f"""var
    Obj1, Board, It, X, V, Comp, GI, P, LibDoc, Lib, LC, Poly : IDispatch;
    Lista, Todas, Polys : TInterfaceList;
    s, nom : String;
    i, n, t, ymax, y2 : Integer;
begin
{ABRIR}s := ''; Lista := TInterfaceList.Create;
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eComponentObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
Comp := It.FirstPCBObject;
while Comp <> nil do begin
  if Comp.Pattern = '{HUELLA}' then begin
    if Comp.Rotation <> 0 then s := s + Comp.Name.Text + ' girado, no se toca; '
    else begin
{marcas('Comp', 'Comp.Name.Text')}
    end;
  end;
  Comp := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
LibDoc := Client.OpenDocument('PCBLIB', '{L}ELO301_G1.PcbLib'); Client.ShowDocument(LibDoc);
Lib := PCBServer.GetCurrentPCBLibrary; LC := Lib.GetComponentByName('{HUELLA}');
{marcas('LC', "'biblioteca'")}
PCBServer.PreProcess;
for i := 0 to Lista.Count - 1 do begin
  P := Lista.Items[i]; P.BeginModify;
  if P.Y1 = P.Y2 then begin
    if P.X1 < P.X2 then P.X2 := P.X1 + MMsToCoord({BAJA}) else P.X1 := P.X2 + MMsToCoord({BAJA});
    P.Y1 := P.Y1 - MMsToCoord({BAJA}); P.Y2 := P.Y2 - MMsToCoord({BAJA});
  end
  else if P.Y1 > P.Y2 then P.Y1 := P.Y1 - MMsToCoord({BAJA}) else P.Y2 := P.Y2 - MMsToCoord({BAJA});
  P.EndModify;
end;
PCBServer.PostProcess;
if Lista.Count > 0 then begin LibDoc.SetModified(True); LibDoc.DoFileSave(''); end;
s := s + 'tramos movidos ' + IntToStr(Lista.Count);
Client.ShowDocument(Obj1);
Polys := TInterfaceList.Create;
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(ePolyObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
X := It.FirstPCBObject;
while X <> nil do begin Polys.Add(X); X := It.NextPCBObject; end;
Board.BoardIterator_Destroy(It);
for i := 0 to Polys.Count - 1 do begin Poly := Polys.Items[i]; Poly.BeginModify; Poly.Rebuild; Poly.EndModify; end;
{RESUMEN}{GUARDAR}ResultText := s;
end;""", 600)
    print(r.split('\n')[0])
    resumen(r, 'DRC con la marca de pin 1 de J3–J6 bajada')
    print('placa guardada:', hora_pcb())
