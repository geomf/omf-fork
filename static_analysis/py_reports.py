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

import pylint.lint as pylint
import pyflakes.api as pyflakes
from pylint.reporters import BaseReporter
from jinja2 import Environment, FileSystemLoader

class CollectionReporter(BaseReporter):
    env = Environment(loader=FileSystemLoader(searchpath='./'))
    fatalCodes = ['E0602', 'E1120', 'W0631']
    errorCodes = ['W0109', 'W0212', 'W0702', 'W0403', 'W0703', 'W0311']
    warningCodes = ['E1305']
    infoCodes = ['W1504', 'W0511']
    def __init__(self):
        self.reports = dict()
        self.str = '{% extends "report_template.html" %}' \
                   '{% block head %}' \
                   '<title></title>' \
                   '{% endblock %}' \
                   '{% block content %}' \
                   '<tbody>'
        super(CollectionReporter, self).__init__()

    def add_message(self, msg_id, location, msg):
        module_path = location[0]
        module = location[1]
        line_no = int(location[3])
        column_no = int(location[4])

        if not module in self.reports:
            self.reports[module] = []

        current_report = self.reports[module]
        current_report.append({line_no, msg_id, column_no, msg, module_path})

        className = ''
        if 'E' in msg_id:
            className = "error"
        elif 'W' in msg_id:
            className = "warning"
        elif 'F' in msg_id:
            className = "fatal"
        elif 'C' in msg_id:
            className = "convention"
        elif 'R' in msg_id:
            className = "refactor"

        if msg_id in self.fatalCodes:
            className = "fatal"
        elif msg_id in self.errorCodes:
            className = "error"
        elif msg_id in self.warningCodes:
            className = "warning"
        elif msg_id in self.infoCodes:
            className = "info"

        self.str += '<tr class="'+className+'"><td>'+ str(module_path) + "</td><td>" + str(line_no) + "</td><td>" + str(column_no) + "</td><td>" + str(msg) + "</td></tr>"

    def _display(self, layout):
        pass

    def flake(self, message):
        self.str += "<tr><td>"+ str(message.filename) + "</td><td>" + str(message.lineno) + "</td><td>" + str(message.col) + "</td><td>" + str(message.message % message.message_args) + "</td></tr>"

    def get_template(self):
        self.str += "</tbody>{% endblock %}"
        return self.str

    def save_report(self, file_name):
        template = self.env.from_string(self.get_template())
        with open(file_name, "w") as text_file:
            text_file.write(template.render())

if __name__ == "__main__":
    dirs = ['./../omf/']
    reporter = CollectionReporter()
    pylint.Run(dirs, reporter=reporter, exit=False)
    reporter.save_report("./pylint_report.html")
    reporter_pyflakes = CollectionReporter()
    warnings = pyflakes.checkRecursive(dirs, reporter_pyflakes)
    reporter_pyflakes.save_report("./pyflakes_report.html")