from ij import IJ, WindowManager
from ij.gui import WaitForUserDialog
from ij.io import OpenDialog

IJ.log("---- Inicio do teste de Exatidao da Posicao ----")
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
    
def ajustar_window_level(imp, level, window):
    min_display = level - window / 2
    max_display = level + window / 2
    imp.setDisplayRange(min_display, max_display)
    imp.updateAndDraw()

WaitForUserDialog("Certifique-se que a imagem T1 esta aberta e clique Ok").show()

# Verifica se a imagem está aberta
imp = IJ.getImage()
if imp is None:
    IJ.error("Nenhuma imagem aberta.")
    raise SystemExit

# --- Primeira imagem ---
# Vai para fatia 1
imp.setSlice(1)

IJ.run(imp, "Original Scale", "")
# Ajusta window/level para valores centrais
IJ.resetMinAndMax(imp)

# Dar zoom como se fosse tecla "+"
IJ.run("In [+]", "")
IJ.run("In [+]", "")


# Ajuste de Window/Level: window = 10, level = 1000
ajustar_window_level(imp, level=1000, window=10)
IJ.run("Window/Level...")
# Espera confirmação para análise
WaitForUserDialog("Imagem 1 - Fatia 1 - Realize a analise e clique OK.\n"
"Caso a barra a esquerda seja maior, a diferenca sera negativa,\n" 
"e caso a barra da direita seja maior a diferenca sera positiva").show()

# Vai para fatia 11
imp.setSlice(11)
WaitForUserDialog("Imagem 1 - Fatia 11 - Realize a analise e clique OK.\n"
"Caso a barra a esquerda seja maior, a diferenca sera negativa,\n" 
"e caso a barra da direita seja maior a diferenca sera positiva").show()

imp.close()

WaitForUserDialog("Teste de Exatidao da Posicao finalizado, colete os resultados.\n"
	"Recomenda-se fechar a janela de W&L.").show()

IJ.run("Clear Results")
IJ.log("---- Fim do teste de Exatidao da Posicao ----")
IJ.log("")