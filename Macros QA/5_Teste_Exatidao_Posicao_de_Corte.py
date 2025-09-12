from ij import IJ, WindowManager
from ij.gui import WaitForUserDialog
from ij.io import OpenDialog

IJ.log("---- Inicio do teste de Exatidao da Posicao ----")

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

WaitForUserDialog("Abra a imagem T1 e realize o teste de exatidao de posicao de corte.").show()
imp = open_dicom_file("Select T1-weighted DICOM image (multi-slice)")

# Verifica se a imagem está aberta
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
IJ.run("Brightness/Contrast...")
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
fechar_wl()

WaitForUserDialog("Teste de Exatidao da Posicao finalizado, colete os resultados.\n").show()

IJ.run("Clear Results")
IJ.log("---- Fim do teste de Exatidao da Posicao ----")
IJ.log("")