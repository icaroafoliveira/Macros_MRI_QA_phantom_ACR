# --- MacroQA File Header ---
# Project: MacroQA - An ImageJ Macro for ACR MRI Quality Assurance
# File: Geometric_accuracy.py
# Version 1.0.3
# Source: https://github.com/icaroafoliveira/Macros_MRI_QA_phantom_ACR
# ---------------------------

# Macro to perform the Geometric Accuracy test of the ACR MRI phantom.
# The script assumes that the user will select the Localizer image first (single slice)
# and then the ACR T1-weighted image (multi-slice).
# The user is prompted to draw straight-line ROIs on specific slices and orientations.
# The lengths of the lines are measured and printed in the log.


from ij import IJ, WindowManager
from ij.io import OpenDialog
from ij.measure import ResultsTable
from ij.gui import WaitForUserDialog, Roi
import sys
import os
import csv
import math

# === All functions used in the script are defined here ===
# === Function to open DICOM files ===
def open_dicom_file(prompt):
    """Open a file chooser to select a DICOM file.

    Returns the ImagePlus object, or ``None`` if the operation is canceled or fails.
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

# === Function to perform line measurements ===
def get_measurement(imp, instruction):
    """Prompt the user to draw a straight-line ROI on the given image.

    Measures the length of the line and returns it.
    """
    # Loop until we get a valid straight-line ROI or the user cancels.
    while True:
        # Prompt the user to draw a straight line on the image.
        wait = WaitForUserDialog("Draw a straight line and click OK to perform the measurement.", instruction)
        wait.show()

        roi = imp.getRoi()

        # If a valid line ROI was drawn, perform the measurement and return it.
        if roi is not None:
            try:
                if roi.getType() == Roi.LINE:
                    # Clear previous results to avoid reading stale entries.
                    IJ.run("Clear Results")
                    IJ.run("Set Measurements...", "length")
                    IJ.run(imp, "Measure", "")

                    rt = ResultsTable.getResultsTable()
                    if rt is None or rt.size() == 0:
                        IJ.log("Measurement failed: no results were produced.")
                        # Offer retry
                        retry = IJ.showMessageWithCancel("Measurement failed", "No measurement was recorded. Click OK to retry or Cancel to abort.")
                        if retry:
                            continue
                        else:
                            return None

                    length = rt.getValue("Length", rt.size() - 1)
                    IJ.log("   Length: {:.3f}".format(length))
                    return length
            except Exception:
                # In case roi.getType() or other calls fail, fall through to retry/cancel.
                pass

        # If we get here, the ROI is invalid or missing. Ask user to retry or cancel.
        retry = IJ.showMessageWithCancel("Invalid ROI", "Please draw a valid straight-line ROI. Click OK to retry or Cancel to abort.")
        if retry:
            # Loop to allow user to redraw the ROI
            continue
        else:
            # User chose to cancel the measurement
            return None

# === Function to close the Results window if open ===
def close_result():
    """
    Closes the "Results" window if it exists.
    """
    # only try if it exists
    if WindowManager.getWindow("Results") is not None:
        IJ.selectWindow("Results")
        IJ.run("Close")

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

def fmt(val):
    """Format a numeric measurement value or return 'NaN' for None."""
    if val is None:
        return 'NaN'
    try:
        return "{:.3f}".format(val)
    except Exception:
        return str(val)

# === function to check limits for PASS/FAIL ===
def check_limits(value, expected):
    """Checks if the value meets the threshold for PASS/FAIL.
    Returns "PASS" if value is within tolerance of expected, otherwise "FAIL".
    """
    tol = 3
    if value is None:
        return "NaN"
    try:
        return "PASS" if abs(value - expected) <= tol else "FAIL"
    except Exception:
        return "Error"
        
# === MAIN SCRIPT ===
IJ.log("========================================")
IJ.log("TEST: Geometric Accuracy")
IJ.log("========================================")
IJ.log("")
IJ.log("[SETUP]")
IJ.log("")

# === LOCALIZER measurements ===
WaitForUserDialog("Click OK to select the Localizer image.").show()
localizer = open_dicom_file("Select LOCALIZER image (single slice)")
if localizer is None:
    sys.exit()

# Extract DICOM metadata (exam date and station name)
exam_date = "N/A"
info = localizer.getInfoProperty()

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
# Print image type
printImageType(localizer)
IJ.log("Tolerance limit: +/- 3 mm")
IJ.log("")
IJ.log("[MEASUREMENTS]")
IJ.log("")
IJ.log("Localizer")
# Zoom in a couple of times for better precision
IJ.setTool("line")
IJ.run("In [+]", "")
IJ.run("In [+]", "")
localizer_measurement = get_measurement(localizer, "LOCALIZER: Draw a straight VERTICAL line. Click OK to perform the measurement.")
localizer.close()

# === T1w measurements ===

WaitForUserDialog("Click OK to select the ACR T1w image.").show()
t1w = open_dicom_file("Select ACR T1-weighted DICOM image")
if t1w is None:
    sys.exit()

# Zoom in a couple of times for better precision
IJ.run("In [+]", "")
IJ.run("In [+]", "")

# --- Slice 1 ---
t1w.setSlice(1)
IJ.log("")
IJ.log("ACR T1w - Slice 1")

t1_vert = get_measurement(t1w, "Slice 1: Draw a straight VERTICAL line. Click OK to perform the measurement.")
t1_horz = get_measurement(t1w, "Slice 1: Draw a straight HORIZONTAL line. Click OK to perform the measurement.")

# --- Slice 5 ---
slices = t1w.getNSlices()     # z dimension
if slices < 5:
    IJ.error("Additional measurements require slice 5, but the selected image has only {} slices.".format(slices))
    t1w.close()
    WaitForUserDialog("Click OK to select the ACR T1w image.").show()
    t1w = open_dicom_file("Select ACR T1-weighted DICOM image (slice 5)")
    IJ.log("ACR T1w - Slice 5")
    if t1w is None:
        sys.exit()

    # Print image type
    printImageType(t1w)

    # Zoom in a couple of times for better precision
    IJ.run("In [+]", "")
    IJ.run("In [+]", "")
else:
    t1w.setSlice(5)
    IJ.log("")
    IJ.log("ACR T1w - Slice 5")

t1_diag1 = get_measurement(t1w, "Slice 5: Draw a straight DIAGONAL line (Diagonal 1). Click OK to perform the measurement.")
t1_diag2 = get_measurement(t1w, "Slice 5: Draw a straight DIAGONAL line (Diagonal 2). Click OK to perform the measurement.")
t1_vert_5 = get_measurement(t1w, "Slice 5: Draw a straight VERTICAL line. Click OK to perform the measurement.")
t1_horz_5 = get_measurement(t1w, "Slice 5: Draw a straight HORIZONTAL line. Click OK to perform the measurement.")

# Capture image directory before closing
try:
    fi = t1w.getOriginalFileInfo()
    image_dir = os.path.dirname(fi.directory)
except:
    image_dir = os.getcwd()

t1w.close()

# === LOG FINAL ===
IJ.log("")
IJ.log("[RESULTS]")
IJ.log("")
IJ.log("{:<25} {:<15} {:<15} {:<10}".format("Measurement", "Value [mm]", "Expected [mm]", "Result"))
IJ.log("-" * 68)
IJ.log("{:<25} {:<15} {:<15} {:<10}".format("Localizer (Vertical)", fmt(localizer_measurement), "148", check_limits(localizer_measurement, 148)))
IJ.log("{:<25} {:<15} {:<15} {:<10}".format("T1 Slice 1 - Vertical", fmt(t1_vert), "190", check_limits(t1_vert, 190)))
IJ.log("{:<25} {:<15} {:<15} {:<10}".format("T1 Slice 1 - Horizontal", fmt(t1_horz), "190", check_limits(t1_horz, 190)))
IJ.log("{:<25} {:<15} {:<15} {:<10}".format("T1 Slice 5 - Diagonal 1", fmt(t1_diag1), "190", check_limits(t1_diag1, 190)))
IJ.log("{:<25} {:<15} {:<15} {:<10}".format("T1 Slice 5 - Diagonal 2", fmt(t1_diag2), "190", check_limits(t1_diag2, 190)))
IJ.log("{:<25} {:<15} {:<15} {:<10}".format("T1 Slice 5 - Vertical", fmt(t1_vert_5), "190", check_limits(t1_vert_5, 190)))
IJ.log("{:<25} {:<15} {:<15} {:<10}".format("T1 Slice 5 - Horizontal", fmt(t1_horz_5), "190", check_limits(t1_horz_5, 190)))
IJ.log("")


IJ.log("[OUTPUT]")

# Save in CSV - check each variable directly
if (localizer_measurement is not None and t1_vert is not None and 
    t1_horz is not None and t1_diag1 is not None and t1_diag2 is not None and 
    t1_vert_5 is not None and t1_horz_5 is not None):
    csv_filename = os.path.join(image_dir, "QA_Results_{0}.csv".format(exam_date))
    
    try:
        file_exists = os.path.isfile(csv_filename)
        
        with open(csv_filename, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(['Geometric_Localizer_Vertical_mm', fmt(localizer_measurement)])
            writer.writerow(['Geometric_T1_Slice1_Vertical_mm', fmt(t1_vert)])
            writer.writerow(['Geometric_T1_Slice1_Horizontal_mm', fmt(t1_horz)])
            writer.writerow(['Geometric_T1_Slice5_Diagonal1_mm', fmt(t1_diag1)])
            writer.writerow(['Geometric_T1_Slice5_Diagonal2_mm', fmt(t1_diag2)])
            writer.writerow(['Geometric_T1_Slice5_Vertical_mm', fmt(t1_vert_5)])
            writer.writerow(['Geometric_T1_Slice5_Horizontal_mm', fmt(t1_horz_5)])
        
        IJ.log("Results saved to: {}".format(csv_filename))
    except Exception as e:
        IJ.log("Error saving CSV: {}".format(str(e)))
else:
    IJ.log("Warning: Could not save CSV (some measurements not found)")

IJ.log("")
WaitForUserDialog("Geometric accuracy test finished. Please collect the results.").show()
close_result()

IJ.run("Clear Results")
