from java.awt import Window, Font
from ij.io import OpenDialog
from ij import IJ, WindowManager
from ij.gui import OvalRoi, WaitForUserDialog, GenericDialog
from ij.measure import Measurements
from ij.plugin.frame import RoiManager
from javax.swing import SwingUtilities
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

# === Function to close the W&L window if open === 
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

# === Function to open DICOM files ===
def open_dicom_file(prompt):
    od = OpenDialog(prompt, None)
    path = od.getPath()
    if path is None:
        return None
    imp = IJ.openImage(path)
    if imp is None:
        IJ.error("Fail to open the image.")
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

IJ.log("---- Image Intensity Uniformity Test ----")
WaitForUserDialog("Open the T1 image and perform the uniformity test").show()
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
        IJ.error("Invalid pixel values")
        raise SystemExit
    pixel_width_cm = pw_mm / 10.0
    pixel_height_cm = ph_mm / 10.0

IJ.log("Calibration used (cm/pixel): {:.6g} x {:.6g}  (unit='{}')".format(pixel_width_cm, pixel_height_cm, cal.getUnit()))

# ===== Passo 2b: Criar ROI grande de 200 cm² para posicionamento manual =====
radius_large = area_to_radius_pixels(200.0, pixel_width_cm, pixel_height_cm)
center_x = imp.getWidth() / 2.0
center_y = imp.getHeight() / 2.0
roi_large = OvalRoi(center_x - radius_large, center_y - radius_large, radius_large*2, radius_large*2)
imp.setRoi(roi_large)

dlg = WaitForUserDialog("Position large ROI (200 cm^2)",
    "Move the large ROI to the desired location.\nPress 'OK' to continue.")
dlg.show()

# Adicionar ROI grande no ROI Manager
rm = RoiManager.getInstance()
if rm is None:
    rm = RoiManager()
rm.reset()  # limpa ROIs antigas
rm.addRoi(roi_large)

gd = GenericDialog("Instructions")
gd.addMessage("WARNING!", Font("SansSerif", Font.BOLD, 20))
gd.addMessage("Select the 'Show All' option in the ROI Manager window before proceeding with the test.", Font("SansSerif", Font.ITALIC, 12))
gd.addMessage("Press 'OK' to continue.", Font("SansSerif", Font.ITALIC, 12))
gd.showDialog()
if gd.wasCanceled():
    IJ.log("Cancelled.")
    raise SystemExit

mean_ref = medir_roi_mean(imp)
IJ.log("Initial mean (large ROI): {:.3f}".format(mean_ref))

# ===== Passo 3: Ajuste manual para baixo sinal =====
# Reduz automaticamente o window ao mínimo
stats_full = imp.getStatistics()
min_val = stats_full.min
IJ.setMinAndMax(imp, min_val, min_val + 1)  # força branco total

# Abre a janela de Brightness/Contrast para ajuste manual
IJ.run("Brightness/Contrast...")
IJ.run("Window/Level...")

dlg = WaitForUserDialog("Manual adjustment - low signal",
    "Increase the level until approximately 1 cm^2 of dark pixels appear within the large ROI.\n"
    "Focus on the largest dark region.\n\nPress 'OK' to continue.")
dlg.show()

IJ.run("Window/Level...")

# ===== Passo 4: ROI pequena (~1 cm²) para baixo sinal =====
radius_small = area_to_radius_pixels(1.0, pixel_width_cm, pixel_height_cm)
roi_small_low = OvalRoi(center_x - radius_small, center_y - radius_small, radius_small*2, radius_small*2)
imp.setRoi(roi_small_low)

dlg = WaitForUserDialog("Position small ROI - low signal",
    "Move the small ROI to the region of lowest signal (within the large ROI).\nPress 'OK' to continue.")
dlg.show()

low_signal = medir_roi_mean(imp)
IJ.log("Low signal mean: {:.3f}".format(low_signal))

# ==== REPOSICIONAR A ROI GRANDE NO MESMO LOCAL PARA REFERÊNCIA ====
imp.setRoi(roi_large)
if not any(r == roi_large for r in rm.getRoisAsArray()):
    rm.addRoi(roi_large)



# ===== Passo 5: Ajuste manual para alto sinal =====
dlg = WaitForUserDialog("Manual adjustment - high signal",
    "Increase the level until only approximately 1 cm^2 of white pixels remain within the large ROI.\n"
    "Focus on the largest white region.\n\nPress 'OK' to continue.")
dlg.show()
IJ.run("Clear Results") 
# ===== Passo 6: ROI pequena (~1 cm²) para alto sinal =====
roi_small_high = OvalRoi(center_x - radius_small, center_y - radius_small, radius_small*2, radius_small*2)
imp.setRoi(roi_small_high)

dlg = WaitForUserDialog("Position small ROI - high signal",
    "Move the small ROI to the region of highest signal (within the large ROI).\nPress 'OK' to continue.")
dlg.show()
rm.addRoi(roi_small_high)
high_signal = medir_roi_mean(imp)
IJ.log("High signal mean: {:.3f}".format(high_signal))

# ===== Passo 7: Cálculo do PIU =====
if (high_signal + low_signal) == 0:
    IJ.log("Error: high + low == 0, unable to calculate PIU.")
else:
    piu = 100.0 * (1.0 - ((high_signal - low_signal) / (high_signal + low_signal)))
    IJ.log("Calculated PIU: {:.2f}".format(piu))
    IJ.log("{:.2f}".format(piu))

gd = GenericDialog("Instructions")
gd.addMessage("WARNING!", Font("SansSerif", Font.BOLD, 20))
gd.addMessage("Close the ROI Manager window right after completing the test.", Font("SansSerif", Font.ITALIC, 12))
gd.addMessage("Press 'OK' to continue.", Font("SansSerif", Font.ITALIC, 12))
gd.showDialog()
if gd.wasCanceled():
    IJ.log("Cancelled.")
    raise SystemExit

dlg=WaitForUserDialog("Uniformity test completed, collect the results.")
dlg.show()
fechar_wl()
imp.close()

IJ.run("Clear Results")
IJ.log("---- End of the Image Intensity Uniformity Test ----")
IJ.log("")