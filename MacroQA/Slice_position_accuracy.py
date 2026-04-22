# --- MacroQA File Header ---
# Project: MacroQA - An ImageJ Macro for ACR MRI Quality Assurance
# File: Slice_position_accuracy.py
# Version 1.0.3
# Source: https://github.com/icaroafoliveira/Macros_MRI_QA_phantom_ACR
# ---------------------------

# Macro to perform the Slice Position Accuracy Test on an ACR phantom MRI scan.
# This test checks for discrepancies between the prescribed and actual slice locations.
# The user is guided to measure the height difference between two vertical bars on slices 1 and 11
# of a T1-weighted image, which corresponds to the slice mis-positioning.

# Required libraries
from ij import IJ, WindowManager
from ij.gui import WaitForUserDialog, Roi, GenericDialog
from ij.io import OpenDialog
from java.lang import Math
from java.awt import Font
from ij.measure import ResultsTable
from ij.process import ImageStatistics
import math
import os
import csv


# === All functions used in the script are defined here ===

# === Function to close the W&L window if open ===
def close_wl():
    """Closes any open 'Brightness/Contrast' or 'Window/Level' dialogs."""
    # brightness/contrast window management
    candidates = ["Brightness/Contrast", "W&L", "Window/Level", "B&C"]
    for t in candidates:
        w = WindowManager.getWindow(t) or WindowManager.getFrame(t)
        if w is not None:
            # close without asking
            try:
                w.dispose()    # close the window
            except:
                try:
                    w.setVisible(False)
                except:
                    pass
            return True
    # fallback: check non-image windows and close if name it equal
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

# === Function to close the Results window if open ===
def close_result():
    """Closes the 'Results' window if it is open."""
    # Get Window only if it exists
    if WindowManager.getWindow("Results") is not None:
        IJ.selectWindow("Results")
        IJ.run("Close")

# === Function to zoom to a rectangle in pixels ===
def zoom_to_rect_pixels(x, y, w, h, set_line_tool=True, clear_roi_after=True):
    """
    Zooms in on a specified rectangular area in pixels.
    Optionally, activates the line tool and clears the ROI after zooming.
    """
    imp = IJ.getImage()
    imp.setRoi(Roi(int(x), int(y), int(w), int(h)))
    # Native ImageJ Command: Image ▸ Zoom ▸ To Selection
    IJ.run(imp, "To Selection", "")
    if set_line_tool:
        IJ.setTool("line")
    if clear_roi_after:
        imp.killRoi()

# === Function to get the measurement from the user-drawn line ===
def get_measurement(imp):
    """
    Prompts the user to draw a line and measures its length.
    The length is then signed based on the measurement of both bars, first the left bar and then the right bar.
    """
    
    # set tool line and waits the user
    IJ.setTool("line")
    
    # Step 1: Prompt user to draw a line and measure it
    
    while True:
        WaitForUserDialog("Draw a straight line in the Left vertical bar.").show()
        roi1 = imp.getRoi()
        if roi1 is None or roi1.getType() != Roi.LINE:
            IJ.showMessage("Invalid ROI", "The drawn ROI is not a straight line.")
            continue
        imp.setRoi(roi1)
        IJ.run("Measure")
        length1 = roi1.getLength()
        break
    
    IJ.log("   {}:  {:.3f}".format("Left bar", length1))
    
    # Step 2: Prompt user to draw a line in the right bar and measure it
    while True:
        WaitForUserDialog("Draw a straight line in the Right vertical bar.").show()
        roi2 = imp.getRoi()
        if roi2 is None or roi2.getType() != Roi.LINE:
            IJ.showMessage("Invalid ROI", "The drawn ROI is not a straight line.")
            continue
        imp.setRoi(roi2)
        IJ.run("Measure")
        length2 = roi2.getLength()
        break
      
    IJ.log("   {}:  {:.3f}".format("Right bar", length2))
    
    diff = length2 - length1
    
    IJ.log("   {}:  {:.3f}".format("Length difference (Right - Left)", diff))
    
    return diff

# === Function to open a DICOM file via dialog ===
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
        IJ.error("Fail to open the image.")
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

