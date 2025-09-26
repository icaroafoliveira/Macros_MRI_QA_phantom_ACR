# --- MacroQA File Header ---
# Project: MacroQA - An ImageJ Macro for ACR MRI Quality Assurance
# File: Percentage_signal_ghosting.py
# Version 1.0.0
# Source: https://github.com/icaroafoliveira/Macros_MRI_QA_phantom_ACR
# ---------------------------

# Macro to calculate the Percentage Signal Ghosting Ratio (GR) from an ACR phantom MRI scan.
# The macro guides the user through placing specific Regions of Interest (ROIs) on a T1-weighted image.
# It measures the signal intensity in these ROIs to quantify ghosting artifacts, which are often caused by patient or gradient motion.

# Required libraries
from ij import IJ, WindowManager
from ij.gui import OvalRoi, WaitForUserDialog, GenericDialog
from ij.measure import Measurements
from ij.plugin.frame import RoiManager
import math
from ij.io import OpenDialog
from java.awt import Font

# === All functions used in the script are defined here ===

# === Function to close the W&L window if open ===
def close_wl():
    """Closes any open 'Brightness/Contrast' or 'Window/Level' dialogs.
    """
    # Common titles for this window
    candidates = ["Brightness/Contrast", "W&L", "Window/Level", "B&C"]
    for t in candidates:
        w = WindowManager.getWindow(t) or WindowManager.getFrame(t)
        if w is not None:
            # Closes without asking
            try:
                w.dispose()  # Closes the window
            except:
                try:
                    w.setVisible(False)
                except:
                    pass
            return True
    # Fallback: scan non-image windows and close if the name matches
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
    """
    Opens a DICOM file selected via a dialog box.
    Returns the ImagePlus object or None if the operation fails.
    """
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
# === Function to print image type based on TR value ===
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

# === Function to convert area in cm² to radius in pixels ===
def area_to_radius_pixels(area_cm2, px_w_cm, px_h_cm):
    """Converts a given area in cm^2 to a circle's radius in pixels."""
    pixel_area_cm2 = px_w_cm * px_h_cm
    return math.sqrt(area_cm2 / (math.pi * pixel_area_cm2))

# === Function to measure mean intensity in ROI ===
def measure_roi_mean(imp, roi=None):
    """Measures the mean pixel value within a given ROI."""
    if roi is not None:
        imp.setRoi(roi)
    stats = imp.getStatistics(Measurements.MEAN)
    return stats.mean

# === Function to create specific ROI size ===
def create_adjust_roi(imp, length_cm, height_cm, disp_x_px, disp_y_px, title, message):
    """
    Creates an ROI of a specific size at a displaced position and
    prompts the user to adjust its location.
    """
    width_px = length_cm / pixel_width_cm
    height_px = height_cm / pixel_height_cm

    # Initial displaced position
    x_pos = center_x - width_px / 2 + disp_x_px
    y_pos = center_y - height_px / 2 + disp_y_px

    roi = OvalRoi(x_pos, y_pos, width_px, height_px)
    imp.setRoi(roi)

    dlg = WaitForUserDialog(title, message)
    dlg.show()

    value = measure_roi_mean(imp)
    IJ.log("{}: {:.3f}".format(title, value))
    return value

# === Main Script ===

IJ.log("---- Start of Percentage Signal Ghosting Test ----")
WaitForUserDialog("Open the T1 or T2 image and perform the residual image test").show()
imp = open_dicom_file("Select T1-weighted or T2-weighted DICOM image")

if imp is None:
    IJ.error("No image open.")
    raise SystemExit

# Print image type for confirmation
printImageType(imp)

# Reset display settings and zoom in for user visibility
IJ.run(imp, "Original Scale", "")
IJ.resetMinAndMax(imp)
IJ.run("In [+]", "")
IJ.run("In [+]", "")

# ==== Step 1: Navigate to slice 7 and adjust window/level ====
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

# Reset window/level to a default central view
IJ.resetMinAndMax(imp)
IJ.log("Window/Level adjusted to central values.")

# --- Step 2: Image Calibration ---
# This block handles the conversion from real-world units (cm) to pixels.
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
    # If calibration is missing or unrecognized, prompt the user for pixel dimensions in mm
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

