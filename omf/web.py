# Portions Copyright (C) 2015 Intel Corporation
''' Web server for model-oriented OMF interface. '''

from flask import Flask, send_from_directory, request, redirect, render_template, session, abort, jsonify, Response, url_for
from flask_sslify import SSLify
from multiprocessing import Process
import json
import os
import flask_login
import hashlib
import random
import time
import datetime as dt
import shutil
import boto.ses
import models
import feeder
import milToGridlab
import cymeToGridlab
import logging
import filesystem
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from omf.config import the_config
from omf.common.email import Email
from omf.model.dbo import set_db
from omf.common.userRole import Role
from omf.common.userStatus import UserStatus

logger = logging.getLogger(__name__)

app = Flask("web")
sslify = SSLify(app)
app.config.from_object(the_config)

fs = filesystem.Filesystem().fs
fs.populate_local()

db = SQLAlchemy(app)
set_db(db)
populated = False

# model and persistence shall be created after db instance is created
from omf.model.user import User
from omf.persistence.databasePersistence import DatabasePersistence
from omf.persistence.filePersistence import FilePersistence

from omf.tools.Converter.BaseElements.DB import set_db as set_postgis_db
from sqlalchemy.ext.declarative import declarative_base

postgis_db = declarative_base()
set_postgis_db(postgis_db)
from omf.tools.Converter.Converter import Converter

_LAT = 38.9589246
_LON = -92.3395017

Session(app)
mail = Mail(app)
URL = the_config.APPLICATION_URL
_omfDir = os.path.dirname(os.path.abspath(__file__))

if the_config.PERSISTENCE_TYPE == 'FILE':
    persistence = FilePersistence()
elif the_config.PERSISTENCE_TYPE == 'DATABASE':
    persistence = DatabasePersistence()
else:
    raise ValueError('Unknown persistence type')

###################################################
# HELPER FUNCTIONS
###################################################

def current_user_name():
    """Returns current user's username"""
    return flask_login.current_user.username

def safeListdir(path):
    ''' Helper function that returns [] for dirs that don't exist. Otherwise new users can cause exceptions. '''
    try:
        return [x for x in fs.listdir(path) if not x.startswith(".")]
    except:
        return []


def getDataNames():
    ''' Query the OMF datastore to get names of all objects.'''
    try:
        currUser = current_user_name()
    except:
        currUser = "public"
    feeders = [x[:-5] for x in safeListdir("data/Feeder/" + currUser)]
    publicFeeders = [x[:-5] for x in safeListdir("data/Feeder/public/")]
    climates = [x[:-5] for x in safeListdir("./data/Climate/")]
    return {"feeders": sorted(feeders), "publicFeeders": sorted(publicFeeders), "climates": sorted(climates),
            "currentUser": currUser}


@app.before_request
def csrf_protect():
    if request.user_agent.browser != "chrome":
        return "<img style='width:400px;margin-right:auto; margin-left:auto;display:block;' \
			src='http://goo.gl/1GvUMA'><br> \
			<h2 style='text-align:center'>The OMF currently must be accessed by <a href='http://goo.gl/X2ZGhb''>Chrome</a></h2>"
    # NOTE: when we fix csrf validation this needs to be uncommented.
    # if request.method == "POST":
    #	token = session.get("_csrf_token", None)
    #	if not token or token != request.form.get("_csrf_token"):
    #		abort(403)


###################################################
# AUTHENTICATION AND USER FUNCTIONS
###################################################

def cryptoRandomString():
    ''' Generate a cryptographically secure random string for signing/encrypting cookies. '''
    if 'COOKIE_KEY' in globals():
        return globals()["COOKIE_KEY"]
    else:
        return hashlib.md5(str(random.random()) + str(time.time())).hexdigest()


login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"
app.secret_key = cryptoRandomString()

