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
    equal-contrib: true # (This is how you can denote equal contributions between multiple authors)
    affiliation: 1
  - name: Pedro Henrique Tosta Cayres de Oliveira
    equal-contrib: true
    affiliation: 1
  - name: Mateus Setubal Quiel
    equal-contribu: true
    affiliation: 1
  - name: Ícaro Agenor Ferreira de Oliveira
    corresponding: true # (This is how to denote the corresponding author)
    orcid: 0000-0002-7102-5569
    affiliation: "2,3"
affiliations:
 - name: "Departamento de Física, Faculdade de Filosofia, Ciências e Letras de Ribeirão Preto, Universidade de São Paulo, Brazil"
   index: 1
 - name: "Fundação de Apoio ao Ensino, Pesquisa e Assistência do Hospital das Clínicas da Faculdade de Medicina de Ribeirão Preto, Brazil"
   index: 2
 - name: "Centro das Ciências da Imagem e Física Médica, Hospital das Clínicas da Faculdade de Medicina de Ribeirão Preto, Universidade de São Paulo, Brazil"
   index: 3 
date: 20 October 2025
bibliography: paper.bib
---

# Summary
MacroQA is an open-source ImageJ/Fiji macro package that provides a reliable and practical implementation of the American College of Radiology (ACR) Quality Assurance (QA) tests. The project was developed with academic and pedagogical goals in mind, aiming to simplify and standardize MRI phantom testing. By leveraging ImageJ/Fiji’s built-in functionality, MacroQA performs several ACR phantom tests with high accuracy and efficiency, completing the full QA workflow within minutes. As a free and accessible alternative to proprietary software, MacroQA lowers barriers to adoption, promotes reproducibility, and supports collaborative development in the MRI research and clinical community.

# Statement of need
Magnetic resonance imaging (MRI) is one of the most powerful diagnostic and research tools in medicine. From a neuroimaging perspective, MRI enables the study of brain anatomy, functions, connectivity (functional and structural), and metabolism. Its diversity and broad applicability has made MRI indispensable in modern medicine and neuroscience [reference].\
To ensure reliable perfomance of the MRI systems, quality assurance (QA) programs and quality control (QC) tests are essential. They monitor scanner stability and detect deviations in parameters that affect image quality. The most widely adopted program is that of the American College of Radiology (ACR), which uses a standardized accreditation phantom.\
Beyond equipment performance, reproducibility has become a central concern in the MRI community. Dedicated QA/QC procedures quantify experimental stability, identify outliers, minimize variability in outcome measures, and ultimately strengthen the reliability of both research findings and clinical diagnoses [references].\
Despite this recognized need, many existing implementations of ACR QA tests rely on proprietary platforms such as MATLAB. These require paid licenses and limit accessibility, creating barriers for MRI facilities that lack commercial software.\
MacroQA addresses this gap by providing an entirely free and open-source implementation of ACR QA tests within ImageJ/Fiji, using the Jython scripting language. This design removes financial barriers while promoting transparency, reproducibility, and collaborative development. By making the code openly available, MacroQA offers a cost-effective, shareable, and verifiable solution for MRI phantom QA, directly supporting both clinical practice and reproducible research.

# Quality control tests and their acceptance criteria

## Required images
For both large and medium phantoms, a minimum of three acquisitions are required; the **Localizer**, **ACR T1 series** and the **ACR T2 series**.\
* **Localizer:** A single-slice saggital spin-echo, acquired at the center of the phantom.\
* **ACR T1:** An 11-slices axial T1-weighted series.\
* **ACR T2:** An 11-slices axial T2-weighted series with two echo times; the longest one is used as the T2-weighted image. 

## Central frequency

**Objetive:** To ensure the scanner is operating at the correct resonance frequency. Operating off-resonance reduces the signal-to-noise ratio (SNR). Changes in resonance frequency may also indicate drift in the static magnetic field.\
**Frequency:** Weekly\
**Acceptance criteria:** Within 1 ppm per day for superconducting magnets.\
**Image Type:** ACR T1w

