{ Simbolos con metadatos de DigiKey para el proyecto ELO301_G1.
  Lee metadatos_digikey.tsv (UTF-8 con BOM, una fila por linea del BOM) y:
    - CrearBibliotecas: deja en cada <TIPO> - <MPN>.SchLib solo su simbolo (copiado de ELO301_G1.SchLib),
      con nombre, designador, descripcion y parametros de DigiKey; corrige los pines del STM32.
    - ActualizarEsquematico: enlaza cada componente de las 4 hojas a su nueva biblioteca y le escribe
      los mismos parametros (los pasivos genericos reciben los suyos aqui, no en la biblioteca).
    - Compilar: compila el proyecto y lista las violaciones.
  Se ejecuta con X2.EXE -RScriptingSystem:RunScript(ProjectName="...\Simbolos.PrjScr"|ProcName="Simbolos.pas>...") }

Const
  RUTA_BASE = 'C:\Users\Estudiante USM\Desktop\resBot\ELO301_Modulo_Control_Secundario\';
  { log y marca fuera del repo: la carpeta del repo la vigilan otros programas y bloquean el archivo }
  RUTA_TMP = 'C:\Users\ESTUDI~1\AppData\Local\Temp\altium_simbolos\';
  RUTA_LOG = 'C:\Users\ESTUDI~1\AppData\Local\Temp\altium_simbolos\log.txt';

Var
  Bitacora : TStringList;
  Filas : TStringList;

Procedure Log(S : String);
Begin
  Bitacora.Add(S);
  Bitacora.SaveToFile(RUTA_LOG);
End;

{ Marca el final con un archivo aparte: quien espera solo comprueba que exista y nunca abre el log
  mientras Altium lo escribe (un archivo bloqueado detiene el script en el depurador). }
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

Function Campo(Linea : String; Idx : Integer) : String;
Var
  I, N, P : Integer;
  Resto : String;
Begin
  Result := '';
  Resto := Linea;
  N := 0;
  While True Do
  Begin
    P := Pos(#9, Resto);
    If N = Idx Then
    Begin
      If P = 0 Then Result := Resto Else Result := Copy(Resto, 1, P - 1);
      Exit;
    End;
    If P = 0 Then Exit;
    Resto := Copy(Resto, P + 1, Length(Resto));
    Inc(N);
  End;
End;

{ Columnas del TSV }
Const
  C_ID = 0; C_DES = 1; C_TIPO = 2; C_LIBREF = 3; C_LIBFILE = 4; C_PREFIJO = 5; C_ORIGEN = 6;
  C_COMENTARIO = 7; C_DESCR = 8; C_FAB = 9; C_MPN = 10; C_SUP1 = 11; C_SPN1 = 12; C_SUP2 = 13;
  C_SPN2 = 14; C_CATEG = 15; C_PKG = 16; C_SDP = 17; C_TEMP = 18; C_CICLO = 19; C_HOJA = 20;
  C_URL = 21; C_EXTRA = 22;

Procedure CargarFilas;
Begin
  Filas := TStringList.Create;
  Filas.LoadFromFile(RUTA_BASE + 'generadores\digikey\metadatos_digikey.tsv');
  Filas.Delete(0);
End;

Function FilaDe(Des : String) : String;
Var
  I : Integer;
Begin
  Result := '';
  For I := 0 To Filas.Count - 1 Do
    If Pos(',' + Des + ',', ',' + Campo(Filas[I], C_DES) + ',') > 0 Then
    Begin
      Result := Filas[I];
      Exit;
    End;
End;

Function BuscarParametro(Comp : Variant; Nombre : String) : Variant;
Var
  It, P : Variant;
Begin
  Result := Nil;
  It := Comp.SchIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eParameter));
  P := It.FirstSchObject;
  While P <> Nil Do
  Begin
    If UpperCase(P.Name) = UpperCase(Nombre) Then
    Begin
      Result := P;
      Break;
    End;
    P := It.NextSchObject;
  End;
  Comp.SchIterator_Destroy(It);
End;

Procedure PonerParametro(Comp : Variant; Nombre, Valor : String);
Var
  P : Variant;
Begin
  If Valor = '' Then Exit;
  P := BuscarParametro(Comp, Nombre);
  If P = Nil Then
  Begin
    P := SchServer.SchObjectFactory(eParameter, eCreate_Default);
    P.Name := Nombre;
    P.IsHidden := True;
    P.Location := Comp.Location;
    P.Text := Valor;
    Comp.AddSchObject(P);
  End
  Else
    P.Text := Valor;
