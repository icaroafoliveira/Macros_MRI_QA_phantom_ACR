# Macro to perform the High-Contrast Spatial Resolution test for MRI ACR phantom.
# This script guides the user through visualization adjustments and ROI selection,
# then records the smallest visible hole size in the resolution insert.

# Steps performed:
# 1. Open T1-weighted DICOM image and confirm the type by slice count.
# 2. Navigate to the first slice and adjust visualization (scale, W&L).
# 3. User selects ROI for zoom in the resolution insert.
# 4. Automatic window/level adjustment followed by manual refinement.
# 5. User inputs the smallest distinguishable hole size (upper and lower patterns).
# 6. Results are logged for reporting.

from java.awt import Rectangle
from ij import IJ, WindowManager
from ij.gui import Roi, WaitForUserDialog
from ij.measure import Measurements
from ij.plugin.frame import RoiManager
from ij.process import ImageStatistics
from ij.measure import ResultsTable
from ij.io import OpenDialog
import ij.io
import math

# === Function to open DICOM files ===
# Prompts the user to select a DICOM image and opens it.
def open_dicom_file(prompt):
    od = ij.io.OpenDialog(prompt, None)
    path = od.getPath()
    if path is None:
        return None
    imp = IJ.openImage(path)
    if imp is None:
        IJ.error("Fail to open the image.")
        return None
    imp.show()
    return imp

# === Function to close the Window/Level dialog if open ===
# Searches for common W&L dialog titles and closes the window automatically.
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

# === Function to print image type based on number of slices ===
# Localizer: 1 slice | ACR T1w: 11 slices | ACR T2w: 22 slices

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

# ---- Main Procedure ----
IJ.log("---- High Contrast Spatial Resolution Test ----")
WaitForUserDialog("Open the T1 image and perform the high-contrast resolution test.").show()
imp = open_dicom_file("Select T1-weighted DICOM image (multi-slice)")

if imp is None:
    IJ.error("No image open.")
    raise SystemExit

# Identify image type by slice count
printImageType(imp)

# ===== Step 1: Select slice and initial adjustments =====
imp.setSlice(1)
IJ.log("Slice set to 1.")

# Reset visualization to original scale and central W&L
IJ.run(imp, "Original Scale", "")
IJ.resetMinAndMax(imp)
IJ.log("Window/Level adjusted to central values.")

# Apply zoom for detailed view
IJ.run("In [+]", ""); IJ.run("In [+]", ""); IJ.run("In [+]", "")
IJ.setTool("rectangle")
win = imp.getWindow()
if win is not None:
    win.pack()

# ===== Step 2: User selects ROI for zoom =====
dlg = WaitForUserDialog(
    "Select the area for zoom.\n"
    "Draw a ROI in the region you want to enlarge and click OK.")
dlg.show()
IJ.log("Zoom adjusted to the selected ROI")

roi = imp.getRoi()
if roi is None:
    IJ.error("No ROI was selected!")
    raise SystemExit
else:
    bounds = roi.getBounds()
    canvas = imp.getCanvas()
    if canvas is not None:
        # Center zoom on selected ROI
        canvas.setSourceRect(Rectangle(bounds.x, bounds.y, bounds.width, bounds.height))
        imp.updateAndDraw()
        # Automatically zoom in until ROI fills the display
        while (canvas.getSrcRect().width > bounds.width or 
               canvas.getSrcRect().height > bounds.height):
            canvas.zoomIn(bounds.x + bounds.width // 2, bounds.y + bounds.height // 2)
            canvas.zoomIn(bounds.x + bounds.width // 2, bounds.y + bounds.height // 2)
            if (canvas.getSrcRect().width <= bounds.width and 
                canvas.getSrcRect().height <= bounds.height):
                break

# ===== Step 3: Automatic window/level adjustment =====
l, w = 450.0, 150.0
min_display = l - (w / 2)
max_display = l + (w / 2)
IJ.setMinAndMax(imp, min_display, max_display)
IJ.run("Brightness/Contrast...")
IJ.run("Window/Level...")

# ===== Step 4: Manual window/level refinement =====
from ij.gui import GenericDialog
from java.awt import Font

gd = GenericDialog("Instructions")
gd.addMessage("WARNING!", Font("SansSerif", Font.BOLD, 20))
gd.addMessage("Adjust level and window in the next step until the holes in the resolution insert are displayed individually.", Font("SansSerif", Font.ITALIC, 12))
gd.addMessage("Press 'OK' to continue.", Font("SansSerif", Font.ITALIC, 12))
gd.showDialog()
if gd.wasCanceled():
    IJ.log("Cancelled.")
    raise SystemExit

dlg = WaitForUserDialog(
    "The three sets of dot patterns forming squares have different hole sizes.\n"
    "From left to right: 1.1 mm, 1.0 mm, and 0.9 mm.\n"
    "Top square = horizontal resolution | Bottom square = vertical resolution.")
dlg.show()

# ===== Step 5: Collect user input for resolution limits =====
CANCEL_SENTINEL = float(-2147483648.0)

def get_number_or_nan(prompt, default=1.0):
    v = IJ.getNumber(prompt, default)
    if v == CANCEL_SENTINEL or (isinstance(v, float) and math.isnan(v)):
        return float('nan')
    return v

valor_upper = get_number_or_nan("Enter the hole size value for the upper in mm:", 1.0)
valor_lower = get_number_or_nan("Enter the hole size value for the lower in mm:", 1.0)

# ===== Step 6: Wrap-up and log results =====
dlg = WaitForUserDialog("High-Contrast Resolution Test completed, collect the results.")
dlg.show()
imp.close()
fechar_wl()
IJ.run("Clear Results")

IJ.log("Upper hole size [mm]: %s" % ("NaN" if (isinstance(valor_upper, float) and math.isnan(valor_upper)) else ("%.1f" % valor_upper)))
IJ.log("Lower hole size [mm]: %s" % ("NaN" if (isinstance(valor_lower, float) and math.isnan(valor_lower)) else ("%.1f" % valor_lower)))
IJ.log("---- End of the High Contrast Spatial Resolution Test ----")
IJ.log("")
