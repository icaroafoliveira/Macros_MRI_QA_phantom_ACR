---
title: 'MacroQA: An ImageJ Macro for ACR MRI Quality Assurance'
tags:
  - ImageJ/Fiji
  - Macro
  - QA
  - MRI
  - Jython
  - Python
authors:
  - name: Gabriel Branco Vitorino
    equal-contrib: true
    affiliation: 1
  - name: Victor Hugo Celoni Gnatkovski
    equal-contrib: true
    affiliation: 1
  - name: Pedro Henrique Tosta Cayres de Oliveira
    equal-contrib: true
    affiliation: 1
  - name: Mateus Setubal Quiel
    equal-contrib: true
    affiliation: 1
  - name: Ícaro Agenor Ferreira de Oliveira
    corresponding: true
    orcid: 0000-0002-7102-5569
    affiliation: "2,3"
affiliations:
 - name: "Departamento de Física, Faculdade de Filosofia, Ciências e Letras de Ribeirão Preto, Universidade de São Paulo, Brazil"
   index: 1
 - name: "Fundação de Apoio ao Ensino, Pesquisa e Assistência do Hospital das Clínicas da Faculdade de Medicina de Ribeirão Preto, Brazil"
   index: 2
 - name: "Centro das Ciências da Imagem e Física Médica, Hospital das Clínicas da Faculdade de Medicina de Ribeirão Preto, Universidade de São Paulo, Brazil"
   index: 3 
date: 5 October 2025
bibliography: paper.bib
---

# Summary
MacroQA is an open-source ImageJ/Fiji macro package that implements the American College of Radiology (ACR) quality assurance (QA) tests for MRI phantoms. The project was developed with academic and pedagogical goals in mind, and it aims to simplify and standardize phantom testing. By leveraging Fiji/ImageJ's built-in functionality, MacroQA performs the ACR phantom tests quickly and reproducibly, completing the QA workflow within minutes. As a free and accessible alternative to proprietary software, MacroQA lowers barriers to adoption, promotes reproducibility, and supports collaborative development in the MRI research and clinical communities.

# Statement of need
MacroQA is a Jython program designed to perform Quality Assurance (QA) procedures for magnetic resonance imaging (MRI). Given how crucial MRI has become in modern medicine and neuroscience—ranging from clinical diagnoses to exploring functional brain connectivity—it’s vital to ensure the quality and consistency of the images produced [@dumoulin_ultra-high_2018; @granziera_quantitative_2021; @ruber_mri_2018; @macdonald_cerebrovascular_2015; @stocker_reproducibility_2025]. This is where robust Quality Assurance (QA) and Quality Control (QC) procedures come into play.

The procedures incorporated in MacroQA align with the American College of Radiology (ACR) guidelines, which utilize a specialized accreditation phantom for their QA program. Many current software solutions for ACR QA are tied to vendor-specific or proprietary systems, which often come with high licensing costs or operate within closed-source frameworks, imposing financial and accessibility challenges for research, education, and clinical practice.

MacroQA bridges this gap by offering an open-source solution of the ACR QA test suite through the Fiji/ImageJ platform, effectively removing dependency on commercial software. Developed using Jython scripting language, MacroQA emphasizes transparency, verifiability, and accessibility, providing a cost-effective and shareable tool that supports both clinical best practices and reproducible research.

# State of the Field
There are alternative open-source frameworks out there, often built on MATLAB applications [@epistatou_automated_2020; @vogelbacher_labqa2go_2019; @sun_open_2015]. For instance, LAB-QA2GO [@vogelbacher_labqa2go_2019] is a virtual machine with fully automated analyses with scripts written in MATLAB. And there are other MATLAB-based solutions like [@davids_fully-automated_2014] and OSAQA[@sun_open_2015], which also deliver fully automated functionalities for key QC tests. While these tools can be highly automated, they come with licensing issues since MATLAB isn’t free and requires users to have programming knowledge. Additionally, automated pipelines may obscure intermediate steps, making it harder for users, especially those still learning the ACR QA procedures, to inspect and understand individual QC measurements.

MacroQA was designed to address these challenges. Instead of relying on proprietary environments or enforcing strict automation, it provides structured automation within the widely-used, open-source Fiji (ImageJ) platform. This design promotes reproducibility while allowing users to interact and visualize data, verify ROI placements, and maintain transparency in methodology. 
The value of MacroQA lies in offering a complete, modular, and openly accessible version of the ACR MRI QA protocol that finds a balance between automation and user interpretation, something that current proprietary or MATLAB-based solutions fail to achieve.

