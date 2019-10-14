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
import shutil

from Qt.QtWidgets import QMessageBox, QApplication, QFileDialog, QDialog
from Qt.QtCompat import loadUi
import Qt

import utilities.msgBox as msgBox
import utilities.appUsageApp as appUsageApp

reload(qutil)

parentWin = QApplication.activeWindow()
homeDir = osp.join(osp.expanduser('~'), 'addWriteNode')
if not osp.exists(homeDir):
    os.mkdir(homeDir)
prefFile = osp.join(homeDir, 'pref.txt')
path = None
if osp.exists(prefFile):
    with open(prefFile) as f:
        path = f.read()
prefixPath = path if path else (
        '\\\\renders\\Storage\\Projects\\external'
        '\\Al_Mansour_Season_02\\02_production\\2D')
if qutil.getUsername() == 'qurban.ali':
    pass
    # prefixPath = 'D:\\shot_test'
title = 'Add Write Nodes'
lastPath = ''

rootPath = qutil.dirname(__file__, depth=2)
uiPath = osp.join(rootPath, 'ui')

archiveScript = '''
try:
    import addWrite
    addWrite.archive(check=True)
except ImportError:
    print ('Could not import addWrite module ... no archiving shall be done')
except Exception as e:
    print ('Some problem occured during archiving ... %s' % str(e))
'''


class PrefixDialog(QDialog):
    def __init__(self, parent=parentWin):
        if parent is None and Qt.IsPyQt4:
            parent = parentWin
        super(PrefixDialog, self).__init__(parent)
        loadUi(osp.join(osp.join(uiPath, 'prefix.ui')), self)

        self.browseButton.clicked.connect(self.setPath)
        self.addButton.clicked.connect(self.accept)

        self.pathBox.setText(prefixPath)
        self.pathBox.textChanged.connect(self.handleTextChange)

    def handleTextChange(self, txt):
        with open(prefFile, 'w') as f:
            f.write(txt)

    def setPath(self):
        global lastPath
        filename = QFileDialog.getExistingDirectory(self, 'Select Prefix',
                                                    lastPath,
                                                    QFileDialog.ShowDirsOnly)
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
    match = re.search(r'[\\/_]%s_?\d+[a-z]?[\\/]' % val, path, re.IGNORECASE)
    if match:
        return match.group()[1:-1].replace('_', '').upper()


def getStereoMatch(path, val='%V'):
    return True if re.search(val, path, re.IGNORECASE) else False


image_re = re.compile(r'.*\.(jpeg|jpg|tga|exr|dpx|mov|png|tiff|yuv)',
                      re.IGNORECASE)


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
        qutil.mkdir(file_dir, dir_name)
        dir_parent = file_dir
        file_dir = os.path.join(dir_parent, dir_name)

    while has_image(file_dir):
        current_version += 1
        dir_name = 'v%03d' % current_version
        qutil.mkdir(dir_parent, dir_name)
        file_dir = os.path.join(dir_parent, dir_name)

    search = version_re.search(file_name)
    if search:
        file_name = version_re.sub(dir_name, file_name)
    else:
        splits = file_name.split('.')
        splits = [splits[0] + '_' + dir_name] + splits[1:]
        file_name = '.'.join(splits)

    file_value = os.path.join(file_dir, file_name)
    node.knob('file').setValue(file_value.replace('\\', '/'))


def addArchiveCheckKnob(node):
    knobName = 'archive_check'
    if knobName not in nuke.Node.knobs(node):
        node.addKnob(nuke.Boolean_Knob(knobName, 'Archive Before Render'))
        node.knob(knobName).setValue(False)


def addArchiveScriptKnob(node):
    knobName = 'archive'
    if knobName not in nuke.Node.knobs(node):
        node.addKnob(nuke.PyScript_Knob(
            knobName, 'Archive Output',
            archiveScript.replace('True', 'False')))


def addArchiveKnobs(node):
    addArchiveCheckKnob(node)
    addArchiveScriptKnob(node)


def archiveBeforeWrite(node=None, check=True):
    ''' This function archive all the images in the destination directory into
    version folders '''

    if not node:
        node = nuke.thisNode()

    if check:
        knob = node.knob('archive_check')
        if knob is not None and not knob.value():
            return False

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
            if (os.path.isdir(os.path.join(file_dir, dirname))
                    and version_match):
                new_version = int(version_match.group(1))
                if new_version > version:
                    version = new_version

        version_dir_name = 'v%03d' % version
        version_dir = os.path.join(file_dir, version_dir_name)
        if not os.path.isdir(version_dir) or has_image(version_dir):
            version += 1
            version_dir_name = 'v%03d' % version
            version_dir = os.path.join(file_dir, version_dir_name)

        if not os.path.exists(version_dir):
            qutil.mkdir(file_dir, version_dir_name)

        for filename in get_images(file_dir):
            splits = filename.split('.')
            splits = [splits[0] + '_' + version_dir_name] + splits[1:]
            versioned_filename = '.'.join(splits)
            image = os.path.join(file_dir, filename)
            shutil.move(image, os.path.join(version_dir, versioned_filename))

        return True
    return False


