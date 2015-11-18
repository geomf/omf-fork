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
from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects import postgres

from ..BaseElements.DB import Base

class Feeder(Base):
    __tablename__ = 'feeder'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    config = Column(postgres.ARRAY(String))

    def __init__(self, name, configList):
        self.name = name
        self.config = configList
