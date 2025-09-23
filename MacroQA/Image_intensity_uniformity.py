from java.awt import Window, Font
from ij.io import OpenDialog
from ij import IJ, WindowManager
from ij.gui import OvalRoi, WaitForUserDialog, GenericDialog
from ij.measure import Measurements
from ij.plugin.frame import RoiManager
from javax.swing import SwingUtilities
import math

# === Utility Functions ===

# Convert ROI area (cm²) into equivalent radius in pixels
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
            try:
                w.dispose()
            except:
                try:
                    w.setVisible(False)
                except:
                    pass
            return True
    # Fallback: search other non-image windows by title
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

# Open DICOM file
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

# Identify image type by slice count
def printImageType(imp):
    # Make sure that the image is the expected one
    # Localizer is a single-slice image
    # T1w has 11 slices
    # T2w has 22 slices (2 echo times)
     
    slices = imp.getNSlices()     # z dimension

    if slices < 11:
        IJ.log("Image Type: Localizer.")
    elif tr >= 300 and tr < 1000:
        IJ.log("Image Type: ACR T1-weighted image.")
    elif tr >= 1000:
        IJ.log("Image Type: ACR T2-weighted image.")

# ---- Main Procedure ----
IJ.log("---- Image Intensity Uniformity Test ----")
WaitForUserDialog("Open the T1 or T2 image and perform the uniformity test").show()
imp = open_dicom_file("Select T1-weighted or T2-weighted DICOM image")

if imp is None:
    IJ.error("No image open.")
    raise SystemExit

# Identify image type
printImageType(imp)

# Reset scale and visualization
IJ.run(imp, "Original Scale", "")
IJ.resetMinAndMax(imp)
IJ.run("In [+]", ""); IJ.run("In [+]", "")

# ===== Step 1: Navigate to slice 7 =====
if imp.getNSlices() < 7:
    IJ.error("The stack does not contain 7 slices (it has {}).".format(imp.getNSlices()))
    raise SystemExit
imp.setSlice(7)
IJ.log("Slice set to 7.")

# Ajusta window/level para valores centrais
IJ.resetMinAndMax(imp)
IJ.log("Window/Level adjusted to central values.")

# ===== Step 2: Calibration =====
cal = imp.getCalibration()
unit = (cal.getUnit() or "").lower()
pw = cal.pixelWidth
ph = cal.pixelHeight

# Handle calibration units (mm, cm, or manual entry)
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

# ===== Step 3: Place large ROI (200 cm²) =====
radius_large = area_to_radius_pixels(200.0, pixel_width_cm, pixel_height_cm)
center_x = imp.getWidth() / 2.0
center_y = imp.getHeight() / 2.0
roi_large = OvalRoi(center_x - radius_large, center_y - radius_large, radius_large*2, radius_large*2)
imp.setRoi(roi_large)

dlg = WaitForUserDialog("Position large ROI (200 cm^2)",
    "Move the large ROI to the desired location.\nPress 'OK' to continue.")
dlg.show()

# Add large ROI to ROI Manager
rm = RoiManager.getInstance()
if rm is None:
    rm = RoiManager()
rm.reset()
rm.addRoi(roi_large)

# Reminder: user must enable "Show All" in ROI Manager
gd = GenericDialog("Instructions")
gd.addMessage("WARNING!", Font("SansSerif", Font.BOLD, 20))
gd.addMessage("Select the 'Show All' option in the ROI Manager window before proceeding with the test.", Font("SansSerif", Font.ITALIC, 12))
gd.showDialog()
if gd.wasCanceled():
    IJ.log("Cancelled.")
    raise SystemExit

mean_ref = measure_roi_mean(imp)
IJ.log("Initial mean (large ROI): {:.3f}".format(mean_ref))

# ===== Step 4: Low-signal adjustment =====
stats_full = imp.getStatistics()
min_val = stats_full.min
IJ.setMinAndMax(imp, min_val, min_val + 1)  # force nearly black display
IJ.run("Brightness/Contrast...")
IJ.run("Window/Level...")

dlg = WaitForUserDialog("Manual adjustment - low signal",
    "Increase the level until ~1 cm^2 of dark pixels appear inside the large ROI.\n"
    "Focus on the largest dark region.\n\nPress 'OK' to continue.")
dlg.show()

# Place small ROI (~1 cm²) in low-signal region
radius_small = area_to_radius_pixels(1.0, pixel_width_cm, pixel_height_cm)
roi_small_low = OvalRoi(center_x - radius_small, center_y - radius_small, radius_small*2, radius_small*2)
imp.setRoi(roi_small_low)

dlg = WaitForUserDialog("Position small ROI - low signal",
    "Move the small ROI to the region of lowest signal (within the large ROI).\nPress 'OK' to continue.")
dlg.show()

low_signal = measure_roi_mean(imp)
IJ.log("Low signal mean: {:.3f}".format(low_signal))

# Ensure large ROI is saved
imp.setRoi(roi_large)
if not any(r == roi_large for r in rm.getRoisAsArray()):
    rm.addRoi(roi_large)

# ===== Step 5: High-signal adjustment =====
dlg = WaitForUserDialog("Manual adjustment - high signal",
    "Increase the level until only ~1 cm^2 of white pixels remain inside the large ROI.\n"
    "Focus on the largest white region.\n\nPress 'OK' to continue.")
dlg.show()

# Place small ROI (~1 cm²) in high-signal region
roi_small_high = OvalRoi(center_x - radius_small, center_y - radius_small, radius_small*2, radius_small*2)
imp.setRoi(roi_small_high)

dlg = WaitForUserDialog("Position small ROI - high signal",
    "Move the small ROI to the region of highest signal (within the large ROI).\nPress 'OK' to continue.")
dlg.show()

rm.addRoi(roi_small_high)
high_signal = measure_roi_mean(imp)
IJ.log("High signal mean: {:.3f}".format(high_signal))

# ===== Step 6: Calculate PIU =====
if (high_signal + low_signal) == 0:
    IJ.log("Error: high + low == 0, unable to calculate PIU.")
else:
    piu = 100.0 * (1.0 - ((high_signal - low_signal) / (high_signal + low_signal)))
    IJ.log("Calculated PIU: {:.2f}".format(piu))
    IJ.log("{:.2f}".format(piu))

# Reminder to close ROI Manager
gd = GenericDialog("Instructions")
gd.addMessage("WARNING!", Font("SansSerif", Font.BOLD, 20))
gd.addMessage("Close the ROI Manager window right after completing the test.", Font("SansSerif", Font.ITALIC, 12))
gd.showDialog()
if gd.wasCanceled():
    IJ.log("Cancelled.")
    raise SystemExit

dlg = WaitForUserDialog("Uniformity test completed, collect the results.")
dlg.show()
fechar_wl()
imp.close()
IJ.run("Clear Results")
IJ.log("---- End of the Image Intensity Uniformity Test ----")
IJ.log("")