#TODO send_link function shall be put elsewhere because it is used by other file (gridlabMulti.py) and it is not the best idea to import common functions from web.py
def send_link(email, message, u={}):
    """
    Send message to email
    :param email: recipient email address (string)
    :param message: message to send (string)
    :param u: user (recipient) data (string)
    :return: 'Success' string if send was successful
    """
    logger.info('Sending link to: %s', email)
    reg_key = hashlib.md5(str(time.time()) + str(random.random())).hexdigest()

    user = persistence.getUser(email)
    user.reg_key = reg_key

    user.timestamp = dt.datetime.now()
    user.registered = False

    persistence.updateUser(user)

    if the_config.USE_AWS_SES_NRECA_SEND_MAIL_METHOD:
        try:
            key = open("emailCredentials.key").read()
        except:
            key = "NO_WAY_JOSE"
        c = boto.ses.connect_to_region("us-east-1",
                                       aws_access_key_id="AKIAJLART4NXGCNFEJIQ",
                                       aws_secret_access_key=key)
        outDict = c.send_email(the_config.SENDER_EMAIL, "OMF Registration Link",
                           message.replace("reg_link", URL + "/register/" + email + "/" + reg_key), [email])
    else:
        Email.send_email(sender=the_config.SENDER_EMAIL, recipients=[email], subject='OMF Registration Link',
                         message=message.replace("reg_link", URL + "/register/" + email + "/" + reg_key))

    logger.info('Link send successfully to: %s', email)
    return "Success"


@login_manager.user_loader
def load_user(username):
    ''' Required by flask_login to return instance of the current user '''
    return persistence.getUser(username)


def generate_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = cryptoRandomString()
    return session["_csrf_token"]

app.jinja_env.globals["csrf_token"] = generate_csrf_token


@app.route("/login", methods=["POST"])
def login():
    ''' Authenticate a user and send them to the URL they requested. '''
    username, password, remember = map(request.form.get, ["username",
                                                          "password", "remember"])
    logger.info('Calling /login for user: %s...', username)

    user = persistence.getUser(username)

    if user is not None and user.verify_password(password):
        flask_login.login_user(user, remember=remember == "on")

    nextUrl = str(request.form.get("next", "/"))
    return redirect(nextUrl)


@app.route("/login_page")
def login_page():
    nextUrl = str(request.args.get("next", "/"))
    if flask_login.current_user.is_authenticated():
        return redirect(nextUrl)
    # Generate list of models with quickRun
    modelNames = []
    for modelName in models.__all__:
        thisModel = getattr(models, modelName)
        if hasattr(thisModel, 'quickRender'):
            modelNames.append(modelName)
    if not modelNames:
        modelNames.append("No Models Available")
    return render_template("clusterLogin.html", next=nextUrl, modelNames=modelNames)


@app.route("/logout")
def logout():
    flask_login.logout_user()
    return redirect("/")


@app.route("/deleteUser", methods=["POST"])
@flask_login.login_required
def deleteUser():
    user = persistence.getUser(current_user_name())
    if user.role != Role.ADMIN.value:
        return "You are not authorized to delete users"
    username = request.form.get("username")
    logger.info('Calling /deleteUser for user: %s...', username)
    # Clean up user data.
    for objectType in ["Model", "Feeder"]:
        try:
            shutil.rmtree("data/" + objectType + "/" + username)
        except Exception, e:
            print "USER DATA DELETION FAILED FOR", e
    persistence.deleteUser(username)
    logger.info("Successfully delete user: %s", username)
    return "Success"


@app.route("/new_user", methods=["POST"])
@flask_login.login_required
def new_user():
    user = persistence.getUser(current_user_name())
    if user.role != Role.ADMIN.value:
        return redirect("/")
    email = request.form.get("email")
    logger.info('Calling /new_user for email: %s...', email)
    user = persistence.getUser(email)
    if user:
        return "Already Exists"
    else:
        user = User(username = email)
        persistence.addUser(user)
    message = "Click the link below to register your account for the OMF.  This link will expire in 24 hours:\n\nreg_link"
    logger.info("Succesfully created user account: %s", email)
    return send_link(email, message)


