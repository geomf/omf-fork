#!/bin/bash
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
set -x

PYTHON_DIR=$HOME/.localpython
THIS_FILE_DIR=$(cd $(dirname $0); pwd)

#local compile dependencies
REQUIRED_APT_PACKAGES="pkg-config libffi-dev python-dev libmemcached-dev libpng-dev libfreetype6-dev libgraphviz-dev unixodbc unixodbc-dev graphviz mdbtools"
for PKG in $REQUIRED_APT_PACKAGES; do
  dpkg-query -W $PKG || sudo apt-get -y install $PKG
done


${PYTHON_DIR}/bin/virtualenv --python ${PYTHON_DIR}/bin/python ${THIS_FILE_DIR}/venv

rm ${THIS_FILE_DIR}/../vendor/*.whl || true
#TODO: for some reason this picks up wrong python ABI -> run the whole script while inside VENV!
/bin/bash -c "source ${THIS_FILE_DIR}/venv/bin/activate; pip wheel -r ${THIS_FILE_DIR}/../requirements.txt --wheel-dir ${THIS_FILE_DIR}/../vendor --cache-dir ${THIS_FILE_DIR}/cache --build ${THIS_FILE_DIR}/build"

