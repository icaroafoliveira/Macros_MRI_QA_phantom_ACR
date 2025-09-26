# --- MacroQA File Header ---
# Project: MacroQA - An ImageJ Macro for ACR MRI Quality Assurance
# File: Low_contrast_objective_detectability.py
# Version 1.0.0
# Source: https://github.com/icaroafoliveira/Macros_MRI_QA_phantom_ACR
# ---------------------------

# Macro to perform the Low Contrast Objective Detectability test of the ACR MRI phantom.
# The script assumes that the user will select the T1-weighted image first (multi-slice or selecting 4 single slices)
# and then the T2-weighted image (multi-slice or selecting 4 single slices).
# The user is prompted to analyze specific slices and enter the number of complete spokes.
# Results are printed to the log.

from ij import IJ, WindowManager, ImagePlus, ImageStack
from ij.io import OpenDialog
from ij.measure import ResultsTable
from ij.gui import WaitForUserDialog
import java
from ij.measure import Measurements
from ij.process import ImageStatistics
from ij.gui import GenericDialog
from java.awt import Font
import math
from javax.swing import JFileChooser
from java.io import File

# === All functions used in the script are defined here ===

# === Function to calculate optimal window/level based on histogram analysis ===
def calculate_window_level(imp):
    """Calculate optimal window and level based on histogram analysis.
    
    Returns (level, window) or (None, None) if calculation fails.
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

    # Calculate the true median
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

# === Function to close any open Brightness/Contrast or Window/Level dialogs ===
def close_wl():
    """
    Closes any open Brightness/Contrast or Window/Level dialogs.
    """
    
    # Common titles for these windows
    candidates = ["Brightness/Contrast", "W&L", "Window/Level", "B&C"]
    for t in candidates:
        w = WindowManager.getWindow(t) or WindowManager.getFrame(t)
        if w is not None:
            # close without prompting
            try:
                w.dispose()   # close the window
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

CANCEL_SENTINEL = float(-2147483648.0)

def get_number_or_nan(prompt, default=1.0):
    v = IJ.getNumber(prompt, default)
    if v == CANCEL_SENTINEL or (isinstance(v, float) and math.isnan(v)):
        return float('nan')
    return v

# === Function to open a DICOM file ===
def open_dicom_file(prompt):
    """Opens a file chooser dialog to select a DICOM file.
    
    Returns the ImagePlus object or None if the operation is canceled or fails.
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

# === Function to open multiple single-slice DICOM files ===
def open_multiple_dicom_files():
    """Opens a file chooser dialog to select multiple DICOM files and combines them into a single stack.
    
    Returns the combined ImagePlus object or None if the operation is canceled or fails.
    """
    # File chooser with multi-selection
    fc = JFileChooser()
    fc.setMultiSelectionEnabled(True)
    fc.setDialogTitle("Select 4 images: slices 8, 9, 10, and 11.")

    if fc.showOpenDialog(None) == JFileChooser.APPROVE_OPTION:
        files = fc.getSelectedFiles()

        if len(files) != 4:
            IJ.showMessage("Please select exactly 4 images: slices 8, 9, 10, and 11.")
            return None
        else:
            # Sort files by name to maintain expected slice order (in case chooser
            # returns them unordered).
            files = sorted(files, key=lambda f: f.getName())

            stack = None
            for i, f in enumerate(files):
                imp = IJ.openImage(f.getAbsolutePath())
                printImageType(imp)
                if stack is None:
                    stack = ImageStack(imp.getWidth(), imp.getHeight())
                stack.addSlice("Image {}".format(i+1), imp.getProcessor())
            result = ImagePlus("4-slice Stack", stack)
            result.show()

            # Return the combined ImagePlus so the caller can navigate slices
            return result

