##############################################################################
#  Copyright (c) 2018 by Paul Scherrer Institute, Switzerland
#  All rights reserved.
#  Authors: Oliver Bruendler
##############################################################################

import pyparsing as pp
from typing import Tuple, List

kw = ["to", "downto", "entity", "port", "generic", "end", "is"]
PP_KEYWORDS = pp.MatchFirst(kw)
PP_SPACE = pp.Regex("\s")
PP_ANYCHAR = PP_SPACE | (pp.Regex("[^\s]").setResultsName("ac",listAllMatches=True))

PP_BRACES = pp.Literal("(") | pp.Literal(")")
PP_ENDOFLINE = pp.Literal(";")("eol")
PP_COMMENTSTART = pp.Literal("--")
PP_UNQUOTED_EXPR =  pp.Combine(pp.OneOrMore(~PP_KEYWORDS + ~PP_ENDOFLINE + ~PP_BRACES + ~PP_COMMENTSTART + PP_ANYCHAR)).setResultsName("ue", listAllMatches=True)
PP_BRACED_EXPR = pp.Forward().setResultsName("be", listAllMatches=True)
PP_BRACE_PAIR = pp.Literal("(") + pp.OneOrMore(PP_BRACED_EXPR|PP_UNQUOTED_EXPR|PP_KEYWORDS) + pp.Literal(")")
PP_BRACED_EXPR << PP_BRACE_PAIR
PP_EXPRESSION = pp.Group(pp.Combine(pp.OneOrMore(PP_UNQUOTED_EXPR|PP_BRACED_EXPR)))

kw = ["to", "downto", "entity", "port", "generic", "end", "is"]
PP_KEYWORDS = pp.MatchFirst(kw)
PP_IDENTIFIER = pp.Word(pp.alphanums+"_")
PP_INTEGER = pp.Word(pp.nums)
PP_COMMENT = pp.Group(pp.Literal("--") + pp.restOfLine("text"))
PP_VALUE = pp.Regex(r"[a-zA-Z0-9\"'_#]*")
PP_RANGEDIR = (pp.CaselessKeyword("to")|pp.CaselessKeyword("downto"))
PP_DIRECTION = (pp.CaselessKeyword("in")|pp.CaselessKeyword("out")|pp.CaselessKeyword("inout")|pp.CaselessKeyword("buffer"))


def PrToStr(pr : pp.ParseResults):
    strings = []
    for r in pr:
        if type(r) is str:
            strings.append(r.strip())
        else:
            strings.append(PrToStr(r))
    return " ".join(strings)

class VhdlConstruct:

    PP_DEFINITION = None

    def __init__(self, code):
        if type(code) is not str:
            code = PrToStr(code)
        code = code.strip()
        self.code = code
        try:
            self._Parse(self.PP_DEFINITION.parseString(code))
        except:
            raise

    def _Parse(self, parts : pp.ParseResults):
        raise NotImplementedError()

    def __str__(self):
        return self.code.replace("( ", "(").replace(" )", ")").strip()

    @classmethod
    def PP(cls):
        return pp.Group(cls.PP_DEFINITION)

class VhdlCommentLine(VhdlConstruct):

    PP_DEFINITION = pp.lineStart + PP_COMMENT

    def _Parse(self, parts : pp.ParseResults):
        self.comment = parts[0].get("text")

class VhdlUseStatement(VhdlConstruct):
    PP_DEFINITION = pp.Literal("use") + PP_IDENTIFIER("library") + pp.Literal(".") + PP_IDENTIFIER("element") + pp.Literal(".") + PP_IDENTIFIER("object")

    def _Parse(self, parts : pp.ParseResults):
        self.library = parts.get("library")
        self.element = parts.get("element")
        self.object = parts.get("object")

class VhdlRange(VhdlConstruct):
    PP_DEFINITION =  pp.Literal("(") + PP_EXPRESSION("left") + PP_RANGEDIR("dir") + PP_EXPRESSION("right") + pp.Literal(")")

    def _Parse(self, parts : pp.ParseResults):
        self.left = parts.get("left")
        self.right = parts.get("right")
        self.direction = str(parts.get("dir")).lower()
        if self.direction == "to":
            self.low = self.left
            self.high = self.right
        elif self.direction == "downto":
            self.low = self.right
            self.high = self.left
        else:
            raise Exception("Illegal range: {}".format(self.code))

