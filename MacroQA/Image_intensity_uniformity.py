# Macro to perform the Image Intensity Uniformity (PIU) test of the ACR MRI phantom.
# The script assumes that the user will select the ACR T1-weighted or T2-weighted image.
# The user is prompted to draw a large circular ROI (~200 cm²) around the area of interest.
# The user is then asked to adjust the window/level settings to identify low and high signal areas.
# Finally, the user is asked to place small circular ROIs (~1 cm²) in the low and high signal areas to measure the mean intensities.
# The script calculates and displays the Percent Image Uniformity (PIU) based on the measured values.

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

def measure_roi_mean(imp, roi=None):
    if roi is not None:
        imp.setRoi(roi)
    stats = imp.getStatistics(Measurements.MEAN)
    return stats.mean

# === Function to close the W&L window if open === 
def close_wl():
    # Títulos mais comuns dessa janela
    candidates = ["Brightness/Contrast", "W&L", "Window/Level", "B&C"]
    for t in candidates:
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
    """Print the DICOM image type based on the TR (Repetition Time) value.

    Typical TR values:
    - Localizer: ~200 ms
    - T1-weighted (T1w): ~500 ms
    - T2-weighted (T2w): ~2000 ms
    """

    tr = None
    info = imp.getInfoProperty()

    if info is not None:
        for line in info.split("\n"):
            if line.startswith("0018,0080"):  # TR tag
                try:
                    tr = float(line.split(":")[1].strip())
                except:
                    tr = None
                    IJ.log("Could not parse TR value.")

    if tr is None:
        IJ.log("TR value not found.")
    elif tr < 300:
        IJ.log("Image Type: Localizer.")
    elif tr >= 300 and tr < 1000:
        IJ.log("Image Type: ACR T1-weighted image.")
    elif tr >= 1000:
        IJ.log("Image Type: ACR T2-weighted image.")

IJ.log("---- Image Intensity Uniformity Test ----")
WaitForUserDialog("Open the T1 or T2 image and perform the uniformity test").show()
imp = open_dicom_file("Select T1-weighted or T2-weighted DICOM image")

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
    #IJ.error("The stack does not contain 7 slices (it has {}).".format(imp.getNSlices()))
    #raise SystemExit
    imp.setSlice(1)
    IJ.log("Slice set to 1 (only {} slices in stack).".format(imp.getNSlices()))
elif imp.getNSlices() == 11:
    imp.setSlice(7)
    IJ.log("Slice set to 7.")
else:
    dlg = WaitForUserDialog(
        "This image has more than 11 slices, assuming it is a Multi-Echo T2-weighted image.\n"
        "Select the slice with no visible structures (usually slice 14 or 18)")
    dlg.show()
    # choose slice
    slice_num = IJ.getNumber("Enter the slice number to analyze (1 to %d):" % imp.getNSlices(), 14)
    if slice_num is None or slice_num < 1 or slice_num > imp.getNSlices():
        IJ.error("Invalid slice number.")
        raise SystemExit
    imp.setSlice(int(slice_num))
    IJ.log("Slice set to %d." % int(slice_num))
    
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

mean_ref = measure_roi_mean(imp)
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

low_signal = measure_roi_mean(imp)
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
high_signal = measure_roi_mean(imp)
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
close_wl()
imp.close()

IJ.run("Clear Results")
IJ.log("---- End of the Image Intensity Uniformity Test ----")
IJ.log("")