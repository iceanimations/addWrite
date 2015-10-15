'''
Created on Apr 1, 2015

@author: qurban.ali
'''
import nuke
import nukescripts
import re
import qutil
import os
import os.path as osp
from PyQt4.QtGui import QMessageBox, QApplication, QFileDialog
import msgBox
reload(qutil)
import appUsageApp
from PyQt4 import uic

parentWin = QApplication.activeWindow()
homeDir = osp.join(osp.expanduser('~'), 'addWriteNode')
if not osp.exists(homeDir):
    os.mkdir(homeDir)
prefFile = osp.join(homeDir, 'pref.txt')
path = None
if osp.exists(prefFile):
    with open(prefFile) as f:
        path = f.read()
prefixPath = path if path else '\\\\renders\\Storage\\Projects\\external\\Al_Mansour_Season_02\\02_production\\2D'
if qutil.getUsername() == 'qurban.ali':
    pass
    #prefixPath = 'D:\\shot_test'
title = 'Add Write Nodes'
lastPath = ''

rootPath = qutil.dirname(__file__, depth=2)
uiPath = osp.join(rootPath, 'ui')

Form, Base = uic.loadUiType(osp.join(osp.join(uiPath, 'prefix.ui')))
class PrefixDialog(Form, Base):
    def __init__(self, parent=parentWin):
        super(PrefixDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.browseButton.clicked.connect(self.setPath)
        self.addButton.clicked.connect(self.accept)
        
        self.pathBox.setText(prefixPath)
        self.pathBox.textChanged.connect(self.handleTextChange)
    
    def handleTextChange(self, txt):
        with open(prefFile, 'w') as f:
            f.write(txt)
            
        
    def setPath(self):
        global lastPath
        filename = QFileDialog.getExistingDirectory(self, 'Select Prefix', lastPath, QFileDialog.ShowDirsOnly)
        if filename:
            self.pathBox.setText(filename)
            lastPath = filename
        
    def getPath(self):
        path = self.pathBox.text()
        if not path or not osp.exists(path):
            showMessage(msg='Could not find the path specified',
                               icon=QMessageBox.Information)
            path = ''
        return path


def showMessage(**kwargs):
    return msgBox.showMessage(parentWin, title=title, **kwargs)

def getMatch(path, val):
    match = re.search(r'[\\/_]%s\d+[\\/]'%val, path, re.IGNORECASE)
    if match:
        return match.group()[1:-1]
    
def getEpSeqSh(node):
    backdropNode = nuke.getBackdrop()
    try:
        backdropNodes = backdropNode.getNodes()
    except:
        backdropNodes = nuke.activateBackdrop(backdropNode, False)
    nuke.selectConnectedNodes()
    readNodes = [node for node in nuke.selectedNodes('Read') if not node.hasError() and
            not node.knob('disable').getValue() and
            node.knob('tile_color').getValue() != 4278190080.0 and
            node in backdropNodes]
    ep = seq = sh = None
    if readNodes:
        for readNode in readNodes:
            path = readNode.knob('file').getValue()
            ep = getMatch(path, 'EP')
            seq = getMatch(path, 'SQ')
            sh = getMatch(path, 'SH')
            if ep and seq and sh:
                break
    return ep, seq, sh

def getSelectedNodes():
    nodes = nuke.selectedNodes()
    if not nodes:
        showMessage(msg='No selection found', icon=QMessageBox.Information)
    return nodes

def addWrite():
    nodes = getSelectedNodes()
    if not nodes: return
    nukescripts.clear_selection_recursive()
    dialog = PrefixDialog()
    if not dialog.exec_():
        return
    pPath = dialog.getPath()
    if not pPath:
        return
    errors = {}
    for node in nodes:
        skip = False
        node.setSelected(True)
        ep, seq, sh = getEpSeqSh(node)
        node.setSelected(False)
        if not ep:
            errors[node.name()] = 'Could not find episode number'
            continue
        if not seq:
            errors[node.name()] = 'Could not find sequence number'
            continue
        if not sh:
            errors[node.name()] = 'Could not find shot number'
            continue
        postPath = osp.join(ep, 'Output', seq, '_'.join([seq, sh]))
        qutil.mkdir(pPath, postPath)
        fullPath = osp.join(pPath, postPath)
        if osp.exists(fullPath):
            fullPath = osp.join(fullPath, osp.basename(fullPath) + '.%04d.jpg').replace('\\', '/')
            nukescripts.clear_selection_recursive()
            node.setSelected(True)
            writeNode = nuke.createNode('Write')
            writeNode.knob('file').setValue(fullPath)
            writeNode.knob('_jpeg_quality').setValue(1)
            writeNode.knob('_jpeg_sub_sampling').setValue(2)
            nukescripts.clear_selection_recursive()
        else:
            errors[node.name()] = 'Could not create output directory\n'+ fullPath
    if errors:
        details = '\n\n'.join(['\nReason: '.join([key, value]) for key, value in errors.items()])
        showMessage(msg='Errors occurred while adding write nodes',
                    icon=QMessageBox.Information,
                    details=details)
    appUsageApp.updateDatabase('AddWrite')