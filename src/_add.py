'''
Created on Apr 1, 2015

@author: qurban.ali
'''

import nuke
import nukescripts
from Qt.QtWidgets import QMessageBox, QMainWindow, QApplication
from Qt.QtCompat import loadUi
import os.path as osp

from utilities import qutil, msgBox

rootPath = qutil.dirname(__file__, 2)
uiPath = osp.join(rootPath, 'ui')
title = 'Add Write Nodes'


class Add(QMainWindow):
    def __init__(self, parent=QApplication.activeWindow()):
        super(Add, self).__init__(parent)
        loadUi(osp.join(rootPath, 'main.ui'), self)
        self.addButton.clicked.connect(self.add)

    def closeEvent(self, event):
        self.deleteLater()

    def populateBoxes(self):
        pass

    def showMessage(self, **kwargs):
        return msgBox.showMessage(self, title=title, **kwargs)

    def getSelectedNodes(self):
        nodes = nuke.selectedNodes()
        if not nodes:
            self.showMessage(msg='No node found in the selection',
                             icon=QMessageBox.Information)
        return nodes

    def getPath(self):
        path = self.pathBox.text()
        if not path or not osp.exists(path):
            self.showMessage(
                    msg='The system could not find the path specified',
                    icon=QMessageBox.Information)
            path = ''
        return path

    def getEp(self):
        ep = self.epBox.currentText()
        if ep == '--Episode--':
            self.showMessage(msg='No Episode selected',
                             icon=QMessageBox.Information)
            ep = ''
        return ep

    def getSeq(self):
        seq = self.seqBox.currentText()
        if seq == '--Sequence--':
            self.showMessage(msg='No Sequence selected',
                             icon=QMessageBox.Information)
            seq = ''
        return seq

    def getSh(self):
        sh = self.shBox.currentText()
        if sh == '--Shot--':
            self.showMessage(msg='No Shot selected',
                             icon=QMessageBox.Information)
            sh = ''
        return sh

    def add(self):
        nodes = self.getSelectedNodes()
        if not nodes:
            return
        ep = self.getEp()
        if not ep:
            return
        seq = self.getSeq()
        if not seq:
            return
        sh = self.getSh()
        if not sh:
            return
        path = self.getPath()
        if not path:
            return

        nukescripts.clear_selection_recursive()