def getReleventReadNodes(node):
    backdropNode = nuke.getBackdrop(None)

    # prefer restricting to backdrop or else get everything
    if backdropNode:
        read_nodes = nuke.activateBackdrop(backdropNode, False)
        read_nodes = [n for n in read_nodes if n.Class() == 'Read']
    else:
        read_nodes = nuke.allNodes('Read')

    read_nodes = [
        _node for _node in read_nodes
        if not _node.hasError() and not _node.knob('disable').getValue()
        and _node.knob('tile_color').getValue() != 4278190080.0]

    return read_nodes


def getEpSeqSh(node):
    '''Find paths in read nodes associated with a given node and try to findout
    the episode, sequence, sh and stereo information'''
    readNodes = getReleventReadNodes(node)
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


char_beauty_re = re.compile('char.*beauty', re.I)
env_beauty_re = re.compile('env.*beauty', re.I)


def getFrameRange(node=None):
    '''Search for a suitable frame range from relevant read nodes'''
    read_nodes = getReleventReadNodes(node)
    rnode = None
    for exp in (char_beauty_re, env_beauty_re):
        for rnode in read_nodes:
            if exp.search(rnode.knob('file').getValue()):
                return rnode.knob('first').value(), rnode.knob('last').value()
    return None, None  # no suitable read node found return no range


def getSelectedNodes():
    nodes = nuke.selectedNodes()
    if not nodes:
        showMessage(msg='No selection found', icon=QMessageBox.Information)
    return nodes


def addWrite():
    '''Add a write node downstream of the selected node'''
    nodes = getSelectedNodes()
    if not nodes:
        return
    nukescripts.clear_selection_recursive()

    # get a root path from the user
    dialog = PrefixDialog()
    if not dialog.exec_():
        return
    pPath = dialog.getPath()
    if not pPath:
        return

    # add write node downstream of each selected node
    errors = {}
    for node in nodes:
        node.setSelected(True)
        ep, seq, sh, stereo = getEpSeqSh(node)
        first, last = getFrameRange(node)
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
            cams = ['Right', 'Left']  # Convention

        file_names = []
        full_paths = []
        abort = False

        # handle case for single and stereo cameras
        for cam in cams:
            folder_name = '_'.join([seq, sh])  # convention e.g.: SQ001_SH001
            # Convention ... e.g: EP001/Output/SQ001/SQ001_SH001/[Right|Left]/
            postPath = osp.normpath(
                osp.join(ep, 'Output', seq, folder_name, cam))
            qutil.mkdir(pPath, postPath)
            fullPath = osp.join(pPath, postPath)
            if not osp.exists(fullPath):
                errors[node.name(
                )] = 'Could not create output directory\n' + fullPath
                abort = True
            else:   # Folder successfully created
                full_paths.append(fullPath)
                # Convention ... e.g.: SQ001_SH001[_Right|_Left]
                file_name = folder_name + ('_' if cam else '') + cam
                file_names.append(file_name)

        # Quit if folder cannot be created
        if abort:
            continue

        # This will handle single camera or first stereo cam
        file_value = osp.join(full_paths[0],
                              file_names[0] + '.%04d.jpg').replace('\\', '/')
        if stereo:  # handle second stereocam if needed
            file_value = '\v' + '\v'.join([
                'default', file_value, 'left',
                osp.join(full_paths[1], file_names[1] + '.%04d.jpg').replace(
                    '\\', '/')
            ])

        nukescripts.clear_selection_recursive()
        node.setSelected(True)
        writeNode = nuke.createNode('Write')
        writeNode.knob('file').setValue(file_value)
        writeNode.knob('_jpeg_quality').setValue(1)
        writeNode.knob('_jpeg_sub_sampling').setValue(2)
        writeNode.setName('%s_%s_%s%s' % (
            ep, seq, sh, '_stereo' if stereo else ''))
        if first and last:
            writeNode.knob('first').setValue(first)
            writeNode.knob('last').setValue(last)
            writeNode.knob('use_limit').setValue(True)
        archiveBeforeWrite(writeNode)
        writeNode.knob('beforeRender').setText(archiveScript)
        addArchiveKnobs(writeNode)
        nukescripts.clear_selection_recursive()

    if errors:
        details = '\n\n'.join(
            ['\nReason: '.join([key, value]) for key, value in errors.items()])
        showMessage(msg='Errors occurred while adding write nodes',
                    icon=QMessageBox.Information,
                    details=details)

    appUsageApp.updateDatabase('AddWrite')
