from ij import IJ, WindowManager
from ij.gui import Roi, WaitForUserDialog
from ij.measure import Measurements
from ij.plugin.frame import RoiManager
from ij.process import ImageStatistics
from ij.measure import ResultsTable
from ij.io import OpenDialog

# === Function to open DICOM files ===
def open_dicom_file(prompt):
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
    # Try if exists
    if WindowManager.getWindow("Results") is not None:
        IJ.selectWindow("Results")
        IJ.run("Close")

# === Function to print image type based on number of slices ===
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

IJ.log("---- Slice Thickness Accuracy Test ----")

WaitForUserDialog("Open the T1 image and perform the slice thickness accuracy test.").show()
imp = open_dicom_file("Select T1-weighted DICOM image (multi-slice)")

if imp is None:
    IJ.error("No image open.")
    raise SystemExit

# Print image type
printImageType(imp)

IJ.run("Clear Results")
IJ.run(imp, "Original Scale", "")
IJ.run("In [+]", "")
IJ.run("In [+]", "")

# Ajustment of Window/Level (window=300, level=200)
window = 300
level = 200
min_display = level - window / 2  # 50
max_display = level + window / 2  # 350
imp.setDisplayRange(min_display, max_display)
imp.updateAndDraw()

# Selects rectangle tool
IJ.setTool("rectangle")

# ROI 1 Selection
WaitForUserDialog("Select ROI 1 (Rectangle)").show()
roi1 = imp.getRoi()
if roi1 is None or roi1.getType() != Roi.RECTANGLE:
    IJ.error("ROI 1 has an invalid shape or was not selected.")
    raise SystemExit
imp.setRoi(roi1)
IJ.run("Measure")
stats1 = imp.getStatistics(Measurements.MEAN)
mean1 = stats1.mean

# ROI 2 Selection
WaitForUserDialog("Select ROI 2 (Rectangle)").show()
roi2 = imp.getRoi()
if roi2 is None or roi2.getType() != Roi.RECTANGLE:
    IJ.error("ROI 2 has an invalid shape or was not selected.")
    raise SystemExit
imp.setRoi(roi2)
IJ.run("Measure")
stats2 = imp.getStatistics(Measurements.MEAN)
mean2 = stats2.mean

# Ajust Window/Level based on medium ROIs pixels
level = (mean1 + mean2) / 2
window = 10
min_display = (level - window) / 2
max_display = (level + window) / 2
imp.setDisplayRange(min_display, max_display)
imp.updateAndDraw()

# Selects line tool
IJ.setTool("line")

# ROI 3 Selection
WaitForUserDialog("Select ROI 3 (Straight Line)").show()
roi3 = imp.getRoi()
if roi3 is None or roi3.getType() != Roi.LINE:
    IJ.error("ROI 3 has an invalid shape or was not selected.")
    raise SystemExit
imp.setRoi(roi3)
IJ.run("Measure")
length3 = roi3.getLength()

# ROI 4 Selection
WaitForUserDialog("Select ROI 4 (Straight Line)").show()
roi4 = imp.getRoi()
if roi4 is None or roi4.getType() != Roi.LINE:
    IJ.error("ROI 4 has an invalid shape or was not selected.")
    raise SystemExit
imp.setRoi(roi4)
IJ.run("Measure")
length4 = roi4.getLength()

# Calculate the result expected
resultado = 0.2 * (length3 * length4) / (length3 + length4)

# shows log
IJ.log("{:.3f}".format(resultado))

# Add the result on the result table
rt = ResultsTable.getResultsTable()
rt.incrementCounter()
rt.addValue("Final result", resultado)
rt.show("Results")
    
WaitForUserDialog("Slice Thickness Accuracy Test completed, collect the results.").show()
imp.close()
fechar_result()

#End of the program
IJ.run("Clear Results")
IJ.log("---- End of the Slice Thickness Accuracy Test ----")
IJ.log("")