class VhdlRangeFromTo(VhdlConstruct):
    PP_DEFINITION = pp.Literal("range") + PP_EXPRESSION("left") + PP_RANGEDIR("dir") + PP_EXPRESSION("right")

    def _Parse(self, parts : pp.ParseResults):
        self.left = parts.get("left")
        self.right = parts.get("right")
        self.direction = str(parts.get("dir")).lower()

class VhdlType(VhdlConstruct):
    PP_DEFINITION = PP_IDENTIFIER("vhdlType") + pp.Optional(VhdlRange.PP()("range")) + pp.Optional(VhdlRangeFromTo.PP())

    def _Parse(self, parts : pp.ParseResults):
        self.name = parts.get("vhdlType")
        range = parts.get("range")
        if range is not None:
            self.range = VhdlRange(range)
        else:
            self.range = None

    def __str__(self):
        if self.range is not None:
            return self.name + str(self.range)
        else:
            return self.name

class VhdlGenericDeclaration(VhdlConstruct):
    PP_DEFINITION = PP_IDENTIFIER("name") + ":" + VhdlType.PP()("type") + pp.Optional(":=" + PP_EXPRESSION("default")) + pp.Optional(";") + pp.Optional(PP_COMMENT("comment"))

    def _Parse(self, parts : pp.ParseResults):
        self.name = parts.get("name")
        self.type = VhdlType(parts.get("type"))
        self.default = None
        if parts.get("default") is not None:
            self.default = parts.get("default")[0]
        self.comment = None
        if parts.get("comment") is not None:
            self.comment = parts.get("comment").get("text")

class VhdlPortDeclaration(VhdlConstruct):
    PP_DEFINITION = PP_IDENTIFIER("name") + ":" + PP_DIRECTION("dir") + VhdlType.PP()("type") +  pp.Optional(":=" + PP_EXPRESSION("default")) + pp.Optional(";") + pp.Optional(PP_COMMENT("comment"))

    def _Parse(self, parts : pp.ParseResults):
        self.name = parts.get("name")
        self.type = VhdlType(parts.get("type"))
        self.direction = parts.get("dir")
        self.default = None
        if parts.get("default") is not None:
            self.default = parts.get("default")[0]
        self.comment = None
        if parts.get("comment") is not None:
            self.comment = parts.get("comment").get("text")

class VhdlEntityDeclaration(VhdlConstruct):
    PP_DEFINITION = pp.CaselessKeyword("entity") + PP_IDENTIFIER("name") + pp.CaselessKeyword("is") + \
                    pp.Optional(pp.CaselessKeyword("generic") + "(" + pp.OneOrMore(VhdlGenericDeclaration.PP())("generics") + ")" + ";") + \
                    pp.Optional(pp.CaselessKeyword("port") + "(" + pp.OneOrMore(VhdlPortDeclaration.PP()("port")|PP_COMMENT("comment"))("ports") + ")" + ";" + pp.Optional(PP_COMMENT)) + \
                    pp.CaselessKeyword("end") + pp.Optional(pp.CaselessKeyword("entity")) + pp.Optional(PP_IDENTIFIER) + ";"

    def _Parse(self, parts : pp.ParseResults):
        self.name = parts.get("name")
        if "generics" in parts:
            self.generics = [VhdlGenericDeclaration(gd) for gd in parts.get("generics")]
        else:
            self.generics = []
        if "ports" in parts:
            self.ports = [VhdlPortDeclaration(pd) for pd in parts.get("ports") if pd.getName() == "port"]
        else:
            self.ports = []


class VhdlFile:

    def __init__(self, fileName : str):
        # Read File
        with open(fileName, "r") as f:
            code = f.read()
        code = code.replace("\t", " ")

        # Parse Entity Declaration
        for t, s, e in VhdlEntityDeclaration.PP().scanString(code):
            self.entity = VhdlEntityDeclaration(code[s:e])
            break
        else:
            raise Exception("Syntax error in VHDL Code!")

        # Parse Library Definitions
        self.usestatements = []
        for t, s, e in VhdlUseStatement.PP().scanString(code):
            self.usestatements.append(VhdlUseStatement(code[s:e]))

        # Parse comment Lines
        self.commentLines = []
        for t,s,e in VhdlCommentLine.PP().scanString(code):
            self.commentLines.append(VhdlCommentLine(code[s:e]))






