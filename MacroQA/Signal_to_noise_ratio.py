# --- MacroQA File Header ---
# Project: MacroQA - An ImageJ Macro for ACR MRI Quality Assurance
# File: Signal_to_noise_ratio.py
# Version 1.0.3
# Source: https://github.com/icaroafoliveira/Macros_MRI_QA_phantom_ACR
# ---------------------------

# Macro to calculate the Signal to Noise Ratio (SNR) from an ACR phantom MRI scan.
# The macro uses a subtraction method, requiring two identical scans (T1-weighted) of the same phantom.
# The SNR is calculated by measuring the mean signal from a central ROI on one image
# and the standard deviation of the noise from a subtracted image (A - B), as described in the ACR phantom test guidelines.

# Required libraries
from ij import IJ, WindowManager
from ij.gui import WaitForUserDialog, Roi, Line, OvalRoi, GenericDialog
from ij.io import OpenDialog
from java.lang import Math
from ij.measure import ResultsTable
import math
from ij.plugin import ImageCalculator
import os
import csv
from ij.measure import Measurements
from ij.plugin.frame import RoiManager
from java.awt import Window, Font

# === All functions used in the script are defined here ===

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
        IJ.error("Fail to open image.")
        return None
    imp.show()
    return imp

# === Function to convert area in cm² to radius in pixels ===
def area_to_radius_pixels(area_cm2, px_w_cm, px_h_cm):
    """Converts a given area in cm^2 to a circle's radius in pixels."""
    pixel_area_cm2 = px_w_cm * px_h_cm
    return math.sqrt(area_cm2 / (math.pi * pixel_area_cm2))

def measure_roi_mean(imp, roi=None):
    """Measures the mean pixel value within a given ROI."""
    if roi is not None:
        imp.setRoi(roi)
    stats = imp.getStatistics(Measurements.MEAN)
    return stats.mean

def measure_roi_std(imp, roi=None):
    """Measures the standard deviation of pixel values within a given ROI."""
    if roi is not None:
        imp.setRoi(roi)
    stats = imp.getStatistics(Measurements.STD_DEV)
    return stats.stdDev

# --- Step 1: Subtract two images to isolate noise ---
def subtract_two_images_via_calculator():
    """
    Guides the user to open two identical T1-weighted images and subtracts them.
    This subtraction isolates the noise component for SNR calculation.
    """
    # 1) Open images A and B
    WaitForUserDialog("Open the first T1 image to proceed with the SNR test.").show()
    impA = open_dicom_file("Select the FIRST image (A)")
    
    # Adjust display settings for image A
    IJ.run(impA, "Original Scale", "")
    IJ.resetMinAndMax(impA)
    IJ.run("In [+]", "")
    IJ.run("In [+]", "")
    if impA is None: return
    
    WaitForUserDialog("Open the second T1 image to proceed with the SNR test.").show()
    impB = open_dicom_file("Select the SECOND image (B)")
    if impB is None: return
    
    # Set both images to slice 7 for consistency
    if impA.getNSlices() < 7:
        impA.setSlice(1)
    else:
        impA.setSlice(7)
    
    if impB.getNSlices() < 7:
        impB.setSlice(1)
    else:
        impB.setSlice(7)
        
 
    # 4) Image Calculator: A - B (creates a new window)
    ic = ImageCalculator()
    result = ic.run("subtract create", impA, impB)  # 'create' => new image
    if result is not None:
        result.setTitle("Subtraction (A - B)")
        result.show()
        IJ.log("Subtraction finished: A - B")
    else:
        IJ.error("Fail to subtract (Image Calculator).")
    
    impB.close()
    
    return result, impA

# --- Main Script Execution ---

IJ.log("========================================")
IJ.log("TEST: Signal to Noise Ratio (SNR)")
IJ.log("========================================")
IJ.log("")
IJ.log("[SETUP]")
# Perform image subtraction
result, impA = subtract_two_images_via_calculator()

# Check if the images were successfully processed and print image type
if impA is None or result is None:
    IJ.error("Image processing failed.")
    raise SystemExit

# Extract DICOM metadata (exam date and station name)
exam_date = "N/A"
info = impA.getInfoProperty()

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

printImageType(impA)


# --- Step 2: Image Calibration ---
# This block handles the conversion from real-world units (cm) to pixels.
cal = impA.getCalibration()
unit = (cal.getUnit() or "").lower()
pw = cal.pixelWidth
ph = cal.pixelHeight

