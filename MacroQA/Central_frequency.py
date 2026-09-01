# --- MacroQA File Header ---
# Project: MacroQA - An ImageJ Macro for ACR MRI Quality Assurance
# File: Central_frequency.py
# Version 1.0.4
# Source: https://github.com/icaroafoliveira/Macros_MRI_QA_phantom_ACR
# ---------------------------

# Macro to extract the central frequency from the DICOM header of an ACR phantom MRI scan.
# The script assumes that the user will select the ACR T1-weighted image.
# The Imaging Frequency tag (0018, 0084) is extracted and printed in the log.

from ij import IJ
from ij.io import OpenDialog
from ij.gui import WaitForUserDialog
import csv
import os
from datetime import datetime


# === All functions used in the script are defined here ===
# === Function to print the image type based on TR value ===
def printImageType(imp):
    """
    Print the type of DICOM image based on the TR value.

    Determines image type based on TR (Repetition Time)
    T1w: TR ~ 500 ms
    T2w: TR ~ 2000 ms
    Localizer: TR ~ 200 ms
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

# === Start of the main script ===

WaitForUserDialog("Select T1w image for Central Frequency test.").show()

# call open dialog to get the DICOM path
open_dia_file = OpenDialog("Open T1w image", None)

# Get the path
path = open_dia_file.getPath()

# Check if path is None (user cancelled dialog)
if path is None:
	IJ.log("No file selected. Exiting.")
	exit()

# Open DICOM
imp = IJ.openImage(path)

# Check if image failed to open
if imp is None:
	IJ.log("Failed to open image. Exiting.")
	exit()

# Check header info
info = imp.getInfoProperty()

# Initiate the log 
IJ.log("========================================")
IJ.log("TEST: Central Frequency")
IJ.log("========================================")
IJ.log("")
IJ.log("[SETUP]")

# Make sure that the image is the expected one
printImageType(imp)

# Extract exam date from DICOM header (tag 0008,0020 - Study Date)
exam_date = "N/A"
try:
	date_start = info.find("0008,0020")
	if date_start != -1:
		date_value_start = info.find(":", date_start) + 1
		date_end = info.find("\n", date_value_start)
		exam_date = info[date_value_start:date_end].strip()
except:
	pass

IJ.log("Exam Date: " + exam_date)
IJ.log("")

# Additional information == Magnetic Field Strength (0018,0087) and Manufacturer (0008,0070)
magnetic_field_strength = "N/A"
manufacturer = "N/A"
try:
	magnetic_field_start = info.find("0018,0087")
	if magnetic_field_start != -1:
		magnetic_field_value_start = info.find(":", magnetic_field_start) + 1
		magnetic_field_end = info.find("\n", magnetic_field_value_start)
		magnetic_field_strength = info[magnetic_field_value_start:magnetic_field_end].strip()
	IJ.log("Magnetic Field Strength: " + magnetic_field_strength + " T")
except:
	pass

try:
	manufacturer_start = info.find("0008,0070")
	if manufacturer_start != -1:
		manufacturer_value_start = info.find(":", manufacturer_start) + 1
		manufacturer_end = info.find("\n", manufacturer_value_start)
		manufacturer = info[manufacturer_value_start:manufacturer_end].strip()
	IJ.log("Manufacturer: " + manufacturer)
except:
	pass

# Imaging Frequency tag is (0018, 0084)
# We need to parse the header string to find this value
# The header is often a Large string with all the tags and values.

imaging_freq_key = "0018,0084"
transmitter_freq_key = "0018,9098"

# A simple way to find the value is to search for the tag in the string.
# The format is typically "Tag_ID: Value"
central_frequency_mhz = None
transmitter_frequency_mhz = None

if info is not None:
    for line in info.split("\n"):
        if line.startswith(imaging_freq_key):
            try:
                central_frequency_mhz = float(line.split(":")[1].strip())
            except ValueError:
                IJ.log("Could not convert the Imaging Frequency value to a number.")
        
        if line.startswith(transmitter_freq_key):
            try:
                transmitter_frequency_mhz = float(line.split(":")[1].strip())
            except ValueError:
                IJ.log("Could not convert the Transmitter Frequency value to a number.")
    
    # Check if tags were found after loop completes
    if central_frequency_mhz is None:
        IJ.log("Imaging Frequency (0018, 0084) tag not found in the DICOM header.")
        # Use transmitter frequency as fallback
        if transmitter_frequency_mhz is not None:
            central_frequency_mhz = transmitter_frequency_mhz
            IJ.log("Using Transmitter Frequency as central frequency.")
    
    if transmitter_frequency_mhz is None:
        IJ.log("Transmitter Frequency (0018, 9098) tag not found in the DICOM header.")
else:
    IJ.log("Could not retrieve DICOM header information.")


dlg=WaitForUserDialog("Central Frequency test finished, collect the results.")
dlg.show()
		
IJ.log("")
IJ.log("[RESULTS]")
IJ.log("Central frequency: " + str(central_frequency_mhz) + " MHz")
IJ.log("Transmitter frequency: " + str(transmitter_frequency_mhz) + " MHz")
 
IJ.log("")
IJ.log("[OUTPUT]")

# Save in CSV
if central_frequency_mhz is not None:
	try:
		image_dir = os.path.dirname(path)
	except NameError:
		image_dir = os.getcwd()
	
	csv_filename = os.path.join(image_dir, "QA_Results_{0}.csv".format(exam_date))
	
	try:
		# Check if file exists to determine if we need to write headers
		file_exists = os.path.isfile(csv_filename)
		
		with open(csv_filename, 'a') as f:
			writer = csv.writer(f)
			
			# Write header and data on same row
			writer.writerow(['Central_Frequency_MHz', str(central_frequency_mhz)])
		
		IJ.log("Results saved to: {}".format(csv_filename))
	except Exception as e:
		IJ.log("Error saving CSV: {}".format(str(e)))
else:
	IJ.log("Warning: Could not save CSV (central frequency not found)")

IJ.log("")




# Close the image without saving changes
if 'imp' in locals():
	imp.close()
