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
from BaseNode import BaseNode

# underground_line and overhead_line have unused lat lon (transformer not)
class ChildNode(BaseNode):

    def __init__(self, element, feeder):
        super(ChildNode, self).__init__(element, feeder)
        self.tags['child_point'] = 'True'

    @staticmethod
    def validate(element):
        if "parent" not in element:
            logging.warning("Warning: object without a parent - {}".format(element))
            return False
        return BaseNode.validate(element)
