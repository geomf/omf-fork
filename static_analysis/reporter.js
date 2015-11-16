/*
 Open Modeling Framework (OMF) Software for simulating power systems behavior
 Copyright (c) 2015, Intel Corporation.

 This program is free software; you can redistribute it and/or modify it
 under the terms and conditions of the GNU General Public License,
 version 2, as published by the Free Software Foundation.

 This program is distributed in the hope it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
 more details.
 */
"use strict";

module.exports = {
    reporter: function (res) {
        var fs = require('fs');
        var text = fs.readFileSync( __dirname + '/report_template.html');
        var str = '';
        var fatalCodes = ['E0602', 'E1120', 'W0631'];
        var errorCodes = ['W0109', 'W0212', 'W0702', 'W0403', 'W0703', 'W0311'];
        var warningCodes = ['E1305'];
        var infoCodes = ['W1504', 'W0511'];

        function compare(a,b) {
            if (a.error.code < b.error.code)
                return -1;
            if (a.error.code > b.error.code)
                return 1;
            return 0;
        }

        res.sort(compare);

        res.forEach(function (r) {
            var file = r.file;
            var err = r.error;
            var className = '';
            if (err.code.indexOf('E') == 0) {
                className = "error";
            } else if (err.code.indexOf('W') == 0) {
                className = "warning";
            } else if (err.code.indexOf('F') == 0) {
                className = "fatal";
            } else if (err.code.indexOf('C') == 0) {
                className = "convention";
            } else if (err.code.indexOf('R') == 0) {
                className = "refactor";
            }

            if (fatalCodes.indexOf(err.code) != -1) {
                className = "fatal";
            } else if (errorCodes.indexOf(err.code) != -1) {
                className = "error";
            } else if (warningCodes.indexOf(err.code) != -1) {
                className = "warning";
            } else if (infoCodes.indexOf(err.code) != -1) {
                className = "info";
            }

            str += '<tr class="'+className+'"><td>' + file + "</td><td>" + err.line + "</td><td>" +
                err.character + "</td><td>" + err.reason + "</td><td style='display: none'>" + err.code + "</td></tr>";
        });


        if (str) {
            var html = text.toString();
            var position = html.indexOf('<div id="body">');
            var output = [html.slice(0, position), str, html.slice(position)].join('');
            process.stdout.write(output);
        }
    }
};