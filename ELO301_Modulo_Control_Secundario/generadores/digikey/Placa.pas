{ Cambios de la placa ELO301_G1 desde Altium. Se ejecuta con correr.ps1 -Script Placa -Proc <procedimiento>.
    - ImportarCambios: Design > Import Changes (ECO) desde el proyecto; el dialogo ECO queda abierto.
    - ClasesDeRed: repone las clases Potencia y Alimentacion que usan las reglas Ancho_*.
    - PourCapa3: polígono de GND en Senal-Potencia con el mismo contorno que los de Top y Bottom.
    - MoverJ9 y RutaVin12J9: J9 fuera de la zona del tornillo de H1, y VIN_12V por fuera del J9.
    - Serigrafia sobre los minimos de JLCPCB (scripts de Python en generadores/serigrafia):
      seda_plan.py -> SerigrafiaPlaca; DesignadoresTamano -> designadores.py -> DesignadoresUbicar;
      VolcarHuellas -> huellas_plan.py -> AplicarHuellas -> BorrarSedaHuellas para las bibliotecas. }

Const
  RUTA_BASE = 'C:\Users\Estudiante USM\Desktop\resBot\ELO301_Modulo_Control_Secundario\';
  RUTA_TMP = 'C:\Users\ESTUDI~1\AppData\Local\Temp\altium_simbolos\';
  RUTA_LOG = 'C:\Users\ESTUDI~1\AppData\Local\Temp\altium_simbolos\log.txt';

Var
  Bitacora : TStringList;

Procedure Log(S : String);
Begin
  Bitacora.Add(S);
  Bitacora.SaveToFile(RUTA_LOG);
End;

Procedure Terminar;
Var
  Marca : TStringList;
Begin
  Log('fin');
  Marca := TStringList.Create;
  Marca.Add('fin');
  Marca.SaveToFile(RUTA_TMP + 'fin.flag');
  Marca.Free;
End;

Function AbrirPlaca : Variant;
Var
  Doc : Variant;
Begin
  GetWorkspace.DM_OpenProject(RUTA_BASE + 'altium\ELO301_G1.PrjPcb', True);
  Doc := Client.OpenDocument('PCB', RUTA_BASE + 'altium\ELO301_G1.PcbDoc');
  Client.ShowDocument(Doc);
  Result := Doc;
End;

Procedure GuardarPlaca(Doc : Variant);
Begin
  Doc.Modified := True;
  Client.ShowDocument(Doc);
  ResetParameters;
  AddStringParameter('ObjectKind', 'Document');
  RunProcess('WorkspaceManager:SaveObject');
End;

Function BuscarRed(Board : Variant; Nombre : String) : Variant;
Var
  It, N : Variant;
Begin
  Result := Nil;
  It := Board.BoardIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eNetObject));
  It.AddFilter_LayerSet(AllLayers);
  It.AddFilter_Method(eProcessAll);
  N := It.FirstPCBObject;
  While N <> Nil Do
  Begin
    If N.Name = Nombre Then Begin Result := N; Break; End;
    N := It.NextPCBObject;
  End;
  Board.BoardIterator_Destroy(It);
End;

{ Miembros separados por espacios }
Procedure CrearClaseDeRed(Board : Variant; Nombre, Miembros : String);
Var
  C : Variant;
  Resto, M : String;
  P : Integer;
Begin
  C := PCBServer.PCBClassFactoryByClassMember(eClassMemberKind_Net);
  C.SuperClass := False;
  C.Name := Nombre;
  Resto := Miembros + ' ';
  While Pos(' ', Resto) > 0 Do
  Begin
    P := Pos(' ', Resto);
    M := Copy(Resto, 1, P - 1);
    Resto := Copy(Resto, P + 1, Length(Resto));
    If M <> '' Then C.AddMemberByName(M);
  End;
  Board.AddPCBObject(C);
  Log('  clase ' + Nombre + ': ' + Miembros);
End;

{ Las clases que ECO quita porque solo existen en la placa (mismos miembros que en el commit e74c17b) }
Procedure ClasesDeRed;
Var
  Doc, Board : Variant;
Begin
  Bitacora := TStringList.Create;
  Log('ClasesDeRed ' + DateTimeToStr(Now));
  Doc := AbrirPlaca;
  Board := PCBServer.GetCurrentPCBBoard;
  Log('  placa: ' + Board.FileName);
  PCBServer.PreProcess;
  CrearClaseDeRed(Board, 'Potencia', 'VIN_12V VIN_PROT SW V_5V');
  CrearClaseDeRed(Board, 'Alimentacion', 'V3V3_MCU V3V3_SENS VDDA V5_SENS');
  PCBServer.PostProcess;
  GuardarPlaca(Doc);
  Log('  guardada');
  Terminar;
  Bitacora.Free;
End;

{ GND en Senal-Potencia: mismo contorno que los pours de Top y Bottom (0,3 mm dentro del borde) }
Procedure PourCapa3;
Var
  Doc, Board, Poly, Red, Seg : Variant;
  X, Y : Array[0..3] Of Double;
  I : Integer;
Begin
  Bitacora := TStringList.Create;
  Log('PourCapa3 ' + DateTimeToStr(Now));
  Doc := AbrirPlaca;
  Board := PCBServer.GetCurrentPCBBoard;
  Red := BuscarRed(Board, 'GND');
  Log('  red GND encontrada: ' + BoolToStr(Red <> Nil, True));
  X[0] := 1011.811; Y[0] := 1011.811;
  X[1] := 3744.0945; Y[1] := 1011.811;
  X[2] := 3744.0945; Y[2] := 2956.6929;
  X[3] := 1011.811; Y[3] := 2956.6929;
  PCBServer.PreProcess;
  Poly := PCBServer.PCBObjectFactory(ePolyObject, eNoDimension, eCreate_Default);
  Poly.Layer := eMidLayer1;
  Poly.PolyHatchStyle := ePolySolid;
  Poly.RemoveDead := True;
  Poly.Name := 'GND_Senal';
  Poly.Net := Red;
  Poly.PointCount := 4;
  For I := 0 To 3 Do
  Begin
    Seg := TPolySegment;
    Seg.Kind := ePolySegmentLine;
    Seg.vx := MilsToCoord(X[I]);
    Seg.vy := MilsToCoord(Y[I]);
    Poly.Segments[I] := Seg;
  End;
  Log('  poligono armado');
  Board.AddPCBObject(Poly);
  Poly.Rebuild;
  PCBServer.PostProcess;
  Log('  vertido; area de cobre (mm2): ' + FloatToStr(Poly.AreaSize / 1E14 * 6.4516));
  GuardarPlaca(Doc);
  Log('  guardada');
  Terminar;
  Bitacora.Free;
End;

Function MM(C : Integer) : String;
Begin
  Result := FormatFloat('0.000', CoordToMMs(C));
End;

Function NombreRed(O : Variant) : String;
Begin
  If O.Net = Nil Then Result := '-' Else Result := O.Net.Name;
End;

{ Geometria de la placa en mm desde el origen: componentes, pads, pistas, arcos y vias }
Procedure Volcar;
Var
  Doc, Board, It, O : Variant;
  L : TStringList;
  X0, Y0 : Integer;
  R : TCoordRect;
  Comp : String;
Begin
  Bitacora := TStringList.Create;
  Log('Volcar ' + DateTimeToStr(Now));
  Doc := AbrirPlaca;
  Board := PCBServer.GetCurrentPCBBoard;
  X0 := Board.XOrigin; Y0 := Board.YOrigin;
  L := TStringList.Create;
  It := Board.BoardIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eComponentObject));
  It.AddFilter_LayerSet(AllLayers);
  It.AddFilter_Method(eProcessAll);
  O := It.FirstPCBObject;
  While O <> Nil Do
  Begin
    R := O.BoundingRectangleNoNameComment;
    L.Add('COMP' + #9 + O.Name.Text + #9 + MM(O.x - X0) + #9 + MM(O.y - Y0) + #9 + FloatToStr(O.Rotation) + #9 + Layer2String(O.Layer) +
          #9 + MM(R.Left - X0) + #9 + MM(R.Bottom - Y0) + #9 + MM(R.Right - X0) + #9 + MM(R.Top - Y0) + #9 + O.Pattern);
    O := It.NextPCBObject;
  End;
  Board.BoardIterator_Destroy(It);
  Log('  componentes ok');
  It := Board.BoardIterator_Create;
  It.AddFilter_ObjectSet(MkSet(ePadObject));
  It.AddFilter_LayerSet(AllLayers);
  It.AddFilter_Method(eProcessAll);
  O := It.FirstPCBObject;
  While O <> Nil Do
  Begin
    If O.Component = Nil Then Comp := '-' Else Comp := O.Component.Name.Text;
    L.Add('PAD' + #9 + Comp + #9 + O.Name + #9 + MM(O.x - X0) + #9 + MM(O.y - Y0) + #9 + NombreRed(O) + #9 + Layer2String(O.Layer) +
          #9 + MM(O.TopXSize) + #9 + MM(O.TopYSize) + #9 + MM(O.HoleSize) + #9 + FloatToStr(O.Rotation));
    O := It.NextPCBObject;
  End;
  Board.BoardIterator_Destroy(It);
  Log('  pads ok');
  It := Board.BoardIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eTrackObject));
  It.AddFilter_LayerSet(AllLayers);
  It.AddFilter_Method(eProcessAll);
  O := It.FirstPCBObject;
  While O <> Nil Do
  Begin
    If Not O.InPolygon Then
      L.Add('TRK' + #9 + Layer2String(O.Layer) + #9 + NombreRed(O) + #9 + MM(O.x1 - X0) + #9 + MM(O.y1 - Y0) + #9 + MM(O.x2 - X0) + #9 + MM(O.y2 - Y0) + #9 + MM(O.Width));
    O := It.NextPCBObject;
  End;
  Board.BoardIterator_Destroy(It);
  Log('  pistas ok');
  It := Board.BoardIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eArcObject));
  It.AddFilter_LayerSet(AllLayers);
  It.AddFilter_Method(eProcessAll);
  O := It.FirstPCBObject;
  While O <> Nil Do
  Begin
    If Not O.InPolygon Then
      L.Add('ARC' + #9 + Layer2String(O.Layer) + #9 + NombreRed(O) + #9 + MM(O.XCenter - X0) + #9 + MM(O.YCenter - Y0) + #9 + MM(O.Radius) + #9 + FloatToStr(O.StartAngle) + #9 + FloatToStr(O.EndAngle) + #9 + MM(O.LineWidth));
    O := It.NextPCBObject;
  End;
  Board.BoardIterator_Destroy(It);
  Log('  arcos ok');
  It := Board.BoardIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eViaObject));
  It.AddFilter_LayerSet(AllLayers);
  It.AddFilter_Method(eProcessAll);
  O := It.FirstPCBObject;
  While O <> Nil Do
  Begin
    L.Add('VIA' + #9 + NombreRed(O) + #9 + MM(O.x - X0) + #9 + MM(O.y - Y0) + #9 + MM(O.Size) + #9 + MM(O.HoleSize));
    O := It.NextPCBObject;
  End;
  Board.BoardIterator_Destroy(It);
  Log('  vias ok');
  L.SaveToFile(RUTA_TMP + 'geometria.tsv');
  Log('  lineas: ' + IntToStr(L.Count));
  L.Free;
  Terminar;
  Bitacora.Free;
End;

{ ---------- Reubicacion: M3 superiores, C3 junto al AP63205 y LDO de sensores entre la IMU y el GNSS ---------- }
Var
  SegN : Integer;
  SegRed : Array[0..99] Of String;
  SegX1, SegY1, SegX2, SegY2 : Array[0..99] Of Double;

Procedure Segmento(Red : String; Xa, Ya, Xb, Yb : Double);
Begin
  SegRed[SegN] := Red; SegX1[SegN] := Xa; SegY1[SegN] := Ya; SegX2[SegN] := Xb; SegY2[SegN] := Yb;
  Inc(SegN);
End;

Function Cerca(A, B : Double) : Boolean;
Begin
  Result := Abs(A - B) < 0.03;
End;

Function BuscarComp(Board : Variant; Des : String) : Variant;
Var
  It, C : Variant;
Begin
  Result := Nil;
  It := Board.BoardIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eComponentObject));
  It.AddFilter_LayerSet(AllLayers);
  It.AddFilter_Method(eProcessAll);
  C := It.FirstPCBObject;
  While C <> Nil Do
  Begin
    If C.Name.Text = Des Then Begin Result := C; Break; End;
    C := It.NextPCBObject;
  End;
  Board.BoardIterator_Destroy(It);
