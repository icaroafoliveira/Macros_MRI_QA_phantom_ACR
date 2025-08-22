# @String path
# @File(label="Choose a DICOM file", style="open") input_file

import os
from ij import IJ
from ij.io import FileOpener
from ij.io import Opener


# Check if a file was selected
if input_file is None:
    IJ.log("No file selected. Please choose a DICOM file.")
else:
    # Open the DICOM file
    imp = Opener().openImage(input_file.getPath())

    if imp is None:
        IJ.log("Failed to open the image. Please ensure it's a valid DICOM file.")
    else:
        # Get the DICOM header information
        info = imp.getInfoProperty()

        # The Imaging Frequency tag is (0018, 0084).
        # We need to parse the header string to find this value.
        # The header is often a large string with all the tags and values.
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
              
            except ValueError:
                IJ.log("Could not convert the value to a number.")
        else:
            IJ.log("Imaging Frequency (0018, 0084) tag not found in the DICOM header.")

# Close the image without saving changes
if 'imp' in locals():
    imp.close()
