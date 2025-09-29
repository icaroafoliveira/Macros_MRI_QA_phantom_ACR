# --- MacroQA File Header ---
# Project: MacroQA - An ImageJ Macro for ACR MRI Quality Assurance
# File: Slice_thickness_accuracy.py
# Version 1.0.1
# Source: https://github.com/icaroafoliveira/Macros_MRI_QA_phantom_ACR
# ---------------------------

# Macro to perform the Slice Thickness Accuracy Test on an ACR phantom MRI scan.
# The user is guided to measure two inclined planes in a T1-weighted image
# to verify if the slice thickness is within the acceptable range.

# Required libraries
from ij import IJ, WindowManager
from ij.gui import Roi, WaitForUserDialog
from ij.measure import Measurements
from ij.plugin.frame import RoiManager
from ij.process import ImageStatistics
from ij.measure import ResultsTable
from ij.io import OpenDialog

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

# --- Main Script Execution ---

IJ.log("---- Slice Thickness Accuracy Test ----")

# Step 1: Open the T1-weighted image
WaitForUserDialog("Open the T1 or T2 image and perform the slice thickness accuracy test.").show()
imp = open_dicom_file("Select T1-weighted or T2-weighted DICOM image")

if imp is None:
    IJ.error("No image open.")
    raise SystemExit

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

# ROI 1 Selection (Background)
WaitForUserDialog("Select ROI 1 (Rectangle)").show()
roi1 = imp.getRoi()
if roi1 is None or roi1.getType() != Roi.RECTANGLE:
    IJ.error("ROI 1 has an invalid shape or was not selected.")
    raise SystemExit
imp.setRoi(roi1)
IJ.run("Measure")
stats1 = imp.getStatistics(Measurements.MEAN)
mean1 = stats1.mean

# ROI 2 Selection (Background)
WaitForUserDialog("Select ROI 2 (Rectangle)").show()
roi2 = imp.getRoi()
if roi2 is None or roi2.getType() != Roi.RECTANGLE:
    IJ.error("ROI 2 has an invalid shape or was not selected.")
    raise SystemExit
imp.setRoi(roi2)
IJ.run("Measure")
stats2 = imp.getStatistics(Measurements.MEAN)
mean2 = stats2.mean

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
WaitForUserDialog("Select ROI 3 (Straight Line)").show()
roi3 = imp.getRoi()
if roi3 is None or roi3.getType() != Roi.LINE:
    IJ.error("ROI 3 has an invalid shape or was not selected.")
    raise SystemExit
imp.setRoi(roi3)
IJ.run("Measure")
length3 = roi3.getLength()

# ROI 4 Selection (Inclined Plane 2)
WaitForUserDialog("Select ROI 4 (Straight Line)").show()
roi4 = imp.getRoi()
if roi4 is None or roi4.getType() != Roi.LINE:
    IJ.error("ROI 4 has an invalid shape or was not selected.")
    raise SystemExit
imp.setRoi(roi4)
IJ.run("Measure")
length4 = roi4.getLength()

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
imp.close()
close_result()
IJ.run("Clear Results")
IJ.log("Slice thickness: {:.3f}".format(results))
IJ.log("{:.3f}".format(results))
IJ.log("---- End of the Slice Thickness Accuracy Test ----")
IJ.log("")
