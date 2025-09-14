# @MenuPath label="MacroQA>Geometric Accuracy Test"

from ij import IJ
from ij.io import OpenDialog
from ij.measure import ResultsTable
from ij.gui import WaitForUserDialog
from ij import ImagePlus
import sys

# === Função para abrir imagem DICOM ===
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

# === Função para obter medida de linha ===
def get_measurement(imp, instruction):
    # Espera o usuário desenhar a ROI
    wait = WaitForUserDialog("Desenhe a linha", instruction)
    wait.show()

    roi = imp.getRoi()
    if roi is None or roi.getType() != roi.LINE:
        IJ.error("ROI inválida", "Por favor, desenhe uma linha reta válida.")
        return None

    IJ.run("Set Measurements...", "length")
    IJ.run(imp, "Measure", "")

    rt = ResultsTable.getResultsTable()
    length = rt.getValue("Length", rt.size() - 1)
    IJ.log("Comprimento: {:.3f}".format(length))
    return length

IJ.log("---- Inicio do teste de Exatidao Geometrica ----")
# === MEDIDA DO LOCALIZER ===
IJ.log("=== Medida do LOCALIZER ===")
WaitForUserDialog("Clique OK para selecionar a imagem do Localizer").show()
localizer = open_dicom_file("Selecione a imagem DICOM do LOCALIZER")
if localizer is None:
    sys.exit()
IJ.setTool("line")
IJ.run("In [+]", "")
IJ.run("In [+]", "")
localizer_measurement = get_measurement(localizer, "Desenhe a linha vertical no LOCALIZER.")
localizer.close()

# === MEDIDAS DO T1-PONDERADO ===
IJ.log("=== Medida da imagem ponderada em T1 ===")
WaitForUserDialog("Clique OK para selecionar a imagem ponderada em T1").show()
t1w = open_dicom_file("Selecione a imagem DICOM ponderada em T1 (multi-slice)")
if t1w is None:
    sys.exit()
IJ.run("In [+]", "")
IJ.run("In [+]", "")

# --- Fatiamento 1 ---
t1w.setSlice(1)
IJ.log("Agora na Fatia 1 da imagem ponderada em T1")

t1_vert = get_measurement(t1w, "Fatia 1: Desenhe linha VERTICAL")
t1_horz = get_measurement(t1w, "Fatia 1: Desenhe linha HORIZONTAL")

# --- Fatiamento 5 ---
t1w.setSlice(5)
IJ.log("Agora na Fatia 5 da imagem ponderada em T1")

t1_diag1 = get_measurement(t1w, "Fatia 5: Desenhe linha DIAGONAL 1")
t1_diag2 = get_measurement(t1w, "Fatia 5: Desenhe linha DIAGONAL 2")
t1_vert_5 = get_measurement(t1w, "Fatia 5: Desenhe linha VERTICAL")
t1_horz_5 = get_measurement(t1w, "Fatia 5: Desenhe linha HORIZONTAL")

t1w.close()

# === LOG FINAL ===
IJ.log("=== MEDIDAS CONCLUIDAS ===")
IJ.log("LOCALIZER: {:.3f}".format(localizer_measurement))
IJ.log("T1 Fatia 1 - Vertical: {:.3f}, Horizontal: {:.3f}".format(t1_vert, t1_horz))
IJ.log("T1 Fatia 5 - Diagonal 1: {:.3f}, Diagonal 2: {:.3f}".format(t1_diag1, t1_diag2))
IJ.log("T1 Fatia 5 - Vertical: {:.3f}, Horizontal: {:.3f}".format(t1_vert_5, t1_horz_5))

IJ.log("{:.3f}".format(localizer_measurement))
IJ.log("{:.3f}".format(t1_vert))
IJ.log("{:.3f}".format(t1_horz))
IJ.log("{:.3f}".format(t1_diag1))
IJ.log("{:.3f}".format(t1_diag2))
IJ.log("{:.3f}".format(t1_vert_5))
IJ.log("{:.3f}".format(t1_horz_5))
IJ.log(("---------------------------------------"))


WaitForUserDialog("Teste de Exatidao Geometrica finalizado, colete os resultados.").show()

IJ.run("Clear Results")
IJ.log("---- Fim do teste de Exatidao Geometrica ----")
IJ.log("")