End;

Procedure QuitarParametro(Comp : Variant; Nombre : String);
Var
  P : Variant;
Begin
  P := BuscarParametro(Comp, Nombre);
  If P <> Nil Then Comp.RemoveSchObject(P);
End;

Procedure AplicarMetadatos(Comp : Variant; Fila : String);
Var
  Extra, Par : String;
  P, Q : Integer;
Begin
  Comp.ComponentDescription := Campo(Fila, C_DESCR);
  PonerParametro(Comp, 'Description', Campo(Fila, C_DESCR));
  PonerParametro(Comp, 'Manufacturer', Campo(Fila, C_FAB));
  PonerParametro(Comp, 'Manufacturer Part Number', Campo(Fila, C_MPN));
  PonerParametro(Comp, 'Supplier 1', Campo(Fila, C_SUP1));
  PonerParametro(Comp, 'Supplier Part Number 1', Campo(Fila, C_SPN1));
  PonerParametro(Comp, 'Supplier 2', Campo(Fila, C_SUP2));
  PonerParametro(Comp, 'Supplier Part Number 2', Campo(Fila, C_SPN2));
  PonerParametro(Comp, 'Category', Campo(Fila, C_CATEG));
  PonerParametro(Comp, 'Case/Package', Campo(Fila, C_PKG));
  PonerParametro(Comp, 'Supplier Device Package', Campo(Fila, C_SDP));
  PonerParametro(Comp, 'Operating Temperature', Campo(Fila, C_TEMP));
  PonerParametro(Comp, 'Lifecycle Status', Campo(Fila, C_CICLO));
  If Campo(Fila, C_HOJA) <> '' Then
  Begin
    PonerParametro(Comp, 'ComponentLink1Description', 'Datasheet');
    PonerParametro(Comp, 'ComponentLink1URL', Campo(Fila, C_HOJA));
  End;
  If Campo(Fila, C_URL) <> '' Then
  Begin
    PonerParametro(Comp, 'ComponentLink2Description', Campo(Fila, C_SUP1));
    PonerParametro(Comp, 'ComponentLink2URL', Campo(Fila, C_URL));
  End;
  { Extra: Nombre=Valor;Nombre=Valor }
  Extra := Campo(Fila, C_EXTRA);
  While Extra <> '' Do
  Begin
    P := Pos(';', Extra);
    If P = 0 Then Begin Par := Extra; Extra := ''; End
    Else Begin Par := Copy(Extra, 1, P - 1); Extra := Copy(Extra, P + 1, Length(Extra)); End;
    Q := Pos('=', Par);
    If Q > 0 Then PonerParametro(Comp, Trim(Copy(Par, 1, Q - 1)), Trim(Copy(Par, Q + 1, Length(Par))));
  End;
  QuitarParametro(Comp, 'LCSC Part #');
End;

{ Nombres de ST (STM32_open_pin_data) para los pines con funcion alternativa fija, y VSS como alimentacion }
Procedure CorregirPinesSTM32(Comp : Variant);
Var
  It, Pin : Variant;
  D : String;
Begin
  It := Comp.SchIterator_Create;
  It.AddFilter_ObjectSet(MkSet(ePin));
  Pin := It.FirstSchObject;
  While Pin <> Nil Do
  Begin
    D := Pin.Designator;
    If D = '3' Then Pin.Name := 'PC14-OSC32_IN';
    If D = '4' Then Pin.Name := 'PC15-OSC32_OUT';
    If D = '5' Then Pin.Name := 'PF0-OSC_IN';
    If D = '6' Then Pin.Name := 'PF1-OSC_OUT';
    If D = '7' Then Pin.Name := 'PG10-NRST';
    If D = '45' Then Pin.Name := 'PB8-BOOT0';
    If (D = '35') Or (D = '47') Then Pin.Electrical := eElectricPower;
    Pin := It.NextSchObject;
  End;
  Comp.SchIterator_Destroy(It);
End;

Function EsGenericaProfe(LibFile : String) : Boolean;
Begin
  Result := (LibFile = 'CAP - GENERIC.SchLib') Or (LibFile = 'RESISTOR - GENERIC.SchLib') Or
            (LibFile = 'INDUCTOR - GENERIC.SchLib') Or (LibFile = 'DIODE - GENERIC.SchLib');
End;

