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

engine = create_engine('postgresql://<db_user>:<db_password>@localhost:5432/ROS_development')

from omf.tools.Converter.Converter import Converter

db.metadata.create_all(engine)

i = 1

while i < 14:
    feeder_json = Converter.deconvert(1, engine)

    with open(str(i)+'.json', 'w') as file:
        json.dump(feeder_json, file)
    i += 1
