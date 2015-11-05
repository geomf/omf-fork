#!/bin/bash -x
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
set -eou pipefail

PACKAGE="libmdbodbc1_0.7~rc1-4_amd64.deb"
THIS_FILE_DIR=$(cd $(dirname $0); pwd)

cd $THIS_FILE_DIR/../vendor/
if [ -f $THIS_FILE_DIR/../vendor/$PACKAGE ]; then
  echo "Other packages are installed"
else
    wget http://us.archive.ubuntu.com/ubuntu/pool/main/m/mdbtools/$PACKAGE -O $PACKAGE
fi

echo "Done."
