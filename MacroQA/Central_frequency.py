# Macro to extract the central frequency from the DICOM header of an ACR phantom MRI scan.
# The script assumes that the user will select the ACR T1-weighted image.
# The Imaging Frequency tag (0018, 0084) is extracted and printed in the log.


from ij import IJ
from ij.io import OpenDialog
from ij.gui import WaitForUserDialog

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
# Localizer is a single-slice image
# T1w has 11 slices
# T2w has 22 slices (2 echo times)
slices = imp.getNSlices()     # z dimension

if slices < 11:
	IJ.log("Image Type: Localizer.")
	IJ.log("You should repeat the measurement with ACR T1w image.")
elif slices > 11:
	IJ.log("Image Type: ACR T2w image.")
	IJ.log("You should repeat the measurement with ACR T1w image.")
else:
	IJ.log("Image Type: ACR T1w image.")
			
	
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
