# --- MacroQA File Header ---
# Project: MacroQA - An ImageJ Macro for ACR MRI Quality Assurance
# File: Run_QA_Workflow.py
# Version 1.0.3
# Source: https://github.com/icaroafoliveira/Macros_MRI_QA_phantom_ACR
# ---------------------------


# Macro to run the selected QA tests for an ACR phantom MRI scan.
# The user is prompted to select a protocol (Weekly, Annual, or Full QA), and
# the corresponding tests are executed in sequence. Each test is implemented
# in a separate macro file, which is called from this main workflow script.


from ij import IJ
from ij.gui import GenericDialog, WaitForUserDialog
import os


# Get the directory of the current script
script_dir = os.path.dirname(__file__)

gd = GenericDialog("ACR MRI Quality Assurance Tests")
gd.addMessage("Select QA tests to run:")
gd.addChoice("Protocol:", ["Weekly QA", "Annual QA", "Full QA"], "Weekly QA")
gd.showDialog()

if gd.wasCanceled():
    print("User cancelled.")
else:
    protocol_choice = gd.getNextChoice()
    print("User selected: " + protocol_choice)

# select the tests to run based on the protocol choice

if protocol_choice == "Weekly QA":
    msg = ("The following tests will be run:\n" +
            "\n" +
            "1. Central Frequency\n" +
            "\n" +
            "2. Geometric Accuracy\n" +
            "\n" +
            "3. High Contrast Spatial Resolution\n" +
            "\n" +
            "4. Low Contrast Object Detectability\n" +
            "\n" +
            "5. Signal to Noise Ratio\n" +
            "\n" +
            "Click OK to proceed.")
    dlg = WaitForUserDialog(msg)
    dlg.show()
    
    IJ.runMacroFile(os.path.join(script_dir, "Central_frequency.py"))
    IJ.runMacroFile(os.path.join(script_dir, "Geometric_accuracy.py"))
    IJ.runMacroFile(os.path.join(script_dir, "High_contrast_spatial_resolution.py"))
    IJ.runMacroFile(os.path.join(script_dir, "Low_contrast_objective_detectability.py"))
    IJ.runMacroFile(os.path.join(script_dir, "Signal_to_noise_ratio.py"))
if protocol_choice == "Annual QA":
    msg = ("The following tests will be run:\n" +
            "\n" +
            "1. Intensity Uniformity\n" +
            "\n" +
            "2. Percentage Signal Ghosting\n" +
            "\n" +
            "3. Slice Position Accuracy\n" +
            "\n" +
            "4. Slice Thickness Accuracy\n" +
            "\n" +
            "Click OK to proceed.")
    dlg = WaitForUserDialog(msg)
    dlg.show()
    
    IJ.runMacroFile(os.path.join(script_dir, "Image_intensity_uniformity.py"))
    IJ.runMacroFile(os.path.join(script_dir, "Percentage_signal_ghosting.py"))
    IJ.runMacroFile(os.path.join(script_dir, "Slice_position_accuracy.py"))
    IJ.runMacroFile(os.path.join(script_dir, "Slice_thickness_accuracy.py"))
if protocol_choice == "Full QA":
    msg = ("The following tests will be run:\n" +
            "\n" +
            "1. Central Frequency\n" +
            "\n" +
            "2. Geometric Accuracy\n" +
            "\n" +
            "3. High Contrast Spatial Resolution\n" +
            "\n" +
            "4. Low Contrast Object Detectability\n" +
            "\n" +
            "5. Signal to Noise Ratio\n" +
            "\n" +
            "6. Intensity Uniformity\n" +
            "\n" +
            "7. Percentage Signal Ghosting\n" +
            "\n" +
            "8. Slice Position Accuracy\n" +
            "\n" +
            "9. Slice Thickness Accuracy\n" +
            "\n" +
            "Click OK to proceed.")
    dlg = WaitForUserDialog(msg)
    dlg.show()
    IJ.runMacroFile(os.path.join(script_dir, "Central_frequency.py"))
    IJ.runMacroFile(os.path.join(script_dir, "Geometric_accuracy.py"))
    IJ.runMacroFile(os.path.join(script_dir, "High_contrast_spatial_resolution.py"))
    IJ.runMacroFile(os.path.join(script_dir, "Low_contrast_objective_detectability.py"))
    IJ.runMacroFile(os.path.join(script_dir, "Signal_to_noise_ratio.py"))
    IJ.runMacroFile(os.path.join(script_dir, "Image_intensity_uniformity.py"))
    IJ.runMacroFile(os.path.join(script_dir, "Percentage_signal_ghosting.py"))
    IJ.runMacroFile(os.path.join(script_dir, "Slice_position_accuracy.py"))
    IJ.runMacroFile(os.path.join(script_dir, "Slice_thickness_accuracy.py"))