@app.route("/forgotpwd", methods=["POST"])
def forgotpwd():
    email = request.form.get("email")
    logger.info('Calling /forgotpwd for user: %s...')
    try:
        user = persistence.getUser(email)
        message = "Click the link below to reset your password for the OMF.  This link will expire in 24 hours.\n\nreg_link"
        return send_link(email, message, user)
    except Exception, e:
        logger.exception('failed to password reset user: %s', email)
        return "Error"


@app.route("/register/<email>/<reg_key>", methods=["GET", "POST"])
def register(email, reg_key):

    logger.info('Calling /register/%s/%s', email, reg_key)
    if flask_login.current_user.is_authenticated():
        return redirect("/")
    try:
        user = persistence.getUser(email)
    except Exception as e:
        logger.exception('Registering user, exception...')
        user = None
    if not (user and
            reg_key == user.reg_key and
            user.timestamp and
            dt.timedelta(1) > dt.datetime.now() - user.timestamp):
        return "This page either expired, or you are not supposed to access it.  It might not even exist"
    if request.method == "GET":
        return render_template("register.html", email=email)
    password, confirm_password = map(
        request.form.get, ["password", "confirm_password"])
    if password == confirm_password:
        user.username = email
        user.password_digest = User.hash_password(password)
        user.registered = True
        persistence.updateUser(user)
        flask_login.login_user(user)
    return redirect("/")


@app.route("/changepwd", methods=["POST"])
@flask_login.login_required
def changepwd():
    old_pwd, new_pwd, conf_pwd = map(
        request.form.get, ["old_pwd", "new_pwd", "conf_pwd"])
    user = persistence.getUser(current_user_name())
    if user.verify_password(old_pwd):
        if new_pwd == conf_pwd:
            user.password_digest =  User.hash_password(new_pwd)
            persistence.updateUser(user)
            return "Success"
        else:
            return "not_match"
    else:
        return "not_auth"


@app.route("/adminControls")
@flask_login.login_required
def adminControls():
    ''' Render admin controls. '''
    user = persistence.getUser(current_user_name())
    if user.role != Role.ADMIN.value:
        return redirect("/")

    users = persistence.getAllUsers()
    users = [x for x in users if x.role == Role.USER.value]

    for user in users:
        tStamp = user.timestamp
        if user.password_digest:
            user.status = UserStatus.REGISTERED
        elif dt.timedelta(1) > dt.datetime.now() - tStamp:
            user.status = UserStatus.EMAILSENT
        else:
            user.status = UserStatus.EMAILEXPIRED
    return render_template("adminControls.html", users=users)


@app.route("/myaccount")
@flask_login.login_required
def myaccount():
    ''' Render account info for any user. '''
    return render_template("myaccount.html", user=current_user_name())


@app.route("/robots.txt")
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

###################################################
# MODEL FUNCTIONS
###################################################


@app.route("/model/<owner>/<modelName>")
@flask_login.login_required
def showModel(owner, modelName):
    ''' Render a model template with saved data. '''
    user = persistence.getUser(current_user_name())
    if owner == current_user_name() or user.role == Role.ADMIN.value or owner == Role.PUBLIC.value:
        modelDir = "data/Model/" + owner + "/" + modelName
        try:
            with fs.open(modelDir + "/allInputData.json") as inJson:
                modelType = json.load(inJson).get("modelType", "")
                thisModel = getattr(models, modelType)
                return thisModel.renderTemplate(thisModel.template, fs, modelDir, False, getDataNames())
        except:
            return redirect("/")
    else:
        return redirect("/")


@app.route("/newModel/<modelType>")
@flask_login.login_required
def newModel(modelType):
    ''' Display the module template for creating a new model. '''
    thisModel = getattr(models, modelType)
    return thisModel.renderTemplate(thisModel.template, fs, datastoreNames=getDataNames())


