## 3.0.0

* None reverse-compatible changes
  * Change code to work with PsiPyUtils 3.0.0 (does not work with 2.x anymore)

## 2.0.1

* Bugfixes
  * GUI does remember last path used now

## 2.0.0

* First open-source release (older history discarded)
* Changes (not reverse compatible)
  * Upgraded PsiPyUtils to version 2.0.0

## 1.1.0

* New Features
  * Added TBPKG tag to define packages that must be added to all testbenches, even if they are not used in production code
* Bugfixes
  * Clocks are now rising edge aligned (required for correctly generating synchronous clocks)
  * Underscores (\_) led to errors when used in tag-values
  * TbGenerator crashed when no generics were exported
  * .mrg files had to be deleted manually which makes no sense since they are only used temporarily for merging
  * Types with range (e.g. "integer range 0 to 3") were not supported. This is now fixed.
  * the "end entity" statement variant with the entity name was not accepted. This is now fixed

## 1.0.0 

* First Release