{ Huella de ELO301_G1.PcbLib que ya usa cada simbolo en el esquematico }
Function Huella(LibRef : String) : String;
Begin
  Result := '';
  If (LibRef = 'B240A-13-F') Or (LibRef = 'SMAJ15A-13-F') Then Result := 'SMA - DIODES';
  If LibRef = 'BOOMELE 2.54-1x14' Then Result := 'HDR 1x14 2.54 - BOOMELE';
  If LibRef = 'BOOMELE 2.54-1x05' Then Result := 'HDR 1x05 2.54 - BOOMELE';
  If LibRef = 'B5B-XH-A(LF)(SN)' Then Result := 'B5B-XH-A - JST';
  If LibRef = 'B4B-XH-A(LF)(SN)' Then Result := 'B4B-XH-A - JST';
  If LibRef = 'U.FL-R-SMT-1(10)' Then Result := 'U.FL - HIROSE';
  If LibRef = 'PTS810 SJM 250 SMTR LFS' Then Result := 'PTS810 - CK';
  If LibRef = 'AP63205WU-7' Then Result := 'TSOT-23-6 - DIODES';
  If LibRef = 'TLV75533PDBVR' Then Result := 'SOT-23-5 - TI';
  If LibRef = 'STM32G431CBT6' Then Result := 'LQFP-48 - ST';
  If LibRef = 'BMI270' Then Result := 'LGA-14 2.5x3.0 - BOSCH';
  If LibRef = 'ATGM336H-5N31' Then Result := 'LCC-18 9.7x10.1 - ZKW';
  If LibRef = 'ABM8-25.000MHZ-10-D1G-T' Then Result := 'ABM8 - ABRACON';
  If LibRef = 'LED - GENERIC' Then Result := 'LED0603 - LITEON';
  If LibRef = 'FERRITE - GENERIC' Then Result := 'L0603 - GENERIC';
  If LibRef = 'MOUNTING HOLE - M3' Then Result := 'M3 - HOLE';
End;

Procedure AgregarHuella(Comp : Variant; Nombre : String);
Var
  It, Impl : Variant;
  Ya : Boolean;
Begin
  If Nombre = '' Then Exit;
  Ya := False;
  It := Comp.SchIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eImplementation));
  Impl := It.FirstSchObject;
  While Impl <> Nil Do
  Begin
    If (Impl.ModelType = 'PCBLIB') And (Impl.ModelName = Nombre) Then Ya := True;
    Impl := It.NextSchObject;
  End;
  Comp.SchIterator_Destroy(It);
  If Ya Then Exit;
  Impl := Comp.AddSchImplementation;
  Impl.ModelName := Nombre;
  Impl.ModelType := 'PCBLIB';
  Impl.Description := 'Huella ' + Nombre;
  Impl.IsCurrent := True;
  Impl.AddDataFileLink(Nombre, 'ELO301_G1.PcbLib', 'PCBLib');
End;

Function ContarSimbolos(Lib : Variant) : Integer;
Var
  It, Comp : Variant;
Begin
  Result := 0;
  It := Lib.SchLibIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eSchComponent));
  Comp := It.FirstSchObject;
  While (Comp <> Nil) And (Result < 100) Do
  Begin
    Inc(Result);
    Comp := It.NextSchObject;
  End;
  Lib.SchIterator_Destroy(It);
End;

Procedure PrepararBiblioteca(Fila : String);
Var
  Ruta, Origen, Victima : String;
  Doc, Lib, It, Comp, Borrar : Variant;
  Hay : Boolean;
  N : Integer;
