"""Corrige Fabricacion.OutJob y regenera «Fabrication Files» en la VM; copia las salidas a fabricacion/vm de la carpeta
compartida. Gerber: origen relativo sin centrar en el film (calza con el taladro), plano GND en positivo, sin «add to all
plots» (mezclaba todas las capas en cada archivo), sin pad master, guía de taladro ni archivo de reglas. Pick and Place en
CSV y mm. El plano sale negativo: con PlotPositivePlaneLayers=True Altium 26 lo dibuja sin antipads. Las claves siguen los OutJob de ejemplo de Altium 26."""
import re, subprocess
from drc_comun import *

qga = lambda c: subprocess.run(['/mnt/sda3/vms/altium/qga.py', c], capture_output=True, text=True).stdout.strip()
COMPARTIDA = '/mnt/hdd-viejo-ro/S2-2026/MATERIA/ELO301-Diseno-Equipos-Electronicos/altium/'   # = \\10.0.2.4\qemu\ en la VM
VACIO = 'SerializeLayerHash.Version~2,ClassName~TLayerToBoolean'
CAPAS = '16777217~1,16777218~1,16842753~1,16842751~1,16973830~1,16973831~1,16973832~1,16973833~1,16973834~1,16973835~1'
GERBER = '|'.join([
    'AddToAllLayerClasses.Set= ', f'AddToAllPlots.Set={VACIO}', 'CentrePlots=False', 'DrillDrawingSymbol=GraphicsSymbol',
    'DrillDrawingSymbolSize=500000', 'EmbeddedApertures=True', 'FilmBorderSize=10000000', 'FilmXSize=200000000', 'FilmYSize=160000000',
    'FlashAllFills=False', 'FlashPadShapes=True', 'G54OnApertureChange=False', 'GenerateDRCRulesFile=False', 'GenerateReliefShapes=True',
    'GerberUnit=Metric', 'IncludeUnconnectedMidLayerPads=False', 'LayerClassesMirror.Set= ', 'LayerClassesPlot.Set= ',
    'LeadingAndTrailingZeroesMode=SuppressLeadingZeroes', 'MaxApertureSize=2500000', 'MinusApertureTolerance=50', f'Mirror.Set={VACIO}',
    'MirrorDrillDrawingPlots=False', 'MirrorDrillGuidePlots=False', 'NumberOfDecimals=5', 'OptimizeChangeLocationCommands=True',
    'OriginPosition=Relative', 'Panelize=False', f'Plot.Set={VACIO},{CAPAS}', 'PlotBoardProfile=True', 'PlotPositivePlaneLayers=False',
    'PlotUsedDrillDrawingLayerPairs=False', 'PlotUsedDrillGuideLayerPairs=False', 'PlusApertureTolerance=50', 'Record=GerberView',
    'SoftwareArcs=False', 'Sorted=False'])
PNP = 'Record=PickPlaceView|Units=Metric|GenerateCSVFormat=True|GenerateTextFormat=False'

oj = open(COMPARTIDA + 'proyecto-G1/Fabricacion.OutJob', newline='').read(); nl = '\r\n' if '\r\n' in oj else '\n'
oj = re.sub(r'^Configuration1_Item1=[^\r\n]*', lambda m: 'Configuration1_Item1=' + GERBER, oj, flags=re.M)
if 'Configuration3_Item1=' in oj:
    oj = re.sub(r'^Configuration3_Item1=[^\r\n]*', lambda m: 'Configuration3_Item1=' + PNP, oj, flags=re.M)
else:
    oj = oj.replace('OutputDefault3=0' + nl, 'OutputDefault3=0' + nl + 'Configuration3_Name1=OutputConfigurationParameter1' + nl + 'Configuration3_Item1=' + PNP + nl)
open(COMPARTIDA + 'fabricacion/Fabricacion.OutJob', 'w', newline='').write(oj)
print(correr(f"Obj2 := Client.GetDocumentByPath('{L}Fabricacion.OutJob'); if Obj2 <> nil then Client.CloseDocument(Obj2); ResultText := 'OutJob cerrado';"))
print(qga(rf"Copy-Item \\10.0.2.4\qemu\fabricacion\Fabricacion.OutJob {L}Fabricacion.OutJob -Force; Remove-Item {L}Fabricacion\* -Recurse -Force -ErrorAction SilentlyContinue; 'OutJob reemplazado, salidas viejas borradas'"))
print(mcp('run_output_jobs', {'container_names': ['Fabrication Files'], 'outjob_path': L + 'Fabricacion.OutJob'})[:160].replace('\n', ' '))
print(qga(rf"Remove-Item \\10.0.2.4\qemu\fabricacion\vm -Recurse -Force -ErrorAction SilentlyContinue; Copy-Item {L}Fabricacion \\10.0.2.4\qemu\fabricacion\vm -Recurse -Force; Start-ScheduledTask -TaskName respaldo-ELO301_G1; (Get-ChildItem \\10.0.2.4\qemu\fabricacion\vm -Recurse -File).Count"), 'archivos copiados')
