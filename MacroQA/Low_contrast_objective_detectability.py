from ij import IJ, WindowManager
from ij.io import OpenDialog
from ij.measure import ResultsTable
from ij.gui import WaitForUserDialog
from ij import ImagePlus
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
        print("Histograma não disponível.")
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

    # Filtrar dados acima da mediana com contagens significativas
    peak = max(y_vals)
    threshold = peak * 0.02

    x_fit = []
    y_fit = []
    for x, y in zip(x_vals, y_vals):
        if x > median_value and y >= threshold:
            x_fit.append(x)
            y_fit.append(y)

    if len(x_fit) < 2:
        print("Poucos pontos significativos acima da mediana.")
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
        IJ.error("Falha ao abrir a imagem.")
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

IJ.log("---- Inicio do teste de Detalhes de Baixo Contraste ----")    
WaitForUserDialog("Clique em OK para selecionar a imagem T1 e realize a contagem das esferas de baixo indice de contraste.").show()

imp = open_dicom_file("Select T1-weighted DICOM image (multi-slice)")

# Verifica se a imagem está aberta
if imp is None:
    IJ.error("Nenhuma imagem aberta.")
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
WaitForUserDialog("Fatia 8 - Realize a analise e clique OK").show()
fatia8 = get_number_or_nan("Digite a quantidade de esferas visiveis na fatia 8:", 1.0)

# Vai para fatia 9
imp.setSlice(9)
WaitForUserDialog("Fatia 9 - Realize a analise e clique OK").show()
fatia9 = get_number_or_nan("Digite a quantidade de esferas visiveis na fatia 9:", 1.0)

# Vai para fatia 10
imp.setSlice(10)
WaitForUserDialog("Fatia 10 - Realize a analise e clique OK").show()
fatia10 = get_number_or_nan("Digite a quantidade de esferas visiveis na fatia 10:", 1.0)

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
    fechar_wl()
    IJ.run("Brightness/Contrast...")
    IJ.run("Window/Level...")
    
WaitForUserDialog("Fatia 11 - Realize a analise e clique OK").show()
fatia11 = get_number_or_nan("Digite a quantidade de esferas visiveis na fatia 11:", 1.0)
imp.close()
# --- Solicita nova imagem ---

WaitForUserDialog("Abra a imagem ponderada em T2.").show()
t2w = open_dicom_file("Clique Ok para selecionar a imagem ponderada em T2")
if t2w is None:
    exit()
# Obtém a nova imagem ativa
imp2 = IJ.getImage()
if imp2 is None or imp2 == imp:
    IJ.error("Nenhuma nova imagem aberta ou a mesma imagem foi reutilizada.")
    raise SystemExit

# Print image type
printImageType(imp2)

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
WaitForUserDialog("Fatia 16 - Realize a analise e clique OK").show()
fatia16 = get_number_or_nan("Digite a quantidade de esferas visiveis na fatia 16:", 1.0)

# Vai para fatia 18 da nova imagem
imp2.setSlice(18)
WaitForUserDialog("Fatia 18 - Realize a analise e clique OK").show()
fatia18 = get_number_or_nan("Digite a quantidade de esferas visiveis na fatia 18:", 1.0)

# Vai para fatia 20 da nova imagem
imp2.setSlice(20)
WaitForUserDialog("Fatia 20 - Realize a analise e clique OK").show()
fatia20 = get_number_or_nan("Digite a quantidade de esferas visiveis na fatia 20:", 1.0)

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
    fechar_wl()
    IJ.run("Brightness/Contrast...")
    IJ.run("Window/Level...")
    
WaitForUserDialog("Fatia 22 - Realize a analise e clique OK").show()
fatia22 = get_number_or_nan("Digite a quantidade de esferas visiveis na fatia 22:", 1.0)
esferas_T1 = fatia8 + fatia9 + fatia10 + fatia11
esferas_T2 = fatia16 + fatia18 + fatia20 + fatia22
imp2.close()
fechar_wl()

WaitForUserDialog("Teste de Detalhes de Baixo Contraste finalizado, colete os resultados.").show()

IJ.run("Clear Results")
IJ.log("Quantidade de esferas em T1: %s" % ("NaN" if (isinstance(esferas_T1, float) and math.isnan(esferas_T1)) else int(esferas_T1)))
IJ.log("Quantidade de esferas em T2: %s" % ("NaN" if (isinstance(esferas_T2, float) and math.isnan(esferas_T2)) else int(esferas_T2)))
IJ.log("---- Fim do teste de Detalhes de Baixo Contraste ----")
IJ.log("")
