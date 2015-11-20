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
from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects import postgres


class Element(object):
    id = Column(Integer, primary_key=True)
    name = Column(String)
    feeder_id = Column(Integer)
    power = Column(String)
    tags = Column(postgres.HSTORE)

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
            self.tags[tag] = element[tag] if tag in element else None

    @abc.abstractmethod
    def perform_post_update(self, firstElementList):
        return

    def _get_tags(self):
        tags = ""
        for tag_name, value in self.tags.iteritems():
            tags = "{} => {},".format(tag_name, value)
        return tags[:-1]

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

    def _update_configuration_ids(self, firstElementList):
        for config in self.configuration_names:
            self.tags[config] = str(firstElementList[self.configuration_names[config]].id)