# === function to check limits for PASS/FAIL ===
def check_limits(value, expected):
    """Checks if the value meets the threshold for PASS/FAIL.
    Returns "PASS" if value is within tolerance of expected, otherwise "FAIL".
    """
    tol = 5  # Tolerance of 5 mm for slice position accuracy, as per ACR guidelines
    if value is None:
        return "NaN"
    try:
        return "PASS" if abs(value - expected) <= tol else "FAIL"
    except Exception:
        return "Error"

# --- Main Script Execution ---

IJ.log("========================================")
IJ.log("TEST: Slice Position Accuracy ")
IJ.log("========================================")
IJ.log("")
IJ.log("[SETUP]")

WaitForUserDialog("Open the T1 or T2 image to proceed with the test.").show()
imp = open_dicom_file("Select T1-weighted or T2-weighted DICOM image")

# Verify if image is opened
if imp is None:
    IJ.error("No image opened.")
    raise SystemExit

# Extract DICOM metadata (exam date and station name)
exam_date = "N/A"
info = imp.getInfoProperty()

if info is not None:
	try:
		# Extract exam date (0008,0020)
		date_start = info.find("0008,0020")
		if date_start != -1:
			date_value_start = info.find(":", date_start) + 1
			date_end = info.find("\n", date_value_start)
			exam_date = info[date_value_start:date_end].strip()
	except:
		pass
	

IJ.log("Exam Date: " + exam_date)
IJ.log("")

printImageType(imp)

# --- Process First Slice (Slice 1) ---
# Go to first slice
if imp.getNSlices() <= 11:
    imp.setSlice(1)
elif imp.getNSlices() > 11:
    dlg = WaitForUserDialog(
        "This image has more than 11 slices, assuming it is a Multi-Echo T2-weighted image.\n"
        "Select the slice that shows the bars (usually slice 2 or 12).")
    dlg.show()
    # choose slice
    slice_num = IJ.getNumber("Enter the slice number to analyze (1 to %d):" % imp.getNSlices(), 1)
    if slice_num is None or slice_num < 1 or slice_num > imp.getNSlices():
        IJ.error("Invalid slice number.")
        raise SystemExit
    imp.setSlice(int(slice_num))
    IJ.log("Slice set to %d." % int(slice_num))
    

IJ.run(imp, "Original Scale", "")
# Adjust window/level to central values
IJ.resetMinAndMax(imp)

# 2x Zoom "+" for better visibility
IJ.run("In [+]", "")
IJ.run("In [+]", "")

# Adjust Window/Level: window = 10, level = 1000
IJ.run("Window/Level...")

# usually the window/level gets stuck, so we run both commands to ensure it opens 
IJ.run("Brightness/Contrast...")
IJ.run("Window/Level...")

# Zoom to a specific region of interest to guide the user to the bars
zoom_to_rect_pixels(x = 100, y = 65, w = 80, h = 10)

# Provide instructions and wait for user action
gd = GenericDialog("Slice position accuracy instructions")
gd.addMessage("Slice Position Accuracy Test: Procedure and interpretation", Font("SansSerif", Font.BOLD, 18))
gd.addMessage("STEP 1: Adjust the Window/Level (W/L)", Font("SansSerif", Font.BOLD, 14))
gd.addMessage("To distinguish the bars from the background, adjust W/L:", Font("SansSerif", Font.PLAIN, 14))
gd.addMessage("- Set the Window close to minimum (e.g., 20).\n"
              "- Shift the Level also towards lower values.\n"
              "- The slope line in the histogram should then appear nearly vertical at the left edge.", Font("SansSerif", Font.ITALIC, 12))
gd.addMessage("STEP 2: Position the measurement tool", Font("SansSerif", Font.BOLD, 14))
gd.addMessage("- Position the measurement tool to the center of longest bar, aiming to measure the length difference between both bars.", Font("SansSerif", Font.ITALIC, 14))
gd.addMessage("STEP 3: Interpretation", Font("SansSerif", Font.BOLD, 14))
gd.addMessage("- If the bar on the right is longer, the slice is mis-positioned superiorly; this bar length difference is assigned a positive value.\n"
              "- If the bar on the left is longer, meaning the slice is mis-positioned inferiorly; this bar length difference is assigned a negative value.\n"
              "- A zero difference indicates perfect positioning.", Font("SansSerif", Font.ITALIC, 14))
