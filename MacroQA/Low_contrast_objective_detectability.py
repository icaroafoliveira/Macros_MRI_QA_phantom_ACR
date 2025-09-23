from ij import IJ, WindowManager
from ij.io import OpenDialog
from ij.measure import ResultsTable
from ij.gui import WaitForUserDialog
import java
from ij.measure import Measurements
from ij.process import ImageStatistics
from ij.gui import GenericDialog
from java.awt import Font
import math

#def ajustar_window_level(imp, level, window):
#    min_display = level - window / 2
#    max_display = level + window / 2
#    imp.setDisplayRange(min_display, max_display)
#    imp.updateAndDraw()

# === Function to calculate optimal window/level based on histogram analysis ===
def calcular_window_level(imp):
    stats = imp.getStatistics()
    hist = stats.histogram
    if hist is None:
        print("Histogram not available.")
        return None, None
    if callable(hist):
        hist = hist()

    hist_min = stats.histMin
    x_vals = [i + hist_min for i in range(len(hist))]
    y_vals = hist

    # Cálculo da mediana real
    total_pixels = sum(y_vals)
    cumulative = 0
    median_value = x_vals[-1]

    for i in range(len(y_vals)):
        cumulative += y_vals[i]
        if cumulative >= total_pixels / 2:
            median_value = x_vals[i]
            break

    # Filter data above the median with significant counts
    peak = max(y_vals)
    threshold = peak * 0.02

    x_fit = []
    y_fit = []
    for x, y in zip(x_vals, y_vals):
        if x > median_value and y >= threshold:
            x_fit.append(x)
            y_fit.append(y)

    if len(x_fit) < 2:
        print("Few significant points above the median.")
        return None, None

    level = (max(x_fit) + min(x_fit)) / 2.0
    window = max(x_fit) - min(x_fit)

    return level, window

# === Function to close any open Brightness/Contrast or Window/Level dialogs ===
def fechar_wl():
    # Títulos mais comuns dessa janela
    candidatos = ["Brightness/Contrast", "W&L", "Window/Level", "B&C"]
    for t in candidatos:
        w = WindowManager.getWindow(t) or WindowManager.getFrame(t)
        if w is not None:
            # fecha sem perguntar
            try:
                w.dispose()   # fecha a janela
            except:
                try:
                    w.setVisible(False)
                except:
                    pass
            return True
    # fallback: varre janelas não-imagem e fecha se bater por nome
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

CANCEL_SENTINEL = float(-2147483648.0)

def get_number_or_nan(prompt, default=1.0):
    v = IJ.getNumber(prompt, default)
    if v == CANCEL_SENTINEL or (isinstance(v, float) and math.isnan(v)):
        return float('nan')
    return v

# === funcao para abrir DICOM file ===
def open_dicom_file(prompt):
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

IJ.log("---- Start of Low Contrast Objective Detectability Test ----")    
WaitForUserDialog("Click OK to select the T1 image and perform the count of low-contrast spheres.").show()

imp = open_dicom_file("Select T1-weighted DICOM image (multi-slice)")

# Verifica se a imagem está aberta
if imp is None:
    IJ.error("No image open.")
    raise SystemExit

# Print image type
printImageType(imp)

# --- Primeira imagem ---

# Ajuste de Window/Level: window = 850, level = 1900
IJ.run("In [+]","")
IJ.run("In [+]","")
IJ.run("Brightness/Contrast...")
IJ.run("Window/Level...")

# Vai para fatia 8
imp.setSlice(8)
level, window = calcular_window_level(imp)

if level is not None:
    # Ajuste manual para imagem T1
    level += 1480
    window *= 0.8

    # Aplicar na imagem
    min_display = level - window / 2.0
    max_display = level + window / 2.0
    imp.setDisplayRange(min_display, max_display)
    imp.updateAndDraw()
#print("Display range aplicado:")
#print("Min:", imp.getDisplayRangeMin())
#print("Max:", imp.getDisplayRangeMax())
WaitForUserDialog("Slice 8 - Perform the analysis and click OK").show()
t1_slice8 = get_number_or_nan("Enter the number of visible spheres in slice 8:", 10.0)

# Vai para fatia 9
imp.setSlice(9)
WaitForUserDialog("Slice 9 - Perform the analysis and click OK").show()
t1_slice9 = get_number_or_nan("Enter the number of visible spheres in slice 9:", 10.0)

