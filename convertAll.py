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

from os import listdir
from os.path import join
from sqlalchemy.ext.declarative import declarative_base
from omf.tools.Converter.BaseElements.DB import set_db
from omf import filesystem
from omf.config import the_config
from omf.tools.Converter.Converter import Converter


def import_all():
    db = declarative_base()
    set_db(db)

    fs = filesystem.Filesystem().fs

    for file in fs.listdir('data/Feeder/public/'):
        feeder_path = join("data/Feeder/public/", file)     # without omf, due to HOME_DIR in filesystem class
        Converter.convert(feeder_path, the_config.POSTGIS_DB_URI, -92.3395017, 38.9589246, 1)
