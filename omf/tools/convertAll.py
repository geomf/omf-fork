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
from sqlalchemy import create_engine

from omf.tools.Converter.BaseElements.DB import set_db

db = declarative_base()
set_db(db)

from omf.tools.Converter.Converter import Converter

i = 0.0

for file in listdir('../data/Feeder/public/'):
    feeder_path = join("data/Feeder/public/", file)
    Converter.convert(feeder_path, 'postgresql://<db_user>:<db_password>@localhost:5432/ROS_development', -92.3395017 + i, 38.9589246)
    i += 0.5
