# --- MacroQA File Header ---
# Project: MacroQA - An ImageJ Macro for ACR MRI Quality Assurance
# File: Slice_thickness_accuracy.py
# Version 1.0.3
# Source: https://github.com/icaroafoliveira/Macros_MRI_QA_phantom_ACR
# ---------------------------

# Macro to perform the Slice Thickness Accuracy Test on an ACR phantom MRI scan.
# The user is guided to measure two inclined planes in a T1-weighted image
# to verify if the slice thickness is within the acceptable range.

# Required libraries
from ij import IJ, WindowManager
from ij.gui import Roi, WaitForUserDialog
from ij.measure import Measurements
from ij.measure import ResultsTable
from ij.io import OpenDialog
import math
import os
import csv

# === All functions used in the script are defined here ===

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
        IJ.error("Fail to open the image.")
        return None
    imp.show()
    return imp

# === Function to close the W&L window if open ===
def close_result():
    """Closes the 'Results' window if it is open."""
    # Try if exists
    if WindowManager.getWindow("Results") is not None:
        IJ.selectWindow("Results")
        IJ.run("Close")

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
    tol = 1
    if value is None:
        return "NaN"
    try:
        return "PASS" if abs(value - expected) <= tol else "FAIL"
    except Exception:
        return "Error"

# --- Main Script Execution ---

IJ.log("========================================")
IJ.log("TEST: Slice Thickness Accuracy ")
IJ.log("========================================")
IJ.log("")
IJ.log("[SETUP]")

# Step 1: Open the T1-weighted image
WaitForUserDialog("Open the T1 or T2 image and perform the slice thickness accuracy test.").show()
imp = open_dicom_file("Select T1-weighted or T2-weighted DICOM image")

if imp is None:
    IJ.error("No image open.")
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

# Print image type for confirmation
printImageType(imp)

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

# Prepare the environment and image display
IJ.run("Clear Results")
IJ.run(imp, "Original Scale", "")
IJ.run("In [+]", "")
IJ.run("In [+]", "")
IJ.run("In [+]", "")

# Step 2: Initial Window/Level Adjustment for plane visibility
# The initial window/level settings (window=300, level=200) are set to highlight the inclined planes.
window = 300
level = 200
min_display = level - window / 2  # 50
max_display = level + window / 2  # 350
imp.setDisplayRange(min_display, max_display)
imp.updateAndDraw()

# Step 3: Measure mean signal from two background ROIs
# This signal is used to automatically adjust the display for better contrast later.
IJ.setTool("rectangle")

# Set log measurements
IJ.log("")
IJ.log("[MEASUREMENTS]")
IJ.log("")

# ROI 1 Selection (Background)
while True:
    WaitForUserDialog("Place the rectangular ROI in the middle of the top ramp.\n"
                      "Click OK to perform the measurement.").show()
    roi1 = imp.getRoi()
    if roi1 is None or roi1.getType() != Roi.RECTANGLE:
        IJ.showMessage("Invalid ROI", "ROI 1 must be a rectangular selection. Please try again.")
        continue
    imp.setRoi(roi1)
    IJ.run("Measure")
    stats1 = imp.getStatistics(Measurements.MEAN)
    mean1 = stats1.mean
    break

IJ.log("   {}:  {:.3f}".format("Rectangular ROI 1 (top)", mean1))

# ROI 2 Selection (Background)
while True:
    WaitForUserDialog("Place the rectangular ROI in the middle of the bottom ramp.\n"
                      "Click OK to perform the measurement.").show()
    roi2 = imp.getRoi()
    if roi2 is None or roi2.getType() != Roi.RECTANGLE:
        IJ.showMessage("Invalid ROI", "ROI 2 must be a rectangular selection. Please try again.")
        continue
    imp.setRoi(roi2)
    IJ.run("Measure")
    stats2 = imp.getStatistics(Measurements.MEAN)
    mean2 = stats2.mean
    break

