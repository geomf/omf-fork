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

import logging
from sqlalchemy import Column, Integer
from geoalchemy2 import Geometry

from Element import Element
from DB import Base


class BaseNode(Element, Base):
    __tablename__ = 'planet_osm_nodes'

    lat = Column(Integer)
    lon = Column(Integer)
    geo_point = Column(Geometry('POINT'))

    def __init__(self, element, feeder_id):
        super(BaseNode, self).__init__(element, feeder_id)
        # change lat with lon in purpose!!!
        _lon = element["latitude"]
        _lat = element["longitude"]

        self.lon = float(_lon) * 10
        self.lat = -float(_lat) * 10
        self.lon += -10281993
        self.lat += 4715996  # 4695996

        self.point = "{} {}".format(self.lon, self.lat)
        self.geo_point = 'SRID=900913;POINT( {} )'.format(self.point)

        # change lat lon to google mercator. 			//39.0085476,-92.3647192
        # in mercator, position is stored in cm
        self.lat *= 100
        self.lon *= 100

    @staticmethod
    def validate(element):
        if "longitude" not in element:
            logging.warning("Warning: object without a longitude - {}".format(element))
            return False
        if "latitude" not in element:
            logging.warning("Warning: object without a latitude - {}".format(element))
            return False
        return Element.validate(element)

    @staticmethod
    def update_geo_data(element, key, nodes):
        if "longitude" not in element:
            if key in nodes and "px" in nodes[key]:
                element["longitude"] = nodes[key]["px"]
        if "latitude" not in element:
            if key in nodes and "py" in nodes[key]:
                element["latitude"] = nodes[key]["py"]
        return element