# === Show dialog for DICOM type RadioButton options ===
def show_dicom_type_dialog():
    """Creates and displays a dialog box with three DICOM options: Enhanced, Multi-Frame, and Single-Frame.
    
    Returns the user's selected option and the multi-echo choice, or None if the dialog is canceled.
    """

    gd = GenericDialog("DICOM Type Selection")

    # Check DICOM type
    gd.addMessage("Select the type of DICOM image:")
    gd.addRadioButtonGroup("DICOM Type:", ["Enhanced", "Multi-Frame", "Single-Frame"], 1, 3, "Enhanced")

    # Check if the data is Multi-Echo
    gd.addMessage("Select whether the data contains two echoes:")
    gd.addRadioButtonGroup("Multi-Echo:", ["Yes", "No"], 1, 2, "No")

    gd.setFont(Font("SansSerif", Font.PLAIN, 12))
    gd.showDialog()

    if gd.wasCanceled():
        return None

    dicom_choice = gd.getNextRadioButton()
    multi_echo_choice = gd.getNextRadioButton()

    return dicom_choice, multi_echo_choice


# === Function to select and open a DICOM file ===
def select_and_open_dicom(prompt, image_type_label=""):
    """Prompts the user to select a DICOM type and opens the corresponding DICOM file(s).
    
    Returns the ImagePlus object, DICOM type, and multi-echo choice."""

    # Identification of DICOM type
    dcm_type, is_multi_echo = show_dicom_type_dialog()

    if dcm_type is None:
        IJ.error("Dialog was canceled. Exiting.")
        raise SystemExit
    elif dcm_type == "Enhanced":
        IJ.log("DICOM Type selected: Enhanced")
        WaitForUserDialog(prompt).show()
        imp = open_dicom_file("Select the Enhanced DICOM image.")
        if imp is None:
            IJ.error("No image open.")
            raise SystemExit
        printImageType(imp)
    elif dcm_type == "Multi-Frame":
        IJ.log("DICOM Type selected: Multi-Frame")
        WaitForUserDialog(prompt).show()
        imp = open_dicom_file("Select the Multi-Frame DICOM image.")
        if imp is None:
            IJ.error("No image open.")
            raise SystemExit
        printImageType(imp)
    elif dcm_type == "Single-Frame":
        IJ.log("DICOM Type selected: Single-Frame")
        imp = open_multiple_dicom_files()
        if imp is None:
            IJ.error("No image open.")
            raise SystemExit
        # printImageType(imp) # Already printed inside the function

    return imp, dcm_type, is_multi_echo

# === End of function definitions ===

# --- Main script starts here ---
IJ.log("---- Start of Low Contrast Objective Detectability Test ----")

# --- T1 weighted image ---
# Identification of DICOM type
imp, dcm_type, is_multi_echo = select_and_open_dicom("Click OK to select the T1 image")

# Handling Window/Level: window = 850, level = 1900
IJ.run("In [+]","")
IJ.run("In [+]","")
IJ.run("Brightness/Contrast...")
IJ.run("Window/Level...")

# Enhanced and Multi-Frame will open at slice 8 by default
# Single-Frame stack may open at slice 1
if dcm_type == "Single-Frame":
    slice_to_start = 1
else:
    slice_to_start = 8

imp.setSlice(slice_to_start)
level, window = calculate_window_level(imp)

if level is not None:
    # Manual adjustment for T1 image
    level += 1480
    window *= 0.8

    # Apply to the image
    min_display = level - window / 2.0
    max_display = level + window / 2.0
    imp.setDisplayRange(min_display, max_display)
    imp.updateAndDraw()

# Prompt user to perform the analysis for each slice
WaitForUserDialog("Slice 8 - Perform the analysis and click OK").show()
t1_slice8 = get_number_or_nan("Enter the number of complete spokes in slice 8:", 10.0)

# Move to slice 9
imp.setSlice(slice_to_start + 1)
WaitForUserDialog("Slice 9 - Perform the analysis and click OK").show()
t1_slice9 = get_number_or_nan("Enter the number of complete spokes in slice 9:", 10.0)

# Move to slice 10
imp.setSlice(slice_to_start + 2)
WaitForUserDialog("Slice 10 - Perform the analysis and click OK").show()
t1_slice10 = get_number_or_nan("Enter the number of complete spokes in slice 10:", 10.0)

