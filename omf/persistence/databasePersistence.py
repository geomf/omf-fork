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

from omf.persistence.persistence import Persistence
from omf.model.dbo import db
from omf.model.user import User

class DatabasePersistence(Persistence):
    """
    The implementation of the abstract class Persistence which operates on database
    """
    def addUser(self, user):
        """
        Add new record to table user in database
        :param user: SQLAlchemy User object to add
        :return:
        """
        db.session.add(user)
        db.session.commit()

    def getUser(self, username):
        """
        Get user record from database
        :param username: String - user name
        :return: SQLAlchemy User object or None if user does not exist in database
        """
        try:
            user = db.session.query(User).filter_by(username=username).one()
        except:
            return None
        return user

    def deleteUser(self, username):
        """
        Delete user record from database
        :param username: String - user name
        :return:
        """
        user = self.getUser(username)
        db.session.delete(user)
        db.session.commit()

    def updateUser(self, user):
        """
        Update user record in database
        :param user: SQLAlchemy User object to update
        :return:
        """
        db.session.merge(user)
        db.session.commit()

    def getAllUsers(self):
        """
        Get list of all users from database
        :return: List of SQLAlchemy User objects
        """
        return User.query.all()