End;

Procedure Mover(Board : Variant; Des : String; X, Y, Rot : Double);
Var
  C : Variant;
Begin
  C := BuscarComp(Board, Des);
  If C = Nil Then Begin Log('  NO ENCONTRADO ' + Des); Exit; End;
  C.BeginModify;
  C.Rotation := Rot;
  C.MoveToXY(Board.XOrigin + MMsToCoord(X), Board.YOrigin + MMsToCoord(Y));
  C.EndModify;
  Log('  movido ' + Des + ' a ' + FormatFloat('0.00', X) + ' ; ' + FormatFloat('0.00', Y) + ' r=' + FloatToStr(Rot));
End;

Procedure Pista(Board, Red : Variant; Xa, Ya, Xb, Yb : Double);
Var
  T : Variant;
Begin
  T := PCBServer.PCBObjectFactory(eTrackObject, eNoDimension, eCreate_Default);
  T.x1 := Board.XOrigin + MMsToCoord(Xa); T.y1 := Board.YOrigin + MMsToCoord(Ya);
  T.x2 := Board.XOrigin + MMsToCoord(Xb); T.y2 := Board.YOrigin + MMsToCoord(Yb);
  T.Width := MMsToCoord(0.6);
  T.Layer := eTopLayer;
  T.Net := Red;
  Board.AddPCBObject(T);
End;

Procedure Reubicar;
Var
  Doc, Board, It, O, Modelo, Nueva, Gnd, VinProt : Variant;
  Borrar : Array[0..299] Of Variant;
  NB, I, J : Integer;
  X0, Y0 : Integer;
  Xa, Ya, Xb, Yb, DX, DY : Double;
  Red : String;
Begin
  Bitacora := TStringList.Create;
  Log('Reubicar ' + DateTimeToStr(Now));
  Doc := AbrirPlaca;
  Board := PCBServer.GetCurrentPCBBoard;
  X0 := Board.XOrigin; Y0 := Board.YOrigin;
  { los pours se guardan para que no estorben; se restauran y repouran al final del ruteo }
  ResetParameters;
  AddStringParameter('ContextObject', 'Polygon');
  AddStringParameter('Action', 'ShelveAllPolygons');
  RunProcess('PCB:ShelvePolygons');
  Log('  polígonos guardados (shelve)');

  { tramos que quedan obsoletos }
  SegN := 0;
  Segmento('VIN_PROT', 16.78, 10.60, 16.78, 12.60);
  Segmento('GND', 18.23, 12.60, 19.20, 12.60);
  Segmento('VIN_PROT', 22.81, 4.76, 22.81, 8.84);
  Segmento('VIN_PROT', 22.10, 9.55, 22.81, 8.84);
  Segmento('VIN_PROT', 22.81, 4.76, 23.15, 4.42);
  Segmento('V_5V', 39.76, 10.50, 40.71, 10.50);
  Segmento('V_5V', 39.57, 10.69, 39.76, 10.50);
  { V3V3_SENS: tramo U3-C11 y tronco de 113 mm hacia el GNSS y la IMU }
  Segmento('V3V3_SENS', 47.12, 11.45, 47.12, 12.83);
  Segmento('V3V3_SENS', 47.12, 12.83, 47.90, 13.61);
  Segmento('V3V3_SENS', 47.90, 13.61, 47.90, 25.75);
  Segmento('V3V3_SENS', 47.90, 25.75, 49.00, 26.85);
  Segmento('V3V3_SENS', 49.00, 26.85, 49.00, 28.73);
  Segmento('V3V3_SENS', 47.12, 11.45, 47.14, 11.45);
  Segmento('V3V3_SENS', 47.14, 11.45, 47.30, 11.45);
  Segmento('V3V3_SENS', 47.30, 11.45, 48.97, 9.78);
  Segmento('V3V3_SENS', 48.97, 9.78, 50.00, 9.78);
  Segmento('V3V3_SENS', 47.60, 28.73, 48.26, 28.73);
  Segmento('V3V3_SENS', 47.12, 29.21, 47.60, 28.73);
  Segmento('V3V3_SENS', 47.12, 29.21, 47.12, 38.20);
  Segmento('V3V3_SENS', 40.01, 45.31, 47.12, 38.20);
  Segmento('V3V3_SENS', 40.01, 45.31, 40.01, 48.17);
  Segmento('V3V3_SENS', 39.69, 48.49, 40.01, 48.17);
  Segmento('V3V3_SENS', 27.94, 48.49, 39.69, 48.49);
  Segmento('V3V3_SENS', 27.56, 48.11, 27.94, 48.49);
  Segmento('V3V3_SENS', 27.56, 43.99, 27.56, 48.11);
  Segmento('V3V3_SENS', 27.23, 43.66, 27.56, 43.99);
  Segmento('V3V3_SENS', 27.23, 39.32, 27.23, 43.66);
  Segmento('V3V3_SENS', 26.01, 38.10, 27.23, 39.32);
  Segmento('V3V3_SENS', 21.09, 38.10, 26.01, 38.10);
  Segmento('V3V3_SENS', 20.78, 37.78, 21.09, 38.10);

  NB := 0;
  Gnd := Nil; VinProt := Nil; Modelo := Nil;
  It := Board.BoardIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eTrackObject));
  It.AddFilter_LayerSet(AllLayers);
  It.AddFilter_Method(eProcessAll);
  O := It.FirstPCBObject;
  While O <> Nil Do
  Begin
    If (O.Net <> Nil) And (Not O.InPolygon) Then
    Begin
      Red := O.Net.Name;
      If (Red = 'VIN_PROT') And (VinProt = Nil) Then VinProt := O.Net;
      Xa := CoordToMMs(O.x1 - X0); Ya := CoordToMMs(O.y1 - Y0); Xb := CoordToMMs(O.x2 - X0); Yb := CoordToMMs(O.y2 - Y0);
      If Red = 'V5_SENS' Then Begin Borrar[NB] := O; Inc(NB); End
      Else
        For J := 0 To SegN - 1 Do
          If (SegRed[J] = Red) And
             ((Cerca(Xa, SegX1[J]) And Cerca(Ya, SegY1[J]) And Cerca(Xb, SegX2[J]) And Cerca(Yb, SegY2[J])) Or
              (Cerca(Xa, SegX2[J]) And Cerca(Ya, SegY2[J]) And Cerca(Xb, SegX1[J]) And Cerca(Yb, SegY1[J]))) Then
          Begin
            Borrar[NB] := O; Inc(NB); Break;
          End;
    End;
    O := It.NextPCBObject;
  End;
  Board.BoardIterator_Destroy(It);
  Log('  pistas a borrar: ' + IntToStr(NB) + ' (lista: ' + IntToStr(SegN) + ' + V5_SENS)');

  { vias: V5_SENS, y GND bajo los separadores nuevos o bajo C11 }
  It := Board.BoardIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eViaObject));
  It.AddFilter_LayerSet(AllLayers);
  It.AddFilter_Method(eProcessAll);
  O := It.FirstPCBObject;
  While O <> Nil Do
  Begin
    If O.Net <> Nil Then
    Begin
      Xa := CoordToMMs(O.x - X0); Ya := CoordToMMs(O.y - Y0);
      If O.Net.Name = 'V5_SENS' Then Begin Borrar[NB] := O; Inc(NB); End;
      If O.Net.Name = 'GND' Then
      Begin
        If Gnd = Nil Then Gnd := O.Net;
        If Cerca(Xa, 23.60) And Cerca(Ya, 5.69) Then Modelo := O;
        If (Sqrt(Sqr(Xa - 3.3) + Sqr(Ya - 38.6)) < 3.6) Or (Sqrt(Sqr(Xa - 66.7) + Sqr(Ya - 38.6)) < 3.6) Or
           (Cerca(Xa, 45.44) And Cerca(Ya, 34.44)) Then Begin Borrar[NB] := O; Inc(NB); End;
      End;
    End;
    O := It.NextPCBObject;
  End;
  Board.BoardIterator_Destroy(It);
  Log('  objetos a borrar en total: ' + IntToStr(NB));

  PCBServer.PreProcess;
  For I := 0 To NB - 1 Do Board.RemovePCBObject(Borrar[I]);
  Log('  borrados');

  Mover(Board, 'H3', 3.3, 38.6, 0);
  Mover(Board, 'H4', 66.7, 38.6, 0);
  Mover(Board, 'C3', 22.5, 7.5, 0);
  Mover(Board, 'U3', 43.0, 34.4, 0);
  Mover(Board, 'C10', 39.6, 34.4, 270);
  Mover(Board, 'FB1', 43.0, 37.6, 0);
  Mover(Board, 'C11', 46.2, 35.0, 270);

  { C3 entre VIN (pin 3) y GND (pin 4) del AP63205, y el ramal de VIN_PROT hacia el divisor sale desde C3 }
  Pista(Board, VinProt, 21.70, 7.50, 21.70, 9.55);
  Pista(Board, VinProt, 21.70, 7.50, 21.70, 4.42);
  Pista(Board, VinProt, 21.70, 4.42, 23.15, 4.42);
  Pista(Board, Gnd, 23.30, 7.50, 23.30, 9.55);
  Pista(Board, Gnd, 23.225, 7.50, 24.50, 7.50);
  If Modelo <> Nil Then
  Begin
    Nueva := Modelo.Replicate;
    Nueva.x := X0 + MMsToCoord(24.50); Nueva.y := Y0 + MMsToCoord(7.50);
    Board.AddPCBObject(Nueva);
    Log('  via GND nueva en 24.5 ; 7.5 (copia de la de 23.6 ; 5.69)');
  End
  Else Log('  sin via modelo: falta la via de GND junto a C3');
  PCBServer.PostProcess;
  GuardarPlaca(Doc);
  Log('  guardada');
  Terminar;
  Bitacora.Free;
