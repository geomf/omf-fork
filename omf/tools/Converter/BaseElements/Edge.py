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
from sqlalchemy import Column, BigInteger
from sqlalchemy.dialects import postgres
from geoalchemy2 import Geometry

from omf.tools.Converter.BaseElements.Element import Element
from omf.tools.Converter.BaseElements.DB import Base


class Edge(Element, Base):
    __tablename__ = 'planet_osm_ways'
    nodes = Column(postgres.ARRAY(BigInteger))
    way = Column(Geometry('LineString'))

    configuration_tags = ['configuration']

    def __init__(self, element, feeder):
        super(Edge, self).__init__(element, feeder)
        self.from_name = element["from"]
        self.to_name = element["to"]
        self.configuration_names = self._get_configuration_tags(element)

    def get_json_dict(self, nodes_list, configuration_list):
        json_dict = super(Edge, self).get_json_dict()
        from_id = self.nodes[0]
        to_id = self.nodes[1]
        json_dict["from"] = next((x.name for x in nodes_list if x.id == from_id), None)
        json_dict["to"] = next((x.name for x in nodes_list if x.id == to_id), None)
        json_dict = self._add_configurations_to_json_dict(json_dict, configuration_list)
        return json_dict

    @staticmethod
    def validate(element):
        if "from" not in element:
            logging.warning("Warning: object without a from - {}".format(element))
            return False
        if "to" not in element:
            logging.warning("Warning: object without a to - {}".format(element))
            return False
        return Element.validate(element)

    def _getWay(self, _from, _to):
        return 'SRID=900913;LINESTRING( {}, {} )'.format(_from.point, _to.point)

    def perform_post_update(self, firstElementList):
        if self.from_name not in firstElementList:
            logging.debug('Edge: {} from node: {} does not exist, cannot create geo data'.format(self.name, self.from_name))
            return False
        if self.to_name not in firstElementList:
            logging.debug('Edge: {} to node: {} does not exist, cannot create geo data'.format(self.name, self.to_name))
            return False
        _from = firstElementList[self.from_name]
        _to = firstElementList[self.to_name]
        self.nodes = [_from.id, _to.id]
        self.way = self._getWay(_from, _to)
        self._update_configuration_ids(firstElementList)
        return True