IJ.log("   {}:  {:.3f}".format("Rectangular ROI 2 (bottom)", mean2))

# Step 4: Refine Window/Level based on measured signal
# The display is re-adjusted to enhance the visibility of the inclined planes,
# using the average background signal as the new level.
level = (mean1 + mean2) / 2
window = 10
min_display = (level - window) / 2
max_display = (level + window) / 2
imp.setDisplayRange(min_display, max_display)
imp.updateAndDraw()

# Step 5: Measure the inclined planes with line ROIs
# The user draws lines along the visible planes to measure their lengths.
IJ.setTool("line")

# ROI 3 Selection (Inclined Plane 1)
while True:
    WaitForUserDialog("Draw a straight line to record the length of the top ramp.\n"
                      "Click OK to perform the measurement.").show()
    roi3 = imp.getRoi()
    if roi3 is None or roi3.getType() != Roi.LINE:
        IJ.showMessage("Invalid ROI", "ROI 3 must be a straight line. Please try again.")
        continue
    imp.setRoi(roi3)
    IJ.run("Measure")
    length3 = roi3.getLength()
    break

IJ.log("   {}:  {:.3f}".format("Length top ramp", length3))

# ROI 4 Selection (Inclined Plane 2)
while True:
    WaitForUserDialog("Draw a straight line to record the length of the bottom ramp.\n"
                      "Click OK to perform the measurement.").show()
    roi4 = imp.getRoi()
    if roi4 is None or roi4.getType() != Roi.LINE:
        IJ.showMessage("Invalid ROI", "ROI 4 must be a straight line. Please try again.")
        continue
    imp.setRoi(roi4)
    IJ.run("Measure")
    length4 = roi4.getLength()
    break

IJ.log("   {}:  {:.3f}".format("Length bottom ramp", length4))

# Step 6: Calculate the final slice thickness
# The formula combines the measured lengths to determine the true slice thickness.
# The factor 0.2 is based on the ACR phantom design (20-degree incline, tan(20) ~ 0.364, simplified).
results = 0.2 * (length3 * length4) / (length3 + length4)

# Step 7: Display and save results
# Add the result to the results table
rt = ResultsTable.getResultsTable()
rt.incrementCounter()
rt.addValue("Final result", results)
rt.show("Results")
    
WaitForUserDialog("Slice Thickness Accuracy Test completed, collect the results.").show()

# Clean up and finalize
# Close the image and results table, clear results for next test, and log the final result with PASS/FAIL status.
# PASS +/- 1 mm from the expected 5 mm slice thickness.

try:
    fi = imp.getOriginalFileInfo()
    image_dir = os.path.dirname(fi.directory)
except:
    image_dir = os.getcwd()
    
imp.close()
close_result()
IJ.run("Clear Results")
IJ.log("")
IJ.log("[RESULTS]")
IJ.log("")
IJ.log("Slice Thickness:")
IJ.log("   Measured:  {:.3f} mm".format(results))
IJ.log("   Expected:  5.0 +/- 1.0 mm")
IJ.log("   Result:    [{}]".format(check_limits(results, 5)))
IJ.log("")
IJ.log("[OUTPUT]")

# Save in CSV
if 'results' in locals():
    
    csv_filename = os.path.join(image_dir, "QA_Results_{0}.csv".format(exam_date))
    
    try:
        file_exists = os.path.isfile(csv_filename)
        
        with open(csv_filename, 'a') as f:
            writer = csv.writer(f)
            
            results_str = "{:.3f}".format(results) if 'results' in locals() else "NaN"
            writer.writerow(['Slice_Thickness_Accuracy_mm', results_str])
        
        IJ.log("Results saved to: {}".format(csv_filename))
    except Exception as e:
        IJ.log("Error saving CSV: {}".format(str(e)))
else:
    IJ.log("Warning: Could not save CSV (thickness value not found)")
IJ.log("")