if unit == "mm":
    pixel_width_cm = pw / 10.0
    pixel_height_cm = ph / 10.0
elif unit == "cm":
    pixel_width_cm = pw
    pixel_height_cm = ph
else:
    # If calibration is missing or unrecognized, prompt the user for pixel dimensions in mm
    gd = GenericDialog("Fail to calibrate")
    gd.addMessage("Inform the pixel size (in mm).")
    gd.addNumericField("Pixel width (mm):", 0.0, 6)
    gd.addNumericField("Pixel height (mm):", 0.0, 6)
    gd.showDialog()
    if gd.wasCanceled():
        IJ.log("Cancelled by the user.")
        raise SystemExit
    pw_mm = gd.getNextNumber()
    ph_mm = gd.getNextNumber()
    if pw_mm <= 0 or ph_mm <= 0:
        IJ.error("Invalid pixel value.")
        raise SystemExit
    pixel_width_cm = pw_mm / 10.0
    pixel_height_cm = ph_mm / 10.0

IJ.log("Calibration used (cm/pixel): {:.6g} x {:.6g}  (unit='{}')".format(pixel_width_cm, pixel_height_cm, cal.getUnit()))

# --- Step 2b: Create 200 cm² ROI for manual positioning ---
# This ROI is used to measure the mean signal from the phantom and the standard deviation from the noise image.
radius_large = area_to_radius_pixels(200.0, pixel_width_cm, pixel_height_cm)
center_x = impA.getWidth() / 2.0
center_y = impA.getHeight() / 2.0
roi_large = OvalRoi(center_x - radius_large, center_y - radius_large, radius_large*2, radius_large*2)
impA.setRoi(roi_large)

# Prompt the user to position the ROI
dlg = WaitForUserDialog("Set ROI (200 cm^2)",
    "Move the ROI to the place that you wish.\nPress OK to continue.")
dlg.show()

# Add the ROI to the ROI Manager
rm = RoiManager.getInstance()
if rm is None:
    rm = RoiManager()
rm.reset()  # Clean previous ROIs
rm.addRoi(roi_large)

# Select the ROI on the subtraction image (result) to measure the noise
result.setRoi(roi_large)

# Final instructions and warning dialog
gd = GenericDialog("Instructions")
gd.addMessage("WARNING!", Font("SansSerif", Font.BOLD, 20))
gd.addMessage("Close the ROI Manager window right after finishing the test.", Font("SansSerif", Font.ITALIC, 12))
gd.addMessage("Press 'OK' to continue.", Font("SansSerif", Font.ITALIC, 12))
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


# --- Calculation of SNR ---
# The signal (mean) is measured from the original image (impA)
mean_ref = measure_roi_mean(impA)
# The noise (standard deviation) is measured from the subtracted image (result)
std_ref = measure_roi_std(result)
# SNR formula based on ACR guidelines
SNR = mean_ref / std_ref
# Note: The ACR method often includes a scaling factor (e.g., * sqrt(2)) depending on the specific protocol.
# This script uses the basic formula.

# --- Display Final Results ---
dlg=WaitForUserDialog("SNR test finished, collect the results.")
dlg.show()

# Capture image directory before closing
try:
    fi = impA.getOriginalFileInfo()
    image_dir = os.path.dirname(fi.directory)
except:
    image_dir = os.getcwd()

impA.close()
result.close()

IJ.log("")
IJ.log("[PROCESS]")
IJ.log("Mean Signal (200 cm^2 ROI):  {:.3f}".format(mean_ref))
IJ.log("Noise Std Dev (Difference): {:.3f}".format(std_ref))
IJ.log("")
IJ.log("[RESULTS]")
IJ.log("SNR:                        {:.3f}".format(SNR))
IJ.log("")
IJ.log("[OUTPUT]")

# Save in CSV
if 'SNR' in locals():
	
	csv_filename = os.path.join(image_dir, "QA_Results_{0}.csv".format(exam_date))
	
	try:
		file_exists = os.path.isfile(csv_filename)
		
		with open(csv_filename, 'a') as f:
			writer = csv.writer(f)
			
			snr_str = "{:.3f}".format(SNR) if 'SNR' in locals() else "NaN"
			writer.writerow(['Signal_to_Noise_Ratio', snr_str])
		
		IJ.log("Results saved to: {}".format(csv_filename))
	except Exception as e:
		IJ.log("Error saving CSV: {}".format(str(e)))
else:
	IJ.log("Warning: Could not save CSV (SNR value not found)")
IJ.log("")
