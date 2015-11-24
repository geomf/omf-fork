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

from ..BaseElements.SuperConfiguration import SuperConfiguration

__all__ = ["LineSpacing", "OverheadLineConductor", "UndergroundLineConductor"]


class LineSpacing(SuperConfiguration):
    tag_names = ["distance_BC", "distance_CN", "distance_AN", "distance_AB", "distance_AC", "distance_BN"]


class UndergroundLineConductor(SuperConfiguration):
    tag_names = []


class OverheadLineConductor(SuperConfiguration):
    tag_names = ["geometric_mean_radius", "resistance"]
