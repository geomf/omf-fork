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

from ..BaseElements.Edge import Edge

__all__ = ['Transformer', 'Fuse', 'UndergroundLine', 'OverheadLine', 'Switch', 'Regulator', 'ChildLine']

class Transformer(Edge):
    tag_names = ["phases"]


class Fuse(Edge):
    tag_names = ["phases", "current_limit"]


class UndergroundLine(Edge):
    tag_names = ["phases", "length"]


class OverheadLine(Edge):
    tag_names = ["phases", "length"]


class Switch(Edge):
    tag_names = ["phases", "status"]


class Regulator(Edge):
    tag_names = ["phases"]


class TriplexLine(Edge):
    tag_names = ["phases", "groupid"]


class ChildLine(Edge):
    def __init__(self, element, feeder_id):
        super(Edge, self).__init__(element, feeder_id)
        self.parent = element["parent"]

        self.from_name = element["parent"]
        self.to_name = element["name"]
        self.power += "_connection"
        self.tags['child_line'] = 'True'
