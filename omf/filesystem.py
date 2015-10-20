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


import hdfs
import vcap_parser
import localfs

class Filesystem(object):

    HOME_DIR = '/user/omf/' # + vcap_parser.get_space_name() + '/'

    def __init__(self):
        credentials = vcap_parser.get_service_credentials('hdfs')
        if credentials and credentials['HADOOP_CONFIG_KEY'] != {}:
            self.fs = hdfs.Hdfs()
        else:
            self.fs = localfs.Localfs()