# Software design

MacroQA is built in Jython (www.jython.org), a Python implementation for the Java platform, and runs within Fiji/ImageJ. Fiji was selected for its wide usage, free availability, and cross-platform. Each QC test is implemented as an independent macro, making development and installation more straightforward. After installation, users can find macros under a dedicated "MacroQA" menu.

- **Inputs:** DICOM images acquired with the ACR accreditation phantom.
- **Outputs:** numerical results displayed in the Fiji log window and optionally saved to disk.

MacroQA is distributed under the GNU General Public License v3.0 (GPL-3.0), which ensures the code remains free to use, modify, and redistribute under the license terms.

# Research Impact Statement

MacroQA has been validated across multiple clinical MRI systems (3T and 1.5T) and is now part of our weekly QA procedures. Benchmarking demonstrated substantial time savings compared to manual analysis while maintaining high repeatability, quantified using normalized repeatability coefficients across several weeks. All ACR-defined tolerance thresholds were consistently met, supporting reliability for longitudinal monitoring. 

These findings have been recognized and will be presented at the upcoming International Society of Magnetic Resonance in Medicine (ISMRM) conference in 2026.

The software also addresses regulatory compliance requirements, covering all tests required by the American College of Radiology (ACR) and ANVISA in Brazil. This makes it useful not just in research settings, but also in clinical settings for accreditation purposes.

To make adoption easier for external users, MacroQA comes with thorough documentation, example datasets, and reproducible materials. Its implementation with Fiji ensures it is compatible with a solid user base in biomedical imaging.