Begin
  Ruta := RUTA_BASE + 'altium\' + Campo(Fila, C_LIBFILE);
  Origen := Campo(Fila, C_ORIGEN);
  Log('  abriendo ' + Ruta);
  Doc := Client.OpenDocument('SCHLIB', Ruta);
  Client.ShowDocument(Doc);
  Lib := SchServer.GetSchDocumentByPath(Ruta);
  If Lib = Nil Then Begin Log('  ERROR: no abre ' + Ruta); Exit; End;
  Log('  abierta, simbolos: ' + IntToStr(ContarSimbolos(Lib)));
  { deja solo el simbolo de origen (con tope, por si la API no borra) }
  N := 0;
  Repeat
    Hay := False;
    It := Lib.SchLibIterator_Create;
    It.AddFilter_ObjectSet(MkSet(eSchComponent));
    Comp := It.FirstSchObject;
    While Comp <> Nil Do
    Begin
      If (Comp.LibReference <> Origen) And (Comp.LibReference <> Campo(Fila, C_LIBREF)) Then
      Begin
        Borrar := Comp; Hay := True; Break;
      End;
      Comp := It.NextSchObject;
    End;
    Lib.SchIterator_Destroy(It);
    If Hay Then
    Begin
      Victima := Borrar.LibReference;
      Lib.RemoveSchComponent(Borrar);
      Inc(N);
      Log('    borrado ' + Victima + ', quedan ' + IntToStr(ContarSimbolos(Lib)));
    End;
  Until (Not Hay) Or (N > 20);
  If N > 20 Then Begin Log('  ERROR: RemoveSchComponent no borra'); Exit; End;
  It := Lib.SchLibIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eSchComponent));
  Comp := It.FirstSchObject;
  Lib.SchIterator_Destroy(It);
  If Comp = Nil Then Begin Log('  ERROR: no quedo el simbolo ' + Origen); Exit; End;
  SchServer.ProcessControl.PreProcess(Lib, '');
  Comp.LibReference := Campo(Fila, C_LIBREF);
  Comp.Designator.Text := Campo(Fila, C_PREFIJO) + '?';
  If Campo(Fila, C_TIPO) = 'PARTE' Then
  Begin
    PonerParametro(Comp, 'Comment', Campo(Fila, C_COMENTARIO));
    AplicarMetadatos(Comp, Fila);
  End
  Else
    Comp.ComponentDescription := Campo(Fila, C_LIBREF);
  If Campo(Fila, C_LIBREF) = 'STM32G431CBT6' Then CorregirPinesSTM32(Comp);
  AgregarHuella(Comp, Huella(Campo(Fila, C_LIBREF)));
  SchServer.ProcessControl.PostProcess(Lib, '');
  Lib.GraphicallyInvalidate;
  Doc.DoFileSave('SCHLIB');
  Client.CloseDocument(Doc);
  Log('  ok ' + Campo(Fila, C_LIBFILE) + ' <- ' + Origen + ' (' + Comp.LibReference + ', ' + Comp.Designator.Text + ')');
End;

Procedure CrearBibliotecasFiltro(SoloEsta : String);
Var
  I : Integer;
  Hechas : TStringList;
  LibFile : String;
Begin
  Bitacora := TStringList.Create;
  Log('CrearBibliotecas ' + DateTimeToStr(Now));
  Hechas := TStringList.Create;
  Try
    CargarFilas;
    Log('filas: ' + IntToStr(Filas.Count));
    For I := 0 To Filas.Count - 1 Do
    Begin
      LibFile := Campo(Filas[I], C_LIBFILE);
      If (LibFile <> '') And (Not EsGenericaProfe(LibFile)) And (Hechas.IndexOf(LibFile) < 0) Then
      Begin
        Hechas.Add(LibFile);
        If (SoloEsta = '') Or (SoloEsta = LibFile) Then
        Try
          PrepararBiblioteca(Filas[I]);
        Except
          Log('  EXCEPCION en ' + LibFile);
        End;
      End;
    End;
  Except
    Log('EXCEPCION general');
  End;
  Terminar;
  Bitacora.Free;
End;

Procedure CrearBibliotecas;
Begin
  CrearBibliotecasFiltro('');
End;

Procedure ProbarDiodo;
Begin
  CrearBibliotecasFiltro('DIODE - B240A-13-F.SchLib');
End;

Procedure ActualizarHoja(Ruta : String);
Var
  Doc, Hoja, It, Comp : Variant;
  Fila, Des : String;
  N : Integer;
Begin
  Doc := Client.OpenDocument('SCH', Ruta);
  Client.ShowDocument(Doc);
  Hoja := SchServer.GetSchDocumentByPath(Ruta);
  If Hoja = Nil Then Begin Log('  ERROR: no abre ' + Ruta); Exit; End;
  SchServer.ProcessControl.PreProcess(Hoja, '');
  N := 0;
  It := Hoja.SchIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eSchComponent));
  Comp := It.FirstSchObject;
  While Comp <> Nil Do
  Begin
    Des := Comp.Designator.Text;
    Fila := FilaDe(Des);
    If Fila = '' Then
      Log('  SIN FILA: ' + Des)
    Else
    Begin
      Comp.LibReference := Campo(Fila, C_LIBREF);
      Comp.DesignItemId := Campo(Fila, C_LIBREF);
      Comp.SourceLibraryName := Campo(Fila, C_LIBFILE);
      If Campo(Fila, C_MPN) <> '' Then AplicarMetadatos(Comp, Fila)
      Else Comp.ComponentDescription := Campo(Fila, C_DESCR);
      If Des = 'U4' Then CorregirPinesSTM32(Comp);
      Inc(N);
    End;
    Comp := It.NextSchObject;
  End;
  Hoja.SchIterator_Destroy(It);
  SchServer.ProcessControl.PostProcess(Hoja, '');
  Hoja.GraphicallyInvalidate;
  { cambiar parametros por API no marca el documento, y DoFileSave('SCH') no escribe la hoja:
    se marca como modificada y se guarda con el mismo proceso de File > Save }
  Doc.Modified := True;
  Client.ShowDocument(Doc);
  ResetParameters;
  AddStringParameter('ObjectKind', 'Document');
  RunProcess('WorkspaceManager:SaveObject');
  Log('  guardado: modificado=' + BoolToStr(Doc.Modified, True));
  Client.CloseDocument(Doc);
  Log('  ok ' + Ruta + ': ' + IntToStr(N) + ' componentes');
