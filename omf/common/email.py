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

from flask_mail import Message


class Email(object):

    @staticmethod
    def send_email(sender, recipients, subject, message):
        from omf.web import mail, app
        with app.app_context():
            msg = Message(sender=sender, recipients=recipients, subject=subject)
            msg.body = message
            mail.send(msg)