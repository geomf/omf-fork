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

import abc
import logging
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects import postgres
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from omf.tools.Converter.BaseElements.Feeder import Feeder

class Element(object):
    id = Column(Integer, primary_key=True)
    name = Column(String)
    power = Column(String)
    tags = Column(postgres.HSTORE)

    @declared_attr
    def feeder_id(cls):
        return Column(Integer, ForeignKey('feeder.id'))

    @declared_attr
    def feeder(cls):
        return relationship(Feeder, primaryjoin=lambda: Feeder.id == cls.feeder_id)

    tag_names = []
    configuration_tags = []
    configuration_names = {}

    def __init__(self, element, feeder):
        self.name = element["name"]
        self.feeder_id = feeder.id
        self.power = element["object"]
        self.objectType = element["object"]
        self.tags = {}
        for tag in self.tag_names:
            if tag in element:
                self.tags[tag] = str(element[tag])

    def get_json_dict(self):
        json_dict = {}
        json_dict["name"] = self.name
        json_dict["object"] = self.power
        for tag_name, tag_value in self.tags.iteritems():
            json_dict[tag_name] = tag_value
        return json_dict

    def _get_tags(self):
        tags = ""
        for tag_name, value in self.tags.iteritems():
            tags = "{} => {},".format(tag_name, value)
        return tags[:-1]

    @abc.abstractmethod
    def perform_post_update(self, firstElementList):
        return

    @staticmethod
    def validate(element):
        if "name" not in element:
            logging.warning("Warning: object without a name - {}".format(element))
            return False
        return True

    @staticmethod
    def update_geo_data(element, key, nodes):
        return element

    def _get_configuration_tags(self, element):
        configuration_names = {}
        for config_name in self.configuration_tags:
            if config_name in element:
                configuration_names[config_name] = element[config_name]
        return configuration_names

    #TODO: zmienic nazwe!!!
    def _add_configurations_to_json_dict(self, json_dict, configuration_list):
        for config_name in self.configuration_tags:
            if config_name in self.tags:
                config_id = int(self.tags[config_name])
                json_dict[config_name] = next((x.name for x in configuration_list if x.id == config_id), None)
        return json_dict

    def _update_configuration_ids(self, firstElementList):
        for config in self.configuration_names:
            self.tags[config] = str(firstElementList[self.configuration_names[config]].id)
