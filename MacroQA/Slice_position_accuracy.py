# Macro to perform the Slice Position Accuracy Test on an ACR phantom MRI scan.
# This test checks for discrepancies between the prescribed and actual slice locations.
# The user is guided to measure the height difference between two vertical bars on slices 1 and 11
# of a T1-weighted image, which corresponds to the slice mis-positioning.

# Required libraries
from ij import IJ, WindowManager
from ij.gui import WaitForUserDialog, Roi, Line
from ij.io import OpenDialog
from java.lang import Math
from ij.measure import ResultsTable
import math

IJ.log("---- Slice Position Accuracy Test ----")

# --- Helper Functions ---

def fechar_wl():
    """Closes any open 'Brightness/Contrast' or 'Window/Level' dialogs."""
    # brightness/contrast window management
    candidatos = ["Brightness/Contrast", "W&L", "Window/Level", "B&C"]
    for t in candidatos:
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

def fechar_result():
    """Closes the 'Results' window if it is open."""
    # Get Window only if it exists
    if WindowManager.getWindow("Results") is not None:
        IJ.selectWindow("Results")
        IJ.run("Close")

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

def get_measurement(imp, instruction, cutoff_px=127):
    """
    Prompts the user to draw a line and measures its length.
    The length is then signed based on its position relative to a central cutoff point.
    """
    # set tool line and waits the user
    IJ.setTool("line")
    WaitForUserDialog("Draw the straight line.", instruction).show()

    roi = imp.getRoi()
    if roi is None or roi.getType() != Roi.LINE:
        IJ.error("Invalid ROI", "If the difference is zero in fact, press 'OK' to continue.")
        return int(0)

    # measure: length + centroid (to get 'X' on the table)
    IJ.run("Set Measurements...", "length centroid")
    IJ.run(imp, "Measure", "")

    rt = ResultsTable.getResultsTable()
    row = rt.size() - 1

    length = rt.getValue("Length", row)

    # get X at the centroid coming from own measure
    x_val = rt.getValue("X", row)  # return NaN if column doesn't exist
    if math.isnan(x_val):
        # rare fallback: if for any reason the program doesn't get 'X', use the geometric medium point
        x_val = (roi.getX1() + roi.getX2()) / 2.0
        # OBS: already in pixels

    # converts X measured as pixels if the image is calibrated (DICOM etc.)
    cal = imp.getCalibration()
    pw = cal.pixelWidth if (cal and cal.pixelWidth) else 1.0
    # if 'X' came in physical units, dividing by pixelWidth brings it to pixels;
    # if it was already in pixels, pw=1.0 and nothing changes.
    x_px = x_val / pw

    # Apply signal rule as half left (x > 127)
    # The length is positive if the measurement is on the left side of the image and negative on the right
    # (or vice-versa, depending on the image convention), indicating mis-positioning direction.
    signed_length = -length if (x_px > float(cutoff_px)) else length

    # optional: refresh table to reflect the signal value
    try:
        rt.setValue("Length", row, signed_length)
        rt.show("Results")
    except:
        pass

    #IJ.log("X_centroide(px)=%.3f  cutoff=%d  comprimento=%.3f" % (x_px, cutoff_px, signed_length))
    return signed_length

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
    
def ajustar_window_level(imp, level, window):
    """Sets the display range (window/level) for the image."""
    min_display = level - window / 2
    max_display = level + window / 2
    imp.setDisplayRange(min_display, max_display)
    imp.updateAndDraw()

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

WaitForUserDialog("Open the T1 image to proceed with the test.").show()
imp = open_dicom_file("Select T1-weighted DICOM image (multi-slice)")

# Verify if image is opened
if imp is None:
    IJ.error("No image opened.")
    raise SystemExit

printImageType(imp)

# --- Process First Slice (Slice 1) ---
# Go to first slice
imp.setSlice(1)

IJ.run(imp, "Original Scale", "")
# Adjust window/level to central values
IJ.resetMinAndMax(imp)

# 2x Zoom "+" for better visibility
IJ.run("In [+]", "")
IJ.run("In [+]", "")

# Adjust Window/Level: window = 10, level = 1000
ajustar_window_level(imp, level=1000, window=10)
IJ.run("Brightness/Contrast...")
IJ.run("Window/Level...")

# Zoom to a specific region of interest to guide the user to the bars
zoom_to_rect_pixels(x = 119, y = 53, w = 18, h = 12)

# Provide instructions and wait for user action
WaitForUserDialog("Slice Position Accuracy Test.\n"
"If the bar on the right is longer, the slice is mis-positioned superiorly; this bar length difference is assigned a positive value.\n"  
"If the bar on the left is longer, meaning the slice is mis-positioned inferiorly; this bar length difference is assigned a negative value.").show()
medida1 = get_measurement(imp, "Slice 1 - Draw the vertical straight line to get the height difference between the bars.\n"
"Press 'OK' only after drawing the straight line.")

# --- Process Eleventh Slice (Slice 11) ---
# Go to 11th slice
imp.setSlice(11)
medida2 = get_measurement(imp, "Slice 11 - Draw the vertical straight line to get the height difference between the bars.\n"
"Press 'OK' only after drawing the straight line.")

# --- Finalization and Results ---
imp.close()
fechar_wl()
fechar_result()

WaitForUserDialog("Slice Position Accuracy Test finished. Collect the results.\n").show()

IJ.run("Clear Results")
IJ.log("Slice 1: {:.3f}".format(medida1))
IJ.log("Slice 11: {:.3f}".format(medida2))
IJ.log("---- End of the Slice Position Accuracy Test ----")
IJ.log("")
