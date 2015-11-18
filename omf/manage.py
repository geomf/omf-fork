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


import os.path
my_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(my_dir)

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from web import app, db
from common.userRole import Role

import logging

logging.basicConfig(format='%(asctime)s - %(process)d:%(threadName)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('boto').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.command
def populate_database():
    logger.info('Populating user database...')
    from omf.model.user import User
    from omf.web import persistence
    admin = User(username='admin', registered=True, password_digest=User.hash_password('admin'), role=Role.ADMIN.value)
    test = User(username='test', registered=True, password_digest=User.hash_password('test'))

    persistence.addUser(admin)
    persistence.addUser(test)


if __name__ == '__main__':
    manager.run()

