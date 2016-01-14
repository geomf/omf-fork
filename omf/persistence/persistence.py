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

from abc import ABCMeta, abstractmethod

class Persistence:
    """
    Abstract class to operate on persistent data
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def addUser(self, user):
        """
        Add user to persistence
        :param user: User object - SQLAlchemy database object
        :return:
        """
        pass

    @abstractmethod
    def getUser(self, username):
        """
        Get user from persistence
        :param username: String - user name
        :return: User database object
        """
        pass

    @abstractmethod
    def deleteUser(self, username):
        """
        Delete user from persistence
        :param username: String - user name
        :return:
        """
        pass

    @abstractmethod
    def updateUser(self, user):
        """
        Update user data in persistence
        :param user: User database object
        :return:
        """
        pass

    @abstractmethod
    def getAllUsers(self):
        """
        Get all users from persistence
        :return: List of users from persistence
        """
        pass
