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

import json
import logging
from os.path import basename
from sqlalchemy.orm import sessionmaker

from BaseElements.BaseNode import BaseNode
from BaseElements.ChildNode import ChildNode
from BaseElements.Edge import Edge
from BaseElements.SuperConfiguration import SuperConfiguration
from BaseElements.Configuration import Configuration
from BaseElements.Feeder import Feeder
from Elements import *

class Converter(object):
    read_type = {
                     "triplex_meter": NodeElements.TriplexMeter,
                     "node": NodeElements.Node,
                     "transformer": EdgeElements.Transformer,
                     "fuse": EdgeElements.Fuse,
                     "underground_line": EdgeElements.UndergroundLine,
                     "overhead_line": EdgeElements.OverheadLine,
                     "switch": EdgeElements.Switch,
                     "regulator": EdgeElements.Regulator,
                     "triplex_line": EdgeElements.TriplexLine,
                     "line_spacing": SuperConfigurationElements.LineSpacing,
                     "overhead_line_conductor": SuperConfigurationElements.OverheadLineConductor,
                     "underground_line_conductor": SuperConfigurationElements.UndergroundLineConductor,
                     "line_configuration": ConfigurationElements.LineConfiguration,
                     "transformer_configuration": ConfigurationElements.TransformerConfiguration,
                     "regulator_configuration":   ConfigurationElements.RegulatorConfiguration,
                     "triplex_node": ChildNodeElements.TriplexNode,
                     "load": ChildNodeElements.Load,
                     "capacitor": ChildNodeElements.Capacitor,
                     "ZIPload": ChildNodeElements.ZIPLoad,
                     "waterheater": ChildNodeElements.WaterHeater,
                     "house": ChildNodeElements.House,
                     "meter": ChildNodeElements.Meter,
                     "battery": ChildNodeElements.Battery,
                     "solar": ChildNodeElements.Solar,
                     "inverter": ChildNodeElements.Inverter,
                     "windturb_dg": ChildNodeElements.WindTurbDg,
                     "triplex_load": ChildNodeElements.TriplexLoad
                }

    feeder_config_types = ["climate", "player", "recorder"]

    @staticmethod
    def convert(feeder_id, feeder_name, engine):
        with open(feeder_name) as data_file:
            data = json.load(data_file)

        configList = []
        nodesList = {}
        firstElementList = {}
        secondElementList = {}
        thirdElementList = {}

        for node in data["nodes"]:
            nodesList[node["treeIndex"]] = node

        for key, element in data["tree"].iteritems():
            if "object" not in element:
                logging.warning("Object without a type - {}, saving to feeder config".format(element))
                configList.append(str(Converter.byteify(element)))
                continue
            if element["object"] in Converter.feeder_config_types:
                configList.append(str(Converter.byteify(element)))
                continue
            if element["object"] not in Converter.read_type:
                logging.warning("not yet supported object type - {}".format(element["object"]))
                continue
            class_Name = Converter.read_type[element["object"]]
            element = class_Name.update_geo_data(element, int(key), nodesList)
            if class_Name.validate(element):
                ele = class_Name(element, feeder_id)
                if isinstance(ele, BaseNode) or isinstance(ele, SuperConfiguration):
                    firstElementList[ele.name] = ele
                    if isinstance(ele, ChildNode):
                        thirdElementList[ele.name] = EdgeElements.ChildLine(element, feeder_id)
                elif isinstance(ele, Configuration):
                    secondElementList[ele.name] = ele
                elif isinstance(ele, Edge):
                    thirdElementList[ele.name] = ele

        Session = sessionmaker(bind=engine)
        session = Session()

        for ele in firstElementList.values():
            session.add(ele)
            session.flush()
            firstElementList[ele.name].id = ele.id

        for ele in secondElementList.values():
            ele.perform_post_update(firstElementList)
            session.add(ele)
            session.flush()
            secondElementList[ele.name].id = ele.id

        for ele in thirdElementList.values():
            ele.perform_post_update(Converter.merge_two_dicts(firstElementList, secondElementList))
            session.add(ele)

        session.add(Feeder(basename(feeder_name), configList))
        session.commit()

    @staticmethod
    def merge_two_dicts(x, y):
        '''Given two dicts, merge them into a new dict as a shallow copy.'''
        z = x.copy()
        z.update(y)
        return z

    @staticmethod
    def byteify(input):
        if isinstance(input, dict):
            return {Converter.byteify(key):Converter.byteify(value) for key,value in input.iteritems()}
        elif isinstance(input, list):
            return [Converter.byteify(element) for element in input]
        elif isinstance(input, unicode):
            return input.encode('utf-8')
        else:
            return input
