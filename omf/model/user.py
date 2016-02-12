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

from passlib.hash import pbkdf2_sha512
from omf.model.dbo import db
from omf.common.userRole import Role
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    reg_key = db.Column(db.String(80), nullable =True)
    timestamp = db.Column(db.TIMESTAMP(timezone=True), nullable =True)
    registered = db.Column(db.Boolean, nullable=True)
    csrf = db.Column(db.String(80), nullable =True)
    password_digest = db.Column(db.String(200), nullable =True)
    role = db.Column(db.Enum('admin', 'user', 'public', name='role'))

    def __init__(self, username, reg_key = None, timestamp = None, registered = None, csrf = None, password_digest = None, role = Role.USER):
        self.username = username
        self.reg_key = reg_key
        self.timestamp = timestamp
        self.registered = registered
        self.csrf = csrf
        self.password_digest = password_digest
        if isinstance(role, Role):
            self.role = role.value
        else:
            self.role = role

    def get_id(self): return self.username

    def get_user_id(self):
        return self.id

    def verify_password(self, password):
        return pbkdf2_sha512.verify(password, self.password_digest)

    @staticmethod
    def hash_password(password):
        return pbkdf2_sha512.encrypt(password)
