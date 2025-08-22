from ij import IJ, WindowManager
from ij.gui import Roi, WaitForUserDialog
from ij.measure import Measurements
from ij.plugin.frame import RoiManager
from ij.process import ImageStatistics
from ij.measure import ResultsTable
from ij.io import OpenDialog

def open_dicom_file(prompt):
    od = OpenDialog(prompt, None)
    path = od.getPath()
    if path is None:
        return None
    imp = IJ.openImage(path)
    if imp is None:
        IJ.error("Falha ao abrir a imagem.")
        return None
    imp.show()
    return imp


IJ.log("---- Inicio do teste de Exatidao de Espessura ----")
WaitForUserDialog("Abra a imagem T1 e realize o teste de exatidao da espessura").show()
imp = open_dicom_file("Select T1-weighted DICOM image (multi-slice)")

if imp is None:
    IJ.error("Nenhuma imagem aberta.")
    raise SystemExit

IJ.run("Clear Results")
IJ.run(imp, "Original Scale", "")
IJ.run("In [+]", "")
IJ.run("In [+]", "")

# Ajuste manual de Window/Level (window=300, level=200)
window = 300
level = 200
min_display = level - window / 2  # 50
max_display = level + window / 2  # 350
imp.setDisplayRange(min_display, max_display)
imp.updateAndDraw()

# Seleciona ferramenta de retângulo
IJ.setTool("rectangle")

# Caixa para ROI 1
WaitForUserDialog("Selecionar ROI 1 (Retangulo)").show()
roi1 = imp.getRoi()
if roi1 is None:
    IJ.error("ROI 1 não selecionada.")
    raise SystemExit
imp.setRoi(roi1)
IJ.run("Measure")
stats1 = imp.getStatistics(Measurements.MEAN)
mean1 = stats1.mean

# Caixa para ROI 2
WaitForUserDialog("Selecionar ROI 2 (Retangulo").show()
roi2 = imp.getRoi()
if roi2 is None:
    IJ.error("ROI 2 não selecionada.")
    raise SystemExit
imp.setRoi(roi2)
IJ.run("Measure")
stats2 = imp.getStatistics(Measurements.MEAN)
mean2 = stats2.mean

# Ajuste de Window/Level baseado na média das ROIs
level = (mean1 + mean2) / 2
window = 10
min_display = (level - window) / 2
max_display = (level + window) / 2
imp.setDisplayRange(min_display, max_display)
imp.updateAndDraw()

# Seleciona ferramenta de linha
IJ.setTool("line")

# Caixa para ROI 3
WaitForUserDialog("Selecionar ROI 3 (Linha)").show()
roi3 = imp.getRoi()
if roi3 is None or roi3.getType() != Roi.LINE:
    IJ.error("ROI 3 nao e uma linha.")
    raise SystemExit
imp.setRoi(roi3)
IJ.run("Measure")
length3 = roi3.getLength()

# Caixa para ROI 4
WaitForUserDialog("Selecionar ROI 4 (Linha)").show()
roi4 = imp.getRoi()
if roi4 is None or roi4.getType() != Roi.LINE:
    IJ.error("ROI 4 nao e uma linha.")
    raise SystemExit
imp.setRoi(roi4)
IJ.run("Measure")
length4 = roi4.getLength()

# Realiza o cálculo solicitado
resultado = 0.2 * (length3 * length4) / (length3 + length4)

# Mostra no log
IJ.log("{:.3f}".format(resultado))

# Adiciona o resultado na tabela de resultados
rt = ResultsTable.getResultsTable()
rt.incrementCounter()
rt.addValue("Resultado Final", resultado)
rt.show("Results")
    
WaitForUserDialog("Teste de Exatidao de Espessura finalizado, colete os resultados.").show()

IJ.run("Clear Results")
IJ.log("---- Fim do teste de Exatidao de Espessura ----")
IJ.log("")