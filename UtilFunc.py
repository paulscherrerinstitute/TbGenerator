##############################################################################
#  Copyright (c) 2018 by Paul Scherrer Institute, Switzerland
#  All rights reserved.
#  Authors: Oliver Bruendler
##############################################################################

from PsiPyUtils.FileWriter import FileWriter
from datetime import datetime as dt

def VhdlTitle(title : str, f : FileWriter, level : int = 1) -> FileWriter:
    if level is 1:
        f.WriteLn("-" * 60)
        f.WriteLn("-- " + title)
        f.WriteLn("-" * 60)
    elif level is 2:
        f.WriteLn("-- *** " + title + " ***")
    else:
        raise Exception("Illegel VHDL Title level")
    return f

def CopyrightNotice(f : FileWriter) -> FileWriter:
    f.WriteLn("-" * 60)
    f.WriteLn("-- Copyright (c) {} by Paul Scherrer Institute, Switzerland".format(dt.now().year))
    f.WriteLn("-- All rights reserved.")
    f.WriteLn("-" * 60)
    f.WriteLn()
    return f


