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
from PyQt4.QtGui import QMessageBox, QApplication
import msgBox
parentWin = QApplication.activeWindow()

prefixPath = '\\\\renders\\Storage\\Projects\\external\\Al_Mansour_Season_02\\02_production\\2D'
#prefixPath = 'D:\\shot_test'
title = 'Add Write Nodes'


def showMessage(**kwargs):
    return msgBox.showMessage(parentWin, title=title, **kwargs)

def getMatch(path, val):
    match = re.search(r'[\\/]%s\d{3}[\\/]'%val, path)
    if match:
        return match.group()[1:-1]
    
def getReadNodePath(node):
    nuke.selectConnectedNodes()
    try:
        node = [node for node in nuke.selectedNodes('Read') if not node.hasError() and
                not node.knob('disable').getValue() and
                node.knob('tile_color').getValue() != 4278190080.0][0]
    except IndexError:
        return
    return node.knob('file').getValue()

def getSelectedNodes():
    nodes = nuke.selectedNodes()
    if not nodes:
        showMessage(msg='No selection found', icon=QMessageBox.Information)
    return nodes

def addWrite():
    nodes = getSelectedNodes()
    if not nodes: return
    nukescripts.clear_selection_recursive()
    errors = {}
    for node in nodes:
        node.setSelected(True)
        path = getReadNodePath(node)
        node.setSelected(False)
        if path:
            ep = getMatch(path, 'EP')
            seq = getMatch(path, 'SQ')
            sh = getMatch(path, 'SH')
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
            qutil.mkdir(prefixPath, postPath)
            fullPath = osp.join(prefixPath, postPath)
            if osp.exists(fullPath):
                fullPath = osp.join(fullPath, osp.basename(fullPath) + '.%04d.jpg').replace('\\', '/')
                nukescripts.clear_selection_recursive()
                node.setSelected(True)
                nuke.createNode('Write').knob('file').setValue(fullPath)
                nukescripts.clear_selection_recursive()
            else:
                errors[node.name()] = 'Could not create output directory\n'+ fullPath
        else:
            errors[node.name()] = 'Could not find file path from Read node'
    if errors:
        details = '\n\n'.join(['\nReason: '.join([key, value]) for key, value in errors.items()])
        showMessage(msg='Errors occurred while adding write nodes',
                    icon=QMessageBox.Information,
                    details=details)