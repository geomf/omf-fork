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

from omf.tools.Converter.BaseElements.Element import Element
from omf.tools.Converter.BaseElements.DB import Base


class BaseNode(Element, Base):
    __tablename__ = 'planet_osm_nodes'

    lat = Column(Integer)
    lon = Column(Integer)
    geo_point = Column(Geometry('POINT'))

    def __init__(self, element, feeder):
        super(BaseNode, self).__init__(element, feeder)

        self.lon = float(element["longitude"]) * 1000 + feeder.lon
        self.lat = float(element["latitude"]) * 1000 + feeder.lat

        self.point = "{} {}".format(self.lon/100, self.lat/100)
        self.geo_point = 'SRID=900913;POINT( {} )'.format(self.point)

    def get_json_dict(self, edge_list):
        json_dict = super(BaseNode, self).get_json_dict()
        json_dict["latitude"] = (self.lat - self.feeder.lat) / 1000.0
        json_dict["longitude"] = (self.lon - self.feeder.lon) / 1000.0
        if "child_point" in self.tags:
            json_dict["parent"] = next((x.name for x in edge_list if x.nodes[1] == self.id), None)
            del json_dict["child_point"]
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
