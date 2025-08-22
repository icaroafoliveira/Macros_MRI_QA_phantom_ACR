from ij import IJ, WindowManager
from ij.io import OpenDialog
from ij.measure import ResultsTable
from ij.gui import WaitForUserDialog
from ij import ImagePlus

def ajustar_window_level(imp, level, window):
    min_display = level - window / 2
    max_display = level + window / 2
    imp.setDisplayRange(min_display, max_display)
    imp.updateAndDraw()

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
IJ.log("---- Inicio do teste de Detalhes de Baixo Contraste ----")    
WaitForUserDialog("Clique em Ok para selecionar a imagem T1 e realize a contagem das esferas de baixo indice de contraste").show()

imp = open_dicom_file("Select T1-weighted DICOM image (multi-slice)")

# Verifica se a imagem está aberta
if imp is None:
    IJ.error("Nenhuma imagem aberta.")
    raise SystemExit

# --- Primeira imagem ---

# Ajuste de Window/Level: window = 850, level = 1900
IJ.run("In [+]","")
IJ.run("In [+]","")
IJ.run("Window/Level...")

# Vai para fatia 8
imp.setSlice(8)
ajustar_window_level(imp, level=1900, window=850)
WaitForUserDialog("Fatia 8 - Realize a analise e clique OK").show()

# Vai para fatia 9
imp.setSlice(9)
WaitForUserDialog("Fatia 9 - Realize a analise e clique OK").show()

# Vai para fatia 10
imp.setSlice(10)
WaitForUserDialog("Fatia 10 - Realize a analise e clique OK").show()

# Vai para fatia 11
ajustar_window_level(imp, level=1800, window=850)
imp.setSlice(11)
WaitForUserDialog("Fatia 11 - Realize a analise e clique OK").show()
imp.close()
# --- Solicita nova imagem ---

WaitForUserDialog("Abra a imagem ponderada em T2").show()
t2w = open_dicom_file("Clique Ok para selecionar a imagem ponderada em T2")
if t2w is None:
    exit()
# Obtém a nova imagem ativa
imp2 = IJ.getImage()
if imp2 is None or imp2 == imp:
    IJ.error("Nenhuma nova imagem aberta ou a mesma imagem foi reutilizada.")
    raise SystemExit

IJ.run("In [+]","")
IJ.run("In [+]","")
# Reset de Window/Level
IJ.run("Window/Level...")

# Vai para fatia 16 da nova imagem
imp2.setSlice(16)
imp2.updateAndDraw()
# Novo ajuste: window = 780, level = -1650
ajustar_window_level(imp2, level=-1650, window=780)

WaitForUserDialog("Fatia 16 - Realize a analise e clique OK").show()

# Vai para fatia 18 da nova imagem
imp2.setSlice(18)
WaitForUserDialog("Fatia 18 - Realize a analise e clique OK").show()

# Vai para fatia 20 da nova imagem
imp2.setSlice(20)
WaitForUserDialog("Fatia 20 - Realize a analise e clique OK").show()

# Vai para fatia 22 da nova imagem
imp2.setSlice(22)
ajustar_window_level(imp2, level=-1700, window=1100)
WaitForUserDialog("Fatia 22 - Realize a analise e clique OK").show()
imp2.close()

WaitForUserDialog("Teste de Detalhes de Baixo Contraste finalizado, colete os resultados.").show()

IJ.run("Clear Results")
IJ.log("---- Fim do teste de Detalhes de Baixo Contraste ----")
IJ.log("")