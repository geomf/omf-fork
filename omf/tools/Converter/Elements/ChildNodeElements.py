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

from ..BaseElements.ChildNode import ChildNode

__all__ = ['TriplexNode', 'Load', 'Capacitor', 'ZIPLoad', 'WaterHeater', 'House', "Meter", 'Battery', 'Solar',
           'Inverter', 'WindTurbDg', 'TriplexLoad']


class TriplexNode(ChildNode):
    tag_names = ["phases", "nominal_voltage", "power_12"]


class Load(ChildNode):
    tag_names = ["phases", "nominal_voltage", "load_class", "constant_power_C","constant_power_B", "constant_power_A"]


class Capacitor(ChildNode):
    tag_names = ["phases", "control", "capacitor_A", "control_level","capacitor_B", "phases_connected", "switchC",
                 "nominal_voltage", "capacitor_C", "switchB", "switchA", "pt_phase"]


class ZIPLoad(ChildNode):
    tag_names = ["schedule_skew", "power_fraction", "current_fraction", "base_power", "current_pf", "power_pf",
                 "heatgain_fraction", "impedance_fraction", "impedance_pf"]


class WaterHeater(ChildNode):
    tag_names = ["schedule_skew", "tank_volume", "location", "thermostat_deadband", "heating_element_capacity",
                 "demand", "temperature", "tank_setpoint", "tank_UA"]


class House(ChildNode):
    tag_names = ["schedule_skew", "floor_area", "cooling_COP", "cooling_system_type", "heating_setpoint",
                 "cooling_setpoint", "air_temperature", "thermal_integrity_level", "heating_COP", "mass_temperature",
                 "heating_system_type"]


class Meter(ChildNode):
    tag_names = ["phases", "nominal_voltage"]


class Battery(ChildNode):
    tag_names = ["power_factor", "base_efficiency", "generator_status", "Energy", "power_type", "V_Max",
                 "generator_mode", "scheduled_power", "parasitic_power_draw", "I_Max", "P_Max", "E_Max"]


class Solar(ChildNode):
    tag_names = ["generator_mode", "area", "generator_status", "efficiency", "panel_type"]


class Inverter(ChildNode):
    tag_names = ["phases", "inverter_type", "generator_status", "power_factor", "generator_mode"]


class WindTurbDg(ChildNode):
    tag_names = ["phases", "Gen_status", "Turbine_Model", "Gen_mode", "Gen_type"]


class TriplexLoad(ChildNode):
    tag_names = ["impedance_pf_12", "phases", "nominal_voltage", "power_pf_12", "power_fraction_12",
                 "impedance_fraction_12", "base_power_12"]
