# --- MacroQA File Header ---
# Project: MacroQA - An ImageJ Macro for ACR MRI Quality Assurance
# File: Geometric_accuracy.py
# Version 1.0.0
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
from ij import ImagePlus
import sys

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
    # Wait for the user to draw the ROI
    wait = WaitForUserDialog("Draw a straight line", instruction)
    wait.show()

    roi = imp.getRoi()
    if roi is None or roi.getType() != Roi.LINE:
        IJ.error("Invalid ROI", "Please redraw a valid straight-line ROI.")
        return None

    IJ.run("Set Measurements...", "length")
    IJ.run(imp, "Measure", "")

    rt = ResultsTable.getResultsTable()
    length = rt.getValue("Length", rt.size() - 1)
    IJ.log("Length: {:.3f}".format(length))
    return length
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
        
# === MAIN SCRIPT ===
IJ.log("---- Geometric Accuracy Test ----")

# === LOCALIZER measurements ===
IJ.log("=== LOCALIZER measurements ===")
WaitForUserDialog("Click OK to select the Localizer image.").show()
localizer = open_dicom_file("Select LOCALIZER image (single slice)")
if localizer is None:
    sys.exit()

# Print image type
printImageType(localizer)

# Zoom in a couple of times for better precision
IJ.setTool("line")
IJ.run("In [+]", "")
IJ.run("In [+]", "")
localizer_measurement = get_measurement(localizer, "LOCALIZER: Draw a vertical straight line.")
localizer.close()

# === T1w measurements ===
IJ.log("=== ACR T1w measurements ===")
WaitForUserDialog("Click OK to select the ACR T1w image.").show()
t1w = open_dicom_file("Select ACR T1-weighted DICOM image (multi-slice)")
if t1w is None:
    sys.exit()

# Print image type
printImageType(t1w)

# Zoom in a couple of times for better precision
IJ.run("In [+]", "")
IJ.run("In [+]", "")

# --- Slice 1 ---
t1w.setSlice(1)
IJ.log("ACR T1w - Slice 1")

t1_vert = get_measurement(t1w, "Slice 1: Draw a VERTICAL straight line")
t1_horz = get_measurement(t1w, "Slice 1: Draw a HORIZONTAL straight line")

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
    IJ.log("ACR T1w - Slice 5")

t1_diag1 = get_measurement(t1w, "Slice 5: Draw a DIAGONAL straight line (Diagonal 1)")
t1_diag2 = get_measurement(t1w, "Slice 5: Draw a DIAGONAL straight line (Diagonal 2)")
t1_vert_5 = get_measurement(t1w, "Slice 5: Draw a VERTICAL straight line")
t1_horz_5 = get_measurement(t1w, "Slice 5: Draw a HORIZONTAL straight line")

t1w.close()

# === LOG FINAL ===
IJ.log("=== SUMMARY ===")
IJ.log("LOCALIZER: {:.3f}".format(localizer_measurement))
IJ.log("T1 Slice 1 - Vertical: {:.3f}, Horizontal: {:.3f}".format(t1_vert, t1_horz))
IJ.log("T1 Slice 5 - Diagonal 1: {:.3f}, Diagonal 2: {:.3f}".format(t1_diag1, t1_diag2))
IJ.log("T1 Slice 5 - Vertical: {:.3f}, Horizontal: {:.3f}".format(t1_vert_5, t1_horz_5))

IJ.log("{:.3f}".format(localizer_measurement))
IJ.log("{:.3f}".format(t1_vert))
IJ.log("{:.3f}".format(t1_horz))
IJ.log("{:.3f}".format(t1_diag1))
IJ.log("{:.3f}".format(t1_diag2))
IJ.log("{:.3f}".format(t1_vert_5))
IJ.log("{:.3f}".format(t1_horz_5))


WaitForUserDialog("Geometric accuracy test finished. Please collect the results.").show()
close_result()

IJ.run("Clear Results")
IJ.log("---- End of the Geometric Accuracy test ----")
IJ.log("")
