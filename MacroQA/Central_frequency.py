# --- MacroQA File Header ---
# Project: MacroQA - An ImageJ Macro for ACR MRI Quality Assurance
# File: Central_frequency.py
# Version 1.0.1
# Source: https://github.com/icaroafoliveira/Macros_MRI_QA_phantom_ACR
# ---------------------------

# Macro to extract the central frequency from the DICOM header of an ACR phantom MRI scan.
# The script assumes that the user will select the ACR T1-weighted image.
# The Imaging Frequency tag (0018, 0084) is extracted and printed in the log.

from ij import IJ
from ij.io import OpenDialog
from ij.gui import WaitForUserDialog

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

# call open dialog to get the DICOM path
open_dia_file = OpenDialog("Open T1w image", None)

# Get the path
path = open_dia_file.getPath()

# if path is None 

# Open DICOM
imp = IJ.openImage(path)

# If imp is None

# Check header info
info = imp.getInfoProperty()

# Initiate the log 
IJ.log("---- Central Frequency Test ----")

# Make sure that the image is the expected one
printImageType(imp)
	
# Imaging Frequency tag is (0018, 0084)
# We need to parse the header string to find this value
# The header is often a Large string with all the tags and values.
tag_key = "0018,0084"

# A simple way to find the value is to search for the tag in the string.
# The format is typically "Tag_ID: Value"
start_index = info.find(tag_key)

if start_index != -1:
	# Find the start of the value part
	value_start = info.find(":", start_index) + 1
	# Find the end of the line
	end_index = info.find("\n", value_start)        
	
	# Extract and clean up the value
	central_freq_str = info[value_start:end_index].strip()
	try:
		# Convert the string to a floating-point number
		central_frequency_mhz = float(central_freq_str)
		IJ.log("The central frequency (Imaging Frequency) is: " + str(central_frequency_mhz) + " MHz")
		IJ.log(str(central_frequency_mhz))
		dlg=WaitForUserDialog("Central Frequency test finished, collect the results.")
		dlg.show()
		IJ.log("---- End of the Central Frequency test ----")
		IJ.log("")
		
	except ValueError:
		IJ.log("Could not convert the value to a number.")
else:
	IJ.log("Imaging Frequency (0018, 0084) tag not found in the DICOM header.")
		
# Close the image without saving changes
if 'imp' in locals():
	imp.close()
