#@ ImagePlus imp

from ij import IJ
from ij.gui import WaitForUserDialog
from java.awt import Rectangle
from ij import WindowManager

IJ.log("---- Inicio do teste de Resolucao de Alto Contraste ----")

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
    "Selecione a area para o zoom",
    "Desenhe uma ROI na regiao que deseja ampliar e clique OK.")
    
dlg.show()
IJ.log("Zoom ajustado para a ROI selecionada")

roi = imp.getRoi()
if roi is None:
    IJ.error("Nenhuma ROI foi selecionada!")
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
dlg = WaitForUserDialog("Ajuste manual - janelamento",
    "Ajuste o valor do janelamento ate que os furos no insert de resolucao sejam exibidos individualmente.")
dlg.show()


dlg = WaitForUserDialog( 
    "Os tres conjuntos de pontos formando quadrados tem diferentes tamanhos de furo.\n"
    "Da esquerda para a direita: 1.1 mm, 1.0 mm e 0.9 mm.\n"
    "Em cada conjunto, o quadrado de cima indica a resolucao horizontal e o de baixo a vertical."
)
dlg.show()

dlg = WaitForUserDialog( 
	"Teste de Resolucao de Alto Contraste finalizado, colete os resultados.\n"
	"Recomenda-se fechar a janela de W&B.")
dlg.show()

IJ.run("Clear Results")
IJ.log("---- Fim do teste de Resolucao de Alto Contraste ----")
IJ.log("")