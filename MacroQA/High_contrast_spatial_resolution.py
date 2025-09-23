# Macro to perform the High Contrast Spatial Resolution test of the ACR MRI phantom.
# The script assumes that the user will select the ACR T1-weighted image (multi-slice).
# The user is prompted to draw a rectangular ROI around the area of interest.
# The script then zooms into the selected ROI and adjusts the window/level settings.
# Finally, the user is asked to enter the measured hole sizes for the upper and lower patterns

from java.awt import Rectangle
from ij import IJ, WindowManager
from ij.gui import Roi, WaitForUserDialog
from ij.measure import Measurements
from ij.plugin.frame import RoiManager
from ij.process import ImageStatistics
from ij.measure import ResultsTable
from ij.io import OpenDialog
from ij.gui import GenericDialog
from java.awt import Font
import ij.io
import math

# === All functions used in the script are defined here ===

# === Function to open DICOM files ===
def open_dicom_file(prompt):
    """Opens a file chooser dialog to select a DICOM file.
    
    Returns the ImagePlus object or None if the operation is canceled or fails.
    """
    od = ij.io.OpenDialog(prompt, None)
    path = od.getPath()
    if path is None:
        return None
    imp = IJ.openImage(path)
    if imp is None:
        IJ.error("Failed to open the image.")
        return None
    imp.show()
    return imp

# === Function to close the W&L window if open ===
def close_wl():
    """
    Closes any open Brightness/Contrast or Window/Level dialogs.
    """
    candidates = ["Brightness/Contrast", "W&L", "Window/Level", "B&C"]
    for t in candidates:
        w = WindowManager.getWindow(t) or WindowManager.getFrame(t)
        if w is not None:
            # closing without prompt
            try:
                w.dispose()   # fecha a janela
            except:
                try:
                    w.setVisible(False)
                except:
                    pass
            return True
    # fallback: scan non-image windows and close if the title matches
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

def get_number_or_nan(prompt, default=1.0):
    """Prompt the user for a numeric value and return NaN on cancel.

    ImageJ returns a sentinel value when the user cancels number dialogs. This
    wrapper calls `IJ.getNumber` with `prompt` and `default`, and converts the
    sentinel or any NaN-like result into a Python `float('nan')` so later code
    can handle missing values cleanly.

    Args:
        prompt (str): Message shown to the user.
        default (float): Default numeric value shown in the dialog.

    Returns:
        float: The entered number, or `float('nan')` if the dialog was canceled
        or an invalid number was provided.
    """
    v = IJ.getNumber(prompt, default)
    if v == CANCEL_SENTINEL or (isinstance(v, float) and math.isnan(v)):
        return float('nan')
    return v

# === MAIN SCRIPT ===
IJ.log("---- High Contrast Spatial Resolution Test ----")
WaitForUserDialog("Open the T1 or T2 image and perform the high-contrast resolution test.").show()
imp = open_dicom_file("Select T1-weighted or T2-weighted DICOM image")

if imp is None:
    IJ.error("No image open.")
    raise SystemExit

# Print image type
printImageType(imp)

# ===== Step 1: Select slice =====
if imp.getNSlices() > 11:
    dlg = WaitForUserDialog(
        "This image has more than 11 slices, assuming it is a Multi-Echo T2-weighted image.\n"
        "Select the slice that shows the resolution patterns (usually slice 2 or 12).")
    dlg.show()
    # choose slice
    slice_num = IJ.getNumber("Enter the slice number to analyze (1 to %d):" % imp.getNSlices(), 12)
    if slice_num is None or slice_num < 1 or slice_num > imp.getNSlices():
        IJ.error("Invalid slice number.")
        raise SystemExit
    imp.setSlice(int(slice_num))
    IJ.log("Slice set to %d." % int(slice_num))
else:
    imp.setSlice(1)
    IJ.log("Slice set to 1.")
    
IJ.run(imp, "Original Scale", "")
IJ.resetMinAndMax(imp)
IJ.log("Window/Level adjusted to central values.")

# Zoom in a few times (equivalent to pressing the "+" key)
IJ.run("In [+]", "")
IJ.run("In [+]", "")
IJ.run("In [+]", "")
#IJ.run("In [+]", "")
IJ.setTool("rectangle")
# Adjust the window to fit the new zoom level
win = imp.getWindow()
if win is not None:
    win.pack()  # force the window to resize
    
# ===== Step 2: user selects the ROI =====
dlg = WaitForUserDialog(
    "Select the area for zoom. \n"
    "Draw a ROI in the region you want to enlarge and click OK..")
    
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
        # Set the canvas source rectangle to the ROI bounds (focus view on ROI)
        canvas.setSourceRect(Rectangle(bounds.x, bounds.y, bounds.width, bounds.height))
        imp.updateAndDraw()
        
        # Automatically zoom in until the ROI fills the source view
        while (canvas.getSrcRect().width > bounds.width or 
               canvas.getSrcRect().height > bounds.height):
            canvas.zoomIn(bounds.x + bounds.width // 2, bounds.y + bounds.height // 2)
            canvas.zoomIn(bounds.x + bounds.width // 2, bounds.y + bounds.height // 2)
            if (canvas.getSrcRect().width <= bounds.width and 
                canvas.getSrcRect().height <= bounds.height):
                break

# ===== Step 3: Automatic window/level adjustment =====
l = 450.0
w = 150.0
min_display = l - (w / 2)
max_display = l + (w / 2)
IJ.setMinAndMax(imp, min_display, max_display)

# Open the Brightness/Contrast and Window/Level dialogs with the
# previously-set min/max so the user can fine-tune visually
IJ.run("Brightness/Contrast...")
IJ.run("Window/Level...")

# ===== Step 4: Manual adjustment =====

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
    "In each set, the top square indicates horizontal resolution and the bottom one indicates vertical resolution."
)
dlg.show()

CANCEL_SENTINEL = float(-2147483648.0)

valor_upper = get_number_or_nan("Enter the hole size value for the upper in mm:", 1.0)
valor_lower = get_number_or_nan("Enter the hole size value for the lower in mm::", 1.0)

dlg = WaitForUserDialog( 
	"High-Contrast Resolution Test completed, collect the results.\n")
dlg.show()
imp.close()
close_wl()

IJ.run("Clear Results")
IJ.log("Upper hole size [mm]: %s" % ("NaN" if (isinstance(valor_upper, float) and math.isnan(valor_upper)) else ("%.1f" % valor_upper)))
IJ.log("Lower hole size [mm]: %s" % ("NaN" if (isinstance(valor_lower, float) and math.isnan(valor_lower)) else ("%.1f" % valor_lower)))
IJ.log("---- End of the High Contrast Spatial Resolution Test ----")
IJ.log("")