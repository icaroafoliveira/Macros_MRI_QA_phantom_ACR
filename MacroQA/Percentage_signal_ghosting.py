from ij import IJ, WindowManager
from ij.gui import OvalRoi, WaitForUserDialog, GenericDialog
from ij.measure import Measurements
from ij.plugin.frame import RoiManager
import math
from ij.io import OpenDialog
from java.awt import Font

def fechar_wl():
    # Títulos mais comuns dessa janela
    candidatos = ["Brightness/Contrast", "W&L", "Window/Level", "B&C"]
    for t in candidatos:
        w = WindowManager.getWindow(t) or WindowManager.getFrame(t)
        if w is not None:
            # fecha sem perguntar
            try:
                w.dispose()   # fecha a janela
            except:
                try:
                    w.setVisible(False)
                except:
                    pass
            return True
    # fallback: varre janelas não-imagem e fecha se bater por nome
    wins = WindowManager.getNonImageWindows() or []
    for w in wins:
        try:
            title = w.getTitle()
        except:
            title = ""
        if title and any(s in title.lower() for s in ["contrast", "brightness", "window/level", "w&l", "b&c"]):
            w.dispose()
            return True
    return False

def open_dicom_file(prompt):
    od = OpenDialog(prompt, None)
    path = od.getPath()
    if path is None:
        return None
    imp = IJ.openImage(path)
    if imp is None:
        IJ.error("Failed to open the image.")
        return None
    imp.show()
    return imp

# === Function to print image type based on number of slices ===
def printImageType(imp):
    # Make sure that the image is the expected one
    # Localizer is a single-slice image
    # T1w has 11 slices
    # T2w has 22 slices (2 echo times)
     
    slices = imp.getNSlices()     # z dimension

    if slices < 11:
        IJ.log("Image Type: Localizer.")
    elif slices > 11:
        IJ.log("Image Type: ACR T2w image.")
    else:
        IJ.log("Image Type: ACR T1w image.")

IJ.log("---- Start of Percentage Signal Ghosting Test ----")
WaitForUserDialog("Open the T1 image and perform the residual image test").show()
imp = open_dicom_file("Select T1-weighted DICOM image (multi-slice)")

if imp is None:
    IJ.error("No image open.")
    raise SystemExit

# Print image type
printImageType(imp)

IJ.run(imp, "Original Scale", "")
IJ.resetMinAndMax(imp)

IJ.run("In [+]", "")
IJ.run("In [+]", "")

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
    IJ.error("The stack does not contain 7 slices (it has {}).".format(imp.getNSlices()))
    raise SystemExit
imp.setSlice(7)
IJ.log("Slice set to 7.")

# Ajusta window/level para valores centrais
IJ.resetMinAndMax(imp)
IJ.log("Window/Level adjusted to central values.")

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
    gd = GenericDialog("Calibration missing or not recognized")
    gd.addMessage("Enter the pixel size (in mm).")
    gd.addNumericField("Pixel width (mm):", 0.0, 6)
    gd.addNumericField("Pixel height (mm):", 0.0, 6)
    gd.showDialog()
    if gd.wasCanceled():
        IJ.log("Cancelled by user.")
        raise SystemExit
    pw_mm = gd.getNextNumber()
    ph_mm = gd.getNextNumber()
    if pw_mm <= 0 or ph_mm <= 0:
        IJ.error("Invalid pixel values.")
        raise SystemExit
    pixel_width_cm = pw_mm / 10.0
    pixel_height_cm = ph_mm / 10.0

IJ.log("Calibration used (cm/pixel) : {:.6g} x {:.6g}  (unit='{}')".format(pixel_width_cm, pixel_height_cm, cal.getUnit()))

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

dlg = WaitForUserDialog("Position large ROI (200 cm^2)",
    "Move the large ROI to the desired location. \nClick OK when done.")
dlg.show()

mean_ref = medir_roi_mean(imp)
IJ.log("Initial mean (large ROI): {:.3f}".format(mean_ref))

# ===== Passo 3: Ajuste manual do janelamento=====

# Reduz automaticamente o window ao mínimo
l=5.0
w=50.0
min_display = l - (w / 2)  # 0
max_display = l + (w / 2)  # 2000
IJ.setMinAndMax(imp, min_display, max_display)

# Abre a janela de W&L já configurada
IJ.run("Brightness/Contrast...")
IJ.run("Window/Level...")

dlg = WaitForUserDialog("Manual adjustment - windowing",
    "Increase the window value until the background of the image becomes illuminated (~50)")
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
    titulo="RRight ROI of the phantom",
    mensagem="Adjust the ROI to the region to the right of the phantom."
)

# ===== Passo 5: ROI abaixo =====
offset_y_baixo = int(imp.getHeight() * 0.25)  # 25% para baixo
btm=criar_roi_ajustar(
    imp,
    largura_cm=20.0,
    altura_cm=1.5,
    desloc_x_px=0,
    desloc_y_px=offset_y_baixo,
    titulo="ROI Below the phantom",
    mensagem="Adjust the ROI to the region below the phantom."
)

# ===== Passo 6: ROI acima =====
offset_y_cima = -int(imp.getHeight() * 0.25)  # 25% para cima
top=criar_roi_ajustar(
    imp,
    largura_cm=20.0,
    altura_cm=1.5,
    desloc_x_px=0,
    desloc_y_px=offset_y_cima,
    titulo="ROI Above the phantom",
    mensagem="Adjust the ROI to the region above the phantom."
)

# ===== Passo 7: ROI à esquerda =====
offset_x_esq = -int(imp.getWidth() * 0.25)  # 25% para esquerda
left=criar_roi_ajustar(
    imp,
    largura_cm=1.5,
    altura_cm=20.0,
    desloc_x_px=offset_x_esq,
    desloc_y_px=0,
    titulo="ROI Left of the phantom",
    mensagem="Adjust the ROI to the region to the left of the phantom."
)


# ===== Passo 8: Cálculo do Ghosting Ratio =====
if (mean_ref) == 0:
    IJ.log("Error: Mean Pixel Value in the Central ROI == 0, unable to calculate GR.")
else:
    GR = abs((((top - btm)-(left+right))*100) / (2.0*mean_ref))
    IJ.log("Ghosting Ratio calculated: {:.10f}%".format(GR))
    IJ.log("{:.10f}%".format(GR))

gd = GenericDialog("Instructions")
gd.addMessage("WARNING!", Font("SansSerif", Font.BOLD, 20))
gd.addMessage("Close the ROI Manager window right after completing the test.", Font("SansSerif", Font.ITALIC, 12))
gd.addMessage("Click 'OK' to continue.", Font("SansSerif", Font.ITALIC, 12))
gd.showDialog()
if gd.wasCanceled():
    IJ.log("Cancelled.")
    raise SystemExit

WaitForUserDialog("Percentage Signal Ghosting Test completed, collect the results.\n").show()
imp.close()
fechar_wl()

IJ.run("Clear Results")
IJ.log("---- End of Percentage Signal Ghosting Test ----")
IJ.log("")