# --- Step 2b: Create large 200 cm² ROI for manual positioning ---
# This ROI is used to measure the central signal of the phantom.
radius_large = area_to_radius_pixels(200.0, pixel_width_cm, pixel_height_cm)
center_x = imp.getWidth() / 2.0
center_y = imp.getHeight() / 2.0
roi_large = OvalRoi(center_x - radius_large, center_y - radius_large, radius_large*2, radius_large*2)
imp.setRoi(roi_large)

# Add the large ROI to the ROI Manager
rm = RoiManager.getInstance()
if rm is None:
    rm = RoiManager()
rm.reset()  # Clears any old ROIs
rm.addRoi(roi_large)

dlg = WaitForUserDialog("Position large ROI (200 cm^2)",
    "Move the large ROI to the desired location. \nClick OK when done.")
dlg.show()

mean_ref = measure_roi_mean(imp)
IJ.log("Initial mean (large ROI): {:.3f}".format(mean_ref))

# --- Step 3: Manual Windowing Adjustment ---
# The window is manually adjusted by the user to better visualize the faint ghosting artifacts.
# Automatically reduce the window to a minimum
l=5.0
w=50.0
min_display = l - (w / 2)  # 0
max_display = l + (w / 2)  # 2000
IJ.setMinAndMax(imp, min_display, max_display)

# Open the W&L window with pre-configured settings
IJ.run("Brightness/Contrast...")
IJ.run("Window/Level...")

dlg = WaitForUserDialog("Manual adjustment - windowing",
    "Increase the window value until the background of the image becomes illuminated (~50)")
dlg.show()

# --- Step 4 to 7: Measure Signal from Ghosting Regions ---
# These steps create and measure four elliptical ROIs at a specific offset from the phantom center.
# The signal from these ROIs is used to calculate the ghosting ratio.

# Step 4: Right ROI
offset_x_dir = int(imp.getWidth() * 0.25)  # 25% to the right
right=create_adjust_roi(
    imp,
    length_cm=1.5,
    height_cm=20.0,
    disp_x_px=offset_x_dir,
    disp_y_px=0,
    title="Right ROI",
    message="Adjust the ROI to the region to the right of the phantom."
)

# Step 5: Bottom ROI
offset_y_baixo = int(imp.getHeight() * 0.25)  # 25% to the bottom
btm=create_adjust_roi(
    imp,
    length_cm=20.0,
    height_cm=1.5,
    disp_x_px=0,
    disp_y_px=offset_y_baixo,
    title="Bottom ROI",
    message="Adjust the ROI to the region below the phantom."
)

# Step 6: Top ROI
offset_y_cima = -int(imp.getHeight() * 0.25)  # 25% to the top
top=create_adjust_roi(
    imp,
    length_cm=20.0,
    height_cm=1.5,
    disp_x_px=0,
    disp_y_px=offset_y_cima,
    title="Top ROI",
    message="Adjust the ROI to the region above the phantom."
)

# Step 7: Left ROI
offset_x_esq = -int(imp.getWidth() * 0.25)  # 25% to the left
left=create_adjust_roi(
    imp,
    length_cm=1.5,
    height_cm=20.0,
    disp_x_px=offset_x_esq,
    disp_y_px=0,
    title="Left ROI",
    message="Adjust the ROI to the region to the left of the phantom."
)


# --- Step 8: Calculate Ghosting Ratio ---
if (mean_ref) == 0:
    IJ.log("Error: Mean Pixel Value in the Central ROI == 0, unable to calculate GR.")
else:
    # The GR formula is ((top - bottom) - (left + right)) / (2 * central_mean) * 100
    GR = abs((((top - btm)-(left+right))*100) / (2.0*mean_ref))
    IJ.log("Ghosting Ratio calculated: {:.10f}%".format(GR))
    IJ.log("{:.10f}%".format(GR))

# --- Finalization ---
# Prompt the user to close the ROI Manager and finish the process.
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
close_wl()

IJ.run("Clear Results")
IJ.log("---- End of Percentage Signal Ghosting Test ----")
IJ.log("")