End;

{ Situs solo sobre las conexiones de los componentes movidos (y C26 para el lado de la IMU) }
Procedure Autorutear;
Var
  Doc, Board, C : Variant;
  I : Integer;
  Lista : TStringList;
Begin
  Bitacora := TStringList.Create;
  Log('Autorutear ' + DateTimeToStr(Now));
  Doc := AbrirPlaca;
  Board := PCBServer.GetCurrentPCBBoard;
  Lista := TStringList.Create;
  Lista.CommaText := 'U3,FB1,C10,C11,C26';
  For I := 0 To Lista.Count - 1 Do
  Begin
    C := BuscarComp(Board, Lista[I]);
    If C <> Nil Then C.Selected := True;
  End;
  Lista.Free;
  Log('  seleccionados; lanzando Situs');
  ResetParameters;
  AddStringParameter('Action', 'OnSelectedComponents');
  RunProcess('PCB:Autoroute');
  Log('  Situs terminado');
  Terminar;
  Bitacora.Free;
End;

Procedure CerrarPlaca;
Var
  Doc : Variant;
Begin
  Bitacora := TStringList.Create;
  Log('CerrarPlaca ' + DateTimeToStr(Now));
  Doc := Client.GetDocumentByPath(RUTA_BASE + 'altium\ELO301_G1.PcbDoc');
  If Doc <> Nil Then
  Begin
    Log('  modificada=' + BoolToStr(Doc.Modified, True));
    Client.CloseDocument(Doc);
    Log('  cerrada');
  End
  Else Log('  no estaba abierta');
  Terminar;
  Bitacora.Free;
End;

Procedure PistaW(Board, Red : Variant; Xa, Ya, Xb, Yb, W : Double);
Var
  T : Variant;
Begin
  T := PCBServer.PCBObjectFactory(eTrackObject, eNoDimension, eCreate_Default);
  T.x1 := Board.XOrigin + MMsToCoord(Xa); T.y1 := Board.YOrigin + MMsToCoord(Ya);
  T.x2 := Board.XOrigin + MMsToCoord(Xb); T.y2 := Board.YOrigin + MMsToCoord(Yb);
  T.Width := MMsToCoord(W);
  T.Layer := eTopLayer;
  T.Net := Red;
  Board.AddPCBObject(T);
End;

{ Rutas del LDO de sensores (las que Situs habia encontrado, sin sus pasadas sobre el resto de la placa),
  designadores ocultos donde chocan, y pours restaurados y vertidos }
Procedure RutasLDO;
Var
  Doc, Board, V5S, V33, V5, It, P : Variant;
  N : Integer;
Begin
  Bitacora := TStringList.Create;
  Log('RutasLDO ' + DateTimeToStr(Now));
  Doc := AbrirPlaca;
  Board := PCBServer.GetCurrentPCBBoard;
  V5S := BuscarRed(Board, 'V5_SENS'); V33 := BuscarRed(Board, 'V3V3_SENS'); V5 := BuscarRed(Board, 'V_5V');
  Log('  redes: ' + BoolToStr((V5S <> Nil) And (V33 <> Nil) And (V5 <> Nil), True));
  PCBServer.PreProcess;
  { V5_SENS: C10 -> U3 IN/EN -> FB1 }
  PistaW(Board, V5S, 39.60, 35.12, 40.54, 35.12, 0.3);
  PistaW(Board, V5S, 40.54, 35.12, 40.77, 35.35, 0.3);
  PistaW(Board, V5S, 40.77, 35.35, 41.86, 35.35, 0.3);
  PistaW(Board, V5S, 40.87, 33.45, 41.86, 33.45, 0.3);
  PistaW(Board, V5S, 40.87, 33.45, 40.87, 35.35, 0.3);
  PistaW(Board, V5S, 41.86, 35.35, 42.62, 35.35, 0.3);
  PistaW(Board, V5S, 42.62, 35.35, 43.79, 36.52, 0.3);
  PistaW(Board, V5S, 43.79, 36.52, 43.79, 37.60, 0.3);
  { V3V3_SENS: U3 OUT -> C11 -> C24 (GNSS) y rama a la IMU }
  PistaW(Board, V33, 44.14, 35.35, 44.99, 35.35, 0.3);
  PistaW(Board, V33, 44.99, 35.35, 45.37, 35.73, 0.3);
  PistaW(Board, V33, 45.37, 35.73, 46.20, 35.73, 0.3);
  PistaW(Board, V33, 46.20, 35.73, 46.20, 35.77, 0.3);
  PistaW(Board, V33, 46.20, 35.77, 49.00, 35.77, 0.3);
  PistaW(Board, V33, 44.53, 35.35, 44.53, 38.43, 0.3);
  PistaW(Board, V33, 44.53, 38.43, 34.44, 48.51, 0.3);
  PistaW(Board, V33, 34.44, 48.51, 27.94, 48.51, 0.3);
  PistaW(Board, V33, 27.94, 48.51, 27.58, 48.16, 0.3);
  PistaW(Board, V33, 27.58, 48.16, 27.58, 45.85, 0.3);
  PistaW(Board, V33, 27.58, 45.85, 28.70, 44.73, 0.3);
  PistaW(Board, V33, 28.70, 44.73, 28.70, 39.69, 0.3);
  PistaW(Board, V33, 28.70, 39.69, 28.33, 39.32, 0.3);
  PistaW(Board, V33, 28.33, 39.32, 27.53, 39.32, 0.3);
  PistaW(Board, V33, 27.53, 39.32, 27.36, 39.14, 0.3);
  PistaW(Board, V33, 27.36, 39.14, 27.36, 33.12, 0.3);
  PistaW(Board, V33, 27.36, 33.12, 26.99, 32.75, 0.3);
  PistaW(Board, V33, 26.99, 32.75, 23.09, 32.75, 0.3);
  { V_5V: desde la via existente del ramal inferior hasta FB1 }
  PistaW(Board, V5, 39.57, 10.69, 40.28, 11.40, 0.6);
  PistaW(Board, V5, 40.28, 11.40, 47.13, 11.40, 0.6);
  PistaW(Board, V5, 47.13, 11.40, 47.47, 11.75, 0.6);
  PistaW(Board, V5, 47.47, 11.75, 47.47, 27.41, 0.6);
  PistaW(Board, V5, 47.47, 27.41, 47.14, 27.74, 0.6);
  PistaW(Board, V5, 47.14, 27.74, 47.14, 32.08, 0.6);
  PistaW(Board, V5, 47.14, 32.08, 47.02, 32.21, 0.6);
  PistaW(Board, V5, 47.02, 32.21, 39.05, 32.21, 0.6);
  PistaW(Board, V5, 39.05, 32.21, 38.66, 32.60, 0.6);
  PistaW(Board, V5, 38.66, 32.60, 38.66, 37.21, 0.6);
  PistaW(Board, V5, 38.66, 37.21, 39.05, 37.60, 0.6);
  PistaW(Board, V5, 39.05, 37.60, 42.21, 37.60, 0.6);
  Log('  pistas agregadas');
  BuscarComp(Board, 'H3').NameOn := False;
  BuscarComp(Board, 'H4').NameOn := False;
  BuscarComp(Board, 'C10').NameOn := False;
  BuscarComp(Board, 'C11').NameOn := False;
  BuscarComp(Board, 'FB1').NameOn := False;
  BuscarComp(Board, 'U3').NameOn := False;
  Log('  designadores ocultos: H3 H4 C10 C11 FB1 U3');
  PCBServer.PostProcess;
  ResetParameters;
  RunProcess('PCB:ShelvePolygons');
  N := 0;
  It := Board.BoardIterator_Create;
  It.AddFilter_ObjectSet(MkSet(ePolyObject));
  It.AddFilter_LayerSet(AllLayers);
  It.AddFilter_Method(eProcessAll);
  P := It.FirstPCBObject;
  While P <> Nil Do
  Begin
    P.Rebuild;
    Inc(N);
    P := It.NextPCBObject;
  End;
  Board.BoardIterator_Destroy(It);
  Log('  polígonos restaurados y vertidos: ' + IntToStr(N));
  GuardarPlaca(Doc);
  Log('  guardada');
  Terminar;
  Bitacora.Free;