End;

Procedure ActualizarEsquematico;
Begin
  Bitacora := TStringList.Create;
  Log('ActualizarEsquematico ' + DateTimeToStr(Now));
  Try
    CargarFilas;
    ActualizarHoja(RUTA_BASE + 'altium\01_Alimentacion.SchDoc');
    ActualizarHoja(RUTA_BASE + 'altium\02_MCU.SchDoc');
    ActualizarHoja(RUTA_BASE + 'altium\03_Sensores.SchDoc');
    ActualizarHoja(RUTA_BASE + 'altium\04_Conectores.SchDoc');
  Except
    Log('EXCEPCION');
  End;
  Terminar;
  Bitacora.Free;
End;

{ Netlist aplanada (red: designador-pin ...) de un proyecto, para comparar antes y despues }
Procedure VolcarRed(RutaPrj, RutaSalida : String);
Var
  Ws, Prj, Fl, Net, Pin : Variant;
  I, J : Integer;
  L : TStringList;
  S : String;
Begin
  Ws := GetWorkspace;
  Prj := Ws.DM_OpenProject(RutaPrj, True);
  Prj.DM_Compile;
  Fl := Prj.DM_DocumentFlattened;
  Log('  componentes: ' + IntToStr(Fl.DM_ComponentCount) + ', redes: ' + IntToStr(Fl.DM_NetCount));
  L := TStringList.Create;
  For I := 0 To Fl.DM_NetCount - 1 Do
  Begin
    Net := Fl.DM_Nets(I);
    S := Net.DM_NetName + ':';
    For J := 0 To Net.DM_PinCount - 1 Do
    Begin
      Pin := Net.DM_Pins(J);
      S := S + ' ' + Pin.DM_PhysicalPartDesignator + '-' + Pin.DM_PinNumber;
    End;
    L.Add(S);
  End;
  L.SaveToFile(RutaSalida);
  L.Free;
End;

Procedure CompararRedes;
Begin
  Bitacora := TStringList.Create;
  Log('CompararRedes ' + DateTimeToStr(Now));
  Log(' actual:');
  VolcarRed(RUTA_BASE + 'altium\ELO301_G1.PrjPcb', RUTA_TMP + 'red_actual.txt');
  Log(' anterior (HEAD):');
  VolcarRed(RUTA_TMP + 'anterior\ELO301_Modulo_Control_Secundario\altium\ELO301_G1.PrjPcb', RUTA_TMP + 'red_anterior.txt');
  Terminar;
  Bitacora.Free;
End;

Procedure Compilar;
Var
  Ws, Prj, Doc, V : Variant;
  I, J, Total : Integer;
Begin
  Bitacora := TStringList.Create;
  Log('Compilar ' + DateTimeToStr(Now));
  Try
    Ws := GetWorkspace;
    Prj := Ws.DM_OpenProject(RUTA_BASE + 'altium\ELO301_G1.PrjPcb', True);
    Prj.DM_Compile;
    Total := 0;
    For I := 0 To Prj.DM_LogicalDocumentCount - 1 Do
    Begin
      Doc := Prj.DM_LogicalDocuments(I);
      For J := 0 To Doc.DM_ViolationCount - 1 Do
      Begin
        V := Doc.DM_Violations(J);
        Log('  [' + IntToStr(V.DM_ErrorLevel) + '] ' + Doc.DM_FileName + ': ' + V.DM_DescriptorString + ' | ' + V.DM_DetailString);
        Inc(Total);
      End;
    End;
    Log('violaciones: ' + IntToStr(Total));
    Log('componentes: ' + IntToStr(Prj.DM_DocumentFlattened.DM_ComponentCount) + ', redes: ' + IntToStr(Prj.DM_DocumentFlattened.DM_NetCount));
  Except
    Log('EXCEPCION');
  End;
  Terminar;
  Bitacora.Free;
End;
