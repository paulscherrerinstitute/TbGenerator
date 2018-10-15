##############################################################################
#  Copyright (c) 2018 by Paul Scherrer Institute, Switzerland
#  All rights reserved.
#  Authors: Oliver Bruendler
##############################################################################

from PsiPyUtils.FileWriter import FileWriter
from DutInfo import DutInfo, Tags
from TbInfo import TbInfo
from UtilFunc import VhdlTitle, CopyrightNotice
from VhdlParse import VhdlPortDeclaration

def WriteTbPkg(path : str, dutInfo : DutInfo, tbInfo : TbInfo, extension : str = ".vhd", overwrite : bool = False):
    pkgName = tbInfo.tbName + "_pkg"
    with FileWriter(path + "/" + pkgName + extension, overwrite=overwrite) as f:
        CopyrightNotice(f)
        #Library Declarations
        dutInfo.LibraryDeclarations(f)
        tbInfo.UserPkgDelcaration(f)
        VhdlTitle("Package Header", f)
        f.WriteLn("package {} is".format(pkgName)).IncIndent()
        f.WriteLn()
        VhdlTitle("Generics Record", f, 2)
        f.WriteLn("type Generics_t is record").IncIndent()
        generics = DutInfo.FilterForTag(dutInfo.generics, Tags.EXPORT, "true")
        for g in generics:
            f.WriteLn("{} : {};".format(g.name, str(g.type)))
        if len(generics) is 0:
            f.WriteLn("Dummy : boolean; -- required since empty records are not allowed")
        f.DecIndent().WriteLn("end record;")
        f.WriteLn()
        VhdlTitle("Not exported Generics", f)
        for g in set(dutInfo.generics) - set(DutInfo.FilterForTag(dutInfo.generics, Tags.EXPORT, "true")):
            if DutInfo.HasTag(g, Tags.CONSTANT):
                value = DutInfo.GetTag(g, Tags.CONSTANT)
            else:
                value = g.default
            f.WriteLn("constant {} : {} := {};".format(g.name, str(g.type), value))
        f.WriteLn()
        f.DecIndent().WriteLn("end package;")
        f.WriteLn()
        VhdlTitle("Package Body", f)
        f.WriteLn("package body {} is".format(pkgName)).IncIndent()
        f.DecIndent().WriteLn("end;")

def PortDirectionForProcedure(processName : str, port : VhdlPortDeclaration) -> str:
    portDir = port.direction.lower()
    if portDir in ["in", "inout"]:
        procsTag = DutInfo.GetTagAsList(port, Tags.PROC)
        if procsTag[0].lower() != processName.lower():
            return "in"
        if DutInfo.HastTagValue(port, Tags.TYPE, "clk"):
            return "in"
        return "inout"
    else:
        return "in"


def WriteCasePkg(path : str, dutInfo : DutInfo, tbInfo : TbInfo, case : str, extension : str, overwrite : bool = False):
    caseName = tbInfo.tbName + "_case_" + case
    with FileWriter(path + "/" + caseName + extension, overwrite=overwrite) as f:
        CopyrightNotice(f)
        #Library Declarations
        dutInfo.LibraryDeclarations(f)
        tbInfo.TbPkgDeclaration(f)
        tbInfo.UserPkgDelcaration(f)
        VhdlTitle("Package Header", f)
        f.WriteLn("package {} is".format(caseName)).IncIndent()
        f.WriteLn()
        for p in tbInfo.tbProcesses:
            f.WriteLn("procedure {} (".format(p)).IncIndent()
            for s in tbInfo.GetPortsForProcess(p):
                procDir = PortDirectionForProcedure(p, s)
                f.WriteLn("signal {} : {} {};".format(s.name, procDir, s.type.name))
            f.WriteLn("constant Generics_c : Generics_t);")
            f.WriteLn().DecIndent()
        f.DecIndent().WriteLn("end package;")
        f.WriteLn()
        VhdlTitle("Package Body", f)
        f.WriteLn("package body {} is".format(caseName)).IncIndent()
        for p in tbInfo.tbProcesses:
            f.WriteLn("procedure {} (".format(p)).IncIndent()
            for s in tbInfo.GetPortsForProcess(p):
                procDir = PortDirectionForProcedure(p, s)
                f.WriteLn("signal {} : {} {};".format(s.name, procDir, s.type.name))
            f.WriteLn("constant Generics_c : Generics_t) is").DecIndent()
            f.WriteLn("begin").IncIndent()
            f.WriteLn("assert false report \"Case {} Procedure {}: No Content added yet!\" severity warning;".format(case.upper(), p.upper()))
            f.DecIndent().WriteLn("end procedure;")
            f.WriteLn()
        f.DecIndent().WriteLn("end;")