@app.route("/runModel/", methods=["POST"])
@flask_login.login_required
def runModel():
    ''' Start a model running and redirect to its running screen. '''
    user = persistence.getUser(current_user_name())
    pData = request.form.to_dict()
    modelModule = getattr(models, pData["modelType"])
    # Handle the user.
    if user.role == Role.ADMIN.value and pData["user"] == Role.PUBLIC.value:
        owner = Role.PUBLIC.value
    elif user.role == Role.ADMIN.value and pData["user"] != Role.PUBLIC.value and pData["user"] != "":
        owner = pData["user"].replace('/', '')
    else:
        owner = user.username
    del pData["user"]
    # Handle the model name.
    modelName = pData["modelName"]
    del pData["modelName"]
    modelModule.run(
        os.path.join("data", "Model", owner, modelName), pData, fs)
    return redirect("/model/" + owner + "/" + modelName)


@app.route("/quickNew/<modelType>")
def quickNew(modelType):
    thisModel = getattr(models, modelType)
    if hasattr(thisModel, 'quickRender'):
        return thisModel.quickRender(thisModel.template, datastoreNames=getDataNames())
    else:
        return redirect("/")


@app.route("/quickRun/", methods=["POST"])
def quickRun():
    pData = request.form.to_dict()
    modelModule = getattr(models, pData["modelType"])
    user = pData["quickRunEmail"]
    modelName = "QUICKRUN-" + pData["modelType"]
    modelModule.run(
        os.path.join("data", "Model", user, modelName), pData)
    return redirect("/quickModel/" + user + "/" + modelName)


@app.route("/quickModel/<owner>/<modelName>")
def quickModel(owner, modelName):
    ''' Render a quickrun model template with saved data. '''
    modelDir = "data/Model/" + owner + "/" + modelName
    with fs.open(modelDir + "/allInputData.json") as inJson:
        modelType = json.load(inJson).get("modelType", "")
    thisModel = getattr(models, modelType)
    return thisModel.quickRender(thisModel.template, modelDir, False, getDataNames())


@app.route("/cancelModel/", methods=["POST"])
@flask_login.login_required
def cancelModel():
    ''' Cancel an already running model. '''
    pData = request.form.to_dict()
    modelModule = getattr(models, pData["modelType"])
    modelModule.cancel(
        os.path.join("data", "Model", pData["user"], pData["modelName"]))
    return redirect("/model/" + pData["user"] + "/" + pData["modelName"])


@app.route("/duplicateModel/<owner>/<modelName>/", methods=["POST"])
@flask_login.login_required
def duplicateModel(owner, modelName):
    user = persistence.getUser(current_user_name())
    newName = request.form.get("newName", "")
    if owner == user.username or user.role == Role.ADMIN.value or owner == Role.PUBLIC.value:
        destinationPath = "data/Model/" + user.username + "/" + newName
        logger.info('Copying model: %s, owned by: %s', modelName, owner)
        fs.copy_within_fs(
            "data/Model/" + owner + "/" + modelName, destinationPath)
        with fs.open(destinationPath + "/allInputData.json") as inFile:
            inData = json.load(inFile)
        inData["created"] = str(dt.datetime.now())
        fs.save(destinationPath + "/allInputData.json", json.dumps(inData, indent=4))
        logger.info('Copy of model: %s, owned by: %s done', modelName, owner)
        return redirect("/model/" + user.username + "/" + newName)
    else:
        return False


@app.route("/publishModel/<owner>/<modelName>/", methods=["POST"])
@flask_login.login_required
def publishModel(owner, modelName):
    user = persistence.getUser(current_user_name())
    newName = request.form.get("newName", "")
    logger.info('Publishing model: %s with new name: %s', modelName, newName)
    if owner == user.username or user.role == Role.ADMIN.value:
        destinationPath = "data/Model/public/" + newName
        fs.create_dir(destinationPath)

        fs.copy_within_fs(
            "data/Model/" + owner + "/" + modelName, destinationPath)
        with fs.open(destinationPath + "/allInputData.json") as inFile:
            inData = json.load(inFile)
            inData["created"] = str(dt.datetime.now())
            inFile.seek(0)
            s = json.dumps(inData, indent=4)
            fs.save(destinationPath + "/allInputData.json", s)
        return redirect("/model/public/" + newName)
    else:
        return False

###################################################
# FEEDER FUNCTIONS
###################################################