End;

{ Correcciones tras el DRC: GND de C10/U3 con vias propias (V5_SENS reordenado) y holgura con R12 }
Procedure AjustesLDO;
Var
  Doc, Board, It, O, V5S, Gnd, Modelo, Nueva, P : Variant;
  Borrar : Array[0..49] Of Variant;
  NB, I, X0, Y0 : Integer;
  Xa, Ya : Double;
Begin
  Bitacora := TStringList.Create;
  Log('AjustesLDO ' + DateTimeToStr(Now));
  Doc := AbrirPlaca;
  Board := PCBServer.GetCurrentPCBBoard;
  X0 := Board.XOrigin; Y0 := Board.YOrigin;
  V5S := BuscarRed(Board, 'V5_SENS'); Gnd := BuscarRed(Board, 'GND');
  NB := 0; Modelo := Nil;
  PCBServer.PreProcess;
  It := Board.BoardIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eTrackObject, eViaObject));
  It.AddFilter_LayerSet(AllLayers);
  It.AddFilter_Method(eProcessAll);
  O := It.FirstPCBObject;
  While O <> Nil Do
  Begin
    If O.Net <> Nil Then
    Begin
      If (O.ObjectId = eTrackObject) And (O.Net.Name = 'V5_SENS') Then Begin Borrar[NB] := O; Inc(NB); End;
      If (O.ObjectId = eViaObject) And (O.Net.Name = 'GND') And (Modelo = Nil) Then Modelo := O;
      { rama a la IMU: el tramo vertical de x = 28,70 pasa a 0,149 mm de R12-2 }
      If (O.ObjectId = eTrackObject) And (O.Net.Name = 'V3V3_SENS') Then
      Begin
        O.BeginModify;
        If Cerca(CoordToMMs(O.x1 - X0), 28.70) Then O.x1 := X0 + MMsToCoord(28.76);
        If Cerca(CoordToMMs(O.x2 - X0), 28.70) Then O.x2 := X0 + MMsToCoord(28.76);
        O.EndModify;
      End;
    End;
    O := It.NextPCBObject;
  End;
  Board.BoardIterator_Destroy(It);
  For I := 0 To NB - 1 Do Board.RemovePCBObject(Borrar[I]);
  Log('  pistas V5_SENS borradas: ' + IntToStr(NB));
  Mover(Board, 'C10', 39.6, 34.4, 90);
  { V5_SENS: EN y C10-1 abajo, IN unido por la izquierda, IN -> FB1 }
  PistaW(Board, V5S, 39.60, 33.45, 41.86, 33.45, 0.3);
  PistaW(Board, V5S, 40.87, 33.45, 40.87, 35.35, 0.3);
  PistaW(Board, V5S, 40.87, 35.35, 41.86, 35.35, 0.3);
  PistaW(Board, V5S, 41.86, 35.35, 42.62, 35.35, 0.3);
  PistaW(Board, V5S, 42.62, 35.35, 43.79, 36.52, 0.3);
  PistaW(Board, V5S, 43.79, 36.52, 43.79, 37.60, 0.3);
  { GND al plano: C10-2 arriba y U3-2 bajo el cuerpo }
  PistaW(Board, Gnd, 39.60, 35.125, 39.60, 36.25, 0.3);
  PistaW(Board, Gnd, 41.86, 34.40, 43.00, 34.40, 0.3);
  Nueva := Modelo.Replicate; Nueva.x := X0 + MMsToCoord(39.60); Nueva.y := Y0 + MMsToCoord(36.25); Board.AddPCBObject(Nueva);
  Nueva := Modelo.Replicate; Nueva.x := X0 + MMsToCoord(43.00); Nueva.y := Y0 + MMsToCoord(34.40); Board.AddPCBObject(Nueva);
  Log('  V5_SENS reordenado y 2 vias de GND');
  PCBServer.PostProcess;
  It := Board.BoardIterator_Create;
  It.AddFilter_ObjectSet(MkSet(ePolyObject));
  It.AddFilter_LayerSet(AllLayers);
  It.AddFilter_Method(eProcessAll);
  P := It.FirstPCBObject;
  While P <> Nil Do Begin P.Rebuild; P := It.NextPCBObject; End;
  Board.BoardIterator_Destroy(It);
  Log('  repour');
  GuardarPlaca(Doc);
  Log('  guardada');
  Terminar;
  Bitacora.Free;
End;

{ Restaura los pours guardados por Reubicar, los vierte de nuevo y guarda }
Procedure Repour;
Var
  Doc, Board : Variant;
Begin
  Bitacora := TStringList.Create;
  Log('Repour ' + DateTimeToStr(Now));
  Doc := AbrirPlaca;
  Board := PCBServer.GetCurrentPCBBoard;
  ResetParameters;
  RunProcess('PCB:ShelvePolygons');
  Log('  restaurados');
  ResetParameters;
  AddStringParameter('Action', 'RepourAllPolygons');
  RunProcess('PCB:ChangeObject');
  Log('  vertidos');
  GuardarPlaca(Doc);
  Log('  guardada');
  Terminar;
  Bitacora.Free;
End;

{ H3 y H4 en 04_Conectores, copiando H2 desde su biblioteca (perforaciones M3 de la mitad superior) }
Procedure AgregarPerforaciones;
Var
  Doc, Hoja, It, O, H2, Nueva : Variant;
  Ruta, Lib : String;
  I : Integer;
Begin
  Bitacora := TStringList.Create;
  Log('AgregarPerforaciones ' + DateTimeToStr(Now));
  Ruta := RUTA_BASE + 'altium\04_Conectores.SchDoc';
  Lib := RUTA_BASE + 'altium\MOUNTING HOLE - M3.SchLib';
  Doc := Client.OpenDocument('SCH', Ruta);
  Client.ShowDocument(Doc);
  Hoja := SchServer.GetSchDocumentByPath(Ruta);
  H2 := Nil;
  It := Hoja.SchIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eSchComponent));
  O := It.FirstSchObject;
  While O <> Nil Do
  Begin
    If O.Designator.Text = 'H2' Then H2 := O;
    If (O.Designator.Text = 'H3') Or (O.Designator.Text = 'H4') Then Begin Log('  ya existe ' + O.Designator.Text); Hoja.SchIterator_Destroy(It); Terminar; Bitacora.Free; Exit; End;
    O := It.NextSchObject;
  End;
  Hoja.SchIterator_Destroy(It);
  Log('  H2 en ' + IntToStr(CoordToMils(H2.Location.X)) + ',' + IntToStr(CoordToMils(H2.Location.Y)) + ' mil');
  SchServer.ProcessControl.PreProcess(Hoja, '');
  For I := 3 To 4 Do
  Begin
    Nueva := SchServer.LoadComponentFromLibrary('MOUNTING HOLE - M3', Lib);
    Log('  cargado desde biblioteca: ' + BoolToStr(Nueva <> Nil, True));
    Nueva.Designator.Text := 'H' + IntToStr(I);
    Nueva.MoveToXY(H2.Location.X + MilsToCoord(500 * (I - 2)), H2.Location.Y);
    Nueva.SourceLibraryName := 'MOUNTING HOLE - M3.SchLib';
    Nueva.ComponentDescription := 'Mounting Hole without connection, M3';
    Hoja.AddSchObject(Nueva);
    Log('  agregado H' + IntToStr(I));
  End;
  { la nota de la hoja nombra las perforaciones }
  It := Hoja.SchIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eLabel));
  O := It.FirstSchObject;
  While O <> Nil Do
  Begin
    If Pos('H1, H2', O.Text) = 1 Then Begin O.Text := 'H1-H4: perforaciones M3 con separadores (H3/H4 fijan el borde de los FOC)'; Log('  nota actualizada'); End;
    O := It.NextSchObject;
  End;
  Hoja.SchIterator_Destroy(It);
  SchServer.ProcessControl.PostProcess(Hoja, '');
  Hoja.GraphicallyInvalidate;
  Doc.Modified := True;
  ResetParameters;
  AddStringParameter('ObjectKind', 'Document');
  RunProcess('WorkspaceManager:SaveObject');
  Log('  hoja guardada');
  Terminar;
  Bitacora.Free;
End;

{ Los objetos agregados por script sin registrarlos quedan en el archivo pero el compilador no los ve:
  se cierra la hoja para que el proyecto la vuelva a leer del disco }
Procedure RecargarHoja04;
Var
  Doc : Variant;
Begin
  Bitacora := TStringList.Create;
  Log('RecargarHoja04 ' + DateTimeToStr(Now));
  Doc := Client.GetDocumentByPath(RUTA_BASE + 'altium\04_Conectores.SchDoc');
  If Doc <> Nil Then
  Begin
    Log('  modificada=' + BoolToStr(Doc.Modified, True));
    Client.CloseDocument(Doc);
    Log('  cerrada');
  End;
  Terminar;
  Bitacora.Free;
End;

Procedure ReabrirHoja04;
Var
  Doc, Hoja, It, O : Variant;
  N : Integer;
Begin
  Bitacora := TStringList.Create;
  Log('ReabrirHoja04 ' + DateTimeToStr(Now));
  Doc := Client.OpenDocument('SCH', RUTA_BASE + 'altium\04_Conectores.SchDoc');
  Client.ShowDocument(Doc);
  Hoja := SchServer.GetSchDocumentByPath(RUTA_BASE + 'altium\04_Conectores.SchDoc');
  N := 0;
  It := Hoja.SchIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eSchComponent));
  O := It.FirstSchObject;
  While O <> Nil Do Begin Inc(N); O := It.NextSchObject; End;
  Hoja.SchIterator_Destroy(It);
  Log('  componentes en la hoja abierta: ' + IntToStr(N));
  Doc.Modified := True;
  ResetParameters;
  AddStringParameter('ObjectKind', 'Document');
  RunProcess('WorkspaceManager:SaveObject');
  Log('  guardada');
  Terminar;
  Bitacora.Free;
