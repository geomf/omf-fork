#
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
import logging
import json
import redis

logger = logging.getLogger(__name__)

class Config(object):
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = '.'
    APPLICATION_URL = 'http://localhost:5000/'
    USE_AWS_SES_NRECA_SEND_MAIL_METHOD = False
    SENDER_EMAIL = 'debug@debug.com'
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/user.db'
    PERSISTENCE_TYPE = 'DATABASE'
    POSTGIS_DB_URI = 'postgresql://<db_user>:<db_password>@localhost:5432/ROS_development'

class DebugConfig(Config):
    pass

class NRECAConfig(Config):
    APPLICATION_URL = 'http://www.omf.coop'
    USE_AWS_SES_SEND_MAIL_METHOD = True
    SENDER_EMAIL = 'admin@omf.coop'
    PERSISTENCE_TYPE = 'FILE'

class Dp2Config(Config):
    def __init__(self):
        logging.root.setLevel(os.environ['LOG_LEVEL'])

        self.vcap_services =  json.loads(os.environ['VCAP_SERVICES'])
        self.vcap_application =  json.loads(os.environ['VCAP_APPLICATION'])
        if self.vcap_application['application_uris']:
            self.APPLICATION_URL = 'http://' + self.vcap_application['application_uris'][0]
        redis_session_service = self.__get_service_configuration('redis28', self.SESSION_SERVICE_NAME)
        redis_session_credentials = redis_session_service['credentials']
        redis_session = redis.Redis(host=redis_session_credentials['hostname'], port=redis_session_credentials['port'],
                                    db=0, password=redis_session_credentials['password'])
        self.SESSION_REDIS = redis_session

        smtp_service = self.__get_service_configuration('smtp', self.SMTP_SERVICE_NAME)
        smtp_credentials = smtp_service['credentials']
        self.MAIL_SERVER = smtp_credentials['host']
        self.MAIL_PORT = int(smtp_credentials['port'])
        self.MAIL_USE_TLS = True
        self.MAIL_USERNAME = smtp_credentials['username']
        self.MAIL_PASSWORD = smtp_credentials['password']

        self.SENDER_EMAIL = os.environ['SENDER_EMAIL']

        user_database_service = self.__get_service_configuration('user-provided', self.USER_DATABASE_SERVICE_NAME)
        user_database_credentials = user_database_service['credentials']
        self.SQLALCHEMY_DATABASE_URI = user_database_credentials['uri']
        self.POSTGIS_DB_URI = user_database_credentials['uri']
        self.MOD_TILE_BG_PROXY = user_database_credentials['mod-tile-bg-proxy']
        self.MOD_TILE_FG = user_database_credentials['mod-tile-fg-host']
        self.ROS_HOST = user_database_credentials['ros-host']

    def __get_service_configuration(self, service_type, service_name):
        service = next((service for service in self.vcap_services[service_type]
                                    if service['name'] == service_name), None)
        if service is None:
            logging.exception('%s service, type: %s not found in VCAP_SERVICES env variable', service_name, service_type)
            raise EnvironmentError('%s service, type: %s not found'.format(service_name, service_type))
        return service

    SESSION_TYPE = 'redis'
    USE_AWS_SES_NRECA_SEND_MAIL_METHOD = False

class ProductionConfig(Dp2Config):
    def __init__(self):
        super(ProductionConfig, self).__init__()

    SMTP_SERVICE_NAME = 'omf_smtp_service'
    SESSION_SERVICE_NAME = 'omf_redis_session_database'
    USER_DATABASE_SERVICE_NAME = 'geomf-service'
    PERMANENT_SESSION_LIFETIME = 21600


if 'OMF_ENVIRONMENT' in os.environ:
    if os.environ['OMF_ENVIRONMENT'] == 'PROD':
        the_config = ProductionConfig()
        logger.info('Using production config')
    elif os.environ['OMF_ENVIRONMENT'] == 'DEBUG':
        the_config = DebugConfig()
        logger.info('Using debug config')
    else:
        raise RuntimeError("Unsupported value ({}) of OMF_ENVIRONMENT env variable".format(
            os.environ['OMF_ENVIRONMENT']))
else:
    the_config = NRECAConfig()
    logger.info('Using NRECA config')