@app.route("/feeder/<owner>/<feederName>")
@flask_login.login_required
def feederGet(owner, feederName):
    ''' Editing interface for feeders. '''
    # MAYBEFIX: fix modelFeeder
    user = persistence.getUser(current_user_name())
    logger.info('Rendering feeder... user: %s; feeder name: %s; feeder owner: %s', current_user_name(), feederName, owner)
    return render_template("gridEdit.html", feederName=feederName, ref=request.referrer,
                           is_admin=user.role == Role.ADMIN.value, modelFeeder=False, public=owner == Role.PUBLIC.value,
                           currUser=user.username, owner=owner)


@app.route("/feeder/geo/<owner>/<feederName>")
@flask_login.login_required
def feederGetGeo(owner, feederName):
    ''' Editing interface for feeders. '''
    # MAYBEFIX: fix modelFeeder
    user = persistence.getUser(current_user_name())
    logger.info('Rendering feeder... user: %s; feeder name: %s; feeder owner: %s', current_user_name(), feederName, owner)
    return render_template("idEdit.html", feederName=feederName, ref=request.referrer,
                           is_admin=user.role == Role.ADMIN.value, modelFeeder=False, public=owner == Role.PUBLIC.value,
                           currUser=user.username, owner=owner)


@app.route("/getComponents/")
@flask_login.login_required
def getComponents():
    path = "data/Component/"
    components = {
        name[0:-5]: json.load(fs.open(path + name)) for name in fs.listdir(path)}
    return json.dumps(components)


@app.route("/milsoftImport/", methods=["POST"])
@flask_login.login_required
def milsoftImport():
    ''' API for importing a milsoft feeder. '''
    feederName = str(request.form.get("feederName", ""))
    stdFileName, seqFileName = map(
        lambda x: request.files[x], ["stdFile", "seqFile"])

    logger.info('Starting milsoft import process... user: %s; feeder name: %s; std file: %s; seq file: %s',
                current_user_name(), feederName, stdFileName.filename, seqFileName.filename)
    startImportProcess(feederName, milToGridlab.convert, [stdFileName.stream.read(), seqFileName.stream.read()])

    return redirect("/#feeders")


@app.route("/gridlabdImport/", methods=["POST"])
@flask_login.login_required
def gridlabdImport():
    '''This function is used for gridlabdImporting'''
    feederName = str(request.form.get("feederName", ""))
    glmFileName = request.files["glmFile"]

    logger.info('Starting gridlab import process... user: %s; feeder name: %s; glm file: %s',
                current_user_name(), feederName, glmFileName.filename)
    startImportProcess(feederName, feeder.convert, [glmFileName.stream.read()])

    return redirect("/#feeders")

# TODO: Check if rename mdb files worked

@app.route("/cymeImport/", methods=["POST"])
@flask_login.login_required
def cymeImport():
    ''' API for importing a cyme feeder. '''
    logger.error("IMPORTING MDB file")
    feederName = str(request.form.get("feederName", ""))
    logger.error("IMPORTING MDB file: "+feederName)
    mdbNetString, mdbEqString = map(
        lambda x: request.files[x], ["mdbNetFile", "mdbEqFile"])

    logger.info('Starting cyme import process... user: %s; feeder name: %s; mdb network: %s; mdb equipement: %s',
                 current_user_name(), feederName, mdbNetString.filename, mdbEqString.filename)
    startImportProcess(feederName, cymeToGridlab.convertCymeModel, [mdbNetString.filename, mdbEqString.filename])

    return redirect("/#feeders")

def startImportProcess(feederName, convertFunc, convertArgs):
    user_conversion_folder = "data/Conversion/" + current_user_name()
    if not fs.exists(user_conversion_folder):
        fs.create_dir(user_conversion_folder)
    file_name = "/" + feederName + ".json"
    fs.save(user_conversion_folder + file_name, "WORKING")

    importProc = Process(
        target=importBackground, args=[current_user_name(), feederName, convertFunc, convertArgs])
    importProc.start()


