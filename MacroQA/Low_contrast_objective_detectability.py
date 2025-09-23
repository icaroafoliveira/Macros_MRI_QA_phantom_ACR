# Macro to perform the Low Contrast Objective Detectability Test on an ACR phantom MRI scan.
# The user must manually count the number of visible spheres in specific slices for both T1-weighted and T2-weighted images.
# The script guides the user through the process, automatically adjusting the display window/level for better visibility and logging the results.

# Required libraries
from ij import IJ, WindowManager
from ij.io import OpenDialog
from ij.measure import ResultsTable
from ij.gui import WaitForUserDialog
from ij import ImagePlus
import java
from ij.measure import Measurements
from ij.process import ImageStatistics
from ij.gui import GenericDialog
from java.awt import Font
import math


# --- Helper Functions ---

# Function to calculate an optimal window/level based on histogram analysis
# This function aims to automatically set a display range that highlights the low-contrast spheres.
def calcular_window_level(imp):
    """
    Calculates an optimal window and level for an image based on histogram analysis.
    This function analyzes the histogram to find a suitable display range,
    especially useful for low-contrast images.
    """
    stats = imp.getStatistics()
    hist = stats.histogram
    if hist is None:
        print("Histogram not available.")
        return None, None
    if callable(hist):
        hist = hist()

    hist_min = stats.histMin
    x_vals = [i + hist_min for i in range(len(hist))]
    y_vals = hist

    # Calculation of the true median
    total_pixels = sum(y_vals)
    cumulative = 0
    median_value = x_vals[-1]

    for i in range(len(y_vals)):
        cumulative += y_vals[i]
        if cumulative >= total_pixels / 2:
            median_value = x_vals[i]
            break

    # Filter data above the median with significant counts
    peak = max(y_vals)
    threshold = peak * 0.02

    x_fit = []
    y_fit = []
    for x, y in zip(x_vals, y_vals):
        if x > median_value and y >= threshold:
            x_fit.append(x)
            y_fit.append(y)

    if len(x_fit) < 2:
        print("Few significant points above the median.")
        return None, None

    level = (max(x_fit) + min(x_fit)) / 2.0
    window = max(x_fit) - min(x_fit)

    return level, window

# Function to close any open Brightness/Contrast or Window/Level dialogs
# This ensures that the macro operates cleanly without user intervention on these windows.
def fechar_wl():
    """Closes any open 'Brightness/Contrast' or 'Window/Level' dialogs."""
    # Common titles for this window
    candidatos = ["Brightness/Contrast", "W&L", "Window/Level", "B&C"]
    for t in candidatos:
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

CANCEL_SENTINEL = float(-2147483648.0)

def get_number_or_nan(prompt, default=1.0):
    v = IJ.getNumber(prompt, default)
    if v == CANCEL_SENTINEL or (isinstance(v, float) and math.isnan(v)):
        return float('nan')
    return v

# Function to open a DICOM file selected by the user
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

# Function to print the image type based on the number of slices
# This helps confirm that the user has selected the correct image sequence.
def printImageType(imp):
    """
    Checks the number of slices and prints the corresponding image type
    (Localizer, T1w, or T2w) to the log.
    """
    # Make sure that the image is the expected one
    # Localizer is a single-slice image
    # T1w has 11 slices
    # T2w has 22 slices (2 echo times)
      
    slices = imp.getNSlices()      # z dimension

    if slices < 11:
        IJ.log("Image Type: Localizer.")
    elif slices > 11:
        IJ.log("Image Type: ACR T2w image.")
    else:
        IJ.log("Image Type: ACR T1w image.")

# --- Main Script Execution ---

IJ.log("---- Start of Low Contrast Objective Detectability Test ----")    
WaitForUserDialog("Click OK to select the T1 image and perform the count of low-contrast spheres.").show()

# Open the T1-weighted image
imp = open_dicom_file("Select T1-weighted DICOM image (multi-slice)")

# Check if the image was successfully opened
if imp is None:
    IJ.error("No image open.")
    raise SystemExit

# Print image type for confirmation
printImageType(imp)

# --- Process T1-weighted image ---

# Zoom in for better visualization
IJ.run("In [+]","")
IJ.run("In [+]","")
IJ.run("Brightness/Contrast...")
IJ.run("Window/Level...")

# Go to slice 8
imp.setSlice(8)
level, window = calcular_window_level(imp)

