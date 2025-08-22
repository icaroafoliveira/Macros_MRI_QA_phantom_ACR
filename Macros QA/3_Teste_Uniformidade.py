#@ ImagePlus imp

from ij import IJ
from ij.gui import OvalRoi, WaitForUserDialog, GenericDialog
from ij.measure import Measurements
from ij.plugin.frame import RoiManager
import math

# ===== Funções =====
def area_to_radius_pixels(area_cm2, px_w_cm, px_h_cm):
    pixel_area_cm2 = px_w_cm * px_h_cm
    return math.sqrt(area_cm2 / (math.pi * pixel_area_cm2))

def medir_roi_mean(imp, roi=None):
    if roi is not None:
        imp.setRoi(roi)
    stats = imp.getStatistics(Measurements.MEAN)
    return stats.mean

IJ.log("---- Inicio do teste de Uniformidade ----")

IJ.run(imp, "Original Scale", "")
IJ.resetMinAndMax(imp)

IJ.run("In [+]", "")
IJ.run("In [+]", "")

# ===== Passo 1: ir para fatia 7 e centralizar window/level =====
if imp.getNSlices() < 7:
    IJ.error("A pilha não possui 7 fatias (tem {}).".format(imp.getNSlices()))
    raise SystemExit
imp.setSlice(7)
IJ.log("Fatia definida para 7.")

# Ajusta window/level para valores centrais
IJ.resetMinAndMax(imp)
IJ.log("Window/Level ajustados para valores centrais.")

# ===== Passo 2: Calibração =====
cal = imp.getCalibration()
unit = (cal.getUnit() or "").lower()
pw = cal.pixelWidth
ph = cal.pixelHeight

if unit == "mm":
    pixel_width_cm = pw / 10.0
    pixel_height_cm = ph / 10.0
elif unit == "cm":
    pixel_width_cm = pw
    pixel_height_cm = ph
else:
    gd = GenericDialog("Calibracao ausente ou nao reconhecida")
    gd.addMessage("Informe o tamanho do pixel (em mm).")
    gd.addNumericField("Pixel width (mm):", 0.0, 6)
    gd.addNumericField("Pixel height (mm):", 0.0, 6)
    gd.showDialog()
    if gd.wasCanceled():
        IJ.log("Cancelado pelo usuário.")
        raise SystemExit
    pw_mm = gd.getNextNumber()
    ph_mm = gd.getNextNumber()
    if pw_mm <= 0 or ph_mm <= 0:
        IJ.error("Valores de pixel invalidos.")
        raise SystemExit
    pixel_width_cm = pw_mm / 10.0
    pixel_height_cm = ph_mm / 10.0

IJ.log("Calibracao usada (cm/pixel): {:.6g} x {:.6g}  (unit='{}')".format(pixel_width_cm, pixel_height_cm, cal.getUnit()))

# ===== Passo 2b: Criar ROI grande de 200 cm² para posicionamento manual =====
radius_large = area_to_radius_pixels(200.0, pixel_width_cm, pixel_height_cm)
center_x = imp.getWidth() / 2.0
center_y = imp.getHeight() / 2.0
roi_large = OvalRoi(center_x - radius_large, center_y - radius_large, radius_large*2, radius_large*2)
imp.setRoi(roi_large)

# Adicionar ROI grande no ROI Manager
rm = RoiManager.getInstance()
if rm is None:
    rm = RoiManager()
rm.reset()  # limpa ROIs antigas
rm.addRoi(roi_large)

dlg = WaitForUserDialog("Posicionar ROI grande (200 cm^2)",
    "Mova a ROI grande para o local desejado.\nClique OK quando terminar.")
dlg.show()

mean_ref = medir_roi_mean(imp)
IJ.log("Media inicial (ROI grande): {:.3f}".format(mean_ref))

# ===== Passo 3: Ajuste manual para baixo sinal =====
# Reduz automaticamente o window ao mínimo
stats_full = imp.getStatistics()
min_val = stats_full.min
IJ.setMinAndMax(imp, min_val, min_val + 1)  # força branco total

# Abre a janela de Brightness/Contrast para ajuste manual
IJ.run("Window/Level...")

dlg = WaitForUserDialog("Ajuste manual - baixo sinal",
    "Ajuste o window/level para aparecer aproximadamente 1 cm^2 de pixels escuros dentro da ROI grande.\n"
    "Concentre-se na maior regiao escura.\n\nClique OK quando terminar.")
dlg.show()

IJ.run("Window/Level...")

# ===== Passo 4: ROI pequena (~1 cm²) para baixo sinal =====
radius_small = area_to_radius_pixels(1.0, pixel_width_cm, pixel_height_cm)
roi_small_low = OvalRoi(center_x - radius_small, center_y - radius_small, radius_small*2, radius_small*2)
imp.setRoi(roi_small_low)

dlg = WaitForUserDialog("Posicionar ROI pequena - baixo sinal",
    "Mova a ROI pequena para a regiao de menor sinal (dentro da ROI grande).\nClique OK quando terminar.")
dlg.show()

low_signal = medir_roi_mean(imp)
IJ.log("Media baixo sinal: {:.3f}".format(low_signal))

# ==== REPOSICIONAR A ROI GRANDE NO MESMO LOCAL PARA REFERÊNCIA ====
imp.setRoi(roi_large)
if not any(r == roi_large for r in rm.getRoisAsArray()):
    rm.addRoi(roi_large)



# ===== Passo 5: Ajuste manual para alto sinal =====
dlg = WaitForUserDialog("Ajuste manual - alto sinal",
    "AUMENTE o nivel ate restar apenas aproximadamente 1 cm^2 de pixels brancos dentro da ROI grande.\n"
    "A ROI grande esta salva no ROI manager, selecione-a para usar de referencia"
    "Concentre-se na maior regiao branca.\n\nClique OK quando terminar.")
dlg.show()
IJ.run("Clear Results")
IJ.log("") 
# ===== Passo 6: ROI pequena (~1 cm²) para alto sinal =====
roi_small_high = OvalRoi(center_x - radius_small, center_y - radius_small, radius_small*2, radius_small*2)
imp.setRoi(roi_small_high)
rm.addRoi(roi_small_high)

dlg = WaitForUserDialog("Posicionar ROI pequena - alto sinal",
    "Mova a ROI pequena para a regiao de maior sinal (dentro da ROI grande).\nClique OK quando terminar.")
dlg.show()
high_signal = medir_roi_mean(imp)
IJ.log("Media alto sinal: {:.3f}".format(high_signal))

# ===== Passo 7: Cálculo do PIU =====
if (high_signal + low_signal) == 0:
    IJ.log("Erro: high + low == 0, não e possivel calcular PIU.")
else:
    piu = 100.0 * (1.0 - ((high_signal - low_signal) / (high_signal + low_signal)))
    IJ.log("PIU calculado: {:.2f}".format(piu))
    IJ.log("{:.2f}".format(piu))

dlg=WaitForUserDialog("Teste de Uniformidade finalizado, colete os resultados.\n"
	"Recomenda-se fechar a janela de W&L.")
dlg.show()

IJ.run("Clear Results")
IJ.log("---- Fim do teste de Uniformidade ----")
IJ.log("")