def importBackground(owner, feederName, convertFunc, convertArgs):
    ''' Function to run in the background for Milsoft import. '''
    file_name = "/" + feederName + ".json"
    user_conversion_folder = "data/Conversion/" + owner
    user_feeder_folder = "data/Feeder/" + owner
    newFeeder = dict(**feeder.newFeederWireframe)
    [newFeeder["tree"], xScale, yScale] = convertFunc(*convertArgs)
    newFeeder["layoutVars"]["xScale"] = xScale
    newFeeder["layoutVars"]["yScale"] = yScale
    logger.info('Attaching schedules.glm file')
    with open("./schedules.glm", "r") as schedFile:
        newFeeder["attachments"] = {"schedules.glm": schedFile.read()}
    logger.info('Save new feeder %s as new json file', feederName)
    fs.save(user_feeder_folder + file_name, json.dumps(newFeeder, indent=4))
    fs.remove(user_conversion_folder + file_name)
    Converter.convert(user_feeder_folder + file_name, the_config.POSTGIS_DB_URI, _LON, _LAT)


@app.route("/newBlankFeeder/", methods=["POST"])
@flask_login.login_required
def newBlankFeeder():
    '''This function is used for creating a new blank feeder.'''
    feederName = str(request.form.get("feederName", ""))
    logger.info('Creating new blank feeder... feder name: %s', feederName)
    with fs.open("static/SimpleFeeder.json") as simpleFeederFile:
        fs.save("data/Feeder/" + current_user_name() + "/" + feederName + ".json", simpleFeederFile.read())
    feederLink = "./feeder/" + current_user_name() + "/" + feederName
    return redirect(feederLink)


@app.route("/feederData/<owner>/<feederName>/")
@app.route("/feederData/<owner>/<feederName>/<modelFeeder>")
@flask_login.login_required
def feederData(owner, feederName, modelFeeder=False):
    # MAYBEFIX: fix modelFeeder capability.
    user = persistence.getUser(current_user_name())
    if user.role == Role.ADMIN.value or owner == user.username or owner == Role.PUBLIC.value:
        with fs.open("data/Feeder/" + owner + "/" + feederName + ".json") as feedFile:
            return feedFile.read()


@app.route("/saveFeeder/<owner>/<feederName>", methods=["POST"])
@flask_login.login_required
def saveFeeder(owner, feederName):
    ''' Save feeder data. '''
    user = persistence.getUser(current_user_name())
    if user.role == Role.ADMIN.value or owner == user.username or owner == Role.PUBLIC.value:
        # If we have a new user, make sure to make their folder:
        if not fs.exists("data/Feeder/" + owner):
            fs.create_dir("data/Feeder/" + owner)
        payload = json.loads(
            request.form.to_dict().get("feederObjectJson", "{}"))
        s = json.dumps(payload, indent=4)
        fs.save("data/Feeder/" + owner + "/" + feederName + ".json", s)
    return redirect("/#feeders")


@app.route("/saveFeederGeo/<feederId>", methods=["POST"])
@flask_login.login_required
def saveFeederFromGeoData(feederId):
    user_name = current_user_name()
    logger.info("Saving feeder: {} to json".format(feederId))
    feeder_data = Converter.deconvert(feederId, the_config.POSTGIS_DB_URI)
    logger.info("Saving feeder: {} to filesystem".format(feeder_data[0]))
    fs.save("data/Feeder/" + user_name + "/" + feeder_data[0], json.dumps(feeder_data[1]))
    return "Success"


###################################################
# OTHER FUNCTIONS
###################################################