gd.addMessage("Click 'OK' to continue.", Font("SansSerif", Font.ITALIC, 16))
# Best-effort: hide the Cancel button so only OK is visible.
try:
    # Preferred: if GenericDialog exposes getButtons()
    buttons = gd.getButtons()
    for b in buttons:
        try:
            lbl = b.getLabel()
        except:
            lbl = ""
        if lbl and lbl.lower().startswith("cancel"):
            b.setVisible(False)
except:
    try:
        # Fallback: some ImageJ builds expose cancelButton attribute
        if getattr(gd, "cancelButton", None) is not None:
            gd.cancelButton.setVisible(False)
    except:
        # If neither approach works, ignore and show dialog normally
        pass
gd.showDialog()

WaitForUserDialog("Slice 1 - Draw the vertical straight line to get the height difference between the bars.\n"
"Press 'OK' only after drawing the straight line.").show()

# Set log measurements
IJ.log("")
IJ.log("[MEASUREMENTS]")
IJ.log("")
IJ.log("Slice 1:")
IJ.log("")

measurement1 = get_measurement(imp)

# --- Process Eleventh Slice (Slice 11) ---

IJ.log("Slice 11:")

if imp.getNSlices() < 11:
    IJ.error("Additional measurements require slice 11, but the selected image has only {} slices.".format(imp.getNSlices()))
    imp.close()
    imp = open_dicom_file("Select ACR T1-weighted DICOM image (slice 11)")
    if imp is None:
        raise SystemExit
    IJ.log("New image opened.")
elif imp.getNSlices() == 11:
    IJ.log("Image has exactly 11 slices; proceeding to slice 11.")
    # Go to 11th slice
    imp.setSlice(11)
else:
    dlg = WaitForUserDialog(
        "This image has more than 11 slices, assuming it is a Multi-Echo T2-weighted image.\n"
        "Select the slice that shows the bars (usually slice 11 or 22).")
    dlg.show()
    # choose slice
    slice_num = IJ.getNumber("Enter the slice number to analyze (1 to %d):" % imp.getNSlices(), 22)
    if slice_num is None or slice_num < 1 or slice_num > imp.getNSlices():
        IJ.error("Invalid slice number.")
        raise SystemExit
    imp.setSlice(int(slice_num))
    IJ.log("Slice set to %d." % int(slice_num))

WaitForUserDialog("Slice 11 - Draw the vertical straight line to get the height difference between the bars.\n").show()
measurement2 = get_measurement(imp)

# --- Finalization and Results ---

try:
    fi = imp.getOriginalFileInfo()
    image_dir = os.path.dirname(fi.directory)
except:
    image_dir = os.getcwd()
    
imp.close()
close_wl()
close_result()

WaitForUserDialog("Slice Position Accuracy Test finished. Collect the results.\n").show()

IJ.run("Clear Results")
IJ.log("")
IJ.log("[RESULTS]")
IJ.log("")
IJ.log("Slice 1:")
IJ.log("   Measured:  {:.3f} mm".format(measurement1))
IJ.log("   Expected:  +/- 5 mm")
IJ.log("   Result:    [{}]".format(check_limits(measurement1, 0)))
IJ.log("")
IJ.log("Slice 11:")
IJ.log("   Measured:  {:.3f} mm".format(measurement2))
IJ.log("   Expected:  +/- 5 mm")
IJ.log("   Result:    [{}]".format(check_limits(measurement2, 0)))
IJ.log("")
IJ.log("[OUTPUT]")

# Save in CSV
if 'measurement1' in locals() and 'measurement2' in locals():
	
	csv_filename = os.path.join(image_dir, "QA_Results_{0}.csv".format(exam_date))
	
	try:
		file_exists = os.path.isfile(csv_filename)
		
		with open(csv_filename, 'a') as f:
			writer = csv.writer(f)
			
			m1_str = "{:.3f}".format(measurement1) if 'measurement1' in locals() else "NaN"
			m2_str = "{:.3f}".format(measurement2) if 'measurement2' in locals() else "NaN"
			
			writer.writerow(['Slice_Position_Accuracy_Slice1_mm', m1_str])
			writer.writerow(['Slice_Position_Accuracy_Slice11_mm', m2_str])
		
		IJ.log("Results saved to: {}".format(csv_filename))
	except Exception as e:
		IJ.log("Error saving CSV: {}".format(str(e)))
else:
	IJ.log("Warning: Could not save CSV (measurement values not found)")
IJ.log("")
