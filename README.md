# MacroQA: An ImageJ Macro for ACR MRI Quality Assurance
`MacroQA` is a comprehensive ImageJ/Fiji [reference] macro designed to provide a more reliable and practical implementation of the American College of Radiology (ACR) Quality Assurance (QA) tests [reference]. Its development was driven by a commitment to serving academic and pedagogical purposes, specifically to facilitate and simplify the testing process for students and other users. By leveraging ImageJ and Fiji's embedded functions, MacroQA is able to perform all tests from the MRI ACR phantom manual with impressive accuracy and efficiency, completing the entire process in just a few minutes.

# What MacroQA does?
Many existing implementations for performing ACR QA tests are based on proprietary software, such as MATLAB, which requires a paid license and limits accessibility. This creates a significant barrier for researchers, educators, and students in resource-constrained environments. In contrast, MacroQA is built on a foundation of completely free and open-source software, ImageJ/Fiji, and utilizes an accessible scripting language (Jython). This design choice not only removes financial barriers but also promotes the core principles of academic research, including transparency and reproducibility.

# Instalation
There are two primary methods for installing MacroQA, both will provide a different user experience.

## Method 1: Using ImageJ and Fiji Macro Editor
This method is ideal for quick use or for running the macro as a one-off process.

### Fiji
1. Open the ***StartupMacros*** in the *Plugins > Macros* tab.
2. With the ***StartMacros*** opened, drag `MacroQA` into File Explorer.
3. Access the `MacroQA` folder.
4. Double click the test that you want to perform.

### ImageJ
to do

## Method 2: Installing as a Plugin
Installing `MacroQA` as a plugin makes it a **permanent** part of your ImageJ/Fiji menu, providing easy access from any session.

You can simply paste the `MacroQA` folder into C:\Program Files\Fiji\Fiji.app\plugins\Macros or any other subfolder that you want.


# TODO
- traduçãopara inglês
- escrever o passo a passo
- corrigir bugs


Created by Gabriel Branco, Victor H. Celoni and Ícaro Oliveira
