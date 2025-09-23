# MacroQA: An ImageJ Macro for ACR MRI Quality Assurance
`MacroQA` is a comprehensive ImageJ/Fiji macro designed to provide a more reliable and practical implementation of the American College of Radiology (ACR) Quality Assurance (QA) tests. Its development was motivated by academic and pedagogical needs, aiming to simplify the testing process for students, researchers, and MRI staff. By leveraging ImageJ/Fiji's built-in functions, MacroQA can perform all tests from the MRI ACR phantom manual with impressive accuracy and efficiency, completing the process in just a few minutes.

---

## Why MacroQA?
Most existing implementations for performing ACR QA tests rely on proprietary software, such as MATLAB, which requires a paid license and limits accessibility. This creates a significant barrier for researchers, educators, students and MRI staff in resource-constrained environments.\
In contrast, MacroQA is:
- **Free and open-source** - built entirely on Image/Fiji.
- **Accessible** - written in Jython, a Python-like (Python2) language already embedded in Fiji.
- **Transparent and reproducible** - the source code is openly available for inspection, validation, and further development.

---

## Tests included
MacroQA performs in a semi-automated way the following ACR phantom QA tests:
- **Central Frequency** – checks imaging frequency stability extracting the value from DICOM header.  
- **Geometric Accuracy** – verifies correct image scaling in all directions.  
- **High-contrast Spatial Resolution** – evaluates ability to resolve small objects.  
- **Slice Thickness Accuracy** – ensures prescribed slice thickness is achieved.  
- **Slice Position Accuracy** – confirms accurate slice prescription relative to the localizer.  
- **Image Intensity Uniformity** – measures uniformity of signal across the phantom.  
- **Percent-signal Ghosting** – quantifies ghosting artifacts.  
- **Low-contrast Object Detectability** – assesses visibility of low-contrast structures.  
- **Signal-to-noise Ratio (SNR)** – optional test for background noise evaluation.  

Each test follows the acceptance criteria defined in the **ACR MRI QA Program**.  

---

## Instalation
1. Ensure that you have [Fiji](https://imagej.net/software/fiji/) installed, preferably with JAVA 8 runtime.
*Note: We recommend Fiji version because it already includes Jython library.*
2. Clone or download the `MacroQA` repository from this GitHub page.

---

## How to use MacroQA in Fiji?
MacroQA can be used in two main ways, depending on your preference:

### Method 1: Run directly via Macro Editor
This method is ideal for quick use or one-off tests.

**Steps (Fiji):**
1. Open the ***StartupMacros*** in the *Plugins > Macros* tab.
2. In your file explorer, locate the `MacroQA` folder.
3. Open the folder and double-click on the macro that you want to run.
4. The macro will open in Fiji's editor - simply press *Run*.

*For ImageJ/ImageJ2 users* the steps are similar, but ensure that the Jython library is also installed.*

---

### Method 2: Install as a Plugin
Installing `MacroQA` as a plugin integrates it into Fiji's menu system, maiking it persistently available across sessions.

**Steps:**
1. Copy the entire `MacroQA` folder into your Fiji installation under: `C:\Program Files\Fiji\Fiji.app\plugins\Macros`(usually on windows) or any other subfolder that you want.
2. Restart Fiji.
3. The macros will now appear in the *Plugins > Macros* menu.

---

## Known notes & recommendations
- **Java / Jython**: MacroQA relies on Jython (Python 2). Ensure Fiji is running with a Java runtime that supports Jython (Java 8 is recommended).  
- **Enhanced/multi-frame DICOMs**: The macros attempt to handle the following cases: *enhanced DICOMs, multi-frame DICOMs and single-frame DICOMs*, but for enhanced DICOM follows proprietary Philips ordering formats.

---

## Contributing
Contributions are welcome. Please open issues for bugs or feature requests. Pull requests should include a short description and, when appropriate, test data.

---

# TODO
- corrigir bugs
- revisão

Created by Gabriel Branco, Victor H. Celoni, Pedro H. Cayres and Ícaro Oliveira
