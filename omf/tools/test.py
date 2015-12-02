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
import json
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

from omf.tools.Converter.BaseElements.DB import set_db

db = declarative_base()
set_db(db)

from omf.tools.Converter.Converter import Converter

i = 1

while i < 2:
    feeder_data = Converter.deconvert(i, 'postgresql://<db_user>:<db_password>@localhost:5432/ROS_development')

    with open(feeder_data[0], 'w') as file:
        json.dump(feeder_data[1], file)
    i += 1
