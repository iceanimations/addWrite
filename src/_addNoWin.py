'''
Created on Apr 1, 2015

@author: qurban.ali
'''
import nuke
import nukescripts
import re
import iutil as qutil
import os
import os.path as osp
from PyQt4.QtGui import QMessageBox, QApplication, QFileDialog
import msgBox
reload(qutil)
import appUsageApp
from PyQt4 import uic
import shutil

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
    match = re.search(r'[\\/_]%s_?\d+[\\/]'%val, path, re.IGNORECASE)
    if match:
        return match.group()[1:-1].replace('_', '').upper()

def getStereoMatch(path, val='%V'):
    return True if re.search(val, path, re.IGNORECASE) else False

image_re = re.compile(r'.*\.(jpeg|jpg|tga|exr|dpx)', re.IGNORECASE)
def has_image(dir_path):
    if not os.path.exists(dir_path):
        return False
    for filename in os.listdir(dir_path):
        image_name = os.path.join(dir_path, filename)
        if os.path.isfile(image_name) and image_re.match(filename):
            return True

def get_images(dir_path):
    if not os.path.exists(dir_path):
        return []
    images = []
    for filename in os.listdir(dir_path):
        image_name = os.path.join(dir_path, filename)
        if os.path.isfile(image_name) and image_re.match(filename):
            images.append(filename)
    return images

version_re = re.compile(r'_?v(\d{3,})', re.IGNORECASE)
def versionUpWriteNode(node=None):
    if not node:
        node = nuke.thisNode()
    file_value = node.knob('file').getValue()
    file_dir, file_name = os.path.split(file_value)
    dir_parent, dir_name = os.path.split(file_dir)

    current_version = 1
    version_match = version_re.match(dir_name)
    if version_match:
        qutil.mkdir(dir_parent, dir_name)
        current_version = int(version_match.group(1))
    else:
        dir_name = 'v001'
        qutil.mkdir( file_dir, dir_name )
        dir_parent = file_dir
        file_dir = os.path.join(dir_parent, dir_name)

    while has_image(file_dir):
        current_version += 1
        dir_name = 'v%03d'%current_version
        qutil.mkdir(dir_parent, dir_name)
        file_dir = os.path.join(dir_parent, dir_name)

    search = version_re.search(file_name)
    if search:
        file_name = version_re.sub(dir_name, file_name)
    else:
        splits = file_name.split('.')
        splits = [ splits[0] + '_' + dir_name ] + splits[1:]
        file_name = '.'.join(splits)

    file_value = os.path.join(file_dir, file_name)
    node.knob('file').setValue(file_value.replace('\\', '/'))

def archiveBeforeWrite(node=None):
    ''' This function archive all the images in the destination directory into
    version folders '''

    if not node:
        node = nuke.thisNode()

    file_value = node.knob('file').getValue()
    file_dir, file_name = os.path.split(file_value)
    dir_parent, dir_name = os.path.split(file_dir)

    if version_re.match(file_dir):
        file_dir = dir_parent

    if version_re.search(file_name):
        file_name = version_re.sub('', file_name)

    file_value = os.path.join(file_dir, file_name)
    node.knob('file').setValue(file_value.replace('\\', '/'))

    if has_image(file_dir):
        version = 0

        for dirname in os.listdir(file_dir):
            version_match = version_re.match(dirname)
            if ( os.path.isdir(os.path.join(file_dir, dirname)) and
                    version_match ):
                new_version = int(version_match.group(1))
                if new_version > version:
                    version = new_version

        version_dir_name = 'v%03d'%version
        version_dir = os.path.join(file_dir, version_dir_name)
        if not os.path.isdir(version_dir) or has_image(version_dir):
            version += 1
            version_dir_name = 'v%03d'%version
            version_dir = os.path.join(file_dir, version_dir_name)

        if not os.path.exists(version_dir):
            qutil.mkdir(file_dir, version_dir_name)

        for filename in get_images(file_dir):
            splits = filename.split('.')
            splits = [ splits[0] + '_' + version_dir_name] + splits[1:]
            versioned_filename = '.'.join(splits)
            image = os.path.join(file_dir, filename)
            shutil.move(image, os.path.join(version_dir, versioned_filename))

    return True

def getEpSeqSh(node):
    backdropNode = nuke.getBackdrop()
    try:
        backdropNodes = backdropNode.getNodes()
    except:
        backdropNodes = nuke.activateBackdrop(backdropNode, False)
    nuke.selectConnectedNodes()
    readNodes = [_node for _node in nuke.selectedNodes('Read') if not _node.hasError() and
            not _node.knob('disable').getValue() and
            _node.knob('tile_color').getValue() != 4278190080.0 and
            _node in backdropNodes]
    ep = seq = sh = stereo = None
    if readNodes:
        for readNode in readNodes:
            path = readNode.knob('file').getValue()
            ep = getMatch(path, 'EP')
            seq = getMatch(path, 'SQ')
            sh = getMatch(path, 'SH')
            stereo = getStereoMatch(path)
            if seq and sh:
                break
    return ep, seq, sh, stereo

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
        node.setSelected(True)
        ep, seq, sh, stereo = getEpSeqSh(node)
        node.setSelected(False)
        if not ep:
            errors[node.name()] = 'Could not find episode number'
            ep = ''
        if not seq:
            errors[node.name()] = 'Could not find sequence number'
            continue
        if not sh:
            errors[node.name()] = 'Could not find shot number'
            continue

        cams = ['']
        if stereo:
            cams = ['Right', 'Left']

        file_names = []
        full_paths = []
        abort = False

        for cam in cams:
            folder_name = '_'.join([seq, sh])
            postPath = osp.normpath(osp.join(ep, 'Output', seq, folder_name, cam)) 
            qutil.mkdir(pPath, postPath)
            fullPath = osp.join(pPath, postPath)
            if not osp.exists(fullPath):
                errors[node.name()] = 'Could not create output directory\n'+ fullPath
                abort = True
            else:
                full_paths.append(fullPath)
                file_name = folder_name + ('_' if cam else '') + cam
                file_names.append(file_name)

        if abort:
            continue

        file_value = osp.join(full_paths[0], file_names[0] + '.%04d.jpg').replace('\\', '/')
        if stereo:
            file_value = '\v'+'\v'.join([
                'default',
                file_value,
                'left',
                osp.join(full_paths[1], file_names[1] +'.%04d.jpg').replace('\\', '/')
                ])

        nukescripts.clear_selection_recursive()
        node.setSelected(True)
        writeNode = nuke.createNode('Write')
        writeNode.knob('file').setValue(file_value)
        writeNode.knob('_jpeg_quality').setValue(1)
        writeNode.knob('_jpeg_sub_sampling').setValue(2)
        # archiveBeforeWrite(writeNode)
        writeNode.knob('beforeRender').setValue(
                'import %s; '%__name__.split('.')[0] +
                __name__ + '.archiveBeforeWrite()')
        nukescripts.clear_selection_recursive()

    if errors:
        details = '\n\n'.join(['\nReason: '.join([key, value]) for key, value in errors.items()])
        showMessage(msg='Errors occurred while adding write nodes',
                    icon=QMessageBox.Information,
                    details=details)
    appUsageApp.updateDatabase('AddWrite')