# Move to slice 11
imp.setSlice(slice_to_start + 3)
level, window = calculate_window_level(imp)

if level is not None:
    # Adjustment for T1 image
    level += 1380
    window *= 0.85

    # Apply to the image
    min_display = level - window / 2.0
    max_display = level + window / 2.0
    imp.setDisplayRange(min_display, max_display)
    imp.updateAndDraw()
    close_wl()
    IJ.run("Brightness/Contrast...")
    IJ.run("Window/Level...")

WaitForUserDialog("Slice 11 - Perform the analysis and click OK").show()
t1_slice11 = get_number_or_nan("Enter the number of complete spokes in slice 11:", 10.0)
imp.close()

# --- T2 weighted image ---

# Identification of DICOM type
imp2, dcm_type, is_multi_echo = select_and_open_dicom("Click OK to select the T2 image")

IJ.run("In [+]","")
IJ.run("In [+]","")
# Reset Window/Level
IJ.run("Window/Level...")

# Enhanced and Multi-Frame will open at slice 8 by default
# Single-Frame stack may open at slice 1
# Enhanced + ME data are interleaved, so the slice moves at even numbers
if dcm_type == "Single-Frame":
    slice_to_start = 1
    steps = 1
elif dcm_type == "Enhanced" and is_multi_echo == "Yes":
    slice_to_start = 16
    steps = 2
elif dcm_type == "Multi-Frame" and is_multi_echo == "Yes":
    slice_to_start = 16
    steps = 2
else:
    slice_to_start = 8
    steps = 1

imp2.setSlice(slice_to_start)
level, window = calculate_window_level(imp2)

if level is not None:
    # Adjustment for T2 image (different values)
    level += 1100
    window *= 1.1

    # Apply to the image
    min_display = level - window / 2.0
    max_display = level + window / 2.0
    imp2.setDisplayRange(min_display, max_display)
    imp2.updateAndDraw()

WaitForUserDialog("Slice 8 - Perform the analysis and click OK").show()
t2_slice8 = get_number_or_nan("Enter the number of complete spokes in slice 8:", 10.0)

# Move to next slice
imp2.setSlice(slice_to_start + 1*steps)
WaitForUserDialog("Slice 9 - Perform the analysis and click OK").show()
t2_slice9 = get_number_or_nan("Enter the number of complete spokes in slice 9:", 10.0)

# Move to next slice
imp2.setSlice(slice_to_start + 2*steps)
WaitForUserDialog("Slice 10 - Perform the analysis and click OK").show()
t2_slice10 = get_number_or_nan("Enter the number of complete spokes in slice 10:", 10.0)

# Move to next slice
imp2.setSlice(slice_to_start + 3*steps)
level, window = calculate_window_level(imp2)

if level is not None:
    # Adjustment for T2 image (different values)
    level += 1000
    window *= 1.1

    # Apply to the image
    min_display = level - window / 2.0
    max_display = level + window / 2.0
    imp2.setDisplayRange(min_display, max_display)
    imp2.updateAndDraw()
    close_wl()
    IJ.run("Brightness/Contrast...")
    IJ.run("Window/Level...")

WaitForUserDialog("Slice 11 - Perform the analysis and click OK").show()
t2_slice11 = get_number_or_nan("Enter the number of complete spokes in slice 11:", 10.0)
spheres_T1 = t1_slice8 + t1_slice9 + t1_slice10 + t1_slice11
spheres_T2 = t2_slice8 + t2_slice9 + t2_slice10 + t2_slice11
imp2.close()
close_wl()

WaitForUserDialog("Low Contrast Detail Test completed. Collect the results.").show()

IJ.run("Clear Results")
IJ.log("Number of complete spokes in T1: %s" % ("NaN" if (isinstance(spheres_T1, float) and math.isnan(spheres_T1)) else int(spheres_T1)))
IJ.log("Number of complete spokes in T2: %s" % ("NaN" if (isinstance(spheres_T2, float) and math.isnan(spheres_T2)) else int(spheres_T2)))
IJ.log("---- End of Low Contrast Objective Detectability Test ----")
IJ.log("")