End;

Procedure DiagnosticoH;
Var
  Hoja, It, O, It2, Imp, Prj, Fl, C : Variant;
  I, N : Integer;
  S : String;
Begin
  Bitacora := TStringList.Create;
  Log('DiagnosticoH ' + DateTimeToStr(Now));
  Hoja := SchServer.GetSchDocumentByPath(RUTA_BASE + 'altium\04_Conectores.SchDoc');
  Log('  hoja en memoria: ' + BoolToStr(Hoja <> Nil, True));
  If Hoja <> Nil Then
  Begin
  It := Hoja.SchIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eSchComponent));
  O := It.FirstSchObject;
  While O <> Nil Do
  Begin
    If Copy(O.Designator.Text, 1, 1) = 'H' Then
    Begin
      N := 0; S := '';
      It2 := O.SchIterator_Create;
      It2.AddFilter_ObjectSet(MkSet(eImplementation));
      Imp := It2.FirstSchObject;
      While Imp <> Nil Do Begin Inc(N); S := S + Imp.ModelName + '/' + Imp.ModelType + ' '; Imp := It2.NextSchObject; End;
      O.SchIterator_Destroy(It2);
      Log('  ' + O.Designator.Text + ' kind=' + IntToStr(O.ComponentKind) + ' modelos=' + IntToStr(N) + ' ' + S);
    End;
    O := It.NextSchObject;
  End;
  Hoja.SchIterator_Destroy(It);
  End;
  Prj := GetWorkspace.DM_OpenProject(RUTA_BASE + 'altium\ELO301_G1.PrjPcb', True);
  Prj.DM_Compile;
  Fl := Prj.DM_DocumentFlattened;
  S := '';
  For I := 0 To Fl.DM_ComponentCount - 1 Do
  Begin
    C := Fl.DM_Components(I);
    If Copy(C.DM_PhysicalDesignator, 1, 1) = 'H' Then S := S + C.DM_PhysicalDesignator + ' ';
  End;
  Log('  compilado: ' + IntToStr(Fl.DM_ComponentCount) + ' componentes; H: ' + S);
  Terminar;
  Bitacora.Free;
End;

{ DRC completo: si Altium muestra el dialogo, se pulsa "Run Design Rule Check" desde afuera }
Procedure DRC;
Var
  Doc, Board, It, V : Variant;
  N : Integer;
Begin
  Bitacora := TStringList.Create;
  Log('DRC ' + DateTimeToStr(Now));
  Doc := AbrirPlaca;
  Board := PCBServer.GetCurrentPCBBoard;
  ResetParameters;
  AddStringParameter('Action', 'Run');
  RunProcess('PCB:DesignRuleCheck');
  Log('  DRC ejecutado');
  N := 0;
  It := Board.BoardIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eViolationObject));
  It.AddFilter_LayerSet(AllLayers);
  It.AddFilter_Method(eProcessAll);
  V := It.FirstPCBObject;
  While V <> Nil Do
  Begin
    Inc(N);
    If N <= 60 Then Log('  ' + V.Name + ' | ' + V.Description);
    V := It.NextPCBObject;
  End;
  Board.BoardIterator_Destroy(It);
  Log('  violaciones: ' + IntToStr(N));
  Terminar;
  Bitacora.Free;
End;

Procedure PistaCapa(Board, Red : Variant; Xa, Ya, Xb, Yb, W : Double; Capa : Integer);
Var
  T : Variant;
Begin
  T := PCBServer.PCBObjectFactory(eTrackObject, eNoDimension, eCreate_Default);
  T.x1 := Board.XOrigin + MMsToCoord(Xa); T.y1 := Board.YOrigin + MMsToCoord(Ya);
  T.x2 := Board.XOrigin + MMsToCoord(Xb); T.y2 := Board.YOrigin + MMsToCoord(Yb);
  T.Width := MMsToCoord(W);
  T.Layer := Capa;
  T.Net := Red;
  Board.AddPCBObject(T);
End;

{ Extremo (Xv, Yv) de una pista llevado a (Xn, Yn) }
Procedure MoverExtremo(Board, T : Variant; Xv, Yv, Xn, Yn : Double);
Begin
  T.BeginModify;
  If Cerca(CoordToMMs(T.x1 - Board.XOrigin), Xv) And Cerca(CoordToMMs(T.y1 - Board.YOrigin), Yv) Then
  Begin T.x1 := Board.XOrigin + MMsToCoord(Xn); T.y1 := Board.YOrigin + MMsToCoord(Yn); End
  Else
  Begin T.x2 := Board.XOrigin + MMsToCoord(Xn); T.y2 := Board.YOrigin + MMsToCoord(Yn); End;
  T.EndModify;
End;

Function TieneExtremo(Board, T : Variant; X, Y : Double) : Boolean;
Begin
  Result := (Cerca(CoordToMMs(T.x1 - Board.XOrigin), X) And Cerca(CoordToMMs(T.y1 - Board.YOrigin), Y)) Or
            (Cerca(CoordToMMs(T.x2 - Board.XOrigin), X) And Cerca(CoordToMMs(T.y2 - Board.YOrigin), Y));
End;

{ J9 (UART de depuracion) 1,45 mm a la derecha: su courtyard quedaba 1,33 mm dentro de la zona del tornillo de H1
  (radio 3,45 mm). Las pistas de Bottom que llegan a sus pads se ajustan a la nueva posicion. }
Procedure MoverJ9;
Var
  Doc, Board, It, T, V33, Rx : Variant;
  Borrar : Array[0..9] Of Variant;
  NB, I, NV, NT, NR : Integer;
  Red : String;
Begin
  Bitacora := TStringList.Create;
  Log('MoverJ9 ' + DateTimeToStr(Now));
  Doc := AbrirPlaca;
  Board := PCBServer.GetCurrentPCBBoard;
  V33 := BuscarRed(Board, 'V3V3_MCU'); Rx := BuscarRed(Board, 'UART_DBG_RX');
  NB := 0; NV := 0; NT := 0; NR := 0;
  PCBServer.PreProcess;
  Mover(Board, 'J9', 8.943, 3.556, 90);
  It := Board.BoardIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eTrackObject));
  It.AddFilter_LayerSet(MkSet(eBottomLayer));
  It.AddFilter_Method(eProcessAll);
  T := It.FirstPCBObject;
  While T <> Nil Do
  Begin
    If T.Net <> Nil Then
    Begin
      Red := T.Net.Name;
      If (Red = 'V3V3_MCU') And TieneExtremo(Board, T, 7.493, 3.556) And TieneExtremo(Board, T, 7.493, 21.031) Then
      Begin MoverExtremo(Board, T, 7.493, 3.556, 7.493, 5.006); Inc(NV); End;
      If (Red = 'UART_DBG_TX') And TieneExtremo(Board, T, 10.033, 3.556) Then
      Begin MoverExtremo(Board, T, 10.033, 3.556, 11.483, 3.556); Inc(NT); End;
      If (Red = 'UART_DBG_RX') And (TieneExtremo(Board, T, 12.573, 3.556) Or (TieneExtremo(Board, T, 12.739, 3.722) And TieneExtremo(Board, T, 13.723, 3.722))) Then
      Begin Borrar[NB] := T; Inc(NB); End;
      If (Red = 'UART_DBG_RX') And TieneExtremo(Board, T, 13.723, 3.722) And TieneExtremo(Board, T, 14.657, 4.656) Then
      Begin MoverExtremo(Board, T, 13.723, 3.722, 14.023, 4.022); Inc(NR); End;
    End;
    T := It.NextPCBObject;
  End;
  Board.BoardIterator_Destroy(It);
  For I := 0 To NB - 1 Do Board.RemovePCBObject(Borrar[I]);
  PistaCapa(Board, V33, 8.943, 3.556, 7.493, 5.006, 0.3, eBottomLayer);
  PistaCapa(Board, Rx, 14.023, 3.556, 14.023, 4.022, 0.2, eBottomLayer);
  Log('  V3V3_MCU ajustada: ' + IntToStr(NV) + '; TX: ' + IntToStr(NT) + '; RX borradas: ' + IntToStr(NB) + ', ajustada: ' + IntToStr(NR));
  PCBServer.PostProcess;
  It := Board.BoardIterator_Create;
  It.AddFilter_ObjectSet(MkSet(ePolyObject));
  It.AddFilter_LayerSet(AllLayers);
  It.AddFilter_Method(eProcessAll);
  T := It.FirstPCBObject;
  While T <> Nil Do Begin T.Rebuild; T := It.NextPCBObject; End;
  Board.BoardIterator_Destroy(It);
  Log('  repour');
  GuardarPlaca(Doc);
  Log('  guardada');
  Terminar;
  Bitacora.Free;
End;

{ La diagonal de VIN_12V en Top (D1-2 -> J1-1) pasaba sobre el nuevo lugar de J9-4: se rehace por fuera del J9,
  horizontal hasta x = 17,5, 45 grados y bajada vertical a J1-1. }
Procedure RutaVin12J9;
Var
  Doc, Board, It, T, Red, Viejo : Variant;
  W : Double;