if level is not None:
    # Manual adjustments for the T1 image to better highlight spheres
    level += 1480
    window *= 0.8

    # Apply the display range to the image
    min_display = level - window / 2.0
    max_display = level + window / 2.0
    imp.setDisplayRange(min_display, max_display)
    imp.updateAndDraw()

# Prompt user to perform the analysis for each slice
WaitForUserDialog("Slice 8 - Perform the analysis and click OK").show()
fatia8 = get_number_or_nan("Enter the number of visible spheres in slice 8:", 1.0)

# Repeat the process for slices 9, 10, and 11
imp.setSlice(9)
WaitForUserDialog("Slice 9 - Perform the analysis and click OK").show()
fatia9 = get_number_or_nan("Enter the number of visible spheres in slice 9:", 1.0)

imp.setSlice(10)
WaitForUserDialog("Slice 10 - Perform the analysis and click OK").show()
fatia10 = get_number_or_nan("Enter the number of visible spheres in slice 10:", 1.0)

imp.setSlice(11)
level, window = calcular_window_level(imp)

if level is not None:
    # Manual adjustments for T1 image, different for the last slice
    level += 1380
    window *= 0.85

    min_display = level - window / 2.0
    max_display = level + window / 2.0
    imp.setDisplayRange(min_display, max_display)
    imp.updateAndDraw()
    fechar_wl()
    IJ.run("Brightness/Contrast...")
    IJ.run("Window/Level...")
    
WaitForUserDialog("Slice 11 - Perform the analysis and click OK").show()
fatia11 = get_number_or_nan("Enter the number of visible spheres in slice 11:", 1.0)
imp.close()

# --- Process T2-weighted image ---

WaitForUserDialog("Open the T2-weighted image.").show()
t2w = open_dicom_file("Click OK to select the T2-weighted image.")
if t2w is None:
    exit()

# Get the newly opened image
imp2 = IJ.getImage()
if imp2 is None or imp2 == imp:
    IJ.error("No new image opened or the same image was reused.")
    raise SystemExit

# Print image type for confirmation
printImageType(imp2)

# Zoom in and reset display settings for the new image
IJ.run("In [+]","")
IJ.run("In [+]","")
IJ.run("Window/Level...")

# Go to slice 16
imp2.setSlice(16)
level, window = calcular_window_level(imp2)

if level is not None:
    # Manual adjustments for the T2 image (different values!)
    level += 1100
    window *= 1.1

    min_display = level - window / 2.0
    max_display = level + window / 2.0
    imp2.setDisplayRange(min_display, max_display)
    imp2.updateAndDraw()

# Prompt user for slices 16, 18, 20, and 22
WaitForUserDialog("Slice 16 - Perform the analysis and click OK").show()
fatia16 = get_number_or_nan("Enter the number of visible spheres in slice 16:", 1.0)

imp2.setSlice(18)
WaitForUserDialog("Slice 18 - Perform the analysis and click OK").show()
fatia18 = get_number_or_nan("Enter the number of visible spheres in slice 18:", 1.0)

imp2.setSlice(20)
WaitForUserDialog("Slice 20 - Perform the analysis and click OK").show()
fatia20 = get_number_or_nan("Enter the number of visible spheres in slice 20:", 1.0)

imp2.setSlice(22)
level, window = calcular_window_level(imp2)

if level is not None:
    # Manual adjustments for the T2 image, different for the last slice
    level += 1000
    window *= 1.1

    min_display = level - window / 2.0
    max_display = level + window / 2.0
    imp2.setDisplayRange(min_display, max_display)
    imp2.updateAndDraw()
    fechar_wl()
    IJ.run("Brightness/Contrast...")
    IJ.run("Window/Level...")
    
WaitForUserDialog("Slice 22 - Perform the analysis and click OK").show()
fatia22 = get_number_or_nan("Enter the number of visible spheres in slice 22:", 1.0)
esferas_T1 = fatia8 + fatia9 + fatia10 + fatia11
esferas_T2 = fatia16 + fatia18 + fatia20 + fatia22
imp2.close()
fechar_wl()

# --- Display Final Results ---

WaitForUserDialog("Low Contrast Detail Test completed, collect the results.").show()

IJ.run("Clear Results")
IJ.log("Number of spheres in T1: %s" % ("NaN" if (isinstance(esferas_T1, float) and math.isnan(esferas_T1)) else int(esferas_T1)))
IJ.log("Number of spheres in T2: %s" % ("NaN" if (isinstance(esferas_T2, float) and math.isnan(esferas_T2)) else int(esferas_T2)))
IJ.log("---- End of Low Contrast Objective Detectability Test ----")
IJ.log("")