@app.route("/")
@flask_login.login_required
def root():
    ''' Render the home screen of the OMF. '''
    # Gather object names.
    if not fs.populated:
        fs.populate_hdfs()
    user = persistence.getUser(current_user_name())
    publicModels = [{"owner": "public", "name": x}
                    for x in safeListdir("data/Model/public/")]
    userModels = [{"owner": user.username, "name": x}
                  for x in safeListdir("data/Model/" + user.username)]
    publicFeeders = [{"owner": "public", "name": x[0:-5], "status":"Ready"}
                     for x in safeListdir("data/Feeder/public/")]
    userFeeders = [{"owner": user.username, "name": x[0:-5], "status":"Ready"}
                   for x in safeListdir("data/Feeder/" + user.username)]
    conversions = [{"owner": user.username, "name": x[0:-5], "status":"Converting"}
                   for x in safeListdir("data/Conversion/" + user.username)]
    allModels = publicModels + userModels
    allFeeders = publicFeeders + userFeeders
    # Allow admin to see all models and feeders.
    if user.role == Role.ADMIN.value:
        allFeeders = [{"owner": owner, "name": feed[0:-5], "status":"Ready"} for owner in safeListdir("data/Feeder/")
                      for feed in safeListdir("data/Feeder/" + owner)]
        allModels = [{"owner": owner, "name": mod} for owner in safeListdir("data/Model/")
                     for mod in safeListdir("data/Model/" + owner)]
    # Grab metadata for models and feeders.
    for mod in allModels:
        try:
            modPath = "data/Model/" + mod["owner"] + "/" + mod["name"]
            allInput = json.load(fs.open(modPath + "/allInputData.json"))
            mod["runTime"] = allInput.get("runTime", "")
            mod["modelType"] = allInput.get("modelType", "")
            mod["status"] = getattr(
                models, mod["modelType"]).getStatus(modPath, fs)
            # mod["created"] = allInput.get("created","")
            mod["editDate"] = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.gmtime(fs.get_file_modification_time(modPath)))
        except Exception as e:
            logger.exception("Exception while setting model status: " + str(e))
            continue
    for feed in allFeeders:
        try:
            feedPath = "data/Feeder/" + \
                feed["owner"] + "/" + feed["name"] + ".json"
            feed["editDate"] = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.gmtime(fs.get_file_modification_time(feedPath)))
        except:
            continue
    for conversion in conversions:
        try:
            convPath = "data/Conversion/" + \
                conversion["owner"] + "/" + conversion["name"] + ".json"
            tm = fs.stat(convPath).modificationTime
            conversion["editDate"] = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.gmtime(fs.get_file_modification_time(convPath)))
        except:
            continue
    return render_template("home.html", models=allModels, feeders=allFeeders + conversions,
                           current_user=user.username, is_admin=user.role == Role.ADMIN.value, modelNames=models.__all__)


@app.route("/delete/<objectType>/<owner>/<objectName>", methods=["POST"])
@flask_login.login_required
def delete(objectType, objectName, owner):
    ''' Delete models or feeders. '''
    user = persistence.getUser(current_user_name())
    if owner != user.username and user.role == Role.ADMIN.value:
        return redirect("/")
    if objectType == "Feeder":
        fs.remove("data/Feeder/" + owner + "/" + objectName + ".json")
        return redirect("/#feeders")
    elif objectType == "Model":
        fs.remove("data/Model/" + owner + "/" + objectName)
    return redirect("/")


@app.route("/downloadModelData/<owner>/<modelName>/<path:fullPath>")
@flask_login.login_required
def downloadModelData(owner, modelName, fullPath):
    pathPieces = fullPath.split('/')
    return send_from_directory("data/Model/" + owner + "/" + modelName + "/" + "/".join(pathPieces[0:-1]), pathPieces[-1])


@app.route("/uniqObjName/<objtype>/<owner>/<name>")
@flask_login.login_required
def uniqObjName(objtype, owner, name):
    ''' Checks if a given object type/owner/name is unique. '''
    if objtype == "Model":
        path = "data/Model/" + owner + "/" + name
    elif objtype == "Feeder":
        path = "data/Feeder/" + owner + "/" + name + ".json"
    return jsonify(exists=fs.exists(path))


@app.route("/id")
def id():
    return redirect(url_for('static', filename='id/index.html'))


if __name__ == "__main__":
    URL = "http://localhost:5000"
    template_files, model_files = fs.populate_hdfs()
    app.run(debug=True, extra_files=template_files + model_files, port=1180)
