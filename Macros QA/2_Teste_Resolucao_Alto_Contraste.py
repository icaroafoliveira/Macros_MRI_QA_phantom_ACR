from java.awt import Rectangle
from ij import IJ, WindowManager
from ij.gui import Roi, WaitForUserDialog
from ij.measure import Measurements
from ij.plugin.frame import RoiManager
from ij.process import ImageStatistics
from ij.measure import ResultsTable
from ij.io import OpenDialog
import ij.io
import math

def open_dicom_file(prompt):
    od = ij.io.OpenDialog(prompt, None)
    path = od.getPath()
    if path is None:
        return None
    imp = IJ.openImage(path)
    if imp is None:
        IJ.error("Falha ao abrir a imagem.")
        return None
    imp.show()
    return imp

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

IJ.log("---- Inicio do teste de Resolucao de Alto Contraste ----")
WaitForUserDialog("Abra a imagem T1 e realize o teste de resolucao de alto contraste.").show()
imp = open_dicom_file("Select T1-weighted DICOM image (multi-slice)")

if imp is None:
    IJ.error("Nenhuma imagem aberta.")
    raise SystemExit

# ===== Passo 1: Selecionar fatia =====
imp.setSlice(1)
IJ.log("Fatia definida para 1.")

IJ.run(imp, "Original Scale", "")
IJ.resetMinAndMax(imp)
IJ.log("Window/Level ajustados para valores centrais.")

# Dar zoom como se fosse tecla "+"
IJ.run("In [+]", "")
IJ.run("In [+]", "")
IJ.run("In [+]", "")
#IJ.run("In [+]", "")
IJ.setTool("rectangle")
# Ajustar a janela para caber no novo tamanho
win = imp.getWindow()
if win is not None:
    win.pack()  # força redimensionamento da janela
    
# ===== Passo 2: Usuário seleciona a ROI =====
dlg = WaitForUserDialog(
    "Selecione a area para o zoom. \n"
    "Desenhe uma ROI na regiao que deseja ampliar e clique OK.")
    
dlg.show()
IJ.log("Zoom ajustado para a ROI selecionada")

roi = imp.getRoi()
if roi is None:
    IJ.error("Nenhuma ROI foi selecionada!")
    raise SystemExit
else:
    bounds = roi.getBounds()
    canvas = imp.getCanvas()
    if canvas is not None:
        # Ajusta visualização para a ROI
        canvas.setSourceRect(Rectangle(bounds.x, bounds.y, bounds.width, bounds.height))
        imp.updateAndDraw()
        
        # Dá zoom automático até caber a ROI
        while (canvas.getSrcRect().width > bounds.width or 
               canvas.getSrcRect().height > bounds.height):
            canvas.zoomIn(bounds.x + bounds.width // 2, bounds.y + bounds.height // 2)
            canvas.zoomIn(bounds.x + bounds.width // 2, bounds.y + bounds.height // 2)
            if (canvas.getSrcRect().width <= bounds.width and 
                canvas.getSrcRect().height <= bounds.height):
                break

# ===== Passo 3: Ajuste automático do window/level =====
l = 450.0
w = 150.0
min_display = l - (w / 2)
max_display = l + (w / 2)
IJ.setMinAndMax(imp, min_display, max_display)

# Abre a janela de W&L já configurada
IJ.run("Window/Level...")

# ===== Passo 4: Ajuste manual =====
from ij.gui import GenericDialog
from java.awt import Font
from ij import IJ

gd = GenericDialog("Instrucoes")
gd.addMessage("AVISO!", Font("SansSerif", Font.BOLD, 20))
gd.addMessage("Ajuste level e window no proximo passo ate que os furos no insert de resolucao sejam exibidos individualmente.", Font("SansSerif", Font.ITALIC, 12))
gd.addMessage("Clique em 'OK' para continuar.", Font("SansSerif", Font.ITALIC, 12))
gd.showDialog()
if gd.wasCanceled():
    IJ.log("Cancelado.")
    raise SystemExit



dlg = WaitForUserDialog( 
    "Os tres conjuntos de pontos formando quadrados tem diferentes tamanhos de furo.\n"
    "Da esquerda para a direita: 1.1 mm, 1.0 mm e 0.9 mm.\n"
    "Em cada conjunto, o quadrado de cima indica a resolucao horizontal e o de baixo a vertical."
)
dlg.show()

CANCEL_SENTINEL = float(-2147483648.0)

def get_number_or_nan(prompt, default=1.0):
    v = IJ.getNumber(prompt, default)
    if v == CANCEL_SENTINEL or (isinstance(v, float) and math.isnan(v)):
        return float('nan')
    return v

valor_upper = get_number_or_nan("Digite o valor do tamanho de furo upper em mm:", 1.0)
valor_lower = get_number_or_nan("Digite o valor do tamanho de furo lower em mm:", 1.0)

dlg = WaitForUserDialog( 
	"Teste de Resolucao de Alto Contraste finalizado, colete os resultados.\n")
dlg.show()
imp.close()
fechar_wl()

IJ.run("Clear Results")
IJ.log("Tamanho de furo upper [mm]: %s" % ("NaN" if (isinstance(valor_upper, float) and math.isnan(valor_upper)) else ("%.1f" % valor_upper)))
IJ.log("Tamanho de furo lower [mm]: %s" % ("NaN" if (isinstance(valor_lower, float) and math.isnan(valor_lower)) else ("%.1f" % valor_lower)))
IJ.log("---- Fim do teste de Resolucao de Alto Contraste ----")
IJ.log("")