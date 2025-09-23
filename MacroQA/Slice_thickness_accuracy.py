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

# --- Helper Functions ---

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

def fechar_result():
    """Closes the 'Results' window if it is open."""
    # Try if exists
    if WindowManager.getWindow("Results") is not None:
        IJ.selectWindow("Results")
        IJ.run("Close")

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

IJ.log("---- Slice Thickness Accuracy Test ----")

# Step 1: Open the T1-weighted image
WaitForUserDialog("Open the T1 image and perform the slice thickness accuracy test.").show()
imp = open_dicom_file("Select T1-weighted DICOM image (multi-slice)")

if imp is None:
    IJ.error("No image open.")
    raise SystemExit

# Print image type for confirmation
printImageType(imp)

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
resultado = 0.2 * (length3 * length4) / (length3 + length4)

# Step 7: Display and save results
IJ.log("{:.3f}".format(resultado))

# Add the result to the results table
rt = ResultsTable.getResultsTable()
rt.incrementCounter()
rt.addValue("Final result", resultado)
rt.show("Results")
    
WaitForUserDialog("Slice Thickness Accuracy Test completed, collect the results.").show()

# Clean up and finalize
imp.close()
fechar_result()
IJ.run("Clear Results")
IJ.log("---- End of the Slice Thickness Accuracy Test ----")
IJ.log("")