# Vai para fatia 10
imp.setSlice(10)
WaitForUserDialog("Slice 10 - Perform the analysis and click OK").show()
t1_slice10 = get_number_or_nan("Enter the number of visible spheres in slice 10:", 10.0)

# Vai para fatia 11
#ajustar_window_level(imp)
imp.setSlice(11)
level, window = calcular_window_level(imp)

if level is not None:
    # Ajuste manual para imagem T1
    level += 1380
    window *= 0.85

    # Aplicar na imagem
    min_display = level - window / 2.0
    max_display = level + window / 2.0
    imp.setDisplayRange(min_display, max_display)
    imp.updateAndDraw()
    close_wl()
    IJ.run("Brightness/Contrast...")
    IJ.run("Window/Level...")

WaitForUserDialog("Slice 11 - Perform the analysis and click OK").show()
t1_slice11 = get_number_or_nan("Enter the number of visible spheres in slice 11:", 10.0)
imp.close()
# --- Solicita nova imagem ---

WaitForUserDialog("Open the T2-weighted image.").show()
t2w = open_dicom_file("Click OK to select the T2-weighted image.")
if t2w is None:
    exit()
# Obtém a nova imagem ativa
imp2 = IJ.getImage()
if imp2 is None or imp2 == imp:
    IJ.error("No new image opened or the same image was reused.")
    raise SystemExit

# Print image type
printImageType(imp2)

# Zoom in and reset display settings for the new image
IJ.run("In [+]","")
IJ.run("In [+]","")
# Reset de Window/Level
IJ.run("Window/Level...")

# Vai para fatia 16 da nova imagem
imp2.setSlice(16)
#imp2.updateAndDraw()
# Novo ajuste: window = 780, level = -1650
level, window = calcular_window_level(imp2)

if level is not None:
    # Ajuste manual para imagem T2 (valores diferentes!)
    level += 1100
    window *= 1.1

    # Aplicar na imagem
    min_display = level - window / 2.0
    max_display = level + window / 2.0
    imp2.setDisplayRange(min_display, max_display)
    imp2.updateAndDraw()
#print("Display range aplicado:")
#print("Min:", imp2.getDisplayRangeMin())
#print("Max:", imp2.getDisplayRangeMax())
WaitForUserDialog("Slice 16 - Perform the analysis and click OK").show()
fatia16 = get_number_or_nan("Enter the number of visible spheres in slice 16:", 1.0)

# Vai para fatia 18 da nova imagem
imp2.setSlice(18)
WaitForUserDialog("Slice 18 - Perform the analysis and click OK").show()
fatia18 = get_number_or_nan("Enter the number of visible spheres in slice 18:", 1.0)

# Vai para fatia 20 da nova imagem
imp2.setSlice(20)
WaitForUserDialog("Slice 20 - Perform the analysis and click OK").show()
fatia20 = get_number_or_nan("Enter the number of visible spheres in slice 20:", 1.0)

# Vai para fatia 22 da nova imagem
imp2.setSlice(22)
#ajustar_window_level(imp2)
level, window = calcular_window_level(imp2)

if level is not None:
    # Ajuste manual para imagem T2 (valores diferentes!)
    level += 1000
    window *= 1.1

    # Aplicar na imagem
    min_display = level - window / 2.0
    max_display = level + window / 2.0
    imp2.setDisplayRange(min_display, max_display)
    imp2.updateAndDraw()
    close_wl()
    IJ.run("Brightness/Contrast...")
    IJ.run("Window/Level...")

WaitForUserDialog("Slice 11 - Perform the analysis and click OK").show()
t2_slice11 = get_number_or_nan("Enter the number of visible spheres in slice 11:", 10.0)
spheres_T1 = t1_slice8 + t1_slice9 + t1_slice10 + t1_slice11
spheres_T2 = t2_slice8 + t2_slice9 + t2_slice10 + t2_slice11
imp2.close()
fechar_wl()

WaitForUserDialog("Low Contrast Detail Test completed. Collect the results.").show()

IJ.run("Clear Results")
IJ.log("Number of spheres in T1: %s" % ("NaN" if (isinstance(spheres_T1, float) and math.isnan(spheres_T1)) else int(spheres_T1)))
IJ.log("Number of spheres in T2: %s" % ("NaN" if (isinstance(spheres_T2, float) and math.isnan(spheres_T2)) else int(spheres_T2)))
IJ.log("---- End of Low Contrast Objective Detectability Test ----")
IJ.log("")