Begin
  Bitacora := TStringList.Create;
  Log('RutaVin12J9 ' + DateTimeToStr(Now));
  Doc := AbrirPlaca;
  Board := PCBServer.GetCurrentPCBBoard;
  Viejo := Nil;
  It := Board.BoardIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eTrackObject));
  It.AddFilter_LayerSet(MkSet(eTopLayer));
  It.AddFilter_Method(eProcessAll);
  T := It.FirstPCBObject;
  While T <> Nil Do
  Begin
    If (T.Net <> Nil) And TieneExtremo(Board, T, 14.681, 6.411) And TieneExtremo(Board, T, 18.491, 2.601) Then Viejo := T;
    T := It.NextPCBObject;
  End;
  Board.BoardIterator_Destroy(It);
  If Viejo = Nil Then Begin Log('  NO ENCONTRADA'); Terminar; Bitacora.Free; Exit; End;
  Red := Viejo.Net; W := CoordToMMs(Viejo.Width);
  Log('  red ' + Red.Name + ', ancho ' + FormatFloat('0.000', W));
  PCBServer.PreProcess;
  Board.RemovePCBObject(Viejo);
  PistaCapa(Board, Red, 14.681, 6.411, 17.5, 6.411, W, eTopLayer);
  PistaCapa(Board, Red, 17.5, 6.411, 18.491, 5.420, W, eTopLayer);
  PistaCapa(Board, Red, 18.491, 5.420, 18.491, 2.601, W, eTopLayer);
  PCBServer.PostProcess;
  It := Board.BoardIterator_Create;
  It.AddFilter_ObjectSet(MkSet(ePolyObject));
  It.AddFilter_LayerSet(AllLayers);
  It.AddFilter_Method(eProcessAll);
  T := It.FirstPCBObject;
  While T <> Nil Do Begin T.Rebuild; T := It.NextPCBObject; End;
  Board.BoardIterator_Destroy(It);
  Log('  rehecha y repour');
  GuardarPlaca(Doc);
  Log('  guardada');
  Terminar;
  Bitacora.Free;
End;

{ ---------- Serigrafia sobre los minimos de JLCPCB (linea 0,15 mm, texto 1,0 mm, pad a serigrafia 0,15 mm) ----------
  seda_plan.tsv (generado fuera de Altium) trae, por cada linea de serigrafia: capa, extremos originales y los tramos que
  quedan al ensancharla a 0,18 mm y alejarla 0,2 mm del cobre de los pads. Unidades de 0,1 um (enteros). }
Var
  SPN : Integer;
  SCapa, SX1, SY1, SX2, SY2, SN, SIni, SUsado : Array[0..599] Of Integer;
  QX1, QY1, QX2, QY2 : Array[0..1199] Of Integer;

Procedure CargarPlanSeda(Archivo : String);
Var
  L, F : TStringList;
  I, J, Q : Integer;
Begin
  L := TStringList.Create;
  L.LoadFromFile(RUTA_TMP + Archivo);
  F := TStringList.Create;
  F.Delimiter := #9;
  SPN := 0; Q := 0;
  For I := 0 To L.Count - 1 Do
    If L[I] <> '' Then
    Begin
      F.DelimitedText := L[I];
      SCapa[SPN] := StrToInt(F[0]);
      SX1[SPN] := StrToInt(F[1]); SY1[SPN] := StrToInt(F[2]); SX2[SPN] := StrToInt(F[3]); SY2[SPN] := StrToInt(F[4]);
      SN[SPN] := StrToInt(F[5]); SIni[SPN] := Q; SUsado[SPN] := 0;
      For J := 0 To SN[SPN] - 1 Do
      Begin
        QX1[Q] := StrToInt(F[6 + 4 * J]); QY1[Q] := StrToInt(F[7 + 4 * J]);
        QX2[Q] := StrToInt(F[8 + 4 * J]); QY2[Q] := StrToInt(F[9 + 4 * J]);
        Inc(Q);
      End;
      Inc(SPN);
    End;
  L.Free; F.Free;
  Log('  plan: ' + IntToStr(SPN) + ' lineas, ' + IntToStr(Q) + ' tramos');
End;

Function Igual(A, B : Integer) : Boolean;
Begin
  Result := Abs(A - B) <= 30;
End;

Function BuscarPlan(Capa, X1, Y1, X2, Y2 : Integer) : Integer;
Var
  K : Integer;
Begin
  Result := -1;
  For K := 0 To SPN - 1 Do
    If (SUsado[K] = 0) And (SCapa[K] = Capa) Then
      If (Igual(SX1[K], X1) And Igual(SY1[K], Y1) And Igual(SX2[K], X2) And Igual(SY2[K], Y2)) Or
         (Igual(SX1[K], X2) And Igual(SY1[K], Y2) And Igual(SX2[K], X1) And Igual(SY2[K], Y1)) Then
      Begin
        SUsado[K] := 1;
        Result := K;
        Break;
      End;
End;

Function U2C(V : Integer) : Integer;
Begin
  Result := MMsToCoord(V / 10000);
End;

Function C2U(C : Integer) : Integer;
Begin
  Result := Round(CoordToMMs(C) * 10000);
End;

{ Aplica seda_plan.tsv a la placa: ancho 0,18 mm, recortes, tramos extra (dentro del mismo componente) y lineas eliminadas }
Procedure SerigrafiaPlaca;
Var
  Doc, Board, It, T, N, Comp : Variant;
  Lista : Array[0..599] Of Variant;
  NL, I, J, K, Q, Capa, X0, Y0, NIntactas, NRecortadas, NNuevas, NBorradas, NSin : Integer;
Begin
  Bitacora := TStringList.Create;
  Log('SerigrafiaPlaca ' + DateTimeToStr(Now));
  CargarPlanSeda('seda_plan.tsv');
  Doc := AbrirPlaca;
  Board := PCBServer.GetCurrentPCBBoard;
  X0 := Board.XOrigin; Y0 := Board.YOrigin;
  NL := 0;
  It := Board.BoardIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eTrackObject));
  It.AddFilter_LayerSet(MkSet(eTopOverlay, eBottomOverlay));
  It.AddFilter_Method(eProcessAll);
  T := It.FirstPCBObject;
  While T <> Nil Do Begin Lista[NL] := T; Inc(NL); T := It.NextPCBObject; End;
  Board.BoardIterator_Destroy(It);
  Log('  lineas de serigrafia en la placa: ' + IntToStr(NL));
  NIntactas := 0; NRecortadas := 0; NNuevas := 0; NBorradas := 0; NSin := 0;
  PCBServer.PreProcess;
  For I := 0 To NL - 1 Do
  Begin
    T := Lista[I];
    If T.Layer = eTopOverlay Then Capa := 33 Else Capa := 34;
    K := BuscarPlan(Capa, C2U(T.x1 - X0), C2U(T.y1 - Y0), C2U(T.x2 - X0), C2U(T.y2 - Y0));
    Comp := T.Component;
    If K < 0 Then
    Begin
      Inc(NSin);
      Log('  sin plan: ' + MM(T.x1 - X0) + ',' + MM(T.y1 - Y0) + ' ' + MM(T.x2 - X0) + ',' + MM(T.y2 - Y0));
      T.BeginModify; T.Width := MMsToCoord(0.18); T.EndModify;
    End
    Else If SN[K] = 0 Then
    Begin
      If Comp <> Nil Then Begin Comp.BeginModify; Comp.RemovePCBObject(T); Comp.EndModify; End;
      Board.RemovePCBObject(T);
      Inc(NBorradas);
    End
    Else
    Begin
      Q := SIni[K];
      If Igual(QX1[Q], SX1[K]) And Igual(QY1[Q], SY1[K]) And Igual(QX2[Q], SX2[K]) And Igual(QY2[Q], SY2[K]) And (SN[K] = 1) Then
        Inc(NIntactas)
      Else
        Inc(NRecortadas);
      T.BeginModify;
      T.x1 := X0 + U2C(QX1[Q]); T.y1 := Y0 + U2C(QY1[Q]);
      T.x2 := X0 + U2C(QX2[Q]); T.y2 := Y0 + U2C(QY2[Q]);
      T.Width := MMsToCoord(0.18);
      T.EndModify;
      For J := 1 To SN[K] - 1 Do
      Begin
        Q := SIni[K] + J;
        N := PCBServer.PCBObjectFactory(eTrackObject, eNoDimension, eCreate_Default);
        N.x1 := X0 + U2C(QX1[Q]); N.y1 := Y0 + U2C(QY1[Q]);
        N.x2 := X0 + U2C(QX2[Q]); N.y2 := Y0 + U2C(QY2[Q]);
        N.Width := MMsToCoord(0.18);
        N.Layer := T.Layer;
        Board.AddPCBObject(N);
        If Comp <> Nil Then Begin Comp.BeginModify; Comp.AddPCBObject(N); Comp.EndModify; End;
        Inc(NNuevas);
      End;
    End;
  End;
  PCBServer.PostProcess;
  Log('  intactas (solo ancho): ' + IntToStr(NIntactas) + '; recortadas: ' + IntToStr(NRecortadas) + '; tramos nuevos: ' +
      IntToStr(NNuevas) + '; eliminadas: ' + IntToStr(NBorradas) + '; sin plan: ' + IntToStr(NSin));
  GuardarPlaca(Doc);
  Log('  guardada');
  Terminar;
  Bitacora.Free;
End;

{ Designadores a 1,2 mm de alto con trazo de 0,2 mm (proporcion 1:6) y la identificacion de la cara inferior;
  vuelca el rectangulo de cada designador para ubicarlos fuera de Altium (designadores.tsv) }
Procedure DesignadoresTamano;
Var
  Doc, Board, It, C, T : Variant;
  L : TStringList;
  R : TCoordRect;
  X0, Y0 : Integer;
  Vis : String;
