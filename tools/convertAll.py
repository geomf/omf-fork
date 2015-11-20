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

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

from Converter.BaseElements.DB import set_db

db = declarative_base()
set_db(db)

engine = create_engine('postgresql://<db_user>:<db_password>@localhost:5432/ROS_development')

from Converter.BaseElements import *
from Converter.Converter import Converter

db.metadata.create_all(engine)

#feeder_path = '../omf/data/Feeder/public/ABEC Columbia.json'
feeder_path = '../omf/data/Feeder/admin/Autocli Alberich Calibrated.json'

Converter.convert(feeder_path, engine, -92.3395017, 38.9589246)
