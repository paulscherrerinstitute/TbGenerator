##############################################################################
#  Copyright (c) 2018 by Paul Scherrer Institute, Switzerland
#  All rights reserved.
#  Authors: Oliver Bruendler
##############################################################################

import os
import sys
if __name__ == "__main__":
    myPath = os.path.realpath(os.path.dirname(__file__))
    sys.path.append(myPath + "/..")

import os
from PsiPyUtils import FileWriter
from UtilFunc import VhdlTitle, CopyrightNotice
from MultiFileTb import WriteTbPkg, WriteCasePkg
from DutInfo import DutInfo, Tags, UnknownVhdlType
from TbInfo import TbInfo
import os
from argparse import ArgumentParser
import shutil

class TbGenerator:

    def __init__(self):
        self.dutInfo = None
        self.tbInfo = None

    def ReadHdl(self, filePath : str):
        self.dutInfo = DutInfo(filePath)
        self.tbInfo = TbInfo(self.dutInfo)

    def _DutInstantiation(self, f : FileWriter) -> FileWriter:
        VhdlTitle("DUT Instantiation", f)
        f.WriteLn("i_dut : entity {}.{}".format(self.dutInfo.dutLibrary, self.dutInfo.name)).IncIndent()
        generics = self.dutInfo.generics
        eg = (DutInfo.FilterForTag(generics, Tags.EXPORT, "true") + DutInfo.FilterForTag(generics, Tags.CONSTANT))
        if len(eg) > 0:
            f.WriteLn("generic map (").IncIndent()
            for g in eg:
                f.WriteLn("{} => {},".format(g.name, g.name))
            f.RemoveFromLastLine(1)
            f.DecIndent().WriteLn(")")
        f.WriteLn("port map (").IncIndent()
        for p in self.dutInfo.ports:
            f.WriteLn("{} => {},".format(p.name, p.name))
        f.RemoveFromLastLine(1)
        f.DecIndent().WriteLn(");").DecIndent()
        return f

    def _Clocks(self, f : FileWriter) -> FileWriter:
        VhdlTitle("Clocks !DO NOT EDIT!", f)
        for clk in DutInfo.FilterForTag(self.dutInfo.ports, Tags.TYPE, "clk"):
            if not DutInfo.HasTag(clk, Tags.FREQ):
                raise Exception("Clock {} has not FREQ tag!".format(clk.name))
            f.WriteLn("p_clock_{} : process".format(clk.name)).IncIndent()
            f.WriteLn("constant Frequency_c : real := real({});".format(DutInfo.GetTag(clk, Tags.FREQ))).DecIndent()
            f.WriteLn("begin").IncIndent()
            f.WriteLn("while TbRunning loop").IncIndent()
            f.WriteLn("wait for 0.5*(1 sec)/Frequency_c;")
            f.WriteLn("{name} <= not {name};".format(name=clk.name))
            f.DecIndent().WriteLn("end loop;")
            f.WriteLn("wait;").DecIndent()
            f.WriteLn("end process;")
            f.WriteLn()
        return f

    def _Resets(self, f : FileWriter) -> FileWriter:
        VhdlTitle("Resets", f)
        for rst in DutInfo.FilterForTag(self.dutInfo.ports, Tags.TYPE, "rst"):
            if not DutInfo.HasTag(rst, Tags.CLK):
                raise Exception("Reset {} has not CLK tag!".format(rst.name))
            clkName = DutInfo.GetTag(rst, Tags.CLK)
            f.WriteLn("p_rst_{} : process".format(rst.name))
            f.WriteLn("begin").IncIndent()
            f.WriteLn("wait for 1 us;")
            f.WriteLn("-- Wait for two clk edges to ensure reset is active for at least one edge")
            f.WriteLn("wait until rising_edge({});".format(clkName))
            f.WriteLn("wait until rising_edge({});".format(clkName))
            f.WriteLn("{} <= {};".format(rst.name, self.dutInfo.GetPortValue(rst, False)))
            f.WriteLn("wait;").DecIndent()
            f.WriteLn("end process;")
            f.WriteLn()
        return f

    def _Processes(self, f : FileWriter) -> FileWriter:
        if self.tbInfo.isMultiCaseTb:
            VhdlTitle("Processes !DO NOT EDIT!", f)
        else:
            VhdlTitle("Processes", f)
        #Generate processes
        for p in self.tbInfo.tbProcesses:
            VhdlTitle(p, f, 2)
            f.WriteLn("p_{} : process".format(p))
            f.WriteLn("begin").IncIndent()
            if self.tbInfo.isMultiCaseTb:
                for i, c in enumerate(self.tbInfo.testCases):
                    f.WriteLn("-- {}".format(c))
                    f.WriteLn("wait until NextCase = {};".format(i))
                    f.WriteLn("ProcessDone(TbProcNr_{}_c) <= '0';".format(p))
                    args = ", ".join(port.name for port in self.tbInfo.GetPortsForProcess(p))
                    f.WriteLn("work.{tb}_case_{case}.{proc}({args}, Generics_c);".format(tb=self.tbInfo.tbName, case=c, proc=p, args=args))
                    f.WriteLn("wait for 1 ps;")
                    f.WriteLn("ProcessDone(TbProcNr_{}_c) <= '1';".format(p))
            else:
                rsts = DutInfo.FilterForTag(self.dutInfo.ports, Tags.TYPE, "rst")
                if len(rsts) > 0:
                    f.WriteLn("-- start of process !DO NOT EDIT")
                    rstLogic = " and ".join([r.name + " = " + self.dutInfo.GetPortValue(r, False) for r in rsts])
                    f.WriteLn("wait until {};".format(rstLogic))
                f.WriteLn()
                f.WriteLn("-- User Code")
                f.WriteLn("assert False report \"Insert your code here!\" severity note;")
                f.WriteLn()
                f.WriteLn("-- end of process !DO NOT EDIT!")
                f.WriteLn("ProcessDone(TbProcNr_{}_c) <= '1';".format(p))
            f.WriteLn("wait;")
            f.DecIndent().WriteLn("end process;")
            f.WriteLn()
        return f

    def _TbControl(self, f : FileWriter) -> FileWriter:
        VhdlTitle("Testbench Control !DO NOT EDIT!", f)
        f.WriteLn("p_tb_control : process")
        f.WriteLn("begin").IncIndent()
        rsts = DutInfo.FilterForTag(self.dutInfo.ports, Tags.TYPE, "rst")
        if len(rsts) > 0:
            rstLogic = " and ".join([r.name + " = " + self.dutInfo.GetPortValue(r, False) for r in rsts])
            f.WriteLn("wait until {};".format(rstLogic))
        if self.tbInfo.isMultiCaseTb:
            for i, c in enumerate(self.tbInfo.testCases):
                f.WriteLn("-- {}".format(c))
                f.WriteLn("NextCase <= {};".format(i))
                f.WriteLn("wait until ProcessDone = AllProcessesDone_c;")
        else:
            f.WriteLn("wait until ProcessDone = AllProcessesDone_c;")
        #end of TB
        f.WriteLn("TbRunning <= false;")
        f.WriteLn("wait;")
        f.DecIndent().WriteLn("end process;")
        return f

    def _GenericConstants(self, f : FileWriter) -> FileWriter:
        gConst = DutInfo.FilterForTag(self.dutInfo.generics, Tags.CONSTANT)
        gExp = DutInfo.FilterForTag(self.dutInfo.generics, Tags.EXPORT, "true")
        VhdlTitle("Fixed Generics", f, 2)
        for g in gConst:
            f.WriteLn("constant {} : {} := {};".format(g.name, g.type, DutInfo.GetTag(g, Tags.CONSTANT)))
        f.WriteLn()
        VhdlTitle("Not Assigned Generics (default values)", f, 2)
        for g in self.dutInfo.generics:
            if (g.default is not None) and (g not in gConst) and (g not in gExp):
                f.WriteLn("constant {} : {} := {};".format(g.name, g.type, g.default))
        if self.tbInfo.isMultiCaseTb:
            f.WriteLn()
            VhdlTitle("Exported Generics", f, 2)
            f.WriteLn("constant Generics_c : Generics_t := (").IncIndent()
            for g in gExp:
                f.WriteLn("{} => {},".format(g.name, g.name))
            if len(gExp) is 0:
                f.WriteLn("Dummy => true,");
            f.RemoveFromLastLine(1, keepNewline=True, append= ");")
            f.DecIndent()
        return f

    def _TbControlSignals(self, f : FileWriter) -> FileWriter:
        VhdlTitle("TB Control", f, 2)
        f.WriteLn("signal TbRunning : boolean := True;")
        f.WriteLn("signal NextCase : integer := -1;")
        f.WriteLn("signal ProcessDone : std_logic_vector(0 to {}) := (others => '0');".format(len(self.tbInfo.tbProcesses)-1))
        f.WriteLn("constant AllProcessesDone_c : std_logic_vector(0 to {}) := (others => '1');".format(len(self.tbInfo.tbProcesses)-1))
        for i, p in enumerate(self.tbInfo.tbProcesses):
            f.WriteLn("constant TbProcNr_{}_c : integer := {};".format(p, i))
        return f

    def _DutSignals(self, f : FileWriter) -> FileWriter:
        VhdlTitle("DUT Signals",f , 2)
        sigs = self.dutInfo.ports
        for sig in sigs:
            try:
                if DutInfo.HastTagValue(sig, Tags.TYPE, "rst"):
                    default = " := " + self.dutInfo.GetPortValue(sig, True)
                elif DutInfo.HastTagValue(sig, Tags.TYPE, "clk"):
                    default = " := " + self.dutInfo.GetPortValue(sig, True) #clocks start active so they are rising edge aligned
                else:
                    default = " := " + self.dutInfo.GetPortValue(sig, False)
            except UnknownVhdlType:
                default = ""
            f.WriteLn("signal {} : {}{};".format(sig.name, str(sig.type), default))
        return f



    def _EntityDeclaration(self, f : FileWriter) -> FileWriter:
        VhdlTitle("Entity Declaration", f)
        f.WriteLn("entity {} is".format(self.tbInfo.tbName))
        f.IncIndent()
        eg = DutInfo.FilterForTag(self.dutInfo.generics, Tags.EXPORT, "true")
        if len(eg) > 0:
            f.WriteLn("generic (")
            f.IncIndent()
            for g in eg:
                line = "{} : {}".format(g.name, g.type)
                if g.default is not None:
                    line += " := {};".format(g.default)
                else:
                    line += ";"
                f.WriteLn(line)
            f.RemoveFromLastLine(1)
            f.DecIndent().WriteLn(");")
        f.DecIndent()
        f.WriteLn("end entity;").WriteLn()
        return f

    def _Header(self, f : FileWriter) -> FileWriter:
        CopyrightNotice(f)
        VhdlTitle("Testbench generated by TbGen.py", f)
        f.WriteLn("-- see Library/Python/TbGenerator")
        return f

    def Generate(self, tbPath : str, extension : str, overwrite : bool = False):
        if self.dutInfo is None:
            raise Exception("No VHDL File parsed yet, call ReadHdl() first!")

        if not os.path.exists(tbPath):
            os.mkdir(tbPath)

        with FileWriter(tbPath + "/" + self.tbInfo.tbName + extension, overwrite=overwrite) as f:
            #Library Declarations
            self._Header(f).WriteLn()
            self.dutInfo.LibraryDeclarations(f)
            self.tbInfo.UserPkgDelcaration(f)
            if self.tbInfo.isMultiCaseTb:
                self.tbInfo.TbPkgDeclaration(f)
                self.tbInfo.TbCaseDeclaration(f)

            #Entity Declaration
            self._EntityDeclaration(f)

            #Architecture Declaration
            VhdlTitle("Architecture", f)
            f.WriteLn("architecture sim of {} is".format(self.tbInfo.tbName)).IncIndent()
            self._GenericConstants(f).WriteLn()
            self._TbControlSignals(f).WriteLn()
            self._DutSignals(f).WriteLn()
            f.DecIndent()
            f.WriteLn("begin").IncIndent()
            self._DutInstantiation(f).WriteLn()
            self._TbControl(f).WriteLn()
            self._Clocks(f).WriteLn()
            self._Resets(f).WriteLn()
            self._Processes(f).WriteLn()
            f.DecIndent().WriteLn("end;")

        #Generate multi-case testbench if required
        if self.tbInfo.isMultiCaseTb:
            WriteTbPkg(tbPath, self.dutInfo, self.tbInfo, extension, overwrite)
            #write case packages
            for case in self.tbInfo.testCases:
                WriteCasePkg(tbPath, self.dutInfo, self.tbInfo, case, extension, overwrite)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-src", dest="src", help="VHDL source file", required=True)
    parser.add_argument("-dst", dest="dst", help="TB destination directory", required=True)
    parser.add_argument("-clear", dest="clear", help="Clear destination directory before generating TB", required=False, default=False, action = "store_true")
    parser.add_argument("-mrg", dest="mrg", help="Create .mrg files intead of .vhd", required=False, default=False, action = "store_true")
    parser.add_argument("-force", dest="force", help="Force -clear without user confirmation", required=False, default = False, action="store_true")
    args = parser.parse_args()

    #Check arguments
    if not os.path.isfile(args.src):
        print("ERROR: -src path {} is not a file", args.src)
        exit(-1)

    #Clear directory if required
    if args.clear:
        if os.path.exists(args.dst):
            if not args.force:
                i = input("Path '{}' exists, do you really want to clear it (Y/N)".format(args.dst))
                if i not in ["Y", "y"]:
                    print("Aborted by user")
                    exit(0)
            try:
                print("Deleting destination directory content")
                for file in os.listdir(args.dst):
                    fp = args.dst + "/" + file
                    if os.path.isfile(fp):
                        os.remove(fp)
            except Exception as e:
                print(e)
                print("ERROR: Failed to clear desitination directory {}, is it open?".format(args.dst))
                exit(-1)

    #Create destination directory if it does not exist
    if not os.path.exists(args.dst):
        print("Creating destination directory")
        os.mkdir(args.dst)

    #Generate TB
    try:
        print("Read HDL")
        tbGen = TbGenerator()
        tbGen.ReadHdl(args.src)
        print("Generate TB")
        extension = ".vhd"
        if args.mrg:
            extension = ".mrg"
        tbGen.Generate(args.dst, extension, overwrite=args.mrg)
        print("Done")
    except Exception as e:
        print("ERROR: " + str(e))
        exit(-1)
