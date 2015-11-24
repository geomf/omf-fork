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

    def __init__(self, element, feeder):
        super(BaseNode, self).__init__(element, feeder)
        # change lat with lon in purpose!!!

        self.lon = float(element["longitude"]) * 10 + feeder.lon
        self.lat = float(element["latitude"]) * 10 + feeder.lat

        self.point = "{} {}".format(self.lon, self.lat)
        self.geo_point = 'SRID=900913;POINT( {} )'.format(self.point)

    def get_json_dict(self):
        json_dict = super(BaseNode, self).get_json_dict()
        json_dict["latitude"] = (self.lat - self.feeder.lat) / 10
        json_dict["longitude"] = (self.lon - self.feeder.lon) / 10
        return json_dict

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