# Installation
1. Ensure that you have [Fiji](https://imagej.net/software/fiji/) installed, preferably with Java 8 runtime.
*Note: We recommend using the Fiji distribution because it already includes the Jython library.*
2. Clone or download the `MacroQA` repository from this GitHub page.
*Note: This software is a self-contained ImageJ/Fiji macro and does not require any external dependencies beyond a standard installation of Fiji. It relies solely on the core functions of ImageJ and Jython.*

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

### Method 2: Install as a Plugin
Installing `MacroQA` as a plugin integrates it into Fiji's menu system, making it persistently available across sessions.

**Steps (general):**
1. Copy the `MacroQA` folder into a subdirectory of your Fiji `plugins` folder (for example, `.../Fiji.app/plugins/` or `.../Fiji.app/plugins/Macros/`).
2. Restart Fiji.
3. The macros will now appear in the *Plugins > Macros* menu.

**Platform-specific examples:**
- Windows (typical): `C:\Program Files\Fiji\Fiji.app\plugins\Macros\MacroQA`
- macOS (typical): `/Applications/Fiji.app/plugins/Macros/MacroQA` or `~/Fiji.app/plugins/Macros/MacroQA`
- Linux (typical): `/home/<user>/Fiji.app/plugins/Macros/MacroQA` or `/opt/Fiji.app/plugins/Macros/MacroQA`

# Functionality

## Usage example
Once installed, MacroQA becomes available under the Plugins > Macros menu in Fiji (Figure 1). From there, the user can select any of the available ACR quality control tests, such as Central Frequency, Geometric Accuracy, or Signal-to-Noise Ratio.
![Figure 1: Accessing QC tests from Macros menu in Fiji.](../figures/macro001.png){ width=60% }
When a test is launched, MacroQA guides the user through the required steps via dialog boxes and messages. For example, running the Central Frequency test (Figure 2) prompts the user to select the appropriate image series and automatically reports the measured resonance frequency in the Fiji log window.
![Figure 2: Example of Central Frequency test dialog.](../figures/macro002.png){ width=60% }
Some tests require user interaction, such as drawing straight lines or selecting regions of interest. In the Geometric Accuracy test (Figures 3), the macro requests that the user load the Localizer image and draw reference lines across the phantom. It then requests that the user load the ACR T1 series, where two different slices are assessed. These inputs are then used to calculate geometric dimensions, which are compared against the ACR acceptance criteria.
![Figure 3: Example of procedure for the Geometric Accuracy test.](../figures/macro003.png){ width=60% }

This combination of guided prompts and automated calculations ensures that even users with limited prior experience can reliably perform ACR phantom quality control tests in a reproducible manner.

## Quality control tests and their acceptance criteria

### Required images
For both large and medium phantoms, a minimum of three acquisitions are required: the **Localizer**, **ACR T1 series**, and the **ACR T2 series**.
- **Localizer:** a single-slice sagittal spin-echo acquired at the phantom's center.
- **ACR T1:** an 11-slice axial T1-weighted (T1w) series.
- **ACR T2:** an 11-slice axial T2-weighted (T2w) series acquired with two echo times; the longer echo is used as the T2-weighted image.

Below is a brief summary of the quality control tests supported by MacroQA. 
Users are encouraged to first review and follow the [ACR MRI Phantom testing guidelines](https://accreditationsupport.acr.org/helpdesk/attachments/11093487417) when using MacroQA for the first time. This ensures familiarity with the procedures and acceptance criteria before relying on automated analysis.

### Central frequency

**Objective:** Ensure the scanner operates at the correct resonance frequency. Off-resonance operation reduces signal-to-noise ratio (SNR) and may indicate drift in the static magnetic field.

**Frequency:** weekly

**Acceptance criteria:** within 1 ppm per day for superconducting magnets

**Image type:** ACR T1-weighted (T1w)

### Geometric accuracy

**Objective:** Verify that image scaling reflects the true dimensions of the imaged object.

**Frequency:** weekly

**Acceptance criteria:** ±3 mm (large phantom) and ±2 mm (medium phantom)

**Image type:** ACR T1-weighted (T1w)

### High-contrast spatial resolution

**Objective:** Assess the scanner's ability to resolve small objects.

**Frequency:** weekly

**Acceptance criteria:** visualization of the 1 mm holes

**Image type:** ACR T1-weighted (T1w) and T2-weighted (T2w)

### Slice thickness accuracy

**Objective:** Verify that the prescribed slice thickness matches the acquired slice.

**Frequency:** annual

**Acceptance criteria:** ±0.75 mm

**Image type:** ACR T1-weighted (T1w) and T2-weighted (T2w)

### Slice position accuracy

**Objective:** Assess the accuracy of slice positioning using the localizer image as a reference.

**Frequency:** annual

**Acceptance criteria:** ≤5 mm in both directions

**Image type:** ACR T1-weighted (T1w) and T2-weighted (T2w)

### Image intensity uniformity

**Objective:** Measure intensity uniformity over a large water-only region of the phantom near the middle of the imaged volume (typically near the head coil center).

**Frequency:** annual

**Acceptance criteria:** for scanners at 3T: PIU ≥ 80; for scanners < 3T: PIU ≥ 85

**Image type:** ACR T1-weighted (T1w) and T2-weighted (T2w)

### Percent-signal ghosting

**Objective:** Quantify ghosting artifacts in ACR images.

**Frequency:** annual

**Acceptance criteria:** ≤ 3%

**Image type:** ACR T1-weighted (T1w) and T2-weighted (T2w)

### Low-contrast object detectability

**Objective:** Determine the extent to which low-contrast objects are discernible in the images.

**Frequency:** weekly

**Acceptance criteria:** for scanners at 3T: ≥37 spokes (ACR T1 and T2). For scanners between 1.5T and <3T: ≥30 spokes (ACR T1) and ≥25 spokes (ACR T2).

**Image type:** ACR T1-weighted (T1w) and T2-weighted (T2w)

### Signal-to-noise ratio (SNR)

**Objective:** Measure the ratio of true signal to background noise. Although SNR is not always explicitly included in the ACR manual, it is a key indicator of image quality.

**Frequency:** weekly

**Acceptance criteria:** not formally specified by the ACR

**Image type:** ACR T1-weighted (T1w) — note: SNR may require additional acquisitions or specific measurement regions

## Availability
MacroQA is publicly available on [GitHub](https://github.com/icaroafoliveira/Macros_MRI_QA_phantom_ACR). The tool is distributed under the GNU General Public License v3.0 (GPL-3.0). Installation and usage instructions are provided in the repository README. We welcome contributions and feedback from the community — please open an issue to report bugs or request features; pull requests are also welcome.

# AI usage disclosure
Limited AI-assisted language editing was used during manuscript preparation to improve clarity and grammar (Grammarly). All technical content, software design decisions, validation procedures, and scientific interpretations were written and verified by the authors.

# Acknowledgements
GBV, VHCG, PHTCO, and MSQ contributed nearly equally to coding, software development, and manuscript preparation during their internship. IAFO conceived the idea for MacroQA, contributed to coding and writing, and provided supervision and mentorship throughout the project.

# References
