{ Cambios de la placa ELO301_G1 desde Altium. Se ejecuta con correr.ps1 -Script Placa -Proc <procedimiento>.
    - ImportarCambios: Design > Import Changes (ECO) desde el proyecto; el dialogo ECO queda abierto.
    - ClasesDeRed: repone las clases Potencia y Alimentacion que usan las reglas Ancho_*.
    - PourCapa3: polígono de GND en Senal-Potencia con el mismo contorno que los de Top y Bottom. }

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
