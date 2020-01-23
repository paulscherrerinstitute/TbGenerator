##############################################################################
#  Copyright (c) 2018 by Paul Scherrer Institute, Switzerland
#  All rights reserved.
#  Authors: Oliver Bruendler
##############################################################################

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys
import os

if __name__ == "__main__":
    myPath = os.path.realpath(__file__)
    sys.path.append(myPath + "/../..")
from TbGen import TbGenerator

class TbGenGui(QDialog):


    def __init__(self, parent = None):
        QDialog.__init__(self, parent=parent)
        self.setWindowTitle("Testbench Generator")
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Source File", parent=self))
        self.srcLine = QLineEdit(parent=self)
        layout.addWidget(self.srcLine)
        self.srcBtn = QPushButton("Select Source", parent=self)
        self.srcBtn.clicked.connect(self.LoadSrc)
        layout.addWidget(self.srcBtn)

        layout.addWidget(QLabel("Destination Directory", parent=self))
        self.dstLine = QLineEdit(parent=self)
        layout.addWidget(self.dstLine)
        self.dstBtn = QPushButton("Select Destination", parent=self)
        self.dstBtn.clicked.connect(self.LoadDst)
        layout.addWidget(self.dstBtn)

        self.genBtn = QPushButton("Generate TB", parent=self)
        self.genBtn.clicked.connect(self.Generate)
        layout.addWidget(self.genBtn)

        hLayout = QHBoxLayout()
        self.clrCb = QCheckBox("Clear Destination Dir")
        hLayout.addWidget(self.clrCb)
        self.mrgCb = QCheckBox("Create Merge Files")
        hLayout.addWidget(self.mrgCb)
        layout.addLayout(hLayout)

        self.setLayout(layout)
        self.show()
        self.lastDirectory = "."


    def LoadSrc(self):
        file = QFileDialog.getOpenFileName(parent=self, caption="Select Source File", directory=self.lastDirectory, filter="*.vhd")[0]
        if file != "":
            self.srcLine.setText(file)
            self.lastDirectory = self.lastDirectory = os.path.dirname(file) + "/.." #Go one directory up because TB and SRT are usually stored in different folders

    def LoadDst(self):
        dir = QFileDialog.getExistingDirectory(parent=self, caption="Select Destination Directory", directory=self.lastDirectory)
        if dir != "":
            self.dstLine.setText(dir)
            self.lastDirectory = dir + "/.." #Go one directory up because TB and SRT are usually stored in different folders

    def Generate(self):
        try:
            src = self.srcLine.text()
            dst = self.dstLine.text()
            #Check files
            if not os.path.isfile(src):
                raise FileNotFoundError("File {} does not exist".format(src))
            if not os.path.isdir(dst):
                raise FileNotFoundError("Directory {} does not exist".format(src))

            #Clear if required
            if self.clrCb.isChecked():
                for file in os.listdir(dst):
                    fp = dst + "/" + file
                    if os.path.isfile(fp):
                        os.remove(fp)

            #Generate
            tbGen = TbGenerator()
            tbGen.ReadHdl(src)
            overwrite = False
            if self.mrgCb.isChecked():
                ext = ".mrg"
                overwrite = True
            else:
                ext = ".vhd"
            tbGen.Generate(dst, ext, overwrite=overwrite)
        except Exception as e:
            QErrorMessage(parent=self).showMessage(str(e))



if __name__ == '__main__':
    app = QApplication(sys.argv)
    dlg = TbGenGui()
    exit(app.exec_())