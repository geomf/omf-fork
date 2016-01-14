# Portions Copyrights (C) 2015 Intel Corporation
""" Common functions for all models """

import json
import os
import sys
import tempfile
import webbrowser
import math
import shutil
from os.path import join as pJoin
from os.path import split as pSplit
import logging

logger = logging.getLogger(__name__)

# Locational variables so we don't have to rely on OMF being in the system path.
_myDir = os.path.dirname(os.path.abspath(__file__))
_omfDir = os.path.dirname(_myDir)


def renderTemplate(template, modelDir="", absolutePaths=False, datastoreNames={}, quickRender=False):
    ''' Render the model template to an HTML string.
    By default render a blank one for new input.
    If modelDir is valid, render results post-model-run.
    If absolutePaths, the HTML can be opened without a server. 
    If quickRender, pass this to template so we can render for non-logged-in users. '''
    logger.debug('Rendering model template... modelDir: %s; absolutePaths: %s; datastoreNames: %s; quickRender: %s',
                 modelDir, absolutePaths, datastoreNames, quickRender)
    try:
        inJson = json.load(open(pJoin(modelDir, "allInputData.json")))
        modelPath, modelName = pSplit(modelDir)
        deepPath, user = pSplit(modelPath)
        inJson["modelName"] = modelName
        inJson["user"] = user
        allInputData = json.dumps(inJson)
    except IOError:
        allInputData = None
    try:
        allOutputData = open(pJoin(modelDir, "allOutputData.json")).read()
    except IOError:
        allOutputData = None
    if absolutePaths:
        # Parent of current folder.
        pathPrefix = _omfDir
    else:
        pathPrefix = ""
    with open('templates/footer.html', 'r') as footer_file:
        footer = footer_file.read()
    with open('templates/nrelsObligation.html') as nrels_file:
        nrels_text = nrels_file.read()
    return template.render(allInputData=allInputData,
                           allOutputData=allOutputData, modelStatus=getStatus(modelDir), pathPrefix=pathPrefix,
                           datastoreNames=datastoreNames, quickRender=quickRender, footer=footer, nrels_text=nrels_text)


def renderAndShow(template, modelDir="", datastoreNames={}):
    ''' Render and open a template (blank or with output) in a local browser. '''
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp:
        temp.write(
            renderTemplate(template, modelDir=modelDir, absolutePaths=True))
        temp.flush()
        webbrowser.open("file://" + temp.name)


def getStatus(modelDir):
    ''' Is the model stopped, running or finished? '''
    if not os.path.isdir(modelDir):
        return "preRun"
    try:
        modFiles = os.listdir(modelDir)
    except:
        modFiles = []
    hasInput = "allInputData.json" in modFiles
    hasPID = "PPID.txt" in modFiles
    hasOutput = "allOutputData.json" in modFiles
    if hasInput and not hasOutput and not hasPID:
        return "stopped"
    elif hasInput and not hasOutput and hasPID:
        return "running"
    elif hasInput and hasOutput and not hasPID:
        return "finished"
    else:
        # Broken! Make the safest choice:
        return "stopped"


def cancel(modelDir):
    ''' Try to cancel a currently running model. '''
    # Kill GLD process if already been created
    logger.info('Canceling running model... modelDir: %s', modelDir)
    try:
        with open(pJoin(modelDir, "PID.txt"), "r") as pidFile:
            pid = int(pidFile.read())
            # print "pid " + str(pid)
            os.kill(pid, 15)
            logger.info("PID KILLED")
    except:
        pass
    # Kill runForeground process
    try:
        with open(pJoin(modelDir, "PPID.txt"), "r") as pPidFile:
            pPid = int(pPidFile.read())
            os.kill(pPid, 15)
            logger.info("PPID KILLED")
    except:
        pass
    # Remove PID, PPID, and allOutputData file if existed
    try:
        for fName in os.listdir(modelDir):
            if fName in ["PID.txt", "PPID.txt", "allOutputData.json"]:
                os.remove(pJoin(modelDir, fName))
        logger.info("CANCELED %s", modelDir)
    except:
        pass


def roundSig(x, sig=3):
    ''' Round to a given number of sig figs. '''
    roundPosSig = lambda y, sig: round(
        y, sig - int(math.floor(math.log10(y))) - 1)
    if x == 0:
        return 0
    elif x != x:
        return 0  # This is handling float's NaN.
    elif x < 0:
        return -1 * roundPosSig(-1 * x, sig)
    else:
        return roundPosSig(x, sig)


def _test():
    """ No test required for this file. """
    pass
