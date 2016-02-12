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


import os
import json

def get_service_credentials(service_name):
    vcap_services = os.getenv('VCAP_SERVICES')
    try:
        if vcap_services:
            return json.loads(vcap_services)[service_name][0]['credentials']
        else:
            return {}
    except KeyError:
        """Service not available in VCAP_SERVICES"""
        return {}

def get_space_name():
    vcap_application = os.getenv('VCAP_APPLICATION')
    if vcap_application:
        return json.loads(vcap_application)['space_name']
    else:
        return 'local'
