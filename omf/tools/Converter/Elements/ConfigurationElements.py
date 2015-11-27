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

from ..BaseElements.Configuration import Configuration

__all__ = ["LineConfiguration", "TransformerConfiguration", "RegulatorConfiguration"]


class LineConfiguration(Configuration):
    tag_names = []

class TransformerConfiguration(Configuration):
    tag_names = ["powerC_rating", "primary_voltage", "secondary_voltage", "connect_type", "impedance", "power_rating"]


class RegulatorConfiguration(Configuration):
    tag_names = ["Control", "raise_taps", "PT_phase", "band_center", "current_transducer_ratio", "power_transducer_ratio",
            "compensator_x_setting_A", "time_delay", "connect_type", "regulation", "CT_phase", "band_width",
            "tap_pos_A", "control_level", "compensator_r_setting_A", "Type", "lower_taps"]

class TriplexLineConfiguration(Configuration):
    tag_names = ["diameter", "insulation_thickness"]
