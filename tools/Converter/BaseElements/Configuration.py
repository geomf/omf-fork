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

from Element import Element
from DB import Base


class Configuration(Element, Base):
    __tablename__ = 'planet_osm_rels'

    configuration_tags = ['spacing', 'conductor_A', 'conductor_B', 'conductor_C', 'conductor_N']

    def __init__(self, element, feeder_id):
        super(Configuration, self).__init__(element, feeder_id)
        self.configuration_names = self._get_configuration_tags(element)

    @staticmethod
    def validate(element):
        return Element.validate(element)

    def perform_post_update(self, firstElementList):
        self._update_configuration_ids(firstElementList)
