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

if grep -q "mc3man/trusty-media" /etc/apt/sources.list /etc/apt/sources.list.d/*; then
    echo "Repo ppa:mc3man/trusty-media already exist"
else
    sudo add-apt-repository ppa:mc3man/trusty-media -y
    sudo apt-get update
fi

#local compile dependencies
REQUIRED_APT_PACKAGES=`cat $THIS_FILE_DIR/../apt_pkg.txt`
for PKG in $REQUIRED_APT_PACKAGES; do
  dpkg-query -W $PKG || sudo apt-get -y install $PKG
  sudo apt-get install -fy
done


${PYTHON_DIR}/bin/virtualenv --python ${PYTHON_DIR}/bin/python ${THIS_FILE_DIR}/venv


#TODO: for some reason this picks up wrong python ABI -> run the whole script while inside VENV!
/bin/bash -c "source ${THIS_FILE_DIR}/venv/bin/activate; pip wheel -r ${THIS_FILE_DIR}/../requirements.txt --wheel-dir ${THIS_FILE_DIR}/../vendor --cache-dir ${THIS_FILE_DIR}/cache --build ${THIS_FILE_DIR}/build -f file://${THIS_FILE_DIR}/../vendor --use-wheel"

