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


from models.__metaModel__ import _omfDir

import os
import shutil
from os.path import join as pJoin

class Localfs(object):

    HOME_DIR = ""

    def __init__(self):
        pass

    def create_dir(self, path):
        print 'Local FS: Creating directory', path
        os.mkdir(pJoin(_omfDir, path))

    def listdir(self, directory):
        return os.listdir(pJoin(_omfDir, directory))

    def remove(self, path):
        try:
            os.remove(pJoin(_omfDir, path))
        except IOError:
            os.rmdir(pJoin(_omfDir, path))

    def stat(self, path):
        status = os.stat(pJoin(_omfDir, path))
        return status

    def get_file_modification_time(self, path):
        return os.stat(pJoin(_omfDir, path)).st_mtime

    def exists(self, path):
        return os.path.exists(pJoin(_omfDir, path))

    def is_dir(self, directory):
        return os.path.isdir(pJoin(_omfDir, directory))

    def open(self, path):
        f = open(pJoin(_omfDir, path), 'r')
        return f

    def save(self, path, content):
        with open(pJoin(_omfDir, path), 'w+') as f:
            f.write(content)

    def walk(self, path):
        return os.walk(pJoin(_omfDir, path))

    def copy_within_fs(self, source, target):
        shutil.copytree(pJoin(_omfDir, source), pJoin(_omfDir, target))

    def export_to_hdfs(self, directory, file_to_export):
        return False

    def export_local_to_hdfs(self, directory, file_to_export):
        return False

    def import_files_to_hdfs(self, local_directory, hdfs_directory):
        return False

    def recursive_import_to_hdfs(self, start_dir):
        pass
