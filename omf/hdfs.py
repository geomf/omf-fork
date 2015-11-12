# Open Modeling Framework (OMF) Software for simulating power systems behavior
# Copyright (c) 2015, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#



import pyhdfs
import shutil
import vcap_parser
import os
from os.path import join as pJoin
from models.__metaModel__ import _omfDir

class Hdfs(object):

    HOME_DIR = '/user/omf/' # + vcap_parser.get_space_name() + '/'
    populated = False

    def __init__(self):
        self.hdfs = pyhdfs.HdfsClient(self.__get_all_namenodes())

    def __get_all_namenodes(self):
        namenodes = []
        credentials = vcap_parser.get_service_credentials('hdfs')
        cluster_config = credentials['HADOOP_CONFIG_KEY']
        names = cluster_config['dfs.ha.namenodes.nameservice1'].split(',')
        for name in names:
            namenodes.append(cluster_config['dfs.namenode.http-address.nameservice1.' + name])
        return namenodes

    def create_dir(self, path):
        print 'HDFS: Creating directory', path
        self.hdfs.mkdirs(Hdfs.HOME_DIR + path)

    def listdir(self, directory):
        return self.hdfs.listdir(Hdfs.HOME_DIR + directory)

    def is_dir(self, directory):
        print self.hdfs.get_file_status(Hdfs.HOME_DIR + directory).type
        return self.hdfs.get_file_status(Hdfs.HOME_DIR + directory).type == "DIRECTORY"

    def remove(self, path):
        try:
            self.hdfs.delete(Hdfs.HOME_DIR + path, recursive=True)
        except pyhdfs.HdfsPathIsNotEmptyDirectoryException:
            self.hdfs.delete(Hdfs.HOME_DIR + path + "/*")
            self.hdfs.delete(Hdfs.HOME_DIR + path)

    def stat(self, path):
        status = self.hdfs.get_file_status(Hdfs.HOME_DIR + path)
        return status

    def get_file_modification_time(self, path):
        return self.hdfs.get_file_status(Hdfs.HOME_DIR + path).modificationTime / 1000

    def exists(self, path):
        return self.hdfs.exists(Hdfs.HOME_DIR + path)

    def open(self, path):
        f = self.hdfs.open(Hdfs.HOME_DIR + path)
        print "Opening file: " + path + ". Type is: " + str(type(f))
        return f

    def save(self, path, content):
        try:
            self.hdfs.create(Hdfs.HOME_DIR + path, content)
        except pyhdfs.HdfsFileAlreadyExistsException:
            self.hdfs.delete(Hdfs.HOME_DIR + path)
            self.hdfs.create(Hdfs.HOME_DIR + path, content)

    def walk(self, path):
        print "Walk in path: " + path
        return self.hdfs.walk(Hdfs.HOME_DIR + path)

    def copy_within_fs(self, source, target):
        print "HDFS: Copy within fs: copying to local... from " + _omfDir + "/tmp/" + source + " to: " + Hdfs.HOME_DIR + target
        self.hdfs.copy_to_local(Hdfs.HOME_DIR + source, pJoin(_omfDir, "tmp", source))
        try:
            print "HDFS: Copy within fs: copying from local... from: " + Hdfs.HOME_DIR + target + " to: " + _omfDir + "/tmp/" + source
            self.hdfs.copy_from_local(pJoin(_omfDir, "tmp", source), Hdfs.HOME_DIR + target)
        except pyhdfs.HdfsFileAlreadyExistsException:
            print "HDFS: Copy within fs: file existed before :("
            self.hdfs.delete(Hdfs.HOME_DIR + target)
            self.hdfs.copy_from_local(pJoin(_omfDir, "tmp", source), Hdfs.HOME_DIR + target)

    def export_to_hdfs(self, directory, file_to_export):
        print 'HDFS: Copying file from local filesystem at ' + file_to_export.filename + ' to HDFS at ' + Hdfs.HOME_DIR + file_to_export.filename
        self.hdfs.copy_from_local(file_to_export.filename, pJoin(Hdfs.HOME_DIR, directory, file_to_export.filename),
                                  overwrite=True)
        return True

    def export_local_to_hdfs(self, directory, file_to_export):
        filename = file_to_export.split("/")[-1]
        print 'HDFS: Copying file from local filesystem at ' + file_to_export + ' to HDFS at ' + Hdfs.HOME_DIR + directory + "/" + filename
        self.hdfs.copy_from_local(file_to_export, pJoin(Hdfs.HOME_DIR, directory, filename), overwrite=True)
        return True

    def export_from_fs_to_local(self, source, target):
        directory = os.path.split(target)[0]
        if not os.path.isdir(directory):
            os.makedirs(directory)
        self.hdfs.copy_to_local(Hdfs.HOME_DIR + source, pJoin(_omfDir, target))

    def import_files_to_hdfs(self, local_directory, hdfs_directory):
        print "Exporting files from local directory: " + local_directory + " to hdfs directory: " + hdfs_directory
        self.create_dir(hdfs_directory)
        for f in os.listdir(local_directory):
            self.export_local_to_hdfs(hdfs_directory, pJoin(local_directory, f))
        return True



    def recursive_import_to_hdfs(self, start_dir):
        self.create_dir(start_dir)
        for f in os.listdir(pJoin(_omfDir, start_dir)):
            if os.path.isdir(pJoin(_omfDir, start_dir, f)):
                self.create_dir(pJoin(start_dir, f))
                self.recursive_import_to_hdfs(pJoin(start_dir, f))
            else:
                self.export_local_to_hdfs(start_dir, pJoin(_omfDir, start_dir, f))
        return True

    def populateHdfs(self):
        template_files = []
        model_files = []
        try:
            template_files = ["templates/" + x for x in self.listdir("templates")]
        except:
            print "importing templates to hdfs"
            if self.import_files_to_hdfs("templates", "templates"):
                template_files = ["templates/" + x for x in self.listdir("templates")]
                shutil.rmtree("templates")
        try:
            model_files = ["models/" + x for x in self.listdir("models") if not (x.endswith('.pyc') or x.endswith('.py'))]
        except:
            print "importing models to hdfs"
            if self.import_files_to_hdfs("models", "models"):
                model_files = ["models/" + x for x in self.listdir("models")]
                shutil.rmtree("models")
        try:
            if not self.exists("data"):
                self.recursive_import_to_hdfs("data")
        except Exception as e:
            print "Could not import data.... Reason: " + str(e)

        try:
            if not self.exists("static"):
                self.recursive_import_to_hdfs("static")
        except Exception as e:
            print "Could not import data.... Reason: " + str(e)

        if not (os.path.exists(_omfDir + "/tmp")):
            os.mkdir(_omfDir + "/tmp")
        if not (os.path.exists(_omfDir + "/tmp/data")):
            os.mkdir(_omfDir + "/tmp/data")
        if not (os.path.exists(_omfDir + "/tmp/data/Feeder")):
            os.mkdir(_omfDir + "/tmp/data/Feeder")
        if not (os.path.exists(_omfDir + "/tmp/data/Climate")):
            os.mkdir(_omfDir + "/tmp/data/Climate")
        if not (os.path.exists(_omfDir + "/tmp/data/Feeder/public")):
            os.mkdir(_omfDir + "/tmp/data/Feeder/public")

        self.populated = True
        return template_files, model_files