Begin
  Bitacora := TStringList.Create;
  Log('DesignadoresTamano ' + DateTimeToStr(Now));
  Doc := AbrirPlaca;
  Board := PCBServer.GetCurrentPCBBoard;
  X0 := Board.XOrigin; Y0 := Board.YOrigin;
  L := TStringList.Create;
  PCBServer.PreProcess;
  It := Board.BoardIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eComponentObject));
  It.AddFilter_LayerSet(AllLayers);
  It.AddFilter_Method(eProcessAll);
  C := It.FirstPCBObject;
  While C <> Nil Do
  Begin
    C.Name.BeginModify;
    C.Name.Size := MMsToCoord(1.2);
    C.Name.Width := MMsToCoord(0.2);
    C.Name.EndModify;
    C.Name.GraphicallyInvalidate;
    R := C.Name.BoundingRectangle;
    If C.NameOn Then Vis := '1' Else Vis := '0';
    L.Add(C.Name.Text + #9 + Layer2String(C.Layer) + #9 + Vis + #9 + FloatToStr(C.Name.Rotation) + #9 +
          IntToStr(C2U(R.Left - X0)) + #9 + IntToStr(C2U(R.Bottom - Y0)) + #9 + IntToStr(C2U(R.Right - X0)) + #9 + IntToStr(C2U(R.Top - Y0)));
    C := It.NextPCBObject;
  End;
  Board.BoardIterator_Destroy(It);
  { identificacion en la serigrafia inferior }
  It := Board.BoardIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eTextObject));
  It.AddFilter_LayerSet(MkSet(eBottomOverlay));
  It.AddFilter_Method(eProcessAll);
  T := It.FirstPCBObject;
  While T <> Nil Do
  Begin
    If Pos('ELO301', T.Text) = 1 Then
    Begin
      T.BeginModify;
      T.Text := 'ELO301 G1 v1.2 2026-11';
      T.Size := MMsToCoord(1.2);
      T.Width := MMsToCoord(0.2);
      T.EndModify;
      T.GraphicallyInvalidate;
      R := T.BoundingRectangle;
      L.Add('ID' + #9 + 'BottomLayer' + #9 + '1' + #9 + FloatToStr(T.Rotation) + #9 +
            IntToStr(C2U(R.Left - X0)) + #9 + IntToStr(C2U(R.Bottom - Y0)) + #9 + IntToStr(C2U(R.Right - X0)) + #9 + IntToStr(C2U(R.Top - Y0)));
      Log('  identificacion: ' + T.Text);
    End;
    T := It.NextPCBObject;
  End;
  Board.BoardIterator_Destroy(It);
  PCBServer.PostProcess;
  L.SaveToFile(RUTA_TMP + 'designadores.tsv');
  Log('  designadores: ' + IntToStr(L.Count));
  L.Free;
  GuardarPlaca(Doc);
  Log('  guardada');
  Terminar;
  Bitacora.Free;
End;

{ Ubica los designadores segun designadores_plan.tsv: designador, visible (0/1), rotacion y centro deseado del texto
  (0,1 um). Se gira el texto y despues se desplaza para que el centro de su rectangulo caiga en el punto pedido. }
Procedure DesignadoresUbicar;
Var
  Doc, Board, C, T : Variant;
  L, F, Salida : TStringList;
  R : TCoordRect;
  I, J, X0, Y0, DX, DY, N, NVis : Integer;
Begin
  Bitacora := TStringList.Create;
  Log('DesignadoresUbicar ' + DateTimeToStr(Now));
  Doc := AbrirPlaca;
  Board := PCBServer.GetCurrentPCBBoard;
  X0 := Board.XOrigin; Y0 := Board.YOrigin;
  L := TStringList.Create; L.LoadFromFile(RUTA_TMP + 'designadores_plan.tsv');
  F := TStringList.Create; F.Delimiter := #9;
  Salida := TStringList.Create;
  N := 0; NVis := 0;
  PCBServer.PreProcess;
  For I := 0 To L.Count - 1 Do
    If L[I] <> '' Then
    Begin
      F.DelimitedText := L[I];
      If F[0] = 'ID' Then
      Begin
        T := Nil;
      End
      Else
      Begin
        C := BuscarComp(Board, F[0]);
        If C = Nil Then Log('  NO ENCONTRADO ' + F[0])
        Else
        Begin
          C.BeginModify;
          C.ChangeNameAutoposition(eAutoPos_Manual);
          C.NameOn := F[1] = '1';
          C.EndModify;
          C.Name.BeginModify;
          C.Name.Rotation := StrToInt(F[2]);
          C.Name.EndModify;
          C.Name.GraphicallyInvalidate;
          { dos pasadas: la segunda corrige lo que el giro haya dejado sin actualizar en el rectangulo }
          For J := 1 To 2 Do
          Begin
            R := C.Name.BoundingRectangle;
            DX := X0 + U2C(StrToInt(F[3])) - (R.Left + R.Right) Div 2;
            DY := Y0 + U2C(StrToInt(F[4])) - (R.Bottom + R.Top) Div 2;
            C.Name.BeginModify;
            C.Name.MoveByXY(DX, DY);
            C.Name.EndModify;
            C.Name.GraphicallyInvalidate;
          End;
          R := C.Name.BoundingRectangle;
          Salida.Add(F[0] + #9 + F[1] + #9 + IntToStr(C2U(R.Left - X0)) + #9 + IntToStr(C2U(R.Bottom - Y0)) + #9 +
                     IntToStr(C2U(R.Right - X0)) + #9 + IntToStr(C2U(R.Top - Y0)));
          Inc(N);
          If F[1] = '1' Then Inc(NVis);
        End;
      End;
    End;
  PCBServer.PostProcess;
  Salida.SaveToFile(RUTA_TMP + 'designadores_resultado.tsv');
  Log('  ubicados: ' + IntToStr(N) + '; visibles: ' + IntToStr(NVis));
  L.Free; F.Free; Salida.Free;
  GuardarPlaca(Doc);
  Log('  guardada');
  Terminar;
  Bitacora.Free;
End;

{ ---------- La misma serigrafia en las bibliotecas de huellas (para que un Update From PCB Libraries no la revierta) ----------
  La API da en el marco de la placa solo la huella abierta en el editor; las demas aparecen desplazadas por el origen de
  la biblioteca (50000 mil). Por eso cada huella se abre (SetState_CurrentComponent) antes de leerla o cambiarla, y los
  tramos nuevos se agregan con Lib.Board.AddPCBObject, que los deja en la huella abierta. }
Function RutaBibHuellas(I : Integer) : String;
Begin
  Case I Of
    0 : Result := RUTA_BASE + 'altium\ELO301_G1.PcbLib';
    1 : Result := RUTA_BASE + 'altium\C0603 - MURATA.PcbLib';
    2 : Result := RUTA_BASE + 'altium\R0603 - YAGEO.PcbLib';
  End;
End;

Function AbrirBibHuellas(I : Integer) : Variant;
Var
  Doc : Variant;
Begin
  Doc := Client.OpenDocument('PCBLIB', RutaBibHuellas(I));
  Client.ShowDocument(Doc);
  Result := Doc;
End;

Procedure CerrarBibHuellas;
Var
  Doc : Variant;
  I : Integer;
Begin
  Bitacora := TStringList.Create;
  Log('CerrarBibHuellas ' + DateTimeToStr(Now));
  For I := 0 To 2 Do
  Begin
    Doc := Client.GetDocumentByPath(RutaBibHuellas(I));
    If Doc <> Nil Then
    Begin
      Log('  ' + RutaBibHuellas(I) + ' modificada=' + BoolToStr(Doc.Modified, True));
      Client.CloseDocument(Doc);
    End;
  End;
  Terminar;
  Bitacora.Free;
End;

Var
  HFp : Array[0..39] Of Variant;
  HN : Integer;

{ Huellas de la biblioteca abierta, en el orden del iterador }
Procedure ListarHuellas(Lib : Variant);
Var
  It, Fp : Variant;
Begin
  HN := 0;
  It := Lib.LibraryIterator_Create;
  It.SetState_FilterAll;
  Fp := It.FirstPCBObject;
  While Fp <> Nil Do Begin HFp[HN] := Fp; Inc(HN); Fp := It.NextPCBObject; End;
  Lib.LibraryIterator_Destroy(It);
End;

{ Vuelca pads y serigrafia de cada huella (coordenadas desde el origen de la biblioteca, en 0,1 um) a huellas.tsv }
Procedure VolcarHuellas;
Var
  Doc, Lib, Fp, GIt, P : Variant;
  L : TStringList;
  I, K, X0, Y0 : Integer;
Begin
  Bitacora := TStringList.Create;
  Log('VolcarHuellas ' + DateTimeToStr(Now));
  L := TStringList.Create;
  For I := 0 To 2 Do
  Begin
    Doc := AbrirBibHuellas(I);
    Lib := PCBServer.GetCurrentPCBLibrary;
    X0 := Lib.Board.XOrigin; Y0 := Lib.Board.YOrigin;
    ListarHuellas(Lib);
    For K := 0 To HN - 1 Do
    Begin
      Fp := HFp[K];
      Lib.SetState_CurrentComponent(Fp);
      L.Add('FP' + #9 + IntToStr(I) + #9 + Fp.Name);
      GIt := Fp.GroupIterator_Create;
      GIt.AddFilter_ObjectSet(MkSet(ePadObject, eTrackObject, eArcObject));
      P := GIt.FirstPCBObject;
      While P <> Nil Do
      Begin
        If P.ObjectId = ePadObject Then
          L.Add('PAD' + #9 + IntToStr(C2U(P.x - X0)) + #9 + IntToStr(C2U(P.y - Y0)) + #9 + IntToStr(C2U(P.TopXSize)) + #9 +
                IntToStr(C2U(P.TopYSize)) + #9 + IntToStr(P.TopShape) + #9 + IntToStr(Round(P.Rotation * 1000)) + #9 +
                IntToStr(C2U(P.HoleSize)) + #9 + IntToStr(P.Layer))
        Else If P.ObjectId = eTrackObject Then
          L.Add('TRK' + #9 + IntToStr(P.Layer) + #9 + IntToStr(C2U(P.x1 - X0)) + #9 + IntToStr(C2U(P.y1 - Y0)) + #9 +
                IntToStr(C2U(P.x2 - X0)) + #9 + IntToStr(C2U(P.y2 - Y0)) + #9 + IntToStr(C2U(P.Width)))
        Else If (P.Layer = eTopOverlay) Or (P.Layer = eBottomOverlay) Then
          L.Add('ARC' + #9 + IntToStr(P.Layer) + #9 + IntToStr(C2U(P.LineWidth)));
        P := GIt.NextPCBObject;
      End;
      Fp.GroupIterator_Destroy(GIt);
    End;
    Log('  ' + RutaBibHuellas(I) + ': ' + IntToStr(HN) + ' huellas');
  End;
  L.SaveToFile(RUTA_TMP + 'huellas.tsv');
  L.Free;
  Terminar;
  Bitacora.Free;
End;

{ huellas_plan.tsv: biblioteca, indice de huella (orden del iterador), capa, extremos, numero de tramos y tramos }
Var
  SLib, SFp : Array[0..599] Of Integer;

Procedure CargarPlanHuellas;
Var
  L, F : TStringList;
  I, J, Q : Integer;
Begin
  L := TStringList.Create;
  L.LoadFromFile(RUTA_TMP + 'huellas_plan.tsv');
  F := TStringList.Create;
  F.Delimiter := #9;
  SPN := 0; Q := 0;
  For I := 0 To L.Count - 1 Do
    If L[I] <> '' Then
    Begin
      F.DelimitedText := L[I];
      SLib[SPN] := StrToInt(F[0]); SFp[SPN] := StrToInt(F[1]); SCapa[SPN] := StrToInt(F[2]);
      SX1[SPN] := StrToInt(F[3]); SY1[SPN] := StrToInt(F[4]); SX2[SPN] := StrToInt(F[5]); SY2[SPN] := StrToInt(F[6]);
      SN[SPN] := StrToInt(F[7]); SIni[SPN] := Q; SUsado[SPN] := 0;
      For J := 0 To SN[SPN] - 1 Do
      Begin
        QX1[Q] := StrToInt(F[8 + 4 * J]); QY1[Q] := StrToInt(F[9 + 4 * J]);
        QX2[Q] := StrToInt(F[10 + 4 * J]); QY2[Q] := StrToInt(F[11 + 4 * J]);
        Inc(Q);
      End;
      Inc(SPN);
    End;
  L.Free; F.Free;
  Log('  plan: ' + IntToStr(SPN) + ' lineas, ' + IntToStr(Q) + ' tramos');
End;

Function BuscarPlanHuella(Lib, Fp, Capa, X1, Y1, X2, Y2 : Integer) : Integer;
Var
  K : Integer;
Begin
  Result := -1;
  For K := 0 To SPN - 1 Do
    If (SUsado[K] = 0) And (SLib[K] = Lib) And (SFp[K] = Fp) And (SCapa[K] = Capa) Then
      If (Igual(SX1[K], X1) And Igual(SY1[K], Y1) And Igual(SX2[K], X2) And Igual(SY2[K], Y2)) Or
         (Igual(SX1[K], X2) And Igual(SY1[K], Y2) And Igual(SX2[K], X1) And Igual(SY2[K], Y1)) Then
      Begin
        SUsado[K] := 1;
        Result := K;
        Break;
      End;
End;

{ Aplica huellas_plan.tsv a las tres bibliotecas de huellas y las guarda }
Procedure AplicarHuellas;
Var
  Doc, Lib, Fp, GIt, T, N : Variant;
  Lista : Array[0..199] Of Variant;
  I, F, NL, K, J, Q, Capa, X0, Y0, NMod, NNuevas, NBorradas, NSin : Integer;
Begin
  Bitacora := TStringList.Create;
  Log('AplicarHuellas ' + DateTimeToStr(Now));
  CargarPlanHuellas;
  For I := 0 To 2 Do
  Begin
    Doc := AbrirBibHuellas(I);
    Lib := PCBServer.GetCurrentPCBLibrary;
    X0 := Lib.Board.XOrigin; Y0 := Lib.Board.YOrigin;
    NMod := 0; NNuevas := 0; NBorradas := 0; NSin := 0;
    ListarHuellas(Lib);
    For F := 0 To HN - 1 Do
    Begin
      Fp := HFp[F];
      Lib.SetState_CurrentComponent(Fp);
      NL := 0;
      GIt := Fp.GroupIterator_Create;
      GIt.AddFilter_ObjectSet(MkSet(eTrackObject));
      T := GIt.FirstPCBObject;
      While T <> Nil Do
      Begin
        If (T.Layer = eTopOverlay) Or (T.Layer = eBottomOverlay) Then Begin Lista[NL] := T; Inc(NL); End;
        T := GIt.NextPCBObject;
      End;
      Fp.GroupIterator_Destroy(GIt);
      For J := 0 To NL - 1 Do
      Begin
        T := Lista[J];
        If T.Layer = eTopOverlay Then Capa := 33 Else Capa := 34;
        K := BuscarPlanHuella(I, F, Capa, C2U(T.x1 - X0), C2U(T.y1 - Y0), C2U(T.x2 - X0), C2U(T.y2 - Y0));
        If K < 0 Then
        Begin
          Inc(NSin);
          Log('    sin plan en ' + Fp.Name + ': ' + MM(T.x1 - X0) + ',' + MM(T.y1 - Y0));
          T.BeginModify; T.Width := MMsToCoord(0.18); T.EndModify;
        End
        Else If SN[K] = 0 Then
          { en una biblioteca RemovePCBObject no saca la linea de la huella: la borra BorrarSedaHuellas }
          Inc(NBorradas)
        Else
        Begin
          Q := SIni[K];
          T.BeginModify;
          T.x1 := X0 + U2C(QX1[Q]); T.y1 := Y0 + U2C(QY1[Q]);
          T.x2 := X0 + U2C(QX2[Q]); T.y2 := Y0 + U2C(QY2[Q]);
          T.Width := MMsToCoord(0.18);
          T.EndModify;
          Inc(NMod);
          For Q := SIni[K] + 1 To SIni[K] + SN[K] - 1 Do
          Begin
            N := PCBServer.PCBObjectFactory(eTrackObject, eNoDimension, eCreate_Default);
            N.x1 := X0 + U2C(QX1[Q]); N.y1 := Y0 + U2C(QY1[Q]);
            N.x2 := X0 + U2C(QX2[Q]); N.y2 := Y0 + U2C(QY2[Q]);
            N.Width := MMsToCoord(0.18);
            N.Layer := T.Layer;
            Lib.Board.AddPCBObject(N);
            Inc(NNuevas);
          End;
        End;
      End;
    End;
    Log('  ' + RutaBibHuellas(I) + ': ' + IntToStr(HN) + ' huellas; lineas ajustadas ' + IntToStr(NMod) + ', nuevas ' + IntToStr(NNuevas) +
        ', por borrar (BorrarSedaHuellas) ' + IntToStr(NBorradas) + ', sin plan ' + IntToStr(NSin));
    Doc.Modified := True;
    Client.ShowDocument(Doc);
    ResetParameters;
    AddStringParameter('ObjectKind', 'Document');
    RunProcess('WorkspaceManager:SaveObject');
    Log('  guardada');
  End;
  Terminar;
  Bitacora.Free;
End;

{ Borra de las huellas las lineas que el plan elimina (las que AplicarHuellas no pudo quitar: en una biblioteca
  RemovePCBObject no las saca de la huella). Se seleccionan en la huella abierta y se borran con Edit > Clear. }
Procedure BorrarSedaHuellas;
Var
  Doc, Lib, Fp, GIt, T : Variant;
  I, F, K, X0, Y0, NSel, NTot, NQueda : Integer;
Begin
  Bitacora := TStringList.Create;
  Log('BorrarSedaHuellas ' + DateTimeToStr(Now));
  CargarPlanHuellas;
  For I := 0 To 2 Do
  Begin
    Doc := AbrirBibHuellas(I);
    Lib := PCBServer.GetCurrentPCBLibrary;
    X0 := Lib.Board.XOrigin; Y0 := Lib.Board.YOrigin;
    ListarHuellas(Lib);
    NTot := 0; NQueda := 0;
    For F := 0 To HN - 1 Do
    Begin
      Fp := HFp[F];
      Lib.SetState_CurrentComponent(Fp);
      ResetParameters;
      AddStringParameter('Scope', 'All');
      RunProcess('PCB:DeSelect');
      NSel := 0;
      GIt := Fp.GroupIterator_Create;
      GIt.AddFilter_ObjectSet(MkSet(eTrackObject));
      T := GIt.FirstPCBObject;
      While T <> Nil Do
      Begin
        If (T.Layer = eTopOverlay) Or (T.Layer = eBottomOverlay) Then
        Begin
          If T.Layer = eTopOverlay Then K := 33 Else K := 34;
          K := BuscarPlanHuella(I, F, K, C2U(T.x1 - X0), C2U(T.y1 - Y0), C2U(T.x2 - X0), C2U(T.y2 - Y0));
          If (K >= 0) And (SN[K] = 0) Then Begin T.Selected := True; Inc(NSel); End;
        End;
        T := GIt.NextPCBObject;
      End;
      Fp.GroupIterator_Destroy(GIt);
      If NSel > 0 Then
      Begin
        ResetParameters;
        RunProcess('PCB:Clear');
        { cuantas lineas de serigrafia quedan en la huella }
        K := 0;
        GIt := Fp.GroupIterator_Create;
        GIt.AddFilter_ObjectSet(MkSet(eTrackObject));
        T := GIt.FirstPCBObject;
        While T <> Nil Do Begin If (T.Layer = eTopOverlay) Or (T.Layer = eBottomOverlay) Then Inc(K); T := GIt.NextPCBObject; End;
        Fp.GroupIterator_Destroy(GIt);
        Log('    ' + Fp.Name + ': seleccionadas ' + IntToStr(NSel) + ', quedan ' + IntToStr(K) + ' lineas de serigrafia');
        NTot := NTot + NSel;
      End;
    End;
    If NTot > 0 Then
    Begin
      Doc.Modified := True;
      Client.ShowDocument(Doc);
      ResetParameters;
      AddStringParameter('ObjectKind', 'Document');
      RunProcess('WorkspaceManager:SaveObject');
      Log('  ' + RutaBibHuellas(I) + ': borradas ' + IntToStr(NTot) + ', guardada');
    End;
  End;
  Terminar;
  Bitacora.Free;
End;

Procedure ImportarCambios;
Var
  Prj : Variant;
Begin
  Bitacora := TStringList.Create;
  Log('ImportarCambios ' + DateTimeToStr(Now));
  Prj := GetWorkspace.DM_OpenProject(RUTA_BASE + 'altium\ELO301_G1.PrjPcb', True);
  Prj.DM_Compile;
  Log('  compilado: ' + IntToStr(Prj.DM_DocumentFlattened.DM_ComponentCount) + ' componentes');
  AbrirPlaca;
  Log('  placa abierta; abriendo ECO');
  ResetParameters;
  AddStringParameter('ObjectKind', 'Project');
  AddStringParameter('Action', 'UpdateMe');
  RunProcess('WorkspaceManager:Compare');
  Log('  ECO cerrado');
  Terminar;
  Bitacora.Free;
End;
