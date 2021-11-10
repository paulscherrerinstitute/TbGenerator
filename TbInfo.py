##############################################################################
#  Copyright (c) 2018 by Paul Scherrer Institute, Switzerland
#  All rights reserved.
#  Authors: Oliver Bruendler
##############################################################################

from DutInfo import DutInfo, Tags
from typing import List
from VhdlParse import VhdlPortDeclaration
from PsiPyUtils import FileWriter

class TbInfo:

    def __init__(self, info : DutInfo):
        self.isMultiCaseTb = Tags.TESTCASES in info.fileScopeTags

        if self.isMultiCaseTb:
            self.testCases = info.fileScopeTags[Tags.TESTCASES]
            if type(self.testCases) is str:
                self.testCases = [self.testCases]
        else:
            self.testCases = None

        self.tbName = info.name + "_tb"

        self.tbProcesses = ["Stimuli"]
        if Tags.PROCESSES in info.fileScopeTags:
            self.tbProcesses = info.fileScopeTags[Tags.PROCESSES]
            if type(self.tbProcesses) is str:
                self.tbProcesses = [self.tbProcesses]

        tbPackages = []
        if Tags.TBPKG in info.fileScopeTags:
            tbPackages = info.fileScopeTags[Tags.TBPKG]
            if type(tbPackages) is str:
                tbPackages = [tbPackages]
        self.tbUserPackages = {}
        for pkg in tbPackages:
            lib, pkgName = tuple(pkg.split("."))
            if lib not in self.tbUserPackages:
                self.tbUserPackages[lib] = [pkgName]
            else:
                self.tbUserPackages[lib].append(pkgName)

        self.dutInfo = info

    def GetPortsForProcess(self, process : str) -> List[VhdlPortDeclaration]:
        return DutInfo.FilterForTag(self.dutInfo.ports, Tags.PROC, process)

    def UserPkgDelcaration(self, f : FileWriter) -> FileWriter:
        for lib, pkgs in self.tbUserPackages.items():
            f.WriteLn("library {};".format(lib)).IncIndent()
            for pkg in pkgs:
                f.WriteLn("use {}.{}.all;".format(lib, pkg))
            f.DecIndent().WriteLn()

    def TbPkgDeclaration(self, f : FileWriter) -> FileWriter:
        f.WriteLn("library {};".format(self.dutInfo.tbLibrary)).IncIndent()
        f.WriteLn("use {}.{}_pkg.all;".format(self.dutInfo.tbLibrary, self.tbName))
        f.DecIndent().WriteLn()

    def TbCaseDeclaration(self, f : FileWriter) -> FileWriter:
        f.WriteLn("library {};".format(self.dutInfo.tbLibrary)).IncIndent()
        for c in self.testCases:
            f.WriteLn("use {}.{}_case_{}.all;".format(self.dutInfo.tbLibrary, self.tbName, c))
        f.DecIndent().WriteLn()
        return f