## Geometric accuracy

**Objective:** To verify that the image scaling reflects the true dimensions of the object being imaged.\
**Frequency:** Weekly\
**Acceptance criteria:** ± 3 mm (Large Phantom) and ± 2mm (Medium Phantom).\
**Image Type:** ACR T1w

## High-contrast spatial resolution

**Objective:** To Assess the scanner's ability to resolver small objects.\
**Frequency:** Weekly\
**Acceptance criteria:** Visualization of the 1 mm holes (spatial resolution of the image).\
**Image Type:** ACR T1w & T2w

## Slice thickness accuracy

**Objective:** To verify that the prescribed slice thickness corresponds to the acquired slice.\
**Frequency:** Annual\
**Acceptance criteria:** ± 0.75mm.\
**Image Type:** ACR T1w & T2w

## Slice position accuracy

**Objective:** To Assess the accuracy of slice positioning using the localizer image as positional reference.\
**Frequency:** Annual\
**Acceptance criteria:** <=5mm in both slices.\
**Image Type:** ACR T1w & T2w

## Image intensity uniformity

**Objective:** To measure the uniformity of the image intensity over a large water-only region of the phantom near the middle of teh imaged volume which is typically near the center of the head coil.\
**Frequency:** Annual\
**Acceptance criteria:** For 3T, PIU >= 80; for <3T, PIU >= 85.\
**Image Type:** ACR T1w & T2w

## Percent-signal ghosting

**Objective:** To quantify ghosting artifacts in the ACR T1 images.\
**Frequency:** Annual\
**Acceptance criteria:** <=3%\
**Image Type:** ACR T1w & T2w

## Low-contrast object detectability

**Objective:** To determine the extet to which ojects of low contrast are discernible in the images.\
**Frequency:** Weekly\
**Acceptance criteria:** For 3T, ACR T1 & T2 >= 37 spokes, for 1.5T-3T, >=30 spokes (ACR T1) and >=25 spokes (ACR T2)\
**Image Type:** ACR T1w & T2w

## Signal to noise ratio (SNR) 

**Objective:** To measure the ratio of the true signal background noise. While not always explicity included in ACR QA manuals, SNR is key indicator of image quality.\
**Frequency:** Weekly\
**Acceptance criteria:** Not formally reported in the ACR manual.\
**Image Type:** ACR T1w

# Usage example

# Software description

MacroQA is implemented in Jython (www.jython.org), a Python implementation for the Java platform, which runs within Fiji/ImageJ. Fiji/ImageJ was chosen because it is a widely used, free, and cross-platform imaging software.
Each QC test is implemented as an independent macro, simplifying both development and installation. After installation, the macros appear in the Fiji menu under a dedicated “QC” submenu, called MacroQA.

* **Inputs:** DICOM images acquired with the ACR accreditation phantom.

* **Outputs:** Numerical results, displayed in the Fiji log window and optionally saved.

MacroQA is distributed under the [choose license, e.g., MIT or GPL] license, ensuring free use, modification, and redistribution.

# Availability
The MacroQA is publicly available on [Github](https://github.com/icaroafoliveira/Macros_MRI_QA_phantom_ACR). The tool is distributed under the MIT License, allowing for free use, modification, and redistribution. Instructions for installation and usage are provided in the README file. We welcome contributions and feedback from the community to improve our tool and expand its capabilities. Opening an issue on the Github repository is the best way to report bugs or request fearures; pull requests are also welcome for contributions and will be reviewed promptly.

# Acknowledgements
IAFO conceived the idea for MacroQA, but the process of development were throrougly discussed with all co-authors. The co-authors, GBV, VHCG, PHTCO and MSQ contributted nearly equally with coding and development of the MacroQA. IAFO contributted with code, paper writing and supervision of the project the implementation.

# References
