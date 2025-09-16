from ij import IJ, WindowManager
from ij.gui import WaitForUserDialog, Roi, Line, OvalRoi, GenericDialog
from ij.io import OpenDialog
from java.lang import Math
from ij.measure import ResultsTable
import math
from ij.plugin import ImageCalculator
from ij.measure import Measurements
from ij.plugin.frame import RoiManager
from java.awt import Window, Font

IJ.log("---- Signal to Noise Ratio Test ----")

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
   
def open_dicom_file(prompt):
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

def area_to_radius_pixels(area_cm2, px_w_cm, px_h_cm):
    pixel_area_cm2 = px_w_cm * px_h_cm
    return math.sqrt(area_cm2 / (math.pi * pixel_area_cm2))

def medir_roi_mean(imp, roi=None):
    if roi is not None:
        imp.setRoi(roi)
    stats = imp.getStatistics(Measurements.MEAN)
    return stats.mean

def medir_roi_std(imp, roi=None):
    if roi is not None:
        imp.setRoi(roi)
    stats = imp.getStatistics(Measurements.STD_DEV)
    return stats.stdDev

def subtract_two_images_via_calculator():
    # 1) Abrir imagens A e B
    WaitForUserDialog("Open the first T1 image to proceed with the SNR test.").show()
    impA = open_dicom_file("Select the FIRST image (A)")
    IJ.run(impA, "Original Scale", "")
    IJ.resetMinAndMax(impA)
    IJ.run("In [+]", "")
    IJ.run("In [+]", "")
    if impA is None: return
    WaitForUserDialog("Open the second T1 image to proceed with the SNR test.").show()
    impB = open_dicom_file("Select the SECOND image (B)")
    if impB is None: return
    
    impA.setSlice(7)
    impB.setSlice(7)


#    # 2) Garantir que B tenha mesmo tamanho que A
#    _match_size_B_to_A(impA, impB)
#
#    # 3) Converter para 32-bit (evita clipping/overflow e padroniza tipo)
#    if impA.getBitDepth() != 32: IJ.run(impA, "32-bit", "")
#    if impB.getBitDepth() != 32: IJ.run(impB, "32-bit", "")

    # 4) Image Calculator: A - B  (criando uma nova janela)
    ic = ImageCalculator()
    result = ic.run("subtract create", impA, impB)  # 'create' => nova imagem
    if result is not None:
        result.setTitle("Subtraction (A - B)")
        result.show()
        IJ.log("Subtraction finished: A - B")
    else:
        IJ.error("Fail to subtract (Image Calculator).")
    
    impB.close()
    
    return result, impA

# Verifica se a imagem está aberta
#if imp is None:
#    IJ.error("Nenhuma imagem aberta.")
#    raise SystemExit

result, impA = subtract_two_images_via_calculator()
printImageType(impA)

# ===== Passo 2: Calibração =====
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

# ===== Passo 2b: Criar ROI grande de 200 cm² para posicionamento manual =====
radius_large = area_to_radius_pixels(200.0, pixel_width_cm, pixel_height_cm)
center_x = impA.getWidth() / 2.0
center_y = impA.getHeight() / 2.0
roi_large = OvalRoi(center_x - radius_large, center_y - radius_large, radius_large*2, radius_large*2)
impA.setRoi(roi_large)

dlg = WaitForUserDialog("Set ROI (200 cm^2)",
    "Move the ROI to the place that you wish.\nPress OK to continue.")
dlg.show()

# Adicionar ROI grande no ROI Manager
rm = RoiManager.getInstance()
if rm is None:
    rm = RoiManager()
rm.reset()  # limpa ROIs antigas
rm.addRoi(roi_large)

result.setRoi(roi_large)

gd = GenericDialog("Instructions")
gd.addMessage("WARNING!", Font("SansSerif", Font.BOLD, 20))
gd.addMessage("Close the ROI Manager window right after finishing the test.", Font("SansSerif", Font.ITALIC, 12))
gd.addMessage("Press 'OK' to continue.", Font("SansSerif", Font.ITALIC, 12))
gd.showDialog()
if gd.wasCanceled():
    IJ.log("Cancelled.")
    raise SystemExit

mean_ref = medir_roi_mean(impA)
std_ref = medir_roi_std(result)
SNR = mean_ref/std_ref
dlg=WaitForUserDialog("SNR test finished, collect the results.")
dlg.show()
impA.close()
result.close()

IJ.log("Mean: {:.3f}".format(mean_ref))
IJ.log("Standard Deviation: {:.3f}".format(std_ref))
IJ.log("SNR: {:.3f}".format(SNR))
IJ.run("Clear Results")
IJ.log("---- End of the SNR test ----")
IJ.log("")