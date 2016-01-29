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
from pyproj import Proj

from omf.tools.Converter.BaseElements.DB import Base

class Feeder(Base):
    __tablename__ = 'feeders'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    config = Column(postgres.JSON)
    lat = Column(Integer)
    lon = Column(Integer)
    user_id = Column(Integer)

    def __init__(self, name, lon, lat, user_id):
        self.name = name
        lon_lat = Feeder.lon_lat_to_mercator(lon, lat)
        self.lon = lon_lat[0]
        self.lat = lon_lat[1]
        self.user_id = user_id

    def set_config(self, configList):
        self.config = configList

    @staticmethod
    def lon_lat_to_mercator(lon, lat):
        p = Proj(init='EPSG:3857')
        lon_lat = p(lon, lat)
        return (lon_lat[0] * 100, lon_lat[1] * 100)
