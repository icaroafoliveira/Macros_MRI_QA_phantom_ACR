#@ ImagePlus imp

from ij import IJ
from ij.gui import OvalRoi, WaitForUserDialog, GenericDialog
from ij.measure import Measurements
from ij.plugin.frame import RoiManager
import math

IJ.log("---- Inicio do teste de imagem residual ----")

# ===== Funções =====
def area_to_radius_pixels(area_cm2, px_w_cm, px_h_cm):
    pixel_area_cm2 = px_w_cm * px_h_cm
    return math.sqrt(area_cm2 / (math.pi * pixel_area_cm2))

def medir_roi_mean(imp, roi=None):
    if roi is not None:
        imp.setRoi(roi)
    stats = imp.getStatistics(Measurements.MEAN)
    return stats.mean

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

# ===== Passo 3: Ajuste manual do janelamento=====

# Reduz automaticamente o window ao mínimo
l=5.0
w=50.0
min_display = l - (w / 2)  # 0
max_display = l + (w / 2)  # 2000
IJ.setMinAndMax(imp, min_display, max_display)

# Abre a janela de W&L já configurada
IJ.run("Window/Level...")

dlg = WaitForUserDialog("Ajuste manual - janelamento",
    "Aumente o valor da janela para que o fundo da imagem se torne iluminado (~50)")
dlg.show()

# Função auxiliar para criar e ajustar ROI em qualquer posição
def criar_roi_ajustar(imp, largura_cm, altura_cm, desloc_x_px, desloc_y_px, titulo, mensagem):
    width_px = largura_cm / pixel_width_cm
    height_px = altura_cm / pixel_height_cm

    # Posição inicial deslocada
    x_pos = center_x - width_px / 2 + desloc_x_px
    y_pos = center_y - height_px / 2 + desloc_y_px

    roi = OvalRoi(x_pos, y_pos, width_px, height_px)
    imp.setRoi(roi)

    dlg = WaitForUserDialog(titulo, mensagem)
    dlg.show()

    valor = medir_roi_mean(imp)
    IJ.log("{}: {:.3f}".format(titulo, valor))
    return valor


# ===== Passo 4: ROI à direita =====
offset_x_dir = int(imp.getWidth() * 0.25)  # 25% para direita
right=criar_roi_ajustar(
    imp,
    largura_cm=1.5,
    altura_cm=20.0,
    desloc_x_px=offset_x_dir,
    desloc_y_px=0,
    titulo="ROI Direita do fantoma",
    mensagem="Ajuste a ROI para a regiao a direita do fantoma."
)

# ===== Passo 5: ROI abaixo =====
offset_y_baixo = int(imp.getHeight() * 0.25)  # 25% para baixo
btm=criar_roi_ajustar(
    imp,
    largura_cm=20.0,
    altura_cm=1.5,
    desloc_x_px=0,
    desloc_y_px=offset_y_baixo,
    titulo="ROI Abaixo do fantoma",
    mensagem="Ajuste a ROI para a regiao abaixo do fantoma."
)

# ===== Passo 6: ROI acima =====
offset_y_cima = -int(imp.getHeight() * 0.25)  # 25% para cima
top=criar_roi_ajustar(
    imp,
    largura_cm=20.0,
    altura_cm=1.5,
    desloc_x_px=0,
    desloc_y_px=offset_y_cima,
    titulo="ROI Acima do fantoma",
    mensagem="Ajuste a ROI para a regiao acima do fantoma."
)

# ===== Passo 7: ROI à esquerda =====
offset_x_esq = -int(imp.getWidth() * 0.25)  # 25% para esquerda
left=criar_roi_ajustar(
    imp,
    largura_cm=1.5,
    altura_cm=20.0,
    desloc_x_px=offset_x_esq,
    desloc_y_px=0,
    titulo="ROI Esquerda do fantoma",
    mensagem="Ajuste a ROI para a regiao a esquerda do fantoma."
)


# ===== Passo 8: Cálculo do Ghosting Ratio =====
if (mean_ref) == 0:
    IJ.log("Erro: Valor de Pixel Medio na ROI Central == 0, não e possivel calcular o GR.")
else:
    GR = abs((((top - btm)-(left+right))*100) / (2.0*mean_ref))
    IJ.log("Ghosting Ratio calculado: {:.10f}%".format(GR))
    IJ.log("{:.10f}%".format(GR))
    

WaitForUserDialog("Teste de Imagem Residual finalizado, colete os resultados.\n"
	"Recomenda-se fechar a janela de W&L.").show()

IJ.run("Clear Results")
IJ.log("---- Fim do teste de imagem residual ----")
IJ.log("")