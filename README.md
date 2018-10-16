# General Information

## Maintainer
Oliver Bründler [oliver.bruendler@psi.ch]

## License
This library is published under [PSI HDL Library License](License.txt), which is [LGPL](LGPL2_1.txt) plus some additional exceptions to clarify the LGPL terms in the context of firmware development.

## Changelog
See [Changelog](Changelog.md)

## Description
This tool automatically creates a testbench skeleton from a DUT VHDL file. Additional settings (e.g. clock frequencies) can be annotated in the VHDL file directly as comments.

The testbench generated can have two forms:

* Single File TB
  * All code in a single file
  * No separate test-cases
* Multi File TB
  * If multiple testcases are specified, a package file is generated for each test-case
  * This allows better organization of large testbenches


For more details, refer to the [documentation](./doc/TbGenerator.pdf)

## Tagging Policy
Stable releases are tagged in the form *major*.*minor*.*bugfix*. 

* Whenever a change is not fully backward compatible, the *major* version number is incremented
* Whenever new features are added, the *minor* version number is incremented
* If only bugs are fixed (i.e. no functional changes are applied), the *bugfix* version is incremented

# Dependencies
## Library

The required folder structure looks as given below (folder names must be matched exactly). 

Alternatively the repository [psi\_fpga\_all](https://github.com/paulscherrerinstitute/psi_fpga_all) can be used. This repo contains all FPGA related repositories as submodules in the correct folder structure.
* Python
  * [PsiPyUtils](https://github.com/paulscherrerinstitute/PsiPyUtils) (2.0.0 or higher)
  * [**TbGenerator**](https://github.com/paulscherrerinstitute/TbGenerator) 

## External

* PIP
  * PyQt4
  * pyparsing