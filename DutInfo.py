##############################################################################
#  Copyright (c) 2018 by Paul Scherrer Institute, Switzerland
#  All rights reserved.
#  Authors: Oliver Bruendler
##############################################################################

from VhdlParse import VhdlFile, VhdlPortDeclaration
import pyparsing as pp
from typing import Iterable, List
from PsiPyUtils import FileWriter
from UtilFunc import VhdlTitle

class UnknownVhdlType(Exception): pass

#Tags in the form $$ BLA=5; BLUBB=1,2,3 $$
class Tags:
    #Generic Tags
    EXPORT = "export"
    CONSTANT = "constant"

    #Port Tags
    LOWACTIVE = "lowactive"
    TYPE = "type" #CLK, RST, SIG
    CLK = "clk"
    FREQ = "freq"
    PROC = "proc"

    #File scope tags
    PROCESSES = "processes"
    TESTCASES = "testcases"
    DUTLIB = "dutlib"
    TBPKG = "tbpkg"

class DutInfo:

    def __init__(self, filePath : str):
        self.parseInfo = VhdlFile(filePath)
        self.name = self.parseInfo.entity.name

        # sort use-statements according to library
        self.libraries = {}
        for s in self.parseInfo.usestatements:
            if s.library not in self.libraries:
                self.libraries[s.library] = []
            self.libraries[s.library].append(s)

        #parse file scope tags
        self.fileScopeTags = {}
        for c in self.parseInfo.commentLines:
            tags = self._ParseTags(c.comment)
            self.fileScopeTags.update(tags)

    @property
    def generics(self):
        return self.parseInfo.entity.generics

    @property
    def ports(self):
        return self.parseInfo.entity.ports

    @property
    def dutLibrary(self):
        if Tags.DUTLIB in self.fileScopeTags:
            return self.fileScopeTags[Tags.DUTLIB]
        else:
            return "work"

    def GetPortValue(self, port : VhdlPortDeclaration, active : bool):
        #Find initial value
        if DutInfo.HastTagValue(port, Tags.LOWACTIVE, "true"):
            initVal = "'0'" if active else "'1'"
        else:
            initVal = "'1'" if active else "'0'"
        if port.type.name == "std_logic":
            return initVal
        elif port.type.name == "std_logic_vector":
            return "(others => {})".format(initVal)
        else:
            raise UnknownVhdlType("Unknown VHDL Type {}".format(port.type.name))


    def LibraryDeclarations(self, f : FileWriter) -> FileWriter:
        VhdlTitle("Libraries", f)
        for l in sorted(self.libraries):
            f.WriteLn("library {};".format(l.replace("work", self.dutLibrary)))
            f.IncIndent()
            for u in self.libraries[l]:
                f.WriteLn("use {}.{}.{};".format(u.library.replace("work", self.dutLibrary), u.element, u.object))
            f.DecIndent().WriteLn()
        return f


    @classmethod
    def _ParseTags(cls, string : str) -> dict:
        SINGLE_VALUE = pp.CharsNotIn(";$")
        LIST_VALUE = pp.OneOrMore(pp.Word(pp.alphanums + "_.") + pp.Literal(",")) + pp.Word(pp.alphanums + "_.")
        ANY_VALUE = pp.Group(LIST_VALUE("listVal") | SINGLE_VALUE("singleVal"))
        TAGS = "$$" + pp.OneOrMore(
            pp.Group(pp.Word(pp.alphas)("tag") + "=" + ANY_VALUE("value") + pp.Optional(";")))("tags") + "$$"

        tags = {}
        for t, s, e in TAGS.scanString(string):
            for tag in t.get("tags"):
                val = tag.get("value")
                if "listVal" in val.keys():
                    val = "".join(val).split(",")
                elif "singleVal" in val.keys():
                    val = val.get("singleVal").strip()
                else:
                    raise Exception("Illegal Tag Format")
                tags[tag.get("tag").lower()] = val
        return tags

    @classmethod
    def HastTagValue(cls, object, tag : str, value : str, casesensitive : bool = False) -> bool:
        tag = tag.lower()
        tags = cls._ParseTags(object.comment)
        if tag not in tags:
            return False
        if casesensitive:
            return tags[tag] == value
        else:
            return tags[tag].lower() == value.lower()

    @classmethod
    def HasTag(cls, object, tag : str):
        tag = tag.lower()
        tags = cls._ParseTags(object.comment)
        if tag not in tags:
            return False
        return True

    @classmethod
    def GetTag(cls, object, tag : str) -> str:
        if not cls.HasTag(object, tag):
            raise Exception("object {} has not tag {}".format(object.name, tag))
        tags = cls._ParseTags(object.comment)
        return tags[tag]

    @classmethod
    def GetTagAsList(cls, object, tag : str) -> List[str]:
        tagVal = cls.GetTag(object, tag)
        if type(tagVal) is str:
            return [tagVal]
        return tagVal

    @classmethod
    def FilterForTag(cls, list : Iterable, tag : str, value : str = None, casesensitive : bool = False) -> List:
        l = []
        tag = tag.lower()
        for e in list:
            tags = cls._ParseTags(e.comment)
            if tag in tags:
                if value is None:
                    l.append(e)
                else:
                    tagValue = tags[tag]
                    tagValueList = [tagValue] if type(tagValue) is str else tagValue
                    tagValueListLower = [x.lower() for x in tagValueList]
                    if casesensitive:
                        if value in tagValueList:
                            l.append(e)
                    else:
                        if value.lower() in tagValueListLower:
                            l.append(e)
        return l