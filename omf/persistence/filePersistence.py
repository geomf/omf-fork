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
import json
import os
import logging
import datetime

from omf.persistence.persistence import Persistence
from omf.model.user import User

logger = logging.getLogger(__name__)

class FilePersistence(Persistence):
    USER_DIRECTORY = 'data/User'
    """
    The implementation of the abstract class Persistence which operates on json files
    """
    def addUser(self, user):
        """
        Add json file named: username.json which contains all columns from user object
        :param user: SQLAlchemy User object to add
        :return:
        """
        logger.info('Adding new user to file persistence, username: {0}', user.username)
        u = self._row2dict(user)
        path = self.__getUserFilePath(user.username)
        with open(path, "w") as file:
            logger.info('Creating user file: {0}', path)
            json.dump(u, file, indent=4)

    def getUser(self, username):
        """
        Get user object based on data in json file
        :param username: String - user name
        :return: SQLAlchemy User object or None if username.json file does not exist
        """
        path = self.__getUserFilePath(username)
        logger.info('Loading user: %s from file: %s', username, path)
        if os.path.isfile(path):
            with open(path, 'r') as file:
                user_dict = json.load(file)
            timestamp = user_dict.get('timestamp', None)
            if timestamp is not None:
                timestamp = datetime.datetime.strptime(timestamp, '%a %b %d %H:%M:%S %Y')

            return User(username=user_dict.get('username'), reg_key=user_dict.get('reg_key', None), timestamp=timestamp,
                        registered=user_dict.get('registered', None), csrf=user_dict.get('csrf', None),
                        password_digest=user_dict.get('password_digest', None), role=user_dict.get('role', None))
        else:
            return None

    def deleteUser(self, username):
        """
        Remove username.json file
        :param username: Strin - user name
        :return:
        """
        path = self.__getUserFilePath(username)
        logger.info('Removing user: %s file: %s', username, path)
        os.remove(path)

    def updateUser(self, user):
        """
        Update user data in username.json file
        :param user: SQLAlchemy User object
        :return:
        """
        u = self._row2dict(user)
        path = self.__getUserFilePath(user.username)
        logger.info('Updating user: %s file: %s', user.username, path)
        with open(path, 'w') as file:
            json.dump(u, file, indent=4)

    def getAllUsers(self):
        """
        Get list of all users from directory
        :return:
        """
        from omf.web import safeListdir
        user_names = []
        for file in safeListdir(self.USER_DIRECTORY):
            file_name , _ = os.path.splitext(file)
            user_names.append(file_name)
        users = []
        for user in user_names:
            users.append(self.getUser(user))
        return users

    @staticmethod
    def _row2dict(row):
        """
        Convert SQL Alchemy representation of row to dict, that contains all columns
        :param row: SQL Alchemy representation of row (database object)
        :return: dictionary, that contains columns and values for specific row
        """
        dict = {}
        for column in row.__table__.columns:
            value = getattr(row, column.name)
            if type(value) is datetime.datetime:
                value = value.strftime(format='%a %b %d %H:%M:%S %Y')
            dict[column.name] = value

        return dict

    @staticmethod
    def __getUserFilePath(username):
        return os.path.join(FilePersistence.USER_DIRECTORY, username + ".json")
