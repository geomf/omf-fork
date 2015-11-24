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
from sqlalchemy import create_engine

from omf.tools.Converter.BaseElements.BaseNode import BaseNode
from omf.tools.Converter.BaseElements.ChildNode import ChildNode
from omf.tools.Converter.BaseElements.Edge import Edge
from omf.tools.Converter.BaseElements.SuperConfiguration import SuperConfiguration
from omf.tools.Converter.BaseElements.Configuration import Configuration
from omf.tools.Converter.BaseElements.Feeder import Feeder
from omf.tools.Converter.Elements import *

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
    def convert(feeder_path, db_address, lon, lat):
        with open(feeder_path) as data_file:
            data = json.load(data_file)

        configList = []
        nodesList = {}
        firstElementList = {}
        secondElementList = {}
        thirdElementList = {}

        for node in data["nodes"]:
            nodesList[node["treeIndex"]] = node

        engine = create_engine(db_address)
        Session = sessionmaker(bind=engine)
        session = Session()

        feeder = Feeder(basename(feeder_path), lon, lat)
        session.add(feeder)
        session.flush()

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
                ele = class_Name(element, feeder)
                if isinstance(ele, BaseNode) or isinstance(ele, SuperConfiguration):
                    firstElementList[ele.name] = ele
                    if isinstance(ele, ChildNode):
                        thirdElementList[ele.name] = EdgeElements.ChildLine(element, feeder)
                elif isinstance(ele, Configuration):
                    secondElementList[ele.name] = ele
                elif isinstance(ele, Edge):
                    thirdElementList[ele.name] = ele

        feeder.set_config(configList)

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

        session.commit()

    @staticmethod
    def deconvert(feeder_id, engine):
        #TODO: Implement it
        Session = sessionmaker(bind=engine)
        session = Session()
        tree = {}

        nodes_list = session.query(BaseNode).filter(BaseNode.feeder_id == feeder_id).all()
        edge_list = session.query(Edge).filter(Edge.feeder_id == feeder_id).all()
        configuration_list = session.query(Configuration).filter(Configuration.feeder_id == feeder_id).all()
        for node in nodes_list:
            json_dict = node.get_json_dict()
            tree[json_dict["name"]] =json_dict
            print(node.name, json_dict)
        for edge in edge_list:
            json_dict = edge.get_json_dict(nodes_list, configuration_list)
            tree[json_dict["name"]] =json_dict
            print(edge.name, json_dict)
        for configuration in configuration_list:
            json_dict = configuration.get_json_dict(configuration_list)
            tree[json_dict["name"]] =json_dict
            print(configuration.name, json_dict)

        with open('asdfg.json', 'w') as file:
            json.dump(tree, file)

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
